Educational only — not financial advice

# night1102 / losers — every major losing trade, 2026-10-20..11-02, all 5 intraday accounts

Live = paper fills (rule 7). R = `pnl_adj / (|entry − stop| × shares)`, run_id 1 of each journal. Plan written first: `PLAN.md`.
Scripts: `load.py` (journals + read-only Alpaca 1-minute SIP GET for every traded symbol-day into scratch), `symtype.py`,
`sim.py` (1-minute path engine), `analyze.py`, `whatif.py`, `patterns.py`, `filters_live.py`, `report.py`, `test2y_filters.py`,
`test2y_exits.py` + `exits2y_report.py`, `add_backlog.py`. Outputs: `losers_primary.csv` (133 rows, one per Primary loser with
every field below), `losers_all.csv.gz` (2,657), `pattern_table.csv`, `whatif_live.csv`, `filters_live.csv`, `filters_2y.csv`,
`exits_2y.csv`, `*_out.txt`. The locked block 2024-11-01..2025-02-28 was never loaded (asserted). Costs always in.

**Configurations: 26 distinct rules** (15 entry/exit what-ifs + 11 filters), **51 scorings** (15 live what-ifs, 11 live
filters, 10 filters × 2 two-year portfolios, 5 exits on two years). Try-count bar at N 26: t ≥ 2.55 (BAR90 2.30).
**0 of 26 pass "better live (Primary and the pool) AND better on two years in up and down sessions".**

## Failures first

1. **No loser pattern survives outside the days that made it.** On Primary's three bad days (10-29 / 10-30 / 11-02, −20.0R on
   43 trades) three entry-time patterns explain **−15.3R of the −20.0R** (18 trades): same symbol again, inverse-ETF short,
   late entry with an extended SPY move. **On Primary's other 7 days the same flags carried +31.6R** (91 trades). Skipping them
   over the full two weeks costs Primary money (table below), and none of them holds on the two-year frames.
