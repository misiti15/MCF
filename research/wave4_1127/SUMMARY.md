# Research wave 4 — 2026-11-27 (evening, market closed) — synthesis

**Educational only — not financial advice.**

## In plain words

Six tasks ran tonight: five studies, each pre-registered before scoring with costs in (LIVE-L first, LR8 alongside) and
the locked block 2024-11-01..2025-02-28 never read, plus one build. **No study passed.** All five fail on out-of-sample data
after costs, and no skeptic was needed to overturn a pass. The one build, the **SPREADFLOOR shadow logger, is safe to
merge**: two skeptics each tried to refute it and neither could. It is log only. It changes no order, size, entry, exit or skip.

What we learned that is useful:
- **Index open-dip bounces are not a broad family.** Across 27 neighbouring configs the family makes about 0R/day (t 0.11).
  Wave 3's IDX3 looks like a lucky point in that grid: its 09:45 and 10:15 neighbours make -0.07 and +0.04R, and under the
  +1 min / +2 bp stress it falls to t 1.24. IDX6 (QQQ >= 1.5% by 09:55, TQQQ, trail) is the only config that clears every bar
  (n 16, +1.15R, t 3.29, stress t 2.35), but 13 of its 16 trades fall in 2016-22 and it was picked from the wave-3 grid.
- **Costs are the wall, again.** Breadth day-type (DAYTYPE) and stock-vs-sector-ETF pairs (PAIRS) both show small real gross
  tilts: +0.03R for breadth, -2..+2 bp for pairs. LIVE-L round-trip cost (about 0.10R, and 15-18 bp for a two-leg pair) is
  3-10x larger.
- **Direction stays the unsolved part.** No 09:50 feature calls direction inside the K6 mover list (GAPNEWS, 0/13 rules
  out of sample). No 12:00 model beats SPY's afternoon upward drift (PMDIR; best pooled hit 52.8% vs always-long 53-55%).
  Morning-to-afternoon momentum held in 2016-22 (57.9%) but has not since 2023 (about 50%).

Verdict rule used: a PASS/LEAD with 2 skeptic refutations becomes FAIL, and 1 refutation becomes INCONCLUSIVE. For a BUILD,
any refutation would mean **not safe to merge**. No refutations were filed tonight. Only SPREADFLOOR was given to skeptics,
and both upheld it.

## Table

