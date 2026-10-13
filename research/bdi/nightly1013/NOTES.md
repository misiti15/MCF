# Nightly winner/loser autopsy: 2026-10-13 (primary, Testing 1, Testing 2)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They are a diagnosis, not evidence. No locked holdout was scored, and **0 configurations were tested on the history**. The tables below are descriptive splits of today's trades (about 25 one-session splits, none of them gated).*

Inputs: `journal.db`, `status.json` (every commit of the day, via `git log`), `reports/scorecard.json` and `intraday/2026-10-13.jsonl` from `origin/mcf-data`, `mcf-data-testing` and `mcf-data-testing2`. GitHub Actions log of the Testing 1 trade job (run 38410196754, read-only). SIP 1-minute bars for the 482 traded symbols plus SPY, QQQ and IWM (Alpaca market data only, read-only; `fetch.py`). No trading endpoint was called, so broker fills were **not** read directly. The broker side of the check is the account equity and the position quantities that `status.json` records from the broker.

Scripts in this folder:
- `build.py` builds `trades.csv` (1,036 real trades, with lot number, retry flag and MFE/MAE from the bars).
- `qtycheck.py` compares broker and journal quantities.
- `mispair.py` re-prices the mispaired lots.
- `summ.py` produces the splits.
- `attr.py` produces the intraday attribution.
- `sc4.py` produces the MF/NS review.

Market: SPY +0.09% open to close (range −0.17% to +0.17%). QQQ was **+0.56%** (high +0.61% at 10:01, back to +0.10% at 11:30, +0.57% again by 12:30). IWM was **−0.46%** (low −0.82% at 11:46). It was a split tape: large-cap tech and semis were strong and small caps weak. The 11:46–12:30 rebound is where the short books bled.

## Failures first

### 1. ACCURACY CHECK: the journal does not fully match the broker in Testing 1 or Testing 2 (new stacking bug). Primary matches exactly.

| account | equity 09:30 (pre-open) | equity 15:55 (closed) | broker day P/L | journal day P/L | gap (broker − journal) | orders still `submitted` today | explained by |
|---|---|---|---|---|---|---|---|
| Primary | 95,798.13 | 95,702.74 | **−95.39** | −95.39 | **0.00** | 0 of 18 | — |
| Testing 1 | 99,989.44 | 99,335.17 | **−654.27** | −629.03 | **−25.24** | 0 of 371 | 7 mispaired lots: −23.26 (re-priced on bars) |
| Testing 2 | 99,330.06 | 99,223.39 | **−106.67** | −103.27 | **−3.40** | 0 of 647 | 2 mispaired lots: −3.69, plus partial target fills of about −0.1 to −1.2 |

- **What is right.** Every order has exactly one trade row (18/18, 371/371, 647/647). No order from today is left `submitted`, so the pagination fix for 10-12's ghost orders works for new orders. In every row, P/L = side × (exit − entry) × shares (maximum deviation 0.00). No exit comes before its entry, and no row has 0 shares.
  - Stacked lots have their own rows, each with its own quantity and its own entry (the parent fill).
  - Sibling lots that were filled in the same poll share the same fill price. For example, HCA MF3 and MF5 in primary each made +$9.52.
- **Bug: a lot can be closed in the journal at another lot's fill ("flatten-path mispairing").**
  - In `reconcile_day`, a lot whose own legs have not filled falls through to the flatten search. That search takes **any** opposite-side order on the same symbol that filled after the lot's entry.
  - In 9 cases, the stop fill of a sibling lot was taken as this lot's exit. The lot was journaled as `flatten` at the sibling's stop price and timestamp, and its order was marked `closed`. Its real exit was never recorded.
  - Evidence from `status.json`, where the broker positions are recorded and the journal says flat:

