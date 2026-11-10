# stoplab C: stop variants (open-loss latch, time-in-trade stop, give-back stop)

*Educational only — not financial advice.* Research only. Nothing in config/, mcf/, setups, exits, docs/live or the
ledger is changed. Written 2026-11-10 against `../PLAN.md` grid C, with the task's additions (listed under Configurations).

## Answer
**None of the three variants passes.** The current rule stays as it is: realised-R latch at -2R in Primary, and each
trade's own stop.

- **Open-loss latch** (block new entries once realised + open marked R <= -k):
  - It blocks more trades than the realised-only latch, and pooled it "saves" more: +219R vs the realised latch at
    k=2, over 1,244 setup-days.
  - That saving is **not a timing edge**. The excess delta (after removing what blocking the setup's own average trade
    would save) is negative at every k: -56 / -53 / -50R. All of the gain comes from trading losing setups less.
  - On setups that were winning on the choose split it costs -28R at k=2 (7 better, 4 worse; losses -43R).
  - In Primary it does worse than the live rule at every k: -4.5 / -1.3 / -3.4R.
  - Validate t is 1.0-1.5, against a bar of 2.96.
- **Time-in-trade stop** ("not at +b R after N min → exit"):
  - On live trades the all-session totals look positive (T15/+0.5R: +196R). But the validate half is flat
    (+28.6R, t 0.30), and it is negative for 9 of the 12 configs on at least one split.
  - The gain lives entirely in **losing** setups (+429R). On winning setups it costs -233R (13 better / 37 worse).
  - On the 2-year lab (917k trades, t/s geometries) every config with b > 0 is worse on VALID. T15/+0.5R comes to
    -0.0087R/trade, with 86 of 117 setups worse.
  - It cuts losers and winners alike. It is not a stop edge.
- **Give-back stop:**
  - Arming at +0.5R hurts in the lab (VALID -0.0003 to -0.0018R/trade, up to 52 of 73 changed setups worse). It is
    positive live only on the choose half.
  - **Arming at +1R with exit at break-even (G_m1.0_g1.0)** is the one variant with the same sign everywhere, but it is
    tiny:
    - live: +27.3R all sessions, +7.0R validate (t 1.44), 34 setups up / 21 down, best day 43% of the gain;
    - lab: +0.0003R/trade VALID (t 1.21), 9 up / 4 down;
    - it fires on only 2% of live trades, because most targets are <= 1R.
  - The neighbour g=0.5 is negative on validate, so there is no plateau. Treat it as a **lead** for hold / holdtr / S
    geometries, which the lab harness cannot walk. It is not a change.

## Exact vs approximate
| Part | What is exact | What is approximate |
|---|---|---|
| C1 / C2 live (12,913 live trades, 180 setups, 5 accounts, 10-06..11-04, 22 sessions) | Variants can only exit EARLIER. A trade whose trigger does not fire before its live exit keeps its live R exactly (pnl_adj, costs in) — 32%..99% of trades depending on config | Fired trades: fill = 1-min close (time stop) or the give-back level / bar open if gapped through; R = R_live + side·(px − live exit)/risk − (1c + 1bps)/risk (conservative: live flattens carry no extra exit cost). Triggers ignore the partial entry and exit minutes. Path check: 1-min path MFE vs journal mfe_r corr 0.961, median abs diff 0.000R (n 11,618) |
| C-open live (1,244 of 1,590 setup-days; 15,605 rows incl. 2,650 latch what-ifs) | Sequence, latch rule and realised R (journal r_multiple, as the runner) are the same as A1 | Open trades marked on the last completed 1-min close before the new entry (gross). What-if R uses backtest costs. What-ifs ignore other blocks. Halt what-ifs excluded |
| Lab (2y, 119 setups, TRAIN 575,639 / VALID 341,682 trades) | k = 1.0 walk reproduces the cached latch_1103 r (mean abs diff 1.6e-8 on 883,317 rows) | 5-min bars: time stop at N/5 bars, give-back checked on earlier-bar peak. t/s geometries only (no hold / holdtr / S, no setups without a lab module) |

