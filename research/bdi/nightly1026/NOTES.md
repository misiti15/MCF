# Nightly learning loop, 2026-10-26 (Monday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one (shortened) session plus the
since-start live record. They describe what happened and are not evidence that anything works. **4 configurations were
replayed tonight** (ST-P: none / latch 1.5 / 2 / 3R on Primary's live trades). No backtest, no locked block, no holdout.
No config, setup or exit was changed. About 45 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin,
cluster, latency, $-risk quartile per account, coil burst history, CWT13-z05-long vs QQQ slope / distance from high),
so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is "R(j)".

**Known outage (not a new fault):** GitHub fired no scheduled trade.yml run this morning; run #140 was started by hand at
10:30 ET and the four day-trading accounts traded from 10:38-10:40 ET. The Gen account crashed at start (numba import in a
GEN-POD1022 module) until run #143 at 12:02 ET (PR #114; setup-load guard PR #116). Coverage below counts from each
account's real start. Primary's missed 09:50-10:39 window is replayed in research/ops/missed1026.md (−$26 / −1.5R cost
model, not part of the live record).

**Moves effective today:** CWT13-vwapstretch-z05-long and ST7-rsi50dn-long-pm-t1s1-FD promoted to Primary (moves);
MF1-945-flowsell-vwapup Primary → Testing 1; CWT09-gapdn-vwaploss-g5-short Testing 2 → Graveyard; Gen caps 200 / 48.

**Scripts** = nightly1023's with the date set to 10-26; `combined.py` now also prints `exbest` (avg R after costs
without the single best session) and `best_share` (owner 2026-10-25 one-big-day rule). Run as in nightly1023
(`fetch.py`, `build.py`, `close.py <scratch> <repo>`, `polls.py <scratch> <repo>`, `autopsy.py`, `giveback.py`,
`tables.py`, `caps.py`, `combined.py`, `rearm.py`, `stp.py`, `riskq.py`).

**Market: up day, high at 11:02 then a slow fade.** SPY +0.40% (high +0.72% 11:02); QQQ +0.71% (high +1.16% 11:02);
IWM +0.29% (high +0.94% 11:23).

## Failures first

1. **Nothing broke after the start.** All 5 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial lots,
   no data outages; "flatten complete: no MCF positions open" in every job log; journal trades = submitted signals =
   EOD report rows = `status.today.trades` = job-log "Trades" line in every account (22 / 136 / 136 / 193 / 24);
   EOD report + scorecard pushed 19:56-19:58 UTC. Not verifiable here: the broker's own open-order list (the job logs
   show only "order pending cancel" on bracket legs at the flatten, then "no MCF positions open").
2. **Start-of-day outage** (above). 4 "missed: triggered at 09:50-10:09" skips in Testing 1 (orb20_a, first poll 10:39)
   are a consequence of the late start, not a new fault.
3. **Testing 2 polls still 84% of the others** (266 vs 316 over the same 10:39-15:54 window; 2nd session in a row):
   98 poll gaps > 70 s vs 49 in Primary, 6.8% of symbol decisions skipped (Primary 0.1%). No gap > 5 min, no decision
   bar missed for a "full" symbol. Graveyard reached 100% today (87% on 10-23). Housekeeping, OPS-POLL stays open.
