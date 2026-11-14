# ANCHOR950 — the index null on the owner's 09:50 anchor (descriptive, 0 configs)
Educational only — not financial advice. Owner rule 2026-11-14 (CLAUDE.md, 'Direction research anchor'): no 09:30 entries;
direction research uses the ~09:50 state and the 09:30-09:50 range as the reference, studies what follows the early swings (e.g.
a dip in the first 20 minutes, then a turn up), and scores by the return after the decision time. LEAD20 / ETFTIER / SHORTUP
used the 09:30 open as the reference, so this re-checks the index null on the owner's anchor.
Data: LEAD20 cache (5-min SIP, 2024-10..2026-11, locked block absent; 453 sessions). `anchor950.py` -> `anchor950_out.txt`.
Decision price = open of the 09:50 bar; early range = high / low of the 09:30-09:45 bars.

| SPY (bps after 09:50) | n | -> 15:55 (t) | -> 10:50 (t) | TRAIN / VALID -> close |
|---|---|---|---|---|
| all days | 453 | +2.2 (0.57) | +0.7 (0.40) | |
| dip-then-turn (dipped >= 1/4 range below the open, back in the top 40% of the range) | 116 | +6.0 (1.00) | +5.3 (1.37) | +17.2 / -0.9 |
| pop-then-fade (mirror) | 96 | +0.5 (0.07) | +0.1 (0.02) | -13.9 / +7.4 |
| at the top of the early range (pos >= 0.8) | 131 | +7.9 (1.57) | +3.3 (1.04) | +16.2 / +2.5 |
| at the bottom (pos <= 0.2) | 99 | +3.1 (0.45) | -0.3 (-0.07) | -4.1 / +7.6 |
| break above the early high -> close | 326 | +3.7 (0.91) | | |
| break below the early low -> close | 291 | +0.1 (0.02) | | |
QQQ, SPXL and TQQQ: same picture. SPXL dip-then-turn is +25bps (t 1.38) and pos >= 0.8 is +27bps (t 1.77), but TRAIN / VALID
flip or shrink (+65 / -5; +55 / +9). TQQQ cells are all |t| < 0.9. 40 cells shown; none reaches |t| 2.

Reading: on the owner's anchor the null holds. After the first 20 minutes, the early pattern (dip-then-turn, pop-then-fade,
position in the early range, a break of it) carries no reliable direction for the rest of the day in the index or its 3x ETFs.
The strongest-looking cells (SPY/SPXL near the top of the early range) are TRAIN-driven (the April-2025 rebound sits in TRAIN).
They are worth at most a forward e-process shadow, not a rule. Any up-day rule should be scored against THIS table (09:50
reference) from now on, alongside Observer's 09:30-reference null.
