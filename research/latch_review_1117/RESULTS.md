# LATCH review 2026-11-17 — results

*Educational only — not financial advice.* Research only: nothing in config changed. Paper (live journal) fills,
journal what-ifs (simulated) and level replays are labelled separately below. R = R after costs throughout.
Plan fixed before scoring: PLAN.md. **10 configurations tried** (latch −2 / −3 / −4 / none; REENTRY 6 / 12 / day;
FADEMOVE 10 / 15 / 20). Locked block 2024-11-01..2025-02-28 not read (all data 2026-10-06..2026-11-17).

## Failures first
- **Neither remedy works.** All six remedy configurations lower total R. The trades they remove were *winners* on
  average (+0.09 to +0.58R per removed trade).
- **Opening the latch board-wide loses R.** The replay is summed over all 583 latch setup-days in 9 accounts:
  −2R gives −2,977R, −3R gives −3,047R, −4R gives −3,116R and no latch gives −3,350R. Replayed Primary account
  totals (−20R halt kept) are −45.4R at −2, −52.0R at −3, −61.7R at −4 and −78.4R with no latch.
- **Today's L3 case does not generalise.** L3-gap-slope-fromopen-FD gained +3.9R on 11-17 with the latch open:
  day R +1.95R with no latch against −1.97R at −2. Over its 9 latch days the trades after the latch made
  −11.9R (−0.19R per trade), and day R is −25.1R at −2 against −37.4R with no latch.

## Part 1 — latch review
Sample:
- 153 setups had 583 latch setup-days.
- **A, actual:** 71 setup-days with the latch on: Primary from 10-29; On Deck, Testing A and Gen on 10-20..10-22.
  On these days 551 blocked signals were journaled (deduplicated: Primary 218, On Deck 259, Testing A 74). The
  what-if covers 549 of them, and 507 are left after the 3-lots-per-symbol cap.
- **B, virtual:** 512 setup-days with the latch off. The setup's realized R crossed −2R and it kept trading, so
  everything after the cross is a real paper fill (2,912 trades).

| sample | post-latch trades | R / trade | total R | day R −2 | −3 | −4 | none |
|---|---|---|---|---|---|---|---|
| A actual (journal what-ifs, simulated) | 507 | +0.086 | +43.7 | −348.4 | −324.1 | −327.9 | −311.5 |
| B virtual (real paper fills) | 2,912 | −0.154 | −447.2 | −2,628.4 | −2,723.3 | −2,787.7 | −3,038.7 |
| of which Primary, A | 186 | −0.065 | −12.1 | −170.6 | −162.4 | −166.3 | −181.1 |

The simulated what-ifs look better than the real fills that came after a −2R cross. Real fills after the cross
average −0.15R. With 2,912 real trades against 507 simulated ones, the real fills are the stronger evidence.

How many setups each level helps or hurts, compared with −2:

| level | setups better | R gained | setups worse | R lost |
|---|---|---|---|---|
| −3 | 35 | +100.4 | 41 | −170.9 |
| −4 | 24 | +90.9 | 57 | −229.7 |
| none | 27 | +219.7 | 67 | −593.1 |

### Setups passing the fixed gate (PLAN)
The gate: at least 5 latch days, post-latch R > 0 and > 0 without the best day, no single symbol above 50% of the
post-latch R, and a level that beats −2 without the best day. Five setups pass. Under the owner's one-big-day rule,
three of them carry the "1 day" tag:

