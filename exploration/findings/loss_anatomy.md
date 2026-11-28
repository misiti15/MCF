# Track 1: loss anatomy (Primary since 10-23 + non-Graveyard testing arena)

Educational only — not financial advice.

**Window:** 25 sessions, 2026-10-23 .. 2026-11-27. Data comes from the journals, run 1, closed lots, with LR8 R after costs (`cost_r_lr8`).
- **Primary:** 943 lots.
- **Arena:** 17,064 lots across 8 accounts (Testing A-F, Explore 1, Live Lab, Gen). The Graveyard is excluded. No identical signal appears in two arena accounts, so the arena total is the same with or without de-duplication.
- **Day types** use SPY minute bars (SIP, Alpaca GET).
- **Configs tried tonight:** 54 lever replays plus 6 within-day checks = **60**. The cumulative count is about 9,423 (from about 9,363).
- The locked holdout was not read. Scripts and outputs are in `exploration/sandbox/loss_anatomy/`.

**Rule changes inside the window (from the ledger). They matter for every number below.**
- **10-23:** per-setup daily stop switched OFF in Testing / Gen (ST-A). The arena has had **no per-setup stop** all window.
- **10-28:** Primary size about $4k.
- **10-29:** Primary −2R per-setup latch (closed R only).
- **11-12:** LR8 costs. Primary −20R halt and latch moved to cost R. Half-day flatten at 12:55.
- **11-17 (TSZ1):** testing lots at half size with **2x slots**. R per lot is comparable across the date, but arena **lots/day roughly doubled** (about 500 → about 1,000). So arena R/day before and after 11-17 is not comparable.
- **11-19:** Epoch 1 and C3-EXIT100.
- **11-20:** stop rounding and FOOTRACE-EXIT.
- **11-21:** cost-basis fix.
- **11-23:** ST7 out of Primary. BRAKE-BURST (at most 30 entries per setup per 10 minutes). Remedy-Q no-entry-after-12:30 copies of the trio go to testing.
- **Next, 11-30:** AV50 for NM-ETF and the Friday-review moves.

---

## 1. Headline: where the losing R comes from (numbers first)

| | Primary | Arena |
|---|---|---|
| Lots / total R | 943 / **−147.0R** | 17,064 / **−3,036R** |
| Avg R per lot (net / before the LR8 add-on / LR8 add-on) | −0.156 / −0.103 / 0.053 | −0.178 / −0.135 / 0.043 |
| Stop exits | 344 lots, **−391R** (avg −1.137R) | 5,930 lots, −6,214R |
| Target exits | 320 lots, +255R | 4,322 lots, +2,588R |
| Flatten exits | 279 lots, −11R | 5,736 lots, +659R |
| Losing-day R | −235.6R (17 red days of 25) | −3,168R (21 red days of 25) |
| **Worst 5 days' share of losing-day R** | **64%** (−151.5R) | **63%** (−2,005R) |
| The single worst day | 11-25: −42.3R | 11-25: −1,160R (**37%** of all arena losing-day R) |
| **Setup-days at −10R or worse** | 8 of 144 setup-days (5.6%) carry **43%** of negative setup-day R | 110 of 1,556 (7.1%) carry **66%** |
| Setup-days with more than 10 lots ("baskets"), share of total R | **66%** (> 10 lots: −96.9R of −147) | **86%** |

### Three things the anatomy says

1. **The loss is lumpy, and it comes from "baskets".**
   - A basket is one setup firing many same-direction lots in one session. A broad move against that side then stops most of them inside 30-60 minutes.
   - The 5 worst Primary days are **100% short** (−150.9R short, −0.6R long). On each of them, one or two setups put on a basket:

     | Day | Setup | Lots | Stopped | R |
     |---|---|---|---|---|
     | 11-25 | L3-fromopen | 35 | 32 | −35.0R |
     | 11-06 | MF2 | 28 | 24 | −23.0R (27 of the stops in one 30-minute window) |
     | 11-09 | MF4 | 17 | 16 | −18.6R |
     | 11-11 | RW5 + RW3 | 21 + 14 | | −25.7R |
     | 11-10 | RW5 + RW3 | 22 + 17 | | −23.0R |

   - **11-25 in detail.** Primary's L3 had **30 lots open at once**, and 26 stops came between 12:00 and 13:00. The closed-R latch could not act: the lots were all on before the stops came.
   - **The arena is the same on 11-25, but larger.** Seven L3 copies lost −1,037R between them, with 87-311 lots *per copy*: the arena has no per-setup stop, and BRAKE-BURST allows 30 lots per 10 minutes.
   - **Longs do it too.** Gen long baskets on sell-off days: 11-17 (−134.6R in one setup) and 11-20 (long side −410R).

