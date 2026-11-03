# Nightly learning loop, 2026-11-03 (Tuesday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **Configurations tried tonight: 4**
(`swarm.py`, 2-year lab trade lists, costs in, locked block 2024-11-01..2025-02-28 not in the file and not read; 0 pass,
no finalist, so no holdout was scored). About 25 descriptive splits were looked at as well (setup, side, hour, exit,
poll, lot, twin, cluster, latency, peak-to-close attribution, latch / brake timing, R2A scale-out, rejects), so some
will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`. The job log shows P/L **before** costs.
What-ifs (blocked / rejected signals) are on SIP 1-minute bars, entry at the signal's ref price, stop / target / 15:50
close, **before costs**.

**Rule changes inside the windows quoted below** (research/ledger.jsonl effective dates): Primary: ST7-FD promoted 10-26,
**position size ~$4,000 from 10-28**, **−2R per-setup stop from 10-29**, **L3 pair promoted 10-30**. All accounts: lab
5-minute clock (GX1) 10-27. Testing: per-setup stop off from 10-23, BAR90 10-29, cost filter (CF) from 10-30;
NS3-FD / RW4-FD to the Graveyard 11-02; PDL-1a R2A legs in Testing 2 from 11-02; **from 11-03: SO-1A (R2A scale-outs
outside the 2/day cap), RW3S in Testing 2, MF3-FD / MF5-FD to the Graveyard**. Next: DM-N3 moves and UNI1 (Testing 2
top-500 pool) from 11-04. No rule changed during today's session.

**Scripts** = nightly1102's with the date set to 11-03 (`fetch.py` [UTC window fixed for EST: 14:25-21:05 UTC],
`build.py`, `close.py`, `polls.py`, `decmin.py`, `autopsy.py`, `giveback.py`, `combined.py`), plus `today.py` (marks,
watches, candidate cards, −2R latch what-if, BRAKE-1 shadow), `rejects.py` (Graveyard buying-power rejects) and
`swarm.py`. Today's Primary 10:52 swing is analysed in `research/bdi/swing1103/AUTOPSY.md` (not redone here).

**Market: a mild up day.** SPY +0.22% (high +0.58% 13:34), QQQ +0.14% (high +0.63% 11:04), IWM −0.01% (high +0.77%
11:16). SPY +0.06% vs the open at 10:00.

## Failures first

1. **No broken session.** All 5 accounts closed clean: phase `closed`, 0 positions, `flatten_failed` [], no partial
   lots, no data outages; journal trades = EOD report rows = `status.today.trades` = job-log "Trades" (43 / 49 / 90 /
   422 / 133); submitted signals = trades = closed orders in every account; job-log P/L = journal before-cost P/L
   (P +146.08, T1 +12.96, T2 +44.54, GY −229.19, Gen −552.75); job logs "flatten complete: no MCF positions open";
   EOD reports 15:58-15:59 ET, final state pushes 15:56-15:57 ET ("job 14:3x done"). Broker positions are not
   reachable from here (no broker keys); journal = report = status = job log is the proxy.
2. **Hand-over to run 41700474260 (~14:28 ET) lost no trades.** Gaps 3.2-4.8 min, **no gap > 5 min** anywhere; the
   14:30 decision minute was missed in 4 accounts (76/77; Gen polled it, 77/77).
3. **Coverage under 90% in 3 accounts** (of 384 1-min polls): Primary 382 (99.5%), T1 381 (99.2%), **T2 327 (85.2%),
   GY 301 (78.4%), Gen 313 (81.5%)**; misses are bucket minutes 1-2 (exp mod 5 = 1 / 2: T2 22 / 77, GY 15 / 57, Gen
   14 / 69), the known OPS-POLL residual; decision minutes 76-77 / 77.
4. **Graveyard ran out of buying power again (GY-BP):** 59 "insufficient buying power" rejects 10:50-11:20, what-if
   **+10.8R** (+0.184R avg; CWT12 coil k4 / k6 −11.4R, MF5-FD / MF3-FD +13.2R). Other skips: Primary crosscheck 1,
   T1 "missed: triggered" 1.
5. **HK-RECON-GEN for 11-02 closed:** Gen 11-02 now has 265 trades booked (was 226 + 39 submitted), −$1,032.88 after
   costs. Gen 11-03: 133 submitted = 133 trades (nothing unbooked).

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`, `decmin_out.txt`)

