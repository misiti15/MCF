Educational only — not financial advice

# BDI primary1029: what went wrong in Primary on 2026-10-29, and what can be done about it

*Live numbers are **paper** trades (rule 7) from Primary's journal (origin/mcf-data `journal.db`, run 1, pulled after the
close: after the close; last journal commit 2026-10-29 19:57 UTC "EOD report"; the 15:04 numbers in the order are unchanged, as no trade opened after DEO). Two-year numbers are **backtests** on the open history (train <= 2025-12-31, valid
2026-01-01..2026-10-07), with costs in. **Configurations tried: 64 in this study (5 rounds, of which 25 are uniform controls) plus 4 prior related
(p3_1029 B1-B4), so N = 68 and the bar is t >= 2.91** (`counts.json`). Grids were fixed in `PLAN.md` (plus 4 amendments) before
each round was scored. **Disclosure: the lead's limit was 4 rounds. Round 5 (breadth) was added after the close data
showed an up session. It is counted, and it failed.** **One locked-block look** was taken, for the one finalist that beat the parent on train and valid
(R2b, section 5). Nothing in config/, mcf/, the setups, exits, docs/live or the ledger was changed. Nothing was
committed. Replays were not used as evidence.*

## Failures first
1. **No rule passes.** No rule cuts down days while keeping total R and avg R, in all 57 configurations. On two
   years, every stacking rule (risk-sharing at 1/k, later lots at half size, profit-gated stacking, one lot per family per
   symbol) does exactly what shrinking **every** trade by the same amount does. It cuts variance and P/L together. Live,
   the stacked lots were Primary's best trades (lot 2-3: +0.79R per trade, mostly 10-22). Risk-sharing would have cost
   about 25% of live P/L to save 2.2R on 10-29.
2. **The one rule that looked free fails its out-of-sample checks.** That is the short-family brake: after 3 family
   stops, the rest of the family trades at half size. On two years it beats a uniform shrink only in valid, not in train.
   Its 2-stop sibling **failed** its one locked-block look against the uniform shrink (t -0.86). In the other four
   accounts (~9.7k live trades), shorts taken after 3 short stops are **not** worse than other shorts. So there is no
   evidence that losses persist within a day for this book.
3. **The autopsy's leads fail.**
   - "Don't short a gap-down name that has climbed back above its open" (NTSK): on two years those shorts are no worse
     than the rest (R4a-d).
   - "Halve the shorts when the universe is trading up" (breadth_open >= 0.55-0.65 at entry, R5a-d) is no better than a
     uniform shrink on the worst days (t -0.19..-0.88).
4. **The root cause stays.** Primary's short family loses -0.069R per trade on two years after costs (p3_1029). Its
   live record is +84R, and 89% of that is 10-22. 10-29 is what this book does about once every 40 sessions in the
   backtest.

## 1. What happened (`autopsy.py` → `autopsy_out.txt`, `trades_today.csv`)
**Final:** 16 trades (12 short, 4 long), 3 winners. **-11.30R after costs, -$411.08** (-$385.14 before the
fill-realism adjustment). Shorts -9.81R / -$353. Longs -1.50R / -$58. Average -0.71R per trade.
- **Timeline:**
  - 10:40-10:50: three single shorts (GMAB, U) and the ST7 long CSX. All were stopped by 11:28, as IWM ran to +1.0% at
    11:34.
  - 11:20-12:00: WDAY was shorted three times. IOVA was shorted twice and both took their targets.
  - 13:00: NTSK was shorted three times on one bar. DEO was shorted the same minute.
  - 13:10: IOVA was re-shorted.
  - 13:59: RW5 tripped ST-P (-2.27R).
  - 14:30: all three NTSK lots were stopped, and MF4 tripped ST-P (-2.86R).
  - 15:04: DEO was stopped.

**Cause by cause.** Each trade is counted once.

