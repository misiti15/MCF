# Workbench results: Monday Weak-RS NS3 Short (near-miss) `NM-RWN5-ns3-mon-weakrs-short` (Testing D; SHORT)
Mechanic, 2026-11-16 (Workbench batch; research files only, no config touched, nothing deployed). Educational only — not
financial advice.

**Very few live trades (8 in 3 sessions, Mondays only): this verdict rests on the 2-year backtest, and says so.** The replay
of the live window (21 sessions 10-19..11-16; the parent trades only the 5 Mondays, 4 of them with trades) holds 51 parent
trades, and 48 of them fall on two Mondays (10-19, 11-02) — it is reported because the pass rule needs it, but it is thin.
The parent's live record (+0.54R on 8 trades) is not used in the decision; on the identical backtest the parent is +0.202R
per trade over 2 years (+0.117R without its best day, 2025-04-14 = 48% of total R).

## Verdict (copies table)
| Copy | Change | Replay avg R (parent +0.078) | 2-year avg R (parent +0.202) | Avg R w/o best day (replay / 2y; parent −0.038 / +0.117) | Worst day R (replay / 2y; parent −2.29 / −3.48) | Trades (replay / 2y; parent 51 / 248) | Verdict |
|---|---|---|---|---|---|---|---|
| `...-WB1` | new sensor P9b: reclaim-bar volume >= 0.45 x 20-bar avg | +0.217 | +0.279 | +0.113 / +0.198 | −1.12 / −3.48 | 35 / 195 | PASS (not deployed: in WB3) |
| `...-WB2` | P6/P14 window start 09:50 → 10:05 | +0.184 | +0.229 | +0.207 / +0.139 | −1.12 / −3.48 | 47 / 230 | PASS (not deployed: in WB3) |
| `...-WB3` | WB1 + WB2 (combo, own config) | **+0.258** | **+0.308** | +0.213 / +0.223 | −1.12 / −3.48 | 34 / 176 | **PASS — recommended** |

Pass rule (RULES.md, clarification 2026-11-16): the copy meets or exceeds the parent's avg R after costs in BOTH tests and is
not worse on avg R w/o best day / worst day by more than 0.02R / 10%. All three clear it; every copy is better than or equal to
the parent on each of those numbers in both tests (2-year worst day is the same session, 2026-01-05, −3.48R). Ids:
`NM-RWN5-ns3-mon-weakrs-short-WB1/2/3`. Paired by day vs the parent (difference not required to pass, reported): WB3 +0.050R
per Monday t 0.32 (2y), +0.959R t 1.35 (replay) — far below the configs-counted bar sqrt(2 ln 113) = 3.07, so this is a
refinement on thin evidence, not a proven edge.

**Why WB3:** it has the best avg R and w/o-best-day in both tests, and the whole 3 x 3 neighbourhood around it (start 10:00 /
10:05 / 10:10 x volume 0.35 / 0.45 / 0.55) beats the parent in both tests: 2-year +0.227..+0.308 (w/o best day
+0.157..+0.225), replay +0.161..+0.388 (w/o best day +0.100..+0.463). Both parts improve both 2-year halves.

## Supervisor sign-off — WB3
- **What changed:** two small entry parts. (1) A new sensor: the 5-minute bar that crosses back above VWAP must carry at least
  0.45x its 20-bar average volume — no dead-volume crosses. (2) The entry window opens at 10:05 instead of 09:50 — no shorts
  on the first three bars after 09:50, which are still the opening chop. Everything else (Monday, > 2% below the open, above
  the SMA50, weaker than SPY, t1s1, 1R = 0.25 ATR, $95M, cost filter 0.15R, 15:55 flat) is the parent's.
- **Why:** 2-year: entries 09:50-10:00 averaged −0.04R (38% stops); the lowest-volume reclaims +0.07R (valid half −0.27R).
  The 72 parent trades WB3 removes averaged −0.067R (train +0.069 / valid −0.293), the 176 it keeps +0.312R (train +0.289 /
  valid +0.338); Welch t 2.83.
