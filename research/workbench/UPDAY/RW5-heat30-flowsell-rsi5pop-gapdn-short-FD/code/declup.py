# RW5 UPDAY check (declared before scores): parent and WB3 must reproduce their Workbench numbers.
from sim2 import BASE as B0
from uplayer import UPDEF
BASE = dict(B0, **UPDEF)
WB3 = dict(BASE, spy950=0.20, costr=0.15, w=(1015, 1500))
CHECK = {"PARENT": BASE, "WB3": WB3}
# ROUND1 (declared 2026-11-17 ~02:20 UTC after the day-type bucket diagnosis, before any layer score). Same list for RW3 and
# RW5, on BOTH bases. U15 = SPY > +0.15% above its 09:50 close (parent); on WB3 (which already skips SPY > +0.20%) the up
# state used is R10 = SPY up > +0.10% over the last 30 minutes. Y = in-trade SPY exit (the L3 WB5 part).
P = lambda **k: dict(BASE, **k)
W = lambda **k: dict(WB3, **k)
U15 = ("spy950", 0.15); R10 = ("spy30", 0.10)
ROUND1 = {
 "PARENT": BASE, "WB3": WB3,
 "P-Y1 exit if SPY +0.30% since entry": P(spyx=0.30),
 "P-Y2 exit if SPY +0.50% since entry": P(spyx=0.50),
 "P-Y3 exit if SPY +0.20% since entry": P(spyx=0.20),
 "P-Z1 exit if SPY +0.30% & under water": P(spyx=0.30, spyx_loss=True),
 "P-T1 U15: entries end 12:00": P(ust=U15, up_wend=1200),
 "P-L3 L3-WB5 recipe (Y1 + U15 end 12:00)": P(spyx=0.30, ust=U15, up_wend=1200),
 "P-X1 U15: max hold 60": P(ust=U15, up_hold=60),
 "P-G3 skip SPY last-30m>+0.20%": P(ust=("spy30", 0.20), up_skip=True),
 "W-Y1 WB3 + exit if SPY +0.30% since entry": W(spyx=0.30),
 "W-Y2 WB3 + exit if SPY +0.50% since entry": W(spyx=0.50),
 "W-Y3 WB3 + exit if SPY +0.20% since entry": W(spyx=0.20),
 "W-Z1 WB3 + exit if SPY +0.30% & under water": W(spyx=0.30, spyx_loss=True),
 "W-T1 WB3 + R10: entries end 12:00": W(ust=R10, up_wend=1200),
 "W-L3 WB3 + Y1 + R10 end 12:00": W(spyx=0.30, ust=R10, up_wend=1200),
 "W-X1 WB3 + R10: max hold 60": W(ust=R10, up_hold=60),
 "W-G3 WB3 + skip SPY last-30m>+0.20%": W(ust=("spy30", 0.20), up_skip=True),
}
# ROUND2 RW5 (declared after ROUND1: on WB3 the under-water SPY exit +0.30% (W-Z1) meets WB3's replay and beats its 2-year;
# the plain +0.30% exit costs the replay 0.013. Mirror of RW3's ROUND2: thresholds 0.35-0.40, under-water at 0.40, and WB3 with
# its SPY gate swapped for the WB5 recipe.)
SWB = dict(BASE, costr=0.15, w=(1015, 1500))   # WB3 without its SPY gate
ROUND2 = {
 "PARENT": BASE, "WB3": WB3,
 "W-Y4 WB3 + exit if SPY +0.40% since entry": W(spyx=0.40),
 "W-Y5 WB3 + exit if SPY +0.35% since entry": W(spyx=0.35),
 "W-Z2 WB3 + exit if SPY +0.40% & under water": W(spyx=0.40, spyx_loss=True),
 "SW1 WB3 gate swapped for WB5 recipe (Y1 + U15 end 12:00)": dict(SWB, spyx=0.30, ust=U15, up_wend=1200),
 "SW2 SW1 with SPY exit +0.40%": dict(SWB, spyx=0.40, ust=U15, up_wend=1200),
 "SW4 WB3 gate swapped for under-water exit +0.30% + U15 end 12:00": dict(SWB, spyx=0.30, spyx_loss=True, ust=U15, up_wend=1200),
}
