# Track 6: outside research (methods from outside the project, tested on our data)

Educational only — not financial advice.

**Data.**
- Live: all 10 journals (run 1, closed trades), 10-23..11-27. R is LR8 after costs: 28,799 lots, of which Primary has 943 lots and −147.0R, matching the inventory.
- Bench: the 2-year minute-bench candidates (`cand.parquet` from the regsteer_1126 bench build, LIVE-L R after costs), run through a simplified P4 book. The book rules are ≤ 30 lots per setup per day, ≤ 3 lots per symbol per setup, the −2R closed latch, and the −20R halt.
  - It matches the E4 engine closely: CHECK −2.88 vs −3.03 R/day, T2 −1.81 vs −1.80.
  - The locked holdout is asserted absent and was never read.
- Scripts and outputs are in `exploration/sandbox/outside/`. `PREREG.md` was written before any scoring.

**Configs this track: 5** (3 for profit lock, 2 for the equity-curve governor). Before tonight the count was about 9,363. Including the other tracks so far, the cumulative count is about 9,437 or more.

**Rule changes inside the live window (ledger):**
- 10-28: Primary size about $4k
- 10-29: −2R closed latch
- 10-30: testing cost filter
- 11-11: TEAM-6
- 11-12: LR8 costs and account restructure. LR8 is applied to every row here, so the whole window is on one cost basis.
- 11-17: half lots in testing. This changes dollars only, not R.
- 11-19: Epoch 1 and U9-TGT
- 11-20: stop rounding and FOOTRACE-EXIT
- 11-21: cost-basis fix
- 11-23: ST7 out of Primary and BRAKE-BURST
- 11-27: GYH V1+V3, ROT-B3, GEN seed

Next is 11-30: AV50 for NM-ETF plus the Friday-review moves. Testing D/E/F have only 11 sessions, and Explore 1 / Live Lab have 16.

## Headline (numbers first)

1. **The daily profit lock ("stop new entries once the day is up +X", a prop-desk habit) cuts red days, but it adds no R beyond trading less.**
   - At X = 0.25 × daily sd (about +4R on Primary, +2.9R on the bench book):
     - Bench CHECK red days: 168 → 142 of 276 (12.8 → 10.8 a month). A random skip of the same lots gives 166 (p5 159).
     - Bench T2: 244 → 233 of 415. Random gives 248 (p5 243).
     - Live: 99 → 88 of 140 account-days. Random gives 100 (p5 97).
     - The fall in red days shows up in all four bench half-periods (−12, −14, −6, −5).
   - On R the lock is only an exposure cut, or slightly worse than one:
     - The lots it removes average −0.105R vs −0.091R for the base on CHECK (82nd percentile vs a random skip of the same size), and −0.092R vs −0.151R on T2 (7th percentile).
     - So on T2 it removes *better*-than-average lots.
   - Red weeks barely change: CHECK 41 → 39 of 58, T2 66 → 66 of 89.
2. **The equity-curve governor ("trade a setup only while its own last-K-session R is ≥ 0", Komar / practitioner method) fails.**
   - On live data it is worse than random:
     - Kept lots average −0.203R and skipped lots −0.122R (K = 5).
     - The total gain of +1,467R is below every one of 1,000 random skips of the same setup-day count (0th percentile; random mean +2,178R).
   - On the bench it skips 66-76% of lots, and kept vs skipped lots are equal (Welch t −1.2 to +0.9). That puts it at the 17th-83rd percentile of random.
   - This agrees with the metrics track (no ranking metric predicts next week) and with the outside practitioner tests (equity-curve filters mostly lower returns).
3. **Outside evidence on what makes traders consistent points the same way as our own research.**
   - Fewer than 1% of day traders earn reliable profits after fees.
   - What persists is (a) skill shown *before* fees in a large sample and (b) discipline about cutting losers, not day-level P&L rules.
   - Kelly sizing at our measured edge (Primary −0.156R per lot, sd 0.89R) gives f* = μ/σ² = **−0.20**, meaning "do not bet". Fractional Kelly says size in proportion to the proven edge.
   - The intraday P&L pattern that loss-limit rules are built on (losses lead to more risk-taking in the afternoon) assumes a human trader. In our book, morning P&L barely predicts afternoon lots:
     - Live Spearman is +0.17: afternoon lots average −0.128R after a green morning and −0.170R after a red one.
     - Bench Spearman is +0.03 on both splits.
   - Day-level rules therefore have little to work with.

