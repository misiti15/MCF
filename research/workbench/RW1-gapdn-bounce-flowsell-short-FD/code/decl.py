# RW1-FD Mechanic: pre-declared one-part tweaks (declared 2026-11-16 ~15:00 ET, after the live component breakdown,
# BEFORE any replay or 2-year score was read). Every part P1..P27 inspected; one tweak per part with a symptom or a knob,
# plus the three parts that passed for siblings RW3 / RW5 (SPY-since-09:50 gate, cost / ATR intake, later start).
# BASE = the parent in its own book (On Deck: no per-setup latch, 150 lots, cost filter CF 0.15, <= 3 lots per symbol).
from sim_rw1 import BASE
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "V01 ADV $95M -> $150M (P2)": D(minadv=150e6),
 "V02 price >= $10 (P3)": D(minpx=10.0),
 "V03 1R >= 0.40% of price (P1/P21 intake, RW3)": D(rpct=0.40),
 "V04 cost filter 0.15 -> 0.10R (P18, RW5 intake)": D(cf=0.10),
 "V05 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V06 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V07 start 09:50->10:30 (P7, RW3)": D(w=(1030, 1500)),
 "V08 start 09:50->11:00 (P7)": D(w=(1100, 1500)),
 "V09 refire on, cooldown 6 (P8)": D(refire=True, cd=6),
 "V10 heat <= -25 (P9)": D(heat=-25.0),
 "V11 heat <= -15 (P9 looser)": D(heat=-15.0),
 "V12 buyPressure < -0.40 (P10)": D(bp=-0.40),
 "V13 RSI(14) 55-60 (P11 hi)": D(rsihi=60.0),
 "V14 RSI(14) 58-65 (P11 lo)": D(rsilo=58.0),
 "V15 gap <= -0.5% (P12)": D(gapmax=-0.5),
 "V16 gap <= -1.0% (P12)": D(gapmax=-1.0),
 "V17 lots per symbol 3 -> 1 (P15)": D(symcap=1),
 "V18 per-setup latch -2R (P16)": D(latch=-2.0),
 "V19 stop 1.0 -> 1.25R (P24)": D(dn=1.25),
 "V20 target 1.0 -> 0.8R (P25)": D(up=0.8),
 "V21 BE stop after +0.5R (P24 move)": D(be_at=0.5),
 "V22 max hold 120 min (P27)": D(maxhold=120),
 "V23 flat 15:55 -> 15:00 (P27, no live knob)": D(flat=1500),
 "V24 gate: skip SPY > +0.20% since 09:50 (new, RW3/RW5)": D(spy950=0.20),
 "V25 gate: skip SPY > +0.30% since 09:50 (new)": D(spy950=0.30),
 "V26 price at/below VWAP (new sensor)": D(vwmax=0.0),
}
# Round 2 (declared after ROUND1, before any combo score). Improved BOTH tests alone: V13 RSI(14) 55-60, V16 gap <= -1%,
# V10 heat <= -25, V03 1R >= 0.40% of price, V05 end 13:00. Sibling parts: SPY-since-09:50 gate (V24 0.20 FAILS alone: replay
# -0.008 vs +0.013, w/o best day -0.103; V25 0.30 fails on replay w/o best day) and start 10:30 (V07 ~neutral) are re-checked
# inside the best combo so they get a fair test there; cost filter 0.10 (V04) failed on replay avg R.
R13 = dict(rsihi=60.0)
ROUND2 = {
 "PARENT": BASE,
 "C1 RSI 55-60 + 1R>=0.40%": D(**R13, rpct=0.40),
 "C2 RSI 55-60 + gap<=-1%": D(**R13, gapmax=-1.0),
 "C3 C1 + gap<=-1%": D(**R13, rpct=0.40, gapmax=-1.0),
 "C4 RSI 55-60 + heat<=-25": D(**R13, heat=-25.0),
 "C5 C1 + end 13:00": D(**R13, rpct=0.40, w=(950, 1300)),
 "C6 C3 + end 13:00": D(**R13, rpct=0.40, gapmax=-1.0, w=(950, 1300)),
 "C7 C1 + SPY gate 0.20 (sibling)": D(**R13, rpct=0.40, spy950=0.20),
 "C8 C1 + start 10:30 (sibling)": D(**R13, rpct=0.40, w=(1030, 1500)),
 "C9 C1 + SPY gate 0.20 + start 10:30 (sibling pack)": D(**R13, rpct=0.40, spy950=0.20, w=(1030, 1500)),
 "C10 C3 + heat<=-25": D(**R13, rpct=0.40, gapmax=-1.0, heat=-25.0),
 "C11 C1 + end 14:00": D(**R13, rpct=0.40, w=(950, 1400)),
 "S1 RSI 55-58 + 1R>=0.40%": D(rsihi=58.0, rpct=0.40),
 "S2 RSI 55-61 + 1R>=0.40%": D(rsihi=61.0, rpct=0.40),
 "S3 C1 + gap<=-0.75%": D(**R13, rpct=0.40, gapmax=-0.75),
}
# Round 3 (declared after ROUND2): C5 (RSI 55-60 + 1R >= 0.40% + end 13:00) is better than the parent in every 2-year split
# and positive in both tests; C6 (C5 + gap <= -1%) scores higher but its TRAIN split is worse than the parent (-0.070 vs -0.044).
# Checks: gap depth on top of C5, neighbouring thresholds (robustness), and attribution (drop one part at a time).
C5 = D(**R13, rpct=0.40, w=(950, 1300))
E = lambda **k: dict(C5, **k)
ROUND3 = {
 "PARENT": BASE, "C5 C1 + end 13:00": C5,
 "D1 C5 + gap<=-0.5%": E(gapmax=-0.5),
 "D2 C5 + gap<=-0.75%": E(gapmax=-0.75),
 "D3 C5 with end 13:30": E(w=(950, 1330)),
 "D4 C5 with RSI 55-61": E(rsihi=61.0),
 "D5 C5 with 1R>=0.35%": E(rpct=0.35),
 "D6 C5 without 1R floor (RSI 55-60 + end 13:00)": D(**R13, w=(950, 1300)),
 "D7 C5 without RSI band (1R>=0.40% + end 13:00)": D(rpct=0.40, w=(950, 1300)),
 "D8 C5 + SPY gate 0.20 (sibling)": E(spy950=0.20),
}
