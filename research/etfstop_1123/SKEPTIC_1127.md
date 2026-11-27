Educational only — not financial advice.

# SKEPTIC_1127: adversarial review of AV50 (ETF-STOP50 variant) before it goes into Primary

Research only: no config, setup or exit change. Owner approved AV50 for `NM-ETF-late-dip-di-long` on 2026-11-24 ("yes so long as testing shows it only costs ~2.2R a year"). The inspector's rule (research/inspector_1127, item 7 and "stop doing") requires a size-matched random control and a constant-cut control before calling a cut or brake a pass. This file adds those controls.

**Verdict: CLEARS, as insurance only.**
- The tail cut is not explained by cutting exposure.
- The cost stays inside about 2.2R a year in every period.
- The claimed R *gain* (+0.98R a year) is **not** real. It comes from CHECK alone and from 1–2 days. Treat AV50 as insurance that costs about 0 to 1.5R a year, not as an edge.

## What was run

- **Script:** `skeptic_control.py`, a copy of `partS.py` with the same engine, bench10 signals, 1-minute exits, LR8 costs and the Primary book (cap 30, at most 3 lots per symbol, −2R latch). Only control switches were added. Scoring is in `skeptic_score.py`, with output in `K_results.csv`, `K_controls.csv` and `K_days.csv`.
- **Reproduction:** the base reproduces exactly (FIT +57.78R, T2 −9.16R, CHECK +10.71R), and so does AV50 (ALL +3.383R).
- **Locked block:** 2024-11-01..2025-02-28 was never read (same pyarrow filter and assert).
- **Size matching:** done per period. AV50 halves the stop risk on its tight lots, so the exposure it removes is 0.5 × tight lots. Tight lots / all lots: FIT 64/226, T2 43/251, CHECK 47/262. The exposure each control removed (`exp_cut`) matches within about 1R.
- **Controls:** 200 seeds each for the random ones, 603 runs in all. Configurations tried here: 4 named (AV50 and Q50 re-runs, CONST, AVSIZE) plus 3 random families. The lineage N goes from 63 to 65 for the two new named rules; the bar is unchanged at about 2.88.
  - **RTB:** half stop on random *burst* lots, the same count as AV50. This tests whether the SPY-below-VWAP filter does better than chance.
  - **RTA:** half stop on random lots of any kind. This tests the burst + VWAP targeting.
  - **RHA:** half *size* on random lots of any kind. This is the size-matched random cut.
  - **CONST:** every lot at constant size 1 − 0.5 × tight/lots (FIT 0.858, T2 0.914, CHECK 0.910).
  - **AVSIZE:** the AV50 lots at half size instead of a half stop. Informative only, not proposed.

## Results (dR vs base, costs in)

| | FIT | T2 | CHECK | ALL | worst-day cut (ALL) | worst-5 cut (ALL) |
|---|---|---|---|---|---|---|
| **AV50** | −0.53 | −2.00 | **+5.92** | +3.38 (+0.98R/yr) | **+4.00** | **+8.97** |
| Q50 | −3.03 | −2.00 | −2.61 | −7.65 (−2.21R/yr) | +4.00 | +8.97 |
| CONST (size-matched) | −6.11 | −0.63 | −0.96 | −7.69 | +0.70 | +1.93 |
| RHA median (5–95%) | −6.79 | +0.47 | −0.93 | −7.12 (−13.3…−1.4) | +0.51 (p95 1.54) | +2.34 (p95 4.26) |
| RTA median | −0.55 | −0.39 | −1.67 | −2.71 (−8.2…+4.4) | +0.50 (p95 1.50) | +2.27 (p95 4.06) |
| RTB median | −0.66 | −1.41 | −1.69 | −3.76 (−8.9…+2.7) | +3.00 (p95 3.76) | +8.01 (p95 9.67) |
| AVSIZE | −7.47 | +2.80 | +3.50 | −1.17 | +4.11 | +12.10 |

AV50's percentile within each control's 200 seeds:

| | dR, FIT | dR, T2 | dR, CHECK | dR, ALL | worst-day cut, ALL | worst-5 cut, ALL |
|---|---|---|---|---|---|---|
| vs RHA | 100 | 11 | 100 | 100 | 100 | 100 |
| vs RTA | 50 | 21.5 | 100 | 92 | 100 | 100 |
| vs RTB | 52.5 | 34 | 100 | 96 | 97 | 82.5 |

## What this shows

1. **The tail cut is real and is not explained by exposure.**
   - A size-matched random cut or constant cut trims the worst day by about 0.5–0.7R. AV50 trims it by 4.0R.
   - The worst-5-day cut is 8.97R for AV50 against about 2R for those controls. AV50 sits at the 100th percentile on T2, CHECK and ALL.
   - The tail cut comes from **burst targeting**: a half stop on random burst lots (RTB) already gets most of it. The SPY < VWAP filter adds little to the tail.
