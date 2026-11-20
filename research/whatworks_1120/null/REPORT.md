Educational only — not financial advice

# OUT-NULL: did our setups beat random entries? (every setup with 10 or more live trades)

**Summary for the owner**
- I tested 165 setups (27,383 live trades from 10-06 to 11-19). Each trade was compared with random entries on the same stock, day and side, using the same stop and target. About 1.46 million simulated entries in all.
- **Random minute within 30 minutes either side of the real entry:** 32 of 165 setups beat it on live R (p<0.05, about 8 would by luck). L3 fromopen, RW3, RW5 and ETF late dip are among them. ST7 is not (p≈0.10).
- **Random minute 1 to 30 minutes *after* the real entry:** only 1 setup beats it, ETF late dip (p=0.02). Luck alone would give about 8. For L3, RW3 and RW5, a random later entry did as well or better.
- What this means: the setups that work pick the right stock-day and avoid entering too early. The exact signal minute adds little, except for ETF late dip. This supports protecting Primary's current entry rules (which stock-day they pick, and not entering before the trigger). It does not support making them more precise.
- No change is recommended. One backlog idea: an entry-delay study for RW3 (it only gets a costs-in 2-year holdout test, no live change).

## Method
- **Trades.** I rebuilt the trades from the 10 account journals on the `origin/mcf-data*` branches (read at 11-20 ~17:20 UTC), using the same run-1 de-dup as `footrace.live_trades()`. R uses `cost_r_lr8` (LR8 applied to every row). That is ~0.04R per trade below the supplied `live_trades.pkl`, which kept the flat pre-11-12 basis (total R −4,241 vs −3,500, same 28,097 rows). Setups are pooled across accounts. 165 setups have 10+ trades; 492 trades had no bars or no valid risk and were left out.
- **Bars.** 1-min SIP bars from Alpaca, read-only GET, 13,360 symbol-days. They were cached under `ww_scratch/null/` and deleted when done. No MarcoFlow, no locked block, no orders.
- **Null.** For each trade I simulated every 1-min bar open from −30 to +30 min around the real entry minute. Entries are clamped to 09:50 and the setup's `window` end from `config/*.yaml`. Each candidate keeps the trade's own stop and target distance (as % of entry) and exits as follows:
  - stop order: a gap through the stop fills at the bar open;
  - target limit: needs 1 tick through;
  - if stop and target are hit in the same bar, the stop counts;
  - otherwise flat at the 15:55 bar open.
- **Costs.** LR8 `lot_costs` formula; checked to match exactly on test rows.
- **Draws per trade.** The ±30 window only has 31 to 61 distinct minutes (median 55), so ">=200 random entries per trade" can't be met with distinct entries. Instead every minute was simulated exactly and 4,000 draws were taken from them with replacement.
- **Setup null.** 4,000 resampled averages give the null mean, the 5–95% band, the percentile and an i.i.d. p-value.
- **Headline p.** The headline uses a **day-clustered p** on (trade R − its own candidate mean). It is more conservative, because trades on the same day are not independent.
- **Three nulls:** ±30 (the approved spec), pre-only (−30 to −1) and post-only (+1 to +30). The ±30 null is a soft bar: before the signal, price is usually still moving against these mostly reversal setups. Average across setups: pre −0.196R, post −0.066R.
- **"sim".** The same simulator at the real minute, entering at the bar open. It gives a clean edge with no live-fill slippage on either side. Live R is on average 0.06R below sim (slippage and fills).

## Does the replay match live? (tested on taken trades, actual prices)
- **All accounts:** exit type (stop/target/flat) matches on **96.3%** of trades. Spearman 0.95; Pearson 0.957 after dropping 15 tiny-stop outliers (0.30 with them). Median replay−live gap is 0.002R; the mean is +0.063R (live slippage).
- **Primary:** match 97.1%, corr 0.971, mean gap +0.029R.
- Verdict: good enough to test entry timing. Scale-outs, time stops and SPY exits (330 trades, about 1%) were replayed as plain brackets.

## Results: all 165 setups
| Test (live R unless noted) | p<0.05 | p<0.10 | BH q<0.10 |
|---|---|---|---|
| ±30 null, day-clustered, live | **32** | 39 | 18 |
| ±30 null, day-clustered, sim | 70 | 81 | 69 |
| ±30 null, i.i.d. resample, live / sim | 41 / 82 | 55 / 88 | 34 / 82 |
| ±30 null without best day, clustered, live | 25 | 29 | – |
| **Post-only null (random later entry), clustered, live** | **1** | 2 | – |
| Post-only null, clustered, sim | 11 | 15 | – |
| Pre-only null, i.i.d., sim | 99 | 103 | – |
| Luck alone (165 tests) | ~8 | ~16.5 | – |

Of the 32 setups that beat the ±30 null, only 13 have positive live avg R. 19 lose money yet still beat random entries (for example heat_fade_long, RW2, NS2). Their setup-wide expectancy is worse than their timing. 21 of the 37 live-positive setups do *not* beat the ±30 null.

