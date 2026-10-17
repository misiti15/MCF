"""Shared pre-declared search space for arena-mid-short (see PLAN.md). Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SCREEN = HERE.parent / "arena" / "single_screen.parquet"
WIN_SCREEN = "1100-1400"
WINDOWS = [(1100, 1400), (1100, 1230), (1230, 1400)]
GEOMS = ["t05s1", "t1s1", "t1s05"]
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


def pick_conditions():
    s = pd.read_parquet(SCREEN)
    w = s[(s.window == WIN_SCREEN) & (s.geom == "t1s1")]
    L, S = w[w.side == "short"], w[w.side == "long"]   # L = searched side (SHORT), S = other side
    k = ["indicator", "bin"]
    m = L.merge(S[k + ["excess"]].rename(columns={"excess": "ex_s"}), on=k)
    m["dir"] = (m.excess - m.ex_s) / 2          # (excess_short - excess_long)/2
    m = m[(m.n >= 2000) & m.live]
    a = m.sort_values("excess", ascending=False).drop_duplicates("indicator").head(20)
    b = m[~m.indicator.isin(a.indicator)].sort_values("dir", ascending=False).drop_duplicates("indicator").head(10)
    trig = [(cond_from_bin(r), "excess" if i < 20 else "dir", float(r.excess), float(r.dir))
            for i, r in enumerate(pd.concat([a, b]).itertuples())]
    filt = [c for ind in FILTER_INDS for c in four_bins(L, ind)]
    ctx = [c for ind in CTX_INDS for c in four_bins(L, ind)]
    return trig, filt, ctx


def needed_names():
    trig, filt, ctx = pick_conditions()
    return sorted({t[0][0] for t in trig} | {f[0] for f in filt} | {c[0] for c in ctx})
