# GEN exposure: why the Setup Generator's GEN-* setups fire far less live than their screens say (2026-10-25)

*Educational only — not financial advice. Research only: no config, setup, exit or code that affects trading was
changed here (the owner decides). The scripts below only read data. Replays are replays, not live results.*

## Answer first

Gen journaled **99 signals (80 submitted)** on 2026-10-19..23. The summed screen `per_day` of the GEN setups live on
those days adds up to **604**. Where the 604 went, counted on the lab universe the screen uses, for the same 5 sessions:

| step | signals | change | cause |
|---|---|---|---|
| summed 2-year `per_day` of the setups live each day | **604** | | expectation |
| the screen's own code on **those actual days** | **421** | −183 (−30%) | **(g) the expectation is too high**: `per_day` is a 2-year *mean* of a skewed, regime-gated count. For the 10-23 set it is 200/day, but the median day is 143, the last 47 sessions averaged 118, and the range is 51..369 (p10..p90). Peak earnings season also takes out 12–33% of lab names (vs 10.9% on an average day): ≈ −58 of the −183 |
| …that the live **5-bar gate** can act on at all | **308** | −113 (−27%) | **(b) the bar-count gate**: `LabStrategy.eligible` needs `len(bars) % 5 == 0`. Any missing 1-minute bar earlier in the day puts a symbol out of phase, and its decision bars are then never evaluated. Because `generate()` only returns the **first** hit, a first hit on a skipped bar loses that symbol-day for the setup |
| …that a live poll actually saw | 66 | −242 | **(b) poll timing**: slow, phase-locked polls before the 10-23 fix. 10-22: the polls saw 4 of 143. 10-20: one 10:55 bar alone held 42. 10-23: 38 of 38 seen |
| …journaled live | **59** | −7 | **(d) context / frame differences** (10-23: live breadth is over ~3,700 polled names, the screen's over the 1,226 lab names) |
| + live lab-universe signals the screen did not have | +11 | | (d) the same context differences, the other way |
| + names outside the screen's universe | +29 | | **(a)** live trades 2,504 names ≥ $20M ADV, the screen 1,222 |
| **= live signals** | **99** | | |
| − spread 14, ETB 4, opposite side 1 | **80 submitted** | −19 | **(f) filters** |

**On 10-23 alone (the first session after the poll fix):** the summed `per_day` was 200. The screen on that day gave
**51**; 38 of those were gate-evaluable; live caught **31** of them, plus 10 other lab-name signals and 18 outside the
lab universe, for **59** signals and 51 submitted. With the polls fixed, live ≈ the screen on the day. The rest of the
"5–25%" was mostly **the expectation (−75%) and the gate (−25%)**.

**(e) Caps did not bind live yet (10-23 peaked at 50 open positions and 14 in one setup, against caps of 80 and 16), but they will once exposure is fixed.** In a replay of the current 63 setups on
10-01..07 (every decision bar seen): 1,017 signals → 621 submitted. The per-setup cap (16) skipped 187 and the
80-position cap skipped 140.
**(c) First-signal / refire:** live and screen both take only the first qualifying bar, so nothing is lost there. But the
first-hit rule is why a gate-skipped first bar is never recovered later in the day.
**(f) ATR / price filters:** 0.6% of screen signals. **(h) Other:** 10-19 started at 12:10 (1 screen signal before that).
The per-setup −2R stop (off since 10-22 evening) skipped 39 on the 10-22 replay.

**The fixes, ranked by extra live trades, are in section 6.** The top two need no change to what the setups are:
1. Evaluate on every completed 5-minute clock bar (the gate fix): **+49% signals**, rule change no.
2. Raise Gen's caps: these bind as soon as (1) lands, **+65 to +144 submitted/day** on early-October-type days, no setup
   rule change.

Together, on the 10-01..07 replay: **~124 → ~287 submitted/day** for the lab universe alone.

## 1. Data and method

- **Live:** `origin/mcf-data-gen` journal.db (signals 99, trades 99, orders 80), `setups/<date>.json` (setups live
  each session: 10 / 20 / 30 / 40 / 50 GEN), `earnings/<date>.json` (the blackout), `universe.csv`, and the poll logs
  `polls/2026-10-22..23` (there are none before 10-22).
- **Screen, reproduced exactly:** `genexposure1025_screen.py` runs the generator's own `spec_mask_idx` / `first_rows`
  month by month over all 426 open sessions. Every setup's `per_day` comes out to its `gen.screen.per_day` (ratio
  0.9987–1.0005).
