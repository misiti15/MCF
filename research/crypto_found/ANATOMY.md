Educational only — not financial advice
# Crypto price-action anatomy: top 10 Alpaca coins (2026-11-26)
**Description, not a strategy search.** No entry or exit rule was scored, and no threshold was fitted. Every cut is a round, a-priori definition (2σ, 3σ, 2/3/5 %, a 50 % wick, fixed session hours). About 200 descriptive cells were looked at, so a single |t| near 3 is within chance (sqrt(2 ln 200) ≈ 3.3). Nothing here counts toward the crypto N, and nothing goes to the backlog.
- **Data:** Alpaca 1-min cache, clean signal bars only (`mcf.crypto.exec1m.clean_traded`: the Amendment-1 bad-print filter, then traded minutes with volume > 0). FIT + CHECK only, 2021-01-01..2026-05-25. LOCKED was never read: the loader clips it, and the script asserts that `MCF_CRYPTO_ALLOW_LOCKED` is unset.
- **Method:** returns are log close-to-close of real buckets, and a bucket with no trade is missing. Event means are **day-weighted**: the mean of per-UTC-day means, with a day-clustered t, so one mania day such as DOGE on 2021-01-28 cannot carry a row. Medians are also shown.
- **Costs** (`mcf/crypto/costs.py`, tier 1, 2026 spreads): round trip, taker both sides / maker entry + taker exit. Script: `anatomy.py`; charts `hour_profile.png`, `move_frequency.png`, `eth_btc.png`.
- **Big caveat (thin venue):** since 2023, alts trade in only 1-4 % of minutes, and in 30-70 % of hours. Prices are last trades, so they carry **bid-ask bounce** and **staleness**. Both inflate short-horizon reversal and fake "lead-lag". Section 4 shows one such artifact directly.

## 0. Top 10 by median daily traded $ volume (Alpaca venue)
| # | coin | median daily $ vol | since 2025 | hours with a trade 2021 / 2022 / 2023-24 / 2025-26 | RT cost taker / maker |
|---|---|---|---|---|---|
| 1 | BTC | 516,734 | 165,957 | 100 / 100 / 96 / 98 % | 0.66 / 0.48 % |
| 2 | ETH | 255,926 | 85,670 | 100 / 100 / 87 / 95 % | 0.67 / 0.48 % |
| 3 | DOGE | 103,291 | 18,147 | 100 / 100 / 68 / 80 % | 0.98 / 0.64 % |
| 4 | SOL | 98,531 | 44,902 | 100 / 100 / 29 / 91 % | 1.06 / 0.68 % |
| 5 | XRP (from 2024) | 71,263 | 37,737 | — / — / 100 / 92 % | 1.05 / 0.68 % |
| 6 | LINK | 39,292 | 8,556 | 100 / 100 / 51 / 68 % | 0.79 / 0.54 % |
| 7 | LTC | 25,515 | 4,304 | 100 / 100 / 51 / 59 % | 1.43 / 0.87 % |
| 8 | BCH | 16,714 | 2,044 | 100 / 99 / 45 / 51 % | 1.44 / 0.87 % |
| 9 | UNI | 15,180 | 1,756 | 100 / 100 / 33 / 50 % | 0.77 / 0.54 % |
| 10 | AVAX | 11,718 | 7,283 | 100 / 100 / 49 / 67 % | 1.44 / 0.87 % |

- **Next in line:** GRT ($10.6k), SUSHI, AAVE. DOT ($3.4k) misses, since it lists in 2023-08.
- **Capacity:** the venue is tiny. BTC trades ~$166k a day on Alpaca since 2025, and most alts trade $2-45k. A setup risking a few hundred dollars per trade on alts would be a visible share of a day's prints. Size limits must come from this table, not from the equity sizing.

