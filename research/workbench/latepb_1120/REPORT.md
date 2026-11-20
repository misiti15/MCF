Educational only — not financial advice.

# Late Pullback Buy (MACD rising): why it is "blocked", and how to let it play more
`GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long`, Testing E since 11-12 (Gen 10-27..11-11).
Workbench, 2026-11-20, during market hours. Research only: no config, setup or account change, nothing merged.

## Owner summary (5 lines)
1. The "79.8% blocked" figure (67 of 84 signals) comes from the Gen account. 42 of the 67 blocks were Gen-account failures: the 11-04 account halt (21) and broker rejects for lack of buying power on 11-06..11-11 (21). Neither can happen in Testing E. There, resource skips are 0.8% and ROT2 family caps are off.
2. All the other blocks are quality filters, and they removed worse trades. Spread > 30 bps: 20 signals at +0.05R before paying the spread, −0.11R after half the spread. Stop-cost filter: 2 signals, both losers (−0.50R). In Testing E the setup already takes every clean signal it gets (3 taken; 9 skipped, all for spread or cost).
3. Unblocking frees nothing more. Priority, a reserved slot, a 2nd lot, a cap exemption or another account would each add 0 trades: no signal was ever skipped for priority, slots, lots or caps. The real limit is signal supply: signals came on only 9 of 18 active days, because of the breadth > 0.5 gate plus the pullback conditions. The Gen-era capacity rejects would have averaged +0.18R (43 trades, +0.10R without 11-10, which is 60% of their R). Those trades are already freed by the 11-12 move.
4. Loosening the signal does not help: 54 configs on the bench10 "normal way", none clears the bar of 2.82 on FIT. On this pipeline the parent itself is about zero (FIT −0.021R, CHECK −0.026R). Loosening Ret15m makes CHECK worse. MACD-hist 0.08 doubles trades at an equal (≈0R) average, but loses on FIT paired by day. The 13:30 start is +0.064R on FIT (80% of it from one day), then −0.017R on CHECK.
5. WB5 (Testing D, 0 signals in 3 sessions) is not proven starving yet. In those 3 sessions the parent signalled on only 1 day, and WB5's backtest trade-session rate (37%) makes 3 empty sessions about a 1-in-4 event. Keep it until 10 active sessions, and check why OSCR on 11-18 (14:00, $175M ADV) did not fire it.

## Owner decisions
| Code | Question | Recommendation |
|---|---|---|
| **LPB-UNBLOCK** | Keep the setup in Testing E as it is: no priority change, no cap / spread / cost-filter exemption, no second lot, no move. Optionally, as a report-only housekeeping fix, split `blocked_pct` in `docs/live/arena_reps.json` into "capacity" (halt, buying power, slots, caps) and "quality filter" (spread, cost, crosscheck, price) so the "blocked" triage tag no longer fires on Gen-era account failures. | **Yes: keep as is. Yes to the report-only split (after hours).** Testing E already takes every clean signal. Every unblock lever frees 0 trades, or frees trades that lose after spread. |
| **LPB-WIDE** | Loosen the signal (window start 13:30, MACD-hist 0.08 / 0.04, Ret15m −0.04 / −0.02, ADV floor $10M / $5M) to get more trades? | **No.** 0 of 53 variants clears the bar. On CHECK, every variant is ≤ 0R, and the extra trades average ≈ 0R. Logged as a parked finding (backlog `lpb-1120-loosen-grid`) so it is not re-run. |
| **LPB-WB5-OFF** | Retire the stricter child `...-WB5` (Testing D) because it starves? | **No (keep).** 3 sessions is too few, and the parent itself signalled on only one of them. Revisit at 10 active sessions (the arena_reps zero-signal triage point). Run a one-off parity check on 11-18 / OSCR first. Retiring it would also conflict with the trimmed-setups rule: low-activity setups get exposure and are never just switched off. |

**Rule-change context** (research/ledger.jsonl, effective dates inside the live window 10-27..11-19):
- 11-09/11-10 EXPO1109 temporary moves of other GEN setups out of Gen (this setup stayed in Gen).
- 11-12 move Gen → Testing E (GEN-GRAD). The Testing cost filter of 0.15R applies from then; Gen had none.
- 11-12 account daily halt 120R → 300R, and Gen buying-power multiple 3.8 → 1.8 (after this setup left).
- 11-17 TSZ1 testing sizing: half-size lots and 2x slots. R is comparable, $ is not.
- 11-18 live quotes recorded on every decision.
- 11-19 C3-ROT / ROT2 family caps. They are not binding: every account is under 5% resource skips.

