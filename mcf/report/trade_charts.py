"""Per-trade charts for the end-of-day email (owner 2026-10-15). Report only. Educational only - not financial advice.

For the day's best 3 trades (by % gained) and worst 5 (by % lost): a 3-minute candlestick chart from 09:00 to 16:00 ET
(the first 30 minutes are pre-market, shaded, so the open is visible), volume under the price, the 09:30 open marked,
the exact entry and exit (time and price) as markers plus horizontal lines, and the journal's stop/target when present.
PNG via matplotlib (Agg), ~900x500 px. A trade whose bars are missing gets a note instead of a chart; nothing here may
stop the email.
"""

from __future__ import annotations

import io
import re

import pandas as pd

from ..setup_names import label as setup_label

NY = "America/New_York"
START, OPEN, END = "09:00", "09:30", "16:00"
BAR = "3min"
UP, DOWN, ENTRY, EXIT = "#0b8a3e", "#d03b3b", "#2a78d6", "#7c3aed"


def pick(tr: pd.DataFrame, best: int = 3, worst: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Best `best` by % gained (only winners) and worst `worst` by % lost (only losers). Adds column `pct` if missing."""
    if tr is None or not len(tr):
        return tr, tr
    if "pct" not in tr:
        tr = tr.assign(pct=tr["side"] * (tr["exit"] / tr["entry"] - 1) * 100)
    winners = tr[tr["pct"] > 0].sort_values("pct", ascending=False).head(best)
    losers = tr[tr["pct"] < 0].sort_values("pct").head(worst)
    return winners, losers


def window(bars: pd.DataFrame | None, day: str) -> pd.DataFrame:
    """1-minute bars (any hours) -> 3-minute OHLCV bars with bar start in [09:00, 16:00) ET of `day`."""
    if bars is None or not len(bars):
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    b = bars.copy()
    idx = pd.DatetimeIndex(b.index)
    b.index = (idx.tz_localize("UTC") if idx.tz is None else idx).tz_convert(NY)
    lo, hi = pd.Timestamp(f"{day} {START}", tz=NY), pd.Timestamp(f"{day} {END}", tz=NY)
    b = b[(b.index >= lo) & (b.index < hi)]
    if not len(b):
        return b
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return b.resample(BAR, label="left", closed="left", origin=lo).agg(agg).dropna(subset=["open"])


def _ts(x) -> pd.Timestamp | None:
    if x is None or (not isinstance(x, pd.Timestamp) and pd.isna(x)):
        return None
    t = pd.Timestamp(x)
    if pd.isna(t):
        return None
    return (t.tz_localize("UTC") if t.tzinfo is None else t).tz_convert(NY)


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v and v != 0 else None


def chart(bars: pd.DataFrame | None, trade, day: str, dpi: int = 100) -> bytes | None:
    """PNG bytes for one trade (a row with symbol, strategy, side, entry_time, entry, exit_time, exit, r_multiple, pnl,
    optional stop/target/pct), or None when there are no bars in the 09:00-16:00 window."""
    w = window(bars, day)
    if not len(w):
        return None
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.patches import Rectangle

    g = trade.get if hasattr(trade, "get") else (lambda k, d=None: getattr(trade, k, d))
    side = 1 if float(g("side", 1)) > 0 else -1
    entry, exit_ = float(g("entry")), float(g("exit"))
    t_in, t_out = _ts(g("entry_time")), _ts(g("exit_time"))
    stop, target = _num(g("stop")), _num(g("target"))
    r, pnl = g("r_multiple"), g("pnl")
    pct = g("pct")
    pct = side * (exit_ / entry - 1) * 100 if pct is None or pd.isna(pct) else float(pct)

    lo, hi = pd.Timestamp(f"{day} {START}", tz=NY), pd.Timestamp(f"{day} {END}", tz=NY)
    x = mdates.date2num(w.index.tz_convert("UTC").tz_localize(None).to_pydatetime())
    width = (3 / 1440) * 0.7
    fig, (ax, av) = plt.subplots(2, 1, figsize=(9, 5), dpi=dpi, sharex=True, gridspec_kw={"height_ratios": [3.2, 1]})
    up = (w["close"] >= w["open"]).to_numpy()
    col = [UP if u else DOWN for u in up]
    ax.vlines(x + width / 2, w["low"], w["high"], color=col, lw=0.8, zorder=2)
    for xi, o, c, cc in zip(x, w["open"], w["close"], col):
        ax.add_patch(Rectangle((xi, min(o, c)), width, max(abs(c - o), 1e-9), facecolor=cc, edgecolor=cc, lw=0.5, zorder=3))
    av.bar(x + width / 2, w["volume"], width=width, color=col, alpha=0.7)

    def n(t):
        return mdates.date2num(t.tz_convert("UTC").tz_localize(None).to_pydatetime())

    for a in (ax, av):
        a.axvspan(n(lo), n(pd.Timestamp(f"{day} {OPEN}", tz=NY)), color="#e1e0d9", alpha=0.6, zorder=0, lw=0)
        a.axvline(n(pd.Timestamp(f"{day} {OPEN}", tz=NY)), color="#52514e", lw=0.9, ls="--", zorder=1)
        a.grid(alpha=0.25)
        a.spines[["top", "right"]].set_visible(False)
    ax.text(n(lo) + 0.0005, 0.02, "pre-market", transform=ax.get_xaxis_transform(), fontsize=7, color="#52514e", va="bottom")
    ax.text(n(pd.Timestamp(f"{day} {OPEN}", tz=NY)) + 0.0005, 0.98, "09:30 open", transform=ax.get_xaxis_transform(),
            fontsize=7, color="#52514e", va="top")

    ys = [float(w["low"].min()), float(w["high"].max()), entry, exit_]
    labels = [(entry, f"entry {entry:.2f}", ENTRY), (exit_, f"exit {exit_:.2f}", EXIT)]
    for lvl, name, c in ((stop, "stop", DOWN), (target, "target", UP)):
        if lvl is not None:
            ax.axhline(lvl, color=c, lw=0.9, ls=":", zorder=1)
            labels.append((lvl, f"{name} {lvl:.2f}", c))
            ys.append(lvl)
    ax.axhline(entry, color=ENTRY, lw=1, ls="--", zorder=1)
    ax.axhline(exit_, color=EXIT, lw=1, ls="--", zorder=1)
    box = dict(boxstyle="round,pad=0.2", fc="white", lw=0.6, alpha=0.9)
    # entry marker: buy = up triangle, sell short = down triangle; exit is the opposite action.
    # The higher of the two prices gets its label above, the lower one below, so the labels never collide.
    if t_in is not None:
        ax.scatter([n(t_in)], [entry], marker="^" if side > 0 else "v", s=90, color=ENTRY, edgecolor="white", zorder=7)
        ax.annotate(f"{'BUY' if side > 0 else 'SHORT'} {t_in:%H:%M:%S} @ {entry:.2f}", (n(t_in), entry),
                    xytext=(0, 18 if entry >= exit_ else -20), textcoords="offset points", ha="center", va="center", fontsize=7,
                    color=ENTRY, weight="bold", bbox=dict(box, ec=ENTRY), zorder=6)
    if t_out is not None:
        ax.scatter([n(t_out)], [exit_], marker="v" if side > 0 else "^", s=90, color=EXIT, edgecolor="white", zorder=7)
        ax.annotate(f"{'SELL' if side > 0 else 'COVER'} {t_out:%H:%M:%S} @ {exit_:.2f}", (n(t_out), exit_),
                    xytext=(0, -20 if entry >= exit_ else 18), textcoords="offset points", ha="center", va="center", fontsize=7,
                    color=EXIT, weight="bold", bbox=dict(box, ec=EXIT), zorder=6)
    span = max(ys) - min(ys)
    ax.set_ylim(min(ys) - 0.04 * span, max(ys) + 0.06 * span)
    ax.set_xlim(n(lo), n(hi))
    # right-margin level labels, nudged apart so close levels (e.g. exit at target) stay readable
    y0, y1 = ax.get_ylim()
    gap, last = 0.045 * (y1 - y0), None
    for lvl, txt, c in sorted(labels):
        y = lvl if last is None else max(lvl, last + gap)
        ax.text(n(hi), y, f" {txt}", color=c, fontsize=7, va="center", ha="left")
        last = y
    rtxt = "" if r is None or pd.isna(r) else f"{float(r):+.2f}R · "
    ptxt = "" if pnl is None or pd.isna(pnl) else f"{'-' if float(pnl) < 0 else '+'}${abs(float(pnl)):,.2f} · "
    ax.set_title(f"{g('symbol')} {'long' if side > 0 else 'short'} · {setup_label(str(g('strategy')))}\n"
                 f"{rtxt}{ptxt}{pct:+.2f}% · exit: {g('exit_reason', '') or ''} · {day} (3-minute bars, ET)",
                 fontsize=9, loc="left")
    ax.set_ylabel("Price")
    av.set_ylabel("Volume", fontsize=8)
    av.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k"))
    av.xaxis.set_major_locator(mdates.HourLocator(tz=NY))
    av.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=NY))
    for a in (ax, av):
        a.tick_params(labelsize=7)
    fig.tight_layout()
    fig.subplots_adjust(right=0.88)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    plt.close(fig)
    return buf.getvalue()


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(s)).strip("-")[:60]


def build(tr: pd.DataFrame, bars: dict | None, day: str, make_cid=None) -> dict:
    """Charts for the best 3 / worst 5 trades. Returns {"best": [...], "worst": [...]} with one dict per trade:
    trade (row), name (file name), png (bytes or None), cid (str or None), note (why there is no chart)."""
    from email.utils import make_msgid

    make_cid = make_cid or (lambda: make_msgid(domain="mcf.local"))
    winners, losers = pick(tr)
    out = {"best": [], "worst": []}
    for key, df in (("best", winners), ("worst", losers)):
        for rank, (_, row) in enumerate(df.iterrows() if df is not None and len(df) else [], start=1):
            name = f"{key}{rank}-{_slug(row['symbol'])}-{_slug(row['strategy'])}.png"
            png, note = None, ""
            try:
                png = chart((bars or {}).get(row["symbol"]), row, day)
                if png is None:
                    note = "Chart unavailable: no 3-minute bars for 09:00-16:00."
            except Exception as e:   # a chart must never stop the email
                note = f"Chart unavailable ({e.__class__.__name__})."
            out[key].append({"trade": row, "name": name, "png": png, "cid": make_cid() if png else None, "note": note})
    return out


def html(items: list[dict], heading: str) -> str:
    if not items:
        return ""
    parts = [f"<h4 style='margin:14px 0 4px'>{heading}</h4>"]
    for i, it in enumerate(items, start=1):
        r = it["trade"]
        side = "long" if float(r["side"]) > 0 else "short"
        rr = "" if pd.isna(r.get("r_multiple")) else f" · {float(r['r_multiple']):+.2f}R"
        parts.append(f"<div style='font-size:13px;margin:8px 0 2px'><b>{i}. {r['symbol']}</b> {side} · {setup_label(r['strategy'])}"
                     f" · {float(r['pct']):+.2f}%{rr} · ${float(r['pnl']):,.2f}</div>")
        if it["png"]:
            parts.append(f"<img src=\"cid:{it['cid'][1:-1]}\" alt=\"{r['symbol']} 3-minute chart with entry and exit\" "
                         "style='max-width:100%;width:900px'>")
        else:
            parts.append(f"<div style='font-size:12px;color:#52514e'>{it['note']}</div>")
    return "".join(parts)
