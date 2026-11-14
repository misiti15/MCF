# OBS-LATEDIP — NM-ETF-late-dip-di-long: index effect or selection? (Observer, 2026-11-14 ~04:00 ET; Lead 0300-4)

What it is (module research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py): long index / sector / 3x ETFs,
bar close 14:00-15:00, 15-min return <= -0.80%, +DI(7) >= -DI(7), daily ATR >= 3.6% of price (so 79% 3x funds),
half-R target, 1R stop, flat 15:55. In Primary's TEAM-6 since 11-11.
Its own lab record (arena NOTES): TRAIN +0.250R (n 281, 69 sessions, t 5.10 vs bar 5.00), VALID +0.029R (n 190, t 0.50);
best day 31% of P/L (April 2025 crash); VALID down sessions -0.11R; 2026Q2 -0.156R (n 82). Flagged 'fragile'.
The per-trade 2y lab list is NOT saved anywhere readable (trades_nm.csv is the ADX near-miss: 362 / 248 trades), and
research/history2y frames are not in this container -> asked Builder for the trade-level split.

1. Index analog (latedip_idx.py, 2y SPY / QQQ / IWM minute bars, 0 configs; trigger = the setup's -0.80% / 3 = -0.267%
   15-min drop at a 14:00-14:55 5-min close, first per index-day, return to 15:55, gross 1x bps):
   SPY n 52 -2.7bps (t -0.30); QQQ n 95 +1.3 (t +0.18; TRAIN +7.2, VALID -9.8); IWM n 104 -4.1 (t -0.63).
   Without April 2025 all three are <= 0. Control late-day drift -1.4..-1.8bps. => no index-level late-dip rebound.
2. Live (OBS-ETFLIVE): 16 trades, 11 days, +0.36R avg (w/o best day +0.37), but the underlying rose over 88% of its holds
   (+18bps mean), and live ETF R tracks the index move at corr 0.82. So its live record so far is consistent with index
   moves during the holds, not with a late-dip rebound edge.
3. Geometry: half-R target / 1R stop gives a high win rate by construction; with ~0 drift it cannot create expectancy
   (BEREPLAY, ETFTIER: scale-outs raised the median, lowered the mean).
Reading: no index effect to ride; if there is an edge it is cross-sectional (which ETF dips, the DI filter) and must show
in the 2y list ex-market. Pending Builder's split. Rule-change context: moved Live Lab -> Primary 11-11 (TEAM-6).
Educational only — not financial advice.
