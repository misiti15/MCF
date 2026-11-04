# flow1_1104: "the book as a sensor" (pre-registration)

*Educational only — not financial advice.* Written 2026-11-04 ~13:15 ET, before any FLOW1 result was computed (only row
counts per journal were looked at). Research only: nothing in config/, mcf/, setups, exits, docs/live or the ledger is
changed. Market is open; no trading-path change of any kind.

## Question (owner 2026-11-04, FLOW1)
If the short-side trades that CLOSE early in the morning are mostly winners, do later short entries that day do better?
Same for longs. And does that say anything the market itself (SPY) does not already say?

## Signal (point-in-time)
For checkpoint **T ∈ {10:15, 10:30, 10:45, 11:00} ET**, per book, per day, per side s ∈ {long, short}: the trades of
side s whose **exit timestamp ≤ T** (nothing else: open trades and later exits are not known at T).
- n_s(T) = count; sumR_s(T) = realised R sum; win_s(T) = share with R > 0.
- **Measure m ∈ {sumR, win}:** "confirmed" = n ≥ k and (sumR > 0 | win share > 0.5); "contra" = n ≥ k and not
  confirmed; "unknown" = n < k (trades as baseline).
- **k ∈ {3, 5}.**

## Outcome
Trades of side s **entered strictly after T** (entry timestamp > T), same day, same book. R after costs.

## Rules scored (vs baseline = all later trades)
- **(a) filter:** after T, later trades of side s are taken only if s is confirmed or unknown; contra side dropped
  (so both / one / neither side can trade).
- **(b) scale:** later lots ×1.5 on a confirmed side, ×0.5 on a contra side, ×1 unknown.
- Score = delta R per day = R(rule) − R(baseline) over later trades; day-clustered t over days; avg R of kept vs
  dropped trades; delta without the best day and that day's share of the total.
- **Configurations per book:** 4 T × 2 k × 2 m × 2 rules = **32**.

## Data
1. **Live (paper, rule 7):** `journal.db` on origin/mcf-data (Primary), mcf-data-testing, -testing2, -graveyard, -gen;
   `run_id = 1`, closed trades, **2026-10-06..2026-11-03** (11-04 is in progress, excluded).
   R = pnl_adj / (|entry − stop| × shares). Books: **Primary alone** and **all five merged** (merged signal = all
   accounts' early closes, merged outcome = all accounts' later trades). 2 books × 32 = 64 live configurations.
   SPY 1-min SIP bars (read-only GET) for the controls.
2. **Lab (2 years, backtest):** the latch_1103 reconstruction (research/bdi/latch_1103/bt_all.py: every enabled lab
   setup, signals walked on the 5-min path to an exit time, production costs, account caps 3 lots/symbol and 30 open
   per setup as latch amendment 1), all setups merged as one book. TRAIN = open dates ≤ 2026-02-28, VALID =
   2026-03-01..2026-10-07. **Locked block 2024-11-01..2025-02-28 never read.** 32 configurations; one rule chosen on
   TRAIN (best day-clustered t), then scored once on VALID.
- **N total = 32 (lab) + 64 (live) = 96 → bar t ≥ max(1.5, sqrt(2 ln 96)) = 3.02.** Day-clustered.

## Key control: beyond SPY (rule 6)
Per (day, side, T) and per trade:
- x_book = side's early-close signal (sumR_s(T) and the confirmed/contra sign; side-own),
- x_spy = s × SPY % from its 09:30 open at T (REG1-style),
- x_vwap = s × (SPY / SPY session VWAP at T − 1) (VWAP from 09:30 1-min bars, typical price × volume).
1. Trade-level OLS of later-trade R on x_book alone, then x_book + x_spy + x_vwap; standard errors clustered by day.
   **Incremental value = x_book's coefficient and t once SPY terms are in.**
2. Conditioning: the rule's delta inside SPY-at-T buckets (side-aligned SPY move > +0.25% / ±0.25% / < −0.25%).
3. Head-to-head controls (same scoring): SPY rule (later shorts only if SPY ≤ open at T, longs only if ≥), VWAP rule
   (same with VWAP), and FLOW1 applied **on top of** the SPY rule (its delta over SPY rule alone = what it adds).
   If the early closes only restate SPY's move, the notes say so plainly.
- Day type split (diagnostic, not point-in-time): SPY open→close > +0.25% up, < −0.25% down, else quiet.

## Simple picture (step 4, reported regardless)
T = 10:30, k ∈ {3, 5}: days on which the side's first k closes (by exit time, all by 10:30) were net green (sum R > 0)
vs net red; later trades of that side (entered after 10:30): n days, n trades, win share, avg R. Long and short, per book.

## Decision rule (fixed)
DECISION card only if one rule (chosen on lab TRAIN) passes lab TRAIN and VALID (delta > 0 both, t ≥ bar on TRAIN or
pooled), holds live (delta > 0 on Primary and merged), and adds beyond SPY (x_book t ≥ 2 with SPY terms in, live and
lab, and positive delta on top of the SPY rule). Otherwise FYI + forward-shadow rule `flow1-book-sensor` in
research/bdi/swings/hypotheses.jsonl. Live ledger changes inside 10-06..11-03 are listed beside the numbers.
