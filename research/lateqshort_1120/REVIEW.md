Educational only — not financial advice

**Plain summary (5 lines)**
1. No rule change caused the hot streak. The setup's code and settings have not changed since 10-28 (module last committed 10-28; the Testing D block is a straight copy of the Gen block).
2. The streak is really the 4 Testing D sessions, 11-16 to 11-19 (+18.2R, 97 trades). 11-05 in Gen was a small win (+3.2R on 6 trades), but 11-13 in Gen lost −6.5R on 37 trades, so the run is not unbroken "since 11/5".
3. About 76% of trades are never stopped or targeted. They are closed at the 15:55 flatten, so the result is mostly "did the market keep falling between entry and 15:55?" On all 4 Testing D days QQQ kept falling into the close. On the Gen days it mostly bounced.
4. On the Testing D days, the whole signal-level gain (+0.158R gross per signal) equals the estimated market component (+0.158R). What is left over is +0.001R. The setup did no better than the index drop it rode.
5. Verdict: mostly regime (afternoon sell-offs). The 0.15R cost filter Testing D applies adds a real but small rule effect (~+0.04 to +0.05R per trade). The move did not change which signals got taken in any way that matters. Keep it, but expect it to give the gains back on days when QQQ is down at 14:00 and then bounces.

---

### 1. Record (LR8 cost-R from journal pnl_adj; matches live_trades.pkl)

| Account | Session | n | R | avg | Exit mix (target / stop / flatten) | QQQ move, entry to 15:54 |
|---|---|---|---|---|---|---|
| Gen | 10-29 | 25 | −5.62 | −0.225 | 16 / 20 / 64% | +0.24% |
| Gen | 10-30 | 6 | −1.74 | −0.290 | 17 / 50 / 33% | +0.72% |
| Gen | 11-02 | 11 | −0.90 | −0.082 | 18 / 27 / 55% | −0.57% (shorted names rose anyway) |
| Gen | 11-05 | 6 | +3.24 | +0.541 | 50 / 0 / 50% | SPY −0.52% from 14:00 (no QQQ data) |
| Gen | 11-13 | 37 | −6.50 | −0.176 | 8 / 8 / 84% | +0.19% |
| Testing D | 11-16 | 50 | +9.30 | +0.186 | 6 / 2 / 92% | −0.36% |
| Testing D | 11-17 | 9 | +3.02 | +0.335 | 22 / 0 / 78% | −0.21% |
| Testing D | 11-18 | 15 | +2.07 | +0.138 | 20 / 7 / 73% | +0.16% (QQQ −0.23% from 14:00) |
| Testing D | 11-19 | 23 | +3.78 | +0.165 | 22 / 4 / 74% | −0.44% |

11-20 is still open: 32 entries so far, QQQ −3.3% at 14:15, another big down day.

By week:
- W44: Gen 31 trades, −7.37R.
- W45: Gen 17 trades, +2.34R.
- W46: Gen 37 trades, −6.50R.
- W47: Testing D 97 trades, +18.18R.

Summary stats by account:

| | Gen | Testing D |
|---|---|---|
| Trades / days | 85 / 5 | 97 / 4 |
| Total R | −11.53 | +18.18 |
| Avg R | −0.136 | +0.187 |
| Avg R w/o best day | −0.187 | +0.189 |
| Avg R w/o top 2 days | −0.204 | +0.212 |
| Best-day share | n/a (net loss) | 51% (11-16): earns the `1 day` tag, just over the 50% line |
| Day-clustered t | −2.31 | 11.3 |

The Testing D t of 11.3 means nothing with only 4 clusters; the t on day means is 4.67 with 3 degrees of freedom. All 182 trades together: avg +0.037, w/o best day −0.02, day-clustered t 0.48.

When the streak started: the first winning day was 11-05 (Gen), but 11-13 (Gen) lost. The streak as a run is 11-16 to 11-19, the first 4 sessions after the move to Testing D.

### 2. Changes that touched it, and whether each explains the swing

- **Move Gen → Testing D (ROT1, ledger 2026-11-16-rot1-arena-block1, effective session 11-16).** A rebalance move with its own rules unchanged. Signal quality did not change.
  - Gross average over all signals (taken plus not taken, from the what-if run): Gen days −0.256, −0.379, −0.290, +0.155, −0.123; Testing D days +0.177, +0.212, +0.024, +0.155.
  - The improvement is the same with or without the account's filters, so the account did not create it.
- **Capacity in Gen did not cause the Gen losses.**
  - Gen's not-taken signals averaged −0.19R gross, against −0.105 for the trades it took.
  - On 11-05 the halt blocked 14 signals averaging −0.17, so the halt helped. The 3 buying-power rejects averaged +0.50 (+1.5R missed in total).
  - Gen's per-setup cap (48, then 150 from 11-12) never bound for this setup.
- **Testing D cap.** The cap of 50 bound on 11-16: 100 signals were skipped as "max positions". They averaged +0.215 gross, the same as the trades taken, so the cap did not pick better trades. The cap rose to 100 under TSZ1 on 11-17.
- **Cost filter, 0.15R (Testing only; Gen has none).** This is a real effect, but small.
  - In Testing D it skipped 25 signals with ≈0 gross R (−0.21R total) and an estimated stop-exit cost of 6.6R, so it avoided roughly −3.5 to −6.8R net.
  - Applying the same formula (runner.py) to Gen's trades: 32 of 85 would have been filtered (−6.59R, avg −0.206). Gen would then have been −0.093 instead of −0.136.
  - So it is worth about +0.04 to +0.05R per trade in either account. It explains about 15% of the swing from −0.136 to +0.187.
