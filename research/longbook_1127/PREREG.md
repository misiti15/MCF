Educational only — not financial advice.

# LONGBOOK-1127 pre-registration (coverage): add ONE live long setup to Primary as a diversifier

Written 2026-11-27 evening (market closed), before any book was simulated or any candidate scored. The lot generator
(`lb_gen.py`) was smoke-run on one month for signal counts only (no exits, no R). Research only: no change to config/,
setups, exits, assignments.json, decisions.json or the ledger.

## Why (mechanism)
Primary is ~80% short (P4 = L3-gap-slope-fromopen-FD, RW3-FD, RW5-FD short + NM-ETF-late-dip-di-long). It loses on
up / squeeze days (11-25: longs +256R vs shorts -1,483R across accounts; 11-27: longs +14.3R vs shorts -115.2R). A long
book that earns on up days should be negatively correlated with the short book and cut the worst days, even if it is
only flat on its own. The question is whether ANY existing live long, under Primary's rules and fair costs, adds R/day
or at least cuts the bad tail without costing R.

## Candidates (existing live long setups outside the Graveyard; no new variants)
Picked from the live journals (all accounts, run 1, LR8, to 11-27) and the task list, before any history score:
- **L1 CWT14-failbrk-orl-p10-long-WB5** (Testing D; live 148 tr, +0.076R, w/o best day +0.035). Existing CWT14 variant,
  evaluated only (consultant guardrail: no new CWT14 variants are made here).
- **L2 ULT-05-withgap-cont-long** (Testing E; live 467 tr, -0.025R). YAML time_stop_min 45, 2R catastrophic stop.
- **L3 GEN-261027-10 Lunch Selling-Flush Buy** (holdtr; Testing D; context breadth_open).
- **L4 GEN-261023-07 Lunch Choppy RSI Turn Buy** (hold; Testing 2; context breadth; the largest live long record,
  +90.8R on 11-25 alone).
NM-ETF is already in Primary and stays in the reference book (REF).

## Data, engine, costs
- Lots: bench10 signals (research/ultimate_1119/top10, unchanged: module mask, home-account YAML window / min_adv /
  refire, ATR geometry, CWT head rows) for P4 + L1..L4, via `lb_gen.py`. Exits walked on 1-minute bars (stop first,
  gap-through at the worse of open/stop, target only when traded through by $0.01, flat 15:55) plus the rules bench10
  lacks for these longs: ULT-05 45-minute time exit; GEN `hold` (stop 1R = 0.25 daily ATR, no target) and `holdtr`
  (plus a 1R trail once +1R, from the next bar).
- T2 (2023-01-03..2024-09-13) frames from data/cache_fresh (469 names). The GEN longs need breadth context: for T2 it is
  rebuilt from those 469 names (share above session VWAP / above the day's open per 5-minute bar): a proxy universe,
  flagged in the report. EARLY (pre-2023) is not available for these setups (no stock minute history before 2022-10).
- Book: E4 (cfprimary_1127 e4nb.py, extended from 4 to 5 setup slots, logic unchanged): 77 slots, 30 lots per setup,
  <= 3 per symbol per setup, burst brake 30 / 10 min, realised -2R per-setup latch, -20R closed+open halt (BASE = live
  Primary rules today). Price >= $5; shorts ETB >= 0.9. The parity of the 5-slot engine with the 4-slot engine on REF is
  checked first (|diff| < 0.01R/day) and reported.
- Costs: **LIVE-L** (primshorts_1126 cells_live.json, pooled side model) on the shorts and on the candidate longs; NM-ETF
  LR8 research (as in every E4 study). **LR8** alongside for the candidate longs.
- Splits: FIT 2024-10 + 2025-03..09 (descriptive), **CHECK 2025-10-01..2026-11-04**, **T2 2023-01-03..2024-09-13**.
  The locked block 2024-11-01..2025-02-28 is filtered at load and asserted absent in every script.

## Configurations (N = 8)
For each long Lk (k = 1..4): Primary BASE book + Lk with per-setup cap **C30** (Primary's normal 30) and **C10**
(diversifier size, 10 open lots). REF = P4 BASE without a candidate. Cumulative N ≈ 9,300 → **≈ 9,308**; global family
bar sqrt(2 ln 9,308) ≈ 4.28 is shown for reference only.

## Measures (per config x split)
R/day (REF, cfg, delta), paired day t of the delta, worst-5 days (mean), red days per month (x 21), days <= -10R,
correlation of the long's daily R with P4's short-book daily R, delta by SPY day type (open->close >= +0.25% up,
<= -0.25% down, else quiet), best-day share of the delta (largest single-day delta / total delta) and delta without the
best day, per-setup effect (each P4 setup's R/month change from slot competition), lots taken, LR8 alongside.
**Controls:** size-matched random add: K = 20 shadow books, each long lot replaced by a same-symbol, same-day lot at a
random entry minute inside the setup's window (same %-risk, same exit rule), booked under the same rules; the config's
percentile and the 95th percentile of the shadow deltas. **Stress:** candidate long lots re-walked with entry one
minute later (same stop/target levels) and +2 bp per side extra cost.

## Pass bar (every item on CHECK and on T2 separately)
1. delta R/day > 0 (LIVE-L).
2. paired day t >= 2.5 (study bar: one-sided 0.05 / 8 configs ≈ z 2.5; global 4.28 shown).
3. delta above the random-add 95th percentile.
4. worst-5 not more than 5% worse than REF (cfg mean >= 1.05 x REF mean).
5. red days per month not higher than REF.
6. best-day share < 25% and delta without the best day > 0.
7. stress delta > 0.
8. no P4 setup worse than -2R per month vs REF.
**PASS** = all 8 on CHECK and T2. **LEAD** = items 1, 4, 6, 7 on both splits and t >= 1.5 on both. Otherwise **FAIL**.
A diversifier finding (cfg worst-5 and red days better, delta >= 0) without a pass is reported as context only.
Every config is reported, failures first. Live records are shown with the rule-change context from the ledger.