2. **Costs are not what makes the worst days. Direction plus size is.**
   - On Primary's 5 worst days the LR8 add-on is **11%** of the loss: gross −135.0R, cost 16.5R.
   - On the other 12 red days it is 20% (gross −67.3R, cost 16.7R).
   - Fills already include the spread, which I estimate at about **0.08R per lot** (median stop 111 bp, median spread 8.6 bp). Total friction is therefore about 0.13R per lot, against a pre-friction edge of about −0.02R.
   - Costs explain the steady drain. Baskets explain the worst days and the red weeks.

3. **Within a day, *which* lot you take barely matters. *How many* the book takes on a basket day is what matters.**
   - Compared inside the same account-day, the following lots are **not** worse than the rest:
     - late lots (the 11th same-side lot onward);
     - repeat lots in the same name;
     - lots that entered inside an entry burst.

     | Comparison (day-clustered) | Primary | Arena |
     |---|---|---|
     | Late vs earlier lots | −0.041R, t −0.33 | +0.002R, t 0.04 |
     | Repeat vs first lots | −0.063R, t −0.63 | +0.022R, t 0.51 |
     | Burst vs non-burst | −0.053R, t −0.36 | +0.007R, t 0.18 |

   - Across days, though, big baskets lose. In the arena, setup-days with more than 20 lots lost on balance: 141 of 222 were negative, for −3,342R against +1,157R. The cross-sectional "bursts and restacks look bad" pattern (avg R −0.224 for lots in bursts of more than 8, against −0.086 for singletons) is a **day effect**, not a lot effect.
   - So a remedy has to act on **basket size**. Picking which lots to keep inside a basket will not work.

## 2. Decomposition tables

### By side and day type (SPY SIP)
| | Primary long | Primary short | Arena long | Arena short |
|---|---|---|---|---|
| R/lot | −0.121 (185 lots) | −0.164 (758) | −0.163 (8,510) | −0.193 (8,554) |
| SPY up days (open-to-close > +0.4%, 6 days) | +3.1 | **−77.8** | −5.0 | **−1,591** |
| SPY down days (< −0.4%, 9 days) | −20.4 | +16.0 | **−1,070** | +211 |
| Quiet days (10) | −5.0 | −62.8 | −312 | −270 |
| SPY gap-up > +0.3% days (9) | −9.1 | **−85.1 (8 of 9 days red)** | −243 | −315 |

- Each side loses mainly on days when the market goes the other way.
- Correlation of daily R with SPY's open-to-close move: Primary shorts −0.39, Primary longs +0.49; arena shorts −0.50, arena longs +0.70.
- **"Shorts underperform" is mostly "Primary is 80% short in a market that rallied on its worst days".** In the arena, longs lose about as much on down days.

### Time of day, stop width, holding time (Primary; arena in brackets)
- **Entry 13:00-14:30:** −0.285R/lot, t −2.24, 147 lots [arena −0.132, not worse than average]. **11:30-13:00:** −0.130 [arena **−0.274**, driven by 11-25]. Neither pattern holds in both books.
- **Stop under 30 bp:** −0.746R/lot. The LR8 add-on alone is 0.18R. [Arena −0.624.]
- **Stop under 8 spreads:** arena 3,352 lots at −0.30R/lot, against −0.13 for the rest. This is the spread-floor result again.
- **Holding time:**
  - Primary lots closed within 5-15 minutes: −0.552R/lot (112 lots, mostly fast stops).
  - Arena lots held 15-60 minutes: −0.35 to −0.38R/lot.
  - Lots held more than 4 hours: +0.21 [arena] and +0.006 [Primary]. Hold-to-flatten lots are the only positive bucket. This matches "holding beats cutting".

