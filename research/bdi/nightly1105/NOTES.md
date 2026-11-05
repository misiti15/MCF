# Nightly learning loop, 2026-11-05 (Thursday): 7 accounts (Primary, Testing 1, Testing 2, Graveyard, Gen, Explore 1, Live Lab)

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **Configurations tried tonight: 1**
(a descriptive fixed-$-risk re-pricing of Primary's live trades since 10-28; no holdout touched, no 2-year run). About 35
descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency, peak-to-close
attribution, UNI1 setup-matched, restart catch-up, latch / brake / REG2 / FLOW1 / leads shadows), so some will look strong
by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`. The job log shows P/L **before** costs. What-ifs
(blocked / halted signals) are on SIP 1-minute bars, entry at the signal's ref price, stop / target / 15:50 close,
**before costs**.

**Rule changes inside the windows quoted below** (research/ledger.jsonl effective dates): Primary: ST7-FD 10-26, ~$4,000
size 10-28, −2R per-setup stop 10-29, L3 pair 10-30. All: GX1 10-27. Testing: per-setup stop off 10-23, BAR90 10-29, CF
10-30; NS3-FD / RW4-FD → GY 11-02; R2A legs T2 11-02; SO-1A, RW3S (T2), MF3-FD / MF5-FD → GY 11-03; UNI1 (T2 top-500)
and DM-N3 11-04. **From today (11-05): ROLL1 — 42 low-rep setups moved to Explore 1 / Live Lab (first session).** Ops
only, not a trading rule: watchdog fix PR #151 merged after the session. No setup / exit rule changed during the session.

**Scripts** = nightly1104's with the date set to 11-05 and the two new accounts added (`fetch.py`, `build.py`, `close.py`,
`polls.py`, `decmin.py`, `autopsy.py`, `giveback.py`, `combined.py`, `today.py`, `forward.py` + per-setup latch lines),
`add_backlog.py`. Scratch data (journals, bars, job logs) were outside the repo.

**Market: a trend-down day.** SPY −1.48% at 10:00, −3.27% 11:00, −3.89% 13:00, close −4.22% (low into the close);
QQQ low −5.27% at 10:53, bounce to −3.24% by 11:30, close −5.17%; IWM −4.67% at 13:03, close −4.48%. REG1 "down".

## Failures first

1. **No position or order left open.** All 7 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial
   lots, no data outages; 14:49 run's job log "flatten complete: no MCF positions open" for all 7 (15:55-15:57 ET);
   journal = EOD report = status = job-log "Trades" (61 / 91 / 271 / 344 / 385 / 36 / 19); status P/L = report P/L;
   EOD reports + scorecards 15:58-15:59 ET. The 08:56 run pushed its final state for all 7 at 14:36-14:40 ET ("job 08:5x
   done"), the 14:49 run pushed "job 14:49/14:50 done" for all 7.
2. **Runner gap 14:35 → 14:50 ET (14.8 min; T2 12.7 min)**: the 08:56 run (42039092749) hit its 355-min limit and no
   standby started (GitHub scheduler outage); manual run 42097550000 began polling 14:49:59. Decision minutes 14:40 and
   14:45 missed in all 7 accounts. Open lots kept their broker brackets (L3-rsi5hi's last stop filled 14:43:19 with no
   runner). **The first poll of the new run entered signals from the gap's bars** (bar index 309-319 = 14:39-14:49) at
   14:50 prices: Primary 1, T1 5, T2 3, GY 15 (+11 at 14:55), Gen 32 (+20 rejects), Explore 1 4, Live Lab 1. Fix for the
   standby is PR #151 (BURST1 / ops own it).
3. **Gen's account halt was not carried over the restart (broken).** Gen halted at 14:10 (account daily loss limit,
   −120R). The 14:49 run rebuilt `realized_r` from the journal, which then lacked the unbooked trades, so it was above the
   limit: 32 new entries + 20 buying-power rejects at 14:50, re-halted by 15:00. Those 32 made +30.65R / +$567.71, so no
   harm today, but the halt is not a latch. Housekeeping: latch the halt like LL-LATCH (running journal R min ≤ −limit,
   or persist `halted` in state) → OPEN_ITEMS `HK-HALT-RESTART`. The per-setup −2R latch *was* restored correctly
   (Primary / GY "setup daily loss limit" skips continue from 14:50).
4. **Gen: 69 submitted entries unbooked** (454 submitted vs 385 trades; 09:55-13:15, most 10:55-11:00 and 13:10-13:15) —
   HK-RECON-GEN again, larger than 11-04's 4 (which are now booked: yesterday's column reads 259). Gen's −$1,100.08 may be
   off. Gen also had **24 buying-power rejects** (20 at 14:50) plus 26 bracket-price rejects.
5. Coverage (1-min polls 09:30-15:54; health `polls` count only the 14:49 run): Primary 367, T1 364, T2 368, GY 310
   (84.5% of Primary), Explore 1 295 (80.4%), Live Lab 310 (84.5%), **Gen 182 (49.6%; 9 gaps > 5 min, halted from 14:10)**;
   decision minutes 74-75 / 77 (14:40, 14:45 all; 10:05 Primary / T2, 10:10 Gen). Rejects: GY 6 (bracket price), Gen 50,
   Live Lab 1; crosscheck skips T2 1 / Gen 10; "missed: triggered" 0.

## 1. Headline per account (`autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | avg R (costs) | sum R | **P/L after costs** (before) | marked peak / trough → close |
|---|---|---|---|---|---|---|
| Primary | 61 | 49% | +0.074 | **+4.54R** | **−$419.00** (−$363.32) | +$153 (11:06) / −$1,673 (11:38) → −$419 |
| Testing 1 | 91 | 53% | +0.066 | +6.04R | +$47.57 (+$58.05) | +$285 (13:08) / −$510 (14:53) → +$48 |
| Testing 2 | 271 | 44% | −0.315 | −85.41R | −$996.45 (−$975.69) | +$13 (09:54) / −$1,057 (14:46) → −$996 |
| Graveyard | 344 | 47% | −0.176 | −60.47R | +$323.31 (+$432.67) | −$1,204 (10:36) → +$323 (close = high) |
| Gen | 385 | 40% | −0.332 | −127.77R | −$1,100.08 (−$872.98) | +$378 (11:38) / −$1,465 (14:54); halted 14:10 |
| Explore 1 | 36 | 33% | −0.426 | −15.32R | +$50.44 (+$54.92) | first session |
| Live Lab | 19 | 58% | −0.076 | −1.44R | +$152.38 (+$154.24) | first session |