The live record mixes the Gen book (no cost filter, cash-limited) with the Testing E book. The backtest grid uses one fixed rule set throughout.

---

## 1. Block diagnosis (most important)
Source: `signals` table, run 1, on `origin/mcf-data-gen` and `origin/mcf-data-testinge`, journal.db. This is the same count `mcf/report/arena_reps.py` uses: blocked = status ≠ `submitted`. Window 10-27..11-19: 84 signals, 17 submitted, 67 blocked (79.8%).

Every signal was replayed on 1-minute SIP bars (read-only Alpaca GET):
- Entry at the signal's reference price, with the live bracket: stop 1R, target +0.5R, R = 0.25 × daily ATR.
- The stop is checked first. A target counts only if traded through by $0.01. Flat at 15:55.
- LR8 costs, x3 under $5.

Replay check on the 17 taken trades: replay +0.211R vs the journal's +0.208R, per-trade correlation 0.87.

| Block reason | Signals | Days | Account | Replay avg R (LR8) | Comment |
|---|---|---|---|---|---|
| **Taken** | 17 | 7 | Gen 14 / E 3 | **+0.211** (w/o best day +0.153; 11-10 share 40%) | live journal +0.208 |
| Account halted (Gen, 11-04) | 21 | 1 | Gen | +0.006 | whole-account halt, one session; a weak day |
| Broker reject: no buying power | 21 | 4 (11-06, 09, 10, 11) | Gen | **+0.328** (w/o best day +0.268; **11-10 = 65% of R, `1 day`**) | Gen cash exhausted (cost basis ≈ $1.7k lots vs $0-1.3k buying power) |
| Spread > 30 bps | 20 | 8 | Gen 13 / E 7 | +0.046 before spread; **−0.111 after half spread** | filter working: 30-50 bps band 9 trades −0.056, > 50 bps 11 trades −0.156 (after half spread) |
| Stop-cost filter > 0.15R | 2 | 2 | E | −0.499 | both losers (SG, GDYN) |
| Opposite side held | 1 | 1 | Gen | +0.494 | GEV held short by a GEN short setup |
| Quote crosscheck | 1 | 1 | Gen | n/a | OMH ref 37.20 vs quote 41.69: data error, correctly skipped |
| Price < $5 | 1 | 1 | Gen | +0.396 | CORD $3.29; house rule |
| **Total** | **84** | **9 of 18 active days** | | | |

Grouped:
- Gen-account capacity / halt: **42 of the 67 blocks (63%)**, replay +0.17R.
- Quality filters (spread, cost): 22 (33%), replay −0.04R before spread, −0.19R after.
- Other: 3.

**Testing E alone (11-12..11-19, 6 active sessions):** 12 signals, 3 taken, 7 spread, 2 cost filter. **0 capacity blocks.** Account-wide, Testing E had 336 submitted, 216 spread, 91 ETB, 71 cost and 5 liquidity-size skips, with no buying-power or slot skips.

**Are blocked signals as good as taken ones?** It depends on the reason:
- The capacity-blocked ones were as good or better (+0.18R vs +0.21R), but their R leans on 11-10 (60% share).
- The filter-blocked ones were clearly worse.

Signal supply is the binding limit now. There were signals on 9 of 18 active days (all 18 were live sessions, none benched). The zero days, for example 11-12, 11-16, 11-17 and 11-19 in Testing E, produced no qualifying bar at all (breadth > 0.5 gate plus the pullback conditions).

## 2. Targeted remedies (quantified on the 18-day live window)
"Freed" = signals that a remedy would turn into trades, scored with the replay above.

