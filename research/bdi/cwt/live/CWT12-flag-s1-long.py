"""Testing 2 (owner-directed forward test, 2026-10-12): Spike-Pullback Flag Breakout.
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B4-partb-k1-t05s1-full (id 212), research/bdi/cwt/test_b/.
09:50-15:00: a 1-ATR push off the open, a 30-50% pullback that stays above VWAP, then the first close above the push high; buy.
Exit: t05s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B4-partb-k1-t05s1-full"]


def mask(df):
    return L.b4b(df, s=1.0)