**Primary live-funds hold: GREEN in R, red in $.** +4.54R after costs (−$419.00 after costs) → **streak 1 in R** (owner:
streak counts in R after costs; 11-04 −10.75R). Since Day 1 (10-23), in R: 4 of 10 sessions positive, −8.36R; in $: 4
of 10, −$1,346.01 after costs (−$1,132.33 before). Since start 7 of 23 positive in $, −$2,367.37. Rule changes in the
window: ~$4k size 10-28, −2R stop 10-29, L3 pair 10-30.

**R vs $ gap (owner note).** $ per R differs by setup because Primary sizes ~$4k notional lots and stop widths differ:
Early Sellers, Strong Heat (all day) (`MF4-h40-open-flowsell-FD`) **$121 / R** (avg risk $111 a lot) vs Gap-Down Pop
Fade, Heavy Selling (all day) (`RW3-gapdn-rsi5pop-flowsell-short-FD`) **$48 / R** ($53), Gap-Down Rebound Overbought
Short (`L3-gap-slope-rsi5hi-FD`) $96 / R, MF2-FD −$42 / R (−1.68R but +$70). Net: MF4-FD −10.66R = −$1,293 wiped RW3-FD
+16.49R = +$790. Primary entries 11:00-11:59: 28 trades **+0.142R avg but −$560**. Since 10-28, the same R at a fixed
median $ risk ($33) would read −$304 instead of −$1,375 (descriptive, 1 config) → added to BURST1's
`burst1-equal-dollar-risk` (same finding; BURST1 traced it to notional sizing). The same effect made Explore 1 / Live Lab green in $ and red in R (CWT09 g10
shorts carry ~$112 risk a lot vs ~$5-8 for the CWT05 / CWT13 longs).

