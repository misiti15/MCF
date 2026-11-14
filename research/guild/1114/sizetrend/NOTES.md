# SIZETREND — does predictable SIZE come with more DIRECTIONAL days? (descriptive, 0 configs)
Educational only — not financial advice. Context: Lead asked Observer (lead-20261114-0700-2) for a direction that turns 'size is
predictable' into something tradable without a direction call. The obvious form is a two-sided bracket (enter whichever side
breaks). It earns in R units only if predicted-big days trend more CLEANLY. Bigger alone does not pay, because the stop and costs
scale with it. The breakout family is already 169 backlog lines (88 parked, 50 rework); this check is the precondition for any
new bracket rule.
Data: SHORTUP's cache (512 top-adv names incl. SPDRs; daily + 30-min, 2025-04..2026-11; 206,191 name-days, 409 days).
`sizetrend.py` -> `sizetrend_out.txt`.

| |gap| / ATR quintile (known 09:30) | median |gap|/ATR | range after 10:00 / ATR | efficiency after 10:00 | P(eff >= 0.6) | whole-day eff |
|---|---|---|---|---|---|
| Q1 | 0.03 | 0.715 | 0.452 | 0.319 | 0.448 |
| Q3 | 0.18 | 0.725 | 0.454 | 0.326 | 0.450 |
| Q5 | 0.52 | 0.838 | 0.452 | 0.322 | 0.454 |
Efficiency Q5 - Q1: -0.0006 (day-t -0.20). Range Q5/Q1: 1.14.

Reading: the gap predicts a modestly bigger afternoon (+14%) and nothing about its shape. Efficiency is flat across
quintiles at ~0.45, the level of an undirected path. So a direction-free bracket on predicted-big names has no edge in R, before
costs. 'Size is predictable' is usable for RISK (vol-scaled size bands, SZBAND / PVSCALE, already adopted) and for choosing
WHERE reps come from (bigger moves = fewer cost-dominated trades). It is not usable as a stand-alone, direction-free entry.
Only convex instruments (options) monetise size without direction, and we don't trade them.
Scope: this tests gap-based size only. A size predictor that also predicted path shape (efficiency) would change this; none
of ours has been shown to.
