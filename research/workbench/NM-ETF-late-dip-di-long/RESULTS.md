# Workbench results: Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` (Primary, TEAM-6; LONG)
Mechanic, 2026-11-16 (Workbench batch; built 13:10-13:45 ET during market hours: research files only, no config touched,
nothing deployed). Educational only — not financial advice.

**Few live trades (21 in 11 sessions): this verdict leans on the 2-year backtest, and says so.** The replay of the live
sessions holds only 30 parent trades (9 for the recommended copy), so on its own it proves nothing; it is reported because
the pass rule needs it, and it points the same way.

## Verdict (copies table)
| Copy | Change | Replay avg R (parent +0.331) | 2-year avg R (parent +0.125) | Avg R w/o best day (replay / 2y; parent +0.236 / +0.091) | Worst day R (replay / 2y; parent −0.82 / −6.97) | Trades (replay / 2y; parent 30 / 480) | Verdict |
|---|---|---|---|---|---|---|---|
| `NM-ETF-late-dip-di-long-WB1` | new sensor P10b: 60-min return (incl. the dip) >= +0.5% | **+0.568** | **+0.220** | +0.340 / +0.163 | −0.09 / −3.01 | 9 / 263 | **PASS — recommended** |
| `NM-ETF-late-dip-di-long-WB2` | P10 15-min dip ret3 <= −0.90% (was −0.80%) | +0.401 | +0.175 | +0.300 / +0.127 | −0.17 / −5.88 | 20 / 355 | PASS (not deployed: weaker) |
| `NM-ETF-late-dip-di-long-WB3` | WB1 + WB2 (combo, own config) | +0.609 | +0.269 | +0.312 / +0.192 | −0.09 / −3.01 | 7 / 200 | PASS (not deployed: see below) |

Pass rule (RULES.md, clarification 2026-11-16): copy meets or exceeds the parent's avg R after costs in BOTH tests and is
not worse on avg R w/o best day / worst day by more than 0.02R / 10%. All three copies clear it with room; all are
better than the parent on every one of those numbers in both tests. Parent's live record not used in the decision.

**Why WB1 and not WB3:** WB3 has the higher 2-year avg R (+0.269 vs +0.220), but its extra gain comes from the ret3 cut,
which does not hold in the replay without its best day (+0.312 vs WB1 +0.340), and it keeps only 200 / 7 trades (0.47 per
session) against WB1's 263 / 9. WB1 is one new sensor with a smooth, monotone threshold curve
(`NM-ETF-late-dip-di-long_wb1_ret12_curve.png`), so it is the less fitted copy and gives the setup more playing time.
One copy only (WB3 contains WB1; running both would put near-twins side by side).

## Supervisor sign-off — WB1
- **What changed:** one extra sensor. The parent buys any sharp 15-minute dip in a volatile ETF between 14:00 and 15:00.
  WB1 buys it only when the ETF is still up at least +0.5% over the last 60 minutes, dip included: a pullback inside an
  up-hour, not the next leg of a falling hour.
- **Why:** 4 of the 5 live losers were dips that continued a falling hour (ret12 −0.71 / −2.12 / −0.86 / −2.01%); over
  2 years the 217 trades WB1 removes averaged +0.003R (valid −0.091R) and the 263 it keeps +0.220R (Welch t 4.0).
- **Overall before → after (costs in, LR8):** 2-year +0.125 → +0.220R (w/o best day +0.091 → +0.163; worst day −6.97 →
  −3.01R; win 71.9 → 77.9%; avg win / loss +0.423 / −0.636 → +0.461 / −0.632; median hold 30 → 14 min). Replay +0.331 →
  +0.568R (w/o best day +0.236 → +0.340; worst day −0.82 → −0.09R). Train +0.213 → +0.257R, valid +0.002 → +0.134R.
  Without April 2025 (the crash month that carried the parent): +0.060 → +0.143R.
