# Nightly learning loop, analysis part: 2026-10-22 (Primary, Testing 1, Testing 2, Graveyard, Setup Generator)

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened; they are not evidence that anything works. **One configuration was replayed
tonight** (`latch2`, the per-setup stop latching for the day, on the ll1020 live candidate set; protection lineage N 92 → 93,
bar 3.01). No backtest, no locked block, no holdout. No config, setup or exit was changed. About 45 descriptive splits were
looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency per account), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is "R(j)". Blocked signals
are priced with the runner's what-if run (run 2) less the production cost model.

**Already analysed today, cited not redone:** `l3_1022` (L3-gap-slope-fromopen-FD, decision L3-1 open), `ns3var1022` (V1),
`st7_1022` (S1), `pdh1022` (P0), `regime1022` (R1/R2/R3).

**Scripts** = nightly1021's with the date set to 10-22, plus three new ones. Run each as `python <script> <scratch>`:
`fetch.py`, `build.py` → `trades.csv`, `close.py <scratch> <repo>` → `close_out.txt` (new: session close + poll log),
`autopsy.py`, `giveback.py`, `tables.py > tables_out.md`, `caps.py`, `combined.py`, `rearm.py` → `rearm_out.txt` (new),
`latch.py` → `latch_out.txt` (new). LL-1.5: `research/bdi/ll1020/replay.py` now has 10-22 in DAYS.

**Market: Nasdaq down, small caps up.** SPY −0.31% (high +0.17% 10:03, low −0.68% 15:02); QQQ −1.27% (high +0.26% 10:03,
low −1.64% 15:47; −0.50% at 12:00 → −0.94% at 13:00); IWM +0.68%.

## Failures first

1. **Nothing broke.** All 5 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages;
   journal trades = submitted signals = EOD report rows = `status.today.trades`; EOD report + scorecard pushed 19:57–19:58 UTC.
   Not verifiable here: open orders at the broker and the GitHub Actions job logs (the journal = report = status match is the
   proxy for "final state push succeeded").
2. **The per-setup −2R stop re-arms** (new finding). `mcf/execution/risk.py` blocks a setup only *while* realized R(j) ≤ −2R;
   a later winner lifts it back above −2R and the setup trades again. The owner's rule reads "a setup stops for the day".
   Graveyard RW2-exhaustion-noon-adv150-short-FD: tripped 10:15 (−2.46R), CCL target at 10:28 (→ −1.84R), re-armed, opened
   20 lots 10:40–11:01 (15 in the 11:00 poll), 18 stopped: **−19.53R after the trip**, day −21.38R (−$272). Since 10-20:
   13 re-arms, 55 entries after the trip, **−31.22R** (`rearm_out.txt`). → DECISION **LL-LATCH**, backlog `nightly-1022-setup-stop-latch`.
3. **The open-lot overshoot again** (no new item; LL-OPEN, R2 answered "no new stop"): Graveyard CWT14-failbrk-orl-p05-long
   13 lots open at the 12:50 trip → −12.43R; Testing 1 CWT14-failbrk-pdl-p05-long 8 open → −7.15R.
4. **The −2R stop also cut a winner hard:** Testing 1 RW7-gapdn-bounce-early-short-FD tripped at 11:25 after 5 trades
   (−3.41R(j)) and then blocked **105 signals worth +45.91R** what-if (75% win) on the Nasdaq slide. All T1 loss-limit blocks
   netted +50.47R (≈ +$384). Feeds LL-1.5 / ll1020 (freq_step already covers "bigger stop for frequent setups"); no new item.
5. **Graveyard −$1,338 and GEN −$568** on longs into a −1.3% Nasdaq (below).

## 0. Session close, this morning's moves, poll log (`close_out.txt`)

| account | phase | positions | flatten_failed | polls | journal = submitted = report = status | EOD + scorecard | poll log (files / size / rows) |
|---|---|---|---|---|---|---|---|
| Primary | closed | 0 | [] | 47 | 126 = 126 = 126 = 126 | yes (15:58 ET) | 32 / 4.27 MB / 379 |
| Testing 1 | closed | 0 | [] | 47 | 113 ×4 | yes | 32 / 4.03 MB |
| Testing 2 | closed | 0 | [] | 48 | 138 ×4 | yes | 26 / 1.87 MB / 157 |
| Graveyard | closed | 0 | [] | 48 | 281 ×4 | yes | 32 / 3.74 MB |
| GEN | closed | 0 | [] | 49 | 4 ×4 | yes | 26 / 1.47 MB |

