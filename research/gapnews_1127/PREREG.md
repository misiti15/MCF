# GAPNEWS_1127 pre-registration (written 2026-11-27 evening, before any feature, rule or setup below was built or scored)

**Educational only — not financial advice.** Research only: no change to config/, setups, exits, assignments.json,
decisions.json or the ledger.

## Question
MOVEHUNT_1127 showed the frozen K6 logit ranks the day's big after-09:50 movers at 09:50 (capture@50 lift 4.9 CHECK /
3.1 T2) but has no direction skill (continuation hit 49%). Is direction predictable *inside* the K6 high-mover list from
information available at 09:50: gap direction x first-20-minute continuation/reversal, opening-range position,
relative strength vs a sector ETF, prior-day close location, first-bar volume profile, prior multi-day trend? If not, is
a direction-neutral stock-only structure (OCO bracket on the 09:30-09:49 range) tradeable after costs?

## Data, splits, list (frozen, no look-ahead)
Same data, eligibility and K6 definition as research/movehunt_1127 (PREREG + build.py + score.py): 1-min RTH bars,
data/cache_hist (FIT/CHECK) and data/cache_fresh (T2/EARLY); P50 = 09:49 bar close; price >= $5, adv20 >= $20M, ATR14,
>= 15 of 20 opening bars. K6 = logistic regression on the 8 MOVEHUNT features, fit on FIT only with the identical code
(coefficients must reproduce results.json logit_coef to 3 dp, asserted), applied unchanged to all days. List = K6 top-20
(setups) and top-50 (direction screen) per day.
Splits: FIT 2024-10 + 2025-03..2025-09; CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13; EARLY 2022-10..2022-12
(after warm-up; extra out-of-sample, reported). Locked block 2024-11-01..2025-02-28 NEVER read (pyarrow filter + asserts).
Shorts need easy_to_borrow (data/universe.csv snapshot, not point-in-time — disclosed).

## Direction features at 09:50 (bars closed by 09:49 and prior days only)
gap_s = open/prev_close - 1; D = sign(P50 - open); orpos = (P50 - L20)/(H20 - L20); rs_sec = r20 - r20 of the stock's
sector ETF, ETF = the one of XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH XBI KRE with the highest correlation of
daily close-to-close returns over the prior 60 sessions (point-in-time, no sector map exists in the repo); pcl = prior-day
close location (C - L)/(H - L); vwap side = P50 - VWAP(09:30-09:49); vimb = (volume of up bars - volume of down bars) /
volume, 09:30-09:49; r5 / r20d = prior 5 / 20 session close-to-close return (ending yesterday).

## Direction screen (13 configurations; scored on the K6 top-50 list, top-20 reported)
Target y = s x (C_last - P50)/ATR14 (the remaining move after 09:50, signed by the rule's call s); also hit rate.
R1 GAP sign(gap_s) · R2 CONT D · R3 GAPGO D where sign(gap)=D only · R4 GAPREV D where sign(gap)!=D only · R5 ORPOS
sign(orpos-0.5) · R6 RSSEC sign(rs_sec) · R7 PDCL sign(pcl-0.5) · R8 VWAP sign(P50-VWAP20) · R9 VIMB sign(vimb) · R10 TR5
sign(r5) · R11 TR20 sign(r20d) · R12 VOTE sign(sum of R1,R2,R5..R11) · R13 DLOGIT = logistic regression of
up = (C_last > P50) on the signed continuous features (gap_s/atr%, (P50-open)/ATR, orpos-0.5, rs_sec/atr%, pcl-0.5,
(P50-VWAP20)/ATR, vimb, r5/atr%, r20d/atr%, sign(gap)*D), fit on the FIT top-50 list only, frozen; call = sign(p - 0.5).
Each rule's orientation (follow or fade) is fixed by the sign of its FIT mean y; CHECK/T2/EARLY are scored with that
orientation. Descriptive "direction skill" bar: oriented mean y > 0 with day-clustered t >= 3.0 on CHECK and >= 2.0 on T2.

## Setups (3 directional + 2 neutral = 5 configurations), K6 top-20 list, entry at the 09:50 bar open
Time exit at the 15:55 bar close (last bar on half days); stop on 1-min high/low, stop-first, a bar opening through the
stop fills at its open; 1R = |entry - stop| >= 0.10% of price.
X1 range stop: long stop = min(L20, entry - 0.10 ATR) - $0.01; short = max(H20, entry + 0.10 ATR) + $0.01.
X2 ATR stop: entry -/+ 0.50 ATR.
SA = the single rule among R1..R11 with the largest FIT |t| (oriented), exit X1.
SB = R13 DLOGIT, exit X1.
SC = R13 DLOGIT, only names whose |p - 0.5| is in the top third of the FIT top-20 distribution (threshold frozen on FIT), exit X2.
N1 = OCO bracket: buy-stop H20 + $0.01 / sell-stop L20 - $0.01, live 09:50-11:29, first trigger wins (fill at the
trigger or the bar open if it opened beyond), the other side cancelled; stop = 20-min range midpoint; stop is checked on
the entry bar too (conservative); both triggered in one bar = scored as a -1R stop-out. N2 = the same with the stop at
the opposite range extreme. N1/N2 are scored regardless of the screen, but are only eligible to pass if no directional
setup passes (they answer "direction still ~coin flip").
Long and short sides are reported separately but the pass is judged on the combined setup only (no side picked later).

## Costs (always in)
LIVE-L (research/primshorts_1126/cells_live.json via calib_live.predict_R; scored basis) and LR8 research (1c + 1bp per
side x time-of-day multiplier, 3x tier for price < $5 or |gap| >= 20%, 2c extra on stops, 1.2 bp borrow on shorts),
exactly as MOVEHUNT score.py.

## Pass bar (per setup; all must hold)
Configurations this study: 13 + 5 = 18. Bonferroni one-sided 0.05/18 -> z = 2.77, rounded up:
1. avg R > 0 at LIVE-L and LR8 on CHECK and on T2; EARLY > 0 at LIVE-L if it has >= 30 trades.
2. Day-clustered t >= 3.0 on CHECK and >= 2.0 on T2 (LIVE-L). Lineage claim (cumulative N ~9,176 -> ~9,194) needs t >= 4.3.
3. One-big-day: avg R without the best day > 0 and best-day share < 50% on CHECK and T2.
4. Controls (LIVE-L): (a) random-direction control = same names and exit, side = coin flip (exact expectation =
   mean of the long and short outcome per name): setup - control > 0 with paired day t >= 2.0 on CHECK and > 0 on T2;
   (b) size-matched random names (eligible, not in list, same rule) reported. Neutral N1/N2 use (b) only.
5. Stress: +1 minute entry (09:51 open; for N1/N2 the bar after the trigger) and +2 bp per side extra cost: avg R > 0
   on CHECK and T2 under each stress.
6. Effect report: results split long/short, gap >= 1 ATR% vs not, price bucket — cells positive / negative and by how much.
FIT is reported, never used to tune after this file. No live trades of these rules exist, so no live window and no ledger
overlap; any live figure quoted gets its ledger rule changes noted.

## Count
18 configurations. Cumulative N ~9,176 -> ~9,194.
Educational only — not financial advice.