2. **Better entries do not help once the measurement is fair.** A first pass showed "wait 1-5 bars" +0.05..+0.07R, t 4-6. That
   was the live fill friction: the live fill is on average **0.041R worse than the next 1-minute open** (median 0.043R in Primary),
   and every "wait" variant was filled at a bar open. Against the same no-friction open fill (`wait0`), waiting 1/3/5 bars adds
   +0.002 / +0.014 / +0.019R (t 0.4 / 1.8 / 1.7) on the pool and −0.011 / +0.008 / −0.007R on Primary. Limit at VWAP / 0.25R
   pullback: +0.018 / +0.010R pool, **−0.153 / −0.113R Primary** (the pullback limit misses Primary's winners).
3. **Exit tweaks fix the losers and give it back on the winners.** On the losers alone every variant "helps" (+0.10..+0.50R,
   t 3-9) — that is selection. On all trades: time stop 30/60 min +0.027 / +0.031R pool, −0.018 / −0.005R Primary; break-even
   after +0.3R +0.001 pool, −0.055 Primary, and −0.023R (t −2.5) on two years; no-progress scratch (out at 15/30/60 min if MFE
   < 0.25R) +0.008 / +0.010 / +0.014R pool, −0.053 / 0.000 / +0.009 Primary, +0.000R on two years; half off at +0.5R +0.005 pool,
   −0.025 Primary, +0.001R two years.
4. **The one adjustment that is better on both data sets fails the regime gate and Primary:** stop 1.5× wider at the same $ risk
   (target price unchanged). Live pool +0.050R/trade (t 4.22, 9 of 10 days, best day 21% of the gain), every testing account
   +0.036..+0.067R, **Primary −0.018R** (10-22 alone −20.4R: the big target day pays less in R). Two years (the 10 lab setups
   Primary ran, 18,240 trades): +0.019R, t 2.81, 15/21 months, **up +0.057 / flat +0.002 / down −0.012R** → fails "positive in up
   AND down". Logged as failed with a rework (`losers1102-wide-stop-15-same-dollar`, parent `gb-1019-wide-stop-t05`).
5. Limits: the sim enters at the live fill and starts on the first full bar after it (sim vs live R corr 0.96, sim mean −0.158 vs
   live −0.125: conservative); freed slots / caps after a skip are not modelled; two-year exits run on 5-minute frames without an
   open (gap fills at the prior close) and the lab universe (1,226 names) — no L3 / CWT / ST7 / GEN setups on two years.

## The loser set

2,657 losers (R ≤ −1, plus each account-day's 10 worst) of 7,357 trades: Primary 133 (−129.9R), Testing 1 486 (−541.8R),
Testing 2 488 (−544.8R), Graveyard 1,068 (−1,183.5R), Gen 482 (−510.5R). Two-week totals: Primary +33.8R on 411 trades (+0.082R),
T1 −146.5R, T2 −103.5R, Graveyard −420.8R, Gen −282.1R.

What a loser looks like (medians, Primary / all): R −1.09 / −1.09 (98% are full stops; 0.09R of slippage past the stop), MFE before
the stop **0.28R / 0.19R** (43% / 52% never reached +0.2R), time to stop **55 / 56 min** (only 3% within 5 min), entry at 61% / 65%
of the prior 5 bars' range in the trade direction (25% / 29% at the extreme 10%), that range = 0.36R / 0.40R, stop 77 / 86 bps,
SPY from open at entry +0.04% / −0.01%. Primary losers: 95 shorts / 38 longs; 102 stocks, 20 ETFs, 8 inverse, 3 leveraged; entry
hour 10:00-11:59 for 61%. **Opposite side in hindsight: 87% (Primary) / 91% (all) would have won** — mostly mechanical (a full stop
on a 1R-ish bracket is most of the way to the mirror trade's target), and not knowable at entry.

Primary's three bad days (SPY open→close +0.09%, −0.75%, −0.97%): 10-29 shorts −9.8R on a flat day (NTSK ×3 lots at 13:00 −3.3R,
WDAY ×3 −3.4R); 10-30 longs +2.1R, shorts −4.6R, all after 13:55 into the afternoon bounce (ZETA ×3 −3.3R); 11-02 SOXS short ×6
(L3 setups, = long semis on a −1% day) −6.1R of the day's −6.2R; the other shorts that day were net positive.

## Pattern table (losers, Primary first) and the one adjustment per pattern

| pattern | Primary losers (share, R) | all losers (share, R) | adjustment | live Primary: R skipped / avg R of skipped | live pool: Δ total R, day t | 2-year (10 Primary lab setups): avg R skipped vs kept, day t | verdict |
|---|---|---|---|---|---|---|---|
| P1 inverse-ETF short (= long the underlying) | 8 (6%, −8.4R) | 31 (1%, −32.9R) | no shorts on inverse / long-VIX ETFs | 13 trades, −0.29R → +3.8R | +19.7R, t 0.95, 4/10 days | **+0.062** vs −0.050, t −0.77 (skipped trades are better) | fail (as `nightly-1102-skip-inverse-etf-shorts`) |
| P2 same symbol again (2nd+ lot that day, any setup) | 32 (24%, −34.5R) | 720 (27%, −794.7R) | one lot per symbol per account per day | 101 trades, **+0.197R** → −19.9R | +192.5R, t 1.71 (Graveyard t 2.94) | −0.055 vs −0.047, t 1.96 | fail: hurts Primary; the pool gain is "trade less" (as `sat1024-one-lot-per-symbol-2y`) |
| P3 stacked same-side lots (4th+ in a 10-min chain) | 44 (33%, −49.8R) | 2,127 (80%, −2,356R) | cap 3 per chain | 186 trades, **+0.344R** → −64.0R | +660.6R (kept avg R worse: −0.178 vs −0.125) | −0.055 vs −0.031 (all 21 setups: kept avg worse) | fail: cuts 80% of trades, Primary's stacks are its winners |
| P4 late (≥ 13:30) entry with SPY ≥ 0.75% from open in the trade direction | 5 (4%, −5.4R) | 46 (2%, −49.6R) | skip | 5 trades, −1.08R → +5.4R | +43.0R, **1 of 10 days** | +0.016 vs −0.049 (n 57, t −0.17); all 21: −0.128, t 1.39, best day 62% | fail: one day (10-30); neighbours 0.5/1.0%, 13:00/14:00 the same |
| P5 chased entry (extreme 10% of the prior 5 bars) | 33 (25%, −30.4R) | 764 (29%, −826.6R) | wait 3 bars / 0.25R pullback limit | wait3 +0.008, pb25 −0.113R | wait3 +0.014 (t 1.8), pb25 +0.010 | not run (needs 1-minute paths) | fail live |
| P6 tight stop (< 53 bps, bottom quintile) | 37 (28%, −38.0R) | 606 (23%, −699.2R) | stop 1.5× at the same $ | −0.018R | **+0.050, t 4.22** | **+0.019, t 2.81**, up +0.057 / down −0.012 | fail (regime gate, Primary) → rework in backlog |
| P7 never worked (MFE < 0.2R) — hindsight | 57 (43%, −63.8R) | 1,387 (52%, −1,531R) | scratch at 30 / 60 min if MFE < 0.25R | 0.000 / +0.009 | +0.010 (t 0.96) / +0.014 (t 2.07) | +0.000 (scr60), t 0.06 | fail |
| P8 fast stop (≤ 5 min) — hindsight | 4 (3%, −5.1R) | 91 (3%, −113.6R) | wait 1 bar | −0.011 | +0.002 | — | fail (rare anyway) |
| P9 market moved against after entry — hindsight | 72 (54%, −69.0R) | 1,583 (60%, −1,736R) | none at entry; regime layer | — | — | — | the main driver (see the regime workstream) |

Primary's live skipped-trade numbers are actual live R (a skipped trade = 0). Two-year = `research/history2y/data/lab_trades.parquet`
(production costs, R = 0.25 × daily ATR) for MF1-4, NS1/3/4/5, RW3, RW5, 2024-10..2026-10 minus the locked block.

## What this says (for the owner)

- **The losers are not a different kind of trade.** At entry they look like the winners: same entry position, same stop width,
  same time of day, same symbol types. 98% are plain full stops that never got going (median MFE 0.2-0.3R, ~55 min to the stop),
  and in 54-60% the market moved against the side after entry. Every "fix" that rescues the losers costs the winners the same or
  more, live and on two years. That is the same conclusion as the simple and regime workstreams from the other end: the book is a
  market-direction bet with ~0.04R of entry friction on top.
- **Each bad day had its own story** (10-29 stacked lots in 2-3 names on a flat day, 10-30 late shorts into a bounce, 11-02 six SOXS
  shorts) — and each story was profitable on the other days. Changing a rule after each bad day would have chased noise.
- **Something concrete that is real: entry friction.** Live fills cost 0.041R per trade against the next 1-minute open (about a
  third of the testing accounts' average loss, half of Primary's +0.08R average). Wider stops at the same $ (fewer shares) are the
  only tested change that improves the pool live and two years, because friction shrinks with the share count — but it fails the
  down-session gate and Primary, so it is a backlog rework, not a proposal. The Testing cost filter CF (skip entries whose
  stop round trip > 0.15R, from 10-30) attacks the same friction; its forward record should be read with this in mind.

**No proposal for a setup or exit change.** Nothing here passes the rules; the only backlog line is the failed wide-stop entry
with its rework test.

## Rule / config changes in effect inside the window (research/ledger.jsonl)

R is per $ risk, so sizing changes do not move R, but they change what trades. 10-20: twin cap + per-setup −2R daily stop in
the testing accounts; MF2-FD / MF4-FD / NS3-FD promoted, MF3 / MF5 demoted. 10-21: promotion = move; Graveyard account starts;
L3-fromopen-FD and CWT14-pdl-p10-lowvol to Primary; MF3-FD demoted. 10-22: L3-fromopen-FD, NS3-FD, RW6G1 out of Primary. 10-23:
per-setup daily stop off in T1 / T2 / Gen (Graveyard keeps −2R). 10-26: MF1 demoted; CWT13-z05-long and ST7-FD promoted. **10-27:
GX1 5-minute clock gate fix (all accounts; a new version of every lab setup's record from here).** 10-27: CWT13 demoted. 10-28:
Primary position size ~$5k then ~$4k (slots 61 → 77); CWT14-pdl-lowvol, MF2 base, NS4-pm rotated out. **10-29: Primary per-setup
daily stop −2R (latched)**; Gen paused after the 10-28 run. **10-30: Testing cost filter CF (T1 / T2)**; L3-rsi5hi-FD and
L3-fromopen-FD promoted. 11-02: R2A legs into T2; NS3-FD / RW4-FD to the Graveyard. So Primary's 10-29..11-02 losers ran under the
−2R per-setup stop and with the two L3 setups behind the 11-02 SOXS lots newly promoted (10-30).
