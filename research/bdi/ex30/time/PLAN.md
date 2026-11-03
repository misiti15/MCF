Educational only — not financial advice

# ex30 / time — time and calendar structure (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups (this lane delivers 5).
Family: the clock and the calendar — lunch reversal, power hour, the 10:00 reversal, turn of the month, the overnight
gap against the intraday drift, quiet-day range fades (SPY within +-0.25% of its open). At least two QUIET-day setups.
Known weakness of the live book: a market-direction bet with no edge on quiet days (research/bdi/night1102/regime).

## Live-runner data check (stated up front)

- Clock: `tod` (bar-close HHMM) is in every frame. LabStrategy entries are bar closes 09:50-15:00 only, so "power hour"
  here is entries 14:30-15:00 held to the 15:55 flat; nothing can enter 15:00-15:30.
- Calendar: history frames carry `date`; the live frame is indexed by today's 5-minute bar starts (DatetimeIndex), so a
  module reads the date from `date` if present, else from the index. Day of month / day of week are known before the
  open. **No exchange holiday calendar is used** (a "last trading day of the month" needs one; the modules use calendar
  day of month instead, known at the open, so live = history).
- Session after a big / small index day: SPY's prior-day direction is NOT available to a lab module live (only
  `spy_prng` = SPY prior-day range / SPY ATR, opt-in daily context). The prior-day setup here therefore uses range,
  not direction. History value of spy_prng = SPY frame first-bar dist_pdh_atr + dist_pdl_atr (as pdl1030/pdl1a,
  which checked it against the live definition).
- Quiet tape: `spy_fo` (opt-in context) at the bar close. The day-type split used in reporting (SPY open-to-close at
  the END of the day) is not known at entry; the setups use only spy_fo so far.
- Not used: `qqq_vwap` (absent from history2y context tables).

## Data, splits, costs, controls (harness = ex30/peer = night1102/simple)

- history2y open frames + lab context (`lib.load_month(m, context=True)`). TRAIN = 2024-10, 2025-03..2025-12;
  VALID = 2026-01..03, 2026-07-01..2026-09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block
  2024-11-01..2025-02-28 never loaded** (asserted; MCF_HIST_ALLOW_LOCKED unset).
- Trades: `mcf.research.gates.lab_trades` (first qualifying bar per symbol-day, production costs 1c + 1 bps per side,
  +2c on stops, time-of-day entry multiplier). R = 0.25 x daily ATR, flat 15:55. ADV floor 95M (adv20).
- Random control: day-matched — trade R minus the mean production R of every eligible bar (same side / geometry /
  window / ADV floor) on that date. Excess and its day-clustered t reported.
- Day type: SPY open-to-close (SIP 1-minute cache): up >= +0.25%, down <= -0.25%, else quiet. R by type, TRAIN, VALID.
- Light lane gate: avg R >= -0.02 on TRAIN and on VALID, 1.5-25 trades/session (TRAIN+VALID sessions), mask parity
  module vs harness on 2026-09 (bar by bar inside window + ADV). No BAR90. A failing setup is still delivered,
  marked gate_pass = false. One-big-day check (avg R w/o best day, best-day share) reported.

## Notation (per symbol-day, at the bar close)

move = (close - day open) / atr_d (day open = close / (1 + fromOpen/100)). hod = close + dist_hod_atr x atr_d,
lod = close - dist_lod_atr x atr_d (running day high / low incl. 09:30-09:45 bars). rng = dist_hod_atr + dist_lod_atr
(day range so far, ATRs); pos = dist_lod_atr / rng. vwa = vwapDistPct / 100 x close / atr_d (VWAP distance in ATRs).
prev_* = the previous 5-minute bar of the same symbol-day. lag k = k bars earlier (only bars from 09:50 are used, so
live and history agree). dom = calendar day of month; dow = weekday (Mon 0).

## The 5 setups (primary form = the delivered module, fixed now; results do not change the choice)

| id | side / geom | window | rule |
|---|---|---|---|
| TM1-lunch-stalled-high-fade-quiet-short | short t05s1 | 11:30-13:30 | abs(spy_fo) <= 0.25, move >= +0.75, dist_hod_atr >= 0.40, hod - hod(lag 6) <= 0.01 atr (no new high for 30 min), close < prev close |
| TM2-quiet-tape-range-floor-fade-long | long t05s1 | 12:00-15:00 | abs(spy_fo) <= 0.20, spy_prng <= 1.0, rng >= 0.75, pos <= 0.15, close > prev close |
| TM3-gapup-drift-powerhour-short | short t05s1 | 14:30-15:00 | gap >= +1.0%, move <= -0.75, dist_lod_atr <= 0.15, vwapDistPct < 0 |
| TM4-ten-oclock-reversal-long | long t1s1 | 10:00-10:15 | move <= -0.75, lod < lod(lag 2) (new low in the last 2 bars), close > prev high, vwapDistPct < 0 |
| TM5-turn-of-month-vwap-pullback-long | long t05s1 | 10:30-14:00 | dom >= 28 or dom <= 3, move >= +0.50, 0 < vwa <= 0.15, close > prev close |

Why each is a time / calendar idea: TM1 = lunch reversal on a QUIET tape — the morning leader whose high is 30 min
old stalls in the lunch lull with no index wind to carry it; TM2 = QUIET-day range fade — on a flat tape after a
narrow SPY prior day (compressed regime), names at the floor of their own day range revert in the afternoon;
TM3 = overnight gap vs intraday drift — a gap-up that has drifted all day below its open and sits at the low going
into the last hour (gap holders capitulate into the close); TM4 = the 10:00 reversal — the opening flush that turns
at the 10:00 clock (first bar to close above the prior bar's high right after a new low); TM5 = turn-of-the-month
inflow days — buy the first VWAP pullback of a name already up on the day only on the calendar days around the
month turn.

**Neighbours (plateau / control check only, never substituted):**
TM1 move >= 1.0; dist_hod_atr >= 0.25. TM2 spy_prng filter off; abs(spy_fo) <= 0.30. TM3 gap >= 2.0; move <= -0.50.
TM4 move <= -1.0; Monday only (dow == 0). TM5 complement calendar (4 <= dom <= 27, the calendar control); dom >= 27
or dom <= 4. = 10 configs.

## Count

5 primary + 10 neighbours = **15 configurations**, all reported in results.csv. Nothing else is scored.
