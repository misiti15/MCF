# LIVE-READY: cost realism and Primary live-funds readiness (2026-11-11)

Research and audit only. It was written during market hours, so no config, workflow or order was changed. Every fix
below is a proposal, to be applied only after the close and only with the owner's yes (reply codes at the end).
Educational only — not financial advice.

## Plain English

**1. Not every R figure includes costs today.** Trades are booked with two numbers. `r_multiple` is the raw broker
paper R. `pnl_adj` is the broker P/L minus a $0.02/share stop-exit allowance. The **leaderboard / scorecard (dashboard
Avg R, win rate, t, total R, "Avg R w/o best day", last-4), the dashboard trade lists, the EOD email, the live status
page, the intraday curve and the brief all use raw `r_multiple`**. The daily post's "last session" R, Team, FASTDEC,
the nightly autopsy and the nightly **System trend** use `pnl_adj`. I checked the System trend: its "All" column
matches the `pnl_adj` R exactly (for example 11-10: 1,294 trades, −90.6R; raw would be −76.0R), so it does include the
current costs. So the same setup row mixes a raw Avg R with a cost-in last-session R. The raw figure flatters by
**+0.023R per trade on average** (Primary +0.024R). The **−20R account halt and the −2R per-setup latch also add up raw
R**. On cost-in R, Primary would have halted on 4 days instead of 3, and latched 59 setup-days instead of 54 (of 192).

**2. Paper is not optimistic where we assumed, and it is optimistic where we did not.** Alpaca paper fills market and
stop orders *at the quote*. On the four sessions where we hold 1-minute SIP bars (11-05, 11-06, 11-09, 11-10; 4,867
trades), 27% of entry fills and 28% of stop fills were *worse than every print in that minute*. Fewer than 0.5% were
better. So market and stop fills are, if anything, conservative. Measured on all 7,087 stop exits at the original stop,
the paper stop fill was on average **4.6 bps (0.054R) beyond the stop price, already inside the P/L**. On top of that,
the $0.02 allowance is charged. The optimism sits in **limit (target) exits**. 44% of the 8,033 target fills got a
price *better than the limit* (mean +0.015R per target exit), which a resting live limit does not get. And 11% of
target fills on the bar days were **touch-only**: the minute never traded ≥ 1¢ through the target, so a live order
in the queue may not have filled.

**3. The flat $0.02 allowance is wrong in shape.** Stop slippage scales with price (about 4–6 bps at every price
level), not with share count. $0.02 is 18 bps on a sub-$20 name, which is too harsh, but only 0.5 bps on a $250+ name,
which is about 10× too lenient. Fast moves cost more: the quintile of stops where price ran furthest through the stop
inside the minute paid 13.1 bps (0.116R), against 3.9 bps (0.046R) for the rest.

**4. Fees are small but not zero, and borrow is ~0 intraday.** As of 2026-11-11: SEC Section 31 is $20.60 per $1M of
sale proceeds (effective 2026-04-04). FINRA TAF is $0.000195/share sold, capped at $9.79 per trade (effective
2026-01-01). The CAT pass-through is estimated at $0.00005/share per side (a conservative estimate, not a published
Alpaca figure). Together they cost about 0.0035R per trade. Short borrow fees are charged only on positions held at
the end of the day, and MCF flattens at 15:55, so borrow is ≈ $0. 44% of trades are shorts, ETB only.

**5. Partial fills and odd lots are a non-issue in the data.** 100% of entries filled their full order quantity. Only
0.6% of trades closed in more than one part (exit_parts). 91% of trades are under 100 shares (odd lots). Odd-lot
market and stop orders fill at or inside the NBBO, so no extra cost is modelled. A median entry is 0.2% of that
minute's volume (p99 6.4%), so market impact is negligible at today's size.

