# Skeptic's pre-score checklist (guild, from days 1-3; 2026-11-11)

*Educational only — not financial advice.* Every item below was a real bug or trap caught on this board. Run the list on any
plan or script BEFORE scoring; each line names where it happened so the reason is traceable.

## A. Look-ahead (information from after the decision)
1. **Negative index wrap.** `x[b - k]` with small b silently reads the END of the array (numpy). Slices go empty instead (a NaN
   nearby is the symptom). Assert `b - k >= 0`. (HODSEP v1: 66% of candidates read the same day's 15:50 close.)
2. **Ties at bar / mark boundaries.** A mark or reading at minute T is usable only after T (live publishes at T + 1 min). Use
   strict `<` for "known before entry". (GATE2 Amendment 2; compass re-tag changed 36% of tags.)
3. **Default values in time lookups.** `dict.get(tod, 999)` turns unknown times into "always known". No defaults; assert.
   (GATE2 sizing.)
4. **Whole-day labels (events AND controls).** "Held day", "flipped day", "up day" defined over the whole session are hindsight for an intraday entry.
   Use "not yet flipped at entry". Day-type splits are fine for REPORTING only. (RCOMPASS held_day; counter-to-morning row.)
5. **Selection window overlaps outcome window.** "Untriggered in the first 10 min" is part of the trade's own result: only the
   continuation after the selection time is tradable. (CONFIRM skip part t 19 = path continuity.)
6. **Event dates.** Report date != reaction session (AMC -> next session); intraday reports are look-ahead for morning rules;
   vendor fields (surprise) may fill in late. Get a gap-alignment table before reading outcomes. (EVD1; earnings_yf.)
7. **Snapshots must be provably pre-decision.** Check the producing code (write-once cache?), commit history, and fallback
   paths (`source`, `complete`). (FAMC calendar.)
8. **Gaps across the locked block.** `shift()` / `rolling()` across the dropped 2024-11..2025-02 hole makes a 4-month "day".
   NaN the first row after a > 5-day gap. (GATE2 A3.)

## B. Controls that are not neutral
9. **Losing-book volume cut.** On a book with negative average R, ANY rule that trades less (gate, filter, smaller size, skip,
   "enter only if") scores positive. Judge on EXCESS over a same-day random block / same-share random skip of equal size, and
   print kept avg R. (BURST2, GATE1, STOPW 85% size cut, CONFIRM skip part.)
10. **The control contains an anti-signal.** Compute the control's own avg R (avg - excess); if it is implausibly bad (worse
    than costs), it is selecting losers. Match on distance-to-stop and time. (GATE2 C1 -0.21R -> C1m halved the excess.)
11. **Mechanism vs proxy.** A random-name control does not separate "lag catch-up" from "driver momentum"; add hedged R and
    a same-event non-laggard control. (SC2: it was driver momentum.)
12. **Opposite-condition controls inflate excess.** "Failed holds" are fades by construction. Descriptive only. (SC1 C1.)
13. **Stratify random blocks** by sub-variant when variants differ in mean R. (CWT14SKIP.)
14. **Non-event controls need the FULL event calendar**, not the subset the rule uses. (FAMC.)

## C. Units and market direction
15. **R next to ATR.** Positive mean R with ~0 move in ATR = R-normalisation (tight-stop winners), not price. Print both and
    median R. (fresh-high longs +0.058R / -0.003 ATR.)
16. **Ex-market everywhere.** Split R by SPY up / down / quiet AND subtract beta x SPY over each leg's own hold (stopped legs
    end early). Most "edges" here were market direction. (L1-L6, counter-to-morning, WHATWORKS, D2PM down-day cell.)
17. **Gross first.** If gross is ~0 and the net loss equals the cost charge, the edge does not exist. (OD0950: -0.10R net in
    every decile = cost.)

## D. Data and sample
18. **Earnings blackout.** Lab trade lists ignore the live +-4-day blackout; a filter whose skips sit on event days vanishes
    live. Check the blackout share of skips. (CWT14SKIP: 51.5% -> blackout-free t 1.05.)
19. **Universes chosen by our own signals** (names we traded) are selected. Use the fixed lab list. (D2PM.)
20. **Classifier precision on a pre-filtered set** overstates live precision. Use the full-universe denominator. (option C
    news: 0.91 -> 0.58.)
21. **Date caps.** Scripts reading live journals must fix the window, or reruns drift. (obs-genlate.)
22. **Split-adjusted bars vs unadjusted live fills** need a price-match guard. (obs-min10.)
23. **Re-check short live windows with the newest day** before acting. (RW7 'survivor' erased by 11-10's -28.7R.)

## E. Counting and reading
24. **Family try-count**, not the study's own N: a new driver or universe does not reset the bet. (laggard family 92;
    market-state gates 2,605.)
25. **"N of N variants better"** is not N confirmations when variants fire on the same symbol-days. Count distinct events.
26. **Post-hoc cells:** count the cells shown; a null cell gets 4 same signs 1 time in 8. (EVD1 AMC cell.)
27. **PBO ~0.5 = selection uninformative**, not "overfit"; equal real edges also give ~0.4-0.5. Read with p_oos_loss.
    (XA-PBO.)
28. **mfe-based give-back** overstates an exit fix ~10x; only a bar replay settles it. (BEREPLAY.)
29. **20 forward sessions** can only rule out harm (e-process power 0-19%); confirmation needs EDGE or 40-60 sessions.
    (XA-EPROC.)
30. **Too consistent = suspect.** All days the same sign on a descriptive scan -> look for look-ahead first. (HODSEP.)
31. **Random baselines must keep the rule's correlation structure.** A day-level rule that switches many setups on the
    SAME days needs one shared day permutation per draw, not independent permutations per setup (too-narrow null).
    (REGSW GAP-U.)
32. **Status snapshots applied backwards** (ETB / shortable lists, index membership) are survivorship look-ahead; report the
    result with the filter off. (REGSW ETB proxy.)
