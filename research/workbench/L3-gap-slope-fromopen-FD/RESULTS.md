# Workbench RESULTS — Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Primary) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built 10:05-11:30 ET (market hours: research files only).

## Verdict
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
**WB3** (it contains WB1 and WB2; running all three would put near-twins side by side). The parent stays in Primary, unchanged.
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
