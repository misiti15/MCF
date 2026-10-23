# BDI 2026-10-23: every trade of the 5 accounts, and the wide-stop-% risk idea on two years of history

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7), one session: a diagnosis, not
evidence. History numbers are **backtests** on the open two-year history (train ≤ 2025-12-31, valid 2026-01-01..10-07)
with production + tier costs in. The locked block (2024-11-01..2025-02-28) was never read and no holdout was scored.
No config, setup, exit or assignment was changed, and no DECISION was added tonight.*

Already done today and **cited, not redone**: `nightly1023/` (P/L, poll coverage, autopsy, give-back, $-risk quartiles →
backlog `nightly-1023-wide-stop-pct-risk`, ST-P live replay, MF1-D / D2 decisions). Configurations today: nightly1023 4
(ST-P) + bdi1023 **30** = 34. 0 pass a bar.

## Failures first
1. **The nightly's new idea fails on history: 0 of 21** (`PLAN.md` written before scoring, `swarm.py`, `swarm_out.txt`,
   `results.csv`, `counts.json`). Skipping wide-stop-% entries (stop > 1.5 / 2 / 2.5% of price, or > the setup's own
   train 75th percentile) or down-sizing them (cap $ risk at slot × 1% / 2%, or equal $ risk) does not help any book
   (Primary, Testing 1, Testing 2; 49 cached live setups):
   - **On two years the widest-stop quintile is the best cell in valid in all three books**, the opposite of the live
     split: avg R after costs by stop-% quintile (train / valid):

     | book | q1 tight | q2 | q3 | q4 | q5 wide | q5 median stop % |
     |---|---|---|---|---|---|---|
     | Primary | −0.098 / −0.065 | +0.022 / −0.039 | +0.032 / −0.050 | −0.082 / −0.014 | −0.112 / **+0.028** | 3.15 |
     | Testing 1 | −0.120 / −0.076 | −0.067 / −0.013 | −0.091 / −0.038 | −0.080 / −0.030 | −0.060 / **+0.009** | 2.31 |
     | Testing 2 | −0.093 / −0.029 | −0.057 / −0.014 | −0.050 / −0.024 | −0.042 / −0.008 | −0.037 / **+0.037** | 2.62 |

   - Every skip variant improves train in Primary (+0.018..+0.038) but loses in valid (−0.002..−0.009) and in down
     sessions; T1/T2 are worse in valid too. Sizing variants: valid delta −0.010..−0.027 (slot-% units) in all 9.
   - Per setup, wide-stop is worse than the rest in both splits for only **3 of 53** setup×book rows.
   - Reading: the live 14-session split (wide-stop quartile worst in every account) is a sample / regime effect, or it
     lives in the CWT12/CWT14 family that the history cache does not cover (stated limit). Backlog entry → `failed`.
2. **The mirror rework (E, tight stops) is a near-miss, 0 of 9** (`PLAN.md` addendum declared after A-D were scored,
   `swarm_e.py`, `swarm_e_out.txt`, `results_e.csv`, `results_e_setups.csv`). Skip if stop < 0.4 / 0.5 / 0.6% of price:
   - **Delta vs the parent book is positive in train AND valid in all 9**, beats the same-minute random control in
     both, all-data day-clustered t **3.32..5.73** (8 of 9 ≥ 3.79), keeps 78-95% of trades.
   - **It fails** because the gated books stay negative after costs (E0.5: Primary −0.034 / −0.017R, T1 −0.074 /
     −0.017, T2 −0.045 / −0.001; n train / valid: Primary 44,570 / 47,662, T1 54,549 / 61,260, T2 41,526 / 45,611) and the delta is slightly negative in
     down sessions (−0.002..−0.024). Not clean: the direction was seen in the quintile table first.
   - It is a cost effect (same per-share costs on a smaller R), the stop-% version of `gb-1019-noise-floor-stop`.
     Per setup it rarely changes the sign; the only new positive-in-both is NM-MF3-qqqdn-gapdn-FD at 0.4% (train
     −0.010 → +0.017, valid −0.010 → +0.015, t 0.4 / 0.3: weak). No routing.
3. **Exit / management levers still flip with the day** (all accounts, Δ R vs the simulated bracket, SIP 1-min, costs in;
   `out_1023.txt`, bdi1021/bdi1022 for the earlier days):

   | lever | 10-20 | 10-21 | 10-22 | **10-23** | 4-day |
   |---|---|---|---|---|---|
   | breakeven at +0.5R | −9.4 | +7.9 | −12.8 | −5.7 | −20.0 |
   | +0.5R target | −7.4 | +11.4 | −48.2 | +14.6 | −29.6 |
   | +1R target | +16.3 | −41.7 | −18.2 | +19.6 | −24.0 |
   | 0.5R trail after +0.5R | +30.9 | −2.8 | +1.6 | **+14.8** | **+44.5** |
   | hold to 15:55 | +3.5 | −132.1 | −4.5 | −14.5 | −147.6 |
   | stop-and-reverse 1R/1R | −13.0 | −27.8 | +29.3 | −33.8 | −45.3 |
   | one re-entry after a stop | +20.9 | −14.2 | −19.6 | +10.1 | −2.8 |
   | opposite side 1R/1R | −165.8 | +179.0 | −11.4 | −63.9 | −62.1 |

   The 0.5R trail is the only lever ahead over 4 days (3 of 4 positive), but the book-wide trail failed on history
   (`t6-exit-overlay`, `sw-w4-book-exits`, `exit-cwt-trail-notarget`); 4 live days do not reopen it. Stop-and-reverse
   is negative again (−45.3R over 4 days). Re-entry after a stop −2.8R.