- **Overall before → after (costs in, LR8, Testing D cost filter):** 2-year +0.202 → **+0.308R** (w/o best day +0.117 →
  +0.223; best-day share 48% → 35%; worst day −3.48 → −3.48R; win 64.1 → 68.8%; avg win / loss +0.860 / −0.972 → +0.882 /
  −0.954; median hold 53 → 53 min; total R 50.1 → 54.3 on 29% fewer trades). Train +0.216 → +0.266R, valid +0.185 →
  +0.356R. Without April 2025: +0.126 → +0.248R. Replay +0.078 → **+0.258R** (w/o best day −0.038 → +0.213; worst day
  −2.29 → −1.12R; total 4.0 → 8.8R).
- **Each family (remedy rule, 2-year):** day type down +0.388 → +0.458, flat +0.119 → +0.264, up +0.018 → +0.132R (all 3
  better); entry time 10:30-11:00 +0.199 → +0.442, 11:00-11:30 −0.092 → +0.205, 10:00-10:30 +0.352 → +0.282R (worse);
  price <$50 +0.350 → +0.441, $50-150 +0.292 → +0.419, $150-300 +0.070 → +0.170, >$300 −0.140 → −0.108R (all better).
- **Where it gives a little back:** (a) the 10:00-10:30 entries (+0.352 → +0.282R) — the volume sensor drops some good early
  reclaims; (b) 29% fewer trades (4.3 → 3.5 per traded Monday), on a setup that is already low-rep; (c) **the live sample
  disagrees**: of the 8 live trades WB3 keeps 3 (+0.16R avg, incl. the only loser LITE) and skips 5 winners (ARM, CRCL, FCEL,
  IONS on volume < 0.45x; CIFR at 10:00). Eight trades decide nothing, but the copy should be watched for exactly this.