| Remedy | Freed trades | Per active day | Avg R of freed | Verdict |
|---|---|---|---|---|
| A capacity-rich home (already done: Gen → Testing E, 11-12) | 43 (21 buying power + 21 halt + 1 opposite side) | +2.39 | **+0.175** (CI −0.02..+0.37; w/o best day +0.098; 11-10 share 60%, `1 day`) | Done. Taken + freed = 60 trades, 3.33 per active day, +0.185R (w/o best day +0.115, best-day share 53%) vs 0.94 per day recorded |
| Higher priority in Testing E / reserved slot | 0 | 0 | n/a | no priority / slot skip ever seen; Testing E resource skips 0.8% |
| Allow a 2nd lot / per-symbol lot cap exemption | 0 | 0 | n/a | no lot-cap skip; refire not in scope |
| Exempt from per-setup cap / family cap | 0 | 0 | n/a | per-setup cap 100 never reached; ROT2 family caps off (all accounts < 5% resource skips, arena_resources.json 11-17..18) |
| Spread limit 30 → 50 bps for this setup only | 9 | 0.50 | +0.020 before / −0.056 after half spread | No: it adds losers |
| Spread limit removed | 20 | 1.11 | −0.111 after half spread | No |
| Cost-filter exemption | 2 | 0.11 | −0.499 | No |
| Move to a less crowded account | 0 | 0 | n/a | Testing E is not crowded |

Owner rules respected:
- No in-session throttling is proposed.
- Nothing caps stacking.
- The only remedy with value, a capacity-rich home, is targeted at the failure (account cash and halt) and is already in place.
- Per-setup effect: one setup affected, no others touched.

## 3. Loosening grid (bench10 "normal way")
**Pipeline:**
- `research/ultimate_1119/top10/bench10.py` functions (walk_trades, add_r LR8 costs, book, stats), testing book: cap 100, ≤ 3 lots per symbol, price ≥ $5, cost filter 0.15R.
- Lab frames `research/history2y` with the breadth context; 1-minute exits from `data/cache_hist/1Min`.
- Entry at the decision-bar close; first qualifying bar per symbol-day.

**Samples:** FIT = 2024-10 + 2025-03..09 (170 sessions); CHECK = 2025-10-01..2026-11-04 (276 sessions; the frames end 11-04). **The locked block 2024-11-01..2025-02-28 was never read.**

**Grid (pre-registered):** window start {14:00, 13:30} × MACD-hist {0.12, 0.08, 0.04} × Ret15m-in-ATR {−0.069, −0.04, −0.02} × ADV floor {$20M, $10M, $5M} = **N = 54 configs**. Bar max(1.5, sqrt(2 ln 54)) = **2.82**. Breadth > 0.5 and the 15:00 window end are fixed, for two reasons: the lab frames end at 15:00, so a 15:30 end cannot be tested on them; and the Mechanic found entries after 14:30 average −0.10R.