## 1. Volatility vs the cost hurdle
| coin | daily σ | ATR 1h | ATR 4h | ATR 1d | day range med / p90 | ATR4h ÷ taker cost |
|---|---|---|---|---|---|---|
| BTC | 3.0 % | 0.59 % | 1.30 % | 3.71 % | 3.8 / 8.6 % | 2.0 |
| ETH | 4.1 | 0.76 | 1.68 | 4.75 | 4.8 / 11.0 | 2.5 |
| DOGE | 7.1 | 1.02 | 2.14 | 6.04 | 6.1 / 16.8 | 2.2 |
| SOL | 6.1 | 1.22 | 2.65 | 7.24 | 7.4 / 17.2 | 2.5 |
| XRP | 4.2 | 0.70 | 1.57 | 4.52 | 4.6 / 11.2 | 1.5 |
| LINK | 5.3 | 1.06 | 2.20 | 6.36 | 6.4 / 14.5 | 2.8 |
| LTC | 4.6 | 0.93 | 1.89 | 5.16 | 5.2 / 12.9 | 1.3 |
| BCH | 5.0 | 0.80 | 1.69 | 4.90 | 4.7 / 12.3 | 1.2 |
| UNI | 5.9 | 1.11 | 2.30 | 6.17 | 6.0 / 15.2 | 3.0 |
| AVAX | 5.2 | 0.96 | 2.06 | 6.08 | 6.0 / 14.5 | 1.4 |

**Moves that clear the hurdle:** the table gives the % of non-overlapping windows whose |close-to-close| move is at least X (chart: `move_frequency.png`).

| coin | 1h ≥2 / 3 / 5 % | 4h ≥2 / 3 / 5 % | 12h ≥2 / 3 / 5 % |
|---|---|---|---|
| BTC | 1.9 / 0.6 / 0.1 | 9.6 / 3.8 / 0.8 | 24 / 13 / 4.4 |
| ETH | 4.0 / 1.3 / 0.2 | 15.9 / 7.6 / 2.0 | 35 / 21 / 8.7 |
| DOGE | 9.8 / 4.6 / 1.5 | 24.0 / 13.4 / 5.1 | 44 / 28 / 13.7 |
| SOL | 9.6 / 4.2 / 1.1 | 28.4 / 16.3 / 6.4 | 51 / 35 / 17.7 |
| XRP | 4.0 / 1.5 / 0.4 | 14.6 / 7.3 / 2.4 | 32 / 19 / 7.8 |
| LINK | 8.6 / 3.2 / 0.7 | 26.8 / 13.9 / 4.6 | 48 / 32 / 14.7 |
| LTC | 7.2 / 2.6 / 0.6 | 21.0 / 10.7 / 3.3 | 39 / 24 / 10.6 |
| BCH | 6.3 / 2.5 / 0.6 | 20.4 / 10.7 / 3.6 | 41 / 26 / 11.2 |
| UNI | 10.1 / 3.9 / 0.9 | 28.8 / 16.0 / 5.7 | 52 / 35 / 17.1 |
| AVAX | 8.6 / 3.4 / 0.8 | 26.8 / 14.2 / 4.2 | 47 / 32 / 15.3 |

**Meaning for setup design:**
- **1h is too short:** a typical hour (ATR 0.6-1.2 %) is about the round trip, and only 2-10 % of hours move ≥ 2 %. **4h-12h is the natural horizon:** 10-29 % of 4h and 24-52 % of 12h windows move ≥ 2 %, 2-3× the taker cost.
- **The best range per unit of cost** is UNI, LINK, SOL, ETH and DOGE (ATR4h ÷ cost ≥ 2.2). LTC, BCH, AVAX and XRP pay 1.0-1.4 % taker on 2026 spreads (AVAX/BCH/LTC 2026 spreads are ~0.9 %, vs ~0.25 % in 2025), so they are poor intraday vehicles.
- **Stops** need ≥ 1-1.5 × ATR4h (2-4 %) to keep costs below ~0.25R.

