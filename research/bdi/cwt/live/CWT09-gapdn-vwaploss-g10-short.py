"""Testing 2 (owner-directed forward test, 2026-10-12): Gap-Down VWAP Loss Short (10% gap).
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package A, configuration A7 gap<=-10 E=out T1 S guest (id 365), research/bdi/cwt/test_a/.
10:30-15:00: a stock that gapped down 10%+ (no earnings within 4 days) traded back above VWAP during 09:35-10:30; from 10:30 the first close back below VWAP; short, stop at the 09:30-10:30 high, hold to 15:55.
Exit: structural: stop at the 09:30-10:30 high (stop_price), no target, flat 15:55 via LabStrategy. Window in config/account_testing2.yaml: [1030, 1500].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "short"
GEOM = "S"
LAYERS = ["A7 gap<=-10 E=out T1 S guest"]


def mask(df):
    return L.a7(df, gap=10, trig=1)


def stop_price(f, i):
    return L.a7_stop(f, i)
