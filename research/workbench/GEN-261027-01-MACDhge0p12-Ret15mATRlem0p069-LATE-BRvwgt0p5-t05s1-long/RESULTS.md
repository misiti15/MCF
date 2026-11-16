# Workbench results: Generated: Late Pullback Buy (MACD rising) `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long` (Testing E; LONG)
Mechanic, 2026-11-16 (Workbench batch; research files only, no config touched, nothing deployed).
Educational only — not financial advice.

**Few live trades (16 in 6 sessions, 14 of them from the Setup Generator account with $510 lots and no cost filter):
this verdict leans on the 2-year backtest, and says so.** The replay of the 14 live-window sessions holds 83 parent
trades on 7 traded sessions (37 for the recommended copy, 5 sessions), so on its own it proves little; it is reported
because the pass rule needs it, and it points the same way.

## Verdict (copies table)
| Copy | Change | Replay avg R (parent +0.122) | 2-year avg R (parent +0.032) | Avg R w/o best day (replay / 2y; parent +0.127 / +0.002) | Worst day R (replay / 2y; parent −3.81 / −75.3) | Trades (replay / 2y; parent 83 / 5,018) | Verdict |
|---|---|---|---|---|---|---|---|
| `...-WB1` | P5 window end 15:00 → 14:30 | +0.186 | +0.086 | +0.163 / +0.041 | −4.19 / −77.5 | 58 / 3,586 | PASS (narrow: replay worst day 10% deeper) |
| `...-WB2` | P2 ADV floor $20M → $100M | +0.180 | +0.046 | +0.153 / +0.019 | −2.51 / −50.3 | 64 / 3,790 | PASS |
| `...-WB3` | new gate P11b: breadth change since 09:50 <= +0.20 | +0.191 | +0.067 | +0.264 / +0.025 | +0.81 / −56.4 | 69 / 3,162 | PASS |
| `...-WB4` | WB1 + WB3 | +0.313 | +0.137 | +0.394 / +0.098 | +0.59 / −13.9 | 46 / 2,293 | PASS |
| `...-WB5` | WB1 + WB2 + WB3 | **+0.366** | **+0.161** | **+0.401 / +0.131** | **+0.45 / −12.6** | 37 / 1,744 | **PASS — recommended** |

Pass rule (RULES.md, clarification 2026-11-16): copy meets or exceeds the parent's avg R after costs in BOTH tests and
is not worse on avg R w/o best day / worst day by more than 0.02R / 10%. All five clear it; WB1 only just (replay worst
day −4.19 vs −3.81R = 9.97% deeper). WB4 and WB5 beat the parent on every number in both tests. The parent's live record
is not used in the decision.

## Supervisor sign-off — WB5
- **What changed (three parts, each tested alone first):** (1) P5 the entry window closes at 14:30 instead of 15:00;
  (2) P2 only names with a 20-day average dollar volume of at least $100M (was $20M); (3) new gate P11b: skip the
  afternoon when the share of stocks above VWAP has already risen more than +0.20 since the 09:50 bar (a broad
  rally / squeeze afternoon; market state measured after 09:50 per the owner rule). Sensors (P9/P10/P11), exits and
  geometry are unchanged.
- **Why:** over 2 years the parent's trades after 14:30 average −0.10R (both halves negative), names under $100M
  −0.01R (valid −0.07R), and the 0.2-0.3 breadth-expansion afternoons −0.20R with 37% stop-outs. In the live record the
  thin names (ZYME $15M, GUSH $21M, SMCIP $9M) and the broad-afternoon entries were among the worst trades. The 3,274
  trades WB5 removes averaged −0.032R (valid −0.097R); the 1,744 it keeps +0.161R (valid +0.191R).
- **Overall before → after (costs in, LR8):** 2-year +0.032 → **+0.161R** (train +0.051 → +0.136, valid +0.008 →
  +0.191; w/o best day +0.002 → +0.131; worst day −75.3 → −12.6R; best-day share 93% → 39%; win 67.8 → 78.6%; avg win /
  loss +0.450 / −0.846 → +0.413 / −0.767; median hold 17 → 14 min; total R 161 → 281 on 65% fewer trades). Replay
  +0.122 → **+0.366R** (w/o best day +0.127 → +0.401; worst day −3.81 → +0.45R; win 73.5 → 89.2%; total R 10.1 → 13.5).
