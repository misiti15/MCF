# Nightly learning loop, 2026-11-04 (Wednesday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **Configurations tried tonight: 0**
(the 2-year lab trade lists `research/history2y/data` are not in this container, so the 4 new hypotheses stay `idea`
and no holdout was touched). About 30 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin,
cluster, latency, peak-to-close attribution, latch / brake / REG2 / FLOW1 / leads shadows), so some will look strong by
chance.*

**Costs are in.** P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`. The job log shows P/L **before** costs (Primary
−$141.37 / −8.8R journal R = the post's figure). What-ifs (blocked / halted signals) are on SIP 1-minute bars, entry at
the signal's ref price, stop / target / 15:50 close, **before costs**.

**Rule changes inside the windows quoted below** (research/ledger.jsonl effective dates): Primary: ST7-FD 10-26,
~$4,000 size 10-28, −2R per-setup stop 10-29, L3 pair 10-30. All: GX1 10-27. Testing: per-setup stop off 10-23, BAR90
10-29, CF 10-30; NS3-FD / RW4-FD → GY 11-02; R2A legs T2 11-02; SO-1A, RW3S (T2), MF3-FD / MF5-FD → GY 11-03.
**From today (11-04): UNI1 (Testing 2 trades a top-500 pool) and DM-N3 (NS5-FD, ST4-FD, RW6G1-FD → Graveyard).**
Next: ROLL1 — 42 low-rep setups move to Explore 1 / Live Lab from 11-05. No rule changed during today's session.

**Scripts** = nightly1103's with the date set to 11-04 (`fetch.py`, `build.py`, `close.py`, `polls.py`, `decmin.py`,
`autopsy.py`, `giveback.py`, `rejects.py`, `combined.py`, `today.py`) plus `forward.py` (REG2 shadow →
`research/bdi/reg2_shadow.csv`, FLOW1 / L1 / L2 / L3 / L6 / latch-category forward tallies → `forward.json`,
GEN-261026-03 halted what-if) and `add_backlog.py`.

**Market: an up day that faded from a 10:00 spike.** SPY +1.65% at 10:00, +0.22% 11:30, +0.77% 13:00, close +0.48%;
QQQ +1.89% (10:15) → +0.50%; IWM +0.70% (09:45) → −1.01% (11:27) → −0.06%. SPY vs open at 10:00 +0.55% (REG1 "up").

## Failures first

1. **No broken session.** All 5 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data
   outages; job logs "flatten complete: no MCF positions open"; journal = EOD report = status = job-log "Trades"
   (54 / 20 / 139 / 507 / 255); job-log P/L = journal before-cost P/L; EOD reports and scorecards 15:57 ET.
2. **Gen: 4 submitted entries unbooked** (GFL 09:50, AVDV 09:55, BA + FCX 10:05; 259 submitted vs 255 trades) —
   HK-RECON-GEN again; the next reconcile should book them. Gen's −$2,454.65 may be understated.
3. **Gen halted at 10:50** (account daily loss limit; 2 "daily loss limit" + 799 "halted" skips; job-log what-if −53R,
   i.e. the halt saved R). Intended rule, not a fault.
4. Coverage (of 384 1-min polls): Primary 384, T1 384, **T2 354 (92.2%), GY 328 (85.4%), Gen 281 (73.2%)**; misses
   are bucket minutes 1-2 (OPS-POLL residual); longest gap 3.9 min (Gen, 14:30 hand-over), **no gap > 5 min**;
   decision minutes 77/77 except Primary and GY 76/77 (14:30). Broker rejects: GY 1 (stop price), Gen 2 (take-profit
   price); crosscheck 1 (Gen); "missed: triggered" 0; Graveyard buying-power rejects **0** (59 yesterday).
5. **Explore 1 / Live Lab readiness (start 11-05):** trade.yml / eod.yml on the base branch carry both accounts (PR #147
   merged 16:06 ET); account-check 21:06 UTC: keys set, both ACTIVE, $100k, shorting on. State branches
   `mcf-data-explore1` / `mcf-data-livelab` do not exist yet — the trade job creates them (orphan) on its first run.
   Nothing to fix tonight; first-session check tomorrow.
6. Ledger check `--only 2026-11-04-lowrep-explore1-livelab`: **not run** — no bar cache (`data/cache` empty in this
   container, so `BarStore.symbols()` is empty and the check raises IndexError). It also scores the Primary config only,
   which a Testing → Explore move does not touch.

## 1. Headline per account (`autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | avg R (costs) | **P/L after costs** (before) | marked peak / trough → close |
|---|---|---|---|---|---|
| Primary | 54 | 48% | −0.199 | **−$208.63** (−$141.37) | **+$463 (12:17)** / −$278 (14:42) → −$209 |
| Testing 1 | 20 | 40% | −0.215 | −$36.66 (−$35.52) | +$7 (11:01) → −$37 (all longs; split-tape gate skipped 151 shorts) |
| Testing 2 | 139 | 45% | −0.232 | −$517.68 (−$501.86) | +$12 (10:09) / −$550 (12:35) → −$518 |
| Graveyard | 507 | 54% | −0.118 | −$771.90 (−$642.72) | +$49 (09:57) / −$1,094 (13:59) → −$772 |
| Gen | 255 | 22% | −0.687 | **−$2,454.65** (−$2,292.89) | never above 0; −$2,614 (13:20); halted 10:50 |

