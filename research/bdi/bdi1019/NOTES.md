# BDI 2026-10-19: index-chase veto on two years of history (Primary + Testing 1 setups)

*Educational only — not financial advice. These are backtest results on the open two-year history (rule 7: not paper or
live). Costs are in. The locked block (2024-11-01..2025-02-28) was not read and no holdout was scored. 23 configurations
were tried (pre-declared in PLAN.md), so the bar is max(1.5, sqrt(2 ln 23)) = **2.50**. Counting the 71 configurations
of the giveback1019 lineage the post-peak guard came from gives N 94 and a bar of 3.01.*

## Failures first
- **0 of 23 configurations pass.** No variant beats the parent on both train and valid with valid day-clustered t >= 2.50.
- **Best: `D-chase-QQQ-60m-0.2-after1100`.** It skips entries after 11:00 whose side agrees with a QQQ 60-min move of more than 0.2%, which is 9% of trades.
  - Train: +0.0062 R per parent trade, t 2.99.
  - Valid: +0.0047, t **2.25**, below the 2.50 bar.
  - Random skip: it beats a random skip of the same share on only 1.13 t (excess +0.0023), short of the 1.65 the plan requires.
  - Down sessions: in valid it is negative (−0.0053).
  - Fails 3 of 4 gates.
- **The veto mostly shrinks a losing book rather than picking out bad trades.**
  - The parent book loses: −0.065 R per trade in train (171,078 trades over 234 days) and −0.026 R in valid (195,162 trades over 192 days).
  - So any skip "helps". The random-skip column shows nearly the same gain.
  - In every config the vetoed trades are no worse than a random skip: valid excess t ≤ 1.14.
  - The two widest chase vetoes (QQQ and SPY, 30 min, threshold 0) skip trades that are *better* than average (excess t −0.89 / −0.93).
- **It is a regime bet, as were the exit rules in giveback1019.**
  - The book is 83% short. It loses in up sessions (−0.21 / −0.14 R train / valid) and makes money in down sessions (+0.04 / +0.07 R).
  - Every veto that skips shorts after the index fell helps in up sessions and hurts in down sessions: 21 of 23 configs have valid Δ down < 0.
- **Post-peak guard (B).**
  - Tested only as a proxy: the account-peak condition cannot be rebuilt on history, so the test skips entries after 10:30 that go against QQQ/SPY's move from the open.
  - Train t is about 3.3 at threshold 0, but valid t is ≤ 1.42.
  - It is no better than a random skip.
  - In valid down sessions it is −0.035 R per trade.
- **Near-extreme variant (C)** is negative or flat in valid: −0.0009 R at 0.10%, +0.0006 at 0.15%.
- **Per setup** (descriptive). Choosing a setup would make the count 23 × 45, so the bar there is 3.73.
  - 0 of 1,035 setup × config rows pass "Δ > 0 on train and valid and valid t ≥ 3.73".
  - Closest: NS5-sma50-flush-oversold-long-FD under D-0.2. Valid +0.028 R, t 3.32 (excess t 3.41), but train only +0.002 (t 0.20).
- **Not covered.**
  - LIQ-orl-sweep and LIQ-pdl-sweep use a structural GEOM "S" exit, which has no frame outcome.
  - RW6G1 and RW6G1-FD give 0 history entries, as in giveback1019.
  - intraday_momentum and IDX* trade the index ETFs themselves, so they are excluded.
  - The windowed T1 copies that traded on one day under the old overlay are replaced by their -FD versions.
  - Exhaustion's prefilter and refire are not modelled, as in rescore.
  - The -FD and windowed twins overlap (MF5 and MF5-FD are the same signal), so the pooled book double-counts some trades. Day-clustering absorbs the correlation but not the duplication.
- **Not tested tonight:** `gb-1019-cut-1100-fd`, `gb-1019-noise-floor-stop` and `gb-1019-wide-stop-t05` stay at "idea".

## What was done
1. **Patterns.** `research/bdi/nightly1019/patterns_1019.csv` (307 rows for 2026-10-19) was merged into `research/bdi/patterns.csv`. The file grew from 2,023 to 2,330 rows. `merge_patterns.py` is idempotent by date: a second run replaced the same 307 rows, and the diff is additions only.
2. **Setups.** Every setup that traded in Primary or Testing 1 over 2026-10-06..10-19 (journals on origin/mcf-data and origin/mcf-data-testing) was included in its current config form. That gives 47 setups with a harness, 45 of them with history entries (`setups_used.csv`).
3. **Entries** (`entries.py`).
   - Method: the research/history2y/rescore method on the history2y 5-min lab frames, open months only.
   - Per setup: module mask, YAML window, point-in-time ADV, first bar per symbol-day, production costs with time-of-day entry costs (`gates.lab_trades`).
   - Heat setups use their formula `score`. orb20_a comes from the production backtester trades.
   - Result: 366,240 entries from 2024-10 to 2026-10-07. The script asserts that no locked date is present.
