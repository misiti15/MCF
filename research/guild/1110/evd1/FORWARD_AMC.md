# FAMC — forward-only shadow: fade the reaction-session gap of after-close (AMC) earnings names (Scout spec, FROZEN 2026-11-10 11:40 ET, before the 11-11 open)

*Educational only — not financial advice. Journal-only shadow: NOTHING trades. Live blacks out earnings names +-4 days; any
use beyond a shadow needs an owner exception (stated up front). Lead lead-20261110-1100-1/-2; Skeptic skeptic-20261110-1056-2.*

## Why, and what is post-hoc
EVD1 (2y, closed by its pre-registered rule) left one literature-backed, post-hoc pattern: on AMC reaction sessions the move
from 09:50 to 15:55 runs AGAINST the gap in every surprise bucket (agree -0.062, disagree -0.045, inline -0.033, unknown -0.060
ATR gross; TRAIN and VALID both negative for agree / disagree), and AMC 'agree' fades more than a matched non-event gapper
(-0.111 ATR, t -2.07). Outside evidence: intraday trades against the overnight earnings reaction (Lou-Polk-Skouras 2019;
Liu-Hope-Hu 2023). Chosen after seeing 2y -> it is judged ONLY on sessions from 2026-11-11 on; no 2y re-mining.

## Surprise is NOT used (check done)
The live calendar (mcf/data/earnings.py, Nasdaq) gives names and dates only; the surprise file (research-data earnings_yf, Yahoo)
is fetched by a manually dispatched workflow and fills surprises late (VALID 'unknown' 612 of 614, Skeptic). Nothing shows a
surprise available by 09:50 -> the rule uses only the AMC timing and the gap side. 'Agree' is reported as a secondary,
descriptive cut from the next calendar refresh, never as the rule.

## Rule (one config)
- Events: names whose report is AFTER the close on day D (calendar snapshot taken by D's evening: Nasdaq row time
  'time-after-hours', or Yahoo report_dt_et >= 16:00), mapped to reaction session D+1. Lab names, adv20 >= $60M, no ETPs.
- On D+1: gap = 09:30 open / prior close - 1; require |gap| >= 1%. Side = AGAINST the gap (short a gap-up, long a gap-down).
- Entry at the 09:51 one-minute open; exit at the 15:55 close; stop 1.0 x ATR14 from entry (R = 1 ATR, so results read in ATR);
  stop-first on 1-min bars, a minute opening through the stop fills at its open. Costs: production (1c + 1bp x tod multiplier +
  4.4bp spread on entry, 1c + 1bp exit, +2c on stops), 3x on price < $5.
- **Control (baseline):** for each event, one same-session NON-event lab name (adv20 >= $60M, no earnings within +-4 days) with
  |gap| in the same bucket (1-2 / 2-5 / > 5%), faded the same way (seeded pick) -> 'fade any gapper'.
- **Ex-market:** each leg minus beta60 x the side-signed SPY move over the same window.

## Monitor (XA-EPROC, research/xaeproc/eproc.py)
- Per session x_t = mean ex-market net R of the event fades minus mean of their controls (sessions with >= 1 event; others skip).
- Cap fixed now: **0.40 R** (expected per-session sd ~0.25 R from EVD1's ~8 AMC events/session x ~0.6 ATR per trade, x1.5).
- **HARM alarm** (mirror process K >= 20): stop the shadow and report. **EDGE alarm** (K >= 20): report to the Lead as evidence.
- Floors: report at 20 sessions (sanity only, power 0-19%); confirmation needs the EDGE alarm or >= 40-60 sessions with the
  ex-market mean > 0 and the gross mean > 0. Family N for any later Testing move: 858 + 1 (BAR90 ~3.31) on whatever forward t.

## Daily job (nightly, after 16:00 ET; Builder or Observer)
`python research/evd1/famc_shadow.py --date YYYY-MM-DD --calendar research/evd1/famc_calendar.csv`
appends one row per event + control to research/evd1/famc_forward.csv and prints the e-process state. Calendar snapshot:
research/evd1/famc_calendar.csv (symbol, report_date, timing, source, snapshot_at) - add D's AMC names on D's evening.

## Amendment 1 (2026-11-10 13:30 ET, before any row exists) — Skeptic skeptic-20261110-1300-1 / -1301-2, Lead lead-20261110-1300-1
1. **Control exclusion:** a control may not have ANY earnings date within +-4 sessions: names in the live job's own snapshot
   mcf-data earnings/<D>.json (`--live-earnings`, asserted to be day D) plus anything in the calendar within 6 days.
2. **Ex-market per leg:** SPY's move over each leg's OWN hold (its entry minute -> its exit minute), so a stopped leg is not
   charged SPY's full-day move.
3. **Point-in-time assert:** every selected calendar row's snapshot_at must be before D 09:30 ET, or the run stops.
4. **Control match:** same gap bucket AND same adv20 tercile (terciles over that day's lab names) - timed names skew to large caps.
5. **Raw mean printed** beside K (the e-process tests the clipped mean; fades cap losses at 1 ATR and leave gains open).
6. **Cap and horizon:** with ~2-3 timed events per session, session sd ~0.5R -> **cap 0.75R** (1.5 x sd); realistic confirmation
   horizon 40-60 sessions; the 20-session check stays a HARM floor only.
**Data status:** UNBUILDABLE until a point-in-time AMC source exists (not zero rows). The guild proxy blocks api.nasdaq.com and the
live snapshot drops Nasdaq's 'time' field. Owner options in tonight's PR: (A) store 'time' in the live snapshot (housekeeping), or
(D) a pre-open re-run of the research calendar fetch (Nasdaq publishes timing weeks ahead; advance labels matched next-session
gaps 81%). **Universe** is then time-supplied names only (~31% of calendar rows) - a stated limit, not a choice from data.
