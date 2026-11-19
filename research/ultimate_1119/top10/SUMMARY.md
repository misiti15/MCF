Educational only — not financial advice

# Top-10 benchmark, variants, and what went into the testing arenas (ultimate_1119, 2026-11-19)

**Deployed after the 16:00 ET close; first live session 2026-11-20.**
- Ledger entry: `2026-11-20-ult1119-testing-admissions`.
- `docs/live/assignments.json` is regenerated (as of 2026-11-20).
- No existing setup changed. Primary, On Deck, the Graveyard and the Setup Generator are untouched.

**Configurations:** 35 frozen variant scorings plus the top-10 re-run, with 0 fitted configs. The job's cumulative N stays at about 1,882.

**Locked block:** 2024-11-01..2025-02-28 was never read.

## In plain words
1. **The owner's two requests:**
   - (1) Put the late-day ETF dip, traded only after high-dispersion days, into testing.
   - (2) Benchmark our live top 10 the normal way, and add every variant that meets that standard.
2. **The top 10 lose money in this backtest engine.** Only 3 of 10 are positive over the 2 years. Live they made money, so the engine under-reads live by a lot. For example, L3-fromopen is +0.053 in the backtest and +0.141 live over the same weeks.
3. **So the standard is negative.**
   - T1 combined ≥ −0.038R and check ≥ −0.046R.
   - T2 (2023-24) ≥ −0.105R.
   - "Meets" means the setup backtests no worse than our live winners. It does not mean it is profitable in backtest.
4. **The owner's admission rule (2026-11-19) lets a setup in if either:**
   - it meets that standard; or
   - it is debatable (not "really bad") and comes from a winning parent.
5. **What went in.** The owner's setup plus 15 variants, as 23 YAML entries: two-sided variants run as a long entry and a short entry. They are spread over Testing A-F, about 2-5 entries per account.
6. **Only 3 of the new setups look clearly positive in backtest:**
   - **ETFDISP**, the owner's setup: +0.19R over 2 years.
   - **H-V2**, the ETF shock snap-back: +0.17R.
   - **ULT-22**, the wider ETF dip: +0.06R.
7. **The rest are near zero or slightly negative after costs.** They go in because the owner's rule and his "add them" say so, and because live has beaten backtest for our leaders. The foot race will show which deserve to stay.
8. **Two variants that "meet" were held back** on the skeptic's findings:
   - **ULT-02** fails the standard when measured in its true risk units, and it has no parent.
   - **ULT-12** is the same ETF-dip bet as ETFDISP, ULT-22 and WB4. It holds every one of ETFDISP's sessions.
9. **Every new setup is kept apart from its close relatives:**
   - No ST7, ETF-dip, L3, RW3/RW5 or CWT09 sibling shares its account.
   - The ETF-long setups are kept out of the accounts whose shorts hold the same ETFs in the afternoon (opposite-side block).
   - Each is appended last in its account's priority order, so existing setups keep their exposure. Arena slot use peaked at 10-29% since TSZ1, with 0 resource skips.
10. **Caveats:**
    - Everything here is in-sample: these windows were seen in earlier rounds.
    - ETFDISP is in practice WB4 on high-dispersion days only: 100% of its trades are also WB4's.
    - Several records rest on one day (the `1 day` tag below).

## Top 10 (live 10-06..11-18, all accounts pooled, LR8) vs the same rules backtested the normal way
- Backtest columns: avg R per trade, home book, costs in.
- T1 = the 2-year history (2024-10 and 2025-03..2026-11-04, 446 sessions).
- T2 = 2023-01..2024-09 (427 sessions, 468 symbols).

