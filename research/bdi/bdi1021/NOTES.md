# BDI 2026-10-21: every trade of the 5 accounts, and one small swarm ("index low is in" gate)

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7), one session, so they are a
diagnosis, not evidence. History numbers are **backtests** on the open two-year history with production costs in.
The locked block (2024-11-01..2025-02-28) was never read and no holdout was scored. No config, setup or exit was
changed and nothing was routed (the owner decides G1 / N5 / N6 first).*

Already done tonight and **not redone here**: `research/bdi/nightly1021/` (per-account P/L, autopsy with SIP 1-min
MFE/MAE for all 696 trades, give-back, −2R stop overshoot, N5/N6), `research/bdi/gates1021/` (NS3-FD / L3-FD autopsy,
718 direction-gate configs, G1) and `research/bdi/reddit1021/` (183 configs, none pass). This run adds the per-trade
management what-ifs, the opposite-side hindsight check, loss types into `patterns.csv`, and one 196-config swarm.

## Failures first
1. **The swarm failed: 0 of 196 configurations pass** (`results.csv`, `counts.json`, `swarm_out.txt`; plan in
   `PLAN.md`, written before scoring).
   - The idea comes from the owner's chart reads (10-15 week, 10-20) and from today: SPY dipped to −0.36% at 10:12,
     then large caps rallied while the short books were open. The gate blocks new shorts once SPY has bounced
     ≥ 0.3% / 0.5% off its session low (low by 10:30, or any time) and is back above its session VWAP. Long setups
     get the mirror ("high is in"). That is 4 gates × 49 live setups.
   - 17 rows show a stable train/valid split. All 17 lose money in down sessions, and none reaches the bar
     (lineage N 914 with gates1021: t ≥ 3.69). The best row is MF4-h40-open-flowsell-FD S3: all-data delta t 3.96,
     but its down-session delta is −0.015 and the gated setup is still −0.039R in valid.
   - Pooled over the 36 short setups, the gate removes shorts that are **better** than the setup's average:
     −0.019R per trade in train and −0.014R in valid. Random same-minute shorts in that state are worse (+0.022
     control delta), so this is plain up-day beta: up sessions +0.034, down sessions −0.060.
   - Today itself does not support it either. Shorts entered in state S1 averaged −0.368R, against −0.284R outside it.
     Most of the short losses came from entries made *before* SPY reclaimed (`today_state_out.txt`).
   - The long side of the same chart read was already tested in longs1020 (0 of 200). Both sides of "morning dip,
     then rally" have now failed as a rule known at the minute of entry.
2. **The opposite side "worked" today, but only in hindsight** (`out_1021.txt`).
   - Taking the opposite side of every trade at the entry price, with 1R/1R, would have made **+94R** today
     (60% win). Yesterday the same flip would have **lost 98R**.
   - The rules known at entry did not point that way. Shorts entered while SPY was already ≥ +0.25% from its open
     did *better* (+0.03R) than the other shorts (−0.38R), so SPY's move from the open sorted them the wrong way.
     The stock's own from-open move (±1%) did not separate them either.
   - No opposite-side rule is proposed. Older items covering this: `loop-1009-opposite-side-family`,
     `nl-1007-opposite-side` (failed) and gates1021.
3. **No exit or management rule helped on both days.** Each line is SIP 1-min, costs in, compared with the same
   simulation of the original bracket. (The simulated bracket was −84.8R on 10-21 against −97.0R live, and +67.3R on
   10-20 against +48.9R live: the simulation is optimistic by about 12–18R a day.)

   | what-if (all accounts) | 10-21 | 10-20 |
   |---|---|---|
   | breakeven at +0.5R | +7.9R | −9.4R |
   | +0.5R target | +11.4R | −7.4R |
   | +1R target | −41.8R | +16.3R |
   | 0.5R trail after +0.5R | −2.9R | +30.9R |
   | hold to 15:55, no target | −132.2R | +3.6R |
   | stop-and-reverse (1R/1R) | **−28.1R** | **−12.9R** |
   | one re-entry after a stop | −14.2R | +21.0R |

   - Stop-and-reverse is negative on both days, which matches the failed `bdi1014-cwt14-sar`.
   - Every other lever flips sign with the day's direction. Re-entry for CWT14 was already tested on the history
     (top5_1020 E13, failed).
4. **Not done:**
   - the 10-21 rule values at entry beyond what the journals keep. The signal `info` holds spread and layer only, so
     the context columns (stock from-open, VWAP distance, 15-min return, SPY from-open) were rebuilt from 1-min bars.
   - GEN and LD/M1 managed-trade checks beyond the table: GEN had 13 trades, and LD/M1 sent no signals.