**6. The proposed cost model** (below) lowers avg R by **−0.038R per trade overall**: from −0.135R to −0.173R on all
19,148 live paper trades. Against the dashboard's raw figure the drop is **−0.061R**. Every setup gets worse, because
the model only adds costs. The median setup loses −0.036R, 90% lose between −0.020R and −0.056R, and 28 of 167
setup-account rows (≥ 20 trades) lose more than 0.05R. The worst hit are wide-price / tight-stop setups (MF1, GEN
ORB-fail shorts, heat_fade_short, intraday_momentum). Of the 38 setup-account rows that are positive on `pnl_adj`, 30
stay positive. The 8 that flip are all within ±0.03R of zero (list below). **Primary's current Team-6 keeps its
positive core:** RW3 +0.268R, RW5 +0.146R, ST7 +0.142R and NS5 +0.025R on Primary trades. L3-fromopen is −0.046R on
Primary but +0.200R on its 222 On Deck trades.

**7. Primary readiness gaps.** The most urgent is a dated bug: **half-day closes are not handled**. On Fri 2026-11-27
(13:00 ET close) and Thu 2026-12-24, the runner sees the market closed at 13:00 and exits **without flattening**. The
DAY stop and target legs then expire, and positions sit unprotected over the weekend. It must be fixed before 11-27.
Next come: no instant kill switch; no automatic broker-vs-journal position check (MTUM and SOXX were found by hand);
halts that count raw R and realized R only; market entries with no price collar or halt check; a flatten-failure path
that only records the failure; and a watchdog still in dry mode. The full ranked list is at the end.

## Data and method

- Source: `journal.db` of every data branch (`mcf-data`, `-testing`, `-testing2`, `-gen`, `-graveyard`, `-livelab`,
  `-explore1`). Testing D/E/F have no trades yet. Run kind `paper` (live), closed trades only: 19,148 trades from
  2026-10-06 to 2026-11-11 (11-11 is partial, as of ~12:30 ET). Universe/ADV/ATR come from `origin/mcf-data:universe.csv`
  (built 11-10).
- 1-minute SIP bars from scratch caches (Move Hunt day files) for 11-05/06/09/10. No Alpaca call was made. The
  NBBO-at-fill comparison is approximated with the 1-minute bar range of the fill minute plus the bid/ask the runner
  journals at signal time (`meta.bid/ask/spread_bps`). A tick-level NBBO comparison needs a quotes fetch, deferred
  to after 16:00 (LR15).
- Stop slippage is measured on exits with `exit_reason == stop` whose fill is within 0.25R of the original stop
  (7,087 of 7,233). The others had a moved stop (breakeven/trail).
- R definitions: `R_raw = r_multiple` (dashboard); `R_cur = pnl_adj / (|entry − stop| × shares)` (post/Team/nightly);
  `R_new` = (broker P/L − proposed costs) / risk.
- Scripts: `research/live_ready/{load,bars,model,build_csv}.py` (paths point at the scratch copies of the journals).

## Where R is reported, and with what costs

| Place | Code | R used | Costs in? |
|---|---|---|---|
| Leaderboard / scorecard (dashboard Avg R, win, t, total R, w/o best day, last 4) | `mcf/report/scorecard.py` → `reports/scorecard.json`; merged in `daily_post.leaderboard` | `r_multiple` | **No** |
| Daily post leaderboard "last session" R | `daily_post.journal_day` | `pnl_adj / risk` | Yes (current) |
| Dashboard trade lists | `mcf/dashboard/build.py::_pack` | `r_multiple` | **No** |
| EOD email per-setup avg R and ex-market adj R | `mcf/report/eod.py` | `r_multiple` | **No** |
| Live status avg R | `mcf/report/live_status.py` | `r_multiple` ($ also shows `pnl_adj`) | **No** (R) |
| Daily review | `mcf/report/daily_review.py` | `r_multiple` | **No** |
| Brief (`mcf/report/brief.py`) | exp per setup | `r_multiple` | **No** |
| Intraday curve | `mcf/report/intraday.py` | `r_multiple`; open marks with no costs | **No** |
| Trade charts | `mcf/report/trade_charts.py` | `r_multiple` | **No** |
| −20R halt / −2R setup latch | `runner.restore` L227-237, `runner.reconcile` L1336-1342 | `r_multiple` | **No** |
| Team shadow (actual Primary side) | `mcf/report/team.py` | `pnl_adj / risk` | Yes |
| Team shadow (simulated side) | replay `fills="costs"` | sim costs (1 bp + $0.01/side, +$0.02 stops) | Yes |
| FASTDEC | `research/fastdec/engine.py` | `pnl_adj / risk` | Yes |
| Nightly brief System trend, autopsy, cands | `research/bdi/nightly11xx/*` | `pnl_adj / risk` (`r_multiple` shown only as avgR_j) | Yes |
| Dollar P/L (post, milestones) | Alpaca equity change (`reconcile_pl`) | — | Broker $ only; the allowance and fees never enter $ (owner rule 11-05) |
| Backtests / 2-yr screens | `mcf/backtest/engine.py` | engine costs | Yes (backtest model) |