### By setup / family
- **Primary:** all 14 setups are negative. The worst 3 (MF4 −52.5R, MF2 −37.5R, L3-family −13.4R) carry 69% of the loss. The worst 5 carry 81%.
- **Arena:** 149 of 215 setups are negative, so the loss is spread out: the worst 10 setups carry 39%.
  - By family: **GEN −993R** (6,913 lots, −0.144) and **L3 −984R** (1,764 lots, **−0.558/lot**). L3 lost about 1,037R on 11-25 alone.
  - Then CWT14 −316R and RW3S −92R.
  - The only positive families are tiny: IDX1 +13.3R (6 lots), NM1, LD6, IDX3, IDX5.

### Eras (Primary R/day; arena in brackets)
| Era | Rule context | Primary R/day | Primary R/lot | Arena R/day |
|---|---|---|---|---|
| 10-23..10-28 | before the latch | +0.3 | +0.011 | [−54] |
| 10-29..11-11 | latch, pre-LR8 (re-costed) | **−13.2** | **−0.306** | [−109] |
| 11-12..11-16 | LR8, TEAM-6 | **+21.3** | +0.440 | [+15] |
| 11-17..11-18 | TSZ1 in testing | −4.0 | −0.112 | [−192, 2x slots] |
| 11-19..11-20 | Epoch 1 | −6.6 | −0.203 | [−48] |
| 11-23..11-27 | ST7 out, BRAKE-BURST | **−14.8** | **−0.564** | [−323] |

No rule change lines up with a lasting step up. The two good stretches (11-12..11-16, 10-23..10-28) are where the basket days happened to go right: L3 made +31.0R on 11-12 (52 lots) and +16.4R on 11-16 (31 lots).

### Weeks (Primary)
| Week ending | −10-23 | 10-30 | 11-06 | 11-13 | 11-20 | 11-27 |
|---|---|---|---|---|---|---|
| R | −3.3 | −10.1 | −33.9 | −44.7 | +4.1 | −59.2 |
| Short R | −6.3 | −3.5 | −33.5 | −44.8 | +26.0 | −62.6 |

Every red week except the one-session 10-23 week and 10-30 has at least one setup-day of −15R or worse.

## 3. Lever replays on live lots (costs in, size-matched controls)

**Method.**
- Each lever skips (or halves) some lots. Freed slots are not refilled.
- Two controls:
  - **U:** skip the same total exposure at random across the book. This is the size-cut control.
  - **W:** skip the same number of lots at random *inside the same setup-day*. This asks whether the lever picks the right lots.
- Each control uses 200-300 draws.
- `dt` is the day-clustered t of the daily difference. The full grid is in `levers_out.txt`, `basket_out.txt` and `daytype_out.txt`.

| Lever (Primary) | Exposure cut | Saved R (per week) | vs U (pct) | dt | Green-day cost | Worst-5 | Red days | Best-day share |
|---|---|---|---|---|---|---|---|---|
| **Basket cap: max 5 lots per setup-day (skip)** | 47% | **+99.7 (+19.9/wk)**; ex-11-25 +68.3 | 98th | 1.47 | −46.1R (U −41.8) | −151.5 → **−56.1** (U −82.4) | 17 → 15 | 34% |
| Basket cap 5, lots 6+ at **half** size | 23% | +49.9 (+10.0/wk) | 92nd | 1.47 | −23.1R | → −97.3 (U −117.0) | 17 → 17 | 34% |
| Basket cap 10 (skip) | 26% | +48.6 (+9.7/wk) | 76th | 0.92 | −42.8R | → −82.7 | 17 → 17 | 57% |
| Max 5 open lots per setup | 37% | +81.3 (+16.3/wk) | 98th | 1.34 | −36.5R | → −67.4 | 17 → 15 | 38% |
| **No shorts on SPY gap-up > 0.3% days** | 20% | **+85.1 (+17.0/wk)** | 100th | **2.31** | +2.5R | → −126.7 | **17 → 13** | 35% |
| No entries from 13:00 | 20% | +46.1 (+9.2/wk) | 93rd | 2.26 | −2.4R | → −130.1 | 17 → 16 | 25% |
| Spread floor (skip stops under 6 spreads) | 9% | +11.1 (+2.2/wk) | 42nd | 0.99 | −11.6R | → −136.1 | 17 → 19 | 45% |
| −2R closed latch (already live) | 3% | +0.7 | — | — | — | — | — | — |

