# rdt1030 / F3 orb5-be-2max: pre-declaration

*Educational only — not financial advice.*

Written 2026-10-30, **before any configuration is scored**. No outcome column has been read. Research only: no config/,
mcf/, ledger or backlog writes; nothing is committed.

Source: the owner's Reddit post of 2026-10-30, idea (4): the poster's backtest label
"NQ - BE / context / 5min / 2 trades / 30 points 2R / more 1R". Design: `../DESIGN.md` sections 0 and F3; the table below
is copied from it unchanged.

## Rule (F3-A)
- **OR5:** ORH / ORL = high / low of the 0935 head row (09:30-09:35). The 0935, 0940 and 0945 head rows must all be present
  (DESIGN 0.1), and OR5 width >= 0.05 ATR_d.
- **Fresh break (trade 1):** per side, the first row after 0935 whose close is beyond ORH (long) / ORL (short).
- **Signal at row i (F1-A's FVG entry on OR5):** a bullish 5-min FVG completes at row i (rows i-2, i-1, i consecutive;
  `low[i] - high[i-2] >= 0.05 ATR_d` and >= $0.02), the break is at row i-1 or i, and `close[i] > ORH`. Shorts mirror.
  Only the first FVG candidate of a break is considered; if it fails a gate (window, universe, risk guard, context) that
  break is finished.
- **Window:** signal rows 0950-1100. A break at 0940 whose FVG would complete at 0945 is before the window and is lost
  (literal port of F1-A's "the break must form the gap" with the DESIGN window).
- **Trade 1** = the earlier of the long and short candidates that pass all gates.
- **Entry** `close[i]`; **stop** `low[i-2]` (long) / `high[i-2]` (short), no buffer; **risk guard** 0.03 <= R/ATR_d <= 1.0.
- **Target:** 2R if R <= 0.085 ATR_d, else 1R. **Break-even:** stop to entry once MFE >= +1R (`be = 1.0`; effective only
  on 2R trades). Flat 15:55.
- **Context gate:** `qqq_fo > 0` (long) / `< 0` (short) at the signal row (lab context table, same date and tod).
- **Trade 2 (max 2 per symbol-day):** signal row strictly after trade 1's exit row (sim `xrow`; an exit in the 15:05+ tail
  rows ends the day). It needs a close back inside the OR (ORL <= close <= ORH) after trade 1's break, then a new close
  beyond either OR side (the next close beyond after an inside close), whose first FVG candidate (break row or the next
  row, close still beyond) passes the same gates. Each new break gets one chance; another inside close re-arms. Trade 2
  may be on either side.
- **Side attribution:** every trade (1 or 2) is attributed to its own side. The `-L` row of a config holds that system's
  long trades, the `-S` row its short trades. A descriptive "both sides" line and a trade-1 / trade-2 split are reported
  but are not extra configs.
- **Universe:** adv20 >= $95M and atr_d > 0 on the signal row.

## Configurations (18 counted: 9 rows × long / short)
| row | change from F3-A | plain-English name |
|---|---|---|
| F3-A | as above | 5-min Opening Range Break with Gap, break-even, 2 tries, QQQ context |
| F3-B | no context gate | ... no index context |
| F3-C | BE at +0.5R (also acts on 1R trades) | ... earlier break-even (+0.5R) |
| F3-D | max 1 trade per symbol-day | ... one try only |
| F3-E | stop after a win: trade 2 only if trade 1 lost (r < 0) | ... second try only after a loss |
| F3-F | 2R switch at R <= 0.20 ATR_d | ... 2R on tight stops (<= 0.20 ATR) |
| F3-G | always 2R with BE at +1R | ... fixed 2R target |
| F3-H | window extended to 1500 | ... all-day window |
| F3-I | context = SPY on the trade side of its VWAP (SPY `vwapDistPct` > 0 / < 0) instead of QQQ from open | ... SPY-VWAP context |

## Harness
- Frames, splits and `_cut` monkeypatches/asserts copied from `../F1/build.py` (which copies pdl1030/combo/build.py).
  TRAIN = 2024-10, 2025-03..12; VALID = 2026-01..03, 2026-07..2026-09-15. Locked block and HOLD months never loaded.
