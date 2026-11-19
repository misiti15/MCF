Educational only — not financial advice.

# st7_fix — root-cause remedy R2 (owner code ST7), results

Pre-registered in `PLAN.md` before any scoring. **Configurations counted: 4** (A-SR, A-GA, B-WIN, C-SKIP). Nothing was
tuned after scoring. The per-trade (avg R) view of the family is a second way of reading the same runs, not a new config.
No live code path was changed; all RSI variants are research copies (`work/rebuild.py`). The locked block
2024-11-01..2025-02-28 was never read: 1-minute bars were filtered to open dates before anything was computed. Costs are
in (production costs plus time-of-day entry costs, gates.lab_trades / LR8). 2023-24 bars (cache_fresh) were not used.

## Summary
1. **(a) Fixing the RSI warm-up in shared code fails badly in both forms. Reject it.** Many RSI setups were found
   *with* today's RSI, so the warm-up behaviour is part of their rules. Changing it at the source moves every one of them.
   - Session-reset (A-SR): 46 setups affected. 6 get better (+54.9R), 40 get worse (-14,416R), so net -14,361R.
     Avg R gets worse in 36 setups.
   - Gap-adjusted (A-GA): 45 setups affected. 14 get better (+936R), 31 get worse (-4,331R), so net -3,395R.
     Avg R gets worse in 29 setups and better in 10.
   - Both forms fail in both halves of the data.
2. **The fix does remove the artifact, and it shows what ST7 really is.** Under A-GA, ST7-FD's 10:45 fires (651) go to 0.
   What is left is the 10:50-13:30 part (n 276, -0.033R) plus the 13:35-15:00 part (n 176, +0.133R). Away from the
   artifact bar, ST7's "RSI collapse" edge before 13:35 is negative. Its positive part is only the source window.
3. **(b) Restoring the 13:35-15:00 window is the best ST7 form in the lab:** n 176, +0.133R, t 1.68, both halves positive,
   +0.076R without its best day (best-day share 46%), worst day -2.4R. Caveats:
   - The window came out of a search over N = 120,500 configurations, so t 1.68 is far below t_required 4.84.
   - On live paper it is n 11, -0.395R.
   - On the 2023-24 holdout, round 5 scored FD (not the window) at -0.016R.
4. **(c) Skipping only the 10:45 bar is a weak option:**
   - It cuts the worst day from -26.1R to -4.3R.
   - Avg R falls from +0.045R to +0.034R, t from 1.01 to 0.74, and total R from +50.0R to +15.8R.
   - Its best day is 61% of total R, so it gets the `1 day` tag.

## (a) Shared RSI fix: every affected setup
The family is every enabled `type: lab` setup whose module or helper library reads rsi / rsi5 / rsiSlope / rsiHeat /
heat / bear_div / bull_div: 82 candidates, 68 runnable (14 use non-standard geometry and are not covered), 65 with trades.
Derived columns were recomputed too (rsiSlope, bear/bull divergence, rsiHeat, heat). A check of the rebuilt as-is RSI
against the frame `rsi` column: max difference 4e-6.

| | affected | better (R) | worse (R) | net R | early half (<2026-03-10) | late half | avg R better / worse |
|---|---|---|---|---|---|---|---|
| A-SR | 46 | 6 (+54.9) | 40 (-14,415.9) | **-14,361.0** | 8 / 38, -10,745.5 | 6 / 39, -3,615.5 | 6 / 36 (median -0.015R) |
| A-GA | 45 | 14 (+936.4) | 31 (-4,331.0) | **-3,394.6** | 16 / 29, -3,157.6 | 16 / 29, -237.0 | 10 / 29 (median -0.005R) |

- **Why the R swings are so large.** A-SR adds +56% trades (235k to 366k). From 09:50 to 10:40 its RSI is built from only
  3-13 changes, so it reaches extreme values and fires the RSI-threshold shorts far more often. Those shorts are negative in
  the lab, because the lab cannot apply ETB. A-GA keeps the trade count almost flat (+8%).
