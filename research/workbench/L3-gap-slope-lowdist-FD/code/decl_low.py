# Pre-declared tweaks for L3-gap-slope-lowdist-FD (declared 2026-11-16 ~18:30 ET after the live + parent-replay component
# analysis, before any variant score). One part each, plus the sibling's WB4 parts (owner brief: test whether they help here).
from sim_low import PARENT as P
D = lambda **k: dict(P, **k)
ROUND1 = {
 "PARENT": P,
 "V01 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V02 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V03 window start 09:50->10:05 (P6/P7)": D(w=(1005, 1500)),
 "V04 gap <=-2.66->-3.2 (P4/P9)": D(gap=-3.2),
 "V05 gap not deeper than -10% (P9 layer)": D(gapmin=-10.0),
 "V06 dist_lod hi 0.977->0.95 (P12)": D(hi=0.95),
 "V07 dist_lod lo 0.782->0.82 (P11)": D(lo=0.82),
 "V08 slope >0.372->>0.45 (P10)": D(slope=0.45),
 "V09 slope <= 1.0 (P10 layer)": D(slopemax=1.0),
 "V10 fromOpen >= 0 (new layer)": D(fomin=0.0),
 "V11 fromOpen >= 3 (new layer)": D(fomin=3.0),
 "V12 rsi5 >= 50 (new layer)": D(rsi5min=50.0),
 "V13 1R >= 1.0% of price (P20 layer)": D(rpct=1.0),
 "V14 max hold 75 min (P26)": D(maxhold=75),
 "V15 max hold 90 min (P26)": D(maxhold=90),
 "V16 max hold 120 min (P26)": D(maxhold=120),
 "V17 target 1R->0.5R t05s1 (P24)": D(up=0.5),
 "V18 stop 1R->1.25R (P23; info, no geom)": D(dn=1.25),
 "V19 BE stop after +0.5R (P23 hook)": D(be_at=0.5),
 "V20 refire on, cooldown 1 (P8)": D(refire=True, cd=1),
 "V21 open-lot cap 150->30 (P13)": D(cap=30),
 "V22 cost filter 0.15->0.10R (P17)": D(costf=0.10),
 "V23 price floor $5->$10 (P2)": D(minpx=10.0),
 "V24 skip SPY>+0.30% since 09:50 (gate)": D(spy950=0.30),
 "V25 VWAP dist >= 1% (new layer)": D(vwmin=1.0),
 "V26 sibling WB4 parts: end 13:00 + gap -3.2 + hold 75": D(w=(950, 1300), gap=-3.2, maxhold=75),
 "V27 sibling parts w/o gap: end 13:00 + hold 75": D(w=(950, 1300), maxhold=75),
}
# Round 2 (declared after ROUND1, before its scores): max hold 75 is the only part better in both tests on avg R AND w/o best
# day; rsi5 >= 50 / VWAP >= 1% / cap 30 / skip SPY>+0.30 cut the 2-year tail (2025-04-07: 308 trades, -164R) with replay ~flat.
H = lambda **k: D(maxhold=75, **k)
ROUND2 = {
 "PARENT": P, "V14 max hold 75 min (P26)": D(maxhold=75),
 "R01 hold 75 + rsi5>=50": H(rsi5min=50.0),
 "R02 hold 75 + VWAP>=1%": H(vwmin=1.0),
 "R03 hold 75 + rsi5>=50 + VWAP>=1%": H(rsi5min=50.0, vwmin=1.0),
 "R04 hold 75 + cap 30": H(cap=30),
 "R05 hold 75 + rsi5>=50 + cap 30": H(rsi5min=50.0, cap=30),
 "R06 hold 75 + rsi5>=50 + gap>=-10": H(rsi5min=50.0, gapmin=-10.0),
 "R07 hold 75 + target 0.5R": H(up=0.5),
 "R08 hold 75 + rsi5>=50 + dist lo 0.82": H(rsi5min=50.0, lo=0.82),
 "R09 hold 75 + rsi5>=50 + skip SPY>+0.30": H(rsi5min=50.0, spy950=0.30),
 "R10 hold 60 + rsi5>=50": D(maxhold=60, rsi5min=50.0),
 "R11 hold 90 + rsi5>=50": D(maxhold=90, rsi5min=50.0),
 "R12 hold 75 + rsi5>=50 + VWAP>=1% + cap 30": H(rsi5min=50.0, vwmin=1.0, cap=30),
}
# Round 3 (declared after ROUND2 + its component split: R08 = hold 75 + rsi5>=50 + dist lo 0.82 is the only combo better than
# the parent in every 2-year split and ex-April-2025; check its neighbours and the remaining weak parts (late window, gap tail).
R8 = lambda **k: D(**dict(dict(maxhold=75, rsi5min=50.0, lo=0.82), **k))
ROUND3 = {
 "PARENT": P, "R08 hold 75 + rsi5>=50 + dist lo 0.82": R8(),
 "S1 R08 + window end 14:00": R8(w=(950, 1400)),
 "S2 R08 + window end 13:00": R8(w=(950, 1300)),
 "S3 R08 + gap>=-10": R8(gapmin=-10.0),
 "S4 R08 with hold 60": R8(maxhold=60),
 "S5 R08 with hold 90": R8(maxhold=90),
 "S6 R08 with dist lo 0.85": R8(lo=0.85),
 "S7 R08 with rsi5>=40": R8(rsi5min=40.0),
}
# Round 4 (declared after ROUND3 and the per-day replay check: R08's hold 75 turns 10-15 from -19.7 to +10.3R but halves 11-12
# (+38.5 -> +19.7R) and is worse on 9 of 18 replay days; does the entry pair work without the clock, or with a softer clock?)
Q = lambda **k: D(**dict(dict(rsi5min=50.0, lo=0.82), **k))
ROUND4 = {
 "PARENT": P, "R08 hold 75 + rsi5>=50 + dist lo 0.82": R8(),
 "Q1 rsi5>=50 + dist lo 0.82 (no clock)": Q(),
 "Q2 Q1 + hold 120": Q(maxhold=120),
 "Q3 Q1 + 75 min only if best < 0.5R": Q(maxhold=75, ts_r=0.5),
 "Q4 Q1 + 90 min only if best < 0.75R": Q(maxhold=90, ts_r=0.75),
}
# Book check (declared after ROUND4: the target testing accounts cap a setup at 30-50 open lots, not On Deck's 150).
BOOK = {"PARENT": P, "R08 hold 75 + rsi5>=50 + dist lo 0.82": R8(),
        "B1 parent at cap 30": D(cap=30), "B2 R08 at cap 30": R8(cap=30), "B3 parent at cap 50": D(cap=50), "B4 R08 at cap 50": R8(cap=50)}
