"""Testing 2 (owner-directed forward test, 2026-10-12): Backside Lower-High Short (big runner).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B1-a2.5-trigT2-t1s1-guest (id 27), research/bdi/cwt/test_b/.
10:30-15:00: a stock that ran 2.5+ daily ATRs off the open has broken down (40% off the high, below VWAP); the bounce retraces 38-62% of the drop and a bar closes below the prior bar's low; short.
Exit: t1s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [1030, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["B1-a2.5-trigT2-t1s1-guest"]


def mask(df):
    return L.b1(df, a=2.5, trig=2)