| Study | Verdict (after skeptics) | Configs | Key numbers (R per trade after LIVE-L costs unless stated) | What next |
|---|---|---|---|---|
| IDXDIP — index open-dip family (SPY/QQQ/IWM x 0.75/1.0/1.5% x 09:45/09:55/10:15) | **FAIL** | 40 | Family +0.001R/day, t 0.11 (EARLY -0.003, T2 +0.002, CHECK -0.015). Stress (+1 min, +2 bp) -0.007, t -0.92. IDX3 n 57, +0.42R, t 2.20; stress +0.23R, t 1.24; neighbours -0.07 / +0.04. IDX6 n 16, +1.15R, t 3.29 (bar 2.72), best day 23%, w/o best day +0.94R, random 500/500, stress +0.73R (t 2.35), but only 3 trades after 2022 (1 each in T2/FIT/CHECK). A +2R target matches the trail (+1.09R). IWM 0.75% @09:45 n 144, +0.24R, t 2.00, survives stress, positive on EARLY/T2/CHECK (EARLY weak). Open-pop shorts fail (QQQ 1.0% -0.29R, t -2.0). Correlation with Primary daily R 0.01-0.05. | Keep `qqqopen-1127-idx6-qqq150-trail` as a forward lead (notes updated). Do not size up IDX3. IWM 0.75% is a possible later pre-registered forward check (not logged: it comes from a FAIL study). |
| DAYTYPE — breadth extremes as one SPY/QQQ position (11:30 / 13:00 to 15:55) | **FAIL** (0/24) | 24 | Every OOS split negative: -0.058..-0.106R, t -3.4..-12.1. Best Bvwap 11:30 QQQ -0.058 (t -3.9); LR8 +0.007 (t 0.5). Gross tilt +0.03R (gross t about 2.1, best day 7%, 95.6-99.6th pct vs random days). Trend alone -0.08..-0.10R. Stress -0.09..-0.15R. Weak-breadth afternoons bounce (+4.9 bp at 13:00). | None. Context only: 11:30 VWAP breadth could serve as a side tie-breaker inside existing afternoon setups (untested). |
| PAIRS — stock vs sector-ETF residual reversion | **FAIL** (0/28) | 28 | Gross -2..+2 bp of notional. Costs 15-18 bp (LIVE-L), 6-7 bp (LR8). All 28 negative on FIT/CHECK/T2 under both models: LIVE-L -13..-20 bp (about -0.13..-0.19R), OOS t -9..-33 (bar 2.61). Finalist P28: CHECK -18.2 bp (n 1,981), T2 -14.8 (n 2,811), stress -24.4. With a zero-cost hedge leg still -8.5 bp or worse. Market-neutral (SPY corr -0.07..+0.11). EARLY not available. | None. The 60-session best-ETF beta hedge in `research/pairs_1127/pr_sim.py` can be reused as a hedge engine. |
| GAPNEWS — direction inside the frozen K6 09:50 mover list | **FAIL** (0/13 rules, 0/5 setups) | 18 | Hit 48.3-50.8% on CHECK/T2, all \|t\| < 1.5 (FIT t 2.4-2.6 shrank to about 0). Directional setups CHECK -0.061..-0.124 (t -2.7..-5.1), T2 -0.071..-0.086, EARLY -0.09..-0.11. OCO bracket N2 CHECK -0.049 (t -4.8), T2 -0.055 (t -5.0). The "beats random names" gap is cost arithmetic: before costs it is 0, because K6 stops are about 3x wider (367 vs 112 bp). | None. Data idea: a point-in-time catalyst tag (earnings/news) collected forward. |
| PMDIR — SPY 12:00-15:55 direction | **FAIL** | 14 | Best model (stump: prior day > +1% -> short) hits 46.4 / 53.8 / 53.6% on CHECK/T2/EARLY vs always-long 50.4 / 55.2 / 54.1%. CHECK AUC 0.41-0.49 for every trained model. Trade LIVE-L -0.12..-0.31R (t -3.5..-7.8). Gross 0..+4 bp. Post-hoc crumb: QQQ-minus-IWM morning spread AUC about 0.55 OOS but 0.408 on FIT; as a rule still -0.09..-0.18R. | None. Optional log-only forward shadow of the QQQ-IWM spread sign (new lineage, post-hoc selection disclosed). Not logged. |
| SPREADFLOOR — log-only spread-floor shadow logger | **BUILT — SAFE TO MERGE** (2 skeptics, 0 refutations) | 0 scored (2 future configs fixed: F6, F8) | Adds `spreadfloor_shadow` (spread c/bp, stop c/bp/spreads, would_skip_6/8, AV50 `bracket` sub-record) to signal info and order meta at each real entry, after all gates and sizing, inside try/except, with an off switch (`live.spreadfloor_log`, default on, config/ untouched). Golden 12-order run unchanged (with and without quotes, with the logger throwing, with the switch off). Full suite 1062 passed / 1 skipped. Skeptics re-ran 22 + 77 + 24 and 22 + 134 related tests. Skeptic nit: at exactly 6.00/8.00 spreads, float error can flag a skip. Scoring should recompute from stop_c/spread_c. `_realism` already rejects stops under 4 spreads, so F6 acts only between 4 and 6. | Score F6/F8 after 20 and 40 tagged sessions per PREREG (backlog entry added). Add a spread term to LIVE-L. Re-run `python -m mcf.research.ledger check` in a full checkout (it failed in a skeptic's sparse worktree for lack of replay data, not because of this change). |

**Configs tonight: 124** (40 + 24 + 28 + 18 + 14 + 0). **Cumulative N ≈ 9,176 → ≈ 9,300.** The agents' own running figures
differ slightly because they ran in parallel. SPREADFLOOR's 2 pre-registered configs are added when they are scored. Lineage
bar stays about t ≥ 4.3. No result tonight reaches it; IDX6's t 3.29 on 16 trades is the closest.

Every finalist is listed in each study's REPORT / results file under `research/<key>_1127/` (idxdip, daytype, pairs,
gapnews, pmdir, spreadfloor).

## Rule changes inside the windows used

The five scored studies use history only (EARLY 2016-22, T2, FIT, CHECK to 2026-11-04) and replay the same rules on every
day, so no ledger effective date falls inside their figures. SPREADFLOOR collects live data from 2026-11-30 on. Changes
effective at the start of that window: `2026-11-30-etf-stop50-av50` (ETF-STOP50 / AV50 half-stop burst lots for
NM-ETF-late-dip-di-long in Primary, logged in the `bracket` sub-record) and `2026-11-30-friday-review-1127` (a move to
the Graveyard). Changes effective just before it: 11-27 GYH V1+V3 and ROT-B3 (Graveyard moves). When F6/F8 are scored,
any later ledger dates inside the 20/40-session window must be listed next to the figures.

## Backlog actions (this commit)

- Added `spreadfloor-1127-f6-f8-skip` (risk, idea): score the pre-registered spread-floor skips F6/F8 on the shadow-logged
  live lots after >= 20 and >= 40 sessions (bars in `research/spreadfloor_1127/PREREG.md`); widen-and-resize is the fallback
  if the skip starves setups. Any live use is an owner decision, outside market hours, with a ledger entry.
- `qqqopen-1127-idx6-qqq150-trail`: notes updated with the IDXDIP result (only clean point in a flat family, stress t 2.35,
  +2R target equal, 3 trades after 2022). Stays an idea / forward lead.
- `qqqopen-1127-idx3-size-haircut`: notes updated. IDXDIP stress gives t 1.24, so no size-up.
- Not added (from FAIL studies): IWM 0.75% open-dip, the breadth tie-breaker, multi-day sector-residual reversion, the
  residual-z tiebreak, the catalyst tag and the QQQ-IWM afternoon shadow. Each would need its own PREREG and N.