**Primary live-funds hold: RED.** −$208.63 after costs (−$141.37 before; 54 trades, −10.75R) → streak **0** (11-03's
streak of 1 ends). Since Day 1 (10-23): **4 of 9 sessions positive, −$927.01 after costs** (−$769.01 before). Since start
7 of 22 positive, −$1,948.37. Rule changes in that window: ~$4k size 10-28, −2R stop 10-29, L3 pair 10-30.

**Why Primary lost: a +$463 midday peak given back by shorts after SPY's 11:30-13:00 rally** ($671 give-back, all
shorts). Entries 12:00-13:59: 16 trades, −$486. Early Sellers, Mid-High RSI (all day) (`MF2-open-rsimidhi-flowsell-FD`)
8 trades −6.48R / −$231.80 — five lots entered in the 12:15 poll, five stops 12:21-12:27, then latched (12:35); Early
Sellers, Strong Heat (all day) (`MF4-h40-open-flowsell-FD`) 12 trades −4.34R / −$163.32 (gold-ETF stops 10:55);
Gap-Down Rebound Overbought Short (all day) (`L3-gap-slope-rsi5hi-FD`) NRIX shorted 3× 13:00-14:10, 3 stops,
−2.87R / −$199.44. Winners: L3-fromopen 5 trades +2.69R / +$180.77, ST7-FD 9 trades +3.14R / +$118.47, RW3-FD +$101.69.

## 2. Winner / loser autopsy (`autopsy_out.txt`; SIP 1-min MFE / MAE for all 975 trades)

- **Primary**: winners peaked at a median +0.77R after 23 min and gave back 0.09R; losers peaked +0.28R, MAE 1.06R;
  11 "never worked" (−$536). Same-setup clusters (≥ 5 in one poll) 20 trades −0.196R ≈ singles. Latency median 2.5 s
  (90th 5.0 s); fast tercile worst (−0.39R) — small n, not a latency problem.
- **Testing 1**: all longs (151 shorts blocked by the split-tape gate on an up morning); CWT05 flush −$28, NS1-FD −$24.
- **Testing 2 (UNI1 day 1)**: Failed PDL-break longs again — `CWT14-failbrk-pdl-p10-long` 25 trades −12.8R / −$195 and
  p10-lowvol 15 trades −8.65R / −$116 on the IWM −1% morning; 46 "never worked" −$568.
- **Graveyard**: top two (owner note) — Gap-Down Bounce Rejection Short (5% gap) (`CWT09-gapdn-bounce-g5-lowerhalf-short`)
  8 trades +5.09R / +$373 and Opening-Range Low Sweep Reversal (`LIQ-orl-sweep-open15-s25-long`) 25 trades +14.76R /
  +$317 (all held to the 15:50 flatten). Worst: CWT14 pdl-p05 longs −$559, ST2-FD −$214, RW2-FD −$174.
