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

## Amendment 1 (2026-11-14 ~12:20 ET, BEFORE any score; Lead lead-20261114-1100-1, Skeptic skeptic-20261114-1050-1)
- Strict window KEPT (rule 19: no locked-block prices, even as features).
- C4 added: 6-1 momentum = close(D_-21) / close(D_-126) - 1, same strict restart (NaN if any session in [D_-126, D_-1] is in
  the block; < 127 prior sessions -> NaN), deciles as C1 (counter = long in 1-3 or short in 8-10). Tags from ~2025-09-02, so
  TRAIN has 2024-10 (if 126 prior sessions exist) and 2025-09. C4 is a counted config, reported like C2/C3: a C4-only pass is
  a lead, not a pass.
- Family 186 + 1 = 187; bar sqrt(2 ln 187) = 3.23, BAR90 = 2.91 (unchanged at two decimals).
- Also fetched with the daily closes: Alpaca corporate actions (cash dividends) for Scout's SIZESTOP Amendment 1; MOMSIDE does
  not use them.

## Amendment 2 (2026-11-14 ~14:40 ET, BEFORE any score; Lead lead-20261114-1300-1, Skeptic skeptic-20261114-1250-1)
- Scope gap fixed: trades_tagged.parquet was the COMPASSBF afternoon subset (entries >= 12:00, plus CWT12). The input is now
  the FULL-DAY 2-year lab lists (research/history2y/data/bt_lab1104, all entry times): 1,176,959 trades, 95 setups, 449 days,
  69.6% of entries before 12:00. gross and spy_move rebuilt exactly as compassbf/retag.py (bt_all cost inverted; SPY entry bar
  close -> exit bar close), code in build_full.py, no outcome statistic printed while building. Same definitions, controls,
  gates. Family unchanged at 187 (sample completed, no new config). Observer's live companion uses all hours as its primary.

## Amendment 3 (2026-11-14 ~16:20 ET, BEFORE any score; reporting only, Skeptic skeptic-20261114-1450-1, Lead 15:00)
- Per config in VALID also print the top-5 setups' share of the total ex-market excess (setups with >= 10 skips) and their
  names (remedies rule: who carries it). No gate change.

## Amendment 4 (2026-11-15 ~06:25 ET, BEFORE any score; checklist #42, Skeptic skeptic-20261115-0951-2, Lead lead-20261115-0500-1; 0 configs)
Early-close sessions dropped entirely: 2025-07-03, 2025-11-28, 2025-12-24 (the 2024 half days lie in the locked block). The 1-min
cache carries after-hours prints after the 13:00 close (SPY 164 bars on 11-28), so the lab window (entries to 15:00, flat 15:55)
placed fills after the close. Outcome-free count on the full-day lists: 4,843 trades on those days (0.41%), 2,023 with entry or
exit after 13:00. Dropping the whole sessions is simpler and stricter than dropping only the after-13:00 trades.
