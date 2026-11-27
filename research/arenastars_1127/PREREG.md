# ARENASTARS-1127 pre-registration (written 2026-11-27 ~19:30 UTC, before any score below was computed)

Educational only — not financial advice. Research only: no config, setup, exit, assignments, decisions.json, ledger or
backlog change. Broker / MarcoFlow: no calls (journals via `git show`, bars from the local caches).

## Question
Three Setup Generator shorts/longs now carry strong live arena records (as quoted by the orchestrator, LR8 basis):
- **G05** = GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short (Testing B = explore1; 223 tr, +0.445R, t 6.57)
- **G07** = GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short (Testing A = testing2; 238 tr, +0.416R, t 6.6)
- **G37** = GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long (Testing A; 139 tr, +0.459R, t 3.7)
Are these records real (costs, concentration, rule changes, fill realism), does the history agree, and does any of them
improve Primary's book (added, or replacing L3 / RW3 / RW5)? Hypothesis (optimistic): at least one is a real,
breadth-conditioned (day-type) edge that survives costs on history and adds to Primary.
Prior disclosed: the generator's own quick screens (module docstrings, open 2-year history, LR8-type costs) were weak:
G05 train +0.040 / valid +0.015R; G07 −0.003 / −0.018R; G37 +0.247 / +0.037R (t <= 0.73). The generator's train/valid
windows overlap FIT and CHECK, so **T2 (2023-01-03..2024-09-13) is the only history the GEN lineage never saw**.

## Part A — live audit (journals, all accounts; identical signals once, footrace de-dup)
Per setup: LR8 R (mcf.report.footrace basis), fill-gross R (fills, no fees), and **LIVE-L R** = engine-basis gross R
from the decision-bar close (signal ref_price) to the engine exit (stop price; target; market = exit fill) minus
LIVE-L cost (primshorts_1126 cells_live.json, predict_R by price bucket x exit kind). Reported: trades, traded and
active sessions, avg R, day-clustered t (t of per-day mean R and the trade-clustered t), green-day %, avg R w/o best 1
and best 2 days, best-day share, price-bucket mix ($5-20 share, LR8 vs LIVE-L by bucket), spread_bps at signal,
borrow / realism / daily-loss skips (scorecards), lot notional vs ADV20, per account, non-overlap record (drop
symbol-days a Primary member traded), shrunk estimate n/(n+150) x avg + 150/(n+150) x (−0.10), and the ledger rule
changes inside the window.
**Live bars (all must hold, LIVE-L basis):** avg R > 0; per-day t >= 2.0; avg w/o best day > 0 and w/o best 2 days > 0;
best-day share < 40% (PRIME-RULES entry) ; >= 20 traded sessions (PRIME-RULES) ; C3-BAR2: >= 30 trades, >= 8 traded
sessions, >= 15 active days, green days >= 50%, shrunk estimate > 0, non-overlap avg w/o best day > 0.

## Part B — history replay (3 configs: each setup at its live config)
bench10 pipeline (research/ultimate_1119/top10/bench10.py), live module mask, YAML window, min_adv on ADV20, first hit
per symbol-day (refire false), entry = decision-bar close, 1-minute walk: stop first (gap-through at the open), hold =
stop 1R / no target / flat 15:55; holdtr = same + stop trails 1R behind the best price once MFE >= 1R (updated after
each minute, as mcf/backtest/engine.py), price >= $5, shorts ETB >= 90%, home testing book (cap 100 per setup, <= 3
per symbol, cost filter 0.15). Costs: **LIVE-L** (headline) and LR8 (bench10 add_r). Context columns: T1 lab context
(breadth / breadth_open over the lab universe); T2 has no breadth column, so breadth and breadth_open are computed
here from the T2 1-minute cache (469 names; share above 5-min VWAP / above the day open, per 5-min bar close) —
universe differs from live (disclosed). Splits: FIT 2024-10 + 2025-03..09, CHECK 2025-10-01..2026-11-04, T2
2023-01-03..2024-09-13. Locked block 2024-11-01..2025-02-28 never read (asserted in every script).
**Random control:** per setup, a pool of random entries with the same side, window, min_adv, price / ETB filters and
geometry (up to 12 random eligible 5-min bars per day, one per symbol-day), walked the same way; 500 draws matched to
the setup's trade count per day; the setup's avg R must exceed the control's 95th percentile.
**History bars (each on CHECK and on T2, LIVE-L):** avg R > 0; day-clustered t >= 1.5 on CHECK (seen by the GEN
lineage) and **>= 2.6 on T2** (3 candidates, Bonferroni one-sided 0.005); above the random-control 95th pct; avg w/o
best day > 0; best-day share < 25%. FIT reported (confirmation only).

## Part C — Primary book (12 configs)
E4 minute book engine (research/cfprimary_1127/e4nb.py, copied with 5 setup slots; Primary rules: 77 slots, 30 per
setup, <= 3 per symbol per setup, burst brake 30/10 min, −2R realised latch, −20R halt), P4 lineup (L3, RW3, RW5,
NM-ETF), bench10 lots regenerated tonight, LIVE-L on shorts, LR8 on NM-ETF; contexts BASE and LO (LATCH-OPEN).
Configs: **ADD-G** (each candidate added, 3) and **REP-X-G** (candidate replaces L3, RW3 or RW5; 9).
Controls: ADD vs a **size-matched random add** (100 draws: the candidate's lots replaced by random-pool lots, same count
per day, same side / window); REP vs **X-out** (the replaced setup removed with nothing added) so the candidate must add
value beyond the removal that rwout_1127 already scored.
**Book bars (CHECK and T2, BASE and LO):** ADD: dR/day > 0, paired day t >= 2.8, above the random-add 95th pct,
best-day share of the gain < 25%. REP: dR vs keep > 0 with t >= 2.8 AND dR vs X-out > 0 with t >= 2.0.

## Verdict
**PASS** only if a candidate passes Parts A, B and C (any one Part-C config). LEAD if A and B pass but not C, or B and C
pass with A short only on reps. FAIL if B fails on T2 for all three. Every candidate and config is reported.
Configs counted: 3 (B) + 12 (C) = **15**; cumulative N ≈ 8,952 → **≈ 8,967** (family bar sqrt(2 ln N) ≈ 4.27,
reference only). Part A is an audit of existing records (not counted as configs).
PRIME-RULES / C3-BAR2 pass/fail listed per candidate. Rule changes inside the live window listed from research/ledger.jsonl.
