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
VALIDATION = Path(__file__).resolve().parents[2] / "config" / "validation.json"


def _validation() -> dict:
    import json

    return json.loads(VALIDATION.read_text()) if VALIDATION.exists() else {}
NY = "America/New_York"


def _chart(spy: pd.DataFrame | None, trades: pd.DataFrame, day: str, intraday: list | None = None) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    grid = pd.date_range(f"{day} 09:30", f"{day} 16:00", freq="15min", tz=NY)
    n = 3 if intraday else 2
    fig, axes = plt.subplots(n, 1, figsize=(9, 5.2 + 2.4 * (n - 2)), sharex=True,
                             gridspec_kw={"height_ratios": [1.2, 1, 1.3][:n]})
    a1, a2 = axes[0], axes[1]
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
    if intraday:
        a3 = axes[2]
        ts = pd.to_datetime([f"{day} {x['t']}" for x in intraday]).tz_localize(NY)
        names = sorted({k for x in intraday for k in x.get("by_setup", {})})
        palette = ["#2a78d6", "#d97706", "#7c3aed", "#0b8a3e", "#d03b3b", "#0891b2", "#a16207", "#be185d"]
        for i, k in enumerate(names):
            a3.plot(ts, [x.get("by_setup", {}).get(k, 0.0) for x in intraday], lw=1.4, color=palette[i % len(palette)], label=k)
        a3.plot(ts, [x.get("total", 0.0) for x in intraday], lw=2.2, color="#0b0b0b", label="MCF total")
        a3.axhline(0, color="#898781", lw=0.8)
        a3.set_ylabel("P/L incl. open ($)")
        a3.legend(fontsize=7, ncol=3, frameon=False, loc="upper left")
    for a in axes:
        a.grid(alpha=0.25)
        a.spines[["top", "right"]].set_visible(False)
    import matplotlib.dates as mdates

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=NY))
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(tz=NY))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return buf.getvalue()


def _quality(tr: pd.DataFrame, bars: dict) -> str:
    """Execution and trade-quality section: signal-to-fill latency, best/worst excursion (MFE/MAE) in R, give-back."""
    if not len(tr):
        return ""
    parts = []
    if "signal_time" in tr and tr["signal_time"].notna().any():
        lat = (tr["entry_time"] - tr["signal_time"]).dt.total_seconds().dropna()
        lat = lat[lat >= 0]
        if len(lat):
            parts.append(f"<p>Signal to fill: median <b>{lat.median():.0f}s</b>, 90th percentile {lat.quantile(0.9):.0f}s "
                         f"({len(lat)} trades). Bars close each minute; the order follows the bar close.</p>")
    rows = []
    for r in tr.itertuples():
        b = bars.get(r.symbol)
        risk = abs(float(r.entry) - float(r.stop)) if getattr(r, "stop", None) is not None else None
        if b is None or not len(b) or not risk:
            continue
        w = b[(b.index >= r.entry_time.floor("1min")) & (b.index <= r.exit_time)]
        if not len(w):
            continue
        fav = (w["high"].max() - r.entry) if r.side > 0 else (r.entry - w["low"].min())
        adv = (r.entry - w["low"].min()) if r.side > 0 else (w["high"].max() - r.entry)
        rows.append((r.symbol, r.strategy, fav / risk, adv / risk, float(r.r_multiple)))
    if rows:
        q = pd.DataFrame(rows, columns=["symbol", "setup", "mfe", "mae", "r"])
        never = (q["mfe"] < 0.25).mean()
        gave = q[(q["mfe"] >= 1.0) & (q["r"] <= 0)]
        parts.append(f"<p>Best excursion (MFE): median <b>{q['mfe'].median():.2f}R</b>; worst (MAE) median {q['mae'].median():.2f}R. "
                     f"<b>{never:.0%}</b> of trades never got +0.25R in our favour; <b>{len(gave)}</b> reached +1R and still closed at or below 0.</p>")
        top = q.assign(gave=q["mfe"] - q["r"]).sort_values("gave", ascending=False).head(5)
        td = "style='padding:3px 8px;border-bottom:1px solid #e1e0d9;text-align:left'"
        parts.append("<table style='border-collapse:collapse;font-size:12px'><tr>" + "".join(f"<th {td}>{h}</th>" for h in ("Symbol", "Setup", "Best R", "Worst R", "Closed R")) + "</tr>" +
                     "".join(f"<tr><td {td}>{x.symbol}</td><td {td}>{x.setup}</td><td {td}>{x.mfe:+.2f}</td><td {td}>{-x.mae:+.2f}</td><td {td}>{x.r:+.2f}</td></tr>" for x in top.itertuples()) +
                     "</table><div style='font-size:11px;color:#52514e'>Largest give-backs: how far each trade went our way vs where it closed.</div>")
    return "<h3>Execution and trade quality</h3>" + "".join(parts) if parts else ""


TOD_BUCKETS = [(930, 950, "09:30-09:50"), (950, 1030, "09:50-10:30"), (1030, 1130, "10:30-11:30"), (1130, 1300, "11:30-13:00"),
               (1300, 1400, "13:00-14:00"), (1400, 1600, "14:00-16:00")]


def tod_bucket(ts) -> str:
    """Entry-time bucket (owner 2026-10-09: keep tracking time of day even though setups trade their tested windows)."""
    hm = ts.hour * 100 + ts.minute
    return next((lab for lo, hi, lab in TOD_BUCKETS if lo <= hm < hi), "other")


