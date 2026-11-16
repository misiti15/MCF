"""Shadow scorecard per account (owner 2026-11-16), written by the EOD job next to the live scorecard:
<state>/reports/shadow_scorecard.json, read by the setup leaderboard's "Shadow / replay" band (docs/live/index.html).

Per setup: the sessions it ran live in this account (shadow-of-live markers), the sessions it ran in shadow only, its
shadow trades and R after costs (LR8), the haircut and session weight of its family's trust-check tier
(mcf/research/shadow_calib.py; the repo's nightly research/shadow/summary.json when it has the family, else this
account's own check, else the lower tier) and its shadow-vs-live gap on matched trades. Shadow is not live trading.
Educational only - not financial advice."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..costs import cost_r
from ..execution.shadow import shadow_run_id
from ..research import effective as E
from ..research import shadow_calib as C

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = ROOT / "research" / "shadow" / "summary.json"


def _info(x) -> dict:
    try:
        v = json.loads(x) if x else {}
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


def build(journal, account: str = "primary", cfg_eff: dict | None = None, global_summary: dict | None = None) -> dict:
    ce = cfg_eff or E.load()
    if global_summary is None and GLOBAL.exists():
        try:
            global_summary = json.loads(GLOBAL.read_text())
        except ValueError:
            global_summary = None
    rid = shadow_run_id(journal)
    card = {"generated": pd.Timestamp.now(tz="America/New_York").isoformat(timespec="minutes"), "account": account,
            "weights": {k: ce[k] for k in ("live_weight", "tiers", "below_weight", "uncalibrated_weight",
                                           "haircut_extra_r", "on_deck_min_live_sessions")},
            "calibration": None, "setups": {},
            "note": "Shadow = the setup's rules on the live polls with no orders; not live trading. Live wins any "
                    "disagreement. Educational only - not financial advice."}
    if rid is None:
        return card
    con = journal.db
    sig = pd.read_sql("SELECT day, strategy, status, info FROM signals WHERE run_id=? AND status='shadow_session'",
                      con, params=[rid])
    days: dict[str, dict[str, set]] = {}
    for r in sig.itertuples():
        m = _info(r.info).get("mode", "of_live")
        d = days.setdefault(str(r.strategy), {"of_live": set(), "only": set()})
        d.setdefault(m, set()).add(str(r.day))
    tr = journal.trades(run_id=rid)
    tr = tr[tr["exit_time"].notna()] if len(tr) else tr
    local = C.summarize(C.journal_rows(con, account), ce)
    card["calibration"] = {"overall": local.get("overall"), "families": local.get("families")}
    if len(tr):
        tr = tr.assign(rc=cost_r(tr).astype(float), mode=tr["meta"].astype(str).str.extract(r"mode=(\w+)")[0].fillna("of_live"))
    names = set(days) | (set(tr["strategy"].astype(str)) if len(tr) else set())
    for s in sorted(names):
        g = tr[tr["strategy"].astype(str) == s] if len(tr) else tr
        fam = C.family_of(s)
        gf = ((global_summary or {}).get("families") or {}).get(fam)
        tier_, w, hc = C.family_weight({"families": {fam: gf}} if gf else local, s, ce)
        n = int(len(g))
        avg = float(g["rc"].mean()) if n else None
        gap = (local.get("setups") or {}).get(s) or {}
        d = days.get(s, {"of_live": set(), "only": set()})
        live_days = sorted(d.get("of_live", set()))
        only_days = sorted(d.get("only", set()) - set(live_days))
        card["setups"][s] = {
            "family": fam, "live_days": live_days, "shadow_days": only_days,
            "trades": n, "trades_only": int((g["mode"] == "only").sum()) if n else 0,
            "trades_of_live": int((g["mode"] == "of_live").sum()) if n else 0,
            "total_r": round(float(g["rc"].sum()), 3) if n else 0.0, "avg_r": None if avg is None else round(avg, 4),
            "n_win": int((g["rc"] > 0).sum()) if n else 0,
            "haircut_r": hc, "avg_r_haircut": None if avg is None else round(avg - hc, 4),
            "tier": tier_, "weight": w, "gap_r": gap.get("gap_r"), "gap_n": gap.get("gap_n") or 0,
            "match": gap.get("match"), "first": str(g["date"].min()) if n else None,
            "last": str(g["date"].max()) if n else None}
    return card


def save(card: dict, state_dir: str | Path) -> Path:
    p = Path(state_dir) / "reports" / "shadow_scorecard.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(card, indent=1, default=str))
    return p
