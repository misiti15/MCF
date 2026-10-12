"""Testing 2 (owner-directed forward test, 2026-10-12): Coil Under the High (4 bars).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B4-parta-k4-t05s1-guest (id 197), research/bdi/cwt/test_b/.
09:50-11:30: the high of day tested 3+ times and the last 4 bars tight just under it; buy for a half-R target.
Exit: t05s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1130].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B4-parta-k4-t05s1-guest"]


def mask(df):
    return L.b4a(df, nco=4)