- **Each family (remedy rule):** inverse ETFs +0.078 → +0.184R, non-inverse +0.147 → +0.234, 3x funds +0.092 → +0.161,
  1x +0.235 → +0.345; up days +0.244 → +0.351, down days +0.061 → +0.171 — all better. **Where it gives a little back:**
  flat days +0.093 → +0.054R (32 trades); total R: 2-year 60.1 → 57.8R on 45% fewer trades (train 59.9 → 47.0R, the April
  2025 crash days; valid 0.3 → 10.7R), replay 9.9 → 5.1R. On the 21 live trades it would have kept 6 at +0.395R (+2.37R)
  and skipped 15 at +0.277R (+4.16R), including 2 of the 5 best (TECL 11-05, TZA 10-22). Trades per session about
  1.1 → 0.6 (2-year).
- **Honest ceiling:** the parent's valid-period record is about zero after costs (+0.002R); WB1 turns it positive
  (+0.134R on 80 trades), but that is still a small sample and the 2-year paired-by-day difference vs the parent is
  −0.005R (t −0.19): the gain is per trade and per unit of risk, not more total R per session. Guild OBS-LATEDIP's "a lead
  at most" still stands for the parent; WB1 is the cross-sectional version that lead pointed to (which dips work).
- **Signed off:** PASS, recommended for a testing account (plan below). Owner decides any On Deck / Primary step.

## Configurations counted: 56
Parent + 34 one-part configs (screen1.csv) + 14 combos / combo neighbours (screen2.csv) + 4 combo neighbours
(screen3.csv) + 2 extra threshold points on the WB1 curve (ret12 >= −0.5 / +1.5%) + WB1 / WB2 / WB3 are among them.
Bar max(1.5, sqrt(2 ln 56)) = **2.84** (reported, not a pass hurdle). Paired by day vs the parent (day totals, all
sessions): WB1 −0.005R/day t −0.19 (2y), −0.241 t −1.30 (replay); WB2 +0.004 t 0.24 / −0.096 t −0.94; WB3 −0.015 t −0.47 /
−0.284 t −1.55 — none clears the bar; they are negative or flat because the copies trade less, not because the kept trades
are worse. Per trade (kept vs removed, 2-year): WB1 t 4.0.

**Every failure** (2-year avg R vs parent +0.125; replay vs +0.331; why it fails):
- Exhaust: target 0.4R +0.123 / +0.280; 0.6R +0.129 / +0.320 (replay w/o best day −0.03, worst 2y −9.1R); 0.75R +0.083;
  stop 0.75R +0.182 / +0.447 but valid −0.003 and replay worst day −1.17R (43% worse); stop 1.25R +0.105; 1.5R +0.086;
  1R 0.20 ATR +0.150 / +0.319 (replay w/o best day −0.08); 1R 0.30 ATR +0.124 / +0.251; flat 15:45 +0.117; 15:30
  +0.118; max hold 60 +0.108, 45 +0.096; breakeven at +0.3R +0.092; lock +0.1R after +0.35R +0.094; exit at 45 min if
  MFE < 0.2R +0.118 / +0.361.
- Timer: window from 13:30 +0.041; window to 14:45 +0.131 / +0.236.
- Sensors: ret3 <= −0.70 +0.097; di >= 5 +0.122; no DI filter +0.056; ATR >= 3.0% +0.114; ATR >= 4.5% +0.093;
  RSI(7) <= 60 +0.180 / +0.159 (replay); day position >= 0.5 +0.173 / 0 replay trades.
- Intake: ADV >= $200M +0.112; no inverse ETFs +0.147 / +0.360 but valid +0.030 (no better) and 2y worst day −7.9R.
- Gates / caps (market state measured after 09:50): SPY since 09:50 >= 0 +0.213 / +0.315 (replay w/o best day −0.002);
  >= −0.25% +0.171 / +0.283; 5 trades per day cap +0.094; 2 lots per symbol +0.131 / +0.281.
