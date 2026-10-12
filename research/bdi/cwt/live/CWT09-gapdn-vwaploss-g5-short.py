"""Testing 2 (owner-directed forward test, 2026-10-12): Gap-Down VWAP Loss Short (5% gap).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package A, configuration A7 gap<=-5 E=out T1 t1s05 guest (id 339), research/bdi/cwt/test_a/.
10:30-15:00: a stock that gapped down 5%+ (no earnings within 4 days) traded back above VWAP during 09:35-10:30; from 10:30 the first close back below VWAP; short with a half-R stop.
Exit: t1s05 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [1030, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "t1s05"
LAYERS = ["A7 gap<=-5 E=out T1 t1s05 guest"]


def mask(df):
    return L.a7(df, gap=5, trig=1)
