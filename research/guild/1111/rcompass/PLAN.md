# RCOMPASS — rolling compass: put afternoon setups on standby when the morning condition flips (Scout plan, FROZEN 2026-11-09 23:30 ET, before any data)

*Educational only — not financial advice. Research only; nothing switches anything live. Owner focus 2026-11-10 (P1, Lead
lead-20261109-2300-1/-3); Skeptic's guards skeptic-20261109-2251-2 written in below before any look.*

## Question
When the morning market condition flips midday, do the setups that open in the afternoon on the *earlier* condition do worse
than the same setups on days the condition held — by more than a random standby of equal size would show, and by more than
"down afternoons are bad for longs" explains? Coil family first (CWT12-coil-k4-long, CWT12-coil-k6-long; Graveyard), then
every family that trades after 12:00 (per-family better/worse, Remedies rule).

## Data (Builder's backfill, audited by Skeptic first — I wait until the live-match rate is >= 95% per field)
- Compass table (date, mark T 09:45..15:45, spy_fo, spy_vwap side, breadth_open, w60, c30, checkpoint, gate1_state),
  backfilled from SPY/QQQ/IWM + Hunch-200 1-min bars with mcf/report/compass_live.py logic, point-in-time (bars that START
  before the mark), **locked block 2024-11-01..2025-02-28 excluded and asserted.**
- 2-year lab trade lists (research/history2y/data/bt_lab1104 + coil lists), each trade tagged with the compass state at the
  last mark at or before its signal-bar close and at every earlier mark that day. Gross R and net R (production costs).

## Morning reading (fixed now)
A day has a **confirmed morning reading** M in {UP, DOWN} when the 30-min checkpoint state is UP / DOWN at the 10:30 or
11:00 checkpoint (|SPY from open| >= 0.30%; first one counts). Days without one are reported as "no morning reading" and
are not part of the flip test.

## Flip definitions (3 pre-declared looks, each counted; each known AT its flip time, never from the close — Guard 1)
- **F1 open-cross:** at a 15-min mark >= 11:15, SPY's % from open is on the opposite side of M.
- **F2 W60 reversal:** at a mark >= 11:15, the W60 rolling compass is confirmed (|level| = 2) on the side opposite M.
- **F3 GATE1 change:** at a 30-min checkpoint >= 11:30, gate1_state differs from M (UP -> DOWN/MIXED or DOWN -> UP/MIXED).
Flip time T_f = the first such mark. A trade is **post-flip** if its signal-bar close is strictly after T_f; else **held**.

## Comparison (Guard 2: same signals on both kinds of day)
Afternoon trades = signal-bar close >= 12:00 on days with a morning reading. For each family x side, split by alignment with
M (aligned = long on UP / short on DOWN mornings; counter = the rest) and compare **post-flip vs held** within entry-time
buckets (12:00-13:00, 13:00-14:00, 14:00-15:55) so later entries are not compared with earlier ones. Report n, days, gross R,
net R, difference post-flip minus held, day-clustered t.

## Controls
- **Random standby (Lead standard):** the rule "stand by after a flip" removes k post-flip afternoon trades of a family-side on
  day d. Control = remove k random afternoon trades of the same family-side on the same day (200 draws); excess = mean R of
  the random-removed minus mean R of the rule-removed (positive = the rule removes worse trades than chance). Days where the
  rule removes every afternoon trade carry no information and are counted.
- **Size control:** the kept book is also compared with "same trades, uniformly smaller size" (STOPW lesson) — a standby rule
  must beat trading less.
- **Guard 3, up-vs-down afternoons:** report the post-flip minus held difference (a) raw, (b) after removing beta x SPY's move
  over each trade's hold (G.summary spy_move -> ex_market_r), and (c) within SPY-afternoon-move terciles; state the share of
  the raw difference that (b) removes. A rule that only re-labels "afternoon fell" is not a compass.

## Stage 2 (only if stage 1 shows a clear, gross, ex-market split on >= 1 definition)
Standby rule per family-side and definition; pass needs: rule-removed trades gross < 0; excess over the random standby t >= the
family bar (market-state lineage N from Skeptic: GATE1 112 + COMP15/HC1 + GATE2 15 + these 3), TRAIN and VALID > 0, up and
down days > 0, w/o best day > 0; keeps >= 80% of the family's trades and >= 90% of its top-decile winners (charter); more
families better than worse, none worse by > 0.03R. Live cross-check (labelled live paper): coil journals 10-06..11-09 against
the recorded live marks (mcf-data-compass).

## Script hygiene (lessons logged)
Every look-back via a guarded slice (no negative-index wrap), marks strictly before the entry, skip funnel printed, gross
before net, every definition counted.

## Stage 1 result (Builder 2026-11-10 02:50 ET, frozen script unchanged) — CLOSED
Midday-flip standby does not separate: post-flip worse than held (ex-market) in 30/67, 27/65, 28/67 family-sides (F1/F2/F3);
standby beats a same-day random block in 28/62, 30/59, 27/64 — coin flips. The coil family has no afternoon trades on 2y.
**My plan's flaw (Skeptic 03:00):** 'held_day' = no flip ALL day, so a 13:00 entry was labelled held because SPY never
crossed LATER — future information. Any forward spec compares post-flip with 'not yet flipped at entry'. Lesson logged.
