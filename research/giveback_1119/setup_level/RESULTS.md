# Setup-level giveback causes and one targeted fix per setup: results

*Educational only — not financial advice.* 2026-11-20. The plan (`PLAN.md`) was written before any fit or check score.
Addendum A was added after the fit selection and before any check score. Nothing was committed. No setup, exit, config
or ledger line was touched.

**Verdict: FAIL.** On the fit half, **0 of 15** setups had an eligible fix. 0 of 84 testable fit cells reached an
excess t of 2 or more; the best was +1.37, on 7 trades. With nothing adopted, the pre-registered check had nothing to
score. The secondary readout (fit-best config, scored once on check) splits **5 better / 5 worse** on lab setups
(families: 2 better, 3 worse). Its best excess t is +1.37 against a bar of **4.14**.

## What was tested
- **Setups (15):**
  - Top 10 by live trades: 8 CWT14 failbrk variants, CWT12-coil-k4-long, heat_fade_short-FD and RW7-gapdn-bounce-early-short-FD.
  - The Primary five: L3-gap-slope-fromopen-FD (protected; scored only), NM-ETF-late-dip-di-long, RW3, RW5 and ST7.
  - heat_fade_short-FD and NM-ETF have no lab list, so they were scored on live only.
- **Data:**
  - Lab: all bt_lab1104 signals with refires kept, list R with bt_all costs, in stop units. Fit runs to 2025-09-30
    and check runs from 2025-10-01 to 2026-11-04. The locked block 2024-11-01..2025-02-28 was asserted absent.
  - Live: run 1, LR8 R, identical signals across accounts de-duplicated. Fit is 10-06..10-28 and check is 10-29..11-19.
- **Candidate fixes per setup.** All are entry-side, change 2 or fewer parts (C3-WB) and use only point-in-time data:
  - A, crowd minute: skip the setup's entries in any minute where it fires K or more signals, K ∈ {3, 5, 10}.
  - B, late entry: no entries at or after X, X ∈ {13:30, 14:00, 14:30}.
  - C, refire into a fade: C1 blocks a second or later entry in the same symbol on the same day; C2 blocks a
    re-entry after a loss in that symbol.
- **Scoring:** paired on the parent's own signals and judged against random removal (BESPOKE_ENTRY_RULES / W4).
  Raw ΔR alone would reward cutting trades from setups that lose money anyway.
- **Configs:** 8 × 15 = **120**, plus 520 descriptive cells.
  - Lineage N = map 916 + time_in_trade 2,664 + day_lock 16 + targets 222 + outside_methods 814 + 640 = **5,272**.
  - Bar = max(1.5, √(2 ln N)) = **4.14**.

## Fit selection
To be adopted, a config had to keep ≥ 70% of trades and ≥ 90% of top-decile winners, with excess > 0, excess t ≥ 2 and
excess without the best day > 0. **None qualified.**
- **Excess t:** 0 of 84 cells reached +2 and 1 reached −2. That is fewer than chance would give, so no setup has a
  removable bad slice.
- **Crowd minutes (A), lab:** summed excess is negative at every K (−26R to −200R). The lab lists are uncapped, so
  60-90% of CWT14 entries fall in crowd minutes. Even so, the crowded entries are no worse than the setup's average.
- **Late entries (B), lab:** cutting them costs R in total (−372R to −1,509R), mostly because of L3:
  - L3's entries at or after 13:30 average **+0.173R** over 6,316 fit trades, against −0.030R for the setup as a whole.
  - The live/W4 lead that L3's 13:30-15:00 entries lose (live: −0.32R, n ≈ 31) runs opposite to the 2-year record.
- **Refires (C):**
  - In the lab, only L3 refires. Cutting refires costs −164R (C1) and −560R (C2), because L3's refires after a loss
    average +0.035R.
  - Live refires are almost all L3 (233, avg +0.18R). RW3 and RW5 refire in 2-3% of trades (n 7 and 4). No other
    top setup refires live.

