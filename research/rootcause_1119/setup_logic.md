Educational only — not financial advice.

# Root cause 11-19, dimension: SETUP LOGIC (L3-gap-slope-fromopen-FD and ST7-rsi50dn-long-pm-t1s1-FD)

Research only. No config, setup, exit or order change (market hours). Costs in throughout (lab: gates.prod_r production
costs with time-of-day entry costs; live: pnl_adj, R = pnl_adj / (|entry - stop| x shares)). The rule-19 locked block
2024-11-01..2025-02-28 was never read (lib.load_month refuses it). Work files:
`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119/sl_work/`
(classify.py, lab.py, an.py, an2.py, live.py, family.py, fam_an.py and their outputs).

## Plain-English answer

**Stacking is not the root cause on either setup. Each setup's own rule set is.** In both cases the rule, read literally,
turned a "single-name" setup into **one market-direction bet placed many times**, and on 11-19 the market went the
other way.

1. **L3 (Gap-Down Recovery Fade, short) shorted SPXS/SQQQ because nothing in its rule stops it from trading inverse
   ETFs, and on an inverse ETF the rule means the opposite of what it means on a stock.** The rule is: gap <= -2.66%,
   20-bar slope up, and price > 3.46% above the open → short. On a stock that is "fade a bounce after bad news" — a
   *market-short-leaning* bet (2-year lab: R falls as SPY rises after entry, corr −0.26). On SPXS (3x inverse S&P) the
   same numbers mean "S&P gapped UP ~0.9% and has since FALLEN ~1.15% from its open" — shorting SPXS is **buying the
   S&P after an intraday sell-off**, a *market-long* bet (lab corr with SPY after entry **+0.26**, the sign flips). This
   is an unintended universe leak, not the mechanism the setup was mined for (its LAYERS/docstring describe a gap-down
   stock; the lab universe simply never excluded inverse products).
   - **On a falling-market day the rule's universe becomes almost only inverse products.** 11-19: every one of the 42
     distinct symbols L3 signalled was an inverse/levered-inverse product (35 classified inverse + 7 unlisted
     single-stock inverse tickers like MSTZ/BMNZ/PLTD; FNGD is a -3x ETN), **0 stocks**. Only SPXS and SQQQ were
     easy-to-borrow, so all 6 lots went into two names that are both "long the index". In the 2-year lab, when SPY is
     down > 0.5% from its open at the entry bar, 33% of L3's fires are inverse products (vs 0.3% when SPY is up > 0.5%).
   - **Live record split (paper, Primary + Testing 1, 10-12..11-19):** stocks 336 trades, win 66%, **+0.247R**, +83.0R
     (w/o best day +0.196R, best day 39% of total); plain ETFs 11, +0.234R; leveraged long ETFs 35, +0.261R; **inverse
     ETFs 17 trades, win 29%, −0.530R, −9.0R** (w/o best day −0.67R). Unlisted (single-stock inverse, e.g. BEZ) 4, −4.3R.
     Inverse products are 4% of L3's live trades and **−13.3R** of its result, while the other 382 trades made +94.7R.
   - **2-year lab split (first fire per symbol-day, n 5,150):** stocks −0.057R (n 3,878), leveraged −0.040R (n 903),
     inverse −0.072R (n 229), plain ETFs +0.265R (n 140, lumpy: best day 116% of total). The lab version of L3 loses in
     every class (known, research/l3leash: the lab cannot apply the live ETB filter that drives live L3's edge), so the
     lab cannot show the inverse leg as much worse than the rest on average. What the lab does show clearly is the
     **sign flip of the market bet** (table below) — inverse legs lose on exactly the days the stock legs win.

2. **ST7 (RSI Collapse Dip Buy, long) bought 7 names in one minute because of an indicator artifact at the 10:45 bar,
   not because 7 independent dips happened.** ST7's trigger is "RSI(14) crosses below 50 AND RSI(14) <= 30" on the same
   5-minute bar — a 20+ point drop in one bar, normally rare. MCF's RSI is computed on continuous 5-minute bars that
   include the prior session (mcf/research/heat.py `_rsi_simple`, live in LabStrategy.generate with `prior5`), so the
   overnight gap is one of the 14 changes until **10:45, when it leaves the window**. On a gap-up day RSI is held up by
   the gap until 10:40 and then collapses at 10:45 in every gap-up name that has faded (median |RSI change| 10:40→10:45
   is 10.5 points vs 2-5 at other bars; 20% of symbols move > 20 points on that bar vs < 2% elsewhere).
   - **The 10:45 bar is 58% of ST7-FD's 2-year fires (651 of 1,114) and 64% of its live trades (37 of 58). Every one
     of those 651 lab fires is a gap-up name (median gap +2.5%).** So most of "RSI Collapse Dip Buy (all day)" is
     really "gap-up names that gave back the gap, all at once at 10:45". 51% of 10:45 fires come in clusters of 5+
     names in the same bar (vs 3.5% for other bars); 96% of the 7+-name clusters happen on SPY gap-up days. 11-19 was
     exactly that: market gapped up and faded, 7 names fired on the 10:44 bar.
   - **Is the per-name edge independent? No.** In 5-minute clusters of 3+ names, all trades end the same way 34% of the
     time vs 14% expected if they were independent. R rises 0.31R per +1% SPY move after entry (corr +0.28). SPY falls
     > 0.5% after entry: win 28%, −0.49R (n 137); SPY rises > 0.5%: win 75%, +0.43R. A 7-name cluster is closer to one
     or two bets than seven.
   - **Per-name edge is thin, so there was nothing to "capitalize on".** ST7-FD 2-year lab: n 1,114, win 54%,
     **+0.045R, day-t 1.01**, w/o best day +0.037R, worst day −26.1R (2025-04-08, 24 names at 10:45). Unseen half
     (< 2026-03-10) −0.023R. Live: 58 paper trades, −3.4R (−0.06R/trade; stocks 50, +0.067R; plain/levered ETFs 7, −7.7R,
     all on 11-19 plus one other day). The record that was promoted came from the *windowed* source rule (13:35-15:00:
     lab n 176, +0.133R, t 1.69); the FD copy kept that headline but removed the window, letting the 10:45 artifact in.
   - Cluster size itself does not make ST7 worse per trade (7+-name clusters +0.094R/trade, n 303; singletons +0.024R).
     The problem is a weak, market-correlated edge fired many times at once — a setup-rule problem, not a stacking one.

**Answer to the owner's question.** A setup that is truly ~100% (independent per-name edge) *should* take every
opportunity. Neither of these is that: L3's live edge lives on stocks (+0.25R) and its inverse-ETF legs are a hidden
opposite bet (−0.53R); ST7-FD's 2-year per-trade edge is +0.045R (t 1.0) and its big bursts are one correlated
gap-fade bet created by an RSI warm-up artifact. Capping stacks would only have shrunk the damage; fixing the rules
removes the failure mode. Today's −15.2R from these two setups (−8.67 ST7, −6.49 L3) traces to: L3 inverse products
(−6.49R, 100% of L3's loss) and ST7's 10:45-artifact burst (−7.53R of ST7's −8.67R).

## Tables

### L3 — R by symbol class x SPY move from entry to the close (2-year lab, first fire per symbol-day)

(see `sl_work/an2_out.txt`; n / avg R)

| class | SPY ≤ −0.5% | −0.5..−0.15 | ±0.15 | +0.15..+0.5 | SPY ≥ +0.5% | corr(R, SPY after entry) |
|---|---|---|---|---|---|---|
| stocks | 697 / **+0.352** | 774 / +0.170 | 1006 / −0.107 | 809 / −0.206 | 589 / **−0.541** | −0.26 |
| leveraged long ETFs | 113 / +0.380 | 211 / +0.332 | 289 / −0.078 | 184 / −0.372 | 106 / −0.547 | −0.25 |
| **inverse ETFs / long VIX** | 47 / **−0.561** | 23 / −0.240 | 77 / −0.118 | 46 / +0.068 | 36 / **+0.589** | **+0.26** |

On a down day (today), L3's stock legs are its best trades and its inverse legs are its worst — and on a down day the
inverse legs are most of what qualifies.

### L3 refires on the same symbol (lab, refire chain cooldown 1, ≤ 3 per symbol-day; live paper)

Lab: 1st −0.046R (n 5,150), 2nd −0.035R, 3rd −0.016R — later lots are not worse. Live: 1st +0.205R (n 170), 2nd
+0.220R, 3rd +0.166R, 4th+ +0.208R. Inverse live: 1st −0.73R, 2nd −0.75R, 3rd −0.23R. **Refire/stacking only
multiplied the sign error; it did not create it.** With inverse products excluded the 6 SPXS/SQQQ lots would not
exist at all.

### ST7-FD by entry bar (2-year lab, first fire per symbol-day)

| bucket | n | days | win | avg R | t | total R | avg R w/o best day | worst day |
|---|---|---|---|---|---|---|---|---|
| 10:45 bar (gap leaves RSI-14 window) | 651 | 204 | 0.551 | +0.052 | 0.77 | +33.6 | +0.038 | −26.1 |
| other bars (10:50-13:30) | 289 | 203 | 0.491 | −0.030 | −0.52 | −8.6 | −0.044 | −4.3 |
| source window 13:35-15:00 | 174 | 118 | 0.586 | +0.143 | 1.81 | +24.9 | +0.087 | −2.4 |
| FD as live (all) | 1,114 | 338 | 0.541 | +0.045 | 1.01 | +50.0 | +0.037 | −26.1 |
| FD without the 10:45 bar (re-chained) | 466 | 263 | 0.526 | +0.034 | 0.74 | +15.8 | +0.014 | −4.3 |

By class (all bars): stocks n 1,020 +0.031R; plain ETFs n 57 +0.348R (t 2.8); leveraged n 24 −0.074R; inverse n 13
−0.001R. Live paper by entry time: 10:45-10:48 n 37 +0.055R (+2.0R; −7.53R on 11-19); other n 10 −0.114R; 13:35+ n 11
−0.395R.

## Remedies (targeted; tested per setup across the family)

Configurations tried in this dimension: **6 remedy variants** (A, A', A'', B, C1, C2 below), declared before scoring
except A'/A'' (narrowings of A made after seeing A's long/short split — counted). Family = all 118 enabled lab setups in
any account YAML that the lab frames can run (2 skipped: non-standard geometry); 2-year lab, first fire per
symbol-day, production costs; live = paper trades of every setup in Primary, Testing 1/2, Explore 1, Live Lab,
Graveyard, Gen (26,313 trades, 210 setups, 10-06..11-19). Per-setup tables: `sl_work/remedyA_per_setup.csv`,
`remedyB_per_setup.csv`, `burst_weight_per_setup.csv`, `fam_out.txt`, `fam_out2.txt`.

| # | remedy (where the failure occurs) | 11-19 effect | live family (paper) | 2-year lab family | verdict |
|---|---|---|---|---|---|
| A' | **SHORT setups do not trade market-inverse products** (inverse/levered-inverse ETFs and ETNs, long-VIX). Shorting one is a market-long bet the short thesis never meant. | L3: 0 lots instead of 6 → **+6.49R** | 48 short setups affected: **32 better (+74.4R), 16 worse (−19.8R; largest MF2-FD −3.9R)**, net **+54.6R**; 200 trades, win 39%, −0.27R; w/o the worst day still −38.3R | 60 short setups affected: 31 better (+747R), 29 worse (−219R), net +529R; unseen half 35/24 (+213R), later half 31/28 (+316R) | **Best-supported targeted fix.** Clear live, positive but mixed by count in the lab (the lab cannot apply ETB, and inverse products are always ETB live, so live is the more relevant read). Candidate for the backlog + forward shadow, not a market-hours change. |
| A'' | A' restricted to short setups whose rule reads the overnight gap (the L3/RW gap-fade family, where the gap sign flips) | same as A' for L3 | L3-FD −9.0R, L3-rsi5hi-FD −3.5R, L3-lowdist-FD −2.2R, L3-FD-WB4 −3.0R, L3-rsi5hi-FD-WB5 −2.1R: all 5 L3 variants improve | 14 affected: 7 better (+118R), 7 worse (−47R), net +70R; unseen half 11/3 (+71R); later half 6/8 (−0.6R) | Narrower but not stronger in the lab; A' is preferred (same mechanism in every short). |
| A | Remove inverse products from ALL setups (long and short) | as A' | 110 setups: 58 better / 52 worse, net +34R; long side on inverse is +0.04R live | 113: 70 better / 43 worse, net +3,110R (driven by LD2/CWT14 longs) | Too broad: longs on inverse products are not the failure mode live (+20.7R). Not recommended. |
| B | Skip the RSI gap-exit bar (RSI-14: 10:45; RSI-5: 10:00) for setups whose rule reads that RSI | ST7: −7.53R avoided | not tested live | 36 RSI setups affected: 27 better (+612R) / 9 worse (−137R); **but ST7 −35.6R and ST7Q −62.6R get worse** (their 10:45 fires average +0.05 / +0.19R) | Not a fix for ST7: the 10:45 burst is a correlated bet with a positive lab mean. (Interesting for the short families, where the bar is negative — separate backlog idea.) |
| C1 | Weight every same-setup same-bar burst of k fires at 1/√k ("cap the stacking" proxy) | ST7 −7.53 → −2.85R; L3 unchanged (its 6 lots were on 6 different bars) | not tested live | **115 setups: day-t falls for 102, rises for 13** (median −0.78) | Confirms the owner: blanket stack capping hurts almost every setup. Rejected. |
| C2 | 1/√k only for bursts on the RSI gap-exit bar (the artifact bursts) | ST7 −7.53 → −2.85R | not tested live | 36 affected: 17 t up / 15 down (median 0); **ST7 t 1.01 → 1.37, worst day −7.9 → −2.3 (per average day's risk)**; ST7Q t 2.80 → 2.53 | Neutral across the family, helps ST7 most. Weak candidate; the cleaner fix (untested) is to compute RSI without the overnight change. |

On 11-19, A' plus C2 together would have turned the two setups' −15.2R into about −4.0R (ST7 −2.85 on the
10:45 burst, −1.12 on IWN; L3 0). This is one day and is shown only to tie the remedies to the failure; it is not evidence.

Untested (need a 1-minute rebuild of the frames, after hours): **RSI on intraday changes only** (drop the
prior-close→first-bar change from MCF's RSI windows, or start RSI at the open). That removes the 10:45 / 10:00 jump
at the source for every RSI setup instead of treating its symptoms, and would show whether ST7 has a genuine
"RSI collapse" edge before 13:35. Also untested: counting an inverse ETF's position as the opposite-sign index
exposure in the risk layer (other dimension).


## Rule-change context (research/ledger.jsonl) for the live windows used

- 2026-10-13 per-lot stacking (max 3 lots/symbol, all accounts); 2026-10-14 same-setup re-entry / refire option B
  (L3 refire: true, cooldown 1).
- L3 in Primary: promoted 10-21, demoted 10-22 (to Testing 1), re-promoted 10-30 (effective 10-30). Testing 1 run
  10-12..10-29.
- ST7-FD: Testing 1 10-12..10-25, promoted to Primary 10-25 (effective 10-26); twin group with ST7Q in Testing 1 from 10-22.
- Per-setup daily stop: −2R latched in Testing 1/2 from 10-19/10-22, switched off in Testing 10-23; Primary −2R latched
  from 10-29 (ledger 2026-10-28-primary-setup-daily-stop-2R). Primary position size ~$5k (10-28) → ~$4k (10-28).
- 10-27 lab clock gate GX1 (5-minute completed bucket) — timing fix inside the live window.
- 11-04 Testing 2 top-500 pool (not these setups).
None of these changes touches the symbol universe by product type or the RSI computation, so the two failure modes
were present over the whole live window.

## Caveats (underestimate rather than overestimate)

- Symbol classes come from asset names (assets_meta.csv + data/universe.csv; regex on "Bear/Short/UltraShort/Inverse",
  "2x/3x/Ultra/Bull", VIX). Live tickers missing from both lists (BEZ, MSTZ, BMNZ, SMCZ, BTCZ, PLTD, CORD) are reported
  as "unlisted"; most look like single-stock inverse funds but that is not verified.
- The 2-year lab is survivor-biased (today's symbol list) and cannot apply the live ETB filter; live samples are small
  (inverse 17 trades over 4 days).
- Lab first-per-symbol-day removal of a bar ignores later same-day fires on that symbol (except where re-chained as
  noted), so remedy deltas from removal are approximate.
- Configurations counted below.