**The same levers in the arena (8 accounts, 25 days).**

| Lever | Exposure cut | Saved | vs U (pct) | Worst-5 | Green-day cost | Setups better / worse |
|---|---|---|---|---|---|---|
| Basket cap 5 (skip) | 70% | +2,295R | 100th | −2,005 → **−321** (U −607) | −174 | 116 / 40 (−278R on the losers) |
| Basket cap 5 (half) | 35% | +1,147R | 94th | −2,005 → −1,098 (U −1,304) | — | Families 29 better / 6 worse (−10.5R) |

- **Basket cap, against W:** 0-13th percentile. Inside a setup-day, random lots would save as much or more. The cap works by trimming *basket days*, not by choosing lots.
- **Gap-up shorts off:** **0th percentile vs U.** It does not replicate.
- **No entries from 13:00:** 0th percentile vs U. It does not replicate.
- **Spread floor:** +519R (+104R/wk across 8 accounts). It is at the **100th percentile vs both U and W**: the only lever here that picks better lots. It also *helps* green days (+38.8R). 114 setups are better and 36 worse.
- **Arena −2R latch (the arena has none):** +1,221R, 100th percentile vs U. But W (random lots in the same setup-days) saves 1,599R. The latch picks the right days but fires after the basket is already on, which is why LATCH-OPEN / open-lot caps matter.

**Weekly view, Primary.**

| Week ending | 10-23 | 10-30 | 11-06 | 11-13 | 11-20 | 11-27 | Green weeks |
|---|---|---|---|---|---|---|---|
| Base | −3.3 | −10.1 | −33.9 | −44.7 | +4.1 | −59.2 | **1 of 6** |
| Cap-5 skip | −4.1 | −3.5 | +4.9 | −27.1 | +5.6 | −23.1 | **2 of 6** |
| Cap-5 skip + no gap-up shorts | −4.1 | −5.0 | +15.7 | −0.5 | +10.0 | −17.8 | **2 of 6**, with 11-13 at −0.5 |

**Per-setup effect of cap-5 (half), as the remedy rule requires.**
- **Primary:** 9 setups better, 1 worse. The one that loses is L3-fromopen, at −5.4R: the cap trims its 11-12 (+31.0R) and 11-16 (+16.4R) basket wins along with its 11-25 loss.
- **Arena:** 29 families better, 6 worse (worst: exhaustion_short −5.2R, NS4 −4.3R).

## 4. The 3 most targeted loss levers (estimated Primary R/week, with green-day cost)

1. **Per-setup basket cap at 5 lots per session (lots 6+ skipped or half size).**
   - Effect: **+20 R/wk skipped (±14 R/wk, 1 SE) or +10 R/wk at half size (±7).**
   - Green-day cost: about 9 R/wk (skip) or 5 R/wk (half). Worst-5 days fall 63% (skip) or 36% (half). Red-day count barely moves (17 → 15 / 17).
   - It targets the dominant mechanism (baskets on the wrong side of a broad move) and holds on both books against a size-matched random cut. **It costs L3's windfall days.**
   - **Conflict to flag:** the bench (rootcause_1119) found stacking caps cost L3/RW3/RW5 13-21R each over two years. The owner has ruled out stacking caps that cut P/L. So the 25-day live evidence disagrees with a two-year bench, and only a forward shadow can settle it.
2. **No shorts on SPY gap-up days (more than +0.3%).**
   - Effect: **+17 R/wk on Primary** (dt 2.31, red days 17 → 13, zero green-day cost).
   - It **fails in the arena** (0th percentile vs a random cut). This is essentially the running GAP-U shadow (+42.7R over 11 sessions). Keep it a Primary-specific forward test; do not adopt it on this evidence.
3. **Spread floor (skip stops under 6 spreads).**
   - Effect: only **+2 R/wk on Primary**, but **+104 R/wk across the arena**.
   - It is the only lever that beats random *within* the setup-day (100th percentile) and helps green days. It is already logging from 11-30 (SPREADFLOOR shadow). No new action is needed beyond scoring it.

