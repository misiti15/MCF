# Results: Gap-Down VWAP Loss Short (10% gap) — Workbench copies vs parent
Mechanic, 2026-11-16. Educational only — not financial advice.

## Tests (identical for parent and every copy; code in `code/`)
- **Replay of the live sessions** 2026-10-12..11-13 (24 sessions): lab frames rebuilt from SIP 1-minute bars exactly
  as live (`mcf.report.engine.lab_frame` + `apply_daily`) for every symbol-day with gap <= -7%; that day's universe
  snapshot, ETB flag and earnings blackout list (as live); price >= $5. All 268 live signals to 11-13 reproduced.
- **2-year backtest** 2024-10-01..2026-10-09 on the research/history2y lab frames (1,226 names), open months only —
  **the locked block 2024-11-01..2025-02-28 is never read** (asserted in sig.py / paths.py). ETB = symbol ETB rate
  >= 0.9 over the universe snapshots; no earnings history exists for 2y, so no blackout there (same for every copy).
- Signals: the live module code (`cwt_live_lib.a7`) plus the copy's clauses; first qualifying bar per symbol-day.
  Fill at the open of the 1-minute bar after the signal bar closes; structural stop (09:30-10:30 high), no target,
  flat 15:55; R = net P/L / |fill - stop| as live. **Costs in**: LR8 live model (entry (1c + 1 bp) x time-of-day + 1 bp,
  stop exit (1c + 1 bp) + max(2c, 4 bps), time exit (1c + 1 bp) + max(1c, 1 bp), SEC / TAF / CAT).
- Replay fidelity on the live trades: CIFR -1.12 vs live -1.08, ARCO +1.20 vs +1.31, DELL +0.91 vs +0.97, CLSK +0.84 vs +0.91.
- **Configs counted: 54 copies** (+ the parent): 31 one-part, 7 neighbours, 16 combos / layers. Bar max(1.5, sqrt(2 ln 54)) = 2.82
  (reported; the 2026-11-16 clarification has no significance hurdle for a pass).
- Few live trades (18): the pass decision uses the two tests above only; the live trades are diagnosis only.

## Copies table
| Copy | Change | Replay avg R (n) | 2-year avg R (n) | w/o best day (replay / 2y) | Worst day (replay / 2y) | Verdict |
|---|---|---|---|---|---|---|
| parent | — | **-0.139** (57) | **+0.079** (545) | -0.177 / -0.006 | -6.30 / -14.22R | — |
| WB1 | P9 + close below the day open at the signal bar | -0.023 (46) | +0.084 (382) | -0.057 / +0.021 | -2.98 / -14.22R | PASS |
| WB2 | P9 + a 5-min close above VWAP in 09:35-10:30 (not a wick) | -0.149 (49) | +0.109 (461) | -0.185 / +0.008 | -6.30 / -7.13R | PASS (replay "meets": -0.010R) |
| WB3 | WB1 + WB2 | -0.011 (38) | +0.125 (300) | -0.047 / +0.046 | -2.98 / -3.37R | PASS |
| **WB4** | **WB1 + WB2 + P2 ADV >= $20M** | **+0.041** (20) | **+0.134** (297) | **-0.019 / +0.055** | **-2.14 / -3.37R** | **PASS — recommended** |

Detail (WB4 vs parent): win 65.0% vs 49.1% (replay), 49.2% vs 45.0% (2y); avg win / loss (2y) +1.134 / -0.833 vs
+1.247 / -0.874; median hold 274 vs 299 min (2y); exits (2y) 203 time / 94 stop vs 353 / 192; best day's share of total R
(2y) 61% vs 108%; 2y TRAIN (..2025-12) +0.121 vs +0.100, VALID (2026-01..10-09) +0.147 vs +0.057; day type (2y, end-of-day
label) up -0.274 / flat +0.204 / down +0.380 vs -0.362 / +0.268 / +0.250; replay up -0.069 / flat -0.119 / down +0.347 vs
-0.320 / -0.217 / +0.078. Paired by day (days both trade): replay -0.010R (t -0.17), 2y -0.060R (t -1.24) — the gain is
from the trades and days the copy leaves out (above-the-open and wick-only signals, small names), not from better
fills on shared days. Neighbours: ADV $1M (WB3) +0.125 / -0.011, ADV $50M +0.181 / +0.004, "within +1% of the open"
instead of "below" +0.180 / -0.054, + BE after +1R +0.148 / -0.013 (2y / replay) — a plateau, not a spike.