## 1. Outside sources: what they say and whether we already tested it

| Idea from outside | What the source says | Status here |
|---|---|---|
| Daily loss limit / book stop | Standard at prop desks. Coval & Shumway (2005): CBOT traders with morning losses were about 15% more likely to take above-average risk in the afternoon. | Tested before: sw-w4-book-process (book stop −10R/−20R, 0/18), the −20R halt and LATCH-OPEN. Not repeated. |
| Daily **profit** lock / "consistency rule" | Prop firms cap the best day's share of profit: Topstep about 40% of net profit; FTMO 1-Step 50% of positive days' profit. Traders often add a daily profit target. House-money evidence is mixed (Frino et al. 2008). | **New. Tested as idea A.** |
| Equity-curve trading | Practitioner tests (R-bloggers QuantStrat, the Elitetrader simulation, TradingView EMA filter): mostly lower returns. It helps only with positive autocorrelation and low costs. | **New for intraday setups** (the Komar governor was tried only on swing books, cwt-c-c9). **Tested as idea B.** |
| Fractional Kelly | MacLean, Thorp & Ziemba (2010): Kelly maximizes long-run growth but is risky in the short run. Fractional Kelly smooths the path. With a non-positive edge the bet is zero. | Analytic only (0 configs): f* = −0.20 at our edge. It supports "cut exposure until the edge is positive". |
| Volatility-managed sizing | Moreira & Muir (2017): scaling exposure by the inverse of last month's variance raises Sharpe for factor portfolios. | Done tonight by the metrics track (RISK-BUDGET): it loses to an exposure-matched cut. Not repeated. |
| Trader skill persistence | Barber, Lee, Liu & Odean (2014): top-ranked day traders keep earning (37.9 bps a day after fees), but fewer than 1% do so reliably. | Our setup ranks do not persist week to week (metrics track). Rule: promote on a large before-cost sample, not on short live streaks. |
| Discipline / disposition | Locke & Mann (2005): the more successful floor traders hold losers for a shorter time; relative discipline predicts later success. Garvey & Murphy (2004): professionals also hold losers too long. | Our exits are mechanical (stop at −1R, −2R latch); stop-widening and holding were tested broadly (about 22,000 giveback configs). Nothing new to test. |

## 2. Idea A: daily profit lock

Rule: per account and day, once **closed** R for the day reaches +X, no new entries are taken for the rest of the day. Open lots run to their normal exits. X = k × daily sd, with k ∈ {0.25, 0.5, 1.0}. Live uses an expanding sd from the account's previous days (at least 5); the bench uses the FIT-period sd (11.65R).

### Bench (simplified P4 book, LIVE-L)

| k (X) | Period | Locked days | Lots cut | dR/day (t) | Removed avg R vs base | vs random skip (R) | Red days base → lock (random p5) | Worst-5 (base / lock / constant cut) | dR w/o best day, best-day share |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 (2.9R) | CHECK | 113 / 276 | 28% | +0.93 (2.17) | −0.105 vs −0.091 | 82nd pct | 168 → **142** (159) | −183.6 / −180.9 / −132.3 | +0.77, 17% |
| 0.25 | T2 | 62 / 415 | 9% | +0.10 (1.33) | −0.092 vs −0.151 | 7th pct | 244 → **233** (243) | −122.3 / −122.3 / −111.4 | +0.06, 37% |
| 0.5 (5.8R) | CHECK | 57 | 13% | +0.28 (0.83) | −0.067 vs −0.091 | 16th pct | 168 → 157 (162) | −183.6 / −180.9 / −159.3 | +0.12, 56% |
| 0.5 | T2 | 21 | 3% | +0.02 (0.61) | −0.053 vs −0.151 | 10th pct | 244 → 242 (242) | flat | 0.00, 92% |
| 1.0 (11.7R) | CHECK / T2 | 19 / 1 | 4% / 0% | −0.06 / 0.00 | +0.053 / — | 0th / 52nd | 168 → 167 / flat | flat | — |

Half-periods for k = 0.25 (`lock_halves_out.txt`):
- Red days fall in each half: CHECK H1 91 → 79 and H2 77 → 63; T2 H1 126 → 120 and H2 118 → 113.
- dR/day t is 1.21, 1.82, 0.99 and 0.90 for those four halves.
- Removed lots are better than the base in 3 of 4 halves.

### Live (10 accounts, account-days as units)

