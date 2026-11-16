# Workbench results: Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (`CWT14-failbrk-orl-p10-long`)
Mechanic, 2026-11-16 (built during market hours; no config changed). Educational only — not financial advice.

> **Superseded by the Rerun at the end of this file (2026-11-16, supervisor standard): deploy WB5, not WB4.** The WB4 deploy plan below was never applied (no account lists WB4) and must not be.


## Verdict
| Copy | One change | Replay avg R (parent -0.188) | 2-year avg R (parent -0.127) | Verdict |
|---|---|---|---|---|
| `CWT14-failbrk-orl-p10-long-WB1` | P15 1R 0.25 -> 0.30 x daily ATR (`r_atr_frac`) | -0.102 | -0.098 | PASS |
| `CWT14-failbrk-orl-p10-long-WB2` | P5 window 09:50-12:00 -> 10:30-12:00 | -0.179 | -0.116 | PASS (narrowly: the replay gain is +0.009R and avg R w/o worst day is 0.008R worse, within the 0.02R allowance) |
| `CWT14-failbrk-orl-p10-long-WB3` | P1 extra intake filter: daily ATR >= 2.0% of price | -0.125 | -0.104 | PASS |
| `CWT14-failbrk-orl-p10-long-WB4` | WB1 + WB3 combined (own config) | **-0.101** | **-0.079** | **PASS — recommended to deploy** |

Pass rule (owner 2026-11-16, replaces the significance bar): the copy meets or exceeds the parent's avg R after costs
in BOTH tests (meets = within ~0.01R or >= 95%), and is not worse on avg R w/o best day / w/o worst day by more than
0.02R / 10%. Parent and copies were scored by the identical pipeline; the parent's live record is NOT used in the
decision (diagnosis only, DIAGNOSIS.md).

**Read this before deploying:** every copy, like the parent, still LOSES after costs in both tests (WB4: -0.101R
replay, -0.079R 2-year). The copies are better than the parent, not profitable. They are positive only on up-market
sessions (2-year: WB4 +0.056R on up days, -0.078R flat, -0.194R down; parent -0.009 / -0.124 / -0.227) — a
market-direction gate is the strongest lead left and is a backlog idea, not tested here.

## Configurations counted: 16
Parent + 7 exit configurations (stop x0.8, stop x1.2, target 0.4R, target 0.6R, scale-out half at +0.35R then
breakeven, 1R x1.2, flat at 13:00) + 7 entry/intake configurations (window start 10:15, window start 10:30, ATR >= 1.5%,
ATR >= 2.0%, reclaim <= 0.08 ATR, poke >= 0.15 ATR, ADV >= $150M), all scored on the TRAIN split only for the shortlist,
+ the WB4 combination. Bar max(1.5, sqrt(2 ln 16)) = **2.35** (reported; no longer a pass hurdle). On the paired-by-day
difference vs the parent, the 2-year test clears it for WB1 (t 8.8), WB3 (6.5) and WB4 (9.7) but not WB2 (2.0); the
22-session replay clears it for none (t 0.4-1.8): the replay gain is consistent in direction, not proven by itself.
Failures (train, avg R vs parent -0.151): stop x0.8 -0.211, target 0.6R -0.155, scale-out -0.172, flat 13:00 -0.151,
poke >= 0.15 -0.150, target 0.4R -0.149, ADV >= 150M -0.147, window 10:15 -0.146; not shortlisted though better:
stop x1.2 alone -0.114 (not a spawn parameter; 1R x1.2 = WB1 is its spawnable twin), ATR >= 1.5% -0.138, reclaim cap -0.136.

## The tests (identical for parent and copies)
- **Replay of the live sessions:** every session day of the parent's live window with bars on hand, 2026-10-12..11-10
  (22 sessions; 11-11..11-13 not cached, fetching is after-hours only). Signals from the lab frames
  (research/history2y frames to 11-04; 11-05..11-10 rebuilt from data/team 1-minute bars with the same
  setup_lab.build pipeline — parity on 11-02..11-04: 526 of 526 rebuilt signals identical; 183 signals of symbols
  missing from the team day files are absent on 11-05..11-10). Isolated (no caps, no -2R latch, no quote checks), so
  it holds far more trades than live (3,197 vs 588 live trades in these sessions).