- **Screen on 10-19..23:** the 2-year frames end on 10-07. `genexposure1025_frames.py` rebuilds lab frames for the lab
  universe with the history pipeline (`setup_lab.build` on data/cache_hist + the replay store's 1-minute bars, a
  read-only SIP fetch). It then builds the context table over every frame row, as the history does, and applies the
  same screen semantics.
  **Validated** on 10-01..07 against the real panel: 1,322 vs 1,324 rows, 97% identical (setup, symbol, date, bar),
  98.6% identical (setup, symbol, date), the same count on 4 of the 5 days.
- **Replay:** `python -m mcf.replay run --account gen --as-live --universe live --fills paper --limit-fill touch` over
  10-19..23. This is the live runner with a poll every minute, on the lab universe ∩ the live universe minus the live
  blackout (789–1,075 symbols). A second replay runs the current 63 setups on 10-01..07 (lab universe; the blackout is
  not recorded for those days, so it is not applied). Both report fast-path checks 0 / 0.
- **Attribution:** `genexposure1025_attrib.py` takes every screen row (setup, symbol, first qualifying bar) and records:
  - whether the live gate can act on that bar: the 1-minute count at the signal's bar is a multiple of 5;
  - whether the replay and the live journal signalled that (setup, symbol) that day;
  - on 10-22/23, whether a poll saw the count (from the poll log).
  Every replay signal that matched a screen row was gate-evaluable (227 of 227; 885 of 886 on 10-01..07, the one exception
  a rounding / frame difference). Every live signal that matched was gate-evaluable (59 of 59).
  So the mechanism is confirmed live.
- **Live universe (10-19..23):** `genexposure1025_breadth.py` fetches 1-minute bars of all ~4,750 Gen-universe names. It
  computes breadth with the live code over all of them and over the lab names only, plus each symbol-day's
  gate-evaluable share of decision bars. Bars are not stored.
- **Clock-gate what-if:** `genexposure1025_clockgate.py` patches **in-process only** (no file under `mcf/` changes)
  `LabStrategy.eligible`: "count % 5 == 0" becomes its intent, "the latest bar is a 5-minute bucket's decision bar".
  It drops the same test from the replay's fast-path gate and runs the same replays. `_signal`, the runner (acts only on
  the latest bar), first-hit, caps and fills are unchanged.

## 2. Per session (lab universe; screen rows use the live blackout)

