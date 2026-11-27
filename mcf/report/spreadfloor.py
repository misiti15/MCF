"""SPREADFLOOR log summary (research/spreadfloor_1127): per setup, the entries tagged by the shadow logger
(mcf/execution/spreadfloor.py), their median stop distance in spreads / bp / cents, how many a 6- / 8-spread floor
WOULD have skipped, and - where the lot has a closed trade in the journal - average R of would-skip vs kept lots.

R: after costs (pnl_adj / risk $) when the trade row carries pnl_adj, else the journaled r_multiple (column `r_basis`
says which). Read only: never writes the journal. Evidence for a later pre-registered test, not a verdict; check
research/ledger.jsonl for rule changes inside the window before reading the numbers.

    python -m mcf.report.spreadfloor data/journal.db [more.db ...] [--json out.json]

Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys

import pandas as pd

from ..execution.spreadfloor import FLOORS, KEY

DISCLAIMER = "Educational only - not financial advice"


def _tag(x):
    try:
        v = json.loads(x) if x else {}
        t = v.get(KEY) if isinstance(v, dict) else None
        return t if isinstance(t, dict) else None
    except (TypeError, ValueError):
        return None


def load(path: str) -> pd.DataFrame:
    """Tagged entries (signals status submitted / dry_run of paper runs) joined to their closed trade R."""
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        sig = pd.read_sql("SELECT s.id, s.day, s.symbol, s.strategy, s.side, s.status, s.broker_order_id, s.info "
                          "FROM signals s JOIN runs r ON r.id=s.run_id WHERE r.kind='paper' "
                          "AND s.status IN ('submitted','dry_run')", db)
        tr = pd.read_sql("SELECT t.* FROM trades t JOIN runs r ON r.id=t.run_id WHERE r.kind='paper'", db)
    finally:
        db.close()
    sig["tag"] = sig["info"].map(_tag)
    sig = sig[sig["tag"].notna()].copy()
    if sig.empty:
        return pd.DataFrame()
    tags = pd.DataFrame(list(sig["tag"]), index=sig.index)
    out = pd.concat([sig.drop(columns=["info", "tag"]), tags], axis=1)
    out["R"], out["r_basis"] = float("nan"), None
    if not tr.empty and "broker_order_id" in tr:
        tr = tr.loc[:, ~tr.columns.duplicated()]
        risk = (tr["entry"] - tr["stop"]).abs() * tr["shares"].fillna(0)
        if "pnl_adj" in tr:
            r = (tr["pnl_adj"] / risk.where(risk > 0)).where(tr["pnl_adj"].notna())
            tr["R"] = r.fillna(tr["r_multiple"])
            tr["r_basis"] = r.notna().map({True: "after_costs", False: "r_multiple"})
        else:
            tr["R"], tr["r_basis"] = tr["r_multiple"], "r_multiple"
        by = tr.dropna(subset=["broker_order_id"]).groupby(tr["broker_order_id"].astype(str))
        rr = by["R"].sum(min_count=1)                    # scale-outs: several trade rows per lot
        rb = by["r_basis"].first()
        oid = out["broker_order_id"].astype(str)
        out["R"] = oid.map(rr)
        out["r_basis"] = oid.map(rb)
    return out


def summarize(df: pd.DataFrame) -> dict:
    res = {"disclaimer": DISCLAIMER, "entries": int(len(df)), "setups": []}
    if df.empty:
        return res
    q = df[df["quote"] == True]  # noqa: E712
    res.update(with_quote=int(len(q)), days=sorted(df["day"].astype(str).unique().tolist()))
    for f in FLOORS:
        c = f"would_skip_{f}"
        res[f"would_skip_{f}"] = int(q[c].fillna(False).astype(bool).sum()) if c in q else 0
    for name, g in q.groupby("strategy"):
        row = {"setup": name, "n": int(len(g)), "days": int(g["day"].nunique()),
               "med_stop_spreads": _r(g["stop_spreads"].median()), "med_stop_bps": _r(g["stop_bps"].median()),
               "med_stop_c": _r(g["stop_c"].median()), "med_spread_bps": _r(g["spread_bps"].median())}
        for f in FLOORS:
            m = g[f"would_skip_{f}"].fillna(False).astype(bool)
            row[f"skip{f}_n"] = int(m.sum())
            row[f"skip{f}_share"] = _r(m.mean())
            row[f"skip{f}_avgR"] = _r(g.loc[m, "R"].mean())
            row[f"kept{f}_avgR"] = _r(g.loc[~m, "R"].mean())
        row["closed"] = int(g["R"].notna().sum())
        res["setups"].append(row)
    res["setups"].sort(key=lambda r: -r["n"])
    return res


def _r(x, k=3):
    return None if x is None or pd.isna(x) else round(float(x), k)


def render(res: dict) -> str:
    lines = [DISCLAIMER, f"SPREADFLOOR log: {res['entries']} tagged entries, {res.get('with_quote', 0)} with a quote, "
             + ", ".join(f"would skip @{f} spreads: {res.get(f'would_skip_{f}', 0)}" for f in FLOORS)]
    if not res["setups"]:
        return "\n".join(lines + ["(no tagged entries yet)"])
    hdr = ["setup", "n", "days", "medSpr", "medBp", "medC"] + [f"{p}{f}" for f in FLOORS for p in ("sk", "skR", "keepR")]
    lines.append(" ".join(f"{h:>8}" for h in hdr))
    for r in res["setups"]:
        vals = [r["setup"][:8], r["n"], r["days"], r["med_stop_spreads"], r["med_stop_bps"], r["med_stop_c"]]
        for f in FLOORS:
            vals += [r[f"skip{f}_n"], r[f"skip{f}_avgR"], r[f"kept{f}_avgR"]]
        lines.append(" ".join(f"{('-' if v is None else v)!s:>8}" for v in vals))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("journals", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    frames = [d for d in (load(p) for p in a.journals) if not d.empty]
    res = summarize(pd.concat(frames, ignore_index=True) if frames else pd.DataFrame())
    print(render(res))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
