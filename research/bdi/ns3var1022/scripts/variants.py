"""ns3var1022 Part 2/3: the pre-declared variant grid (PLAN.md), as-run (mask -> refire chain -> lot cap on each
variant's own exit times), judged against P0 and same-minute random entries. Writes variants.csv, regime_table.csv,
counts.json and the P0 / finalist trade lists (scratch). Educational only - not financial advice.

    python research/bdi/ns3var1022/scripts/variants.py
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from load import build, chain, lot_cap
from nv import HERE, NV
from sim import simulate

REG = ["Bull", "Bear", "Choppy", "Quiet"]
N_LINEAGE_PRIOR = 165_764 + 1_254
DEF_RUN = {"refire": True, "cooldown": 1, "first_only": False, "cap": 3}
DEF_EXIT = {"side": "short", "ku": 1.0, "kd": 1.0}


def t_req(n):
    return max(1.5, math.sqrt(2 * math.log(n)))


# ------------------------------------------------------------------------------------------------ specs
def specs(df, P):
    p0 = df["p0"].to_numpy()
    f = {k: df[k].to_numpy(float) for k in ("rs", "runs_below", "vwapDistPct", "volumeRatio", "min6", "atr_pct_d",
                                             "peer_med", "spy_vwap", "qqq_vwap", "spy_fo", "d2", "breadth", "ret20",
                                             "beta60", "gap", "fromOpen", "sma50_dist_pct", "tod")}
    with np.errstate(invalid="ignore"):
        hold = (P["v"][:, 0] > 0) & (P["v"][:, 1] > 0) & (P["t"][:, 1] <= 1500)
    S = {}

    def add(fam, name, mask=None, exit=None, run=None, entry=0, desc=""):
        S[name] = {"fam": fam, "mask": p0 if mask is None else mask, "exit": {**DEF_EXIT, **(exit or {})},
                   "run": {**DEF_RUN, **(run or {})}, "entry": entry, "desc": desc}

    with np.errstate(invalid="ignore"):
        add("P", "P0", desc="NS3-FD as run (refire cd1, 3 lots)")
        for x in (3, 4, 5):
            add("A", f"A1 rs<=-{x}", p0 & (f["rs"] <= -x), desc=f"stock at least {x} pts weaker than SPY from the open")
        for x in (3, 6, 12):
            add("A", f"A2 below>={x}", p0 & (f["runs_below"] >= x), desc=f">= {x} bars below VWAP before the reclaim")
        add("A", "A3 reclaim<=0.10", p0 & (f["vwapDistPct"] <= 0.10), desc="reclaim closes <= 0.10% above VWAP")
        add("A", "A3 reclaim<=0.25", p0 & (f["vwapDistPct"] <= 0.25), desc="reclaim closes <= 0.25% above VWAP")
        add("A", "A3 reclaim>=0.25", p0 & (f["vwapDistPct"] >= 0.25), desc="reclaim closes >= 0.25% above VWAP")
        add("A", "A4 vol<=1.0", p0 & (f["volumeRatio"] <= 1.0), desc="reclaim bar volume ratio <= 1.0")
        add("A", "A4 vol>=1.5", p0 & (f["volumeRatio"] >= 1.5), desc="reclaim bar volume ratio >= 1.5")
        add("A", "A5 min6<=-1.0", p0 & (f["min6"] <= -1.0), desc="was >= 1% below VWAP in the 6 bars before")
        add("A", "A5 min6>=-0.5", p0 & (f["min6"] >= -0.5), desc="stayed within 0.5% of VWAP in the 6 bars before")
        add("A", "A6 atr%<=3", p0 & (f["atr_pct_d"] <= 3), desc="daily ATR <= 3% of price")
        add("A", "A6 atr%<=5", p0 & (f["atr_pct_d"] <= 5), desc="daily ATR <= 5% of price")
        add("A", "A6 atr%>=3", p0 & (f["atr_pct_d"] >= 3), desc="daily ATR >= 3% of price")
        add("A", "A7 peers<0", p0 & (f["peer_med"] < 0), desc="5 most-correlated peers' median from-open < 0")
        add("A", "A7 peers<-1", p0 & (f["peer_med"] < -1), desc="peers' median from-open < -1%")
        add("A", "A8 spy<vwap", p0 & (f["spy_vwap"] < 0), desc="SPY below its VWAP at entry")
        add("A", "A8 qqq<vwap", p0 & (f["qqq_vwap"] < 0), desc="QQQ below its VWAP at entry")
        add("A", "A8 spy>vwap", p0 & (f["spy_vwap"] > 0), desc="SPY above its VWAP at entry")
        add("A", "A8 spy_fo>0", p0 & (f["spy_fo"] > 0), desc="SPY up from the open at entry")
        add("A", "A9 breadth falling", p0 & (f["d2"] < 0), desc="breadth fell over the last 2 bars")
        add("A", "A9 breadth<=0.5", p0 & (f["breadth"] <= 0.5), desc="breadth <= 0.5")
        add("A", "A10 ret20<=10", p0 & (f["ret20"] <= 10), desc="20-day return <= +10%")
        add("A", "A10 ret20<0", p0 & (f["ret20"] < 0), desc="20-day return < 0")
        add("A", "A11 beta<=1", p0 & (f["beta60"] <= 1.0), desc="60-day beta to SPY <= 1.0")
        add("A", "A11 skip beta>=1.5", p0 & ~(f["beta60"] >= 1.5), desc="skip 60-day beta >= 1.5")
        add("A", "A12 gap>-2", p0 & (f["gap"] > -2), desc="not gapped down more than 2%")
        add("A", "A12 gap<0", p0 & (f["gap"] < 0), desc="gapped down")
        sma = f["sma50_dist_pct"] > 0
        add("A", "A13 fo<-1.5", sma & (f["fromOpen"] < -1.5), desc="down > 1.5% from the open (was 2%)")
        add("A", "A13 fo<-3", sma & (f["fromOpen"] < -3), desc="down > 3% from the open")
        add("A", "A13 fo<-4", sma & (f["fromOpen"] < -4), desc="down > 4% from the open")
        add("A", "A14 no sma50", f["fromOpen"] < -2, desc="sma50 condition removed")
    add("B", "B1 t05s1", exit={"ku": 0.5}, desc="target 0.5R")
    add("B", "B2 t1s05", exit={"kd": 0.5}, desc="stop 0.5R (R = 0.5 x 0.25 ATR, same $ risk)")
    for k, mins in ((6, 30), (12, 60), (24, 120)):
        add("B", f"B3 time{mins}", exit={"time_bars": k}, desc=f"time stop {mins} min")
    add("B", "B4 trail1 notgt", exit={"ku": None, "trail": 1.0}, desc="trailing 1R stop, no target")
    add("B", "B4 t1 trail0.5@0.5", exit={"trail": 0.5, "trail_after": 0.5}, desc="1R target, 0.5R trail after +0.5R")
    add("B", "B5 scale0.35", exit={"scale": 0.35}, desc="half off at +0.35R, rest 1R/1R")
    add("B", "B5 scale0.5 be", exit={"scale": 0.5, "scale_be": True}, desc="half off at +0.5R, rest stop to entry")
    add("B", "B6 be@0.5", exit={"be": 0.5}, desc="stop to entry after +0.5R")
    for k in (1.25, 1.5):
        add("B", f"B7 stop{k}x same tgt", exit={"kd": k, "ku": 1.0}, desc=f"stop {k}x wider, same $ risk, same price target")
        add("B", f"B7 stop{k}x tgt{k}x", exit={"kd": k, "ku": k}, desc=f"stop and target {k}x wider, same $ risk")
    add("B", "B8 flat1400", exit={"flat_tod": 1400}, desc="flat by 14:00")
    add("B", "B8 flat1500", exit={"flat_tod": 1500}, desc="flat by 15:00")
    add("C", "C1 first only", run={"first_only": True}, desc="first signal per symbol-day only")
    add("C", "C2 cooldown3", run={"cooldown": 3}, desc="refire cooldown 3 bars")
    add("C", "C2 cooldown6", run={"cooldown": 6}, desc="refire cooldown 6 bars")
    add("C", "C3 cap1", run={"cap": 1}, desc="max 1 open lot per symbol")
    add("C", "C3 cap2", run={"cap": 2}, desc="max 2 open lots per symbol")
    tod = f["tod"]
    add("D", "D1 from1000", p0 & (tod >= 1000), desc="no entries before 10:00")
    add("D", "D2 until1400", p0 & (tod <= 1400), desc="no entries after 14:00")
    add("D", "D3 1000-1400", p0 & (tod >= 1000) & (tod <= 1400), desc="10:00-14:00 only")
    add("D", "D4 0950-1130", p0 & (tod <= 1130), desc="09:50-11:30 (parent window) with refire")
    add("D", "D5 1130-1500", p0 & (tod > 1130), desc="after 11:30 only")
    add("E", "E1 long mirror", exit={"side": "long"}, desc="LONG at the NS3 signal bar, t1s1")
    add("E", "E2 long hold2", p0 & hold, exit={"side": "long"}, entry=2,
        desc="LONG when price holds above VWAP 2 more bars (entry at the 2nd bar close), t1s1")
    with np.errstate(invalid="ignore"):
        add("E", "E3 long hold2 spy>vwap", p0 & hold & (f["spy_vwap"] > 0), exit={"side": "long"}, entry=2,
            desc="E2 while SPY is above its VWAP at the signal")
    add("E", "E4 long hold2 t05s1", p0 & hold, exit={"side": "long", "ku": 0.5}, entry=2, desc="E2 with target 0.5R")
    return S


# ------------------------------------------------------------------------------------------------ run one variant
_SIM = {}


def run_exit(df, P, Q, ex, entry):
    key = json.dumps({**ex, "entry": entry}, sort_keys=True)
    if key in _SIM:
        return _SIM[key]
    kw = {k: v for k, v in ex.items() if k != "side"}
    if entry == 0:
        E, tod0 = df["close"].to_numpy(float), df["tod"].to_numpy(float)
        sl = slice(0, None)
        Eq = df["p_close"].to_numpy(float)
    else:
        E, tod0 = P["c"][:, entry - 1], P["t"][:, entry - 1]
        sl = slice(entry, None)
        Eq = Q["c"][:, entry - 1]
    D = 0.25 * df["atr_d"].to_numpy(float)
    r, et, kd = simulate(E, D, P["h"][:, sl], P["l"][:, sl], P["c"][:, sl], P["t"][:, sl], ex["side"], tod0,
                         df["gap"].to_numpy(float), **kw)
    Dq = 0.25 * df["p_atr"].to_numpy(float)
    rq, _, _ = simulate(Eq, Dq, Q["h"][:, sl], Q["l"][:, sl], Q["c"][:, sl], Q["t"][:, sl], ex["side"], tod0,
                        df["p_gap"].to_numpy(float), **kw)
    rq = np.where(df["p_ok"].to_numpy(bool), rq, np.nan)
    _SIM[key] = (r, et, kd, rq, tod0)
    return _SIM[key]


def as_run(df, P, Q, sp):
    r, et, kd, rq, tod0 = run_exit(df, P, Q, sp["exit"], sp["entry"])
    m = np.asarray(sp["mask"], bool) & np.isfinite(r) & np.isfinite(tod0) & (tod0 <= 1500)
    idx = np.flatnonzero(m)
    run = sp["run"]
    ck = chain(df["symbol"].to_numpy()[idx], df["date"].to_numpy()[idx], df["tod"].to_numpy()[idx],
               run["refire"], run["cooldown"], run["first_only"])
    idx = idx[ck]
    lk = lot_cap(df["date"].astype(str).to_numpy()[idx], tod0[idx], df["symbol"].to_numpy()[idx], et[idx], run["cap"])
    idx = idx[lk]
    t = df.iloc[idx][["symbol", "date", "tod", "split", "regime", "dow"]].copy()
    t["r"], t["ctrl"], t["exit_tod"], t["kind"] = r[idx], rq[idx], et[idx], kd[idx]
    t["row"] = idx
    return t.reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ statistics
def cl(x, dates):
    """mean, day-clustered t, n (gates.summary convention)."""
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    x, dates = x[ok], np.asarray(dates)[ok]
    if len(x) < 2:
        return (float(x.mean()) if len(x) else float("nan")), float("nan"), len(x)
    mu = x.mean()
    g = pd.DataFrame({"d": dates, "x": x}).groupby("d")["x"].agg(["sum", "size"])
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(x)
    return float(mu), (float(mu / se) if se > 0 else float("nan")), len(x)


def day_diff_t(t, p0):
    a = t.groupby("date")["r"].sum()
    b = p0.groupby("date")["r"].sum()
    d = a.reindex(b.index.union(a.index), fill_value=0) - b.reindex(b.index.union(a.index), fill_value=0)
    if len(d) < 2 or d.std(ddof=1) == 0:
        return float("nan")
    return float(d.mean() / (d.std(ddof=1) / math.sqrt(len(d))))


def stats(t, p0):
    out = {"n": len(t)}
    for sp in ("train", "valid", "all"):
        x = t if sp == "all" else t[t["split"] == sp]
        q = p0 if sp == "all" else p0[p0["split"] == sp]
        mu, tt, n = cl(x["r"], x["date"])
        out[f"{sp}_n"], out[f"{sp}_avg"], out[f"{sp}_t"], out[f"{sp}_tot"] = n, mu, tt, float(x["r"].sum())
        out[f"{sp}_kept"] = n / max(1, len(q))
        ex, ext, _ = cl(x["r"] - x["ctrl"], x["date"])
        out[f"{sp}_ctrl"] = float(np.nanmean(x["ctrl"])) if len(x) else float("nan")
        out[f"{sp}_excess"], out[f"{sp}_excess_t"] = ex, ext
        out[f"{sp}_vs_thin"] = float(x["r"].sum() - q["r"].sum() * n / max(1, len(q)))
        out[f"{sp}_diff_t"] = day_diff_t(x, q)
        for rg in REG:
            xr = x[x["regime"] == rg]
            out[f"{sp}_{rg}_n"], out[f"{sp}_{rg}_avg"] = len(xr), (float(xr["r"].mean()) if len(xr) else float("nan"))
            out[f"{sp}_{rg}_tot"] = float(xr["r"].sum())
    dd = t.groupby("date")["r"].sum().sort_values()
    out["days"] = len(dd)
    out["worst_day"] = float(dd.iloc[0]) if len(dd) else float("nan")
    k = max(1, int(round(0.05 * len(dd))))
    out["worst5pct_mean"] = float(dd.iloc[:k].mean()) if len(dd) else float("nan")
    out["best_day"] = float(dd.iloc[-1]) if len(dd) else float("nan")
    tot = float(t["r"].sum())
    out["best_day_share"] = float(dd.iloc[-1] / tot) if tot > 0 and len(dd) else float("nan")
    return out


def judge(o, p, n_study, n_lin):
    """Pre-declared tests (PLAN.md Part 3)."""
    bar_s, bar_l = t_req(n_study), t_req(n_lin)
    w = {}
    w["W1"] = o["train_avg"] > p["train_avg"] and o["valid_avg"] > p["valid_avg"]
    w["W2"] = o["train_vs_thin"] > 0 and o["valid_vs_thin"] > 0
    bc_p = p["all_Bull_tot"] + p["all_Choppy_tot"]
    bc_v = o["all_Bull_tot"] + o["all_Choppy_tot"]
    w["W3"] = (bc_v >= 0.75 * bc_p) and (o["all_Bear_tot"] >= 0.75 * p["all_Bear_tot"])
    w["W4"] = o["train_kept"] >= 0.5 and o["valid_kept"] >= 0.5
    w["W5"] = (o["all_diff_t"] or 0) >= bar_l
    w["W5_study"] = (o["all_diff_t"] or 0) >= bar_s
    edit = all(w[k] for k in ("W1", "W2", "W3", "W4", "W5"))
    pos = o["train_avg"] > 0 and o["valid_avg"] > 0
    beats = (o["train_excess"] > 0) and (o["valid_excess"] > 0)
    testing = pos and beats and (o["all_t"] or 0) >= bar_l
    near = pos and beats and o["train_n"] >= 30 and o["valid_n"] >= 20 and \
        (np.isfinite(o["best_day_share"]) and o["best_day_share"] <= 0.25)
    fails = [k for k in ("W1", "W2", "W3", "W4", "W5") if not w[k]]
    return {**{k: bool(v) for k, v in w.items()}, "edit_pass": edit, "pos_both": pos, "beats_random_both": beats,
            "testing_bar": testing, "near_miss_merit": bool(near), "edit_fails": ",".join(fails)}


def combine(S, a, b):
    sa, sb = S[a], S[b]
    m = np.asarray(sa["mask"], bool) & np.asarray(sb["mask"], bool)
    ex = sb["exit"] if sb["fam"] == "B" else sa["exit"]
    run = dict(DEF_RUN)
    for s_ in (sa, sb):
        if s_["fam"] == "C":
            run = s_["run"]
    return {"fam": "F", "mask": m, "exit": ex, "run": run, "entry": 0, "desc": f"{a} + {b}"}


def main():
    df, P, Q = build()
    # parity: the simulator reproduces the frames' lab outcome (production cost, tier) at the signal bar
    from mcf.research.gates import prod_r
    par = {}
    for geom, (ku, kd) in {"t1s1": (1, 1), "t05s1": (0.5, 1), "t1s05": (1, 0.5)}.items():
        r, _, _ = simulate(df["close"].to_numpy(float), 0.25 * df["atr_d"].to_numpy(float), P["h"], P["l"], P["c"], P["t"],
                           "short", df["tod"].to_numpy(float), df["gap"].to_numpy(float), ku=ku, kd=kd)
        lab = df[f"r_short_{geom}"].to_numpy(float)
        win = df[f"win_short_{geom}"].to_numpy(float)
        c, atr, tod = df["close"].to_numpy(float), df["atr_d"].to_numpy(float), df["tod"].to_numpy(float)
        p = prod_r(lab, win, c, atr, geom, tod=tod)
        R = 0.25 * atr
        gross = lab + 2 * 0.01 / R
        tier = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
        ref = gross - tier * (gross - p) if kd == 1 else None
        if kd != 1:      # lab R for t1s05 is in units of 0.25 ATR; ours is per $ risk (0.5 x that)
            ref = (gross - tier * (gross - p)) / kd
        d = np.abs(r - ref)
        par[geom] = {"n": int(np.isfinite(d).sum()), "max_abs_diff": float(np.nanmax(d)),
                     "share_within_1e-4": float(np.mean(d[np.isfinite(d)] < 1e-4))}
    print("parity", par, flush=True)
    S = specs(df, P)
    rows, trades = [], {}
    p0 = as_run(df, P, Q, S["P0"])
    trades["P0"] = p0
    pst = stats(p0, p0)
    n_study = 73
    n_lin = N_LINEAGE_PRIOR + n_study
    for name, sp in S.items():
        t = p0 if name == "P0" else as_run(df, P, Q, sp)
        trades[name] = t
        o = stats(t, p0)
        rows.append({"variant": name, "fam": sp["fam"], "desc": sp["desc"], **o, **judge(o, pst, n_study, n_lin)})
        print(name, len(t), round(o["train_avg"], 4), round(o["valid_avg"], 4), flush=True)
    res = pd.DataFrame(rows)
    # pairs (selected on TRAIN only)
    single = res[res["fam"].isin(["A", "C", "D"])]
    top_e = single[single["train_vs_thin"] > 0].sort_values("train_vs_thin", ascending=False)["variant"].head(3).tolist()
    top_x = res[res["fam"] == "B"].sort_values("train_avg", ascending=False)["variant"].head(2).tolist()
    pairs = [(a, b) for a in top_e for b in top_x] + [(top_e[i], top_e[j]) for i in range(len(top_e))
                                                       for j in range(i + 1, len(top_e))]
    for a, b in pairs:
        name = f"F {a} + {b}"
        sp = combine(S, a, b)
        S[name] = sp
        t = as_run(df, P, Q, sp)
        trades[name] = t
        o = stats(t, p0)
        rows.append({"variant": name, "fam": "F", "desc": sp["desc"], **o, **judge(o, pst, n_study, n_lin)})
        print(name, len(t), round(o["train_avg"], 4), round(o["valid_avg"], 4), flush=True)
    res = pd.DataFrame(rows)
    n_counted = int((res["variant"] != "P0").sum())
    res.to_csv(HERE / "variants.csv", index=False, float_format="%.4f")
    json.dump({"configs_counted": n_counted, "planned": 73, "pairs_selected_on_train": {"entry": top_e, "exit": top_x},
               "study_bar": round(t_req(n_counted), 3), "lineage_prior": N_LINEAGE_PRIOR,
               "lineage_N": N_LINEAGE_PRIOR + n_counted, "lineage_bar": round(t_req(N_LINEAGE_PRIOR + n_counted), 3),
               "parity": par, "reference_rows_not_counted": ["P0"]},
              open(HERE / "counts.json", "w"), indent=1)
    pd.to_pickle({"trades": trades, "S_desc": {k: v["desc"] for k, v in S.items()}}, NV / "trades.pkl")
    df.drop(columns=[]).to_pickle(NV / "cand.pkl")


if __name__ == "__main__":
    main()