## Secondary readout: fit-best config scored once on check (counts zero)
| setup | cfg | lab check ΔR | excess (t) | rand pct | live check excess |
|---|---|---|---|---|---|
| CWT14-pdl-p05-lowvol | B1400 | +153.5 | +20.2 (0.66) | 0.15 | −1.3 |
| CWT14-orl-p05-lowvol | B1430 | +99.4 | +5.5 (0.23) | 0.38 | −2.2 |
| CWT14-orl-p10-lowvol | B1400 | +62.5 | −3.9 (−0.16) | 0.32 | +4.8 |
| CWT14-pdl-p05 | B1430 | +143.6 | +2.2 (0.07) | 0.05 | −0.3 |
| CWT14-pdl-p10 | B1430 | +97.8 | +33.0 (1.37) | 0.44 | −2.0 |
| CWT14-orl-p05 | B1430 | +210.4 | −11.5 (−0.23) | 0.10 | −2.0 |
| RW7-gapdn-bounce-early | B1400 | +154.6 | +84.9 (0.80) | 1.00 | +6.6 |
| RW3-gapdn-rsi5pop | A10 | −18.3 | −21.0 (−1.11) | 0.02 | 0 fired |
| RW5-heat30 | A10 | −21.2 | −24.4 (−1.23) | 0.02 | 0 fired |
| ST7-rsi50dn-pm | B1430 | −7.6 | −3.8 (−0.76) | 0.31 | −0.0 |
| heat_fade_short-FD (live only) | B1430 | | | | −15.3 (−1.11) |

The raw CWT14 gains (+62R to +210R, raw t 2.7-4.8) come almost entirely from removing trades from setups that lose
money. Removing the same number of random trades does about as well: excess is near 0 and the random-removal
percentile is 0.05-0.44.
- **Lab, by setup:** 5 better, 5 worse.
- **By family:** CWT14 is net +45.6R (4 better, 2 worse) and RW7 is better. RW3, RW5 and ST7 are worse.
- **Live check:** 3 better, 7 worse, and 2 never fired.
- **Avg R without the best day:** it moves with avg R in every row. No best day carries more than 41% of a lab gain.

## Setup-specific giveback causes (live descriptive, all 33 sessions; `data/live_causes.csv`)
- **CWT14 (8 setups) and CWT12-k4:**
  - These setups give little back: only 6-12% of trades reach +0.8R, and 3-14% of those end at a stop.
  - They lose because they have no edge at their 0.5R target, not because winners are given back.
  - Crowd-minute entries (≥ 3 in a minute; 39-58% of trades) average −0.16 to −0.24R. The parents average −0.12
    to −0.18R, so crowd entries are mildly worse live, but the lab does not confirm it.
- **RW3 and RW5:** live crowd-minute entries are their best trades (+0.79R and +0.45R, n 38 and 34). This is the
  opposite of their fit-half lab sign, and the fit-best A10 lost on check.
- **ST7:** 27% of its trades that reach +0.8R end at a stop. It is the only top setup with a giveback rate like
  the far-target pocket (n 58, too few to split).
- **Late entries (≥ 14:00):** under 13% of trades for every setup except NM-ETF, whose entries are all late. None
  of these shows a large loss.

## Rule changes inside the live windows (research/ledger.jsonl)
- **Fit window:** Testing2 scale-out to breakeven (10-16/17), per-setup latch (10-23), Primary sizing changed twice (10-28).
- **Check window:** Primary −2R latch (10-29) and Testing cost filter (10-30). LR1 flatten time, LR3/LR8 costs and
  Gen/Graveyard sizing (11-12). TSZ1 sizing and SPYEXIT copies (11-17). C3 Epoch 1 (11-19).
- Entry filters are scored per trade in R, so sizing changes do not move these results. The latches truncate the
  live samples.

## Caveats
- The lab is uncapped, with no ETB, latch or stacking. Crowd counts in the lab are therefore far higher than live.
- Refires exist in the lab lists only for L3, so C could not be tested in the lab on the other setups.
- 2-year evidence counts zero for a Primary rule under W4-FRAME (SRCV1). A future pass would still need TAGS1-style
  shadow tagging on live.
- If a fixed setup were ever adopted, it would be a new setup (a tweaked copy) entering through Testing.

## Where this points
Setup-level entry trims do not answer the giveback question for these 15 setups. Their losses are spread evenly
across minutes, clock times and refires. The giveback that hurts remains in the map's three pockets: far targets,
GEN holds without a target, and one-sided books in market reversals. Those pockets need exit-side or book-level
remedies, scored by WB2.

## Files
- In this folder: `PLAN.md` and `score.py` (fit/check), `secondary.py` (Addendum A).
- In `data/`: `fit_grid.csv`, `fit_diag.csv`, `adopted.csv` (empty), `fitbest_check.csv`, `live_causes.csv` and `fit_out.txt`.
