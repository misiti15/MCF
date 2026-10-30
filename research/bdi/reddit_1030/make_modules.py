"""Writes the 10 pre-declared reddit_1030 modules (PLAN.md). Educational only - not financial advice."""
from pathlib import Path
OUT = Path(__file__).resolve().parent / "modules"
HEAD = '''"""{name} - Reddit scout 2026-10-30 (research/bdi/reddit_1030/PLAN.md). {desc}
Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rc_util as U  # noqa: E402
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1500)
MIN_ADV = 95e6


def stop_price(f, i):
    return float(f["_rc_stop"].iloc[i])
'''
T2R = '''

def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + 2.0 * (px - stop)
'''
n = 0
for lv in ("ema8", "vwap"):
    for vol, exits in ((True, ("t2r", "hold")), (False, ("hold",))):
        for ex in exits:
            name = f"RC1-volconfirm-{lv}-{'vol' if vol else 'novol'}-{ex}-long"
            s = HEAD.format(name=name, desc=f"RS stock pullback test of {lv}, volume sequence {'on' if vol else 'off'}, exit {ex}.")
            s += f'''

def mask(df):
    return U.volconfirm(df, "{lv}", {vol})
'''
            if ex == "t2r":
                s += T2R
            (OUT / f"{name}.py").write_text(s); n += 1
for D in (0.3, 0.6):
    for ex in ("t2r", "hold"):
        name = f"RC2-rs-spydip-orh-d{int(D*10):02d}-{ex}-long"
        s = HEAD.format(name=name, desc=f"RS >= 1% vs SPY while SPY is >= {D}% off its intraday high, close back above the 09:30-09:50 high with volume, exit {ex}.")
        s += f'''

def mask(df):
    return U.rs_spydip_orh(df, {D})
'''
        if ex == "t2r":
            s += T2R
        (OUT / f"{name}.py").write_text(s); n += 1
print(n, "modules")
