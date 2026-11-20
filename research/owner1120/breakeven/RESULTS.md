Educational only — not financial advice

# Owner item 2 (2026-11-20): extensive breakeven (stop-to-entry) test — RESULTS

Plan: PLAN.md (frozen before scoring). Code: lab_be.py (2-year engine), live_be.py (live replay), score.py (pass bar).
Outputs: out/score_out.txt, out/extra_out.txt, out/grid_all.csv.gz (every scope x rule cell), out/fam_best5.csv.
**Configs counted: N = 18,144** (432 rules x 42 scopes: book, 2 sides, 3 instrument types, 36 family-sides). The bar is
max(1.5, sqrt(2 ln N)) = **t >= 4.43**. The locked block 2024-11-01..2025-02-28 was filtered at read and asserted
absent. Costs are in: the bt_all model in the lab, LR8 live, and a breakeven exit pays stop slippage.

## Owner summary
1. **Verdict: FAIL. 0 of 18,144 cells pass.** Across the whole grid, no breakeven rule adds R on 2 years net of costs.
   The grid covered every trigger (+0.3 to +1.0R, 50 / 80% of target), every stop level (entry, entry + costs, entry
   -0.25R), every activation (immediate, +10 min, after 30 min, after a swing), every condition (always, after 13:00,
   SPY turning against the trade) and both sizes (whole position, half).
2. **Book-wide, all 216 whole-position rules lose on 2 years** (216 of 216 negative; 0 positive on the check half).
   - Losses range from -0.0001R/trade, where the rule almost never fires (+1R, soft BE, after 13:00), to
     -0.037R/trade (+0.3R trigger, entry + costs): -42,863R over 2 years, with 0 of 36 families and 0 of 91 setups better.
   - The rule that fires earlier and closer to entry loses more, on every axis.
   - The L16 rule (stop to entry at 80% of target) re-scores at exactly **-0.0070R/trade**, the same as L16, which
     confirms the engine.
3. **What it costs on the big winning days.** The book's top 10% days (45 of 446) take 30-80% of each rule's loss.
   - L16-type: -3,125R of -8,154R.
   - BE at +0.5R: -5,107R of -9,164R.
   - Breakeven turns the trades that would run to target on strong days into scratches.
4. **The one pocket that came close: inverse and long-vol ETPs.** The rule was soft BE (stop to entry -0.25R) after
   +1R, from 13:00 only. Result: +0.0012R/trade, t 3.58, fit t 2.01, check t 3.01, 7 of 8 families better, best day 9%.
   It still fails on four counts:
   - t 3.58 is below the 4.43 bar.
   - The worst family loses -0.05R/trade.
   - **Live it is negative** (-0.0135R/trade on 803 trades).
   - The size is tiny: about +26R over 2 years.
   This is not a remedy for the L3 inverse issue; that is a direction problem (item INV), not a stop problem.
5. **Per side, per instrument type and per family.**
   - Long and short: 0 of 432 cells positive.
   - Stocks and ETFs: none positive.
   - Families: 519 of 7,776 family cells are positive over 2 years, but none reaches the bar. All 10 family candidates
     from the fit half turned negative on the check half (CWT09_S, NS3V1_S, CWT13_S, GEN_S).
6. **Live looks the other way, and that is the trap.**
   - Live replay over 33 sessions: 183 of 216 rules positive. The best is +0.3R trigger, entry + costs: +0.016R/trade,
     +444R, t 2.1.
   - Lab and live deltas correlate **-0.58**.
   - The live gain comes from the red days: +540R on losing book days and -96R on green days.
   - The live window averages -0.15R/trade, so breakeven helps when targets are not being hit. Over 446 lab days the
     pattern reverses.
   - 157R of the 444R comes from GEN hold trades (no target, not in the lab): +0.046R/trade on 3,391 trades. That is a
     lead for GB-GENTRAIL, not evidence for breakeven.
7. **Recommendation: BE-NO.** Keep breakeven off in every account. This is consistent with GB-NOEXIT. Record the 18,144
   configs as tested. Do not re-propose without a new mechanism. Fold the GEN-hold live observation into the GB-GENTRAIL
   research.

## Data
- **Lab:** the bt_lab1104 signals (the L16 set): 1,165,484 trades, 95 setups, 446 sessions.
  - BASE avg -0.0711R, matching L16.
  - Fit = sessions up to 2025-09-30. Check = after that, scored once, and only fit candidates are judged on it.
  - GEN hold geometry is not in the lab lists.