## 2. Time of day, day of week, sessions (UTC; pooled top 10, chart `hour_profile.png`)
| hours | $vol share | rel |1h r| | mean 1h r bps | median | t | BTC mean |
|---|---|---|---|---|---|---|
| 00-03 | 15.0 % | 1.09 | -1 | -0 | -0.2 | -1 |
| 03-06 | 11.0 | 0.87 | +1 | +1 | +1.2 | -0 |
| 06-09 | 8.9 | 0.90 | -0 | +1 | +0.6 | +1 |
| 09-12 | 8.9 | 0.88 | +0 | +0 | +0.4 | +0 |
| 12-15 | 14.1 | 1.14 | -1 | -1 | -1.3 | -0 |
| 15-18 | 16.0 | 1.14 | -0 | -1 | +0.4 | -0 |
| 18-21 | 14.0 | 0.99 | -1 | +2 | +0.2 | +0 |
| 21-24 | 12.1 | 0.98 | +1 | +3 | +1.7 | +2 |

| window | rel |1h r| | $vol share / hours share | mean 1h r bps (t) |
|---|---|---|---|
| Weekday | 1.05 | 79 / 71 % | -0 (-0.2) |
| Weekend | 0.86 | 21 / 29 % | +0 (+0.7) |
| US 13-20 weekday | **1.19** | 30 / 21 % | -1 (-1.2) |
| Asia 00-08 / EU 08-13 / late 20-24 weekday | 1.01 / 0.97 / 0.99 | 23 / 13 / 13 % | +0 / +0 / +2 (≤ 1.4) |
| Funding hours (23, 00, 07, 08, 15, 16) | 1.06 | 27 / 25 % | +1 (+0.8) |
| Fri 07-09 (Deribit expiry) vs Mon-Thu 07-09 | 1.03 vs 0.96 | — | -2 (-0.7) vs +3 (+1.4) |
| Last Friday of the month, 07-09 | 1.18 | — | -13 (-1.6), n = 811 coin-hours |

- **Day of week** (daily close to close, pooled): the means run from Thu -36 to Wed +32 bps, all with |t| ≤ 1.4, against a daily σ of 4.3-5.9 %. Sat and Sun carry 10 % of $ volume each and have the lowest σ.
- **Drift by hour, weekday or session is noise.** Every mean is ≤ 4 bps an hour with |t| ≤ 2.1, which is 1/15 of the cost. The 24-hour mean-return profiles even correlate **negatively** across regimes (-0.01 to -0.23).
- **The vol and volume profile is real and stable.** The US equity session (13:30-20:00, peaking at 14-15 UTC) carries 1.2-1.3× the average hourly move. 00-01 UTC (the daily close and funding) is the second peak. Asia late / EU morning (04-11) is the quietest stretch, at 0.85×. Weekend moves are 0.75-0.88× weekday moves in every regime.
- **Funding resets and Deribit expiry** add at most a 3-18 % bump in |r|, and no direction. **Setup design:** time windows are useful for *when there is movement to capture*, chiefly the US session and the 00 UTC turn. Use them as filters, never as a signal. Expect half the opportunity on weekends.

## 3. Structure
**Lag-1 autocorrelation of returns** (median over coins): everything is slightly negative, with no momentum at intraday horizons.

| tf | all (range over coins) | 2021 | 2022 | 2023-24 | 2025-26 |
|---|---|---|---|---|---|
| 15m | -0.006 .. -0.039 | -0.010 | -0.008 | -0.042 | -0.030 |
| 1h | +0.005 .. -0.034 | -0.006 | -0.015 | -0.030 | -0.014 |
| 4h | -0.001 .. -0.037 | -0.033 | -0.006 | -0.047 | +0.016 |
| 1d | -0.011 .. -0.090 | -0.072 | -0.025 | -0.032 | -0.061 |

**After a ≥ 2σ 1h move** (σ is the trailing 30-day 1h σ; returns are signed, + = continuation):

