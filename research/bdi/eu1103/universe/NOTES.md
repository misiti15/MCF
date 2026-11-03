Educational only — not financial advice

# eu1103 / universe — is our universe the right pool? (owner Q2, 2026-11-03)

Research only. Nothing in `config/`, no setup, exit, ledger, backlog or live-path file was changed. Costs are in
everywhere (live: journal `pnl_adj` / $ risk; two-year and live-period re-score: production 1c + 1 bps per side, +2c on
stops, time-of-day entry multiplier, `gates.lab_trades`). The rule-19 locked block 2024-11-01..2025-02-28 was never
loaded (asserted; `lib.daily()` drops it; the daily fetch starts 2025-03-03). Live = **paper** fills (rule 7); the
live-period re-score is a backtest on live dates, **not** live fills.

**Configurations: 10 distinct universe rules** (S1 top-300 / 500 / 800 dollar-ATR, S2 move history, S3 ATR% >= 3,
S4 no idiosyncratic names, S5 ADV >= $300M, L1 floor $50M, L2 floor $20M, C1 R >= $0.25/share), **scored 188 times**
(rule x setup-or-pooled x data set: 2y 144, live 24, live-period re-score 12, C1 5, CF-overlap 2, ETB what-if 1), plus
~330 descriptive bucket cells. 7 rules were written down in `PLAN.md` before the 2-year and re-score results were read;
S4 was taken from the live buckets (so it is live-derived); C1 and the CF-overlap check were added afterwards
(post hoc, labelled). At N ≈ 188 the try-count bar is t ≥ sqrt(2 ln 188) = 3.24.

Setups (8 busiest live by trades 10-06..11-02, one per family): CWT14-failbrk-orl-p05-long, CWT14-failbrk-pdl-p05-long,
CWT12-coil-k4-long, CWT14-failbrk-pdh-p10-short, heat_fade_short-FD, RW7-gapdn-bounce-early-short-FD,
RW2-exhaustion-noon-adv150-short-FD, L3-gap-slope-fromopen-FD. Masks are the live modules' own `mask()` / `score()`.

## Failures first

1. **No universe rule makes the book green.** The best pre-declared rule (S1 top-500) leaves every pooled number
   negative after costs: 2y VALID −0.037R (base −0.060R), live-period re-score −0.078R (base −0.093R), live paper
   −0.145R (all setups, base −0.138R). The share of green sessions goes up but stays below half (2y VALID 39% vs 20%; live
   paper 2/20 → 2/20). **The universe is not where the missing edge is.**
2. **A larger universe is worse on every test.** Lower floor $50M on 2y (L1, survivor-biased lab names): the names it adds
   average −0.116R TRAIN / −0.088R VALID vs base −0.080 / −0.060; worse in 7 of 7 setups on both splits. Floor $20M on the
   live period (L2, the 10-05 universe, not survivor-biased, 2,419 names): added names −0.128R (n 19,882, t −7.7) vs base
   −0.093R (n 15,029); worse in 6 of 7 setups (only RW2 better). The sub-$95M names that live actually traded (398 trades,
   setups with a lower floor) were −0.081R (t −0.72, −0.152R without the best day): too few, too noisy.
3. **S4 (drop idiosyncratic names) fails.** Live, names with no sector anchor (residual corr < 0.15 with every sector
   SPDR: MDB, ZS, MSTR, GME, HOOD, ZM, ...) were the worst bucket: −0.246R, −0.111R vs their setup's mean (t −3.19, 820
   trades, negative in all 5 accounts). On 2 years the same rule does nothing (kept-minus-dropped −0.020R TRAIN t −1.60,
   −0.001R VALID). A live-only pattern from 20 sessions; not proposed.
4. **S2 (names with a history of big moves) adds nothing:** +0.008 / +0.009R per session (t 1.33 / 1.15), kept −0.076 /
   −0.057R. "Big movers" are not better signal hosts for these setups.
5. **S5 ADV >= $300M** passes on 2y (+0.025 / +0.033R, t 5.3 / 5.7) but **fails live** (kept-minus-dropped −0.024R) and
   adds only +0.011R (t 0.63) on the live-period re-score.