| account | symbol | journal "flatten" lots (pnl) | sibling stop it copied | broker still held | until | re-priced exit (bars) | diff |
|---|---|---|---|---|---|---|---|
| T1 | CLS | RW2 + exhaustion_short, 2 sh each (−1.78, −1.78) | L3-lowdist stop 14:18:00 | −4 sh | 15:38 | own stop 353.71 (15:38) | −16.24 |
| T1 | P | L3-lowdist 6 sh (−6.06) | NS2-FD stop 14:22:21 | −6 sh | 15:38 | own stop 156.77 (15:41) | −4.64 |
| T1 | CRDO | RW2 + exhaustion_short, 4 sh each (−3.20, −3.20) | L3-rsi5hi stop 14:20:37 | −8 sh | 15:52 | flatten ≈197.92 | −1.96 |
| T1 | CAT | RW7 + heat_fade_short-FD, 1 sh each | MF3-FD stop 14:24:18 | −2 sh, then −1 sh | 14:32 | own stops 14:27 and 14:34 | −0.42 |
| T2 | XP | CWT14-pdl-p05-lowvol + coil-k4, 29 sh each | CWT14-pdl-p10-lowvol stop 12:10:30 | 58 sh | 12:13 (one snapshot) | own stops 12:15 | −3.69 |

- **How much this explains.** Re-pricing the 9 lots on the bars gives **T1 −$23.26 against a gap of −$25.24**, and **T2 −$3.69 against −$3.40**. The timing matches every broker snapshot, so this accounts for essentially all of today's gap.
  - Of the 41 (T1) and 95 (T2) stacked lots that stayed open while a sibling's leg filled, all the others were paired correctly. The bug therefore does not hit every overlap, and why these stop fills were visible to the flatten search is not confirmed without broker order data.
  - The fix is housekeeping (rule 15): in the flatten path, exclude every leg id of every parent in `by_id`, and accept only the lot's own `-x` order or a fill at or after the flatten time.
  - **Side effect, worse than the P/L:** `_release_closed_lots` frees the mispaired lot in the runner. Broker shares and their resting brackets then remain with no lot record, which also miscounts the lot cap and slots. The status `lots` label showed CLS −4 sh as "1 lot, exhaustion_short".
- **Second, smaller defect: partial fills of target legs.** Reconcile books the whole lot at `leg.filled_avg_price` even when the target limit filled only partly. Persistent broker-vs-journal quantity mismatches (≥ 2 snapshots) in T2:
  - RBLX: 18 sh short, 10 filled at target 14:58. The remaining 8 sh rode to the flatten. Re-priced effect −$1.08 to +$0.28.
  - GLD: 1 of 2 sh rode to the flatten (≈ −$0.14).
  - SAIA (1 of 2 sh), EWY (4 of 5 sh) and BROS (3 of 75 sh) are probably remainders that filled later at the same limit, so price was not affected.
  - Fix: use `leg.filled_qty`, and pair any remainder to its own close.
- **Not explained here.** Equity moved overnight between the 10-12 close snapshot and the 10-13 pre-open: primary −0.85, T1 −3.72, T2 −6.67. Possibly late fills after the 15:55 snapshot, or fees; not checked.
- **Old ghost orders from 10-12 remain.** T1 has 16 and T2 has 24 orders from 10-12 still `submitted`, down from 20 and 45. Reconcile recovered 4 T1 trades and 21 T2 trades into 10-12: T1 10-12 is now 188 trades / +$36.03, and T2 10-12 is 336 trades / −$652.05 against the broker's −$663.27, a gap of −$11.22.
- **The 36 rejects in Testing 2.**
  - **35 at 10:10:24.** All are CWT14 ORL-reclaim longs plus one CWT05, on the 10:09 decision bar (bar_index 39), in CNP, D, EXC, LULU, NEE, NI, PCG, PEG, PPL and XLU, mostly utilities moving together. The message was "take_profit.limit_price must be >= base_price + 0.01": the live price had passed the tight 0.5R target (8–39 c) by submit, from −0.06R to +0.49R past it. Up to 4 setups were rejected per symbol.
  - **This was not a restart artifact.** The job restarted at 10:04:50, and the first poll after it (10:05:03) had 0 rejects. The runner only takes market signals on the latest bar, so the restart does not replay old signals.
  - **It is a recurring risk of tight-target market brackets on 5-minute polls**, and it will repeat whenever a correlated group gaps through targets at a poll. The reject itself is the safe outcome: the trade would have been an instant target fill at about 0R minus costs.
  - The cost is in the near-misses that were accepted: the 87 entries in the same poll made −$77.10 (−0.083R).
  - **1 at 12:15 (TTD).** The quote was already through the stop. The "price already through stop" guard uses the bar close, not the quote.
  - Rejected entries do not use up the lot cap. The near-miss risk is now backlog item `nightly-1013-tight-target-progress-skip`.

