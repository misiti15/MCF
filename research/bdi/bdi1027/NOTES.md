# BDI 2026-10-27: per-account session review, every trade of the 5 accounts, and two-year tests of a new long setup and three reworks

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7) from one full session (trading
from 09:30; run #149 → standby #155 handover at 14:28 ET, 1.8-4.5 min poll gap, no decision minute missed). One session
is a diagnosis, not evidence. History numbers are **backtests** on the open two-year history (train ≤ 2025-12-31, valid
2026-01-01..10-07) with production + time-of-day costs in. The locked block (2024-11-01..2025-02-28) was never read
and no holdout was scored. No config, setup, exit or assignment was changed. No DECISION was added tonight.*

Already done tonight and **cited, not redone**: `nightly1027/` (close and coverage, P/L, give-back curves, autopsy,
QQQ-low age, 15:45 flatten replay, ST-P, DECISION K4). **Configurations tonight: 25** (A 12 + A rework 4 + B 4 + C 4 +
1 descriptive flatten look), **0 pass**, 0 near-misses (`counts.json`).

## Failures first
1. **New long setup "Leaders on the Index Reclaim" (BDI1027-LIR-long) fails: 0 of 16** (`PLAN.md` written before
   scoring; `scan_1027.py`, `eval_1027.py`, `eval_out.txt`, `results.csv`, `rework_1027.py`, `rework_out.txt`).
   Rule: the first 5-min bar in 10:00-13:00 at which QQQ is back at or above its open after a dip of ≥ d; buy every
   liquid stock (ADV ≥ $95M) above its VWAP and ≥ k points ahead of QQQ from the open; R = 0.25 ATR, 1R stop.
   - 12 configs (d 0.20 / 0.40% × k 0.5 / 1.0 × hold-to-close / t1s1 / t2s1): all negative overall
     (−0.002..−0.059R). Best row d 0.40 / k 1.0 / t1s1: n 9,869 in 54 sessions, train +0.124R, **valid −0.088R**,
     up sessions +0.14R / down −0.18R, t −0.04.
   - **What it learned:** every row beats the same-minute random long by +0.01..+0.05R, so picking the leaders beats
     buying any stock at the same bounce. But every row loses in down sessions (−0.18..−0.44R): the index-reclaim
     trigger is a market-direction bet, as the coil was on 10-26.
   - Rework (4 configs: the two best rows on valid with breadth at the trigger ≥ 0.5 / 0.6): best valid −0.041R, t 1.07,
     up +0.14R / down −0.45R. Lineage counted with the relative-strength family (N 753, bar 3.64).
     Backlog `bdi1027-index-reclaim-leaders-long` → **failed** (16 configs).
2. **Tonight's nightly idea `nightly-1027-pdl-long-index-low-age` fails: 0 of 4.** Failed prior-day-low longs
   (pdl-p10, pdl-p05-lowvol, live geometry) skipped while the QQQ low is < 15 / < 30 min old: −0.086..−0.097R vs
   parents −0.084 / −0.094R. Train and valid are both negative, and no row beats its parent in valid. The live split
   (−0.214R vs +0.00R since 10-06) does not exist on two years. Backlog entry → **failed**.
3. **Cluster cap for the same pdl longs fails: 0 of 4** (`cluster_1027.py`, `cluster_out.txt`). Skipping bars where
   the setup fires on ≥ 5 / ≥ 10 symbols leaves −0.091..−0.104R. **Burst entries are slightly better than singles on
   two years** (≥ 10: −0.065 / −0.079R vs kept −0.100 / −0.101R): the same answer as the coil (bdi1026) and the short
   bursts (nightly-1015). New backlog `bdi1027-pdl-long-burst-skip` → **failed**.
4. **The 15:45 flatten (`nightly-1027-flatten-1545`) gets no two-year support** (`last10.py`, `last10_out.txt`;
   descriptive, 1 config). A long held from the 15:45 to the 15:55 close gains +0.004R per liquid symbol-day
   (n 382,764, 426 sessions, t 0.70; train +0.006 / valid +0.002R). Names up > 1R since 15:00 lose −0.024R, a small
   fade of open winners. The idea stays an idea at lower priority, because the full test needs the live setups' own lots.
5. **The opposite side has no rule known at entry.** Shorts on stocks already ≥ +1% from the open: n 82, live −0.544R,
   opposite +0.556R. Shorts without that flag were also bad (n 206, live −0.396R): it was the rally from the 10:17 low,
   which nothing showed at entry. The same flags sorted the other way on 10-22/10-23. Nothing to propose.

## 0. Per-account session review (`accounts.py` → `accounts_out.txt`; `skipped.py` → `skipped_out.txt`)
R = after costs (journal `pnl_adj` / $ risk). Break-even win% = avg loss R / (avg win R + avg loss R). Blocked signals
were replayed as their own bracket on SIP 1-min bars at the setup's median cost (no extra spread).

### Primary (mcf-data): +$87.73, the only green intraday book besides Gen
- **Day:** 58 trades, **65.5% win vs 58.2% break-even**, +0.110R (+6.4R). Shorts 23 trades +0.310R (+$90.73), longs 35 −0.022R (−$3.00).
- **Peak vs close:** trough −$76 (10:24: CWT14 pdl-p10-lowvol bought 12 names in the 10:10 poll before the 10:17 index
  low) → peak +$97 (15:36) → +$88. Give-back $9: none to speak of.
- **Best:** Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` 5 trades +1.10R +$47.05.
  Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` +$35.82.
  Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` +$24.63.
- **Worst:** Afternoon VWAP Reclaim Fade `NS4-pm-vwap-reclaim-oversold-short` 1 trade −$17.68. Failed Prior-Day-Low
  Break Long (0.1 ATR, low volume) `CWT14-failbrk-pdl-p10-lowvol-long` 34 trades −0.036R −$14.26 (2 never worked, a
  12-lot cluster).
- **Blocked:** "spread bps > max" 12 signals would have made +6.4R (+0.53R each) and 4 not-shortable +6.0R; "spread %
  of stop" 16 −3.5R; twin-held 2 −2.0R.
- **Edits:**
  1. *Tested:* the CWT14 pdl-lowvol long leaves for Testing 2 tomorrow (owner rotation). Tonight's two filters on its
     family both fail on history (QQQ-low age 0/4, cluster cap 0/4), so removal was the right lever; nothing to add.
  2. *Queued:* `bdi1027-spread-bps-skip-replay`. Across all accounts the bps cap skipped ~+9R (156 signals) today,
     while the stop-distance guard saved ~33R (172). Needs a replay of every skip since 10-06 with the quoted spread
     charged before either guard is touched.
  3. *Not adopted:* hold-to-close would have been +17.6R vs +6.4R live, but it is −109R over the 5 earlier days
     (bdi1026). Today was an up day; don't over-correct.

### Testing 1 (mcf-data-testing): −$406.88, never above zero
- **Day:** 189 trades, **43.4% win vs 66.2% break-even**, −0.321R (−60.6R). Shorts 81 trades −0.538R (−$374.59), longs
  108 −0.158R (−$32.29). Every entry hour was negative.
- **Peak vs close:** never above $0; trough −$421 at 15:50. MF3-FD tripped −2R at 10:33 and took 14 more shorts
  (−8.5R after the trip). CWT14 pdl-p05 tripped at 10:48 and took 26 more (−8.8R).
- **Best:** `RW4-ns3-adv150-short-FD` (no display name in setup_names.json) 2 trades +$16.14. Big Gainer Dip-and-Pop (all day)
  `NS1-rsidip-rsi5pop-long-FD` 4 trades +$6.44.
- **Worst:** Afternoon Blow-off Short `exhaustion_short` 0/6 −$92.07, and its all-day version 1/9 −$76.22.
  Early Sellers into a Pop (all day) `MF3-open-flowsell-rsi5hi-FD` 18 trades −0.72R −$57.21. Failed Prior-Day-Low
  Break Long (stop 0.05) `CWT14-failbrk-pdl-p05-long` 99 trades −16.0R −$48.06, with a 22-lot cluster.
- **Losses:** wrong side after a big swing −$249 (14), small MFE −$174, never worked −$166 (30).
- **Blocked:** twin-held 12 signals −12.0R if taken (the twin rule saved 12R). Lot cap 6 −5.9R. "Spread bps" 27 +6.4R.
- **Edits:**
  1. *Tested:* a cluster cap or a QQQ-low-age filter on CWT14 pdl-p05-long. Both fail on two years (above); the setup's
     own record is 541 trades −0.089R and −0.088R on two years. Its fate goes to the Friday rotation, not a filter.
  2. *Watch (nightly):* MF3-FD. 124 trades, 47.6% win vs 57.8% needed, −0.195R, −0.239R without its best day, last 4
     sessions −0.467R. It is a Graveyard-move candidate for Friday's review, not a single-day call.
  3. *No change:* the after-trip losses (−17.3R from the two setups above) are the per-setup stop that is off in the
     Testing accounts (ST-A, owner "revisit later" as ST-P). Not re-raised.

### Testing 2 (mcf-data-testing2): −$261.04
- **Day:** 238 trades (125/day before GX1), **58.0% win vs 69.4% break-even**, −0.162R (−38.5R). Shorts 40 trades
  −0.591R (−$253.91), longs 198 −0.075R (−$7.13).
- **Peak vs close:** +$17 (11:45) → −$298 (15:36) → −$261. The give-back came from entries in the 11:00 hour
  (−$116, mostly shorts) and the 14:00 hour (−$52), not from open winners fading.
- **Best:** Coil Under the High (4 bars) `CWT12-coil-k4-long` 73 trades, 75% win, +0.086R, +$106.98. `RW1-gapdn-bounce-flowsell-short-FD`
  (no display name) 3/3 +$10.36. SPY Dip of 0.2 ATR, Breadth Turn (SPXL) `LD6-spy-dip020atr-breadthturn-spxl-holdtr-long` +$10.08.
- **Worst:** Afternoon Blow-off Short (all day) `exhaustion_short-FD` 13 trades −$119.70. `L3-gap-slope-rsi5hi-FD` (no display name) 0/4 −$74.07 (MRNA shorted three times). Sellers into Strength (all day)
  `MF5-flowsell-vwapup-rsi5hi-FD` 1 of 14 won −$59.37. CWT14 pdl-p05-lowvol −$51.22, pdl-p10 −$44.02.
- **Blocked:** spread-% 40 −9.8R, not shortable 30 −7.3R, twin-held 7 −5.9R. The guards were right.
- **Edits:**
  1. *No change:* coil-k4 with a +1R target would have made +21.9R today vs +6.3R. But its geometry variants already
     failed on two years (top5_1021), and K4 (move to the Graveyard) is open on its 12-session record. Today's +$107
     does not change that record (−0.078R).
  2. *Watch:* MF5-FD (nightly). 65 trades −0.293R, but today is 70% of the loss.
  3. *Note for the Friday review:* from 10-28 Testing 2 runs three versions of the same failed-PDL long signal
     (pdl-p05-lowvol, pdl-p10 and, arriving, pdl-p10-lowvol). Each setup's twin-held count must be shown with its
     record (rule 20), because they will take each other's symbols.

### Graveyard (mcf-data-graveyard): −$949.76, the worst book
- **Day:** 392 trades, **58.2% win vs 67.0% break-even**, −0.120R (−46.9R). Shorts 132 trades −0.531R (−$1,224.43),
  longs 260 +0.089R (+$274.67).
- **Peak vs close:** +$100 (10:02) → −$1,149 (15:46) → −$950. The drop was entries, not give-back: CWT14 pdh shorts took
  25 entries in the 09:55 poll into the 10:17 low-and-rally, the 09:xx entries made −$472, and
  `RW2-exhaustion-noon-adv150-short-FD` (no display name) lost −$375.
- **Best:** Failed Opening-Range-Low Break Long `CWT14-failbrk-orl-p05-long` 77 trades +$97.88. Coil Under the High
  (6 bars) `CWT12-coil-k6-long` 11 trades +$72.93 (first Graveyard day). Opening-Range Low Sweep Reversal
  `LIQ-orl-sweep-open15-s25-long` +$60.95.
- **Worst:** RW2-FD 18 trades 17% win −$375.14. Failed Prior-Day-High Break Short `CWT14-failbrk-pdh-p10-short`
  34 trades −$270.92 and `pdh-p05-lowvol-short` 23 trades −$256.64. Morning Bounce Fade `heat_fade_short` 0/9 −$223.39.
- **Blocked:** "max positions for this setup" 131 signals would have made +25.4R (118 ORL longs +28.8R). The −2R
  per-setup stop blocked 84 that would have lost −22.3R, so it earned its keep.
- **Edits:**
  1. *Queued (analysis only):* `bdi1027-graveyard-cap-replay`. Replay the cap-blocked and stop-blocked signals over
     every Graveyard session to see whether the half caps clip one side only on trend days. The caps are the owner's
     design.
  2. *No change:* a burst cap on the 09:55 pdh shorts failed on two years (nightly-1015). The ORL longs' green day does
     not change their record (640 trades −0.123R, two years −0.093R).

### Setup Generator (mcf-data-gen): +$564.80, best day of the five
- **Day:** 89 trades (23/day before GX1 and the new GEN setups), **62.9% win vs 50.2% break-even**, +0.168R (+15.0R).
  Longs 77 trades +$535.47, shorts 12 +$29.33. The 11:00 hour made +$566.
- **Peak vs close:** −$74 (11:12) → **+$863 (15:46) → +$565**. $298 was given back in the last 9 minutes: 44 open hold-type
  winners faded into the 15:55 flatten as the index dipped.
- **Best:** Generated ORB-fail-up mid-day hold long `GEN-261021-06-…-hold-long` 25 trades +0.53R +$440.99. VolRatio ORL-distance mid-day long
  `GEN-261027-05-…-t05s1-long` 18 trades +$94.46 (day 1). RSI-slope lunch hold long `GEN-261023-07` +$88.58.
- **Worst:** MACD-hist / RSI5 afternoon long `GEN-261020-01-…-t1s05-long` 0/3 −$77.32. MACD-hist bull-div mid-day short `GEN-261020-04` −$43.93.
  ORB-fail-down lunch hold long `GEN-261020-05` 17 trades −$29.24.
- **Blocked:** spread-% 6 −4.9R; nothing notable.
- **Edits:**
  1. *Tested (first look):* a 15:45 flatten for the give-back. There is no general last-10-minute fade for longs on two
     years (+0.004R, t 0.70); open winners fade only −0.024R. It stays queued for a test on the generator's own lots.
  2. *No change:* GEN-261021-06 is 37 trades +0.336R but −0.058R without its best day (today 106%, **1 day**).
     Not promotion-ready; GEN setups move only with the owner's consent.

## 1. Every trade (966 of 966 with bars; `trades_bdi.py` = bdi1026's, unchanged → `per_trade_1027.csv`, `by_setup_1027.csv`, `out_1027.txt`)
- R after costs: Primary +6.4R, Testing 1 −60.6R, Testing 2 −38.5R, Graveyard −46.9R, Gen +15.0R. **Total −124.6R**
  (10-26 −41.9R). **Longs +1.5R (678), shorts −126.1R (288)**, the mirror of 10-26 (longs −74.0R, shorts +32.1R).
- **Exit levers** (Δ R vs the simulated bracket, all accounts):

  | lever | 5 days to 10-26 | **10-27** | 6-day |
  |---|---|---|---|
  | breakeven at +0.5R | −22.8 | +13.0 | −9.8 |
  | +0.5R target | −44.6 | +24.4 | −20.2 |
  | +1R target | −12.9 | +40.4 | +27.5 |
  | 0.5R trail after +0.5R | +50.2 | +27.6 | **+77.8** |
  | hold to 15:55 | −109.4 | **+131.2** | +21.8 |
  | stop-and-reverse 1R/1R | −82.5 | −0.4 | −82.9 |
  | one re-entry after a stop | −17.2 | −11.8 | −29.0 |
  | opposite side 1R/1R | −34.3 | +98.8 | +64.5 |

  The trail is ahead on 5 of 6 days (+77.8R), but the book-wide trail already failed on history (`t6-exit-overlay`,
  `sw-w4-book-exits`, `exit-cwt-trail-notarget`). Hold and opposite flip with the day's direction (today +131R / +99R
  on the rally). Stop-and-reverse (−82.9R) and re-entry after a stop (−29.0R) are negative again.
- **patterns.csv:** +420 loser rows for 10-27 (3,616 → 4,036; `merge_patterns.py`, idempotent by date). Loss mix:
  small MFE 27.1% (10-26: 15.8%), never worked 26.4% (33.8%), late hold 14.5%, gave back 11.2%, wrong side after a big
  swing 11.2%, stopped then reversed 9.5%. As on 10-26, the losses were mostly entries rather than exits.
- **Intraday give-back** (curves from nightly1027, attribution here): only Gen gave back materially ($298 after 15:46,
  open hold winners). Primary's $9 is noise. T2/Graveyard fell on new short entries, not on fading winners. Nothing new
  for `giveback1019/`. The Gen pattern is the `nightly-1027-flatten-1545` / `nightly-1020-gen-hold-mfe-giveback` pair.

## 2. Recurring patterns (≥ 3 of the last 10 sessions), all already in the backlog
- CWT14 pdl/orl longs never worked or small MFE (12 days): today's two filters fail on history (above).
- Shorts into an index reversal (MF3/MF5/exhaustion/RW2/heat_fade_short; 10-12, 10-14, 10-20, 10-27): covered by
  `bdi1015-short-index-up-veto` and `nightly-1019-index-chase-veto`, and the ix-gate already failed on two years.
- Burst entries: tested and failed for shorts, coil and now pdl longs.

## 3. Backlog (`research/backlog.jsonl`, `research/BACKLOG.md` regenerated)
- New, failed: `bdi1027-index-reclaim-leaders-long` (16 configs), `bdi1027-pdl-long-burst-skip` (4).
- Updated: `nightly-1027-pdl-long-index-low-age` → failed (4). `nightly-1027-flatten-1545`: first-look note added; still an idea.
- New, idea (queued with the test each needs): `bdi1027-spread-bps-skip-replay`, `bdi1027-graveyard-cap-replay`.

## vs yesterday (10-26)
10-26: 20 configurations, 0 pass, −41.9R live. 10-27: 25 configurations, 0 pass, −124.6R live (shorts −126R on the
rally). **Not improved.** Why: the books are still direction bets. Tonight's long setup does pick better stocks than
random (+0.01..+0.05R in every row), but its trigger loses in down sessions like every index-conditioned rule so far.
**Next:** keep the leader-selection kernel (it beat the control in all 16 rows) and pair it with a trigger that is not
a market-direction bet, for example a stock-specific event such as a gap or news, which first needs that event data in the history cache. Also run
the two queued replays.

## Suggestions
None pass, so there is no DECISION. No near-miss for Testing. K4 (nightly) stays the only open owner question tonight.

Files: `PLAN.md`, `trades_bdi.py`, `merge_patterns.py`, `per_trade_1027.csv`, `patterns_1027.csv`, `by_setup_1027.csv`,
`out_1027.txt`, `accounts.py`, `accounts_out.txt`, `skipped.py`, `skipped_out.txt`, `skipped_1027.csv`, `scan_1027.py`,
`eval_1027.py`, `eval_out.txt`, `results.csv`, `rework_1027.py`, `rework_out.txt`, `results_rework.csv`,
`cluster_1027.py`, `cluster_out.txt`, `results_cluster.csv`, `last10.py`, `last10_out.txt`, `counts.json`. Scan
trades are in the scratchpad (not in git).

Educational only — not financial advice.