| account | polls | % of 384 | decision minutes | hand-over gap | longest gap | trades (journal = report = status = log) |
|---|---|---|---|---|---|---|
| Primary | 382 | 99.5% | 76 / 77 (14:30) | 3.9 min | 3.9 | 43 |
| Testing 1 | 381 | 99.2% | 76 / 77 (14:30) | 4.8 min | 4.8 | 49 |
| Testing 2 | 327 | **85.2%** | 76 / 77 (14:30) | 3.8 min | 3.8 | 90 |
| Graveyard | 301 | **78.4%** | 76 / 77 (14:30) | 3.9 min | 3.9 | 422 |
| Gen | 313 | **81.5%** | 77 / 77 | 3.2 min | 3.2 | 133 |

## 1. Headline per account (`autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | avg R (costs) | **P/L after costs** (before) | marked peak / trough → close |
|---|---|---|---|---|---|
| Primary | 43 | 67% | +0.263 | **+$136.10** (+$146.08) | +$207 (15:39) / −$219 (10:54) → +$136 |
| Testing 1 | 49 | 57% | +0.130 | **+$12.56** (+$12.96) | +$70 (14:56) / −$35 (10:54) → +$13 |
| Testing 2 | 90 | 67% | +0.057 | **+$40.64** (+$44.54) | closed at its peak; trough −$75 (11:48) |
| Graveyard | 422 | 58% | −0.069 | **−$307.89** (−$229.19) | +$44 (09:58) / −$633 (12:55) → −$308 |
| Gen | 133 | 40% | −0.196 | **−$585.51** (−$552.75) | +$10 (10:13) / −$1,206 (14:58) → −$586 |

By side: shorts won in Primary / T1 / GY / Gen (+$192 / +$63 / +$54 / +$14; T2 flat), longs lost everywhere except Testing 2 (P −$56, T1 −$50, GY −$362, Gen −$599; T2 +$41).

**Primary live-funds hold: GREEN.** +$136.10 after costs (+$146.08 before; 43 trades, +11.33R) → streak **1** (after
three red days). Since Day 1 (10-23): **4 of 8 sessions positive, −$718.38 after costs** (−$627.64 before). Since start:
7 of 21 positive, −$1,739.74. Nothing changes; lifting the hold is the owner's call. Rule changes in that window: ~$4k
size 10-28, −2R setup stop 10-29, L3 pair 10-30.

**Why Primary won: one setup.** Gap-Down Pop Fade (all day) (`RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`) 18 trades,
83% win, +9.79R, **+$178.59** — more than the day; without it Primary was −$42. MF4-FD +2.68R / +$68.63, L3-fromopen 2
trades +$97.69. Losers: RW3-FD 7 trades −1.36R / −$61.94 (4 stops before 10:50, then latched), L3-rsi5hi 1 SOXS stop
−$115.37 (12:55), NS5 UVIX / UVXY longs −$56.26 (the −$70 give-back from the 15:39 peak is these two vol-ETP lots into
the close). The 10:54 low and the turn: see swing1103/AUTOPSY.md.

## 2. Winner / loser autopsy (`autopsy_out.txt`; SIP 1-min MFE / MAE for all 737 trades)

- **Primary**: winners peaked at a median +0.78R after 66 min, gave back 0.04R; losers peaked +0.39R, MAE 0.95R;
  4 "never worked" (−$65). All 7 stops came 09:55-10:50 or at 12:55 (the morning cluster is the swing1103 dip). Bigger
  same-setup clusters did better (≥ 2 per poll +0.43 / +0.55R vs single +0.12R); twins (5) +0.94R. Latency median
  1.6 s (90th 4.8 s), fast tercile best (+0.41R) — small n.
- **Testing 1**: shorts +0.266R (40), longs −0.478R (9: NS1-FD ×4 −$27, NS5-FD ×2, CWT05). RW7-FD 17 trades +$33.79.
- **Testing 2**: RW3S day 1 (below); MF5 (base) 10 trades +0.566R; CWT14 pdl p10 19 trades flat (+0.003R, a 10-lot
  burst); 14 "never worked" −$84.
