"""Testing 1 (owner request 2026-10-12, Reddit "trade liquidity" study): Prior-Day Low Sweep Reversal to VWAP Long.
Educational only - not financial advice. Did NOT pass the research gates; added under the lowered Testing bar
(research/bdi/reddit1012liq/PLAN.md section 5 (b)); train and valid disagree in sign (see NOTES.md).

Source: configuration LIQ-PD-long-x0.05-open-k15-a1-A-NL-BE+TS (research/bdi/reddit1012liq/score.py).
Price trades 0.05+ daily ATR below yesterday's low (coming from above it); within 60 minutes a 15-minute bar closes
above the open of the 15-minute bar that made the sweep (proxy: the prior 15-minute close); buy, but only when VWAP
is at least 2R (0.5 ATR) above. Stop 0.25 ATR (1R), target VWAP at the signal bar, flat 15:55.
Management in config/account_testing.yaml: be_at_r 1.0 (stop to entry at +1R), time_stop_min 15 / time_stop_min_r
0.25 (exit if not +0.25R within 15 minutes). Window [950, 1500]. Parity: verify.py -> verify.json.
"""
import numpy as np

import liq_live_lib as L

SIDE = "long"
GEOM = "S"
LAYERS = ["LIQ-PD-long-x0.05-open-k15-a1-A-NL-BE+TS"]
X, R_ATR, MIN_RR = 0.05, 0.25, 2.0


def mask(df):
    flag, _ = L.sweep(df, level="PD", side="long", x=X, trig="open", k=15)
    with np.errstate(invalid="ignore"):
        room = L.vwap(df) - df["close"].to_numpy(float)
        return flag & (room >= MIN_RR * R_ATR * L.atr_row(df))


def stop_price(f, i):
    return float(f["close"].iloc[i]) - R_ATR * float(L.atr_row(f)[i])


def target_price(f, i, stop):
    return float(L.vwap(f)[i])