Not covered:
- live trades after 11-04 or on uncached symbols (4,629 rows; Explore 1 / Live Lab entirely);
- 42 scale-out rows;
- 346 setup-days for C-open.

## Configurations counted
- C1 time stop: N ∈ {15, 30, 60, 90} min × b ∈ {0, +0.25, +0.5} R = 12.
  - The PLAN had b ∈ {0, 0.25}; the task added b = 0.5 and asked for N ∈ {15, 30, 60}.
- C2 give-back: m ∈ {0.5, 1.0} × g ∈ {50%, 70%, 100% = break-even} = 6.
  - The PLAN had g ∈ {BE, 50%}; the task added 70%.
- C-open: k ∈ {2, 3, 4} = 3. Realised-latch references at the same k are A1 rows and are not new.
- Sources: C1 + C2 on live and on lab (18 × 2 = 36), plus C-open on live (3) = **39 counted**. The PLAN had 24 for C.
  - The study-wide N rises from 64 to **79**, so the bar is sqrt(2 ln 79) = **2.96**.
- Per-setup choice (best of 18 + none on CHOOSE / TRAIN) is a diagnostic. Per-setup bar sqrt(2 ln 18) = 2.40.
- Splits:
  - live: per setup, first ceil(60%) of its sessions = choose, the rest = validate;
  - lab: TRAIN <= 2025-12, VALID 2026-01..03 + 07..09-15;
  - lab HOLD months were not walked, and the locked block 2024-11..2025-02 was never loaded (asserted).

## Live C1 / C2 (d = R_variant − R_live; baseline -1,881.2R, avg -0.146R/trade)
| config | fired | d all | d choose | d validate (t) | d w/o best day | best-day share | setups ≥20 up / down (sum up / down, worst) | validate up / down |
|---|---|---|---|---|---|---|---|---|
| T15 b0 | 10% | +1.6 | +16.7 | -15.1 (-1.37) | -12.7 | — | 34 / 44 (+73 / -81, -9.0) | 23 / 22 |
| T15 b0.25 | 49% | +87.3 | +81.3 | +6.0 (0.09) | +28.0 | 68% | 44 / 37 (+344 / -278, -29.9) | 30 / 33 |
| T15 b0.5 | 68% | +196.3 | +167.7 | +28.6 (0.30) | +96.7 | 51% | 44 / 37 (+516 / -352, -43.9) | 37 / 27 |
| T30 b0 | 5% | -3.9 | +15.4 | -19.3 (-1.66) | -10.2 | — | 32 / 35 | 11 / 24 |
| T30 b0.25 | 33% | +60.2 | +89.9 | -29.8 (-0.61) | +26.4 | 56% | 37 / 42 | 23 / 35 |
| T30 b0.5 | 51% | +128.3 | +167.1 | -38.8 (-0.52) | +69.5 | 46% | 39 / 41 (+347 / -254, -30.0) | 28 / 34 |
| T60 b0 | 3% | +10.3 | +12.8 | -2.5 (-0.84) | +4.4 | 57% | 33 / 28 | 11 / 15 |
| T60 b0.25 | 20% | +63.9 | +57.4 | +6.4 (0.42) | +36.4 | 43% | 33 / 45 | 27 / 25 |
| T60 b0.5 | 33% | +105.3 | +115.8 | -10.5 (-0.40) | +65.1 | 38% | 43 / 36 | 29 / 28 |
| T90 b0 | 1% | +6.7 | +9.1 | -2.4 (-0.51) | +1.6 | 75% | 29 / 22 | 9 / 12 |
| T90 b0.25 | 13% | +38.8 | +18.3 | +20.5 (1.83) | +20.1 | 48% | 37 / 39 (+102 / -63, -5.0) | 28 / 19 |
| T90 b0.5 | 24% | +24.4 | +28.7 | -4.2 (-0.96) | -7.2 | 130% | 38 / 39 | 28 / 24 |
| G m0.5 g0.5 | 23% | +144.6 | +153.5 | -8.9 (-0.64) | +108.0 | 25% | 38 / 40 (+278 / -139, -18.1) | 26 / 31 |
| G m0.5 g0.7 | 19% | +126.1 | +126.6 | -0.5 (-0.03) | +89.9 | 29% | 40 / 37 | 27 / 30 |
| G m0.5 g1.0 | 15% | +98.4 | +84.3 | +14.2 (0.65) | +66.3 | 33% | 39 / 38 | 28 / 29 |
| G m1.0 g0.5 | 4% | +35.3 | +38.2 | -2.9 (-0.19) | +10.0 | 72% | 31 / 35 | 13 / 10 |
| G m1.0 g0.7 | 3% | +27.7 | +20.0 | +7.7 (0.76) | +5.7 | 79% | 32 / 32 | 14 / 8 |
| G m1.0 g1.0 | 2% | +27.3 | +20.3 | +7.0 (1.44) | +15.7 | 43% | 34 / 21 (+64 / -41, -6.8) | 13 / 5 |