### 2. Testing 1 lost −$629 (journal; broker −$654)
- The loss came from shorts in names that kept rising, and stacking concentrated it. Shorts: 275 trades, −0.196R, −$760.20. Longs: 96 trades, +0.120R, +$131.17.
- The account was green only 11:00–11:52 and 13:24–13:34. Its minimum was −$726 at 15:44.

## Headline per account (real trades, run 1)
| account | trades | win% | avg R | P/L (journal) | broker | cost-adj | stop / target / flatten | green intraday |
|---|---|---|---|---|---|---|---|---|
| Primary (11 setups) | 18 | 50% | −0.194 | **−$95.39** | −$95.39 | −$101.67 | 8 / 9 / 1 | 10:51–12:01 (peak +$92 at 11:39; min −$102 at 14:11) |
| Testing 1 (39) | 371 | 43% | −0.114 | **−$629.03** | −$654.27 | −$677.45 | 120 / 84 / 167 | 11:00–11:52 and 13:24–13:34 (peak +$118 at 11:37) |
| Testing 2 (30) | 647 | 67% | +0.020 | **−$103.27** | −$106.67 | −$183.19 | 160 / 422 / 65 | 09:53–10:25 (peak +$157 at 10:13; min −$311 at 11:48) |

Exit asymmetry, with the same picture as 10-12:
- T1: stops −1.067R against targets +0.953R, at a 43% win rate.
- T2: stops −1.048R against targets +0.456R. Its t05 geometries need about 70% wins, and it won 67%.

## Primary (per setup)
| setup | n | win% | avg R | P/L | stops | MFE | MAE |
|---|---|---|---|---|---|---|---|
| MF5-flowsell-vwapup-rsi5hi | 5 | 60 | +0.089 | +24.28 | 2 | 0.71 | 0.48 |
| MF3-open-flowsell-rsi5hi | 1 | 100 | +0.688 | +9.52 | 0 | 0.86 | 0.17 |
| MF4-h40-open-flowsell | 1 | 100 | +0.198 | +6.27 | 0 | 0.32 | 0.32 |
| NS1-rsidip-rsi5pop-long | 1 | 100 | +0.134 | +3.90 | 0 | 0.20 | 0.20 |
| NS3-failed-vwap-reclaim-short | 1 | 0 | −1.093 | −12.59 | 1 | 0.18 | 1.02 |
| MF2-open-rsimidhi-flowsell | 1 | 0 | −1.033 | −16.43 | 1 | 1.45 | 1.00 |
| MF1-945-flowsell-vwapup | 1 | 0 | −1.223 | −18.54 | 1 | 0.20 | 1.08 |
| NS2-sma50break-overbought-short | 7 | 43 | −0.230 | **−91.80** | 3 (+1 flatten) | 0.62 | 0.71 |

- NS2 was the whole loss. EBAY, AMD and SEI hit their targets (+$48.20); SWKS, CORZ and TTMI were stopped (−$102.43) and CBRS was flattened (−$37.57).
- NS2 shorted semis and AI hardware into the QQQ rebound, the same names that hurt Testing 1.
- 17 of 18 trades were shorts. Stacking touched 1 symbol (HCA: MF3 and MF5, +$9.52 each).
- RW6G1 made 0 trades and logged **0 signals** in 4 sessions. See the MF/NS review.