4. **Opposite side: no rule known at entry.** Today shorts entered while SPY was not yet up
   +0.25% would have done better reversed (opp +0.165 vs live −0.253R, n 88), and so would shorts on names already
   ≥ +1% from the open (+0.090 vs −0.187R, n 70), while shorts entered with SPY already up were fine (live +0.017,
   opp −0.044, n 114); on 10-22 the same flags sorted shorts the other way and on 10-21 not at all. It is the
   day's direction, not a rule known at entry. Nothing to propose.
5. **Owner chart reads: nothing new** (OWNER_CHART_READS.md unchanged since 10-20; 10-23 had no 09:45 SPY dip — low
   −0.16% at 10:27).

## What was done
1. **Every trade, 635 of 635 with bars** (`trades_bdi.py`, bdi1022's script unchanged, on `nightly1023/trades.csv` +
   SIP 1-min bars fetched read-only for 305 symbols): context at entry, MFE / MAE / time to MFE, the what-ifs above,
   opposite side with hindsight flags, loss type → `per_trade_1023.csv`, `by_setup_1023.csv`, `out_1023.txt`.
   - R after costs, live: Primary −2.1R (32), Testing 1 +5.3R (131), Testing 2 +18.2R (147), Graveyard −24.6R (274),
     Generator +5.8R (51).
   - **Long vs short** (mirror of 10-22): longs +22.9R (433), shorts −20.3R (202). Primary shorts −5.5R / −$152.65,
     longs +3.5R / +$60.59. On 10-22 shorts were +36.1R and longs −74.4R.
   - Best: CWT14-failbrk-pdl-p10-long (T2) +10.9R, GEN-261020-07 hold-long +7.8R, CWT12-coil-k4-long (T2) +7.4R.
     Worst: CWT14-failbrk-orl-p05-long (Graveyard) −8.0R, RW2-exhaustion-noon-adv150-short-FD (Graveyard) −7.7R.
2. **patterns.csv:** +250 loser rows for 10-23 (3,126 → 3,376; `merge_patterns.py`, idempotent by date). Loss mix vs
   10-12..10-22: **late hold 24.0% (was 10.6%)**, small MFE 21.6% (20.9%), never worked 19.2% (23.4%), gave back 15.6%
   (15.8%), wrong side after a big swing 10.0% (16.4%), stopped then reversed 9.6% (12.9%). A day without a trend
   shows up as more 15:55 flattens of trades that went nowhere.
3. **Give-back (nightly1023, not recomputed):** Testing 2 gave back $73 (7 open winners at the 14:51 peak, −$63 at
   the 15:55 flatten); Primary was never positive (two widest-risk shorts FCEL / FRVO −$128 into QQQ's +1% morning);
   Generator $43; Graveyard never positive. The late-hold jump and T2's flatten are the same thing; the time-stop /
   late-flatten tunes are already in the backlog (top5 execution variants, failed on history).
4. **Recurring patterns (≥ 3 of the last 10 sessions)** — CWT14 ORL longs never-worked / stopped-then-reversed,
   RW2-FD small MFE, heat_fade_short never-worked, morning flow-sell shorts stopped into an index rally — all already in
   the backlog (top5 tunes, `bdi1015-short-index-up-veto`, `nightly-1019-index-chase-veto`, LL-LATCH). Not re-added.
5. **Backlog:** `nightly-1023-wide-stop-pct-risk` → **failed** (21 configs, numbers in its notes); new
   **`bdi1023-tight-stop-pct-skip`** (failed, near-miss, 9 configs, parent `gb-1019-noise-floor-stop`).
   `research/BACKLOG.md` regenerated.

## vs yesterday
10-22: 36 configurations, 0 pass, both families' gains were plain up-day thinning. 10-23: 30 configurations, 0 pass,
but rework E is the first book-wide gate in this lineage whose delta is positive in train and valid and above the
random control in all 9 rows; it fails on the books still being negative and on down sessions. Learned: the live
"wide stops lose" split does not survive two years; tight stops are the cost sink instead.

## Queued
- `gb-1019-noise-floor-stop` widen-to-floor at the same $ risk (stop ≥ 0.5% of price, size down so $ risk is unchanged)
  — needs path re-simulation; pre-declare 3 floors × 3 books.
- Add the CWT12/CWT14 family to the history signal cache so risk rules cover Testing 1/2's busiest setups.
- `bdi1022-short-cluster-profit-lock` on the two-year history (from yesterday, not started).

Files: `PLAN.md`, `swarm.py`, `swarm_out.txt`, `results.csv`, `swarm_e.py`, `swarm_e_out.txt`, `results_e.csv`,
`results_e_setups.csv`, `counts.json`, `trades_bdi.py`, `merge_patterns.py`, `per_trade_1023.csv`, `patterns_1023.csv`,
`by_setup_1023.csv`, `out_1023.txt`.

Educational only — not financial advice.