**Why the all-session totals mislead:** 125 of the 180 replayed setups were losing on their choose half (base -2,100R).
Cutting their trades short recovers R in any form. On the 55 setups that were winning, every config loses R on the
choose half: T15 b0.5 -233R (13 / 37), G m0.5 g0.5 -86R (12 / 37). Their validate deltas are +5R at most
(`C12_by_expectancy.csv`).

**Per family (T15 b0.5, all sessions):**
- Better: GEN +174R (45 / 20 setups), CWT +45R (17 / 14).
- Worse: RW -66R (5 / 15), L3 -58R (0 / 4), MF -39R (2 / 9).
- By geometry: t1s1 -113R (22 / 36). hold / holdtr / no-module setups gain. Those are mostly losing GEN hold books with
  few validate sessions.
- Full tables: `C12_by_family_geom.csv`.

**Per-setup choice:** 65 setups have >= 5 sessions and >= 20 trades. 60 pick a variant on choose. On validate 27 improve
and 26 worsen, net +39.8R (+107.8 / -68.0), which is a coin flip.

## Lab 2-year (t/s geometries, d per trade, VALID; base VALID avg -0.0576R)
| config | fired VALID | d TRAIN | d VALID (t) | setups up / down VALID | up / down in both splits |
|---|---|---|---|---|---|
| T15 b0 / b0.25 / b0.5 | 3% / 41% / 66% | +.0005 / -.0031 / -.0074 | .0000 (0.08) / -.0042 (-1.23) / -.0087 (-1.75) | 45/65, 38/79, 31/86 | 21/29, 18/51, 8/56 |
| T30 b0 / b0.25 / b0.5 | 2% / 26% / 48% | +.0004 / -.0015 / -.0057 | -.0001 / -.0035 (-1.38) / -.0083 (-2.03) | 45/60, 36/80, 28/89 | 22/24, 16/44, 14/60 |
| T60 b0 / b0.25 / b0.5 | 1% / 14% / 29% | .0000 / -.0005 / -.0027 | .0000 / -.0011 / -.0033 (-1.17) | 37/52, 42/72, 36/80 | |
| T90 b0 / b0.25 / b0.5 | 0.3% / 8% / 19% | +.0001 / -.0001 / -.0010 | .0000 / -.0000 / -.0010 | 37/40, 51/61, 44/72 | |
| G m0.5 g0.5 / 0.7 / 1.0 | 15% / 12% / 9% | -.0000 / -.0018 / -.0033 | -.0003 / -.0011 / -.0018 (-1.04) | 31/42, 27/46, 21/52 | 16/23, 14/28, 13/32 |
| G m1.0 g0.5 / 0.7 / 1.0 | 1.0% / 0.9% / 0.7% | +.0003 / +.0004 / +.0002 | +.0002 (0.64) / +.0002 (0.59) / +.0003 (1.21) | 5/8, 5/8, 9/4 | 2/3, 4/4, 6/3 |

