# primary1029 - PLAN (written 2026-10-29 ~15:25 ET, after the live autopsy and a TRAIN-only description of the parent's
stacking context (`decomp_train.py`), BEFORE any configuration below was scored on valid or on the full history)

*Educational only — not financial advice. Two-year numbers are backtests; live numbers are paper (rule 7).*

## Question
Primary lost -11.3R / -$411 by 15:05 on 2026-10-29, mostly shorts from the RW3/RW5/MF2/MF4 family, with 3-lot stacks
on WDAY and NTSK and a late re-entry into IOVA. Find a rule that lowers down-day damage (worst days, red days, max
drawdown) while keeping trades, avg R per trade and total R not worse (within noise).

## What the TRAIN description already showed (so it is not "found" later)
- Later lots on a symbol are NOT worse per trade than first lots (train: lot 1 -0.092R, lot 2 -0.079R, lot 3 -0.040R).
  Same-poll triples are worse (-0.154R, n 396, se 0.045). Re-entry after a same-symbol target exit is better, not worse.
- So stacking is a variance (correlation) problem, not an edge problem. Any size cut on stacked lots will shrink their
  wins too; live (10-15..10-28) the stacked lots were the best trades (+0.79R per trade, mostly 10-22).

## Data, split, costs (fixed; same engine as p3_1029)
- Signals: p3_1029 `bt.py` output (open months only; locked block 2024-11-01..2025-02-28 never loaded, asserted).
- Portfolio: `sim.py` (= p3 evalp parent: setup_order priority, <= 3 same-side lots per symbol, no opposite side, 30
  per setup, 77 in all, 5-min path, stop first, 15:55 flatten, production costs). ST-P (-2R latch) not modelled in the
  parent (it is live-only); it is tested here as a control row (D0).
- TRAIN <= 2025-12-31, VALID 2026-01-01..2026-10-07. Regimes `lib.regimes()`.

## Configurations (round 1, 14)
Size rules keep every trade (w = lot size as a fraction of a normal lot; R reported per trade is unchanged, the
account's R is sum(w x r)):
- W1 poll-split: lots taken on the same symbol+side in the same poll share 1R (w = 1/poll_n).
- W2 later lots half: w = 0.5 when lot_seq >= 2.
- W3 harmonic: w = 1/lot_seq.
- W4 profit-gated: lot_seq >= 2 at w = 0.5 unless every open lot on the symbol is >= +0.25R at this entry price.
- W5 = W1 then W4 (same-poll split; a later-poll lot half unless the open lots are >= +0.25R).
- W6 ticker cap 1.5R: lot 2 at 0.5, lot 3 blocked.
Blocks (change the trade list):
- B5 one short-family lot per symbol per day.
- B6 a later lot only if every open lot on the symbol is >= +0.25R.
- B7 no re-entry within 60 min after a same-symbol same-side target exit.
Brakes:
- D0 ST-P as live: a setup takes no new entries after its realized day R <= -2 (control: what live already has).
- D1 after 2 same-symbol same-side stops today, block that symbol+side.
- D2 after 3 short-family stops today, family lots at w = 0.5 for the rest of the day.
- D3 after account realized day R <= -4 (full lots), new lots at w = 0.5.
- D4 after account realized day R <= -8, new lots at w = 0.5.
Control (counted): for each size rule, U(w) = every trade scaled by that rule's mean weight (same exposure, no
selection). A size rule is only useful if it beats its own uniform control.

## Scoring (fixed)
Per config, all / train / valid / up / down: n, avg R per trade (unweighted r), R per unit risk (sum wr / sum w),
total R (sum wr), worst day, CVaR5 (mean of the worst 5% of days), red days, max drawdown of the daily cumulative R,
day sd, and the paired daily delta vs the parent (day-clustered t).
**Qualify** (all must hold, in train AND valid): (1) CVaR5 better than the parent; (2) red days not more than the
parent's; (3) total R delta >= -1 SE of the paired daily delta (not worse within noise); (4) R per unit risk >= parent
- 0.01; (5) for size rules: CVaR5 and max DD per unit |total R| better than its uniform control U(w).
Primary bar for adoption: paired delta in CVaR-days (worst 5% of parent days) with day-clustered t >= max(1.5,
sqrt(2 ln N)), N = lineage count (p3_1029 B1-B4 = 4 prior + every config here).

