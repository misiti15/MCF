"""Deploy-time duplicate check for BEG-ORB / BEG-GNG (2026-11-20). Inputs (trade lists, day tables) are session-scratchpad
files, not in git; output overlap.json is. Educational only - not financial advice.
BEG-01 stopOR / BEG-03 base: 70% symbol-day duplicate test vs MCF's orb, orb20_a, gap_and_go, gap_continuation
(rules re-implemented on the same T1 cache, fit + check) and vs the live top-10 books (top10w). Research only."""
import json
from pathlib import Path
import numpy as np, pandas as pd
S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
R = pd.read_parquet(S / "begdup/r20.parquet")
D = pd.read_parquet(S / "beg01w/days_t1.parquet")[["symbol", "date", "atr", "adv20", "gap", "dc"]]
R = R.merge(D, on=["symbol", "date"], how="left").sort_values(["symbol", "date"])
R["prev_close"] = R.groupby("symbol").dc.shift(1)
def rv(col):
    out = np.full(len(R), np.nan)
    for _, idx in R.groupby("symbol").indices.items():
        v = R[col].to_numpy(float)[idx]; d = pd.to_datetime(R.date.to_numpy()[idx]).values
        for j in range(len(idx)):
            lo = np.searchsorted(d, d[j] - np.timedelta64(30, "D")); j0 = max(lo, j - 14)
            if j - j0 >= 5:
                m = v[j0:j].mean(); out[idx[j]] = v[j] / m if m > 0 else np.nan
    return out
R["rvol20"], R["rvol5"] = rv("v20"), rv("v5")
uni = (R.prev_close >= 5) & R.atr.notna()
for c, rk in (("rvol20", "rank20"), ("rvol5", "rank5")):
    R[rk] = np.nan
    R.loc[uni & R[c].notna(), rk] = R[uni & R[c].notna()].groupby("date")[c].rank(ascending=False, method="first")
T1 = R[((R.date >= "2024-10-01") & (R.date <= "2024-10-31")) | ((R.date >= "2025-03-01") & (R.date <= "2026-11-04"))]
liq = (T1.prev_close >= 5) & (T1.atr >= 0.5) & ((T1.adv20 / T1.prev_close) >= 1e6)
# orb20_a (live On Deck; WB3 in Testing C is top 10 + price >= 20): OR20, dir 09:30 open -> 09:49 close, VWAP agree, fill to 11:29
sd = np.sign(T1.c949 - T1.o930)
vwok = sd * (T1.c949 - T1.vw949) > 0
fill20 = np.where(sd > 0, T1.h_1129 >= T1.hi20 + 0.01, T1.l_1129 <= T1.lo20 - 0.01)
orb20a = T1[liq & (T1.rank20 <= 20) & (T1.rvol20 >= 1.5) & (sd != 0) & vwok & fill20].assign(side=sd)
orb20wb3 = T1[liq & (T1.rank20 <= 10) & (T1.prev_close >= 20) & (T1.rvol20 >= 1.5) & (sd != 0) & vwok & fill20].assign(side=sd)
# orb (default, disabled everywhere): OR5, top 20 by opening (5-min) rvol, rvol >= 1, ATR >= 0.5; fills approximated 09:35-11:29
s5 = np.sign(T1.c934 - T1.o930)
hmax = np.fmax(T1.h5_1034, T1.h_1129); lmin = T1.l_1129   # low 09:35-09:49 not kept: short fills slightly undercounted
fill5 = np.where(s5 > 0, hmax >= T1.hi5, lmin <= T1.lo5)
orb = T1[(T1.rank5 <= 20) & (T1.atr >= 0.5) & (T1.rvol5 >= 1.0) & (s5 != 0) & fill5].assign(side=s5)
# gap_and_go (default, disabled everywhere): gap >= 4%, OR5, rvol(09:34) >= 2, close >= VWAP at 09:34, buy-stop OR5 high, 60 bars
gng = T1[(T1.gap >= 4) & (T1.rvol5 >= 2) & (T1.c934 >= T1.vw934) & (T1.h5_1034 >= T1.hi5)].assign(side=1)
# gap_continuation (library, disabled everywhere): |gap| >= max(3, ATR%), rvol20 >= 3, hold above VWAP/open/mid; R20 extreme to 10:59
gs = np.sign(T1.gap); mid = (T1.hi20 + T1.lo20) / 2
gc_ok = (T1.gap.abs() >= np.maximum(3, 100 * T1.atr / T1.prev_close)) & (T1.rvol20 >= 3) & liq & (T1.prev_close <= 250) \
    & (gs * (T1.c949 - T1.vw949) > 0) & (gs * (T1.c949 - T1.o930) > 0) & (gs * (T1.c949 - mid) > 0)
fillg = np.where(gs > 0, T1.h_1059 >= T1.hi20 + 0.01, T1.l_1059 <= T1.lo20 - 0.01)
gcont = T1[gc_ok & fillg].assign(side=gs)
others = {"orb20_a (live On Deck)": orb20a, "orb20_a-WB3 (live Testing C)": orb20wb3, "orb (default, off)": orb,
          "gap_and_go (default, off)": gng, "gap_continuation (library, off)": gcont}
live = pd.read_parquet(S / "top10w/booked_trades.parquet"); live = live[(live.test == "T1") & (live.half != "none")]
for s, g in live.groupby("setup"):
    others[f"{s} (live top-10 book)"] = g
b1 = pd.concat([pd.read_parquet(S / f"beg01w/booked_t1_stopOR_{h}.parquet") for h in ("fit", "check")])
b3 = pd.read_parquet(S / "beg03w/bk_base_all.parquet"); b3 = b3[b3.test.str.lower() == "t1"]
b3 = b3[b3.date >= "2024-10-01"]
def keys(df, side=False):
    return set(zip(df.symbol, df.date, df.side.astype(int))) if side else set(zip(df.symbol, df.date))
out = {}
for nm, B in (("BEG-01 stopOR", b1), ("BEG-03 base", b3)):
    kb, kbs = keys(B), keys(B, True)
    rows = {}
    for o, O in others.items():
        ko, kos = keys(O), keys(O, True)
        rows[o] = {"n_other": len(ko), "share_of_BEG_symdays": round(len(kb & ko) / len(kb), 3),
                   "share_same_side": round(len(kbs & kos) / len(kbs), 3),
                   "share_of_other": round(len(kb & ko) / len(ko), 3) if ko else None}
    out[nm] = {"n": len(kb), "overlap": dict(sorted(rows.items(), key=lambda x: -x[1]["share_of_BEG_symdays"]))}
json.dump(out, open(S / "begdup/overlap.json", "w"), indent=1)
print(json.dumps(out, indent=1))
