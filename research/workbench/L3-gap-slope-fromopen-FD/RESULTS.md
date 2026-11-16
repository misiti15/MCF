# Workbench RESULTS — Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Primary) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built 10:05-11:30 ET (market hours: research files only).

## Verdict
> **RERUN 2026-11-16 (supervisor standard): `L3-gap-slope-fromopen-FD-WB4` = WB3 + max hold 75 min supersedes WB3** — replay +0.173R, 2-year −0.027R, more trades; see the RERUN section at the end. WB3 is no longer planned for deployment.

| copy | one-line change | replay avg R (parent +0.059) | 2-year avg R (parent −0.048) | verdict |
|---|---|---|---|---|
| `L3-gap-slope-fromopen-FD-WB1` | P6 entry window ends 13:00 instead of 15:00 | **+0.132** | −0.048 (meets) | PASS (meets in 2-year; VALID split slightly worse) |
| `L3-gap-slope-fromopen-FD-WB2` | P4+P10 gap ≤ −3.2% instead of ≤ −2.66% (module + prefilter) | +0.059 (meets) | **−0.036** | PASS |
| `L3-gap-slope-fromopen-FD-WB3` | WB1 + WB2 combined (own config) | **+0.150** | **−0.040** | **PASS — beats the parent in both tests on avg R, avg R w/o best day and worst day; recommended to deploy** |

Pass rule (owner 2026-11-16): meets or exceeds the parent's avg R after costs in BOTH tests (meets = within 0.01R or
≥ 95%), and not worse on avg R w/o best day by > 0.02R or on worst day by > 10%. Parent and copies were scored by the
identical pipeline; the parent's live record is NOT used in the decision (DIAGNOSIS.md uses it for diagnosis only).

**Read this before deploying (honest caveats):**
- The 2-year backtest of the PARENT loses after costs (−0.048R/trade, −233R; TRAIN −0.060, VALID −0.058, FWD +0.112). The
  copies are better than the parent, not profitable over 2 years. Because that base is negative, a copy that trades less
  looks better there almost automatically; the replay (where the parent is positive, +0.059R) is the more telling test,
  and there WB3 adds +12.2R on 132 fewer trades (avg R w/o best day −0.003 → +0.086; best-day share 104% → 50%).
- The improvements are small: paired-by-day t vs parent WB3 +0.56 (replay) / +1.20 (2-year); none clears the counted bar
  (2.26 at N 13). WB3 is worse than the parent in TRAIN (−0.064 vs −0.060) and on up-market days (−0.209 vs −0.160R),
  better in VALID (−0.044 vs −0.058) and FWD (+0.136 vs +0.112).
- The gap ≤ −3.2% part also drops winners: the best live trade (SNAP 10-22, +2.24R) gapped −2.68% and would not be taken.
- The replay uses Primary's book (≤ 30 lots, −2R latch) for parent and copies alike; the testing accounts run 50 lots and
  no latch, so live testing-account numbers will not match these tables one for one.
- The replay universe = the parent's live ETB signal symbol-days; copies that LOOSEN a condition could not be replayed
  (none of the shortlist loosens anything).
# Workbench results - Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` vs its copies

Educational only — not financial advice. Mechanic job 2026-11-16 (market hours: research only; no config change).

**Configs tried: 13** (12 one-part tweaks V01-V12 pre-declared in `variants_decl` before any score + 1 combined copy C1 of two that passed alone). Bar for the paired day-t on the improvement: max(1.5, sqrt(2 ln 13)) = 2.26 (lineage incl. L3LEASH/L3LEASH-2's 26: N 39, bar 2.71). Under the owner's clarified pass rule (2026-11-16: meet-or-exceed the parent on the identical backtests; 'meets' = within 0.01R or >= 95%; not worse on avg R w/o best day by > 0.02R or on worst day by > 10%; no t hurdle) the t is reported, not used to pass. **No copy clears the t bar** — the improvements are small and not statistically distinguishable from noise; they pass on meet-or-exceed only.

## Method (identical for parent and every copy)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any account and passed the shortable+ETB check, 2026-10-12..11-13 (384 symbol-days, 23 sessions with signals). 1-min SIP bars (read-only GET) -> lab frame (mcf.report.engine.lab_frame + daily priors as live). Limit: symbols that never signalled live are not in it, so copies that LOOSEN a condition cannot be replayed (none of the shortlist loosens).
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted), restricted to names shortable+ETB on >= 90% of 26 universe snapshots 10-07..11-13 (E90 proxy, research/l3leash2). Splits TRAIN <= 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: signals on 5-min bar close, refire chain (cooldown), entry at signal-bar close, price >= $5, exits walked on 1-min bars (stop first; target fills only when traded through by >= $0.01 — UGP 10-26 touched without filling; flat 15:55), **LR8 costs** (entry 1 bp + SEC + TAF + CAT; stop max($0.02, 4 bps); time exit max($0.01, 1 bp); target at limit), live book (<= 30 open lots, <= 3 per symbol, -2R net latch). Parent's live journal record NOT used in the pass decision (owner).
- Rule changes inside the replay window (ledger): LR1/LR3/LR5/LR7 (11-12), LR8 cost model (11-12), Primary -2R latch (10-29), Primary size/cap 30 (10-28), moves Testing 1 <-> Primary (10-20, 10-22, 10-30), TEAM-6 (11-10). The replay applies today's rules to every session, so these do not mix into the comparison.

## Side by side (ALL = whole test)

