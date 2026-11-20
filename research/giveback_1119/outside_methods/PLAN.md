# Outside exit methods (giveback_1119/outside_methods): pre-registered plan

*Educational only. Not financial advice.* Written 2026-11-20 before any of these exits was scored. Research only:
no setup, exit or config change. A passing class would go to `research/backlog.jsonl` and ship only outside 09:30-16:00 ET.

## Sources opened (only these are cited)
1. Robot Wealth, K. Longmore, "Stop Losses: Rethinking Conventional Wisdom" (2025-05-30),
   robotwealth.com/stop-losses-rethinking-conventional-wisdom/. P&L-based exits help only when the trade's own P&L
   predicts its future return (trend); otherwise they cut the edge. A backtest that improves with stops is more often
   fitted to noise.
2. Quantpedia, "Trend-following Effect in Stocks", quantpedia.com/strategies/trend-following-effect-in-stocks.
   Volatility-scaled exit: a 10-period ATR trailing stop. ATR multiples 8-12 gave no material difference. Looser stops
   gave higher win rates and lower win/loss ratios.
3. Quantpedia, C. Dujava, "Lunch Effect in the U.S. Stock Market Indices" (2024-08-21),
   quantpedia.com/lunch-effect-in-the-u-s-stock-market-indices/. SPY is weak or flat into lunch and turns up after it,
   a clock-time reversal pattern.
4. arXiv 1701.03960, T. Leung and H. Zhang, "Optimal Trading with a Trailing Stop" (abstract). It proves that a sell
   limit order (take-profit) used together with the trailing stop is optimal, which supports a partial or fixed take
   profit plus a trail.
5. arXiv 1005.3535, S. Heston, R. Korajczyk and R. Sadka, "Intraday Patterns in the Cross-section of Stock Returns"
   (abstract). Half-hour returns continue at daily multiples, and short-term reversal comes from liquidity imbalances
   that last under an hour. This motivates clock-time exits rather than elapsed-time exits.

Could not open: arxiv.org through WebFetch (DNS; reached through curl/export API instead), dspace.mit.edu (Kaminski and
Lo, "When do stop-loss rules stop losses?"), nd.edu (Gao et al. intraday momentum), alphaarchitect.com (403),
papers.ssrn.com (403). These are not cited as read.

## What MCF has already tried (not repeated)
- Fixed 1R trail after +1R (Wave 2, parked). Breakeven stops: book-wide (off), BE50/BE75 (BEREPLAY), L16 near-target BE (failed).
- Scale-out: half at +0.25/+0.35R with the rest at breakeven, on 7 CWT14/CWT12 setups in Testing 2 (ledger 10-16/10-17).
- SPY-since-entry exit (spy_exit_pct) on RW3/RW5 WB4 only (ledger 11-16).
- State-conditioned elapsed-time cuts (sibling time_in_trade: FAIL). MAE-based early cuts are the same as its class A
  ("never worked", mark < r), so they are **not** re-tested here.

## Exit classes (all new to MCF in this form)
Each class is walked on 1-minute bars with BEREPLAY geometry (live geometry, stop-first inside a minute, the target
stays in place unless stated). Exits caused by the new rule pay the bt_all exit cost (0.01 + 1 bp) **plus an extra
0.01/share**. Trail or stop-type exits also pay the bt_all stop slippage (0.02). All costs are multiplied by the
bt_all tier. Unit = stop distance (D).
- **O1 Chandelier / ATR trail (volatility-scaled)**: ATR = mean 1-minute true range of the last 14 bars, using bars
  through the previous minute (day bars only). Arms once the best close since entry is ≥ a·D in favour. Level for
  bar i = best close through i−1 ∓ k·ATR(i−1), never looser than the original stop. Fills at the level, or at the bar
  open if price gaps through. Grid a ∈ {0.5, 1.0} x k ∈ {3, 6, 10} = **6 configs**.
- **O2 Scale-out + runner**: bank half at +x·D with a limit fill (stop-first: if the stop and the level are touched in
  the same bar, the stop wins). The runner keeps the target and its stop is r = original, or entry (breakeven) from
  the next bar. x ∈ {0.5, 1.0} x r ∈ {orig, BE} = **4 configs**. The scaled half pays exit cost + 0.01 extra. If the
  target is ≤ x·D, the class does nothing for that trade.
- **O3 Index turn (SPY reversal from its best since entry)**: per minute close, SPY's best close since the entry
  (signal-bar close) in the trade's direction. Exit the stock at that minute's close when SPY has retraced ≥ z% from
  that best and the trade's mark ≥ m. z ∈ {0.25, 0.50} x m ∈ {none, +0.5D} = **4 configs**.
- **O4 Clock exit (time of day)**: a trade still open at clock time Tc exits at the close of the minute before Tc,
  if c = all, or only if its mark ≥ +0.5D, if c = winners. Tc ∈ {12:00, 13:00, 14:00, 15:00} x c ∈ {all, winners} =
  **8 configs**.
A rule fires only before the base exit (a base stop or target in the same minute stands).

## Data and protocol (WB2)
- The parent's own signals: first signal per (setup, symbol, day) of bt_lab1104 (the map's sample), cache_hist
  1-minute bars, bt_all costs. The locked block 2024-11-01..2025-02-28 is filtered at read and asserted absent.
  Delta = variant net R − base net R on the same trade (paired).
- Fit = sessions ≤ 2025-09-30, check = later. Family = setup prefix (GEN pooled), split by side.
- **Per class, per family-side**: pick the config of that class with the largest fit total delta. Adopt it only if
  fit avg delta > 0, fit day-clustered t ≥ 2.0, fit delta without its best day > 0, and it changes ≥ 100 fit trades.
  Otherwise the family keeps the base exit. Secondary: one book-wide config per class, chosen on fit.
- **Configs: 22 per family-side x 36 family-sides = 792, + 22 book-wide = 814 (this class).** Lineage: map 916
  descriptive cells + time_in_trade 2,664 + day_lock 16 + 814 = **N 4,410**, bar = max(1.5, sqrt(2 ln N)) = **4.10**
  (4.63 at 10x N).

## Check half (scored once per class)
Report per class: total and avg R before and after, paired day-clustered t of the delta, avg R without the best day
before and after, best-day share of the improvement, per family-side and per setup better/worse counts and sizes
(total R and avg R), the secondary book-wide rule, and the far-target pocket (t1s05 setups) separately.
Live: the live minute bars were deleted after the map and the live parquet holds only checkpoints, so live scoring is
descriptive only and only if a class passes on the lab (stated, not hidden).

## Pass rule (pre-registered, from the task)
On the check half: total R and avg R improve after costs; avg R without best day not worse; best-day share of the
improvement < 50%; more families and more setups better than worse; and the paired day-clustered t ≥ 4.10. All must hold.
