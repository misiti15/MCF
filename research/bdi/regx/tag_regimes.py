"""REGX (owner yes 2026-11-21, display only): add the REGX reliability tag of each setup's dashboard "Best conditions"
rating (table.csv, scheme DASH: trustworthy / weak / false) and the "hindsight (known at close)" label to
docs/live/regimes.json, then validate it. Nothing here changes which trades are taken. Idempotent.

    python research/bdi/regx/tag_regimes.py

Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.report.regimes import HINDSIGHT, PATH, validate  # noqa: E402


def tag(d: dict, table: pd.DataFrame) -> dict:
    t = table[table.scheme.eq("DASH")].drop_duplicates("setup").set_index("setup")
    d["hindsight"] = HINDSIGHT
    d["regx"] = {"tagged": "2026-11-21", "source": "research/bdi/regx (table.csv, scheme DASH)",
                 "note": "REGX reliability of the best / worst rating: trustworthy = TRAIN t >= 2 and VALID t >= 1 (w/o "
                         "best day too) and live agrees; weak = below those bars; false = best / worst flips out of "
                         "sample. The labels are hindsight (SPY at the close): never an entry filter. Setups without a "
                         "tag were not in REGX scope."}
    for name, s in d["setups"].items():
        if name in t.index:
            r = t.loc[name]
            s["regx"] = {"verdict": str(r.verdict), "reason": str(r.reason), "source": str(r.source)}
        else:
            s.pop("regx", None)
    return d


def main():
    d = tag(json.loads(PATH.read_text()), pd.read_csv(HERE / "table.csv"))
    err = validate(d)
    assert not err, err
    PATH.write_text(json.dumps(d, indent=1) + "\n")
    v = pd.Series([s["regx"]["verdict"] for s in d["setups"].values() if "regx" in s]).value_counts().to_dict()
    print(PATH, "REGX tags:", v)


if __name__ == "__main__":
    main()
