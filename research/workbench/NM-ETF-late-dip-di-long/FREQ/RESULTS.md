# Workbench FREQ: Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` — more trades per session
Mechanic, 2026-11-17 (owner request 2026-11-16 ~22:15 ET). Primary (TEAM-6), LONG, 14:00-15:00. Research files only: no
config change, nothing deployed. Educational only — not financial advice. Diagnosis (blocked signals, universe, rules):
`DIAGNOSIS.md`. The first Workbench pass (WB1-WB3, `../RESULTS.md`) is separate; WB1 (owner-approved for a Testing
account tonight) is untouched.

## Pass rule for this job (fixed in `code/exp.py` before the first screen was scored)
A copy **passes the frequency rule** if, on BOTH the replay of the live sessions and the 2-year backtest:
trades per session >= 1.25 x parent, AND total R >= parent, AND avg R per trade >= parent − 0.03R, AND avg R without its
best day >= parent − 0.03R, AND worst day not worse than the parent's by more than 10%.
A "higher success" copy may pass the normal Workbench rule instead (RULES.md: avg R >= parent in both tests, w/o best day
not worse by > 0.02R, worst day not worse by > 10%). Costs in (LR8), locked block 2024-11-01..2025-02-28 never read
(never fetched for the new symbols; cached frames from the open directory only; asserted). Parent's live record not used
to decide.

## Verdict
| Copy | Change | Trades / session (replay; 2y) | Avg R (replay; 2y) | Total R (replay; 2y) | Avg R w/o best day (replay; 2y) | Worst day R (replay; 2y) | Win % (replay; 2y) | Verdict |
|---|---|---|---|---|---|---|---|---|
| parent | — | 1.52; 1.30 | +0.330; +0.117 | +10.5; +65.6 | +0.241; +0.086 | −0.82; −8.00 | 78.1; 71.1 | — |
| **`NM-ETF-late-dip-di-long-WB4`** | 15-min dip <= −0.75% (was −0.80), DI(7) >= −5 (was 0), NEW 60-min return >= −1.0% (falling-hour guard), refire on (cooldown 1 bar, live stacking) | **2.52; 1.92** (+66%; +48%) | **+0.337; +0.130** | **+17.9; +107.8** | +0.281; +0.092 | −0.63; −7.79 | 84.9; 71.0 | **PASS — frequency rule AND normal rule; recommended** |

17 of 113 configurations pass the frequency rule (15 the success rule); WB4 sits on a plateau — every one-step neighbour
passes (lots 2, cooldown 2 / 6, ret12 −0.75 / −1.25, DI −3 / −7, one lot at a time); the two that fail are dip −0.70% (2y
avg +0.108, worst day −9.27R) and no ret12 guard (2y +0.086R, worst day −10.5R). Chart:
`NM-ETF-late-dip-di-long_freq_configs.png`, curves `NM-ETF-late-dip-di-long_freq_wb4_curve.png`.

