"""regime1022 Part D: write docs/live/regimes.json from classes.csv (2-year as-run backtest, by hindsight market
condition), one entry per live setup name that was scored, then validate it (mcf.report.regimes). Best / worst are
taken among conditions with >= 30 trades. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys

import pandas as pd

from rc import HERE, ROOT
from regime import DEFS, LABELS

sys.path.insert(0, str(ROOT))
from mcf.report.regimes import PATH, validate  # noqa: E402


def main():
    C = pd.read_csv(HERE / "classes.csv")
    out = {}
    for _, c in C.iterrows():
        br = json.loads(c["by_regime"])
        by = {k: {"trades": int(br[k]["trades"] or 0),
                  "avg_r": None if br[k]["avg_r"] is None else round(float(br[k]["avg_r"]), 3)} for k in LABELS}
        sc = {k: v["avg_r"] for k, v in by.items() if v["avg_r"] is not None and v["trades"] >= 30}
        if not sc:
            continue
        best, worst = max(sc, key=sc.get), min(sc, key=sc.get)
        for name in str(c["names"]).split(","):
            out[name] = {"best": best, "worst": worst, "by_regime": by, "class": c["class"],
                         "avg_r": round(float(c["avg_r"]), 3), "trades": int(c["n"]),
                         "source": "2-year as-run backtest"}
    d = {"generated": "2026-10-22", "labels": list(LABELS), "definitions": DEFS,
         "note": "Hindsight label of each session from SPY's regular session; per-setup avg R after costs on the open "
                 "two-year history (2024-10..2026-10-07, locked block excluded), refire chain + lot cap 3. "
                 "research/bdi/regime1022. Educational only - not financial advice.",
         "setups": dict(sorted(out.items()))}
    err = validate(d)
    assert not err, err
    PATH.write_text(json.dumps(d, indent=1) + "\n")
    print(len(out), "setups ->", PATH)


if __name__ == "__main__":
    main()