## Rounds (max 4, stop when a config qualifies and its neighbour also qualifies, plateau)
- Round 2: neighbourhood of the best round-1 config (thresholds 0.0 / 0.5R for W4/B6; poll-split floor 0.5; D3/D4 at
  -3/-6/-10; B7 at 30/120 min). Declared here; exact rows written to `counts.json` before scoring.
- Round 3: pairs of the round-2 bests. Round 4: only if round 3 leaves a near miss.
- Live check (10-06..10-29 current-8 trades, paper): every qualifier is replayed on the live trades with the same rule.
- Holdout: at most ONE look at the locked block, only for a finalist that beats the parent on train AND valid.

## Amendment 1 (2026-10-29 ~15:40 ET, after round 1, before round 2 was scored)
Round 1 (`results_r1.csv`, 14 configs + 9 uniform controls = 23 counted) showed: (i) every stacking size rule (W1-W6)
is no better than shrinking every trade by the same average amount (its U control), because on two years later lots are
not worse per trade; (ii) the two brakes with selection value are D0 (ST-P, already live) and D2 (after 3 short-family
stops, family lots at half size): D2 beats its uniform control on CVaR5, total R and R per unit risk; (iii) every
brake and size rule adds red days (a smaller afternoon cannot pull a red morning back to green), so qualify rule (2)
fails for all of them; this is reported, not re-defined.
ST-P is live from 2026-10-29, so **round 2 uses D0 (ST-P on) as the base** and tests on top of it (counted):
- R2a D0+D2 fam>=3 stops half; R2b fam>=2 half; R2c fam>=4 half; R2d fam>=5 half; R2e fam>=3 at w 0.33; R2f fam>=3 block;
- R2g D0+W1 poll-split; R2h D0+W1+D2(3); R2i D0 + account (any setup) stops >= 3 half; R2j account stops >= 4 half;
- plus the uniform control of every size row. Base row D0 is not counted again.

## Amendment 2 (2026-10-29 ~15:48 ET, after round 2 and the live replay, before round 3 was scored)
Round 2 (19 counted): the family brake beats its uniform control in VALID for every threshold (2-5 stops) but in TRAIN
only at 2 stops; live (current-8, 16 sessions) the 3- and 4-stop versions raise total R and $ while cutting 10-29 by
~2.8R, and the 2-stop version halves 10-22. Backtest days carry ~3x live's trade count, so a stop COUNT trips far earlier
in the backtest than live. Round 3 (counted, + uniform controls) tests the net-R version, which counts wins too:
- R3a D0 + short-family realized day R <= -2 -> family lots half; R3b <= -3; R3c <= -4;
- R3d D0 + (family stops >= 3 AND family realized day R < 0) -> half.
Added scoring (all rounds, no new configs): paired daily delta of each size row vs its uniform control U (mean, t,
train, valid) - the test of whether the rule SELECTS, rather than just shrinks a losing book.

## Amendment 3 (2026-10-29 ~15:25 ET, before round 4 was scored)
Round 3 left no qualifier and the out-of-account live check (other_accts.py) showed no loss persistence, so the brake
family is closed. Round 4 tests the autopsy's own lead (e): short-family entries fading a stock that already trades
above today's open (NTSK 10-29). Open = the history's daily open (`lib.daily`). Size versions keep every trade (counted,
each with its uniform control), ST-P base:
- R4a family short, gap < 0 and entry > open -> w 0.5; R4b family short, entry > open (any gap) -> 0.5;
- R4c family short, entry > open x 1.01 -> 0.5; R4d = R4a as a block (skip) for reference.

## Amendment 4 (2026-10-29 ~16:20 ET, after the close, before round 5 was scored)
The final pull shows 2026-10-29 was an **up** session for the universe (median open-to-close +0.48%, 68% of names up;
history cut for "up" is +0.21%) even though QQQ fell, and the short family's two-year expectancy is -0.22R in up
sessions vs +0.065R in down sessions. The session class is only known at the close, but the lab context column
`breadth_open` (share of the universe above its own open at the decision bar; available live via LabStrategy context)
is known at entry. Round 5 (size versions keep every trade; ST-P base; each with its uniform control):
- R5a family shorts at w 0.5 when breadth_open >= 0.55; R5b >= 0.60; R5c >= 0.65; R5d >= 0.60 at w 0 (skip, reference).