## Testing 1: drivers of the −$629
| setup (worst first) | n | win% | avg R | P/L | | setup (best first) | n | win% | avg R | P/L |
|---|---|---|---|---|---|---|---|---|---|---|
| heat_fade_short-FD (ex-primary FD) | 69 | 35 | −0.229 | −146.58 | | **LIQ-orl-sweep-open15-s25-long (new)** | 44 | 64 | +0.316 | **+137.45** |
| NS2-sma50break-overbought-short-FD | 24 | 33 | −0.332 | −132.85 | | NS1-rsidip-rsi5pop-long-FD | 7 | 86 | +0.189 | +22.67 |
| RW7-gapdn-bounce-early-short-FD | 32 | 38 | −0.259 | −103.57 | | heat_fade_long (ex-primary) | 8 | 50 | +0.381 | +21.47 |
| RW2-exhaustion-noon-adv150-short-FD | 21 | 33 | −0.254 | −78.28 | | L3-gap-slope-fromopen-FD | 15 | 47 | −0.030 | +15.36 |
| RW1-gapdn-bounce-flowsell-short-FD | 8 | 12 | −0.701 | −64.77 | | MF3-open-flowsell-rsi5hi-FD | 5 | 60 | +0.094 | +11.96 |
| heat_fade_long-FD | 18 | 22 | −0.414 | −54.71 | | ST6 / ST5 / ST4 | 5 | — | — | +27.47 |
| exhaustion_short-FD | 11 | 36 | −0.260 | −50.40 | | MF4-FD | 2 | 100 | +0.219 | +5.47 |
| L3-gap-slope-rsi5hi-FD | 16 | 56 | −0.094 | −44.49 | | RW3-FD | 3 | 33 | −0.089 | +5.60 |
| RW6-ns2-up3-short-FD | 9 | 33 | −0.301 | −41.29 | | | | | | |
| exhaustion_short (ex-primary) | 7 | 29 | −0.208 | −35.78 | | | | | | |

The full 35-setup table is reproduced by `summ.py`. Other notable rows: L3-lowdist-FD −$27.82 (14 trades), NS3-FD −$27.20 (8), RW5-FD −$18.16 (3), RW6G1-FD −$17.49 (5), RW4-FD −$14.06 (4).

- **Shorts in names that kept rising.** The 10 biggest losing symbols lost −$473: SOXL, AXTI, STX, TTMI, RIOT, FCEL, CRDO, RDW, FPS and IREN. All ten were stacked 2–3 deep.
- **Time of day.** 12:00–12:59 lost −$341.42 on 122 entries (111 shorts, −$379.50). Shorts entered 11:30–12:59: 130 trades, 38% wins, −$390.69, into the 11:46→12:30 rebound. 10:xx shorts lost −$188.50. Longs were positive in every hour except 09:5x and 14:xx.
- **Stacking: see the next section.** Symbols that got stacked lost −$623.90 over 172 trades. Symbols with a single lot lost −$5.13 over 199 trades.
- **New LIQ setups.**
  - LIQ-orl (its first session with trades): 44 trades, all first lots, entered 10:00–12:00. It made +$137.45, or +$77.79 without its best 3 trades (LW +27, SITE +19.7, PCG +13). 37 of its 44 exits were flattens: it holds all day.
  - LIQ-pdl-sweep: 0 signals.
- **retry_after_release: 0 retry entries in T1 and T2.** No signal row carries `"retry_after_release": true`. Since stacking went live, only "lot cap" (T1 37, T2 45) and "opposite side held" (23 and 8) skips are eligible. A retry also needs a fresh market signal on the latest bar from a setup that already fired, which most of these one-shot setups never produce. The setting cannot be evaluated yet.
- **Ex-primary setups.** 20 trades, −$22.57, avg R +0.092:
  - heat_fade_long +$21.47 (8 trades)
  - exhaustion_short −$35.78 (7)
  - heat_fade_short −$10.65 (1)
  - orb20_a +$1.81 (2)
  - intraday_momentum +$0.58 (2)

  orb20_a and intraday_momentum now fire, so housekeeping item H-2 from 10-12 is resolved. Their -FD copies (heat_fade_short-FD −$146.58, heat_fade_long-FD −$54.71, exhaustion_short-FD −$50.40) lost far more than the originals.
- **Before vs after the restart.** Before 10:04:50: 10 trades, −$30.48. After: 361 trades, −$598.55.
- **Loss types.**
  - Losers: 210, median MFE 0.24R, MAE 1.00R.
  - Winners: 158, MFE 0.89R, MAE 0.32R.
  - 91 losers never worked (MFE < 0.2R) and cost −$809.