- **Not touched / still open:** the Monday part (other weekdays ~0R; the edge has no known mechanism), the one-big-day
  dependence (2025-04-14 is still 35% of WB3's total R), and names above $300 (still negative).

## Experimental layers (counted, not spawned)
| Config | Replay avg R (w/o best) | 2-year avg R (w/o best) | Trades | Why not |
|---|---|---|---|---|
| WB3 + SPY at/above its 09:50 close (after-09:50 gate) | +0.258 (+0.213) | +0.484 (+0.375) | 34 / 114 | the gate alone fails the replay (w/o best day −0.087 vs −0.038) and its stand-alone gain is all in the valid half (train +0.208 vs +0.216); binds no WB3 replay trade, so the replay cannot confirm it |
| WB3 + target 1.25R | +0.387 (+0.369) | +0.319 (+0.212) | 34 / 176 | needs a new lab geometry (`t125s1`) in live code; 2-year w/o best day slightly below WB3 |

## Every config tried (113; screen1.csv, screen2.csv, screen3.csv, code/final_out.txt, code/ana_out.txt)
Failures and weaker passes, replay / 2-year avg R vs +0.078 / +0.202:
- Gates: SPY since 09:50 > −0.20 / −0.15 / −0.10 / −0.07 / −0.05 / −0.03 / >= −0.02 / >= 0 / > 0 / > 0.05: 2-year
  +0.247..+0.360 but replay +0.060..+0.068 with w/o best day −0.087 (FAIL: removes the IONS winner) except > 0 (+0.081 /
  +0.340, passes; = also skips every 09:50 bar) and > 0.05 (2-year worst day −12.3R, FAIL).
- Intake: price <= $150 / 200 / 225 / 250 FAIL replay; <= $300 / 350 / 500 pass (+0.133 / +0.262 best); adv >= $150M FAIL
  replay w/o best day; adv >= $75M FAIL.
- Timer: start 10:00 pass small; 10:10 / 10:15 pass (2-year +0.209 / +0.215, replay +0.242 / +0.276; weaker than 10:05 on the 2-year); end 11:00
  FAIL replay (−0.110); end 11:15 FAIL; end 12:00 FAIL worst day (−3.93R).
- Sensors: fromOpen < −2.2 / −2.5 FAIL replay; < −1.75 FAIL w/o best day; SMA50 > 0.5% FAIL; SMA50 off −0.068 (the SMA50
  part carries the setup); weaker-than-SPY off / < −0.5 = parent (never binds); rsi5 <= 70 FAIL; dist from LOD <= 0.35 /
  0.45 ATR FAIL replay; upper wick >= 0.03 / 0.05 pass, >= 0.08 FAIL; macdPct >= 0 pass, >= 0.1 FAIL; volume >= 0.35 / 0.55
  pass (weaker than 0.45); skip stock up since 09:50 FAIL; fill +2 min −0.033 / −0.044R (fill-sensitive).
- Exhaust: target 0.75R FAIL; 1.1 / 1.2 / 1.25 / 1.3 / 1.4R pass (needs new geometry); 1.5R FAIL worst day; no target / trail
  1R FAIL 2-year; stop 1.25R FAIL 2-year; stop 0.8R FAIL w/o best day; BE +0.5R FAIL; flat 13:00 / max hold 120 FAIL; 1R 0.30
  ATR pass (+0.307 / +0.206, meets only); 1R 0.20 ATR FAIL.
- Caps / cost / days: cost filter off FAIL 2-year; 0.10R pass small; Mon+Tue / all days FAIL (Tue +0.030, Wed −0.052, Thu
  −0.047, Fri −0.027 with the parent rules; with the WB3 parts +0.048 / −0.101 / −0.005 / −0.023).
- Combos: spy gate + price / target / window / volume / fromOpen (10 combos): 2-year up to +0.533 but every one with the gate
  is unconfirmed on the replay; price <= 300 + t1.25, volume + wick, upper wick + t1.25, 1R 0.30 + t1.25 pass, weaker or need
  the new geometry.

## Method
Identical engine for parent and copies (code/sim.py): module conditions on the 5-minute bar close (lab frames:
research/history2y for 2 years, SIP bars rebuilt as live via mcf.report.engine for the replay), first qualifying bar per
symbol-day, fill = open of the 1-minute bar starting one minute after the signal bar closes, t1s1 bracket around the signal
close, flat 15:55, LR8 costs (SEC fee + TAF on the short sale), Testing D cost filter 0.15R. 2-year = 2024-10..2026-10-16, the
locked block 2024-11-01..2025-02-28 never read; replay = 2026-10-19..11-16 (21 sessions). Parity: with the cost filter off the
2-year parent gives exactly the module's documented 295 trades; replay and 2-year frames give identical trades on the
overlapping Mondays (10-19, 11-02); all 8 live trades are found in the replay at the same bar; each copy's module mask equals
the sim's selection on both tests (code/modparity.py).

## Ready to deploy after the close (plan — NOT applied)
1. Account: **Testing E** (`config/account_testinge.yaml`) — a testing account, not the parent's (Testing D keeps the parent
   unchanged, twins apart); Testing E carries equal weight for promotion.
2. Add under `strategies:` (copy of `NM-RWN5-ns3-mon-weakrs-short-WB3.yaml`, `enabled: true`): `type: lab`, `module:
   research/workbench/NM-RWN5-ns3-mon-weakrs-short/modules/NM-RWN5-ns3-mon-weakrs-short-WB3.py`, `context: [spy_fo]`,
   `min_adv: 95000000`, `window: [1005, 1130]`, `scale_out_r: null`, `refire: false`; display name in
   `config/setup_names.yaml`: "Monday Weak-RS NS3 Short (near-miss) — WB3: reclaim volume >= 0.45x, from 10:05".
3. Put it FIRST in Testing E's `live.setup_order` (Workbench rule 5).
4. Ledger entry in `research/ledger.jsonl` (effective from the next session, after the close), regenerate
   `docs/live/assignments.json` (`python -m mcf.report.assignments`) in the same commit, `python -m mcf.research.ledger check`,
   `pytest -q`, PR merged outside 09:30-16:00 ET (setup-freeze).
5. Review after ~10 Mondays (it trades Mondays only, ~3.5 trades per traded Monday in the backtest): compare against the
   parent on the same Mondays; watch the live low-volume skips (see sign-off (c)).
