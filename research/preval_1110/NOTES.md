Educational only — not financial advice.

# PREVAL 1110 — two days out-of-sample (11-09, 11-10) for PV0 / PV1 / PV2 / TEAM-6, and the Team switch (owner 2026-11-10)

Research only: **no config, setup, assignments or ledger change**. The owner decides. Paper trading (Alpaca paper) and
simulated books are labelled as such. 11-09 and 11-10 are the first sessions after the PV options were drawn up
(research/preval_1107, records through 11-06), so they are out-of-sample for every option. Two sessions is a small sample.

**Configurations tried / books compared (all reported):** PV0 (live + lab), PV1 (lab + live subset), PV2 = TEAM-6 lineup
(lab + Team sim + live subset), TEAM-8 (Team sim), all-26 together (lab) = 5 books; 1 hindsight cut (TEAM-6 without RW3/RW5)
shown as a data point only. Exposure Lab 11-10: 30 runs (26 alone + together + 3 PV books), as on 11-09.

## Inputs and checks
- **PV0 truth = live Primary journal** (origin/mcf-data journal.db, run_id=1, closed trades, R = pnl_adj / (|entry − stop| ×
  shares)): 11-09 −18.10R / 36 trades / Alpaca −$172.26; 11-10 −31.25R / 99 / Alpaca −$109.40.
- **Exposure Lab 11-10** run tonight (`python -m mcf.report.exposure_lab --date 2026-11-10 --jobs 4`, exit 0, no code change)
  → research/exposure_lab/2026-11-10.json.
- **Universe / blackout check (the PR #174 bug):** both lab days ran after the close on the *published* lists, not the stale
  intraday ones: 11-09 universe built 11-09 (5,094 → 3,655 symbols after PTP + earnings blackout, same as the Team final),
  11-10 universe built 11-10 (5,144 → 3,894, same as the Team final, blackout 1,250). The Team-6 sim numbers used here are the
  corrected after-close finals (research/shadow_primary/team/2026-11-09.json, 2026-11-10.json). No inflated intraday figure is used.
- **Drawdowns:** worst intraday drawdown = peak-to-trough of the 5-minute marked R path (closed + open lots at the last
  1-minute close), the lab's `r_path` / `book_stats`. For the live journal and the Team trades: `live_dd.py` (same functions,
  Team 1-minute bar cache) → `dd_out.json`. `summary.py` prints every table below.
- **Spread pool:** the 11-09 lab used the journaled spread pool as of the 11-09 evening, the 11-10 lab and the Team finals the
  current pool. Team R moves about ±5R with the pool on a day like 11-10 (Team-8 11-10 was −6.76R on the older pool, −12.31R now).

## Simulation margin
| same book, sim vs live | 11-09 | 11-10 |
|---|---|---|
| PV0: lab vs live Primary | −17.85 vs −18.10 (33 vs 36 trades) | −30.22 vs −31.25 (94 vs 99) |
| PV1: lab vs live subset (live Primary minus MF2-FD / MF4-FD / MF4) | +0.19 vs +0.19 | −21.91 vs −19.66 |
| TEAM-6: lab PV2 vs live subset (Primary RW3/RW5/L3-fromopen/ST7/NS5 + Live Lab NM-ETF) | +1.16 vs +0.13 | −17.77 vs −15.89 |

- The engine tracks live within about **1R** for the same book (PV0); a live subset is not a clean check (crowding and the
  latch differ once setups are removed), but it lands within about 2R. Plus the spread-pool sensitivity above (±5R on 11-10).
- Read differences between books of under ~3R as noise.
- TEAM-6 lab PV2 = Team sim on 11-10 exactly (−17.77R / 56 trades, DD −22.75R). On 11-09 the Team ran 7 setups with no L3
  (+0.48R / 7 trades for the TEAM-6 setups); the lab PV2 book has the full TEAM-6 incl. L3-fromopen (+1.16R / 17).

