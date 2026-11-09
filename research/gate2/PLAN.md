# GATE2 — trade WITH the held side on pullbacks (Builder, pre-registered 2026-11-09 ~08:15 ET, before any score)

*Educational only — not financial advice.* Owner queue item GATE2 (research/queue.jsonl, 2026-11-05); Lead request
lead-20261109-0758-2; Skeptic pre-attack skeptic-20261109-0846-5 answered point by point below. Research only.

## The fact we build on (research/bdi/gate1/NOTES.md, COMPASS)
Once SPY is >= 0.30% from its open at a checkpoint from 10:30, it closes on that side of its open 89 / 89 / 97%
(TRAIN / VALID / live). Direction *from here* is a coin flip. So the edge, if any, must come from "a pullback toward
the open does not cross it" — a defined risk (stop just beyond the open) with the close expected on the held side.

## Rule (frozen)
- **Reading:** at each 5-minute bar close from 10:30 to 13:00 ET, SPY % from its open `fo` (bar close, point-in-time).
  The first bar with |fo| >= X sets the held side s = sign(fo) and the confirmation time Tc. One reading per day.
- **Instruments:** (I-ETF) SPY, QQQ, IWM; (I-HB) U names (top 500 by adv20 x ATR%, adv20 >= $95M, index ETFs and
  earnings blackout excluded) with 60-session daily beta to SPY >= 1.2 (window ending the day before).
- **Pullback trigger** (bars after Tc, closes 10:35..14:30): the instrument's own move from ITS open in direction s,
  M = s x (extreme-so-far - open), has M >= 0.25 ATR_d; price has retraced >= RET x M from that extreme; price is still
  on the held side of its own open (s x fo_own > 0). First trigger per instrument-day.
- **Entry** next 5-minute bar open (bars from the 1-minute SIP cache). **Stop** = own open - s x 0.10 ATR_d (stop-first
  in a bar; gap through fills at the bar open). R = |entry - stop|; skip if R < 0.10 ATR_d. **Exit** 15:55 close (E1),
  or E2: a breakeven-then-trail (after +1R, stop to entry; after +2R, trail 1R behind the best close).
- **Costs:** production (gates.py: 1c + 1 bp per side x tod multiplier, stop +2c) + 4.4 bp spread on entry, I-HB;
  I-ETF same formula (conservative for SPY/QQQ/IWM). No floor.

## Grid (8 setup configs + 3 sizing configs = 11)
| | X (SPY |fo|) | RET | exit |
|---|---|---|---|
| I-ETF, I-HB | 0.30 / 0.50 | 0.40 | E1 |
| I-ETF, I-HB | 0.30 | 0.60 | E1 |
| I-ETF, I-HB | 0.30 | 0.40 | E2 |
= 4 per instrument set x 2 = 8. Plus **sizing-by-reading** of the GATE1 near-miss combos (phase 2, same reading,
X 0.30): L3-gap-slope-fromopen-FD shorts x1.5 in UP / x0.5 otherwise; ST7-FD longs x1.5 in DOWN / x0.5 otherwise;
NM-AR longs x1.5 in DOWN / x0.5 otherwise (2-year lab trade lists, research/history2y/data/bt_lab1104) = 3.

**Try count:** GATE2 grows out of GATE1's compass (112 looks), so the lineage is counted together:
N = 112 + 11 = **123 → full bar 3.10, BAR90 2.79**. (As a new lineage alone N 11: 2.19 / 1.97 — shown, never used.)

## Pass bar (per config, fixed now)
Day-clustered t of avg R >= 2.79 **and** day-clustered t of the excess over the **no-pullback control** >= 2.79
(Skeptic f); TRAIN and VALID avg R > 0; avg R > 0 on SPY up AND down days (o-c +-0.25%) and reported on quiet;
walk-forward positive months >= 54%; avg R w/o best day > 0, best-day share flagged at >= 50%; worst day R reported;
>= 1.5 trades/session (I-HB) — I-ETF is a 0-3/day sleeve, judged on t and controls only. Sizing configs: weighted
book minus unweighted book, day-clustered t >= 2.79, kept trades 100% (sizing removes nothing).

## Controls
(C1) **no-pullback control:** same instrument, same day, same side, entry at a uniformly random bar between Tc and
14:30 (seed 20261109), same stop rule and exit — isolates the pullback timing. (C2) **same-minute random names:**
same side, same entry minute, random U names (I-HB) — isolates the stock pick from the SPY direction. (C3) days
with no reading are not traded and are listed (count) so the trade-day mix is visible.

## Skeptic's pre-attack (skeptic-20261109-0846-5), answered by design
(a) reading = closed bars only; entries at the next bar. (b) the close is never used to pick or label a trade; the
"held" rate is not an input. (c) R is the instrument's own R, stop at its own open. (d) report R and worst-day R, not
hit rate. (e) all t are day-clustered. (f) control C1 above. Burst times (Observer) will be tagged in the output.

## Data / windows
2-year SIP 1-minute cache rebuilt per research/bdi/1104/DATA.md, **after 16:00 ET** (live job's Alpaca rate budget);
TRAIN 2024-10 + 2025-03..2025-09, VALID 2025-10..2026-11-06; the live-window sub-period 2026-10-06..11-06 shown
separately. Locked block 2024-11-01..2025-02-28 dropped at read, asserted, never read.
