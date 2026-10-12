"""Testing 2 (owner-directed forward test, 2026-10-12): Backside VWAP-Test Short (big runner).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B1-a2.5-trigT1-t1s1-full (id 18), research/bdi/cwt/test_b/.
09:50-15:00: after a 2.5-ATR run breaks down below VWAP, a bar reaches back up to VWAP and closes below it; short.
Exit: t1s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1500].
Signal code: cwt_live_lib.py (ports of the scored kernels). Parity: verify.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["B1-a2.5-trigT1-t1s1-full"]


def mask(df):
    return L.b1(df, a=2.5, trig=1)
