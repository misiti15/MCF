# Pre-declared one-part copies (declared 2026-11-16 ~13:40 ET after the live-trade teardowns, before any score).
from sim import PARENT
D = lambda **k: dict(PARENT, **k)
ROUND1 = {
 "PARENT": PARENT, "PARENT isolated (no book)": D(book=False),
 "V01 P5/P8 skip the 10:45 bar when gap > 0": D(g1045=0.0), "V02 P5 start 10:50": D(w=(1050, 1500)),
 "V03 P5 end 14:00": D(w=(950, 1400)), "V04 P10 fromOpen < -1.5": D(fo=-1.5), "V05 P11 buyPressure > 0.10": D(bp=0.10),
 "V06 P1 cost/R <= 0.10": D(costr=0.10), "V07 P1 ATR >= 2% of price": D(atrmin=2.0), "V08 P3 price >= $10": D(minpx=10.0),
 "V09 P18 1R 0.30 ATR": D(rf=0.30), "V10 P21 stop 1.25R": D(dn=1.25), "V11 P22 target 0.8R": D(up=0.8),
 "V12 P24 max hold 90 min": D(maxhold=90), "V13 P24 60 min if best < 0.3R": D(maxhold=60, ts_r=0.3),
 "V14 P21 BE after +0.6R": D(be_at=0.6, be_to=0.0),
 "V15 gate skip SPY since 09:50 < -0.30%": D(spymin=-0.30), "V16 gate skip SPY since 09:50 > +0.30%": D(spymax=0.30),
 "V17 gate skip SPY above 09:30-09:50 high": D(spyhi=1), "V18 P12 open lots 10": D(cap=10),
}
# Round 2 (declared after ROUND1: V06 cost/R <= 0.10 and V16 skip SPY > +0.30% since 09:50 beat the parent in both tests and
# cut the worst day; V07 / V10 / V17 marginal; neighbours + combinations).
ROUND2 = {
 "PARENT": PARENT,
 "W01 cost/R <= 0.08": D(costr=0.08), "W02 cost/R <= 0.12": D(costr=0.12), "W03 cost/R <= 0.15": D(costr=0.15),
 "W04 skip SPY > +0.20%": D(spymax=0.20), "W05 skip SPY > +0.40%": D(spymax=0.40), "W06 skip SPY > 0.00%": D(spymax=0.0),
 "C1 cost/R 0.10 + SPY > +0.30%": D(costr=0.10, spymax=0.30), "C2 cost/R 0.12 + SPY > +0.30%": D(costr=0.12, spymax=0.30),
 "C3 cost/R 0.15 + SPY > +0.30%": D(costr=0.15, spymax=0.30), "C4 C1 + stop 1.25R": D(costr=0.10, spymax=0.30, dn=1.25),
 "C5 C1 + price >= $10": D(costr=0.10, spymax=0.30, minpx=10.0), "C6 C1 + 60 min if best < 0.3R": D(costr=0.10, spymax=0.30, maxhold=60, ts_r=0.3),
 "C7 C1 + bp > 0.10": D(costr=0.10, spymax=0.30, bp=0.10), "C8 cost/R 0.10 + SPY above 09:30-09:50 high": D(costr=0.10, spyhi=1),
 "C9 C1 + ATR >= 2%": D(costr=0.10, spymax=0.30, atrmin=2.0), "C10 C1 + open lots 10": D(costr=0.10, spymax=0.30, cap=10),
}
# Round 3 (declared after ROUND2: W06 skip-when-SPY-up-since-09:50 is the strongest single layer in both tests; combos with
# cost/R thin the 77-trade replay too far. Neighbours of W06, light add-ons, and ST7Q's QQQ<=VWAP rule as a twin check).
ROUND3 = {
 "PARENT": PARENT, "W06 skip SPY > 0.00%": D(spymax=0.0),
 "X1 skip SPY > -0.10%": D(spymax=-0.10), "X2 skip SPY > +0.10%": D(spymax=0.10),
 "X3 W06 + cost/R <= 0.15": D(spymax=0.0, costr=0.15), "X4 W06 + stop 1.25R": D(spymax=0.0, dn=1.25),
 "X5 W06 + ATR >= 2%": D(spymax=0.0, atrmin=2.0), "X6 W06 + price >= $10": D(spymax=0.0, minpx=10.0),
 "X7 W06 + 60 min if best < 0.3R": D(spymax=0.0, maxhold=60, ts_r=0.3), "X8 W06 + target 1.25R": D(spymax=0.0, up=1.25),
}
# Round 4 (declared after ROUND3: X2 skip-SPY > +0.10% keeps the most trades and the best 2-year total and is positive in both
# 2-year halves; W06/X1 thinner. Light add-ons on X2).
ROUND4 = {
 "PARENT": PARENT, "X2 skip SPY > +0.10%": D(spymax=0.10),
 "Y1 X2 + cost/R <= 0.15": D(spymax=0.10, costr=0.15), "Y2 X2 + ATR >= 2%": D(spymax=0.10, atrmin=2.0),
 "Y3 X2 + price >= $10": D(spymax=0.10, minpx=10.0), "Y4 X2 + stop 1.25R": D(spymax=0.10, dn=1.25),
}
