Educational only — not financial advice

# U7 Workbench at scale — pre-registration (written 2026-11-18 ~18:30 UTC, before any tune was scored)

USAGE PLAN item 7 (owner 2026-11-18), run under the C3-WB rules (research/consultant_p3/RESULTS.md #6) and ODPREP.
Research only, market hours: no config / code / runtime change, no PR, no merge, nothing deployed. The promotion hold
is on: a pass becomes a Testing-copy proposal (decision code) for the owner, never a live change by this study.

## Data

- Live journals (run_id 1) of all ten mcf-data* state branches, sessions 10-06..11-17 (11-18 is open and left out).
  R after costs = pnl_adj / (|entry - stop| x shares). A setup's record pools every account it ran in (the live record).
  De-duplication (fixed): when one setup traded the same symbol-day in two accounts (76 symbol-days, mostly Gen + a
  testing copy), only the account with the most trades of that setup is kept.
- 1-minute RTH bars (SIP, split-adjusted) for every traded symbol-day of the 20 setups and daily bars 08-20..11-17,
  fetched GET-only from Alpaca market data (no locked-block date is anywhere near: 2024-11-01..2025-02-28 never read).
- Shadow (run_id 3) exists for one session only (11-17); it is reported as a paired read-out, not used for verdicts.

## The 20 setups (fixed before scoring; u7_eligible_ranked.csv)

Arena setups (On Deck, Testing A-F per docs/live/assignments.json as of 11-18) ranked by live avg R w/o best day, after
these exclusions: the C3-WB5 queue (CWT09-gapdn-vwaploss-g10, NS3-failed-vwap-reclaim, MF2 / MF4 all versions,
GEN-261027-08, L3-gap-slope-rsi5hi-FD) and NM1-cwt09-g10-vwaploss-short (same signal as the CWT09-g10 tune); CWT12/CWT14
(closed to variants); existing -WB copies; losing parents with 100+ trades (C3-WB: those go to EXIT100, not the
Workbench); fewer than 5 traded sessions or 15 trades (no split possible). Top 20:

1 GEN-261027-01 (long) · 2 GEN-261026-03 (short) · 3 L3-gap-slope-lowdist-FD · 4 RW7-gapdn-bounce-early-short-FD ·
5 GEN-261026-07 · 6 RW1-gapdn-bounce-flowsell-short-FD · 7 GEN-261029-07 · 8 GEN-261019-10 · 9 CWT05-flush-m05-v5-long ·
10 NM-HL-T75-pm-long · 11 GEN-261029-06 · 12 NS1-rsidip-rsi5pop-long · 13 NS4-pm-vwap-reclaim-oversold-short ·
14 GEN-261028-07 · 15 ST8-volspikedn-long-pm-t1s1-FD · 16 ST3-rsi5up-short-pm-t1s1-FD · 17 ST6-volspikeup-short-mid-t1s1-FD ·
18 GEN-261019-08 · 19 NS4-pm-vwap-reclaim-oversold-short-FD · 20 MF3-open-flowsell-rsi5hi.
L3-gap-slope-fromopen-FD (protected, Primary) is not touched. Five of the 20 already carry an 11-16 WB copy (WB1/3/4/5);
a pass here would replace that copy (ODPREP: one tune per setup), not add a second.

## Split (per setup, fixed)

Fit = the first ceil(D/2) of the setup's D traded sessions (chronological); check = the later sessions, never looked
at while choosing the tune. The tune is chosen on fit only; the verdict is on check only.

## Tune type by parent record (C3-WB) and the fixed menus (one change per tune; <= 2 allowed, 1 used)

- Proven parent (live avg R > 0 AND avg R w/o best day > 0): exits / frequency only — menu X:
  target at 0.5x / 0.75x the parent's target R (if the parent has a target); for hold / no-target parents a target at
  1.0 / 1.5 / 2.0 R instead; time stop at 30 / 60 / 120 min after entry; refire off (first entry per symbol-day).
- Every other parent (unproven or small losing): one threshold or gate step — menu G: drop the bottom third or the top
  third (fit tertile cut, so >= 2/3 of fit trades kept) of ONE entry-time feature: clock time, stop width (|entry-stop|
  / entry), move from the day open in trade direction (ATR14 units), distance from VWAP in trade direction (ATR14),
  gap in trade direction, relative volume so far, stop_cost_r (journal); or refire off. 15 candidates.
- Features are measured on the last completed 1-minute bar before the live entry (no look-ahead); ATR14 / prior close /
  ADV20 from daily bars strictly before the session.
- Fit choice: the candidate with the highest fit total R (gates: >= 50% of fit trades kept and >= 5 kept); it must beat
  the parent's fit total R, else "no tune found" = FAIL.

## How a variant is scored (parent = its live record as traded)

- Gates: the variant's trades are the parent's live trades that pass the gate (live R, costs already in).
- Exit tunes can only exit earlier than live: walk the 1-minute bars from the first full minute after entry to the live
  exit; a target fills only when traded THROUGH by max($0.01, 0.03%) (shadow "fills B"), at the limit; a time stop exits
  at the close of the bar at entry + N min. Variant pnl = live pnl_adj + side x (new exit - live exit) x shares, with
  the time-stop exit charged max($0.01, 1 bp) + $0.01 per share and the live exit cost left in (conservative).
- Random entries (control, every setup): for each check trade, 5 seeds of a random entry minute on the same symbol-day
  inside the setup's live entry-time span, same side and same $ risk per share, exits = stop / parent target R (if any)
  / the variant's exit change / flat 15:55, LR8 costs (entry + max($0.01,1bp)+1bp; stop + max($0.02,4bp)+$0.01; flat +
  max($0.01,1bp)+$0.01). The real entries are run through the SAME simplified engine, so entries vs random entries is
  like for like. Gates also get a random-subset control: 2,000 draws keeping the same number of check trades per day.

## Verdict on check sessions (all must hold for PASS -> Testing-copy proposal)

1. Variant check avg R >= parent check avg R + 0.02 and > 0.
2. Variant check avg R w/o best day > 0 and best-day share < 50%.
3. Worst check day not worse than the parent's by more than 10% (day R totals).
4. Paired daily difference (variant - parent, check days) day-clustered t >= bar = max(1.5, sqrt(2 ln N_v)) with
   N_v = 20 verdicts scored on check -> 2.45. (Every fit candidate is counted and reported as configs tried; the bar with
   N = all configs is also shown.)
5. Beats random entries (simplified-engine avg R, real > random) and, for gates, >= 80th percentile of random subsets.
6. Enough reps: >= 4 check sessions and >= 15 variant check trades (C3-ROT spirit; fewer = "too few reps", not a pass).
LEAD (reported, not proposed) = 1 and 2 hold but 4, 5 or 6 fail.
Every setup is reported with fit / check numbers, avg R w/o best day + share, improve / worsen counts across the 20.
Note: Workbench RULES also ask the 2-year backtest of parent and copy before deployment; any PASS here still needs it.
