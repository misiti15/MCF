"""End-of-day email: deterministic (no AI), sent by the trade workflow after the close.

Contents: day summary, the 10 worst trades by % lost, a 15-minute chart of how the day flowed
(SPY next to MCF's cumulative realized P/L), and every trade as an editable CSV attachment.
A copy is saved to the state branch (reports/<date>.html and .csv).
Needs repository secrets MCF_SMTP_USER / MCF_SMTP_PASSWORD (Gmail app password); without them the
report is still written, just not emailed.
"""

from __future__ import annotations

import io
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

import numpy as np
import pandas as pd

DISCLAIMER = "Educational only — not financial advice."
NY = "America/New_York"


def _chart(spy: pd.DataFrame | None, trades: pd.DataFrame, day: str) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    grid = pd.date_range(f"{day} 09:30", f"{day} 16:00", freq="15min", tz=NY)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.2), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    if spy is not None and len(spy):
        s = spy["close"].resample("15min", label="right", closed="left").last().reindex(grid).ffill()
        a1.plot(s.index, s.values, color="#2a78d6", lw=1.8)
        a1.set_ylabel("SPY")
        a1.set_title(f"How the day flowed — {day} (15-minute steps)", fontsize=11, loc="left")
    pnl = pd.Series(0.0, index=grid)
    if len(trades):
        ex = pd.to_datetime(trades["exit_time"], utc=True, format="ISO8601").dt.tz_convert(NY)
        steps = pd.Series(trades["pnl"].astype(float).to_numpy(), index=ex).sort_index()
        pnl = steps.resample("15min", label="right", closed="left").sum().reindex(grid, fill_value=0).cumsum()
    col = np.where(pnl.values >= 0, "#0b8a3e", "#d03b3b")
    a2.bar(pnl.index, pnl.values, width=0.008, color=col)
    a2.axhline(0, color="#898781", lw=0.8)
    a2.set_ylabel("MCF realized P/L ($)")
    for a in (a1, a2):
        a.grid(alpha=0.25)
        a.spines[["top", "right"]].set_visible(False)
    import matplotlib.dates as mdates

    a2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=NY))
    a2.xaxis.set_major_locator(mdates.HourLocator(tz=NY))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return buf.getvalue()


