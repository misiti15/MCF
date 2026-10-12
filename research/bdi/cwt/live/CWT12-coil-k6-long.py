"""Testing 2 (owner-directed forward test, 2026-10-12): Coil Under the High (6 bars).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B4-parta-k6-t1s05-guest (id 207), research/bdi/cwt/test_b/.
09:50-11:30: the high of day has been tested 3+ times and the last 6 bars are tight (half the usual range) just under it; buy the coil.
Exit: t1s05 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1130].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t1s05"
LAYERS = ["B4-parta-k6-t1s05-guest"]


def mask(df):
    return L.b4a(df, nco=6)
