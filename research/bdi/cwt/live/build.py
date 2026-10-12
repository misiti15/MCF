"""Write the Testing 2 lab modules (research/bdi/cwt/live/<NAME>.py) and print the config/account_testing2.yaml
strategy blocks and the config/setup_names.yaml entries from selection.py. Educational only - not financial advice.

    python research/bdi/cwt/live/build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from selection import S  # noqa: E402

TEMPLATE = '''"""Testing 2 (owner-directed forward test, 2026-10-12): {title}.
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package {pkg}, configuration {cfg} (id {cid}), research/bdi/cwt/test_{pkgl}/.
{what}
Exit: {geom} (R = 0.25 x daily ATR, flat 15:55) via LabStrategy. Window in config/account_testing2.yaml: {window}.
Signal code: cwt_live_lib.py (ports of the scored kernels). Parity: verify.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "{side}"
GEOM = "{geom}"
LAYERS = ["{cfg}"]


def mask(df):
    return L.{call}
'''


def main():
    for s in S:
        (HERE / f"{s['name']}.py").write_text(TEMPLATE.format(pkgl=s["pkg"].lower(), **s))
    print(len(S), "modules written")


if __name__ == "__main__":
    main()