| cause | trades | R | $ |
|---|---|---|---|
| 1 extra lots stacked on a losing name (WDAY lots 2-3 RW5/MF4, NTSK lots 2-3 MF4/RW3) | 4 | -4.48 | -206.47 |
| 2 late re-entry after the move had paid (IOVA RW5 13:10) | 1 | -1.10 | -104.50 |
| 3 single-lot short losers (GMAB, U, DEO, WDAY RW3, NTSK RW5) | 5 | -5.58 | -178.94 |
| 4 long setups (CSX ST7 -1.25, HPE NS1 -1.03, LYV +0.43, VG +0.36) | 4 | -1.49 | -57.79 |
| 5 short winners (IOVA MF4 +0.45, IOVA RW3 lot 2 +0.91) | 2 | +1.36 | +136.62 |
| **total** | 16 | **-11.30** | **-411.08** |
| *cuts across the rows:* execution (stop fills beyond the stop 0.85R + fill-realism cost 0.60R) | | *-1.45* | *-26* |
| *cuts across the rows:* concentration, i.e. the clusters WDAY + NTSK + IOVA RW5 = 7 trades | | *-7.77* | *-407* |

The rows add up. In $, NTSK x3 plus the IOVA re-entry are $295 of the $411. Those names carried 1.5-2.4% stops, and
with a fixed ~$4k slot that means 2-3× the $ risk of a WDAY lot.

**Notes on the causes:**
- **Same-bar triple, NTSK 13:00.** RW5-FD, MF4-FD and RW3-FD all fired on the 12:55 bar at the same price and the same
  stop. That is one bet taken three times: 3.27R, $191. NTSK was +3.3% above its open when it was shorted and closed
  +4.5%. Twin protection covers only X / X-FD pairs, so it did not apply.
- **WDAY, three shorts in 40 minutes (11:20 / 11:55 / 12:00).**
  - The second and third lots were added while the first was flat to underwater (-0.11R and +0.07R at their entries).
  - None of them got more than 0.47R in its favour.
  - All were stopped 12:18-12:25 as WDAY bounced from -1.8% to -0.9% on the day.
- **IOVA re-entry, RW5-FD 13:10.**
  - IOVA was -11% on the day. MF4-FD and RW3-FD had already taken their targets at 12:06 and 12:19.
  - RW5 shorted 0.2 ATR above the day's low, with a 2.4% stop. That is the widest stop of the day in percentage
    terms, so it carried the largest $ risk ($95).
  - It went 0.81R in favour, then was stopped: -1.10R, -$104.50, the single largest $ loss of the day.
- **Single-lot shorts** (GMAB, U, DEO and the first lots on WDAY and NTSK): a normal losing run.
  - 5 of these 5 were stopped. GMAB reached its target after it was stopped out (the stop was hit at 11:19, and the
    stock then fell 1.3R below the entry).
- **Losers that never worked:** 8 of the 13 got less than 0.5R in their favour. Only U (1.03R), IOVA RW5 (0.81R) and
  DEO (0.59R) went well in favour first.
- **The entries were not bad fills:**
  - Median latency from signal to fill was ~25 s.
  - The entry vs the signal's reference price was ~0R in total.
  - Median spread was ~10 bps, about 0.1 of the stop distance.
  - Stop fills beyond the stop came to 0.85R in total, and the fill-realism cost to 0.6R.
  - Execution was about 1.4R of the -11.3R. The rest is direction.

## 2. Market context (`regime_today.py`, SIP bars)
- **The session was an up day for stocks, not for the index.**
  - The universe's median open-to-close was **+0.48%**, and 68% of 1,222 names were up. By the history's own tercile
    rule (+0.21% cut point) that is an **"up" session**.
  - Over the same session QQQ was -0.49%, SPY -0.13% and IWM +0.28% (IWM was +1.0% at 11:34).
- **Why that matters:** on two years, with ST-P on, Primary's shorts make **-0.22R per trade in up sessions**, against
  +0.065R in down sessions.
- **So the main driver was not bad entries.** It was a short book on a broad up day, while the tech index (the usual
  thing people watch) looked weak.
- **This is not a squeeze day in the index sense, and it was not visible in time.** Universe breadth at entry
  (`breadth_open`) does not flag these days early enough to help (R5).

## 3. ST-P, the -2R per-setup latch, live from today (`stp_whatif.py`)
- **It fired as designed, twice:**
  - RW5-FD at 13:59, at -2.27R (WDAY -1.17, IOVA -1.10).
  - MF4-FD at 14:30, at -2.86R (GMAB -1.09, IOVA +0.45, WDAY -1.14, NTSK -1.08).
