# UPDAY pre-declared configs (Mechanic 2026-11-17). Round 1 declared ~02:10 UTC after the day-type diagnosis (diag.txt),
# before any config score. All on the PARENT (the requested base). U = up state at the signal bar (post-09:50 anchors).
from sim3 import BASE, WB4
P = lambda **k: dict(BASE, **k)
U15 = ("spy950", 0.15)
ROUND1 = {
 "PARENT": BASE, "WB4": WB4,
 "G1 skip SPY>+0.25% since 09:50": P(ust=("spy950", 0.25), up_skip=True),
 "G2 skip SPY>+0.40% since 09:50": P(ust=("spy950", 0.40), up_skip=True),
 "G3 skip SPY last-30m>+0.20%": P(ust=("spy30", 0.20), up_skip=True),
 "G4 skip SPY>+0.15% & rising 30m": P(ust=("both", 0.15), up_skip=True),
 "S1 half size SPY>+0.25%": P(ust=("spy950", 0.25), up_w=0.5),
 "S2 half size SPY last-30m>+0.20%": P(ust=("spy30", 0.20), up_w=0.5),
 "X1 U15: max hold 60": P(ust=U15, up_hold=60),
 "X2 U15: target 0.75R": P(ust=U15, up_tgt=0.75),
 "X3 U15: stop 0.8R": P(ust=U15, up_stop=0.8),
 "X4 U15: half off at +0.5R": P(ust=U15, up_so=0.5),
 "Y1 exit if SPY +0.30% since entry": P(spyx=0.30),
 "Y2 exit if SPY +0.50% since entry": P(spyx=0.50),
 "Y3 exit if SPY +0.20% since entry": P(spyx=0.20),
 "Q1 U15: gap <= -5%": P(ust=U15, up_gap=-5.0),
 "Q2 U15: fromOpen > 5": P(ust=U15, up_fo=5.0),
 "Q3 U15: RS since 09:50 < 4%": P(ust=U15, up_rs=4.0),
 "T1 U15: entries end 12:00": P(ust=U15, up_wend=1200),
 "T2 SPY rising 30m>+0.10%: no entries before 10:30": P(ust=("spy30", 0.10), up_wstart=1030),
}
# Round 2 (declared after ROUND1: only the in-trade SPY exit Y1-Y3 lifts up days in BOTH tests while leaving 2-year down
# days ~unchanged; entry gates / size-down / U-only exits lift one test and cut the other). Tune the SPY exit, stack it with
# the two time-of-day parts that passed (T1, T2) and with G3, and put the best parts on WB4.
W = lambda **k: dict(WB4, **k)
ROUND2 = {
 "PARENT": BASE, "WB4": WB4,
 "R2a exit if SPY +0.40% since entry": P(spyx=0.40),
 "R2b exit if SPY +0.25% since entry": P(spyx=0.25),
 "R2c U15 trades only: exit if SPY +0.30%": P(ust=U15, spyx=0.30, spyx_u=True),
 "R2d Y1 + U15 entries end 12:00": P(spyx=0.30, ust=U15, up_wend=1200),
 "R2e Y1 + SPY rising 30m>+0.10%: none before 10:30": P(spyx=0.30, ust=("spy30", 0.10), up_wstart=1030),
 "R2f Y1 + skip SPY last-30m>+0.20%": P(spyx=0.30, ust=("spy30", 0.20), up_skip=True),
 "W1 WB4 + exit if SPY +0.30% since entry": W(spyx=0.30),
 "W2 WB4 + exit if SPY +0.20% since entry": W(spyx=0.20),
 "W3 WB4 + exit if SPY +0.40% since entry": W(spyx=0.40),
 "W4 WB4 + Y1 + U15 entries end 12:00": W(spyx=0.30, ust=U15, up_wend=1200),
 "W5 WB4 + skip SPY last-30m>+0.20%": W(ust=("spy30", 0.20), up_skip=True),
 "W6 WB4 + SPY rising 30m>+0.10%: none before 10:30": W(ust=("spy30", 0.10), up_wstart=1030),
}
# Round 3 (declared after ROUND2: on the parent Y1 + U15 entries end 12:00 (R2d) lifts both tests; on WB4 the SPY exit cuts
# replay winners (W1-W3). Test the SPY exit only while the short is under water (targets the failure: the stock dragged up
# with the market) on both bases, and two neighbours of R2d.
ROUND3 = {
 "PARENT": BASE, "WB4": WB4,
 "Z1 exit if SPY +0.30% & short under water": P(spyx=0.30, spyx_loss=True),
 "Z2 exit if SPY +0.20% & short under water": P(spyx=0.20, spyx_loss=True),
 "Z3 R2d with SPY exit at +0.40%": P(spyx=0.40, ust=U15, up_wend=1200),
 "Z4 Y1 + U15 entries end 11:30": P(spyx=0.30, ust=U15, up_wend=1130),
 "Z5 WB4 + exit if SPY +0.30% & under water": W(spyx=0.30, spyx_loss=True),
 "Z6 WB4 + exit if SPY +0.20% & under water": W(spyx=0.20, spyx_loss=True),
 "Z7 WB4 + exit if SPY +0.40% & under water": W(spyx=0.40, spyx_loss=True),
 "Z8 R2d with under-water SPY exit": P(spyx=0.30, spyx_loss=True, ust=U15, up_wend=1200),
}
# Round 4 (declared after ROUND3: on WB4 every SPY-exit form gives back replay and does not lift replay up days (WB4's
# 75-min hold already covers them). Last try on WB4 with U-only entry / exit parts.
ROUND4 = {
 "PARENT": BASE, "WB4": WB4,
 "V1 WB4 + U15: max hold 45": W(ust=U15, up_hold=45),
 "V2 WB4 + U15: no entries before 11:00": W(ust=U15, up_wstart=1100),
 "V3 WB4 + U15: RS since 09:50 < 4%": W(ust=U15, up_rs=4.0),
 "V4 WB4 + U15: target 0.75R": W(ust=U15, up_tgt=0.75),
}
