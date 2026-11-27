Educational only — not financial advice.

# UPDAY_1127 — long mechanisms for up / squeeze days (COVERAGE): **FAIL (0/16)**

## In plain words
We pre-registered 16 long-only configurations (PREREG.md, committed before scoring) across three mechanisms:
**SQZ** (gap-down, weak names that reclaim VWAP after 10:30 — the short-squeeze shape that hurt Primary on 11-25),
**RSL** (relative-strength leaders on a weak open that reclaim their open — the 11-27 shape) and **GUP** (gap-up names
whose VWAP pullback holds). **None passes, and none is a LEAD.** After LIVE-L costs every config is at or below zero on
out-of-sample data (CHECK 2025-10..2026-11-04 and T2 2023-01..2024-09). The best is R1/R3 (RSL core) at **−0.004R/trade**
(n 950, day t −0.07), with only a +0.07R gross edge before costs.

The useful finding is about **hedging**. SQZ does what the hypothesis predicted on the days that matter. Its daily R is
**negatively correlated with Primary's bench daily R: −0.25 for S1 and −0.32 for S2** (−0.30 / −0.34 on CHECK). On
Primary's worst 20% of days it makes **+0.8 to +1.7R per day**, while it loses −0.6 to −1.1R on other days. On V-days
(SPY weak at 09:49 and closing above its open, the 11-25 / 11-27 shape) it averages **+1.07R per trade** on CHECK (S1).
But that is a market-direction bet, not an edge. Gross R is about 0 (+0.007 S1, +0.014 S2), and SQZ trades lose on
DOWN days about as much as they win on UP days. It also does not beat random names entered at the same minute with the
same stop size (S1 −0.100 vs random p95 −0.027). Paying LIVE-L costs (about 0.10R) for a beta hedge is the same wall
that HEDGE-B hit on 11-26.

GUP fails clearly (−0.17 to −0.23R/trade; win rate about 21%). The 0.10 ATR stop under VWAP is tight (median 62 bp),
so costs and the +1 min stress (−0.31R) wreck it. RSL without the weak-open gate (R2) is a pure up-day bet: +0.25 to
+0.32R/trade on UP days, −0.32 to −0.36 on DOWN days, −0.027 overall.

**Why the hypothesis fails:** the long side of a squeeze / V-day pays only when the day turns, and none of the
point-in-time triggers we tried (VWAP reclaim after 10:30, reclaiming the open with RS, VWAP hold after a gap-up) tells
in advance whether the turn will hold. Each trigger fires about as often on days that roll back over.

## Count and bars
16 configs → **cumulative N ≈ 9,300 → ≈ 9,316**. Study bar: pooled OOS day-clustered t ≥ 2.96 (Bonferroni 0.05/16,
two-sided). Lineage bar about t ≥ 4.3 (descriptive). Locked block 2024-11-01..2025-02-28 never read (pyarrow filter at
load + asserts on every output). EARLY (pre-2023): no single-stock minute data, so not available. FIT was reported only,
and nothing was tuned on it.