- **Graveyard**: worst CWT14-failbrk-orl-p05 lowvol / plain longs −$179 / −$138 and CWT12 coil k4 −$147 (longs into the
  10:30-11:30 dip); best heat_fade_long-FD +$72, MF3-FD +$57 (day 1 there).
- **Gen**: longs −$599 (120), shorts +$14 (13); GEN-261021-06 (ORBfailUp MID hold long) −$220 again (11-02 −47.3R);
  GEN-261029-03 marked −$432 at the trough (14:58) and recovered into the close.
- **Recurring patterns tied to losers**: (a) early short stops on an up morning (RW3 / MF2 at 10:25-10:50) — the
  swing1103 L3 lead, failed tonight on two years (below); (b) vol-ETP "longs" are market shorts (NS5) — swing1103 L1;
  (c) one-setup days: Primary's green day is RW5 alone, as 11-02's red day was L3 SOXS alone.

## 3. Backlog (6 new; `research/backlog.jsonl`, research/BACKLOG.md regenerated)
- `swing1103-L1-ns5-vol-etp-beta` (setup, idea) — swarm V1: **not testable** on the 2-year list (8 vol-ETP NS5 trades).
- `swing1103-L2-rotation-turn-short-timing` (setup, idea) — needs IWM in the 2-year context file; not run.
- `swing1103-L3-upmorning-delay-family-shorts` (setup, **parked**) — swarm U1-U3: **0 of 3 pass**. Skipped trades lose in
  TRAIN (−0.275 / −0.287 / −0.324R, t 1.48 / 1.25 / 1.13) but not in VALID (−0.025 / −0.023 / −0.009R vs kept −0.033R,
  t 0.63 / 0.48 / 0.15); bar 1.665.
- `swing1103-L4-net-beta-cap` (risk, idea) — not run.
- `swing1103-L5-early-latch-whatif` (risk, idea) — forward tally started (below).
- `nightly-1103-brake1-morning-trigger` (risk, idea) — BRAKE-1 time gate; needs exit times (lab lists have entry only).

Swarm (rule 10, `swarm_out.txt`): 4 configurations, 0 pass, no finalist, holdouts untouched. Failures: BRAKE-1 timing
and the latch are not testable on the lab lists (no exit times); L2 and the IWM leg of L3 need IWM in the context.

## 4. Suggestions (`combined_out.txt`, `today_out.txt`; all accounts merged, 21 sessions 10-06..11-03, costs in)

**No DECISION tonight.** No promotion is ready and no demotion has crossed its bar:
- **Primary drift watch** (no move): L3 pair on Primary since 10-30 — Gap-Down Recovery Fade (all day)
  (`L3-gap-slope-fromopen-FD`) 6 trades −0.511R, −$326; Gap-Down Rebound Overbought Short (all day)
  (`L3-gap-slope-rsi5hi-FD`) 5 trades −0.442R, −$307 (review 11-12). RSI Collapse Dip Buy (all day)
  (`ST7-rsi50dn-long-pm-t1s1-FD`) on Primary since 10-26: 10 trades −0.245R, −$166 (record 26 +0.028R, −0.151R w/o
  best day, 551% share `1 day`); review 11-06. Gap-Down Pop Fade, Heavy Selling (all day)
  (`RW3-gapdn-rsi5pop-flowsell-short-FD`): record 98 trades +0.327R but +0.106R w/o best day (10-22, 76%), last 4
  −0.382R (14).
- **Testing → Graveyard watch** (not raised): Early Sellers Above VWAP (`MF1-945-flowsell-vwapup`, T1, ex-Primary)
  30 trades / 13 sessions, 26.7% win vs 35.3% break-even, −0.360R, −0.438R w/o best day, last 4 −1.043R; reaches its
  10 Testing sessions (rule 20) on 11-06 → prompt then if still below. Index Last-Half-Hour Momentum
  (`intraday_momentum`, T1) 34 / 15, −0.266R, −0.309R w/o best day, 3 busiest −0.667R, −$20.97 (tiny $). Gap-Down
  Capitulation Buy (near-miss) (`NM-AR-AM-gapdown-capitulation-long`, T2) 40 / 5, −0.345R, −0.533R w/o best day vs
  2-year parent +0.278R; rare (INACT2: judged at 60 trades).
