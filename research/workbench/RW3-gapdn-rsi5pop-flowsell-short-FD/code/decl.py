# RW3-FD Mechanic: pre-declared one-part tweaks (declared 2026-11-16 ~13:35 ET, after the live + replay component breakdown,
# BEFORE any 2-year score was read). Every part P1..P26 is inspected; tweaks are for the parts with a symptom or a knob.
from sim_rw3 import BASE
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "V01 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V02 window start 09:50->10:30 (P6/P7)": D(w=(1030, 1500)),
 "V03 gap <0 -> <=-1.0% (P12)": D(gapmax=-1.0),
 "V04 gap <0 -> <=-0.5% (P12)": D(gapmax=-0.5),
 "V05 +price at/below VWAP (new sensor)": D(vwmax=0.0),
 "V06 +skip SPY >+0.20% since 09:50 (new gate)": D(spy950=0.20),
 "V07 max hold 90 min (P26)": D(maxhold=90),
 "V08 max hold 120 min (P26)": D(maxhold=120),
 "V09 BE stop after +0.5R (P23)": D(be_at=0.5),
 "V10 RSI(5) >80 -> >85 (P11)": D(rsi5=85.0),
 "V11 buyPressure <-0.35 -> <-0.40 (P10)": D(bp=-0.40),
 "V12 heat <=-20 -> <=-25 (P9)": D(heat=-25.0),
 "V13 target 1.0 -> 0.8R (P24)": D(up=0.8),
 "V14 stop 1.0 -> 1.25R (P23)": D(dn=1.25),
 "V15 ADV $95M -> $150M (P2)": D(minadv=150e6),
 "V16 flat 15:55 -> 15:00 (P26)": D(flat=1500),
 "V17 refire on, cooldown 6 bars (P8)": D(refire=True, cd=6),
 "V18 per-setup latch -2R -> off (P16)": D(latch=-99.0),
}
# Round 2 (declared after ROUND1, before any combo score): passed alone in both tests = V02 start 10:30, V06 SPY gate,
# V08 max hold 120, V10 RSI(5) > 85, V16 flat 15:00, V17 refire (meets only), V01 end 13:00 (meets only). Combos stack the
# strongest (V06 + V16) and add each other passer; V06 threshold sensitivity (0.10 / 0.30) checks it is not a lucky cut.
ROUND2 = {
 "PARENT": BASE,
 "C1 SPY gate + flat 15:00": D(spy950=0.20, flat=1500),
 "C2 C1 + start 10:30": D(spy950=0.20, flat=1500, w=(1030, 1500)),
 "C3 C1 + RSI(5) > 85": D(spy950=0.20, flat=1500, rsi5=85.0),
 "C4 SPY gate + max hold 120": D(spy950=0.20, maxhold=120),
 "C5 C1 + max hold 120": D(spy950=0.20, flat=1500, maxhold=120),
 "C6 SPY gate + start 10:30": D(spy950=0.20, w=(1030, 1500)),
 "C7 C2 + RSI(5) > 85": D(spy950=0.20, flat=1500, w=(1030, 1500), rsi5=85.0),
 "S1 SPY gate +0.10%": D(spy950=0.10),
 "S2 SPY gate +0.30%": D(spy950=0.30),
 "S3 flat 14:30": D(flat=1430),
}
# Round 3 (declared after ROUND2: C2 = SPY gate + flat 15:00 + start 10:30 is the best in both tests; its 2-year trades
# show 1R < 0.30% of price at -0.24R (71 trades: cost eats thin R, as PDBC / XLI live), heat <= -25 and max hold also checked on top).
C2 = D(spy950=0.20, flat=1500, w=(1030, 1500))
E = lambda **k: dict(C2, **k)
ROUND3 = {
 "PARENT": BASE, "C2 SPY gate + flat 15:00 + start 10:30": C2,
 "R1 C2 + 1R >= 0.30% of price": E(rpct=0.30),
 "R2 C2 + 1R >= 0.40% of price": E(rpct=0.40),
 "R3 C2 + heat <= -25": E(heat=-25.0),
 "R4 C2 + max hold 120": E(maxhold=120),
 "R5 C1 + 1R >= 0.30% (start 09:50)": D(spy950=0.20, flat=1500, rpct=0.30),
}
# Round 4 (declared after ROUND3 and a deployability check: the live runner does NOT act on a per-setup flatten time
# (Signal.exit_by is backtest-only; mcf/strategies/index_dip.py), so "flat 15:00" cannot ship as a config copy. Deployable
# stand-ins for it: max hold (runner time_stop_min / time_stop_min_r) and an earlier window end.)
G = D(spy950=0.20, w=(1030, 1500), rpct=0.40)
F = lambda **k: dict(G, **k)
ROUND4 = {
 "PARENT": BASE, "R2 C2 + 1R >= 0.40% of price": E(rpct=0.40),
 "D1 SPY gate + start 10:30 + 1R >= 0.40%": G,
 "D2 D1 + max hold 120": F(maxhold=120),
 "D3 D1 + max hold 150": F(maxhold=150),
 "D4 D1 + window end 14:00": F(w=(1030, 1400)),
 "D5 D1 + end 14:00 + max hold 120": F(w=(1030, 1400), maxhold=120),
 "D6 D1 + max hold 90": F(maxhold=90),
}
# Round 5 (declared after ROUND4: D1 is the best deployable copy; attribution check of its parts).
ROUND5 = {"PARENT": BASE, "D1 SPY gate + start 10:30 + 1R >= 0.40%": G,
          "D7 SPY gate + 1R >= 0.40% (start 09:50)": D(spy950=0.20, rpct=0.40),
          "D8 1R >= 0.40% of price alone (P1/P20)": D(rpct=0.40)}
# Round 6 (destination check, declared after choosing WB3: the testing accounts run a different book than Primary - no -2R
# latch, 50 lots per setup, cost filter CF 0.15. Parent and copies re-scored under that book; information for the deploy plan.)
TB = dict(latch=-99.0, cap=50, cf=0.15)
ROUND6 = {"PARENT": BASE, "T0 parent, testing book": D(**TB), "T1 WB1 start 10:30, testing book": D(w=(1030, 1500), **TB),
          "T2 WB2 SPY gate, testing book": D(spy950=0.20, **TB), "T3 WB3 (D1), testing book": dict(G, **TB)}
