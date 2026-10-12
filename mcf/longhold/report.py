"""Weekly long-hold report (Saturday): self-contained HTML. Educational only - not financial advice."""
from __future__ import annotations

import html
from datetime import date

import pandas as pd


def _pc(x, d=2):
    try:
        return "–" if x is None or x != x else f"{float(x) * 100:+.{d}f}%"
    except (TypeError, ValueError):
        return "–"


def _m(x):
    try:
        return "–" if x is None or x != x else f"${float(x):,.2f}"
    except (TypeError, ValueError):
        return "–"


def _table(head, rows):
    h = "".join(f"<th>{html.escape(str(c))}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b or '<tr><td colspan=9>none</td></tr>'}</tbody></table>"


def _cum(m: pd.DataFrame, col: str) -> pd.Series:
    r = pd.to_numeric(m.get(col), errors="coerce").fillna(0.0) if col in m else pd.Series(0.0, index=m.index)
    r.iloc[0] = 0.0
    return (1 + r).cumprod() - 1


def weekly_html(marks: pd.DataFrame, fills: pd.DataFrame, plans: list[dict], st: dict, events: list[dict],
                today: date) -> str:
    label = st.get("label", "paper")
    parts = [f"<h1>Long-hold (S6) weekly report — {today}</h1>",
             f"<p class=sub><b>{html.escape(label)}</b> account, strategy <code>{html.escape(st.get('strategy', ''))}"
             "</code>. Paper results (or a dry-run shadow book) and the backtest replay are labelled separately "
             "(rule 7). Educational only — not financial advice.</p>"]
    al = st.get("alerts") or []
    parts.append("<h2>Alerts</h2>" + (_table(["level", "kind", "message"], [[a["level"], a["kind"], html.escape(a["msg"])]
                                                                             for a in al]) if al else "<p>None.</p>"))
    if len(marks):
        m = marks.copy()
        eq = pd.to_numeric(m["equity"])
        m["cum_book"] = eq / eq.iloc[0] - 1
        m["cum_spy"], m["cum_ew"], m["cum_model"] = _cum(m, "spy_ret"), _cum(m, "ew_ret"), _cum(m, "model_ret")
        last = m.iloc[-1]
        parts.append("<h2>Since start</h2>" + _table(
            ["start", "sessions", "book (" + html.escape(label) + ")", "SPY", "EW universe", "backtest replay",
             "max drawdown", "20-session tracking diff."],
            [[m["date"].iloc[0], len(m), _pc(last.cum_book), _pc(last.cum_spy), _pc(last.cum_ew),
              _pc(last.cum_model), _pc((eq / eq.cummax() - 1).min()), _pc(last.get("te_20d"))]]))
        wk = m.tail(5)
        parts.append("<h2>This week, day by day</h2>" + _table(
            ["date", "equity", "day P/L", "book", "SPY", "EW univ.", "replay", "tracking diff.", "drawdown"],
            [[r.get("date"), _m(r.get("equity")), _m(r.get("day_pl")), _pc(r.get("day_ret")), _pc(r.get("spy_ret")),
              _pc(r.get("ew_ret")), _pc(r.get("model_ret")), _pc(r.get("te")), _pc(r.get("drawdown"))]
             for r in wk.to_dict("records")]))
        to = pd.to_numeric(m["turnover"], errors="coerce").fillna(0) if "turnover" in m else pd.Series(0.0)
        mto = pd.to_numeric(m["model_turnover"], errors="coerce").fillna(0) if "model_turnover" in m else pd.Series(0.0)
        yrs = max(len(m) / 252, 1e-9)
        parts.append(f"<h2>Turnover and costs</h2><p>Turnover (one-way, fraction of equity): book {to.sum():.2f} "
                     f"({to.sum() / yrs:.1f}x/yr annualised over {len(m)} sessions), backtest replay {mto.sum():.2f}. "
                     "Paper commissions are zero, so the model cost (1c/share + 1 bps per traded dollar) is the cost "
                     "charged to the replay; measured slippage vs the auction print is below.</p>")
    else:
        parts.append("<p>No marks yet.</p>")
    if len(fills):
        f = fills.copy()
        f["slippage_bps"] = pd.to_numeric(f["slippage_bps"], errors="coerce")
        g = f.groupby("exec_day").agg(fills=("symbol", "size"), notional=("notional", "sum"),
                                      slip=("slippage_bps", "mean"), model=("model_cost_bps", "mean"))
        parts.append("<h3>Slippage vs the official print, per execution day</h3>" + _table(
            ["exec day", "fills", "notional", "mean slippage bps", "model cost bps"],
            [[d, int(r.fills), _m(r.notional), f"{r.slip:+.1f}" if r.slip == r.slip else "–",
              f"{r.model:.1f}" if r.model == r.model else "–"] for d, r in g.iterrows()]))
    pos = st.get("positions") or {}
    parts.append("<h2>Holdings</h2>" + _table(
        ["symbol", "qty", "value", "weight", "entry day", "unrealised P/L"],
        [[s, f"{(p.get('qty') or 0):g}", _m(p.get("market_value")), _pc(p.get("weight"), 1), p.get("entry_day") or "–",
          _m(p.get("unrealized_pl"))] for s, p in pos.items()]))
    parts.append(f"<p>Next rebalance (signal at the close): <b>{st.get('next_rebalance') or '–'}</b>; orders at the "
                 "next session's open (MOO).</p>")
    rows = [[p["signal_day"], p.get("kind"), p.get("status"), len(p.get("orders", [])),
             html.escape(str(p.get("skip_reason") or "")), p.get("slippage_bps_mean")] for p in plans[-6:]]
    parts.append("<h2>Rebalances</h2>" + _table(["signal day", "kind", "status", "orders", "skip reason",
                                                  "mean slippage bps"], rows))
    bad = [e for e in events if e.get("level") in ("warn", "halt", "error")][-20:]
    parts.append("<h2>Skips, kill-switch and order events (last 20)</h2>" + _table(
        ["time", "level", "kind", "message"], [[e["ts"], e["level"], e["kind"], html.escape(e["msg"])] for e in bad]))
    css = ("body{font:14px/1.45 system-ui,sans-serif;max-width:980px;margin:0 auto;padding:16px;background:#fcfcfb;"
           "color:#0b0b0b}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:13px}"
           "td,th{padding:4px 8px;border-bottom:1px solid #e1e0d9;text-align:right}td:first-child,th:first-child"
           "{text-align:left}.sub{color:#52514e}@media(prefers-color-scheme:dark){body{background:#1a1a19;color:#fff}"
           "td,th{border-color:#2c2c2a}.sub{color:#c3c2b7}}")
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,"
            f"initial-scale=1'><title>Long-hold weekly {today}</title><style>{css}</style></head><body>"
            + "".join(parts) + "<p class=sub>Educational only — not financial advice.</p></body></html>")
