# RERUN pre-declared layers on top of WB3 (declared 2026-11-16 ~11:35 ET after the component analysis, before any score).
from sim2 import BASE, WB3
D = lambda **k: dict(WB3, **k)
ROUND1 = {
 "PARENT": BASE, "WB3": WB3,
 "A1 +2 lots/symbol": D(symcap=2), "A2 +cooldown 3": D(cd=3), "A3 +slope>0.45": D(slope=0.45), "A4 +flat 15:00": D(flat=1500),
 "A5 +2 lots +cooldown 3": D(symcap=2, cd=3), "A6 +2 lots +flat 15:00": D(symcap=2, flat=1500),
 "B1 skip SPY>+0.30% since 09:50": D(spy950=0.30), "B2 skip SPY>+0.15% since 09:50": D(spy950=0.15),
 "B3 skip SPY above 09:30-09:50 high": D(spyrng=1),
 "C1 target 1c shallower (touch fills)": D(tgtc=True), "C2 target 0.95R": D(up=0.95),
 "D1 BE stop after +0.5R": D(be_at=0.5, be_to=0.0), "D2 stop->+0.2R after +0.6R": D(be_at=0.6, be_to=0.2),
 "D3 stop->+0.4R after +0.75R": D(be_at=0.75, be_to=0.4), "D4 max hold 90 min": D(maxhold=90),
 "D5 stop 1.25R": D(dn=1.25), "D6 stop 1.25R +2 lots": D(dn=1.25, symcap=2),
 "E1 1R >= 1.0% of price": D(rpct=1.0), "E2 fromOpen <= 10": D(fomax=10.0), "E3 VWAP dist <= 4%": D(vwmax=4.0),
}
# Round 2 (declared after ROUND1: exits D1/D4/A4 lifted both tests without cutting trades; D5 lifts avg R but deepens the 2y worst day).
ROUND2 = {
 "PARENT": BASE, "WB3": WB3,
 "F1 BE@0.5 + hold 90": D(be_at=0.5, maxhold=90), "F2 hold 60": D(maxhold=60), "F3 hold 120": D(maxhold=120),
 "F4 stop 1.25 + BE@0.5": D(dn=1.25, be_at=0.5), "F5 stop 1.25 + hold 90": D(dn=1.25, maxhold=90),
 "F6 stop 1.25 + BE@0.5 + hold 90": D(dn=1.25, be_at=0.5, maxhold=90),
 "F7 F1 + 2 lots": D(be_at=0.5, maxhold=90, symcap=2), "F8 F1 + skip SPY>+0.30": D(be_at=0.5, maxhold=90, spy950=0.30),
 "F9 BE@0.4": D(be_at=0.4), "F10 F6 + 2 lots": D(dn=1.25, be_at=0.5, maxhold=90, symcap=2),
 "F11 F1 + slope>0.45": D(be_at=0.5, maxhold=90, slope=0.45),
}
# Round 3 (declared after ROUND2: max hold 60-90 and stop 1.25 + hold 90 are the only ones better in every 2y split; BE/2-lot add-ons do not stack).
ROUND3 = {
 "PARENT": BASE, "WB3": WB3,
 "G1 stop 1.25 + hold 90 + 2 lots": D(dn=1.25, maxhold=90, symcap=2), "G2 hold 90 + 2 lots": D(maxhold=90, symcap=2),
 "G3 stop 1.25 + hold 60": D(dn=1.25, maxhold=60), "G4 stop 1.15 + hold 90": D(dn=1.15, maxhold=90),
 "G5 hold 75": D(maxhold=75), "G6 stop 1.25 + hold 75": D(dn=1.25, maxhold=75),
}
# Round 4 (declared after ROUND3: stop 1.25 + max hold 60/75/90 all better than WB3 in every 2y split; 2-lot add-on helped G1).
ROUND4 = {"PARENT": BASE, "WB3": WB3, "G6 stop 1.25 + hold 75": D(dn=1.25, maxhold=75),
          "H1 stop 1.25 + hold 75 + 2 lots": D(dn=1.25, maxhold=75, symcap=2), "G5 hold 75": D(maxhold=75),
          "G1 stop 1.25 + hold 90 + 2 lots": D(dn=1.25, maxhold=90, symcap=2)}
# Round 5 (declared after ROUND4. Note: stop 1.25R is not a config option (LabStrategy GEOMS) and, with risk-based sizing, its
# R per trade is /1.25 in its own risk units -> dropped from the recommendation; the runner's time_stop_min / time_stop_min_r
# exists per setup, so test the 'not working yet' time stop and the 2-lot add-on on top of max hold 75).
ROUND5 = {"PARENT": BASE, "WB3": WB3, "G5 hold 75": D(maxhold=75),
          "I1 hold 75 + 2 lots": D(maxhold=75, symcap=2), "I2 60 min if best < 0.5R": D(maxhold=60, ts_r=0.5),
          "I3 45 min if best < 0.3R": D(maxhold=45, ts_r=0.3), "I4 75 min if best < 0.75R": D(maxhold=75, ts_r=0.75),
          "I5 90 min if best < 0.5R": D(maxhold=90, ts_r=0.5)}
# Round 6 (declared after the best-5 teardowns: WB3's gap <= -3.2 excludes CRWV (-3.04), CLSK (-3.19), SNAP (-2.68) and its
# 13:00 end excludes PBR; does max hold 75 still win with the gap left at the parent's -2.66 or at -3.0?).
ROUND6 = {"PARENT": BASE, "WB3": WB3, "G5 hold 75": D(maxhold=75),
          "J1 window 13:00 + hold 75 (gap -2.66)": dict(BASE, w=(950, 1300), maxhold=75),
          "J2 parent + hold 75": dict(BASE, maxhold=75),
          "J3 window 13:00 + gap -3.0 + hold 75": dict(BASE, w=(950, 1300), gap=-3.0, maxhold=75)}