2. **The R "gain" is not an edge.**
   - Against size-matched random selection, AV50 is at the median on FIT and *below* it on T2 (11th–34th percentile). It wins only on CHECK (100th percentile).
   - AV50 and Q50 differ on just 4 days, all in AV50's favour: 2026-06-11 +6.51R, 2026-01-30 +2.02R, 2025-04-09 +1.42R, 2025-04-07 +1.07R. 2026-06-11 alone is 59% of that +11.0R.
   - The same index-side split flipped sign in final1121.
3. **The cost bound (owner: about 2.2R a year) holds.**

   | Measure | AV50 R per year |
   |---|---|
   | FIT | −0.79 |
   | T2 | −1.18 |
   | CHECK | +5.41 |
   | ALL | +0.98 |
   | ALL without its best dR day (2026-06-17, 31% of positive dR) | −0.34 |
   | ALL without its best 2 dR days | −1.49 |

   - 5,000-resample day bootstrap: median +0.89R a year, 5th percentile −3.68R a year, P(cost > 2.2R a year) = 13%. For Q50 that probability is 49%.
   - AV50 changes only 13 days in 3.46 years. Its worst is 2024-08-01, where the base +1.87R becomes −3.85R (a winner cut, with SPY below VWAP).
4. **One-big-day check.**

   | | Avg R per lot | Avg R w/o best day | Best day | Best day's share |
   |---|---|---|---|---|
   | Base | +0.080 | +0.054 | 2025-04-10 | 13% |
   | AV50 | +0.085 | +0.058 | 2025-04-10 | 13% |
   | Q50 | +0.071 | +0.043 | 2025-04-10 | 14% |

   No `1 day` tag. AV50's *dR*, however, rests on 2026-06-17 (+4.56R) and 2023-02-07 (+4.00R).
5. **FIT caveat.** AV50's FIT worst-day cut is only +0.14R, and its FIT worst-5 is 0.53R *worse*. The tail protection shows up in T2 and CHECK (and live 11-20), not in FIT.

## Look-ahead and live implementability

**No look-ahead found:**
- The bench entry is the close of minute m−1, decided at m.
- The SPY state uses SPY's minute m−1 close against the session VWAP computed from regular-hours 1-minute bars from 09:30 through m−1. The caches hold no extended-hours bars.
- The burst count uses lots booked before m plus the candidates of decision minute m, all known at decision time.
- If the SPY state is unknown, the lot keeps its normal stop.

**Points the implementation must match exactly:**
- **Burst count is by decision bar, not wall clock.** The sim counts booked lots with bar time strictly greater than m − 10 minutes. On the 5-minute grid that means only the previous bar (m−5). It then adds *every* NM-ETF signal of bar m, including the lot itself and any later skipped by caps.
  - The runner's existing `_burst_count` uses wall-clock entry times. That would also count the bar m−10, because entries land a few seconds after the bar. Do not reuse it as is.
  - The plateau (K4W5 = K4W10 on CHECK and FIT; K4W15 similar) says a small mismatch is tolerable, but match the sim.
- **Sizing stays on the original stop.** Shares are sized from the original stop; only the bracket stop moves. R must stay in original risk units.
  - The journal `stop` column feeds R. If the tightened stop is written there, every report shows that lot's R doubled.
  - Keep the original stop as the R basis and journal the tight stop separately.
- **SPY bars.** SPY 1-minute bars must be polled from 09:30 for Primary, as `spy_exit` already adds SPY to the watchlist. Use SPY's last completed bar only if it is no more than 3 minutes stale (the runner's `SPY_STALE_MIN`). Otherwise use the normal stop.
- **Feed.** The live feed is SIP, the same as the caches.

## Rule-change context

- **Backtest:** simulated entirely under today's Primary book (−2R latch, LR8, cap 30), so no live rule change mixes into it. AV50's R is in original risk units, so TSZ1 does not apply.
- **Live, around the windows cited:**
  - −2R latch from 10-29.
  - NM-ETF in Primary from 11-11.
  - LR8 costs from 11-12.
  - TSZ1 from 11-17.
  - WB1, WB4 and ULT-22 from 11-17..11-20.
  - BRAKE-BURST from 11-23 (30 entries per 10 minutes; never binds on NM-ETF).
- **Frozen test:** the owner approved a *frozen* 25-session Primary forward test for NM-ETF on 11-20, and NMETF-SIZE (11-21) is conditional on it. AV50 changes NM-ETF's exit mid-test. The ledger entry must give AV50's effective date, and the test record must be split at it.
- **Remedy rule:** the remedy is setup-specific, which conflicts with the 11-05 "not tailored to one setup" rule. The owner was told this on the card and approved anyway.