- **Live:** run 1 of all 10 journals, 10-06..11-19, 27,954 trades replayed on Alpaca 1-minute SIP bars (550 read-only
  requests; bars kept in scratch). The replay is descriptive: bar-level stop-first fills, and the exit minute's bar is
  ambiguous.
- **Borrow and inverse funds:** breakeven does not change how long a trade is held overnight (all trades are intraday), so
  borrow is the same in BASE and the variant and cancels in the paired delta. Leveraged and inverse decay works over days
  and does not apply intraday. Their wider spreads enter only through the cost tier (price < $5 or gap >= 20%).

## Book-wide grid (whole position; mean delta R/trade by dimension, lab full / fit / check, live)
| Dimension | Value | 2y delta | Fit | Check | Live | Top-decile-day R |
|---|---|---|---|---|---|---|
| Trigger | +0.3R | -0.0133 | -0.0185 | -0.0106 | +0.0061 | -6,526 |
| | +0.5R | -0.0051 | -0.0078 | -0.0038 | +0.0034 | -3,527 |
| | +0.75R | -0.0023 | -0.0034 | -0.0017 | +0.0023 | -1,537 |
| | +1.0R | -0.0004 | -0.0002 | -0.0004 | +0.0006 | -162 |
| | 50% of target | -0.0114 | -0.0172 | -0.0085 | +0.0015 | -5,258 |
| | 80% of target | -0.0043 | -0.0065 | -0.0032 | +0.0009 | -1,787 |
| Level | entry | -0.0060 | -0.0087 | -0.0046 | +0.0021 | -3,252 |
| | entry + costs | -0.0087 | -0.0124 | -0.0068 | +0.0028 | -3,913 |
| | entry -0.25R (soft) | -0.0037 | -0.0057 | -0.0027 | +0.0025 | -2,233 |
| Activation | immediate | -0.0074 | -0.0110 | -0.0056 | +0.0034 | -3,715 |
| | +10 min | -0.0056 | -0.0082 | -0.0044 | +0.0024 | -2,909 |
| | after 30 min in trade | -0.0053 | -0.0075 | -0.0042 | +0.0013 | -2,679 |
| | after a swing | -0.0061 | -0.0091 | -0.0047 | +0.0028 | -3,228 |
| Condition | always | -0.0087 | -0.0119 | -0.0071 | +0.0037 | -4,111 |
| | after 13:00 | -0.0047 | -0.0070 | -0.0036 | +0.0008 | -2,406 |
| | SPY turned against | -0.0050 | -0.0079 | -0.0035 | +0.0029 | -2,881 |

The half-size rules are exactly half of each delta, with the same t. Moving the stop on half the position halves the
damage but does not change the sign.

