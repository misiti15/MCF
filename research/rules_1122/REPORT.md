Educational only — not financial advice.

# rules-1122: latch, burst brake, $ vs R, and NM-ETF tail protection (research only)

Owner-approved 2026-11-22. Research only: no config, setup or exit change. Part D was widened the same day into a full NM-ETF-late-dip-di-long protection study (owner: limit any significant loss without limiting its R). Report text from the study agent's hand-back (its file write was blocked); scripts and CSVs in this folder.

## Data and engines

- **Live data:** every mcf-data* journal (run 1, closed trades, 2026-10-06..2026-11-20), LR8 cost-R (`mcf.costs.cost_r_lr8`). Identical signals across accounts are counted once.
- **What-if:** the journals' "signals not taken" rows, costed with each setup's median live cost gap + 0.05R haircut (E4 what-if).
- **Part D:** 2-year bench (bench10 signals, 1-minute exits, LR8 costs, Primary book).
  - FIT = 2024-10 + 2025-03..09; T2 = 2023-01..2024-09; CHECK = 2025-10-01..2026-11-04.
  - The locked block (2024-11..2025-02) was never read.

**Rule-change context (ledger dates in the window):**
- Per-setup −2R latch: Testing 1/2 from 10-19 to 10-22 only; Graveyard from 10-21; Primary from 10-29.
- Primary sizing: $4k slots from 10-28.
- Primary roster: L3 promotions 10-21 / 10-22 / 10-30; TEAM-6 with NM-ETF from 11-11; NS5 out 11-19.
- 11-12: LR8 costs, LR3, caps raised, account halts at 300R, On Deck split-tape gate off.
- 11-17: TSZ1 (half-size testing lots).
- 11-23: burst brake, ST7 out, PSHADOW.

Live samples cover at most 33 sessions, and 11-05, 11-12, 11-17 and 11-20 dominate several totals.

## Failures and limits first

- **A:** the latch is **−68R worse than a random trim** of the same size on live trades (−304R with what-if rows). It gains only because it trims setups that lose on average. It never touched NM-ETF on 11-20: the latch counts closed R, and all 12 lots were still open.
- **B:** the brake never binds in Primary (at most 24 entries per setup in 10 minutes). It costs Explore 1 −47.9R by blocking the 11-20 GEN short winners.
- **D:** no configuration improves R significantly.
  - Best per-day dR t is +1.00, against a bar of 2.47 for this study (2.75 for the lineage).
  - Q50 is the only pre-registered finalist, and it costs −7.65R over 3.5 years.
  - The bench's worst day is −8.21R, so live 11-20 (−12.57R) is beyond the backtest's tail.

## A. Per-setup −2R latch, every setup (228 setups, 29,564 live trades)

- **Latch rule tested:** the day stops once realized cost-R ≤ −2, as in Primary. Version L uses live trades only; version W adds back the what-if rows the real latch skipped (9,028 rows, estimate).
- **Headline (L):** −4,443.7R → −3,714.6R, **dR +729.1R**.
  - 102 of 228 setups touched: 68 better, 34 worse.
  - Excess vs a random trim: −68.3R (W: −303.9R). After a −2R start, the rest of the day tends to recover.
- **Other levels:**

  | Latch | dR |
  |---|---|
  | −1R | +1,345 |
  | −1.5R | +853 |
  | −2R | +729 |
  | −3R | +556 |
  | −4R | +417 |

  None is selective.

| family | touched | better / worse | dR total | excess vs random |
|---|---|---|---|---|
| gap-down short (L3, RW1/3/5/7, RW3S, CWT09-gapdn) | 13 | 3 / 10 | **−103.7** | **−103.0** |
| GEN | 34 | 22 / 12 | +150.7 | −38.5 |
| CWT14 | 14 | 13 / 1 | +352.5 | −17.1 |
| classic (heat / exhaustion / intraday) | 6 | 6 / 0 | +151.0 | +62.3 |
| MF | 7 | 6 / 1 | +48.7 | +15.1 |
| NS | 9 | 4 / 5 | +28.9 | +12.1 |
| ETF (NM-ETF and copies) | 1 | 1 / 0 | +0.9 | −3.1 |

- **Worst setups under the latch:**
  - RW7 −64.5R (208 winners blocked, +139.2R, vs 120 losers avoided, −74.7R)
  - RW6 −25.6R
  - RW3S −15.3R
  - CWT09-g5 −14.1R
- **Best:** CWT14-orl-p05 +74.2R, CWT14-pdl-p10 +70.9R.
- **Primary members (already latched):** L3-fromopen +6.4R, RW3 −0.6R, RW5 −1.1R, L3-rsi5hi −0.2R, NM-ETF 0.
- **Conclusion:** gap-down shorts are the one family the latch clearly hurts (W: −371.5R, with 11-20 at −193.6R). Their early losers come just before the fade they wait for. No change is proposed: the Primary impact is small and the sample is short and day-dominated. "No −2R latch for gap-down shorts" goes to the backlog.

## B. BRAKE-BURST replay (30 entries per setup per rolling 10 minutes)

