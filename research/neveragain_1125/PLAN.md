Educational only — not financial advice.

# NEVERAGAIN pre-registration (written 2026-11-25 ~17:55 UTC, before any configuration below was scored)

Owner 11-25 (Primary halted at -20R; 12:20 ET -24.5R closed + -12.8R open): "A day like today simply cannot happen.
Explore ways of making sure this doesn't happen again... our goal of being positive every single day."
Failure mode: gap-down shorts (L3-gap-slope-fromopen-FD 13 lots open at once, ~25 names; a few RW3) squeezed together
as SPY (~+0.7% from open) and IWM (~+1.2%) rallied 11:50-12:10 ET. The -2R per-setup latch counts CLOSED R only, so
L3 kept entering while open losses grew; the -20R halt stopped new entries, open lots ran to their own stops.
Research only: no config, ledger, setup or account change; nothing committed.

## Engine (bench)
s8cap/hsscale minute-by-minute book engine (s8sim.py logic), Primary book: price >= $5, shorts ETB >= 0.9, 30 open lots
per setup, <= 3 lots per symbol per setup, 77 slots, burst brake 30 / 10 min per setup, sticky -2R CLOSED per-setup
latch (as live risk.py: never undone), -20R no-new-entries halt on closed + open. Point in time: entries in minute m see
state at the end of minute m-1 (index guard uses closes up to m-1).
Candidate lots: the bench10 per-setup trade lists are no longer on disk (pyramid/L1, L2 work files deleted), so the
candidate universe = union of pyramid/R3B/booked.parquet rows for the 4 Primary setups booked under (a) testing rules
(cap 100, no latch, stop-cost filter 0.15) and (b) Primary home rules (cap 30, -2R latch, no cost filter), deduped by
setup/symbol/date/tod/side. Disclosed limitation: candidates that are BOTH stop-cost > 0.15 AND after the RAW -2R latch
are missing (NOW blocks them anyway on RAW; on NEUTRAL/P10 books the latch could fire later). Final R = bench cost R
(B.add_r); open mark = side x (minute close - entry) / risk - (r_gross - r) of the lot. Minute closes from cache_hist
(>= 2024-09-16) and cache_fresh (T2). Lineup P4 = today's Primary (L3-fromopen, RW3, RW5, NM-ETF).
Periods: T2 2023-01-03..2024-09-13, FIT 2024-10 + 2025-03..09, CHECK 2025-10-01..2026-11-04. Locked block
2024-11-01..2025-02-28 never read (asserted). First 120 sessions = warm-up for the scaled account stop, not scored for
any configuration (one shared scored set).

