# BDI daily 2026-11-12 (Thursday), VERY LEAN

*Educational only — not financial advice. Live **paper** results from one session; descriptive, not evidence that anything
works. **Configurations tried tonight: 0** (one what-if pricing of capped signals, no backtest).*

Builds on research/bdi/nightly1112/NOTES.md. **Rule changes in window (ledger):** restructure PR #183 (On Deck roster, Testing D/E/F
fill, Testing A full universe, caps / sizing / halt unlocks), LR fixes PR #185, LR3 cost-in latch/halt + LR8 cost model on
Primary — all effective **from 11-12** (today is their first session); TEAM-6 on Primary since 11-11 (frozen to 11-13);
RW6-ns2-up3-short-FD -> Testing C and ST4-emadn-long-am-t1s05-FD -> Testing B take effect 11-13 (not in today's data).
Accounts: testing = On Deck; testing2/explore1/livelab/testingd/testinge/testingf = Testing A–F.

**Skipped tonight (usage):** swarm, per-account autopsies, precursor scan, new backtests / remedy tests, other forward shadows
(the nightly ran LEASH, regime switch, BRAKE-1, latch, compass), research queue, Claude's Team (stopped by the owner).

## 1 Move Hunt (research/bdi/moves/moves_1112_out.txt, moves.csv +100 rows)
Inputs rebuilt in scratch `mh1112/` (coverage1029/fetch.py + fetch5.py + frames_today.py); live trades from **all 10 accounts**
(1,793 trades, 782 symbols; 11-11 scored 5 accounts — not like-for-like). Liquid names 1,299.
- **Capture 5/50 = 10%** in the right direction, **R captured +9.31R** (11-11: 1/50 = 2%, −1.01R). Long 4/25 (+8.21R: MP, CORZ,
  NVDL, CLSK), short 1/25 (+1.10R: SMCI). Wrong-direction trades 8 (−8.46R). Excluding earnings-blackout names: 5/33.
  Blackout-removed set: 10/50 = 20%, +13.74R.
- **Miss reasons (50):** blackout 17, traded outside the move 14, no setup signalled 7, spread skip 4, wrong side only 3.
- **Main miss:** earnings season — 17 of 50 top movers were earnings-blackout names (by design untradeable); among the rest,
  "traded outside the move" (14) is the biggest bucket: we were in the name, but not in the move window.
- Note the Primary's +36R fade (L3 shorts 11:00-11:59 on gap-down names) does not show in the short top 25: the top shorts were
  single-name breaks (GPN −13.7%, NVD, ZM late), not the broad gap-recovery fade L3 trades.

## 2 Primary positive swing (+39.88R, Alpaca +$2,843)
What turned the day: SPY ran to +1.08% at 11:15 and then faded to +0.37%; Primary put on 53 entries between 11:00 and 11:59
(+36.05R) right at the top, 40-46 short lots held from 11:30, 39 targets hit (+35.25R) and only 4 stops (−4.16R); the 15:55
flatten added +8.79R. L3-gap-slope-fromopen-FD made **+30.97R of the +39.88R (78%)** while sitting at its 30-lot
`max_positions_per_strategy` sleeve for most of the hour. **The cap cost R, it did not make it:** what-if of the 648 cap skips
(research/bdi/1112/l3cap.py, first skip per symbol, SIP 1-min stop/target/15:50, gross) = 135 symbols **+108.9R** (avg +0.81R,
99% win), of which **103 never-traded symbols +82.4R gross (~+80.7R after L3's mean cost 0.016R)**; 125 of the 135 first skips
fell in 11:00-11:59. Upper bound: buying power and sizing for ~100 more lots are not modelled, and it is one strong-fade day.
L3 record (Primary since 10-30): 95 trades avg +0.350R, **w/o best day (11-12, 93% of total R) +0.053R — `1 day` tag**; whole
L3 record (Primary + On Deck) 340 trades +0.223R, w/o best day +0.163R. Material -> backlog `bdi-1112-l3-fromopen-cap-overflow`
(idea, configs_tried 0, parent nightly-1015-l3-fromopen-refire-cap). No test tonight; no live change.

## 3 Forward shadows (hypotheses.jsonl / forward.csv)
research/bdi/1112/fwd_swings.py = swings/forward.py on all 10 accounts, refresh limited to L1/L2/L3/L6 + L13 (the original
refresh rewrites every hypothesis' forward dict, incl. L13's days — not used). 11-11 was not logged for L1-L6 (gap).
- swing1103-L1 (vol/inverse NS5 longs, beta class A): today n 2 avg +0.329; running 6 sessions n 91 avg −0.420R, t −0.92.
- swing1103-L2 rotation turn: no trigger; running n 0.
- swing1103-L3 up-morning: not qualifying (SPY +0.49%, IWM −0.55% at 10:00); running unchanged (n 156, avg −0.432).
- swing1103-L6 counter-index entries: today 819 avg +0.147 vs others 974 avg −0.100 (+0.247); running 6 sessions n 3,003
  avg −0.160R, t −0.89.
- swing1111-L13 LATCH-CLOSE: 1 forward session, −34.23R (nightly, gross basis); t n/a.
Not updated (no 11-12 script run tonight): gate1, comp15, burst1/2, fb1, L7-L12, mh1106-p1, stopL-*, flow1 (nightly logged
FLOW1 delta 0).

## 4 Owner inbox
Per-account FYI lines + capture / today's win / swing cause appended to research/owner_inbox/2026-11-12.md.

Scratch (deleted after): `mh1112/` (build.sh). Educational only — not financial advice.