| copy | change | test | trades | win % | avg R | avg R w/o best day | total R | worst day | t vs parent (paired by day) | dR vs parent | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | PARENT | replay | 350 | 53.4% | +0.059 | -0.003 | +20.5 | -9.7 | +0.00 | +0.0 | — |
| parent | PARENT | 2y | 4885 | 49.1% | -0.048 | -0.056 | -232.6 | -28.8 | +0.00 | +0.0 |  |
| WB1 | V01 window end 15:00->13:00 (P6) | replay | 263 | 58.2% | +0.132 | +0.029 | +34.7 | -9.7 | +1.22 | +14.1 | PASS |
| WB1 | V01 window end 15:00->13:00 (P6) | 2y | 4031 | 49.3% | -0.048 | -0.058 | -194.3 | -28.8 | +1.08 | +38.3 |  |
|  | V02 window end 15:00->14:00 (P6) | replay | 312 | 54.8% | +0.061 | -0.019 | +19.1 | -11.9 | -0.24 | -1.5 | FAIL |
|  | V02 window end 15:00->14:00 (P6) | 2y | 4484 | 49.5% | -0.041 | -0.051 | -185.7 | -28.8 | +2.19 | +46.9 | replay worst day -11.9R vs -9.7R (>10% worse) |
|  | V03 window start 09:50->10:05 (P6/P7) | replay | 364 | 53.0% | +0.054 | -0.005 | +19.8 | -9.7 | -0.09 | -0.7 | FAIL |
|  | V03 window start 09:50->10:05 (P6/P7) | 2y | 4821 | 48.4% | -0.059 | -0.066 | -284.3 | -25.1 | -0.79 | -51.7 | 2y avg R -0.059 < parent -0.048 |
|  | V04 target 1.0->0.8R (P22) | replay | 386 | 56.2% | +0.032 | -0.018 | +12.3 | -10.4 | -0.95 | -8.2 | FAIL |
|  | V04 target 1.0->0.8R (P22) | 2y | 5565 | 54.1% | -0.040 | -0.048 | -221.0 | -32.0 | +0.25 | +11.6 | replay avg R +0.032 < parent +0.059; 2y worst day -32.0R vs -28.8R (>10% worse) |
|  | V05 stop 1.0->1.25R (P21) | replay | 397 | 59.2% | +0.098 | +0.052 | +38.7 | -9.7 | +0.88 | +18.2 | FAIL |
|  | V05 stop 1.0->1.25R (P21) | 2y | 5457 | 54.0% | -0.028 | -0.037 | -152.3 | -40.3 | +1.16 | +80.3 | 2y worst day -40.3R vs -28.8R (>10% worse) |
|  | V06 time exit 15:55->15:00 (P24) | replay | 355 | 58.6% | +0.067 | -0.008 | +23.7 | -9.6 | +0.27 | +3.1 | PASS |
|  | V06 time exit 15:55->15:00 (P24) | 2y | 4901 | 50.3% | -0.035 | -0.044 | -173.1 | -29.0 | +1.51 | +59.5 |  |
|  | V07 fromOpen >3.46->>4.0 (P9) | replay | 304 | 51.0% | +0.023 | -0.028 | +7.1 | -7.6 | -0.62 | -13.5 | FAIL |
|  | V07 fromOpen >3.46->>4.0 (P9) | 2y | 4459 | 50.2% | -0.024 | -0.033 | -106.0 | -26.2 | +2.70 | +126.6 | replay avg R +0.023 < parent +0.059; replay w/o best day -0.028 vs -0.003 |
|  | V08 slope >0.372->>0.45 (P11) | replay | 321 | 53.9% | +0.080 | +0.020 | +25.7 | -6.3 | +0.50 | +5.2 | PASS |
|  | V08 slope >0.372->>0.45 (P11) | 2y | 4470 | 49.0% | -0.050 | -0.058 | -224.7 | -26.8 | +0.15 | +7.9 |  |
| WB2 | V09 gap <=-2.66->-3.2 (P4+P10) | replay | 293 | 52.6% | +0.059 | +0.030 | +17.3 | -7.3 | -0.12 | -3.3 | PASS |
| WB2 | V09 gap <=-2.66->-3.2 (P4+P10) | 2y | 4137 | 49.6% | -0.036 | -0.045 | -147.8 | -26.9 | +1.00 | +84.8 |  |
|  | V10 refire cooldown 1->3 bars (P8) | replay | 329 | 54.7% | +0.092 | +0.038 | +30.3 | -8.5 | +0.82 | +9.7 | PASS |
|  | V10 refire cooldown 1->3 bars (P8) | 2y | 4279 | 48.7% | -0.055 | -0.064 | -235.4 | -28.1 | -0.04 | -2.8 |  |
|  | V11 lots per symbol 3->2 (P13) | replay | 297 | 60.3% | +0.131 | +0.082 | +39.0 | -6.5 | +0.90 | +18.5 | PASS |
|  | V11 lots per symbol 3->2 (P13) | 2y | 4208 | 49.5% | -0.045 | -0.053 | -190.5 | -29.1 | +1.06 | +42.1 |  |
|  | V12 open-lot cap 30->40 (P12) | replay | 378 | 53.7% | +0.059 | +0.003 | +22.4 | -9.9 | +0.59 | +1.8 | FAIL |
|  | V12 open-lot cap 30->40 (P12) | 2y | 5033 | 49.1% | -0.049 | -0.058 | -245.4 | -32.5 | -0.69 | -12.8 | 2y worst day -32.5R vs -28.8R (>10% worse) |
| WB3 | C1 window end 13:00 + gap <=-3.2 (P6+P4/P10) | replay | 218 | 58.3% | +0.150 | +0.086 | +32.7 | -7.3 | +0.56 | +12.2 | PASS |
| WB3 | C1 window end 13:00 + gap <=-3.2 (P6+P4/P10) | 2y | 3326 | 49.7% | -0.040 | -0.050 | -133.0 | -26.9 | +1.20 | +99.6 |  |