## Key table — two days out-of-sample (R after costs; trades in brackets)
| option | 11-09 | 11-10 | total | green days | worst intraday DD |
|---|---|---|---|---|---|
| **PV0** Primary as is — **live (truth)** | −18.10 (36) | −31.25 (99) | **−49.35** | 0/2 | −40.49 (11-10) |
| PV0 lab (cross-check) | −17.85 (33) | −30.22 (94) | −48.07 | 0/2 | −37.93 |
| **PV1** (opt1b, 7 setups) lab | +0.19 (16) | −21.91 (67) | **−21.72** | 1/2 | −26.37 (11-10) |
| **PV2 = TEAM-6** lineup, lab | +1.16 (17) | −17.77 (56) | **−16.61** | 1/2 | −22.75 (11-10) |
| TEAM-6, Team sim (11-09 without L3) | +0.48 (7) | −17.77 (56) | −17.29 | 1/2 | −22.75 |
| TEAM-8 Team sim, reference (11-09 = Team-7, no L3) | +2.54 (14) | −12.31 (70) | −9.77 | 1/2 | −21.67 |
| all 26 together, lab (reference) | −15.74 (89) | −39.22 (120) | −54.96 | 0/2 | −46.23 |

- Dollars: Team-8 11-10 +$352 (R red, $ green: sizing differs per trade); TEAM-6 11-10 −$145, 11-09 +$238. Primary live −$172.26 / −$109.40.
- Ordering on both days: TEAM-6 ≥ PV1 > PV0. TEAM-6 beat live Primary by +13.5R on 11-10 and +18.6–19.3R on 11-09. TEAM-6 is
  still **red over the two days** (−16.6 to −17.3R).
- The −20R account stop: live Primary closed 11-10 at −31.25R (low −32.04R), so new entries stopped but open lots ran on.
  No PV1 / TEAM-6 run reached −20R closed (TEAM-6 low −17.77R).

## Per setup — alone vs in the TEAM-6 book vs all-26 together (lab, R / trades)
| setup | 11-09 alone | 11-09 TEAM-6 | 11-09 all-26 | 11-10 alone | 11-10 TEAM-6 | 11-10 all-26 |
|---|---|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD | −0.29/1 | −0.29/1 | 0/0 | −9.52/19 | −9.52/19 | −1.16/3 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | −1.22/3 | −1.22/3 | −0.11/2 | −10.69/15 | −10.69/15 | −2.10/2 |
| L3-gap-slope-fromopen-FD | +0.68/10 | +0.68/10 | −1.22/8 | +2.35/19 | +2.35/19 | +4.95/8 |
| ST7-rsi50dn-long-pm-t1s1-FD | +1.00/1 | +1.00/1 | +1.00/1 | 0/0 | 0/0 | 0/0 |
| NS5-sma50-flush-oversold-long | 0/0 | 0/0 | 0/0 | −0.40/2 | −0.40/2 | −0.40/2 |
| NM-ETF-late-dip-di-long | +0.99/2 | +0.99/2 | 0/0 | +0.98/2 | +0.49/1 | 0/0 |
| *leaving:* L3-gap-slope-rsi5hi-FD | +1.37/3 | – | +0.45/1 | −3.62/12 | – | −0.97/3 |
| *leaving:* MF2-open-rsimidhi-flowsell-FD | −1.34/1 | – | −1.34/1 | −2.48/5 | – | −2.48/5 |
| *leaving:* MF4-h40-open-flowsell-FD | −16.71/16 | – | −16.71/16 | −5.82/22 | – | −0.37/6 |
| *leaving:* MF4-h40-open-flowsell | −16.71/16 | – | 0/0 | +1.63/7 | – | 0/0 |
| *leaving:* NS1-rsidip-rsi5pop-long | +0.55/1 | – | +0.55/1 | −0.41/4 | – | −0.59/2 |

- **Crowding inside TEAM-6 is small:** every setup's book R equals its alone R except NM-ETF on 11-10 (+0.98/2 alone → +0.49/1:
  1 `held_by_other` — L3-fromopen was short the same ETF). On 11-10 RW3 / RW5 lost 10 / 20 signals to their own −2R latch
  (`daily_loss`); L3-fromopen lost 210 to borrow, 16 to `held_by_other`.
