# MFX1 — midday-flip open-book exit (pre-registered 2026-11-10, before any two-year read)

*Educational only — not financial advice.* Source: swing autopsy 11-10 (Primary +8R midday → −31R after SPY flipped back
above its open) and nightly backlog `nightly-1110-midday-flip-open-book-exit`. ONE configuration. Lead id `swing1110-L12`.

**Rule (exact).**
1. Morning side M = sign of SPY's 1-minute close of the 11:59 bar vs SPY's 09:30 open (no threshold; M = 0 → no rule).
2. Flip minute F = end of the first run of 15 consecutive 1-minute SPY closes (bars starting 12:00..15:29) on the side −M
   of the open (strictly). No flip → no action.
3. At F, every open trade on side M (shorts if M = −1, longs if M = +1) whose entry is before F and whose exit is after
   the last 5-minute bar closing at or before F is closed at that bar's close (mark-to-market, stop units), minus an exit
   cost of 1 bp + $0.01 / share (production costs) in R. Entries after F are untouched (the guild's 11-10 rcompass showed
   "standby" for new entries does not earn). Trades on side −M untouched.

**Data.** 2-year lab lists bt_lab1104 (every lab setup, both sides), enriched with 5-minute mark-to-market paths
(burst1/enrich.py, scratch burst2/enr); SPY 1-minute cache. Locked block 2024-11-01..2025-02-28 excluded (asserted).
Splits: TRAIN 2024-10 + 2025-03..2025-12, VALID 2026-01-01..2026-10-05, LATE 2026-10-06..11-04.

**Pass bar (fixed now).** Lineage = compass-learn FLIP detector configs (33) + this = N 34 → full bar day-clustered
t ≥ 2.66, BAR90 2.39. Day-t = mean / s.e. of the daily delta (rule − actual, R, costs in) over days the rule acts.
Pass = VALID t ≥ 2.66 AND TRAIN delta > 0 AND VALID delta without its best day > 0 AND ≥ 60 % of setup families
(≥ 30 affected trades) better. Owner remedies rule: report every family better / worse and by how much. QDAY: delta by
SPY day type (open→close ±0.25 %) and by SPY vs its open at 10:00. False flips (day closes on side M) reported
separately.

**Forward shadow (every later session, all accounts with trades on side M).** Pass bar: ≥ 15 flip sessions, total
delta > 0 and delta > 0 on ≥ 60 % of flip sessions (Primary + Testing 1 + Testing 2 + Graveyard pooled; Primary
reported alone). A forward pass becomes a DECISION for a Testing account trial, never straight to Primary.
