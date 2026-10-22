"""docs/live/regimes.json: each setup's best / worst market condition on its 2-year as-run backtest (research/bdi/
regime1022). Display only - the dashboard's "Best conditions" column and the setup drill-down read it; nothing here
changes which trades are taken. `python -m mcf.report.regimes` validates the file. Educational only - not financial
advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "docs" / "live" / "regimes.json"
LABELS = ("Bull", "Bear", "Choppy", "Quiet")
CLASSES = ("regime specialist", "all-weather", "loser")


def validate(d: dict) -> list[str]:
    """Return a list of schema problems (empty = valid)."""
    err = []
    for k in ("generated", "labels", "definitions", "setups"):
        if k not in d:
            err.append(f"missing key {k}")
    if err:
        return err
    if tuple(d["labels"]) != LABELS:
        err.append(f"labels must be {LABELS}")
    if set(d["definitions"]) != set(LABELS) or not all(isinstance(v, str) and v for v in d["definitions"].values()):
        err.append("definitions must define every label")
    if not isinstance(d["setups"], dict) or not d["setups"]:
        err.append("setups must be a non-empty object")
        return err
    for name, s in d["setups"].items():
        for k in ("best", "worst", "by_regime", "class", "source"):
            if k not in s:
                err.append(f"{name}: missing {k}")
        if err:
            continue
        if s["best"] not in LABELS or s["worst"] not in LABELS:
            err.append(f"{name}: best/worst must be a label")
            continue
        if s["class"] not in CLASSES:
            err.append(f"{name}: class {s['class']!r}")
        br = s["by_regime"]
        if set(br) != set(LABELS):
            err.append(f"{name}: by_regime must have every label")
            continue
        for lab, v in br.items():
            if not isinstance(v.get("trades"), int) or v["trades"] < 0:
                err.append(f"{name}/{lab}: trades")
            if v.get("avg_r") is not None and not isinstance(v["avg_r"], (int, float)):
                err.append(f"{name}/{lab}: avg_r")
        scored = {k: v["avg_r"] for k, v in br.items() if v.get("avg_r") is not None and v["trades"] >= 30}
        if scored and (br[s["best"]]["avg_r"] != max(scored.values()) or br[s["worst"]]["avg_r"] != min(scored.values())):
            err.append(f"{name}: best/worst do not match by_regime")
    return err


def main() -> int:
    err = validate(json.loads(PATH.read_text()))
    print("\n".join(err) if err else f"{PATH.name}: ok")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
