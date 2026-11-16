# RW5 one-part tweaks, every part P2..P26 (declared 2026-11-16 ~13:20 ET after the live + replay component analysis, before any 2-year score).
from sim2 import BASE
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "V01 ADV >= $150M (P2)": D(adv=150e6),
 "V02 price >= $10 (P3)": D(minpx=10.0),
 "V03 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V04 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V05 window start 09:50->10:15 (P6/P7)": D(w=(1015, 1500)),
 "V06 refire on, cooldown 6 (P8)": D(refire=True, cd=6),
 "V07 heat <= -35 (P9)": D(heat=-35.0),
 "V08 heat in [-40,-30] (P9 band)": D(heatmin=None) if False else D(fomin=None),
 "V09 buyPressure < -0.20 (P10)": D(bp=-0.20),
 "V10 RSI(5) > 85 (P11)": D(rsi5=85.0),
 "V11 RSI(5) <= 97 (P11 cap)": D(rsimax=97.0),
 "V12 gap < -0.5% (P12)": D(gap=-0.5),
 "V13 gap < -1.0% (P12)": D(gap=-1.0),
 "V14 latch -2R -> -4R (P16, tool)": D(latch=-4.0),
 "V15 1R 0.25 -> 0.30 ATR (P20)": D(rf=0.30),
 "V16 cost/R <= 0.15 (P20/intake)": D(costr=0.15),
 "V17 stop 1.0 -> 1.25R (P23)": D(dn=1.25),
 "V18 target 1.0 -> 0.8R (P24)": D(up=0.8),
 "V19 BE stop after +0.5R (P23 move)": D(be_at=0.5),
 "V20 max hold 90 min (P26)": D(maxhold=90),
 "V21 max hold 120 min (P26)": D(maxhold=120),
 "V22 flat 15:55 -> 15:00 (P26)": D(flat=1500),
 "V23 gate: skip SPY > +0.30% since 09:50 (new)": D(spy950=0.30),
 "V24 gate: skip SPY above 09:30-09:50 high (new)": D(spyrng=1),
}
del ROUND1["V08 heat in [-40,-30] (P9 band)"]
# Round 2 (declared after ROUND1, before any combo score): passing parts in both tests = SPY gate (V23/V24), cost/R (V16),
# start 10:15 (V05), price >= $10 (V02), bp < -0.20 (V09), RSI(5) > 85 (V10), end 13:00/14:00 (V03/V04), flat 15:00 (V22, no
# per-setup knob live -> tested, not deployable). Max hold / BE / stop 1.25 / target 0.8 / 1R 0.30 / heat -35 / latch -4 / ADV 150M failed.
G = dict(spy950=0.30)
ROUND2 = {
 "PARENT": BASE,
 "S1 skip SPY > +0.20% since 09:50": D(spy950=0.20),
 "S2 skip SPY > +0.45% since 09:50": D(spy950=0.45),
 "C1 SPY gate + cost/R<=0.15": D(**G, costr=0.15),
 "C2 C1 + start 10:15": D(**G, costr=0.15, w=(1015, 1500)),
 "C3 C1 + RSI(5)>85": D(**G, costr=0.15, rsi5=85.0),
 "C4 C1 + bp<-0.20": D(**G, costr=0.15, bp=-0.20),
 "C5 C2 + price>=$10": D(**G, costr=0.15, w=(1015, 1500), minpx=10.0),
 "C6 C1 + end 14:00": D(**G, costr=0.15, w=(950, 1400)),
 "C7 C2 + end 14:00": D(**G, costr=0.15, w=(1015, 1400)),
 "C8 spyrng gate + cost/R<=0.15 + start 10:15": D(spyrng=1, costr=0.15, w=(1015, 1500)),
 "C9 C2 + flat 15:00 (no live knob)": D(**G, costr=0.15, w=(1015, 1500), flat=1500),
 "C10 SPY gate + start 10:15": D(**G, w=(1015, 1500)),
}
# Round 3 (declared after ROUND2: C2 = SPY gate 0.30 + cost/R 0.15 + start 10:15 positive in both tests; S1 gate 0.20 slightly stronger alone).
ROUND3 = {
 "PARENT": BASE, "C2 C1 + start 10:15": D(**G, costr=0.15, w=(1015, 1500)),
 "D1 C2 with SPY gate 0.20": D(spy950=0.20, costr=0.15, w=(1015, 1500)),
 "D2 C2 with cost/R<=0.10": D(**G, costr=0.10, w=(1015, 1500)),
 "D3 C2 + RSI(5)>85": D(**G, costr=0.15, w=(1015, 1500), rsi5=85.0),
}
