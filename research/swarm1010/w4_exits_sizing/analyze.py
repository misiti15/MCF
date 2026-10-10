"""W4 step 3 (NOTES.md 1.2, 1.4-1.7): build books P and T (one position per symbol, frozen under the base exits), apply
the 28 book rules and the 58 heat_fade_short configurations, score them. Open history only (inputs built from
lib.py frames and locked-filtered 1-minute bars). Output: results.csv, data/daily_*.parquet, data/report.json.
    python research/swarm1010/w4_exits_sizing/analyze.py
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

D = HERE / "data"
EXITS = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11"]
SCRATCH = ["X15", "X30", "X45"]
ZS = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8"]
PS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
DESC = {"base": "base exits (setup geometry, flatten 15:55)",
        "E1": "ATR5 trail 1.0x, no target", "E2": "ATR5 trail 1.5x, no target", "E3": "ATR5 trail 2.0x, no target",
        "E4": "time stop 30 min if MFE < +0.25R", "E5": "time stop 60 min if MFE < +0.25R",
        "E6": "time stop 90 min if MFE < +0.25R", "E7": "structural stop (30-min swing), risk = swing distance",
        "E8": "structural stop (60-min swing), risk = swing distance", "E9": "scale out 1/2 at +1R, rest BE to 15:55",
        "E10": "breakeven after +0.75R (target kept)", "E11": "flatten 15:30",
        "X15": "scratch: exit if MFE < +0.5R after 15 min", "X30": "scratch: MFE < +0.5R after 30 min",
        "X45": "scratch: MFE < +0.5R after 45 min",
        "Z1": "size x clip(med60/S13 SPY ATR%, 0.5, 2)", "Z2": "size x clip(med60/S14 SPY OR width, 0.5, 2)",
        "Z3": "skip if S13 > trailing p67", "Z4": "skip if S14 > trailing p67 (same tod)",
        "Z5": "S16 disp@09:50 > p67: no entries before 10:00", "Z6": "S16 disp@09:50 > p67: no entries before 10:30",
        "Z7": "S12 gap disp > p67: no entries before 10:30", "Z8": "anti: size x clip(S13/med60, 0.5, 2)",
        "P1": "per setup/day: stop after 2 losses", "P2": "per setup/day: stop after 3 losses",
        "P3": "per setup/day: stop at -3R closed", "P4": "per setup/day: stop at -5R closed",
        "P5": "max 5 entries/setup/day", "P6": "max 10 entries/setup/day", "P7": "max 20 entries/setup/day",
        "P8": "book daily stop -10R closed", "P9": "book daily stop -20R closed"}
PLATEAU = {"E1": ["E2"], "E2": ["E1", "E3"], "E3": ["E2"], "E4": ["E5"], "E5": ["E4", "E6"], "E6": ["E5"],
           "E7": ["E8"], "E8": ["E7"], "E9": [], "E10": [], "E11": [], "Z1": ["Z2"], "Z2": ["Z1"], "Z3": ["Z4"],
           "Z4": ["Z3"], "Z5": ["Z6"], "Z6": ["Z5"], "Z7": ["Z6"], "Z8": [], "P1": ["P2"], "P2": ["P1"],
           "P3": ["P4"], "P4": ["P3"], "P5": ["P6"], "P6": ["P5", "P7"], "P7": ["P6"],
           "X15": ["X30"], "X30": ["X15", "X45"], "X45": ["X30"]}


def tmin(tod):
    tod = np.asarray(tod)
    return (tod // 100) * 60 + tod % 100


# ------------------------------------------------------------------------------------------------ inputs
def load_inputs():
    t = pd.read_parquet(D / "trades_lab.parquet")
    t["key"] = t["symbol"] + "|" + t["date"] + "|" + t["tod"].astype(str) + "|" + t["side"] + "|" + t["geom"]
    s = pd.read_parquet(D / __import__("os").environ.get("W4_SIM", "sim.parquet"))
    t = t.merge(s, on="key", how="inner")
    t["entry_min"] = tmin(t["tod"])
    t["wnot"] = 0.25 * t["atr_d"] / t["close"]          # live notional view: $ at risk per slot-$ ~ 0.25 ATR%
    t = t.rename(columns={"base": "r"})
    for v in EXITS + SCRATCH:
        t[v] = t[v].astype(float)
    # orb20_a / intraday_momentum (backtester trades; own exits held fixed in every exit variant)
    b = pd.read_parquet(ROOT / "research/history2y/data/bt_trades.parquet")
    b["date"] = pd.to_datetime(b["date"]).dt.strftime("%Y-%m-%d")
    s_open = (b["date"] < lib.LOCKED[0]) | (b["date"] > lib.LOCKED[1])
    b = b[s_open].copy()
    et = pd.to_datetime(b["entry_time"]).dt.tz_convert("America/New_York")
    xt = pd.to_datetime(b["exit_time"]).dt.tz_convert("America/New_York")
    bb = pd.DataFrame({"date": b["date"], "symbol": b["symbol"], "setup": b["strategy"],
                       "side": np.where(b["side"] > 0, "long", "short"), "geom": "bt",
                       "entry_min": (et.dt.hour * 60 + et.dt.minute).to_numpy(),
                       "exit_min": (xt.dt.hour * 60 + xt.dt.minute).to_numpy(), "r": b["r_multiple"].astype(float),
                       "wnot": (b["entry"] - b["stop"]).abs() / b["entry"], "book": "P"})
    bb["tod"] = bb["entry_min"] // 60 * 100 + bb["entry_min"] % 60
    for v in EXITS + SCRATCH:
        bb[v] = bb["r"]
    bb["order"] = np.where(bb["setup"] == "orb20_a", 50, 51)
    return t, bb


def context(trades: pd.DataFrame) -> pd.DataFrame:
    """Z-rule signals at the trade's entry bar and their trailing (previous 60 open sessions, min 20) references."""
    c = pd.read_parquet(ROOT / "research/bdi/regime1009/data/ctx.parquet")[
        ["date", "tod", "S12_gap_disp", "S13_spy_atrpct", "S14_spy_orw", "S16_sect_disp"]]
    c["date"] = c["date"].astype(str)
    refs = {}
    for sig in ("S13_spy_atrpct", "S14_spy_orw", "S12_gap_disp", "S16_sect_disp"):
        pv = c.pivot(index="date", columns="tod", values=sig).sort_index()
        med = pv.shift(1).rolling(60, min_periods=20).median()
        p67 = pv.shift(1).rolling(60, min_periods=20).quantile(2 / 3)
        refs[sig] = (pv, med, p67)
    x = trades[["date", "tod"]].copy()
    bar = np.clip((tmin(x["tod"]) // 5) * 5, 590, 900)            # latest 5-min bar close <= entry, 09:50..15:00
    x["bar"] = (bar // 60) * 100 + bar % 60
    out = pd.DataFrame(index=trades.index)

    def look(df, dates, tods):
        s = df.stack()
        k = pd.MultiIndex.from_arrays([dates, tods])
        return s.reindex(k).to_numpy()

    for sig, (pv, med, p67) in refs.items():
        out[sig] = look(pv, x["date"], x["bar"])
        out[sig + "_med"] = look(med, x["date"], x["bar"])
        out[sig + "_p67"] = look(p67, x["date"], x["bar"])
        o950 = np.full(len(x), 950)
        out[sig + "_950"] = look(pv, x["date"], o950)
        out[sig + "_950p67"] = look(p67, x["date"], o950)
    return out


# ------------------------------------------------------------------------------------------------ book
def one_per_symbol(t: pd.DataFrame) -> pd.DataFrame:
    t = t.sort_values(["date", "entry_min", "order", "symbol"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    busy: dict = {}
    for i, (d, sym, em, xm) in enumerate(zip(t["date"].to_numpy(), t["symbol"].to_numpy(), t["entry_min"].to_numpy(),
                                             t["exit_min"].to_numpy())):
        k = (d, sym)
        if busy.get(k, -1) <= em:
            keep[i] = True
            busy[k] = xm
    return t[keep].reset_index(drop=True)


def stop_after(t: pd.DataFrame, group: list[str], kind: str, x: float) -> np.ndarray:
    """Keep mask for 'no new entries after the trigger' rules. Trigger = first exit time at which the closed P/L of the
    group reaches <= -x (kind 'r') or the count of losing closed trades reaches x (kind 'loss'). Trades entered
    before the trigger cannot be affected by blocked ones (those exit later), so the trigger is computed on all."""
    keep = np.ones(len(t), bool)
    for _, g in t.groupby(group, sort=False):
        o = g.sort_values("exit_min", kind="mergesort")
        v = o["r"].to_numpy() if kind == "r" else (o["r"].to_numpy() < 0).astype(float) * -1
        cum = np.cumsum(v)
        hit = np.flatnonzero(cum <= -x + 1e-12)
        if not len(hit):
            continue
        trig = o["exit_min"].to_numpy()[hit[0]]
        keep[g.index[g["entry_min"].to_numpy() >= trig]] = False
    return keep


def rule_weights(t: pd.DataFrame, cx: pd.DataFrame, rule: str) -> np.ndarray:
    w = np.ones(len(t))
    em = t["entry_min"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        if rule == "Z1":
            q = cx["S13_spy_atrpct_med"] / cx["S13_spy_atrpct"]
            w = np.where(np.isfinite(q), np.clip(q, 0.5, 2), 1.0)
        elif rule == "Z2":
            q = cx["S14_spy_orw_med"] / cx["S14_spy_orw"]
            w = np.where(np.isfinite(q) & (cx["S14_spy_orw"] > 0), np.clip(q, 0.5, 2), 1.0)
        elif rule == "Z8":
            q = cx["S13_spy_atrpct"] / cx["S13_spy_atrpct_med"]
            w = np.where(np.isfinite(q), np.clip(q, 0.5, 2), 1.0)
        elif rule == "Z3":
            w = np.where(cx["S13_spy_atrpct"] > cx["S13_spy_atrpct_p67"], 0.0, 1.0)
        elif rule == "Z4":
            w = np.where(cx["S14_spy_orw"] > cx["S14_spy_orw_p67"], 0.0, 1.0)
        elif rule in ("Z5", "Z6"):
            hi = cx["S16_sect_disp_950"] > cx["S16_sect_disp_950p67"]
            w = np.where(hi & (em < (600 if rule == "Z5" else 630)), 0.0, 1.0)
        elif rule == "Z7":
            hi = cx["S12_gap_disp_950"] > cx["S12_gap_disp_950p67"]
            w = np.where(hi & (em < 630), 0.0, 1.0)
        elif rule in ("P1", "P2"):
            w = stop_after(t, ["date", "setup"], "loss", 2 if rule == "P1" else 3).astype(float)
        elif rule in ("P3", "P4"):
            w = stop_after(t, ["date", "setup"], "r", 3 if rule == "P3" else 5).astype(float)
        elif rule in ("P5", "P6", "P7"):
            n = {"P5": 5, "P6": 10, "P7": 20}[rule]
            rank = t.sort_values(["entry_min", "order", "symbol"]).groupby(["date", "setup"]).cumcount()
            w = (rank.reindex(t.index).to_numpy() < n).astype(float)
        elif rule in ("P8", "P9"):
            w = stop_after(t, ["date"], "r", 10 if rule == "P8" else 20).astype(float)
    return np.asarray(w, float)


# ------------------------------------------------------------------------------------------------ metrics
def daily(t: pd.DataFrame, r: np.ndarray, w: np.ndarray, days: pd.Index) -> pd.Series:
    return pd.Series(r * w, index=t.index).groupby(t["date"].to_numpy()).sum().reindex(days, fill_value=0.0)


def maxdd(x: pd.Series) -> float:
    c = x.cumsum()
    return float((c - c.cummax()).min())


def book_metrics(name, rule, t, r, w, base_d, reg, days, half, scale_match=True):
    d_raw = daily(t, r, w, days)
    risk_b, risk_v = float(len(t)), float(w.sum())
    k = risk_b / risk_v if (scale_match and risk_v > 0) else 1.0
    d = d_raw * k
    delta = d - base_d
    up, dn = reg.reindex(days).to_numpy() == "up", reg.reindex(days).to_numpy() == "down"
    kept = w > 0
    rr, ww = r[kept], w[kept]
    regt = t.loc[kept, "date"].map(reg).to_numpy()
    exp_reg = {g: float((rr[regt == g] * ww[regt == g]).sum() / max(1e-9, ww[regt == g].sum())) for g in ("up", "down")}
    mon = pd.Series(delta.to_numpy()).groupby(np.array([d[:7] for d in days])).sum()
    sd = delta.std(ddof=1)
    out = {"book": name, "rule": rule, "desc": DESC.get(rule, rule), "n": int(kept.sum()), "mean_w": round(float(w[kept].mean()), 3),
           "risk_share": round(risk_v / risk_b, 3), "exp_r": round(float((rr * ww).sum() / ww.sum()), 4),
           "exp_up": round(exp_reg["up"], 4), "exp_down": round(exp_reg["down"], 4),
           "day_mean_raw": round(float(d_raw.mean()), 3), "sharpe_raw": round(float(d_raw.mean() / d_raw.std(ddof=1) * math.sqrt(252)), 3),
           "maxdd_raw": round(maxdd(d_raw), 1), "worst_day_raw": round(float(d_raw.min()), 1),
           "day_mean_rm": round(float(d.mean()), 3), "maxdd_rm": round(maxdd(d), 1),
           "up_day_rm": round(float(d[up].mean()), 3), "down_day_rm": round(float(d[dn].mean()), 3),
           "d_mean": round(float(delta.mean()), 4), "d_t": round(float(delta.mean() / (sd / math.sqrt(len(delta)))), 2) if sd > 0 else None,
           "d_up": round(float(delta[up].mean()), 4), "d_down": round(float(delta[dn].mean()), 4),
           "d_flat": round(float(delta[~up & ~dn].mean()), 4),
           "d_h1": round(float(delta[half].mean()), 4), "d_h2": round(float(delta[~half].mean()), 4),
           "d_month_pos": round(float((mon > 0).mean()), 3), "up_days": int(up.sum()), "down_days": int(dn.sum())}
    # live-notional view (weights x atr%/price), same risk matching
    wn = t["wnot"].to_numpy() / t["wnot"].mean()
    kn = float(wn.sum() / (w * wn).sum()) if (scale_match and (w * wn).sum() > 0) else 1.0
    dn_v = daily(t, r, w * wn, days) * kn
    dn_b = daily(t, t["r"].to_numpy(), wn, days)
    dd = dn_v - dn_b
    out["notional_d_mean"] = round(float(dd.mean()), 4)
    out["notional_d_up"] = round(float(dd[up].mean()), 4)
    out["notional_d_down"] = round(float(dd[dn].mean()), 4)
    return out, d


def heat_gates(name, rule, t, r, w, reg, n_tries):
    kept = w > 0
    tr = pd.DataFrame({"date": t.loc[kept, "date"].to_numpy(), "r": r[kept] * w[kept] / w[kept].mean()})
    s = G.summary(tr)
    rg = G.regime_split(tr, reg.to_frame("regime"))
    wf = G.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    busiest = float(tr.groupby("date").size().max() / len(tr)) if len(tr) else None
    v, fails = G.verdict(s, rg, wf, n_tries)
    return {"book": name, "rule": rule, "desc": DESC.get(rule, rule), "n": s.get("n"), "exp_r": s.get("exp_r"),
            "t": s.get("t"), "t_req": G.t_required(n_tries), "exp_up": rg["up"].get("exp_r"), "n_up": rg["up"].get("n"),
            "exp_down": rg["down"].get("exp_r"), "n_down": rg["down"].get("n"), "exp_flat": rg["flat"].get("exp_r"),
            "wf_share": wf.get("share_positive"), "ex_best_day": s.get("ex_best_day"),
            "busiest_share": round(busiest, 4) if busiest else None, "verdict": v, "fails": "; ".join(fails)}


def main():
    trades, bt = load_inputs()
    reg = lib.regimes()["regime"]
    reg.index = pd.Index([str(x) for x in reg.index])
    days = pd.Index(sorted(reg.index))
    half = np.arange(len(days)) < len(days) // 2
    rows, report = [], {}
    # reconciliation (1-minute base vs 5-minute lab r)
    rec = trades.groupby(["book", "setup"]).apply(lambda g: pd.Series({
        "n": len(g), "lab5_exp": g["r_lab5"].mean(), "min1_exp": g["r"].mean(),
        "corr": np.corrcoef(g["r_lab5"], g["r"])[0, 1], "share_diff": float((np.abs(g["r_lab5"] - g["r"]) > 1e-3).mean())}))
    rec.round(4).to_csv(D / "reconcile.csv")
    report["reconcile"] = {"max_abs_exp_diff": float((rec["lab5_exp"] - rec["min1_exp"]).abs().max()),
                           "min_corr": float(rec["corr"].min()), "max_share_diff": float(rec["share_diff"].max())}
    print(rec.round(4).to_string(), flush=True)

    for book in ("P", "T"):
        t = trades[trades["book"] == book].copy()
        if book == "P":
            t = pd.concat([t, bt], ignore_index=True)
        n_raw = len(t)
        t = one_per_symbol(t)
        cx = context(t)
        # max concurrent positions (base exits)
        ev = pd.concat([pd.DataFrame({"d": t["date"], "m": t["entry_min"], "x": 1}),
                        pd.DataFrame({"d": t["date"], "m": t["exit_min"], "x": -1})]).sort_values(["d", "m", "x"])
        conc = int(ev.groupby("d")["x"].cumsum().max())
        report[book] = {"raw_trades": int(n_raw), "book_trades": int(len(t)), "setups": int(t["setup"].nunique()),
                        "per_day": round(len(t) / len(days), 1), "max_concurrent": conc,
                        "per_setup": t.groupby("setup").size().to_dict()}
        print(book, report[book]["raw_trades"], "->", len(t), "max conc", conc, flush=True)
        base_d = daily(t, t["r"].to_numpy(), np.ones(len(t)), days)
        o, _ = book_metrics(book, "base", t, t["r"].to_numpy(), np.ones(len(t)), base_d, reg, days, half)
        rows.append(o)
        base_d.rename("base").to_frame().assign(regime=reg.reindex(days).to_numpy()).to_parquet(D / f"daily_{book}.parquet")
        for v in EXITS:
            r = t[v].to_numpy()
            ok = np.isfinite(r)
            r = np.where(ok, r, t["r"].to_numpy())
            o, _ = book_metrics(book, v, t, r, np.ones(len(t)), base_d, reg, days, half, scale_match=False)
            rows.append(o)
        for z in ZS + PS:
            w = rule_weights(t, cx, z)
            o, _ = book_metrics(book, z, t, t["r"].to_numpy(), w, base_d, reg, days, half)
            rows.append(o)
        # per-setup view of each exit rule (exp change per setup; how many setups improve in both regimes)
        ps = []
        regt = t["date"].map(reg).to_numpy()
        for v in EXITS:
            for su, g in t.groupby("setup"):
                gi = g.index.to_numpy()
                dlt = t.loc[gi, v].to_numpy() - t.loc[gi, "r"].to_numpy()
                rg = regt[gi]
                ps.append({"book": book, "rule": v, "setup": su, "n": len(gi), "base_exp": t.loc[gi, "r"].mean(),
                           "d_exp": dlt.mean(), "d_up": dlt[rg == "up"].mean() if (rg == "up").any() else np.nan,
                           "d_down": dlt[rg == "down"].mean() if (rg == "down").any() else np.nan})
        pd.DataFrame(ps).round(4).to_csv(D / f"per_setup_exits_{book}.csv", index=False)

    # heat_fade_short alone (current = book P's list before the symbol rule; full = Testing FD)
    n_tries = 19648 + 58
    hrows = []
    for lst, nm in (("P", "heat_fade_short"), ("T", "heat_fade_short-FD")):
        t = trades[(trades["book"] == lst) & (trades["setup"] == nm)].reset_index(drop=True)
        cx = context(t)
        hrows.append(heat_gates(nm, "base", t, t["r"].to_numpy(), np.ones(len(t)), reg, n_tries))
        for v in EXITS + SCRATCH:
            hrows.append(heat_gates(nm, v, t, t[v].to_numpy(), np.ones(len(t)), reg, n_tries))
        for z in ZS + PS[:7]:
            hrows.append(heat_gates(nm, z, t, t["r"].to_numpy(), rule_weights(t, cx, z), reg, n_tries))
    h = pd.DataFrame(hrows)
    h["plateau_mean"] = [np.nanmean([h.loc[(h["book"] == b) & (h["rule"] == q), "exp_r"].astype(float).mean()
                                     for q in PLATEAU.get(r, [])]) if PLATEAU.get(r) else np.nan
                         for b, r in zip(h["book"], h["rule"])]
    h["probation_pass"] = ((h["n"] >= 150) & (h["exp_up"] > 0) & (h["exp_down"] > 0) & (h["n_up"] >= 30)
                           & (h["n_down"] >= 30) & (h["t"].fillna(0) >= 2.0) & (h["wf_share"].fillna(0) >= 0.6)
                           & (h["plateau_mean"] > 0) & (h["ex_best_day"] > 0) & (h["busiest_share"] <= 0.10))
    b = pd.DataFrame(rows)
    b["pass"] = ((b["d_up"] > 0) & (b["d_down"] > 0) & (b["d_t"].fillna(0) >= G.t_required(56)) & (b["d_h1"] > 0)
                 & (b["d_h2"] > 0) & (b["d_month_pos"] >= 0.6))
    base = b[b["rule"] == "base"].set_index("book")
    b["sharpe_ok"] = [s >= base.loc[k, "sharpe_raw"] for k, s in zip(b["book"], b["sharpe_raw"])]
    b["dd_ok"] = [m >= base.loc[k, "maxdd_rm"] for k, m in zip(b["book"], b["maxdd_rm"])]
    b["pass"] = b["pass"] & b["sharpe_ok"] & b["dd_ok"]
    b.insert(0, "part", "book")
    h.insert(0, "part", "heat_fade_short")
    res = pd.concat([b, h], ignore_index=True)
    res.to_csv(HERE / "results.csv", index=False)
    report["configs"] = {"book": int((b["rule"] != "base").sum()), "heat": int((h["rule"] != "base").sum())}
    json.dump(report, open(D / "report.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    print(b.drop(columns=["desc"]).to_string(), flush=True)
    print(h.drop(columns=["desc", "fails"]).to_string(), flush=True)
    print(json.dumps({k: v for k, v in report.items() if k != "reconcile"}, default=str)[:3000])


if __name__ == "__main__":
    main()
