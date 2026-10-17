"""Shared pre-declared search space for arena-pm-both (see PLAN.md). Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SCREEN = HERE.parent / "arena" / "single_screen.parquet"
WIN_SCREEN = "1400-1530"
WINDOWS = [(1400, 1530), (1400, 1430), (1430, 1530)]
GEOMS = ["t05s1", "t1s1", "t1s05"]
SIDES = ["long", "short"]
FILTER_INDS = ["gap_atr", "atr_d_pct", "prev_range_atr", "day_vs_prev_range", "rvol_day", "from_pc_atr", "dist_pdh_atr",
               "dist_pdl_atr", "rv12", "day_range_atr", "vwap_atr", "fromOpen_atr", "or_high_dist_atr", "buyPressure",
               "emaDiff", "di_diff7", "sma50_dist_pct", "adx7", "day_pos", "vwap_side_bars"]
CTX_INDS = ["spy_fromOpen", "qqq_fromOpen", "breadth_vwap", "spy_ret3", "rs_spy"]


def cond_from_bin(r):
    if r.op == "between":
        return (r.indicator, "between", (float(r.lo), float(r.hi)))
    return (r.indicator, r.op, float(r.lo))


def four_bins(L, ind):
    q = L[L.indicator == ind].set_index("bin")
    med = float(q.loc["d05", "hi"])
    return [(ind, "<=", float(q.loc["le_q20", "lo"])), (ind, "<=", med), (ind, ">=", med),
            (ind, ">=", float(q.loc["ge_q80", "lo"]))]


def pick_conditions(side):
    s = pd.read_parquet(SCREEN)
    w = s[(s.window == WIN_SCREEN) & (s.geom == "t1s1")]
    other = "short" if side == "long" else "long"
    S, O = w[w.side == side], w[w.side == other]
    k = ["indicator", "bin"]
    m = S.merge(O[k + ["excess"]].rename(columns={"excess": "ex_o"}), on=k)
    m["dir"] = (m.excess - m.ex_o) / 2
    m = m[(m.n >= 2000) & m.live]
    a = m.sort_values("excess", ascending=False).drop_duplicates("indicator").head(20)
    b = m[~m.indicator.isin(a.indicator)].sort_values("dir", ascending=False).drop_duplicates("indicator").head(10)
    trig = [(cond_from_bin(r), "excess" if i < 20 else "dir", float(r.excess), float(r.dir))
            for i, r in enumerate(pd.concat([a, b]).itertuples())]
    filt = [c for ind in FILTER_INDS for c in four_bins(S, ind)]
    ctx = [c for ind in CTX_INDS for c in four_bins(S, ind)]
    return trig, filt, ctx


def needed_names():
    out = set()
    for sd in SIDES:
        trig, filt, ctx = pick_conditions(sd)
        out |= {t[0][0] for t in trig} | {f[0] for f in filt} | {c[0] for c in ctx}
    return sorted(out)
