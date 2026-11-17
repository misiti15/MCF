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
Lineage: IMOM (intraday time-of-day return prediction, 1 look) + these 2 = N 3. BAR90 = max(1.35, 0.9 x max(1.5, sqrt(2 ln 3)))
= **1.35**. Shown, never used: own-only N 2.

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
