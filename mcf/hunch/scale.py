"""Hunch at 20 -> 100 -> 200 tickers: one comparison page from the replays' summary files (research/hunch/SCALE.md).
Educational only - not financial advice."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import data as D

RUNS = [("20", ""), ("100", "u100"), ("200", "u200")]
MAIN = ["pooled:logreg", "pooled:gbt", "pooled:top8", "ticker:logreg"]


def _pct(x, d=2):
    return "—" if x is None or not np.isfinite(x) else f"{x * 100:.{d}f}%"


def build(root: Path) -> Path:
    L = ["# Hunch scale-up: 20 → 100 → 200 tickers", "",
         "*Educational only — not financial advice. Replay (backtest) results; the live shadow scoreboard is on branch "
         "mcf-data-hunch and is never mixed in.*", "",
         "Same code, features, learners and periods at every size; only the universe changes (20-set = SPY, QQQ, IWM + "
         "19 most-traded live names = 22 tickers; 100 / 200 = the 20-set + the most liquid names by 20-day dollar ADV, "
         "lists in research/hunch/universe100.txt / universe200.txt). VALID = 2026-03-01..2026-10-07; locked block "
         "2024-11-01..2025-02-28 never read. z = day-clustered z vs the best baseline; the bar grows with the number of "
         "tests at each size (per-ticker comparisons count).", ""]
    S = {}
    for size, sub in RUNS:
        for met in ("M1", "M3"):
            f = root / sub / f"{met}_summary.json"
            if f.exists():
                S[(size, met)] = json.loads(f.read_text())
    for met in ("M1", "M3"):
        L += [f"## {met}", "", "| tickers | pooled:logreg | pooled:gbt | pooled:top8 | ticker:logreg (all Hunches) | best "
              "baseline | best z | bar | pooled:logreg on the 22 common tickers | tickers where own Hunch > its best "
              "baseline | best single ticker (own) | any 65% consistent | runtime | peak memory |",
              "|---" * 14 + "|"]
        common = list(D.UNIVERSE)
        for size, _ in RUNS:
            s = S.get((size, met))
            if not s:
                L.append(f"| {size} | not run |" + " |" * 12)
                continue
            v = s["valid"]
            bb = s["best_baseline"]
            zbest = max(s["z_vs_best_valid"][n] for n in MAIN if n in s["z_vs_best_valid"])
            vt = s.get("valid_by_ticker", {})
            own = s.get("valid_by_ticker_own", {})
            base = s.get("valid_by_ticker_base", {})
            cm = np.mean([vt[t] for t in common if t in vt]) if vt else np.nan
            nbeat = sum(own[t] > base[t] for t in own)
            bt = max(own, key=own.get) if own else None
            cons = any(c.get("pass") for c in s["consistent"].values())
            L.append(f"| {s.get('n_tickers', size)} | {_pct(v.get('pooled:logreg'))} | {_pct(v.get('pooled:gbt'))} | "
                     f"{_pct(v.get('pooled:top8'))} | {_pct(v.get('ticker:logreg'))} | `{bb}` {_pct(v[bb])} | "
                     f"{zbest:.2f} | {s['bar']:.2f} | {_pct(cm)} | {nbeat} / {len(own)} (raw, no z) | "
                     f"{bt} {_pct(own.get(bt)) if bt else '—'} | {'YES' if cons else 'no'} | "
                     f"{s.get('runtime_s', float('nan')):.0f} s | {s.get('max_rss_mb', 0):,} MB |")
        L.append("")
        if met == "M1":
            L.append("**M1 reading (replay of 2026-11-04):** next-bar direction is ~51% at every size. At 200 tickers the pooled GBT and the "
                     "per-ticker Hunches clear the multiple-testing bar against the best baseline by about +0.4-0.5 pp — "
                     "real but tiny, and nowhere near 65% (best 20-session VALID window ~52%).\n")
        s20 = S.get(("20", met), {})
        if met == "M3" and "ind:vol20" in s20.get("valid", {}):
            L.append(f"**M3 reading:** next-bar volume is predictable, but mostly by volume mean reversion: the "
                     f"single-indicator vol20 learner alone scores {_pct(s20['valid']['ind:vol20'])} on VALID (20-set); "
                     f"the combined Hunch adds ~{(s20['valid']['pooled:gbt'] - s20['valid']['ind:vol20']) * 100:.1f} pp. "
                     "The ladder is not advanced automatically: the owner decides.\n")
    L += ["## Live cost estimate (one GitHub job polling 200 symbols every 3 min)", "",
          "- One job a trading day, ~09:40-16:01 ET (~6.4 runner-hours; a hand-over to the queued hourly standby after "
          "~5h40m because of the 6-hour job limit). Light: one Python process, < 1 GB RAM.",
          "- Per tick (every 3 min, 121 a day): 3 Alpaca bars GETs (204 symbols in chunks of 100, incremental since the "
          "last tick), ~10 s to rebuild 200 tickers' features from 7 days of 1-min bars, < 1 s to walk the models. "
          "About 400 market-data requests a day — far under Alpaca's rate limit, and on the data key only (no orders).",
          "- A push to mcf-data-hunch every ~15 minutes (~26 a day) plus the end-of-day model save. guesses/<day>.csv "
          "≈ 24,000 rows (~2 MB) a day.", "", "*Educational only — not financial advice.*"]
    out = root / "SCALE.md"
    out.write_text("\n".join(L) + "\n")
    return out
