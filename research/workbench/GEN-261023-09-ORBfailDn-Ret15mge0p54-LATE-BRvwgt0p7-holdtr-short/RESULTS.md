# Workbench results: Generated: Late Failed-Breakdown Pop Short `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short` (Testing E; SHORT)
Mechanic, 2026-11-16/17 (Workbench batch; research files only, no config touched, nothing deployed).
Educational only — not financial advice.

**Only 10 live trades, all in one session (2026-11-09): this verdict rests on the 2-year backtest, plainly.** The replay of the
17 live-window sessions holds 29 parent trades on 2 sessions and 7-23 copy trades on 1 session (11-09); it is reported
because the pass rule needs it and it points the same way, but on its own it proves nothing.

## Verdict (copies table; avg R after LR8 costs)
| Copy | Change | Replay avg R (parent +0.025) | 2-year avg R (parent +0.036) | Avg R w/o best day (2y; parent −0.020) | Worst day R (replay / 2y; parent +0.13 / −120.5) | Trades (replay / 2y; parent 29 / 5,442) | Verdict |
|---|---|---|---|---|---|---|---|
| `...-WB1` | P6/P7 window 14:00 → 14:30-15:00 | +0.234 | +0.209 | +0.137 | +5.38 / −64.9 | 23 / 3,689 | PASS |
| `...-WB2` | new P11b: ret3_atr >= 0.20 | +0.064 | +0.181 | +0.064 | +0.77 / −41.9 | 12 / 2,304 | PASS (narrow on replay) |
| `...-WB3` | WB1 + WB2 | +0.690 | +0.407 | +0.254 | +6.21 / −39.7 | 9 / 1,509 | PASS |
| `...-WB4` | WB3 + new layer P11c ADX(7) >= 44 | **+0.689** | **+0.475** | **+0.368** | **+4.82 / −25.8** | 7 / 981 | **PASS — recommended** |

Replay w/o best day: the parent's best replay day is 11-11 (1 trade); without it +0.005 on 11-09. Every copy trades only on
11-09, so "w/o best day" leaves no trades; compared on the same session (11-09) the copies make +0.064..+0.690R per trade vs the
parent's +0.005, and their worst replay day is better (positive). Pass rule (RULES.md, clarification 2026-11-16) met by all four.