| setup (now in) | latch days A/all | post trades | post R/tr | post R | best-day share | day R −2 → best level | w/o best day | call |
|---|---|---|---|---|---|---|---|---|
| RW7-gapdn-bounce-early-short-FD (Testing F, latch off; Graveyard review pending) | 1/15 | 359 | +0.29 | +105.3 | 48% | −75.1 → **none +28.2** | −81.9 → −17.1 | **clear**: 12 trade days, top symbol 2% |
| RW1-gapdn-bounce-flowsell-short-FD (On Deck, latch off) | 1/9 | 35 | +0.45 | +15.6 | 45% | −25.6 → none −12.2 | −33.2 → −24.0 | passes; improvement comes from 3 days |
| RW3S-gapdn-flowsell-short-FD (Graveyard, −2R latch on) | 0/8 | 68 | +0.19 | +13.2 | 57% **1 day** | −100.4 → none −87.2 | −98.3 → −91.0 | not recommended (1 day) |
| L3-gap-slope-rsi5hi-FD (Testing 1) | 4/7 | 37 | +0.33 | +12.3 | 97% **1 day** | −17.9 → −3 −5.6 | −15.9 → −15.1 | not recommended (11-05 only) |
| RW3-gapdn-rsi5pop-flowsell-short-FD (Primary) | 6/6 | 30 | +0.23 | +7.0 | 95% **1 day** | −29.1 → −3 −20.6 | −27.8 → −24.0 | not recommended (11-03 = 95% of post R; 11-10 −5.5R) |

Primary's current six setups:
- **L3-gap-slope-fromopen-FD:** 9 latch days, post-latch −0.19R per trade. **Keep −2.**
- **RW3-FD:** carries the "1 day" tag. **Keep −2.**
- **RW5-FD:** 6 latch days, post-latch −0.17R per trade. **Keep −2.**
- **NS5:** 3 latch days, post-latch −0.86R per trade. **Keep −2.**
- **ST7-FD:** 1 latch day, with no blocked trades. **Keep −2.**
- **NM-ETF-late-dip:** never latched.

### Per setup: every setup with an actual latch day or at least 5 latch days
Full list: per_setup_latch.csv. Day R is summed over the setup's latch days. "Best-day share" is the best day's
share of the post-latch R; it is not given when the post-latch total is ≤ 0.