- It blocked 4 signals. Priced on SIP 1-min bars with production costs:
  - SPG MF4 14:35: stopped, -1.10R.
  - FUTU RW5 14:50: stopped, -1.06R.
  - JETS MF4 15:00: +0.26R.
  - UNP MF4 15:00: -0.51R.
- **ST-P saved about 2.4R (about $60).** Without it the day was about -13.7R.
- It could not have done more. Both latches tripped after the damage, and the NTSK lots of RW5 were entered at 13:00,
  before RW5's latch.
- On two years, ST-P is the one tested rule with real value. R per unit risk goes from -0.070 to -0.059 and CVaR5 from
  -52.7 to -39.4.

## 4. Position size
- Every lot was slot-capped at about $3,970 of notional. The 0.25%-of-equity risk cap (~$239) never binds, so a
  trade's $ risk = $4k × stop%. That ranged from $13 (DEO) to $97 (IOVA).
- **In R the day is the same at any size:** -11.3R.
- At the pre-10-28 sizing (160 slots, ~$1,914 per slot) the same trades would have lost about **-$198 instead of -$411**.
- The bigger slots doubled the $ swing, both ways. 10-28's +$246 was also about twice what it would have been.

## 5. Remedy research (`sim.py`, `eval.py` → `results_r1..r4.csv`; live replays `live_rules.py`, `live_wide.py`, `other_accts.py`)
**Engine:**
- The p3_1029 portfolio sim of Primary's 8 setups on two years, matched to p3's parent (n 29,285, -0.070R).
- From round 2 on, ST-P is modelled as the base, because it is live.
- The fairness test for a size rule is its **uniform control U**: every trade shrunk by the rule's average weight.
  Without that control, any cut looks good on a book that loses.

### Two years: base = ST-P on (24,754 trades, -0.059R per trade, total -1,467R, CVaR5 -39.4R/day, max DD 1,704R, 262 red days of 426)

| config | R per unit risk (train / valid) | total R | CVaR5 | max DD | red days | vs uniform shrink: train t / valid t |
|---|---|---|---|---|---|---|
| base ST-P | -0.083 / -0.037 | -1,467 | -39.4 | 1,704 | 262 | |
| poll-split (same-bar lots share 1R) | -0.081 / -0.038 | -1,204 | -34.8 | 1,394 | 263 | +0.53 / -0.30 |
| fam >= 2 stops → half | -0.080 / -0.022 | -907 | -26.0 | 1,131 | 265 | +0.30 / +2.08 |
| **fam >= 3 stops → half** | -0.085 / -0.024 | -1,025 | -29.1 | 1,273 | 268 | -0.36 / +2.01 |
| fam >= 4 stops → half | -0.087 / -0.028 | -1,141 | -31.6 | 1,387 | 267 | -0.84 / +1.44 |
| family net R <= -2 / -3 / -4 → half | -0.084..-0.087 / -0.034..-0.035 | -1,319..-1,403 | -36.2..-37.6 | 1,524-1,620 | 269-274 | -0.19..-1.28 / +0.63..+1.04 |
| account stops >= 3 → half | -0.086 / -0.026 | -1,009 | -27.6 | 1,236 | 271 | -0.58 / +1.59 |
| gap-down short above open → half | -0.085 / -0.040 | -1,322 | -35.2 | 1,447 | 266 | -0.02 / -1.06 |
| breadth_open >= 0.55 / 0.60 / 0.65 → shorts half | -0.082..-0.089 / -0.032..-0.035 | -1,164..-1,382 | -37.3..-38.3 | 1,355-1,585 | 261-266 | +0.63..-0.72 / +0.29..+0.79 (worst days -0.88..-0.19) |

**Round 1** (no ST-P in the base, `results_r1.csv`):
- W1-W6 stacking size rules: each within ±1R/day of its uniform control.
- B5 one family lot per symbol per day, and B6 later lot only if the first is >= +0.25R: R per unit risk -0.069 / -0.070,
  vs the parent's -0.070.
