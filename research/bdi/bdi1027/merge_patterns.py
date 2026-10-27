"""Merge a nightly patterns_<date>.csv into research/bdi/patterns.csv, idempotent by date: rows of the dates in the new
file are replaced, other rows kept; columns of patterns.csv kept. Usage: python merge_patterns.py <new.csv>.
Educational only - not financial advice."""
import csv
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "patterns.csv"
new = Path(sys.argv[1])
with MAIN.open(newline="") as f:
    r = csv.DictReader(f); cols = r.fieldnames; old = list(r)
with new.open(newline="") as f:
    add = list(csv.DictReader(f))
dates = {x["date"] for x in add}
keep = [x for x in old if x["date"] not in dates]
rows = keep + [{c: x.get(c, "") for c in cols} for x in add]
rows.sort(key=lambda x: x["date"])          # stable: within a date the original order is kept
with MAIN.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(f"{MAIN}: {len(old)} -> {len(rows)} rows (replaced {len(old) - len(keep)}, added {len(add)} for {sorted(dates)})")