| set | n | +1h bps (t) | +4h bps (t) | +4h cont % | +12h bps (t) | +12h median |
|---|---|---|---|---|---|---|
| up moves | 7,467 | -11 (-3.9) | -23 (-4.8) | 49 | -28 (-2.9) | +8 |
| down moves | 8,012 | -21 (-8.3) | **-54 (-10.2)** | 43 | -89 (-7.7) | -30 |
| down, by regime 2021 / 2022 / 23-24 / 25-26 | — | — | -120 / -25 / -48 / -35 | — | -184 / -61 / -77 / -52 | — |
| up, by regime 2021 / 2022 / 23-24 / 25-26 | — | — | +1 / -44 / -15 / -38 | — | +31 / -82 / -18 / -46 | — |

**The down-shock bounce, per coin** (long side, 4h after a ≥ 2σ down hour, compared with the cost):

| coin | n | +4h bps (t) | median | skip 1st hour: h+1→h+4 | cost taker / maker |
|---|---|---|---|---|---|
| BTC | 1218 | +30 (6.4) | +19 | +19 (4.8) | 66 / 48 |
| ETH | 1219 | +32 (4.8) | +26 | +21 (3.8) | 67 / 48 |
| DOGE | 872 | +69 (5.6) | +42 | +55 (5.1) | 98 / 64 |
| SOL | 817 | +51 (4.3) | +29 | +29 (3.0) | 106 / 68 |
| LINK / UNI | 781 / 636 | +48 / +44 | +24 / +33 | +39 / +42 | 79 / 54, 77 / 54 |
| XRP / LTC / BCH / AVAX | 507-761 | +21 .. +51 | +22 .. +41 | +1 .. +31 | 105-144 / 68-87 |

**Flushes (1h z ≤ -3), long side:**

| set | n | +4h bps (t) | +4h med | +12h bps (t) | +12h med |
|---|---|---|---|---|---|
| lower wick ≥ 50 % of the range | 100 | -35 (-0.7) | +31 | +98 (+1.6) | +43 |
| no long wick | 2,687 | +54 (+5.8) | +26 | +106 (+5.7) | +32 |
| BTC + ETH | 917 | +21 (+2.5) | +15 | +39 (+2.9) | +24 |
| 8 alts | 1,870 | +69 (+5.6) | +35 | +132 (+5.4) | +43 |
| 2021 / 2022 / 2023-24 / 2025-26 | 501 / 869 / 679 / 738 | +139 / +17 / +45 / +37 | +80 / -1 / +34 / +27 | +228 / +72 / +90 / +78 | +118 / -17 / +53 / +28 |

**The other structural tests:**
- **Asia range (00-08) breakouts, 08-20 UTC:** 46 % of coin-days break up first, 45 % down first, 22 % both sides. From the broken level to 20:00: up -23 bps (t -3.1, median -5), down -17 bps (median +6). Only 49-51 % close beyond the level (44-55 % in every regime): **no follow-through**.
- **CME weekend gap** (Fri 21:00 → Sun 23:00): 24h fill rates are 85 / 68 / 34 % for gaps < 0.5 / 0.5-2 / ≥ 2 %. A **mirror level** at the same distance on the other side is touched 88 / 75 / 34 % (BTC 0.5-2 %: 59 vs 77 %). **"Gaps fill" is just distance, with no edge.**
- **Round numbers** (multiples of 10^(⌊log10 p⌋-1), hourly touches, vs control levels at +0.37 step): price holds beyond the level 4h later 51.2 vs 50.5 % (from below) and 49.2 vs 49.9 % (from above). **No magnet or rejection.**
- **Wick reversals:** a long lower wick on a ≥ 3σ flush hour is rare (100 events) and adds nothing. The bounce comes from the flush itself, not the wick.

**Setup design:**
- **(a)** Intraday crypto on Alpaca is **mean-reverting**, never momentum: big up hours fade, big down hours bounce. **(b)** The long-only expression is "buy after a flush": +20-70 bps over 4h, +40-130 bps over 12h, medians about half the means.
- **(c)** About a third of the 4h bounce sits in the first hour, where bid-ask bounce lives (BTC +30 → +19 bps when it is skipped): enter on a resting limit, never chase the print. **(d)** Breakouts, Asia-range plays, gap fills and round numbers have no measurable edge and should not seed setups.

