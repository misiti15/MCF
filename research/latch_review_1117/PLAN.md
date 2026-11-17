# LATCH review 2026-11-17 — plan (written before any scoring)

*Educational only — not financial advice.* Research only: no config, setup or exit change in this folder.

Owner 2026-11-17 ~13:45 ET: "LATCH review yes … certain setups do need certain conditions … a -2R cap across the
entire board may be a great safety gate but it also could hinder some setups if we want to open it slightly."

## Data (live journals only; locked block 2024-11-01..2025-02-28 is never read)
- journal.db from the state branches mcf-data (Primary), mcf-data-testing (On Deck), mcf-data-testing2 / -explore1 /
  -livelab / -testingd / -testinge / -testingf (Testing A-F), mcf-data-gen, as of 2026-11-17 after the close.
- Live trades = run_id 1. What-ifs = run_id 2 (`meta why=setup daily loss limit` = the post-latch blocked signals,
  simulated by the runner's what-if engine to 15:54 with the signal's own stop/target; entry slip in, exits raw).
  Shadow = run_id 3: not used.
- Blocked signals: signals.status='skipped', reason='setup daily loss limit', deduplicated on (ts, symbol, setup)
  (each skip is journaled twice). A 1-minute Alpaca replay is used only for blocked signals with no what-if row.

## Costs
- Live trades: R after costs (mcf.costs.cost_r: pnl_adj / risk; LR8 model from 2026-11-12, flat allowance before).
- What-ifs: r_multiple minus the setup's measured live gap (mean r_raw − R after costs over its live trades in that
  account; 0.05R when it has < 10 live trades there).

## Part 1 — latch review
A. **Actual latch days** (a setup really latched; Primary from 10-29, Testing 1/2 + On Deck 10-20..10-22, Graveyard not
   in scope): post-latch trades = the what-ifs, with the 3-lots-per-symbol cap (live lots of every setup in that
   account on that symbol + accepted hypothetical lots; same side only) applied in entry order.
B. **Virtual latch days** (latch off: every other account-day where a setup's running realized R after costs, in exit
   order, reached ≤ −2R): post-cross trades are real fills. This is the largest clean sample of "what a setup does
   after −2R" and is reported separately from A.
C. **Level replay** for each latch level L ∈ {−2, −3, −4, none}: per account-day, all trades (live + post-latch
   what-ifs) are re-run in time order; a setup is latched from the exit that takes its running R to ≤ L; entries after
   that time are dropped. The account halt is kept: −20R in Primary (R after costs from 11-12, raw before, as LR3),
   each other account at its own configured halt (120R / 300R). Lot cap as in A.
   Simplifications (stated, not hidden): extra hypothetical lots do not crowd out other setups' slots; Primary's
   LR3 open-mark halt is approximated with realized R.

Per setup: latch days, blocked signals, post-latch trades after the cap, post-latch R per trade and total, best-day
share of the post-latch total, and day-level R (sum over its latch days) under each level.

**Recommendation gate (fixed now):** a per-setup level other than −2 only if ALL hold: ≥ 5 latch days (A+B pooled),
post-latch total R > 0 AND > 0 without its best day, no single symbol > 50% of the post-latch positive R, and the
chosen level beats −2 on day-level R without the best day. Otherwise: keep −2 (no change).

## Part 2 — two targeted remedies (all live trades, all accounts, R after costs)
- (a) REENTRY-N: after a stop exit, the same setup takes no new entry on the same symbol for N decision bars (5-min):
  N ∈ {6 (30 min), 12 (60 min), rest of day}.
- (b) FADEMOVE-X: skip an entry when the symbol has already moved more than X% from today's open against the trade
  (long: price ≤ open × (1 − X); short: price ≥ open × (1 + X)), X ∈ {10, 15, 20}%. Open = Alpaca SIP daily open;
  price = the trade's entry.
- Removal-only (dropped trades are not replaced by other signals). Per setup and per family: trades removed, ΔR,
  count of setups improved / worsened and by how much, total. A remedy is called "targeted" only if it removes
  < 5% of all trades, improves the total, and worsens no setup by more than 1R.

## Configurations tried (counted up front)
Latch levels 4 (−2 baseline + 3) + REENTRY 3 + FADEMOVE 3 = **10 configurations** (9 non-baseline).

## Rule changes inside the window
Listed in NOTES.md from research/ledger.jsonl effective dates (latch on/off dates per account, LR3/LR8 cost basis
from 11-12, halts 120 → 300 from 11-12, TSZ1 sizing 11-17, Primary TEAM-6 from 11-11).
