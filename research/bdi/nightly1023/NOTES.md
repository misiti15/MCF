# Nightly learning loop, 2026-10-23 (Friday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **4 configurations were replayed tonight**
(ST-P: none / latch 1.5 / 2 / 3R on Primary's live trades). No backtest, no locked block, no holdout. No config, setup or
exit was changed. About 40 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency,
$-risk quartile per account), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is "R(j)".

**Context effective today:** ST-A (per-setup −2R stop OFF in Testing 1/2 and Gen; Graveyard keeps it, latched: LL-LATCH);
D1 (CWT13-vwapstretch-z05-short T2 → Graveyard); L3-1 (L3-gap-slope-fromopen-FD Primary → Testing 1); OPS-POLL fix live.

**Scripts** = nightly1022's with the date set to 10-23 (`latch.py` dropped: the latch is live now), plus three new ones.
Run each as `python <script> <scratch>`: `fetch.py`, `build.py` → `trades.csv`, `close.py <scratch> <repo>` → `close_out.txt`,
`polls.py <scratch> <repo>` → `polls_out.txt` (new: 1b coverage, reuses `research/ops/pollspeed1022_missed.py`),
`autopsy.py`, `giveback.py`, `tables.py > tables_out.md`, `caps.py`, `combined.py`, `rearm.py`,
`stp.py` → `stp_out.txt` (new: ST-P replay), `riskq.py > riskq_out.txt` (new: $-risk quartiles).

**Market: Nasdaq up, SPY flat.** SPY 0.00% (high +0.47% 11:27, low −0.16% 10:27); QQQ +0.31% (high +1.01% 10:53, low −0.15%
09:37); IWM +0.32%.

## Failures first

1. **Nothing broke.** All 5 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages;
   journal trades = submitted signals = EOD report rows = `status.today.trades` in every account (32 / 131 / 147 / 274 / 51);
   EOD report + scorecard pushed 19:57 UTC (scorecard as of 15:57 ET). Not verifiable here: open orders at the broker and the
   Actions job logs (journal = report = status is the proxy for "final state push succeeded").
2. **5 broker bracket rejects** (H-1 / HK-1, known): "take_profit.limit_price must be >= / <= base_price ± 0.01" — price
   already through the target at submit. Testing 2 1 (CWT14-failbrk-pdl-p10-long, S), Graveyard 4 (CWT14 orl-p10 / pdh-p05
   lowvol: WMT, EFG ×2, ITB). Matches backlog `nightly-1013-tight-target-progress-skip`; no new item.
3. **Graveyard in-poll overshoot again** (LL-OPEN, R2 answered "no new stop"): CWT14-failbrk-orl-p05-long and -lowvol-long
   tripped in the 10:15 poll with 21 / 22 lots already open; RW2-exhaustion-noon-adv150-short-FD tripped at 11:30 with 13 open
   (→ −5.56R). The latch held: no entry after the trip poll in any Graveyard setup (`rearm_out.txt` lists 1 same-poll entry each).
4. **Poll coverage improved but T2 / Gen / Graveyard still ~85% of Primary's polls** (below).

## 0. Session close and poll coverage (`close_out.txt`, `polls_out.txt`)

| account | polls (log) | vs 10-22 | % of Primary | longest gap | symbol decisions missed | 10-22 |
|---|---|---|---|---|---|---|
| Primary | 382 | 379 | 100% | 4.1 min (10:44) | 1,615 (0.7%) | 1,775 |
| Testing 1 | 383 | 351 | 100% | 1.8 min | 464 (0.2%) | 11,784 |
| Testing 2 | **321** | **157** | 84% | 2.4 min (was 17.5) | 19,089 (8.1%) | 91,042 (36%) |
| Gen | **330** | **126** | 86% | 2.5 min (was 32.6) | 16,431 (7.0%) | 119,089 (47%) |
| Graveyard | 331 | — | 87% | 2.3 min | 16,026 (6.8%) | — |

