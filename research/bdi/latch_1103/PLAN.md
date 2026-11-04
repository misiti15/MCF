# latch_1103: which kinds of setups does the per-setup daily latch help? (pre-registration)

*Educational only — not financial advice.* Written 2026-11-04 before any result was computed. Research only:
nothing in config/, mcf/, the setups, exits, docs/live or the ledger is changed.

## Question (owner 11-03)
Primary's per-setup latch (`account.max_setup_daily_loss_r: 2.0`, live from 2026-10-29): once a setup's net realised R
that day reaches -2R it takes no new entries that day. It saved 16.8R on 11-02 and cost 8.19R on 11-03 (RW3-FD latched
10:47; 13 blocked entries would have made +8.19R). Do some KINDS of setups gain from the latch and others lose?

## Data
- **(a) Backtest:** every enabled `type: lab` setup in config/default.yaml, account_testing.yaml, account_testing2.yaml,
  account_graveyard.yaml and account_gen.yaml (deduplicated by name; first account in that order wins for params).
  Signals from the two-year lab frames (`research/history2y/lib`, open months only; locked block 2024-11-01..2025-02-28
  never read, `MCF_HIST_ALLOW_LOCKED` unset and asserted). Same signal rules as `research/bdi/p3_1029/bt.py` (mask,
  window clipped to 09:50-15:00, min_adv, gap prefilter, refire chain) and **each trade walked on the 5-min path after
  the entry bar (stop first in a bar, flatten 15:55 via the head/tail file)** so every trade has an entry AND exit
  time (the lab outcome columns have no exit time). Production costs as bt.py (1c + 1bp per side, +2c on stops, 3x on
  extended-tier names, time-of-day entry multiplier). Base exits only (no scale-out, no trail). Setups that are not
  lab masks (heat, classic, index-dip, symbol allow-lists) are listed as not covered.
- **(b) Live (paper, rule 7):** journals of Primary, Testing 1, Testing 2, Graveyard, Setup Generator
  (`origin/mcf-data*` `journal.db`), 2026-10-06..2026-11-03. "Latch off" sequence per setup-day = taken trades (run 1)
  + what-if trades of signals skipped for `setup daily loss limit` (run 2, the runner's own what-if outcomes). Any
  level is then simulated on that sequence. Slots / lot caps / other skips are not re-modelled (second order).

## Simulation
Per setup, per day, independently of other setups (the latch is per setup). Trades in entry order; a trade is
blocked if the setup's realised R from trades that EXITED at or before its entry bar is <= -L (latched: once touched,
blocked for the rest of the day, as live since 10-23). Blocked trades also do not count toward realised R.
Levels **L = 1.5, 2, 3** vs **off**. Delta per setup-day = R(latch) - R(off) (> 0: the latch saved R).

## Split
TRAIN = open dates <= 2026-02-28 (about 2/3 of the open sessions); VALID = 2026-03-01..2026-10-07. Live = 10-06..11-03.
Every categorizer that uses a setup property (win rate, frequency, autocorrelation) measures it on TRAIN only.

## Categorizers (fixed here; every cell is reported, effect or not)
1. **side:** long / short.
2. **family:** name prefix before the first digit or dash: MF, RW, NS, ST, CWT, L3, GEN, other (anything else, incl.
   NM, LD, LIQ, exhaustion, heat).
3. **entry style** (name keywords, first match wins): *reclaim* (reclaim, vwapx, failbrk, failed) > *fade*
   (rsi5pop, rsi5hi, overbought, oversold, exhaustion, fade, bounce, flush, dip, stretch, rsimidhi, rsi50dn, ordn, rsi5up,
   up3, lh, backside) > *breakout/momentum* (brk, break, slope, emadn, volspike, flowsell, coil, flag, thrust, trend,
   momentum, vwaploss) > *other*. GEN setups classed from their spec conds by the same keywords.
4. **frequency:** TRAIN trades per active setup-day >= 2.0 (high) vs < 2.0 (low).
5. **exit geometry:** target/stop ratio > 1 (t1s05), = 1 (t1s1, t05s05), < 1 (t05s1).
6. **win-rate band (TRAIN):** < 45%, 45-55%, >= 55%.
7. **time window:** open-only (window end <= 11:00), mid (end 11:05-13:59), full day (end >= 14:00).
8. **day context (split by setup-day, not by setup):**
   8a. SPY vs open at the latch time (point-in-time): market AGAINST the setup's side (short latched with SPY above
       its open, long latched with SPY below) vs WITH it. Scored on latched setup-days only.
   8b. diagnostic only (not point-in-time): session type by SPY open-to-close on the session: trend (|oc| top tercile
       on TRAIN) vs quiet (bottom tercile) vs middle; and reversal (sign of SPY-vs-open at the latch time opposite to
       the close's sign).
9. **mechanism (the key test):** per setup on TRAIN, (i) the within-day lag-1 autocorrelation of trade R (consecutive
   trades in entry order, same setup-day, pooled within setup), split > 0 (clustering) vs <= 0; (ii)
   P(next trade loses | the last two realised trades that day both lost) - P(loss), split > +0.05 vs <= +0.05
   (point-in-time: only trades exited before the next entry count). Setups with < 20 qualifying pairs go to "n/a".
10. **cherry-pick control:** each setup's own TRAIN latch delta at L=2 (> 0 vs <= 0). This is the per-setup
    selection the owner warns about; it is reported as the benchmark a categorical rule must beat.

## Scoring per cell and level
Delta R per setup-day (sum over the cell's setups per date, day-clustered t over dates), total delta, delta per
latched setup-day, n latched setup-days, delta without the best date and that date's share. TRAIN and VALID separately;
live per account where the setups are covered (live is matched by category, not by setup).
**Configurations N** = levels (3) x all cells, plus the 3 all-setup rows; bar t >= max(1.5, sqrt(2 ln N)), counted in
`counts.json`.

## Decision rule (fixed)
A categorical split "latch on for X, off for Y" is a finding only if, at one level chosen on TRAIN, (1) the cell X has
delta > 0 and cell Y has delta < 0 on TRAIN, (2) both signs hold on VALID, (3) the X-minus-Y difference reaches the bar
on TRAIN or VALID-pooled, and (4) live does not contradict (signs, where n >= 5 latched setup-days). Otherwise: FYI and a
forward-shadow tally rule in research/bdi/swings/hypotheses.jsonl.

## Amendment 1 (2026-11-04, before any latch delta was read)
The raw lab signal lists have no account caps (CWT14 failbrk fires up to ~240 times a setup-day). Before the latch is
simulated, each setup-day applies the live caps that bind most: <= 3 open lots per symbol per setup and <= 30 open
positions per setup (Primary's per-setup cap). Only counts per setup were looked at to decide this.

## Amendment 2 (2026-11-04, before any VALID or full-history result was read)
Control (rule 6): a latch "helps" any setup with negative average R just by trading less. Every cell also reports the
**excess delta** x = delta + n_blocked x (the setup's own average R on that split): the part of the saving that comes
from the blocked trades being worse than the setup's average, i.e. from same-day clustering. A categorical rule must
work on delta AND on x. Pairwise contrasts between cells are counted in N as well (counts.json).
