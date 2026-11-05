# SIZE1 — sizing study for live funds (owner 2026-11-04) — PRE-REGISTRATION

*Educational only — not financial advice. Written 2026-11-04 after the close, before any SIZE1 configuration was
scored. Research only: nothing in config/ or the trading path changes.*

Seed: `research/ops/sizing1104/NOTES.md` (17 live sessions, top-5 picked in hindsight). Not repeated: SZ-PROOF
(`research/ops/sizing_proof.md`, proof tiers balanced out, 10-27) — weights here are TRAIN-derived only and are
normalised so they redistribute risk, never add it.

## Data and windows
- **2-year lab trade lists** `/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet` (production costs,
  stop first, 15:55 flatten; uncapped signal chains; entry = close of bar `tod`, exit during bar `xtod`).
  Stop distance per trade = GEOM stop multiple x 0.25 x `atr_d` / entry close, joined from the lab frames
  (`research/history2y/lib.load_month`, open months only).
  - **TRAIN** = 2024-10 + 2025-03..2025-12 (11 open months). **VALID** = 2026-01-02..2026-10-05.
  - Lab trades dated 2026-10-06..11-04 are NOT used (that is the live window).
  - **Locked block 2024-11-01..2025-02-28 is never read** (no trade files exist for it; loader refuses it).
- **LIVE (paper)** = journals `origin/mcf-data`, `-testing`, `-testing2`, `-graveyard` `journal.db`, run_id = 1,
  2026-10-06..2026-11-04, closed trades; R = pnl_adj / (|entry - stop| x shares); stop fraction = |entry - stop| /
  entry; duplicates (same setup, symbol, entry time) dropped. Live trades are the trades the live engines actually took
  (signals blocked by slots/caps there are absent), so live is a censored signal list. Paper fills; pnl_adj on.

## Books
- **A (top-5).** LIVE: the five named setups (11-03 shrunk-avg-R top 5): MF2-open-rsimidhi-flowsell-FD,
  RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, RW3-gapdn-rsi5pop-flowsell-short-FD, L3-gap-slope-fromopen-FD,
  NM-MF3-qqqdn-gapdn-FD. 2-YEAR: re-ranked on TRAIN only — the top 5 by TRAIN shrunk avg R (mean x n/(n+20)) among
  the lab-covered setups with >= 20 live trades by 11-03 (49 setups; the pool uses trade counts only), TRAIN n >= 100.
- **B (Primary).** The 10 enabled setups of `config/default.yaml` (all lab-covered), same lists on 2-year and live
  (live = their trades in any account).

## Engine (same for every config)
$100k start; risk $ = risk% x equity at start of day x weight x half-size factor; notional = risk $ / stop fraction;
a trade is skipped (not shrunk) if open notional + notional > BP x equity; equity compounds daily. Exits free buying
power at their exit bar before entries of that bar. Max 3 same-side lots per symbol, no opposite side, twin
(X / X-FD) never on the same symbol, max 30 open per setup, 77 concurrent, per-setup daily stop -2R latched and
account -20R daily stop (today's Primary risk controls; R in units of the base risk). No per-position notional cap in
the grid (sensitivity rows below add the 10% cap).

## Knobs / configurations (all counted)
- Stage 1 grid per book: risk {0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50}% x BP {1x, 2x, 4x} x allocation
  {FC first-come (lab: random order within a 5-min decision bar, seed fixed; live: actual entry time),
  QS ranked by TRAIN shrunk avg R within the bar, QX ranked by TRAIN ex-market avg R (trade R minus the mean R of all
  95 lab setups' same-side trades that date) within the bar, FAM first-come but one new entry per family per bar}
  = **84**.
- Stage 2 per book, each on top of (a) the baseline and (b) the TRAIN-selected stage-1 config:
  WT TRAIN tiers (book tertiles by TRAIN shrunk avg R -> 1.5x / 1.0x / 0.5x, rescaled so the TRAIN trade-weighted
  mean weight = 1); HQ1 half size if SPY |% from open| < 0.15% at entry; HQ2 half size if SPY 30-min high-low range
  (last 30 1-min bars before entry, % of price) < its median at the same time of day over the prior 20 sessions;
  HB half size on the 3rd+ entry of the same family within 15 min (entries taken); ALL = every stage-2 rule that
  raised TRAIN return/DD on (b) = **5 x 2 = 10**.
- Sensitivity: baseline and selected with a 10% per-position notional cap = **2**.
- **N = 96 per book, 192 total.** Bar = max(1.5, sqrt(2 ln 192)) = **3.24** on the VALID day-clustered t of
  (config daily P/L % - baseline daily P/L %).
- Families: setups with "flowsell" in the name, MF*, RW1/RW3/RW5 and NM-MF3 = FLOW-S (short flow-sell); otherwise
  the first name token (L3, ST7, NS1, NS5, CWT14, ...).
- **Baseline** = 0.25% risk, 4x BP, FC, no weights, no half size (today's Primary rule).

## Metrics (TRAIN, VALID, LIVE)
Return (compounded), max drawdown (daily closes), return/|DD|, green-day rate in R (days with trades whose taken R
sum > 0), avg R per trade taken, avg R without the best day + the best day's share of total R, trades taken,
t of daily P/L (% of equity, all sessions), R per unit of risk (weighted).

## Selection (TRAIN only)
Stage-1 selected = highest TRAIN return/|DD|; any config within 5% of that ratio -> the higher TRAIN return.
Second finalist = highest TRAIN return with max DD no worse than -10%. Finalists reported on VALID and LIVE:
baseline, both selected, the TRAIN-best of each allocation rule and of each BP, every stage-2 row, the two
sensitivity rows. A rule is recommended only if it clears the bar vs baseline on VALID and is not negative vs
baseline on LIVE (and LIVE is not carried by one day).