## Every config (R per trade, LIVE-L unless stated; OOS = CHECK + T2 pooled; day t on day means)
| Cfg | Rule | FIT n / R | CHECK n / R | T2 n / R | OOS t | OOS gross / LR8 / stress | Random p95 (beats/20) | Corr w/ Primary | R/day on Primary worst-20% vs other | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | SQZ core (gap ≤ −1%, ret20 bottom 30%, below VWAP 09:50-10:29, reclaim 10:30-13:30) | 310 / −0.116 | 980 / −0.123 | 574 / −0.061 | −3.97 | +0.007 / −0.075 / −0.133 | −0.027 (4) | −0.25 | +0.82 vs −0.65 | FAIL |
| S2 | S1 w/o crowding proxy | 749 / −0.050 | 1876 / −0.109 | 1264 / −0.074 | −4.37 | +0.014 / −0.067 / −0.138 | −0.075 (12) | **−0.32** | **+1.70 vs −1.11** | FAIL |
| S3 | S1 gap ≤ −3% | 66 / −0.344 | 311 / −0.031 | 91 / −0.095 | −1.10 | +0.036 / −0.021 / −0.058 | +0.006 (14) | −0.17 | +0.44 vs −0.20 | FAIL |
| S4 | S1 + reclaim-bar vol ≥ 2× | 96 / −0.038 | 334 / −0.096 | 92 / +0.013 | −2.52 | +0.035 / −0.052 / −0.108 | +0.002 (4) | −0.17 | +0.32 vs −0.18 | FAIL |
| S5 | S1 TRAIL | 310 / −0.148 | 980 / −0.128 | 574 / −0.098 | −4.66 | −0.007 / −0.098 / −0.150 | −0.057 (2) | −0.26 | +0.67 vs −0.65 | FAIL |
| S6 | S1 window 10:30-12:00 | 253 / −0.090 | 865 / −0.113 | 477 / −0.023 | −3.54 | +0.027 / −0.057 / −0.114 | −0.039 (12) | −0.24 | +0.81 vs −0.54 | FAIL |
| R1 | RSL core (SPY ≤ −0.20% at 09:49, RS ≥ +0.5%, dipped below open, reclaim by 11:30, top 10 by RS) | 220 / +0.028 | 410 / +0.010 | 540 / −0.014 | −0.07 | +0.067 / +0.030 / −0.004 | +0.027 (13) | −0.05 | +0.15 vs −0.01 | FAIL |
| R2 | R1 w/o weak-open gate | 1410 / +0.029 | 2760 / −0.022 | 4270 / −0.029 | −1.32 | +0.039 / −0.003 / −0.044 | −0.048 (20) | −0.21 | +1.24 vs −0.38 | FAIL |
| R3 | R1 RS ≥ +1.0% (identical trades to R1: the top-10-by-RS names already clear 1.0%) | = R1 | = R1 | = R1 | −0.07 | = R1 | +0.012 (11) | −0.05 | = R1 | FAIL |
| R4 | R1 TRAIL | 220 / +0.040 | 410 / −0.006 | 540 / −0.038 | −0.55 | +0.049 / +0.009 / −0.042 | +0.013 (6) | −0.08 | +0.24 vs −0.04 | FAIL |
| R5 | R1 SPY ≤ −0.40% | 70 / +0.080 | 70 / +0.246 | 140 / −0.211 | −0.50 | +0.015 / −0.016 / −0.085 | +0.193 (0) | −0.01 | +0.07 vs +0.05 | FAIL |
| G1 | GUP core (gap ≥ +2%, holds VWAP, pullback 10:00-12:00) | 762 / −0.203 | 1956 / −0.139 | 1062 / −0.239 | −1.28 | −0.003 / −0.207 / −0.313 | −0.111 (13) | +0.02 | −0.84 vs −0.99 | FAIL |
| G2 | G1 gap ≥ +4% | 282 / −0.432 | 936 / −0.178 | 290 / −0.188 | −2.49 | −0.031 / −0.206 / −0.345 | −0.025 (1) | +0.06 | −1.24 vs −0.50 | FAIL |
| G3 | G1 + rvol ≥ 2 | 501 / −0.210 | 1156 / −0.242 | 581 / −0.199 | −2.78 | −0.053 / −0.257 / −0.383 | −0.122 (0) | −0.00 | −0.64 vs −0.92 | FAIL |
| G4 | G1 TRAIL | 762 / −0.221 | 1956 / −0.168 | 1062 / −0.232 | −4.96 | −0.018 / −0.242 / −0.315 | −0.162 (8) | +0.07 | −1.88 vs −0.92 | FAIL |
| G5 | G1 on weak-open days | 124 / −0.512 | 226 / +0.075 | 77 / −0.695 | −0.93 | +0.047 / −0.142 / −0.254 | +0.003 (11) | +0.06 | −0.10 vs −0.11 | FAIL |

Concentration: no config has a positive OOS total, so best-day share is undefined. Avg R without the best day is
negative everywhere (S2 −0.107, R1 −0.024, G1 −0.192). Bars missed by every config: (a), (b), (c), (e). Only R2 beats
its random control 20/20, because its random names are worse, not because R2 is positive.