**Why Primary swung (peak $153 → trough −$1,673 → −$419).** 13 MF4-FD shorts entered 11:00-11:10 (5-per-poll clusters)
right after QQQ's −5.27% low at 10:53; QQQ bounced to −3.24% by 11:30 and 12 of them stopped 11:10-11:18 (−$1,456 marked
at the trough; latched 11:12:56). RW3-FD (13 shorts from 11:20, 92% win, +16.49R) and RW5-FD (+2.99R) rebuilt it; the
5 lots still open at the 15:50 flatten added +$458. BURST1 is analysing the burst — not repeated here.

## 2. Winner / loser autopsy (`autopsy_out.txt`; SIP 1-min MFE / MAE for all 1,207 trades)

- **Primary**: winners peaked at a median +1.39R after 45 min (gave back 0.15R); losers peaked +0.22R, MAE 1.09R; 13
  "never worked" −$1,400 (8 of them MF4-FD). Shorts 57 (+0.083R, −$445), longs 4. Latency median 2.3 s.
- **Testing 1**: shorts carried it — Gap-Down Bounce Early Short (all day) (`RW7-gapdn-bounce-early-short-FD`) 49 trades
  +14.27R / +$157 (peak +$334 marked at 13:08, gave back −$333 into the 14:50 low, then recovered); losers CWT05 flush
  longs −6.23R, NS3 base −4.36R, orb20_a −$77 (3 trades, $164 / R).
- **Testing 2 (UNI1 day 2)**: 193 longs / 78 shorts; RW3S (no-RSI RW3) 60 shorts −30.81R / −$542 (28% win); Stretched
  Below VWAP Bounce (`CWT13-vwapstretch-z05-long`) 100 trades −23.86R; CWT14 pdl longs (p10, p10-lowvol, p05-R2A) 79
  trades −35.6R. Best RW1-FD +4.78R, NM-HL-T75-pm +3.12R. 88 "never worked" −$976.
- **Graveyard**: −60R but +$323: shorts carried the $ (CWT09-vwaploss-g5 +28.4R, heat_fade_short-FD +14.1R, CWT09-bounce-g5
  21 trades +8.75R / **+$1,071** at $122 / R, MF3-FD +7.4R); CWT14 orl longs 84 trades −70.5R (latched early); ST2-FD −15.5R.