Not levers: restack bans and entry-burst caps are inside-the-day lot pickers (t ≤ 0.6). Time-of-day cut-offs and gap-down long-off do not replicate across books.

## 5. Confidence

- **High** that losses are concentrated in basket setup-days and that the worst days are direction/size losses, not costs. Both books show it, the worst-5 share is 63-64% in each, and the within-day checks are clean.
- **Medium-low** that a basket cap adds R going forward:
  - The sample is 25 days, with day t 1.47 on Primary and 2.07 in the arena.
  - It holds after removing 11-25 (Primary +68R, arena +1,203R) and in both halves (Primary +80 / +20, arena +842 / +1,453).
  - But it is mostly a conditional size cut, which beats a random cut by only about 6R/wk on Primary. It contradicts the two-year bench on the trio.
- **Low** for gap-up shorts off and time-of-day cuts: Primary only, and they do not replicate.

## 6. PROPOSAL candidates

### P1. BASKET5 shadow (replay only, no runtime change). It can START Monday 11-30.
- **What:** each night (or at the Friday review), re-score every account's journal twice:
  - (a) each setup's lots after the 5th in a session skipped;
  - (b) the same lots at half size.

  Compare both with actual and with an exposure-matched random cut (200 draws). Use the code in `exploration/sandbox/loss_anatomy/basket.py`.
- **Accounts:** Primary (decision book) and the arena (8 accounts, for sample size). Primary rules stay untouched.
- **Baseline:** actual live R (LR8) for the same sessions.
- **Duration:**
  - Arena read at 10 sessions (around 12-11).
  - Primary decision at 20 sessions (around 12-28). The window contains 12-24, a half day, which should be reported separately.
- **Success criteria (all must hold on Primary):**
  - variant (b) saves at least +5 R/wk;
  - day-clustered t at least 2.0;
  - at least the 90th percentile vs the exposure-matched random cut;
  - worst-5 improved by at least 30%;
  - best-day share of the saving under 50%;
  - no setup loses more than 50% of its own positive R.

  The arena must agree in sign and in percentile.
- **Expected effect:** variant (b) +10 R/wk (1 SE ±7; a plausible range of −5 to +25). Variant (a) +20 R/wk (±14).
- **Risk:**
  - None while it is a shadow.
  - If later adopted: it cuts the windfall basket days (L3 11-12 / 11-16 type, about −20 to −45R in such a week). It contradicts the bench finding and the owner's stacking-cap stance. It is a size cut that only partly beats random.
- **Owner decision needed for:** nothing to start it (it is reporting only). Any live adoption is a later Friday-epoch decision.

### P2. GAP-U shadow: add a book split and a random control at its 15-20 session bar. It can START Monday (reporting only).
- **What:** when GAP-U is scored (around 12-10), also report:
  - its effect per book (Primary vs arena);
  - its percentile against a random skip of the same exposure;
  - red days before and after.
- **Why:** in tonight's replay it is the best Primary lever (+17 R/wk, red days 17 → 13, no green-day cost), but it fails in the arena (0th percentile).
- **Success:** on Primary, at least the 90th percentile vs random, at least +5 R/wk, with the arena not significantly negative.
- **Expected:** +5 to +17 R/wk on Primary if it holds. **Risk:** none while it is a shadow.

### P3 (supporting, no new experiment).
- **SPREADFLOOR:** already logging from 11-30. Tonight's live replay confirms it is the only lot-picking lever that works. Score it as planned.
- **LATCH-OPEN:** 11-25 shows 30 L3 lots open before the first stop cluster. This supports the pending LATCH-OPEN card as the targeted tail fix inside Primary rules.

## Sources
- Journals: origin/mcf-data, mcf-data-testing, -testing2, -gen, -livelab, -explore1, -testingd, -testinge, -testingf. All read through git show and deleted after use.
- `mcf.costs.cost_r_lr8`; `research/ledger.jsonl`; SPY 1-minute SIP bars from Alpaca (GET).
- Prior work: exploration/PRIOR_RESEARCH.md; rootcause_1119 (stacking caps); RWOUT; neveragain_1125 (LATCH-OPEN); GAP-U shadow.
- Scripts, in run order: `extract.py`, `features.py`, `describe.py`, `levers.py`, `basket.py`, `daytype_levers.py`. Outputs: `*_out.txt`, `days_*.csv`.