## 2-year by split (consistency check)

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) | TRAIN dR | VALID dR | FWD dR |
|---|---|---|---|---|---|---|
| PARENT | -0.060 (2218) | -0.058 (2332) | +0.112 (335) | +0.0 | +0.0 | +0.0 |
| V01 window end 15:00->13:00 (P6) | -0.058 (1848) | -0.069 (1898) | +0.155 (285) | +27.6 | +4.2 | +6.5 |
| V02 window end 15:00->14:00 (P6) | -0.048 (2043) | -0.062 (2136) | +0.151 (305) | +35.6 | +2.8 | +8.5 |
| V03 window start 09:50->10:05 (P6/P7) | -0.098 (2139) | -0.045 (2239) | +0.056 (443) | -74.6 | +35.9 | -13.0 |
| V04 target 1.0->0.8R (P22) | -0.066 (2471) | -0.036 (2731) | +0.109 (363) | -28.6 | +38.3 | +1.9 |
| V05 stop 1.0->1.25R (P21) | -0.043 (2524) | -0.026 (2558) | +0.067 (375) | +25.0 | +68.0 | -12.7 |
| V06 time exit 15:55->15:00 (P24) | -0.034 (2226) | -0.058 (2340) | +0.112 (335) | +59.1 | +0.5 | -0.1 |
| V07 fromOpen >3.46->>4.0 (P9) | -0.038 (2023) | -0.035 (2071) | +0.118 (365) | +57.1 | +64.0 | +5.4 |
| V08 slope >0.372->>0.45 (P11) | -0.064 (1993) | -0.060 (2135) | +0.090 (342) | +6.2 | +8.3 | -6.7 |
| V09 gap <=-2.66->-3.2 (P4+P10) | -0.067 (1837) | -0.026 (1990) | +0.085 (310) | +11.1 | +84.9 | -11.2 |
| V10 refire cooldown 1->3 bars (P8) | -0.080 (1894) | -0.056 (2061) | +0.095 (324) | -16.2 | +20.4 | -6.9 |
| V11 lots per symbol 3->2 (P13) | -0.063 (1906) | -0.055 (2011) | +0.136 (291) | +14.8 | +25.4 | +1.9 |
| V12 open-lot cap 30->40 (P12) | -0.065 (2298) | -0.058 (2386) | +0.117 (349) | -14.6 | -1.3 | +3.1 |
| C1 window end 13:00 + gap <=-3.2 (P6+P4/P10) | -0.064 (1511) | -0.044 (1576) | +0.136 (239) | +38.3 | +66.4 | -5.2 |

## Shape (avg win / avg loss, median hold min, exit mix; 2-year by SPY day type open->close >+0.25% up / <-0.25% down)

| config | test | avg win | avg loss | median hold | stop share | target share | up-day avg R | flat | down |
|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | +0.895 | -0.901 | 82 | 34% | 43% |  |  |  |
| PARENT | 2y | +0.893 | -0.957 | 46 | 43% | 42% | -0.160 | -0.010 | +0.075 |
| V01 window end 15:00->13:00 (P6) | replay | +0.917 | -0.960 | 85 | 34% | 50% |  |  |  |
| V01 window end 15:00->13:00 (P6) | 2y | +0.913 | -0.983 | 44 | 45% | 43% | -0.187 | -0.003 | +0.110 |
| V02 window end 15:00->14:00 (P6) | replay | +0.898 | -0.954 | 86 | 36% | 45% |  |  |  |
| V02 window end 15:00->14:00 (P6) | 2y | +0.906 | -0.970 | 46 | 44% | 43% | -0.174 | +0.010 | +0.101 |
| V03 window start 09:50->10:05 (P6/P7) | replay | +0.899 | -0.899 | 76 | 34% | 43% |  |  |  |
| V03 window start 09:50->10:05 (P6/P7) | 2y | +0.891 | -0.952 | 49 | 43% | 41% | -0.165 | +0.000 | +0.044 |
| V04 target 1.0->0.8R (P22) | replay | +0.747 | -0.886 | 62 | 31% | 50% |  |  |  |
| V04 target 1.0->0.8R (P22) | 2y | +0.745 | -0.965 | 36 | 40% | 49% | -0.140 | +0.016 | +0.054 |
| V05 stop 1.0->1.25R (P21) | replay | +0.858 | -1.005 | 97 | 25% | 45% |  |  |  |
| V05 stop 1.0->1.25R (P21) | 2y | +0.890 | -1.106 | 58 | 35% | 46% | -0.170 | +0.028 | +0.114 |
| V06 time exit 15:55->15:00 (P24) | replay | +0.718 | -0.855 | 67 | 29% | 34% |  |  |  |
| V06 time exit 15:55->15:00 (P24) | 2y | +0.820 | -0.901 | 40 | 39% | 37% | -0.146 | +0.024 | +0.061 |
| V07 fromOpen >3.46->>4.0 (P9) | replay | +0.896 | -0.885 | 78 | 35% | 42% |  |  |  |
| V07 fromOpen >3.46->>4.0 (P9) | 2y | +0.896 | -0.950 | 44 | 42% | 43% | -0.124 | +0.017 | +0.074 |
| V08 slope >0.372->>0.45 (P11) | replay | +0.912 | -0.893 | 73 | 33% | 45% |  |  |  |
| V08 slope >0.372->>0.45 (P11) | 2y | +0.890 | -0.953 | 46 | 43% | 42% | -0.141 | -0.006 | +0.048 |
| V09 gap <=-2.66->-3.2 (P4+P10) | replay | +0.893 | -0.865 | 66 | 33% | 44% |  |  |  |
| V09 gap <=-2.66->-3.2 (P4+P10) | 2y | +0.891 | -0.949 | 46 | 42% | 42% | -0.178 | +0.072 | +0.048 |
| V10 refire cooldown 1->3 bars (P8) | replay | +0.899 | -0.883 | 80 | 32% | 44% |  |  |  |
| V10 refire cooldown 1->3 bars (P8) | 2y | +0.879 | -0.940 | 55 | 42% | 40% | -0.160 | -0.013 | +0.070 |
| V11 lots per symbol 3->2 (P13) | replay | +0.842 | -0.947 | 85 | 31% | 45% |  |  |  |
| V11 lots per symbol 3->2 (P13) | 2y | +0.895 | -0.966 | 43 | 44% | 42% | -0.166 | +0.009 | +0.069 |
| V12 open-lot cap 30->40 (P12) | replay | +0.892 | -0.906 | 78 | 34% | 43% |  |  |  |
| V12 open-lot cap 30->40 (P12) | 2y | +0.890 | -0.956 | 47 | 43% | 42% | -0.162 | -0.013 | +0.082 |
| C1 window end 13:00 + gap <=-3.2 (P6+P4/P10) | replay | +0.913 | -0.914 | 66 | 32% | 51% |  |  |  |
| C1 window end 13:00 + gap <=-3.2 (P6+P4/P10) | 2y | +0.905 | -0.974 | 44 | 44% | 43% | -0.209 | +0.080 | +0.079 |

