# Nightly learning loop, 2026-11-06 (Friday): 7 accounts (Primary, Testing 1, Testing 2, Graveyard, Gen, Explore 1, Live Lab)

*Educational only — not financial advice. Live **paper** results from one session plus the since-start live record; they
describe what happened and are not evidence that anything works. **Configurations tried tonight: 13** (BURST2,
research/bdi/burst2, pre-registered; locked block never read). About 30 descriptive splits were looked at (setup, side,
hour, exit, poll, lot, twin, cluster, latency, peak-to-close, UNI1 setup-matched, halt / latch / brake / REG2 / FLOW1 /
leads shadows), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`. Job-log P/L is before costs. What-ifs (latch- or
halt-blocked signals) are on SIP 1-minute bars, entry at the signal's ref price, stop / target / 15:50, **before costs**.

**Rule changes inside the windows quoted** (research/ledger.jsonl): Primary: MF2-FD / MF4-FD promoted 10-20, ST7-FD
10-26, ~$4,000 lot 10-28, −2R per-setup stop 10-29, L3 pair 10-30. All: GX1 10-27. Testing: per-setup stop off 10-23,
BAR90 10-29, CF 10-30; Graveyard moves 11-02 / 11-03; UNI1 (T2 top-500) 11-04; ROLL1 (Explore 1 / Live Lab) 11-05.
**No setup / exit rule changed on 11-06.** Ops: GitHub's scheduler was down in the morning — the session guard dispatched
trade at 08:49 ET (run 42228656837) and Hunch at 09:49; a scheduled run (42281448892) took over at 14:38 (the self-handover
successor 42280141739 was cancelled). The −20R account halt (10:55) was restored by the 14:38 run ("restore: account
daily-loss halt fired earlier today - staying halted").

**Scripts** = nightly1105's with the date set to 11-06 (`close.py`, `polls.py`, `decmin.py`, `fetch.py`, `build.py`,
`autopsy.py`, `giveback.py`, `combined.py`, `today.py` (+ halt-blocked what-ifs), `forward.py`), new `cands.py`
(ex-market / busiest-session cards), `add_backlog.py`. Scratch (journals, bars, job logs) outside the repo.

**Market: up open, then a tech rollover and chop.** SPY +1.01% high at 09:54, +0.85% 10:00, +0.46% 10:30, +0.69% 12:00,
+0.20% 13:00, close +0.07%. **QQQ +0.68% at 10:00 → −0.21% at 10:30** (semis led), +0.31% 11:30, low −0.67% 12:53, close
−0.38%. IWM up all day (+0.94% high 15:33, close +0.61%). REG1 "up" (SPY +0.78% at 10:00).

## Failures first
1. **Session closed clean in all 7 accounts.** Phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data
   outages; 14:38 run's job log "flatten complete: no MCF positions open" for all 7; journal = EOD report = status =
   job-log "Trades" (52 / 92 / 165 / 623 / 356 / 24 / 19), submitted = booked in all 7 (Gen too: 356 / 356); EOD reports +
   scorecards 15:59 ET; final state pushes "job 14:39–14:42 done" (20:56–20:58 UTC) after the 08:58–09:00 run's pushes.
2. **Broker (Primary, read-only GET):** 0 positions, 0 open orders, equity $81,813.95 (last equity $83,052.55).
   **MTUM −183 fully closed by the flatten** (buy 183 filled 15:55:56 at $63.59; the MF2-FD MTUM short of 54 was a real
   journal trade, covered 10:46). The other six accounts' keys are not in this session: their state files show 0 positions.
3. **Gen: 348 buying-power rejects** (vs 24 on 11-05; all day 10:1x–15:0x, most 10:5x / 11:3x / 14:0x) + 1 bracket-price
   reject. Gen −12.9R / −$272.82; the rejected signals are not in the record. Housekeeping row `HK-GEN-BP` (capacity vs
   positions held), not a setup issue. Graveyard 67 buying-power + 15 bracket-price rejects.
4. **Changeover 08:49 run → 14:38 run (no runner gap > 5 min):** the 08:49 jobs ended 14:39:24–14:42:12 ET and the 14:38
   jobs started 14:39:26–14:42:14. Longest poll gap: Primary 1.9 min (14:38:12 → 14:40:07), T1 2.6, T2 2.0, Ex1 2.3, LL 2.9,
   GY 3.7 (10:35), Gen 5.3 (10:30; 4 gaps > 5 min). Decision minute 14:40 missed in T2 / GY / Gen / LL; Primary / T1 / Ex1 77
   of 77. The morning dispatch at 08:49 polled from 09:30:01 in all 7.
5. Coverage (1-min polls 09:30–15:54): Primary 384, T2 384, T1 352 (91.7%), Ex1 348 (90.6%), LL 314 (81.8%), GY 268 (69.8%),
   Gen 203 (52.9%). Skips: Primary 279 not shortable (ETB), 92 halted, 33 spread, 14 twin held; crosscheck 3 (Gen);
   "missed: triggered" 0.
6. Primary's runner snapshot trough −$8,107 at 10:44 is the MTUM phantom marked against its bogus $30.94 basis, not MCF
   trades (marked MCF trough −$1,386 at 11:35).

## 1. Headline per account (`autopsy_out.txt`, `giveback_out.txt`)
| account | trades | win% | avg R (costs) | sum R | **P/L after costs** (before) | marked peak / trough → close |
|---|---|---|---|---|---|---|
| Primary | 52 | 33% | −0.465 | **−24.18R** | **−$1,091.13** (−$1,057.07) | +$435 (10:36) / −$1,386 (11:35) → −$1,091 |
| Testing 1 | 92 | 61% | +0.040 | +3.64R | +$12.80 (+$16.36) | +$61 (10:42) / −$159 (15:10) → +$13 |
| Testing 2 | 165 | 61% | −0.012 | −2.00R | +$46.83 (+$51.95) | +$165 (11:14) / −$67 (15:10) → +$47 |
| Graveyard | 623 | 64% | +0.035 | +21.75R | +$396.52 (+$536.28) | +$2,153 (11:34) / −$632 (12:55) → +$397 |
| Gen | 356 | 52% | −0.036 | −12.90R | −$272.82 (−$157.92) | +$510 (10:36) / −$466 (11:35) → −$273 |
| Explore 1 | 24 | 54% | +0.100 | +2.40R | +$48.32 (+$51.12) | low-rep home (totals stay out of the post) |
| Live Lab | 19 | 42% | −0.062 | −1.17R | −$60.52 (−$59.54) | low-rep home (totals stay out of the post) |

**Primary dollars, with / without MTUM (owner rule 11-06):** Alpaca equity change **−$1,238.60 with MTUM**; the phantom
−183 marked from the 11-05 close ($62.585) to the $63.59 cover = **≈ −$184 → ≈ −$1,054 without MTUM** (journal −$1,091.13
after costs, −$1,057.07 before). 11-05 + 11-06 on Alpaca: −$13,062.62 with MTUM, ≈ −$1,422 without (11-05 trading-only
≈ −$367.71).

## 2. Autopsy — Primary (all 52 entries 10:00–10:50; halted 10:55)
- **MF2-FD (Early Sellers, Mid-High RSI (all day)) 28 trades −21.62R / −$641.36.** 10:20–10:30 entries (8) were fine (TER
  +2.68R, MU +2.16R targets). Then **6 shorts at the 10:35 poll and 14 at the 10:40 poll** (10:40:32–10:40:53), almost all
  semis / tech: ASML, AMKR, DELL, FIX, ASX, AVGO, MRVL, MU, SNDK, SKHY, UMC, ENTG, PANW and 5 ETPs (SOXX, SOXQ, QTEC, IYW,
  MTUM). QQQ had already fallen +0.68% → −0.21% (10:00–10:30) while SPY stayed ~+0.5% above its open. **20 stopped
  10:44–10:52** in the bounce, MFE of the 10:35 / 10:40 wave 0.05–0.8R, time to MFE 2 min for losers. 10:40 poll: 14 entries,
  0 winners, −16.1R (ETPs −6.1R). Cluster ≥ 10 per poll: 14 trades, 0% win, −1.15R avg.
- **MF4-FD (Early Sellers, Strong Heat (all day)) 14 trades −5.52R / −$456.14** — 4 early targets (10:10–10:30, +0.3..+0.7R),
  then 10 shorts 10:35–10:40 in the same names (KLAC, STX, AMKR, AXTI, AVGO, MRVL, SNDK, SOXQ, UMC, WDC): 7 stops, $ per R
  ~$83 (AXTI −$144 on −1.06R). 5 cross-setup twins (MF2 / MF4 on AVGO, MRVL, SNDK, SOXQ, UMC) all lost (−1.11R avg).
- **Same failure pattern as 11-05** (BURST1): both setups fire on selling that has already happened; when a whole theme
  qualifies in one poll the entries are one bet at the low, and the tight stops (0.125 / 0.25 × ATR) go together.
- Others: RW3-FD 4 trades +1.54R, RW5-FD 1 +0.49R, L3-fromopen 1 +1.20R, NS1 4 −0.27R (SOXS long −1.01R).
- Swing: +$435 at 10:36 (MF2 marked +$358) → −$1,386 at 11:35. Peak→close −$1,526: entered after the peak 28 trades −$764,
  open winners at the peak −$430, open losers −$332; 100% from 10:xx entries.
- Testing 1 +3.64R (RW7-FD 39 trades +6.70R; exhaustion_short −0.67R). Testing 2 −2.00R (RW3S −6.52R / 29; NS3V1 +1.65R).
  Graveyard +21.75R (heat_fade_short +23.3R / heat_fade_short-FD +12.4R / heat_fade_long +11.5R; CWT14 orl longs 91 trades
  −30.5R with 17–19 entries per poll at 10:0x). Gen −12.90R (GEN-261021-02 long +35.9R / 85; GEN-261029-08 short +24.8R;
  GEN-261021-07 long −26.6R / 46, GEN-261029-01 −21.3R). Longs 10:00–11:00 lost in GY (−33.2R) and Gen (−49.4R 10–12h).

## 3. Backlog (+3 ideas, 1 updated; `research/backlog.jsonl`, research/BACKLOG.md regenerated)
- `burst2-mf-after-flush-rework` (setup) — MF2 / MF4 entry condition "QQQ not already −0.4% in 30 min" or an RSI(5) pop,
  tested on their own record (BURST2's system gate failed two years).
- `nightly-1106-etp-component-stack` (risk) — one theme = one bet (ETP + its holdings in the same 15 min).
- `nightly-1106-halt-scope-latched-only` (risk) — halt only latched setups; 11-06's halt cost +8.1R (non-latched setups).
- `nightly-1029-burst20-one-bet` — 11-06 evidence (GY CWT14 orl / Gen bursts cut both ways).

## 4. BURST2 (priority tonight) — research/bdi/burst2/NOTES.md
13 configs, lineage 29, bar 2.60, **0 pass, no DECISION.** Open-loss latch (−2/−3/−4), same-family burst gate (4/6/8),
compass for burst shorts (SPY from-open side), symmetric compass, QQQ-flush gate. Near-miss `burst2-openloss-latch4`
(passes two years, fails live −49R); targeted runner-up `burst2-flush-gate-short` (Primary +36.7R with 0 setups worse,
11-05 +18.9R / 11-06 +11.6R; two-year VALID t 1.99, excess −0.38, MF family −57R). Both forward shadows only.
Queue: GATE2 / FLOW1-2Y not run tonight (BURST2 took the time); ROTA1 is Saturday's.

## 5. Live-funds hold
**Primary red: −24.18R after costs (−$1,091.13).** Positive-day streak in R: **0** (11-05 +4.54R ended at 1). Since Day 1
(10-23): 4 of 11 sessions green in R, **−32.54R**, −$2,437.14 after costs (journal). Alpaca since 11-05: see §1.

## 6. Suggestions (combined record 10-06..11-06, 24 sessions; `combined_out.txt`, `cands_out.txt`)
| setup | trades / sessions | win vs BE | avg R | ex-mkt | w/o best (share) | t | last 4 | bt | 3 busiest | per session |
|---|---|---|---|---|---|---|---|---|---|---|
| Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` | 124 / 18 | 44.4 / 38.3% | +0.121 | −0.106 | −0.141 (196%, `1 day` 10-22) | 0.37 | −0.485 | +0.046 | +0.083 | 6.9 |
| Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` | 121 / 20 | 59.5 / 67.0% | −0.118 | −0.148 | −0.171 | −0.94 | −0.364 | −0.017 | −0.302 | 6.1 |
| Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long` | 21 / 9 | 76.2 / 72.3% | +0.050 | +0.057 | −0.131 (289%, `1 day`) | 0.28 | −0.152 | +0.056 | +0.192 | 2.3 |
| Early Sellers, Strong Heat `MF4-h40-open-flowsell` | 22 / 7 | 63.6 / 58.6% | +0.052 | +0.061 | −0.029 (148%, `1 day`) | 0.32 | – | −0.017 | −0.100 | 3.1 |
| Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` | 90 / 16 | 70.0 / 64.8% | +0.063 | −0.063 | −0.033 (142%, `1 day`) | 0.44 | −0.528 | – | +0.247 | 5.6 |
| Big Loser Flush Buy `NS5-sma50-flush-oversold-long` | 31 / 12 | 51.6 / 46.0% | +0.064 | +0.199 | −0.004 (107%, `1 day`) | 0.33 | −0.328 | +0.002 | −0.037 | 2.6 |
| RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` | 37 / 12 | 59.5 / 48.7% | +0.161 | +0.225 | +0.058 (68%) | 0.92 | +0.476 | – | +0.032 | 3.1 |
| Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` | 257 / 17 | 61.1 / 49.3% | +0.169 | −0.033 | +0.056 (77%) | 1.05 | +0.615 | – | +0.367 | 15.1 |
| Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | 129 / 19 | 72.1 / 48.2% | +0.361 | +0.204 | +0.270 (42%) | 2.01 | +0.495 | – | +0.614 | 6.8 |
| Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` | 121 / 19 | 71.1 / 46.6% | +0.404 | +0.189 | +0.256 (50%, `1 day`) | 1.66 | +0.517 | – | +0.842 | 6.4 |
- Primary-only: MF2-FD 101 trades +0.065R; MF4-FD 89 −0.258R, −$1,825.20 combined; L3-rsi5hi since 10-30 14 −0.536R.
- **DECISIONs (for Saturday's Primary reevaluation):** `DM-MF2` and `DM-MF4` — move both to Testing 1 (a move; ex-primary
  marker), see the inbox. Borderline (hold, list for Saturday): NS1, MF4-h40 (base), L3-rsi5hi (L3H open), NS5 — all four
  are below zero without one session. ST7-FD (PROMO-ST7 10-session review, due today): keep — Primary since 10-26 21 trades
  +0.133R (−0.029R w/o best day, 112%), full record ex-market +0.225R.