## Did stacking add winners or losers? (lot 1 = no same-side lot open at entry)
| account | single-lot symbols (lot 1) | first lot on symbols that later stacked | lots 2–3 (added by stacking) | of which clone lots (same entry + stop as a sibling) |
|---|---|---|---|---|
| Primary | 16 trades, −$114.43 | 1, +$9.52 | **1, +$9.52** | 1, +$9.52 |
| Testing 1 | 199 trades, −0.047R, **−$5.13** | 72, −0.314R, −$356.59 | **100 trades, 36% win, −0.104R, −$267.31** (journal; about −$290 with the mispaired lots re-priced) | 57, −$143.88 |
| Testing 2 | 179 trades, −0.033R, −$66.07 | 219, +0.063R, +$20.63 | **249 trades, 67% win, +0.022R, −$57.83** (lot 3 alone: 60 trades, −$67.76) | 166, +$35.35 |

- **Testing 1: stacking added losers.** About 42% of the journal loss came from the extra lots: shorts −$307.30 over 93 lots, longs +$40.00 over 7. 60 of the 100 were opened in the **same poll** as lot 1 (−$201.40, −0.167R). These are windowed and -FD copies, or sibling variants, firing together with an identical bracket, which is one trade at 2–3× size.
  - A first lot that later got company was itself the worst group (−0.314R).
  - Agreement among short setups marked bad shorts today. This matches the 2026-10-08 history test (`loop-1008-multisetup-consensus-t1`): short agreement of 2, 3 or 4 setups scored −0.112, −0.130 and −0.222R.
- **Testing 2: roughly neutral.** Lots 2–3 were −$57.83 at +0.022R. Lot 3 was negative (−$67.76) and clone lots were slightly positive.
- **One session, descriptive, and not a test.** Two backlog ideas (below).

## Testing 2 (per setup)
| setup | n | win% | avg R | P/L | stops/tgt/flat |
|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p05-long | 66 | 73 | +0.152 | +74.47 | 12/46/8 |
| CWT14-failbrk-pdl-p10-long | 53 | 79 | +0.141 | +66.06 | 8/39/6 |
| CWT14-failbrk-pdh-p10-short | 36 | 86 | +0.285 | +59.18 | 4/31/1 |
| CWT12-coil-k4-long | 32 | 69 | +0.001 | +36.53 | 9/22/1 |
| CWT14-failbrk-pdh-p10-lowvol-short | 17 | 76 | +0.273 | +31.21 | 3/13/1 |
| CWT14-failbrk-pdl-p10-lowvol-long | 26 | 81 | +0.156 | +22.18 | 5/21/0 |
| CWT12-coil-k6-long | 14 | 36 | +0.048 | +14.49 | 9/5/0 |
| CWT14-failbrk-pdl-p05-lowvol-long | 41 | 71 | +0.141 | +11.06 | 6/29/6 |
| CWT14-failbrk-orl-p05-lowvol-long | 80 | 70 | −0.002 | +10.45 | 18/56/6 |
| CWT13-vwapstretch-z05-long | 10 | 70 | +0.094 | +5.82 | 1/7/2 |
| CWT05 (4 variants) | 14 | 50 | — | −28.93 | 7/7/0 |
| CWT14-failbrk-orl-p10-lowvol-long | 50 | 70 | −0.034 | −28.22 | 14/35/1 |
| CWT14-failbrk-pdh-p05-lowvol-short | 39 | 54 | −0.128 | −41.84 | 14/20/5 |
| CWT13-vwapstretch-z05-short | 12 | 25 | −0.404 | −52.97 | 4/1/7 |
| CWT14-failbrk-orl-p10-long | 49 | 69 | −0.067 | −55.06 | 14/34/1 |
| CWT14-failbrk-orl-p05-long | 83 | 64 | −0.048 | −58.58 | 20/52/11 |
| CWT09 shorts (4 variants: g5/g10 vwaploss and lowerhalf) | 18 | 11 | — | **−166.51** | 12/0/6 |

