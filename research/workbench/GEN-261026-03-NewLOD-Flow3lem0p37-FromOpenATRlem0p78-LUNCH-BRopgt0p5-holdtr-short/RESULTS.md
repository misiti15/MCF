# Workbench results: Generated: Lunch New-Low Short (selling) `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` (Testing D; SHORT)
Mechanic, 2026-11-16 (Workbench batch; built 13:30-15:00 ET during market hours: research files only, no config touched,
nothing deployed). Educational only — not financial advice.

**Few live trades (21 in 5 sessions, all in the Gen account): this verdict leans on the 2-year backtest, and says so.**
The replay of the live window holds 87 parent trades in 9 trading sessions (15 sessions scored); it is reported because the
pass rule needs it and it points the same way, but it is small. The parent's live record (+0.379R, 77% from 10-27) is
not used in the decision; on the identical backtest the parent is −0.039R per trade over 2 years.

## Verdict (copies table)
| Copy | Change | Replay avg R (parent +0.044) | 2-year avg R (parent −0.039) | Avg R w/o best day (replay / 2y; parent −0.132 / −0.055) | Worst day R (replay / 2y; parent −4.88 / −9.58) | Trades (replay / 2y; parent 87 / 1,180) | Verdict |
|---|---|---|---|---|---|---|---|
| `...-WB1` | new sensor P11b: close vs prior close <= −1.3 daily ATRs | **+0.175** | **+0.090** | +0.080 / +0.055 | −3.30 / −8.72 | 41 / 359 | **PASS — recommended** |
| `...-WB2` | P6/P7 window end 14:00 → 13:00 | +0.153 | −0.001 | −0.016 / −0.022 | −3.82 / −9.49 | 64 / 795 | PASS (not deployed: 2-year still ~0) |
| `...-WB3` | WB1 + WB2 (combo, own config) | +0.349 | +0.101 | +0.199 / +0.049 | −3.30 / −8.72 | 30 / 237 | PASS (not deployed: see below) |

Pass rule (RULES.md, clarification 2026-11-16): the copy meets or exceeds the parent's avg R after costs in BOTH tests and
is not worse on avg R w/o best day / worst day by more than 0.02R / 10%. All three clear it; every copy is better than the
parent on every one of those numbers in both tests. Ids: `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB1/2/3`.

**Why WB1 and not WB3:** WB3 has the higher avg R in both tests (+0.101 / +0.349), but its extra gain over WB1 comes from
the train half and the 15-session replay: valid period (2026-01..10-16) +0.052 vs WB1 +0.095, 2-year w/o best day +0.049 vs
+0.055, and it keeps 34% fewer trades (237 vs 359; 1.0 vs 1.6 per traded session). WB1 is one new sensor with a smooth
plateau (`..._wb1_frompc_curve.png`: −1.1 to −1.5 all positive in train and valid), so it is the less fitted copy and gives
the setup more playing time. One copy only (WB3 contains WB1).

## Supervisor sign-off — WB1
- **What changed:** one extra sensor. The parent shorts the first new low of the day between 11:30 and 14:00 when the
  stock is >= 0.78 daily ATR below today's OPEN, selling volume dominates and most stocks are up. WB1 also requires the
  stock to be >= 1.3 daily ATRs below YESTERDAY'S CLOSE: a stock that is truly weak on the day, not a gap-up that has only
  faded from a high open.
- **Why:** 3 of the 5 worst live trades were gap-up fades or shallow day-drops (JD +1.15 ATR above the prior close, CCEP
  −0.59, TOST −0.80); over 2 years the 822 trades WB1 removes averaged −0.132R (train −0.120 / valid −0.140) and the 359 it
  keeps +0.090R (train +0.084 / valid +0.095); Welch t 2.92.
- **Overall before → after (costs in, LR8, Testing D cost filter):** 2-year −0.039 → **+0.090R** (w/o best day −0.055 →
  +0.055; worst day −9.58 → −8.72R; win 46.5 → 51.5%; avg win / loss +0.954 / −0.903 → +1.091 / −0.973; median hold 111 →
  73 min; total R −45.7 → +32.5). Replay +0.044 → **+0.175R** (w/o best day −0.132 → +0.080; worst day −4.88 → −3.30R;
  total 3.8 → 7.2R). Train −0.025 → +0.084R, valid −0.048 → +0.095R. W/o its best month +0.025R. Paired by day vs the
  parent: +0.181R/day t 1.90 (2y), +0.223 t 0.33 (replay).
- **Each family (remedy rule):** day type up −0.123 → −0.118R, flat −0.051 → +0.126, down +0.474 → +0.864; entry time
  11:30-12:00 +0.011 → +0.186, 12:30-13:00 −0.045 → +0.058, 13:00-13:30 −0.031 → +0.250, 13:30-14:00 −0.207 → −0.141;
  price < $50 −0.160 → +0.123, $50-150 +0.005 → +0.190, $150-400 −0.031 → +0.106. **Where it gives a little back:**
  12:00-12:30 entries +0.022 → +0.013R; names above $400 −0.117 → −0.149R (68 trades); up days stay negative (−0.118R —
  the setup still loses on strong up days); trades −70% (1,180 → 359; 5.1 → 2.5 per traded session, 230 → 145 traded
  sessions). On the 21 live trades it keeps 8 at +0.910R (+7.28R) and skips 13 at +0.052R (+0.68R), including 2 of the 5 best
  (SU 10-27 +1.49R, DKS 11-03 +0.84R).