- **Gen**: everything entered 09:50-10:50 into the SPY spike; SPY-gated setups worst (GEN-261021-02 SPYgt0p5 long 71
  trades −0.451R / −$827; GEN-261029-08 SPYgt0p5 short 49 trades −0.978R / −$713). Shorts −0.88R, longs −0.42R.
- **Recurring patterns tied to losers**: (a) index-up gates firing at a spike top (Gen); (b) same-symbol re-entry after a
  stop (NRIX ×3); (c) failed-breakdown longs on a small-cap-down / large-cap-up day (T2, GY); (d) a time cluster of family
  stops marks an index turn against the short book (MF2 12:21-12:27; BRAKE-1 helped today, hurt 11-03).

## 3. Backlog (4 new, status idea; `research/backlog.jsonl`, research/BACKLOG.md regenerated)
- `nightly-1104-no-reentry-after-stop-same-symbol` (risk) — (b).
- `nightly-1104-spy-gate-spike-exhaustion` (setup filter) — (a).
- `nightly-1104-pdl-longs-smallcap-rotation` (setup filter) — (c); needs IWM in the 2-year context file.
- `nightly-1104-midday-index-turn-short-cluster` (risk) — (d); needs exit times on the 2-year lists.

**Swarm (step 4): not run.** 4 new hypotheses would trigger it, but the 2-year lab lists are not in this container (the
FLOW1 note found the same on 11-04). Queue order stays FLOW1-2Y → SIZE1 → GY-BP; tonight's four go behind them.

## 4. Suggestions (`combined_out.txt`, `today_out.txt`; 22 sessions 10-06..11-04, costs in)

**One DECISION (L3H)**: Gap-Down Rebound Overbought Short (all day) (`L3-gap-slope-rsi5hi-FD`), Primary → Testing 1 now
instead of the 11-12 review. Primary since 10-30: 9 trades, 33% win, −0.564R, −$506.34, 1 of 4 sessions green; full record
85 trades / 15 sessions, +0.095R, **+0.001R w/o best day (10-26 = 99%, `1 day`)**, t 0.65, last 4 −0.564R (9), 3 busiest
+0.247R, P/L −$312.70; no backtest figure in the scorecard. Rule changes: ~$4k size 10-28, −2R stop 10-29 (latched
today 14:16), promoted 10-30.
- **No promotion is ready.** Best non-Primary 20+-trade records are still one-day records (NS4-FD −0.006R w/o best day;
  GEN-261022-07 +0.161R / −0.317R; NM-MF3 −1.009R).
- **Graveyard → Testing: not supported.** The two top setups today have losing full records: CWT09-gapdn-bounce-g5 120
  trades / 14 sessions, 37.5% win vs 41.1% break-even, −0.102R, −0.202R w/o best day, last 4 +0.637R (37), −$292.24;
  LIQ-orl-sweep 277 / 17, 42.6% vs 47.7%, −0.087R, −0.154R w/o best day, last 4 +0.211R (46), −$388.71. Watch the last-4
  turn; no move.
- **Primary drift watch**: ST7-FD on Primary since 10-26: 19 trades +0.036R, −$47.95 (today +3.14R) — review 11-06.
  L3-fromopen on Primary since 10-30: 11 trades −0.034R, −$145.30 — review 11-12.
- **Testing → Graveyard watch (not raised)**: MF1-945 (T1) 30 trades −0.360R, −0.438R w/o best day, no trade today,
  rule-20 date 11-06; intraday_momentum (T1) 38 / 16, −0.296R, −0.335R w/o best day, t −2.01, last 4 −0.677R, −$26.55
  (rare, INACT2: judged at 60 trades); NS3V1 (T2) 22 / 4, −0.502R, −$501.
- **UNI1 (Testing 2 top-500) day 1**: 139 trades (prior 5 sessions 151 / session), −0.232R, −$517.68 vs −0.101R the prior 5
  sessions and −0.131R since start; entry slip 6.3 vs 3.7 bps; pool live (health `universe_top_n` 500). One day — no
  read. (universe.csv's `top_n` flag is not the runner's pool: 105 of 139 trades carry it; the runner ranks on priors.)

