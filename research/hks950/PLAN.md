# HKS950 — same half-hour continuation, anchored after 10:00 ET (Scout, pre-registered 2026-11-17 ~09:25 ET, BEFORE any signal is computed)
Educational only — not financial advice.

Source: backlog `wi-same-halfhour` (status idea since 10-07, never tested). The paper is Heston, Korajczyk and Sadka (2010),
"Intraday patterns in the cross-section of stock returns" (arXiv 1005.3535). It finds a name's return in a given half-hour
tends to repeat in that same half-hour on later days, for weeks. The backlog red flag: bps-sized, so costs may dominate.

## Why it might work for us
- It is cross-sectional (long and short legs at once), so it does not depend on market direction: it may work on up and down days.
- It works for any time slot, including quiet midday, and we can use it after 10:00 only (owner anchor rule; no 09:30 entries).
- Even if it fails as a stand-alone trade after costs, a positive gross effect could serve as an entry-timing tilt for existing setups.

## Data (cached, no new fetch)
`<scratch>/shortup_rth/m30.csv.gz`: 512 names, 30-min bars, 450 sessions 2024-10-01..2026-11-13. It was fetched with the #43 guard,
so the locked block is absent. Half days (2025-07-03, 11-28, 12-24) are dropped. Universe caveat: the names are the SHORTUP list,
not the full 3,000.

## Rule (exact)
- Slots: the half-hours starting 10:00, 10:30, ..., 15:30 ET (12 slots; the 09:30 bar is used only as the prior close).
- Slot return r(s,d,k) = close of slot k / close of slot k-1 - 1.
- Signal at the START of slot k on day d: mean of r(s, d-j, k) over the prior L sessions (j = 1..L). Needs >= 0.8 L non-missing values.
- Each (d,k): long the top decile of the signal and short the bottom decile, equal weight, and hold for that half-hour.
- Configs: L in {20, 40} = **2 configs**.

## Family and bar
SUPERSEDED by Amendment 2: family N 42, BAR90 2.46. (The original was N 3 / BAR90 1.35.)

## Scoring (one look per config, run after 16:00 ET)
- Unit: per-day mean of the 12 slot spreads (equal-size bins, so this is not a #39 issue). t uses days as clusters.
- Split: TRAIN = sessions before 2026-01-01 (231 days); VALID = 2026 sessions (219 days).
- Report, gross first in bps: the L-S spread; the long leg minus the universe mean; the short leg minus the universe mean.
  Then by slot (12), by SPY up/down day, the best-day share, and the avg w/o the best day.
- Control: shuffle the signal across names within each (d,k), 200 times, giving a null distribution for the L-S spread.
- Cost: a pre-set 6 bps round trip per name per leg, so the L-S net = gross - 12 bps per slot-trade. Print break-even cost.

## Pre-registered reading table
| outcome | reading |
|---|---|
| VALID t >= 1.35, same sign as TRAIN, net > 0 | stand-alone lead: rework into a setup (Lead routes) |
| VALID t >= 1.35, same sign, gross > 0 but net <= 0 | no stand-alone trade; test as an entry-timing TILT for live setups (new plan, own count) |
| VALID t < 1.35 or sign flips | CLOSED: "nothing above X bps; smaller unknown" |

## Power (computed from the NULL only, with random deciles and no signal)
Per-day SD of a random L-S: 2.92 bps in TRAIN and 3.27 in VALID, so SE is 0.19 / 0.22 bps. MDE80 is 0.54 / 0.62 bps, and the
MDE at the bar is 0.42 / 0.48 bps. The test can see an effect far below cost, so power is not the risk; costs are.
Null script (no signal): research/hks950/power_null.py.

## Amendment 1 (2026-11-17 ~11:40 ET, before the real look; code only, no rule change)
- Scorer: research/hks950/hks950.py. `--selftest` plants an 8 bps same-slot effect (found: VALID t +29.8, LEAD) and a 0 effect
  (CLOSED, t +0.51), and checks that the first session has no signal (no look-ahead). Both the loop and the vectorized
  versions give identical selftest numbers.
- The shuffle control is drawn as iid random ranks within each (day, slot), which is equivalent to permuting the signal.
- SPY up/down day = SPY close of the 15:30 bar / close of the 09:30 bar - 1 (from the 10:00 anchor). SPY is also one of the 512
  names; it stays in the universe as written.

## Amendment 2 (2026-11-17 ~13:30 ET, before the real look; Skeptic skeptic-20261117-1550-1/-1551-2/-1750-1, Lead lead-20261117-1100-1/-1300-1)
1. **Family N 42** (cross-sectional return prediction from own past returns, the same bet as the ex30 family 39 + these). Full bar
   sqrt(2 ln 42) = 2.73 and **BAR90 2.46** are both printed; **BAR90 decides**.
2. **Slot 15:30 is dropped from the main reading** (it ends at the 16:00 close; Live is flat by 15:55), so the main reading uses
   11 slots (10:00..15:00). 15:30 is reported apart.
3. **Pass needs all of the following:** VALID L-S t >= 2.46; TRAIN the same sign (positive); the same sign in >= 8 of 11 VALID
   slots; and the observed VALID mean > the 95th percentile of the 200-draw shuffle null.
4. Printed: break-even cost per leg round trip, per slot and overall; the LONG leg alone (gross and net of 6 bps), because a
   tilt uses one side. If gross passes and net fails, the tilt plan is scored on Live setups' own entries, not on this portfolio.
5. Universe: the fixed top-500 ADV list of the 2026-10-05 snapshot (512 names incl. ETFs), applied back to 2024 (checklist 32).
   Inside one fixed list this mostly costs breadth (survivor names). It is stated with the result.
6. **RTH (checklist 42): m30 is NOT RTH-only.** Raw bar starts run from 08:00 to 17:00 ET (pre 08:00-09:00: 226,555 bars;
   post 16:00-17:00: 414,605). prep() drops them and asserts that every day runs 09:30..15:30. The selftest checks that the
   assert fires on a day missing its 15:30 bar.
Selftest (rerun): planted 8 bps gives LEAD (t +28.6, 11/11 slots); 3 bps gives TILT (t +5.9, net <= 0); 0 gives CLOSED
(t +0.46, 6/11); 8 bps in ONE slot only gives CLOSED (t +3.71 but 6/11 slots). RTH assert ok.