- **The largest per-trade losses are in the best long and short RSI setups:**

| setup | A-SR avg R | A-GA avg R |
|---|---|---|
| NM-RWN4 | +0.105 → -0.258 | +0.105 → -0.221 |
| NM-RWR4 | +0.093 → -0.245 | +0.093 → -0.218 |
| ST7Q | +0.150 → -0.040 | +0.150 → +0.066 |
| ST7-FD-WB1 | +0.108 → -0.071 | +0.108 → +0.033 |
| ULT-HV2-K | +0.107 → -0.026 | +0.107 → -0.020 |
| RW6-FD | -0.021 → -0.146 | -0.021 → -0.134 |
| NS2 | +0.002 → -0.120 | +0.002 → -0.106 |

- **Largest A-GA gains:** MF3-open-FD +198R, exhaustion_short-FD +140R, MF4-FD +130R, MF1-FD +108R, MF5 (both) +98R each,
  L3-rsi5hi (both copies) +31R each.
- The full per-setup tables (n, avg R before and after, delta, halves) are in `work/an_out.txt` and
  `work/family_delta.csv`.
- **Pass bar (pre-registered):** net >= 0 in both halves, >= 60% of setups not worse, no setup worse by more than 10R.
  Both forms fail every part of it: not-worse share is 13% for A-SR and 31% for A-GA.

**Live (paper, run 1, all accounts, 10-06..11-04, the dates the bars cover).**
- Coverage: 85% of live trades matched a base lab fire on their decision bar.
- The live check can only show **removals**. Trades the fix would add cannot be scored live, and in the lab those added
  trades are the main source of harm.
- Removal-only results:
  - A-SR: 31 setup-accounts affected. 18 better (+86.0R), 13 worse (-25.5R), net +60.5R.
  - A-GA: 33 setup-accounts affected. 24 better (+88.1R), 9 worse (-20.8R), net +67.3R.
  - The removed trades average -0.30R. Most are early-morning MF/exhaustion shorts (MF3-open-FD Testing 1 +14-16R,
    MF5-FD Testing 2 +9.5R, MF1-FD +7-10R).
- Worse in both forms:
  - ST7-FD Primary -5.31R
  - ST7-FD Testing 1 -5.04R
  - ST7Q -3.12R
  - NS4-FD -2.70R
- This one-sided live read does not offset the lab result. The 2,874 live trades after 11-04, including the 11-19 burst,
  have no bars and cannot be re-evaluated.

## ST7-rsi50dn-long-pm-t1s1-FD: all configurations (2-year lab, first fire per symbol-day)

| config | n | days | win | avg R | t | total R | avg R w/o best day | best-day share | worst day | early / late avg R | 10:45 fires |
|---|---|---|---|---|---|---|---|---|---|---|---|
| as live (FD) | 1,114 | 338 | 0.541 | +0.045 | 1.01 | +50.0 | +0.037 | 19% | -26.1 | -0.023 / +0.093 | 651 |
| A-SR | 810 | 326 | 0.499 | -0.039 | -1.06 | -31.7 | -0.052 | n/a (neg) | -7.1 | -0.019 / -0.057 | 0 |
| A-GA | 469 | 261 | 0.520 | +0.027 | 0.59 | +12.5 | +0.006 | 77% `1 day` | -3.5 | +0.036 / +0.018 | 0 |
| **B-WIN 13:35-15:00** | 176 | 120 | 0.580 | **+0.133** | 1.68 | +23.4 | **+0.076** | 46% | -2.4 | +0.116 / +0.148 | 0 |
| C-SKIP 10:45 | 466 | 263 | 0.526 | +0.034 | 0.74 | +15.8 | +0.014 | 61% `1 day` | -4.3 | +0.047 / +0.022 | 0 |

