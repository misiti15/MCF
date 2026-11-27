# PYRAMID round 2 — Team G ("gate the tape, grow from live") — pre-registration
Educational only — not financial advice. Written 2026-11-25 BEFORE any gated row was scored. Research only.
Inputs read so far: round-1 reports (L1, L3, S, X), their scripts and saved trade lists (not re-scored), BENCHMARK.md.

## Part 1 — TAPE-TURN gate (configs counted here)
Gate TT1 at a decision bar whose 5-minute bar closes at time T (ET), using SPY 1-minute bars labelled in [09:30, T) only
(point-in-time; T1 = data/cache_hist SPY, T2 = data/cache_fresh SPY, live = Alpaca SIP SPY 1-min fetched by L3):
  vwap = cumulative(close x volume) / cumulative(volume) from 09:30;
  (a) RECLAIMED: last SPY close (bar labelled T-1) > vwap;
  (b) WAS BELOW: some SPY 1-min close in bars labelled [09:35, T) was <= -0.05% from its running vwap;
  (c) TURNING UP: SPY 30-min return (last close vs close of bar labelled T-31) > 0.
TT1 = (a) & (b) & (c).  Sensitivity gate TT0 = (a) & (c) (no "was below" leg). Both counted as configs; no selection
between them: TT1 is the primary result, TT0 is reported beside it.

Gate is applied as a FILTER on each candidate's saved first-hit trades (signal unchanged), then the book is applied.
(A live implementation inside the mask would take the first bar where mask & gate hold; this filter version is the
approximation available without regenerating signals — stated, not tuned.)

Candidates (saved trades, exactly as round 1 scored them; no rule change except the gate):
  C3  L1 C3_V25 geometry G2 (OR20-RECLAIM, 10:00-12:00, t2s1)         - L1/trades_{fit,check,t2}.parquet, kind_=sig
  A1  GEN-261027-01 parent (14:00-15:00, t05s1, ADV>=$20M)             - L3/work/trades_{t1,t2}.parquet cfg A1 ctrl 0
  A3  GEN-261019-02 parent (13:00-15:00, t05s1, ADV>=$150M)            - L3 cfg A3 ctrl 0
  NM  NM-ETF-late-dip-di-long live config (14:00-15:00, t05s1)          - L1 kind_=prim cfg NM-ETF-late-dip-di-long
  B3  L3 B3a TREND-CLOSE-DRIFT (14:30, stop 1R, hold to 15:55)         - L3 cfg B3a ctrl 0
Configs: 5 candidates x {TT1, TT0} = 10. (Ungated parents are round-1 numbers, re-shown, not counted.)
Book: testing-arena rules (bench10.TESTING_RULES: cap 100, <=3 lots/symbol, price>=$5, stop-cost filter 0.15R) for all;
NM also shown under its Primary home rules. Costs LR8 research basis (bench10.add_r). Exits as saved (1-minute walk).
Split: bench10 half(): FIT = 2024-10 + 2025-03..09 (170 sessions), CHECK = 2025-10-01..2026-11-04 (276), T2 = 2023-01-03..
2024-09-13 (427, cache_fresh 469 names). Locked block 2024-11-01..2025-02-28 never read.

Controls (not counted):
  R1 same-symbol-day random bar (round-1 saved ctl rows), gated the same way.
  R2 UNIVERSE random long bars: per session, 60 random symbol-days from the 1-minute caches (cache_hist T1 / cache_fresh T2),
     price>=$5, ADV20>=$20M (A3: >=$150M; B3: >=$50M & price>=$10; NM: the module's ETF list & ADV>=$95M, all symbol-days),
     one uniform random 5-min close in each candidate window (C3 10:00-12:00, A1/NM 14:00-15:00, A3 13:00-15:00, B3 14:30),
     entry = close at T, R = 0.25 x ATR14(daily TR, prior days), the candidate's exit, same costs and book. Seed 20261125.
  Gate effect beyond random = (gated cand - ungated cand) - (gated R2 - ungated R2), and gated cand - gated R2.

Verdict bars (per gated config):
  PASS-GATE (the question asked): check avg R > 0 AND T2 avg R > 0 AND check w/o best day > 0 AND gated cand beats gated R2
    on check and on T2.
  TIER A: PASS-GATE + fit avg R > 0, check day-clustered t >= 1.5, both check halves > 0, >= 0.5 trades/session on check.
  ULTIMATE (owner bar, clear-cut better than the top 10): TIER A + check avg R >= +0.071 and T2 avg R >= +0.034 (best top-10
    values in BENCHMARK.md) and check w/o best day >= +0.028.
  TIER B: fit avg R > 0 and check avg R > -0.02.  Else FAIL.
Reported for every config: card per BRIEF (trades, sessions, /session, avg R fit/check/T2/live-gated, win vs break-even,
day-t, w/o best day + share, vs R1/R2, Primary reference book corr + R on its 10 worst days, median hold, gate-true share
of sessions). Cumulative job N ~1,906 + 10 -> t bar sqrt(2 ln N) ~ 3.89 (reported).

## Part 2 — live-vs-backtest gap (diagnostic, 0 configs)
GEN-261027-01 and L3-gap-slope-fromopen-FD, matched window 2026-10-06..2026-11-04 (lab data end). Decompose live vs
engine on: (1) set: live symbol-days outside the lab universe / in universe but no engine signal / engine signals not traded
live (book, ETB, caps, timing); (2) on matched symbol-days: entry minute and entry price (fill vs bar close, in R),
stop/target distance (R unit), exit path (engine 1-min walk replayed from live entry/stop/target), costs (live LR8 vs
add_r). Replays of non-lab names use Alpaca SIP 1-min bars (GET only). Report the gap per component in R/trade.
