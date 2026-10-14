# Nightly winner/loser autopsy: 2026-10-14 (primary, Testing 1, Testing 2)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They are a diagnosis, not evidence. No locked holdout was scored. One small history backtest was run (section "Backtest", **12 configurations**, pre-declared in `bt1014.py`); everything else is a descriptive split of today's trades (about 30 one-session splits, none of them gated).*

Inputs: `journal.db`, `status.json` (every commit of the day, via `git log`), `reports/scorecard.json`, `setups/2026-10-14.json` and `intraday/2026-10-14.jsonl` from `origin/mcf-data`, `mcf-data-testing` and `mcf-data-testing2`; `longhold/status.json` from `mcf-data-longhold` (S6, one line only). GitHub Actions logs of the cancelled run 38569911389 and the restart run 38579584269 (read-only). SIP 1-minute bars for the 342 traded symbols plus SPY, QQQ and IWM, and for the 9 T1 symbols in failure 1 (Alpaca market data only; `fetch.py`, `ghost.py`). No trading endpoint was called, so broker orders and fills were **not** read. The broker side of every check is the equity and position quantities that `status.json` records from the broker.

Scripts in this folder (copied from nightly1013 and adapted, plus new ones):
- `build.py` builds `trades.csv` (681 real trades) with lot number, refire flag (`"refire": true` in the signal info), same-setup sequence and MFE/MAE from the bars.
- `statusscan.py` reads every status commit (equity, broker positions, split-tape gate).
- `qtycheck.py` compares broker and journal quantities at each snapshot.
- `gapcurve.py` and `brokermtm.py` localise a broker-vs-journal gap in time (two independent methods).
- `exitcheck.py` checks every journal entry/exit price against the 1-minute bar range.
- `ghost.py` re-prices the T1 orders the journal never closed (`t1_unjournaled_lots.csv`).
- `summ.py` (splits), `attr.py` (intraday attribution + market), `giveback.py` (give-back after the peak), `whatif.py` (skipped-signal what-if, run 2), `cap50.py` (Testing 2 cap 50), `sc3.py` (3-account scorecard), `bt1014.py` (backtest).

**Market: a broad down day.** SPY −0.69% open to close (high +0.16% at 09:49, low −1.03% at 14:01). QQQ **−1.24%** (low −1.56% at 15:05), IWM −0.71% (high +0.38% at 09:31, low −1.08% at 15:05). Everything peaked in the first 20 minutes and slid all day, with a bounce from 15:05 into the close. Large caps fell more than small caps (QQQ − IWM from −0.05 to −0.43 pts), the opposite of 10-13's split tape.

**Restart.** The 08:12 ET scheduled run was cancelled at 10:20:41 ET (Testing 2 had just sent AKAM at 10:20:40) and the dispatched run started 10:20:41–10:20:48 ET; its first poll was 10:21. The 10:20 poll was lost in all three accounts. The restart wrote the setup snapshot again ("setups snapshot written for 2026-10-14 (30 enabled)").

## Failures first

### 1. ACCURACY CHECK: Primary matches; Testing 1 and Testing 2 do not.

| account | equity 09:29 (pre-open) | equity 15:55 (closed) | broker day P/L | journal day P/L | gap (broker − journal) | orders still `submitted` today | explained by |
|---|---|---|---|---|---|---|---|
| Primary | 95,708.17 | 95,771.70 | **+63.53** | +63.53 | **0.00** | 0 of 11 | — |
| Testing 1 | 99,328.40 | 99,393.61 | **+65.21** | +71.27 | **−6.06** | **9 of 326** | 9 filled lots never closed in the journal (re-priced ≈ −0.30), rest ≈ −5.8 not explained |
| Testing 2 | 99,211.34 | 98,050.88 | **−1,160.46** | −785.74 | **−374.72** | 0 of 353 | **not explained**; all of it appears between the 10:18:54 and 10:22:13 status snapshots = the restart |

