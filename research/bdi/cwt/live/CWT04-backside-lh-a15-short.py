"""Testing 2 (owner-directed forward test, 2026-10-12): Backside Lower-High Short.
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B1-a1.5-trigT2-t1s1-guest (id 11), research/bdi/cwt/test_b/.
10:30-15:00: as the big-runner version but the run off the open only needs 1.5 daily ATRs; short the failed 38-62% bounce.
Exit: t1s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [1030, 1500].
Signal code: cwt_live_lib.py (ports of the scored kernels). Parity: verify.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["B1-a1.5-trigT2-t1s1-guest"]


def mask(df):
    return L.b1(df, a=1.5, trig=2)
