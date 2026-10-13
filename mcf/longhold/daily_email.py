"""S6 daily email after the evening mark (owner 2026-10-12: EOD emails for Primary and S6 only).
Once per day (marker file), only when SMTP secrets exist; failures never stop the run. Educational only."""
from __future__ import annotations

import json
import os
from pathlib import Path

DISCLAIMER = "Educational only - not financial advice."


def _pc(x, d=2):
    return "–" if x is None else f"{x * 100:+.{d}f}%"


def build(status: dict, day: str) -> tuple[str, str, str]:
    mk, ss = status.get("mark") or {}, status.get("since_start") or {}
    pos = sorted((status.get("positions") or {}).items(), key=lambda kv: -(kv[1].get("unrealized_pl") or 0))
    alerts = status.get("alerts") or []
    subj = f"MCF S6 {day}: equity ${mk.get('equity', 0):,.0f}, day {_pc(mk.get('day_ret'))} (SPY {_pc(mk.get('spy_ret'))})"
    lines = [f"S6 long-hold paper account, {day}. {DISCLAIMER}",
             f"Equity ${mk.get('equity', 0):,.2f} (cash ${mk.get('cash', 0):,.2f}, {mk.get('positions', len(pos))} holdings)",
             f"Day P/L ${mk.get('day_pl') or 0:,.2f} ({_pc(mk.get('day_ret'))}); SPY {_pc(mk.get('spy_ret'))}, "
             f"EW universe {_pc(mk.get('ew_ret'))}, backtest replay {_pc(mk.get('model_ret'))}",
             f"Since start {_pc(ss.get('return'), 1)} over {ss.get('sessions', 0)} sessions; drawdown {_pc(mk.get('drawdown'), 1)}",
             f"Next rebalance signal {status.get('next_rebalance', '–')} (close), orders at the next open"]
    if alerts:
        lines.append("Alerts: " + "; ".join(f"{a.get('kind')}: {a.get('msg')}" for a in alerts))
    rows = "".join(f"<tr><td>{s}</td><td>{p.get('qty')}</td><td>${p.get('market_value') or 0:,.0f}</td>"
                   f"<td>${p.get('unrealized_pl') or 0:,.2f}</td></tr>" for s, p in pos)
    html = ("<div style='font-family:system-ui,sans-serif'><h2>MCF S6 — " + day + "</h2>"
            + "".join(f"<p>{l}</p>" for l in lines)
            + "<table style='border-collapse:collapse;font-size:13px'><tr><th>Symbol</th><th>Qty</th><th>Value</th>"
              "<th>Unrealised P/L</th></tr>" + rows + "</table></div>")
    return subj, "\n".join(lines), html


def maybe_send(state_dir: Path, day: str, to: str | None = None) -> bool:
    d = Path(state_dir)
    marker = d / "emails" / f"{day}.sent"
    st = d / "status.json"
    if marker.exists() or not st.exists() or not (os.environ.get("MCF_SMTP_USER") and os.environ.get("MCF_SMTP_PASSWORD")):
        return False
    try:
        from ..report.brief import send_email

        subj, text, html = build(json.loads(st.read_text()), day)
        send_email(subj, text, html, to or os.environ.get("MCF_EMAIL_TO") or "")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("sent\n")
        return True
    except Exception as e:   # an email must never stop the long-hold run
        print(f"S6 email not sent: {e.__class__.__name__}")
        return False
