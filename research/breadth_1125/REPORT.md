Educational only — not financial advice
# BREADTH-1125: our own intraday breadth as a close-gate, and the PYR4 hedge book (2026-11-26, research only)
Pre-registered before scoring (PREREG.md, sha256 275b9023…f328, 06:12 UTC). 14 configs (12 gates + 2 books); cumulative N ≈ 2,244. Locked block never read for data (one early `min/max` timestamp probe of SPY's cache index skipped the filter; no locked values were used). FIT 170 / CHECK 276 / T2 427 sessions. Backtest applies today's Primary rules (−2R latch, cap 30, LR8 costs + borrow) to every window; no live trades, so no ledger rule-change dates fall inside these figures.
**Data gap closed:** `build_breadth.py` builds 5 point-in-time breadth series (VWAP %, open %, 30-min A/D, up-volume, new highs − new lows) from the 469 names cached for 2023-01..2026-11 in ~12 min; % above VWAP has corr 0.98 with the lab's `breadth` column. The 2023-24 blocker is gone.
## Verdict: FAIL on both parts. No gate predicts the close; PYR4 is worse than Primary. No DECISION draft.
**Part A** gate on SPY close > SPY at T: hit-rate lift vs base rate, in pp (z). θ fitted on FIT only.
| Gate | T | FIT | CHECK | T2 |
|---|---|---|---|---|
| GA % above VWAP (frozen: FIT-best, θ 0.58) | 13:00 | +12.1 (2.03) | −2.7 (−0.53) | +4.2 (1.11) |
| GA | 11:00 / 12:00 | +9.4 / +11.5 | +3.4 / −2.2 | −1.6 / +1.8 |
| GB 5-measure composite | 11/12/13 | +11.4 / +15.9 / +13.5 | +3.2 / −3.1 / −14.7 | −0.9 / +2.2 / +3.6 |
| GC 60-min breadth thrust | 11/12/13 | +9.4 / +2.4 / +10.6 | −1.5 / +2.4 / +4.3 | −2.3 / 0.0 / −1.0 |
| GD TT1 + composite | 11/12/13 | +15.5 / +14.9 / +15.0 | −1.1 / −9.6 / −6.2 | −2.1 / −1.2 / +7.2 |
0 of 12 are "useful" (≥ +5 pp with z ≥ 2 on both CHECK and T2). Every FIT lift of +9 to +16 pp shrinks to noise (|z| < 1.8) out of sample. Midday breadth describes the morning; it does not forecast the afternoon.
**Part B** (bench10, Primary book rules, 1R/trade). PYR4 = L3-fromopen + RW3 + RW5 shorts + NM-ETF + GEN-261027-01, longs gated.
| Book | CHECK avg day / worst-5 / red % / days ≤ −10R | T2 avg day / worst-5 / red % / ≤ −10R | Paired t vs Primary, CHECK / T2 |
|---|---|---|---|
| Primary (3 shorts + NM-ETF ungated) | −1.83 / −39.6 / 58.0 / 57 | −1.51 / −24.3 / 56.9 / 31 | — |
| PYR4-BR (frozen GA 13:00 day switch) | −2.04 / −41.0 / 59.1 / 64 | −1.53 / −25.4 / 56.7 / 31 | −1.81 / −0.41 |
| PYR4-TT1 (TT1 at entry) | −1.93 / −40.5 / 58.3 / 64 | −1.53 / −25.9 / 57.4 / 28 | −0.69 / −0.39 |
One-big-day check: every book is negative in every window, so best-day share is n/a. Avg day without the best day: CHECK −2.06 / −2.27 / −2.16, T2 −1.55 / −1.57 / −1.57 (Primary / BR / TT1).
Per leg (remedy rule), CHECK / T2 total R: GEN-261027-01 ungated −59.6 / −40.0, +BR −54.8 / −6.5, +TT1 −23.3 / −18.1; NM-ETF ungated +10.7 / −9.2, +BR +8.0 / −11.7, +TT1 +6.2 / −2.0. The gates cut GEN's losses but do not make it positive anywhere, and adding it costs more than gating NM-ETF saves. In CHECK, NM-ETF's gated per-trade R is better (+0.135 BR, +0.079 TT1 vs +0.041), but on fewer trades.
Hedge: long-sleeve vs short daily correlation is −0.19 for Primary (CHECK) but ~0 for PYR4-BR and +0.02..0.06 in T2. On the shorts' 10 worst CHECK days the long sleeve adds +3.4R (Primary), −5.7R (BR) and +18.2R (TT1), against −365R from the shorts on those days. The long legs are too small and too weak to hedge. Pass bar (worst-5 and avg day better in both windows, CHECK t ≥ 2): not met by either book.
## What next (backlog, optimistic but honest)
1. Keep `build_breadth.py` as shared infrastructure. Breadth now exists for 2023-24, so breadth-conditioned setups (e.g. the R3N "TT1 + thrust" idea, which GD tested and failed) can be scored on T2.
2. Move the close-gate target from SPY to the long book's own R. A gate tuned for the index close may not be what saves a stock long; pre-register 1 config.
3. The hedge problem is on the short side: the 3 Primary shorts lose ~1.5–1.8R a day in this engine. The R3C live-cost re-score of the gap-down family comes before any further hedge work.