## Measured paper-vs-live gaps

**Entry fills vs signal price (`slip_bps`, all 19,148 trades):** mean +4.4 bps, median +3.6, p90 +25, p99 +68. That is
about the half-spread at signal (mean spread 9.3 bps). Paper already pays the quote.

| Price | n | slip mean bps | median | p90 | half-spread bps |
|---|---|---|---|---|---|
| < $20 | 2,707 | 4.6 | 4.7 | 33.1 | 5.3 |
| $20–50 | 4,311 | 4.0 | 2.6 | 24.8 | 3.8 |
| $50–100 | 4,618 | 3.8 | 3.2 | 21.6 | 3.9 |
| $100–250 | 4,470 | 5.3 | 4.2 | 25.1 | 5.4 |
| $250+ | 3,042 | 4.6 | 4.0 | 23.5 | 5.3 |

| ADV quartile (20d $) | n | slip mean bps | median | p90 | half-spread |
|---|---|---|---|---|---|
| Q1 (< $183M) | 4,753 | 4.7 | 4.0 | 26.5 | 5.3 |
| Q2 | 4,753 | 4.6 | 3.9 | 22.9 | 4.8 |
| Q3 | 4,754 | 4.5 | 3.5 | 23.8 | 4.5 |
| Q4 (> $932M) | 4,739 | 4.0 | 3.0 | 26.7 | 4.0 |

**Stop exits at the original stop (7,087):** the paper fill beyond the stop is already in the P/L. The current $0.02
allowance comes on top of it.

| Price | n | paper slip $/sh mean | p90 | bps mean | bps p90 | R mean | current $0.02 = bps | proposed = bps |
|---|---|---|---|---|---|---|---|---|
| < $20 | 947 | 0.004 | 0.014 | 3.6 | 13.0 | 0.027 | 18.3 | 18.3 |
| $20–50 | 1,593 | 0.012 | 0.033 | 3.8 | 10.1 | 0.044 | 6.4 | 6.4 |
| $50–100 | 1,757 | 0.032 | 0.082 | 4.4 | 10.7 | 0.057 | 2.8 | 4.0 |
| $100–250 | 1,627 | 0.093 | 0.237 | 5.8 | 13.9 | 0.069 | 1.3 | 4.0 |
| $250+ | 1,163 | 0.237 | 0.595 | 5.1 | 13.6 | 0.064 | 0.5 | 4.0 |

By account, the paper stop slip is the same everywhere (4.2–5.4 bps; Primary 4.3 bps, n 426). On the bar days, fast
stops (top quintile of run-through beyond the stop inside the minute) paid 13.1 bps / 0.116R; the rest paid 3.9 bps /
0.046R. 48% of stop fills were already more than $0.02 beyond the stop.

**Fill vs the 1-minute bar (4 bar days):**

| Check | Result |
|---|---|
| Entry fill worse than every print of its minute | 27.0% |
| Entry fill better than every print (impossible-favourable) | 0.45% |
| Stop fill worse than the minute's worst print | 28.1% |
| Stop fill better than the minute's best print | 0.1% |
| Target exits where the bar traded ≥ 1¢ through the target | 88.9% |
| Target exits that were **touch-only** (< 1¢ through) | **11.1%** |
| Target fills better than the limit (all 8,033 target exits) | **43.9%**, mean +$0.026/sh, **+0.015R** |
| Flatten fills outside the minute's range | 7.8% |
| Entry size / entry-minute volume | median 0.21%, p95 2.2%, p99 6.4% |