Educational only — not financial advice.

---

## Reviewer notes (review_loss_anatomy, 2026-11-28)

Educational only — not financial advice.

**What I checked.**
- I read all six scripts.
- I re-ran the Primary headline numbers with independent code (`exploration/sandbox/review_loss_anatomy/recheck.py`, 1,000 random draws).
- I re-scored the two Primary levers on the setups that will actually be in Primary from 11-30 (`roster.py`).
- Configs added by this review: 5 (2 re-checks and 3 roster replays). Cumulative is about 9,428. The holdout was not read.

**Process and integrity.**
- `git diff --name-only <merge-base with the default branch> HEAD` on explore/2026-11-27 shows no path outside `exploration/`. Commit 00b36d2d91 touches only `exploration/findings/loss_anatomy.md` and `exploration/sandbox/loss_anatomy/*`.
- No remote branch other than explore/2026-11-27 points at 00b36d2d91 or ffc4ccfd1f.
- Journals were read through `git show` and deleted after use, and SPY was read with a GET. The scripts contain no secrets.

**Reproduction (exact match).**

| Primary number | Track | Re-check |
|---|---|---|
| Lots / total R | 943 / −147.0R | 943 / −147.0R |
| Red days | 17 of 25 | 17 of 25 |
| Losing-day R | −235.6 | −235.6 |
| Worst-5 | −151.5 (64%) | −151.5 (64%) |
| L3 on 11-25 | 35 lots, 32 stops, −35.0R | 35 lots, 32 stops, −35.0R |
| Cap-5 skip | +99.7R, dt 1.47, worst-5 → −56.1, red days → 15, green-day cost −46.1 | same |
| Cap-5 half | +49.9R | +49.9R, but 88th percentile vs random on 1,000 draws (track: 92nd on 200) |
| Gap-up shorts off | +85.1R, dt 2.31, 8 of 9 days red | same (from days_primary.csv) |

**Method checks.**

*Lookahead.* None found.
- The lot cap uses entry order within the setup-day.
- The spread floor uses the spread recorded at entry.
- The SPY gap is known at 09:30.
- The open-lot and closed-R counts use only earlier lots. Small caveat: they count lots the same lever would itself have skipped, so the replay is approximate.

*Costs.* LR8 is applied to every lot through `cost_r_lr8`. Spread is already in the fills.
- The claim that pre-friction edge is about −0.02R rests on a *median* spread/stop estimate. The mean is higher because of tight stops, so treat it as indicative.
- Half-size replays scale R linearly, which ignores any fixed per-order cost. The effect is small.

*Labels.*
- The SPY bars were fetched with `feed="iex"` (regular hours via `rth()`), not SIP as the text says. That is fine for SPY day types.
- The arena de-duplication key includes the strategy name, so copies of a setup under different names (for example, the seven L3 copies) are *not* merged.
  - "No duplicate signals" is true only by exact key.
  - Arena lot counts and per-setup better/worse counts overstate independent evidence. The day-clustered t is not affected.

*Controls.* The U and W percentiles randomise at the lot level, not by day, so they overstate significance for a book whose losses cluster by day. The day-clustered t values are the honest test, and the track reports them.

*Rule-change context.* The list is mostly right. Three items are missing, and they all change setup composition inside the window:
- 11-19: C3-EXIT100 moved 20 arena setups to the Graveyard.
- 11-20: Friday review. MF2-FD and MF4-FD left Primary; assignments show them as since 11-20, with first session 11-23. Also GY-FOOTRACE.
- 11-23: FOOTRACE-EXIT moved 12 arena setups.
- 11-27: ROT-B3 moved 8 arena setups.

The arena and Primary rosters at the end of the window are therefore not the rosters that produced most of the losses.

**Per finding.**

1. **Losses are lumpy and driven by baskets: HOLDS** (descriptive). Reproduced exactly. Both books show it, and it is not a selection claim, so multiplicity does not apply.
   - Caveats: one-big-day carry is real. 11-25 is 18% of Primary losing-day R and 37% of the arena's.
   - The arena 11-25 size (87-311 lots per L3 copy) comes partly from the arena having no per-setup stop (ST-A) and from 2x slots (TSZ1, 11-17). It does not carry over one-for-one to Primary.