| k | Lots cut | dR total | Removed avg R vs all | Date-clustered t | vs random (R) | Red account-days (eligible 140) base → lock (random p5) | Primary |
|---|---|---|---|---|---|---|---|
| 0.25 | 3,198 (11%) | +534R | −0.167 vs −0.165 | 1.70 | 13th pct | 99 → **88** (97) | +79.3R, red 17 → 13, 9 locked days |
| 0.5 | 1,383 (5%) | +32R | −0.023 vs −0.165 | 0.37 | 0th pct | 99 → 98 (97) | +50.4R |
| 1.0 | 961 (3%) | +71R | −0.074 | 1.36 | 0th pct | 132 → 132 (all days) | −2.7R |

- At k = 0.25, 9 accounts do better and 1 does worse (Explore 1, −51R).
- **The Primary gain is carried by two days.** 11-10 contributed +41.9R and 11-06 +29.8R. Those are 90% of the +79R (`1 day` share at 53% for 11-10 alone).
- On Primary the removed lots average −0.378R vs −0.156R, but the bench shows no such edge.
- The same-day random control (100th percentile) is biased, because locked days are selected for their good early lots. It is not used as evidence.

**Reading.** The lock is a **red-day lever, not an R lever.**
- It turns "green early, then drifting" days into small green days. That cuts red days by about 2 a month on CHECK and about 0.5 a month on T2, beyond what a random cut of the same size does.
- Its R effect is the size of the exposure cut or a little worse, and it leaves worst-5 and red weeks untouched, because it only fires on good days.
- With a negative per-lot edge it does *not* fix the weekly result. It only changes how the red days are spread.

## 3. Idea B: setup equity-curve governor

Rule: setup s trades on day d only if the sum of its R over its last K sessions (walk-forward, using shadow results) is ≥ 0. K ∈ {5, 10}. On live data there are 177 setups with at least 20 deduped trades. On the bench, the 8 cand setups run as raw candidates (≤ 30 lots a day, ≤ 3 per symbol).

| Set | K | Setup-days eligible / skipped | Lots skipped | Kept R/lot | Skipped R/lot | Welch t (kept − skipped) | dR total | vs random skip | Setups better / worse |
|---|---|---|---|---|---|---|---|---|---|
| live | 5 | 1,211 / 808 | 68% | −0.203 | −0.122 | +0.05 | +1,467R | **0th pct** (random +2,178) | 81 / 55 |
| live | 10 | 585 / 438 | 76% | −0.312 | −0.127 | −1.38 | +989R | **0th pct** (random +1,307) | 54 / 20 |
| bench CHECK | 5 | 1,188 / 756 | 66% | −0.087 | −0.100 | +0.72 | +1,026R | 61st | 8 / 0 |
| bench CHECK | 10 | 1,148 / 786 | 69% | −0.105 | −0.087 | −1.16 | +911R | 17th | 6 / 2 |
| bench T2 | 5 | 1,197 / 814 | 68% | −0.128 | −0.144 | +0.91 | +613R | 59th | 5 / 0 |
| bench T2 | 10 | 1,172 / 882 | 76% | −0.095 | −0.152 | −0.55 | +698R | 83rd | 4 / 1 |

**Reading.**
- The "gain" is entirely the size cut: the governor skips two-thirds or more of the lots on a book whose lots all lose.
- On live data it picks *worse* than random, so recent live R is anti-informative at the setup level.
- **Fail on every split.** Do not use own-equity-curve gating for rotation or benching decisions. It confirms the metrics-track finding that rank does not persist.

## 4. Confidence

- **Idea A red-day effect: medium.**
  - It is below the random-control p5 on bench CHECK, bench T2 and live, and in all 4 bench halves.
  - The mechanism is simple and does not depend on the edge.
  - Two limits: the bench book is simplified (no LATCH-OPEN, no burst brake, closed R only), and the live window is short (25 sessions, 140 eligible account-days).
- **Idea A R effect: high confidence that there is none beyond exposure** (7th-82nd percentile vs random; removed lots are not worse than average).
- **Idea B: high confidence it fails.** It is at the 0th percentile live, kept and skipped lots are equal on the bench, and outside tests agree.

## 5. Proposal candidates

### P1. PROFIT-LOCK shadow (log-only, all accounts): CAN START Monday 11-30 without touching any rule
- **What:** a nightly computation from the journals, run with no live change.
  - Per account and day, mark the first entry after closed day R ≥ +0.25 × that account's expanding daily sd. Primary is about +4.3R today.
  - Record the R of the lots after the mark ("lock-skipped").
  - Report red days with and without the lock, plus a 500-draw random-skip control of the same lot count.