| setup | accounts | latch days (A/all) | blocked | post trades | post R/tr | post R | best-day share | top sym share | day R −2 | −3 | −4 | none | fixed-gate verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF4-h40-open-flowsell-FD | On Deck,Primary | 7/10 | 41 | 45 | +0.02 | +0.75 | 173% **1 day** | 9% | -68.65 | -68.90 | -68.90 | -67.90 | keep -2 (post-latch not positive w/o best day) |
| RW3-gapdn-rsi5pop-flowsell-short-FD | Primary | 6/6 | 30 | 30 | +0.23 | +6.97 | 95% **1 day** | 7% | -29.12 | -20.58 | -19.64 | -21.12 | candidate L3 |
| MF2-open-rsimidhi-flowsell-FD | On Deck,Primary | 5/12 | 26 | 39 | -0.53 | -20.50 |  | 26% | -70.73 | -74.01 | -75.27 | -86.43 | keep -2 (post-latch not positive w/o best day) |
| L3-gap-slope-fromopen-FD | On Deck,Primary | 4/9 | 69 | 63 | -0.19 | -11.88 |  | 16% | -25.08 | -28.40 | -30.76 | -37.38 | keep -2 (post-latch not positive w/o best day) |
| L3-gap-slope-rsi5hi-FD | On Deck,Primary,Testing A | 4/7 | 34 | 37 | +0.33 | +12.26 | 97% **1 day** | 4% | -17.89 | -5.63 | -5.63 | -5.63 | candidate L3 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | On Deck,Primary | 4/6 | 21 | 27 | -0.17 | -4.49 |  | 27% | -36.39 | -37.71 | -40.27 | -40.89 | keep -2 (post-latch not positive w/o best day) |
| RW4-ns3-adv150-short-FD | On Deck,Testing A | 3/8 | 0 | 11 | -0.57 | -6.25 |  | 45% | -22.88 | -22.53 | -22.53 | -29.13 | keep -2 (post-latch not positive w/o best day) |
| MF3-open-flowsell-rsi5hi-FD | On Deck,Primary | 2/11 | 41 | 86 | +0.02 | +1.94 | 517% **1 day** | 7% | -41.07 | -28.31 | -27.69 | -34.81 | keep -2 (post-latch not positive w/o best day) |
| NM-AR-AM-gapdown-capitulation-long | Testing A | 2/7 | 0 | 0 |  | +0.00 |  |  | -31.52 | -31.52 | -31.52 | -31.52 | keep -2 (post-latch not positive w/o best day) |
| CWT12-coil-k6-long | On Deck,Testing A | 2/5 | 1 | 7 | -0.71 | -4.98 |  | 100% | -25.06 | -26.25 | -28.75 | -31.91 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-pdh-p10-short | On Deck,Testing A | 2/5 | 11 | 56 | -0.21 | -11.71 |  | 12% | -26.82 | -37.19 | -39.65 | -43.29 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-pdh-p05-lowvol-short | On Deck,Testing A | 2/4 | 8 | 41 | -0.32 | -13.31 |  | 10% | -29.52 | -31.22 | -32.20 | -43.63 | keep -2 (< 5 latch days) |
| CWT13-vwapstretch-z05-short | Testing A | 2/4 | 28 | 28 | -0.73 | -20.44 |  | 37% | -26.03 | -25.09 | -26.36 | -46.46 | keep -2 (< 5 latch days) |
| RW7-gapdn-bounce-early-short-FD | On Deck,Testing F | 1/15 | 105 | 359 | +0.29 | +105.25 | 48% | 2% | -75.07 | -68.40 | -69.39 | +28.20 | candidate none |
| CWT14-failbrk-pdl-p10-long | Testing A | 1/15 | 5 | 301 | -0.15 | -46.16 |  | 8% | -93.16 | -86.91 | -98.26 | -135.63 | keep -2 (post-latch not positive w/o best day) |
| exhaustion_short-FD | On Deck,Testing A | 1/12 | 1 | 14 | -0.07 | -0.99 |  | 27% | -33.80 | -31.94 | -34.67 | -34.67 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-pdl-p05-lowvol-long | Testing A | 1/12 | 17 | 197 | -0.07 | -14.73 |  | 4% | -51.21 | -45.48 | -52.08 | -65.46 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-pdl-p05-long | On Deck,Testing A | 1/10 | 28 | 171 | -0.07 | -11.68 |  | 3% | -80.65 | -76.09 | -73.91 | -88.32 | keep -2 (post-latch not positive w/o best day) |
| RW1-gapdn-bounce-flowsell-short-FD | On Deck,Testing A | 1/9 | 10 | 35 | +0.45 | +15.64 | 45% | 5% | -25.60 | -18.61 | -19.10 | -12.17 | candidate none |
| MF5-flowsell-vwapup-rsi5hi | On Deck,Testing A | 1/8 | 1 | 7 | -0.46 | -3.25 |  | 74% | -22.71 | -21.72 | -22.74 | -25.95 | keep -2 (post-latch not positive w/o best day) |
| MF5-flowsell-vwapup-rsi5hi-FD | On Deck,Testing A | 1/8 | 8 | 27 | -0.34 | -9.25 |  | 20% | -17.20 | -15.87 | -19.09 | -24.29 | keep -2 (post-latch not positive w/o best day) |
| NS3-failed-vwap-reclaim-short | On Deck,Primary | 1/7 | 0 | 6 | -0.14 | -0.84 |  | 100% | -17.61 | -18.46 | -18.46 | -18.46 | keep -2 (post-latch not positive w/o best day) |
| GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long | Gen | 1/7 | 0 | 3 | -0.67 | -2.00 |  | 100% | -4.49 | -4.37 | -5.33 | -5.33 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-orl-p05-long | Testing A | 1/7 | 8 | 110 | -0.11 | -12.03 |  | 5% | -52.40 | -60.65 | -63.35 | -64.25 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-orl-p05-lowvol-long | Testing A | 1/7 | 4 | 99 | -0.28 | -27.29 |  | 7% | -69.38 | -68.97 | -71.65 | -95.64 | keep -2 (post-latch not positive w/o best day) |
| CWT05-flush-m05-v3-long | On Deck,Testing F | 1/6 | 1 | 11 | -0.12 | -1.28 |  | 47% | -18.04 | -20.90 | -20.27 | -19.76 | keep -2 (post-latch not positive w/o best day) |
| heat_fade_short | On Deck,Primary | 1/6 | 0 | 29 | -0.46 | -13.27 |  | 21% | -26.32 | -30.05 | -29.52 | -38.09 | keep -2 (post-latch not positive w/o best day) |
| MF1-945-flowsell-vwapup-FD | On Deck | 1/5 | 22 | 32 | +0.31 | +10.05 | 146% **1 day** | 8% | -11.56 | -17.90 | -14.87 | -0.40 | keep -2 (post-latch not positive w/o best day) |
| NS1-rsidip-rsi5pop-long-FD | On Deck,Testing E | 1/5 | 0 | 6 | +0.04 | +0.22 | 100% **1 day** | 36% | -13.94 | -13.72 | -13.72 | -13.72 | keep -2 (post-latch not positive w/o best day) |
| L3-gap-slope-lowdist-FD | On Deck | 1/5 | 0 | 1 | -0.38 | -0.38 |  |  | -9.68 | -10.06 | -10.06 | -10.06 | keep -2 (post-latch not positive w/o best day) |
| orb20_a | On Deck,Primary | 1/4 | 0 | 0 |  | +0.00 |  |  | -9.80 | -9.80 | -9.80 | -9.80 | keep -2 (< 5 latch days) |
| NS2-sma50break-overbought-short-FD | On Deck | 1/4 | 24 | 39 | -0.16 | -6.35 |  | 12% | -30.19 | -32.98 | -35.26 | -33.18 | keep -2 (< 5 latch days) |
| RW6-ns2-up3-short-FD | On Deck | 1/4 | 0 | 8 | -0.82 | -6.53 |  | 100% | -21.44 | -25.68 | -27.96 | -25.68 | keep -2 (< 5 latch days) |
| CWT14-failbrk-pdh-p10-lowvol-short | Testing A | 1/4 | 1 | 28 | -0.39 | -10.89 |  | 15% | -12.02 | -18.08 | -18.08 | -21.16 | keep -2 (< 5 latch days) |
| RW2-exhaustion-noon-adv150-short-FD | On Deck,Testing A | 1/4 | 1 | 52 | -0.25 | -13.14 |  | 16% | -25.41 | -28.04 | -27.38 | -41.63 | keep -2 (< 5 latch days) |
| heat_fade_short-FD | On Deck | 1/4 | 1 | 125 | -0.27 | -33.85 |  | 6% | -22.31 | -21.37 | -22.36 | -52.18 | keep -2 (< 5 latch days) |
| NS4-pm-vwap-reclaim-oversold-short-FD | On Deck,Testing F | 1/3 | 0 | 12 | +0.20 | +2.42 | 100% **1 day** | 18% | -7.08 | -7.08 | -7.08 | -4.66 | keep -2 (< 5 latch days) |
| NS5-sma50-flush-oversold-long | Primary | 1/3 | 4 | 4 | -0.86 | -3.44 |  |  | -7.93 | -10.31 | -10.31 | -10.31 | keep -2 (< 5 latch days) |
| ST7-rsi50dn-long-pm-t1s1-FD | On Deck | 1/1 | 0 | 0 |  | +0.00 |  |  | -2.66 | -2.66 | -2.66 | -2.66 | keep -2 (< 5 latch days) |
| CWT14-failbrk-pdl-p10-lowvol-long | Primary,Testing A,Testing D | 0/10 | 0 | 79 | -0.29 | -22.74 |  | 5% | -50.45 | -52.08 | -58.33 | -73.19 | keep -2 (post-latch not positive w/o best day) |
| CWT13-vwapstretch-z05-long | Primary,Testing A | 0/9 | 0 | 153 | -0.13 | -19.72 |  | 2% | -38.67 | -53.45 | -53.79 | -57.19 | keep -2 (post-latch not positive w/o best day) |
| RW3S-gapdn-flowsell-short-FD | Testing A,Testing E | 0/8 | 0 | 68 | +0.19 | +13.19 | 57% **1 day** | 9% | -100.38 | -99.50 | -100.07 | -87.19 | candidate none |
| exhaustion_short | On Deck,Primary,Testing F | 0/8 | 0 | 15 | +0.03 | +0.45 | 1508% **1 day** | 89% | -23.41 | -21.75 | -22.95 | -22.95 | keep -2 (post-latch not positive w/o best day) |
| GEN-261029-01-ORBfailUp-RSI14le41-ADX7le29-LAM-QQQgt0p3-hold-long | Gen | 0/6 | 0 | 0 |  | +0.00 |  |  | -3.98 | -3.98 | -3.98 | -3.98 | keep -2 (post-latch not positive w/o best day) |
| GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long | Gen | 0/6 | 0 | 37 | -0.52 | -19.22 |  | 14% | -8.42 | -8.42 | -8.42 | -27.64 | keep -2 (post-latch not positive w/o best day) |
| heat_fade_long | On Deck,Primary | 0/6 | 0 | 69 | -0.41 | -28.25 |  | 11% | -23.69 | -33.85 | -33.99 | -51.44 | keep -2 (post-latch not positive w/o best day) |
| GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long | Gen,Testing C | 0/5 | 0 | 28 | +0.31 | +8.80 | 129% **1 day** | 18% | -24.59 | -14.20 | -14.94 | -15.79 | keep -2 (post-latch not positive w/o best day) |
| GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long | Gen,Testing B | 0/5 | 0 | 13 | +0.53 | +6.89 | 121% **1 day** | 18% | -34.08 | -34.08 | -35.54 | -27.19 | keep -2 (post-latch not positive w/o best day) |
| GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long | Gen | 0/5 | 0 | 0 |  | +0.00 |  |  | -37.96 | -37.96 | -37.96 | -37.96 | keep -2 (post-latch not positive w/o best day) |
| GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short | Gen | 0/5 | 0 | 0 |  | +0.00 |  |  | -25.24 | -25.24 | -25.24 | -25.24 | keep -2 (post-latch not positive w/o best day) |
| GEN-261026-08-RSIslopege19-Ret5mge0p063-DayRngVsPrevge1p2-OPEN-SPYup-holdtr-short | Gen,Testing B | 0/5 | 0 | 0 |  | +0.00 |  |  | +2.44 | +2.44 | +2.44 | +2.44 | keep -2 (post-latch not positive w/o best day) |
| intraday_momentum | On Deck | 0/5 | 0 | 0 |  | +0.00 |  |  | -14.47 | -14.47 | -14.47 | -14.47 | keep -2 (post-latch not positive w/o best day) |
| CWT12-coil-k4-long | Testing A | 0/5 | 0 | 48 | -0.02 | -0.77 |  | 9% | -57.05 | -56.70 | -54.28 | -57.74 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-orl-p10-lowvol-long | Testing A | 0/5 | 0 | 43 | -0.06 | -2.77 |  | 6% | -26.58 | -24.95 | -27.75 | -29.65 | keep -2 (post-latch not positive w/o best day) |
| CWT14-failbrk-orl-p10-long | Testing A | 0/5 | 0 | 33 | -0.12 | -4.05 |  | 14% | -33.81 | -33.89 | -33.32 | -38.25 | keep -2 (post-latch not positive w/o best day) |
| GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short | Gen | 0/5 | 0 | 44 | -0.11 | -4.70 |  | 14% | -56.78 | -61.91 | -62.75 | -61.77 | keep -2 (post-latch not positive w/o best day) |
| GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short | Gen | 0/5 | 0 | 9 | -0.89 | -8.02 |  |  | -12.13 | -19.75 | -19.75 | -20.14 | keep -2 (post-latch not positive w/o best day) |
| GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long | Gen,On Deck | 0/5 | 0 | 23 | -0.50 | -11.47 |  | 20% | +2.49 | +2.49 | +2.49 | -8.98 | keep -2 (post-latch not positive w/o best day) |
| GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long | Gen | 0/5 | 0 | 28 | -0.42 | -11.70 |  | 39% | -55.36 | -60.44 | -61.21 | -65.99 | keep -2 (post-latch not positive w/o best day) |
| heat_fade_long-FD | On Deck | 0/5 | 0 | 83 | -0.41 | -34.23 |  | 21% | -38.53 | -45.83 | -45.76 | -65.86 | keep -2 (post-latch not positive w/o best day) |

