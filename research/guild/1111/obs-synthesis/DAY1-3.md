Educational only — not financial advice.

# Research Guild, days 1-3 (2026-11-09 .. 11-10 night): what we now know — Observer, for the owner

Plain-English, one page. Every number points to a file on the `mcf-guild` branch. Lead's tally: **40 ideas, 38 tested, 134 configs
scored, 0 passed a Testing bar, 1 forward shadow running (FAMC).** Live figures are paper trades (an optimistic lower bound on real costs).
The window 10-06..11-10 contains ~140 rule changes (research/ledger.jsonl): Primary sizing 10-28, per-setup stops 10-23/10-29, and the
Testing cost filter from 10-30. Live results are never read without them.

## What three days established
1. **Our costs are conservative, not hidden losses.** On 16,615 live trades the lab charges 0.218R per trade; live paper fills cost about
   0.06R (skeptic-20261109/costgap). On the 17 'cost-killed' setups: 0.065R live vs 0.192R lab (obs-costkilled).
2. **Live losses are direction, not friction.** 71 of 91 setups, holding 87% of live trades, lose *before* any cost (obs-stopcost). Tight
   stops lose on direction too (tightest quartile: gross -0.30R).
3. **New data sources carry SIZE, not direction.** Premarket volume (AUC 0.60 for the day's big movers), recent volume, and the 5-minute
   compass all predict how much prices move. None says which way once the gap is known. Each was tested against a 'just follow the gap'
   baseline: earnings calendar (EVD1), premarket drift (d2pm), options flow (OPTFLOW), news polarity (NEWSDIR), unexplained gaps (UNGAP).
   All closed by their own pre-registered kill lines.
4. **The compass reads 'staying', not 'heading'.** 'SPY finishes on this side of its open ~P%' is arithmetic: distance from the open against
   the typical rest-of-day move. Benchmark +0.4 pt, t 0.38 (obs-compass-rw). Next-hour direction is 48-53% at every horizon
   (main session, 142 tests). Trading the held side failed (GATE2, 0/15). Switching setups on/off by midday flip or morning reading is at
   coin-flip counts (RCOMPASS, COILAM, obs-morningmap).
5. **Exits and execution don't fix it.** Break-even stops hurt 27 of 27 families (BEREPLAY). Cheaper limit entries are adversely
   selected: the trades a limit misses earn +0.22R, the ones it fills -0.07R (LIMEX). Wider minimum stops were 85% just 'trade smaller' (STOPW).
6. **What works live is one short family in one window.** One setup x account clears 'positive after costs, positive without its best day,
   best day < 50%': RW1-gapdn-bounce-flowsell-short-FD in Testing 2 (75 trades, +0.211R; scout WHATWORKS). The 11 near-misses are all shorts,
   carried by 11-04/11-05. Rule changes (cost filter 10-30) and that sell-off overlap completely.

## Still open (honestly labelled)
- **FAMC** — fading after-close earnings gaps, journal-only forward shadow, first session 11-11 (ALC, RGTI). Calendar precision 0.887
  (obs-amcnews). A post-hoc idea from 2 years of data. Needs 40-60 sessions or an e-process EDGE alarm (XA-EPROC: 20 sessions almost never confirm).
- **D3GEN** — a 'worst-quarter' screen is the first that ranks live Setup Generator results at all (rho +0.24, p 0.04). It ranks but does
  not rescue: the top third is still -0.10R live. Forward test on new generator runs.
- **CONFIRM** — enter only once price moves in the trade's direction (the flip side of LIMEX). One counted test, plan pending.
- Display tools ready for the card: the continuous close-side line (COMPCAL M1) and the volatility-scaled size band (PVSCALE).

## Questions only the owner can answer
1. **Hunt or harvest?** Four new data sources gave size, not direction. Keep one direction pilot a day, or move most effort to
   sizing/risk for the few setups that are positive before costs?
2. **Earnings names.** About 70% of the biggest movers are earnings names, and live blacks them out for +-4 days. Should a forward-only
   earnings shadow (FAMC) be allowed to become a live exception if it clears the bar, or does the blackout stay absolute?
3. **The Setup Generator's slots.** Its screen does not rank live (rho -0.04..-0.21 old screen). Keep 200 live slots for exploration,
   shrink them, or gate new GEN setups by the worst-quarter screen? (Plus Skeptic's success-line question: 20 shadow sessions as a harm
   floor, 40-60 for confirmation.)
