# BDI Saturday deep run 2026-11-07: pre-declared plan (written before anything below is scored)

*Educational only — not financial advice.* Research only: no config, setup, exit or assignment changes. Costs in on every
number (live: journal `pnl_adj`; two years: lab trade lists `bt_lab1104` with production costs). The locked block
2024-11-01..2025-02-28 is never read (`MCF_HIST_ALLOW_LOCKED` never set; the BURST2 / FB1 inputs already exclude it
and every script asserts it). Old holdouts (Apr–Jun 2026, ≥ 2026-09-16) are inside VALID / not used for tuning; no
holdout is scored tonight (no finalist will reach that stage unless it passes VALID + live first).
Splits as in the parent studies: BURST lineage TRAIN ≤ 2026-02-28, VALID 2026-03-01..10-05, LIVE 10-06..11-06 (7 paper
journals incl. latch / halt-blocked what-ifs); FB1 lineage train < 2025-09-01, valid after.
QDAY focus (owner, through 11-17): every row reports its R split by SPY day type (open-to-close > +0.25% up,
< −0.25% down, else quiet).
Not duplicated: ROTA1 (rolling Primary re-evaluation, FAILED N=975, branch claude/rota1-1107) and the Primary
re-evaluation agent (wt-preval). Nothing here re-ranks Primary setups.

## Block A — burst / give-back near-misses (rework of `burst2-flush-gate-short`, `burst1-openloss-latch3`; BURST lineage 29 → 36)
Overlays on the BURST2 trade tables (`trades2_2y` / `trades2_live`, unchanged harness `burst2/score2.py` logic):
- A1 `D_flush_2_30`: block a setup's 3rd+ short within 15 min when QQQ 30-min return ≤ −0.30% (neighbour of 0.40%).
- A2 `D_flush_2_50`: same, ≤ −0.50%.
- A3 `D_flush_3_40`: 4th+ short (B = 3), ≤ −0.40%.
- A4 `D_flushQ_2_40` (QDAY-targeted): the flush gate only when SPY is not down from its open at entry (SPY from-open ≥ −0.25%)
  — selling an index flush inside a range / up tape is the 11-06 failure; on a real down tape (11-05) the shorts are kept.
- A5 `D_flushQ_2_30`: A4 with −0.30%.
- A6 `latch_or_-3`: the live realised −2R latch **plus** an open + closed (5-min marked) −3R latch (either one stops new entries),
  i.e. the burst1 −3R latch added to, not replacing, the live latch.
- A7 `A4 + A6` (pair).
Pass (BURST2 decision rule, unchanged): VALID Δ t ≥ max(1.5, √(2 ln 36)) = 2.68 and VALID excess t ≥ 1.0; TRAIN Δ and
excess > 0; LIVE all-accounts Δ > 0; no family harmed (Δ < 0 with t ≤ −1, or worse > 2 × improved and Δ < −5% of family |R|).
Reported per config: Remedies table (setups / families better vs worse and by how much, Primary and all accounts), R split
by SPY up / down / quiet, Primary 11-04 / 11-05 / 11-06, and the give-back effect (peak − close of the realised-R curve by exit
time, Primary-account setups on VALID and the live Primary book).

## Block B — `burst2-mf-after-flush-rework` (setup-level, new lineage N = 6)
Lab trades of `MF2-open-rsimidhi-flowsell-FD` and `MF4-h40-open-flowsell-FD`; drop entries with QQQ 30-min return ≤ −y at
entry, y ∈ {0.30, 0.40, 0.50}% (3 × 2 = 6). Scored as a setup: avg R after costs, day-clustered t vs BAR90
0.9 × max(1.5, √(2 ln 6)) = 1.70 (full bar 1.89), positive in up AND down sessions (and quiet reported), walk-forward months
≥ 54%, avg R without the best day (+ share), excess vs the parent's removed trades, live (paper) check on the same filter.

## Block C — FB1 flush-chase rework (lineage 4 → 8)
FB1 harness (`1105/fb1.py` features: entry-bar `dist_lod_atr`, QQQ distance from its low, SPY from-open at entry).
The FB1 2-year read said index-flush shorts lose on quiet / up days and win on down days, but day type is hindsight. Rework
uses the at-entry proxy (SPY from-open ≥ −0.25%):
- C1 guard lab shorts with `dist_lod_atr` ≤ 0.15 when SPY from-open ≥ −0.25%;
- C2 same with ≤ 0.10; C3 ≤ 0.25;
- C4 C1 plus QQQ within 0.15 ATR of its own low (index flush).
Pass: guarded trades' excess (R − setup train mean) negative, i.e. removing them helps, day-clustered t of the daily Δ
≥ max(1.5, √(2 ln 8)) = 2.04 on valid with train Δ > 0; ≤ 2 × more families harmed than helped; up and down splits not
both negative.

## Block D — GATE1 checkpoint gate: not reworked tonight (stated in advance)
Lineage N = 112, bar 3.07 (look-up rises with N); best row VALID t 2.26 / excess t 1.22. Its trade table needs a full
state + data rebuild; a neighbour cannot plausibly clear 3.1 and the forward shadow is already logging. Kept parked.

## Block E — new ideas (Move Hunt, long side, QDAY; new lineage `sat1107-range-extreme`, N = 4)
Range-tape extremes from the lab signal lists (existing setups' entries, costs in):
- E1a long entries within 0.15 ATR of the session low while |SPY from-open| ≤ 0.25% (buy the flush in a range tape);
- E1b same, ≤ 0.25 ATR;
- E2a short entries within 0.15 ATR of the session high while |SPY from-open| ≤ 0.25% (fade the range high);
- E2b same, ≤ 0.25 ATR.
Testing bar (rule 22): day-clustered t ≥ 0.9 × max(1.5, √(2 ln 4)) = 1.50, WF months ≥ 54%, positive in up AND down
sessions, beats the same-side same-tape baseline (all lab entries of that side with |SPY from-open| ≤ 0.25%), avg R without
best day reported.

**Total configurations tonight: 7 + 6 + 4 + 4 = 21.**

## Give-back proposals (task 5)
At most 2, chosen only from rows that pass their block's rule; if none pass, no proposal (the best candidates are
reported as shadows).