- Best non-Primary records with 20+ trades are still one-day records (NS4-FD +0.166R / −0.006R w/o best day, 103%;
  NM-MF3-qqqdn-gapdn-FD +0.236R / −1.009R).

### 4a. Monitoring (docs/live/monitor.json)
- **Afternoon VWAP Reclaim Fade (all day)** (`NS4-pm-vwap-reclaim-oversold-short-FD`), Testing 1 → Primary, marked
  10-27: 5 sessions since, 10 trades, 20% win, −0.435R, −$4.89 (0 green sessions; today 1 trade −0.37R); full record 27
  trades +0.166R, −0.006R w/o best day (10-22, 103%, `1 day`). Lean **drop** (owner: wait).
- **Generated NewLOD LUNCH short** (`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`),
  Gen → Testing 1, marked 10-27: 4 traded sessions since, 17 trades, 76.5% win, +0.406R, +$97.50, +0.074R w/o best day
  (10-27, 89%); full record 21 +0.379R, +0.129R w/o best day (77%, `1 day`). **Owner rule (set 11-03 10:53 ET): next
  TWO traded sessions green in R → 1 of 2 met** (11-03: 6 trades +1.67R, +$24.77). Not yet met. Lean **wait**.

### 4b. Watches
- **Failed Prior-Day-Low Break Long (0.1 ATR, low volume)** (`CWT14-failbrk-pdl-p10-lowvol-long`, T2 since 10-28):
  today 10 trades +0.82R, +$9.43; since the move 73 trades / 5 sessions (1 green), 57.5% win, −0.173R, −$97.52,
  −0.214R w/o best day; record 245 −0.031R.
- **PDL-1a R2A legs (T2)**: long leg (`CWT14-failbrk-pdl-p05-R2A-long`) today 20 trades, 70% win, +0.014R, +$23.22;
  **8 got the half-off** (5 scaled + breakeven, 3 scaled + target; +0.046R avg), **12 ran plain** (8 hit the ~0.1R full
  target inside one poll before a scale-out could fire, 4 flattened without reaching the +0.083R trigger; −0.007R avg).
  No cap blocking today (SO-1A exemption live). Since 11-02: 39 trades −0.069R, −$146.75. Short leg
  (`CWT14-failbrk-pdl-p05-R2A-short`): 0 signals in 2 sessions.
- **Gap-Down Heavy-Selling Short, no RSI condition (all day)** (`RW3S-gapdn-flowsell-short-FD`, T2, observation day 1 of
  5): 24 trades, 54% win, −0.049R, −1.17R, −$39.00 (9 stops, 7 targets, 8 flattens); its parent RW3-FD on Primary
  −0.195R (7).

### 4c. Primary −2R per-setup stop (FYI)
One latch: RW3-FD at 10:47 ET (4 stops 10:25-10:50). **13 entries blocked** 10:50-13:30 (HON, SPLV, VTR, CMS, TTAN,
ACN, DIA, INTU, VFLO, KBWB, DG, BTI, CB): what-if **+8.19R** (+0.63R avg, 7 of 13 at the 1R target) — the latch
**cost** R today (11-02 it saved 16.8R). Net since 11-02: +8.6R saved (before costs). Tracked under
`swing1103-L5-early-latch-whatif`.

### 4d. BRAKE-1 shadow line (FYI; never switched on)
Family stops: 6 (RW3-FD VG 10:25, MF2-FD IWB 10:44, RW3-FD IWR 10:47, RW3-FD MMM 10:50, MF4-FD IWB 11:15, RW3-FD SSNC
11:26) → trigger 10:47; the 26 family lots after it made +12.73R (+$221.18). **Primary R actual +11.33R vs with brake
+4.96R (−6.37R, −$110.59).** Running total since 2026-11-02: **−6.37R** (2 sessions). An 11:00-gated brake would not
have triggered (backlog `nightly-1103-brake1-morning-trigger`).
