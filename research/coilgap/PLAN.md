# COILGAP — CWT12 coil longs off on SPY gap-down mornings (FROZEN 2026-11-11 09:30 ET, before reading coil R by gap)
Educational only — not financial advice. Research only; no live change. Owner task item 3 (owner-20261111-0821-1),
Lead lead-20261111-0900-4. I have not looked at coil R by SPY gap; COILAM's (checkpoint) result is known and is a different state.

## Rule (one config)
Skip every CWT12 coil long (CWT12-coil-k4-long, CWT12-coil-k6-long) on a session whose SPY gap <= -0.25%.
SPY gap = official daily open / prior session's official close - 1 (Alpaca daily SIP bars). Known at 09:30, before any coil
entry. It is the long leg of Phase 1's GAP-U state (GAP = SPY gap +-0.25%; longs off on -1).
The first session after the locked block (2025-03-03) gets gap = NaN, and the rule keeps its trades (Skeptic's fix, a).
The locked block 2024-11-01..2025-02-28 is never fetched or read (SPY is fetched in two ranges around it; asserted).

## Data
research/compassbf/coil_tagged.csv.gz (20,779 trades, 445 days, columns r = net R, gross, spy_move, side, date).
TRAIN <= 2025-09-30 < VALID. Ex-market R = R - beta x side x spy_move, beta per setup fitted on TRAIN only (as COILAM).

## Score: shared-day random switch (Skeptic skeptic-20261111-0900-1)
Rule: removes all coil-long trades on D gap-down days. Null: draw D random days from the coil trade days in the same split
(TRAIN / VALID separately, preserving each split's count). Remove all coil-long trades of BOTH setups on those days (one
permutation shared by k4 and k6). 5,000 draws. Statistic: kept-book total R, rule minus null mean; z = (rule - null mean) /
null sd; p = share of draws >= rule. Computed on gross, net and ex-market R. Reported for ALL, TRAIN, VALID, and per setup.
Also: removed n / share, kept avg R (gross, net), w/o-best-day kept avg, and SPY open->close on gap-down vs other days
(Skeptic c: whether the gain is market direction).

## Bars and pass
Lineage: REGSW (Builder's REGSW-2 at 103) + 1 = 104 -> BAR90 2.74 to call a lead (forward shadow). Any Testing move needs the
market-state family N 2,605 -> BAR90 3.57 (Lead 11-10).
Pass (shadow-worthy lead): ex-market z >= 2.74 over ALL, AND z > 0 in TRAIN and in VALID, AND k4 and k6 each not worse than
their own null mean (per-setup harm), AND the kept book's gross avg R > 0. Below 2.74 -> closed (one look).

## RESULT (one look, 2026-11-11 09:45 ET) — FAIL, COILGAP closed
`python -I research/coilgap/coilgap.py research/compassbf/coil_tagged.csv.gz <spy cache>` -> `coilgap_out.txt`.
20,779 coil long trades, 445 days. 107 gap-down days (TRAIN 40 / VALID 67) remove 4,716 trades (22.7%).
- Removed trades are worse in raw terms (net -0.103 vs kept -0.073 R; gross -0.029 vs -0.002), but almost all of that is the
  market: ex-market -0.090 vs -0.084.
- Shared-day random switch, ex-market: ALL z -0.01 (diff -1.4R), TRAIN +0.08, VALID -0.06. Net z +0.56, gross z +0.68.
- Per setup ex-market: k4 -20.5R (harmed), k6 +20.0R. The kept book's gross avg R is -0.0015 (not > 0).
- SPY open->close on gap-down days averages -0.008% (vs +0.004% on other days), so the day itself does not keep falling. The
  coil trades on those days lose through their market beta over their own hold (k4 beta 0.93, k6 2.14).
Reading: the SPY gap state carries nothing for coil longs beyond market beta, the same as COILAM.