## Every other config (replay avg R / 2-year avg R; parent -0.139 / +0.079)
Intake: gap >= 8% -0.106 / +0.045 (fail 2y); >= 12% -0.182 / +0.095 (fail replay); >= 15% -0.215 / +0.144 (fail replay);
no ETFs -0.067 / +0.026 (fail 2y); ADV >= $20M -0.134 / +0.093 (fail: replay w/o best day -0.219); ADV >= $50M -0.118 / +0.123
(fail: replay w/o best day -0.218). Timer: end 12:00 -0.103 / +0.059, 13:00 -0.127 / +0.051, 11:00 -0.088 / +0.077 (2y w/o
best day -0.032; fail). Sensors: VWAP loss >= 0.3% / 0.5% / 0.75% / 1.0% -0.117 / +0.076, -0.117 / +0.083 (pass), -0.050 /
+0.077, +0.012 / +0.042 (fail 2y); bounce >= 0.15 ATR -0.177 / +0.089 (fail); stop dist <= 1.0 ATR -0.179 / +0.101 (fail);
>= 0.2 / 0.3 / 0.4 ATR -0.104 / +0.083, -0.093 / +0.092 (pass), -0.103 / +0.057; below open by >= 1% / >= 2% -0.047 / +0.064,
+0.009 / +0.008 (fail 2y); within +1% of open -0.058 / +0.131 (pass). Gates (SPY since 09:50): <= 0 -0.005 / +0.096
(2y w/o best day -0.017, pass marginal); <= +0.25% -0.153 / +0.076 (fail); >= -0.25% -0.079 / +0.104 (fail: replay w/o
best day -0.237). Stop: cap 0.5 / 0.75 / 1.0 ATR -0.058 / +0.007, -0.105 / +0.053, -0.130 / +0.071 (fail 2y); signal-bar /
VWAP stop -0.315 / -0.088 (fail). Target 1R / 2R / 3R +0.016 / -0.009, -0.062 / +0.012, -0.139 / +0.012 (fail 2y). BE after
+1R -0.125 / +0.078 (pass, flat); trail 1R after +1R -0.079 / +0.031 (fail); lock +0.5R after +1.5R -0.125 / +0.069 (fail).
Time exit 13:00 / 14:00 / 15:00 -0.005 / -0.012, +0.013 / -0.018, -0.015 / +0.020 (fail 2y). Combos: S4+S7 -0.018 / +0.097;
S4+S1 -0.018 / +0.087; S4+S7+S1 -0.006 / +0.079; S4+S7+S3 -0.004 / +0.102; S4+S7+ADV50M +0.006 / +0.137; S4+S7+S1+S3
+0.011 / +0.086; S4+BE -0.025 / +0.095; S4+S7+BE -0.017 / +0.096; S4+S3+ADV50M +0.004 / +0.181 (replay w/o best day -0.078,
16 trades); S4c+S3 -0.054 / +0.180; S4+S3+BE -0.013 / +0.148; S4+S3+S7a = WB3; S4+S3+S1a 0.000 / +0.105.
Full table: scratch `all_results.csv` (columns n, win, avg, w/o best, worst day, avg win/loss, hold, paired diff, day types, train/valid).

## Supervisor sign-off (WB4)
- **What changed:** two entry checks and a liquidity floor. Short only when the stock is (1) back below today's open
  and (2) had a real first-hour bounce (a 5-minute close above VWAP, not a wick), on names with 20-day ADV >= $20M.
  Stop, exits, window and timing are the parent's.
