# sat1114 give-back proposals — pre-registered before any score (BDI Saturday 2026-11-14)

*Educational only — not financial advice. Research only: no config, setup, exit or assignment changes.*

Week finding that motivates both (giveback.py, mtm snapshots): Primary gave back 95R peak→close over 11-09..11-13, of which
**entries after the peak −68.8R** (open winners −23.7R, twins −8.7R). On Deck 116.6R (after-peak entries −71.1R). Both
remedies act only on NEW entries after a give-back has begun; open trades and exits are untouched (winners not shortened).

Data: lab trade lists `burst1/trades_2y.parquet` (95 setups, production costs as of 11-04, account map of 11-04, entry /
exit minute; 1,102,755 rows, 2024-10-01..2026-10-05). **Locked block 2024-11-01..2025-02-28 absent from the file (0 rows,
asserted)**; `MCF_HIST_ALLOW_LOCKED` never set. TRAIN ≤ 2026-02-28, VALID 2026-03-01..10-05. Live check: this week's
journals (run 1), effect = R of the trades the rule would have blocked (realised-only replay).

Base = the live per-setup realised −2R latch (a setup stops for the day once its R booked from exits before the entry ≤ −2).

## Configs (4; BURST / give-back lineage 36 → 40, bar max(1.5, √(2 ln 40)) = 2.72)
- **G1 `trail2`** per-setup trailing latch: also stop the setup once its booked day R ≤ (its day high of booked R) − 2R
  (high floored at 0, so at a 0 high it is the live −2R latch). Targets a setup that was up and keeps re-entering into a fade.
- **G2 `trail3`**: the same with 3R.
- **G3 `acct10`** account give-back brake: no new entries in the account for the rest of the day once the account's booked
  day R ≤ (its day high of booked R) − 10R (high floored at 0), on top of the base latch. Per account (primary, testing,
  testing2, gen, graveyard of the 11-04 map).
- **G4 `acct15`**: the same with 15R.

## Pass (all required; unchanged BURST2 logic)
VALID Δ t ≥ 2.72 and VALID excess t ≥ 1.0 (gain beyond removing random trades at the setup mean); TRAIN Δ > 0 and excess > 0;
live week Δ ≥ 0 (all 8 accounts in scope); no family harmed (Δ < 0 with t ≤ −1, or worse > 2 × improved and Δ < −5% of the
family |R|); trades removed ≤ 10% of the base (owner: "not limit trade count much"). Reported per setup and family
(improved / worse and by how much), Primary book separately, and the give-back effect (peak − close of the booked-R curve).