- **Poll-input log, first day: landed on all 5 data branches** (`polls/2026-10-22/HHMMSS.jsonl.gz`, 09:40–15:55, one gz per
  ~12 min push; one JSON row per 1-min fetch: t, ms, n, got, fresh, late, miss, none list, stale). **15.4 MB/day in total**
  (≈ 0.3 GB/month across the 5 branches if it stays this size).
- **This morning's moves traded in their new accounts only.**
  - Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD): Testing 2 only, 11 signals → 6 trades
    (+$14.06, 5 of 6 won); 5 spread skips; disabled in Testing 1, absent from Primary.
  - RW6G1-ns2-up3-vwap2sd-short: enabled in Testing 1, **0 signals** (it is rare: last fired 10-15 in Primary); its -FD
    traded 2 (+$13.20). No twin conflict possible today.
  - CWT14-failbrk-pdh-p05-lowvol-short / -p10-lowvol-short: Graveyard only, 13 and 14 trades (−$19.56 each); none in T1/T2.
- **"Twin held" behaved:** Primary 6 (MF4-h40 base ← MF4-FD 5, MF2 base ← MF2-FD 1; what-if +2.38R), T1 3 (−2.56R),
  GY 12 (−7.29R), T2 0 (NS3-T2 group starts tomorrow with NS3V1).
- **TWIN-GRP:** still no LD signal (LD1–LD8 fired nothing again); NM-MF3-qqqdn-gapdn-FD (M1 observation) fired for the
  first time: 18 trades, 78% win, +$95.47.

## 1. Headline per account (real trades, run 1)

| account | trades | win% | avgR (costs) | R(j) | P/L journal | **P/L after costs** | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|---|---|
| Primary | 126 | 76% | +0.522 | +0.547 | +$1,432.56 | **+$1,369.10** | 23 / 87 / 16 | +$1,553 (15:47) → +$1,369 (trough −$168 12:26) |
| Testing 1 | 113 | 50% | −0.190 | −0.160 | −$46.33 | **−$72.69** | 47 / 50 / 14 | +$22 (10:04) → −$73 |
| Testing 2 | 138 | 59% | −0.007 | +0.037 | +$31.78 | **+$1.32** | 45 / 74 / 18 | +$105 (13:28) → +$1 (trough −$204 11:15) |
| Graveyard | 281 | 46% | −0.275 | −0.249 | −$1,217.73 | **−$1,338.43** | 131 / 110 / 40 | +$12 (09:54) → −$1,338 (trough −$1,594 15:44) |
| GEN | 4 | 0% | −1.057 | −1.026 | −$549.95 | **−$568.11** | 4 / 0 / 0 | 0 → −$568 |

**Total after costs: −$608.81** (5 accounts). Every account's long book lost (Primary −$180, T1 −$150, T2 −$162, GY −$1,196,
GEN −$568); only short books made money (Primary +$1,549).

### 1a. Intraday peak vs close (`giveback_out.txt`)

| account | giveback | where it went |
|---|---|---|
| Primary | $184 | all 12 open shorts flattened at 15:55 as QQQ bounced off −1.64% (late flatten −$174, 16 trades) — fits `nightly-1014-fd-short-late-giveback` |
| Testing 1 | $95 | entries after the 10:04 peak −$59, mostly CWT14-failbrk-pdl-p05-long (−$164) into the Nasdaq slide |
| Testing 2 | $104 | open losers at the 13:28 peak −$79; late flatten −$53 |
| Graveyard | $1,350 | 273 entries after a 09:54 peak: CWT14-failbrk-orl-p05-long −$639, RW2-FD −$272, LIQ-orl-sweep −$263 |
| GEN | $568 | GEN-261022-01 ORB-fail-up hold-long: 4 longs 10:36–10:59, all stopped |

