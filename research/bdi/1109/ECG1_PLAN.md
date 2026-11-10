# ECG1 — early compass gate for momentum shorts (pre-registered 2026-11-09, before any two-year read)

*Educational only — not financial advice.*

**Source.** Swing autopsy 11-09: Primary's −18.1R was Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD`
17 shorts entered 10:20-10:51 **after the live W60 compass confirmed UP at 10:00** (held all day, 0 flips). The 11:00
GATE1 checkpoint gate came too late (dropped 0 Primary entries). The nightly MF1109 B / B2 proxy (SPY/VWAP/QQQ/IWM only,
no breadth, MF only) was a near-miss (VALID t 2.51 / 2.56 vs 2.64) but lost on lab rows after 10-05 (−123R).

**Rule (ONE configuration).** Block a new *momentum short* when the entry minute is at or after 10:00 ET and the
**W60 15-min compass at the latest mark ≤ the entry minute (marks 10:00, 10:15, ... 15:30) reads UP-confirmed (+2)**.
W60 exactly as research/bdi/hc1/comp15.py (votes: SPY from-open sign, SPY VWAP side, breadth_open side, SPY/QQQ/IWM
agreement, + persistence = from-open sign the same at every 15-min mark of the last 60 min; confirmed = votes ≥ 4 with
persistence and ≥ 2 marks), point-in-time state of research/bdi/hc1/state15.py (1-min cache, bars closed by the mark;
breadth_open from the lab context, GATE1 convention). Entries before 10:00 are untouched; when W60 is no longer +2 at a
later mark, shorts are allowed again (state, not latch).

**Momentum-short family (fixed by name, before scoring):** lab short setups matching `^(NM-)?MF\d`, `flowsell` or `^L3-`
in research/history2y/data/bt_lab1104: MF1, MF2-FD, MF3-FD, MF4, MF4-FD, MF5-FD, NM-MF3-qqqdn, RW1-FD, RW3-FD, RW3S-FD,
RW5-FD, L3-fromopen / lowdist / rsi5hi (14 setups). Fades / reversion shorts (exhaustion, CWT, NS, RW2/4/6/7) and GEN
(own index gates) are out of scope.

**Data / splits.** bt_lab1104 lists (uncapped, production costs in), **locked block 2024-11-01..2025-02-28 excluded
(asserted)**. TRAIN 2024-10 + 2025-03..2025-12, VALID 2026-01-01..2026-10-05, LATE lab rows 2026-10-06..11-04 (context).

**Pass bar (all must hold).** Configs counted: MF short-gate lineage 33 (BURST1 16 + BURST2 13 + MF1109 4) + ECG1 1 = **N 34**:
1. VALID day-clustered t of the daily delta (−sum R of blocked trades) ≥ max(1.5, √(2 ln 34)) = **2.66** (BAR90 2.39 reported);
2. TRAIN delta > 0;
3. LATE lab rows delta ≥ 0 (the proxy's known failure);
4. Remedies rule: no family setup worse by > 5 % of its |R| in VALID; per-setup better / worse reported.
Reported in any case: blocked vs kept avg R, kept-trade expectancy, QDAY split (SPY open-to-close up / down / quiet at
±0.25 %; SPY vs its open at 10:00), avg R w/o best day of the delta and its share.

**Forward shadow (journal-only, no trading change), from 11-09.** Each session: every live family short (7 accounts,
run 1) entered ≥ 10:00 while the live compass `compass/<date>.csv` (mcf-data-compass) W60 at the latest mark ≤ entry is
`UP-confirmed` is shadow-blocked; tally n and live R (gate gain = −R). Bar: after 15 forward sessions with ≥ 1 blocked
entry, gain > 0 on ≥ 60 % of them and in total, then DECISION. 11-09 is in-sample (the lead came from it).
