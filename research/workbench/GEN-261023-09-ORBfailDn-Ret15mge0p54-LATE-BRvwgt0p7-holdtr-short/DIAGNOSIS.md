# Diagnosis — Generated: Late Failed-Breakdown Pop Short `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short` (Testing E; SHORT)
Educational only — not financial advice. Mechanic, 2026-11-16/17 (Workbench batch; research files only, no config touched,
nothing deployed).

Engine: `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_engine.png` (P1..P27, blueprint `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short.md`). The setup shorts the first 5-minute bar closing 14:00-15:00
where the stock broke below its opening-range low earlier, is now back above it (P10 orb_fail_dn), popped >= 0.54% in
15 minutes (P11 ret3), while more than 70% of stocks are above VWAP (P12 breadth > 0.7); ADV >= $150M; stop 1R
(0.25 x daily ATR), no target, 1R trail once +1R, flat 15:55.

**Very few live trades: 10, all in ONE session (2026-11-09, Setup Generator account, no cost filter, $-lots). The decision
rests on the 2-year backtest (5,442 parent trades, 127 sessions) — said plainly.** The replay of the 17 live-window sessions
(10-23..11-16) has parent trades on only 2 sessions (breadth > 0.7 afternoons are rare). The parent's live record is not used
in the pass decision (owner 2026-11-16).

Rule-change context inside the live window (research/ledger.jsonl): the 10 trades are Gen-account ($510 lots, no cost
filter); from 11-12 Gen buying power / slots changed (REPV-1), LR1 flatten, LR5, LR8 cost allowance (live R before 11-12 uses
the older allowance); moved to Testing E 11-15 (ROT1 spotlight, max_positions_per_strategy 50, cost filter 0.15) from session
11-16 (0 trades since). Backtests use LR8 costs throughout.

## The live trades (10 — worst5 and best5 are all of them)
Sensor values from the replay lab frames (live pipeline); parity: the replay finds all 10 at the same signal bar.
W = window 14:30-15:00 (WB1), RA = ret3_atr >= 0.20 (WB2), ADX = ADX(7) >= 44, CF = Testing cost filter 0.15R.

| Trade (chart) | What happened | Part behind it | Catalogue part | Small tweak on THIS trade |
|---|---|---|---|---|
| worst1 IAU −1.15R (`_worst1_IAU_2026-11-09.png`) | 14:40 signal; MFE +1.11R at 14:47, gold reversed up, P24 stop 15:22 | P10/P11 fire on a gold ETF pop; P15/twins: GLD/GLDM/IAU = one bet x3 | Sensors / Caps | CF skips (0.163R); ADX 42.6 < 44 skips (WB4) → +1.15R |
| worst2 GLDM −1.14R (`_worst2_GLDM_2026-11-09.png`) | same gold move, same minute | as above | Sensors / Caps | CF skips (0.157R); ADX 40 skips |
| worst3 GLD −1.05R (`_worst3_GLD_2026-11-09.png`) | same; P24 stop | as above | Sensors | all copies KEEP it (ret3_atr 0.32, ADX 45); no single part fixes it |
| worst4 PATH −0.17R | $13 name, 1R $0.17; drifted, flattened | P18 cost (0.33R) | Intake | CF skips; RA (0.14) skips |
| worst5 UNG +0.11R | 14:25 signal, $10 name, cost 0.54R | P6 window; P18 | Timer / Intake | W skips (14:25); CF skips |
| best1 LUV +3.38R | 14:40, ret3 0.95%, 0.22 ATR, ADX 49; faded into the close | — | — | kept by every copy |
| best2 KGC +1.79R | small pop 0.13 ATR, ADX 18 | — | — | RA/ADX skip it (−1.79R) |
| best3 NCLH +0.87R | 0.11 ATR pop | — | — | CF / RA skip it |
| best4 GDX +0.80R | 0.19 ATR pop | — | — | RA skips (0.192) |
| best5 GDXJ +0.50R | 0.205 ATR, ADX 70 | — | — | kept by every copy |

Live sample: under today's Testing E cost filter only 4 of the 10 would have been taken (GLD, GDXJ, GDX, LUV; +3.63R).
WB4 keeps GLD / GDXJ / LUV (+2.83R, +0.94R avg) and skips 7 (+1.10R). Ten trades on one day prove nothing either way.

## All-trades component analysis (2-year backtest, parent as Testing E runs it; code/ana.py, ana.txt)
- **P6/P7 timer is the main failure:** entries 14:00-14:15 −0.064R, 14:15-14:30 −0.110R (both halves negative), 14:30-14:45
  +0.183R, 14:45-15:00 +0.362R (both halves positive). The setup shorts afternoon pops; the early ones keep running.
- **P11 pop size measured in % ignores the stock's range:** ret3_atr (pop in daily ATRs) < 0.18 ≈ −0.03R, >= 0.25 +0.22R
  (train +0.147 / valid +0.366). ADX(7) (directional strength of the pop) low −0.03, high +0.06-0.08 — weak alone, strong on
  top of the window + ATR-pop.
- **P14 open-lots cap (50) binds hard:** the parent averages 43 trades per traded day (max 353); the edge sits in the late
  entries of mass-signal days. With the live cap of 50 open lots the parent is **−0.051R** over 2 years (isolated +0.036R);
  with a 20/day cap −0.076R. Fewer, later signals is the remedy: the copies' cap-50 numbers are reported throughout.
- P12 breadth: > 0.6 is worse (−0.031), > 0.75/0.8 better but only on top of the window; P2/P3/P18 intake: neutral to small;
  exits (P24 stop / P25 target / trail / BE / max hold / flat time) — none helps over 2 years (stop 1.25R / 1R 0.30 ATR small
  gain in 2y only; max hold / earlier flat clearly worse: the short works into the close). Stops are mostly clean
  (only 15% of stop-outs had MFE >= 0.5R).
- Day type (end-of-day regime, diagnostic): up −0.131 / flat +0.135 / down +0.429 — it is a "broad rally fades into the close"
  setup; best-day share 153% (one day, 2026-07-29, +299R).

## Candidate tweaks (one part each, then combos)
1. WB1 — P6/P7 window start 14:00 → 14:30.
2. WB2 — new sensor P11b: ret3_atr >= 0.20 (pop >= 0.20 daily ATRs).
3. WB3 = WB1 + WB2. WB4 = WB3 + experimental layer P11c ADX(7) >= 44.