**Primary's day was one noon burst.** 52 trades from the 12:10–12:20 polls made **+$994 (73% of the day)**: RW5-FD 21
(+$410), MF2-FD 15 (+$352), RW3-FD 13 (+$297) on 35 symbols (12 taken by two setups; 22 stacked lots), shorting gap-down
names' noon bounce just before QQQ fell from −0.50% to −0.94%. Clusters of ≥ 5 per poll won 97% today (on 10-21 stacked lots
lost −$284). It is one correlated bet; cluster caps were already tested and rejected (regime1022 R2), so no new item.

## 2. Winner/loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 662 trades)

| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winner give-back | time to MFE winners / losers | entry slip | latency median / p90 |
|---|---|---|---|---|---|---|---|
| Primary | 15 of 30, −$320 | 4 | 0.97 / 0.22 | 0.06R | 37 / 3 min | 4.1 bps | 1.3 / 2.7 s |
| Testing 1 | 29 of 57, −$288 | 11 | 0.65 / 0.27 | 0.08R | 16 / 2 min | 5.4 bps | 1.2 / 3.4 s |
| Testing 2 | 25 of 56, −$262 | 14 | 0.85 / 0.23 | 0.07R | 32 / 10 min | 1.3 bps | 1.3 / 2.7 s |
| Graveyard | 75 of 152, −$1,579 | 28 | 0.67 / 0.35 | 0.09R | 34 / 6 min | 4.0 bps | 1.5 / 3.4 s |
| GEN | 3 of 4, −$389 | 0 | — | — | — / 5 min | 5.8 bps | 2.7 / 3.3 s |