## Supervisor sign-off — WB4
- **What changed:** (1) P6/P7 entries only on 5-minute bars closing 14:30-15:00 (was 14:00); (2) new sensor P11b: the 15-minute
  pop must also be >= 0.20 daily ATRs (the parent's 0.54% treats a quiet ETF and a volatile stock alike); (3) new layer P11c:
  ADX(7) >= 44 (the pop is a strong directional push). Breadth gate, ORB-fail sensor, ADV, cost filter and the holdtr exit
  are unchanged.
- **Why:** over 2 years the parent's 14:00-14:30 entries lose in both halves (−0.06 / −0.11R) and the late ones win in both;
  small-in-ATR pops lose; ADX adds on top (fails alone: replay −0.036). The 4,461 trades WB4 removes averaged +0.024R; the 981
  it keeps +0.475R.
- **Overall before → after (2-year, costs in):** +0.036 → **+0.475R** (train +0.001 → +0.450, valid +0.092 → +0.524);
  w/o best day −0.020 → **+0.368**; worst day −120.5 → −25.8R; best-day share 153% → 30%; win 52.1 → 69.4%; avg win / loss
  +0.676 / −0.662 → +0.966 / −0.637; total R 196 → 466 on 82% fewer trades; w/o best month −0.020 → +0.363.
  Replay +0.025 → +0.689R (7 trades, 1 session).
- **With the live P14 cap (50 open lots per setup — the cap binds on this setup):** parent −0.051 → WB4 **+0.312R**
  (train +0.234, valid +0.405, w/o best day +0.189, worst day −22.4R; paired by day +0.86R/session, t 2.53). Cap 30: parent
  −0.071 → +0.200R. Day cap 20: −0.076 → +0.117R.
- **Robustness (neighbours all beat the parent, 2y iso / cap 50):** ADX 35 / 40 / 48 / 52: +0.466 / +0.489 / +0.463 / +0.440
  (cap +0.243..+0.327); ret3_atr 0.18 / 0.22 with ADX 44: +0.439 / +0.519; start 14:25 / 14:35: +0.385 / +0.410.
- **Day types (remedy rule):** up −0.131 → **+0.181**, flat +0.135 → +0.062 (gives back), down +0.429 →
  +0.889. Better in 2 of 3 day types and in train and valid.
- **Where it gives a little back:** flat days (+0.135 → +0.062); trade count 5,442 → 981 over 2 years (74 of 127 traded
  sessions); on the live day it keeps 3 of 10 trades (GLD −1.05, GDXJ +0.50, LUV +3.38) and skips KGC +1.79 / GDX +0.80 /
  NCLH +0.87. Paired by day vs the parent isolated: +0.62R/session, t 0.82 — more R per trade and per session, not a proven
  daily edge; the record still leans on a few broad-rally days (2026-07-29 class). Breadth here is from the 1,226-name lab
  universe (2y) / the $20M+ universe (replay); live breadth uses the poll universe. Earnings blackout (P4) not modelled
  (calendar file absent) — same for parent and copies.
- **Signed off:** PASS, recommended for a testing account (plan below). Owner decides any On Deck / Primary step.

## Configurations counted: 151
122 configs in screen_all.csv (one-part, combos, layers, exits, caps) + 19 in screen_fin.csv (neighbours / layers on WB3) +
10 in screen_adx.csv (ADX neighbours); each scored isolated and with the P14 cap of 50 (sensitivity, not counted twice).
WB1..WB4 are among them. Bar max(1.5, sqrt(2 ln 151)) = 3.17 (reported, not a pass hurdle). Paired by day vs the parent
(2y isolated / cap 50): WB1 +1.32 t 2.01 / +0.55 t 2.17; WB2 +0.51 t 1.19 / +0.44 t 2.12; WB3 +0.96 t 1.42 / +0.71 t 2.20;
WB4 +0.62 t 0.82 / +0.86 t 2.53 — none clears 3.17.

**Every failure** (2y avg R vs parent +0.036 / replay vs +0.025):
- Timer: window 14:00-14:45 −0.018 / −0.001; 14:15 start +0.081 (fails cap 50 −0.061).
- Sensors: ret3 >= 0.45 +0.002; ret3 >= 0.80 / 1.0 pass alone (+0.115 / +0.184) but weaker than ret3_atr; macd_hist >= 0.10
  alone +0.126 / replay −0.037 (fails); ADX >= 44 alone +0.062 / replay −0.036 (fails).
- Gates: breadth > 0.6 −0.031 / −0.120; breadth > 0.75 +0.097 / replay +0.005 (fails replay); > 0.8 +0.154 / +0.047.
- Intake / cost: ADV 100M +0.036 / −0.028; ADV 300M +0.031; price >= $20 +0.041 / +0.025 (no change); no cost filter +0.021;
  cf 0.10 +0.038 / +0.004.
- Exhaust: 1R 0.20 ATR −0.002; stop 0.75R +0.006 / −0.078; stop 1.25R / 1.5R / 1R 0.30 ATR +0.059 / +0.054 / +0.058 (pass, small;
  on WB3 they lower avg R); target 1R / 1.5R / 2R +0.041 / +0.033 / +0.032; trail 0.5R −0.012, 0.75R +0.026, after 1.5R +0.045 /
  +0.007; no trail +0.031 (worst day −199R); BE +0.5R +0.002; max hold 30 / 60 −0.037 / +0.016 (replay −0.287 / −0.113);
  flat 15:30 / 15:45 −0.018 / +0.028; exit at 30/45 min if MFE small +0.025 / +0.038 (replay −0.188 / −0.111).
- Caps: day cap 10 / 20 −0.050 / −0.076.
- Passed but not spawned: W + macd_hist >= 0.10 combos (2y up to +0.70 but replay 1-3 trades, and they skip all 10 live trades);
  W+RA+ADX + trail after 1.5R +0.536 / +0.689 (cap +0.332) and W+RA + breadth > 0.75 +0.530 — small extra on 2y only;
  W+RA + sma20_dist >= 1 +0.551 (replay 3 trades). WB4 is the strongest copy that keeps a replay sample.

## The tests (identical for parent and copies)
- **Replay of the live sessions:** 2026-10-23..11-16 (17 sessions; Gen 10-23..11-13, Testing E 11-16). Read-only SIP GETs:
  daily + 5-minute bars of the $20M+ universe (breadth = share above own session VWAP, lab_context rules), 1-minute bars
  10-09..11-16 for the $75M+ names → lab frames as live (engine.lab_frame + apply_daily), arena indicators. Parity: all 10 live
  trades found at the same signal bar; module parity (code/modparity.py): each module's own mask() reproduces the harness
  selection exactly (parent 39/39 + 1 module-only, WB1 32/32, WB2 18/18, WB3 15/15, WB4 8/8).
- **2-year backtest:** 2024-10-01..2026-10-22 (ends before the live window), research/history2y frames + context, open months
  only; **locked block 2024-11-01..2025-02-28 never read** (asserted). Train ..2025-12-31, valid 2026-01-01..10-22.
- Engine (code/sim.py): module conditions on the 5-minute bar close, ADV >= $150M, price >= $5, Testing cost filter
  (stop-exit cost <= 0.15R, runner formula), first qualifying bar per symbol-day. Fill = open of the 1-minute bar 1 minute after
  the signal bar; stop = signal close + 1R (0.25 x daily ATR), no target, trail 1R once +1R, flat at the 15:55 open; stop checked
  first. R = net P/L / |fill − stop|. Optional P14 cap (open lots per setup) as sensitivity.
- Costs (LR8 production model): entry (1c + 1 bp) x time-of-day multiplier + 1 bp; stop exits + max(2c, 4 bp); time exits
  + max(1c, 1 bp); SEC + TAF on the short sale; CAT both sides.
- Code: `code/`; numbers: `results_final.csv`, `screen_all.csv`, `screen_fin.csv`, `screen_adx.csv`.

## Side by side (avg R after costs)
| Copy | Test | Trades | Sessions | Win % | Avg R | w/o best day | Total R | Worst day | Best-day share | Avg win / loss | Train / valid | Cap-50 avg R (w/o best day) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | replay | 29 | 2 | 48.3 | +0.025 | +0.005 | +0.7 | +0.13 | 82% | +0.674 / −0.580 | — | +0.025 |
| parent | 2y | 5,442 | 127 | 52.1 | +0.036 | −0.020 | +196 | −120.5 | 153% | +0.676 / −0.662 | +0.001 / +0.092 | −0.051 (−0.072) |
| WB1 | replay | 23 | 1 | 56.5 | +0.234 | — | +5.4 | +5.38 | 100% | +0.769 / −0.462 | — | +0.234 |
| WB1 | 2y | 3,689 | 113 | 60.1 | +0.209 | +0.137 | +771 | −64.9 | 39% | +0.733 / −0.580 | +0.201 / +0.221 | +0.028 (+0.005) |
| WB2 | replay | 12 | 1 | 58.3 | +0.064 | — | +0.8 | +0.77 | 100% | +0.767 / −0.920 | — | +0.064 |
| WB2 | 2y | 2,304 | 105 | 57.2 | +0.181 | +0.064 | +418 | −41.9 | 68% | +0.891 / −0.770 | +0.101 / +0.353 | +0.012 (−0.042) |
| WB3 | replay | 9 | 1 | 77.8 | +0.690 | — | +6.2 | +6.21 | 100% | +1.059 / −0.601 | — | +0.690 |
| WB3 | 2y | 1,509 | 82 | 66.8 | +0.407 | +0.254 | +614 | −39.7 | 46% | +0.959 / −0.704 | +0.341 / +0.512 | +0.161 (+0.108) |
| WB4 | replay | 7 | 1 | 71.4 | +0.689 | — | +4.8 | +4.82 | 100% | +1.205 / −0.601 | — | +0.689 |
| WB4 | 2y | 981 | 74 | 69.4 | +0.475 | +0.368 | +466 | −25.8 | 30% | +0.966 / −0.637 | +0.450 / +0.524 | +0.312 (+0.189) |

Day type (2y, up / flat / down): parent −0.131 / +0.135 / +0.429; WB1 +0.009 / +0.050 / +0.724; WB2 −0.145 / +0.442 / +0.630;
WB3 +0.046 / +0.029 / +0.912; WB4 +0.181 / +0.062 / +0.889.

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies this after 16:05 ET, effective the next session. One copy only: **WB4** (WB1-WB3 are contained in it).
The parent stays in Testing E, unchanged.
Account: **Testing 1** (`config/account_testing.yaml`) — a testing account, not the parent's (Testing E); chosen because its
per-setup cap (150 open lots) does not starve this setup's late mass-signal days (cap 30 → +0.200R, cap 50 → +0.312R,
isolated +0.475R). Twin check: `-WB4` ≠ parent key; different account.
1. `config/account_testing.yaml`, under `strategies:` add
   ```yaml
   GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4:
     # Workbench copy of GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short (Testing E), Mechanic 2026-11-17: window 14:30-15:00 + pop >= 0.20 ATR + ADX(7) >= 44;
     # research/workbench/GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short/RESULTS.md.
     enabled: true
     type: lab
     module: research/workbench/GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short/modules/GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4.py
     context: [breadth]
     min_adv: 150000000
     window: [1430, 1500]
     refire: false
     scale_out_r: null
     tags: [workbench, "parent:GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short", generated]
   ```
   and put it FIRST in `live.setup_order` (RULES 5).
2. `config/setup_names.yaml`: `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4: "Generated: Late Failed-Breakdown Pop Short — WB4: 14:30-15:00, pop >= 0.20 ATR, ADX(7) >= 44"`.
3. `research/ledger.jsonl`: one entry (add, effective next session, "Workbench WB4 of GEN-261023-09 to Testing 1, first in
   order; parent unchanged in Testing E"), then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments` in the same commit, `pytest -q`, PR with setup-freeze passing (after 16:00 ET).
5. Review after ~10 traded sessions alongside the parent, with the one-big-day check (breadth > 0.7 afternoons are rare:
   expect few traded sessions per month).

Educational only — not financial advice.