The remaining rows are small: CWT13-z075-long −$1.65 (4 trades) and CWT12-flag-s1-long −$0.96 (3).

- **CWT09 gap-down shorts lost −$166.51 on 18 trades.** They were stopped or flattened against the rebound. Their structural stops give them a large dollar risk per trade (see `nightly-1012-structural-exit-risk-normalize`).
- 10:xx lost −$320.86 on 373 entries (58% of all entries). 09:5x (55 trades, before the restart) made +$119.10.
- Longs +$67.66, shorts −$170.93. On the down-drift 10-12 it was the reverse.

## Intraday attribution (when green, who carried it)
Each table marks P/L at the peak: realized plus open lots marked to the 1-minute close.
- **Primary, peak +$92 at 11:39.** NS2 +$56.3, MF2 +$17.5, MF5 +$11.1, MF4 +$6.3, MF3 +$6.0. MF1 −$18.5.
  - After that, NS2's SWKS, CORZ, TTMI and CBRS reversed in the 11:46–12:30 QQQ rebound, and NS2 ended at −$91.80.
- **Testing 1, peak +$118 at 11:37** (+$80 marked).
  - Carried by LIQ-orl +$43.1, orb20_a +$29.1, NS2-FD +$22.1, L3-fromopen-FD +$16.5 and MF5-FD +$10.9.
  - Dragged by heat_fade_long-FD −$65.2 and heat_fade_short-FD −$21.2.
  - **Second green spell, about 13:30:** carried by the L3 gap-slope trio (+$80.4, +$61.9 and +$44.0 marked) plus heat_fade_long +$35.2. heat_fade_short-FD was at −$80.3. The L3 lots then gave most of it back (L3 total over the day: −$56.95).
- **Testing 2, peak +$157 at 10:13.** CWT14-pdl-p05-long +$54.2, pdh-p10-short +$50.2, pdl-p10-long +$47.1, pdh-p05-lowvol-short +$20.7. The ORL longs were already negative (−$3.8 to −$14.0).
  - The account then fell to −$311 at 11:48 as the 10:05–10:30 ORL-reclaim long burst (utilities and small caps while IWM made lows) was stopped.

## MF/NS 4-session review: Primary (Oct 8, 9, 12, 13; journal real trades)
Primary by day:
- 10-08: 48 trades, −$120.66
- 10-09: 70 trades, −$238.87
- 10-12: 22 trades, +$117.93
- 10-13: 18 trades, −$95.39

That is 158 trades and −$336.99 in total. The MF/NS/RW6G1 setups account for 93 trades and −$60.86. "Exp R" is the Apr–Jun locked-holdout expectancy from `config/validation.json`, the same value the scorecard uses. The scorecard verdict uses the fixed bar in `mcf/report/scorecard.py`: "below backtest – review" needs n ≥ 10 and avg R < exp − 0.15. The Testing 1 -FD column covers 10-12 and 10-13.