def tod_table(tr: pd.DataFrame) -> pd.DataFrame:
    """Trades, win rate, avg R and P/L per entry-time bucket."""
    if tr is None or not len(tr):
        return pd.DataFrame(columns=["bucket", "trades", "win", "avg_r", "pnl"])
    t = tr.assign(bucket=pd.to_datetime(tr["entry_time"], utc=True).dt.tz_convert("America/New_York").map(tod_bucket))
    g = t.groupby("bucket").agg(trades=("pnl", "size"), win=("pnl", lambda p: (p > 0).mean()),
                                avg_r=("r_multiple", "mean"), pnl=("pnl", "sum")).reset_index()
    order = {lab: i for i, (_, _, lab) in enumerate(TOD_BUCKETS)}
    return g.sort_values("bucket", key=lambda b: b.map(order).fillna(99))


def _time_of_day(tr: pd.DataFrame) -> str:
    g = tod_table(tr)
    if not len(g):
        return ""
    td = "style='padding:3px 8px;border-bottom:1px solid #e1e0d9;text-align:left'"
    return ("<h3>By time of day (entry)</h3><table style='border-collapse:collapse;font-size:12px'><tr>" +
            "".join(f"<th {td}>{h}</th>" for h in ("Entry time", "Trades", "Win", "Avg R", "P/L")) + "</tr>" +
            "".join(f"<tr><td {td}>{x.bucket}</td><td {td}>{x.trades}</td><td {td}>{x.win:.0%}</td><td {td}>{x.avg_r:+.2f}</td>"
                    f"<td {td}>${x.pnl:,.2f}</td></tr>" for x in g.itertuples()) +
            "</table><div style='font-size:11px;color:#52514e'>Tracked to test whether time of day matters live; "
            "the cumulative view is in the scorecard.</div>")


def build(journal, run_id: int, day: str, spy: pd.DataFrame | None, review: dict | None = None,
          intraday: list | None = None, bars: dict | None = None):
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
    val = _validation()
    vs = val.get("setups", {})
    banner = (f"<p style='background:#fff4e5;border-left:4px solid #d97706;padding:8px 10px;font-size:13px'>"
              f"{val['_banner']}</p>") if val.get("_banner") else ""
    by_setup = ""
    if n:
        g = tr.groupby("strategy").agg(trades=("pnl", "size"), pnl=("pnl", "sum"), win=("pnl", lambda p: (p > 0).mean()),
                                       avg_r=("r_multiple", "mean"))
        by_setup = "".join(f"<tr><td>{k}<br><span style='font-size:11px;color:#b45309'>{vs.get(k, {}).get('note', '')}</span></td><td>{v.trades}</td><td>{v.win:.0%}</td><td>{v.avg_r:+.2f}</td><td>${v.pnl:,.2f}</td></tr>"
                           for k, v in g.iterrows())
    findings = "".join(f"<li>{f}</li>" for f in (review or {}).get("findings", [])) or "<li>None today.</li>"
    cid = make_msgid(domain="mcf.local")
    td = "style='padding:4px 8px;border-bottom:1px solid #e1e0d9;text-align:left'"
    html = f"""<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#0b0b0b;max-width:760px">
<h2 style="margin:0 0 4px">MCF end of day — {day}</h2>
<div style="color:#52514e;font-size:13px">{DISCLAIMER} Paper trading.</div>
<p style="font-size:15px"><b>{n}</b> trades · win rate <b>{'–' if n == 0 else f'{win:.0%}'}</b> ·
P/L <b style="color:{'#0b8a3e' if pnl >= 0 else '#d03b3b'}">${pnl:,.2f}</b></p>
{banner}<img src="cid:{cid[1:-1]}" alt="SPY and MCF P/L in 15-minute steps" style="max-width:100%">
<h3>Top 10 losing trades (by % lost)</h3>
<table style="border-collapse:collapse;font-size:13px">
<tr><th {td}>Symbol</th><th {td}>Setup</th><th {td}>Side</th><th {td}>In</th><th {td}>Out</th><th {td}>Entry</th><th {td}>Exit</th><th {td}>Exit reason</th><th {td}>% lost</th><th {td}>P/L</th></tr>
{rows}</table>
{_quality(tr, bars or {})}
{_time_of_day(tr)}
<h3>By setup</h3>
<table style="border-collapse:collapse;font-size:13px"><tr><th {td}>Setup</th><th {td}>Trades</th><th {td}>Win</th><th {td}>Avg R</th><th {td}>P/L</th></tr>
{by_setup or '<tr><td colspan=5>No trades.</td></tr>'}</table>
<h3>Improvement candidates (daily review)</h3><ul>{findings}</ul>
<p style="font-size:12px;color:#52514e">Every trade is attached as a CSV you can open and edit in Excel or Google Sheets.
Live page: https://misiti15.github.io/MCF/live/</p></div>"""
    text = f"MCF end of day {day}: {n} trades, P/L ${pnl:,.2f}. {DISCLAIMER}"
    csv = tr.drop(columns=[c for c in ("meta",) if c in tr]).to_csv(index=False) if n else "no trades\n"
    return {"subject": f"MCF EOD {day}: {n} trades, ${pnl:,.0f}", "html": html, "text": text,
            "png": _chart(spy, tr, day, intraday), "cid": cid, "csv": csv}


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