## Replay vs live (sanity check, not used in the verdict)
Parent replay 350 trades +0.059R vs live 340 trades +0.223R on the same sessions. The gap comes mostly from costs (the
replay charges LR8 on every session; live booked the older, lighter allowance until 11-11, ≈ −0.04R/trade per LR8
notes), from entries at the 5-min bar close vs live fills (live slip was often favourable, e.g. SNAP −53.7 bps), and from
the replay's stricter target fill (traded through by $0.01). Same pipeline for parent and copies, so the comparison holds.

## Every configuration tried (13), including failures
V01-V12 pre-declared (code/variants_decl.py) before any score was read; C1 added after V01 and V09 had each passed.
PASS: V01 (=WB1), V06 flat 15:00, V08 slope > 0.45, V09 (=WB2), V10 cooldown 3 bars, V11 ≤ 2 lots/symbol, C1 (=WB3).
FAIL: V02 end 14:00 (replay worst day −11.9 vs −9.7R), V03 start 10:05 (2-year −0.059 vs −0.048), V04 target 0.8R
(replay +0.032; 2-year worst day −32.0R), V05 stop 1.25R (2-year worst day −40.3 vs −28.8R, though avg R better in both),
V07 fromOpen > 4.0 (replay +0.023), V12 cap 40 (2-year worst day −32.5R). Not spawned though passing: V06/V08/V10 (gains
small or one-test only); V11 needs a per-setup lot cap (today `live.max_lots_per_symbol` is account-wide) — backlog idea.

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. One copy only:
**WB3** [SUPERSEDED by WB4 — see RERUN below; do not add WB3] (it contains WB1 and WB2; running all three would put near-twins side by side). The parent stays in Primary, unchanged.
Account: **Testing 2** — not the parent's account (Primary); Testing 1 = Testing 2 in weight, and Testing 1 already runs the
L3 sisters `L3-gap-slope-rsi5hi-FD` / `L3-gap-slope-lowdist-FD` (same gap-down names; they would fight for the 3-lot
symbol cap) plus today's CWT14-WB4 addition. Testing 2 has no L3-family setup. Twin check: `twin_key` strips only `-FD`,
so `...-FD-WB3` is not the parent's twin key; no twin_group needed (different accounts anyway).
1. `config/account_testing2.yaml`, under `strategies:` add
   ```yaml
   L3-gap-slope-fromopen-FD-WB3:
     # Workbench copy of L3-gap-slope-fromopen-FD (Primary), Mechanic 2026-11-16: window ends 13:00 + gap <= -3.2%;
     # research/workbench/L3-gap-slope-fromopen-FD/RESULTS.md. Effective session 2026-11-17.
     refire: true
     refire_cooldown: 1
     enabled: true
     type: lab
     module: research/workbench/L3-gap-slope-fromopen-FD/modules/L3-gap-slope-fromopen-FD-WB3.py
     min_adv: 0
     window: [950, 1300]
     prefilter: "gap_le:-3.2"
     scale_out_r: null
     tags: [workbench, "parent:L3-gap-slope-fromopen-FD"]
   ```
   and put `L3-gap-slope-fromopen-FD-WB3` FIRST in `live.setup_order` (ahead of GEN-261028-01-MACDhge0p12-...).
