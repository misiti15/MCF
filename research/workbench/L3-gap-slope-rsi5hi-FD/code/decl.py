# Pre-declared one-part tweaks for L3-gap-slope-rsi5hi-FD (declared 2026-11-16 ~18:20 ET after the live component analysis
# and the sibling's results, BEFORE any score). Each changes ONE part; combos are declared only after round 1.
from sim import PARENT
D = lambda **k: dict(PARENT, **k)
ROUND1 = {
 "PARENT": PARENT,
 "V01 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V02 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V03 window start 09:50->10:30 (P6/P7)": D(w=(1030, 1500)),
 "V04 max hold 75 min (P25)": D(maxhold=75),
 "V05 max hold 60 min (P25)": D(maxhold=60),
 "V06 max hold 90 min (P25)": D(maxhold=90),
 "V07 gap <=-2.66->-3.2 (P4+P10)": D(gap=-3.2),
 "V08 slope >0.60->>0.70 (P11)": D(slope=0.70),
 "V09 RSI(5) >70->>80 (P9)": D(rsi=80.0),
 "V10 RSI(5) <100 (skip flat-top bars) (P9)": D(rsimax=99.9),
 "V11 refire cooldown 6->3 bars (P8)": D(cd=3),
 "V12 refire cooldown 6->12 bars (P8)": D(cd=12),
 "V13 lots per symbol 3->2 (P13)": D(symcap=2),
 "V14 lots per symbol 3->1 (P13)": D(symcap=1),
 "V15 geometry t05s1->t1s1 (target 1R) (P23)": D(up=1.0),
 "V16 geometry t05s1->t05s05 (stop 0.5R) (P22)": D(dn=0.5),
 "V17 1R 0.25->0.30 x ATR (P19)": D(rf=0.30),
 "V18 cost filter 0.15->0.10R (P16)": D(cf=0.10),
 "V19 1R >= 1.0% of price (P1 intake)": D(rpct=1.0),
 "V20 skip SPY > +0.30% since 09:50 (gate)": D(spy950=0.30),
 "V21 skip SPY < -0.30% since 09:50 (gate)": D(spydn=0.30),
 "V22 price >= $5 -> >= $10 (P2)": D(minpx=10.0),
}
# Round 2 (declared after ROUND1 + the component analysis in comp.txt, before any ROUND2 score): sibling parts (13:00 end,
# max hold 75) help the replay but NOT the 2-year here; cost/R, RSI cap, slope cap, volume cap, price, VWAP distance, short
# max hold and a 'not working' time stop are the slices that look better in most of replay/TRAIN/VALID/FWD.
ROUND2 = {
 "PARENT": PARENT,
 "W01 cost filter 0.15->0.075R (P16)": D(cf=0.075),
 "W02 cost filter 0.15->0.05R (P16)": D(cf=0.05),
 "W03 RSI(5) <= 90 (P9 cap)": D(rsimax=90.0),
 "W04 SMA20 slope <= 1.0 (P11 cap)": D(slopemax=1.0),
 "W05 volumeRatio <= 2.5 (new sensor)": D(volmax=2.5),
 "W06 price >= $20 (P2)": D(minpx=20.0),
 "W07 VWAP dist <= 2% (new sensor)": D(vwmax=2.0),
 "W08 max hold 30 min (P25)": D(maxhold=30),
 "W09 max hold 45 min (P25)": D(maxhold=45),
 "W10 30 min if best < 0.25R (P25)": D(maxhold=30, ts_r=0.25),
 "W11 skip 13:00-14:00 bar closes (P6)": D(todskip=(1305, 1400)),
 "W12 cf 0.10 + start 10:30": D(cf=0.10, w=(1030, 1500)),
 "W13 cf 0.10 + RSI<100 + start 10:30": D(cf=0.10, rsimax=99.9, w=(1030, 1500)),
 "W14 cf 0.10 + RSI<100 + start 10:30 + vol<=2.5": D(cf=0.10, rsimax=99.9, w=(1030, 1500), volmax=2.5),
}
# Round 3 (declared after ROUND2: cost/R <= 0.05, slope <= 1.0, price >= $20, VWAP <= 2% and the RSI<100/start-10:30 combo lift both
# tests; max hold / 13:00 cut lift only the replay). Combos of the both-test parts, plus the replay-only exit parts on top.
B3 = dict(cf=0.05, slopemax=1.0, rsimax=99.9, w=(1030, 1500))
ROUND3 = {
 "PARENT": PARENT,
 "X01 cf0.05 + slope<=1.0": D(cf=0.05, slopemax=1.0),
 "X02 cf0.05 + slope<=1.0 + RSI<100": D(cf=0.05, slopemax=1.0, rsimax=99.9),
 "X03 cf0.05 + slope<=1.0 + RSI<100 + start 10:30": D(**B3),
 "X04 X03 + skip 13:00-14:00": D(**B3, todskip=(1305, 1400)),
 "X05 X03 + max hold 30": D(**B3, maxhold=30),
 "X06 X03 + max hold 45": D(**B3, maxhold=45),
 "X07 cf0.075 + slope<=1.0 + RSI<100 + start 10:30": D(**dict(B3, cf=0.075)),
 "X08 X03 + VWAP dist <= 3%": D(**B3, vwmax=3.0),
 "X09 X03 + lots per symbol 1 (tool only)": D(**B3, symcap=1),
 "X10 cf0.05 + RSI<=90 + slope<=1.0": D(cf=0.05, rsimax=90.0, slopemax=1.0),
 "X11 cf0.05 + slope<=1.0 + skip 13:00-14:00": D(cf=0.05, slopemax=1.0, todskip=(1305, 1400)),
 "X12 X03 + window end 13:00": D(**dict(B3, w=(1030, 1300))),
}
# Round 4 (declared after ROUND3: X10 = cost/R <= 0.05 + RSI(5) <= 90 + slope <= 1.0 is best in both tests and every 2y split;
# check small neighbours / add-ons before choosing; exit parts once more on top).
B4 = dict(cf=0.05, rsimax=90.0, slopemax=1.0)
ROUND4 = {
 "PARENT": PARENT,
 "X10 cf0.05 + RSI<=90 + slope<=1.0": D(**B4),
 "Y01 X10 + start 10:30": D(**B4, w=(1030, 1500)),
 "Y02 X10 + price >= $20": D(**B4, minpx=20.0),
 "Y03 X10 with cost/R 0.075": D(**dict(B4, cf=0.075)),
 "Y04 X10 + volumeRatio <= 2.5": D(**B4, volmax=2.5),
 "Y05 X10 + max hold 45": D(**B4, maxhold=45),
 "Y06 X10 with slope cap 0.85": D(**dict(B4, slopemax=0.85)),
 "Y07 X10 with RSI cap 85": D(**dict(B4, rsimax=85.0)),
}
