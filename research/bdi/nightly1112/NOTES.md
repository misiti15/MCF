# Nightly learning loop, 2026-11-12 (Thursday), LEAN: 10 accounts (Primary TEAM-6 day 2, On Deck, Testing A-F, Gen, Graveyard)

*Educational only — not financial advice. Live **paper** results from one session; descriptive, not evidence that anything
works. **Configurations tried tonight: 0.** Swarm (step 4), long per-account autopsies and 6c4 (Claude's Team, STOPPED by the
owner 11-12) skipped. REG2 parked (its csv row not written).*

Rule changes in window (ledger): restructure PR #183 (On Deck roster, Testing D/E/F fill, Testing A full universe, caps /
sizing / halt unlocks), LR fixes PR #185, LR3 cost-in latch/halt + LR8 cost model on Primary — **all effective from today
11-12**, so today is the first session under them; TEAM-6 on Primary since 11-11 (frozen to 11-13). After the close:
RW6-ns2-up3-short-FD -> Testing C, ST4-emadn-long-am-t1s05-FD -> Testing B (from 11-13; does not touch today's data).
Market: SPY +0.42% at 09:45, high +1.08% at 11:15, faded to +0.37% at 15:45; compass UP-confirmed from 10:00.

## 1 Clean close / LR5 health
All 10 accounts: status phase closed 15:55 ET, 0 positions, 0 open journal trades, flatten_failed [], **position_mismatch []**,
no health.alerts emitted, position_check at ~15:54 with 0 blocked; EOD report + scorecard + pl_reconcile landed on all 10
branches (~16:00 ET), every one "all match Alpaca".

## 1b Coverage (polls_out.txt)
Primary 380 polls (max gap 1.8 min), On Deck 329 (87%), Testing A 321 (85%), Testing B 322 (85%), Testing C 369 (97%),
Testing D 353 (93%), Testing E 352 (93%), Testing F 361 (95%), Graveyard 262 (69%, max 4.2 min, 1 full-symbol bar missed),
**Gen 205 (54%), 4 gaps > 5 min (max 6.3 at 14:50), 2 full-symbol decision bars missed**. No gap like 11-11's Testing B.
Scheduler missed the 08:47 start again (dispatched 08:49; 2nd day running).

## 2 Owner question: "the leaderboard showed only ONE setup traded today"
- **Data is right.** EOD scorecards vs journals (run 1, 11-12, per setup): exact match on all 10 accounts (Primary 6 setups /
  75 trades, On Deck 11/133, A 7/121, B 6/30, C 3/4, D 5/50, E 5/75, F 7/95, Gen 26/300, GY 31/910). The rendered leaderboard
  (page script run in node on the real files) now shows Last session 2026-11-12 = 79 setups / 1,416 trades; the rest are
  by design: 26 Gen-only GEN setups (own Generated card) and RW6-ns2-up3-short-FD (76) + ST4-emadn-long-am-t1s05-FD (1),
  Graveyard-origin setups moved after the close to Testing C / B with `no_leaderboard` (owner 11-04 rule).
- **Why it looked wrong during the day:** the leaderboard had NO intraday per-setup data. Its "Last session" band is the last
  COMPLETED session from the EOD scorecards, so all day it showed 2026-11-11 (57 setups / 563 trades, many in their old
  account, tagged "in OD" etc.), and Testing D/E/F had no scorecard at all until 16:00. Today's trades only appeared after
  the EOD reports landed. (The exact "one setup" view could not be reproduced from the files; every intraday rendering shows
  11-11's 57 setups, so it was 11-11's numbers or a filtered view, not today's.)
- **Fix (display only):** new "Today so far" band (trades, R after costs) on the leaderboard: each account's status.json
  closed[] summed per setup, all 10 accounts, only for a session the scorecards do not cover yet; blank after the EOD reports.
  Node check: intraday files -> 79 setups / 1,416 trades in the band; EOD files -> band blank. Test added.
- **Signal exposure (signals table, run_id 1), enabled setups as of today's configs:** Primary 6/6, On Deck 14/14, GY 32/33
  had signals. **88 enabled setups had zero signals:** A 3, B 4, C 8, D 5, E 5, F 2, Gen 60 (of 88), GY 1. Reasons:
  **gate 45** — index / breadth-gated off on an up day (SPYdn / SPYltm / QQQdn / QQQltm / BRvwlt / BRoplt; IDX2/3/5 need
  SPY >= +0.50 / +0.75% at 09:45 / 09:55, SPY was +0.46%; LD dip / breadth-turn longs; POD1022 breadth thrusts);
  **rare / low rate 27** — 8 rare by design (audit P >= 5%) + 19 whose quiet streak is within normal odds for their expected
  rate (no alarm; 14 Gen, CWT04 a25 shorts, LIQ-pdl-sweep, CWT12-flag, ST5, ST1; Gen also had only 54% poll coverage);
  **blocks 13** — the audit's streak cause is borrow / short gate, spread-cost filter, buying power, halt or the quote
  crosscheck (CWT04 a15 shorts, ST7Q, NM-PM-gapdn, 10 Gen); **regime split 1** (R2A long: the leg only fires on its regime
  days; R2A short traded 46); **weekday 1** (NM-RWN5-...-mon-...); **unexplained 1, already on the inactive alarm list:
  CWT13-vwapstretch-z075-short (Testing A, 4 quiet, P 0.0%)**. Watch NM-MF3-qqqdn-gapdn-FD is QQQ-down-gated, consistent with
  QQQ-down, consistent with an up day). No cap-only zero (caps bind on setups that do signal: Primary L3 648 'max positions
  for this setup' over 135 symbols; Testing F 84). No bug found. Housekeeping: the inactive audit (research/ops/inactive1103)
  does not know Testing D/E/F yet (their 12 zero-signal setups were classified by hand above).

## 3 Primary autopsy (pautopsy_out.txt) and 5 streak
- **+39.88R after costs** (75 trades, 89% win; LR3 basis), **Alpaca +$2,843.11** (pnl_adj $2,753.24). The ~+31R at 15:51 was
  realized only; 32 lots still open then were flattened at 15:55 for another ~+8.8R.
- Driver: **L3-gap-slope-fromopen-FD 52 shorts +30.97R** (78% of the day); RW3-FD 12 +5.61R, RW5-FD 7 +3.91R, NS5 2 +0.26R,
  ETF late dip 1 +0.21R, ST7 1 -1.07R. Shorts 71 trades +40.49R, longs 4 -0.60R.
- Shape: 53 entries 11:00-11:59 (+36.05R) as SPY topped (+1.08% at 11:15) and faded to +0.37%; 40-46 short lots held from 11:30.
  Exits: 39 targets +35.25R, 32 flatten +8.79R, only 4 stops -4.16R. Peak +40.79R at 15:45, gave back 0.91R.
- L3 was capped: 648 'max positions for this setup' blocks (135 symbols) + 557 not-ETB (82). L3 record (Primary + On Deck):
  340 trades, avg +0.223R, w/o best day (10-20, 44% of total R) +0.163R — today does not carry the record alone.
- **Streak: 1** (green after 11-11's red). Since Day 1: 5 of 15 green, $-644.83.
- No Primary / On Deck move suggestions (Primary frozen to Fri; On Deck just rebuilt).

## 6c shadows
- **-2R latch (6c):** Primary 0 latches, 0 blocked signals (no setup below -2R; LR3 cost-in basis from today). Latch by
  category (GY only): 560 blocked, raw -23.91R (the latch cost R today) / excess -93.11R (longs +9.72R, shorts -33.64R).
- **BRAKE-1 (6c2):** 1 family stop (RW3-FD SMCI 14:23), no trigger; actual = brake +39.88R; running since 11-02 **+5.03R**.
- **LEASH (6c5)** forward 2 of 20: Primary L3 n 52, base +30.97R; K11 (half size when SPY >= +0.40%) +15.48R (**-15.48R**),
  K12 (-1R stop after UP-confirmed) +1.64R (**-29.33R**). Both leashes would have cut most of today's winner.
- **compass_cond (6c6):** 11-12 appended (+36 rows; 463 sessions, 1,090 cells), pushed to mcf-data-compass.
- **Compass live bug:** a `compass_live --push` run on a checkout with an older COLS (no 'spy_px') raised "dict contains fields
  not in fieldnames: 'spy_px'" against today's file (written by the newer code), so only 09:45 landed during the day. The
  16:06 ET workflow run (current code) backfilled the other 24 marks (tagged backfilled=1); file now complete 09:45-15:45.
  Fix: the writer keeps any column already in the file (header = COLS + extras, missing values blank). Test added.
- **Regime switch (6c7)** forward day 2 (now incl. Testing D/E/F; base +108.54R): GAP-U off **+19.37R** (681 trades), IDX3-P
  **-45.13R**, SPYO-P **-20.79R**. Running forward (2 sessions): GAP-U +130.92R, IDX3-P -44.64R, SPYO-P -16.41R.
- **LATCH-CLOSE forward shadow (swing1111-L13)**, first live session (research/bdi/1111/latch_close_live.py, gross basis):
  Primary 0 lots; On Deck +0.32R, A -2.20R, D -4.45R, E -5.29R, F +19.94R, GY -17.74R, Gen -24.81R → **total -34.23R**,
  setups better 16 / worse 14. A strong-trend day where latched lots recovered (GY RW6 shorts, Gen). One day; no decision change.
  Gross-basis caveat: Primary's live latch is costs-in from today (LR3).

## 6a marks / 6d
NS4-pm-vwap-reclaim (Testing F) 17 trades -3.38R (since 10-27: 33 -0.328R, 0 of 9 green); GEN-261026-03 (Testing D) 0 signals;
CWT14-pdl-p10-lowvol-long 34 +7.74R (since 10-28 180 -0.110R; today is its best day); RW3S (Testing E) 42 +3.85R (262 -0.248R).
OPEN_ITEMS: LB-TODAY + COMPASS-COLS shipped; INACT-DEF and OPS-SCHED-0847 added; LATCH-CLOSE forward day 1 noted.

Scripts (scratch dir of journals + SIP bars): build, fetch, polls, today, pautopsy, latchopen, combined, forward (this dir);
research/bdi/1111/latch_close_live.py, research/l3leash/shadow.py, research/regime_switch/shadow.py (D/E/F added).
