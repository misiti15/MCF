Educational only — not financial advice.

# Crypto setups round 1 (first hand-built setups): pre-registration (written 2026-11-26, before any scoring run)

Owner request 2026-11-26: "In the same way we established the first setups before the generator for intraday
trading, do a full blown research project... and create the first setups for testing." Research only: no live or
config changes, no Alpaca trading or account endpoints (public GET market data only, no keys). LOCKED
(2026-05-26..2026-11-25) is never read: the loader clips at its start and the runner asserts that
`MCF_CRYPTO_ALLOW_LOCKED` is unset.

**Sources of every parameter** (none fitted): `research/crypto_found/ANATOMY.md` (our own clean-bar measurements;
it overrides KNOWLEDGE where they conflict), `research/crypto_found/KNOWLEDGE.md` (ranked candidates and their
thresholds), rounds 1-3 (`research/crypto_r{1,2,3}/REPORT.md`). Engine smoke test on real data: none run before
this file (synthetic unit tests only, `tests/test_crypto.py`).

## 0. Data, engine, costs (common to all setups)
- **Signal bars:** clean traded-only bars (`mcf.crypto.exec1m.clean_traded`: Amendment-1 bad-print filter, then
  minutes with volume > 0), resampled to 1h / 4h / 1d UTC. An hour with no trade has no close (no signal, NaN
  return). Trigger hours must have >= 3 traded minutes and a traded previous hour (ANATOMY §4 stale-print artifact).
- **Fills (engine E5c, `mcf/crypto/setups1.run_levels`):** every entry is a **maker limit buy** that fills only on a
  later traded minute whose low is strictly below the limit (round-2 Amendment-1 rule); fill = limit price, maker
  fee, no spread. Missed orders are counted, not chased. Stop = limit − risk, taker (half-spread + 2 bps + 5 bps stop
  extra), fills at the stop or the minute's open on a gap, checked on the fill minute too. Target (when set) is a
  resting maker sell that fills only on a later traded minute trading through it. Time stop = taker at the first
  minute at/after fill + hold. One open position or resting order per pair per setup.
- **Costs:** Alpaca tier 1 (maker 15 bps, taker 25 bps), half-spreads from `research/crypto_r1/spreads.json`.
- **Common stop:** risk = max(1.5 × ATR(14, 4h), floor × limit), floor **3 % BTC/ETH, 4 % alts** (ANATOMY §7.1:
  stops ≥ 1-1.5 × ATR4h so the 0.5-0.7 % maker round trip is ≤ ~0.2R). CPI is the one exception (below).
- **Default limit:** decision close − 0.25 × ATR(14, 1h) (ANATOMY §3(c): a third of the bounce sits in the first
  hour where bid-ask bounce lives; rest a limit below, never chase the print).
- **Coins:** majors M = BTC, ETH (lowest cost, most capacity); alts A = SOL, DOGE, LINK, UNI (best ATR4h ÷ cost,
  ANATOMY §1). XRP (FIT starts 2024), LTC, BCH, AVAX (≈0.9 % spreads in 2026) are left out.
- **Regime gates** (BTC daily, last completed UTC day): `not_down` = off when BTC close < SMA50 **and** SMA50 below
  its value 10 days earlier (ANATOMY §5: the flush 12h median flips in the 2022 bear); `btc_up` = BTC close > SMA50.
- **Vol clock:** a filter only (US session ×1.2-1.3, weekends ×0.75-0.88). No time-of-day drift is used.