## What was done
1. **Every trade** (696 on 10-21; 484 on 10-20 as a backfill: `patterns.csv` had no 10-20 rows).
   - `trades_bdi.py` reads `nightly<MMDD>/trades.csv` plus SIP 1-min bars and writes `per_trade_<MMDD>.csv`.
   - Columns: context at entry, MFE/MAE/time to MFE, the what-ifs above, the opposite side, hindsight flags and the
     loss type.
   - It also writes `by_setup_<MMDD>.csv`, and `out_<MMDD>.txt` holds the summaries.
2. **patterns.csv:** +175 loser rows for 10-20 and +324 for 10-21 (2,330 → 2,829 rows). The classifier and column
   format are the same as nightly1019. `merge_patterns.py` is idempotent by date.
   - Today's loss mix compared with 10-12..10-20:
     - small MFE then failed: 23.5% (was 20.7%)
     - late hold: 14.5% (was 10.9%)
     - never worked: 22.2% (was 23.7%)
     - wrong side after a big swing: 13.6% (was 16.0%)
   - By account (count of losers / $):
     - Graveyard: small-MFE 46 / −$815, never-worked 36 / −$610
     - Testing 1: small-MFE 26 / −$260, never-worked 22 / −$201
     - Primary: wrong-side 11 / −$379, the NS3-FD miners
3. **Intraday give-back** (numbers from nightly1021, not recomputed):
   - Primary $717 from peak to close: open NS3-FD / L3-FD shorts stopped in the 13:00–14:00 squeeze (gates1021).
   - Testing 1 $597 and Graveyard $946: new shorts entered *after* the account peak (−$519 / −$671), not winners
     giving back.
   - Every lever for this is already in the backlog:
     - `gb-1019-post-peak-index-guard` (failed)
     - `nightly-1020-setup-loss-limit-open-risk` (Saturday replay)
     - `gb-1019-twin-setup-exposure`
     - `nightly-1013-stack-clone-skip`
4. **Recurring patterns (≥ 3 sessions, still present on 10-21)** were checked against the 566 backlog items. Most
   are already covered:
   - CWT14 failbrk never-worked / small-MFE: the top5 execution tunes, the day-class gates and N6.
   - heat_fade_short-FD and RW2: the top5 execution tunes.
   - L3-FD wrong side: gates1021.

   Two are new and went to the backlog as ideas (tag `bdi-1021`, status idea, 0 history configurations):
   - `bdi1021-cwt12k6-breakeven`: CWT12-coil-k6-long gave back gains on 5 sessions (20 losers). Today 10 of its 20
     losers reached +0.5R first, and breakeven would have taken it from −6.7R to −0.5R. The prior is weak: the k4
     sibling's breakeven variant failed.
   - `bdi1021-hfl-fd-hold-no-target`: heat_fade_long-FD gave back gains on 6 sessions and was on the wrong side on 5.
     Over 2 days, holding to the close would have added +15.7R and a re-entry +8.4R (21 trades). Both days were
     up-tape afternoons for longs, so this is likely regime.
5. **Swarm entry:** `bdi1021-index-low-in-short-gate`, status **failed**, with its numbers (196 configurations).

## Day-over-day
- 10-20 → 10-21 after costs:
  - Primary −$46 → −$627
  - Testing 1 +$692 → −$548
  - Testing 2 +$281 → −$15
  - Graveyard (new): −$747
  - GEN: +$420
- Why it got worse: the book is mostly short (bdi1019: 83%). 10-20 rewarded the shorts (L3-FD in T1 made +$655);
  10-21 was a large-cap up-tape from 11:00. Two different market directions on consecutive days, and no rule known at
  entry told them apart, either tonight (196 configs) or in gates1021 (718).
- Next: the open-risk loss-limit replay on Saturday 10-24 (LL-OPEN). Then the two new exit ideas on the history
  (top5_1019 harness), and the owner's G1 / N5 / N6 answers.

## Files
- `trades_bdi.py`
- `per_trade_1021.csv`, `per_trade_1020.csv`
- `by_setup_1021.csv`, `by_setup_1020.csv`
- `out_1021.txt`, `out_1020.txt`
- `patterns_1021.csv`, `patterns_1020.csv`
- `merge_patterns.py` (copy of bdi1019's)
- `PLAN.md`, `swarm.py`, `results.csv`, `counts.json`, `swarm_out.txt`
- `today_state.py`, `today_state_out.txt`
- `backlog_proposals.jsonl`

Bars and journals stay in scratch.

Educational only — not financial advice.