- **Pairs inside TEAM-6 (alone runs):** RW3 × RW5 11-10 5 same-symbol overlaps, corr 0.79 (11-09: 0 overlaps, corr 0.14) — on a
  bad short day they are one bet taken twice. L3-fromopen × NM-ETF 11-10 3 overlaps, **all opposite side** (corr −0.20): a
  real, small clash on ETFs. L3-fromopen × RW3 / RW5 corr 0.43 / 0.36 on 11-10 (no shared symbols).
- The all-26 book does worse than TEAM-6 (−39.2R on 11-10): more short setups, more shared halt; the latch/halt there cut
  RW3/RW5 to 3/2 trades, which is why they look smaller in that column.
- Hindsight data point only (picked after seeing the result, not proposed): TEAM-6 without RW3/RW5 = +2.67R (11-09) /
  +2.44R (11-10). RW3+RW5 = −1.51R (11-09) and −20.21R (11-10), more than TEAM-6's whole 11-10 loss.

## The three thin setups on 11-10 (live vs Team)
| setup | home | live 11-10 | Team 11-10 | lab alone 11-10 | live 11-09 |
|---|---|---|---|---|---|
| CWT09-gapdn-vwaploss-g10-short | Live Lab | 0 trades | 0 | 0 | 0 |
| NM-ETF-late-dip-di-long | Live Lab → Primary in TEAM-6 | 1 / +0.54R | 1 / +0.49R | 2 / +0.98R | 2 / +0.90R |
| GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long | Gen | 3 / +1.18R | 14 / +5.46R | – (not in the lab set) | 1 / +0.22R |

GEN-261027-01 traded 14 times in the Team (Primary room, Primary universe) vs 3 in Gen (Gen is the overloaded account:
halt / buying-power / per-setup-cap skips, exposure_lab Part 1). It was the Team-8's best setup on 11-10 and is the main
reason Team-8 (−12.31R) beat TEAM-6 (−17.77R). Owner T7c keeps it (and CWT09-g10) out of Primary to build reps.

## Proposal for Wed 11-11 → Fri 11-13 (frozen, no rotation): TEAM-6
**In Primary (3 short / 3 long):** RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
L3-gap-slope-fromopen-FD (shorts); ST7-rsi50dn-long-pm-t1s1-FD, NS5-sma50-flush-oversold-long, NM-ETF-late-dip-di-long (longs).

**Moves (promotion = move; trimmed setups go to a testing account, never off):**
| setup | from | to | why this account |
|---|---|---|---|
| NM-ETF-late-dip-di-long | Live Lab | **Primary** | switched off in Live Lab in the same change |
| MF2-open-rsimidhi-flowsell-FD | Primary | Testing 1 | as in DM-MF2 / preval_1107 |
| MF4-h40-open-flowsell-FD | Primary | Testing 1 | as in DM-MF4 / preval_1107 |
| L3-gap-slope-rsi5hi-FD | Primary | Testing 1 | balance (it came from Testing 2 on 10-30; Testing 1 has the other L3 variant L3-lowdist, a different setup) |
| MF4-h40-open-flowsell | Primary | Testing 2 | kept apart from its FD twin, else "twin held" gives it no trades |
| NS1-rsidip-rsi5pop-long | Primary | Testing 2 | Testing 1 holds its FD twin NS1-rsidip-rsi5pop-long-FD (would be twin-held) |

- Counts after: Primary 10 → 6; Testing 1 13 → 16; Testing 2 15 → 17; Live Lab 21 → 20. Testing 1 = Testing 2 weight
  (16 / 17 is the closest split of 33). Testing 2 trades its top-500 pool (UNI1).
- MF4 base and NS1 have < 20 live trades from Testing 1/2; under the low-rep rule they could rotate through Explore 1 / Live Lab
  instead — owner's call.
- CWT09-gapdn-vwaploss-g10-short (Live Lab) and GEN-261027-01 (Gen) stay on in their homes.
- **Primary safety rules unchanged** (config/default.yaml): 0.25% risk per trade, −2R per-setup daily stop (latched),
  −20R account stop (no new entries), 77 slots, buying power ×3.2.