def build(journal, run_id: int, day: str, spy: pd.DataFrame | None, review: dict | None = None):
    tr = journal.trades(run_id=run_id)
    tr = tr[tr["date"].astype(str) == day].copy() if len(tr) else tr
    if len(tr):
        tr["pct"] = tr["side"] * (tr["exit"] / tr["entry"] - 1) * 100
    losers = tr.sort_values("pct").head(10) if len(tr) else tr
    losers = losers[losers["pct"] < 0] if len(losers) else losers
    n = len(tr)
    pnl = float(tr["pnl"].sum()) if n else 0.0
    win = float((tr["pnl"] > 0).mean()) if n else float("nan")
    rows = "".join(
        f"<tr><td>{r.symbol}</td><td>{r.strategy}</td><td>{'long' if r.side > 0 else 'short'}</td>"
        f"<td>{str(r.entry_time)[11:16]}</td><td>{str(r.exit_time)[11:16]}</td><td>{r.entry:.2f}</td><td>{r.exit:.2f}</td>"
        f"<td>{r.exit_reason}</td><td style='color:#d03b3b'>{r.pct:.2f}%</td><td>${r.pnl:,.2f}</td></tr>"
        for r in losers.itertuples()) or "<tr><td colspan=10>No losing trades today.</td></tr>"
    by_setup = ""
    if n:
        g = tr.groupby("strategy").agg(trades=("pnl", "size"), pnl=("pnl", "sum"), win=("pnl", lambda p: (p > 0).mean()),
                                       avg_r=("r_multiple", "mean"))
        by_setup = "".join(f"<tr><td>{k}</td><td>{v.trades}</td><td>{v.win:.0%}</td><td>{v.avg_r:+.2f}</td><td>${v.pnl:,.2f}</td></tr>"
                           for k, v in g.iterrows())
    findings = "".join(f"<li>{f}</li>" for f in (review or {}).get("findings", [])) or "<li>None today.</li>"
    cid = make_msgid(domain="mcf.local")
    td = "style='padding:4px 8px;border-bottom:1px solid #e1e0d9;text-align:left'"
    html = f"""<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#0b0b0b;max-width:760px">
<h2 style="margin:0 0 4px">MCF end of day — {day}</h2>
<div style="color:#52514e;font-size:13px">{DISCLAIMER} Paper trading.</div>
<p style="font-size:15px"><b>{n}</b> trades · win rate <b>{'–' if n == 0 else f'{win:.0%}'}</b> ·
P/L <b style="color:{'#0b8a3e' if pnl >= 0 else '#d03b3b'}">${pnl:,.2f}</b></p>
<img src="cid:{cid[1:-1]}" alt="SPY and MCF P/L in 15-minute steps" style="max-width:100%">
<h3>Top 10 losing trades (by % lost)</h3>
<table style="border-collapse:collapse;font-size:13px">
<tr><th {td}>Symbol</th><th {td}>Setup</th><th {td}>Side</th><th {td}>In</th><th {td}>Out</th><th {td}>Entry</th><th {td}>Exit</th><th {td}>Exit reason</th><th {td}>% lost</th><th {td}>P/L</th></tr>
{rows}</table>
<h3>By setup</h3>
<table style="border-collapse:collapse;font-size:13px"><tr><th {td}>Setup</th><th {td}>Trades</th><th {td}>Win</th><th {td}>Avg R</th><th {td}>P/L</th></tr>
{by_setup or '<tr><td colspan=5>No trades.</td></tr>'}</table>
<h3>Improvement candidates (daily review)</h3><ul>{findings}</ul>
<p style="font-size:12px;color:#52514e">Every trade is attached as a CSV you can open and edit in Excel or Google Sheets.
Live page: https://misiti15.github.io/MCF/live/</p></div>"""
    text = f"MCF end of day {day}: {n} trades, P/L ${pnl:,.2f}. {DISCLAIMER}"
    csv = tr.drop(columns=[c for c in ("meta",) if c in tr]).to_csv(index=False) if n else "no trades\n"
    return {"subject": f"MCF EOD {day}: {n} trades, ${pnl:,.0f}", "html": html, "text": text,
            "png": _chart(spy, tr, day), "cid": cid, "csv": csv}


def save(rep: dict, out_dir: str | Path, day: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{day}.html").write_text(rep["html"].replace(f"cid:{rep['cid'][1:-1]}", f"{day}.png"))
    (out / f"{day}.png").write_bytes(rep["png"])
    (out / f"{day}.csv").write_text(rep["csv"])


def send(rep: dict, to: str, day: str) -> bool:
    user, pwd = os.environ.get("MCF_SMTP_USER"), os.environ.get("MCF_SMTP_PASSWORD")
    if not user or not pwd:
        print("EOD email not sent: add MCF_SMTP_USER and MCF_SMTP_PASSWORD repository secrets")
        return False
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = rep["subject"], user, to
    msg.set_content(rep["text"])
    msg.add_alternative(rep["html"], subtype="html")
    msg.get_payload()[1].add_related(rep["png"], "image", "png", cid=rep["cid"])
    msg.add_attachment(rep["csv"].encode(), maintype="text", subtype="csv", filename=f"mcf-trades-{day}.csv")
    with smtplib.SMTP_SSL(os.environ.get("MCF_SMTP_HOST", "smtp.gmail.com"), int(os.environ.get("MCF_SMTP_PORT", "465")),
                          context=ssl.create_default_context(), timeout=30) as s:
        s.login(user, pwd)
        s.send_message(msg)
    print(f"EOD email sent to {to}")
    return True
