"""Testing 1 (owner request 2026-10-12, Reddit "trade liquidity" study): Opening-Range Low Sweep Reversal Long.
Educational only - not financial advice. Did NOT pass the research gates; added under the lowered Testing bar
(research/bdi/reddit1012liq/PLAN.md section 5 (b)). Open-history numbers: research/bdi/reddit1012liq/NOTES.md.

Source: configuration LIQ-OR-long-x0.15-open-k15-a1-S-2.5R-none (research/bdi/reddit1012liq/score.py).
From 10:05: price trades 0.15+ daily ATR below the 09:30-10:00 low (coming from above it); within 60 minutes a
15-minute bar closes above the open of the 15-minute bar that made the sweep (proxy: the prior 15-minute close); buy.
Stop 0.05 ATR under the sweep low (skipped if that is more than 1 ATR away), target 2.5x the risk, flat 15:55.
Exit: GEOM "S" with stop_price / target_price via LabStrategy. Window in config/account_testing.yaml: [950, 1500].
Parity: research/bdi/reddit1012liq/live/verify.py -> verify.json.
"""
import numpy as np

import liq_live_lib as L

SIDE = "long"
GEOM = "S"
LAYERS = ["LIQ-OR-long-x0.15-open-k15-a1-S-2.5R-none"]
X, BUF, MAXRISK, TGT_R = 0.15, 0.05, 1.0, 2.5


def _stop(df):
    flag, E = L.sweep(df, level="OR", side="long", x=X, trig="open", k=15)
    return flag, E - BUF * L.atr_row(df)


def mask(df):
    flag, stop = _stop(df)
    with np.errstate(invalid="ignore"):
        risk = df["close"].to_numpy(float) - stop
        return flag & (risk > 0) & (risk <= MAXRISK * L.atr_row(df))


def stop_price(f, i):
    return float(_stop(f)[1][i])


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + TGT_R * (px - stop)
