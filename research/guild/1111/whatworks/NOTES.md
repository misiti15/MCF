# WHATWORKS — which live setups work after live paper costs, without one big day? (Scout, 2026-11-10 23:40 ET; descriptive, 0 configs)

*Educational only — not financial advice. Live PAPER results (fills are optimistic; Skeptic: paper costs ~1/3 of the lab charge).*

Source: the 7 account journals (mcf-data*, journal.db, live paper run only) to 2026-11-10; R = pnl_adj / (|entry - stop| x shares).
18,878 trades, 194 setups, 2026-10-06..11-10. Filter (Lead lead-20261110-2300-3): setup x account with >= 20 trades on >= 5 days.

**Result: 128 rows -> 28 positive after live costs -> 11 also positive without their best day -> 1 also has best-day share < 50%.**

| setup | acct | n | days | avg R | w/o best | best-day share | lab |
|---|---|---|---|---|---|---|---|
| RW1-gapdn-bounce-flowsell-short-FD | testing2 | 75 | 14 | +0.211 | +0.175 | 34% | (2y: Builder) |

Near-misses (positive and positive w/o best day, but best day >= 50% of the total): RW3 (testing 0.55, primary 0.78), RW5 (testing 0.67,
primary 0.87), MF4-h40 (testing 0.56), L3-gap-slope-rsi5hi-FD (testing2 0.69), L3-gap-slope-fromopen-FD (testing 0.68, 222 trades),
GEN-261026-03 NewLOD lunch short (gen 0.77), CWT09 gap-down bounce lower-half short (graveyard 0.57), MF2-open-rsimidhi (testing 0.82).

**Every one of the 12 is a SHORT** (long share 0), mostly gap-down / flow-sell shorts; most best days fall in the 11-04/11-05 sell-off.
By account (rows with n >= 20): pooled avg R gen -0.165, testing2 -0.166, testing -0.123, graveyard -0.094, primary -0.065.

**Rule changes inside RW1's window (Testing 2, 10-21..11-10), from research/ledger.jsonl (effective dates):** 10-23 testing per-setup
stop off; 10-26 ST7-FD promotion; 10-30 Testing cost filter CF; 11-03 SO1A / R2A cap exempt; 11-04 UNI1 Testing 2 top-500 pool;
11-05 low-rep Explore 1 / Live Lab (and later entries). Skeptic (23:00): RW1 across T1+T2 116 trades +0.078, w/o best +0.036, w/o
11-04/11-05 +0.020 - mostly the post-10-30 short-friendly window. **So 'what works' live is one short family in one regime window.**
Lab 2-year avg R per setup: requested from Builder (bt_lab1104 lists live in his container); GEN rows carry their screen valid exp_r.
Files: whatworks.py, whatworks_out.txt, whatworks_live.csv (passers), whatworks_all.csv (all 128 rows).
