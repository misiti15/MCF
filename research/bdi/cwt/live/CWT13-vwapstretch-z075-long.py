"""Testing 2 (owner-directed forward test, 2026-10-12): Stretched Below VWAP Bounce (far).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B2-z0.75-Uall-sidelong-t1s1-full (id 74), research/bdi/cwt/test_b/.
09:50-15:00: price sits at the low of day 0.75+ daily ATRs below VWAP after using 40% of its range; the next bar makes a higher low; buy.
Exit: t1s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1500].
Signal code: cwt_live_lib.py (ports of the scored kernels). Parity: verify.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t1s1"
LAYERS = ["B2-z0.75-Uall-sidelong-t1s1-full"]


def mask(df):
    return L.b2(df, z=0.75, side='long')