- Passed but not spawned (smaller gains than WB1): ADX(7) >= 40 +0.136 / +0.443; above VWAP +0.200 / +0.565; ret12 >= 0
  +0.170 / +0.512; ret12 >= 0.25 / 0.75 / 1.0 (+0.192 / +0.232 / +0.265); combos WB1 + above VWAP +0.253 / +0.937 (4 replay
  trades), WB1 + SPY >= −0.25% +0.280 / +0.757 (5), WB1 + stop 0.75R +0.294 / +1.022 (valid +0.108 < WB1), WB1 + target 0.6R
  +0.208, WB1 + 2 lots +0.220, WB1 + window 13:30 +0.121 (fails), WB1 + ATR 3.0 +0.218, WB1 + ret3 −0.70 +0.173, WB1 without
  DI +0.154 (w/o best day +0.055, fails), WB1 + 45-min exit +0.195; WB3 neighbours (ret3 −0.85 / −1.00, ret12 0.25 / 0.75 on
  ret3 −0.90): +0.246 / +0.294 / +0.254 / +0.280 — WB3 sits on a smooth plateau.

## The tests (identical for parent and copies)
- **Replay of the live sessions:** every session of the live window 2026-10-19..11-13 (20 sessions). Read-only SIP GET of
  1-minute + daily bars for the module's 128 ETFs (+SPY/QQQ), lab frames built as live (mcf.report.engine.lab_frame +
  apply_daily: daily ATR(14) and prior levels from daily bars), adv20 from daily bars, the module's own indicator code
  (mcf.research.arena.indicators.compute, context=False). Parity: on 10-19..11-04 the rebuilt frames give the same 15
  signals as the research/history2y frames (+2 LABU signals the 2-year frames miss on adv20); each spawned module's own
  `mask()` reproduces the engine's selection exactly (30 / 9 / 20 / 7 of 30 / 9 / 20 / 7). Isolated (no caps / latch /
  quote checks), so it holds 30 trades vs 21 live.
- **2-year backtest:** 2024-10-01..2026-10-16 (ends before the live window), open months only; **locked block
  2024-11-01..2025-02-28 never read** (frames from the open directory; 1-minute rows in the block dropped on read; assert on
  the candidates). Train = ..2025-12-31, valid = 2026-01-01..10-16. Parity with the arena record: the module selection on
  the frames gives train 281 trades (+0.251R lab outcome) and valid 190 to 10-07 — the setup's documented counts.
- Engine: module conditions on the 5-minute bar close, adv20 >= $95M, price >= $5, the module's ETF list, first qualifying
  bar per symbol-day (refire false). Fill = open of the 1-minute bar 1 minute after the signal bar closes. Stop / target
  from the signal-bar close (as LabStrategy), 1R = 0.25 x daily ATR, target +0.5R, stop 1R; same-minute stop + target =
  stop first; flat 15:55. R = net P/L / |fill − stop| (the live R definition). 1-minute bars: data/cache_hist (2y), SIP
  fetch (replay).
- **Costs in (LR8 production model)**, every config alike: entry (1c + 1 bp) x time-of-day multiplier + 1 bp cushion;
  target filled at the limit; stop (1c + 1 bp) + max(2c, 4 bp); market / time exits (1c + 1 bp) + max(1c, 1 bp);
  SEC $20.60/M on the sale, TAF $0.000195/sh, CAT $0.00005/sh/side.
- Code: `code/` (common.py, sig2y.py, fetch_replay.py, paths.py, sim.py, ana.py, exp.py + e1/e2/e3.json, final.py,
  curve.py; scratch paths inside). Numbers: `results_final.csv`, `screen1.csv`..`screen3.csv`.

## Side by side (avg R after costs)
**Replay of the live sessions, 2026-10-19..11-13 (20 sessions)**

| Copy | Trades | Win % | Avg R | w/o best day | w/o worst day | Total R | Worst day R | Best-day share | Avg win / loss | Median hold |
|---|---|---|---|---|---|---|---|---|---|---|
| parent | 30 | 76.7 | +0.331 | +0.236 | +0.384 | +9.9 | −0.82 | 38% | +0.545 / −0.371 | 36 min |
| WB1 ret12 >= +0.5% | 9 | 88.9 | +0.568 | +0.340 | +0.651 | +5.1 | −0.09 | 47% | +0.651 / −0.092 | 54 min |
| WB2 ret3 <= −0.90% | 20 | 80.0 | +0.401 | +0.300 | +0.431 | +8.0 | −0.17 | 36% | +0.547 / −0.181 | 45 min |
| WB3 = WB1 + WB2 | 7 | 85.7 | +0.609 | +0.312 | +0.726 | +4.3 | −0.09 | 56% | +0.726 / −0.092 | 78 min |

