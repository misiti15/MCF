"""Summarise data/mining.json -> mining_summary.json (committed, small) and printed tables for NOTES.md.
Popularity = documents (posts + comments) mentioning the item; weighted = sum of log1p(score). Trend = mentions per
10,000 documents of that year in the day-trading core subs (Daytrading, algotrading, RealDayTrading, Trading), 2019
vs 2025 and the slope over years. Educational only - not financial advice."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(HERE))
from mine import TAX  # noqa: E402

CORE = {"Daytrading", "algotrading", "RealDayTrading", "Trading"}


def main():
    M = json.load(open(HERE / "data" / "mining.json"))
    label = {k: l for k, l, _, _ in TAX}
    group = {k: g for k, _, g, _ in TAX}
    docs = defaultdict(int)
    docs_core_year = defaultdict(int)
    for d in M["docs"]:
        docs[d["sub"]] += d["n"]
        if d["sub"] in CORE:
            docs_core_year[d["year"]] += d["n"]
    tot = defaultdict(lambda: {"docs": 0, "score": 0, "logscore": 0.0, "core_docs": 0, "by_sub": defaultdict(int),
                               "core_year": defaultdict(int)})
    for r in M["tab"]:
        t = tot[r["key"]]
        t["docs"] += r["docs"]; t["score"] += r["score"]; t["logscore"] += r["logscore"]
        t["by_sub"][r["sub"]] += r["docs"]
        if r["sub"] in CORE:
            t["core_docs"] += r["docs"]
            t["core_year"][r["year"]] += r["docs"]
    years = sorted(docs_core_year)
    rows = []
    for k, t in tot.items():
        rate = [1e4 * t["core_year"].get(y, 0) / docs_core_year[y] for y in years]
        slope = float(np.polyfit(np.arange(len(years)), rate, 1)[0]) if len(years) > 2 else 0.0
        v = M["verdict"].get(k, [0, 0, 0, 0])
        rows.append({"key": k, "label": label[k], "group": group[k], "docs": t["docs"], "core_docs": t["core_docs"],
                     "logscore": round(t["logscore"]), "score": t["score"],
                     "rate_per10k_core": dict(zip(map(str, years), [round(x, 1) for x in rate])),
                     "trend_slope_per_year": round(slope, 2),
                     "trend_rel": round((rate[-1] - rate[0]) / max(1e-9, (rate[0] + rate[-1]) / 2), 2),
                     "by_sub": dict(sorted(t["by_sub"].items(), key=lambda x: -x[1])),
                     "verdict_sent": {"pos": v[0], "neg": v[1], "regime": v[2], "decay": v[3]},
                     "neg_share": round(v[1] / max(1, v[0] + v[1]), 3)})
    rows.sort(key=lambda r: -r["logscore"])
    out = {"docs_total": sum(docs.values()), "docs_by_sub": dict(docs), "docs_core_by_year": {str(k): v for k, v in docs_core_year.items()},
           "items": rows}
    json.dump(out, open(HERE / "mining_summary.json", "w"), indent=1)
    print("docs", out["docs_total"], dict(docs))
    print("core docs/year", dict(docs_core_year))
    print(f"{'#':>2} {'key':15} {'docs':>7} {'core':>6} {'logsc':>7} " + " ".join(f"{y}" for y in years) + "  slope  pos  neg negsh regime decay")
    for i, r in enumerate(rows, 1):
        print(f"{i:>2} {r['key']:15} {r['docs']:>7} {r['core_docs']:>6} {r['logscore']:>7} " +
              " ".join(f"{r['rate_per10k_core'][str(y)]:>4.0f}" for y in years) +
              f" {r['trend_slope_per_year']:>6.1f} {r['verdict_sent']['pos']:>4} {r['verdict_sent']['neg']:>4} {r['neg_share']:>5} {r['verdict_sent']['regime']:>5} {r['verdict_sent']['decay']:>5}")


if __name__ == "__main__":
    main()