- **2-year backtest:** 2024-10-01..2026-10-09, open months only; **locked block 2024-11-01..2025-02-28 never read**
  (frames come from the open directory; 1-minute rows in the block are dropped on read; an assert checks the signals).
  Train = ..2025-12-31 (used to pick the shortlist), valid = 2026-01-01..10-09.
- Engine: module mask (cwt_live_lib.b3, OR level, p 0.10), point-in-time ADV20 >= $95M, price >= $5, ATR >= 1% (account
  universe), window on the 5-minute bar close, first qualifying bar per symbol-day (refire false). Fill = open of the
  1-minute bar 1 minute after the signal bar closes. Stop / target from the signal-bar close (as LabStrategy);
  same-minute stop+target = stop first; flat 15:55. R = net P/L / |fill - stop| (the live R definition).
- **Costs in (LR8 production model)**, every config alike: entry (1c + 1 bp) x time-of-day multiplier + LR8 1 bp
  entry cushion; target filled at the limit (no improvement); stop (1c + 1 bp) + max(2c, 4 bp); market / time exits
  (1c + 1 bp) + max(1c, 1 bp); SEC $20.60/M on the sale, TAF $0.000195/sh, CAT $0.00005/sh/side.
- Code: `code/` (sig.py, extra.py, sig_extra.py, sim.py, ana.py, evalc.py, extra_stats.py; scratch paths inside),
  numbers: `results.csv`.

## Side by side (avg R after costs; worst day = total R of the worst session)

**Replay of the live sessions, 2026-10-12..11-10 (22 sessions)**

| Copy | Trades | Win % | Avg R | Avg R w/o best day | Avg R w/o worst day | Total R | Worst day R | Avg win / avg loss | Paired-by-day diff vs parent (t) |
|---|---|---|---|---|---|---|---|---|---|
| parent | 3197 | 62.7 | -0.188 | -0.215 | -0.141 | -602 | -181.4 | +0.443 / -1.249 | - |
| WB1 r_atr_frac 0.30 | 3197 | 63.6 | -0.102 | -0.122 | -0.082 | -327 | -81.7 | +0.444 / -1.056 | +0.069R (t 1.69) |
| WB2 window 1030-1200 | 1673 | 60.8 | -0.179 | -0.199 | -0.149 | -300 | -69.4 | +0.429 / -1.123 | +0.020R (t 0.40) |
| WB3 ATR%>=2.0 | 2549 | 62.8 | -0.125 | -0.148 | -0.106 | -319 | -69.7 | +0.455 / -1.105 | +0.050R (t 1.37) |
| WB4 r30 + ATR%>=2.0 | 2549 | 63.0 | -0.101 | -0.121 | -0.080 | -257 | -69.0 | +0.454 / -1.046 | +0.075R (t 1.79) |

**2-year backtest, 2024-10..2026-10-09 (428 sessions, locked block excluded)**

| Copy | Trades | Win % | Avg R | Avg R w/o best day | Avg R w/o worst day | Total R | Worst day R | Avg win / avg loss | Paired-by-day diff vs parent (t) |
|---|---|---|---|---|---|---|---|---|---|
| parent | 56316 | 63.0 | -0.127 | -0.129 | -0.125 | -7152 | -165.8 | +0.457 / -1.122 | - |
| WB1 r_atr_frac 0.30 | 56316 | 63.3 | -0.098 | -0.100 | -0.096 | -5513 | -151.6 | +0.453 / -1.047 | +0.027R (t 8.81) |
| WB2 window 1030-1200 | 33295 | 63.6 | -0.116 | -0.118 | -0.113 | -3856 | -113.3 | +0.452 / -1.107 | +0.013R (t 2.01) |
| WB3 ATR%>=2.0 | 43552 | 63.3 | -0.104 | -0.106 | -0.101 | -4523 | -149.6 | +0.468 / -1.092 | +0.022R (t 6.53) |
| WB4 r30 + ATR%>=2.0 | 43552 | 63.4 | -0.079 | -0.082 | -0.076 | -3449 | -150.7 | +0.463 / -1.018 | +0.044R (t 9.74) |

