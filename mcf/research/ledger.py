"""Change ledger: every approved setup/exit change, re-checkable against all later changes.

research/ledger.jsonl holds one JSON object per approved change:
  {"id", "date", "title", "patch": {"strategies.orb.enabled": [before, after], ...},
   "evidence": [paths], "metrics_at_approval": {...}, "approved_by": "owner"}

`python -m mcf.research.ledger check [--days 30]` runs the JOINT portfolio (all enabled setups sharing the real
slot/position limits) on the latest stored sessions, then once per ledger entry with that entry reverted.
If reverting a past change improves expectancy or total R, the change is flagged: it conflicts with later
changes or has decayed, so it is reviewed instead of silently stacked on. Results go to research/ledger_check.json.
Educational only — not financial advice.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import pandas as pd

LEDGER = Path(__file__).resolve().parents[2] / "research" / "ledger.jsonl"


def entries() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def _set(cfg: dict, dotted: str, value):
    keys = dotted.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    if value is None and keys[-1] in d and dotted.count(".") == 1:
        d.pop(keys[-1])          # a whole setup that did not exist before
    else:
        d[keys[-1]] = value


def revert(cfg: dict, entry: dict) -> dict:
    out = copy.deepcopy(cfg)
    for path, (before, _after) in entry["patch"].items():
        _set(out, path, before)
    return out


def portfolio(cfg: dict, data: dict, start: str, end: str) -> dict:
    """Joint backtest with the real account limits (slots, per-setup sleeves, one position per symbol)."""
    from ..analytics.metrics import summarize
    from ..backtest.engine import Backtester
    from ..strategies.setups import build_strategies

    tr = Backtester(build_strategies(cfg), cfg).run(data)
    if len(tr):
        d = pd.to_datetime(tr["date"])
        tr = tr[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))]
    s = summarize(tr) if len(tr) else {"trades": 0}
    keep = ("trades", "win_rate", "expectancy_r", "profit_factor", "total_pnl", "max_drawdown", "green_day_rate")
    out = {k: (round(float(s[k]), 4) if isinstance(s.get(k), (int, float)) else s.get(k)) for k in keep if k in s}
    out["total_r"] = round(float(tr["r_multiple"].sum()), 2) if len(tr) else 0.0
    return out


def check(days: int = 30) -> dict:
    from ..config import load_config
    from ..data.store import BarStore

    cfg = load_config()
    store = BarStore(cfg["data"]["cache_dir"])
    syms = store.symbols()
    probe = store.load("SPY") if "SPY" in syms else store.load(syms[0])
    dates = sorted(set(probe.index.date))
    start, end = str(dates[-days]), str(dates[-1])
    warm = str(dates[max(0, len(dates) - days - 25)])           # history for ATR / rvol baselines
    data = store.load_many(syms, start=warm)
    base = portfolio(cfg, data, start, end)
    rows = []
    for e in entries():
        alt = portfolio(revert(cfg, e), data, start, end)
        flag = (alt.get("total_r", 0) > base.get("total_r", 0)) and (alt.get("expectancy_r", 0) > base.get("expectancy_r", 0))
        rows.append({"id": e["id"], "title": e["title"], "reverted": alt,
                     "verdict": "FLAG: reverting improves the portfolio — review" if flag else "ok: still adds value"})
    res = {"window": [start, end], "current": base, "entries": rows}
    (LEDGER.parent / "ledger_check.json").write_text(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "list"])
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    if a.cmd == "list":
        for e in entries():
            print(e["date"], e["id"], e["title"])
    else:
        print(json.dumps(check(a.days), indent=1, default=str))
