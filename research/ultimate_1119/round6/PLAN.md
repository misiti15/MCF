Educational only — not financial advice

# Round 6 plan: market-state (regime) gates for the long mean-reversion books (pre-registered 2026-11-19)

Written and committed to the session before any gate is scored. No setup, exit, YAML, account or ledger change.

## Question
Is there a point-in-time market-state reading (known before the session, or at the decision bar) that tells us when
the long mean-reversion edges work, so that a gated book is positive in all three windows?

## Books (trade rows are fixed; nothing is re-tuned)
- **BOOK-EM** = ULT-32 config 32e (leg E late ETF dip + leg M one-bar RSI collapse, ADV >= $500M, RMAX 30).
  - W1: round5/fresh_trades.csv.gz rule R1 (270 rows).
  - W2: re-generated with the frozen round4/ULT-32/bt.py (`sig fit`, `walk fit`, `book(S, 32e)`); must reproduce
    fit_grid.json 32e exactly (270 trades, +0.1879). Done before this plan: reproduced 270 / +0.1879.
  - W3: round4/ULT-32/check_trades.csv.gz legs E + M (341 rows, +0.1148 = check_plateau 32e).
- **ST7-FD** (benchmark, current best).
  - W1: round5/fresh_trades.csv.gz rule R4 (481 rows with R). The known harness flaw (entries after a 13:00 early
    close) is removed: rows on 2023-07-03, 2023-11-24, 2024-07-03 with tod >= 1255 are dropped (reported).
  - W2 / W3: benchmark work dir trades.parquet (bench.py), setup ST7-rsi50dn-long-pm-t1s1-FD, column r1.
- Costs: as stored (LR8; long only, so no borrow).

## Windows
W1 = 2023-01-03..2024-09-13 (427 sessions); W2 = fit = 2024-10 + 2025-03..2025-09 (170 sessions);
W3 = check = 2025-10-01..2026-11-04 (276 sessions). The locked block 2024-11-01..2025-02-28 is never read (pyarrow
date filters on every daily / 1-minute read; the history2y `locked` folder is not opened).

## Features (all point-in-time)
Daily SPY / VXX / universe closes: data/cache_fresh/daily.parquet (2022-10-03..2024-09-13) + research/history2y/data/
daily.parquet (2024-09-16.., locked rows filtered out at read). "Prior" = sessions before the trade date only.
A lookback feature whose window would cross the locked gap (2024-10-31 -> 2025-03-03) is NaN (not bridged).
1. **rv20**: SPY 20-day realized vol of close-to-close returns (prior 21 closes), annualized.
2. **tr20**: SPY prior close / mean(prior 20 closes) - 1.
3. **tr50**: SPY prior close / mean(prior 50 closes) - 1.
4. **ret1**: SPY prior-day close-to-close return.
5. **ret5**: SPY prior close / close 5 sessions earlier - 1.
6. **vxx10** (VIX proxy): VXX prior close / mean(prior 10 VXX closes) - 1.
7. **disp**: cross-sectional std of prior-day returns (clipped +-50%) over names with prior-day adv20 >= $95M.
8. **breadth20**: share of names with prior-day adv20 >= $95M whose prior close > mean of their prior 20 closes.
9. **gap**: SPY today's open / prior close - 1 (known at 09:30).
10. **spy_fo**: SPY at the decision time (close of the 1-minute bar ending at tod+5, the decision-bar close) / SPY
    09:30 open - 1.
11. **spy30**: SPY at the decision time / SPY 30 minutes earlier - 1.
12. **dow**: weekday.

## Gate grid (counted)
- Gates 1-11: direction {keep low, keep high} x keep fraction f in {0.4, 0.5, 0.6, 0.7, 0.8, 0.9} = 12 each. The
  threshold is the f (low) or 1-f (high) quantile of the feature over the training trades (two training windows
  pooled, trades with a known feature).
- Gate 12: drop one weekday (5 options).
- Per book per rotation: 11 x 12 + 5 = 137 configs. Two books x three rotations = **822 configs**.
- N_job = 1,044 (up to 1,060) before + 822 = **1,866 (up to 1,882)**; t bar = max(1.5, sqrt(2 ln 1,882)) = **3.88**.

## Leave-one-window-out
For each held-out window H (W1, W2, W3) and each gate, pick the config on the other two windows by: maximise
min(gated avg R in train window A, gated avg R in train window B); ties -> larger f. Apply that frozen config to H.
Trades whose feature is NaN are left out of that gate's comparison (gated and ungated), and their count is reported.

## Pass bar (per book, per gate)
A gate is **promising** for a book only if all hold:
1. held-out gated avg R > 0 in all three rotations;
2. held-out gated avg R without its best day > 0 in all three;
3. the gate keeps >= 40% of that window's (known-feature) trades in each held-out window;
4. day-clustered t on the pooled held-out gated trades (all three windows) >= 3.88.
Also reported: ungated per-window figures, gated - ungated per window, per-leg effect (E / M) for BOOK-EM, the selected
config per rotation, best-day share. Every gate is reported, including failures.

## Honesty notes (fixed in advance)
- All three windows have been seen in some form (W1 scored once in round 5; W2 / W3 shaped rounds 1-4). A pass is
  "promising, needs the locked block or live forward confirmation", never proven, and is not deployed.
- Already known before this plan: ungated BOOK-EM W1 -0.040 / W2 +0.188 / W3 +0.115; ST7-FD W1 -0.016 / W2 -0.132 /
  W3 +0.084; round 5 saw the W1 damage on SPY full-day down days (a look-ahead label, not usable as a gate).
- Survivorship in W1 (today's symbol list) flatters the books; breadth / dispersion use the same lists.