Train / valid split (same direction in both halves for every copy):

| Copy | Train ..2025-12 avg R (n) | Valid 2026-01..10-09 avg R (n) |
|---|---|---|
| parent | -0.151 (28116) | -0.103 (28200) |
| WB1 | -0.116 (28116), t 7.1 | -0.080 (28200), t 5.2 |
| WB2 | -0.134 (16682), t 1.8 | -0.097 (16613), t 1.0 |
| WB3 | -0.127 (19898), t 4.4 | -0.084 (23654), t 5.8 |
| WB4 | -0.096 (19898), t 6.9 | -0.065 (23654), t 7.4 |

(Valid worst day: WB1 -151.6 vs parent -144.0, 5% worse, inside the 10% allowance.)

Day type (2-year, session regimes from research/history2y): parent up -0.009 / flat -0.124 / down -0.227;
WB1 +0.038 / -0.095 / -0.213; WB2 +0.010 / -0.105 / -0.224; WB3 +0.010 / -0.103 / -0.200; WB4 +0.056 / -0.078 / -0.194.
Median hold (base exits): parent 21 min, WB2 27, WB3 22.

## Pending config change — "ready to deploy after close" (NOT applied; built 10:40 ET during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session (2026-11-17).
One copy only: **WB4** (it contains WB1 and WB3; deploying the near-identical WB1 / WB3 as well would run three
twins). The parent stays in the Graveyard, unchanged.
1. Module: copy `research/workbench/CWT14-failbrk-orl-p10-long/modules/CWT14-failbrk-orl-p10-long-WB4.py` to
   `research/bdi/cwt/live/CWT14-failbrk-orl-p10-long-WB4.py` (next to cwt_live_lib.py; the workbench copy also
   finds it through its own sys.path line).
2. `config/account_testing.yaml` (Testing 1 — not the parent's account; Testing 1 = Testing 2 in weight), under
   `strategies:` add
   ```yaml
   CWT14-failbrk-orl-p10-long-WB4:
     # Workbench copy of CWT14-failbrk-orl-p10-long (Graveyard), Mechanic 2026-11-16: 1R 0.30 x ATR + ATR >= 2.0% intake;
     # research/workbench/CWT14-failbrk-orl-p10-long/RESULTS.md. Effective session 2026-11-17.
     enabled: true
     type: lab
     module: research/bdi/cwt/live/CWT14-failbrk-orl-p10-long-WB4.py
     min_adv: 95000000
     window: [950, 1200]
     r_atr_frac: 0.30
     scale_out_r: 0.35
     live_scale_out: false
     tags: [workbench, "parent:CWT14-failbrk-orl-p10-long"]
   ```
   and put `CWT14-failbrk-orl-p10-long-WB4` FIRST in `live.setup_order` (ahead of ST6-volspikeup-short-mid-t1s1-FD).
3. `config/setup_names.yaml`: `CWT14-failbrk-orl-p10-long-WB4: {name: "Failed Opening-Range-Low Break Long (0.1 ATR) [fill] — WB4: 1R 0.30 ATR + ATR >= 2%", side: long, what: "as the parent, 1R = 0.30 x daily ATR (stop 1R, target +0.5R), only names with daily ATR >= 2.0% of price"}`.
4. `research/ledger.jsonl`: id `2026-11-16-wb-cwt14-orl-p10-wb4`, effective 2026-11-17, title "Workbench copy
   CWT14-failbrk-orl-p10-long-WB4 added to Testing 1, first in setup_order (Mechanic pass)", patch
   `{"strategies.CWT14-failbrk-orl-p10-long-WB4 (testing)": [null, "added, enabled"], "live.setup_order (testing)": ["...", "WB4 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5 (passes go to a testing account at once)";
   then `python -m mcf.research.ledger check`.
5. `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit), `pytest -q`,
   commit, push to claude/charming-mccarthy-i3rhhr after 16:05 ET (setup-freeze).

