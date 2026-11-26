Educational only — not financial advice.

# SQUEEZE_1125 pre-registration (written 2026-11-26 ~06:15 UTC, before any configuration below was built or scored)

Owner 2026-11-25: "explore unforeseen tactics... that will make this better". Failure mode targeted: **swing-midday-flip**
(11-10, 11-25) — a one-sided short book during an index reversal (11-25: 30 shorts / 0 longs at 11:39, net beta
−19.6R per +1% SPY; SPY −0.6% → +2.1% vs open, turn 11:56–12:20; 34.9R of the 48.5R swing was market direction).
Not re-tested here (already done): G1-2/G1-3 latch-open, G2-6 lot cap, G3 SPY+IWM squeeze no-new-entry guard,
SCALED-K4 / SHOCK-V (neveragain_1125, hsscale_1125), per-setup crash caps (s8cap_1125), L19 / VRL flip longs (bdi 1125).
Research only: no config, ledger, decisions or live change.

## Remedies (5 configurations)
**R1 NET-BETA BUDGET (B ∈ {8, 12, 16}; 3 configs).** Each open lot carries beta-weighted risk
`b_i = side_i × β_i × 0.01 × entry_i / risk_i` (R per +1% SPY). Net book beta NB = Σ b_i over the account's open lots
at the moment of the entry decision. A new SHORT is blocked while NB ≤ −B; a new LONG is blocked while NB ≥ +B
(re-evaluated at every entry; open lots untouched). β_i = point-in-time daily-return beta to SPY over the prior 60
sessions (≥ 20 obs, else 1.0), shrunk 0.67·β̂ + 0.33, clipped to [−3, 3] (keeps inverse/vol ETPs negative). Daily
closes: history2y daily.parquet (2024-09-16 on) + cache_fresh daily (≤ 2024-09-13); returns across the locked gap are
dropped (never read). Live: same formula on Alpaca daily bars.
**R2 SQUEEZE EXIT (reclaim ∈ {VWAP, OPEN}; 2 configs).** SPY 1-min bars, session open = 09:30 bar open, session VWAP
= cumulative Σ(typical price × volume)/Σ volume from 09:30. At the close of bar k (10:00 ≤ k ≤ 15:50): trigger SHORT-SIDE
if (a) some bar close earlier in the session ≤ open × (1 − 0.004), (b) close_k ≥ VWAP_k (VWAP variant) or ≥ open (OPEN
variant), (c) close_k / close_{k−30} − 1 > +0.005. Action at the close of bar k+1 (next minute): close every open short
at that minute's close (lot's cost in) and block new shorts for the rest of the day. Mirror for longs: SPY ≥ 0.4% above
the open earlier, close_k ≤ VWAP (≤ open), 30-min return < −0.5% → close all longs, block new longs. Each side fires at
most once per day.
**Cumulative count:** ≈ 2,264 before (R3N 2,230 + R3C 2 + s8cap 8 + neveragain 9 + BDI 1125 3 + scout 1125 12) → ≈ 2,269.
LATCH-OPEN runs are the required context (already counted as neveragain G1-2), not new configurations.

## Engine and book
neveragain/s8cap/hsscale minute-by-minute book engine (bench_sim.py logic, re-used): Primary lineup P4
(L3-gap-slope-fromopen-FD, RW3-…-short-FD, RW5-…-short-FD, NM-ETF-late-dip-di-long); price ≥ $5, shorts ETB ≥ 0.9,
30 open lots per setup, ≤ 3 per symbol per setup, 77 slots, burst brake 30 / 10 min, sticky −2R closed per-setup latch,
−20R closed + open no-new-entries halt. Entries see state at the end of minute m−1. Open marks from 1-min closes,
less the lot's cost. Candidate lots: bench10 regenerated tonight for the 4 setups unchanged (only SETUPS replaced; the
earlier work files are deleted), all raw signals, LR8 research costs + borrow (bench add_r). Baselines:
**BASE** (= live rules today) and **BASE+LO** (LATCH-OPEN: per-setup −2R latch counts closed + open R). Each remedy is
run on both: 5 configs × 2 = 10 runs + 2 baselines. RAW book (bench costs) is the scored book; a zero-expectancy book
(every lot shifted by its setup's BASE avg R; "trading less ≠ skill") is reported alongside, not scored.

## Splits
FIT 2024-10 + 2025-03..2025-09 (reported); CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13. The locked block
2024-11-01..2025-02-28 is NEVER read (pyarrow filters + asserts). Live window 2026-10-23..2026-11-25: Primary journal
lots (run 1, LR8 cost-R via mcf.costs, as footrace.live_trades), Alpaca SIP 1-min bars for open marks and SPY;
LIVE-BASE = actual lots with the −2R closed latch + −20R halt as a what-if; remedies only remove lots or flatten.

## Metrics (per config, vs BASE and vs BASE+LO; per period)
total R, avg daily R, avg of worst-5 days, days ≤ −10R, R given up on recovered days (Σ cfg − base over days whose
base trough of closed + open R ≤ −10R and whose close recovered ≥ half of that trough), fires per year (days fired /
sessions × 252), one-big-day check (dR without the best dR day, best day's share of total dR), per-setup dR (number of
setups better / worse and the sums; Remedies rule).

## Pass bar (fixed by the caller, applied to the RAW book, judged ON TOP OF LATCH-OPEN; "PASS-both" if it also holds vs BASE)
1. Avg worst-5 days improves by ≥ 20% (|cfg − base| / |base|, toward zero) in BOTH CHECK and T2.
2. Cost ≤ 2.5R per year in total R on CHECK (dR/yr ≥ −2.5).
3. Fewer than half of setups worse (pooled CHECK + T2 + FIT; with 4 setups: ≤ 1 worse).
Disclosed caveat (fixed now): the bench book loses on average, so blocking trades can raise RAW total R by trading
less; the zero-expectancy book is shown so this is visible. If a config passes: DECISION draft (Testing-first trial or
Primary option) for the Friday epoch in REPORT.md; decisions.json is not edited.
