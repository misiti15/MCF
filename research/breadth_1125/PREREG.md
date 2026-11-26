Educational only — not financial advice

# BREADTH-1125 pre-registration (owner 2026-11-25 "explore unforeseen tactics"; written 2026-11-26 before any scoring)

Research only: no config, ledger, decisions or live change. Locked block 2024-11-01..2025-02-28 is never read
(pyarrow filters + asserts on every load). Splits: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..2026-11-04;
T2 = 2023-01-03..2024-09-13. Half-day sessions (no SPY 15:59 bar) are dropped from Part A.

## Breadth series (research/breadth_1125/build_breadth.py)
Universe U = the 469 symbols held in BOTH data/cache_fresh/1Min (2023-24) and data/cache_hist/1Min (2024-10..2026-11),
so FIT/CHECK/T2 use the same names. Regular-session 1-min bars. At decision minute T (HHMM, 5-min grid 09:50..15:00)
only bars labelled < T are used (point-in-time). Among names with ≥ 1 bar before T that day:
- M1 pct_vwap: share with last close > cumulative session VWAP.
- M2 pct_open: share with last close > the day's first 1-min open.
- M3 ad30: (n up − n down) / n on the 30-min return (last close vs last close labelled < T−30).
- M4 upvol: Σ volume of 1-min bars closing above the previous close / Σ volume of bars closing above or below it, since the open, all names pooled.
- M5 nhnl: Σ over minutes 09:45..T−1 of (#names printing a new session high − #new session low) / n.
TT1 (existing gate, Team G definition) recomputed from SPY 1-min bars: SPY > session VWAP, was ≥ 0.05% below VWAP
since 09:35, SPY 30-min return > 0.

## Part A — breadth close-gate (12 configs)
Target y(T) = 1 if SPY's last regular-session close > SPY's last close labelled < T. Decision times T ∈ {11:00, 12:00, 13:00}.
Gates (statistic ≥ θ):
- GA VWAP breadth: M1.
- GB composite: Z = mean of the five measures, each z-scored with its FIT mean/std at that T.
- GC breadth thrust: M1(T) − M1(T − 60 min).
- GD TT1 + breadth: TT1(T) true AND Z ≥ θ.
θ is fitted on FIT only, per config, from the FIT quantiles {0.3,0.4,0.5,0.6,0.7,0.8} of the statistic (GD: of Z on
TT1-on FIT days, plus "TT1 alone"), maximising the binomial z = (hits − n·p0)/√(n·p0(1−p0)) with p0 = FIT base rate
at T and n ≥ 15 gate-on FIT days. Reported on CHECK and T2 for all 12: gate-on days, hit rate, base rate, lift (pp),
binomial z. Descriptive bar ("useful gate"): lift ≥ +5 pp with z ≥ 2 on BOTH CHECK and T2.
The FIT-best config (highest FIT z of the 12) is frozen for Part B.

## Part B — PYR4 book test (2 configs)
Engine: research/ultimate_1119/top10/bench10.py unchanged (live config signals, 1-min exits, LR8 research costs +
1.2 bp borrow on shorts, price ≥ $5, ETB shorts), each setup in the Primary book rules (cap 30, −2R per-setup latch,
≤ 3 lots/symbol), 1R per trade.
- Reference = Primary's current book: L3-gap-slope-fromopen-FD, RW3-gapdn-rsi5pop-flowsell-short-FD,
  RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, NM-ETF-late-dip-di-long (ungated).
- PYR4 = the same 3 shorts + NM-ETF-late-dip-di-long + GEN-261027-01 (its generator module, ADV ≥ $20M, 14:00-15:00,
  t05s1, first hit per symbol-day), longs gated by
  (i) B-BR: the frozen Part A config as a day switch (both longs enter ≥ 14:00, after every T); (ii) B-TT1: TT1 at the
  long's entry bar.
Metrics per split: avg daily R, worst-5 days (mean of 5 worst), red-day %, days ≤ −10R, avg daily R w/o best day and the
best day's share; paired t of daily (PYR4 − Primary).
Pass bar (fixed now): PYR4 improves worst-5 days AND avg daily R vs Primary on BOTH CHECK and T2, with paired t ≥ 2 on CHECK.
A pass → DECISION draft (Testing-first) in the report only; decisions.json is not edited.

## Count
14 configs (12 + 2). Cumulative job N ≈ 2,230 (after Pyramid R3N) + 14 ≈ 2,244.
