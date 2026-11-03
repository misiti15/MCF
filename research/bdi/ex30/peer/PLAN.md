Educational only — not financial advice

# ex30 / peer — peers, sympathy, dispersion (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups (this lane delivers 5).
Family: a name against a moving peer group — sympathy laggards, index-vs-component divergence, index lead-lag, pair
spreads. Starting evidence: BDI 11-02 MH4 (`research/bdi/1102/mh4_group.py`): laggards of a residual-correlation peer
group moving >= 0.4 ATR by 09:40-09:50 beat a day-matched random entry by +0.075R (t 2.4-2.7), absolute P/L negative.

## Live-runner constraint found before scoring (stated up front)

`LabStrategy.generate` calls `mask(df)` on ONE symbol's 5-minute frame. `DayContext.peers` (today's bars of every polled
symbol) exists, but a lab module only sees it through `mcf/strategies/lab_context.py` columns: spy_fo, qqq_fo, breadth,
breadth_open, qqq_vwap, spy_prng. There is **no per-symbol peer group, no sector ETF and no pair leg** in that list, and
adding one is an `mcf/` change this lane may not make. MH4's residual-correlation peers (daily returns of 10 named peers)
and sector-ETF lead-lag therefore cannot run live today. Also: `qqq_vwap` is absent from the history2y context tables,
so no setup here uses it (it could not be scored).

What the runner does give, and what these 5 setups use as the "peer group":
- **SPY and QQQ as each name's moving peer**, with the name's *own intraday sympathy measured from the frame*: the
  expanding correlation and beta of its 5-minute returns against SPY's / QQQ's 5-minute returns (from the per-bar
  `spy_fo` / `qqq_fo` columns) over today's bars from the 09:50 bar close. History frames start at 09:50; the modules
  use only returns of bars with tod >= 09:55 (prev bar >= 09:50) live as well, so live and history compute the same stat.
- **The universe as the component set of the index** (`breadth_open`) for index-vs-component divergence.
- **QQQ vs SPY** spread for growth-led (narrow) tapes.

## Data, splits, costs, controls (reuse of night1102/simple and ex30/xsec harness)

- history2y open frames + lab context (`lib.load_month(m, context=True)`). TRAIN = 2024-10, 2025-03..2025-12;
  VALID = 2026-01..03, 2026-07-01..2026-09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block
  2024-11-01..2025-02-28 never loaded** (asserted: no locked month in the list, MCF_HIST_ALLOW_LOCKED unset).
- Trades: `mcf.research.gates.lab_trades` (first qualifying bar per symbol-day, no refire; production costs 1c + 1 bps
  per side, +2c on stops, time-of-day entry multiplier). R = 0.25 x daily ATR, flat 15:55. ADV floor 95M (adv20).
- Random control: day-matched — trade R minus the mean production R of every eligible bar (same side / geometry /
  window / ADV floor) on that date. Excess and its day-clustered t reported.
- Day type: SPY open-to-close (SIP 1-minute cache): up >= +0.25%, down <= -0.25%, else quiet. R by type, TRAIN and VALID.
- Light lane gate: avg R >= -0.02 on TRAIN and on VALID, 1.5-25 trades/session (TRAIN+VALID sessions), mask parity
  module vs harness on 2026-09 (bar by bar inside window + ADV). No BAR90. A failing setup is still delivered,
  marked gate_pass = false.

## Notation (all at the bar close, per symbol-day)

rs = stock 5-min return %, ri = index 5-min return % from consecutive `spy_fo` / `qqq_fo` values; both only for rows
with tod >= 955. n = number of such return pairs so far (incl. this bar). corr / beta = expanding Pearson correlation and
OLS beta of rs on ri over those n bars (corr_s/beta_s vs SPY, corr_q/beta_q vs QQQ). atrp = atr_d / close x 100.
move = (close - open) / atr_d. res_s = (fromOpen - beta_s x spy_fo) / atrp (move left after the name's own SPY beta,
in daily ATRs); res_q likewise vs QQQ. q2 = QQQ % change over the last 2 bars; s2 = stock % change over the last 2 bars.
vwd = vwapDistPct.

## The 5 setups (primary form = the delivered module, fixed now; results do not change the choice)

| id | side / geom | window | rule |
|---|---|---|---|
| PR1-sympathy-laggard-long | long t1s1 | 10:30-13:30 | n >= 8, spy_fo >= +0.30, corr_s >= 0.50, beta_s >= 0.50, res_s <= -0.50, close > prev close |
| PR2-decoupled-quiet-breakdown-short | short t1s1 | 10:30-14:30 | n >= 8, abs(spy_fo) <= 0.25, abs(corr_s) <= 0.15, move <= -1.0, vwd < 0, close <= lowest earlier close of the day |
| PR3-narrow-rally-laggard-short | short t1s1 | 10:30-14:30 | spy_fo >= +0.30, breadth_open <= 0.45, qqq_fo >= spy_fo, move <= -0.50, vwd < 0 |
| PR4-qqq-residual-stretch-revert-short | short t05s1 | 11:00-15:00 | n >= 12, corr_q >= 0.40, res_q >= +1.25, res_q < its value one bar earlier, close < prev close |
| PR5-qqq-impulse-leadlag-long | long t05s1 | 10:20-15:00 | n >= 6, corr_q >= 0.50, beta_q >= 0.80, q2 >= +0.20, s2 <= 0.25 x beta_q x q2 |

Why each is a peer idea: PR1 = MH4's laggard catch-up with the peer group the runner has (the index the name is
co-moving with today); PR2 = the quiet-day design — a name that has *decoupled* from the tape and is breaking down on
its own while the index is flat (the live book has no quiet-day edge); PR3 = index-vs-component divergence (index up,
most components below their open, QQQ-led: a narrow rally) — short the components that are not being carried;
PR4 = a pair spread stock vs QQQ: the residual over the name's own QQQ beta is stretched and rolling over; PR5 = index
lead-lag: QQQ impulses over 10 minutes, a high-beta sympathy name has not responded yet.

**Neighbours (plateau check only, never substituted):** PR1 res_s <= -0.35; corr_s >= 0.35. PR2 move <= -0.75;
abs(corr_s) <= 0.30. PR3 breadth_open <= 0.40; spy_fo >= +0.20. PR4 res_q >= 1.0; res_q >= 1.5. PR5 q2 >= 0.15;
q2 >= 0.30. = 10 configs.

## Count

5 primary + 10 neighbours = **15 configurations**, all reported in results.csv. Nothing else is scored.
