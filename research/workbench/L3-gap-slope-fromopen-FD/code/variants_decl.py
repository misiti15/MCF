# Pre-declared one-part tweaks (declared 2026-11-16 ~10:40 ET, after reading the live trade breakdown, before any test score).
VARIANTS = {
    "V01 window end 15:00->13:00 (P6)": dict(w=(950, 1300)),
    "V02 window end 15:00->14:00 (P6)": dict(w=(950, 1400)),
    "V03 window start 09:50->10:05 (P6/P7)": dict(w=(1005, 1500)),
    "V04 target 1.0->0.8R (P22)": dict(up=0.8),
    "V05 stop 1.0->1.25R (P21)": dict(dn=1.25),
    "V06 time exit 15:55->15:00 (P24)": dict(flat=1500),
    "V07 fromOpen >3.46->>4.0 (P9)": dict(fo=4.0),
    "V08 slope >0.372->>0.45 (P11)": dict(slope=0.45),
    "V09 gap <=-2.66->-3.2 (P4+P10)": dict(gap=-3.2),
    "V10 refire cooldown 1->3 bars (P8)": dict(cd=3),
    "V11 lots per symbol 3->2 (P13)": dict(symcap=2),
    "V12 open-lot cap 30->40 (P12)": dict(cap=40),
}
# Combined copy (declared after the single-part results: V01 and V09 each passed alone; both config-only).
COMBO = {"C1 window end 13:00 + gap <=-3.2 (P6+P4/P10)": dict(w=(950, 1300), gap=-3.2)}
import os
if os.environ.get("COMBO"):
    VARIANTS = COMBO
