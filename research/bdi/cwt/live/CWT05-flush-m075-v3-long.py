"""Testing 2 (owner-directed forward test, 2026-10-12): Panic Flush Reversal (deep, 3x volume).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B5-m0.75-v3-Dnone-t05s1-full (id 260), research/bdi/cwt/test_b/.
09:50-15:00: a 0.75-ATR drop in 30 minutes to a new low of day with a 3x volume bar, then the first bar closing above the prior bar's high; buy.
Exit: t05s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1500].
Signal code: cwt_live_lib.py (ports of the scored kernels). Parity: verify.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B5-m0.75-v3-Dnone-t05s1-full"]


def mask(df):
    return L.b5(df, m=0.75, v=3)