- Promotion: none ready. Best Testing records RW1-FD (T2, 108 / 20, +0.088R, +0.045R w/o best, t 0.80, ex-market −0.107R)
  and RW7-FD (T1, 436 / 19, +0.061R, t 0.96, ex-market −0.132R) — both negative ex-market.
- **UNI1 (Testing 2 top-500, session 3):** same 18 setups since 11-04: 552 trades −0.201R vs −0.013R 10-20..11-03 (10 worse /
  8 better); today −0.012R on 165 (T1 +0.040R). Still mixed with two index trend days; the 11-06 chop day was flat.

### 6a. Monitoring (docs/live/monitor.json)
- **M1 — NS4-pm-vwap-reclaim-oversold-short-FD** (T1 → Primary mark 10-27): today 2 trades −0.41R; since mark 12 trades /
  6 sessions (0 green), −0.397R, −$5.81; record 29 +0.141R, −0.023R w/o best day (113%). Lean drop unchanged.
- **M2 — GEN-261026-03 NewLOD LUNCH short** (Gen → T1 mark 10-27): 1 signal, rejected (Gen buying power; what-if −1.00R);
  no trade → two-green rule still **1 of 2**.

### 6b. Watches
- `CWT14-failbrk-pdl-p10-lowvol-long` (T2 since 10-28): today 24 trades +2.52R; since the move 127 / 8 sessions (2 green),
  −0.224R, −$268.10; record 299 −0.078R.