---
# Rerun — supervisor standard (owner 2026-11-16)
Mechanic rerun, 2026-11-16, built 11:15-12:30 ET during market hours: research files only, no config touched.
Educational only — not financial advice.

Brief: build on WB4, try the experimental layers the first run left untested (market-state gate measured AFTER 09:50,
entry-drift guard, max 2 lots per symbol, time of day, exits, day caps), 5 worst + 5 best live trades, count every
config, aim for a copy clearly better OVERALL. Evidence: DIAGNOSIS.md "Rerun"; engine `..._engine.png` (refreshed);
trades `..._rerun_worst{1-5}_*.png`, `..._rerun_best{1-5}_*.png`.

## What the parts showed
1. **The worst trades are a measurement fault, not a signal fault.** 4 of the 5 worst live trades (VXX, UVXY, KEY, FNB,
   -1.8..-2.6R) are cheap names where 1R was a few cents and a fill under the signal close shrank it further. A
   cost-to-R intake (round-trip + stop slippage <= 10% of 1R) removes all four and, over 2 years, lifts WB4 from
   -0.079R to -0.061R (paired vs WB4 t 7.5).
2. **WB4's gain was mostly the bigger R denominator.** Per dollar traded, WB4 is no better than the parent (2-year
   -7.9 vs -8.1 bps; replay -13.7 vs -12.0 bps). The new layers cut the loss per dollar traded as well (WB5: -4.6 bps
   2-year, -3.4 bps replay), so this copy's gain is real money, not a different unit.
3. **Down mornings are where it bleeds; the 09:50-anchored gate cuts those days.** SPY since 09:50 >= -0.20% at the
   decision bar halves the worst day (2-year -120 -> -65R; replay -56 -> -43R) and lifts the replay to near flat. On the
   2-year test its per-trade gain comes from skipping the heavy days (paired by day vs WB4 it is -0.010R, t -1.5:
   it does not improve the days it trades), so it is mainly a tail / down-day part. Stricter gates (SPY >= 0, above VWAP) look great on the 22 replay days but do nothing
   over 2 years — not used.
4. **The stop was too tight for this trade; nothing else in the exhaust helps.** Stop 1.0 -> 1.2 -> 1.5 -> 2.0 x 1R
   (target unchanged at +0.15 ATR) improves 2-year avg R -0.050 -> -0.038 -> -0.027 -> -0.020 on the gated set, and
   per-notional -5.6 -> -5.1 -> -4.6 -> -4.2 bps. Breakeven moves, max hold, trailing, wider target, fill-anchored or
   structural stops all lose. Signal sensors (poke, reclaim, RSI, VWAP, flow, gap, relative strength) are flat.