2. `config/setup_names.yaml`: `L3-gap-slope-fromopen-FD-WB3: {name: "Gap-Down Recovery Fade (all day) — WB3: ends 13:00, gap 3.2%+", side: short, what: "09:50-13:00: a stock that gapped down 3.2%+ has rallied more than 3.5% from its open with its 20-bar average turning up; short the rally."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-l3-fromopen-wb3`, effective 2026-11-17, title "Workbench copy
   L3-gap-slope-fromopen-FD-WB3 added to Testing 2, first in setup_order (Mechanic pass)", patch
   `{"strategies.L3-gap-slope-fromopen-FD-WB3 (testing2)": [null, "added, enabled"], "live.setup_order (testing2)": ["...", "WB3 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5 (passes go to a testing account at once)";
   then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit), `pytest -q`, commit,
   push to claude/charming-mccarthy-i3rhhr after 16:05 ET (setup-freeze).
Low-rep note: WB3 is a new setup (< 20 live trades) — it sits first in Testing 2's order for exposure per RULES 5.

## Files
`code/` (sim.py engine, run.py, variants_decl.py, fetch_replay.py, cand2y.py, paths2y.py, etb.py, extras.py, report.py;
run from a scratch dir holding their inputs), `results_main.csv`, `results_combo.csv`, `extras.csv`, `variants.jsonl`.

---

# RERUN 2026-11-16 (supervisor standard) — WB4 supersedes WB3
Educational only — not financial advice. Mechanic RERUN, built 11:15-12:30 ET (market hours: research files only).
Owner 2026-11-16: "the supervisor would want improvements without caveats ... the finished outgoing setup needs to perform
better OVERALL even if it means a slight decrease under certain conditions". Bar for this rerun = beat **WB3** (not only the
parent) in BOTH identical tests, without trading less to get there.

Images: engine `L3-gap-slope-fromopen-FD_engine.png`; 5 worst live trades `_trade1_RRGB`, `_trade2_UGP`, `_worst3_JBS`,
`_worst4_JBS`, `_worst5_QLYS`; 5 best `_best1_SNAP`, `_best2_SNAP`, `_best3_PBR`, `_best4_CRWV`, `_best5_CLSK`;
equity curves parent / WB3 / WB4 `_rerun_curves.png`.

## Method (unchanged from the first run; parent, WB3 and every copy scored identically)
Same engine (`code/sim2.py` = `sim.py` + optional layers, all off by default; it reproduces the first run's parent and WB3 to
the trade: 350 / +0.059, 4885 / −0.048, 218 / +0.150, 3326 / −0.040). Live-session replay 10-12..11-13 (384 ETB symbol-days)
and 2-year backtest (open months only, locked block 2024-11-01..2025-02-28 never read — asserted), same E90 borrow proxy, same
TRAIN ≤ 2025-12-31 / VALID ..2026-10-05 / FWD ..11-04 split, LR8 costs, Primary book for all (≤ 30 open lots, ≤ 3 per symbol
unless a config says 2, −2R latch). SPY 1-min for the 09:50 gates: cache to 11-04 + read-only SIP GET 10-12..11-13.
Parent's live record used to diagnose only. Rule changes inside the replay window: as in the first run (LR1/3/5/7/8 11-12,
Primary latch 10-29, cap 30 10-28, moves 10-20/10-22/10-30, TEAM-6 11-10); the replay applies today's rules to every session.

## Evidence — 5 worst + 5 best live trades (prices/times on the PNGs)
| trade | what happened | part | WB3 | WB4 (WB3 + max hold 75 min) |
|---|---|---|---|---|
| RRGB 10-15 −1.71R | refire short 10:32:33 @ 8.75, 1R $0.09, stop 10:38:00 @ 8.89 | P10 gap −2.71% | not taken | not taken |
| UGP 10-26 −1.42R | short 12:35:53 @ 6.47, touched +1.42R target 12:47 unfilled, stop 13:07:33 @ 6.52 | P22 touch-no-fill | taken, −1.42 | taken, −1.42 (stopped at 32 min) |
| JBS 10-22 −1.37R | short 11:35:47 @ 12.21, best +0.09R, drifted 2h20m, stop 13:58:10 @ 12.35 | P24 (no time limit) | taken, −1.37 | out 12:50 @ ~12.30: ≈ −0.75R |
| JBS 10-22 −1.34R | refire 11:45:45 @ 12.22, best +0.14R, stop 13:58:11 @ 12.34 | P24 + P8 | taken, −1.34 | out 13:00 @ ~12.28: ≈ −0.5R |
| QLYS 10-29 −1.32R | refire 14:05:39 @ 225.80, never green, stop 15:55:22 @ 230.17 | P6 late entry | not taken | not taken |
| SNAP 10-22 +2.24R / +1.73R | 11:40:54 @ 6.55 → target 12:51:17; 11:50:54 @ 6.57 → target 12:22:13 | — | not taken (gap −2.68%) | not taken |
| PBR 10-26 +1.71R | 14:35:48 @ 22.68 → target 15:02:07 @ 22.47 | — | not taken (after 13:00) | not taken |
| CRWV 10-20 +1.66R | 10:41:12 @ 63.68 → target 14:42:47 @ 61.80 (4 h) | — | not taken (gap −3.04%) | not taken (would be +0.96R at 75 min) |
| CLSK 10-20 +1.50R | 10:41:08 @ 8.80 → target 11:14:17 @ 8.55 | — | not taken (gap −3.19%) | not taken |
WB3's gap/window parts remove 3 of the 5 worst but also all 5 of the best live trades; re-tested in round 6 (gap −2.66 / −3.0
with the new exit): both worse than WB4 in both tests, so the −3.2% gap stays.

## What the parts showed (all-trades component analysis, WB3 trades: replay 218, 2-year 3,326)
1. **P24 time exit is the part that pays.** Losers drift: 441 2-year stops had been +0.5R first; time exits averaged MFE
   +0.64R but ended at +0.01R. A plain 60/75/90-min cap beats WB3 in both tests at every length (2y −0.037/−0.027/−0.036,
   replay +0.161/+0.173/+0.178) and in every 2-year split; it frees book slots, so it trades MORE (2y 3,326 → 3,495).
   Conditional "not working yet" stops (exit only if best < 0.3-0.75R) are worse (I2-I5) — the fixed clock is the edge.
2. **Up-day gates measured after 09:50 do not travel.** SPY up > 0.15/0.30% since 09:50 lifts the 2-year (to −0.006) but cuts
   the replay to +0.048/+0.105; SPY above its 09:30-09:50 high is worse in both. The 2-year "up day" loss is an open→close
   label not visible at entry. (Compass state has no 2-year history: not testable on identical terms.) WB4 still softens up
   days by exits: 2-year up-day avg R −0.209 → −0.127.
3. **Target and entry-guard tweaks are noise.** Touch-fills target (1 cent shallower) −0.005/−0.003; target 0.95R replay
   +0.125; BE / profit-lock stops ±0.01; fromOpen ≤ 10 / VWAP ≤ 4% / 1R ≥ 1% of price each lose in one test.
4. **Max 2 lots per symbol is not a stand-alone add-on here.** On WB3 it lifts the replay (+0.196) but lowers the 2-year
   (−0.049); on WB4 (I1) it lowers both. It only helps together with a 1.25R stop (G1/H1) — interaction, see below.

## Copies table (identical tests; parent's live stats not used)
| copy | change | replay avg R | 2-year avg R | w/o best day (replay / 2y) | worst day (replay / 2y) | trades (replay / 2y) | R per day (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|
| parent | — | +0.059 | −0.048 | −0.003 / −0.056 | −9.7 / −28.8 | 350 / 4,885 | +0.89 / −0.56 | — |
| WB3 | 13:00 end + gap ≤ −3.2% | +0.150 | −0.040 | +0.085 / −0.050 | −7.3 / −26.9 | 218 / 3,326 | +1.42 / −0.32 | superseded |
| **WB4** | **WB3 + max hold 75 min (P24)** | **+0.173** | **−0.027** | **+0.134 / −0.034** | **−7.3 / −22.2** | **236 / 3,495** | **+1.78 / −0.23** | **PASS — recommended** |
| (G1, not spawned) | WB3 + stop 1.25R + hold 90 + 2 lots | +0.251 (+0.201 in its own 1.25R risk units) | −0.027 (−0.022) | +0.185 / −0.033 | −5.2 / −22.6 | 246 / 3,076 | +2.68 / −0.20 | best numbers, not deployable: needs 2 runner hooks; 2-lot gain is an interaction |
WB4 by 2-year split vs WB3: TRAIN −0.048 vs −0.064, VALID −0.036 vs −0.044, FWD +0.148 vs +0.136 (better in all three).
Day type (2y SPY open→close): up −0.127 vs −0.209, flat +0.035 vs +0.080, down +0.051 vs +0.079 (gives a little back on
flat/down days, gains more on up days). Replay best-day share 50% → 37%. Avg win/loss +0.736/−0.775 vs +0.905/−0.974;
exit mix (2y) time 40% / target 30% / stop 30%; median hold 47 min. Paired-by-day t vs WB3 +0.53 (replay) / +0.54 (2y);
vs parent +0.62 / +1.32. Same-entry effect (2y): 1,258 exits changed, 621 better (+436R) / 637 worse (−419R) = +17R, plus
186 extra trades from freed slots +16R; replay 45 better (+35.8R) / 54 worse (−26.5R).

## Supervisor sign-off
WB4 = WB3 with one added part: every lot is closed at market 75 minutes after entry (config `time_stop_min: 75`,
`time_stop_min_r: 99` — runner time stop, no code change). Why: the setup's losers are slow drifts (JBS 10-22 ×2, 2h20m to
the stop); the backtests show a fixed clock removes more loss than winner give-back. Overall before → after (WB3 → WB4):
replay +0.150 → +0.173R/trade, 2-year −0.040 → −0.027R/trade, w/o best day +0.085 → +0.134 / −0.050 → −0.034, worst day
−7.3 → −7.3 / −26.9 → −22.2, with MORE trades (218 → 236, 3,326 → 3,495) and better R per day in both tests. Gives back:
avg win shrinks (0.91 → 0.74R), flat/down 2-year days slightly lower, long-running winners like CRWV 10-20 (target after 4 h)
are cut near +1R. Not hidden: the improvement is small (t ≈ 0.5 vs WB3; counted bar 2.77 at N 46, 2.86 with the first run's
13 — not cleared; passes on meet-or-exceed) and the 2-year is still below zero after costs (−0.027R) — WB4 is the better car,
not yet a proven profitable one; live testing decides. Signed off for Testing A.

## Configs counted: 46 (rerun) + 13 (first run) = 59; L3 lineage incl. L3LEASH/-2: 85
Pre-declared in rounds (`code/decl2.py`), each round declared before its scores. Every configuration (ALL rows; vs WB3 =
beats WB3's avg R in both tests and not worse on w/o best day by > 0.02R or worst day by > 10%):

| config (on top of WB3 unless named) | replay n | replay avg R | replay w/o best | replay worst day | 2y n | 2y avg R | 2y w/o best | 2y worst day | 2y R/day | vs WB3 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 +2 lots/symbol | 211 | +0.196 | +0.138 | -6.4 | 2862 | -0.049 | -0.059 | -28.7 | -0.34 | 2y avg R lower |
| A2 +cooldown 3 | 175 | +0.174 | +0.107 | -6.2 | 2833 | -0.066 | -0.078 | -29.6 | -0.45 | 2y avg R lower; w/o best day worse |
| A3 +slope>0.45 | 177 | +0.134 | +0.052 | -6.3 | 2924 | -0.037 | -0.048 | -25.3 | -0.26 | replay avg R lower; w/o best day worse |
| A4 +flat 15:00 | 218 | +0.168 | +0.104 | -7.3 | 3326 | -0.034 | -0.043 | -26.8 | -0.27 | beats WB3 |
| A5 +2 lots +cooldown 3 | 153 | +0.132 | +0.065 | -5.2 | 2573 | -0.075 | -0.086 | -29.6 | -0.46 | replay avg R lower; 2y avg R lower; w/o best day worse |
| A6 +2 lots +flat 15:00 | 211 | +0.194 | +0.152 | -5.2 | 2862 | -0.047 | -0.056 | -28.7 | -0.32 | 2y avg R lower |
| B1 skip SPY>+0.30% since 09:50 | 175 | +0.105 | +0.032 | -7.3 | 2476 | -0.030 | -0.043 | -26.8 | -0.18 | replay avg R lower; w/o best day worse |
| B2 skip SPY>+0.15% since 09:50 | 124 | +0.048 | +0.017 | -7.3 | 2061 | -0.006 | -0.021 | -23.3 | -0.03 | replay avg R lower; w/o best day worse |
| B3 skip SPY above 09:30-09:50 high | 131 | +0.141 | +0.057 | -6.3 | 1955 | -0.045 | -0.063 | -25.8 | -0.21 | replay avg R lower; 2y avg R lower; w/o best day worse |
| C1 target 1c shallower (touch fills) | 218 | +0.145 | +0.083 | -7.3 | 3386 | -0.043 | -0.052 | -27.0 | -0.35 | replay avg R lower; 2y avg R lower |
| C2 target 0.95R | 219 | +0.125 | +0.063 | -7.3 | 3391 | -0.036 | -0.045 | -27.3 | -0.29 | replay avg R lower; w/o best day worse |
| D1 BE stop after +0.5R | 224 | +0.160 | +0.099 | -7.3 | 3732 | -0.034 | -0.042 | -26.4 | -0.31 | beats WB3 |
| D2 stop->+0.2R after +0.6R | 225 | +0.141 | +0.082 | -7.3 | 3837 | -0.043 | -0.050 | -24.8 | -0.39 | replay avg R lower; 2y avg R lower |
| D3 stop->+0.4R after +0.75R | 224 | +0.127 | +0.068 | -7.3 | 3675 | -0.036 | -0.046 | -26.1 | -0.32 | replay avg R lower |
| D4 max hold 90 min | 225 | +0.178 | +0.128 | -7.3 | 3371 | -0.036 | -0.043 | -23.7 | -0.29 | beats WB3 |
| D5 stop 1.25R | 240 | +0.202 | +0.147 | -9.4 | 3481 | -0.031 | -0.041 | -35.7 | -0.26 | worst day >10% worse |
| D6 stop 1.25R +2 lots | 218 | +0.281 | +0.153 | -5.8 | 2971 | -0.037 | -0.047 | -35.8 | -0.26 | worst day >10% worse |
| E1 1R >= 1.0% of price | 193 | +0.109 | +0.028 | -7.3 | 2694 | -0.066 | -0.081 | -27.0 | -0.43 | replay avg R lower; 2y avg R lower; w/o best day worse |
| E2 fromOpen <= 10 | 230 | +0.162 | +0.103 | -7.3 | 3255 | -0.043 | -0.053 | -29.3 | -0.34 | 2y avg R lower |
| E3 VWAP dist <= 4% | 228 | +0.155 | +0.094 | -6.3 | 3194 | -0.039 | -0.048 | -26.8 | -0.30 | beats WB3 |
| F1 BE@0.5 + hold 90 | 232 | +0.169 | +0.119 | -7.3 | 3773 | -0.042 | -0.048 | -26.1 | -0.38 | 2y avg R lower |
| F2 hold 60 | 257 | +0.161 | +0.125 | -7.3 | 3608 | -0.037 | -0.045 | -22.7 | -0.32 | beats WB3 |
| F3 hold 120 | 220 | +0.163 | +0.096 | -7.3 | 3343 | -0.047 | -0.056 | -25.8 | -0.38 | 2y avg R lower |
| F4 stop 1.25 + BE@0.5 | 252 | +0.166 | +0.111 | -9.4 | 3933 | -0.029 | -0.036 | -33.7 | -0.27 | worst day >10% worse |
| F5 stop 1.25 + hold 90 | 255 | +0.156 | +0.109 | -8.2 | 3599 | -0.027 | -0.034 | -28.3 | -0.23 | worst day >10% worse |
| F6 stop 1.25 + BE@0.5 + hold 90 | 261 | +0.152 | +0.105 | -7.4 | 3995 | -0.034 | -0.039 | -30.0 | -0.32 | worst day >10% worse |
| F7 F1 + 2 lots | 232 | +0.138 | +0.098 | -5.2 | 3330 | -0.047 | -0.053 | -25.7 | -0.37 | replay avg R lower; 2y avg R lower |
| F8 F1 + skip SPY>+0.30 | 182 | +0.123 | +0.057 | -7.3 | 2747 | -0.043 | -0.052 | -23.5 | -0.29 | replay avg R lower; 2y avg R lower; w/o best day worse |
| F9 BE@0.4 | 228 | +0.150 | +0.093 | -7.4 | 3871 | -0.040 | -0.047 | -23.7 | -0.37 | beats WB3 |
| F10 F6 + 2 lots | 252 | +0.234 | +0.166 | -5.2 | 3498 | -0.049 | -0.055 | -28.4 | -0.41 | 2y avg R lower |
| F11 F1 + slope>0.45 | 209 | +0.180 | +0.133 | -6.3 | 3312 | -0.053 | -0.059 | -24.6 | -0.42 | 2y avg R lower |
| G1 stop 1.25 + hold 90 + 2 lots | 246 | +0.251 | +0.185 | -5.2 | 3076 | -0.027 | -0.033 | -22.6 | -0.20 | beats WB3 |
| G2 hold 90 + 2 lots | 223 | +0.136 | +0.095 | -5.8 | 2949 | -0.039 | -0.045 | -23.1 | -0.28 | replay avg R lower |
| G3 stop 1.25 + hold 60 | 253 | +0.157 | +0.110 | -8.1 | 3871 | -0.019 | -0.027 | -22.8 | -0.18 | worst day >10% worse |
| G4 stop 1.15 + hold 90 | 224 | +0.167 | +0.116 | -7.3 | 3613 | -0.026 | -0.035 | -24.2 | -0.22 | beats WB3 |
| G5 hold 75 | 236 | +0.173 | +0.134 | -7.3 | 3495 | -0.027 | -0.034 | -22.2 | -0.23 | beats WB3 |
| G6 stop 1.25 + hold 75 | 261 | +0.175 | +0.130 | -7.4 | 3706 | -0.021 | -0.027 | -25.8 | -0.18 | beats WB3 |
| H1 stop 1.25 + hold 75 + 2 lots | 262 | +0.235 | +0.177 | -5.6 | 3173 | -0.024 | -0.030 | -21.0 | -0.18 | beats WB3 |
| I1 hold 75 + 2 lots | 229 | +0.155 | +0.120 | -5.7 | 3014 | -0.036 | -0.043 | -21.1 | -0.26 | beats WB3 |
| I2 60 min if best < 0.5R | 240 | +0.129 | +0.066 | -8.2 | 3434 | -0.044 | -0.052 | -23.1 | -0.36 | replay avg R lower; 2y avg R lower; worst day >10% worse |
| I3 45 min if best < 0.3R | 236 | +0.133 | +0.068 | -6.5 | 3428 | -0.045 | -0.056 | -25.5 | -0.37 | replay avg R lower; 2y avg R lower |
| I4 75 min if best < 0.75R | 232 | +0.172 | +0.117 | -7.3 | 3452 | -0.038 | -0.046 | -23.7 | -0.32 | beats WB3 |
| I5 90 min if best < 0.5R | 226 | +0.161 | +0.096 | -7.3 | 3325 | -0.049 | -0.057 | -26.2 | -0.39 | 2y avg R lower |
| J1 window 13:00 + hold 75 (gap -2.66) | 289 | +0.057 | -0.019 | -8.1 | 4229 | -0.044 | -0.050 | -23.4 | -0.45 | replay avg R lower; 2y avg R lower; w/o best day worse; worst day >10% worse |
| J2 parent + hold 75 | 425 | -0.005 | -0.051 | -8.1 | 5321 | -0.036 | -0.041 | -23.4 | -0.46 | replay avg R lower; w/o best day worse; worst day >10% worse |
| J3 window 13:00 + gap -3.0 + hold 75 | 263 | +0.138 | +0.089 | -7.3 | 3796 | -0.033 | -0.039 | -23.1 | -0.30 | replay avg R lower |

Failures and not-kept, in short: up-day gates B1-B3 and F8 (replay falls); targets C1/C2; BE/lock D1-D3/F9 (tiny or mixed);
stop 1.25R alone D5/F4 (2y worst day −35.7/−33.7R) and every stop 1.15-1.25R copy not deployable (LabStrategy GEOMS has no
t1s125; with risk-based sizing its R is ÷1.25); conditional time stops I2-I5; 2 lots I1/A1/G2/F7 (inconsistent); refire
cooldown A2/A5 (2y worse); slope 0.45 A3/F11 (replay lower); entry guards E1-E3; gap −2.66/−3.0 with hold 75 J1-J3; passed
but not chosen: A4 flat 15:00 (no effect beyond hold 75), D4/F2 hold 90/60 (neighbours, slightly behind), G4/G6/H1/G1 (stop
1.25R). Next-step idea (backlog, not built): G1/H1 = WB4 + 1.25R stop + per-setup 2-lot cap, once the runner has a
`t1s125` geom and the per-setup lot cap.

## Pending config change — "ready to deploy after close" (NOT applied; replaces WB3's planned slot)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. **WB4 replaces WB3**
in the plan above (do NOT add WB3). Account: **Testing A** (`config/account_testing2.yaml`), FIRST in `live.setup_order`.
Parent stays in Primary unchanged. Twin check as for WB3 (`...-FD-WB4` is not the parent's twin key; different account).
1. `config/account_testing2.yaml`, under `strategies:` add
   ```yaml
   L3-gap-slope-fromopen-FD-WB4:
     # Workbench copy of L3-gap-slope-fromopen-FD (Primary), Mechanic RERUN 2026-11-16: window ends 13:00 + gap <= -3.2%
     # + every lot closed 75 min after entry; research/workbench/L3-gap-slope-fromopen-FD/RESULTS.md (RERUN). Effective 2026-11-17.
     refire: true
     refire_cooldown: 1
     enabled: true
     type: lab
     module: research/workbench/L3-gap-slope-fromopen-FD/modules/L3-gap-slope-fromopen-FD-WB4.py
     min_adv: 0
     window: [950, 1300]
     prefilter: "gap_le:-3.2"
     scale_out_r: null
     time_stop_min: 75
     time_stop_min_r: 99.0
     tags: [workbench, "parent:L3-gap-slope-fromopen-FD"]
   ```
   and put `L3-gap-slope-fromopen-FD-WB4` FIRST in `live.setup_order`.
2. `config/setup_names.yaml`: `L3-gap-slope-fromopen-FD-WB4: {name: "Gap-Down Recovery Fade (all day) — WB4: ends 13:00, gap 3.2%+, 75-min hold", side: short, what: "09:50-13:00: a stock that gapped down 3.2%+ has rallied more than 3.5% from its open with its 20-bar average turning up; short the rally; out at target, stop or 75 minutes."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-l3-fromopen-wb4`, effective 2026-11-17, title "Workbench copy
   L3-gap-slope-fromopen-FD-WB4 added to Testing A, first in setup_order (Mechanic RERUN pass; replaces planned WB3)", patch
   `{"strategies.L3-gap-slope-fromopen-FD-WB4 (testing2)": [null, "added, enabled"], "live.setup_order (testing2)": ["...", "WB4 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments`, `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: Testing A runs 50 lots and no −2R latch, so live numbers will not match the Primary-book tables one for one; the runner's
time stop acts on its poll (≈ 1 min), the backtest exits at the next 1-min open after 75 min.
