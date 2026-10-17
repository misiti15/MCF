# BDI Saturday deep run 2026-10-17

*Educational only — not financial advice. Daily-bar backtests (rule 7: not paper, not live); costs in; the locked
block 2024-11-01..2025-02-28 was never loaded (`MCF_HIST_ALLOW_LOCKED` never set). PLAN.md was written before scoring.*

## Failures first
- **0 of 56 configurations pass.** One configuration (N1_ONID_L20_H20) passed the pre-declared gates. It was then
  **refuted** by the pre-declared adversarial checks (amendment 2026-10-17): it is a high-beta basket, not a timing edge.
- **Discover workflow:** the 10-10 run finished "success", but its backlog re-test **scored nothing**. The step ran in
  under 1 s and published no `backlog_results.jsonl`: `mcf-data/backlog/` holds only backlog.jsonl and BACKLOG.md, and
  the results history has 0 lines. The workflow was changed since then and now fails loudly. Today's run (id
  39042010842, started 14:44 UTC) was still in the "Mine" step at the last check, so the bar refresh and the backlog
  step had not started.
- R1-A (C3 beta-hedged) fails everywhere. Once hedged, C3 loses money in every split.

## Configurations (counted)
| part | lineage | configs | lineage N / t bar | candidate / near / fail |
|---|---|---|---|---|
| R1 C3 MA pullback: A hedge, B +RS63 | cwt-c-c3 | 16 | 31 / 2.62 | 0 / 8 / 8 |
| R2 C7 down-streak on 28 new equity ETFs | cwt-c-c7 | 12 | 22 / 2.49 | 0 / 12 / 0 |
| R3 residual momentum, 756-session beta | lh-resmom | 12 (+12 parity, +24 re-span) | 147 / 3.16 | 0 / 11 / 1 |
| N1 overnight-minus-intraday persistence | new | 8 | 8 / 2.04 | 1 → refuted / 7 / 0 |
| N2 high-volume return premium | new | 8 | 8 / 2.04 | 0 / 8 / 0 |
| **total** | | **56** | | **0 pass** |

## R1: C3 MA pullback (`gates_daily.csv`)
- **A, beta-hedged:** net −11..−33 bps in train, −41..−82 bps in valid1, t −3 to −5. The +23..+51 bps per trade was
  all beta, which confirms the original diagnosis. **Flaw not fixable by hedging.**
- **B, + 63-day return > SPY:** raises net to +1..+58 bps in every split, and trval t reaches 2.3-3.2 (bar 2.62).
  It still fails on excess vs the universe (valid1 −31..−75 bps), on down months (−51..−97 bps), on 2022
  (−52..−105 bps) and on valid1 t (0.07-0.99). This is still beta.

## R2: C7 streaks on new ETFs (`gates_daily.csv`)
- The rule replicates in sign out of instrument. Every U_eq row is positive in all 3 splits: streak4 +9 / +38 / +96 bps,
  n 1,133 / 329 / 270, valid1 t 2.18.
- Every row fails the try-count bar: best trval t is 1.65 against a bar of 2.49.
- Streak 2-3 also loses in down months (−10..−16 bps). Streak 4 passes both up and down months (+73 / +6.4 bps).
- **Verdict near.** It is the most honest near-miss of the day: no excess problem, and costs are tiny (~3 bps).

## R3: residual momentum, beta from 756 sessions (`gates_resmom*.csv`)
- Parity: the 252-session version reproduces longhold S2 exactly (all 12 active returns match).
- Common span from 2018-02 (amendment): the 756 beta lifts active t on average.
  - res12_1 N20 M goes from t 1.20 to t 2.33.
  - Valid2 active is +12..+51 %/yr.
- **0 of 12 reach t 3.16.** Deflated-Sharpe concerns from longhold still apply.

## N1: tug of war (Lou, Polk & Skouras) (`gates_daily.csv`, `diag_n1.csv`, `diag_n1_years.csv`)
- N1_ONID_L20_H20 passed the gates: weekly top decile of (20-day overnight minus intraday return), MOO, 20-day hold.
  Net +130 / +238 / +246 bps (n 9,388 / 3,151 / 3,172), trval t 2.80.
- **Refuted by the checks:**
  - net-excess t (train+valid1) is 1.03, against a required 1.5;
  - valid2 net excess is −2.3 bps;
  - beta-hedged net is −22 bps in trval and −66 bps in valid1;
  - on the top-300 names, excess is negative in train and valid2;
  - basket beta is 1.2-1.5;
  - net excess by year swings from −74 bps (2021) to +68 bps (2023).
- The neighbours show the same pattern.

## N2: high-volume premium (`gates_daily.csv`)
- Every row is positive in all splits: +21..+176 bps; the H20 rows have valid1 t up to 3.3.
- Every row fails the try-count bar: trval t is at most 2.03 against a bar of 2.04.
- Excess vs the universe is mostly negative in valid1 and valid2, and down months are negative except one H5 row.
  This is beta again.

## Lesson (day over day)
Every daily stock-long family tested in MCF is mostly beta: W3, longhold, package C and now N1/N2. The pre-declared
excess and hedge checks catch it every time. A daily idea is only worth testing if it is designed market-neutral
from the start (hedged or long-short), or if it trades ETFs, where there is no survivorship (R2).