- **OPS-POLL worked:** Testing 2 and Gen poll 2.0× / 2.6× as often as on 10-22, no gap over 2.5 min, and no decision bar
  missed for the "full" symbols (10-22: 24 / 61 bar times). Residual: ~118 polls over 70 s (vs 63 in Primary, the 5-min-bar
  polls), so T2 / Gen / Graveyard sit at 84–87% of Primary's count and still skip ~7–8% of symbol decisions (late symbols).
  Under the ~90% flag but no gap > 5 min; FYI only, keep OPS-POLL open one more session.
- **Skips:** no price-crosscheck, no "missed: triggered" skips in any account; Testing 1/2 and Gen had **0 "setup daily loss
  limit" skips** (ST-A off, as intended); Graveyard 186 (latched).
- **Moves traded in their new accounts only:** CWT13-vwapstretch-z05-short Graveyard only (12 trades, +$8.40);
  L3-gap-slope-fromopen-FD Testing 1 only (4 trades +$46.16; 16 of 33 signals "not shortable/ETB" — HK-2);
  CWT14-failbrk-pdh-p10-short Graveyard only (18, −$60.19).
- **OBS-1023:** ST7Q (Testing 1) 0 signals — its parent ST7-FD also 0 (QQQ above VWAP most of the day); NS3V1 (Testing 2) 0
  signals — it is morning-only and NS3-FD fired only after 13:55 (SOXS), so the NS3-T2 twin group was not exercised yet.

## 1. Headline per account (real trades)

| account | trades | win% | avgR (costs) | **P/L after costs** | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|
| Primary | 32 | 56% | −0.064 | **−$92.06** | 7 / 16 / 9 | never positive; trough −$105 (10:39) → −$92 |
| Testing 1 | 131 | 62% | +0.041 | **+$180.20** | 30 / 68 / 31 | +$190 (14:41) → +$180 |
| Testing 2 | 147 | 72% | +0.124 | **+$156.53** | 28 / 100 / 17 | +$230 (14:51) → +$157 |
| Graveyard | 274 | 57% | −0.090 | **−$651.23** | 86 / 128 / 60 | never positive; trough −$728 (14:47) |
| Gen | 51 | 45% | +0.113 | **+$889.88** | 14 / 1 / 36 | +$933 (15:37) → +$890 |

**Total after costs: +$483.32.** The mirror of 10-22: long books made money (Primary +$60.59, T1 +$92, Gen GEN-261020-07
hold-long +$612), Primary's short book lost (−$152.65) into QQQ's +1% morning.

### 1a. Intraday peak vs close (`giveback_out.txt`)
- **Primary −$92:** 10:05–10:15 shorts into the Nasdaq rally — FCEL (MF4-h40-FD, −$80.50) and FRVO (MF1, −$47.38) were the two
  largest-$-risk trades of the day ($77 and $38 vs median $13) and together lost more than the day. Feeds the new idea below.
- **Testing 2 gave back $73:** 7 open winners at the 14:51 peak flattened at 15:55 for −$63 (late-flatten pattern, known).
- **Graveyard −$651:** RW2-exhaustion-noon-adv150-short-FD −$247 (2nd worst day running), CWT14-orl-p05-long −$128,
  CWT14-pdh-p10-lowvol-short −$110, heat_fade_short −$108.

## 2. Winner/loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 635 trades)

| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | time to MFE winners / losers | latency median / p90 |
|---|---|---|---|---|---|
| Primary | 5 of 14, −$81 | 5 | 0.53 / 0.24 | 18.5 / 20 min | 1.5 / 3.5 s |
| Testing 1 | 16 of 50, −$131 | 10 | 0.61 / 0.21 | 18 / 11.5 min | 1.4 / 3.6 s |
| Testing 2 | 17 of 41, −$136 | 4 | 0.53 / 0.23 | 19 / 5 min | 1.5 / 3.0 s |
| Graveyard | 45 of 118, −$774 | 17 | 0.60 / 0.33 | 39.5 / 8 min | 1.3 / 3.3 s |
| Gen | 6 of 28, −$470 | 8 | 1.62 / 0.22 (give-back 0.37R) | 187 / 16 min | 1.3 / 3.1 s |

