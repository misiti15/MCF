Educational only — not financial advice

# BEG-01 ORB-15 on stocks in play: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change. Locked block 2024-11-01..2025-02-28 is never read.

## Rule as written (research/beginner_1120/DESIGN.md B01), implemented exactly
- Universe U0: price >= $5 (09:49 close), ADV20 >= $20M (prior 20 sessions, RTH dollar volume). Then price >= $10,
  RVOL20 >= 2.0, rank_rvol20 <= 20 (rank inside the day's U0, 1 = highest), daily ATR(14) >= $0.50.
- OR15 = 09:30-09:44 high / low; candle = 09:30 open vs 09:44 close. Up candle -> buy-stop OR15 high + $0.01;
  down candle -> sell-stop OR15 low - $0.01; doji (close == open) -> no trade. Shorts: ETB only (book rule, >= 90%
  of snapshots) and never inverse / volatility funds.
- Order placed at the 09:49 bar close (RVOL20 needs 09:30-09:49 volume), working on the 09:50..11:29 bars.
- Stop = trigger -/+ 0.10 x ATR, never beyond the far side of OR15. Target = 2R from the trigger price.
  Breakeven stop once the trade has gone +1R (from the next bar). Otherwise flat at the 15:55 open. One trade per
  symbol-day.

### Plainest readings chosen where the spec is ambiguous (noted)
1. RVOL20 = 09:30-09:49 volume / mean of the same window over the prior **14** sessions (DESIGN global convention;
   the "20" names the 20-minute window). Sessions older than 30 calendar days are not used; >= 5 needed. So the first
   ~5 sessions after the locked block (early March 2025) have no RVOL and no trades (the lock gap, not a rule).
2. "Price" for the price filters = 09:49 close. ETFs stay in U0 (the spec says stocks/ETFs).
3. Stop and target are fixed prices set from the trigger at order time (the live `Signal` contract,
   mcf.strategies.base: `entry_type="stop"`, `stop`, `target`, `be_at_r=1`). A stop already through at 09:50 fills
   at the bar open (mcf.backtest.engine semantics); R is then measured on the fill, so the trade's real R is larger
   and the 2R target is nearer than 2R. A fill at or beyond the target is skipped (engine rule).
4. ATR / ADV20 on T1 = the lab frames' point-in-time `atr_d` / `adv20` (as bench10). T2: same formulas from
   data/cache_fresh 1-minute bars (ATR = 14-session mean true range, min 10, through the prior close).

## Engine ("normal way", research/ultimate_1119/top10/bench10.py components)
- 1-minute walk from the fill bar: stop first (on the entry bar the stop is checked against the bar's low/high, as
  mcf.backtest.engine; later bars fill at the worse of open/stop on a gap-through), target only when traded through
  by >= $0.01, BE from the next bar, flat at 15:55 open.
- Costs bench10.add_r (LR8: entry (1c + 1bp) x tod mult at the fill bar's close time, exit 1c + 1bp except target
  limit fills, +2c on stops incl. breakeven stops, x3 extended tier, shorts +1.2 bp borrow).
- Book bench10.book under testing rules (TESTING_RULES: cap 100, <= 3 lots / symbol, price >= $5, ETB shorts,
  stop-cost filter 0.15R, no latch) — the destination-account view of PLAN.md (top10).
- Universe = the cache's symbols: T1 1,226 (data/cache_hist), T2 469 (data/cache_fresh, reference only). Live has
  ~4,200 names, so rank_rvol20 <= 20 is a rank inside a much smaller universe (stated bias).

## Tests and scoring
- FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions); CHECK = 2025-10-01..2026-11-04 (276), scored ONCE for the
  base and ONCE for the fit-picked tweak; T2 2023-01-03..2024-09-13 reference.
- Per test: trades, /session, win, avg R, avg R w/o best day + best-day share, total R/session, worst day, day-clustered
  t, SPY day-type split, vs random entries (same symbol-day and side, a random fill minute in 09:50..11:29 at that
  bar's open, same $ risk, same 2R target / BE / 15:55 exit, same costs and book; 5 seeds averaged).
- Tier vs the top-10 standard (top10/PLAN.md): MEETS = all of T1 combined avg R >= -0.0383, T1 check avg R >= -0.0464,
  w/o best day >= -0.0674 / -0.0781, total R/session >= -0.4862 / -0.5218, T2 avg R >= -0.1048, >= 20 trades on check
  and T2. NEAR = every failed avg-R / w/o-best-day threshold missed by <= 0.02R (and R/session criteria within 0.02R/
  session). Else FAIL.

## Tweaks (step 3)
At most 3 one-part tweaks, chosen from a FIT-only diagnosis of the base's worst losers and appended below BEFORE any
tweak is scored. The best on FIT (avg R, with avg R w/o best day as tie-break; must keep >= 20 FIT trades) is scored
once on CHECK and T2. Configurations counted: base 1 + tweaks <= 3.

## Addendum 1 (2026-11-20, after the BASE FIT score and FIT-only diagnosis; before any tweak is scored; CHECK unread)
Base FIT (testing book): 556 trades, avg R -0.384, w/o best day -0.392, day-t -9.6; random entries on the same
symbol-days and sides -0.101. Diagnosis of the worst losers (diag.py, FIT only): all 55 worst-decile trades are full
stops; 78% of all stops come within 5 minutes (36% on the entry bar itself) and 67% of stopped trades later reach the
2R target the same day. The 0.10 x ATR stop is a few cents inside the breakout bar's noise: the **stop** is the part
that fails. Entry timing is secondary (fills after 10:15 average about -0.66R vs -0.34R at 09:50-09:59); filters
(rank, RVOL, ATR) show no clear slope.
Pre-registered one-part tweaks (everything else exactly the base):
- **TW-a stop25**: stop 0.25 x ATR from the trigger (was 0.10), still never beyond the far side of OR15.
- **TW-b stopOR**: stop = the far side of OR15 (the classic ORB stop; the 0.10 x ATR leg dropped).
- **TW-c until1015**: the order works 09:50..10:14 only (was ..11:29).
Pick = best FIT avg R (tie-break avg R w/o best day; >= 20 FIT trades). Only the pick is scored on CHECK, once.
Configurations: 1 base + 3 tweaks = 4.