**Fees (sources, read 2026-11-11):**
- SEC Section 31: $20.60 per $1M of covered sales, effective 2026-04-04 (it was $0.00 before that).
  [SEC fee rate advisory 2026-2](https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2),
  [Release 34-104909](https://www.sec.gov/files/rules/other/2026/34-104909.pdf).
- FINRA TAF (covered equity sales): $0.000195/share, max $9.79/trade, from 2026-01-01.
  [FINRA Section 1 fee schedule](https://www.finra.org/rules-guidance/rulebooks/corporate-organization/section-1-member-regulatory-fees),
  [SR-FINRA-2024-019 fee adjustment schedule](https://www.finra.org/rules-guidance/rule-filings/sr-finra-2024-019/fee-adjustment-schedule).
- CAT fee pass-through: **estimate** $0.00005/share per side (not verified against Alpaca's current schedule. Check
  the first real-money confirmation).
- Commission: $0 (Alpaca equities).
- Borrow: Alpaca charges stock borrow on short positions held at the end of the day. MCF is flat by 15:55, so ≈ $0.
  Only ETB names are shorted (`shorts.require_easy_to_borrow`).

## Proposed cost model (conservative, live-like)

All costs are applied on top of the broker paper P/L, in R only (dollars stay Alpaca, per the owner rule of 11-05).

| Component | Rule | Why | Avg R cost |
|---|---|---|---|
| Stop exits | extra **max($0.02, 4 bps × price)** per share (replaces the flat $0.02) | Paper stop slip is a constant ~4.6 bps across prices, and the fast quintile pays 3× more. The 4-bps floor gives large-price names the same proportional cushion that $0.02 gives a $50 name | 0.032 |
| Target (limit) exits | fill **at the limit price**, with no improvement | A resting live limit does not get price improvement | 0.008 |
| Flatten / time-stop (market) | extra max($0.01, 1 bp) | Close-of-day impact and latency | 0.005 |
| Entry | extra 1 bp (latency/impact cushion) | Paper already pays the quote, so this is the softest component. Drop it if the owner wants "calibrated" rather than "conservative" | 0.013 |
| Fees | SEC $20.60/M on sell notional, TAF $0.000195/sh sold (cap $9.79), CAT est. $0.00005/sh/side | Regulatory | 0.0035 |
| Borrow | 0 (intraday) | Charged only on overnight shorts | 0 |
| *Sensitivity* (not in base) | half of the touch-only target fills (11.1% × 50%) do not fill; that trade takes its setup's average non-target outcome | Queue position on a touch | 0.035 more |

**Effect (all live paper trades, 2026-10-06..11-11):**

| Account | n | Dashboard raw | Current (pnl_adj) | Proposed | Proposed + touch sensitivity |
|---|---|---|---|---|---|
| Primary | 1,109 | −0.064 | −0.088 | −0.128 | −0.163 |
| On Deck (testing) | 3,872 | −0.100 | −0.119 | −0.157 | −0.187 |
| Testing A (testing2) | 5,032 | −0.119 | −0.143 | −0.182 | −0.225 |
| Setup Generator | 2,827 | −0.193 | −0.224 | −0.259 | −0.272 |
| Graveyard | 6,187 | −0.086 | −0.106 | −0.144 | −0.186 |
| Testing C (livelab) | 49 | +0.003 | −0.004 | −0.033 | −0.064 |
| Testing B (explore1) | 72 | −0.121 | −0.133 | −0.171 | −0.206 |
| **All** | 19,148 | **−0.112** | **−0.135** | **−0.173** | **−0.208** |

**Primary Team-6 setups (avg R; the full table is in `costs.csv`):**

| Setup | Account | n | Raw | Current | Proposed | Proposed w/o best day | + touch sens. |
|---|---|---|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD | Primary | 102 | +0.317 | +0.304 | +0.268 | +0.051 | +0.225 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | Primary | 122 | +0.192 | +0.186 | +0.146 | −0.010 | +0.114 |
| ST7-rsi50dn-long-pm-t1s1-FD | Primary | 22 | +0.203 | +0.173 | +0.142 | +0.024 | +0.095 |
| NS5-sma50-flush-oversold-long | Primary | 31 | +0.081 | +0.053 | +0.025 | −0.041 | −0.016 |
| L3-gap-slope-fromopen-FD | Primary | 63 | +0.009 | −0.020 | −0.046 | −0.194 | −0.074 |
| L3-gap-slope-fromopen-FD | On Deck | 222 | +0.244 | +0.224 | +0.200 | +0.091 | +0.165 |
| NM-ETF-late-dip-di-long | Testing A / C | 10 / 8 | +0.262 / +0.408 | same | +0.248 / +0.367 | +0.194 / +0.342 | +0.221 / +0.336 |

One-big-day check: RW5 (Primary) goes to −0.010R without its best session, and ST7 (Primary, n 22) to +0.024R. Both
records lean on one or two big days.

**By family (Δ = proposed − current; setup-account rows with ≥ 20 trades):**

| Family | n | Current | Proposed | Δ | rows | worst row Δ | median row Δ |
|---|---|---|---|---|---|---|---|
| MF1 | 150 | −0.305 | −0.422 | −0.117 | 3 | −0.143 | −0.086 |
| intraday_momentum | 52 | −0.352 | −0.427 | −0.075 | 1 | −0.076 | −0.076 |
| NS4 | 69 | −0.039 | −0.100 | −0.060 | 2 | −0.061 | −0.058 |
| MF2 | 150 | −0.003 | −0.059 | −0.056 | 2 | −0.064 | −0.062 |
| MF5 | 241 | −0.233 | −0.288 | −0.055 | 6 | −0.062 | −0.055 |
| MF3 | 305 | −0.238 | −0.289 | −0.051 | 5 | −0.068 | −0.050 |
| heat_fade_short | 1,070 | −0.164 | −0.209 | −0.046 | 5 | −0.082 | −0.042 |
| CWT13 | 526 | −0.141 | −0.184 | −0.043 | 5 | −0.066 | −0.045 |
| CWT12 | 1,006 | −0.083 | −0.124 | −0.041 | 5 | −0.067 | −0.057 |
| CWT14 | 7,142 | −0.117 | −0.157 | −0.040 | 26 | −0.055 | −0.039 |
| RW5 | 156 | +0.224 | +0.185 | −0.039 | 2 | −0.040 | −0.038 |
| RW3 | 141 | +0.283 | +0.247 | −0.036 | 2 | −0.036 | −0.035 |
| GEN | 2,890 | −0.224 | −0.260 | −0.035 | 42 | −0.150 | −0.032 |
| CWT09 | 296 | +0.009 | −0.024 | −0.034 | 4 | −0.053 | −0.031 |
| L3 | 459 | +0.124 | +0.100 | −0.025 | 6 | −0.031 | −0.025 |
| NM | 211 | −0.052 | −0.075 | −0.023 | 3 | −0.029 | −0.024 |
| NS5 | 100 | −0.179 | −0.205 | −0.026 | 2 | −0.028 | −0.025 |
| ST1 | 58 | −0.290 | −0.307 | −0.017 | 2 | −0.021 | −0.017 |

Improve / worsen count (owner remedy rule): 0 of 167 rows improve; 167 get worse. The median is −0.036R, the 10th–90th
percentile range is −0.056 to −0.020R, 28 rows lose more than 0.05R and 2 lose more than 0.10R (both MF1-945 /
GEN ORB-fail: high price, tight stops).

**Worst-hit setup-account rows (≥ 20 trades):** GEN-261027-09-ORBfailDn…-short (Gen, −0.150), MF1-945-flowsell-vwapup-FD
(Graveyard, −0.143), GEN-261022-09-Ret15m…-short (Gen, −0.089), MF1-945-flowsell-vwapup (Primary history, −0.086),
MF1-945-flowsell-vwapup-FD (On Deck, −0.084), heat_fade_short (On Deck, −0.082), intraday_momentum (On Deck, −0.076),
MF3-open-flowsell-rsi5hi (On Deck, −0.068).

**Flip from positive to ≤ 0 under the proposed model (8 of 38):** RW6-ns2-up3-short-FD (Graveyard +0.007 → −0.016),
NS4-pm-vwap-reclaim-oversold-short-FD (On Deck +0.042 → −0.019), orb20_a (On Deck +0.007 → −0.026),
NS4-pm-vwap-reclaim-oversold-short (Primary history +0.025 → −0.030), and four GEN setups (+0.011..+0.023 →
−0.006..−0.014).

**Rule-change context inside the window (research/ledger.jsonl):**
- 10-28: Primary position size ~$4k (slots 61 → 77). This changes dollars, not R.
- 10-29: Primary −2R per-setup latch (ST-P).
- 10-30: Testing 1/2 cost filter CF (`max_stop_cost_r 0.15`). After this date, Testing trades skip the
  highest-cost-per-R entries, so their cost per trade is lower than before.
- 11-04: Testing 2 top-500 pool (UNI1).
- 11-05: ROLL1 low-rep homes (Testing B/C).
- 11-11: Team-6 on Primary (frozen to 11-13).
- Many promotions / demotions (moves) between 10-22 and 11-11. A setup's rows by account in `costs.csv` keep those
  periods apart.

## Primary live-funds readiness: what Primary has today

| Control | Today | Status |
|---|---|---|
| −20R account halt | `risk.check` on **realized, raw** R; sticky; restored after a restart (`_restore_latches`, PR #152) | Present. Raw R; open lots ignored |
| −2R per-setup latch (Primary only) | Latched, restored from journal + signals | Present. Raw R |
| Slot / position caps | 77 slots = 77 max concurrent, 30 per setup, 3 lots/symbol, participation ≤ 10% of 5-bar avg volume | Present |
| Buying power | Sizing assumes 3.2× equity (~$306k of ~$321k paper BP); a broker reject is journaled | No pre-check vs `daytrading_buying_power` |
| 15:55 flatten | `flatten_mcf`: cancel by prefix, 3 close passes, `health.flatten_failed` | No retry or escalation after 3 passes; watchdog window ends 15:55, mode dry |
| Self-handover / restart | `handover.py` dispatches its successor; broker-side brackets stay; restore from broker + journal | Present |
| Max order size / notional | Only in sizing (`min(risk/ps, slot cap)`, `max_position_notional_pct` 10%) | No independent guard at submit |
| Price collar | Entries are **market** orders; pre-trade cross-check: ref vs mid ≤ 2%, quote age ≤ 300 s, spread ≤ 30 bps and ≤ 25% of stop | No collar; 300 s quote age is loose |
| Duplicate orders | Deterministic client ids per setup/symbol/bar; `entered`/`moments` sets; Alpaca rejects duplicate ids | Present |
| Rejected orders | Journaled `rejected`, not fatal | Present (none on Primary to date) |
| Stuck orders | No cancel of an unfilled entry (e.g. a halted name); pending grace 300 s for slot accounting only | Missing |
| Phantom / corporate action | No broker-qty vs journal-lot check. MTUM (11-05) and SOXX (T1X) found by hand; post corrections by hand | Missing |
| Halts / LULD / MWCB | Not detected. Stale-data escalation (pause 5 min, protect 15, flatten 30) covers a feed outage only | Partial |
| Holidays | Alpaca clock `is_open` / `next_open`; session guard checks the market day | Present |
| **Early-close days** | Runner exits at the 13:00 close **without flattening**; flatten is a fixed 15:55 | **Missing (dated: 11-27, 12-24)** |
| Data outage / stale data | `_check_data`, outage escalation, independent watchdog (dry) | Present (watchdog dry; no backup feed, deferred to real funds in DECISIONS) |
| Clock drift | Runner uses the broker clock | Present |
| Kill switch | None for intraday MCF (long-hold has a HALT file) | **Missing** |
| Paper/live switch | `AlpacaBroker(paper=True)` hard-coded; trade and data share `ALPACA_API_KEY` on Primary | Needs a guarded live switch + separate keys |
| Alerts | Owner rule: no emails; `_alert` is email only | Real funds need a push alert on halt / flatten failure / mismatch |
| PDT / margin / locate | Paper equity ~$95k (> $25k PDT floor); ETB-only shorts | See LR9 / LR14 |
| `lot_cap_ignore_residual_frac` | Marked "REVIEW BEFORE REAL FUNDS" in config | Open |

## Ranked gap list (reply codes)

Each fix is applied only after the close, with the owner's yes. Setup/exit-adjacent items follow the setup-freeze
rule. Where Primary is the target, the fix can be copied to all accounts once proven.

| Code | Severity | Gap | Proposed fix | Scope | Risk of the fix |
|---|---|---|---|---|---|
| **LR1** | Critical (dated) | **Half-day closes**: on 11-27 and 12-24 the runner breaks at the 13:00 close without flattening. DAY legs expire, so positions go unprotected over the weekend/holiday | Flatten time = min(config 15:55, Alpaca `clock.next_close` − 5 min). The watchdog, session guard and EOD chain read the calendar close, not 16:00/15:55. Add a drill test with a 13:00 close | All accounts | Low: only half days change. **Needed before Fri 11-27** |
| **LR2** | High | Dashboard / leaderboard / scorecard / EOD / brief / live status / intraday show **raw R**, mixed with cost-in R in the same row; raw flatters by +0.023R/trade. Promotions are judged on it | One helper `r_cost(trade)` (pnl_adj / risk, later the LR8 model) used by scorecard, dashboard, eod, brief, live_status, intraday, daily_review, trade_charts. Keep raw as a hidden column for audit | All accounts (reporting) | Low: display only. Every Avg R drops ~0.02-0.03R at once, so post a one-line note in the daily post |
| **LR3** | High | −20R halt and −2R latch add up **raw, realized-only** R. On cost-in R Primary would have halted on 1 more day and latched 5 more setup-days. Up to 77 open lots (~19R at risk) keep running after a halt | Latches on cost-in R. Account halt on realized + open marks (the MTM snapshot already exists) ≤ −20R. Option: "halt → flatten" for Primary | Primary (the Testing 120R backstop can follow) | Medium: fewer trades on bad days. Report what-if R for the halted window |
| **LR4** | High | **No instant kill switch.** Today the owner must cancel GitHub runs, and broker brackets stay working | `HALT` file on the state branch / repo variable `MCF_HALT` read every poll: `entries` = no new entries; `flatten` = cancel + flatten by prefix (`outage.flatten_prefix`). Plus a manual `kill.yml` (workflow_dispatch, account or all) that flattens directly without the runner. One-line owner instruction | All accounts | Low (only acts when set) |
| **LR5** | High | **No phantom / corporate-action detector** (MTUM fake 1:4 split 11-05, SOXX phantom in T1X) | Each status poll: broker qty per symbol vs Σ open-lot `left` qty for MCF symbols; also flag positions MCF never traded today. Mismatch → `health.position_mismatch`, block entries on that symbol, include in the :51 check. Auto-flatten only MCF-traded mismatches at 15:55 (others: report) | All accounts | Low (flag + block); medium if auto-flatten |
| **LR6** | High | **Market entries with no collar or halt check**; quote age allowed 300 s. A market order into a halted / LULD name fills at the reopen | Primary entries as **marketable limit** (ask + min(0.25 × risk, 20 bps) for buys, mirror for sells). Cancel an entry unfilled after 60 s (stuck-order cancel). `quote_crosscheck_max_age_s` 300 → 15 for Primary. Skip if the quote condition shows a halt | Primary first (execution change, so setup-freeze timing) | Medium: a few missed fills. Measure the fill rate for 5 sessions |
| **LR7** | High | **Flatten failure only recorded**: 3 passes, then `health.flatten_failed`; no retry or alert; watchdog dry and its window ends 15:55 | Retry every 20 s until 15:59, then an extended-hours limit close (already used after hours), a push alert, and the watchdog in `act` for Primary with its window extended to 16:05 (calendar close + 5) | Primary first | Low |
| **LR8** | Medium | **Cost allowance mis-shaped**: flat $0.02 stop (0.5 bps on $250+ names); paper target improvement; no fees | Adopt the proposed model in `pnl_adj` (stop max($0.02, 4 bps); targets at the limit; market exits max($0.01, 1 bp); entry 1 bp; SEC/TAF/CAT). Re-run the CF filter's `stop_cost_r` with the same formula | All accounts (R only; $ stay Alpaca) | Low: R −0.038/trade. A reporting change, so it gets a ledger entry |
| LR9 | Medium | Buying power / PDT / margin for a real account: DTBP = 4 × (equity − maintenance) at the prior close; exceeding it gives a DT margin call; PDT needs ≥ $25k equity; shorts need Reg-T 150% initial | Pre-trade check vs `get_account().daytrading_buying_power` minus open-order notional, keeping 10% headroom. Real-money slot cap ≤ 3.0×. Stop all entries if equity < $27k | Primary | Low |
| LR10 | Medium | No independent order-size guard at submit | `submit_bracket` refuses qty × px > `max_position_notional_pct` × equity or qty > 5,000 sh, and journals `rejected: guard` | All accounts | Low |
| LR11 | Medium | `paper=True` hard-coded; Primary trade + data share one key (rate limits) | One guarded `MCF_LIVE_FUNDS` switch (owner-only variable) → `paper=False` for Primary only; separate live trade keys; data on its own key | Primary | Low |
| LR12 | Medium | No push alert (email off by owner rule) | Push (or the Claude scheduled task) on: halt, flatten failure, position mismatch, outage flatten, kill switch | All accounts | Low |
| LR13 | Low | MWCB / LULD market-wide halts: stale-data escalation would try to flatten during a halt | Detect all-symbol staleness at the same minute + SPY move ≥ 7% → mark `mwcb`, hold (brackets stay), no flatten loop until the reopen | All accounts | Low |
| LR14 | Low | Shorts on real money: ETB = pre-located at Alpaca; a recall is possible; borrow fee only overnight | Keep ETB-only. Refresh the ETB flag at each job start (already a per-session cache). Never carry a short past 15:55 (LR1 covers half days) | Primary | Low |
| LR15 | Low | Tick-level paper-vs-NBBO check not done (bars only) | After 16:00: fetch SIP quotes around ~300 sampled Primary fills (entries, stops, targets) and repeat the tables | Research | None |
| LR16 | Low | `lot_cap_ignore_residual_frac 0.25` marked "REVIEW BEFORE REAL FUNDS" | Set 0 for Primary-live (every lot counts) | Primary | Low |

**What the half-hourly :51 glitch check should also check** (alongside the :21 monitor), per account:
1. Broker positions vs open journal lots (qty per symbol; any non-MCF or untraded-today symbol), as in LR5.
2. Any open MCF position with **no working stop leg** (unprotected lot) and `-u` closes.
3. Orders stuck in new/accepted/pending for > 2 min; entries unfilled.
4. `health.flatten_failed`, `health.outage_actions`, `health.data_stale`, `health.partial_lots`.
5. Realized + open MTM R vs the −20R halt, and per-setup vs −2R. Is the latch state consistent with the journal?
6. status.json age (< 5 min) and that the job / handover successor is queued.
7. Rejected-order count and reasons since the last check (buying power, duplicate id, asset not tradable).
8. Equity jump vs MTM (a corporate-action / phantom tell, as MTUM's ~$11.6k phantom swing in the 11-06 running total).
9. Early-close / holiday flag for today (from the Alpaca calendar) and the flatten time in use.
10. Buying-power headroom (DTBP − open notional) and PDT flag / day-trade count (real money).

Reply with codes, e.g. "LR1 yes", "LR2 yes", "LR8 yes (no entry bp)".

Educational only — not financial advice.