6. **Borrow is not an opportunity.** Shorts skipped as "not shortable/ETB" (what-if run 2, 3,902 signals on 307 names,
   mostly single-stock leveraged ETFs NBIL, CRWG, MSTU, MSTX): −0.095R gross, the same as the shorts we took (−0.100R
   gross). On 2 years non-ETB names are −0.009 / −0.012R vs setup mean. Unlocking HTB names would add borrow fees and no edge.
7. **The 2-year universe gain does not show up live under C1.** C1 (R >= $0.25/share) is the strongest 2y split
   (+0.145 / +0.159R per session, t 16.5 / 12.1, 8/8 setups) and holds on the live-period re-score (+0.162R, t 6.28), but on
   live paper it is +0.000R (t 0.02). Live friction is set by the quoted spread in bps (median 5–10 bps in every bucket,
   0.04–0.09R), not by cents per share as the lab model assumes, and the Testing cost filter CF (from 10-30) already
   skips the costliest entries. Live, only the very smallest stops lose clearly (R < 5c/share: −0.63R, n 67).

## What the evidence does say

- **Within today's universe (≥ $95M), live R is flat across liquidity, price, ATR%, stock vs ETF vs leveraged ETF, ETB
  and sector.** All buckets sit at −0.13..−0.15R; setup-mix-adjusted differences are within ±0.04R and |t| < 1.6 except
  the idiosyncratic-name bucket (failure 3). Live, the pool does not decide the result; the setups do.
  (live_buckets_out.txt)
- **On 2 years every bucket carries the same small skill over random entry: +0.02..+0.05R** (vs_rand, same symbol-day,
  same costs), in every ADV, price, ATR%, sector and move-history bucket. What changes between buckets is the **cost per R**:
  avg R + estimated cost is +0.54R at R < 5c/share and +0.01R at R > 75c, i.e. gross edge per trade is tiny and costs
  decide the sign (cost_mech_out.txt). This is the owner's "extremely small, almost scalping edges" in numbers: the
  setups beat a random entry by ~0.03R; the pool can only change how much of that the costs eat.
- **Smaller = cheaper, not smarter.** S1 / S3 / S5 / C1 all raise avg R by ~+0.02..+0.05R on 2y with the same vs_rand.
- **Larger = more expensive and not smarter.** Mid caps add trades with the same ~+0.03R vs random but higher cost per R.

| rule (pooled 8 setups) | 2y TRAIN kept / base R, kd (t) | 2y VALID kept / base R, kd (t) | live-period re-score kd (t) | live paper kd (t), all / busiest 8 | VALID setups ≥ base |
|---|---|---|---|---|---|
| S1 top-300 dollar-ATR | −0.066 / −0.080, +0.028 (4.88) | −0.029 / −0.060, +0.049 (6.47) | — | +0.023 (0.39) / +0.095 (2.19) | 7/8 |
| **S1 top-500 dollar-ATR** | **−0.069 / −0.080, +0.037 (6.24)** | **−0.037 / −0.060, +0.053 (7.08)** | **+0.036 (1.99)** | **+0.019 (0.42) / +0.048 (1.07)** | **8/8** |
| S1 top-800 dollar-ATR | −0.076 / −0.080, +0.084 (4.13) | −0.050 / −0.060, +0.071 (7.33) | — | +0.034 (0.57) / +0.046 (0.88) | 6/8 |
| S2 move history ≥ 3% | +0.008 (1.33) | +0.009 (1.15) | — | +0.029 (0.92) | 5/8 |
| S3 ATR% ≥ 3 | +0.036 (5.33) | +0.045 (5.05) | — | +0.012 (0.22) | 7/8 |
| S4 no idiosyncratic | −0.020 (−1.60) | −0.001 (−0.05) | — | +0.062 (1.21) | 5/8 |
| S5 ADV ≥ $300M | +0.025 (5.30) | +0.033 (5.68) | +0.011 (0.63) | −0.024 (−0.59) | 8/8 |
| C1 R ≥ $0.25/sh (post hoc) | +0.145 (16.5) | +0.159 (12.1) | +0.162 (6.28) | +0.000 (0.02) | 8/8 |
| L1 floor $50M (added) | added −0.116 vs −0.080 | added −0.088 vs −0.060 | — | — | 0/7 better |
| L2 floor $20M (added) | — | — | added −0.128 vs −0.093 | sub-95M live −0.081 (n 398) | 1/7 better |

kd = per-session mean of kept minus dropped trades, day-clustered. With the CF-like cost filter applied first, S1
top-500 still adds +0.015R (t 2.39) TRAIN / +0.033R (t 4.28) VALID (cf_overlap_out.txt).