| session | GEN setups | Σ per_day (2y) | screen on the day | gate-evaluable | polls saw | replay signals (today's gate) | replay submitted | live signals: lab / all | live submitted |
|---|---|---|---|---|---|---|---|---|---|
| 10-19 (from 12:10) | 10 | 40.2 | 13 | 9 | – | 10 | 7 | 6 / 7 | 6 |
| 10-20 | 20 | 84.0 | 102 | 74 | – | 68 | 22 | 7 / 10 | 6 |
| 10-21 | 30 | 121.5 | 63 | 44 | – | 37 | 21 | 14 / 16 | 13 |
| 10-22 | 40 | 157.5 | 192 | 143 | **4** | 153 | 66 | 2 / 7 | 4 |
| 10-23 | 50 | 199.9 | 51 | 38 | 38 | 20 | 19 | 41 / 59 | 51 |
| **total** | | **603.6** | **421** | **308** | | **288** | **135** | **70 / 99** | **80** |

Notes on the table:
- **Replay skips:**
  - 10-20: 46 per-setup cap (16).
  - 10-21: 10 per-setup cap, 6 ETB.
  - 10-22: 39 per-setup −2R stop (as configured that morning), 38 per-setup cap, 8 ETB, 3 other.
  - 10-19: 3 ETB. 10-23: 1 ETB.
- **10-23 in the replay** has only 20 signals against 31 live matches. The replay computes breadth over its own 789
  names (the lab ∩ live universe after a 1,005-name blackout), a third definition of breadth. The live poll is closer to
  the screen's 1,226 that day. Treat the replay's context-gated counts as ± that.
- **Lost bar times are whole bars:** e.g. 10-20 lost 42 signals at 10:55 alone, and 10-21 lost 9 at 13:00. That is the
  poll-gap signature (research/ops/pollspeed1022.md).

## 3. The 5-bar gate in detail (b)

`LabStrategy.eligible` returns False unless `len(bars) % 5 == 0`. The runner acts only on a signal whose bar is the
latest bar. That bar is `_signal`'s `end`: the first 1-minute bar at or after the bucket's 4th minute. So bucket *k* is
decided only if the 1-minute count at its `end` bar is a multiple of 5, which holds only when the symbol has had a
multiple of 5 missing minutes so far that day. The screen (and every backtest: `eligible` returns True for full-day
contexts) evaluates every bucket.

Share of decision bars (closes 09:50–15:00) the gate can act on even with a poll every minute. Gen live universe,
10-19..23, 23,616 symbol-days:

| 20-day ADV | lab names | other names |
|---|---|---|
| > $1B | **96.5%** | – |
| $150M–1B | 58.1% | 56.1% |
| $95–150M | 35.2% | 36.5% |
| $50–95M | 32.5% | 29.3% |
| $20–50M | 39.0% (10) | 24.9% |
| < $20M (not GEN) | – | ~20% |
| **all ≥ $20M** | **55.6%** | **27.3%** |

Only 36% of lab symbol-days have all 390 minutes. Weighted by where GEN signals actually fall (liquid names, active
bars), **27% of screen signals** on 10-19..23 (113 of 421) and **31% on 10-01..07** (414 of 1,324) sit on a bar the
gate cannot act on.

**Clock-gate what-if (same replays, gate replaced by its intent):**

| replay | screen rows | reproduced, today's gate | reproduced, clock gate | replay signals | submitted (caps as configured) |
|---|---|---|---|---|---|
| 10-01..07, 63 setups (current config) | 1,324 | 886 (66.9%) | **1,288 (97.3%)** | 1,017 → **1,511 (+49%)** | 621 → 712 |
| 10-19..23 as live | 421 | 227 (53.9%) | 292 (69.4%) | 288 → **397 (+38%)** | 135 → 170 |

Entry timing is the same as today for names trading every minute. For a name whose 4th-minute bar is missing it is the
next bar, at most a few minutes later; this is the bar `_signal` already uses. In the what-if every signal was acted on
1 minute after its bar time, as today. The extra signals mostly hit the caps: with the clock gate, 10-01..07 skipped
313 at the per-setup cap and 409 at the 80-position cap. Replay R per trade is noise at this size
(10-01..07: +0.107 → +0.034 R/trade; 10-19..23: −0.12 → −0.07); the purpose here is reps, not R.

**This gate is engine-wide.** Every `type: lab` setup in every account (Primary, Testing 1/2, Graveyard) loses its
first-hit decision bars the same way. Their backtests and screens count every bucket. This is a live-vs-backtest gap
the replay validation (research/replay/VALIDATION.md) could not see, because the replay runs the same gate.

## 4. The other causes, numbers

- **(a) Universe.** The live Gen universe is *wider* than the screen's: 2,504 names ≥ $20M ADV (10-23) vs the 1,222
  lab names the screen was built on.
  - 1,193 lab names are live. 29 are not (e.g. SPY, DIA, GS, EFA, PTPs), which is negligible.
  - The 1,311 other names gave **29 of the 99 live signals** (18 of 59 on 10-23). They are outside the screened
    population, and the gate catches only ~27% of their bars.
  - The earnings blackout is in both, but it is seasonal: 10.9% of lab symbol-days on average, 12.2 / 12.9 / 17.9 /
    24.1 / **33.0%** on 10-19..23.
- **(d) Context.** Live breadth is computed over every polled name (~3,700 with bars); the screen's history is over
  the lab universe.
  - Over 10-19..23: mean |Δbreadth| **0.019** (p90 0.043), |Δbreadth_open| **0.013**. Live breadth averages 1 point lower.
  - At the GEN thresholds the two disagree on **0–7%** of decision bars (breadth > 0.6: 6.7%; breadth_open > 0.5: 7.0%).
  - Net effect on 10-23: −7 screen signals, +10 others, so about neutral for reps. It changes *which* trades, not how many.
- **(e) Caps.** Gen: 80 slots / 80 concurrent, 16 per setup, 1,000 per day.
  - Not hit live: 10-23 peaked at 50 open positions and 14 open in one setup (cap 16).
  - Binding with full exposure: 10-01..07 skipped 32% of replay signals today and **48% with the clock gate**. Long
    `hold`/`holdtr` geometries stay open until 15:55, so positions accumulate.
- **(f) Filters.** Live: 19 of 99 skipped (spread > max or > % of stop 14, ETB 4, opposite side 1). Replays: ETB 3–4%,
  opposite side 3%. ATR ≥ 1% of price would remove 0.6% of screen signals. Price is negligible.
- **(g) Screen over-counting / mis-scaled expectation.**
  - `per_day` = all first-bar signals / 426 sessions, so it is correct as a mean. The distribution is skewed (Apr 2025:
    624/day for the 10-23 set; Aug 2026: 92).
  - Most GEN specs carry a regime gate (SPY/QQQ from open, breadth), so a given day often has 2–5x fewer or more.
  - The generator also picked high-count specs on the full history, so the mean leans on volatile months.
  - Not an overlap or double count: the overlap rule is across setups, and `per_day` counts each setup once per
    symbol-day, as live does.
- **(c) Refire.** Measured only as an option: with `refire: true` (cooldown 1), the 10-23 set's screen signals would go
  from **138 to 258/day** (Sep–Oct 2026, 26 sessions). Most of that is in a few setups (median setup +10%, max ×5.7).
  It is a different trade population from the one screened: a rule change.

## 5. Why the gap looked like 5–25%

Live ÷ Σ`per_day` per day: 17% / 12% / 13% / 4% / 30%. Splitting out the multiplicative causes on the lab universe,
for the 5 sessions together:
- actual day ÷ mean: **0.70** (421 / 604; 10-23 alone: 0.26)
- × gate: **0.73** (308 / 421)
- × polls seen: 10-19..22 **0.06–0.32**, 10-23 **1.00**
- × context: **~0.8–1.1**

Then add the non-lab names (+40% on the lab count) and remove the filters (−19%). For 10-23 this gives
200 × 0.26 × 0.75 × 1.0 × 0.82 ≈ 32 lab matches (31 observed). Most of the shortfall now left is the expectation and
the gate, not a fault.

## 6. Fixes ranked by extra live trades

"Rule change" means: does it change what a setup *is* (its entries, filters or trade population as screened)?
Extra trades are submitted trades/day unless noted, measured on the replays above (lab universe). The 10-01..07 replay
has 63 setups, a busier week; 10-19..23 has 10–50 as live.

| # | fix | extra trades/day | rule change | effort | notes |
|---|---|---|---|---|---|
| 1 | **Gate on the 5-minute clock, not the bar count.** `eligible` asks "is the latest bar a bucket's decision bar (the first bar at or after its 4th minute)?" instead of `len(bars) % 5 == 0`; the replay fast-path gate gets the same change. Engine-wide, or behind `live.lab_clock_gate` per account | **+99 signals/day** (10-01..07, +49%); +22 (10-19..23, +38%). Submitted with today's caps only **+18 / +7**: the caps take the rest (see 2). Outside the lab universe ×~2–3.7 on its part (gate share 27% → ~100%): ≈ +20–50 signals/day at 10-23 volume (estimate; those bars were not replayed) | **No.** It implements what the screen and every backtest measure (first qualifying 5-minute bar, decided at its close). Same entry minute for names trading every minute | S–M: ~15 lines + tests (gappy-name decision bars; equivalence for full-minute names; once per bucket) + a replay check. Touches every account's lab setups: merge outside 09:30–16:00 ET (setup-freeze). Owner: Gen only, or all accounts |
| 2 | **Raise Gen's caps** (`max_positions_per_strategy` 16 → ~48, `max_concurrent_positions` / `slots` 80 → ~200; capital per slot = equity × 3.8 / slots falls to ~$1,900) | **Today's gate: +65/day** (327 cap skips in 5 sessions, 10-01..07). **With fix 1: +144/day** (722). 10-19..23 as live: +19/day (94 per-setup-cap skips) | No for setups (account limits). Smaller size per trade (R-based stats unaffected) | XS (config); owner decides | Only pays once polls (done) and/or fix 1 deliver the exposure. **1 + 2 together, 10-01..07: ~124 → ~287 submitted/day** |
| 3 | **Keep the poll fix honest** (research/ops/pollspeed1022; landed for 10-23: Gen polls 126 → 330) | Already worth up to **+139/day** on a 10-22-type day (polls saw 4 of 143 evaluable signals). 10-23: 0 missed of 38 | No | XS: `python research/ops/pollspeed1022_missed.py` on each session's poll log (0 liquid-name bars missed on 10-23; 7% symbol-decisions, thin names) | Regresses if a 5-minute-bar poll goes over ~4 min again (more GEN context setups) |
| 4 | **Replay reps as a separate "replay" track for GEN** (nightly `mcf.replay run --account gen --as-live --universe live`, results labelled replay, never mixed with live) | Replay submitted: **~124/day** (63 setups, 10-01..07, today's engine); 27/day for 10-19..23 as configured; ~287/day with 1+2 in the replay. These are reps measured offline, not live trades | No | S: the CLI exists. ~6 min/session (50 setups) to ~13 min (63) on 3 cores; needs the day's lab-universe 1-minute bars (~6 MB/day) | Lab universe only. Context columns there are over the replay's own universe (a third breadth definition, ±) |
| 5 | **Report expectations on the right basis** (generator summary / docs/live/generator_lab.json: per setup the median day, the last-60-session mean, × the measured gate share, and the live-universe share) | 0 (expectations only) | No | XS–S | For the 10-23 set: mean 200 → median 143 → last 47 sessions 118 → × 0.73 gate ≈ 86 lab signals/day, + ~40% outside the lab universe, − ~19% filters. That is the honest live expectation today; with fix 1 ≈ 118 + ext |
| 6 | **Catch-up of missed decision bars** (act on a first hit up to N minutes late when no poll saw it) | Small after 1 and 3: 0 of 38 evaluable lab signals were unseen on 10-23 (thin names: ≤ 7% of symbol-decisions) | **Mild yes:** late entry at a different price than measured | S (flag) | Only if poll logs show skipped bars again |
| 7 | **Breadth over a fixed lab-universe list live** (align the context definition with the screen) | ≈ 0 net (10-23: −7 / +10) | Restores the screened definition (fidelity, not reps) | S | Do if the owner wants live GEN trades to be the screened population |
| 8 | **Refire for GEN** (`refire: true`) | Screen level **+120 signals/day** (138 → 258, Sep–Oct) before caps; concentrated in few setups | **Yes** (different trade population; refire outcomes were never screened) | XS config, but each setup needs its own refire screen | Not recommended under "more reps without changing the rules" |
| 9 | **Earnings blackout off for GEN** | ~+12% on average; up to +50% on peak days (33% of lab names out on 10-23) | **Yes** (the screen excluded those symbol-days) | XS | Not recommended |
| 10 | Narrow the live universe to the screen's lab universe | **−29 signals / 5 sessions (−30%)** | Fidelity yes, reps down | XS | Not recommended for reps. Better: tag outside-lab GEN trades in the review so they are read separately |
| 11 | Looser spread / ETB filters | ≤ 19% of signals | Yes (costs / execution) | XS | No (RESEARCH_RULES rule 1: costs in) |

**Suggested order for the owner:**
- 1 + 2 together (biggest; neither changes a setup).
- 5 now (so the dashboard expectation matches).
- 4 if more offline reps are wanted.
- 3 as a daily check.
- Leave 6–11 unless the poll logs or the owner ask.

Fix 1 is a live-engine change for every lab setup, not only GEN. Replaying Testing 1/2 with
`genexposure1025_clockgate.py` (same arguments as `mcf.replay run`) would size it there before deciding. Not done here.

## 7. Limits

- 5 live sessions; Gen's setup count changed every day (10 → 50). The 10-19..21 poll losses are inferred: there are
  no poll logs before 10-22, but whole bar times are missing.
- The replay and the frame rebuild cover only the lab universe (1,226 names with stored bars). Numbers for the other
  1,311 live names (the 29 signals) come from the gate-share table, not a replay.
- Context columns differ in three ways: screen = lab universe incl. blackout names; live = polled names; replay =
  its own symbols. Context-gated counts carry about ±10–20% from this alone.
- Replay fills are paper-modelled, and quotes / ETB are modelled (VALIDATION.md). Skip counts by reason are
  indicative, not exact.
- The 10-01..07 replay ran the *current* 63-setup config, not what was live: Gen did not exist then.

## 8. Files

- `genexposure1025_screen.py` — screen per setup per session over the open months (reproduces `per_day`) + ATR-filter share.
- `genexposure1025_rows.py` — the screen's first-bar rows (for matching) and refire counts.
- `genexposure1025_frames.py` — rebuilt lab frames + context + screen rows for sessions after the frames (validated on 10-01..07).
- `genexposure1025_breadth.py` — live-universe breadth vs lab breadth, and the gate-evaluable share per symbol-day.
- `genexposure1025_attrib.py` — screen → gate → replay → live attribution per session.
- `genexposure1025_clockgate.py` — in-process clock-gate what-if replay (no trading code changed).
- `genexposure1025_results.json` — every number above (attribution per day for both gates, replay summaries, gate
  shares by ADV band, breadth differences, screen distribution, refire counts).

Scratch (replay runs, fetched live-universe bars, journal copy) was deleted after the run. The replay store gained
1-minute bars for 10-19..23 (lab universe), daily bars and priors (data/replay, git-ignored).
