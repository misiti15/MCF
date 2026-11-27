"""QQQOPEN-1127 scoring (PREREG.md): costs (LIVE-L, LR8, ETF-TIGHT), per-split stats, H1 / H2 bars, size-matched
random-day control, per-year and regime splits, live parity. Locked block never read (asserted).
    python research/qqqopen_1127/qo_score.py <scratch_out_dir> <raw_2016_2022_dir> <late_dir>
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import qo_sim  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

CELLS = json.load(open(HERE.parent / "primshorts_1126/cells_live.json"))
PB = [0, 5, 10, 20, 50, 100, 1e9]; PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]
KIND = {0: "market", 1: "stop"}
LOCK = qo_sim.LOCK
SPLITS = ["EARLY", "T2", "FIT", "CHECK"]
H1 = [("QQQ", "TQQQ", 1.0, "FADE-LONG", "HOLD"), ("QQQ", "TQQQ", 1.0, "FADE-LONG", "TRAIL"),
      ("SPY", "SPXL", 0.75, "FADE-LONG", "TRAIL")]
H1NAME = {H1[0]: "IDX1-hold", H1[1]: "IDX1-trail", H1[2]: "IDX3-trail"}
KEY = ["sig", "trd", "X", "rule", "exit"]


def costs(t: pd.DataFrame) -> pd.DataFrame:
    price = t.entry.to_numpy(float); risk = t.risk.to_numpy(float); kind = t.kind.to_numpy(int)
    pb = pd.cut(price, PB, labels=PBL, right=False).astype(str)
    a = np.empty(len(t)); b = np.empty(len(t))
    for i, (p, k) in enumerate(zip(pb, kind)):
        a[i], b[i] = CELLS.get(f"{p}|{KIND[k]}", CELLS[f"*|{KIND[k]}"])[:2]
    t["c_livel"] = a / (risk / price * 1e4) + b
    side = t.side.to_numpy(); px = t.exit_px.to_numpy(float)
    tier = np.where(price < 5, 3.0, 1.0)
    ec = (0.01 + price * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = 0.01 + px * 1e-4 + np.where(kind == 1, 0.02, 0.0)
    br = np.where(side < 0, 1.2e-4 * price, 0.0)
    t["c_lr8"] = (tier * (ec + xc) + br) / risk
    t["c_tight"] = (1e-4 * price + 1e-4 * px + np.where(kind == 1, 0.01, 0.0)) / risk
    for c in ("livel", "lr8", "tight"):
        t[f"r_{c}"] = t.gross - t[f"c_{c}"]
    return t


def st(x: pd.Series, d: pd.Series | None = None) -> dict:
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return dict(n=0)
    if d is not None:                      # day-clustered: sum per day
        s = pd.Series(x).groupby(np.asarray(d)).sum().to_numpy()
    else:
        s = x
    m = s.mean(); sd = s.std(ddof=1) if len(s) > 1 else np.nan
    tot = x.sum(); best = s.max()
    return dict(n=n, days=len(s), mean=round(float(x.mean()), 3), tot=round(float(tot), 2),
                t=round(float(m / (sd / np.sqrt(len(s)))), 2) if len(s) > 1 and sd > 0 else None,
                win=round(float((x > 0).mean()), 3),
                best_share=round(float(best / tot), 3) if tot > 0 else None,
                wo_best=round(float((tot - best) / (n - 1)), 3) if n > 1 else None)


@numba.njit(cache=False)
def sim_nb(o, h, l, c, mins, j, fill, stop, side, exit_min, trail):
    risk = side * (fill - stop)
    mfe = 0.0
    n = len(o)
    for k in range(j, n):
        if mins[k] >= exit_min:
            return side * (o[k] - fill) / risk, 0
        hit = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk, 1
        fav = h[k] if side == 1 else l[k]
        v = side * (fav - fill) / risk
        if v > mfe:
            mfe = v
        if trail and mfe >= 1.0:
            tr = fill + side * (mfe - 1.0) * risk
            if side == 1:
                stop = max(stop, tr)
            else:
                stop = min(stop, tr)
    return side * (c[n - 1] - fill) / risk, 0


def control(tr: pd.DataFrame, days: dict, draws: int, rng) -> dict:
    """Size-matched random-day control: same count per split, random other days of the same split, entry at the same
    clock minute, same stop distance in % of price, same side and exit, cost = the actual trade's LIVE-L cost."""
    actual = tr.r_livel.mean()
    sig_days = set(tr.date)
    pools = {s: [d for d in days if qo_sim.split_of(pd.Timestamp(d).date()) == s and d not in sig_days] for s in SPLITS}
    means = np.empty(draws)
    rows = tr[["split", "emin", "stop_pct", "side", "exit", "c_livel"]].to_numpy()
    for b in range(draws):
        rs = []
        for sp, em, spct, side, ex, cst in rows:
            for _ in range(20):
                d = pools[sp][rng.integers(len(pools[sp]))]
                o, h, l, c, mins = days[d]
                js = np.searchsorted(mins, em)
                if js < len(mins) - 1 and mins[js] == em:
                    break
            fill = o[js]; stop = fill * (1 - side * spct / 100)
            exit_min = min(955, mins[-1] + 1 - 5)
            g, _ = sim_nb(o, h, l, c, mins, js, fill, stop, int(side), exit_min, ex == "TRAIL")
            rs.append(g - cst)
        means[b] = np.mean(rs)
    return dict(actual=round(float(actual), 3), ctrl_mean=round(float(means.mean()), 3),
                ctrl_p95=round(float(np.quantile(means, 0.95)), 3), pct=round(float((means < actual).mean()), 3))