## Week scorecard 10-12..10-16 (paper; source `research/swarm1017/week/summ_out.txt`, mcf-data-longhold marks.csv)
| account | trades | win % | avg R (adj) | P/L (adj) | per session |
|---|---|---|---|---|---|
| Primary | 135 | 43.7 | −0.210 | −$866 | −$154 (last week −$185) |
| Testing 1 | 1,449 | 44.5 | −0.149 | −$2,504 | −$445 |
| Testing 2 | 2,281 | 57.2 | −0.180 | −$4,134 | −$738 |
| S6 long-hold (S6_mom12_1rev_N20_W) | 20 names, weekly | – | – | **−7.2 %** (equity $90,388) | SPY −1.97 %, EW −1.53 % |

- S6 notes:
  - drawdown is −12.6 % from the 10-13 high (the kill switch is at 25 %);
  - the book was only half invested on 10-12;
  - the 10-19 rebalance (24 OPG orders) is submitted.
- One week of a 20-name momentum book is noise, not evidence. Judge it on tracking vs the model and on drawdown
  (DESIGN.md).

## Next week (2026-10-19..23)
- **Mon 10-19:**
  - MF review (MF4 decision; MF1/3/5 demotion per Q6 after the close);
  - check the S6 rebalance fills and slippage against the official open;
  - confirm that today's discover run published `backlog_results.jsonl`, or re-run it with workflow_dispatch.
- **Tue 10-20:**
  - Graveyard conversion after the close (Q4/Q5/Q7);
  - Q1 (real funds) answer due: recommendation unchanged, stay on paper;
  - Q15 items (CPA, backup feed, loss limit with open P/L, separate keys) stay open and block any real-funded account.
- **Q16 (PTP exclusion for S6):** housekeeping, after hours, any day. S6 holds no PTP today.
- **Testing 2:**
  - 12 near-misses for observation and the scale-outs on 7 setups: first scorecard after 4 sessions (Thu 10-23);
  - check their mutual overlap before Tuesday.
- **BDI weekdays:**
  - (1) R2 C7-ETF streak4: pre-declare a sector-neutral ETF version and an n-expanding version (adding TLT/GLD is a new
    lineage);
  - (2) design every new daily idea market-neutral from the start (hedged long-short deciles of N1/N2);
  - (3) do not spend locked looks on anything in this file.
- **Where things run:**
  - GitHub Actions: discover on Saturday, earnings-data;
  - the cloud runner: Primary, T1, T2 and S6;
  - BDI: Claude sessions after the close.

## Files
PLAN.md, study_daily.py → results_daily.csv, gates_daily.csv, trades_r2_eq3.parquet; study_resmom.py →
gates_resmom.csv, gates_resmom_from2018-02.csv; diag_n1.py → diag_n1.csv, diag_n1_years.csv.

## Backlog entries (for the lead; not written to research/backlog.jsonl)
```
{"id":"sat1017-rw-c3-hedge-rs","title":"C3 MA pullback: beta hedge / +RS63 rework","category":"strategy","status":"failed","notes":"16 configs (lineage 31, bar 2.62). Hedged: -11..-33 bps train, -41..-82 valid1. +RS63: +1..+58 bps all splits, t up to 3.19, but excess valid1 -31..-75, down months -51..-97, 2022 -52..-105. Beta, not timing. research/bdi/sat1017/. Educational only - not financial advice."}
{"id":"sat1017-rw-c7-etf-streak","title":"C7 down-streak buy on 28 equity ETFs (new instruments)","category":"strategy","status":"failed","notes":"12 configs (lineage 22, bar 2.49), all near. U_eq streak4 cap20 +9/+38/+96 bps (n 1133/329/270), trval t 1.50, valid1 t 2.18, up/down months +73/+6. Sign replicates out of instrument; t below bar. Next look = look 2 (t>=1.5), lead only. Educational only - not financial advice."}
{"id":"sat1017-rw-resmom-beta756","title":"Residual momentum with 756-session beta","category":"strategy","status":"failed","notes":"12 configs (+parity, +2018-02 re-span; lineage 147, bar 3.16). 756 beta lifts t (res12_1 N20 M 1.20 -> 2.33 on common span), 0 pass. Educational only - not financial advice."}
{"id":"sat1017-new-overnight-tugofwar","title":"Overnight-minus-intraday return persistence, weekly top decile, 5-20d hold","category":"strategy","status":"failed","notes":"8 configs (bar 2.04). ONID L20 H20 passed gates (+130/+238/+246 bps) but refuted: net-excess t 1.03, valid2 excess -2 bps, beta-hedged -22 bps trval, beta 1.2-1.5. Rework: hedged long-short deciles. Educational only - not financial advice."}
{"id":"sat1017-new-highvolume-premium","title":"High-volume return premium (vol >= 2-3x, small move), 5-20d hold","category":"strategy","status":"failed","notes":"8 configs (bar 2.04), all near: +21..+176 bps all splits, trval t <= 2.03, excess mostly negative in valid1/valid2, down months negative. Beta. Rework: hedged long-short. Educational only - not financial advice."}
```