## 4. Cross-asset
**Beta and correlation to BTC on 1h returns** (BTC regime = BTC daily close vs its SMA50, known at the prior close):

| coin | β up / down | ρ up / down | ρ SPY RTH (β) | crypto bps on SPY ≤ -1 % / ≥ +1 % days | ρ(SPY 1st hr, crypto rest) |
|---|---|---|---|---|---|
| ETH | 0.99 / 1.12 | 0.77 / 0.84 | 0.48 (1.46) | -269 / +245 | +0.08 |
| DOGE | 1.18 / 1.11 | 0.50 / 0.51 | 0.41 (1.65) | -364 / +253 | +0.10 |
| SOL | 1.16 / 1.28 | 0.57 / 0.65 | 0.48 (1.76) | -370 / +291 | +0.02 |
| XRP | 0.95 / 0.98 | 0.51 / 0.64 | 0.42 (1.51) | -256 / +297 | +0.01 |
| LINK | 1.16 / 1.22 | 0.63 / 0.72 | 0.44 (1.76) | -364 / +218 | +0.04 |
| LTC | 1.08 / 1.11 | 0.62 / 0.76 | 0.43 (1.32) | -270 / +195 | +0.09 |
| BCH | 0.99 / 1.01 | 0.61 / 0.71 | 0.43 (1.32) | -271 / +139 | +0.10 |
| UNI | 1.16 / 1.20 | 0.59 / 0.66 | 0.39 (1.57) | -316 / +251 | -0.00 |
| AVAX | 1.20 / 1.34 | 0.57 / 0.69 | 0.45 (1.67) | -340 / +204 | +0.07 |
| BTC | 1 | 1 | 0.47 (1.14); 2023 0.42, 2024 0.42, 2025 0.56 | -214 / +197 | +0.06 |

