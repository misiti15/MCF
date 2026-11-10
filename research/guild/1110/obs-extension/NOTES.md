Educational only — not financial advice.

# obs-extension — GATE2's selector book-wide: are fresh-extension entries worse before costs? (Observer, 2026-11-09 ~22:30 ET)

Lead's request lead-20261109-2100-4. Descriptive. **2 looks**: EXT at 0.10 ATR (pre-declared in the script docstring before scoring)
and 0.20 ATR (sensitivity). 14,770 live paper trades with bars and ATR (all 7 accounts, 10-14..11-06, 18 sessions; 10-06..10-13
dropped for ATR warm-up), 178 setups, 43 families. Bars: 1-min SIP for 1,522 traded symbols, downloaded after 16:00 ET (guild
research/data/dl.py, stop guard 07:30 ET), into data/cache_hist/1Min (not committed).
Definitions: EXT = the day's extreme in the trade direction (HOD for longs, LOD for shorts, closed minutes before entry) was set
within the last 15 min and entry is within 0.10 ATR of it; PB = entry >= 0.30 ATR from that extreme; MID = the rest.
gross = net + paper cost (as obs-stopcost).
Rule-change context: same window as obs-stopcost (Owner CF cost filter in Testing 1/2 from 10-30; Primary sizing 10-28; per-setup stop changes 10-23/10-29).

## Failures first
- **Book-wide, NO.** EXT entries are not worse: EXT gross -0.045R (1,063, 7%), MID -0.062 (4,998), **PB -0.177 (8,709, 59%)**.
  Day-clustered EXT minus non-EXT: +0.075R, t 1.29, EXT worse on 9 of 18 days. By family, EXT is worse in only 3 of 8 testable families.
  So "don't enter at a fresh extension" is NOT a book-wide remedy. GATE2's selector does not generalise to our live setups.
- At 0.20 ATR the book-wide picture is the same, and top-decile retention fails (89.2% < 90%).

## What it shows instead
1. **Shorts vs longs flip.** Shorts at a fresh low: gross -0.189 (443) vs MID -0.007. **Longs at a fresh high: gross +0.058 (620)**,
   the only positive cell, vs PB longs -0.222 (5,078). Cross-check with obs-longmovers (up-movers sit near HOD): buying strength at
   the high is the one long entry that is not losing live. 620 trades, 18 days, descriptive.
2. **The book's loss sits in PB entries** (59% of trades, ~-0.18R gross): entries far from the day's extreme in the trade direction,
   i.e. dip-buys / counter-trend. Same story as 'our long book is a dip-buying book'.
3. **Flow-sell SHORT family at fresh lows is the one targeted pattern**, at both thresholds:
   MF2 EXT -0.40 vs other +0.28 (29 vs 101 trades), MF4 -0.30 vs -0.01, RW3 -0.10 vs +0.09 (0.20 ATR: -1.00 / -0.49 / -0.37 diffs).
   This is "selling the low after the drop", MarcoFlow's lesson #5 turned around: short the drop, but not at the fresh low.
   Small n (25-39 EXT per family). MF4 top-decile kept 77% (< 90%), so as written it fails retention for MF4.