4. **Index context** (`index_ctx.py`).
   - Built from SPY and QQQ 1-min SIP bars, with locked rows dropped on load.
   - The decision minute is the frame `tod`, which is the 5-min bar *close* time.
   - Check: the `*_fo` columns match `lib.load_context` qqq_fo / spy_fo to 1e-7.
   - The first draft used tod + 5 min. That would have looked 5 minutes ahead, and it was fixed before any scoring (PLAN addendum).
5. **Scoring** (`veto.py`).
   - The 23 configs are scored with skipped trades counted as 0 R.
   - Columns: Δ = total R change per parent trade, day-clustered t, Δ without the best day, up / flat / down sessions, and a random skip of the same count per setup and split (500 draws).
   - Excess = Δ minus the random expectation.

## Pooled results (R per parent trade; train ≤ 2025-12-31, valid 2026-01-01..2026-10-07)
Parent: train n 171,078 over 234 days, win 49.0%, avg −0.0649 R (up −0.206 / flat −0.017 / down +0.042). Valid n 195,162
over 192 days, win 51.0%, avg −0.0259 R (up −0.138 / flat −0.026 / down +0.075).

| config | skip % (valid) | train Δ R/trade (t) | valid Δ (t) | valid Δ without best day | valid random-skip Δ | valid excess (t) | valid kept win% / avg R | valid Δ up / flat / down |
|---|---|---|---|---|---|---|---|---|
| A-chase-QQQ-30m-0.0 | 37 | +0.0244 (3.88) | +0.0049 (1.03) | +0.0037 | +0.0091 | -0.0042 (-0.89) | 50.4% / -0.0332 | +0.0499 / +0.0012 / -0.0316 |
| A-chase-QQQ-30m-0.2 | 13 | +0.0104 (2.13) | +0.0029 (1.29) | +0.0022 | +0.0031 | -0.0002 (-0.11) | 50.8% / -0.0265 | +0.0171 / -0.0006 / -0.0061 |
| A-chase-QQQ-30m-0.4 | 5 | +0.0048 (1.09) | +0.0007 (0.55) | +0.0003 | +0.0011 | -0.0005 (-0.36) | 50.9% / -0.0266 | +0.0067 / -0.0005 / -0.0035 |
| A-chase-QQQ-60m-0.0 | 37 | +0.0204 (3.79) | +0.0090 (1.71) | +0.0074 | +0.0090 | -0.0001 (-0.01) | 50.7% / -0.0269 | +0.0503 / +0.0066 / -0.0257 |
| A-chase-QQQ-60m-0.2 | 18 | +0.0102 (2.71) | +0.0053 (1.62) | +0.0042 | +0.0043 | +0.0010 (0.30) | 50.8% / -0.0252 | +0.0254 / +0.0037 / -0.0110 |
| A-chase-QQQ-60m-0.4 | 9 | +0.0049 (1.63) | +0.0024 (1.04) | +0.0013 | +0.0022 | +0.0003 (0.11) | 50.9% / -0.0259 | +0.0138 / +0.0008 / -0.0061 |
| A-chase-SPY-30m-0.0 | 35 | +0.0203 (3.35) | +0.0047 (1.09) | +0.0038 | +0.0088 | -0.0041 (-0.93) | 50.5% / -0.0327 | +0.0430 / +0.0024 / -0.0272 |
| A-chase-SPY-30m-0.2 | 7 | +0.0044 (1.16) | +0.0018 (1.35) | +0.0014 | +0.0016 | +0.0002 (0.15) | 50.9% / -0.0259 | +0.0074 / +0.0003 / -0.0018 |
| A-chase-SPY-30m-0.4 | 2 | +0.0039 (1.14) | +0.0010 (1.65) | +0.0007 | +0.0003 | +0.0006 (1.06) | 51.0% / -0.0253 | +0.0028 / -0.0002 / +0.0007 |
| A-chase-SPY-60m-0.0 | 36 | +0.0171 (3.37) | +0.0090 (1.83) | +0.0077 | +0.0089 | +0.0002 (0.03) | 50.7% / -0.0264 | +0.0426 / +0.0125 / -0.0250 |
| A-chase-SPY-60m-0.2 | 12 | +0.0055 (1.64) | +0.0044 (1.98) | +0.0035 | +0.0027 | +0.0017 (0.76) | 51.0% / -0.0243 | +0.0172 / +0.0031 / -0.0057 |
| A-chase-SPY-60m-0.4 | 3 | +0.0026 (1.40) | +0.0022 (1.79) | +0.0016 | +0.0008 | +0.0014 (1.14) | 51.0% / -0.0245 | +0.0077 / -0.0001 / -0.0003 |
| B-against-QQQ-fo-1030-0.00 | 44 | +0.0361 (3.30) | +0.0125 (1.42) | +0.0092 | +0.0122 | +0.0003 (0.03) | 51.1% / -0.0240 | +0.0758 / +0.0042 / -0.0353 |
| B-against-QQQ-fo-1030-0.25 | 34 | +0.0273 (2.79) | +0.0108 (1.39) | +0.0076 | +0.0093 | +0.0015 (0.20) | 51.1% / -0.0229 | +0.0575 / +0.0026 / -0.0221 |
| B-against-QQQ-fo-1030-0.50 | 24 | +0.0135 (1.61) | +0.0067 (1.04) | +0.0036 | +0.0064 | +0.0003 (0.05) | 50.9% / -0.0251 | +0.0379 / -0.0008 / -0.0132 |
| B-against-SPY-fo-1030-0.00 | 44 | +0.0383 (3.34) | +0.0115 (1.35) | +0.0083 | +0.0121 | -0.0005 (-0.06) | 50.9% / -0.0257 | +0.0788 / -0.0081 / -0.0275 |
| B-against-SPY-fo-1030-0.25 | 28 | +0.0260 (2.67) | +0.0051 (0.75) | +0.0024 | +0.0075 | -0.0024 (-0.36) | 50.9% / -0.0287 | +0.0477 / -0.0132 / -0.0131 |
| B-against-SPY-fo-1030-0.50 | 14 | +0.0115 (1.43) | -0.0004 (-0.08) | -0.0020 | +0.0036 | -0.0040 (-0.83) | 50.8% / -0.0304 | +0.0143 / -0.0106 / -0.0024 |
| C-near-QQQ-extreme-0.10 | 7 | +0.0048 (2.55) | -0.0009 (-0.62) | -0.0016 | +0.0017 | -0.0026 (-1.84) | 50.8% / -0.0289 | +0.0024 / +0.0009 / -0.0058 |
| C-near-QQQ-extreme-0.15 | 11 | +0.0058 (2.16) | +0.0006 (0.32) | -0.0003 | +0.0026 | -0.0020 (-0.98) | 50.8% / -0.0285 | +0.0061 / +0.0026 / -0.0064 |
| C-near-QQQ-extreme-0.25 | 20 | +0.0111 (2.75) | +0.0051 (1.52) | +0.0040 | +0.0049 | +0.0003 (0.08) | 50.9% / -0.0261 | +0.0186 / +0.0072 / -0.0093 |
| D-chase-QQQ-60m-0.2-after1100 | 9 | +0.0062 (2.99) | +0.0047 (2.25) | +0.0037 | +0.0023 | +0.0023 (1.13) | 51.0% / -0.0234 | +0.0138 / +0.0063 / -0.0053 |
| D-chase-QQQ-60m-0.4-after1100 | 4 | +0.0046 (2.59) | +0.0018 (1.61) | +0.0013 | +0.0008 | +0.0009 (0.85) | 51.0% / -0.0250 | +0.0056 / +0.0019 / -0.0018 |

