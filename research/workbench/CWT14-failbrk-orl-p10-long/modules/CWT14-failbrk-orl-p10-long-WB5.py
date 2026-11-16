# WORKBENCH VARIANT CWT14-failbrk-orl-p10-long-WB5 (research only, not enabled in any account)
# parent: CWT14-failbrk-orl-p10-long (research/bdi/cwt/live/CWT14-failbrk-orl-p10-long.py); built on WB4; Mechanic rerun 2026-11-16.
# Layers on top of the parent's signal (each scored in RESULTS.md "Rerun"):
#   intake  daily ATR >= 2.0% of price (WB4) and cost-to-R <= 0.10: (2 x (1c + 1 bp) + 2c) / (0.30 x ATR) <= 0.10
#   gate    SPY since 09:50 >= -0.20% at the decision bar (owner direction rule: anchored after 09:50), needs `context: [spy_fo]`
#   exits   GEOM "S": stop = signal close - 0.45 x ATR (1.5 x the WB4 1R of 0.30 ATR), target = close + 0.15 x ATR, flat 15:55
# Educational only - not financial advice.
"""Failed Opening-Range-Low Break Long (0.1 ATR) — WB5. Parent signal unchanged (cwt_live_lib.b3, OR level, p 0.10):
09:50-12:00, price pokes 0.1+ ATR under the 09:30-10:00 low, then closes back above it within 3 bars; buy."""
import sys as _sys
_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'research' / 'bdi' / 'cwt' / 'live'))
import numpy as np  # noqa: E402
import cwt_live_lib as L  # noqa: E402

SIDE = "long"
GEOM = "S"
LAYERS = ["B3-LOR-p0.1-Vany-sidelong-t05s1-guest", "WB4 atr>=2%", "cost/R<=0.10", "SPY since 09:50 >= -0.20%", "stop 0.45 ATR / target 0.15 ATR"]
R_ATR = 0.30            # the WB4 1R
STOP_R, TARGET_R = 1.5, 0.5
MAX_COST_R = 0.10
SPY_MIN_SINCE_0950 = -0.20   # percent


def _cost_ps(px):
    return 2 * (0.01 + px * 1e-4) + 0.02          # round trip + stop-exit slippage per share (the runner's CF model)


def mask(df):
    m = L.b3(df, level='OR', p=0.10, lowvol=False, side='long')
    close = df["close"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    m &= atr / close >= 0.02
    m &= _cost_ps(close) / (R_ATR * atr) <= MAX_COST_R
    if "spy_fo" not in df.columns:                  # fail safe: no market context, no signal
        return m & False
    x = L.arrays(df)
    fo = df["spy_fo"].to_numpy(float)
    at950 = np.where(x.tod == 950, fo, np.nan)
    import pandas as pd
    fo950 = pd.Series(at950).groupby(x.seg).transform("first").to_numpy(float)
    since = ((1 + fo / 100) / (1 + fo950 / 100) - 1) * 100
    return m & (since >= SPY_MIN_SINCE_0950)        # NaN (no 09:50 row) -> False


def stop_price(f, i):
    return float(f["close"].iloc[i]) - STOP_R * R_ATR * float(f["atr_d"].iloc[i])


def target_price(f, i, stop):
    return float(f["close"].iloc[i]) + TARGET_R * R_ATR * float(f["atr_d"].iloc[i])