Latency had no edge (Primary fast/mid/slow terciles +0.64 / +0.38 / +0.55R). Losers fail fast (median 2–10 min to their best
point); winners take 15–37 min. Patterns tied to existing items:
- **Primary.** RW3-FD 25 of 25 won (+$613.54), RW5-FD 86% (+$457.30), MF2-FD 78% (+$426.49), MF4-h40-FD 80% (+$83.82).
  Losers: Failed Prior-Day-Low Break Long (0.1 ATR, low volume) (CWT14-failbrk-pdl-p10-lowvol-long) 18 trades −$195.12
  (8 stops, losers' best 0.29R within 2 min: longs into a falling Nasdaq — `nightly-1012-cwt14-long-index-confirm`);
  L3-fromopen-FD 18 trades −$15.12 (SNAP shorted 3 times, all stopped; see l3_1022). 14:00+ entries 0 of 8 (−$103).
  Refire entries +0.15R (15) vs first entries +0.57R.
- **Testing 1.** CWT14-failbrk-pdl-p05-long −$168.55 (36, 11 of 17 losers never worked, clusters of 12). orb20_a +$133.10
  (6, 83%). NS4-pm-vwap-reclaim-oversold-short-FD +$48.15 (5).
- **Testing 2.** NM-AR-AM-gapdown-capitulation-long −$197.14 (22, 32%, 8 of 15 losers never worked, clusters of 9; 25
  trades −$238 over 2 days) — capitulation longs on a Nasdaq-down day (`swarm1017-arena-am-long-gapdown-capitulation`).
  Stretched Above VWAP Fade (CWT13-vwapstretch-z05-short) 1 of 8 won, tripped, blocked 27 more worth −24.71R.
- **Graveyard.** CWT14-failbrk-orl-p05-long −$639.14 (65 trades, 18 of 30 losers never worked, 13 lots open at the trip);
  RW2-FD re-arm (above); LIQ-orl-sweep −$262.90 (17, 18%). heat_fade_short-FD +$227.43 (47, 57%) — a reversal of 10-21.
- **GEN.** GEN-261022-01 (first day): 4 of 4 stopped, 3 never worked; GEN sizing is $137 median risk/trade (80 slots,
  by design) against $8–19 elsewhere, so 4 trades = −$568.

**Backlog:** 1 new idea, `nightly-1022-setup-stop-latch` (risk, status idea, 1 configuration). Everything else above
matches existing items (cited). **Step 4 swarm deferred:** only 1 new hypothesis (< 3), and no setup is near a gate
(best: NS4-pm-vwap-reclaim-oversold-short-FD 16 live trades, t_day 2.09; backtest of its base −0.080R).

### LL-LATCH replay (`latch_out.txt`, 1 configuration)

Same candidate set and pricing as ll1020 (live trades + the limit's blocked signals priced by the what-if run), Testing 1/2,
GEN, Graveyard, 10-12..10-22:

| rule | 9-day net R | 10-22 | entries taken |
|---|---|---|---|
| none | −822.17 | −98.99 | 6,729 |
| fixed2 (live, re-arms) | −583.39 | −105.93 | 5,179 |
| **latch2** | **−545.23** | −75.31 | 4,863 |
| fixed1.5 (LL-1.5) | −518.93 | −81.60 | 4,978 |

latch2 − fixed2: **+38.16R**, 6 days better / 2 worse, day-clustered t 1.12 (bar 3.01); without 10-22 +7.54R. Weak evidence
either way; the case for it is that it makes the stop do what the owner's rule says.

## 3. Live-funds hold: Primary positive-day streak

| | 10-12 | 10-13 | 10-14 | 10-15 | 10-16 | 10-19 | 10-20 | 10-21 | 10-22 |
|---|---|---|---|---|---|---|---|---|---|
| after costs | **+115.77** | −101.67 | **+60.35** | −926.53 | −14.41 | −63.92 | −46.13 | −626.57 | **+1,369.10** |

- **Today: positive (best day since start). Consecutive positive Primary sessions: 1.** 3 of 13 sessions positive.
- Since start: 592 trades, 50.0% win, **−$1,021.36 after costs**. The hold stays.

## 4. Promotion / demotion suggestions (`combined_out.txt`; owner decides each)

Not re-suggested: L3-1 and N3 (pending, numbers not materially changed: L3-fromopen-FD Primary now 23 trades −$192.05,
exactly as l3_1022 reported).

| setup | trades | sessions | win / BE win | avgR | t_day | last-4 R (n) | backtest | suggestion |
|---|---|---|---|---|---|---|---|---|
| Stretched Above VWAP Fade (CWT13-vwapstretch-z05-short), Testing 2 | 61 | 7 | 32.8% / 55.3% | −0.403 | −2.06 | −0.468 (20) | −0.069 | **D1: → Graveyard** |
| Failed Prior-Day-Low Break Long (0.05 ATR, low volume) (CWT14-failbrk-pdl-p05-lowvol-long), T2 | 207 | 9 | 60.4% / 66.2% | −0.108 | −0.86 | −0.104 (62) | −0.096 | watch (no decision) |
| NS4-pm-vwap-reclaim-oversold-short-FD, T1 | 16 | 5 | 68.8% / 41.5% | +0.537 | 2.09 | +0.356 (14) | −0.080 (base) | too few trades |

Primary keepers holding up: RW3-FD 76 trades +0.455R (t_day 1.43), RW5-FD 78 +0.436R (1.72), MF2-FD 49 +0.819R (1.36),
MF4-h40-FD 51 +0.212R (2.13).

## 6b. Watch list (Primary-only since 2026-10-21)
- Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD): 23 trades, 39% win, −0.31R, −$192.05 — see l3_1022 / L3-1.
- Failed Prior-Day-Low Break Long (0.1 ATR, low volume) (CWT14-failbrk-pdl-p10-lowvol-long): 24 trades, 67% win, −0.09R,
  −$161.77 (10-21 +$33.35, 10-22 −$195.12); backtest −0.095R. First review 10-27.

## 6c. LL-1.5 monitor (`research/bdi/ll1020/replay.py`, DAYS now ends 10-22)

| 10-22 net R after costs | −2R (live) | −1.5R |
|---|---|---|
| Testing 1 | −21.42 | −21.42 |
| Testing 2 | +0.19 | +1.01 |
| GEN | −4.23 | −4.23 |
| Graveyard | −80.47 | −56.96 |
| **day** | **−105.93** | **−81.60** |

- **10-22: −1.5R ahead by +24.33R**, +19.53R of it the RW2-FD re-arm (at −1.5R the CCL winner left realized at −1.83R, still
  blocked). **Since 10-21: +23.90R** (2 of 3 sessions). **7-day base +40.56R**; 9 days +64.46R, 7 better / 2 worse,
  day-clustered t 2.36 (protection bar 3.01 not met). Decision due in tomorrow's brief.

## Housekeeping
- H-1 / H-2 not re-counted tonight (no change in the code paths). Nothing else broken.

Educational only — not financial advice.