## Supervisor sign-off — WB4
- **What changed (4 parts):** the parent buys the FIRST sharp 15-minute dip (<= −0.80%) per ETF per day while +DI >= −DI.
  WB4 takes slightly shallower dips (<= −0.75%), allows a slightly negative DI balance (>= −5), takes the NEXT dips on the
  same ETF too (refire, as live LabStrategy does it: a fresh qualifying bar at least 2 bars after the previous signal,
  stacking under the account's 3 lots per symbol), and skips any dip that sits inside an hour already down more than 1%
  (ret12 >= −1.0%, a much looser version of WB1's guard).
- **Why:** the owner's three questions came back: blocked signals are ~15% of logged signals, mostly spread / cost / data,
  and not another Primary setup in practice (DIAGNOSIS Q1); more tickers dilute (Q2); the binding rules are one-entry-per-day,
  the DI sensor and the dip depth — but loosening them alone lets in falling-hour dips that lose. The guard removes those,
  so the loosening adds good trades.
- **Overall before -> after (costs in):** trades per session 1.52 -> 2.52 (replay), 1.30 -> 1.92 (2-year); avg R +0.330 ->
  +0.337 / +0.117 -> +0.130; total R +10.5 -> +17.9 / +65.6 -> +107.8; w/o best day +0.241 -> +0.281 / +0.086 -> +0.092;
  worst day −0.82 -> −0.63 / −8.00 -> −7.79; win 78.1 -> 84.9% / 71.1 -> 71.0%; avg win / loss +0.526 / −0.371 -> +0.485 /
  −0.496 (replay), +0.424 / −0.638 -> +0.449 / −0.649 (2y); median hold 36 -> 28 / 33 -> 30 min; gross avg R +0.362 -> +0.371 /
  +0.148 -> +0.164; green days 10 -> 10 of 21 (replay; red 3 -> 5), 106 -> 117 (2y; red 67 -> 86).
- **Splits (2y):** train +0.201 (334) -> +0.166 (531), total 67.0 -> 87.9R; valid −0.006 (227) -> **+0.067 (299)**, total
  −1.4 -> +19.9R. Without April 2025 (the crash month): +0.060 (372) -> +0.086 (513), total 22.2 -> 43.9R.
- **Families (remedy rule):** inverse ETFs +0.082 (179) -> +0.108 (263); non-inverse +0.133 -> +0.140; 3x +0.088 -> +0.097;
  1x/2x +0.232 -> +0.237 — all better. Per ETF (2y total R): 51 better, 21 worse, 18 unchanged; biggest give-backs SPXU −2.3R,
  SOXX −2.2, SOXL −1.6 (SOXL avg +0.139 -> +0.085 on 62 -> 83 trades), UPRO −1.5, TAN −1.1; biggest gains SQQQ +4.8, LABD
  +4.2, IWM +3.4, TECL +3.1, GDXU +3.1.
- **Where the trades come from (2y):** kept 469 parent trades (+0.157), added 361 (+0.095, +34.1R): 161 later dips on a
  symbol-day the parent traded (+0.135) and 200 new symbol-days (+0.062); removed 92 parent trades (−0.087, −8.0R) — the
  falling-hour dips. Added vs removed Welch t 2.59.
- **Where it gives a little back:** train-period avg R (+0.201 -> +0.166, more trades at a lower average; total R still up);
  more red days (replay 3 -> 5, 2y 67 -> 86); 15:00-bar entries still weak (−0.119R on 40). Paired by day vs the parent:
  +0.097R/day t 1.73 (2y), +0.348R/day t 2.21 (replay) — below the configs-counted bar 3.08 (reported, not a pass hurdle).
- **Honest ceiling:** both curves still owe much to April 2025 (the parent's whole 2-year result does); WB4 is better with
  and without it. The replay has 53 trades — a small sample that points the same way.
- **Live parity:** the WB4 module's own `mask()` + LabStrategy `refire_select` on live-built frames of the 21 replay sessions
  give exactly the engine's 53 signals (53 / 53, 0 differences). Refire and stacking are existing YAML / account settings
  (`refire: true`, `refire_cooldown: 1`, `same_setup_reentry: true`, `max_lots_per_symbol: 3`) — no code change.
- **Signed off:** PASS (both rules). Ready for a testing account after the close (plan below). On Deck / Primary is the owner's call.

## Configurations counted: 114 (parent + 113)
Screens f1 (22 one-part: universe sets, ADV floor, refire variants, dip depth, ATR, DI, window), f2 (18 ADV / refire / guard
combos), f3 (13 cluster caps), f4 (16 universe + guard grid), f5 (8 guard combos on the parent list), f6 (14 H6 neighbours),
f7 (8), f8 (14 WB4 neighbours / ablations). Bar max(1.5, sqrt(2 ln 114)) = 3.08. Full numbers: `screen_all.csv`.

## The tests (identical for parent and every copy)
- **Replay of the live sessions:** all 21 sessions 2026-10-19..11-16 (Testing 2, Testing C, Primary). Read-only SIP GET of
  1-minute + daily bars for every symbol of every set (374), frames built as live (mcf.report.engine.lab_frame + apply_daily),
  arena indicators (context=False), adv20 from daily bars. Parity: the parent selection reproduces the first pass's 30
  replay trades to 11-13 exactly and all 27 live signals. Isolated (no caps, quote checks or latch).
- **2-year backtest:** 2024-10-01..2026-10-16 open months (433 sessions), locked block never read. Cached symbols: the
  research/history2y frames (parity: the parent on the cached ETFs gives the first pass's 480 trades, +0.125R, exactly);
  85 symbols the cache lacks (24 of the parent's own ETFs + new sets) fetched read-only and built with the same pipeline
  (setup_lab.build on 5-minute bars; their early-March-2025 ATR / adv20 use pre-block days as priors — disclosed).
- Engine (`code/sim2.py` = first pass `../code/sim.py` exits and costs, unchanged, + refire / lots / universe / caps):
  conditions on the 5-minute bar close, adv20 >= $95M, price >= $5; fill = open of the 1-minute bar 1 minute after the
  signal bar; 1R = 0.25 x daily ATR, target +0.5R, stop 1R, stop first on a same-minute tie, flat 15:55; R = net P/L /
  |fill − stop|. **Costs in (LR8 production model)** for every config.
- Universe sets: `code/sets.py` (from the live universe.csv of 2026-11-16, ADV >= $95M, price >= $5; chosen with today's
  list — a mild look-ahead on which ETFs exist, the per-day adv20 floor still applies).

## Every configuration (replay 21 sessions; 2-year 433 sessions)
| # | Config | Replay n / tps / avg / w/o best / total / worst | 2y n / tps / avg / w/o best / total / worst | Frequency rule | Success rule |
|---|---|---|---|---|---|
| 0 | parent | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 561 / 1.30 / +0.117 / +0.086 / 65.6 / -8.00 | — | — |
| 1 | U1 +EQ1X (1x equity ETFs) | 33 / 1.57 / +0.338 / +0.254 / 11.2 / -0.82 | 584 / 1.35 / +0.110 / +0.082 / 64.5 / -11.16 | replay trades/session +3% (<25%); 2y trades/session +4% (<25%); 2y total R 64.5 < 65.6; 2y worst day -11.16 | fail |
| 2 | U2 +LEVIX (lev index/sector, ADV>=95M) | 38 / 1.81 / +0.307 / +0.218 / 11.6 / -0.82 | 605 / 1.40 / +0.110 / +0.081 / 66.7 / -9.02 | replay trades/session +19% (<25%); 2y trades/session +8% (<25%); 2y worst day -9.02 | fail |
| 3 | U3 +LEV50 & ADV>=$40M | 48 / 2.29 / +0.334 / +0.228 / 16.0 / -0.82 | 981 / 2.27 / +0.083 / +0.063 / 81.5 / -13.40 | 2y avg R +0.083; 2y worst day -13.40 | fail |
| 4 | U4 +SSLEV (single-stock lev ETFs) | 81 / 3.86 / +0.194 / +0.131 / 15.7 / -2.34 | 1090 / 2.52 / +0.037 / +0.017 / 40.7 / -9.91 | replay avg R +0.194; replay w/o best +0.131; replay worst day -2.34; 2y total R 40.7 < 65.6; 2y avg R +0.037; 2y w/o best +0.017; 2y worst day -9.91 | fail |
| 5 | U5 +CMDTY | 33 / 1.57 / +0.317 / +0.230 / 10.5 / -0.82 | 659 / 1.52 / +0.092 / +0.064 / 60.7 / -10.29 | replay trades/session +3% (<25%); 2y trades/session +17% (<25%); 2y total R 60.7 < 65.6; 2y worst day -10.29 | fail |
| 6 | U6 +CRYPTO | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 606 / 1.40 / +0.106 / +0.076 / 64.5 / -11.35 | replay trades/session +0% (<25%); 2y trades/session +8% (<25%); 2y total R 64.5 < 65.6; 2y worst day -11.35 | fail |
| 7 | U7 +STK (large-cap stocks ADV>=$1B) | 75 / 3.57 / +0.310 / +0.212 / 23.2 / -0.66 | 1478 / 3.41 / +0.038 / +0.017 / 56.5 / -35.22 | 2y total R 56.5 < 65.6; 2y avg R +0.038; 2y w/o best +0.017; 2y worst day -35.22 | fail |
| 8 | U8 ADV floor $50M (parent list) | 37 / 1.76 / +0.360 / +0.237 / 13.3 / -0.82 | 726 / 1.68 / +0.117 / +0.090 / 85.0 / -8.97 | replay trades/session +16% (<25%); 2y worst day -8.97 | fail |
| 9 | R1 refire cool1 lots3 (live semantics) | 35 / 1.67 / +0.271 / +0.184 / 9.5 / -0.91 | 641 / 1.48 / +0.129 / +0.094 / 82.8 / -7.68 | replay trades/session +9% (<25%); replay total R 9.5 < 10.5; replay avg R +0.271; replay w/o best +0.184; replay worst day -0.91; 2y trades/session +14% (<25%) | fail |
| 10 | R2 refire cool1 one lot (re-enter after exit) | 33 / 1.57 / +0.286 / +0.195 / 9.5 / -0.82 | 604 / 1.40 / +0.123 / +0.086 / 74.4 / -7.68 | replay trades/session +3% (<25%); replay total R 9.5 < 10.5; replay avg R +0.286; replay w/o best +0.195; 2y trades/session +8% (<25%) | fail |
| 11 | R3 refire cool2 lots2 | 34 / 1.62 / +0.282 / +0.193 / 9.6 / -0.82 | 611 / 1.41 / +0.128 / +0.092 / 78.4 / -7.68 | replay trades/session +6% (<25%); replay total R 9.6 < 10.5; replay avg R +0.282; replay w/o best +0.193; 2y trades/session +9% (<25%) | fail |
| 12 | R4 refire cool3 lots3 | 34 / 1.62 / +0.282 / +0.193 / 9.6 / -0.82 | 606 / 1.40 / +0.128 / +0.091 / 77.7 / -7.68 | replay trades/session +6% (<25%); replay total R 9.6 < 10.5; replay avg R +0.282; replay w/o best +0.193; 2y trades/session +8% (<25%) | fail |
| 13 | R5 refire cool6 (30 min) lots3 | 34 / 1.62 / +0.282 / +0.193 / 9.6 / -0.82 | 594 / 1.37 / +0.121 / +0.092 / 71.9 / -8.00 | replay trades/session +6% (<25%); replay total R 9.6 < 10.5; replay avg R +0.282; replay w/o best +0.193; 2y trades/session +6% (<25%) | fail |
| 14 | R6a ret3<=-0.70 | 44 / 2.10 / +0.308 / +0.255 / 13.5 / -0.82 | 746 / 1.72 / +0.082 / +0.061 / 61.0 / -9.94 | 2y total R 61.0 < 65.6; 2y avg R +0.082; 2y worst day -9.94 | fail |
| 15 | R6b ret3<=-0.60 | 61 / 2.90 / +0.257 / +0.203 / 15.7 / -1.04 | 972 / 2.25 / +0.061 / +0.043 / 59.2 / -12.12 | replay avg R +0.257; replay w/o best +0.203; replay worst day -1.04; 2y total R 59.2 < 65.6; 2y avg R +0.061; 2y w/o best +0.043; 2y worst day -12.12 | fail |
| 16 | R6c ret3<=-0.50 | 84 / 4.00 / +0.165 / +0.119 / 13.9 / -1.64 | 1321 / 3.05 / +0.034 / +0.019 / 45.1 / -15.84 | replay avg R +0.165; replay w/o best +0.119; replay worst day -1.64; 2y total R 45.1 < 65.6; 2y avg R +0.034; 2y w/o best +0.019; 2y worst day -15.84 | fail |
| 17 | R7a ATR>=3.0% | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 589 / 1.36 / +0.107 / +0.068 / 63.2 / -11.28 | replay trades/session +0% (<25%); 2y trades/session +5% (<25%); 2y total R 63.2 < 65.6; 2y worst day -11.28 | fail |
| 18 | R7b ATR>=2.5% | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 604 / 1.40 / +0.115 / +0.063 / 69.6 / -11.28 | replay trades/session +0% (<25%); 2y trades/session +8% (<25%); 2y worst day -11.28 | fail |
| 19 | R8a DI>=-5 | 43 / 2.05 / +0.344 / +0.301 / 14.8 / -0.56 | 710 / 1.64 / +0.097 / +0.053 / 69.0 / -12.04 | 2y w/o best +0.053; 2y worst day -12.04 | fail |
| 20 | R8b no DI | 115 / 5.48 / +0.161 / +0.115 / 18.5 / -2.75 | 1943 / 4.49 / +0.048 / +0.022 / 94.2 / -11.58 | replay avg R +0.161; replay w/o best +0.115; replay worst day -2.75; 2y avg R +0.048; 2y w/o best +0.022; 2y worst day -11.58 | fail |
| 21 | R9a window from 13:30 | 41 / 1.95 / +0.295 / +0.224 / 12.1 / -0.82 | 766 / 1.77 / +0.031 / +0.004 / 23.8 / -11.43 | replay avg R +0.295; 2y total R 23.8 < 65.6; 2y avg R +0.031; 2y w/o best +0.004; 2y worst day -11.43 | fail |
| 22 | R9b window from 13:45 | 38 / 1.81 / +0.320 / +0.246 / 12.2 / -0.82 | 654 / 1.51 / +0.090 / +0.060 / 59.0 / -8.00 | replay trades/session +19% (<25%); 2y trades/session +17% (<25%); 2y total R 59.0 < 65.6 | fail |
| 23 | U8b ADV>=$40M | 37 / 1.76 / +0.360 / +0.237 / 13.3 / -0.82 | 775 / 1.79 / +0.114 / +0.089 / 88.0 / -10.56 | replay trades/session +16% (<25%); 2y worst day -10.56 | fail |
| 24 | U8c ADV>=$60M | 36 / 1.71 / +0.361 / +0.233 / 13.0 / -0.82 | 694 / 1.60 / +0.117 / +0.088 / 81.5 / -8.97 | replay trades/session +12% (<25%); 2y trades/session +24% (<25%); 2y worst day -8.97 | fail |
| 25 | U8d ADV>=$70M | 36 / 1.71 / +0.361 / +0.233 / 13.0 / -0.82 | 666 / 1.54 / +0.114 / +0.085 / 75.7 / -8.97 | replay trades/session +12% (<25%); 2y trades/session +19% (<25%); 2y worst day -8.97 | fail |
| 26 | U8e ADV>=$80M | 36 / 1.71 / +0.361 / +0.233 / 13.0 / -0.82 | 634 / 1.46 / +0.117 / +0.088 / 74.2 / -8.97 | replay trades/session +12% (<25%); 2y trades/session +13% (<25%); 2y worst day -8.97 | fail |
| 27 | C1 ADV50 + refire cool1 lots3 | 40 / 1.91 / +0.307 / +0.186 / 12.3 / -0.91 | 829 / 1.92 / +0.119 / +0.087 / 98.8 / -8.97 | replay w/o best +0.186; replay worst day -0.91; 2y worst day -8.97 | fail |
| 28 | C2 ADV50 + refire one lot | 38 / 1.81 / +0.322 / +0.196 / 12.2 / -0.82 | 783 / 1.81 / +0.116 / +0.082 / 90.7 / -8.97 | replay trades/session +19% (<25%); replay w/o best +0.196; 2y worst day -8.97 | fail |
| 29 | C3 ADV50 + refire cool2 lots2 | 39 / 1.86 / +0.317 / +0.195 / 12.4 / -0.82 | 791 / 1.83 / +0.120 / +0.087 / 95.1 / -8.97 | replay trades/session +22% (<25%); replay w/o best +0.195; 2y worst day -8.97 | fail |
| 30 | C4 ADV50 + LEV50 | 47 / 2.24 / +0.333 / +0.225 / 15.6 / -0.82 | 915 / 2.11 / +0.085 / +0.064 / 77.9 / -11.32 | 2y avg R +0.085; 2y worst day -11.32 | fail |
| 31 | C5 ADV50 + LEVIX | 43 / 2.05 / +0.336 / +0.216 / 14.4 / -0.82 | 770 / 1.78 / +0.112 / +0.086 / 86.0 / -9.67 | 2y worst day -9.67 | fail |
| 32 | C6 ADV50 + DI>=-5 | 50 / 2.38 / +0.362 / +0.275 / 18.1 / -0.56 | 920 / 2.12 / +0.098 / +0.058 / 90.0 / -13.68 | 2y worst day -13.68 | fail |
| 33 | C7 ADV50 + daycap 6 | 37 / 1.76 / +0.360 / +0.237 / 13.3 / -0.82 | 499 / 1.15 / +0.085 / +0.076 / 42.2 / -4.73 | replay trades/session +16% (<25%); 2y trades/session +-11% (<25%); 2y total R 42.2 < 65.6; 2y avg R +0.085 | fail |
| 34 | C8 ADV50 + ret12>=-0.5 | 28 / 1.33 / +0.433 / +0.295 / 12.1 / -0.56 | 579 / 1.34 / +0.163 / +0.132 / 94.6 / -8.97 | replay trades/session +-13% (<25%); 2y trades/session +3% (<25%); 2y worst day -8.97 | fail |
| 35 | C9 ADV50 + ret12>=-1.0 | 35 / 1.67 / +0.387 / +0.259 / 13.5 / -0.64 | 644 / 1.49 / +0.154 / +0.126 / 99.5 / -8.97 | replay trades/session +9% (<25%); 2y trades/session +15% (<25%); 2y worst day -8.97 | fail |
| 36 | C10 ADV50 + refire1 lots3 + ret12>=-1.0 | 37 / 1.76 / +0.340 / +0.213 / 12.6 / -0.64 | 725 / 1.67 / +0.162 / +0.128 / 117.6 / -8.97 | replay trades/session +16% (<25%); 2y worst day -8.97 | fail |
| 37 | C11 ADV40 + refire1 lots3 | 40 / 1.91 / +0.307 / +0.186 / 12.3 / -0.91 | 883 / 2.04 / +0.113 / +0.083 / 99.4 / -10.25 | replay w/o best +0.186; replay worst day -0.91; 2y worst day -10.25 | fail |
| 38 | C12 ADV50 + LEV50 + refire1 lots3 | 50 / 2.38 / +0.292 / +0.185 / 14.6 / -0.91 | 1054 / 2.43 / +0.087 / +0.062 / 91.3 / -11.01 | replay avg R +0.292; replay w/o best +0.185; replay worst day -0.91; 2y avg R +0.087; 2y worst day -11.01 | fail |
| 39 | C13 refire1 lots3 + DI>=-5 | 50 / 2.38 / +0.306 / +0.264 / 15.3 / -0.63 | 855 / 1.98 / +0.094 / +0.053 / 80.3 / -11.19 | 2y w/o best +0.053; 2y worst day -11.19 | fail |
| 40 | C14 ADV50 + ret3<=-0.70 + ret12>=0 | 28 / 1.33 / +0.443 / +0.232 / 12.4 / -0.59 | 667 / 1.54 / +0.122 / +0.102 / 81.7 / -10.97 | replay trades/session +-13% (<25%); 2y trades/session +19% (<25%); 2y worst day -10.97 | fail |
| 41 | B1 barcap 3 | 31 / 1.48 / +0.323 / +0.231 / 10.0 / -0.82 | 404 / 0.93 / +0.090 / +0.075 / 36.2 / -3.11 | replay trades/session +-3% (<25%); replay total R 10.0 < 10.5; 2y trades/session +-28% (<25%); 2y total R 36.2 < 65.6 | fail |
| 42 | B2 barcap 4 | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 439 / 1.01 / +0.097 / +0.080 / 42.7 / -3.54 | replay trades/session +0% (<25%); 2y trades/session +-22% (<25%); 2y total R 42.7 < 65.6 | fail |
| 43 | B3 barcap 5 | 32 / 1.52 / +0.330 / +0.241 / 10.5 / -0.82 | 461 / 1.06 / +0.091 / +0.077 / 41.8 / -4.57 | replay trades/session +0% (<25%); 2y trades/session +-18% (<25%); 2y total R 41.8 < 65.6 | fail |
| 44 | K1 ADV50 + barcap 4 | 36 / 1.71 / +0.356 / +0.227 / 12.8 / -0.82 | 547 / 1.26 / +0.093 / +0.080 / 51.1 / -3.97 | replay trades/session +12% (<25%); 2y trades/session +-3% (<25%); 2y total R 51.1 < 65.6 | fail |
| 45 | K2 ADV50 + barcap 5 | 37 / 1.76 / +0.360 / +0.237 / 13.3 / -0.82 | 583 / 1.35 / +0.097 / +0.085 / 56.8 / -4.57 | replay trades/session +16% (<25%); 2y trades/session +4% (<25%); 2y total R 56.8 < 65.6 | fail |
| 46 | K3 ADV50 + refire1 lots3 + barcap 4 | 39 / 1.86 / +0.301 / +0.176 / 11.8 / -0.91 | 613 / 1.42 / +0.082 / +0.068 / 50.2 / -8.56 | replay trades/session +22% (<25%); replay w/o best +0.176; replay worst day -0.91; 2y trades/session +9% (<25%); 2y total R 50.2 < 65.6; 2y avg R +0.082 | fail |
| 47 | K4 ADV50 + refire1 lots3 + barcap 5 | 40 / 1.91 / +0.307 / +0.186 / 12.3 / -0.91 | 654 / 1.51 / +0.090 / +0.075 / 59.1 / -9.31 | replay w/o best +0.186; replay worst day -0.91; 2y trades/session +17% (<25%); 2y total R 59.1 < 65.6; 2y worst day -9.31 | fail |
| 48 | K5 ADV50 + DI>=-5 + barcap 4 | 46 / 2.19 / +0.346 / +0.248 / 15.9 / -0.56 | 706 / 1.63 / +0.071 / +0.054 / 50.3 / -4.74 | 2y total R 50.3 < 65.6; 2y avg R +0.071; 2y w/o best +0.054 | fail |
| 49 | K6 ADV50 + DI>=-5 + barcap 5 | 47 / 2.24 / +0.350 / +0.255 / 16.4 / -0.56 | 749 / 1.73 / +0.071 / +0.053 / 53.5 / -5.08 | 2y total R 53.5 < 65.6; 2y avg R +0.071; 2y w/o best +0.053 | fail |
| 50 | K7 ADV50 + DI>=-5 + refire1 lots3 + barcap 5 | 54 / 2.57 / +0.314 / +0.229 / 17.0 / -0.63 | 864 / 2.00 / +0.060 / +0.043 / 52.0 / -11.42 | 2y total R 52.0 < 65.6; 2y avg R +0.060; 2y w/o best +0.043; 2y worst day -11.42 | fail |
| 51 | K8 ADV50 + ret12>=-1 + refire1 lots3 + barcap 5 | 37 / 1.76 / +0.340 / +0.213 / 12.6 / -0.64 | 563 / 1.30 / +0.126 / +0.108 / 70.9 / -5.14 | replay trades/session +16% (<25%); 2y trades/session +0% (<25%) | fail |
| 52 | K9 ADV50 + LEVIX + refire1 lots3 + barcap 5 | 46 / 2.19 / +0.291 / +0.174 / 13.4 / -0.91 | 700 / 1.62 / +0.090 / +0.076 / 63.2 / -9.31 | replay avg R +0.291; replay w/o best +0.174; replay worst day -0.91; 2y trades/session +25% (<25%); 2y total R 63.2 < 65.6; 2y worst day -9.31 | fail |
| 53 | K10 ADV50 + DI>=-5 + barcap 3 | 43 / 2.05 / +0.332 / +0.224 / 14.3 / -0.56 | 650 / 1.50 / +0.072 / +0.059 / 47.1 / -4.74 | 2y trades/session +16% (<25%); 2y total R 47.1 < 65.6; 2y avg R +0.072 | fail |
| 54 | G ADV50+LEVIX+ret12>=-0.5 | 31 / 1.48 / +0.401 / +0.275 / 12.4 / -0.56 | 610 / 1.41 / +0.158 / +0.128 / 96.6 / -9.67 | replay trades/session +-3% (<25%); 2y trades/session +9% (<25%); 2y worst day -9.67 | fail |
| 55 | G ADV50+LEVIX+ret12>=-0.5+DI-5 | 35 / 1.67 / +0.384 / +0.272 / 13.5 / -0.56 | 747 / 1.73 / +0.134 / +0.096 / 100.2 / -9.67 | replay trades/session +9% (<25%); 2y worst day -9.67 | fail |
| 56 | G ADV50+LEVIX+ret12>=-0.5+ret3-0.70 | 46 / 2.19 / +0.338 / +0.245 / 15.5 / -0.59 | 819 / 1.89 / +0.118 / +0.102 / 96.9 / -11.67 | 2y worst day -11.67 | fail |
| 57 | G ADV50+LEVIX+ret12>=-0.5+refire | 32 / 1.52 / +0.355 / +0.228 / 11.3 / -0.63 | 689 / 1.59 / +0.166 / +0.129 / 114.1 / -9.67 | replay trades/session +0% (<25%); 2y trades/session +23% (<25%); 2y worst day -9.67 | fail |
| 58 | G ADV50+LEVIX+ret12>=-0.5+DI-5+refire | 38 / 1.81 / +0.352 / +0.247 / 13.4 / -0.63 | 868 / 2.00 / +0.136 / +0.097 / 118.2 / -10.76 | replay trades/session +19% (<25%); 2y worst day -10.76 | fail |
| 59 | G ADV50+LEVIX+ret12>=-0.5+ret3-0.70+DI-5 | 53 / 2.52 / +0.305 / +0.222 / 16.1 / -0.75 | 991 / 2.29 / +0.106 / +0.079 / 104.7 / -11.67 | 2y worst day -11.67 | fail |
| 60 | G ADV50+LEVIX+ret12>=-1.0 | 40 / 1.91 / +0.354 / +0.227 / 14.2 / -0.64 | 679 / 1.57 / +0.150 / +0.123 / 102.0 / -9.67 | 2y trades/session +21% (<25%); 2y worst day -9.67 | fail |
| 61 | G ADV50+LEVIX+ret12>=-1.0+DI-5 | 50 / 2.38 / +0.361 / +0.265 / 18.1 / -0.56 | 836 / 1.93 / +0.134 / +0.100 / 112.2 / -9.67 | 2y worst day -9.67 | fail |
| 62 | G ADV50+LEVIX+ret12>=-1.0+ret3-0.70 | 56 / 2.67 / +0.309 / +0.216 / 17.3 / -0.59 | 907 / 2.10 / +0.104 / +0.088 / 94.2 / -11.67 | 2y worst day -11.67 | fail |
| 63 | G ADV50+LEVIX+ret12>=-1.0+refire | 42 / 2.00 / +0.314 / +0.188 / 13.2 / -0.64 | 767 / 1.77 / +0.158 / +0.125 / 121.0 / -9.67 | replay w/o best +0.188; 2y worst day -9.67 | fail |
| 64 | G ADV50+LEVIX+ret12>=-1.0+DI-5+refire | 55 / 2.62 / +0.337 / +0.247 / 18.5 / -0.63 | 977 / 2.26 / +0.128 / +0.093 / 125.0 / -11.36 | 2y worst day -11.36 | fail |
| 65 | G ADV50+LEVIX+ret12>=-1.0+ret3-0.70+DI-5 | 69 / 3.29 / +0.297 / +0.222 / 20.5 / -0.75 | 1107 / 2.56 / +0.100 / +0.076 / 110.6 / -11.67 | replay avg R +0.297; 2y worst day -11.67 | fail |
| 66 | G ADV50+LEVIX+DI-5 | 57 / 2.71 / +0.328 / +0.241 / 18.7 / -0.56 | 973 / 2.25 / +0.093 / +0.055 / 90.5 / -14.70 | 2y w/o best +0.055; 2y worst day -14.70 | fail |
| 67 | G ADV50+LEVIX+ret3-0.70 | 61 / 2.90 / +0.274 / +0.190 / 16.7 / -0.59 | 1019 / 2.35 / +0.078 / +0.063 / 79.6 / -11.67 | replay avg R +0.274; replay w/o best +0.190; 2y avg R +0.078; 2y worst day -11.67 | fail |
| 68 | G ADV50+LEV50+ret12>=-1.0+DI-5 | 54 / 2.57 / +0.366 / +0.279 / 19.7 / -0.56 | 982 / 2.27 / +0.111 / +0.081 / 109.0 / -10.78 | 2y worst day -10.78 | fail |
| 69 | G ADV40+LEV50+ret12>=-1.0+DI-5 | 55 / 2.62 / +0.366 / +0.281 / 20.1 / -0.56 | 1056 / 2.44 / +0.107 / +0.079 / 113.4 / -11.83 | 2y worst day -11.83 | fail |
| 70 | H1 ret12>=-1.0 + refire1 lots3 | 32 / 1.52 / +0.306 / +0.214 / 9.8 / -0.64 | 563 / 1.30 / +0.170 / +0.132 / 95.6 / -7.27 | replay trades/session +0% (<25%); replay total R 9.8 < 10.5; 2y trades/session +0% (<25%) | fail |
| 71 | H2 ret12>=-1.0 + DI>=-5 | 37 / 1.76 / +0.363 / +0.292 / 13.4 / -0.56 | 613 / 1.42 / +0.144 / +0.103 / 88.4 / -7.27 | replay trades/session +16% (<25%); 2y trades/session +9% (<25%) | pass |
| 72 | H3 ret12>=-1.0 + DI>=-5 + refire1 lots3 | 42 / 2.00 / +0.331 / +0.266 / 13.9 / -0.63 | 721 / 1.67 / +0.138 / +0.099 / 99.7 / -9.06 | 2y worst day -9.06 | fail |
| 73 | H4 ret12>=-1.0 + ret3<=-0.70 | 42 / 2.00 / +0.327 / +0.276 / 13.8 / -0.64 | 669 / 1.54 / +0.114 / +0.093 / 76.5 / -9.27 | 2y trades/session +19% (<25%); 2y worst day -9.27 | fail |
| 74 | H5 ret12>=-0.5 + ret3<=-0.70 + refire1 lots3 | 38 / 1.81 / +0.385 / +0.269 / 14.6 / -0.63 | 690 / 1.59 / +0.151 / +0.115 / 104.2 / -9.77 | replay trades/session +19% (<25%); 2y trades/session +23% (<25%); 2y worst day -9.77 | fail |
| 75 | H6 LEVIX + ret12>=-1.0 + DI>=-5 | 43 / 2.05 / +0.343 / +0.271 / 14.8 / -0.56 | 655 / 1.51 / +0.138 / +0.100 / 90.6 / -7.97 | 2y trades/session +17% (<25%) | pass |
| 76 | H7 ret12>=-1.0 + DI>=-5 + refire cool2 lots2 | 41 / 1.95 / +0.324 / +0.257 / 13.3 / -0.63 | 673 / 1.55 / +0.141 / +0.096 / 94.9 / -9.11 | 2y trades/session +20% (<25%); 2y worst day -9.11 | fail |
| 77 | H8 ret12>=-0.5 + DI>=-5 + refire1 lots3 | 30 / 1.43 / +0.350 / +0.276 / 10.5 / -0.63 | 642 / 1.48 / +0.148 / +0.105 / 95.3 / -8.47 | replay trades/session +-6% (<25%); 2y trades/session +14% (<25%) | pass |
| 78 | I1 H6 + refire cool2 lots2 | 47 / 2.24 / +0.311 / +0.241 / 14.6 / -0.63 | 719 / 1.66 / +0.136 / +0.094 / 97.6 / -9.11 | 2y worst day -9.11 | fail |
| 79 | I2 H6 + refire cool3 lots2 | 47 / 2.24 / +0.311 / +0.241 / 14.6 / -0.63 | 714 / 1.65 / +0.134 / +0.091 / 95.6 / -9.50 | 2y worst day -9.50 | fail |
| 80 | I3 H6 + refire one lot | 45 / 2.14 / +0.312 / +0.239 / 14.0 / -0.63 | 722 / 1.67 / +0.127 / +0.086 / 91.4 / -8.39 | PASS | fail |
| 81 | I4 H6 + ret3<=-0.75 | 51 / 2.43 / +0.301 / +0.248 / 15.3 / -0.56 | 744 / 1.72 / +0.125 / +0.092 / 92.7 / -8.49 | PASS | fail |
| 82 | I5 H6 + window 13:45 | 50 / 2.38 / +0.323 / +0.280 / 16.2 / -0.56 | 773 / 1.78 / +0.105 / +0.070 / 81.2 / -7.97 | PASS | fail |
| 83 | I6 H6 + ADV>=$70M | 47 / 2.24 / +0.366 / +0.262 / 17.2 / -0.56 | 768 / 1.77 / +0.138 / +0.101 / 105.9 / -9.67 | 2y worst day -9.67 | fail |
| 84 | I7 H6 + EQ1X | 44 / 2.10 / +0.349 / +0.297 / 15.4 / -0.56 | 679 / 1.57 / +0.132 / +0.098 / 89.6 / -8.46 | 2y trades/session +21% (<25%) | pass |
| 85 | I8 H6 + CMDTY | 45 / 2.14 / +0.334 / +0.264 / 15.0 / -0.56 | 762 / 1.76 / +0.115 / +0.080 / 87.7 / -7.97 | PASS | fail |
| 86 | I9 H6 + CRYPTO | 43 / 2.05 / +0.343 / +0.271 / 14.8 / -0.56 | 700 / 1.62 / +0.132 / +0.095 / 92.2 / -7.97 | 2y trades/session +25% (<25%) | pass |
| 87 | I10 H6 + DI>=-10 | 48 / 2.29 / +0.291 / +0.221 / 14.0 / -0.56 | 787 / 1.82 / +0.102 / +0.053 / 80.3 / -7.97 | replay avg R +0.291; 2y w/o best +0.053 | fail |
| 88 | I11 H6 ret12>=-1.5 | 48 / 2.29 / +0.319 / +0.267 / 15.3 / -0.56 | 695 / 1.60 / +0.128 / +0.091 / 88.7 / -7.97 | 2y trades/session +24% (<25%) | fail |
| 89 | I12 H6 + SSLEV | 95 / 4.52 / +0.212 / +0.162 / 20.1 / -0.88 | 1229 / 2.84 / +0.049 / +0.024 / 59.8 / -9.84 | replay avg R +0.212; replay w/o best +0.162; 2y total R 59.8 < 65.6; 2y avg R +0.049; 2y w/o best +0.024; 2y worst day -9.84 | fail |
| 90 | I13 H6 + ATR>=3.0 | 43 / 2.05 / +0.343 / +0.271 / 14.8 / -0.56 | 692 / 1.60 / +0.141 / +0.085 / 97.8 / -7.97 | 2y trades/session +23% (<25%) | pass |
| 91 | I14 H6 + refire cool1 lots3 | 48 / 2.29 / +0.317 / +0.250 / 15.2 / -0.63 | 774 / 1.79 / +0.133 / +0.097 / 102.8 / -9.06 | 2y worst day -9.06 | fail |
| 92 | J1 H2 + refire one lot | 39 / 1.86 / +0.327 / +0.256 / 12.7 / -0.63 | 677 / 1.56 / +0.133 / +0.090 / 89.8 / -8.39 | replay trades/session +22% (<25%); 2y trades/session +21% (<25%) | fail |
| 93 | J2 H2 + ret3<=-0.75 | 44 / 2.10 / +0.311 / +0.262 / 13.7 / -0.56 | 699 / 1.61 / +0.131 / +0.097 / 91.6 / -7.79 | 2y trades/session +25% (<25%) | fail |
| 94 | J3 H2 + CMDTY | 39 / 1.86 / +0.352 / +0.284 / 13.7 / -0.56 | 720 / 1.66 / +0.119 / +0.082 / 85.4 / -7.27 | replay trades/session +22% (<25%) | pass |
| 95 | J4 H2 + window 13:45 | 43 / 2.05 / +0.352 / +0.319 / 15.2 / -0.56 | 723 / 1.67 / +0.108 / +0.070 / 78.2 / -7.27 | PASS | fail |
| 96 | J5 I3 + CMDTY (H6 + refire one lot + CMDTY) | 47 / 2.24 / +0.305 / +0.235 / 14.3 / -0.63 | 838 / 1.94 / +0.104 / +0.067 / 87.3 / -8.39 | PASS | fail |
| 97 | J6 I4 + CMDTY (H6 + ret3-0.75 + CMDTY) | 53 / 2.52 / +0.295 / +0.251 / 15.6 / -0.56 | 878 / 2.03 / +0.105 / +0.076 / 92.5 / -8.49 | replay avg R +0.295 | fail |
| 98 | J7 H6 + refire one lot + ret3<=-0.75 | 56 / 2.67 / +0.321 / +0.255 / 18.0 / -0.63 | 823 / 1.90 / +0.116 / +0.076 / 95.1 / -8.49 | PASS | fail |
| 99 | J8 H2 + refire one lot + ret3<=-0.75 | 48 / 2.29 / +0.331 / +0.268 / 15.9 / -0.63 | 775 / 1.79 / +0.122 / +0.080 / 94.6 / -7.79 | PASS | pass |
| 100 | N1 J8 with live stacking (lots3) | 53 / 2.52 / +0.337 / +0.281 / 17.9 / -0.63 | 830 / 1.92 / +0.130 / +0.092 / 107.8 / -7.79 | PASS | pass |
| 101 | N2 J8 lots2 | 53 / 2.52 / +0.337 / +0.281 / 17.9 / -0.63 | 828 / 1.91 / +0.129 / +0.091 / 107.0 / -7.79 | PASS | pass |
| 102 | N3 J8 cool2 | 48 / 2.29 / +0.331 / +0.268 / 15.9 / -0.63 | 758 / 1.75 / +0.127 / +0.085 / 96.2 / -7.79 | PASS | pass |
| 103 | N4 J8 cool6 | 48 / 2.29 / +0.331 / +0.268 / 15.9 / -0.63 | 734 / 1.70 / +0.133 / +0.099 / 97.6 / -7.79 | PASS | pass |
| 104 | N5 J8 ret12>=-0.75 | 44 / 2.10 / +0.347 / +0.276 / 15.3 / -0.63 | 735 / 1.70 / +0.132 / +0.088 / 96.7 / -7.79 | PASS | pass |
| 105 | N6 J8 ret12>=-1.25 | 51 / 2.43 / +0.337 / +0.293 / 17.2 / -0.63 | 796 / 1.84 / +0.117 / +0.076 / 93.4 / -7.79 | PASS | pass |
| 106 | N7 J8 ret3<=-0.70 | 56 / 2.67 / +0.338 / +0.248 / 18.9 / -0.75 | 910 / 2.10 / +0.108 / +0.069 / 98.7 / -9.27 | 2y worst day -9.27 | fail |
| 107 | N8 J8 DI>=-3 | 44 / 2.10 / +0.332 / +0.262 / 14.6 / -0.63 | 720 / 1.66 / +0.116 / +0.077 / 83.9 / -7.79 | PASS | fail |
| 108 | N9 J8 DI>=-7 | 51 / 2.43 / +0.307 / +0.245 / 15.6 / -0.63 | 843 / 1.95 / +0.119 / +0.065 / 99.9 / -7.79 | PASS | fail |
| 109 | N10 J8 without ret12 guard | 54 / 2.57 / +0.322 / +0.279 / 17.4 / -0.63 | 889 / 2.05 / +0.086 / +0.043 / 76.9 / -10.51 | 2y avg R +0.086; 2y w/o best +0.043; 2y worst day -10.51 | fail |
| 110 | N11 J8 without refire | 44 / 2.10 / +0.311 / +0.262 / 13.7 / -0.56 | 699 / 1.61 / +0.131 / +0.097 / 91.6 / -7.79 | 2y trades/session +25% (<25%) | fail |
| 111 | N12 J8 DI>=0 (parent DI) | 38 / 1.81 / +0.338 / +0.256 / 12.8 / -0.64 | 614 / 1.42 / +0.138 / +0.101 / 85.0 / -7.79 | replay trades/session +19% (<25%); 2y trades/session +9% (<25%) | pass |
| 112 | N13 J8 + LEVIX | 56 / 2.67 / +0.321 / +0.255 / 18.0 / -0.63 | 823 / 1.90 / +0.116 / +0.076 / 95.1 / -8.49 | PASS | fail |
| 113 | N14 J8 + ADV>=$50M | 57 / 2.71 / +0.337 / +0.253 / 19.2 / -0.63 | 1003 / 2.32 / +0.115 / +0.076 / 115.1 / -9.49 | 2y worst day -9.49 | fail |
(tps = trades per session; avg, w/o best = avg R per trade after costs; total and worst day in R. Config N1 = WB4.)

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies it after 16:05 ET, effective the next session; one copy: **WB4**. The parent stays in Primary,
unchanged. WB1 (approved tonight) is a different copy; WB4 overlaps WB1's trades (a WB1 dip, ret12 >= +0.5 and DI >= 0,
meets every WB4 condition), so put them in **different** accounts.
Account: a testing account other than WB1's and not Primary — suggested **Testing A** (`config/account_testing2.yaml`,
the setup's first home, full universe), first in `live.setup_order`. Notes for that account: the Testing cost filter
(stop-exit cost > 0.15R) and the 30 bps spread check stay on (they skipped LABD 11-02 and GDXU twice in the live record);
the testing per-setup -2R latch is off, as in the tests.
1. Under `strategies:` add
   ```yaml
   NM-ETF-late-dip-di-long-WB4:
     # Workbench FREQ copy of NM-ETF-late-dip-di-long (Primary), Mechanic 2026-11-17: dip <= -0.75%, DI >= -5, ret12 >= -1.0%,
     # refire; research/workbench/NM-ETF-late-dip-di-long/FREQ/RESULTS.md.
     enabled: true
     type: lab
     module: research/workbench/NM-ETF-late-dip-di-long/modules/NM-ETF-late-dip-di-long-WB4.py
     symbols: module
     min_adv: 95000000
     window: [1400, 1500]
     scale_out_r: null
     refire: true
     refire_cooldown: 1
     tags: [workbench, "parent:NM-ETF-late-dip-di-long", etf]
   ```
2. `config/setup_names.yaml`: `NM-ETF-late-dip-di-long-WB4: {name: "Late-Day ETF Dip Buy — WB4: more dips", side: long, what: "14:00-15:00: buy each sharp 15-min dip (0.75%+) in a volatile ETF while buyers roughly hold (DI balance >= -5), skipping dips inside an hour already down 1%+; can re-enter on a later dip."}`
3. `research/ledger.jsonl`: id `2026-11-17-wb-nmetf-latedip-wb4`, patch `{"strategies.NM-ETF-late-dip-di-long-WB4 (testing2)":
   [null, "added, enabled"]}`, evidence this file; `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments`, `pytest -q`, commit, push after 16:05 ET (setup-freeze).

## Owner decisions (optional)
- **D1 — WB4 next to WB1:** both are improvements of the same parent in different directions (WB1 fewer, better trades;
  WB4 more trades at a slightly better average). Run both in separate testing accounts (recommended) or pick one.
- **D2 — opposite-side conflicts in Primary:** short setups on 3x ETFs (L3-gap-slope-rsi5hi-FD / L3-gap-slope-fromopen-FD,
  RW5, RW3) can block this long ("opposite side held"); ~3% of its signals in the replay window. No change recommended.