## Headline rules: per-family and per-setup effect (2 years; live)
| Rule | 2y delta/trade (t) | Total | w/o best day | Top-decile days | Families better / worse | Setups better / worse | Live delta/trade, total (best-day share) |
|---|---|---|---|---|---|---|---|
| L16: 80% of target, entry | -0.0070 (-8.6) | -8,154R | -0.0071 | -3,125R | 1 (+11R) / 35 (-8,165R) | 6 (+17R) / 85 (-8,164R) | +0.0011, +30R (72%: one day) |
| +0.5R, entry (BE50) | -0.0079 (-4.8) | -9,164R | -0.0081 | -5,107R | 0 / 27 (-9,164R) | 0 / 55 (-9,091R) | +0.0051, +143R (22%) |
| +0.3R, entry + costs (live best) | -0.0368 (-13.6) | -42,863R | -0.0372 | -14,358R | 0 / 36 (-42,863R) | 0 / 91 (-42,686R) | +0.0159, +444R (16%) |
| +0.75R, soft, after swing | -0.0015 (-3.5) | -1,765R | -0.0016 | -1,184R | 5 (+73R) / 22 (-1,837R) | 14 (+126R) / 41 (-1,893R) | +0.0025, +71R (25%) |
| 50% of target, entry, +10 min, SPY against | -0.0091 (-7.1) | -10,643R | -0.0094 | -4,931R | 4 (+70R) / 32 (-10,713R) | 9 (+94R) / 82 (-10,728R) | +0.0016, +44R (108%: one day) |
| +1.0R, soft, after 13:00 (book's least-bad) | -0.0001 (-1.1) | -87R | -0.0001 | -67R | 2 (+56R) / 6 (-144R) | 2 (+56R) / 7 (-141R) | -0.0005, -15R |

The worst family under almost every rule is ST4 long, followed by ST7 long and the GEN / L3 / RW6 / NM groups (L16 table).

## Fit candidates (32 cells: fit delta > 0, fit t >= 2) on the check half
| Scope | Rule | Fit t | Check delta (t) | 2y t | Live (n) | Why it fails |
|---|---|---|---|---|---|---|
| inverse / vol ETPs | +1.0R, soft BE, after 13:00 (4 activations, F and H) | 2.01 | +0.0014 (3.0) | 3.47-3.58 | -0.0056 to -0.0135 (803) | t below 4.43; worst family -0.05; live negative |
| inverse / vol ETPs | +1.0R, soft BE, after a swing, always / SPY | 2.60 / 2.25 | +0.0002 (0.2) / -0.0005 | 1.28 / 0.48 | negative | check fails |
| GEN short | +1.0R, soft BE, 30 min, SPY | 2.53 | -0.0001 | 0.78 | -0.005 (1,938) | check fails |
| CWT09 short | L16 rule (80% of target, entry) | 2.32 | -0.0131 (-1.8) | -0.26 | +0.015 (428) | check fails |
| NS3V1 short | 50% of target, soft BE, after 13:00 | 2.26 | -0.0051 (-0.9) | -0.10 | +0.012 (86) | check fails |
| CWT13 short | +0.75R / 80% of target, soft BE, after 13:00 | 2.01-2.09 | -0.0036 to -0.0042 | -0.1 to -0.3 | +0.002 (233) | check fails |

## Rule / config changes inside the live window (research/ledger.jsonl)
The live replay spans these changes and mixes the regimes:
- 10-16/17: Testing 2 CWT14 scale-out.
- 10-23: per-setup latch; Testing setup stop off.
- 10-26: Gen caps (GX2).
- 10-28: Primary sizing changed twice.
- 10-29: Primary -2R latch.
- 10-30: Testing cost filter.
- 11-12: LR1 / LR3 / LR8; Gen and Graveyard sizing (REPV).
- 11-16: ROT1.
- 11-17: TSZ1 sizing; SPYEXIT engine; WB4 copies.
- 11-18: GY-BENCH, SRCV1.
- 11-19: C3 Epoch 1 (EXIT100, ROT / ROT2, WB / WB5, U9-TGT, U9-ETB, TAGS1; NS5 out of Primary).
- After the window: the 11-20 broker stop / target rounding fix, 9 new testing setups, the ULT admissions and FOOTRACE-EXIT.

## Proposal (nothing applied)
| Code | Recommend | What | Effect per setup | Conflicts | Next step |
|---|---|---|---|---|---|
| **BE-NO** | Yes | Keep breakeven / stop-to-entry off in every account. Record the 18,144 configs (lineage with L16, BEREPLAY and giveback) as tested and failed. | none (no change); avoids -0.001 to -0.037R/trade, 0-5 of 36 families better | consistent with GB-NOEXIT; no change to the -2R latch or WB2 | backlog finding line on your yes |
| BE-INVWATCH | Optional (research only) | Keep the inverse / vol "+1R, soft BE, after 13:00" cell on watch. Re-score it once 6 more months of live and lab data exist. | inverse / vol trades only (about 2% of trades) | INV (direction rule) comes first; a tweaked copy would be a new setup (11-18) | none now |
| (into GB-GENTRAIL) | Yes | Add "+0.3 / +0.5R stop to entry" as two configs in the GEN-hold trail study | GEN hold setups (live 3,391 trades, -0.219R) | GENTRAIL is already research only | inside GENTRAIL |

## Caveats
- Lab fills at the stop level or the bar's open. Stop-first inside a minute is slightly conservative for breakeven
  (a same-minute target and breakeven touch counts as the breakeven).
- The lab covers first signals without account caps, so the live account mix differs.
- The live replay is 33 sessions, descriptive only, and the window was a losing one.
- The SPY-against threshold (0.10%) and the swing pivot (2 bars) are single pre-registered values, not tuned.

Educational only — not financial advice.