def main(out_dir: str, raw_dir: str, late_dir: str):
    out = Path(out_dir)
    t = pd.read_csv(out / "trades.csv.gz")
    dd = pd.to_datetime(t.date).dt.date
    assert not ((dd >= LOCK[0]) & (dd <= LOCK[1])).any()
    t = costs(t)
    ctx = pd.read_csv(out / "dayctx.csv.gz")
    t = t.merge(ctx[["date", "sig", "above50", "rv20"]], on=["date", "sig"], how="left")
    q = ctx.groupby("sig").rv20.quantile([1 / 3, 2 / 3]).unstack()
    t["vol"] = [("lo" if v <= q.loc[s, 1 / 3] else "hi" if v > q.loc[s, 2 / 3] else "mid") if np.isfinite(v) else "na"
                for s, v in zip(t.sig, t.rv20)]
    t["year"] = t.date.str[:4]
    res = {"configs": {}, "n_configs": 0}
    grid = t.groupby(KEY)
    for k, g in grid:
        name = "|".join(map(str, k))
        r = {"ALL": st(g.r_livel, g.date), "ALL_lr8": st(g.r_lr8, g.date), "ALL_tight": st(g.r_tight, g.date),
             "ALL_gross": st(g.gross, g.date)}
        for s in SPLITS:
            gs = g[g.split == s]
            r[s] = st(gs.r_livel, gs.date); r[s + "_lr8"] = st(gs.r_lr8, gs.date)
        dev = g[g.split.isin(["EARLY", "FIT"])]; oos = g[g.split.isin(["T2", "CHECK"])]
        r["DEV"] = st(dev.r_livel, dev.date); r["T2CHECK"] = st(oos.r_livel, oos.date)
        res["configs"][name] = r
    res["n_configs"] = len(res["configs"])
    # ---- H1
    traded = {}
    for s in ("TQQQ", "SPXL"):
        df = qo_sim.load(s, Path(raw_dir))
        traded[s] = {str(d): (g.open.to_numpy(float), g.high.to_numpy(float), g.low.to_numpy(float),
                              g.close.to_numpy(float), qo_sim.tmin(g.index).astype(np.int64))
                     for d, g in df.groupby(df.index.date) if len(g) >= 40}
    rng = np.random.default_rng(20261127)
    h1 = {}
    for k in H1:
        g = t[(t.sig == k[0]) & (t.trd == k[1]) & (t.X == k[2]) & (t.rule == k[3]) & (t.exit == k[4])].copy()
        name = "|".join(map(str, k))
        r = res["configs"][name]
        yrs = g.groupby("year").r_livel.agg(["size", "mean", "sum"]).round(3)
        y3 = yrs[yrs["size"] >= 3]
        ctrl = control(g, traded[k[1]], 500, rng)
        reg = {f"above50={a}": st(x.r_livel, x.date) for a, x in g.groupby("above50")}
        reg.update({f"vol={a}": st(x.r_livel, x.date) for a, x in g.groupby("vol")})
        bars = {
            "1_pos_EARLY_T2_CHECK": all((r[s].get("mean") or -1) > 0 for s in ("EARLY", "T2", "CHECK")),
            "2_t_all_ge_2.13": (r["ALL"]["t"] or 0) >= 2.13,
            "3_wo_best_pos_share_lt_50": (r["ALL"]["wo_best"] or -1) > 0 and (r["ALL"]["best_share"] or 1) < 0.5,
            "4_control_gt_p95": ctrl["actual"] > ctrl["ctrl_p95"],
            "5_years_pos_ge_60pct": bool((y3["mean"] > 0).mean() >= 0.6),
            "6_both_trend_regimes_pos": all((reg.get(f"above50={a}", {}).get("mean") or -1) > 0 for a in (True, False)),
        }
        h1[H1NAME[k]] = dict(config=name, stats=r, years=yrs.reset_index().to_dict("records"), control=ctrl,
                             regimes=reg, bars=bars, passed=all(bars.values()))
    res["H1"] = h1
    # 1x instrument check
    one = t[t.trd == t.sig]
    res["onex"] = {"|".join(map(str, k)): {s: st(g[g.split == s].r_livel) for s in SPLITS} | {"ALL": st(g.r_livel)}
                   for k, g in one.groupby(KEY)}
    # ---- H2
    rows = []
    for name, r in res["configs"].items():
        sig, trd = name.split("|")[:2]
        if sig == trd:
            continue
        rows.append(dict(config=name, dev_n=r["DEV"].get("n", 0), dev_t=r["DEV"].get("t") or -9,
                         dev_mean=r["DEV"].get("mean"), t2=r["T2"].get("mean"), check=r["CHECK"].get("mean"),
                         early=r["EARLY"].get("mean"), fit=r["FIT"].get("mean"), oos_t=r["T2CHECK"].get("t"),
                         all_mean=r["ALL"].get("mean"), all_t=r["ALL"].get("t"), all_n=r["ALL"].get("n"),
                         lr8_all=r["ALL_lr8"].get("mean"), tight_all=r["ALL_tight"].get("mean"),
                         best_share=r["ALL"].get("best_share"), wo_best=r["ALL"].get("wo_best")))
    tab = pd.DataFrame(rows).sort_values("dev_t", ascending=False)
    tab.to_csv(HERE / "grid.csv", index=False)
    elig = tab[(tab.dev_t >= 2.0) & (tab.dev_n >= 30)].head(4)
    fin_is = len(elig) > 0
    fins = elig if fin_is else tab.head(4)
    h2 = {}
    for _, f in fins.iterrows():
        sig, trd, X, rule, ex = f.config.split("|")
        g = t[(t.sig == sig) & (t.trd == trd) & (t.X == float(X)) & (t.rule == rule) & (t.exit == ex)].copy()
        ctrl = control(g, traded[trd], 300, rng)
        r = res["configs"][f.config]
        bars = {"dev_t_ge_2.90": f.dev_t >= 2.90, "T2_pos": (f.t2 or -1) > 0, "CHECK_pos": (f.check or -1) > 0,
                "T2CHECK_t_ge_1.5": (f.oos_t or 0) >= 1.5,
                "wo_best_pos_share_lt_50": (r["ALL"]["wo_best"] or -1) > 0 and (r["ALL"]["best_share"] or 1) < 0.5,
                "control_gt_p95": ctrl["actual"] > ctrl["ctrl_p95"]}
        yrs = g.groupby("year").r_livel.agg(["size", "mean"]).round(3)
        reg = {f"above50={a}": st(x.r_livel, x.date) for a, x in g.groupby("above50")}
        reg.update({f"vol={a}": st(x.r_livel, x.date) for a, x in g.groupby("vol")})
        h2[f.config] = dict(finalist=fin_is, stats=r, control=ctrl, bars=bars, passed=fin_is and all(bars.values()),
                            years=yrs.reset_index().to_dict("records"), regimes=reg)
    res["H2"] = h2
    # ---- live parity (LATE data 2026-11-05..11-25, the dates the live setups traded)
    late = Path(late_dir)
    par = []
    for sig, trd in qo_sim.PAIRS.items():
        I = pd.read_parquet(late / f"{sig}_2026_2026.parquet"); T = pd.read_parquet(late / f"{trd}_2026_2026.parquet")
        for d, gi in I.groupby(I.index.date):
            gt = T[T.index.date == d]
            for r in qo_sim.day_trades(gi, gt, sig, trd):
                if (r["sig"], r["trd"], r["X"], r["rule"], r["exit"]) in H1:
                    par.append(dict(date=r["date"], setup=H1NAME[(r["sig"], r["trd"], r["X"], r["rule"], r["exit"])],
                                    entry=round(r["entry"], 2), gross=round(r["gross"], 3), stop_pct=round(r["stop_pct"], 2)))
    res["late_parity"] = par
    json.dump(res, open(HERE / "results.json", "w"), indent=1, default=str)
    # brief print
    for n, h in h1.items():
        s = h["stats"]
        print(n, {k: s[k].get("mean") for k in ("EARLY", "T2", "FIT", "CHECK")}, "ALL", s["ALL"], "lr8", s["ALL_lr8"].get("mean"),
              "tight", s["ALL_tight"].get("mean"), "gross", s["ALL_gross"].get("mean"))
        print("   ctrl", h["control"], "bars", h["bars"])
    print(tab.head(12).to_string())
    print("H2", {k: (v["finalist"], v["passed"], v["bars"]) for k, v in h2.items()})
    print("parity", par)
    print("n_configs", res["n_configs"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