## 1. Setups and configs (8 setups, 14 configs, ids 1478-1491; at most 2 variants each)
| id | setup / var | trigger (decision time) | entry | target | time stop | gate | session filter | coins |
|---|---|---|---|---|---|---|---|---|
| 1478 | CRY-FLUSH-1 a | 1h z ≤ −3 (z = 1h log return / trailing 720h σ) at the hour close | lim default, live 120 min | none | 12 h | not_down | 24/7 | M |
| 1479 | CRY-FLUSH-1 b | same | same | none | 12 h | not_down | 24/7 | A |
| 1480 | CRY-SHOCK-1 a | 1h −3 < z ≤ −2 in a vol-clock hour (weekday 13:00-20:59 UTC or the 00 UTC hour); skip one hour, decide at the close of h+1 (must trade) | lim default, live 60 min | none | 12 h | not_down | vol clock, weekdays | A |
| 1481 | CRY-REV12-1 a | at 00:00 / 12:00 UTC: prior 12h block return ≤ −2 σ12 (σ of the trailing 180 blocks); the block's last hour traded | lim default, live 60 min | none | 12 h | not_down | weekday decisions | M |
| 1482 | CRY-REV12-1 b | same | same | none | 12 h | not_down | weekday decisions | M + A |
| 1483 | CRY-UPDIP-1 a | extreme up-day D: daily z ≥ +2 (σ of trailing 90 daily returns), close > open, D a weekday; decide 00:00 D+1 | limit at a 50 % retrace of D's body, live 24 h | D's close (maker) | 24 h | btc_up | weekday up-days | M |
| 1484 | CRY-UPDIP-1 b | same | same | same | 24 h | btc_up | same | A |
| 1485 | CRY-DAY2-1 a "reclaim" | crash day D: UTC return ≤ −8 % (M) / ≤ −12 % (A); on D+1 00-16 UTC, after a trade below D's low, the first 1h close back above it | limit at D's low, live 4 h | max(mid of D's range, +0.5R) maker | 24 h | none (built for crashes) | — | M + A |
| 1486 | CRY-DAY2-1 b "open" | same crash day; decide 00:00 D+1 | limit D close − 0.25 × ATR(14, 1d), live 16 h | same | 24 h | none | — | M + A |
| 1487 | CRY-WKND-1 a | weekend low (Fri 16:00 ET → Sun 22:00 UTC) ≤ Friday close −4 % (M) / −6 % (A); then the first 1h close above the Friday close with its close in (Sun 22:00, Mon 15:00 UTC] | limit at the Friday close, live 4 h | max(weekend high, +1R) maker | 24 h | not_down | by construction | BTC ETH LINK |
| 1488 | CRY-WKND-1 b | same | same | same | 24 h | not_down | same | M + A |
| 1489 | CRY-CPI-1 a | CPI day (64 BLS dates 2021-01..2026-05), 08:45 ET: last print ≥ +1.2 % vs the last print before 08:30 ET and above the 08:30-08:45 VWAP | limit at that VWAP, live 30 min | +2R maker | 435 min (16:00 ET) | none | event | M |
| 1490 | CRY-DIP-1 a | at each 4h close (weekdays): 24h return ≤ −1.5 σ24 (σ of the trailing 540 4h-spaced 24h returns), the coin's own and BTC's daily close > SMA50 | lim default, live 4 h | none | 24 h | btc_up (+ own > SMA50) | weekday decisions | M |
| 1491 | CRY-DIP-1 b | same | same | none | 24 h | same | same | A |

CPI stop: risk = max(limit − the pre-08:30 print, 2 % × limit) (KNOWLEDGE #6). CPI has about 64 events, of which
only a handful can trigger, so it **cannot reach the 60-trade bar**; it is scored for information.

**Reference only (not a new config, not re-scored):** CRY-TREND-REF = round-3 rule 980 (BTC/ETH/SOL long while the
daily close > SMA50), the swing overlay. Its numbers are quoted from round 3; only its current state is reported.

**Dropped as seeds (ANATOMY §6):** Asia-range breakout, CME gap, round numbers, BTC→alt lead (stale prints), SPY
lead, hour-of-day drift, big-hour continuation (ANATOMY: up-hours fade −23 bps / 4h, no momentum at any horizon).

## 2. Splits, counting, bars
- FIT 2021-01-01..2024-12-31; CHECK 2025-01-01..2026-05-25 (**its 4th look as a window**, bar raised to t ≥ 1.5);
  LOCKED never read. Signals use history from 2021-01-01 (warm-up: about 60-90 days before the first signal).
- **N_cum = 1,477 + 14 = 1,491; noise bar sqrt(2 ln 1491) = 3.82.** Every config is counted.
- Metrics per config and split: trades, maker fill rate, avg R, avg R without the best UTC day and that day's share
  of total R, day-clustered t (UTC entry day), win %, cost per trade in R, max drawdown in R (cumulative, by exit
  time), active-day share (UTC days with a position), avg R by regime year (2021 / 2022 / 2023 / 2024 / 2025-26),
  per-coin n and avg R, and **random entries at the same exposure**: 100 reps, the same number of signals per coin
  placed at random traded-hour closes in the split, each with the geometry (limit offset, stop, target as fractions
  of the limit, expiry, hold) of a random real signal of that coin; the setup's percentile on avg R.
- **Active now:** the share of BTC-below-SMA50 days (FIT + CHECK) on which the setup held a position, plus the gate
  state on the last readable day (2026-05-25) and in November 2026 (KNOWLEDGE §0: BTC ≈ 50 % off its peak, below a
  falling SMA50).

## 3. Pass bar ("testing candidate"; all required)
1. FIT eligible: ≥ 60 trades, best-day share < 0.5, avg R without the best day > 0, day t ≥ 3.82.
2. CHECK (scored ONCE for all 14 configs; FIT results are written to disk and committed before CHECK runs):
   avg R > 0 with day t ≥ 1.5.
3. Positive avg R in at least 3 of the 5 regime years (2021, 2022, 2023, 2024 on FIT; 2025-26 = CHECK).
- **Near-miss** (reported, may go to the backlog as an idea): net avg R > 0 and avg R w/o best day > 0 on FIT and
  avg R > 0 on CHECK, failing only on t, trade count or the year count.
- A pass or near-miss goes to `research/backlog.jsonl` as status "idea", tag "crypto". Nothing goes live: a paper
  run needs the owner's yes, a crypto paper account, a 24/7 runner, the r1 §4 failsafes and a crypto change window.

## 4. Known biases
Survivorship (only today's listed pairs; 2021-26 winners flatter any long), last-trade prices on a thin venue
(bid-ask bounce inflates short-horizon reversal; limits below the print guard against it), spreads before 2023 use
the earliest sampled year, the bad-print filter removes real > 25 % one-minute wicks (slightly optimistic on stops),
alt capacity of $2-45k a day since 2025 (ANATOMY §0), and 2021-22 CPI dates taken from the BLS schedule as recalled.