Latency had no edge (Primary fast / mid / slow terciles +0.04 / −0.29 / +0.04R). Patterns tied to existing items:
- **Primary.** Failed Prior-Day-Low Break Long (0.1 ATR, low volume) (CWT14-failbrk-pdl-p10-lowvol-long) 14 trades 86% win
  +$60.59 on the up day (10-22: −$195 on the down day) — the index-direction dependence of `nightly-1012-cwt14-long-index-confirm`
  (failed as a gate). Morning flow-sell shorts MF4-h40-FD (5, −$89.61), MF1 (1, −$47.38), MF2-FD (2, −$19.27) stopped into the
  QQQ rally — `bdi1015-short-index-up-veto` / `nightly-1019-index-chase-veto` (both failed as gates). BKH shorted by 3 setups
  11:50–11:55 (−$35.52; twin held does not span different setups — `nightly-1016-primary-one-lot-per-symbol`).
- **Testing 1.** CWT14-failbrk-pdl-p05-long 73 trades +$75.38; L3-fromopen-FD 4 trades +$46.16 (first T1 day);
  CWT05-flush-m05-v3-long 7 of 7. 11:40–11:45 polls 0 of 10 (−$57) as QQQ pulled back from its 10:53 high.
- **Testing 2.** Coil Under the High (4 bars) (CWT12-coil-k4-long) 31 trades 87% +$89.27; Failed Prior-Day-Low Break Long
  (CWT14-failbrk-pdl-p10-long) 31, 84%, +$72.45. NS3-FD 2 SOXS shorts −$37.88.
- **Graveyard.** see 1a; 45 never-worked losers.
- **Gen.** GEN-261020-07 (RSI-slope AM hold-long) 13 trades +$611.78; GEN-261021-06 (ORB-fail-up MID hold-long) 11 trades, 18%
  win, −$302.48 although its winners' MFE was 1.65R — the hold-exit give-back of `nightly-1020-gen-hold-mfe-giveback`.
  Gen's median risk is $75/trade (by design), so its $ swings dwarf the other accounts.

**ST-A, first day:** the two testing setups that would have hit −2R under the old rule kept trading and made money after the
would-be trip: Testing 1 CWT14-failbrk-pdl-p05-long (36 entries, +5.23R), Testing 2 CWT14-failbrk-pdl-p05-lowvol-long (34,
+3.17R) — +8.40R together. One day; FYI.

### New pattern → backlog (`riskq_out.txt`)

**$ risk scales with stop % of price, and the widest-stop quartile is the worst in every account.** Sizing is
min(0.25% equity / stop, slot ~$1,930) and the slot nearly always binds, so $ risk = slot × stop %.

| account | q1 (tight) avgR | q2 | q3 | **q4 (wide) avgR / $** | account total $ | median stop % in q4 |
|---|---|---|---|---|---|---|
| Primary (624) | +0.032 | +0.088 | −0.046 | **−0.206 / −$1,149** | −$1,113 | 2.1% |
| Testing 1 (2,661) | −0.213 | −0.080 | −0.050 | **−0.110 / −$1,604** | −$2,815 | 2.3% |
| Testing 2 (3,109) | −0.166 | −0.103 | −0.072 | **−0.187 / −$2,596** | −$3,789 | 1.7% |

→ backlog **`nightly-1023-wide-stop-pct-risk`** (risk, idea, 0 configurations): test skip / down-size of wide-stop-% entries
on the 2-year backtest. The tight-stop quartile in T1/T2 is also poor (cost drag) — existing `gb-1019-noise-floor-stop`.

**Step 4 swarm: not launched.** 1 new hypothesis (< 3) and no setup is near a gate (best: NS4-pm-vwap-reclaim-oversold-short-FD
17 live trades, t_day 2.06; backtest of its base −0.080R).

## 3. Live-funds hold: Primary positive-day streak

