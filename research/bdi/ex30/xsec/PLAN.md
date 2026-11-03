Educational only — not financial advice

# ex30 / xsec — cross-sectional ranks (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups (this lane delivers 5).
Family: rank the whole universe at a decision time on one feature and trade the extremes.

## Live-runner constraint found before scoring (stated up front)

`LabStrategy.generate` calls `mask(df)` on ONE symbol's 5-minute frame. A true universe rank ("this name is in the
bottom 10 of 1,200 on move-from-open") is data the live runner does NOT have today: no context column carries a rank
(`mcf/strategies/lab_context.py` offers spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap, spy_prng). Adding one would be
an `mcf/` change, which this lane may not make. So:

- **The 5 deliverable setups use the cross-sectional columns the runner already has** — `breadth` (share of the universe
  above its own VWAP), `breadth_open` (share above its own open) and `spy_fo` — as the rank reference. A name that is
  below its open by >= 0.75 ATR while >= 65% of the universe is above its open is, by construction, in the universe's
  weak tail on that bar. These are "rank-proxy" setups: the stock's standing against the whole tape, not its own chart.
- **True top/bottom-k ranks are scored as information only** (grid T below), to show whether the rank method itself has
  anything; none of them can be deployed without a new context column (owner/lead decision, not this lane).

## Data, splits, costs, controls (reuse of night1102/simple harness)

- history2y open frames + lab context (`lib.load_month(m, context=True)`). TRAIN = 2024-10, 2025-03..2025-12;
  VALID = 2026-01..03, 2026-07-01..2026-09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block
  2024-11-01..2025-02-28 never loaded** (asserted: no locked month in the list, MCF_HIST_ALLOW_LOCKED unset).
- Trades: `mcf.research.gates.lab_trades` (first qualifying bar per symbol-day, as live without refire; production costs
  1c + 1 bps per side, +2c on stops, time-of-day entry multiplier). R = 0.25 x daily ATR, flat 15:55.
- ADV floor 95M (adv20), as the FD setups. Window = each setup's own (inside 09:50-15:00 bar closes).
- Random control: day-matched — trade R minus the mean production R of every eligible bar of the same side / geometry /
  window / ADV floor on that date. Excess and its day-clustered t reported.
- Day type: SPY open-to-close from the SIP 1-minute SPY cache: up >= +0.25%, down <= -0.25%, else quiet (night1102/regime
  eod3). R by up / down / quiet reported for TRAIN and VALID.
- Light lane gate (this run): avg R >= -0.02 on TRAIN and on VALID, 1.5-25 trades/session (TRAIN+VALID sessions),
  mask parity module vs harness on 2026-09 (bar by bar inside window + ADV). No BAR90 for the exploratory accounts.
  A setup failing the gate is still delivered, marked gate_pass = false.

## The 5 setups (primary form = the delivered module, fixed now; results do not change the choice)

Notation: move = (close - open of day) / daily ATR (open = close / (1 + fromOpen/100)); vwapATR = (close - VWAP) / ATR;
excess = (fromOpen - spy_fo) / ATR% (stock's move from open minus SPY's, in units of the stock's daily ATR%).

| id | side / geom | window | rule (all at the bar close) |
|---|---|---|---|
| XS1-laggard-greentape-short | short t1s1 | 10:00-14:00 | breadth_open >= 0.65 and spy_fo > 0 and move <= -0.75 and close < VWAP |
| XS2-leader-redtape-long | long t1s1 | 10:00-14:00 | breadth_open <= 0.35 and spy_fo < 0 and move >= +0.75 and close > VWAP |
| XS3-quiet-topoutlier-fade-short | short t1s1 | 10:30-14:30 | abs(spy_fo) <= 0.25 and 0.35 <= breadth <= 0.65 and excess >= +1.0 and close < prev close |
| XS4-quiet-bottomoutlier-fade-long | long t1s1 | 10:30-14:30 | abs(spy_fo) <= 0.25 and 0.35 <= breadth <= 0.65 and excess <= -1.0 and close > prev close |
| XS5-rankclimb-fallingtape-long | long t05s1 | 10:00-15:00 | breadth fell >= 0.15 over the last 3 bars and the stock's vwapDistPct rose over the same 3 bars and close crosses above VWAP on this bar (prev <= 0, now > 0) |

XS3 + XS4 are the market-neutral quiet-tape basket (short the top tail, long the bottom tail of the same bars); XS1 / XS2
are relative-strength baskets that trade AGAINST the tape (the live book's weakness is being a tape bet); XS3/XS4 are the
quiet-day design (they can only fire while SPY is within +-0.25% of its open).

**Neighbours (plateau check only, never substituted for the primary):** two per setup —
XS1/XS2: breadth threshold 0.60/0.40 (move 0.75), move 1.0 (breadth 0.65/0.35); XS3/XS4: excess 0.75 and 1.5;
XS5: breadth drop 0.10 and 0.20. = 10 configs.

## Grid T — true universe ranks (information only; not live-runnable)

At decision bar tod in {1000, 1100, 1300}, rank every ADV >= 95M name with a frame row on feature in {move, vwapATR};
take the top 10 or bottom 10; trade momentum (long top / short bottom) or fade (short top / long bottom); t1s1, enter at
that bar's close. 3 x 2 x 2 x 2 = 24 configs. Same costs, splits, control and day-type split.

## Count

5 primary + 10 neighbours + 24 grid T = **39 configurations**, all reported in results.csv.