## R by day type (LIVE-L R/trade; SPY open→close UP > +0.25%, DOWN < −0.25%; V = SPY ≤ −0.20% at 09:49 and closes up)
| Cfg | CHECK UP / FLAT / DOWN / V | T2 UP / FLAT / DOWN / V | CHECK R per V-day |
|---|---|---|---|
| S1 | +0.23 / −0.10 / −0.45 / **+1.07** | +0.20 / −0.02 / −0.34 / +0.40 | +5.8 |
| S2 | +0.13 / −0.10 / −0.37 / +0.80 | +0.18 / −0.02 / −0.35 / +0.58 | +6.5 |
| R1 | +0.23 / +0.04 / −0.15 / +0.18 | +0.17 / −0.03 / −0.11 / +0.10 | +1.8 |
| R2 | +0.25 / −0.04 / −0.32 / +0.18 | +0.32 / −0.16 / −0.36 / +0.10 | +1.8 |
| G1 | +0.25 / −0.25 / −0.48 / +0.13 | +0.09 / −0.33 / −0.66 / −0.13 | +0.7 |
Every mechanism is long beta: it pays on UP and V days and gives it back on DOWN days. SQZ has the largest V-day payoff
(+1.07R/trade on CHECK), which matches the 11-25 squeeze story. But V-days cannot be known at 10:30: the same reclaim on
a day that rolls over loses −0.45R.

## Hedge view (Primary 4 bench daily R, FIT + CHECK, 446 days)
Primary proxy: bench10 walked lots for L3-fromopen / RW3 / RW5 / NM-ETF (LONGBOOK's walk_t1, built tonight), LIVE-L on
shorts / LR8 on NM-ETF, cap 30 lots per day by entry minute, **no −2R latch** (simplified, disclosed). Mean −2.36R/day;
worst-20% days average −16.7R. S2 lifts those days to −15.0R (+1.7R/day), at a cost of −1.1R on the other 80% of days.
Net over all days: −0.55R/day. A hedge that pays 1.7R on bad days and costs 1.1R on all other days loses money overall
unless it is sized and gated. A gate needs a day call, which is the unsolved part (PMDIR, DAYTYPE, GAPNEWS: all FAIL).
T2 correlation was not computed (no T2 walk built). Live sessions (11-25, 11-27) are outside the bar cache (ends
2026-11-04), so there is no live replay.

## What can be salvaged (optimism, honestly)
- **SQZ as a Primary hedge sleeve** is the only mechanism with a real, stable sign. Correlation is −0.24 to −0.32 in
  every SQZ variant on both FIT and CHECK, and the V-day payoff is positive on both CHECK and T2. Its problem is cost
  per unit of hedge (gross about 0). A cheaper vehicle for the same exposure (one index long on the days Primary's
  gap-down shorts are crowded, triggered at the SQZ moment: SPY/QQQ reclaiming VWAP after 10:30 on a gap-down-heavy
  morning) would pay about 1/5 of the costs. That is a new pre-registered idea, not tested here. It overlaps HEDGE-B's
  "one-shot hedge" salvage lead.
- **RSL core (R1)** is the closest to flat (+0.067R gross, LR8 +0.030, LIVE-L −0.004). It is not tradeable as is. Any
  rework (e.g. a wider target, a better exit) would be a new lineage under RESEARCH_RULES 18.
- Caveats: the universe includes leveraged / inverse ETFs (e.g. QID, PSQ, SPXU appear among the top trades); PREREG did
  not exclude them. Short interest / float are not available point-in-time, so the crowding proxy is ret20 in the
  bottom 30% plus a gap down. Removing the proxy (S2) changes little, so the proxy is not what drives the result.

## Rule-change context
History only (FIT / CHECK / T2 replay the same rules on every day), so no ledger effective date falls inside these
figures. Ledger changes in effect for the motivating live days (11-25, 11-27): 11-23 burst brake / PSHADOW / ST7 out of
Primary; 11-27 GYH V1+V3, GEN seed, ROT-B3 (testing / Graveyard). Next: 11-30 AV50 / ETF-STOP50.

## Files
PREREG.md (+ sha256), up_build.py (candidates, exits, stress), up_rand.py (size-matched random control, 20 draws),
up_score.py (configs, bars, day types, hedge view), up_primary.py (Primary bench daily R proxy), results.json.
Scratch data (about 55 MB) was deleted after scoring. No config/, setup, exit, assignments, decisions or ledger change.
