"""Build data/marcoflow.sqlite from the MarcoFlow Folder2_Data CSV export.

Usage: python scripts/import_marcoflow.py [Folder2_Data dir or .zip] [--out data/marcoflow.sqlite]
       (default source: data/marcoflow_export/Folder2_Data.zip)

- One table per CSV; SignalObservation_*.csv parts are concatenated into one table.
- Column types come from export_manifest.json (Postgres types -> SQLite affinities).
- Row counts are checked against the manifest; exits non-zero on mismatch.
Timestamps stay as the exported UTC ISO strings (sortable, comparable as text).
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

csv.field_size_limit(sys.maxsize)

TYPE_MAP = {
    "integer": "INTEGER", "bigint": "INTEGER", "smallint": "INTEGER", "boolean": "INTEGER",
    "double precision": "REAL", "real": "REAL", "numeric": "REAL",
}
INDEXES = [
    ("PaperTrade", ["entryTime", "symbol"]),
    ("SignalObservation", ["observedAt", "symbol"]),
    ("PaperTrade", ["observationId"]),
    ("SignalObservation", ["source", "status"]),
]


def convert(value: str, sqltype: str):
    if value == "":
        return None
    if sqltype == "INTEGER":
        if value in ("true", "t", "True"):
            return 1
        if value in ("false", "f", "False"):
            return 0
        try:
            return int(float(value))
        except ValueError:
            return value
    if sqltype == "REAL":
        try:
            return float(value)
        except ValueError:
            return value
    return value


def files_for(table: str, src: Path) -> list[Path]:
    exact = src / f"{table}.csv"
    if exact.exists():
        return [exact]
    return sorted(src.glob(f"{table}_*.csv"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path, nargs="?", default=Path("data/marcoflow_export/Folder2_Data.zip"))
    ap.add_argument("--out", type=Path, default=Path("data/marcoflow.sqlite"))
    args = ap.parse_args(argv)

    if args.src.suffix == ".zip":
        tmp = tempfile.mkdtemp(prefix="marcoflow_")
        with zipfile.ZipFile(args.src) as z:
            z.extractall(tmp)
        found = list(Path(tmp).rglob("export_manifest.json"))
        if not found:
            raise SystemExit("export_manifest.json not found in zip")
        args.src = found[0].parent
    manifest = json.loads((args.src / "export_manifest.json").read_text())["tables"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        args.out.unlink()
    con = sqlite3.connect(args.out)
    ok = True
    for table, meta in manifest.items():
        cols = [(c["name"], TYPE_MAP.get(c["type"], "TEXT")) for c in meta["columns"]]
        ddl = ", ".join(f'"{n}" {t}' + (" PRIMARY KEY" if n == "id" else "") for n, t in cols)
        con.execute(f'CREATE TABLE "{table}" ({ddl})')
        files = files_for(table, args.src)
        n = 0
        for f in files:
            with open(f, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                missing = {c for c, _ in cols} - set(reader.fieldnames or [])
                if missing:
                    print(f"  ! {f.name} missing columns {missing}")
                    ok = False
                rows = ([convert(r.get(c, ""), t) for c, t in cols] for r in reader)
                q = f'INSERT INTO "{table}" VALUES ({",".join("?" * len(cols))})'
                before = con.total_changes
                con.executemany(q, rows)
                n += con.total_changes - before
        if not files and meta["rows"]:
            status = "WARN: no CSV in export"
        else:
            status = "OK" if n == meta["rows"] else "MISMATCH"
            ok &= n == meta["rows"]
        print(f"{table:<24} {n:>8} rows  (manifest {meta['rows']:>8})  {status}  <- {', '.join(f.name for f in files) or 'no file'}")
    for table, cols in INDEXES:
        name = f"idx_{table}_{'_'.join(cols)}"
        con.execute(f'CREATE INDEX IF NOT EXISTS "{name}" ON "{table}" ({", ".join(chr(34) + c + chr(34) for c in cols)})')
    con.commit()
    con.execute("ANALYZE")
    con.close()
    print(f"\nwrote {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