2. **Costs are not what makes the worst days: HOLDS** (11% vs 20%).
   - Part of this is arithmetic: stop-outs magnify gross R while cost per lot is flat.
   - "Shorts underperform is mostly exposure": **weakened to partly**. Shorts are still worse per lot in both books (Primary −0.164 vs −0.121; arena −0.193 vs −0.163). The 25-day correlations depend on this window's market path.

3. **Which lot inside a day does not matter: HOLDS** for the arena, where the estimates are tight (|diff| ≤ 0.02R).
   - On Primary the point estimates are negative (−0.04 to −0.06R) and the test has little power. Read it as "no evidence", not "proven zero".
   - "Big baskets lose across days" is a description in a book with a negative per-lot edge. Smaller K always saves more (K3 > K5 > K8 …), which is what a size cut does.

**Levers and proposals.**

- **Basket cap (P1): WEAKENED, with no forward Primary case.**
  - *Size cut, not selection.* On the full window, the excess over a proportional size cut is only +29.6R (+5.9 R/wk) for skip and +14.3R (+2.9 R/wk) for half. The day-clustered t of that excess is **0.91**.
  - *The saving came from setups that have already left Primary.* MF4 (+37.2R) and MF2 (+36.9R) give **74%** of the skip-variant saving, and both left Primary after 11-20.
  - *On the roster that trades from 11-30 (L3-fromopen, NM-ETF, RW3, RW5):* 576 lots, −30.1R.
    - Cap-5 skip saves +16.9R (+3.4 R/wk). That is the **58th percentile** vs random, with excess +0.4 R/wk and **dt 0.30**.
    - **Without its best day (11-25) it is −14.5R.** Its best-day share is 186%, and its green-day cost is −58.5R.
    - The half variant saves +1.7 R/wk at the 54th percentile.
  - *The arena* says the same: K5 cuts 70% of exposure, and a random cut of 70% already saves about 2,125 of the 2,295R.
  - *Verdict:* P1 as written would very likely fail its own success bar on Primary. A basket shadow is still cheap to keep as reporting, but the criteria should measure **excess over an exposure-matched cut** with a day-block random control, not saving vs actual. Do not expect a Primary decision from it.

- **Gap-up shorts off (P2): WEAKENED** but still the best Primary lever.
  - On the current roster: +51.3R (+10.3 R/wk), 100th percentile, excess +8.9 R/wk, dt **1.72** (down from 2.31). Ex-best-day +22.1R, best-day share **57%**, so it gets the `1 day` tag. Red days 14 → 14.
  - It fails in the arena (0th percentile). Two thresholds were tried (0.3 / 0.5), and it overlaps the already-running GAP-U shadow, which limits the multiplicity cost.
  - P2 as a reporting add-on (book split plus random control) is sound and can start Monday. The expected value should be +0 to +10 R/wk, not +5 to +17.

- **Spread floor (P3): HOLDS.** It is the strongest result in the track.
  - Arena: dt 3.45, 100th percentile vs both U and W, positive on green days, best-day share 24%.
  - Primary: small (42nd percentile).
  - It was pre-existing, so there is no new multiplicity. Scoring it as planned is right.

- **LATCH-OPEN support: HOLDS** as a mechanism. All 30 L3 lots were on before the first stop, and the arena −2R latch beat random by day. It is not quantified for Primary here.

- **Not levers (restack/burst bans, time cut-offs, gap-down long-off): HOLD.**

- **Challenge to the goal: HOLDS.** Red days barely move under any lever. On the current roster even the best lever leaves 14 of 25 red. Green weeks need a positive per-lot edge, not tail trimming.

**Final confidence.**
- High in the anatomy: concentration, baskets, and the direction-times-size mechanism.
- Low that the basket cap adds R in Primary going forward (current roster: 58th percentile, dt 0.30, carried by 11-25).
- Low-medium for gap-up shorts off (Primary only, one-day tag).
- Medium-high for the spread floor.
- For Monday: keep P2 and P3 as reporting. Run P1 only as a re-scoped reporting shadow on excess over random.
