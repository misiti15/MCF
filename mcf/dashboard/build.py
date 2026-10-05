"""Build the static progress dashboard (single self-contained HTML file) from the journal."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..journal import Journal

TEMPLATE = Path(__file__).with_name("template.html")


def _pack(trades: pd.DataFrame) -> list[list]:
    if trades.empty:
        return []
    et = pd.to_datetime(trades["entry_time"])
    xt = pd.to_datetime(trades["exit_time"])
    return [
        [r.symbol, r.strategy, int(r.side), str(r.date), e.strftime("%H:%M"), x.strftime("%H:%M"),
         round(float(r.entry), 4), round(float(r.exit), 4), r.exit_reason,
         round(float(r.r_multiple), 4), round(float(r.pnl), 2), int(r.shares)]
        for r, e, x in zip(trades.itertuples(), et, xt)
    ]


def build(journal_path: str | Path, out: str | Path) -> Path:
    j = Journal(journal_path)
    runs = j.runs()
    sources = []
    for _, run in runs.sort_values("id", ascending=False).iterrows():
        tr = j.trades(run_id=int(run["id"]))
        label = run["label"] or f"run {run['id']}"
        sources.append({
            "id": int(run["id"]), "kind": run["kind"], "label": label,
            "created": run["created_at"][:16].replace("T", " "), "trades": _pack(tr),
        })
    # paper runs first: they are the source of truth once live
    sources.sort(key=lambda s: (s["kind"] != "paper", -s["id"]))
    payload = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "sources": sources}
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out