## Guards (8 candidates) — each = NOW + guard
| id | guard |
|---|---|
| G1-2 | per-setup sticky latch on CLOSED + OPEN R: at the end of minute m, if setup s closed + open cost-R today <= -2R, s takes no new entries for the rest of the day (open lots keep their own exits) |
| G1-3 | same at -3R |
| G2-6 | per-setup cap of 6 concurrent open lots (RISK cap — not a playing-time/starvation throttle; labelled as such) |
| G3 | squeeze guard, gap-down short family only (P4: L3-fromopen, RW3, RW5; live also RW7/L3-* variants): no NEW entry at minute m if SPY and IWM are BOTH >= +0.50% above their 09:30 session open at the close of m-1 AND both closes at m-1 are above their closes at m-31 (no block before 10:01). Re-evaluated each minute (not sticky). |
| G3-L | same with +0.30% |
| G4 | HS-SCALE account stop: SCALED-K4 (at account closed + open <= -X: flatten all lots, no entries rest of day; X = clip(4 sigma, 2.5N, 8N), sigma = std of the configuration's own simulated daily closed R over trailing <= 250 sessions, min 120, recomputed each ISO week) + fixed -20R no-new halt (s8cap side finding). SHOCK-V reported on the live minute curve only (alert layer). |
| G5a | G4 + the best of {G1-2, G1-3, G2-6, G3, G3-L} |
| G5b | G4 + the best two from DIFFERENT families (G1 / G2 / G3) |
G5 selection rule (fixed now): rank the five single guards by day-clustered t of NEUTRAL daily dR vs NOW over FIT + T2
only (P4). CHECK and live are then the out-of-sample look for G5.
References (not candidates): NOW (live rules today), and a G3 PLACEBO: G3 with each day's SPY/IWM minute paths replaced
by those of a random other bench day (20 draws, seed 1125), NEUTRAL book — G3 must beat the placebo 90th percentile, so
"blocks some gap-down shorts on some afternoons" is not mistaken for index information.
Configurations counted: 8 candidates. Bar sqrt(2 ln 8) = 2.04 -> t >= 2.0; lineage with hardstop_1123 / hsscale /
capfit / s8cap / rules_1122 / regime_switch is ~110+ configs -> ~3.0 (stated descriptively).

## Books (trading less != skill)
RAW = bench costs. NEUTRAL = every lot of setup s shifted by -a_s (a_s = s's avg R per lot under NOW RAW over scored
sessions), drift removed linearly over the holding time for open marks (as s8cap). P10 = shift a_s - 0.10 (every setup
earns +0.10R / lot). Each book fully re-simulated (latch, guards and account stop see the repriced R).

## Metrics (P4 x config x book; FIT / T2 / CHECK / pooled), vs NOW on the same book
dR, dR/yr, worst day, avg worst-5 days, days <= -10R, red days, day-clustered t of daily dR, days turned red->green and
green->red, lots entered, guard fires/yr, per-setup dR (better / worse, sums; Remedies rule).

## Live replay (Primary 2026-10-06..2026-11-25; journals, LR8 cost-R)
Lots = Primary journal trades (run_id 1). Minute closes by Alpaca GET (SIP 1-min) for every Primary symbol-day + SPY and
IWM. LIVE-NOW = actual trades with the sticky -2R closed latch and -20R closed+open halt applied as a what-if on every
day (equals the live rule since 10-29). Guards applied on top (they only remove lots / flatten; blocked actual trades
cannot be added back). X live = clip(4 sigma_acct, 2.5N, 8N), N = distinct setups Primary traded that day, sigma from
prior replayed Primary days (>= 10, else 8N). Reported: total R, worst day, worst-5, days red->green / green->red,
per-setup dR, today's minute curve with when/where each guard fires, SHOCK-V fires. Today: data through the latest
journal poll if the session is not finished (noted); re-pulled after 16:00 ET if still running. Also reported: all
other accounts' gap-down-short lots under G3 (closed-R only, descriptive).

## Pass bar (fixed now). A candidate PASSES if all hold:
1. NEUTRAL dR vs NOW > 0 in each of FIT, T2, CHECK.
2. Pooled NEUTRAL day-clustered t >= 2.0.
3. P10 pooled dR >= 0 (a guard that loses on a profitable book is mainly "trading less").
4. RAW worst day and avg worst-5 not worse than NOW in any period.
5. No setup worse by > 10R (NEUTRAL, pooled).
6. Live Primary RAW total not worse than LIVE-NOW, and live worst day not worse.
7. G3 / G3-L only: NEUTRAL pooled dR above the placebo 90th percentile.
INSURANCE class: fails 1-3 but passes 4 and 6 with NEUTRAL cost <= 30R/yr -> may be offered as insurance, labelled.
EMERGENCY (same-week) candidate only if: passes all 7 with t >= 3.0 and P10 dR > 0 in every period. Otherwise the
report says plainly that nothing qualifies as an emergency rule.
Pick for the Friday 11-27 package: the passing candidate (else best insurance) with the highest pooled NEUTRAL dR/yr;
ties within 10% -> fewer fires.

## "Positive every single day" (descriptive)
Daily R distribution of live Primary (10-06..11-25) and of the bench P4 book (RAW / NEUTRAL / P10; NOW and the pick):
share of red days, percentiles, worst-5; and the per-lot edge e that would make the share of red days <= 20% / <= 10%
(every lot shifted by +e, re-simulated), so the owner sees a realistic target (e.g. red days capped at about -X R).
