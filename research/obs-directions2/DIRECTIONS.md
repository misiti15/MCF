# Directions the evidence still allows — Observer, 2026-11-14 (Lead lead-20261114-0700-2)

What five days established (board, 11-09..11-14): costs are fine (live paper ~1/3 of the lab charge; LR8 adds ~0.04R,
exit-linked); losses are direction (87% of live trades in setups that lose before costs); new data carries size, not
direction (SIZETREND: |gap|/ATR raises later range +14% Q5/Q1, path efficiency flat); market-state switches (5 shapes)
and up-day timing (5 tracks) fail against honest nulls; replays now match live where live traded (5-min 0.88, LR8-basis
gap -0.009R) but not for untraded names (pool-priced 0.3%). The only direction that clears costs is slow: 12-1 momentum.

## D1 — size-conditioned stop width (size -> tradable, no direction call). Remedy-shaped (owner rule 2026-11-05).
Idea: direction stays with each setup; predicted size only sets the stop. On days in the top two |gap|/ATR quintiles
(known 09:30), widen stops 1.5x at the SAME $ risk (fewer shares); otherwise unchanged. Why it can work where STOPW
failed: unconditional 1.5x widening was live +0.050R (t 4.22), 2y +0.019R (t 2.81) but failed in down sessions; cost per R
scales with spread/stop (OBS-STOPSLIP: slip = 0.012 + 0.63 x spread/stop, stops cost ~0.10R vs 0.03R for targets), and
big-range days are where tight stops get hit by noise. Family: STOPW exit-geometry N 77 + this (2 configs: Q4-5 and Q5
only) = 79, BAR90 ~2.66 on delta t. Kill line: delta vs the setup's own stop, ex-market, day-clustered, TRAIN and VALID
both > 0 AND down sessions not worse AND >= 60% of setups better (report each setup's better/worse and by how much);
otherwise closed. Prior: modest (+0.01..0.02R), honest odds below even.

## D2 — MOMSIDE: slow 12-1 momentum as a side filter on intraday setups (queued since 11-11).
Idea: the one surviving direction is slow. Do intraday shorts do better on names with weak 12-1 momentum, and longs on
strong ones? Uses only data known at the open; no new entry. Family: slow-momentum (longhold 105) + this (<= 3 configs:
tercile cut, side-aligned keep) = 108; but as a FILTER it must also beat the volume-cut trap: compare against a random
same-share skip within setup-day (CONFIRM standard). Kill line: aligned-minus-random excess, ex-market, TRAIN and VALID
> 0 with VALID t >= BAR90 (~2.7), >= 60% setups better, best-day share < 50%; else closed. Prior: weak-moderate; REGSW-2
showed counter-state (market) trades do better, but that was SPY reversion, a different axis from stock-level momentum.

## D3 — calibrated forward replays for live-traded names = faster verdicts (the reps priority, not a profit rule).
Idea: FWDCAL now matches live within +-0.03R in Gen, On Deck, Testing A, Testing E where trades are priced from live
quotes. For setups whose names live evaluates, replay the sessions since each setup's freeze date (decision-bar match, LR8
basis, max-form stops) and add them as a SEPARATE, labelled record beside live (never mixed). That multiplies setup-days
for exactly the setups the owner must judge (Gen, arena). Family: none (calibration, 0 strategy configs). Kill line: the
frozen engine fails rule 21 (RULE21-DB reading: decision-bar match >= 95% AND |gap| <= 0.03, never optimistic) on the
fresh 11-16..11-17 window in that account -> no replay record for that account. Pool-priced (untraded-name) replays stay out.

Not recommended (evidence closed): up-day timing, market-state on/off, brackets on predicted-big days (SIZETREND),
scale-outs (ETFTIER: raise the median, lower the mean), news-timed entries (NEWSMID A6: headline follows the move).
Educational only — not financial advice.