## Part 2 — targeted remedies for the L3 BEZ failure mode (all 16,768 live trades, 9 accounts)
| remedy | trades removed | ΔR total | R / removed trade | setups better (R) | setups worse (R) | worst setup | ΔR w/o best day |
|---|---|---|---|---|---|---|---|
| REENTRY6: no same-setup, same-symbol entry for 6 × 5-min bars after a stop | 44 (0.26%) | −5.6 | +0.13 | 5 (+7.7) | 3 (−13.3) | On Deck exhaustion_short −6.2 | −14.6 |
| REENTRY12 | 52 | −6.6 | +0.13 | 6 (+9.0) | 3 (−15.5) | Primary L3-fromopen −6.7 | −15.7 |
| REENTRYDAY: rest of day | 60 | −5.4 | +0.09 | 6 (+8.8) | 4 (−14.3) | Primary L3-fromopen −6.7 | −13.3 |
| FADEMOVE10: skip when the name has moved >10% from the open against the trade | 159 (0.95%) | −31.0 | +0.19 | 17 (+16.6) | 22 (−47.6) | Gen GEN-261020-09 −9.1 | −36.5 |
| FADEMOVE15 | 30 | −14.7 | +0.49 | 3 (+2.6) | 13 (−17.3) | Gen GEN-261019-04 −5.1 | −14.7 |
| FADEMOVE20 | 4 | −2.3 | +0.58 | 1 (+0.5) | 2 (−2.8) | Gen GEN-261019-04 −2.3 | −2.3 |