| # | setup | live trades | live avg R | live w/o best day | T1 comb | T1 check | T2 |
|---|---|---|---|---|---|---|---|
| 1 | L3-gap-slope-fromopen-FD | 397 | +0.204 | +0.156 | −0.085 | −0.063 | −0.120 |
| 2 | RW3-gapdn-rsi5pop-flowsell-short-FD | 199 | +0.139 | +0.025 (1 day) | −0.080 | −0.049 | −0.105 |
| 3 | L3-gap-slope-lowdist-FD | 109 | +0.231 | +0.091 (1 day) | −0.107 | −0.104 | −0.086 |
| 4 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 206 | +0.110 | +0.022 (1 day) | −0.076 | −0.051 | −0.143 |
| 5 | L3-gap-slope-rsi5hi-FD | 158 | +0.089 | +0.007 (1 day) | −0.010 | −0.020 | −0.084 |
| 6 | RW6-ns2-up3-short-FD | 197 | +0.057 | −0.222 (1 day) | −0.031 | −0.055 | +0.034 |
| 7 | NM-RWN4-ns2-spyup05-notfri-short | 40 | +0.223 | −0.066 (1 day) | +0.070 | +0.071 | −0.049 |
| 8 | CWT14-failbrk-orl-p10-long-WB5 | 75 | +0.103 | −0.199 (1 day) | −0.025 | −0.024 | −0.040 |
| 9 | NM-ETF-late-dip-di-long | 30 | +0.248 | +0.235 | +0.140 | +0.041 | −0.037 |
| 10 | CWT09-gapdn-vwaploss-g10-short | 24 | +0.218 | +0.141 | +0.054 | +0.054 | −0.181 |
| | **median = the standard** | | | | **−0.028** | **−0.036** | **−0.085** |

- **Tier A thresholds (PLAN.md, fixed before any variant was scored):** the medians with a small tolerance, plus:
  - w/o best day ≥ −0.067 / −0.078;
  - R/session ≥ −0.49 / −0.52;
  - at least 20 trades on check and at least 20 on T2.
- **REALLY BAD:** T1 combined ≤ −0.05 with t ≤ −2.0, OR < −0.03 on fit, check and T2 alike. By this rule, 4 of the top 10, including the live #1, would count as REALLY BAD.

## Variants (normal-way backtest, testing book, LR8 + borrow) and decisions
- comb / check / T2 = avg R per trade.
- wo = T1 combined avg R without its best day.

| variant | comb | wo | check | T2 | rule | decision | setup id(s) → account |
|---|---|---|---|---|---|---|---|
| leg-E+disp (ETFDISP) | +0.192 | +0.145 | +0.125 | +0.214 (34) | owner decision; meets A | **deployed** | ETFDISP-late-dip-hidisp-long → Testing D |
| H-V2 | +0.171 | +0.115 | +0.196 | +0.005 (1 day) | A | **deployed** | ULT-HV2-shock-snap-etf-long-K → Testing D |
| ULT-22 | +0.063 | +0.037 | +0.002 (1 day) | −0.050 | A, debatable / derived from WB4 | **deployed** | ULT-22-wb4-wide-etf-long → Testing C |
| ULT-02 | +0.059 | −0.000 | +0.035 (1 day) | −0.059 | A by the letter only; fails in u units; no parent | held back (skeptic) | — |
| ULT-14 | +0.044 (1 day) | +0.010 | +0.017 (1 day) | −0.069 | A; skeptic: debatable / derived from WB4 | **deployed** | ULT-14-snap-long / -short → Testing F |
| ULT-12 | +0.040 | +0.025 | +0.001 (1 day) | −0.054 | A | held back (skeptic HOLD: ETF-dip stack, ULT-22 kept) | — |
| ULT-20 | +0.013 (1 day) | +0.001 | +0.013 | −0.012 | A by the letter, no parent | **deployed** | ULT-20-evr-ranker-long / -short → Testing B |
| ULT-21 | +0.011 (1 day) | −0.010 | −0.016 | +0.021 | A by the letter, no parent | **deployed** | ULT-21-etf-rank-long → Testing C |
| ULT-13 | +0.010 | +0.006 | +0.021 | −0.023 | A, debatable / derived from ST7-FD | **deployed** | ULT-13-st7-sharp-long → Testing A |
| ULT-25 | −0.001 | −0.003 | −0.004 | +0.003 | A by the letter, no parent | **deployed** | ULT-25-ultracheap-long / -short → Testing F |
| ULT-16 | −0.002 | −0.004 | −0.002 | −0.002 | A by the letter (market-entry twin) | **deployed** | ULT-16-costgeo-long / -short → Testing E |
| ULT-01 | −0.006 | −0.016 | −0.014 | −0.008 | A by the letter; debatable / derived from RW3/RW5 | **deployed** | ULT-01-gapdn-pop-fade-short → Testing A |
| ULT-19 | −0.012 (t −1.89) | −0.014 | −0.012 | −0.015 | A by the letter, no parent | **deployed** | ULT-19-lrlite-long / -short → Testing A |
| ULT-26 | −0.014 | −0.025 | −0.018 | −0.016 | A by the letter; loose L3 parent | **deployed** | ULT-26-withgap-trend-long / -short → Testing D |
| H-V1 | +0.081 | +0.060 | +0.103 | −0.130 | B: debatable / derived from NM-ETF / WB4 (mirror) | **deployed** | ULT-HV1-etf-late-pop-fade-short-X → Testing A |
| ULT-05 | −0.022 (t −1.87) | −0.024 | −0.009 | −0.024 | B: debatable / derived from L3 (loose) | **deployed** | ULT-05-withgap-cont-long / -short → Testing E |
| ULT-09 | −0.036 | −0.131 | −0.198 | −0.234 | B: debatable / derived from CWT09-g10 (fit +0.174; sign flip) | **deployed** (weakest) | ULT-09-failed-vwap-reclaim-short → Testing B |
| ULT-07 | −0.082 | −0.090 | −0.030 | −0.063 | B: debatable / derived from NM-ETF (escapes REALLY BAD by 0.0001R) | **deployed** (last) | ULT-07-pm-volatile-dip-long → Testing F |