- **Honest ceiling:** +0.090R on 359 trades is a modest edge after costs; the paired-by-day gain (t 1.90) is under the
  configs-counted bar (3.03) — reported, not a pass hurdle. It keeps FISV-type late entries (13:30-14:00 still −0.141R:
  WB2's cut would remove them, at the cost of the valid-period gain). Borrow, halts and earnings days are not modelled.
- **Signed off:** PASS, recommended for a testing account (plan below). Owner decides any On Deck / Primary step.

## Configurations counted: 98
Parent + 44 one-part configs (screen1.csv) + 25 one-part neighbours / combos (screen2.csv) + 28 WB1 threshold points and
WB1-based combos (screen3.csv). WB1 / WB2 / WB3 are among them. Bar max(1.5, sqrt(2 ln 98)) = **3.03** (reported, not a
pass hurdle). Paired by day vs the parent: WB1 +0.181R/day t 1.90 (2y), +0.223 t 0.33 (replay); WB2 +0.105 t 1.80 / +0.395
t 1.15; WB3 +0.161 t 1.49 / +0.441 t 0.62 — none clears the bar.

**Every failure** (2-year avg R vs parent −0.039; replay vs +0.044; why it fails):
- Exhaust: stop 1.25R −0.086 / +0.011 (worst day −47R); stop 0.75R −0.093 / −0.010; 1R 0.20 ATR −0.057 / −0.013; 1R 0.30
  ATR −0.046 / +0.033; no trail (hold) −0.086 / +0.021; trail after +0.5R −0.046 / +0.044; trail 0.5R −0.025 / +0.007
  (replay); trail 1.5R after 1.5R −0.068; target 2R −0.033 / +0.035 (replay); target 1.5R −0.037 / +0.029; breakeven +0.5R
  −0.060; max hold 120 −0.032 / +0.037; exit at 60 min if MFE < 0.3R −0.038 / +0.006; fill 2 min later −0.047 / −0.024.
- Timer: start 11:00 −0.026 / −0.011; start 12:00 −0.067; end 14:30 −0.071 / +0.018.
- Sensors: flow3 <= −0.25 −0.049 / +0.036; fromOpen <= −1.0 −0.060 / −0.114; fromOpen <= −0.6 −0.067; from_pc <= −0.8
  −0.034 (2y) — below the plateau; volume ratio <= 1.0 +0.019 / +0.041 (replay lower, w/o best day −0.104); below VWAP 0.5
  ATR −0.019 / +0.003; below prior-day low −0.057 / +0.006; RSI(7) >= 20 −0.010 / −0.181; day range <= 1.5 ATR −0.046 /
  +0.033; gap <= 0 +0.009 / +0.116 and ATR% >= 2.5 −0.017 / +0.105 (both: replay worst day −6.25R vs −4.88R, > 10% worse);
  rvol >= 1.5: 1 trade.
- Gates / intake / caps (market state after 09:50): breadth gate off −0.147 / +0.039; breadth > 0.4 −0.110; > 0.6 −0.064 /
  −0.166; SPY since 09:50 <= 0 −0.006 / +0.258 (replay w/o best day −0.541); <= +0.3% −0.035 / −0.060; >= 0 −0.057 /
  −0.080; ADV >= $100M −0.048 (worst day −19R); $200M −0.051 / $300M −0.065 (2y); cost filter off −0.075 / +0.004; 2 lots
  per symbol −0.046 / +0.042; daily cap 5 −0.052.
- Passed but not spawned (smaller gains than WB1, or no live knob): ADV >= $250M −0.018 / +0.112; flow3 <= −0.50 −0.042 /
  +0.059 (meets by the close rule only; no gain); cost filter 0.10 −0.041 / +0.076 (meets); flat 15:00 −0.024 / +0.089; flat 15:30
  −0.028 / +0.079; flat 14:30 −0.028 / +0.071; end 13:15 −0.012 / +0.113; end 12:45 −0.002 / +0.142; ret12 <= −0.5% −0.034 /
  +0.070; gap <= +0.25 ATR −0.002 / +0.089 (replay worst −6.25R: fails); **per-setup daily cap 8 −0.019 / +0.216 and 12
  −0.031 / +0.057** (no live per-setup daily cap: backlog); WB1 threshold points −1.1 +0.042 / +0.084, −1.2 +0.071 / +0.114,
  −1.4 +0.124 / +0.106 (replay w/o best day −0.035: fails), −1.5 +0.102 / +0.185, −1.75 +0.065 / +0.093, −2.0 +0.021;
  combos on the parent: end 13:00 + ADV 250M +0.017 / +0.266, end 13:00 + daily cap 8 +0.007 / +0.219, end 13:00 + flat
  15:00 +0.011 / +0.191, end 13:00 + from_pc −1.0 +0.017 / +0.186, end 13:00 + gap <= 0 +0.029 / +0.244; combos on WB1:
  + end 13:00 = WB3, + end 13:15 +0.114 / +0.214, + daily cap 8 +0.113 / +0.277 (best whole-package candidate, needs a
  per-setup daily cap), + end 13:00 + daily cap 8 +0.139 / +0.403, + ADV 250M +0.104 / +0.282 (204 trades), + volume ratio
  <= 1.0 +0.210 / +0.258 (197 / 19 trades, replay w/o best day +0.062), + flat 15:00 +0.074 / +0.089 (fails replay), +
  flow3 −0.5 +0.065 / +0.170, + cost filter 0.10 +0.028 / +0.207, + trail 0.5R +0.059 / +0.034 (fails replay), + breadth
  off −0.139 / +0.102 (fails), + breadth > 0.4 −0.060 (fails), + fromOpen −0.6 +0.076 / +0.101, + start 11:00 +0.094 /
  +0.165 (w/o best day +0.001), + end 14:30 +0.056 / +0.138, + stop 1.25R −0.086 (fails), + target 2R +0.092 / +0.110, +
  2 lots +0.069 / +0.192, + ATR% >= 2.5 +0.065 / +0.210.

## The tests (identical for parent and copies)
- **Replay of the live sessions:** every session of the live window 2026-10-26..11-13 (15 sessions: Gen 10-26..11-11,
  Testing 2 temporarily 11-09/11-10, Testing D from 11-12). Read-only SIP GETs: daily bars and 5-minute bars for the
  universe file's 2,593 names with ADV >= $20M (adv20 / ATR(14) as live priors; breadth_open per 5-minute bucket by the
  lab_context rules), 1-minute bars 10-14..11-13 for the 1,272 names with ADV >= $100M that fell >= 0.4 ATR under their
  open on some replay day. Lab frames as live (mcf.report.engine.lab_frame + apply_daily: daily ATR set before the
  ATR-scaled extra features, as setups.py does), the module's indicator code (arena compute, context=False). Parity: all
  21 live trades reproduced (20 on the same bar); the copies' own modules give exactly the harness's signals.