- B7 no re-entry within 60 min of a target: +0.01R/day, t 0.24. Train re-entries after a target are *better* than
  average.
- D1 block a symbol after 2 stops: -0.01R/day.
- **D0 ST-P alone** is the one rule with real value: R per unit risk -0.070 → -0.059, CVaR5 -52.7 → -39.4, max DD
  -23%.

**Locked block** (2024-11-01..2025-02-28, one look, `holdout_out.txt`). The finalist was R2b, fam >= 2 → half, the
only config that beat the base on both train and valid:

| | total R | R per unit risk | worst day | CVaR5 | red days | max DD |
|---|---|---|---|---|---|---|
| base ST-P | -519 | -0.130 | -56.0 | -42.7 | 57 | 540 |
| R2b fam >= 2 → half | -394 | -0.139 | -33.2 | -27.9 | 59 | 412 |
| uniform shrink (0.71) | -369 | -0.130 | -39.7 | -30.3 | 57 | 383 |

- R2b vs the uniform shrink: -0.32R/day, t -0.86. **FAIL.** It cuts the worst days (+5.0R/day on the base's worst 5%)
  but costs R elsewhere.

### Live paper replays, current-8 trades 10-08..10-29 (245 trades, 16 sessions)
| rule | trades | total R | $ | 10-29 R ($) | 10-22 R | red days | max DD R | R w/o best day |
|---|---|---|---|---|---|---|---|---|
| as traded | 245 | +84.0 | +1,568 | -11.3 (-411) | +74.7 | 5 | 11.3 | +9.3 |
| poll-split 1/k | 245 | +63.2 | +1,423 | -9.1 (-284) | +57.2 | 5 | 9.1 | +6.0 |
| later lots half | 245 | +65.4 | +1,318 | -9.5 (-353) | +57.6 | 5 | 9.5 | +7.8 |
| harmonic 1/lot | 245 | +63.4 | +1,301 | -9.1 (-336) | +55.2 | 5 | 9.1 | +8.2 |
| fam >= 2 stops half | 245 | +44.5 | +981 | -7.8 (-263) | +41.2 | 6 | 7.8 | +3.4 |
| **fam >= 3 stops half** | 245 | **+85.8** | **+1,728** | **-8.5 (-257)** | +76.4 | 5 | **8.5** | +9.4 |
| fam >= 4 stops half | 245 | +89.2 | +1,764 | -8.5 (-257) | +77.1 | 5 | 8.5 | +12.0 |
| account >= 3 stops half | 245 | +87.6 | +1,743 | -7.8 (-263) | +76.4 | 5 | 7.8 | +11.2 |
| shorts stop x2.5, same $ (p1_1029 backlog) | 245 | +40.3 | +752 | -6.4 (-228) | +31.8 | 4 | 6.4 | +8.4 |

**How to read the table:**
- The stacking rules and the wide stop cut the bad day and the good day by the same share. 10-22's stacked lots were
  the live edge.
- The fam >= 3 brake touched only 29 trades (12%; avg -0.12R vs +0.47R for the rest of the family). It left 10-22
  intact, because 10-22's family stops came late. That is a property of 16 sessions, not a proven pattern (section 5,
  other accounts).

### Other accounts, live paper (`other_accts.py`): shorts after >= 3 short stops vs the other shorts (avg R)
- **Testing 1:** -0.057 vs -0.103.
- **Testing 2:** -0.162 vs -0.197.
- **Graveyard:** -0.155 vs -0.466.
- **Gen:** -0.370 vs -0.275.
- **Primary, all setups since 10-06:** +0.107 vs -0.157. The brake would have cost Primary's full live book 15R.
- **Reading:** in 4 of 5 accounts the braked trades were no worse, and in Primary they were better. There is no
  persistence to exploit.

### How rare was today (two years, ST-P base, 426 sessions)
- Days with an average of <= -0.71R per trade: **2.6% (11 days, about 1 in 40 sessions, ~6 a year)**. All 11 were
  up sessions for the universe.
- If the trades were independent, 16 trades at that average would happen 0.3% of the time. The common short-side
  driver makes such days about 8× more frequent.

