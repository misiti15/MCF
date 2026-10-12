"""Testing 2 (owner-directed forward test, 2026-10-12): Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill].
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B3-LPD-p0.1-Vlowvol-sidelong-t05s1-full (id 142), research/bdi/cwt/test_b/.
09:50-15:00: price pokes 0.1+ ATR under yesterday's low on below-average volume, then closes back above it within 3 bars; buy. Fill: over the 4-per-family cap.
Exit: t05s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B3-LPD-p0.1-Vlowvol-sidelong-t05s1-full"]


def mask(df):
    return L.b3(df, level='PD', p=0.10, lowvol=True, side='long')