- **2-year backtest:** research/history2y open months 2024-10 and 2025-03..2026-10-16 (230 traded sessions; the locked
  block 2024-11-01..2025-02-28 is never read), the lab frames with their context table (breadth_open), 1-minute paths from
  data/cache_hist/1Min.
- **Engine (code/sim.py):** first qualifying 5-minute bar per symbol-day (refire false), ADV >= $150M, price >= $5, the
  Testing D cost filter (max_stop_cost_r 0.15); short at the open of the 1-minute bar starting 1 minute after the signal
  bar closes; stop = signal close + 1R (1R = 0.25 x daily ATR), no target, trail 1R behind the best low once +1R, flat at
  15:55; stop checked first in each minute. LR8 costs (1c + 1 bp x time-of-day multiplier + 1 bp + CAT + SEC fee + TAF on
  the short sale; stop exit 1c + 1 bp + max(2c, 4 bp)). R = net P/L / |fill − stop| (live R definition).
- Not modelled (same for parent and copies): borrow / ETB, halts, spreads, earnings blackout (file not in this checkout),
  per-setup / account caps.

## Ready to deploy after the close (plan — NOT applied)
1. After 16:00 ET (setup-freeze), on a branch: add `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB1`
   to **Testing E** (`config/account_testinge.yaml`; not Testing D, where the parent runs — twins rule) from the stub
   `research/workbench/GEN-261026-03-.../GEN-261026-03-...-WB1.yaml` (enabled: true, module
   `research/workbench/GEN-261026-03-.../modules/GEN-261026-03-...-WB1.py`, context breadth_open, min_adv 150M, window
   1130-1400, refire false, scale_out_r null, geom holdtr from the module), placed **first in `live.setup_order`** (ahead of
   the ROT1 spotlight setups). Testing E has the same 0.15R cost filter the tests used.
2. Display name in `config/setup_names.yaml`: "Generated: Lunch New-Low Short (selling) — WB1: down >= 1.3 ATR on the day".
3. Ledger entry in `research/ledger.jsonl` (Workbench copy added; parent unchanged in Testing D), regenerate
   `docs/live/assignments.json` (`python -m mcf.report.assignments`) in the same commit, `python -m mcf.research.ledger
   check`, `pytest -q`, PR with setup-freeze passing.
4. The parent stays in Testing D, unchanged, and on the leaderboard. Review WB1 next to the parent after ~10 sessions
   (with the one-big-day check).

## Files
`DIAGNOSIS.md`; `..._engine.png`; trade charts `..._worst1..5_*.png`, `..._best1..5_*.png`; `..._wb1_frompc_curve.png`;
`variants.jsonl`; stubs `...-WB1/2/3.yaml` + `modules/`; `screen1-3.csv`, `results_final.csv`; code in `code/` (common,
cand2y, fetch_replay, build_replay, paths, sim, ana, exp + e1-e3.json, parity, modparity, final, charts, make_variants; run
outputs `*_out.txt`).
