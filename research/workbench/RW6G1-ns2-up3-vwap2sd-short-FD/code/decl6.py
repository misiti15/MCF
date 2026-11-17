# RW6G1 one-part tweaks, every part P2..P26 (declared 2026-11-16 ~20:15 ET after the live + replay component analysis, before any 2-year score).
from sim3 import BASE, TESTBOOK
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "T0 parent, testing book": D(**TESTBOOK),
 "V01 ADV >= $150M (P2)": D(adv=150e6),
 "V02 price >= $10 (P3)": D(minpx=10.0),
 "V03 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V04 window start 09:50->11:00 (P6/P7)": D(w=(1100, 1500)),
 "V05 refire off (P8)": D(refire=False),
 "V06 refire cooldown 1->6 (P8)": D(cd=6),
 "V07 fromOpen > 3 -> > 4 (P10)": D(fo=4.0),
 "V08 fromOpen > 3 -> > 2.5 (P10)": D(fo=2.5),
 "V09 fromOpen <= 8 cap (P10)": D(fomax=8.0),
 "V10 RSI(14) >= 65 (P11)": D(rsi=65.0),
 "V11 RSI(14) >= 55 (P11)": D(rsi=55.0),
 "V12 band 2 SD -> 2.5 SD (P12)": D(k=2.5),
 "V13 band 2 SD -> 1.5 SD (P12)": D(k=1.5),
 "V14 band guard off (P12)": D(k=None),
 "V15 latch -2R off (P16, tool)": D(latch=-1e9),
 "V16 1R 0.25 -> 0.30 ATR (P20)": D(rf=0.30),
 "V17 cost/R <= 0.15 (P20/intake)": D(costr=0.15),
 "V18 stop 1.0 -> 1.25R (P23)": D(dn=1.25),
 "V19 target 1.0 -> 0.8R (P24)": D(up=0.8),
 "V20 target 1.0 -> 0.6R (P24)": D(up=0.6),
 "V21 BE stop after +0.5R (P23 move)": D(be_at=0.5),
 "V22 max hold 60 min (P26)": D(maxhold=60),
 "V23 max hold 120 min (P26)": D(maxhold=120),
 "V24 gate: skip SPY > +0.30% since 09:50 (new)": D(spy950=0.30),
 "V25 gate: skip SPY above 09:30-09:50 high (new)": D(spyrng=1),
 "V26 price >= VWAP at signal (new sensor)": D(vwmin=0.0),
 "V27 close >= VWAP + 0.5 SD at signal (new sensor)": D(z5min=0.5),
}
# Round 2 (declared ~21:20 ET after ROUND1 + the 2-year component analysis, before any Round-2 score). Passing one-part
# copies in both tests: start 11:00 (V04), close >= VWAP + 0.5 SD (V27), ADV >= $150M (V01), band guard off (V14), target
# 0.6R (V20), refire off (V05) / cooldown 6 (V06), fromOpen <= 8 (V09), price >= VWAP (V26), BE (V21), hold 120 (V23).
# 2-year component analysis: entries > 0.5 daily ATR below the high of day -0.17 / -0.66R; gap <= -2% -0.14R; volumeRatio < 0.8 -0.14R.
A = dict(w=(1100, 1500), z5min=0.5)
ROUND2 = {
 "PARENT": BASE,
 "S1 close within 0.5 ATR of HOD (new sensor)": D(hodmax=0.5),
 "S2 gap >= -2% (intake)": D(gapmin=-2.0),
 "S3 volumeRatio >= 0.8 (new sensor)": D(volmin=0.8),
 "C1 start 11:00 + z5 >= 0.5": D(**A),
 "C2 C1 + ADV >= $150M": D(**A, adv=150e6),
 "C3 C2 + HOD <= 0.5 ATR": D(**A, adv=150e6, hodmax=0.5),
 "C4 C3 + target 0.6R": D(**A, adv=150e6, hodmax=0.5, up=0.6),
 "C5 C2 + refire off": D(**A, adv=150e6, refire=False),
 "C6 C3 + band guard off": D(**A, adv=150e6, hodmax=0.5, k=None),
 "C7 C1 + HOD <= 0.5 ATR": D(**A, hodmax=0.5),
 "C8 C3 + gap >= -2%": D(**A, adv=150e6, hodmax=0.5, gapmin=-2.0),
 "C9 C3 + skip SPY > +0.30% since 09:50": D(**A, adv=150e6, hodmax=0.5, spy950=0.30),
 "C10 C3 + volumeRatio >= 0.8": D(**A, adv=150e6, hodmax=0.5, volmin=0.8),
 "C11 start 11:00 + ADV >= $150M + HOD <= 0.5 ATR (no z5)": D(w=(1100, 1500), adv=150e6, hodmax=0.5),
}
# Round 3 (declared ~21:45 ET after ROUND2: C2 = start 11:00 + close >= VWAP + 0.5 SD + ADV >= $150M best in both tests;
# 2-year gap > +5% consistently worst in parent and C2 (gap-and-go runners); the -2R latch hurts in 2y (V15 / T0), and the
# destination Testing book has none -> score the finalists in the testing book too (TB-*), paired against T0.)
C2 = dict(w=(1100, 1500), z5min=0.5, adv=150e6)
ROUND3 = {
 "PARENT": BASE,
 "C2 C1 + ADV >= $150M": D(**C2),
 "D1 C2 + gap <= +5%": D(**C2, gapmax=5.0),
 "D2 C2 + gap <= +2%": D(**C2, gapmax=2.0),
 "D3 C2 + max hold 120 min": D(**C2, maxhold=120),
 "D4 C2 + latch off (tool)": D(**C2, latch=-1e9),
 "T0 parent, testing book": D(**TESTBOOK),
 "TB-C1 C1 in testing book": D(**TESTBOOK, w=(1100, 1500), z5min=0.5),
 "TB-C2 C2 in testing book": D(**TESTBOOK, **C2),
 "TB-D1 D1 in testing book": D(**TESTBOOK, **C2, gapmax=5.0),
 "TB-D2 D2 in testing book": D(**TESTBOOK, **C2, gapmax=2.0),
}
# Round 4 (declared ~22:30 ET after ROUND3: TB-D2 misses the worst-day rule vs T0 only through 2025-04-09 (tariff-pause rally,
# SPY ~+9% intraday). Extreme-rally guard measured after 09:50 (owner rule), loose enough to keep 11-09-type days.)
ROUND4 = {
 "PARENT": BASE,
 "T0 parent, testing book": D(**TESTBOOK),
 "E1 D2 + skip SPY > +1.5% since 09:50": D(**C2, gapmax=2.0, spy950=1.5),
 "TB-E1 E1 in testing book": D(**TESTBOOK, **C2, gapmax=2.0, spy950=1.5),
}