- **Sizing.**
  - Gen REPV-1 (11-12) cut lots to about $520. Cost per trade rose to 0.041R on 11-13, against 0.022–0.035 before.
  - TSZ1 (11-17) put Testing D on half-size lots (about $485). Cost was 0.02–0.03R per trade.
  - R per trade is size-independent. Effect ≤0.02R.
- **LR8 cost model (11-12).** live_trades.pkl keeps the flat basis before 11-12; restating with LR8 lowers those Gen trades by about 0.04R. It makes Gen look slightly worse, so it does not explain the streak.
- **Changes with no effect on this setup:**
  - LR1, LR3, LR4, LR5: LR3 is Primary only; the others are not relevant.
  - ROT2 and C3-ROT (11-19): never benched, because it is a rare / day-gated setup.
  - GY-BENCH: did not touch it.
  - SPYEXIT: only on the WB4 copies.
  - U9-TGT (11-19): a few skips at most.
  - Stop rounding (11-20) and BRAKE-BURST (11-23): after the window.
  - Universe: full universe and ADV ≥ $20M in both accounts.
  - EXPO1109 temporary moves: did not include it.

Rule-change context for these figures: LR8 costs from 11-12, Gen REPV-1 sizing 11-12, the move to Testing D 11-16 (where the cost filter applies), TSZ1 half-size 11-17, U9-TGT 11-19. None of them changed the entry or exit logic.

### 3. Market regime

- **Qualifying days (QQQ < −0.3% since open, 14:00–15:00).**
  - Before 11-05: 3 of 5 sessions (10-29, 10-30, 11-02).
  - 11-05: qualified.
  - 11-06 to 11-12: none of 5 sessions, all UP days on Compass.
  - 11-13 to 11-20: 6 of 6.
  - Long-run rate: 42% of days (457 days, 2024-09 to 2026-11-04, with 2024-11-01..2025-02-28 excluded).
- **What QQQ does after 14:00 on qualifying days.** Historically it drifts only −0.066% to 15:55 and falls 55% of the time.
  - In Testing D's window it fell from 14:00 on 4 of 4 days (about 9% odds at 55% each), by about −0.2% to −0.4%.
  - In Gen's window it rallied on 10-29 (+0.25%), 10-30 (+0.57%) and 11-13 (+0.23%).
  - The correlation of the day's signal average with QQQ's move from entry to 15:54 is −0.54.
- **Trade level (431 signals, beta-1 market component = −QQQ move / stop distance as % of price).**
  - Slope 0.56.
  - Testing D: gross +0.158 against a market component of +0.158. Left over: +0.001.
  - Gen: gross −0.207 against a market component of −0.097. Left over: −0.11, almost all from 11-02.
  - Left over across all days: +0.002 (t 0.04). There is no stock-picking edge beyond the index move.
- **Compass.**
  - Testing D days: 11-13 leaning down / MIXED, 11-18 mixed / MIXED, 11-19 and 11-20 DOWN-confirmed. Rows for 11-16 and 11-17 are missing from the Compass csv; polls show QQQ −1.0% / −1.4% at 14:00.
  - The gate1 study found the Compass state at 10:00 does not separate results (DOWN train +0.008 / valid +0.06; MIXED +0.042 / −0.014; UP −0.099 on n=17).

### 4. Random-entry null and history

- **Random-entry null** (research/whatworks_1120/null/null_results.csv; n=170, LR8 basis, live avg +0.028):
  - ±30-minute null mean −0.070. Live edge +0.097, day-clustered p 0.0002.
  - It still beats this null without its best day (edge +0.095).
  - Random later entries (+1 to +30 min) do as well: post-null mean +0.064, clustered p 0.75.
  - So it picks the right stock-day and avoids shorting too early. The exact minute adds nothing. That fits a "short weak names into a falling close" bet.
- **Generator screen** (173 days):
  - Train +0.047 (t 0.43), valid +0.052 (t 0.96), all +0.049 (t 0.73).
  - By session type: up sessions −0.238, down sessions +0.125, flat −0.061.
  - Excess over a same-minute random baseline: only +0.008 train / +0.036 valid.
- **2-year regime table** (research/bdi/regx): Bear days +0.121 / +0.090 against Choppy −0.202 / −0.025. Verdict "weak" (TRAIN t 1.67, VALID t 0.99), and the split is by hindsight day type.

### 5. Verdict and what to watch

The streak is mostly regime, partly luck in sequencing, with one small rule contribution.
- **Regime:** four afternoons in a row where QQQ kept falling into the close. Every bit of Testing D's gain is explained by that index move.
- **Small rule help:** Testing D's 0.15R cost filter (about +0.04 to +0.05R per trade). It is worth keeping.
- **No help:** the move to Testing D, capacity, sizing and LR changes.

Expect the setup to be roughly flat to slightly positive over many qualifying days, as the screen suggests (+0.05R), and strongly negative on days when the market is down at 14:00 and then bounces (like 10-29, 10-30, 11-13).

To protect and watch:
- Keep the cost filter.
- Do not promote on these 4 days: one regime, a best-day share of 51%, only 9 active days, and not yet at C3-BAR2's 15 days.
- Watch its R on qualifying days split by whether QQQ falls or rises after 14:00. If the left-over after the market move stays near 0, it is an index-direction bet rather than a setup edge. Possible backlog idea: a late-day QQQ-bounce exit, tested with costs in on 2-year data.

Working files are in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/lq/ (trades2.pkl, qqq_days.pkl, poll_series.pkl, a1.py to a5.py). Nothing was changed or committed in the repo.
