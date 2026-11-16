# Workbench results: Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (`CWT14-failbrk-orl-p10-long`)
Mechanic, 2026-11-16 (built during market hours; no config changed). Educational only — not financial advice.

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