- **Why:** a "VWAP loss" while the stock is still above its open is a pause inside a recovery day (SOXS 11-06 -1.04R,
  HPQ 10-30 gave back +2.2R); a wick-only bounce trapped no buyers (SNDX, VIR); sub-$20M names add noise and the
  one-big-day dependence.
- **Overall before / after:** replay -0.139 -> **+0.041R**, 2-year +0.079 -> **+0.134R** (after costs); avg R w/o best day
  -0.177 -> -0.019 (replay), -0.006 -> **+0.055** (2y; the parent's 2-year record was carried by one day, the copy's is not);
  worst day -6.3 -> -2.1R / -14.2 -> -3.4R; both 2y halves better. Positive after costs in both tests.
- **Where it gives back:** about half the trades (2y 545 -> 297, replay 57 -> 20; total 2y R +43 -> +40); live winners
  that were still above the open at 10:30 get a later, worse entry (DELL +0.97 -> -0.20 replay) or are skipped (ARCO
  +1.31R, ADV $18.6M); on the 18 live trades the copy would have made about +0.25R/trade vs +0.30R. Up days are still
  negative (2y -0.274R). Replay is only 20 trades.
- **Signed off:** PASS — meets/exceeds the parent on both tests, w/o best day and worst day better. Recommended copy.

## Pending config change — "ready to deploy after close" (NOT applied)
Built 2026-11-16; the main session applies it after 16:05 ET, effective session 2026-11-17. One copy only: **WB4**. The
parent stays in On Deck, unchanged. Account: **Testing E** (`config/account_testinge.yaml`) — a testing account, not
the parent's (On Deck), not its former homes (Testing A / Testing C); only one other Workbench copy is queued there today.
Twin check: `twin_key` strips only `-FD`, so `...-WB4` is not the parent's key; different account anyway.
1. `config/account_testinge.yaml`, under `strategies:` add
   ```yaml
   CWT09-gapdn-vwaploss-g10-short-WB4:
     # Workbench copy of CWT09-gapdn-vwaploss-g10-short (On Deck), Mechanic 2026-11-16: + below the day open + first-hour
     # 5-min close above VWAP + ADV >= $20M; research/workbench/CWT09-gapdn-vwaploss-g10-short/RESULTS.md. From session 2026-11-17.
     enabled: true
     type: lab
     module: research/workbench/CWT09-gapdn-vwaploss-g10-short/modules/CWT09-gapdn-vwaploss-g10-short-WB4.py
     min_adv: 20000000
     window: [1030, 1500]
     scale_out_r: null
     tags: [workbench, "parent:CWT09-gapdn-vwaploss-g10-short"]
   ```
   and put it FIRST in `live.setup_order` (Workbench rule 5: ahead of rotated / spotlight setups; if the L3-rsi5hi
   WB4 plan lands in Testing E the same evening, keep both at the top, earlier pass first).
2. `config/setup_names.yaml`: `CWT09-gapdn-vwaploss-g10-short-WB4: {name: "Gap-Down VWAP Loss Short (10% gap) — WB4: below open, real bounce, ADV 20M", side: short, what: "10:30-15:00: a stock that gapped down 10%+ (no earnings within 4 days, 20-day ADV >= $20M) closed a 5-minute bar above VWAP during 09:35-10:30; from 10:30 the first close back below VWAP while below today's open; short, stop at the 09:30-10:30 high, hold to 15:55."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-cwt09g10-wb4`, effective 2026-11-17, title "Workbench copy
   CWT09-gapdn-vwaploss-g10-short-WB4 added to Testing E, first in setup_order (Mechanic pass)", patch
   `{"strategies.CWT09-gapdn-vwaploss-g10-short-WB4 (testinge)": [null, "added, enabled"], "live.setup_order (testinge)": ["...", "WB4 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit), `pytest -q`, commit,
   push after 16:05 ET (setup-freeze).