- **Expected effect on weekly R:** about 0, within ±3R a week on Primary. The bench gives +0.9 R/day on CHECK and +0.1 on T2, which is the size of the exposure cut; live Primary's +79R comes from 2 days and should not be expected.
- **Expected effect on red days:** about −2 a month on a Primary-like book (CHECK). The range is −0.5 (T2) to −3 (live).
- **Risk:** none while it is a shadow. If adopted later, it gives up the right tail of strong days (lots after the lock are no worse than average) and can cost R on trend days.
- **Experiment:** baseline = the actual journals; duration = 20 sessions (to about 12-28). Success needs all of:
  - (a) lock red days below the random-skip p5 on Primary and on the pooled accounts;
  - (b) lock dR ≥ the random mean (no worse than an equal cut);
  - (c) not carried by 1-2 days (best-day share < 50%).
- Only after that, and only if the owner wants the green-day count as a goal in itself, propose a live test in one testing account (Testing D or E, k = 0.25, 20 sessions, against that account's own shadow baseline).

### P2. Retire "own recent results" as a gating signal (process rule; it can apply Monday as review guidance)
- **What:** in Friday reviews and rotation, do not bench or switch off a setup because of its last 5-10 sessions alone. Use exposure-matched controls and before-cost samples, in line with Barber et al. and our metrics track.
- **Expected effect on weekly R:** 0R direct. It avoids decisions that, live, picked worse than random (kept −0.203 vs skipped −0.122 R/lot).
- **Risk:** low.
- **Experiment:** none needed; it is a review rule. Re-check after 20 sessions with the governor table re-run (`governor.py`).

### P3. Kelly framing for sizing: support the exposure cut, do not size up (decision aid for the 11-30 review)
- At the measured edge (−0.156R per lot, sd 0.89R), Kelly f* = −0.20, so the growth-optimal size is the minimum.
- Fractional Kelly is the standard outside answer: size ∝ proven edge.
- Concretely, size stays at the minimum (half lots, as in testing) until a setup's day-clustered t, net of costs, is ≥ 2 over at least 20 sessions. This is consistent with the declined size-up tests (SZ-PROOF lost 33-47R).
- **Expected effect on weekly R:** less loss in proportion to the size cut, e.g. half size gives half the loss. **Risk:** slower to profit if an edge appears.
- **Can start Monday:** as a review rule, yes. It changes no Primary rule unless the owner chooses to.

## Sources
- Coval, J. & Shumway, T. (2005), "Do Behavioral Biases Affect Prices?", *Journal of Finance* 60(1): https://ideas.repec.org/a/bla/jfinan/v60y2005i1p1-34.html ; summary: https://rpc.cfainstitute.org/en/research/cfa-digest/2005/11/do-behavioral-biases-affect-prices-digest-summary
- Barber, Lee, Liu & Odean (2014), "The cross-section of speculator skill: Evidence from day trading", *Journal of Financial Markets* 18: https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html ; full text: https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf
- Locke, P. & Mann, S. (2005), "Professional trader discipline and trade disposition", *Journal of Financial Economics* 76(2): https://ideas.repec.org/a/eee/jfinec/v76y2005i2p401-444.html
- Garvey, R. & Murphy, A. (2004), "Are Professional Traders Too Slow to Realize Their Losses?", *Financial Analysts Journal* 60(4): https://ideas.repec.org/a/taf/ufajxx/v60y2004i4p35-43.html
- MacLean, Thorp & Ziemba (2010), "Good and bad properties of the Kelly criterion": https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf
- Moreira, A. & Muir, T. (2017), "Volatility-Managed Portfolios", *Journal of Finance* 72(4): https://www.nber.org/papers/w22208
- Topstep consistency rule (official help centre): https://intercom.help/topstep-llc/en/articles/8284208-consistency-at-topstep ; overview of firm rules: https://tradetanto.com/learn/prop-firm-consistency
- Equity-curve trading practitioner tests: https://www.r-bloggers.com/2014/10/structural-arbitrage-trading-the-equity-curve/ ; https://www.elitetrader.com/et/threads/trading-the-equity-curve-doesnt-seem-to-work.295776 ; https://in.tradingview.com/script/QLDOWdxE-Equity-Curve-Trading-with-EMA

Educational only — not financial advice.