Clean close: all three accounts closed with `positions: []`, `health.flatten_failed: []`, the "flatten complete: no MCF positions open" log line, and the EOD report and scorecard committed at 15:57 ET. No duplicate entries (0 repeated client order ids, 0 repeated setup/symbol/bar signals). Every journal entry and exit price lies inside its 1-minute bar range (one exception, DHT, is a correct blend of a partial target fill and the flatten). The lot reconcile fix (#53) held: **0 mispaired lots** (0 "flatten" exits before 15:50), and the partial target fills (T2 BHP, EQNR, XLB; T1 DHT) were booked at the right prices.

**(a) Testing 1: 9 filled lots stayed `submitted` in the journal and were never booked.** `status.json` shows the broker holding every one of them from its fill until the 15:52 snapshot (`qtycheck_t1.csv`), and the flatten closed them; the journal has no trade row:

| symbol | setup | qty | sent (ET) | broker held until |
|---|---|---|---|---|
| TXG | L3-gap-slope-fromopen-FD (a refire) | −12 | 11:36:49 | 15:52 |
| PTC | heat_fade_short-FD | −4 | 12:06:28 | 15:52 |
| DHR | heat_fade_short-FD | −4 | 12:25:53 | 15:52 |
| DRAM | RW3-gapdn-rsi5pop-flowsell-short-FD | −18 | 12:55:51 | 15:52 |
| CEG | ST2-slope20up-long-am-t05s1-FD | +3 | 13:20:46 | 15:52 |
| AMD | RW1-gapdn-bounce-flowsell-short-FD | −1 (broker −3 vs journal −2) | 13:35:41 | 15:52 |
| SNPS | heat_fade_short-FD | −1 | 14:16:30 | 15:52 |
| EWJ | RW7-gapdn-bounce-early-short-FD | −9 | 14:20:55 | 15:52 |
| GDXJ | RW3-gapdn-rsi5pop-flowsell-short-FD | −9 | 15:01:04 | 15:52 |

- None of them crossed its stop or target before 15:55, so they all rode to the flatten. Re-priced (bar open after the order → 15:55 close) they sum to about **−$0.30** (−5.88 to +8.82 each).
- AMD is the clearest case: MF2-FD and RW1-FD each sent 1 share in the same 13:35 poll. The flatten closed 2 shares together and the journal booked only the MF2 lot (+0.87, "flatten"). The other 8 symbols had a single lot, so the cause is not only sibling pairing. These orders are spread through the day (not the oldest), so it is not the 10-12 pagination problem either. Without the broker's order list this is not confirmed.
- **Side effect:** the runner still counts these 9 lots as open entries, so they used slots and the per-symbol lot cap all afternoon (AMD: RW7-FD at 13:35 and MF2-FD at 13:45 were skipped for "lot cap"). Housekeeping H-1.

**(b) Testing 2 lost $374.72 at the broker that the journal does not show.**
- Two independent checks agree: broker equity change minus journal P/L marked at the same minute (`gapcurve.py`) and broker equity change minus the broker's own positions marked to SIP (`brokermtm.py`). The gap is −2.46 at 10:18:54 and **−388.59 at 10:22:13**, then stays between −328 and −452 all day and ends at −374.72.
- In that 3.3-minute window the broker positions changed only where the journal booked exits (14 symbols, 32 targets and 9 stops, journal +$30) and the one restored AKAM entry. Held positions gained +$101.57 on the bars, yet equity fell −$302.41. Residual: **−$403.98** in that interval alone.
- So money left through orders that were in and out between two snapshots and that neither the positions nor the journal show. The cancelled job's log ends with `ENTER CWT05-flush-m05-v3-long AKAM` at 10:20:40 and "The operation was canceled"; the new job logs "restored 1 MCF orders from the broker that the journal had not saved yet" (AKAM) and "reconciled 28 trades".
- Primary and Testing 1 show no step at the restart (T1 residual +4.82 in the same interval). **Needs the broker's FILL activities for the Testing 2 account, 14:18:54–14:22:13 UTC** (read-only, lead). Housekeeping H-2. Until then today's Testing 2 broker loss is −$1,160.46, not −$785.74.
- Overnight equity moves, not explained (same as 10-13): Primary +5.43, T1 −6.77, T2 −12.05 between the 10-13 close and the 10-14 pre-open snapshot.

### 2. Testing 2 hit its daily loss limit at 10:30 and lost −$786 (journal; broker −$1,160)
- All 353 trades were entered 09:50–10:28. At 10:30:25 realized R reached the account's −60R limit ("daily loss limit", AEM) and the risk manager halted new entries for the day: **459 later signals were skipped as "halted"**. The EOD what-if prices them at **−123.0R** (402 longs −110.7R, 57 shorts −12.3R), so the halt saved money today.
- **The 09:50 first poll was the damage:** 64 entries (60 longs), 8% wins, −0.95R, **−$420.84**. Market peaked at 09:49. Mostly CWT14 PDL fail-break longs entered on the first decision bar and stopped as the index slid. By setup: pdl-p05-long −$297.18 (50 trades, 18% wins), pdl-p10-long −$172.82, pdl-p05-lowvol-long −$106.12.
- 89 losers never worked (MFE < 0.2R) and cost −$760.34; only 33 losers had reached 0.5R first. Stops −1.064R against targets +0.477R: the t05 geometry needs ≈ 69% wins and got 48%.
- Longs −$754.76 (305 trades), shorts −$30.98 (48).

### 3. Testing 1 gave back $247 after 15:05
- Marked P/L peaked at **+$318 at 15:05** (QQQ's low) and closed at +$71. The 123 lots open at 15:05 were marked +$111 and finished −$137 (`giveback.py`).
- The short lots that rode to the flatten gave back **−$186.46** (66 lots). RW7-FD −$83, heat_fade_short-FD −$52 and RW5-FD −$40 lost most in the last 50 minutes.
- This is hindsight (the 15:05 low is known only afterwards). It is an exit idea for the backlog, not a finding.

### 4. LIQ-orl lost −$251 on the down day
- 47 trades, 30% wins, −0.416R, 31 stops, 16 flattens, median MFE 0.18R; 24 never worked.
- **30 of the 47 entered in the 10:45 poll** (−$202, 20% wins), a basket of opening-range-low sweeps as SPY broke to −0.3%. Its own config note says "up sessions +0.59R, down −0.49R (long beta)"; today was a down session and it behaved as its history says. On 10-13 it made +$137.

## Headline per account (real trades, run 1)
| account | trades | win% | avg R | P/L (journal) | broker | cost-adj | stop / target / flatten | intraday (marked, 5-min) |
|---|---|---|---|---|---|---|---|---|
| Primary (11 setups) | 11 | 64% | +0.293 | **+$63.53** | +$63.53 | +$60.35 | 3 / 7 / 1 | peak +$83 at 11:20; green from 09:55 on |
| Testing 1 (39) | 317 | 51% | +0.025 | **+$71.27** | +$65.21 | +$14.47 | 106 / 124 / 87 | min −$193 at 13:05, peak +$318 at 15:05 |
| Testing 2 (30) | 353 | 48% | −0.322 | **−$785.74** | **−$1,160.46** | −$864.78 | 183 / 169 / 1 | never green; min −$800 at 12:25 |
| S6 long-hold (separate, not ranked) | — | — | — | — | **−$3,337.95 (−3.33%)**, equity 97,047.95 | — | — | — |

S6 note: the broker's `last_equity` for 10-13 is 100,385.90, while `marks.csv` recorded 103,471.81 (+$3,486.54) for 10-13; the two differ by $3,085.91 (H-5).

Entry latency (signal → fill, median / p90): Primary 37 / 57 s, T1 49 / 82 s, T2 88 / 145 s. Entry slippage mean: Primary +12.1 bps, T1 +5.1, T2 −2.2. Primary losers paid 22.3 bps against 6.2 for winners (4 losers, small sample).

## Refire (#57), same-setup re-entry (#54) and the snapshot

**Snapshot verdict: confirmed.** `setups/2026-10-14.json` on `mcf-data` has `refire: true` (cooldown 1) on `RW6G1-ns2-up3-vwap2sd-short`, the only refire setup among Primary's 11. On `mcf-data-testing` it has `refire: true` on exactly the 13 enabled Testing 1 setups of the change: exhaustion_short, MF2-FD, NS1-FD, NS3-FD, RW6G1-FD, L3-gap-slope-rsi5hi-FD, L3-gap-slope-fromopen-FD, ST1-FD, ST5-FD, ST6-FD, RW4-FD, RW5-FD, RW6-FD (cooldowns 1/3/6 as in config/account_testing.yaml). The Testing 1 and Testing 2 snapshots also carry `refire: true` on the disabled primary `RW6G1-ns2-up3-vwap2sd-short` (inherited from config/default.yaml); it is disabled there, so it has no effect. The snapshot is the restart's (written 10:21 and committed with "job 10:21 done"); the cancelled run's snapshot never reached the branch, so the branch has no record of what ran 09:30–10:20 (before the change, by design).

- **Primary:** RW6G1 produced its **first signal in 5 sessions** (10:44, `"refire": false`, i.e. a first signal) and it was skipped for spread (54.9 bps > 30). No refire. This partly answers 10-13's H-4: the setup is wired.
- **Testing 1 refire signals:** 32 after 10:25 (the first refire-capable poll). 9 submitted, 23 skipped (14 not shortable, 6 lot cap, 2 opposite side, 2 spread). By setup: L3-fromopen-FD 11, NS3-FD 8, RW4-FD 8, MF2-FD 2, RW6-FD 2, RW6G1-FD 1, exhaustion_short 1.
- **Refire trades:** 8 journaled, 62% wins, **+1.032R, +$27.97**, plus TXG (L3-fromopen, never booked, failure 1, ≈ −$2). Non-refire trades: 309, −0.001R, +$43.30. Without UVXY exhaustion_short (+6.52R, +$14.27) the other 7 made +$13.70.
  - AVEX (L3-fromopen-FD) refired 4 times in 40 minutes, stacked to 3 lots: +12.80, −14.30, +11.52, −13.65 = −$3.63.
- **Same-setup re-entry (2nd+ lot of the same setup on the same symbol):** 5 trades, −$4.12 (avg R +0.996 is lifted by UVXY). Primary 0, Testing 2 0: T2's CWT setups fire once a day, so re-entry cannot happen there without refire.
- One partial session (from 10:25). Nothing here is evidence (rules 7, 13).

## Split-tape short gate (Testing 1)
- **It blocked 0 shorts.** The gate never turned on: QQQ − IWM from the open stayed between +0.11 (09:50) and −0.43 pts all day, never near the +0.50 threshold (`health.split_tape_gate.blocking` false at every snapshot).
- What-if: nothing to price. Shorts made +$589.67 (232 trades, 59% wins, +0.205R) and longs lost −$518.40 (85, 31%, −0.465R) on a down tape, as expected. 10-13 (blocking would have applied) is the case it was built for; today is a session where it correctly stayed off.

## Testing 2 cap 50 (#55)
- Only CWT14-orl-p05-long reached 50 open lots (19 signals skipped "max positions for this setup", what-if −5.14R, saved). Max open per setup: orl-p05-long 49, orl-p05-lowvol-long 46, pdl-p05-long 29, orl-p10-long 26.
- **81 trades were taken while their setup already held ≥ 25 lots** (would have been skipped at the old cap 25): 47% wins, −0.334R, **−$158.28** (orl-p05-long 38 −$55.88, orl-p05-lowvol-long 32 −$57.63, pdl-p05-long 9 −$41.11). Caveat: at cap 25 the −60R halt would have come later and other trades would have been taken; not simulated.

## Primary (per setup)
| setup | n | win% | avg R | P/L | exits | MFE | MAE |
|---|---|---|---|---|---|---|---|
| MF4-h40-open-flowsell | 3 | 100 | +0.564 | +51.40 | 3 targets | 0.76 | 0.64 |
| MF1-945-flowsell-vwapup | 1 | 100 | +1.911 | +48.60 | target (FRVO) | 1.97 | 0.19 |
| NS2-sma50break-overbought-short | 2 | 100 | +0.943 | +48.36 | 2 targets | 1.00 | 0.15 |
| NS4-pm-vwap-reclaim-oversold-short | 1 | 100 | +1.396 | +29.60 | target (14:50) | 1.55 | 0.35 |
| MF5-flowsell-vwapup-rsi5hi | 1 | 0 | −0.392 | −4.56 | flatten | 0.22 | 0.60 |
| MF2-open-rsimidhi-flowsell | 1 | 0 | −1.202 | −17.07 | stop | 0.03 | 1.08 |
| MF3-open-flowsell-rsi5hi | 1 | 0 | −1.043 | −25.55 | stop | 0.01 | 1.04 |
| NS1-rsidip-rsi5pop-long | 1 | 0 | −1.022 | **−67.25** | stop | −0.04 | 1.04 |

- 10 of 11 were shorts (+$130.78); the one long, NS1, lost −$67.25 at −1.02R. Every loser was a never-worked trade (MFE ≤ 0.03R, −$109.87 for the 3 stops). Winners kept almost all of their peak (median MFE − R = 0.11R).
- 10 signals skipped: spread > 30 bps 4 (incl. RW6G1), not shortable 4, spread vs stop 2.

## Testing 1: drivers of the +$71
| setup (worst first) | n | win% | avg R | P/L | | setup (best first) | n | win% | avg R | P/L |
|---|---|---|---|---|---|---|---|---|---|---|
| LIQ-orl-sweep-open15-s25-long | 47 | 30 | −0.416 | −250.67 | | RW7-gapdn-bounce-early-short-FD | 62 | 60 | +0.176 | +177.82 |
| ST2-slope20up-long-am-t05s1-FD | 17 | 41 | −0.333 | −100.87 | | RW3-gapdn-rsi5pop-flowsell-short-FD | 15 | 73 | +0.356 | +81.91 |
| NS5-sma50-flush-oversold-long-FD | 2 | 50 | −0.412 | −60.18 | | NS2-sma50break-overbought-short-FD | 8 | 88 | +0.555 | +72.17 |
| ST4-emadn-long-am-t1s05-FD | 4 | 0 | −1.046 | −45.24 | | MF4-h40-open-flowsell-FD | 9 | 100 | +0.538 | +70.06 |
| NS1-rsidip-rsi5pop-long-FD | 1 | 0 | −1.028 | −32.18 | | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 13 | 77 | +0.585 | +64.81 |
| exhaustion_short-FD | 6 | 50 | −0.234 | −26.44 | | MF3-open-flowsell-rsi5hi-FD | 10 | 60 | +0.313 | +51.95 |
| heat_fade_long | 5 | 20 | −0.790 | −17.33 | | MF2-open-rsimidhi-flowsell-FD | 7 | 71 | +0.609 | +42.75 |
| RW2-exhaustion-noon-adv150-short-FD | 9 | 44 | −0.321 | −16.22 | | RW6-ns2-up3-short-FD | 2 | 100 | +0.953 | +35.57 |

The full table is reproduced by `summ.py`. Ex-primary setups: 18 trades, −$36.72.
- **Long side lost, short side won**, the mirror of 10-13. Every long setup except intraday_momentum (+0.56) was red.
- **Stacking added winners today:** lot 1 −$91.73 (236), lot 2 +$127.82 (57), lot 3 +$35.17 (24). On 10-13 the extra lots were the losers. Stacking follows the day's direction (agreement among shorts paid on a down day); two sessions, opposite signs, so nothing is learned about stacking itself.
- Restart gap: no entries 10:10–10:29. Before the restart: 18 trades +$72.58; after: 299 trades −$1.31.
- Loss types: 154 losers, median MFE 0.18R, MAE 1.02R; 83 never worked (−$830.70). 163 winners, MFE 0.94R, MAE 0.25R.
- Skipped-signal what-if (T1): opposite side held 33 −5.3R, lot cap 11 −2.1R, not shortable 54 −3.5R (all saved); spread rules 45 +12.0R (cost).

## Testing 2 (per setup)
| setup | n | win% | avg R | P/L | stops/tgt/flat |
|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p10-lowvol-long | 13 | 69 | −0.007 | +6.43 | 4/9/0 |
| CWT12-coil-k4-long | 2 | 50 | −0.266 | +1.47 | 1/1/0 |
| CWT14-failbrk-orl-p10-lowvol-long | 19 | 63 | −0.087 | −2.34 | 7/12/0 |
| CWT14-failbrk-orl-p10-long | 32 | 69 | +0.014 | −6.90 | 10/22/0 |
| CWT14-failbrk-pdh-p10-lowvol-short | 8 | 38 | −0.456 | −7.97 | 5/3/0 |
| CWT14-failbrk-pdh-p05-lowvol-short | 19 | 58 | −0.099 | −8.34 | 8/11/0 |
| CWT05 (2 variants) | 4 | 25 | — | −39.37 | 3/1/0 |
| CWT14-failbrk-pdh-p10-short | 21 | 48 | −0.241 | −14.67 | 10/11/0 |
| CWT14-failbrk-orl-p05-long | 67 | 58 | −0.126 | −67.31 | 27/40/0 |
| CWT14-failbrk-orl-p05-lowvol-long | 58 | 55 | −0.220 | −70.62 | 26/32/0 |
| CWT14-failbrk-pdl-p05-lowvol-long | 21 | 38 | −0.542 | −106.12 | 13/8/0 |
| CWT14-failbrk-pdl-p10-long | 39 | 28 | −0.655 | −172.82 | 28/11/0 |
| CWT14-failbrk-pdl-p05-long | 50 | 18 | −0.810 | **−297.18** | 41/8/1 |

- Polls: 09:50 −$420.84 (64), 09:55 −$55.69 (21), 10:05 −$108.73 (52), **10:10 +$116.21 (126, 76% wins)**, 10:15 −$79.83 (34), 10:25 −$216.94 (40, after the restart).
- Lots per symbol-poll: 1 lot 74 times, 2 lots 87, 3 lots 35 (the CWT14 sibling variants fire together). Lot 3 was flat (−$1.44); lots 1–2 carried the loss.
- 7 broker rejects (take-profit already through the base price: the tight-target issue of `nightly-1013-tight-target-progress-skip`), what-if +2.4R.
- "not shortable/ETB" skipped 63 signals that would have made +31.6R (what-if); see `nightly-1012-cwt09-etb-universe`.

## Intraday attribution (marked: realized plus open lots at the 1-minute close)
- **Primary, peak +$83 at 11:20:** MF4 +51.4, MF1 +48.6, NS2 +48.4; MF3 −25.6, NS1 −22.9, MF2 −17.1. Green at every 5-minute mark from 09:55; NS4's 14:50 target added the last +$29.6.
- **Testing 1, min −$193 at 13:05** (LIQ-orl −298.5, exhaustion_short-FD −35.9, NS1-FD −32.2; MF4-FD +54.3, NS2-FD +36.8 held it up). **Peak +$318 at 15:05:** RW7-FD +261.0, RW5-FD +105.1, RW3-FD +87.3, MF3-FD +76.5, NS2-FD +72.9 against LIQ-orl −285.8 and ST2-FD −107.1. Then the 15:05→15:55 give-back (failure 3).
- **Testing 2, never green:** low −$800 at 12:25: pdl-p05-long −295.7, pdl-p10-long −172.8, pdl-p05-lowvol-long −97.6, orl-p05-lowvol-long −83.1.

## Scorecard summary, all three accounts (every 3 market days; last summary 10-12 or earlier)
Journal real trades; the verdict uses the fixed bar in `mcf/report/scorecard.py`. Paper results, not evidence.

| account | sessions in scorecard | trades | P/L | by day | verdicts |
|---|---|---|---|---|---|
| Primary | 4 (10-09..10-14) | 121 | −$152.80 | 10-09 −238.87, 10-12 +117.93, 10-13 −95.39, 10-14 +63.53 | 4 positive so far (MF5 +32.21, MF4 +31.48, MF3 +17.88, NS2 −36.92 at +0.055R), 9 too few, 1 below backtest (heat_fade_short, already demoted to Testing 1) |
| Testing 1 | 4 (10-09..10-14) | 923 | −$541.97 | 10-09 −25.03, 10-12 +40.79, 10-13 −629.03, 10-14 +71.27 | 10 positive (best RW3-FD +118.17, MF4-FD +90.30, RW5-FD +87.30, MF3-FD +75.26), 14 negative (worst ST2-FD −133.64, heat_fade_long-FD −118.43, LIQ-orl −113.22, heat_fade_short-FD −84.53), 28 too few |
| Testing 2 | 3 (10-12..10-14) | 1,336 | −$1,541.06 (broker worse, failure 1b) | 10-12 −652.05, 10-13 −103.27, 10-14 −785.74 | 2 positive (pdl-p10-lowvol-long +38.56, pdh-p10-short +31.75), 10 negative, **3 below backtest – review: CWT14-pdl-p05-long (132, −0.250R vs −0.088), CWT13-z05-short (17, −0.245 vs −0.069), CWT12-coil-k6-long (24, −0.290 vs −0.070)**, 11 too few |

- Testing 2's three "below backtest" flags are owner decisions (rule 20 concerns removal from Testing and needs the owner prompt; nothing is removed here). Note that every CWT expectation in the scorecard is itself negative (−0.07 to −0.10R).
- No Primary setup is at the "below backtest" bar. NS3 (10-13's near-miss) did not trade today.

## Backtest (two-year open history; 12 configurations; 0 pass)
Pre-declared in the docstring of `bt1014.py` before scoring. Frames via `research/history2y` (open months only; the locked block 2024-11-01..2025-02-28 is refused by the loader, `MCF_HIST_ALLOW_LOCKED` never set; the regime table has 0 locked sessions), with the head/tail rows and outcomes of `research/bdi/refire1014/scan.py` (production R, time-of-day entry costs, structural exits simulated). One signal per setup per symbol-day, first qualifying bar. Bar for each configuration: exp > 0, better than baseline in both halves (≤ 2025-12 / 2026) and in up and down sessions, day-clustered t ≥ max(1.5, √(2 ln 12)) = **2.23**. Results: `bt1014_results.csv`.

| hypothesis | configuration | n | exp R | t | Δ vs baseline (train / 2026 / up / down) | verdict |
|---|---|---|---|---|---|---|
| H1 CWT14 skip 09:50 | pdl-p10-long | 32,706 | −0.093 | −8.86 | −0.010 / −0.008 / −0.014 / −0.008 | fail |
| | pdl-p05-long | 61,733 | −0.092 | −10.05 | −0.008 / −0.004 / −0.009 / −0.007 | fail |
| | pdl-p05-lowvol-long | 42,983 | −0.095 | −9.79 | −0.001 / +0.001 / −0.002 / +0.001 | fail |
| | pdl-p10-lowvol-long | 19,641 | −0.094 | −8.74 | −0.001 / −0.001 / −0.003 / 0.000 | fail |
| | pdh-p10-short | 24,971 | −0.091 | −9.04 | +0.002 / +0.003 / −0.002 / +0.002 | fail |
| | pdh-p05-lowvol-short | 42,756 | −0.092 | −11.02 | +0.002 / +0.003 / +0.001 / +0.003 | fail |
| | pdh-p10-lowvol-short | 19,011 | −0.087 | −9.15 | 0.000 / +0.001 / −0.001 / +0.002 | fail |
| | orl-p05-long, orl-p05-lowvol, orl-p10-long, orl-p10-lowvol | identical to baseline | | | 0 (the 30-minute OR setups cannot fire at 09:50) | fail |
| | *pooled CWT14 (10), reported only* | 494,503 | −0.091 | −13.18 | baseline −0.090 | — |
| H2 LIQ-orl index confirm | (a) SPY up from open | 6,169 | **+0.043** | 1.11 | +0.086 / +0.007 / −0.037 / **−0.145** | fail (t, down sessions) |
| | (b) SPY above VWAP | 7,674 | −0.016 | −0.42 | +0.015 / −0.041 / −0.059 / −0.111 | fail |

- **H1 is refuted on history.** The 09:50 entries are 5.5% of CWT14 trades and were *better* than the later ones (−0.071 vs −0.091R). Today's 09:50 loss was the day (the index topped at 09:49), not the bar. Note every CWT14 baseline is negative after costs (−0.084..−0.094R, t −7 to −11); the scorecard's expectation for these setups is negative too.
- **H2 fails.** Requiring SPY up from the open lifts LIQ-orl from −0.002R to +0.043R but with t 1.11, and its down-session trades get worse (−0.432R): the gate does not remove the long-beta problem, it only thins the sample.
- Both entries are recorded as `failed` with their configuration counts (rule 3). Rework (rule 18) is possible but not queued tonight.

## Hypotheses added to `research/backlog.jsonl` (status "idea", source "nightly-2026-10-14")
| id | category | status | from |
|---|---|---|---|
| `nightly-1014-cwt14-skip-first-bar` | setup (parent cwt-b-b3-failed-breakout-reversal) | **failed** (10 configs) | T2 09:50 poll 64 trades, 8% wins, −$420.84 |
| `nightly-1014-liq-orl-index-confirm` | filter (parent bdi-reddit1012-liquidity-sweep) | **failed** (2 configs) | LIQ-orl −$250.67; 30 entries in the 10:45 poll −$202 |
| `nightly-1014-fd-short-late-giveback` | exit | idea | T1 66 short lots flattened at 15:55: +$76.89 at 15:05 → −$109.57 |
| `nightly-1014-t2-cap50-review` | risk (parent ledger 2026-10-14-testing2-setup-cap-50) | idea | 81 T2 trades above 25 open lots per setup, −0.334R, −$158.28 |

`add_backlog.py` writes them; `python -m mcf.research.backlog report` regenerated `research/BACKLOG.md` (387 entries). Nothing went into config/ or mcf/.

## Housekeeping for the lead (not backlog)
- **H-1 (T1 lots never booked, real defect).** 9 filled T1 entries are still `submitted` (table in failure 1a). Find why reconcile did not pair their flatten closes (AMD: one flatten order closed two lots and only one was booked). Then re-reconcile them (≈ −$0.30) and re-run the T1 scorecard. Also release them from the runner's lot state on the next start.
- **H-2 (T2 −$374.72 at the restart, unexplained).** Pull the Testing 2 account's FILL activities for 14:18:54–14:22:13 UTC (read-only) and match them to `mt2-` orders. Until then, Testing 2's broker day is −$1,160.46.
- **H-3.** Old ghost orders from 10-12 remain: T1 15 (was 16), T2 24 still `submitted`.
- **H-4.** A cancelled job loses its last minutes of journal and its setup snapshot; the restart rewrites the snapshot. Consider committing the snapshot at the first poll so a cancel cannot lose it.
- **H-5 (S6).** `longhold/marks.csv` 10-13 equity 103,471.81 vs broker `last_equity` 100,385.90 on 10-14 (diff $3,085.91). Check which one the S6 10-13 day P/L (+$3,486.54) should use.
- **H-6.** The EOD CSV still has empty `mfe_r`/`mae_r` for real trades (`build.py` fills them from the bars).