### 4a. Monitoring (docs/live/monitor.json)
- **Afternoon VWAP Reclaim Fade (all day)** (`NS4-pm-vwap-reclaim-oversold-short-FD`), T1 → Primary, marked 10-27: no
  trade today; since mark 10 trades / 5 sessions (0 green), −0.435R, −$4.89; record 27 +0.166R / −0.006R w/o best day
  (103%, `1 day`). Lean drop (owner: wait).
- **Generated NewLOD LUNCH short** (`GEN-261026-03-…-holdtr-short`), Gen → T1, marked 10-27: **did not trade** — its 8
  signals (11:40-13:55) were all skipped by Gen's 10:50 account halt (what-if −7.93R, 7 of 8 stops). **Rule still 1 of 2
  green traded sessions; not met.** Since mark 17 trades +0.406R, +0.074R w/o best day (89%).

### 4b. Watches
- `CWT14-failbrk-pdl-p10-lowvol-long` (T2 since 10-28): today 15 trades −8.65R, −$115.67; since the move 88 trades / 6
  sessions (1 green), −0.242R, −$213.19, −0.284R w/o best day; record 260 −0.062R.
- **R2A legs (T2)**: a short-regime day — long leg 0 signals (the inactive-check alarm on it is the regime gate, not a
  fault), short leg's first trades: 13 trades, 38% win, −0.238R, −$54.11 (2 stops, 2 targets, rest scaled / flattened).
  Long leg since 11-02: 39 trades −0.069R, −$146.75. Scale-out vs plain: no long-leg lots today.
- **RW3S-gapdn-flowsell-short-FD** (T2, day 2 of 5): 27 trades −2.08R, −$46.83; 2 days 51 trades −0.064R, −$85.83,
  0 green (parent RW3-FD on Primary −1.17R today).

### 4c. Primary −2R per-setup stop (FYI)
Journal blocks: MF2-FD (first 12:35, 5 signals) and MF4-FD (first 13:16, 2 signals): what-if **−2.5R → the latch saved
+2.5R** today; running since 11-02 **+11.1R saved** (before costs). L3-rsi5hi reached −2R at 14:16 with no later signal.
latch1103-category-shadow (all accounts): Graveyard 16 setups latched, 847 first skips, what-if **+43.4R → the latch
cost 43.4R** (excess −177.8R; longs −33.0R, shorts −10.4R; heat_fade_short-FD +21.1R, CWT14 orl longs +25R blocked);
Primary +2.5R (excess +5.1R). Day 1 of ≥ 20.

### 4d. BRAKE-1 shadow (never switched on)
Family stops 16 (first three by 10:55: MF2-FD IP 10:38, MF4-FD JD 10:52, GLDM 10:55) → trigger 10:55; 19 family lots after
it made −11.16R (−$285.20). **Primary actual −10.75R vs with brake −5.17R (+5.58R, +$142.60).** Running total since
11-02: **−0.79R** (3 sessions: 0 / −6.37 / +5.58).

### 4e. REG2 shadow, day 1 of 5 (`research/bdi/reg2_shadow.csv`)
SPY +0.55% vs open at 10:00 → keep shorts, drop longs. Primary actual −10.75R; **kept-only −13.06R (−$298.77), 2.32R
worse**; kept 37 shorts avg −0.369R, dropped 16 longs avg +0.145R (+$90.14); 1 pre-10:00 trade (+0.58R).

### 4f. FLOW1 and swing leads, forward day 1 (`forward.json`; research/bdi/swings/hypotheses.jsonl)
- FLOW1 merged (T 10:15, k 3, win): longs "contra" (78 closed, 50% win) → 303 later longs dropped (avg +0.013R) vs kept
  shorts −0.375R → **delta −3.90R**; Primary (sumR): only 2 trades closed by 10:15 → no state, delta 0. SPY-rule control
  (trade with SPY's side at 10:15) +140.5R merged / +13.5R Primary — the opposite of REG2's fade on this day.
- L1 vol / inverse ETP longs (symbol-list proxy): 20 trades +0.208R vs the same setups' other longs −0.152R (against the
  lead). L2: no trigger. L3: not a qualifying day (IWM −0.05% at 10:00). L6 counter-index entries: 469 trades −0.389R vs
  others −0.198R; setup-adjusted excess +0.003R.
