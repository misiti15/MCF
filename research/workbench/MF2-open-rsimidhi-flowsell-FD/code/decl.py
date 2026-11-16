# MF2-FD one-part tweaks over every part P2..P26 + new layers. Declared 2026-11-16 ~19:55 ET after the live (141 trades) and
# replay (parent without cost filter, 275 trades) component analysis, BEFORE any 2-year score. R = parent stop distance (0.125 ATR).
from sim_mf2 import BASE
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "V01 ADV >= $150M (P2)": D(adv=150e6),
 "V02 price >= $10 (P3)": D(minpx=10.0),
 "V03 window start 09:50->10:15 (P6/P7)": D(w=(1015, 1500)),
 "V04 window start 09:50->11:00 (P6/P7)": D(w=(1100, 1500)),
 "V05 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V06 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V07 refire off (P8)": D(refire=False),
 "V08 refire cooldown 1->3 (P8)": D(cd=3),
 "V09 heat in [-40,-30] (P9 floor)": D(heatmin=-40.0),
 "V10 heat <= -35 (P9)": D(heat=-35.0),
 "V11 RSI(14) 55-62 (P10 top)": D(rsihi=62.0),
 "V12 RSI(14) 57-65 (P10 bottom)": D(rsilo=57.0),
 "V13 buyPressure in [-0.5,-0.25) (P11 floor)": D(bpmin=-0.5),
 "V14 buyPressure < -0.30 (P11)": D(bp=-0.30),
 "V15 lots per symbol 3->1 (P14, tool)": D(symcap=1),
 "V16 cost filter 0.15->0.10 (P17)": D(acct_costr=0.10),
 "V17 cost filter off (P17, account-level)": D(acct_costr=None),
 "V18 1R 0.25->0.30 ATR (P20)": D(rf=0.30),
 "V19 stop 0.5R->0.75R (P23)": D(dn=0.75),
 "V20 geom t1s1: stop 0.5R->1R (P23)": D(dn=1.0),
 "V21 geom t05s05: target 1R->0.5R (P24)": D(up=0.5),
 "V22 geom holdtr: stop 1R, no target, trail 1R after +1R (P23/P24)": D(dn=1.0, up=None, trail=(1.0, 1.0)),
 "V23 trail 0.5R after +0.75R (P23 move)": D(trail=(0.5, 0.75)),
 "V24 gate: skip SPY > +0.30% since 09:50 (new)": D(spy950=0.30),
 "V25 gate: skip SPY above 09:30-09:50 high (new)": D(spyrng=1),
 "V26 skip rising 20-SMA slope > +0.05%/bar (new)": D(slopemax=0.05),
 "V27 skip gap-ups > +2% (new)": D(gapmax=2.0),
 "V28 skip > 1% below VWAP (new)": D(vwmin=-1.0),
 "V29 skip ATR% (5-min) > 0.8 (new)": D(atrpmax=0.8),
}
# Round 2 (declared ~20:55 ET after ROUND1, before any combo score). Passed both tests: V01 ADV $150M (2-year only - the replay
# cannot test ADV), V11 RSI <= 62, V16 cost/R <= 0.10, V26 skip rising 20-SMA, V27 skip gap-ups > +2%, plus near-neutral V09 /
# V13 / V06 / V04. Failed: refire off / cd 3, heat <= -35, RSI >= 57, bp < -0.30, 1 lot per symbol, cost filter off, 1R 0.30,
# stop 0.75R / 1R, target 0.5R, holdtr, trail, both SPY gates (V24/V25: the after-09:50 SPY gate that helped RW5 does NOT help
# MF2 in the replay), VWAP-distance, ATR% cap.
SG = dict(slopemax=0.05, gapmax=2.0)
ROUND2 = {
 "PARENT": BASE,
 "S1 slope <= +0.10": D(slopemax=0.10),
 "S2 slope <= +0.02": D(slopemax=0.02),
 "S3 gap <= +1%": D(gapmax=1.0),
 "S4 gap <= +3%": D(gapmax=3.0),
 "S5 ADV >= $200M": D(adv=200e6),
 "S6 RSI(14) 55-60": D(rsihi=60.0),
 "C1 slope<=0.05 + gap<=2%": D(**SG),
 "C2 C1 + ADV>=$150M": D(**SG, adv=150e6),
 "C3 C1 + RSI<=62": D(**SG, rsihi=62.0),
 "C4 C1 + ADV150 + RSI<=62": D(**SG, adv=150e6, rsihi=62.0),
 "C5 C4 + cost/R<=0.10": D(**SG, adv=150e6, rsihi=62.0, acct_costr=0.10),
 "C6 C2 + cost/R<=0.10": D(**SG, adv=150e6, acct_costr=0.10),
 "C7 C4 + heat>=-40": D(**SG, adv=150e6, rsihi=62.0, heatmin=-40.0),
 "C8 C4 + bp>=-0.5": D(**SG, adv=150e6, rsihi=62.0, bpmin=-0.5),
 "C9 C4 + end 13:00": D(**SG, adv=150e6, rsihi=62.0, w=(950, 1300)),
}
# Round 3 (declared ~21:10 ET after ROUND2: C4 = skip rising 20-SMA + skip gap-ups > 2% + ADV $150M + RSI <= 62 positive in every
# test and split; C7 (heat floor) / C8 (bp floor) / C9 (end 13:00) add a little on top).
C4 = dict(SG, adv=150e6, rsihi=62.0)
ROUND3 = {
 "PARENT": BASE,
 "C4 C1 + ADV150 + RSI<=62": D(**C4),
 "D1 C4 + heat>=-40 + bp>=-0.5": D(**C4, heatmin=-40.0, bpmin=-0.5),
 "D2 C4 with slope<=0.02": D(**dict(C4, slopemax=0.02)),
 "D3 C4 + heat>=-40 + end 14:00": D(**C4, heatmin=-40.0, w=(950, 1400)),
 "D4 C4 with gap<=1%": D(**dict(C4, gapmax=1.0)),
}
