# Nightly learning loop, 2026-11-11 (Wednesday): Primary (TEAM-6 day 1), On Deck, Testing A, Testing B, Testing C, Gen, Graveyard

*Educational only — not financial advice. Live **paper** results from one session plus the record since start; descriptive,
not evidence that anything works. **Configurations tried tonight: 0.** Step 4 (swarm backtest) skipped: usage tight, no new
hypothesis (11-11 evidence added to two existing ideas), nothing near a gate.*

Rule changes in window: TEAM-6 on Primary from 11-11 (ledger 2026-11-10-team6-primary, frozen to 11-13); EXPO1109 revert
effective 11-11; the account restructure (PRs #182/#183, ledger 2026-11-12-*) takes effect 11-12 and does not touch today's data.
Market: SPY −0.14% at 09:45, above its open from 10:45, +0.74% at 13:45, +0.47% at the close; compass W60 UP-confirmed from 11:30.

## 1 Close / 1b coverage
- All 7 accounts flat (status positions 0, every trade closed), flatten_failed empty, EOD report + charts + pl_reconcile on all
  7 data branches ("all match Alpaca"). Journal-vs-job-log count not re-checked (usage); pl_reconcile matched in all 7.
- Polls (polls_out.txt): Primary 379, Testing A 384, On Deck 321 (85%), GY 318 (84%), Testing C 271 (72%), Gen 207 (55%,
  5 gaps > 5 min, max 5.9), **Testing B 188 (50%), gap 132.6 min 12:18:13 → 14:30:49 ET**.
- Testing B: first trade job (run 43032649308, job 130563372565) ended in failure at 18:14Z (13:14 ET); GitHub annotation
  "The hosted runner lost communication with the server ... starves it for CPU/Memory"; log blob gone, Trade step never
  concluded. Last recorded poll 12:18 ET (later ones, if any, went with the runner); resumed by the 14:29 hand-over job
  (started 19:29:52Z). ~130 polls / 26 full-symbol decision bars missed. Likely cause: runner resource starvation (not code).
- Rejects: buying power 0 (code 40310000) GY 253, Gen 248 rejected signals; On Deck 2 "missed: triggered" skips; Primary 33 not-ETB.

## 2 Primary autopsy (pautopsy_out.txt, latchgross_out.txt)
- 43 trades, **−26.63R after costs** (gross −25.91R), win 14%, $−690.56; **Alpaca −$670.08** → streak 0; since Day 1 4 of 14 green, $−3,487.94.
- Shorts 38 trades −27.75R, longs +1.12R (ST7 +1.01R, NS5 +0.11R). RW5-FD 21 −14.54R, RW3-FD 14 −9.68R, L3-gap-slope-fromopen-FD 3 −3.52R.
- Shorts entered at/after 11:30 (compass UP-confirmed): 30 trades −21.33R. Peak +2.37R at 12:30 (realized +1.80, 23 open, 20 short);
  short book grew to 31 lots by 14:00; gave back 29.0R to the close. Losers never worked: RW3/RW5 losers avg MFE 0.17-0.20R,
  MAE ~0.9R, time-to-MFE ~20 min; 11 trades never reached +0.1R (−8.96R). Exits: stops 19 −20.51R, 15:50 flatten 20 −9.65R, targets 4 +3.52R.
- **Latch post-latch loss:** L3 latched 13:57, RW5 14:25, RW3 15:20 (live basis, gross r_multiple ≤ −2R). 30 lots open at the
  latch finished −20.86R vs −9.84R marked at the latch minute → **−11.02R lost after the latch on already-open lots** (RW5 −8.19R / 19 lots,
  RW3 −2.47R / 10, L3 −0.36R / 1) — 41% of the day's loss. SPY was flat after each latch (−0.03..−0.29%), so the open shorts bled on
  name-level bounces after the 13:45 index high, not further index rise. Second data point for nightly-1110-latch-closes-open-lots
  (11-10: −22.46R vs −9.34R). Other accounts (latchopen_out.txt, costs-in basis): On Deck +8.55R, Testing A +9.37R, GY +39.68R if closed;
  24 setup-days better, 3 worse (GY dip-buy longs CWT12-coil-k6-long −15.6R, CWT14-failbrk-orl-p05-lowvol-long −9.5R) — same split as 11-10.

## Other accounts (short)
On Deck −28.47R / −$189.80 (MF3-open-flowsell-rsi5hi 16 −10.42R); Testing A −17.66R / −$147.78 (RW3S-FD 16 −11.50R; exhaustion_short-FD +6.51R);
GY −97.47R / −$2,073.36 (heat_fade shorts −49.0R; CWT14-orl longs +21.3R); Gen +8.23R / −$337.94; Testing B +0.56R / +$29.01 (1 trade);
Testing C +0.31R / +$5.05 (low-rep).

## 3 Backlog
No new id; 11-11 evidence appended to nightly-1110-latch-closes-open-lots and ecg1-1109-early-compass-momentum-short-gate (add_backlog.py).

## 6c4 Team final
Team-8 −16.07R / −$305.29 (39 trades); TEAM-6 subset −16.58R (33) vs Primary live −26.63R (replay had 27 RW3/RW5 lots vs 35 live).

## 6 Shadows
- −2R latch: 7 Primary signals blocked (L3 6, RW5 1), what-if +1.48R (deduped +0.21R) → latch cost ~1.5R at most; not costing Primary.
  Latch-by-category: Primary −0.21R raw / +0.22R excess; GY +32.64R raw / −33.34R excess (shorts +72.7R, longs −40.1R).
- BRAKE-1: trigger 14:25, −26.63R → −26.22R (+0.42R); running since 11-02 **+5.03R**.
- LEASH (forward 1 of 20): Primary L3 n 3, base −3.52R, K11 / K12 ±0.
- Regime switch forward day 1 (all accounts, base −93.09R): GAP-U off +111.55R (half +55.78R, 212 trades switched), SPYO-P +4.38R, IDX3-P +0.49R.
- Compass: live marks already complete (25, to 15:45 UP-confirmed; nothing to backfill); compass_cond +36 rows, 462 sessions, pushed.
- REG2 is parked (day 5 printed only by forward.py).

Scripts: fetch, polls, build, today, latchopen, latchgross, pautopsy, combined, forward, add_backlog (run with the scratch dir of journals + SIP bars).