**Not deployed:**
- **Duplicates (70% or more of their symbol-sessions overlap a live or admitted setup):** leg-E, BOOK-EM, BOOK-EM+disp, ULT-32, leg-M, ULT-03, ULT-23, ULT-10.
- **No promising parent and not Tier A:** ULT-06, 08, 11, 28, 30, 33.
- **REALLY BAD:** ULT-04, 34, 35.
- **Not scorable:** ULT-15, 17, 18, 24, 27, 29, 31.

## Where they run (effective 2026-11-20)
| account | new setups | why there |
|---|---|---|
| Testing A (testing2) | ULT-13, ULT-01, ULT-19 L/S, H-V1 | No ST7 or RW3/RW5 sibling. H-V1 (short ETFs) sits away from every new ETF-long setup. |
| Testing B (explore1) | ULT-20 L/S, ULT-09 | No CWT09 sibling. The ETF longs stay out because WB1 lives here. |
| Testing C (livelab) | ULT-22, ULT-21 | No ETF-dip sibling. Few afternoon ETF shorts. |
| Testing D (testingd) | ETFDISP, H-V2, ULT-26 L/S | Holds neither WB4 (Testing E) nor NM-ETF (Primary). No short setup here held these ETFs 14:00-15:45 in the live journals. No ST7 or L3 sibling. |
| Testing E (testinge) | ULT-16 L/S, ULT-05 L/S | No ST7 or L3 sibling. The ETF longs stay out because WB4 lives here. |
| Testing F (testingf) | ULT-14 L/S, ULT-25 L/S, ULT-07 | No WB4 / NM-ETF sibling. |

- **Close pairs are split across accounts:**
  - ULT-26 and ULT-05 (66% of ULT-26's sessions are inside ULT-05);
  - ULT-01 and ULT-16 (66%);
  - H-V1 and ULT-21 (46%).
- **Live wiring:** each YAML entry reproduces the window, ADV floor, symbol list, geometry, 45-minute time stop and refire that were scored (checked through `build_strategies`). `tests/test_ult1119_deploy.py` locks the placement.
- **ETFDISP:** it uses the new opt-in `disp_prev` column (`Prior.prev_ret`, lab_context, runner, backtester). No other setup reads it.

## Rule-change context
- **Backtest numbers:** fixed rules, so no rule changes apply.
- **Live top-10 window 10-06..11-18** carries these changes:
  - L3-fromopen moves on 10-20, 10-22 and 10-30;
  - the Primary −2R latch from 10-29;
  - the 0.15R cost filter from 10-30;
  - Primary sizing / cap 30 from 10-28;
  - LR8 costs from 11-12;
  - RW6 in the Graveyard 10-21..11-13;
  - TSZ1 half-size testing lots from 11-17;
  - WB4 from 11-17, CWT14-WB5 from 11-17.
- **Policy:** the testing-admission rule itself takes effect 2026-11-20.

Files:
- `PLAN.md`, `BENCHMARK.md`, `benchmark.json`, `VARIANTS.md`, `variants.json` and `overlap.json`: the benchmark and variant results.
- `bench10.py`, `bench_var.py`, `score_var.py` and `overlap_var.py`: the engines and scoring scripts.
- `research/ultimate_1119/etfdisp/RESULTS.md`: the ETFDISP build.