Against the pre-declared bar (PLAN.md: pooled kd > 0 on TRAIN, VALID and live, t ≥ 1.0 on both 2y splits, ≥ 6/8 setups
not worse on VALID): **S1 top-300, top-500, top-800 and S3 pass; S2, S4, S5, L1, L2 fail.** No live t reaches 1.0 on all
setups (S1 top-500 busiest-8 t 1.07), and no kept book is positive.

## Proposal (backlog candidate, not a change) — UNI-1 "top-500 by dollar-ATR"

- **Rule:** each morning rank the live universe snapshot's names with ADV ≥ $95M by ADV × ATR% (the dollars that move
  in a name per day) and let the lab setups trade only the top 500. One number, one daily list, computable at 09:25 from
  the universe file the runner already builds (no new data).
- **Numbers:** 2y: kept 62% / 56% of trades, avg R −0.069 / −0.037 vs −0.080 / −0.060 (TRAIN / VALID), +0.037 / +0.053R per
  session (t 6.2 / 7.1), 8/8 setups not worse on VALID, green sessions 20% → 39% on VALID (14% → 19% TRAIN). Live-period re-score: kept 53%,
  −0.078R vs −0.093R (+0.036R, t 1.99), 5/20 green vs 2/20. Live paper: +0.019R all setups (t 0.42), +0.048R busiest 8
  (t 1.07); Primary +0.043R (t 0.45).
- **What it is and is not:** a cost-per-R filter, not a new edge — it roughly halves trades and lifts avg R by
  +0.02..+0.05R, but **every setup stays negative after costs**; it overlaps the Testing cost filter CF (still +0.015 /
  +0.033R on top of a CF-like filter on 2y). Not for Primary before a live test; it would go through
  `research/backlog.jsonl` and the gates (lead's call — this workstream did not touch the backlog).
- **What not to do:** do not lower the ADV floor (both tests worse), do not add HTB names, do not filter by sector or
  move history.

## New data sources (not used here)

- Sector: derived here from Alpaca daily bars (residual correlation with the 11 sector SPDRs, TRAIN-fitted for 2y).
  True GICS / industry codes are not in Alpaca; free SEC SIC codes or a paid reference feed would be needed.
- Short interest: not in Alpaca. FINRA's twice-monthly short interest is free but about two weeks stale; daily
  vendor estimates (e.g. Ortex, S3) are paid, roughly tens to hundreds of dollars a month or more for API access.
- Borrow fee: Alpaca gives only the shortable / easy-to-borrow flags; fee rates need a broker/vendor feed.

## Rule changes inside the windows used (research/ledger.jsonl)

Live window 10-06..11-02 spans: 10-20 scale-out fix / twin cap; 10-21 Graveyard opens, promotion = move; 10-23 per-setup
stop off in T1/T2/Gen; **10-27 GX1 5-minute clock** (new record version for every lab setup); 10-26..10-30 CWT12-coil-k4,
CWT14-pdl-p05, CWT13 moves to the Graveyard; **10-28 Primary size ~$5k → ~$4k**; **10-29 Primary −2R latched stop, BAR90,
Generator paused**; **10-30 Testing cost filter CF** (directly relevant: it filters on cost per R, as C1 does);
10-30 L3 pair promoted; 11-02 R2A in Testing 2, NS3-FD / RW4-FD to the Graveyard. Live bucket results mix these
versions. The 2-year and live-period re-scores use the lab rules with no live caps (no slots, no CF, no stops by setup).

## Files

`score2y.py` (2y trades), `analyze2y.py` → `analyze2y_out.txt`, `rules2y.csv`; `fetch_daily.py` (SIP daily bars,
read-only GET); `live_buckets.py` → `live_buckets_out.txt`; `live_rules.py` → `live_rules_out.txt`; `expand_live.py`
(5-min SIP bars, read-only GET, bars never stored) → `analyze_exp.py` → `analyze_exp_out.txt`; `cost_mech.py` →
`cost_mech_out.txt`; `cf_overlap.py` → `cf_overlap_out.txt`; `PLAN.md` (pre-declared rules). Scratch deleted.
ETB what-if numbers: inline query on the journals (run_id 2, `why=not shortable/ETB`, shorts), quoted in failure 6.
