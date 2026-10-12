"""Testing 2 (owner-directed forward test, 2026-10-12): Stretched Above VWAP Fade (far).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B2-z0.75-Uall-sideshort-t1s1-guest (id 67), research/bdi/cwt/test_b/.
11:00-15:00: price at the high of day 0.75+ daily ATRs above VWAP; the next bar makes a lower high; short.
Exit: t1s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [1100, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["B2-z0.75-Uall-sideshort-t1s1-guest"]


def mask(df):
    return L.b2(df, z=0.75, side='short')
