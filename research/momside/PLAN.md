Educational only — not financial advice.

# MOMSIDE — slow 12-1 momentum as a side filter on intraday setups (Builder, frozen 2026-11-14 ~10:40 ET, BEFORE any score)

Brief: Lead lead-20261114-0900-2 (Observer D2, Skeptic pre-audit skeptic-20261114-0851-2). One score; no tuning after this commit.
Only dated amendments below, each written before the score, may change it.

## Question
Do intraday lab trades do better when their side agrees with the name's slow 12-1 momentum (longs on strong names, shorts on
weak ones)? As a FILTER, the rule skips COUNTER trades (longs on weak, shorts on strong). It must beat a random same-share skip
within the same setup-day (checklist 9: losing-book volume cut).

## Data (fixed)
- Trades: research/compassbf/trades_tagged.parquet (75 setups, 2-year lab lists, both sides, production costs; locked block
  2024-11-01..2025-02-28 never read). Earnings-blackout trades (+-4 sessions, mcf GD._blackout) removed (checklist 18).
- Universe for deciles: research/lab_symbols.txt (fixed lab list, checklist 19).
- Daily closes: Alpaca SIP 1Day split-adjusted, lab symbols + SPY, 2023-09-01..2026-11-13, fetched after 16:05 ET or on a
  weekend (read-only GETs, keys from env, never printed). Cached to research/momside/data/ (git-ignored).

## 12-1 momentum (point in time, checklist 2 and 8)
- For trade date D: mom = close(D_-21) / close(D_-252) - 1, where D_-k is the k-th session strictly BEFORE D (D_-1 = prior close).
- Window RESTART at the locked block (Skeptic 2, checklist 8): mom is NaN if any session in [D_-252, D_-1] falls inside
  2024-11-01..2025-02-28 (no stretching across the hole; locked prices never read). Also NaN with < 253 prior sessions.
- Deciles 1-10 across the lab universe names with a valid mom on date D (ties by rank, method first).
- Consequence, stated now: tagged trades exist only on dates up to 2024-10-31 and from ~2026-03-03 on. TRAIN (<= 2025-09-30)
  is therefore 2024-10 only (~10.5k trades, ~23 days): LOW POWER, used as a sign check. VALID = 2026-03-03..2026-10-07 is the
  primary test. FWD = 2026-10-08..2026-11-13 reported.

## Configurations (3; cells shown = 3 configs x 3 periods x {gross, ex-market, net}, checklist 26)
- C1 (primary): counter = long in deciles 1-3 or short in deciles 8-10; skip counter.
- C2: stricter: counter = long in 1-2 or short in 9-10.
- C3: longs-only leg of C1 (skip longs in 1-3 only): the survivorship-conservative read (Skeptic 1).

## Score (within setup-day, as REGSW-2 S2-S4)
- delta = -sum(R of skipped trades) per day; control = expected delta of a random skip of the SAME count within the same
  setup-day = (k/n) x setup-day total R; excess = delta - control, summed per day; day-clustered t over days.
- Columns: gross R, EX-MARKET (gross - beta_setup x SPY move over each leg's own hold; beta per setup by OLS on ALL TRAIN
  trades, tagged or not, checklist 16), net r. Gross first (checklist 17). Also print the control's own avg R and the
  kept trades' avg R (checklist 10), the skip share, by side, by SPY up/down/quiet day (reporting only).
- Per setup (setups with >= 10 skipped trades in the period): excess per trade, count better / worse, worst setup.
- Best-day share of the excess; total without the best day.

## Family and bar (checklist 24)
longhold 105 + RS63 rework 31 (sat1017 lineage) + leader/laggard spread 8 + ex30 cross-sectional 39 + MOMSIDE 3 = 186.
Bar = max(1.5, sqrt(2 ln 186)) = 3.23; BAR90 = 2.91.

## Pass / kill line (C1 primary; C2/C3 reported, a C2/C3-only pass is a lead, not a pass)
PASS only if ALL: (1) VALID ex-market excess > 0 with day-t >= 2.91; (2) TRAIN ex-market excess > 0 (sign only, low power);
(3) >= 60% of setups better in VALID (per-setup ex-market excess per trade); (4) best day < 50% of VALID excess;
(5) gross excess > 0 in VALID. Else CLOSED. FWD is reported, never a gate. Survivorship (Skeptic 1): today's lab list drops
delisted names, so past 'weak' names are survivors (biased to rebounds): this biases AGAINST skipping longs-on-weak... and
flatters skipping shorts-on-weak; C3 (longs only) is printed beside C1 and a C1 pass whose C3 is <= 0 is reported as
'short-leg-driven, survivorship-suspect'. Not measurable directly (dropped names are absent); stated, not corrected.

## Companion
Observer's research/momside-live (frozen 11-14 ~09:50) runs on LIVE trades only AFTER this result is posted; descriptive.

## Checklist walked (research/SKEPTIC_CHECKLIST.md)
1 index wrap: session offsets via searchsorted on a per-symbol date index, assert k >= 0 | 2 strict prior close | 3 no
defaults | 4 no whole-day labels (12-1 known at the open) | 5 n/a | 6 n/a | 7 daily bars are final closes | 8 gap restart |
9 random same-share skip within setup-day | 10 control avg R printed | 13 stratified by setup-day | 16 ex-market | 17 gross
first | 18 blackout removed | 19 fixed lab list | 24 family 186 | 26 cells counted | 37 lab R only (no live pnl_adj).