Verdicts: every row fails (see `veto_out.txt`; the gate list is in PLAN.md). Per-setup rows for every config are in `by_setup.csv`.

## Reading
- **The live 10-19 pattern does not generalise as a book-wide filter.** On 10-19, entries on the side of QQQ's last 60 minutes had 169 trades and −0.285 R. That was one two-way day.
- **On two years of history, chase entries are not worse than other entries once the regime is accounted for.** At threshold 0, the trades vetoed by A-QQQ-60m average −0.061 R in train against a parent −0.065, and −0.024 R in valid against −0.026.
- **The remaining effect is a short book losing in up sessions.** That is the regime problem documented in RESEARCH_RULES 19 and giveback1019, not a chase effect.
- **Rework leads (rule 18; each is a new lineage and gets counted):**
  1. A side-specific version for the long setups only. The live loss was T1/T2 longs. On history, heat_fade_long / -FD and NS5-FD lean positive under D, but none clears its bar.
  2. Combining with a regime/day-type gate instead of a raw index-move gate. The earlier `bdi1016-dayclass-direction-gate` already failed, so this needs a different construction.

## Backlog
`backlog_updates.jsonl` holds two full entries with status "failed", configs_tried and these numbers:
`nightly-1019-index-chase-veto` (17 configs: A, C, D) and `gb-1019-post-peak-index-guard` (6 configs: B, a proxy without the
peak condition). research/backlog.jsonl was not modified.

## Files
PLAN.md (pre-declared, plus one pre-result addendum), merge_patterns.py, entries.py, index_ctx.py, veto.py,
backlog_updates.py; outputs setups_used.csv, results.csv, by_setup.csv, veto_out.txt, backlog_updates.jsonl. Scratch
(journals, entries.parquet, idx.parquet; about 10 MB) is outside the repo and was deleted. Run order: `python entries.py <scratch>`,
`python index_ctx.py <scratch>`, `python veto.py <scratch>`, `python backlog_updates.py`.

Educational only — not financial advice.