4. **No broker rejects, no price-crosscheck skips.**

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`)

| account | start | polls | expected (own window) | longest gap | symbol decisions skipped |
|---|---|---|---|---|---|
| Primary | 10:39:41 | 316 | 100% | 1.5 min | 160 (0.1%) |
| Testing 1 | 10:39:14 | 316 | 100% | 1.5 min | 109 |
| Testing 2 | 10:39:58 | **266** | **84%** | 2.1 min | 15,641 (6.8%) |
| Graveyard | 10:38:39 | 316 | 100% | 1.6 min | 539 |
| Gen | 12:02:24 | 233 | ~100% (233 min) | 1.7 min | 109 |

Moved setups traded only in their new accounts: CWT13-z05-long Primary only (11 trades, −$59.17); CWT09-vwaploss-g5-short
Graveyard only (1, −$31.59); ST7-FD 0 signals in Primary; MF1 base 0 signals in Testing 1. GEN-POD1022-01..03: 0 signals
(Gen started 12:02). ST7Q / NS3V1 still 0 signals (OBS-1023).

## 1. Headline per account (real trades)

| account | trades | win% | avgR (costs) | **P/L after costs** | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|
| Primary | 22 | 50% | −0.153 | **+$33.67** | 9 / 10 / 3 | +$61 (11:30) → trough −$39 (14:40) → +$34 |
| Testing 1 | 136 | 58% | +0.073 | **+$503.93** | 39 / 58 / 39 | trough −$188 (11:39) → +$553 (15:54) |
| Testing 2 | 136 | 49% | −0.213 | **−$40.45** | 58 / 58 / 20 | +$12 (10:50) → −$220 (11:39) |
| Graveyard | 193 | 52% | −0.094 | **−$404.86** | 66 / 79 / 48 | +$36 (10:50) → −$1,191 (13:21) |
| Gen | 24 | 42% | −0.061 | **−$64.43** | 9 / 1 / 14 | +$229 (13:58) → −$64 |

Total after costs: +$27.86. Shorts made money in the fade after 11:02 (Primary +$72.53, Testing 1 +$589, Testing 2 +$91);
longs lost in every account (Primary −$38.86, T1 −$85, T2 −$131, Gen −$108).

**Primary live-funds hold:** +$33.67 → positive-day streak **1** (10-23 was −$92.06). Since Day 1 (10-23): 1 of 2
sessions positive, −$58.39. Since start: 4 of 15 positive, −$1,079.75. With the replayed missed window (−$26 cost
model) the day would still be about +$8. The hold stays.

### 1a. Intraday peak vs close (`giveback_out.txt`)
- **Primary:** +$61 at 11:30 (MF2-open-rsimidhi-FD +$86.59 on 3 trades, CWT14 pdl-p10-lowvol early winners) →
  −$39 at 14:40: CWT13-vwapstretch-z05-long (first Primary day) bought 11 stretched-below-VWAP dips 11:45-14:00 while
  QQQ faded from its high: 5 stops, 4 never reached +0.2R (−$59.17).
- **Testing 1** made its money late (shorts: L3-gap-slope-fromopen-FD +$263.63, exhaustion_short 16 of 17 winners
  +$208.74); peak at 15:54, no give-back.
- **Testing 2 −$220 at 11:39:** CWT12-coil-k4-long took **24 entries in the 11:25 poll** (12% win, −21.1R) and 10 at
  11:30, right after the index high; plus a Latin-America gap-down basket (below). L3-gap-slope-rsi5hi-FD 17 of 18
  winners (+$146.94) pulled it back.
- **Graveyard:** RW2-exhaustion-noon-adv150-short-FD shorted 21 high-beta names at 10:50-11:00 as QQQ ran to its high
  (−$394.22 for the day; tripped −2R at 11:30 with 24 lots open, latched); CWT09-g5-lowerhalf −$184.63 (LatAm basket).
- **Gen gave back $294:** GEN-261020-05 (lunch long, hold with a 1R trail once +1R) had +$177 open at 13:58; most lots
  never reached +1R, so the trail never armed and 12 lots rode the 14:00-15:00 fade to the 15:55 flatten (−$287 from
  peak). Same mechanism as the failed late profit lock (sat1024-late-profit-lock: locks hurt on two years) — no new item.

## 2. Winner / loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 511 trades)

- **Losers are "never worked", not "gave back":** losers' MFE 0.10-0.36R in every account; 142 of 243 losers never
  reached +0.2R (Primary 7 / T1 23 / T2 49 / GY 57 / Gen 6); only 36 losers had been ≥ +0.5R (T1 20, mostly L3-fromopen-FD
  11 — its winners still average +1.09R MFE). Winners reach MFE late (median 18-147 min); losers peak early (median 2-32 min).
- **Clusters = the day's losses.** Same-setup same-poll clusters > 9: T2 34 trades −0.80R each (coil-k4); GY clusters
  5-9 −0.32R, > 9 −0.21R (RW2). Single entries were the best bucket in T2 (+0.07R) and GY (−0.05R).
- **Coil burst history** (all sessions): coil-k4 bursts ≥ 10 per poll on 3 days, all negative (10-12 −1.5R, 10-15 −1.0R,
  10-26 −27.0R; 55 trades, 33% win, −0.54R) vs −0.05 / −0.03R for clusters ≤ 5 → backlog `nightly-1026-coil-breadth-burst-skip`.
- **LatAm basket:** all 10 Testing 2 and 8 of 9 Graveyard CWT09-family trades were Latin-America names gapping on one
  macro event (ARCO, EWZ, ILF, ITUB, PBR, PAX, UGP, MELI, TIMB); the 11:20 bounce-rejection shorts ITUB / PBR / PAX / UGP
  fired together in both accounts and lost together (T2 −$95, GY −$189) → backlog `nightly-1026-country-gap-basket-cap`.
- **Checked, no pattern:** CWT13-z05-long R vs QQQ's 30-min slope at entry (falling −0.014R vs flat/rising +0.013R, 64
  trades since start) and vs QQQ's distance from its day high (no monotone split). No item.
- **Latency:** Testing 2's fastest fills were worst (−0.31R vs −0.04R slowest) — the burst entries; not a latency effect.
- **Twins:** T2 9 twin entries −0.43R (IREN / NBIS doubled by NM-RWR4 + NM-RWN4); GY twins −0.07R vs −0.10R non-twin.
- **HTB skips (HK-2):** Testing 1 skipped 92 "not shortable/ETB" signals, 82 of them L3-gap-slope-fromopen-FD refiring
  on leveraged single-stock ETFs (CWVX, CRWG, NCLD, NBIL, NBIG, NEBX, FLBR); the what-if "+64.8R" cannot be traded
  (no borrow). Housekeeping noise item HK-2 stays queued.
- **$-risk quartiles** (`riskq_out.txt`): Primary's top quartile is still the whole loss (−$1,012 of −$1,080); the
  two-year test of this already failed (nightly-1023-wide-stop-pct-risk). No new item.

## 3. Backlog (2 new, status idea)
- `nightly-1026-coil-breadth-burst-skip` (risk; parent nightly-1015-short-breadth-cluster-skip)
- `nightly-1026-country-gap-basket-cap` (risk)
No swarm tonight: 2 new ideas (< 3), no setup near a gate, and both need CWT12 / CWT09 in the 2-year cache (BDI plan).

## 4. Suggestions (`combined_out.txt`; all accounts merged, costs in)

- **DECISION D3** — move Coil Under the High (6 bars) (CWT12-coil-k6-long, Testing 1) and optionally Coil Under the
  High (4 bars) (CWT12-coil-k4-long, Testing 2) to the Graveyard:
  - k6: 90 trades / 9 sessions, 31% win vs 38% needed, −0.273R, w/o best day −0.414R (total negative, no best-day
    share), t_day −1.57, last 4 sessions 48 trades −0.369R, −$114.61; 2-year backtest −0.070R; top5 tune 10-21 0 pass.
  - k4: 276 / 11, 62% vs 69%, −0.122R, w/o best day −0.167R, t_day −0.95, last 4 103 trades −0.188R, −$191.43;
    backtest −0.075R. Today −29.8R, mostly the 11:25 burst.
- **Nearest promotion, not ready:** NS4-pm-vwap-reclaim-oversold-short-FD (Testing 1; base = Afternoon VWAP Reclaim
  Fade, in Primary): 17 trades / 6 sessions, 71% vs 43%, +0.52R, w/o best day +0.351R, best day 52% (**1 day**), t 2.06,
  base backtest −0.080R. L3-gap-slope-rsi5hi-FD (Testing 2): 56 / 8, +0.196R but +0.078R w/o best day, today = 73% of
  its R (**1 day**). L3-gap-slope-fromopen-FD (Testing 1, demoted 10-22): +0.155R, −0.026R w/o best day.
- **Primary first-day notes:** CWT13-z05-long 11 trades −0.403R, −$59.17 (review 11-06, PROMO-Z05L); ST7-FD 0 signals.
  Early Sellers, Mid-High RSI (MF2-open-rsimidhi-flowsell, Primary) 4 trades all losers −$52.37 over 4 sessions
  (last 10-14) — too few trades to suggest anything.
- **Watch PROMO-PDL** (CWT14-failbrk-pdl-p10-lowvol-long, Primary only since 10-21): 44 trades / 4 sessions, 70.5% win
  vs 67.6% needed, +0.014R, −$80.87, w/o best day (10-23) −0.095R (total R +0.61, best day 3.46R = 5.7x total),
  t_day 0.07; backtest −0.095R; today 6 trades −0.68R. Full review 10-27.
- **On deck / demotion watch:** no open `[MCF ON-DECK]` / `[MCF DEMOTE-WATCH]` issues by misiti15.

## 5. ST-P live replay (`stp_out.txt`; 4 configs, counted)

Primary 15 sessions (10-06..10-26), latched per-setup stop vs none: **1.5R +19.65R** (6 days better / 4 worse, t 0.84),
**2R +21.10R** (6/4, t 0.90), 3R +10.03R (5/4, t 0.75); best day (10-22) give-up 0.8-1.7R. Today 2R / 1.5R +1.73R (−3.37R → −1.64R; 3R no change). The 2-year backtest is done (saturday1024) and the
decision was raised 10-24; owner 10-25: "revisit later". Numbers did not change materially (+19.4R → +21.1R), so no new
DECISION; ST-P stays open.

Educational only — not financial advice.