- **Betas and correlations rise in BTC down-trends** in 8 of 9 cases. Diversification across alts disappears when BTC falls.
- **Lead-lag (median over alts):** ρ(alt_t, BTC_t-1) = +0.022 at 1h and -0.004 at 4h; the reverse is +0.013 / -0.014. **BTC barely leads at 1h, and the lead is gone by 4h.**
- **After a BTC ≥ 2σ hour,** the alt's next hour moves +10 bps in BTC's direction; for "lagging" alts (moved < ½ of BTC) +38 bps at 1h, +26 at 4h (t 6.7). That splits into **+59 bps when the alt barely traded** (a stale last print) and **+6 bps (t 0.8) when it traded ≥ 15 minutes**: **a stale-print artifact, not a tradeable lag** (it also explains round 1's failed "BTC→lagging alt" seed).
- **ETH/BTC (`eth_btc.png`):** +220 % in 2021, -8 % in 2022, -50 % in 2023-24, -23 % in 2025-26; above its SMA50 on 31-61 % of days; the 30-day trend does not persist (ρ with the next 30 days -0.13 to +0.17).
- **SPY (equity cache, 2022-10..2026-05):** crypto in US RTH co-moves at ρ 0.39-0.48 (0.47-0.56 in 2025) and moves 2-4 % the same way on SPY ±1 % days. SPY's first hour barely predicts crypto's rest of session (ρ ≤ 0.10). **Use SPY as risk context** (avoid longs into a weak tape), **not as a lead signal**.

## 5. Regime stability
| effect | 2021 bull | 2022 bear | 2023-24 | 2025-26 | stable? |
|---|---|---|---|---|---|
| US-session |1h r| vs all | 1.09 | 1.21 | 1.29 | 1.28 | **yes** |
| Weekend / weekday |1h r| | 0.88 | 0.78 | 0.75 | 0.76 | **yes** |
| Lag-1 autocorr at 1h / 15m | ≤ 0 | ≤ 0 | ≤ 0 | ≤ 0 | **yes** (weak) |
| Down ≥ 2σ → 4h bounce (bps) | +120 | +25 | +48 | +35 | **sign yes**, size no |
| Up ≥ 2σ → 4h (bps) | +1 | -44 | -15 | -38 | fade, except 2021 |
| Flush ≤ -3σ → 12h median (bps) | +118 | -17 | +53 | +28 | **flips in the bear** |
| Asia-range up break → close beyond | 50 % | 44 % | 51 % | 52 % | no edge anywhere |
| CME gap fill vs mirror (24h, ≥ 0.5 %) | 51 vs 46 % | 43 vs 57 % | 49 vs 51 % | 43 vs 42 % | no edge anywhere |
| Hour-of-day mean-return profile | — | ρ vs others ≤ 0 | — | — | **flips (noise)** |
| Alt β to BTC | ~1.0-1.2 | ~1.0-1.3 | — | — | stable; higher in BTC down-trends |
| ETH/BTC trend | +220 % | -8 % | -50 % | -23 % | regime-specific |

## 6. Verdict per effect against the cost hurdle (taker 66-144 bps, maker 48-87 bps round trip)
| effect | gross size | verdict |
|---|---|---|
| Hour / weekday / session / funding / expiry drift | ≤ 4 bps an hour, ≤ 36 bps a day, |t| ≤ 2 | **noise** |
| Vol profile (US session 1.2-1.3×, weekend 0.8×) | changes the opportunity, not the direction | **useful as a filter** |
| Down ≥ 2σ hour → 4h bounce, BTC / ETH | +30 bps (median +19-26) | **below the hurdle** (maker 48) |
| Down ≥ 2σ hour → 4h bounce, DOGE / LINK / UNI | +44-69 bps (median +24-42) | **borderline** vs maker 54-64 |
| Flush ≤ -3σ → 12h, alts | +132 bps mean, +43 median; negative median in 2022 | **borderline, regime-dependent** |
| Up ≥ 2σ hour → fade | -23 bps at 4h | **not usable** (needs a short; Alpaca is long-only) |
| Asia-range breakout, CME gap, round numbers, wick shape | ≈ 0 vs control | **noise** |
| BTC leads alts (1h) | +6 bps when the alt really traded | **noise** (stale-print artifact) |
| SPY co-movement | ρ 0.4-0.56, contemporaneous | **context only** |

## 7. Implications for the first hand-built setups
1. **Hold 4-24 h, with stops ≥ 2-4 %** (≥ 1-1.5 × ATR4h), so the 0.5-1.4 % round trip is ≤ 0.25R. 1h scalps cannot clear costs on Alpaca.
2. **Lead family: long-only "flush rebound".** Trigger: a 1h z ≤ -2..-3 down hour. Entry: a resting maker limit below the flush close, never a market buy into the print. Coins: the best range-to-cost ones (ETH, SOL, DOGE, LINK, UNI, plus BTC for capacity). Gate: a regime switch (e.g. off when BTC is below its SMA50 *and* falling), because the median flips in 2022. Round 2's flush seed lost (-0.17R, few trades, taker-heavy), so the bounce is real but thin: pre-register one or two variants, not a grid.
3. **Use the vol clock, not a drift clock.** Let the US session and the 00 UTC hour be when signals are allowed, and treat weekends as lower opportunity. Do not build a time-of-day drift setup.
4. **Drop these as setup seeds:** momentum or breakout (Asia range, 1h continuation), CME gap fill, round numbers, BTC→alt lag and SPY-lead. Each is noise after costs or a data artifact.
5. **Plan for thin books:** size each trade against the median daily $ volume in section 0; prefer BTC / ETH / SOL / XRP ($38-166k a day since 2025); count a zero-print hour as no signal; LTC, BCH and AVAX are poor intraday vehicles at 2026 spreads (~0.9 %).
6. **Biases:** survivorship (delisted pairs are missing), last-trade prices on a thin venue (bounce and staleness), and 2021 mania days inflate means (medians shown). Crypto is not live, so no rule, config or ledger change falls inside this window.

*Educational only — not financial advice.*