**By bar under each config:**
- A-SR: before 10:40, n 360, -0.133R (partial-window noise); 10:50-13:30, -0.026R; 13:35+, +0.133R.
- A-GA: before 10:45, n 17; 10:50-13:30, n 276, -0.033R; 13:35+, n 176, +0.133R.

**Pre-registered ST7 bar** (avg > 0 in both halves and > 0 without the best day): B-WIN passes clearly; C-SKIP and
A-GA pass only narrowly and carry the `1 day` tag; A-SR fails.

**Live ST7 (paper), by decision bar.**
- ST7-FD: Primary 42 trades, -6.63R (-0.158R; -0.296R without the best day); Testing 1 16 trades, +3.18R.
- WB1 (Live Lab, from 11-17): 8 trades, -8.28R.
- Under B-WIN, ST7-FD would keep 11 of 58 trades (-4.34R) and drop 47 (+0.89R).
- Under C-SKIP it would keep 21 (-5.48R) and drop 37 (+2.03R in total: 11-19 was -7.53R, the other 10:45 fires
  were +9.6R).
- So live, neither (b) nor (c) has a positive record of its own. The samples are tiny.

## Rule changes inside the windows (research/ledger.jsonl)
- **Lab window (2024-10 / 2025-03..2026-11):** no live rules apply.
- **Live window:**
  - stacking/refire 10-13/10-14
  - ST7Q added to Testing 1 and twin group 10-22/23
  - **ST7-FD Testing 1 → Primary 10-26**
  - GX1 5-min clock fix 10-27
  - Primary sizing 10-28
  - Primary -2R latch 10-29
  - ROLL1 11-05
  - **ST7-FD-WB1 to Live Lab 11-17**
  - promotion hold 11-17
  - C3-EPOCH / C3-BAR2 / C3-EXIT100 11-19
  - stop rounding, footrace exit and 9 testing admissions effective 11-20
- ST7-FD's live figures mix its Testing 1 and Primary periods and the 10-28/10-29 sizing and latch changes.

## Proposal (owner decides; nothing applied)
- **ST7-A: do not change the shared RSI.** Both forms of (a) fail the family pass bar by thousands of R. Log R2-(i) as a
  tested-and-failed remedy, so it is not re-proposed. Applying it would break the "targeted, not broad" remedies rule
  (owner 2026-11-05).
- **ST7-B: return ST7 to its source window (13:35-15:00) instead of the FD copy.** This is the best-supported ST7 form,
  but the evidence is thin (search-selected, t 1.68, live n 11 at -0.40R). Conflicts to name before acting
  (conflict-check rule, 11-19):
  - The window was removed under owner policy of 2026-10-09 ("full-day versions first").
  - Under the 11-18 rule, a windowed copy is a brand-new setup, so it enters testing under the testing-admission rule.
    It does not replace ST7-FD in Primary.
  - The promotion hold (11-17) applies.
  - Any Primary change (for example, moving ST7-FD out) happens only in the Friday epoch window (C3-EPOCH). It is a
    move: assignments.json is regenerated in the same commit, and the setup is never just switched off.
  - It goes through the backlog (RESEARCH_RULES 15-17) and the ledger.
- **ST7-C (skip 10:45 only): not recommended.** It cuts the tail (worst day -26 to -4R) but lowers t, keeps a
  negative-mean middle part, and carries the `1 day` tag.
- **Untested next step (not run, would count as config 5):** a "strict" session-reset RSI that stays blank until 14
  intraday changes exist (10:45 onward). It is still a shared-code change, so the same family test would apply.

Files: `PLAN.md`, `work/` (scripts rebuild.py, scan.py, an.py, live.py; outputs an_out.txt, live_out.txt, family_delta.csv).
Limits:
- The lab is survivor-biased and cannot apply ETB.
- 14 RSI candidates with non-standard geometry were not run.
- Live matching uses entry-minute bars (±10 min).