- **Gen**: GEN-261022-09 (AM short) 48 trades −58.5R (0% win); GEN-261019-05 (SPY < −0.5% OPEN long) 50 trades −52.9R
  (4% win) — an index-down gate firing into a trend-down morning (mirror of 11-04's SPY-up gate at the spike); halted 14:10.
- **Recurring patterns tied to losers**: (a) a same-setup short burst right after an index low (MF4-FD; BURST1);
  (b) long dip-buy families on a trend-down day — counter-index entries 639 trades −0.428R vs others −0.011R, but the
  setup-adjusted excess is −0.001R, i.e. it is *which* setups fired (long dip-buys), not their timing → evidence added to
  `nightly-1016-trend-day-long-reversal-veto` (REGX covers regime); (c) $ per R spread on Primary (above); (d) restart
  catch-up entries and the unlatched Gen halt (Failures 2-3).

## 3. Backlog (+2 ideas, 2 updated; `research/backlog.jsonl`, research/BACKLOG.md regenerated)
- (c) → evidence added to BURST1's `burst1-equal-dollar-risk` (no duplicate).
- `nightly-1105-uni1-pool-by-daytype` (setup / universe) — the UNI1 flag below.
- `nightly-1105-restart-catchup-entries` (risk / ops) — (d).
- `nightly-1016-trend-day-long-reversal-veto` — 11-05 evidence appended (still idea).

**Swarm (step 4): not run.** 2 new ideas (below the 3 trigger) and no setup near a gate; tonight's CPU also goes to BURST1 / REGX and the queue
(`python -m mcf.research.queue tonight`: GATE2, FLOW1-2Y, owner p0). Tonight's two go behind them.

## 4. Suggestions (`combined_out.txt`, `today_out.txt`; 23 sessions 10-06..11-05, costs in)

**No new DECISION.** Open with the owner: L3H (numbers updated below and in docs/live/decisions.json) and the 11-05
summary items (P4 trim / HN1 / HN3 / compass live / BASE1 / M1 / M2) — not duplicated.
- **L3H update (material: the record without its best day is now below zero).** Gap-Down Rebound Overbought Short (all
  day) (`L3-gap-slope-rsi5hi-FD`): Primary since 10-30 **14 trades / 5 sessions (1 green), 35.7% win, −0.536R, −$739.41**
  (today 5 trades −2.42R / −$233, latched 14:43); full record 90 / 16, +0.063R, **−0.033R w/o best day (10-26 = 142% of
  R, `1 day`)**, ex-market (Primary) −0.508R, last 4 −0.603R (13), 3 busiest +0.247R. Counter-note: after the latch its 31
  blocked late-day shorts would have made +14.3R before costs (repeats on a falling close).
- **Primary drift — MF4-FD** (fold into P4 trim if it is not already there): Early Sellers, Strong Heat (all day)
  (`MF4-h40-open-flowsell-FD`) 107 trades / 19 sessions, 62.6% win vs 67.5% break-even, −0.082R, **−0.139R w/o best day**
  (10-14), Primary ex-market −0.214R (75), last 4 −0.397R (37), 3 busiest −0.289R, −$1,369.06; today −10.66R / −$1,293.
- **ST7-FD on Primary since 10-26** (review 11-06): 21 trades +0.133R, +$30.58, −0.029R w/o best day (11-04, 112%).
  RW3-FD full record 117 +0.405R, +0.251R w/o best day (51%, 10-22), Primary ex-market +0.226R — the steady one.
- **No promotion is ready**; **Graveyard → Testing not supported**: today's top GY shorts still lose on their full
  records (CWT09-vwaploss-g5 103 / 13, −0.013R, −0.377R w/o best day = today; CWT09-bounce-g5 141 / 15, −0.024R, −0.109R;
  heat_fade_short-FD 624 / 19, −0.066R; MF3-FD 188, −0.133R). Last 4 positive for all four — watch only.
- **Testing → Graveyard watch (not raised)**: MF1-945 (T1) no trade (rule-20 date 11-06); intraday_momentum 42 / 17,
  −0.296R; NM-AR-AM-gapdown-capitulation (T2) 48 / 6, −0.372R, −0.527R w/o best day; CWT13-z05-long (T2) 266 / 17,
  −0.157R, −0.202R w/o best day, last 4 −0.242R (138).
- **UNI1 flag — worth an owner look: does the top-500 pool hurt Testing 2?** Testing 2 today −85.4R on 271 trades vs
  Testing 1 +6.0R on 91. Since UNI1 (2 sessions): 410 trades, **setup-matched avg R −0.291 vs −0.034 for the same setups
  10-20..11-03 (−0.256R; 14 of 23 setups worse, 9 better)**; same two days Testing 1 +0.061, Graveyard +0.003, Primary
  −0.274. T2 per session −0.232 / −0.315R vs −0.101R the 5 sessions before. Caveat: T2 is long-heavy (63% longs since
  UNI1) and both days were index trend days (spike-fade up, then −4%), so pool and day type are mixed; the clean test is
  backlog `nightly-1105-uni1-pool-by-daytype`. UNI1 rule change 11-04; ROLL1 moved low-rep setups out of T2 on 11-05.
- **Explore 1 / Live Lab first day (FYI only; account totals stay out of the daily post).** Explore 1: 36 trades (3
  shorts), 33% win, −15.32R, +$50.44 — CWT13-z075-long 23 trades −10.67R, ST8-FD −5.93R, CWT09-bounce-g10 2 shorts +1.13R
  / +$145; 67 "max positions for this setup" skips (12:20-14:35), 62 not shortable. Live Lab: 19 trades, 58% win, −1.44R,
  +$152.38 — CWT09-vwaploss-g10 2 shorts +1.20R / +$147, CWT05-m075-v3 −3.83R. Polls 80-85% of Primary, clean close.

### 4a. Monitoring (docs/live/monitor.json)
- **M1 — Afternoon VWAP Reclaim Fade (all day)** (`NS4-pm-vwap-reclaim-oversold-short-FD`), T1 → Primary mark 10-27:
  **no trade today** (also none 11-04); since mark 10 trades / 5 sessions (0 green), −0.435R, −$4.89; record 27 +0.166R /
  −0.006R w/o best day (103%, `1 day`). Lean drop unchanged.
- **M2 — Generated NewLOD LUNCH short** (`GEN-261026-03-…-holdtr-short`), Gen → T1 mark 10-27: **no signal today**
  (its LUNCH window 11:40-13:55 was before Gen's 14:10 halt; nothing fired). Two-green-sessions rule: **pending, 1 of 2**
  (11-03 green). Since mark 17 trades +0.406R, +0.074R w/o best day (89%).

### 4b. Watches
- `CWT14-failbrk-pdl-p10-lowvol-long` (T2 since 10-28): today 15 trades −9.62R, −$72.38; since the move 103 trades / 7
  sessions (1 green), −0.300R, −$285.58, −0.341R w/o best day; record 275 −0.094R.
- **R2A legs (T2)**: long leg 37 trades −8.86R / −$200.89 (12 targets, 5 stops, 12 flattened); **scale-out vs plain:
  scaled 8 lots avg +0.026R vs plain 29 avg −0.313R** (11 plain lots reached the +0.083R scale trigger by journal MFE).
  Long leg since 11-02 76 trades −0.152R. Short leg no trades today (13 trades −0.238R since 11-04).
- **RW3S-gapdn-flowsell-short-FD** (T2, **day 3 of 5**): 60 trades −30.81R, −$542.17 (28% win); 3 days 111 trades,
  −0.307R, −$628.00, **0 green**; ex-market −0.211R. Same day its parent RW3-FD (RSI(5) pop required) made +1.27R a trade on
  Primary — the pop condition is doing the work on this evidence.

### 4c. Primary −2R per-setup stop (FYI)
Latched today: NS5 (10:52), **MF4-FD (11:12:56)**, MF2-FD (12:14:36), L3-rsi5hi (14:43:19, stop filled during the runner
gap). Blocked signals (first skip per setup-symbol, 79): what-if **+15.25R → the latch cost 15.25R** today (L3-rsi5hi
31 late shorts +14.3R, MF2-FD +2.3R, MF4-FD +1.6R, NS5 −2.9R); job log (all repeats) +7.4R. Running since 11-02:
+11.1R saved → **−4.15R (cost)** over 4 sessions. **latch1103-category-shadow day 2**: Graveyard 15 setups latched, 1,207
first skips, what-if −292.2R → **the latch saved 292.2R** (longs +350.0R saved, shorts −57.7R cost; excess vs own avg
+87.2R); Primary −15.25R (excess −10.2R). 2-day tally: GY +248.8R saved, Primary −12.75R.

### 4d. BRAKE-1 shadow (never switched on)
Family stops 26 (third at 11:12:43, all MF4-FD) → 37 family lots after it made +17.80R (+$1,081). **Primary actual
+4.54R vs with brake −4.36R (−8.90R, −$540.66).** Running total since 11-02: **−9.69R** (4 sessions: 0 / −6.37 / +5.58 /
−8.90).

### 4e. REG2 shadow, day 2 of 5 (`research/bdi/reg2_shadow.csv`, 61 rows appended)
SPY −1.48% vs open at 10:00 → keep longs, drop shorts. Primary actual +4.54R; **kept-only +0.31R (+$83.39), 4.24R
worse in R** (better in $ by $502); kept 4 longs −0.042R, dropped 56 shorts +0.076R (−$502.39); 1 pre-10:00 trade +0.47R.
2-day tally: kept-only −6.56R vs actual.

### 4f. FLOW1 and swing leads, forward day 2 (`forward.json`)
- FLOW1 merged (T 10:15, k 3, win): longs 17% win at 10:15 → 502 later longs dropped (avg −0.300R) → **delta +150.3R**,
  identical to the SPY-side control (+150.3R): no lift on top of SPY. Primary: no trade closed by 10:15 → delta 0.
- L1 inverse / vol ETP longs 5 trades +0.12R vs same setups' others −0.10R. L2 no trigger. L3 not a qualifying day.
  L6 counter-index entries −0.428R vs −0.011R; setup-adjusted excess −0.001R.
