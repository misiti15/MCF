"""Per-setup scorecard over the last N sessions (owner 2026-10-09: 4 sessions before a removal
decision; was 3).

Live (paper) results per setup next to what its backtest expected (config/validation.json, or a setup's own
expected_r in config/scorecard_expectations.json). Few trades decide nothing on their own: the verdict only flags
setups to review. Written to <state>/reports/scorecard.json for the live page and the EOD email.
Educational only — not financial advice.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def _expected() -> dict[str, float]:
    out: dict[str, float] = {}
    v = ROOT / "config" / "validation.json"
    if v.exists():
        for k, x in json.loads(v.read_text()).get("setups", {}).items():
            if x.get("apr_jun_exp_r") is not None:
                out[k] = float(x["apr_jun_exp_r"])
    e = ROOT / "config" / "scorecard_expectations.json"
    if e.exists():
        out.update({k: float(x) for k, x in json.loads(e.read_text()).items()})
    return out


def build(trades: pd.DataFrame, sessions: int = 4) -> dict:
    if trades is None or not len(trades):
        return {"sessions": 0, "window": "no trades yet", "setups": []}
    days = sorted(trades["date"].astype(str).unique())[-sessions:]
    tr = trades[trades["date"].astype(str).isin(days)]
    exp = _expected()
    rows = []
    for s, g in tr.groupby("strategy"):
        r = g["r_multiple"].astype(float)
        e = exp.get(s)
        if len(g) < 10:
            verdict = "too few trades"
        elif e is not None and r.mean() < e - 0.15:
            verdict = "below backtest - review"
        elif r.mean() > 0:
            verdict = "positive so far"
        else:
            verdict = "negative so far"
        rows.append({"setup": s, "trades": int(len(g)), "win_rate": round(float((g["pnl"] > 0).mean()), 3),
                     "avg_r": round(float(r.mean()), 3), "pnl": round(float(g["pnl"].sum()), 2),
                     "expected_r": None if e is None else round(e, 3), "verdict": verdict})
    rows.sort(key=lambda x: x["avg_r"], reverse=True)
    from .eod import tod_table   # cumulative time-of-day tracking (owner 2026-10-09), all sessions so far

    tod = tod_table(trades)
    by_time = [{"bucket": x.bucket, "trades": int(x.trades), "win_rate": round(float(x.win), 3),
                "avg_r": round(float(x.avg_r), 3), "pnl": round(float(x.pnl), 2)} for x in tod.itertuples()]
    return {"sessions": len(days), "window": f"{days[0]} to {days[-1]}", "setups": rows, "by_time": by_time,
            "note": "Paper results; a scorecard flags setups to review, it does not prove or disprove an edge."}


def save(card: dict, state_dir: str | Path) -> Path:
    p = Path(state_dir) / "reports" / "scorecard.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(card, indent=1))
    return p