| account | R without → with | dR | blocks green / red days (R) | max same-underlying lots |
|---|---|---|---|---|
| Primary | −130.4 → −130.4 | 0.0 | 0 / 0 | 14 (SPY group, 10-22) → 14 |
| On Deck | −647.9 → −640.7 | +7.2 | 0 / 33 (−7.2) | 19 → 9 |
| Testing A | −985.5 → −973.7 | +11.8 | 0 / 80 | 16 → 16 |
| Live Lab | −154.9 → −126.3 | +28.5 | 0 / 50 | 11 |
| Explore 1 | +41.9 → −6.0 | −47.9 | 39 (+49.4) / 0 | 6 |
| Gen | −873.6 → −720.3 | +153.3 | 84 (+41.1) / 312 (−206.6) | 20 → 17 |
| Graveyard | −1,605.8 → −1,490.0 | +115.8 | 0 / 205 | 24 → 22 |

- **Totals:** 143 blocks on profitable days (+95.4R) and 692 on losing days (−407.5R).
- **NM-ETF on 11-20:** 12 lots amounted to about 4 bets (SPY group 5, semis 3, gold 3, IWM 1). The brake can't see this.

## C. $ vs R, Primary since 10-23 (836 trades, MTUM 11-05/06 excluded)

| measure | value |
|---|---|
| R after LR8 costs | −88.2 |
| $ gross journal (the "+$310") | +$348 |
| LR8 modelled costs | $1,363 (−44R of the −88R) |
| $ after LR8 costs | −$1,015 |
| $ risk per trade | mean $48.4, median $32.6, P10 $11.4, P90 $103.5, max $233.7 |
| same book at fixed $48.4 risk | −$4,269 |

Where the gap comes from:

1. **Costs (about half).** R includes LR8 modelled costs; the gross $ figure does not.
2. **Uneven $ risk.** Size is set by the ~$3.4k notional cap, so $ risk = notional × stop %.
   - Losses sat in small-$-risk trades: deciles D1–D3 lost −69R but only −$932 (MF4/MF2 −90R).
   - Gains sat in wide-stop trades: D8–D9 made +25R and +$2,157 (L3-fromopen +43.9R, +$3,734).
3. **Not a few huge trades.** The top 10% by $ risk explains only −2.7R / −$550.

| week ending | R | $ after LR8 | $ at fixed risk | mean $ risk |
|---|---|---|---|---|
| 10-23 | −3.3 | −108 | −158 | 16.6 |
| 10-30 | −10.1 | −217 | −488 | 23.4 |
| 11-06 | −34.3 | −2,474 | −1,660 | 50.2 |
| 11-13 | −44.7 | +1,371 | −2,163 | 51.8 |
| 11-20 | +4.1 | +414 | +199 | 63.1 |

## D. NM-ETF protection (21 configurations, `D_PREREG.md`)

- **Base:** exact match to bench10 (FIT +57.78R, T2 −9.16R, CHECK +10.71R).
  - Worst day −8.21R; 4 days at or below −4R (−25.3R in total).
  - 36 burst days, 7 of them in April 2025.

| cfg | idea | total R (base 59.32) | dR | worst day | days ≤ −4R | worst-day cut per R given up |
|---|---|---|---|---|---|---|
| G2 | shared group stop, k = 2 | 60.64 | +1.32 | −5.95 | 4 (−21.6) | free |
| G3 | shared group stop, k = 3 | 59.46 | +0.14 | −5.95 | 4 (−21.4) | free |
| **Q50** | **burst lots: half-distance stop** | **51.68** | **−7.65** | **−4.21** | **2 (−8.3)** | **0.52** |
| Q65 | 0.65 stop (plateau) | 52.61 | −6.71 | −5.41 | 5 | 0.42 |
| Q40 | 0.40 stop (plateau) | 47.58 | −11.74 | −3.73 | 0 | 0.38 |
| B2 | burst loss budget −2R | 51.00 | −8.32 | −6.03 | 3 | 0.26 |
| W4x1.5 | burst sentinel | 46.62 | −12.71 | −6.03 | 3 | 0.17 |
| T15 | burst time stop, 15 min | 50.08 | −9.24 | −7.13 | 3 | 0.12 |
| SH | late lots half size* | 37.14 | −22.19 | −5.66 | 2 | 0.11 |
| O4 | open-risk budget, 4R | 19.44 | −39.88 | −4.12 | 1 | 0.10 |
| S4 | bar risk split, 4R* | 35.94 | −23.38 | −5.95 | 2 | 0.10 |
| P1 | stagger + latch | 28.55 | −30.77 | −7.53 | 4 | 0.02 |
| P1W | stagger + sentinel | 1.02 | −58.31 | −4.39 | 2 | 0.07 |

(*) conflicts with C3-BAR2 ("per-setup risk stays flat"). Other configurations are in `D_results.csv`.

- **Live 11-20 replay, Primary NM-ETF (−12.57R):**
  - Without interpolated marks: Q50 −6.36, O4 −4.21, S4 −7.35.
  - With interpolated marks (these flatter the result): B2 −2.49, W3x1.5 −3.55, G2 −7.21.
- **Reading:**
  - Every rule that cuts 11-20 also cuts some profitable bursts.
  - Q50 is the best trade of tail cut for R and the only finalist; Q40 / Q65 show the tail cut holds on a plateau.
  - G2 / G3 are R-neutral but cut little.
  - All options run in-runner with no extra job.
  - Any of these is a Primary exit change: Friday epoch, rule-27 skeptic review, PROTECTED / WB-copy route. It is also setup-specific under the CLAUDE.md remedy rule.

## Configurations tried

- A: 5 latch levels (descriptive)
- B: 1
- C: 0
- D: 21
