# C3FR — friction rework of COMBO1 C3 LAG-OF-SCAN (Builder, pre-declared 2026-11-09 ~08:30 ET, before any score)

*Educational only — not financial advice.*

## Why this idea
COMBO1 C3 (research/bdi/combo1, MCF branch) is the best near-miss on the books for "find the move beforehand": the
laggard of a residual-correlation peer group whose peers (>= 2 of them in the 09:35 volume scan) already moved
>= 0.40 ATR the same way. It picks names: day-matched excess vs a random U name +0.096R (t 2.32), gross +0.083R. It
failed only because friction (0.16-0.23R per trade) is 2-10x the gross edge — R = 0.25 x daily ATR is tiny next to
the opening spread and slippage. Targeted remedy (CLAUDE.md "Remedies"): same signal, a wider R so the fixed $ costs
are a smaller share of R, and an early time exit so the trade holds only the catch-up phase. Nothing else changes.

## Frozen signal (unchanged from combo1.py C3)
U = top 500 by adv20 x ATR% (adv20 >= $95M); S = top 150 of U by 09:30-09:35 $ volume / adv20; >= 2 of the name's
top-10 residual-correlation peers in S (120-session window ending before the month); peer median ex-market move
side x P >= 0.40 ATR, agreement >= 0.7; own side x z < side x P / 2; signal bar close 09:40..09:50 against the side;
side = sign(P); first per symbol-day; earnings blackout; index ETFs excluded.

## Grid (6 new configs; lineage N = 15 + 6 = 21)
| R width (x daily ATR) | exit |
|---|---|
| 0.50 / 0.75 / 1.00 | **B**: -1R stop / +1R target bracket, flat 15:55 |
| 0.50 / 0.75 / 1.00 | **T**: -1R stop, else out at the 11:00 bar close |

Execution (stricter than the parent): entry at the **next** 5-minute bar's open (from the 1-minute SIP cache);
stop-first inside a bar; a bar opening through the stop fills at its open; targets fill at the target (no gap gain).
Costs = combo1's friction formula unchanged: production slippage (1c + 1 bp) x opening tod multiplier on entry +
4.4 bp spread x multiplier, stop exits +1c +1bp +2c, time exits 1c + 1 bp, target exits 0; **floor 0.10R per trade
kept** (it binds at R = 1 ATR — reported honestly; a no-floor number is shown for information only, never for a pass).
Anchor (not a new config): the parent's R 0.25 bracket re-scored on the new data so the comparison is like-for-like.

## Data
Two-year SIP 1-minute cache rebuilt per research/bdi/1104/DATA.md (MCF branch) — **after 16:00 ET** so the live job's
Alpaca rate budget is untouched. Locked block 2024-11-01..2025-02-28 dropped at read (asserted), never read.
TRAIN <= 2025-09-30 < VALID (same split as COMBO1).

## Pass bar (fixed now)
BAR90 (rule 22): day-clustered t >= 0.9 x max(1.5, sqrt(2 ln 21)) = **2.22**; TRAIN and VALID avg R > 0; up AND down
SPY days > 0; walk-forward positive months >= 54%; day-matched excess vs random U names (same bar, side, R, exit) > 0;
avg R without the best day > 0 (flag best-day share >= 50%); >= 1.5 trades/session in TRAIN and VALID (rule 21 lane).
Reported for every config: n, /session, avg R, t, w/o best day + share, TRAIN/VALID, SPY up/down/quiet (o-c +-0.25%),
WF+, vs random, mean friction, plateau (neighbour R widths). A pass goes to Skeptic, then Lead for the locked block.

## Honest prior
Wider R lowers friction in R about 2-4x but also shrinks the gross edge measured in R; the catch-up move has to be
worth > ~0.1 ATR net for this to work. Expect 0-1 passes; the frequency gate (2.1/session overall, 1.25 in TRAIN) is
the likeliest failure, not the edge.