| setup | n | win% | avg R | P/L | 10-08 | 10-09 | 10-12 | 10-13 | exp R (holdout) | scorecard | T1 -FD (n, avg R, P/L) | **suggestion (rule 20)** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | 8 | 38 | +0.125 | −20.49 | −6.21 | −7.00 | +11.26 | −18.54 | −0.050 | too few | 10, +0.463, +14.95 | keep |
| MF2-open-rsimidhi-flowsell | 3 | 0 | −1.077 | −31.56 | −7.99 | – | −7.14 | −16.43 | +0.046 | too few | 7, −0.289, −7.81 | keep, watch (3 of 3 stopped) |
| MF3-open-flowsell-rsi5hi | 16 | 69 | +0.220 | +45.89 | +2.46 | +3.45 | +30.46 | +9.52 | −0.034 | positive so far | 9, +0.262, +23.31 | keep |
| MF4-h40-open-flowsell | 13 | 54 | −0.064 | −36.96 | −17.04 | −39.53 | +13.34 | +6.27 | −0.017 | negative so far | 5, +0.238, +20.24 | keep (within the 0.15R bar) |
| MF5-flowsell-vwapup-rsi5hi | 23 | 48 | +0.016 | +12.66 | −24.11 | −7.97 | +20.46 | +24.28 | −0.010 | positive so far | 13, +0.140, +7.25 | keep |
| NS1-rsidip-rsi5pop-long | 4 | 100 | +0.393 | +29.62 | – | +25.72 | – | +3.90 | +0.056 | too few | 8, +0.175, +23.27 | keep |
| NS2-sma50break-overbought-short | 10 | 60 | +0.021 | −51.97 | +33.31 | – | +6.52 | −91.80 | +0.021 | positive so far | 24, −0.332, −132.85 | keep (avg R = expectation; the $ loss is today's 7-trade cluster) |
| NS3-failed-vwap-reclaim-short | 9 | 33 | **−0.326** | −88.84 | – | −76.25 | – | −12.59 | **−0.136** (t −2.06) | too few | 10, −0.191, −15.07 | **demotion candidate**: 1 trade short of the n ≥ 10 gate; at this average it would read "below backtest" (−0.326 < −0.286), and its holdout expectation is itself negative. Owner decision. |
| NS4-pm-vwap-reclaim-oversold-short | 2 | 50 | +0.058 | +8.33 | +8.33 | – | – | – | −0.080 (t −1.65) | too few | 0 | keep (too few; negative holdout expectation) |
| NS5-sma50-flush-oversold-long | 5 | 60 | +0.507 | +72.46 | – | +29.43 | +43.03 | – | +0.002 | too few | 4, +0.163, +18.71 | keep |
| RW6G1-ns2-up3-vwap2sd-short | 0 | – | – | 0.00 | – | – | – | – | 2-year +0.264 (n 424) | — | 5, −0.116, −17.49 | keep; **check wiring**: 0 signals in 4 primary sessions |

- RW6G1 signal check: if its 424 two-year trades span about 500 sessions, that is roughly 0.85 per day, or about 3.4 expected over 4 sessions, so seeing 0 has about a 3% chance. The -FD copy fired 5 times in T1.
- **No MF/NS setup meets the fixed "below backtest" bar today.** NS3 is the only one close to it.
- Four sessions and 93 trades are far below the forward gate of at least 20 sessions and 60 trades per setup. Nothing here is evidence for or against any setup (rules 7, 13 and 14). Demoting or keeping a setup is the owner's decision, and a demoted setup moves to Testing 1 in its primary form (rule 20).

## Hypotheses added to `research/backlog.jsonl` (status "idea", source "nightly-2026-10-13")
| id | category | from |
|---|---|---|
| `nightly-1013-stack-clone-skip` | risk (parent loop-1008-multisetup-consensus-t1) | 57 T1 clone lots −$143.88; 166 T2 clone lots +$35.35 |
| `nightly-1013-no-short-stacking` | risk (parent loop-1008-multisetup-consensus-t1) | T1 stacked short lots 2–3: 93, −$307.30; stacked symbols −$623.90 vs single-lot −$5.13 |
| `nightly-1013-tight-target-progress-skip` | setup (parent cwt-b-b3) | 35 rejects at 10:10:24; 87 same-poll accepted entries −$77.10 |

`python -m mcf.research.backlog list` reads all 380 entries.

## Housekeeping for the lead (not backlog)
- **H-1 (stacking reconcile, real defect).** Fix the flatten-path pairing in `mcf/execution/reconcile.py`: exclude legs of other parents, and accept only the lot's own `-x` order or the flatten fill.
  - Then re-reconcile the 9 lots (`mispaired_lots.csv`) and re-run the T1 and T2 scorecards for 10-13.
  - Also check `_release_closed_lots`: today it released lots whose shares were still at the broker.
- **H-2 (partial target fills).** Use `filled_qty` on legs, and pair any remainder (RBLX, GLD) to its own close.
- **H-3.** 16 (T1) and 24 (T2) orders from 10-12 are still `submitted`.
- **H-4.** RW6G1 shows 0 signals in primary over 4 sessions. Check the wiring and the playing-time "silent" flag.
- **H-5.** The EOD CSV still has empty `mfe_r` and `mae_r` for real trades (`build.py` fills them from the bars).