## Copies (avg R after costs; parent and copies through the identical pipeline)
| Copy | Change | Replay avg R | 2-year avg R | W/o best day (replay / 2y) | Worst day (replay / 2y) | Verdict |
|---|---|---|---|---|---|---|
| parent | — | -0.188 | -0.127 | -0.215 / -0.129 | -181.4 / -165.8 | — |
| WB4 (first run) | 1R 0.30 ATR + ATR >= 2% | -0.101 | -0.079 | -0.121 / -0.082 | -69.0 / -150.7 | superseded |
| step: WB4 + C1 | + cost/R <= 0.10 | -0.080 | -0.061 | -0.099 / -0.063 | -56.5 / -120.1 | layer kept |
| step: + G3 | + SPY since 09:50 >= -0.20% | -0.024 | -0.050 | -0.043 / -0.053 | -43.2 / -65.1 | layer kept |
| **WB5** | WB4 + C1 + G3 + stop 1.5R (0.45 ATR), target +0.15 ATR | **-0.007** | **-0.027** | -0.020 / -0.029 | -38.6 / -53.9 | **PASS — recommended** |
| alt (not spawned) | WB5 with stop 2.0R (0.60 ATR) | -0.003 | -0.020 | -0.013 / -0.021 | -35.1 / -53.2 | pass; not chosen (target = 0.25R of a 4:1 stop; most of the extra gain is the denominator: replay -3.7 vs -3.4 bps) |
| alt (not spawned) | WB5 + first 30 trades per session | +0.052 | -0.031 | +0.040 / -0.032 | -12.2 / -26.5 | not deployable as a setup rule (no per-setup trades/day knob); account-level idea |
| alt (not spawned) | WB5 + start 10:15 | -0.022 | -0.023 | -0.034 / -0.025 | -32.7 / -50.0 | mixed (replay worse) |

Pass rule (RULES.md clarification 2026-11-16): WB5 beats the parent in BOTH tests (+0.181R replay, +0.100R 2-year per
trade) and is better on w/o best day and worst day. It also beats WB4 in both. **It is still not positive after costs
in either test** (-0.007R replay — within noise of zero — and -0.027R over 2 years); it is up-day positive (+0.074R)
and nearly flat on flat days.

## Supervisor sign-off — WB5
- **What changed (vs the parent):** (1) intake: daily ATR >= 2% (WB4) and cost-to-R <= 0.10 — skips names where a stop
  costs more than 10% of the risk; (2) gate: SPY must not be down more than 0.20% since 09:50 at the decision bar;
  (3) brakes: stop at 0.45 x ATR under the signal close (was 0.25), target unchanged in price terms at +0.15 x ATR
  (was +0.125). Signal, window 09:50-12:00, first bar per symbol-day and flat 15:55 unchanged.
- **Why:** the losses came from thin-R cheap names (cost + fill drift), from down mornings, and from a stop that sat
  inside the noise (the first run: 37 of 222 live stops had first gone >= +0.4R).
- **Overall before -> after (parent -> WB5):** replay -0.188 -> -0.007R/trade (paired-by-day +0.134R, t 2.94),
  2-year -0.127 -> -0.027R (+0.062R, t 8.32; train -0.151 -> -0.038, valid -0.103 -> -0.019, same direction in both);
  w/o best day -0.215 -> -0.020 / -0.129 -> -0.029; worst day -181 -> -39R / -166 -> -54R; loss per dollar traded
  -12.0 -> -3.4 bps (replay), -8.1 -> -4.6 bps (2-year); win 63 -> 72% / 69%. Up / flat / down days (2-year):
  -0.009 / -0.124 / -0.227 -> +0.074 / -0.024 / -0.143 (better on every day type).
- **Where it gives a little back:** about 55% fewer trades (2-year 56,316 -> 24,867; replay 3,197 -> 1,450); avg win
  smaller in R (+0.46 -> +0.31R, the wider stop); the gate skips reversal mornings — 2 of the 5 best live trades (BABA
  11-05, TNA 10-14) fired while SPY was falling after 09:50 and would not be taken; 19 of 428 sessions have no trade.
  ORCL 11-06 (a real failed reclaim) is still taken and still stopped (about -1.0R instead of -1.84R).
- **Rule-change context:** live window 10-12..11-16 holds the Testing 2 scale-out (10-17), the Graveyard move (10-21),
  latch policy (10-23), Graveyard BP / caps and LR1 / LR5 / LR8 (11-12); the backtests apply one rule set throughout
  (LR8 costs, no scale-out, no latch), so no rule change is mixed into the copy-vs-parent numbers.