**2-year backtest, 2024-10..2026-10-16 (locked block excluded; 156 parent trading sessions)**

| Copy | Trades | Win % | Avg R | w/o best day | w/o worst day | Total R | Worst day R | Best-day share | Avg win / loss | Median hold | Train / valid avg R (n) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 480 | 71.9 | +0.125 | +0.091 | +0.145 | +60.1 | −6.97 | 31% | +0.423 / −0.636 | 30 min | +0.213 (281) / +0.002 (199) |
| WB1 | 263 | 77.9 | +0.220 | +0.163 | +0.235 | +57.8 | −3.01 | 32% | +0.461 / −0.632 | 14 min | +0.257 (183) / +0.134 (80) |
| WB2 | 355 | 74.6 | +0.175 | +0.127 | +0.200 | +62.0 | −5.88 | 32% | +0.452 / −0.641 | 30 min | +0.256 (213) / +0.053 (142) |
| WB3 | 200 | 80.0 | +0.269 | +0.192 | +0.290 | +53.9 | −3.01 | 37% | +0.493 / −0.627 | 13 min | +0.297 (145) / +0.195 (55) |

Day type (2-year, end-of-day session regime, diagnostic only): parent up +0.244 / flat +0.093 / down +0.061;
WB1 +0.351 / +0.054 / +0.171; WB2 +0.278 / +0.164 / +0.111; WB3 +0.389 / +0.108 / +0.217. Without April 2025: parent
+0.060, WB1 +0.143, WB2 +0.100, WB3 +0.186.

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session (2026-11-17). One
copy only: **WB1**. The parent stays in Primary (TEAM-6), unchanged.
Account: **Testing B** (`config/account_explore1.yaml`) — a testing account, not the parent's (Primary); not Testing A
(today's L3-WB4 plan goes first there), not Testing C (Live Lab, the parent's former home), not On Deck. Twin check:
`twin_key` only strips `-FD`, so `...-WB1` is not the parent's key; different account anyway.
1. `config/account_explore1.yaml`, under `strategies:` add
   ```yaml
   NM-ETF-late-dip-di-long-WB1:
     # Workbench copy of NM-ETF-late-dip-di-long (Primary), Mechanic 2026-11-16: + ret12 >= +0.5% (dip inside an up-hour);
     # research/workbench/NM-ETF-late-dip-di-long/RESULTS.md. Effective session 2026-11-17.
     enabled: true
     type: lab
     module: research/workbench/NM-ETF-late-dip-di-long/modules/NM-ETF-late-dip-di-long-WB1.py
     symbols: module
     min_adv: 95000000
     window: [1400, 1500]
     scale_out_r: null
     tags: [workbench, "parent:NM-ETF-late-dip-di-long", etf]
   ```
   and put `NM-ETF-late-dip-di-long-WB1` FIRST in `live.setup_order` (ahead of IDX1-qqq100-0955-TQQQ-hold).
2. `config/setup_names.yaml`: `NM-ETF-late-dip-di-long-WB1: {name: "Late-Day ETF Dip Buy — WB1: dip inside an up-hour", side: long, what: "14:00-15:00: buy a sharp 15-min dip in a volatile ETF only while it is still up 0.5%+ over the last hour (a pullback, not a falling hour)."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-nmetf-latedip-wb1`, effective 2026-11-17, title "Workbench copy
   NM-ETF-late-dip-di-long-WB1 added to Testing B, first in setup_order (Mechanic pass)", patch
   `{"strategies.NM-ETF-late-dip-di-long-WB1 (explore1)": [null, "added, enabled"], "live.setup_order (explore1)": ["...", "WB1 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5 (passes go to a testing account at once)";
   then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit), `pytest -q`, commit,
   push after 16:05 ET (setup-freeze).