## 6. The plan (numbers above; owner decisions marked)
1. **Keep ST-P exactly as it is** (no change).
   - It is the only tested rule that earns its place on two years: R per unit risk -0.070 → -0.059, CVaR5 -25%,
     max DD -23%.
   - Today it saved about 2.4R.
2. **Do not add stacking caps or risk-sharing** (no change; the owner's no-P/L-cut condition rules them out).
   - Same-bar 1/k sharing would have saved 2.2R today but cost 21R (25%) of the live record.
   - On two years it is no better than shrinking every trade.
   - The same holds for half-size later lots, one lot per family per symbol, profit-gated stacking and no re-entry
     after a target.
3. **OWNER DECISION, optional insurance: the short-family brake.** After 3 RW3/RW5/MF2/MF4 stops in a day, new lots of
   that family trade at half size. Every trade is kept. ST-P stays on top.
   - **Live replay:** total +84.0 → +85.8R, +$1,568 → +$1,728. 10-29 -11.3 → -8.5R (-$411 → -$257). Max DD 11.3 →
     8.5R. Red days unchanged.
   - **Two years:** CVaR5 -39.4 → -29.1R/day, worst day -69 → -40R, max DD -25%, total R better, +6 red days of 426.
   - **What it costs, honestly:**
     - It is insurance, not an edge. On two years it is no better than an equal uniform size cut in train (t -0.36),
       only in valid (t +2.0).
     - Its sibling failed the locked block.
     - In 4 other accounts the braked trades were not worse.
     - If the family's live edge (+0.34R per trade) is real, expect to give up about 0.5 × 12% × 0.34 ≈ 0.02R per
       trade.
   - **Below the Primary full bar (t 2.91).** If the owner says yes, it goes through backlog → after-close merge →
     ledger, like ST-P did (that approval was at t 1.12). Otherwise it runs as a shadow line (step 4) for 20 sessions.
4. **HOUSEKEEPING (rule 15, ships without changing trades): a "red-day attribution" block in the EOD report.** It shows:
   - R and $ from stacked lots (lot >= 2) and from same-bar duplicates;
   - re-entries after a target;
   - ST-P blocks, priced;
   - the session class (universe median open-to-close);
   - the brake's shadow result.
   - This way every red day is explained the same evening, and step 3 gets a forward record.
5. **Say it plainly to the owner: a day like 10-29 will happen again.**
   - On two years this book has a day at <= -0.7R per trade in about 1 of every 40 sessions (~6 a year). **All 11 of
     them were up sessions for the universe.**
   - The levers that really shrink such days also shrink the good days:
     - size (at the pre-10-28 slots today would have been about -$198);
     - the p1_1029 wide stop (-6.4R today, but 10-22 +32R instead of +75R).
   - The real fix is the short family's edge: -0.069R per trade on two years, -0.22R in up sessions. That is a setup
     review (p3_1029 / p1_1029 backlog), not a risk rule.

## 7. Caveats
- **Live samples are small.** There are 16 sessions, and 10-22 is 89% of the live R. Each live replay is one path.
- **The two-year engine differs from live:**
  - It does not model the spread / ETB / participation skips. Live, 19 of today's 35 signals were skipped.
  - It trades about 3× more per day than live, so count-based brakes trip earlier there.
  - There is a survivorship bias in the universe (rule 19).
- **The family brake's live gain rests on 29 trades over 4 days.** The two-year and cross-account checks do not support
  it as a selection rule.
- **The holdout was spent.** The single locked look went to R2b, not to the fam >= 3 version that is now offered as a
  risk control. That version has had no locked look.
- **The stop-width numbers for 10-29 are a 1-min replay,** not a live fill.

## Files
- `PLAN.md`: grids and amendments, written before each round.
- `counts.json`: the configuration count.
- `fetch.py`, `autopsy.py`, `stp_whatif.py`, `regime_today.py`, `live_days.py`: what happened on 10-29.
- `sim.py`, `decomp_train.py`, `eval.py`, `results_r1..r4.csv`, `holdout.py`, `holdout_out.txt`: the two-year study.
- `live_rules.py`, `live_wide.py`, `other_accts.py`: the live replays.
- `backlog_proposed.jsonl`: the proposed backlog lines.