- Simulator: the F1 numba copy of the top5_1028 `sim` with the DESIGN 0.2 patches (per-trade R and target multiple, 1c+1bp
  entry × ToD multiplier, 1c+1bp on every exit, +2c on stop / moved-stop exits, ×3 extended tier, gap-through stop fill),
  plus the unchanged `be` logic (stop to entry from the bar after MFE reaches `be`). F1 already proved the copy equals
  `scan_1028.sim` with patches off; F3 re-runs that check (`build.py check`) before scoring. Harness parity (F4-18,
  CWT14 p05 = -0.0677R) was passed by F2 on the same frames/splits.
- Random control: per trade, 5 random other universe symbols at the same signal row (seed 20261030), same side, R in ATR
  units, target multiple and `be`, same sim and costs.

## Sanity check before scoring
F3-B (no gate) trade-1 count per session, the share of first breaks lost to the 0945 rule, the trade-2 share, median
R/ATR_d and median cost/R are printed **before** any R column is read, and compared with DESIGN 0.4 (OR5 median width 0.33
ATR; F1-A ~140 trades/session per side; median cost/R 0.05-0.11).

## Bar (BAR90, rules 21-22)
N = 2,000 + 108 (swarm pre-declared) + rework rows declared by the swarm so far (F1 6, F2 6) + any F3 rework; t_req =
0.9 × sqrt(2 ln N) ≈ 3.52. A row passes only if: day-clustered t >= t_req; `gates.walk_forward` share >= 54%; avg R > 0 on
TRAIN and VALID separately; >= 3 trades/session; avg R > 0 on SPY up and down days; avg R above the random control.

Reported for every row: n, trades/session, win rate, avg win / avg loss in R and ratio, TRAIN/VALID/all avg R and day t,
WF share, up/flat/down-day R, avg R without the best day and its share, busiest-session share, median cost/R, exit mix
(target / stop / BE / 15:55), control avg R, trade-2 share.

## Live-support check (DESIGN)
`mcf/execution/runner.py` has `live.same_setup_reentry` (default true, owner 2026-10-14): a setup may re-enter a symbol on
a later decision bar. A **per-setup cap of 2 per symbol-day** and the "close back inside first" re-arm would still need to be
encoded in the mask itself. Checked only if a row passes.

## Rework (rule 18)
Only after a row fails, as new counted rows declared below as a dated amendment before they are scored.

## Sanity check result (2025-06, printed before any R column was read)
F3-B trade 1: 110 long / 99 short per session; trade 2: 4.8 / 2.8 per session. F3-A (QQQ gate): 91 long / 31 short trade-1
per session in that month. Median R/ATR_d 0.31-0.34, median cost/R 0.060-0.066, 2R share 0.1-0.2% (literal switch), median
signal time 10:00-10:05. OR5 median width 0.33 ATR (DESIGN 0.4: 0.33). 4,202 first long breaks happened at 09:40 and are lost
to the window rule, as declared. Counts are in line with F1-A (~140 per side per session on OR15).

## Amendment 2026-10-30 (rework, rule 18; declared after all 18 rows failed, before any of these is scored)
All 18 rows failed (best: F3-G-S fixed 2R short, VALID +0.008R but TRAIN -0.086R; every long row lost ~0.38R on SPY down
days despite the QQQ gate). Gross R ≈ 0 on every row. Three rework rows (6 counted configs) are declared; N = 2,000 + 108 +
12 (F1/F2 rework) + 6 = 2,126, t_req 3.53.

| row | change | plain-English name |
|---|---|---|
| F3-RW1 | F3-G (fixed 2R, BE +1R) + round-trip cost <= 10% of R (F1 cost-floor gradient; one condition added) | 5-min ORB with Gap, 2R target, low-cost only |
| F3-RW2 | F3-A with a stronger QQQ gate: `qqq_fo` >= +0.30% / <= -0.30% (neighbour) | 5-min ORB with Gap, BE, 2 tries, strong QQQ trend |
| F3-RW3 | F3-A + F3-I together: QQQ from open and SPY VWAP side both on the trade side (one condition added) | 5-min ORB with Gap, BE, 2 tries, QQQ and SPY-VWAP agree |