## Configurations counted: 60 more in this rerun, 76 in all
Families (each scored on the WB4 base unless noted; selection on TRAIN, then valid / replay / 2-year reported):
gates 8 (SPY since 09:50 >= 0 / -0.10 / -0.20%, SPY not below its 09:30-09:50 low, SPY above VWAP, breadth_open >= 0.40,
breadth_open not lower than at 09:50, SPY >= -0.10% since 09:50 and fo >= -0.5%); cost-to-R 3 (0.10 / 0.15 / 0.20);
drift guards 3 (|drift| <= 0.5R, drift >= -0.25R, runner CF at the fill <= 0.15); lots 2 (max 2 per symbol with 10-min
cooldown / after the first exits); window 4 (10:15, 10:30 start, end 11:00, end 13:00); exits 8 (levels from the fill,
breakeven +0.3R, max hold 30 / 60, trail no target, target 0.7R, stop 1.2R, stop 1.2R from the fill); day caps 3 (latch
-10 / -20R, 40 trades/day); combinations 9; exits on C1+G3 11 (stop 1.5 / 2.0R, 1.5R+target 0.6 / 0.4R, 2.0R+0.6R,
1.2R+0.4R, 1.5R+max hold 60, 1.2R+breakeven 0.4R, structural stop under the poke low, structural + 0.6R; stop 1.5 / 2.0R
on plain WB4); layers on WB5 8 (max 30 / 60 trades per day, cost/R <= 0.07, SPY >= -0.30%, + breadth_open >= 0.30,
start 10:15, max 2 lots after exit, drift guard 0.5R); C1+G3 at stop 1.0R 1. Bar max(1.5, sqrt(2 ln 76)) = **2.94**:
WB5 vs parent clears it on the 2-year test (t 8.32) and reaches it on the 22-session replay (t 2.94); WB5 vs WB4 t 2.83
replay / 2.94 2-year. Code: `code2/` (sim2.py, ctx.py, ev.py, exp.py, combo.py, comp.py, exits3.py, bps.py, exp4.py,
final.py; exp1-4.csv), numbers `results_rerun.csv`.

**Failures (2-year avg R vs WB4 -0.079 unless noted):** SPY >= 0 since 09:50 -0.079 (replay +0.015 only), SPY above
VWAP -0.083, breadth_open >= 0.40 -0.091, breadth_open vs 09:50 -0.080, SPY range gate -0.078 (worst day -157R); drift
guard 0.5R -0.079 (no effect at a 1-minute fill), drift >= -0.25R -0.077; 2 lots per symbol -0.078 / -0.080 (worst day
-179R); window 10:30 start -0.070 but replay -0.142, 10:15 start replay -0.112, end 11:00 -0.083, end 13:00 -0.079;
breakeven +0.3R -0.094, max hold 30 / 60 -0.095 / -0.086, trail without target -0.118, target 0.7R -0.080 (worst day
-191R), levels from the fill -0.076; latch -10 / -20R -0.081 / -0.080; on C1+G3: structural stop -0.073 (replay -0.125,
replay worst day -196R), breakeven +0.4R -0.045, stop 1.2R + target 0.4R -0.038, stop 1.5R + max hold 60 -0.035;
on WB5: cost/R <= 0.07, + breadth_open >= 0.30, 2 lots, drift guard — each within ±0.004R of WB5 (not worth a part).

## The tests (identical for parent and every copy)
As the first run: replay of the live sessions 2026-10-12..11-10 (22 sessions, isolated: no caps / latch / quote
checks), 2-year backtest 2024-10-01..2026-10-09 (open months; **locked block 2024-11-01..2025-02-28 never read**: no
signals in it, 1-minute rows in it dropped on read, asserts in code2/sim2.py), train ..2025-12-31 / valid 2026-01..10-09,
fill = open of the 1-minute bar 1 minute after the signal bar closes, same-minute stop+target = stop, flat 15:55,
R = net P/L / |fill - stop|, LR8 production costs on every config. New in the rerun: market state per (date, 5-minute
bar close) from SPY 1-minute bars closed by that time (code2/ctx.py; matches the runner's `spy_fo` context column,
correlation 1.00) and breadth from research/history2y/data/context (11-05..11-10 rebuilt from the lab frames). The
gate in the module (`context: [spy_fo]`, SPY since 09:50 = (1 + fo) / (1 + fo at 09:50) - 1) reproduces the research
trade list on 2026-03: 1,765 of 1,768 symbol-days identical (3 at the threshold).