## Primary's 5 (pooled across accounts; Primary-only slice in the last columns)
| Setup | n | Live avg | Null ±30 (5–95%) | Edge (live) | p clust | w/o best day: avg / edge / p | Best-day share | Post-null | p post | Primary-only n / live / null / p |
|---|---|---|---|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 384 | +0.195 | +0.076 (+0.026..+0.124) | **+0.119** | 0.002 | +0.142 / +0.124 / 0.007 | 42% | +0.207 | 0.60 | 170 / +0.177 / +0.042 / 0.001 |
| NM-ETF-late-dip-di-long | 33 | +0.198 | −0.006 (−0.115..+0.096) | **+0.204** | <0.001 | +0.180 / +0.190 / <0.001 | 20% | +0.002 | **0.02** | 15 / +0.075 / −0.078 / 0.007 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 196 | +0.144 | −0.001 (−0.072..+0.070) | **+0.144** | 0.015 | +0.027 / +0.132 / 0.037 | **83% (1 day)** | +0.238 | 0.91 | 162 / +0.139 / −0.010 / 0.002 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 204 | +0.098 | −0.012 (−0.063..+0.038) | **+0.110** | 0.001 | +0.007 / +0.111 / 0.004 | **94% (1 day)** | +0.129 | 0.84 | 173 / +0.067 / −0.044 / 0.001 |
| ST7-rsi50dn-long-pm-t1s1-FD | 56 | −0.094 | −0.220 (−0.342..−0.100) | +0.127 | 0.10 | −0.177 / +0.058 / 0.20 | n/a (net loss) | −0.184 | 0.21 | 41 / −0.197 / −0.238 / 0.33 |

The Primary-only p in the last column is the i.i.d. resample p.

**Avg R (sim, after costs) by entry offset, Primary 5:**

| Setup | −30..−16 | −15..−6 | −5..−1 | 0 (real) | +1..+5 | +6..+15 | +16..+30 |
|---|---|---|---|---|---|---|---|
| L3 | −0.18 | +0.04 | +0.15 | +0.19 | +0.21 | +0.22 | +0.20 |
| ETF late dip | −0.01 | −0.05 | +0.10 | **+0.17** | +0.11 | +0.07 | −0.14 |
| RW3 | −0.38 | −0.12 | +0.03 | +0.13 | +0.22 | +0.24 | +0.24 |
| RW5 | −0.32 | −0.01 | +0.07 | +0.13 | +0.14 | +0.14 | +0.13 |
| ST7 | −0.36 | −0.19 | −0.13 | −0.12 | −0.04 | −0.17 | −0.29 |

How to read it:
- **L3 and RW5:** the edge lasts about 30 minutes after the signal (no rush to enter, but don't go early).
- **RW3:** entries 5 to 30 minutes later were about 0.1R better. That is in-sample and comes from 28 days with one big day.
- **ETF late dip:** peaks exactly at the signal minute.
- **ST7:** no timing edge anywhere.

**Rule changes in effect during this window (from the ledger):**
- 10-13: per-lot stacking.
- 10-20: twin cap and per-setup −2R.
- 10-28: Primary size ~$4k.
- 10-29: Primary −2R latch.
- 11-12: LR8 costs (restated uniformly here) and LR3 after-cost halt.
- 11-16: TSZ1 testing half-size (R comparable).
- 11-17: SPYEXIT on the WB4 copies only (separate setups).
- 11-19: U9-TGT entry skip.
- Promotions and moves in the window: L3 Primary 10-21, demoted 10-22, re-promoted 10-30. RW3 and RW5 promoted 10-15 (moved 10-21). ST7 promoted 10-26. ETF late dip promoted 11-11.

The null keeps each trade's own geometry, so sizing changes do not affect R. Pooled figures mix Testing and Primary periods.

## Recommendation
1. **Protect** Primary's current stock-day selection and the "don't enter before the trigger" timing for L3, RW3, RW5 and ETF late dip. All four beat the ±30 null on live R, after costs and without their best day. RW3 and RW5 carry the 1-day tag, but their edge vs the null survives without that day (p 0.037 / 0.004).
2. **ETF late dip** is the only setup whose exact minute adds value (it beats the later-entry null, p=0.02). Treat its trigger timing as fragile; don't tune it.
3. **ST7** does not beat random entries (p 0.10, w/o best day p 0.20). This adds evidence for its existing review; it is not a new verdict.
4. **Backlog** (not a live change): entry-delay study (+5 to +15 min) for RW3, and possibly L3, on 2-year data with a costs-in holdout.
5. Don't read the ±30 count alone as "32 setups have skill". Against random later entries, the number is at luck level.

## Configurations and counts
- **Null variants:** ±30, pre, post.
- **Test types:** i.i.d. and day-clustered.
- **Measures:** live, sim, and without best day (live and sim).
- That is 165 setups × about 10 p-values, all reported in the CSV. Headline: day-clustered ±30 on live R, with post-only as the strict check.
- **Replays:** 27,383 actual-price replays plus 1,457,405 candidate-entry simulations; 4,000 resamples per null.
- **Chart:** 4 drafts; no other settings were tuned.

## Files
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/null/null_vs_live.png
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/null/null_results.csv
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/null/null.py
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/null/fetch.py (rebuilds the bar cache)
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/null/replay_agreement.json

Scratch (151 MB of bars, journals and pkl) has been deleted. To re-run, run fetch.py first to rebuild the bar cache.
