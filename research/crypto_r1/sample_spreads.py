"""Sample Alpaca historical crypto quotes -> median relative spread per pair and year (cost-model input).

Seeded random timestamps inside FIT/CHECK only (before the locked block starts, docs/CRYPTO_PLAN.md); one quote per
timestamp (the first quote at/after it, kept only if within 10 minutes). GET on the public market-data API only.
    python research/crypto_r1/sample_spreads.py
Educational only — not financial advice.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.crypto import data as D  # noqa: E402
from mcf.crypto.splits import LOCKED_START  # noqa: E402

PER_YEAR = 16
SEED = 20261126
OUT = Path(__file__).with_name("spreads.json")


def one(pair: str, ts: pd.Timestamp):
    try:
        js = D._get("quotes", {"symbols": f"{pair}/USD", "start": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 1})
    except Exception:  # noqa: BLE001
        return None
    q = (js.get("quotes") or {}).get(f"{pair}/USD") or []
    if not q:
        return None
    q = q[0]
    t = pd.Timestamp(q["t"])
    if (t - ts) > pd.Timedelta(minutes=10) or q["ap"] <= 0 or q["bp"] <= 0 or q["ap"] < q["bp"]:
        return None
    mid = (q["ap"] + q["bp"]) / 2
    return pair, t.year, (q["ap"] - q["bp"]) / mid


def main() -> int:
    rng = np.random.default_rng(SEED)
    jobs = []
    end = pd.Timestamp(LOCKED_START, tz="UTC")
    for pair in D.PAIRS:
        for y in range(2023, end.year + 1):
            lo, hi = pd.Timestamp(f"{y}-01-01", tz="UTC"), min(pd.Timestamp(f"{y+1}-01-01", tz="UTC"), end)
            span = int((hi - lo).total_seconds() // 60)
            for m in rng.integers(0, span, PER_YEAR):
                jobs.append((pair, lo + pd.Timedelta(minutes=int(m))))
    with ThreadPoolExecutor(4) as ex:
        res = [r for r in ex.map(lambda a: one(*a), jobs) if r]
    df = pd.DataFrame(res, columns=["pair", "year", "rel"])
    med = df.groupby(["pair", "year"])["rel"].median()
    cnt = df.groupby(["pair", "year"])["rel"].size()
    out = {"median_rel_spread": {}, "n": {}, "seed": SEED, "per_year": PER_YEAR,
           "window_end_exclusive": str(end.date()),
           "note": "one quote per seeded random minute; Alpaca venue quotes; Educational only - not financial advice."}
    for (p, y), v in med.items():
        if cnt[(p, y)] >= 5:
            out["median_rel_spread"].setdefault(p, {})[str(y)] = round(float(v), 6)
            out["n"].setdefault(p, {})[str(y)] = int(cnt[(p, y)])
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(med.unstack().round(5).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
