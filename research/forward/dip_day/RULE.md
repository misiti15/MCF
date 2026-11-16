# Dip-day forward question — FROZEN 2026-11-16 (forward log only)

*Educational only — not financial advice. Research only: no order, no config, no account runs this.*

Source: `research/drop_rebound_1116/NOTES.md` (owner idea 2026-11-16). The study found the rebound trigger itself adds
nothing as an entry (random entries on the same days earn the same). This log asks a different, frozen question: are
dip days good days for the index-dip / ETF-dip long setups we already run live?

## Day type (definitions exactly as in research/drop_rebound_1116 "from_runhigh", ported in `dipday.py`)

- SPY 1-minute RTH bars; bar index 0 = the 09:30 bar; a bar's close = the price at its start + 1 min.
- **Drop**: some bar starting 09:30-10:29 has a low >= **0.65%** below the highest SPY high since 09:30 (inclusive).
- **Bottom**: the lowest low from the bar of that running high up to the decision bar.
- **Rebound**: some bar close from 09:50 to 12:00 (bars 09:49 .. 11:59) is >= **0.5%** above the bottom.
- **DIP** day = drop and rebound. Every other session = **OTHER** (drop-only days are tagged `drop_no_rebound` but count
  as OTHER).

## Setups (frozen list of families)

Live setups whose name starts with `IDX<n>`, `LD<n>` or `NM-ETF-late-dip` (any suffix, e.g. `-FD`), in any of the ten
intraday accounts (journal run_id = 1 = live paper; the what-if run is excluded). At freeze: IDX1 hold / trail, IDX2,
IDX3, IDX5, LD1-LD8, NM-ETF-late-dip-di-long (config/account_*.yaml, docs/live/assignments.json 2026-11-16).
Setups joining these families later are included; nothing is dropped for being bad.

## Measure

R per setup-trade = pnl_adj / (|entry - stop| x shares) (journal's cost-adjusted P/L). Unit = one live trade.

## Pass bar (stated up front, scored once)

Scored when the log holds **>= 10 DIP days** (sessions 2026-11-13 onward; 11-13 and 11-16 backfilled at freeze):

- avg R per setup-trade on DIP days minus avg R on OTHER days **> 0**, with Welch **t >= 1.5**, and
- the DIP-day avg R **without the best DIP day** still **>** the OTHER-day avg R (positive w/o best day).

All three → write it up for the owner (a DECISION: e.g. a dip-day context flag for these setups; nothing enabled
automatically). Any one missing → close the question (logged; no re-tune on the same forward data).
At ~2 DIP days a month (study: 12% of sessions), 10 DIP days take roughly 4-5 months.

## Run

    python research/forward/dip_day/dipday.py --date YYYY-MM-DD

Idempotent: re-running a date replaces its rows in `days.csv` (day type) and `forward.csv` (that day's trades).
Any change to the definitions above = a new question with a new freeze date and a fresh count.
