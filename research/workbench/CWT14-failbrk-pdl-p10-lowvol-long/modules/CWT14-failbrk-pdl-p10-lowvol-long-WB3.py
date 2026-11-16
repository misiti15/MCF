# WORKBENCH VARIANT CWT14-failbrk-pdl-p10-lowvol-long-WB3 (research only, not enabled in any account)
# parent: CWT14-failbrk-pdl-p10-lowvol-long (research/bdi/cwt/live/CWT14-failbrk-pdl-p10-lowvol-long.py); Mechanic 2026-11-16. Change: stop 0.45 ATR (WB1) + gap <= -0.5% intake (WB2)
# Educational only - not financial advice.
"""Failed Prior-Day-Low Break Long (0.1 ATR, low volume) - WB3: stop 0.45 ATR (WB1) + gap <= -0.5% intake (WB2). Parent signal unchanged (cwt_live_lib.b3, PD level,
p 0.10, poke bar volumeRatio < 1): 09:50-15:00, price pokes 0.1+ ATR under yesterday's low on below-average volume, then
closes back above it within 3 bars; buy."""
import sys as _sys
_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'research' / 'bdi' / 'cwt' / 'live'))
import cwt_live_lib as L  # noqa: E402

SIDE = "long"
GEOM = "S"
LAYERS = ["B3-LPD-p0.1-Vlowvol-sidelong-t05s1-full", "stop 0.45 ATR (WB1) + gap <= -0.5% intake (WB2)"]
GAP_MAX = -0.5         # percent: today's open vs yesterday's close (stock-level intake, known at the open)
STOP_ATR, TARGET_ATR = 0.45, 0.125   # parent t05s1 at 1R = 0.25 ATR: stop 0.25, target 0.125 (x daily ATR, from the signal close)


def mask(df):
    m = L.b3(df, level='PD', p=0.10, lowvol=True, side='long')
    m &= df["gap"].to_numpy(float) <= GAP_MAX           # NaN gap -> False
    return m


def stop_price(f, i):
    return float(f["close"].iloc[i]) - STOP_ATR * float(f["atr_d"].iloc[i])


def target_price(f, i, stop):
    return float(f["close"].iloc[i]) + TARGET_ATR * float(f["atr_d"].iloc[i])