## Pending config change — "ready to deploy after close" (NOT applied; replaces the WB4 plan above)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. One copy only:
**WB5** (WB4 is NOT deployed — WB5 contains it; running both would be twins). The parent stays in the Graveyard, unchanged.
Destination: **Testing D** (`config/account_testingd.yaml`; full universe, no top_n pool, max_stop_cost_r 0.15 — WB5's
stop is >= 15x its cost so the CF only bites on a large adverse drift, which is the drift guard the live worst trades
needed; not the parent's account; Testing D = the other testing areas in weight). **Normal priority** (owner): not first,
not spotlight, not On Deck.
1. Module: copy `research/workbench/CWT14-failbrk-orl-p10-long/modules/CWT14-failbrk-orl-p10-long-WB5.py` to
   `research/bdi/cwt/live/CWT14-failbrk-orl-p10-long-WB5.py` (next to cwt_live_lib.py).
2. `config/account_testingd.yaml`, under `strategies:` add
   ```yaml
   CWT14-failbrk-orl-p10-long-WB5:
     # Workbench copy of CWT14-failbrk-orl-p10-long (Graveyard), Mechanic rerun 2026-11-16: WB4 (ATR >= 2%) + cost/R <= 0.10
     # + SPY since 09:50 >= -0.20% + stop 0.45 ATR / target 0.15 ATR (module GEOM "S");
     # research/workbench/CWT14-failbrk-orl-p10-long/RESULTS.md "Rerun". Effective session 2026-11-17.
     enabled: true
     type: lab
     module: research/bdi/cwt/live/CWT14-failbrk-orl-p10-long-WB5.py
     min_adv: 95000000
     window: [950, 1200]
     context: [spy_fo]
     scale_out_r: null
     live_scale_out: false
     tags: [workbench, "parent:CWT14-failbrk-orl-p10-long"]
   ```
   and add `- CWT14-failbrk-orl-p10-long-WB5   # workbench copy, normal priority (~58 trades/session isolated)` at the
   END of `live.setup_order` (after CWT14-failbrk-pdl-p10-lowvol-long: narrowest-first order puts the highest-volume
   setup last) — not at the top.
3. `config/setup_names.yaml`: `CWT14-failbrk-orl-p10-long-WB5: {name: "Failed Opening-Range-Low Break Long (0.1 ATR) [fill] — WB5: cost/R + SPY-since-09:50 gate + 0.45 ATR stop", side: long, what: "as the parent; only names with ATR >= 2% and stop cost <= 10% of 1R (0.30 ATR); skipped while SPY is down > 0.20% since 09:50; stop 0.45 ATR under the signal close, target +0.15 ATR, flat 15:55"}`.
4. `research/ledger.jsonl`: id `2026-11-16-wb-cwt14-orl-p10-wb5`, effective 2026-11-17, title "Workbench copy
   CWT14-failbrk-orl-p10-long-WB5 added to Testing D at normal priority (Mechanic rerun pass; replaces the unapplied WB4
   plan)", patch `{"strategies.CWT14-failbrk-orl-p10-long-WB5 (testingd)": [null, "added, enabled"], "live.setup_order (testingd)": ["...", "WB5 appended last"]}`,
   evidence this file, approved_by "owner 2026-11-16 (Workbench rerun: copy to a Testing A-F account at normal priority)";
   then `python -m mcf.research.ledger check`.
5. Smoke test before commit: load the account config and run the setup over one cached session (the module needs the
   `spy_fo` context column; without it the mask fires nothing — fail safe), `python -m mcf.report.assignments`
   (regenerates docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
