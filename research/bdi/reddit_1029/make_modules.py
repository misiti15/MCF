"""Writes the 12 pre-declared reddit_1029 modules (PLAN.md). Educational only - not financial advice."""
from pathlib import Path
OUT = Path(__file__).resolve().parent / "modules"
HEAD = '''"""{name} - Reddit scout 2026-10-29 (research/bdi/reddit_1029/PLAN.md). {desc}
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rb_util as U  # noqa: E402
SIDE = "long"
GEOM = "S"
WINDOW = {win}
MIN_ADV = 95e6
'''
n = 0
for K in (2, 3):
    for ip in (0, 1):
        for ex in ("t2r", "hold"):
            name = f"RB1-3barplay-k{K}-{'inplay' if ip else 'all'}-{ex}-long"
            s = HEAD.format(name=name, win=(950, 1500), desc=f"3 Bar Play: igniting bar >= {K}x 5m ATR, vol ratio >= 2, "
                            f"1-2 resting bars in its upper half, buy the break; in-play filter {'on' if ip else 'off'}; exit {ex}.")
            s += f'''

def mask(df):
    return U.three_bar_play(df, {K}, {bool(ip)})


def stop_price(f, i):
    return float(f["_rb_stop"].iloc[i])
'''
            if ex == "t2r":
                s += '''

def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + 2.0 * (px - stop)
'''
            (OUT / f"{name}.py").write_text(s); n += 1
for p in ("A", "B"):
    for ex in ("vwap", "hold"):
        name = f"RB2-vwap2sd-absorb-{'rsidiv' if p == 'A' else 'flow3'}-{ex}-long"
        s = HEAD.format(name=name, win=(1020, 1500), desc=f"VWAP -2SD extension, close back inside above the prior high, "
                        f"delta proxy {p}; stop below the 4-bar low; exit {ex}.")
        s += f'''

def mask(df):
    return U.vwap_absorb(df, "{p}")


def stop_price(f, i):
    return float(f["_rb_stop"].iloc[i])
'''
        if ex == "vwap":
            s += '''

def target_price(f, i, stop):
    return float(f["_rb_vwap"].iloc[i])
'''
        (OUT / f"{name}.py").write_text(s); n += 1
print(n, "modules")
