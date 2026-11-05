"""Live status snapshot (JSON) for the dashboard: today's MCF session next to MarcoFlow's record.

Written every few minutes by the runner and pushed to the `mcf-data` branch, which the dashboard reads.
Win = P/L > 0 for both systems so the comparison is like-for-like.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REF = Path(__file__).resolve().parents[2] / "config" / "marcoflow_reference.json"
VALIDATION = REF.parent / "validation.json"
DISCLAIMER = "Educational only — not financial advice."


def _stats(tr: pd.DataFrame) -> dict:
    if tr is None or tr.empty:
        return {"trades": 0}
    p = tr["pnl"].astype(float)
    pa = tr["pnl_adj"].astype(float) if "pnl_adj" in tr and tr["pnl_adj"].notna().any() else p
    gw, gl = p[p > 0].sum(), -p[p <= 0].sum()
    out = {
        "trades": int(len(tr)), "wins": int((p > 0).sum()), "win_rate": round(float((p > 0).mean()), 3),
        "pnl": round(float(p.sum()), 2), "pnl_adj": round(float(pa.sum()), 2),
        "avg_pnl": round(float(p.mean()), 2), "avg_r": round(float(tr["r_multiple"].mean()), 3),
        "profit_factor": round(float(gw / gl), 2) if gl > 0 else None,
        "stop_exit_share": round(float((tr["exit_reason"] == "stop").mean()), 3),
    }
    if "slip_bps" in tr and tr["slip_bps"].notna().any():
        out["avg_entry_slip_bps"] = round(float(tr["slip_bps"].astype(float).mean()), 1)
    return out


def _prior_status(runner) -> dict:
    try:
        return json.loads(Path(runner.status_path).read_text()) if getattr(runner, "status_path", None) else {}
    except Exception:
        return {}


def equity_history(prior: dict, acct: str, day: str, account: dict) -> dict:
    """Broker truth per session (owner 2026-11-05: one dollar truth = Alpaca): {date: {equity_close, alpaca_day_pl,
    source}}. Seeded from docs/live/equity_history.json (backfill) and the previous status.json's equity_history; today's
    row = account equity now and equity - last_equity; the previous session's close is reset to Alpaca's last_equity
    (it includes the regulatory fees Alpaca posts after the close), and its day P/L recomputed."""
    from .reconcile_pl import equity_history as stored

    eqh = {d: dict(r) for d, r in stored(acct).items()}
    for d, r in ((prior or {}).get("equity_history") or {}).items():
        if (eqh.get(d) or {}).get("source") != "alpaca" or (r or {}).get("source") == "alpaca":
            eqh[d] = dict(r)
    eq, le = account.get("equity"), account.get("last_equity")
    if eq is None:
        return eqh
    eqh[day] = {"equity_close": eq, "alpaca_day_pl": account.get("day_pl"), "source": "alpaca"}
    prev = max((d for d in eqh if d < day), default=None)
    if prev and le:
        pp = max((d for d in eqh if d < prev), default=None)
        base = (eqh.get(pp) or {}).get("equity_close") if pp else None
        eqh[prev] = {"equity_close": le, "alpaca_day_pl": _f(le - base) if base is not None else eqh[prev].get("alpaca_day_pl"),
                     "source": "alpaca"}
    return eqh


def _since_alpaca(by_day: list[dict]) -> dict:
    """Since-start dollars from the broker: the sum of each session's Alpaca day P/L (journal pnl for a session with no
    stored equity; alpaca_days says how many sessions are broker-measured)."""
    if not by_day:
        return {}
    n = sum(h.get("alpaca_day_pl") is not None for h in by_day)
    tot = sum(h["alpaca_day_pl"] if h.get("alpaca_day_pl") is not None else (h.get("pnl") or 0.0) for h in by_day)
    return {"alpaca_pnl": round(tot, 2), "alpaca_days": n, "sessions": len(by_day)}


def _f(x, nd=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def build_status(runner, now, phase: str) -> dict:
    j, day = runner.journal, str(now.date())
    sig = j.signals(runner.run_id, day)
    trades = j.trades(run_id=runner.run_id)
    today = trades[trades.date == day] if len(trades) else trades
    by_day = []
    if len(trades):
        for d, g in trades.groupby("date"):
            by_day.append({"date": d, **_stats(g)})
    positions = []
    if not runner.dry_run:
        for sym, p in runner.broker.positions().items():
            if sym not in runner.open_strategy:
                continue  # not MCF's
            lots = getattr(runner, "lots", {}).get(sym) or {}
            setups = list(dict.fromkeys(lot.get("strategy", lid) for lid, lot in lots.items()))   # lots keyed by id
            positions.append({"symbol": sym, "strategy": ",".join(setups) if lots else runner.open_strategy.get(sym),
                              "lots": len(lots) or 1, "side": str(p.side).split(".")[-1].lower(),
                              "qty": _f(p.qty, 0), "entry": _f(p.avg_entry_price), "last": _f(p.current_price),
                              "upl": _f(p.unrealized_pl)})
    counts = sig["status"].value_counts().to_dict() if len(sig) else {}
    reasons = (sig[sig.status == "skipped"]["reason"].str.replace(r"\d+(\.\d+)?", "#", regex=True)
               .value_counts().head(8).to_dict() if len(sig) else {})
    recent = []
    for r in sig.tail(40).iloc[::-1].itertuples() if len(sig) else []:
        recent.append({"t": r.ts[11:16], "symbol": r.symbol, "strategy": r.strategy, "side": int(r.side),
                       "ref": _f(r.ref_price), "stop": _f(r.stop), "status": r.status, "reason": r.reason})
    closed = []
    for r in today.itertuples() if len(today) else []:
        closed.append({"symbol": r.symbol, "strategy": r.strategy, "side": int(r.side),
                       "entry_t": str(r.entry_time)[11:16], "exit_t": str(r.exit_time)[11:16],
                       "entry": _f(r.entry), "exit": _f(r.exit), "reason": r.exit_reason, "r": _f(r.r_multiple, 2),
                       "pnl": _f(r.pnl), "slip_bps": _f(getattr(r, "slip_bps", None), 1)})
    try:
        acct = runner.broker.client.get_account() if not runner.dry_run else None
        account = {"equity": _f(acct.equity), "cash": _f(acct.cash)} if acct else {}
    except Exception:
        account = {}
    try:   # Alpaca's own day P/L base: last_equity = the prior session's closing equity
        le = _f(acct.last_equity) if account and getattr(acct, "last_equity", None) is not None else None
        if le:
            account.update(last_equity=le, day_pl=_f(float(acct.equity) - le))
    except Exception:
        pass
    acct_name = (runner.cfg or {}).get("account_name", "primary")
    eqh = equity_history(_prior_status(runner), acct_name, day, account)
    by_day = [dict(h, **{k: (eqh.get(h["date"]) or {}).get(k) for k in ("equity_close", "alpaca_day_pl")}) for h in by_day]
    return {
        "title": "MCF Update",
        "disclaimer": DISCLAIMER,
        "asof": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asof_et": now.strftime("%Y-%m-%d %H:%M ET"),
        "session_date": day, "phase": phase, "dry_run": runner.dry_run,
        "rules": {"no_entry_before": runner.live.get("no_entry_before"), "feed": runner.cfg["data"]["feed"],
                  "max_spread_bps": runner.live.get("max_spread_bps"),
                  "max_spread_risk_frac": runner.live.get("max_spread_risk_frac"),
                  "max_participation": runner.live.get("max_participation"),
                  "strategies": [s.name for s in runner.strategies]},
        "health": {"universe": len(runner.watchlist), **runner.health},
        "account": account,
        "today": {**_stats(today), "alpaca_day_pl": account.get("day_pl"), "signals": int(len(sig)), "by_status": counts, "skip_reasons": reasons,
                  "open_positions": len(positions)},
        "positions": positions,
        "closed": closed,
        "signals": recent,
        "history": by_day[-30:],
        "equity_history": dict(sorted(eqh.items())[-60:]),
        "since_start": {**_stats(trades), **_since_alpaca(by_day)},
        "marcoflow": json.loads(REF.read_text()) if REF.exists() else None,
        "validation": json.loads(VALIDATION.read_text()) if VALIDATION.exists() else None,
    }
