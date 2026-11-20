# GB-GENTRAIL: trail / target exits for GEN "hold" setups (pre-registered plan)

*Educational only - not financial advice.* Written 2026-11-20 before any config below was scored. Research only:
no setup, exit or config change. Owner reply 11-19: "Research gentrail" (GB-GENTRAIL yes, research only);
GB-NOEXIT / GB-NOLOCK yes stand. Backlog line: gb-1119-gen-hold-trail (parent nightly-1020-gen-hold-mfe-giveback).

## Setups
GEN setups whose generator geometry is `hold` (stop 1R, no target, flat 15:55) or `holdtr` (same + 1R trail once
+1R), R = 0.25 x daily ATR. Universe = every such spec in config/account_gen.yaml (enabled or not; 57 specs), since
the same spec runs (as itself or as a WB copy) in Gen / Explore 1 / Live Lab / Testing 2/D/E/F / Graveyard.
GEN-POD* seeds and -WB copies have no generator spec: live only (WB copies inherit their parent's spec in the lab).

## Exit configs (7 rules; for each setup its own geometry is the baseline, so 6 alternatives per setup)
- C1 HOLD: stop 1R, no target, flat 15:55 (= `hold`).
- C2 TR1R: C1 + trail 1R behind the best price once +1R (= `holdtr`).
- C3 TR50: C1 + once +1R, stop at entry + 50% of max favourable excursion (giveback 50%).
- C4 T1: fixed +1R target (limit) + 1R stop, else flat 15:55.
- C5 P1: half off at +1R (limit), runner on the C2 trail (stop at entry at activation, 1R behind best after).
- C6 CH2 / C7 CH3: chandelier, stop = max(initial stop, best price since entry - k x ATR5), k = 2 / 3, ATR5 = mean
  5-minute true range of the last 6 five-minute bars up to the entry bar (vol-scaled, active from entry).
Trail / stop levels move only from the bar after the bar that set them (no intrabar look-ahead); the stop is checked
before the target inside a bar.

## Costs (RESEARCH_RULES rule 1)
Lab: generator cost model (mcf/research/generator/data.py: 1c + 1 bp x time-of-day multiplier on entry; exit 1c + 1 bp,
+2c on stop-type fills, limit target 0; x3 tier for |gap| >= 20% or price < $5). **Extra 1c + 1 bp per share on every
exit caused by a rule that is not the setup's own geometry** (penalises the change, as giveback_1119).
Live: LR8 cost (gross journal R - journal R) subtracted from every arm; rule-driven early exits also pay half spread
+ 1c + 1 bp. Shorts: intraday only (no overnight borrow); hard-to-borrow fees are not modelled (noted). No inverse /
leveraged ETF issue specific to this item (GEN hold signals are equities; any ETF hits are listed if found).

## Data and split
Lab: generator 2-year open frames + 15:05-15:55 tail (headtail), first signal per symbol-day inside the window,
earnings blackout as the generator. Locked block 2024-11-01..2025-02-28 never read (lib refuses it; asserted absent).
Sessions <= 2026-10-31 (the tail file ends 2026-11-04). **Fit** = sessions <= 2025-09-30, **check** = after
(giveback_1119 convention). Caveat: GEN specs were selected on the whole open history (entry selection in-sample);
the comparison is paired on the same signals, so it measures the exit change only.
Live: run-1 journals 10-06..11-19 (be1120 extract, LR8 basis), replay on 1-minute SIP bars, descriptive only.

## Scoring (WB2 protocol: paired on the parent's own signals)
- Per trade delta = config R - baseline R. Pooled mean, day-clustered t, per setup and per family
  (family = side x window x hold/holdtr) better / worse counts and sizes, avg R w/o best day + that day's share.
- Selection: the config with the best pooled fit-half delta (among C1..C7 alternatives, separately for the hold group and
  the holdtr group) is the adopted one and is scored once on check.
- **PASS** needs all: check delta > 0 with day-clustered t >= 2.0 (lineage bar t >= 4.14 also reported); fit delta > 0;
  more setups better than worse on check; best check day < 50% of the gain; live paired delta >= 0 (descriptive).
- All 7 configs on both halves are reported (configs counted: 7 rules x 2 groups = 14 group-config cells, 12
  alternatives). No tuning after the check half is read.
- A PASS would only lead to a backlog proposal (new copies, journal-only shadow in Gen, owner decision outside market
  hours, Primary only in the Friday epoch window). Nothing changes live.