**Selection:** the FIT finalist filter (more trades per session than the parent AND avg R ≥ the parent's FIT CI lower bound −0.154) admitted all 53 variants, because the parent's FIT CI is so wide. CHECK was therefore read once, for all 54. Every row is in `fit_all.csv` / `check_finalists.csv`.

**Parent on this pipeline:**
- FIT: 1,625 trades, 9.6 per session, **−0.021R** (CI −0.154..+0.112, w/o best day −0.056, t −0.32, worst day −64R).
- CHECK: 2,271 trades, 8.2 per session, **−0.026R** (CI −0.108..+0.056, w/o best day −0.047, t −0.61, worst day −54R, best day 2026-07-29).
- Best-day share is not defined, because total R is negative.

Selected rows (all 54 are in the CSVs):

| Config (start / MACD-hist / Ret15m / ADV) | FIT trades per session | FIT avg R (t) | CHECK trades per session | CHECK avg R (t) | CHECK w/o best day | Paired vs parent, CHECK R/day (t) |
|---|---|---|---|---|---|---|
| **Parent 14:00 / 0.12 / −0.069 / $20M** | 9.6 | −0.021 (−0.32) | 8.2 | −0.026 (−0.61) | −0.047 | n/a |
| 14:00 / 0.12 / −0.069 / $5M | 9.8 | −0.026 | 8.3 | −0.024 | −0.045 | +0.015 (1.83) |
| 14:00 / 0.08 / −0.069 / $20M | 16.1 | −0.023 (−0.43) | 15.6 | **−0.008** (−0.31) | −0.018 | +0.087 (0.53); FIT paired −0.171 (−0.48) |
| 14:00 / 0.04 / −0.069 / $5M | 31.9 | −0.024 (−0.68) | 35.8 | −0.006 (−0.35) | −0.012 | +0.013 (0.03) |
| 14:00 / 0.12 / −0.040 / $20M | 13.9 | −0.023 | 13.7 | −0.025 | −0.039 | −0.132 (−0.80) |
| 14:00 / 0.12 / −0.020 / $20M | 17.4 | −0.012 | 18.6 | −0.014 | −0.026 | −0.045 (−0.17) |
| 13:30 / 0.12 / −0.069 / $20M | 14.3 | **+0.064 (1.06)**; w/o best day +0.017, best-day share 80% (2025-04-09) | 11.8 | −0.017 (−0.50) | −0.032 | +0.016 (0.09) |
| 13:30 / 0.12 / −0.020 / $20M | 24.6 | +0.053 (1.20) | 26.9 | −0.022 | −0.032 | −0.391 (−0.85) |
| 13:30 / 0.04 / −0.020 / $5M (loosest) | 93.7 | −0.011 | 94.7 | **−0.046 (−3.49)** | −0.049 | −4.10 (−3.49) |

**Findings:**
- No config clears 2.82 on FIT (the maximum is 1.20) or on CHECK (all ≤ 0).
- **ADV floor:** neutral (≤ 0.003R change; about +1% trades).
- **Ret15m loosening:** worse on CHECK at every step.
- **MACD-hist 0.08:** about doubles trades. The extra 2,201 CHECK trades average +0.008R, the 1,272 FIT ones −0.030R. Avg R is about equal to the parent's, but not better than zero, and it loses on FIT paired by day.
- **13:30 start:** the only FIT gain, built on April 2025 (80% best-day share), and it fails on CHECK.

Under the "keep only variants that raise trades/day while avg R stays within the parent's CI" rule, several rows qualify on the letter: the parent's CHECK CI is wide and spans zero. None of them is an improvement worth deploying. Two more reasons not to:
- The C3-WB reform allows only exit / frequency changes on a proven parent.
- Gates on proven setups are on the guardrail list (rule 26).

**Not recommended.**

**Honest gap: bench vs live.** Live is +0.21R over 17 trades (day-clustered CI +0.08..+0.34, 7 traded days). The bench parent is about −0.02R on both halves. The Mechanic's earlier 2-year run (different engine) had +0.032R, with valid +0.008R. In the three live-window days the frames cover (10-27, 10-28, 11-04), the bench books 47 parent trades at −0.014R. The causes differ:
- The lab universe is 1,226 names; live polls more names.
- Breadth is computed on different universes.
- Live fills come from the quote and spread filter.

The live edge is therefore not confirmed by the backtest. That is one more reason to grow reps in its current home, rather than loosen the signal on a ≈0R backtest.

## 4. WB5 child (Testing D): retire?
`...-WB5` (window 14:00-14:30, ADV ≥ $100M, breadth change since 09:50 ≤ +0.20) has been enabled in Testing D on 11-17, 11-18 and 11-19, with **0 signals**.

Context:
- The parent signalled on only one of those days (11-18: OSCR, APPS, AVTX, BBNX, GDYN).
- Only OSCR fits WB5's window and ADV ($175M 20-day ADV; the others are $20-40M). OSCR would have been spread-blocked anyway (32 bps).
- In the Mechanic's backtest, WB5 traded on 162 of 439 sessions (37%), so 3 empty sessions has a probability of about 0.63³ ≈ 25%.

**Recommendation: No, do not retire it yet.**
- Revisit at 10 active sessions: arena_reps tags "zero-signal" there, and the tag never disables a setup.
- First, a one-off parity check: did the 11-18 OSCR bar fail on br_chg > 0.20, or is the 09:50 breadth missing in the live frame? WB5's `br_chg()` needs a tod = 950 breadth value. If that value is NaN live, the mask can never fire. This is worth ruling out.
- Owner rule (trimmed setups): low-activity setups get more exposure and are never just switched off.

## Files
- `live_signals_replay.csv`: all 84 live signals with reason, category, replay exit and R.
- `fit_all.csv`: all 54 configs on FIT.
- `check_finalists.csv`: CHECK for all 54, with paired-by-day vs the parent.
- `code/`: replay.py (journal + SIP 1-minute replay), grid.py (candidates + 1-minute walk on bench10 functions), score.py, parity.py. Scratch paths inside; bench10.py is imported from a copy with ROOT=/home/user/MCF.
- Configs counted: 54 grid configs. The live replay is diagnostic, not a config search.

Educational only — not financial advice.