**Per-setup choice (lab):** 108 of 117 setups pick a variant on TRAIN. 42 improve on VALID and 63 worsen. **0** clear the
per-setup bar of 2.40. The best is CWT04-backside-vwaptest-a15-short with G m0.5 g0.5: +0.114R/trade, t 2.06.

## Open-loss latch (C-open), 1,244 setup-days with bars
| config | vs | R | d | d choose | d validate (t) | extra blocked | excess d (validate) | d w/o best day | setups up / down (sum up / down, worst) |
|---|---|---|---|---|---|---|---|---|---|
| off | — | -1,956.8 | | | | | | | |
| real2 (live rule) | off | -1,452.0 | +504.9 | +310.9 | +194.0 (1.77) | 4,376 | -185.0 (-35.2) | +373.1 | 44 / 21 (+627 / -122, -52.4) |
| open2 | real2 | -1,233.3 | +218.7 | +178.2 | +40.5 (1.50) | 2,115 | **-55.7** (-45.6) | +177.0 | 44 / 22 (+315 / -96, -29.5) |
| open3 | real3 | -1,360.7 | +202.6 | +126.8 | +75.8 (1.03) | 1,873 | **-53.2** (-3.9) | +123.0 | 37 / 18 (+313 / -111, -25.3) |
| open4 | real4 | -1,447.1 | +213.1 | +154.5 | +58.6 (1.12) | 1,802 | **-49.9** (-20.9) | +162.6 | 28 / 15 (+271 / -58, -21.8) |

By account (R): see `C_open_latch_by_account.csv`.

| Account | open2 vs real2 | Read |
|---|---|---|
| Primary | -4.6 | worse |
| Testing 1 | +19.7 | gains |
| Testing 2 | +76.9 | gains |
| Gen | +40.3 | gains |
| Graveyard | +86.4 | gains, mostly from what-ifs |

The accounts that gain are the ones whose books lose. On winning setups:
- open2 vs real2: -28.1R (7 up / 4 down, -43R lost);
- open4 vs real4: +17.5R (5 / 1).

## Rule changes inside the window (do not read the figures as a single regime)
- Per-setup stop:
  - on in T1/T2/Gen 10-19..10-22, latching (LL-LATCH) from 10-23;
  - ST-A switched it off in T1/T2/Gen on 10-23;
  - Graveyard at -2R since 10-21;
  - ST-P: Primary at -2R latched since 10-29.
- Scale-out fixes 10-16 and 10-20 (42 scale-out rows excluded).
- Primary size ~$5k, then ~$4k from 10-28.
- BAR90 10-29.
- CF cost filter in T1/T2 from 10-30.
- R2A cap exemption 11-03.
- ROLL1 11-05 (Explore 1 / Live Lab, after the bar coverage ends).
- EXPO1109 11-09 (outside coverage).
- Many setup moves 10-20..11-09.

The replay compares variants on the same trades, so these changes move the sample, not the comparison.

## Files
- Scripts: `live_variants.py` (live C1/C2 + C-open), `bt_variants.py` (lab walk, copied from B3 with the variant exits
  added), `analyze_lab.py`.
- Logs: `live_out.txt`, `lab_out.txt`, `expectancy_out.txt`.
- Live outputs: `C12_global.csv`, `C12_per_setup.csv`, `C12_by_family_geom.csv`, `C12_by_expectancy.csv`,
  `C12_per_setup_choice.csv`, `trades_c12.csv.gz` (per-trade variant R + fired flags).
- Open-latch outputs: `C_open_latch*.csv`, `units_open_latch.csv.gz`.
- Lab outputs: `lab_global.csv`, `lab_by_family_geom.csv`, `lab_per_setup.csv`, `lab_per_setup_choice.csv`.
- The lab walk parquet is in /dev/shm/stopc_lab and is not kept.