- Mechanics if approved: one config change + `python -m mcf.report.assignments` (docs/live/assignments.json) + ledger entry +
  `python -m mcf.research.ledger check`, merged outside 09:30–16:00 ET (setup-freeze).

## Against switching (plain)
1. **TEAM-6 was red: −17.77R on 11-10** (−$145), −16.6 to −17.3R over the two days, 1 of 2 green (the green day was only
   +0.5 to +1.2R). It is better than Primary (−31.25R on 11-10, −49.35R over two days), but it is "lose less", not "win".
2. **RW3 and RW5 lost heavily on 11-10 in both places:** TEAM-6 −9.52 / −10.69R (−20.21R together), live Primary −8.83 / −12.53R
   (−21.36R). They were a third of TEAM-6's trades and more than all of its loss.
3. **RW3 and RW5 overlap:** same gap-down pop-fade idea; on 11-10 5 same-symbol overlaps and a 0.79 correlation. On a short-hostile
   day the book carries the same bet twice; 3 of 6 setups (RW3, RW5, L3-fromopen) are gap-down shorts.
4. **Their records lean on 10-22:** without it RW3-FD +0.088R and RW5-FD +0.032R per trade, ~55% best-day share (BDI 1110);
   2-year lists −0.07 / −0.06R. L3-fromopen is a burst-day setup (77% of its R on one day).
5. **Conditions:** RW3-FD works when SPY is below its open at 10:00 (+0.71R vs −0.14R); L3-fromopen the reverse; RW5-FD works on
   ETFs, loses on stocks (top-20 CONDITIONS). A frozen book can't use that.
6. **Small sample, thin newcomer:** 2 sessions; NM-ETF has ~17 live trades and +0.029R on its 2-year validation block;
   ST7 traded once in two days.
7. **Simulation margin:** about 1R vs live for the same book, ±5R from the spread pool on a day like 11-10; differences between
   books under ~3R are noise. TEAM-6 vs PV1 (−16.6 vs −21.7R) is just beyond that.

## The honest alternatives
| choice | 2-day R | green | worst DD | trade-off |
|---|---|---|---|---|
| **TEAM yes** (TEAM-6) | −16.6 (lab) / −17.3 (Team) | 1/2 | −22.8 | best of the three on both days; one new setup (NM-ETF, low-rep); 5 setups out |
| **PV2 yes** | same lineup as TEAM-6 | | | identical setups; the only difference is framing (PV2 = Option 2, rotation allowed after) |
| **PV1 yes** | −21.7 | 1/2 | −26.4 | smaller change (3 Early Sellers out, nothing new in); keeps L3-rsi5hi (−3.62R alone 11-10) and NS1 |
| **PV0** | −49.4 (live) | 0/2 | −40.5 | no change; the Early Sellers setups (MF2-FD + MF4-FD) lost −18.3R (11-09) and −11.6R (11-10) live |

- PV0 is clearly worst. TEAM-6 and PV1 differ by ~5R over two days (TEAM-6 ahead both days), so the case for TEAM-6 over PV1
  is modest; the case for leaving PV0 is strong.
- A careful owner might take PV1 (fewer moving parts, no low-rep promotion) — it costs about 5R vs TEAM-6 on these two days
  and has a deeper drawdown. Neither option fixes the RW3/RW5 short-day exposure; both keep them.

## Rule changes in the window
- **EXPO1109** (`2026-11-09-expo1109-gen-temp-moves`): 5 GENs temporarily in Testing 1/2 on 11-09/11-10; reverted from 11-11
  (`2026-11-10-expo1109-revert`, PR #173). Not in any PV/TEAM book; affects Testing totals only.
- **Team fix PR #174/#175** (11-10, 21:42 UTC): intraday Team figures before 14:37 ET on 11-10 (and 11-06 / 11-09 intraday) used
  the stale universe and no earnings blackout and were inflated; the after-close finals used here are correct.
- No Primary sizing / stop / filter / timing change in 11-09..11-10 (ledger). Earlier: −2R latch from 10-29, ~$4k lot from 10-28.

Files: `summary.py`, `live_dd.py`, `dd_out.json`; research/exposure_lab/2026-11-10.json.

Educational only — not financial advice.
