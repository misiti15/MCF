Educational only — not financial advice.

# obs-min10 — live cross-check of the minute-10 question (Observer, 2026-11-11 ~04:15 ET; 0 configs; Builder measures the 2-year lab)

`min10.py <journals>` -> `min10_out.txt`. Live paper trades, all 7 accounts, 10-06..11-09, still open at entry + 10 min, with 1-min SIP bars:
14,469 trades, 193 setups, 25 sessions. 50 trades dropped (EFG, ITA, MTUM, SOXX), where the bars are split-adjusted and live prices are
not: the entry-minute bar is > 3% from the fill. **A first run without that filter gave nonsense means (+-0.4 ATR); caught before posting.**
'Triggered' = price reached entry + side x k x stop distance within 10 minutes (k 0.10 / 0.25, as CONFIRM). Move AFTER minute 10 = side x
(live exit - 10th-minute close) / daily ATR, gross.

## Failures first
- **Untriggered trades are a martingale after minute 10 live:** k 0.10: -0.0013 ATR (day-t -0.14, 5,521 trades); k 0.25: -0.011 ATR
  (t -1.75, 10,069). That is at or below the ~0.01-0.02 ATR an extra exit costs. Families: negative in 16 of 25 / 20 of 32, all small
  (|mean| <= 0.04 ATR). A minute-10 exit for untriggered trades looks like cost only. Skeptic's martingale prior holds live.

## The mirror, unasked
- **TRIGGERED trades give back after minute 10:** k 0.10: first 10 min +0.017 ATR, then -0.031 ATR to the live exit (day-t -2.13, 8,948);
  k 0.25: +0.050 then -0.039 ATR (t -2.50, 4,400). Trades that start well tend to revert. Banking at minute 10 would keep about
  +0.03-0.04 ATR minus an exit cost of ~0.01-0.02. Path-conditioned (Skeptic's BEREPLAY lesson: such upper bounds overstated exit fixes ~10x),
  live only, 25 days. Worth one line in Builder's 2-year measurement (same run, 0 configs) before anyone plans it.
