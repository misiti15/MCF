# WORKBENCH VARIANT CWT14-failbrk-orl-p10-long-WB1 (research only, not enabled in any account)
# parent: CWT14-failbrk-orl-p10-long (research/bdi/cwt/live/CWT14-failbrk-orl-p10-long.py); changed ONE part: r_atr_frac 0.25 -> 0.3; 2026-11-16
# Next: backtest under docs/RESEARCH_RULES.md; testing arena only with the owner's yes. Educational only - not financial advice.
"""Testing 2 (owner-directed forward test, 2026-10-12): Failed Opening-Range-Low Break Long (0.1 ATR) [fill].
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package B, configuration B3-LOR-p0.1-Vany-sidelong-t05s1-guest (id 179), research/bdi/cwt/test_b/.
09:50-12:00: price pokes 0.1+ ATR under the 09:30-10:00 low, then closes back above it within 3 bars; buy. Fill: over the 4-per-family cap.
Exit: t05s1 (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: [950, 1200].
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["B3-LOR-p0.1-Vany-sidelong-t05s1-guest"]


def mask(df):
    return L.b3(df, level='OR', p=0.10, lowvol=False, side='long')