- R2A legs (T2): long 34 trades −0.55R (+$2.92): scaled 17 +0.085R vs plain 17 −0.118R (8 plain reached the scale trigger);
  since 11-02 110 trades −0.110R. Short leg: no trade (13 since 11-04, −0.238R).
- **RW3S-gapdn-flowsell-short-FD (T2) — verdict: fails.** Today 29 trades −6.52R; since 11-03 **140 trades / 4 sessions,
  0 green, −0.290R, −$661.59, ex-market −0.260R**. (Session count: 11-03..11-06 = 4; OPEN_ITEMS had day 5 = 11-09.) Its
  parent RW3-FD (RSI(5) pop required) made +1.54R today on Primary: the pop condition is doing the work. Suggest a
  Graveyard move after the 11-09 session unless it is green (owner's decision; rule 20).

### 6c. Primary −2R per-setup stop and −20R account halt
- Latched: **MF2-FD 10:46:02, MF4-FD 10:51:59** — both after their last entry (10:40:53 / 10:40:55): **0 entries blocked by
  the latch today.** Latch running since 11-02: −4.15R (cost) over 5 sessions (today 0).
- **Account halt 10:55** (−20R): 92 signals blocked (47 first per setup-symbol) → what-if **+8.1R** before costs (all repeats
  +10.6R; job log +6.5R): RW3-FD +5.1R, RW5-FD +2.6R, NS5 +1.4R, L3-rsi5hi +1.1R, ST7 +0.1R, MF4 base +0.5R vs L3-fromopen
  −0.5R, MF2-FD −1.7R, MF4-FD −0.5R. → backlog `nightly-1106-halt-scope-latched-only`.
- latch1103-category-shadow day 3: Graveyard 11 setups latched, 411 first skips, what-if +30.6R → the latch **cost** 30.6R
  today (longs 25.8R; heat_fade_long +20.9R blocked); Primary 0. **3-day tally: GY +218.2R saved, Primary −12.75R.**

### 6c2. BRAKE-1 shadow
Family stops 32 (third at 10:45:29) → 4 family lots after it made +1.25R → with brake −24.80R vs −24.18R (**−0.63R**, −$9.26).
Running since 11-02: **−10.32R** (5 sessions).

### 6c3. REG2 shadow, session 3 of 5 (`research/bdi/reg2_shadow.csv`, 52 rows)
SPY +0.78% vs open at 10:00 → keep shorts, drop longs: kept 48 shorts −23.90R, dropped 4 longs −0.27R → kept-only −23.90R
vs actual −24.18R (**+0.27R**). 3-session tally −6.29R.

### 6c4. Claude's Team final (shadow, `research/shadow_primary/team/2026-11-06.json`, pushed to mcf-data-team)
**Team +10.84R / +$96.09 after costs (57 trades)** vs Primary −24.18R / Alpaca −$1,238.60 with MTUM (≈ −$1,054 without).
RW3-FD +5.04R (13), RW1-FD (T2) +4.21R (22), RW5-FD +2.72R (8), NS5 +1.18R (9), NM-ETF-late-dip +0.37R (2), ST7-FD −0.66R,
CWT09-g10 vwaploss −1.01R, GEN-261026-03 −1.01R. The Team held no MF2 / MF4.

### 6d. Other forward shadows (`forward.json`)
FLOW1: no trade closed by 10:15 on Primary → 0; merged rule 0 (SPY control +39.0R). L2 no trigger; L3 not qualifying;
L6 counter-index +0.082R vs −0.073R, setup-adjusted excess +0.003R.
