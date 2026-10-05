"""Daily Brief: one concise email after the close — how we did, and what to improve.

Built only from the journal. Sent via SMTP using env vars (never written to files/logs):
  MCF_SMTP_HOST (default smtp.gmail.com), MCF_SMTP_PORT (465), MCF_SMTP_USER, MCF_SMTP_PASSWORD,
  MCF_EMAIL_TO (default: owner address in config report.email_to)
For Gmail, MCF_SMTP_PASSWORD must be a Google *app password* (Google Account -> Security -> App passwords).
"""

from __future__ import annotations

import html
import os
import smtplib
import ssl
from email.message import EmailMessage

import pandas as pd

from ..analytics.metrics import summarize
from ..journal import Journal

DISCLAIMER = "Educational only — not financial advice."


def _fmt(v, kind="r"):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return {"r": f"{v:+.2f}R", "pct": f"{v * 100:.1f}%", "usd": f"${v:,.0f}"}[kind]


def build_brief(journal: Journal, day: str | None = None, kind: str = "paper", dashboard_url: str | None = None):
    tr = journal.trades(kind=kind)
    if tr.empty:
        return f"MCF Daily Brief — no {kind} trades yet", f"No {kind} trades in the journal yet.\n\n{DISCLAIMER}", None
    tr["date"] = tr["date"].astype(str)
    day = day or tr["date"].max()
    today = tr[tr["date"] == day]
    hist = tr[tr["date"] <= day]
    s_day, s_all = summarize(today), summarize(hist)
    last5 = hist[hist["date"].isin(sorted(hist["date"].unique())[-5:])]
    s_5 = summarize(last5)

    by_setup = today.groupby("strategy").agg(
        trades=("r_multiple", "size"), win=("r_multiple", lambda r: (r > 0).mean()),
        exp=("r_multiple", "mean"), pnl=("pnl", "sum")).sort_values("pnl")
    never = (today["mfe_r"].fillna(0) < 0.25).sum() if "mfe_r" in today else 0
    gave_back = ((today["mfe_r"].fillna(0) >= 1.0) & (today["r_multiple"] <= 0)).sum()

    notes = []
    if s_day.get("trades"):
        if s_day["win_rate"] < 0.5:
            notes.append(f"Win rate {_fmt(s_day['win_rate'], 'pct')} is below the 50% floor.")
        worst = by_setup.index[0]
        notes.append(f"Weakest setup today: {worst} ({_fmt(by_setup.loc[worst, 'exp'])} avg, {int(by_setup.loc[worst, 'trades'])} trades).")
        if never:
            notes.append(f"{never} trades never moved +0.25R in our favour — review the entry trigger on those.")
        if gave_back:
            notes.append(f"{gave_back} trades reached +1R and still closed red — exit/scale-out review.")
    subject = (f"MCF {day}: {_fmt(s_day.get('total_pnl', 0), 'usd')} · {s_day.get('trades', 0)} trades · "
               f"win {_fmt(s_day.get('win_rate'), 'pct')}")

    def row(label, s):
        return (label, s.get("trades", 0), _fmt(s.get("win_rate"), "pct"), _fmt(s.get("breakeven_win_rate"), "pct"),
                _fmt(s.get("expectancy_r")), _fmt(s.get("total_pnl", 0), "usd"), _fmt(s.get("green_day_rate"), "pct"))

    rows = [row("Today", s_day), row("Last 5 sessions", s_5), row("All time", s_all)]
    head = ("Period", "Trades", "Win %", "Break-even win %", "Avg / trade", "P/L", "Green days")
    text = [subject, ""] + [" | ".join(map(str, r)) for r in [head] + rows] + ["", "By setup today:"]
    text += [f"  {k}: {int(v.trades)} trades, win {_fmt(v.win, 'pct')}, {_fmt(v.exp)}, {_fmt(v.pnl, 'usd')}"
             for k, v in by_setup.iterrows()]
    text += ["", "What to improve:"] + [f"  - {n}" for n in notes or ["Nothing flagged."]]
    if dashboard_url:
        text += ["", f"Dashboard: {dashboard_url}"]
    text += ["", DISCLAIMER]

    td = 'style="padding:4px 10px;border-bottom:1px solid #e1e0d9;text-align:right"'
    tbl = "".join(
        "<tr>" + "".join(f"<td {td}>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    setups = "".join(
        f"<tr><td {td}>{html.escape(k)}</td><td {td}>{int(v.trades)}</td><td {td}>{_fmt(v.win, 'pct')}</td>"
        f"<td {td}>{_fmt(v.exp)}</td><td {td}>{_fmt(v.pnl, 'usd')}</td></tr>" for k, v in by_setup.iterrows())
    html_body = f"""<div style="font:14px system-ui,sans-serif;color:#0b0b0b;max-width:680px">
<h2 style="font-size:18px">{html.escape(subject)}</h2>
<table style="border-collapse:collapse"><tr>{''.join(f'<th {td}>{h}</th>' for h in head)}</tr>{tbl}</table>
<h3 style="font-size:15px">By setup today</h3>
<table style="border-collapse:collapse"><tr><th {td}>Setup</th><th {td}>Trades</th><th {td}>Win %</th><th {td}>Avg</th><th {td}>P/L</th></tr>{setups}</table>
<h3 style="font-size:15px">What to improve</h3><ul>{''.join(f'<li>{html.escape(n)}</li>' for n in notes or ['Nothing flagged.'])}</ul>
{f'<p><a href="{html.escape(dashboard_url)}">Open the dashboard</a></p>' if dashboard_url else ''}
<p style="color:#52514e;font-size:12px">{DISCLAIMER}</p></div>"""
    return subject, "\n".join(text), html_body


def send_email(subject: str, text: str, html_body: str | None, to: str) -> None:
    user = os.environ.get("MCF_SMTP_USER")
    pwd = os.environ.get("MCF_SMTP_PASSWORD")
    if not user or not pwd:
        raise RuntimeError("MCF_SMTP_USER / MCF_SMTP_PASSWORD not set")
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.set_content(text)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    host = os.environ.get("MCF_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("MCF_SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as s:
        s.login(user, pwd)
        s.send_message(msg)
