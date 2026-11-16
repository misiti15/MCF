# WORKBENCH VARIANT CWT14-failbrk-pdl-p10-lowvol-long-WB2 (research only, not enabled in any account)
# parent: CWT14-failbrk-pdl-p10-lowvol-long (research/bdi/cwt/live/CWT14-failbrk-pdl-p10-lowvol-long.py); Mechanic 2026-11-16. Change: intake: only names that gapped down >= 0.5% (gap <= -0.5%)
# Educational only - not financial advice.
"""Failed Prior-Day-Low Break Long (0.1 ATR, low volume) - WB2: intake: only names that gapped down >= 0.5% (gap <= -0.5%). Parent signal unchanged (cwt_live_lib.b3, PD level,
p 0.10, poke bar volumeRatio < 1): 09:50-15:00, price pokes 0.1+ ATR under yesterday's low on below-average volume, then
closes back above it within 3 bars; buy."""
import sys as _sys
_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'research' / 'bdi' / 'cwt' / 'live'))
import cwt_live_lib as L  # noqa: E402

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B3-LPD-p0.1-Vlowvol-sidelong-t05s1-full", "intake: only names that gapped down >= 0.5% (gap <= -0.5%)"]
GAP_MAX = -0.5         # percent: today's open vs yesterday's close (stock-level intake, known at the open)



def mask(df):
    m = L.b3(df, level='PD', p=0.10, lowvol=True, side='long')
    m &= df["gap"].to_numpy(float) <= GAP_MAX           # NaN gap -> False
    return m