| | 10-12 | 10-13 | 10-14 | 10-15 | 10-16 | 10-19 | 10-20 | 10-21 | 10-22 | 10-23 |
|---|---|---|---|---|---|---|---|---|---|---|
| after costs | +115.77 | −101.67 | +60.35 | −926.53 | −14.41 | −63.92 | −46.13 | −626.57 | +1,369.10 | **−92.06** |

- **Today: negative. Consecutive positive Primary sessions: 0** (was 1). 3 of 14 sessions positive since 10-06.
- Since start: 624 trades, **−$1,113.42 after costs** (−20.63R). The hold stays.

## 4. Promotion / demotion suggestions (`combined_out.txt`; owner decides each)

Not re-suggested: N3 (pending; NS5-FD now 30 trades −0.47R, RW6G1-FD 19 −0.26R — not materially changed).

| setup | trades | sessions | win / BE win | avgR | t_day | last-4 R (n) | backtest | suggestion |
|---|---|---|---|---|---|---|---|---|
| Early Sellers Above VWAP (MF1-945-flowsell-vwapup), Primary | 25 | 10 | 32% / 35% | −0.190 | −0.80 | −0.542 (9) | −0.050 | **MF1-D: → Testing 1** (P4 on 10-19 was "not yet" at +0.13R / 16 trades) |
| Gap-Down VWAP Loss Short (5% gap) (CWT09-gapdn-vwaploss-g5-short), Testing 2 | 33 | 6 | 15% / 40% | −0.699 | −1.69 | −0.318 (4) | −0.031 | **D2: → Graveyard** |
| Gap-Down Capitulation Buy (near-miss) (NM-AR-AM-gapdown-capitulation-long), T2 | 25 | 2 | 28% / 55% | −0.534 | — | — | — | observation, 2 sessions: wait |

Primary keepers: RW3-FD 78 trades +0.443R (t_day 1.42), RW5-FD 85 +0.398R (1.68), MF2-FD 51 +0.743R (1.25), MF4-h40-FD
56 +0.157R (1.46). Base MF2-open-rsimidhi-flowsell (Primary) 4 trades, 0 wins, −1.21R — too few to judge.

## 6a. On deck
No open "[MCF ON-DECK]" / "[MCF DEMOTE-WATCH]" issues in misiti15/MCF (0 open issues).

## 6b. Watch: CWT14-failbrk-pdl-p10-lowvol-long (Primary since 2026-10-21)
Primary only: 38 trades in 3 sessions, 74% win vs 69% needed, **+0.034R**/trade but **−$101.18** (10-21 +3.09R, 10-22 −5.26R,
10-23 +3.46R; the $ loss comes from the wide-stop losers, see the new idea); backtest −0.095R. First full review 10-27.

## 6c. ST-P (backlog `st-a-1022-primary-setup-stop`), live part (`stp_out.txt`, 4 configurations)

Primary's live trades (no per-setup stop live, so nothing was blocked and the live trades are the full candidate set; slot
effects ignored), hypothetical per-setup stop that latches for the day:

| rule | trades | net R | $ | vs none | days better / worse | t_day | 10-22 (best day) vs none |
|---|---|---|---|---|---|---|---|
| none | 624 | −20.63 | −1,113 | — | — | — | — |
| latch 1.5R | 494 | −2.72 | −554 | +17.92 | 5 / 4 | 0.76 | +0.82 |
| latch 2R | 498 | −1.27 | −537 | +19.37 | 5 / 4 | 0.82 | +1.69 |
| latch 3R | 526 | −10.62 | −880 | +10.03 | 5 / 4 | 0.75 | +1.69 |

14 sessions (10-06..10-23); today no setup reached −1.5R (all rules −2.05R). Most of the gain is one day (10-15: +19.2R at
1.5/2R); no rule cost the best day anything. Not significant (t < 1). **No DECISION** until ≥ 10 sessions here and the 2-year
joint backtest are done (the backtest is not started).

LL-1.5 is retired (superseded by ST-A): closed in OPEN_ITEMS.md.

## Housekeeping
- H-1 / HK-1 bracket rejects: 5 today (above). HK-2 not-shortable noise: 75 skips across accounts (L3-fromopen-FD 16 of 33).

Educational only — not financial advice.