- **Robustness:** without April 2025 (35% of the parent's trades): +0.001 → +0.147R. With a 20-trades-per-day cap
  (rough stand-in for live lot / account caps): parent −0.050R → WB5 +0.038R — the parent's "typical day" is negative,
  the copy's is positive. Dropping the 5 best and 5 worst days: −0.022 → +0.034R. Neighbours all beat the parent:
  window end 14:25 / 14:35 / 14:40 (with B) +0.142 / +0.105 / +0.095 (2y); B at 0.15 / 0.25 +0.157 / +0.084; ADV
  $50M / $75M / $150M (with W+B) +0.143 / +0.147 / +0.169. B is the steepest part: above 0.25 the gain falls fast
  (B 0.30 + W: +0.048), so 0.20 is not a loose knob.
- **Each day type (remedy rule; it is a long, so up days matter):** up days +0.041 → **+0.136R** (2,900 → 894 trades),
  flat −0.054 → +0.002R, down +0.079 → +0.261R — all better; train and valid both better.
- **Where it gives a little back:** trades: 5,018 → 1,744 over 2 years (about 6 per traded session, 162 of 439 sessions;
  parent 277), 83 → 37 in the replay (5 of 14 sessions; 16 of the 37 on 11-04, best-day share 38%). Live: of the 16
  live trades WB5 would have kept only 3 (NYT −1.12, GDXU +0.35, GDXJ +0.38 = −0.13R avg) and skipped 13 at +0.26R,
  including the two late winners TTD / CBRS whose +1R came from fills 28-58 bps below the signal close. The live sample
  disagrees; it is 16 trades.
- **Honest ceiling:** paired by day vs the parent the copy adds +0.27R per session over 2 years (t 0.59) and +0.24R per
  session in the replay (t 0.71): more R per trade and per session, not a proven daily edge. The 2-year record still
  leans on spring 2025 and June-July 2026 (best days 2025-04-10 +110R, 2026-06-11 +98R, 2026-07-29 +59R). Breadth is
  computed on the 1,226-name lab universe here; live it comes from the poll universe (larger), so the 0.20 line may sit
  slightly differently live. The earnings blackout (P4) could not be modelled (calendar file not on this machine) — same
  for parent and copies.
- **Signed off:** PASS, recommended for a testing account (plan below). Owner decides any On Deck / Primary step.

## Configurations counted: 106
Parent + 51 one-part configs (screen_e1.csv) + 29 combos (screen_e2.csv) + 19 neighbours / layers on WB4-WB5
(screen_e3.csv) + 6 day-cap sensitivity runs (parent, WB1..WB5 at 20 trades/day). WB1..WB5 are among them. Bar
max(1.5, sqrt(2 ln 106)) = **3.05** (reported, not a pass hurdle). Paired by day vs the parent: WB1 +0.332R/day t 1.94
(2y), +0.046 t 0.24 (replay); WB2 +0.029 t 0.16 / +0.098 t 0.57; WB3 +0.115 t 0.27 / +0.216 t 0.77; WB4 +0.351 t 0.78 /
+0.303 t 0.91; WB5 +0.272 t 0.59 / +0.243 t 0.71 — none clears the bar. Per trade (kept vs removed, 2-year, ignores day
clustering): WB5 Welch t 9.7, WB4 9.3.

**Every failure** (2-year avg R vs parent +0.032 / replay vs +0.122; why it fails):
- Exhaust: stop 0.75R +0.047 / +0.153 but valid −0.042 and 2y w/o best day −0.011; stop 1.25R +0.037 / +0.109; 1.5R
  +0.031 / +0.081; target 0.4R +0.031; 0.6R +0.026 (2y worst day −135R); 0.75R +0.009; 1R 0.20 ATR +0.007; 0.30 ATR
  +0.018; max hold 30 +0.013 / 60 +0.014; flat 15:30 +0.022; breakeven at +0.3R +0.034 / +0.079; exit at 30 min if
  MFE < 0.2R +0.015 / +0.077.
- Timer: window 14:05-15:00 +0.052 / +0.132 (replay w/o best day +0.103); 13:30-15:00 +0.052 / +0.091; 14:00-14:45
  +0.050 / +0.152 (w/o best day +0.106).
- Sensors: macd_hist >= 0.10 +0.021; 0.15 +0.064 / +0.097; 0.20 +0.069 / +0.056; ret3_atr <= −0.06 +0.026; −0.08
  +0.040 / +0.079; −0.10 +0.057 / +0.089.
- Gates: breadth > 0.4 +0.005 (worst day −229R); > 0.6 +0.014; no breadth gate −0.009 (worst day −243R); breadth
  0.5-0.85 +0.021; SPY since 09:50 <= +1.2% +0.022; >= −0.3% +0.026 / +0.099; B alone at 0.25 +0.032 / +0.122 (no better).
- Intake / cost: price >= $10 +0.032 (no change); ADV >= $50M +0.036 / +0.122 (w/o best day +0.121, about equal); cost
  filter 0.10R +0.047 / +0.130 (replay w/o best day +0.096); 0.05R +0.057 / +0.112; no cost filter +0.012.
- New layers (one at a time): SMA20 slope >= 0.12 / 0.25 / 0.37 +0.075 / +0.089 / +0.105 (2y) but replay +0.103 /
  +0.117 / +0.087 with w/o best day +0.073 / +0.073 / +0.014; macdPct >= 0 +0.077 / +0.121 (w/o best day +0.082);
  emaDiff >= 0.1 +0.072 / +0.066; vwap_atr >= −0.17 +0.065 / +0.107; day position >= 0.27 +0.061 / +0.013; ADX(7) <= 81
  +0.056 / +0.133 (replay worst day −4.20); ADX(7) >= 49 +0.051 / +0.074; eff6 <= 0.40 +0.054 / +0.042; RVOL <= 1.0
  +0.028; rsi5 <= 64 +0.038 / +0.171 (2y w/o best day +0.005, about equal).
- Passed but not spawned (weaker than WB5 or one test only): daily ATR >= 3.5% +0.052 / +0.160; dist from high <= 1.08
  ATR +0.061 / +0.182; lower wick <= 0.38 +0.055 / +0.123; combos W+A +0.102 / +0.254, W+T +0.106 / +0.233, W+H +0.127 /
  +0.251, A+B +0.084 / +0.242, B+T +0.090 / +0.186, W+B+T +0.160 / +0.288, W+A+B+T +0.171 / +0.342 (w/o best day 2y
  +0.135, replay +0.379, 32 / 1,408 trades), W+A+B+H +0.193 / +0.364 (23 replay trades), W+A+B+T+H +0.202 / +0.341
  (20), W+B+S(slope 0.25) +0.184 / +0.277 (18), W+A+B+S +0.209 / +0.255 (14; replay w/o best day +0.149); W+B + stop
  0.75R +0.132 / +0.332 (valid +0.081, worst day −18R); W+B + target 0.6R +0.149 / +0.337 (replay worst day −1.22R);
  W+B + max hold 60 +0.109; W+B + SPY >= −0.3% +0.090 (train +0.020); W+B + breadth > 0.55 +0.109; W+B + macd_hist >=
  0.15 +0.179 / +0.278; W+A+B + cost filter 0.10R +0.165 / +0.335. WB5 is the simplest copy that is better in both tests
  on every number; the extra layers raise the 2-year figure further but thin the replay to 14-23 trades.

## The tests (identical for parent and copies)
- **Replay of the live sessions:** every session of the setup's live window 2026-10-27..11-13 (14 sessions). Lab
  universe (research/lab_symbols.txt, 1,226 names — the 2-year frames' universe; 8 of the 16 live symbols are outside it).
  10-27..11-04 from the research/history2y frames; 11-05..11-13 rebuilt with the SAME pipeline (build_frames: cache +
  read-only SIP GET of 1-minute bars → resample 5min → mcf.research.setup_lab.build; adv20 from the daily table; context
  via mcf.strategies.lab_context.context_from_frames). Parity: the rebuilt 11-03 / 11-04 frames match the history2y frames
  exactly (close, atr_d, macd_hist, ret3_atr, breadth, SPY since 09:50 identical; same 38 parent signals).
- **2-year backtest:** 2024-10-01..2026-10-26 (ends before the live window), open months only; **locked block
  2024-11-01..2025-02-28 never read** (frames through lib.py; 1-minute rows in the block dropped on read; assert on the
  candidates). Train = ..2025-12-31, valid = 2026-01-01..10-26. Parity with the generator's screen: train 3,466 parent
  signals here vs 3,155 in the generator run — the gap is the earnings blackout (the generator removed it; the calendar
  file is not on this machine).
- **Module parity:** each copy's own `mask()` reproduces the engine's selection exactly (2025-04 / 2026-06 / 2026-10:
  2049 / 597 / 294 parent signals, WB5 687 / 409 / 40; code/parity.py).
- Engine: module conditions on the 5-minute bar close (arena compute, context=False; breadth = lab context column),
  adv20 floor, price >= $5, account cost filter P17 (stop-exit cost <= 0.15R, live runner formula), first qualifying bar
  per symbol-day (refire false). Fill = open of the 1-minute bar 1 minute after the signal bar closes. Stop / target from
  the signal-bar close (as LabStrategy), 1R = 0.25 x daily ATR, target +0.5R, stop 1R; same-minute stop + target = stop
  first; flat 15:55. R = net P/L / |fill − stop| (the live R definition). Isolated: no lot caps / latch / quote checks
  (identical for all; the 20/day cap is the sensitivity above).
- **Costs in (LR8 production model)**, every config alike: entry (1c + 1 bp) x time-of-day multiplier + 1 bp cushion;
  target filled at the limit; stop (1c + 1 bp) + max(2c, 4 bp); market / time exits (1c + 1 bp) + max(1c, 1 bp);
  SEC $20.60/M on the sale, TAF $0.000195/sh, CAT $0.00005/sh/side.
- Code: `code/` (common, cand, fetch_replay, build_replay, paths, sim, exp + e1/e2/e3.json, ana0-ana3, live_off,
  live_feat, mkvar, parity, final; scratch paths inside). Numbers: `results_final.csv`, `screen_e1.csv`..`screen_e3.csv`.

## Side by side (avg R after costs)
**Replay of the live sessions, 2026-10-27..11-13 (14 sessions, lab universe)**

| Copy | Trades | Sessions traded | Win % | Avg R | w/o best day | w/o worst day | Total R | Worst day R | Best-day share | Avg win / loss | Median hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 83 | 7 | 73.5 | +0.122 | +0.127 | +0.194 | +10.1 | −3.81 | 39% | +0.442 / −0.764 | 35 min |
| WB1 window 14:00-14:30 | 58 | 7 | 77.6 | +0.186 | +0.163 | +0.312 | +10.8 | −4.19 | 46% | +0.461 / −0.768 | 36 min |
| WB2 ADV >= $100M | 64 | 7 | 76.6 | +0.180 | +0.153 | +0.246 | +11.5 | −2.51 | 48% | +0.453 / −0.712 | 36 min |
| WB3 breadth chg <= +0.20 | 69 | 5 | 76.8 | +0.191 | +0.264 | +0.184 | +13.2 | +0.81 | 30% | +0.456 / −0.688 | 35 min |
| WB4 = WB1+WB3 | 46 | 5 | 84.8 | +0.313 | +0.394 | +0.306 | +14.4 | +0.59 | 34% | +0.476 / −0.597 | 38 min |
| WB5 = WB1+WB2+WB3 | 37 | 5 | 89.2 | +0.366 | +0.401 | +0.364 | +13.5 | +0.45 | 38% | +0.487 / −0.629 | 38 min |

**2-year backtest, 2024-10..2026-10-26 (locked block excluded; 439 sessions)**

| Copy | Trades | Sessions traded | Win % | Avg R | w/o best day | w/o worst day | Total R | Worst day R | Best-day share | Avg win / loss | Median hold | Train / valid avg R (n) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 5,018 | 277 | 67.8 | +0.032 | +0.002 | +0.052 | +161 | −75.3 | 93% | +0.450 / −0.846 | 17 min | +0.051 (2,828) / +0.008 (2,190) |
| WB1 | 3,586 | 249 | 72.1 | +0.086 | +0.041 | +0.122 | +307 | −77.5 | 57% | +0.456 / −0.873 | 13 min | +0.080 (2,203) / +0.094 (1,383) |
| WB2 | 3,790 | 266 | 68.8 | +0.046 | +0.019 | +0.061 | +174 | −50.3 | 63% | +0.442 / −0.827 | 18 min | +0.065 (2,037) / +0.024 (1,753) |
| WB3 | 3,162 | 216 | 71.1 | +0.067 | +0.025 | +0.088 | +212 | −56.4 | 70% | +0.413 / −0.787 | 18 min | +0.103 (1,575) / +0.031 (1,587) |
| WB4 | 2,293 | 187 | 77.1 | +0.137 | +0.098 | +0.150 | +315 | −13.9 | 47% | +0.411 / −0.781 | 13 min | +0.119 (1,304) / +0.162 (989) |
| WB5 | 1,744 | 162 | 78.6 | +0.161 | +0.131 | +0.172 | +281 | −12.6 | 39% | +0.413 / −0.767 | 14 min | +0.136 (950) / +0.191 (794) |

Day type (2-year, end-of-day session regime, diagnostic only): parent up +0.041 / flat −0.054 / down +0.079;
WB1 +0.104 / −0.059 / +0.130; WB2 +0.051 / −0.031 / +0.094; WB3 +0.034 / −0.057 / +0.216; WB4 +0.115 / −0.054 / +0.258;
WB5 +0.136 / +0.002 / +0.261. Without April 2025: parent +0.001, WB1 +0.060, WB2 +0.018, WB3 +0.022, WB4 +0.111,
WB5 +0.147. Day cap 20: parent −0.050, WB1 −0.040, WB2 −0.038, WB3 −0.018, WB4 +0.023, WB5 +0.038.

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session (2026-11-17). One
copy only: **WB5** (WB4 is contained in it; running both would put near-twins side by side). The parent stays in
Testing E, unchanged.
Account: **Testing D** (`config/account_testingd.yaml`) — a testing account, not the parent's (Testing E). Testing D
also has today's CWT14 WB5 plan (normal priority); both are workbench copies, so the main session orders them (this
one at the top per RULES 5, the CWT14 copy as its plan says). Twin check: `-WB5` is not the parent's key; different
account anyway.
1. `config/account_testingd.yaml`, under `strategies:` add
   ```yaml
   GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB5:
     # Workbench copy of GEN-261027-01-...-long (Testing E), Mechanic 2026-11-16: window 14:00-14:30 + ADV >= $100M +
     # breadth change since 09:50 <= +0.20; research/workbench/GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long/RESULTS.md.
     # Effective session 2026-11-17.
     enabled: true
     type: lab
     module: research/workbench/GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long/modules/GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB5.py
     context: [breadth]
     min_adv: 100000000
     window: [1400, 1430]
     refire: false
     scale_out_r: null
     tags: [workbench, "parent:GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long", generated]
   ```
   and put it FIRST in `live.setup_order` (RULES 5).
2. `config/setup_names.yaml`: `...-WB5: "Generated: Late Pullback Buy (MACD rising) — WB5: 14:00-14:30, $100M ADV, breadth gate"`.
3. `research/ledger.jsonl`: one entry (type move/add, effective 2026-11-17, "Workbench WB5 of GEN-261027-01 to Testing D,
   first in order; parent unchanged in Testing E"), then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit), `pytest -q`, PR with
   the setup-freeze check passing (after 16:00 ET).
5. Review after ~10 traded sessions alongside the parent (same sessions), with the one-big-day check.

Educational only — not financial advice.
