"""Post-close daily review: is MCF getting better, and what should change next?

P/L on a single day is mostly noise (MarcoFlow had 1 green day in 22; strong published intraday systems
still lose on ~40% of days), so "better every day" is measured on things a day CAN show:
  * execution: entry slippage vs signal, stop-exit share, rejected/missed signals
  * data: polls, slow polls, symbols with fresh bars
  * decisions: what each skip rule and the 9:30-9:50 shadow window cost or saved (what-if trades)
  * results: today next to yesterday and the rolling 5/20-day averages (R, not just dollars)
Each finding becomes a concrete improvement candidate. Strategy changes still go through the
promotion gates; a single day never changes a setup on its own.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DISCLAIMER = "Educational only — not financial advice."


def _day_stats(tr: pd.DataFrame) -> dict:
    if tr is None or tr.empty:
        return {"trades": 0}
    p, r = tr["pnl"].astype(float), tr["r_multiple"].astype(float)
    out = {"trades": int(len(tr)), "win_rate": round(float((p > 0).mean()), 3), "exp_r": round(float(r.mean()), 3),
           "total_r": round(float(r.sum()), 2), "pnl": round(float(p.sum()), 2),
           "stop_exit_share": round(float((tr["exit_reason"] == "stop").mean()), 3)}
    if "pnl_adj" in tr and tr["pnl_adj"].notna().any():
        out["pnl_adj"] = round(float(tr["pnl_adj"].astype(float).sum()), 2)
    if "slip_bps" in tr and tr["slip_bps"].notna().any():
        out["slip_bps"] = round(float(tr["slip_bps"].astype(float).mean()), 1)
    return out


def build_review(journal, run_id: int, day: str, health: dict | None = None) -> dict:
    trades = journal.trades(run_id=run_id)
    trades["date"] = trades["date"].astype(str)
    days = sorted(trades["date"].unique()) if len(trades) else []
    today = trades[trades.date == day] if len(trades) else trades
    prev_days = [d for d in days if d < day]
    yday = trades[trades.date == prev_days[-1]] if prev_days else trades.iloc[0:0]
    roll = lambda n: [_day_stats(trades[trades.date == d]) for d in prev_days[-n:]]

    def avg(rows, k):
        v = [x[k] for x in rows if x.get("trades") and k in x]
        return round(float(np.mean(v)), 3) if v else None

    t, y = _day_stats(today), _day_stats(yday)
    r5, r20 = roll(5), roll(20)
    sig = journal.signals(run_id, day)
    whatif_id = journal.get_or_create_run("whatif", "MCF what-if (signals not taken)")
    wi = journal.trades(run_id=whatif_id)
    wi = wi[wi.date.astype(str) == day] if len(wi) else wi
    decisions = []
    if len(wi):
        wi = wi.assign(status=wi.meta.str.extract(r"status=([^;]+)")[0], why=wi.meta.str.extract(r"why=(.*)$")[0])
        wi["why"] = wi["why"].str.replace(r"\d+(\.\d+)?", "#", regex=True)
        for (st, why), g in wi.groupby(["status", "why"]):
            decisions.append({"status": st, "reason": why, "signals": int(len(g)),
                              "whatif_exp_r": round(float(g.r_multiple.mean()), 3),
                              "whatif_total_r": round(float(g.r_multiple.sum()), 2),
                              "verdict": "rule cost us R today" if g.r_multiple.sum() > 0 else "rule saved R today"})
    by_setup = {s: _day_stats(g) for s, g in today.groupby("strategy")} if len(today) else {}

    findings = []
    if t.get("slip_bps") is not None and t["slip_bps"] > 10:
        findings.append(f"Entry slippage averaged {t['slip_bps']} bps against the signal price. Candidates: resting stop-entry "
                        "orders at the broker, or streaming bars to cut polling latency.")
    for d in decisions:
        if d["signals"] >= 10 and d["whatif_total_r"] > 0:
            findings.append(f"'{d['reason']}' ({d['status']}) blocked {d['signals']} signals that would have made "
                            f"{d['whatif_total_r']:+.1f}R. Track it for 20 sessions before loosening it.")
    miss = int(sig.reason.str.startswith("missed").sum()) if len(sig) else 0
    if miss:
        findings.append(f"{miss} signals were missed because their trigger traded before the runner saw it "
                        "(job start or restart). Check job start times in the Actions log.")
    rej = int((sig.status == "rejected").sum()) if len(sig) else 0
    if rej:
        findings.append(f"{rej} orders were rejected by the broker. Read the reasons in the journal.")
    if health and health.get("last_poll_s") and health["last_poll_s"] > 30:
        findings.append(f"The last data poll took {health['last_poll_s']} s. More than 30 s delays entries.")
    better = {}
    for k, higher in (("exp_r", True), ("win_rate", True), ("slip_bps", False), ("stop_exit_share", False)):
        if t.get(k) is not None and avg(r5, k) is not None:
            better[k] = (t[k] >= avg(r5, k)) if higher else (t[k] <= avg(r5, k))
    return {
        "date": day, "disclaimer": DISCLAIMER, "today": t, "yesterday": y,
        "rolling5": {k: avg(r5, k) for k in ("exp_r", "win_rate", "pnl", "slip_bps", "stop_exit_share")},
        "rolling20": {k: avg(r20, k) for k in ("exp_r", "win_rate", "pnl", "slip_bps", "stop_exit_share")},
        "beat_rolling5": better, "by_setup": by_setup, "decisions": decisions,
        "signals": sig.status.value_counts().to_dict() if len(sig) else {}, "health": health or {},
        "findings": findings,
    }


def to_markdown(rv: dict) -> str:
    t, y, r5 = rv["today"], rv["yesterday"], rv["rolling5"]
    f = lambda v, p="": "–" if v is None else f"{v}{p}"
    lines = [f"# MCF daily review — {rv['date']}", "", f"*{rv['disclaimer']}*", "",
             "| | Today | Yesterday | 5-day avg |", "|---|---|---|---|",
             f"| Trades | {t.get('trades', 0)} | {y.get('trades', 0)} | – |",
             f"| Win rate | {f(t.get('win_rate'))} | {f(y.get('win_rate'))} | {f(r5.get('win_rate'))} |",
             f"| Expectancy (R) | {f(t.get('exp_r'))} | {f(y.get('exp_r'))} | {f(r5.get('exp_r'))} |",
             f"| P/L ($) | {f(t.get('pnl'))} | {f(y.get('pnl'))} | {f(r5.get('pnl'))} |",
             f"| Entry slippage (bps) | {f(t.get('slip_bps'))} | {f(y.get('slip_bps'))} | {f(r5.get('slip_bps'))} |",
             f"| Stop-exit share | {f(t.get('stop_exit_share'))} | {f(y.get('stop_exit_share'))} | {f(r5.get('stop_exit_share'))} |",
             "", "## Rules and filters: what they cost or saved today (what-if)", ""]
    lines += [f"- {d['status']} · {d['reason']}: {d['signals']} signals, {d['whatif_total_r']:+.1f}R ({d['verdict']})"
              for d in rv["decisions"]] or ["- No signals were held back today."]
    lines += ["", "## Improvement candidates", ""] + ([f"- {x}" for x in rv["findings"]] or ["- None today."])
    return "\n".join(lines) + "\n"


def write_review(journal, run_id: int, day: str, out_dir: str | Path, health: dict | None = None) -> Path:
    rv = build_review(journal, run_id, day, health)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{day}.json").write_text(json.dumps(rv, indent=1, default=str))
    (out / f"{day}.md").write_text(to_markdown(rv))
    (out / "latest.json").write_text(json.dumps(rv, indent=1, default=str))
    return out / f"{day}.md"