By family (ΔR, from remedy_by_family.csv):
- **REENTRY:** L3 −0.9 to −3.0, exhaustion_short −6.2, MF2 +1.5 to +2.6, RW4 +1.1 (day only).
- **FADEMOVE10:** GEN −19.0, L3 −12.1, NM −2.0, heat_fade_long +2.8, ST4 +1.1.

Primary L3-gap-slope-fromopen-FD:
- **REENTRY:** loses 5.9–6.7R over its 156 live trades. It gains about +3R on 11-17 (the three BEZ re-entries) but
  loses that and more on other days. The same remedy gains +2.1 to +3.2R on L3-gap-slope-rsi5hi-FD (Primary record).
- **FADEMOVE15** would not have touched today's Primary BEZ trades. Those entries were 6–13% above the open, and only
  10% catches 3 of the 4. FADEMOVE10 costs Primary L3-fromopen −5.4R.

**Verdict: neither remedy is targeted under the plan's test** (improves the total, < 5% removed, no setup worse by
more than 1R). Re-entries after a stop, and names already stretched against the trade, are positive on average in
the live record.

## Decision codes
- **LATCH-RW7 (Yes, conditional):**
  - If RW7-gapdn-bounce-early-short-FD moves to the Graveyard or Primary (both have the −2R latch), it runs with no
    per-setup latch there; the account halt stays.
  - No change today: Testing F, where it runs now, has the latch off.
- **LATCH-RW1 (Optional, conditional):**
  - The same, for RW1-gapdn-bounce-flowsell-short-FD, if it is ever promoted from On Deck (promotions are on hold).
  - The evidence is thinner: the gain comes from 3 days.
- **No codes for:** a board-wide level change (keep −2), any Primary setup's own level, REENTRY, or FADEMOVE.
