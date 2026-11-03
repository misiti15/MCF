Educational only — not financial advice

# Night 2026-11-02 — synthesis plan ("plan"): what must change after three bad Primary days

Owner, 2026-11-02 evening: "Something has to be different and has to change. This low level of success for the past 3 days
is unacceptable." Primary 10-29 −11.3R, 10-30 −2.5R, 11-02 −6.2R = **−20.0R on 43 trades, 33% wins**. The owner trusts the
2-year backtest less ("live testing rules all"), asks whether setups are too complex, and wants setups that work in more than
one kind of market.

This plan pulls together five overnight workstreams (all research only, nothing in `config/`, setups or exits changed, nothing
merged, costs always in, locked block 2024-11-01..2025-02-28 never loaded):
`regime/`, `simple/`, `losers/`, `livelab/`, `replay/` (each has its own NOTES.md in this folder).

**Configurations scored overnight: 2,229** (regime 2,070, simple 89, losers 26, livelab 32, replay 12). **Pre-declared
finalists that passed their bar: 0.** Nothing tonight justifies a change to a Primary setup or exit.

## Failures first — what we learned does NOT fix it

1. **Simpler setups are not better.** Across 89 forms of the 7 busiest live setups, avg R falls with every condition
   removed, on 2 years and on a re-score of the live dates. A one-condition setup is the same as a random entry
   (+0.002R over random on 2 years). The four live one-condition setups (heat_fade family) are the worst live group
   (mean −0.28R). Condition count vs live avg R: rho +0.08 (p 0.42), no link. The problem is not too many conditions; it is
   that the conditions add only ~0.01-0.03R each on top of a random-entry base of about −0.08 to −0.10R after costs.
2. **The losing trades look like the winning trades at entry.** 98% are plain full stops (median best gain before the stop
   0.28R on Primary). Three patterns explain −15.3R of the −20R (repeat lots in one name, six SOXS shorts, late shorts into a
   bounce) — but the same flagged trades made **+31.6R on Primary's other 7 days**. A rule written after each bad day would
   have chased noise. 0 of 26 entry / exit / filter adjustments pass.
3. **No simple day switch passes.** Three switches were pre-declared from live data and tested once on 2 years; all fail
   (best: switch A, 2-year VALID t 0.62 vs the 1.0 bar). Live and 2-year results disagree on switches in general: the best
   2-year switch found after the fact is t −1.55 on live.
4. **No live setup is robust across day types.** 0 of 68 live setups with 30+ trades are positive on up, down and quiet days
   alike; no pair of setups hedges the market; 0 of 17 pairs/books checked on 2 years are positive in all three day types.
5. **The replay is not yet usable as evidence.** It now matches live 95.8% of trades when fed what live saw (2 sessions), but
   still fails the avg-R band (+0.059R optimistic, mostly a Gen journal gap) and a new setup has no recorded quotes yet.
   Rule 21: no replay number may be used, even as a filter, until it passes on 10+ sessions.

## What the evidence does say (live first, then 2 years)

- **The book is a bet on the market's direction, and it has no edge on quiet days.** Live, all 5 accounts, 12,256 trades,
  10-06..11-02 (5 up, 5 down, 10 quiet sessions; SPY open-to-close beyond ±0.25%): longs −0.34R per trade on down days,
  shorts −0.28R on up days, and **both sides lose on quiet days (−611R together, half of all sessions)**. On 2 years every
  family tested this week behaves the same way (shorts lose about −0.30R on up days whatever their conditions).
- **Primary's record is a short-side direction bet plus a few big days.** Primary shorts: +0.37R per trade on down days
  (+61.5R), −0.20R on up days, −0.21R on quiet days. Primary over 10-20..11-02 is still **+33.8R on 411 trades (+0.082R)**,
  but 10-22 alone gave about +70R; three of its five best setups take ≥ 50% of their R from one session. The last three days
  are inside what this noise allows (median sd of a setup's daily mean R is 0.53R): they are not proof that Primary broke,
  and the +33.8R is not proof it works.
- **11-02 was not a plain wrong-direction day.** SPY was +0.55% at 10:30 before falling: Primary shorted into the morning
  rally and was stopped. Six of the 12 trades were SOXS shorts (an inverse semiconductor ETF, so in effect long semis on a
  −1% day), −6.1R of the −6.2R, at $87-124 risk per lot against a Primary median of $12-48.
- **Exposure, not the gate, is the bottleneck for live testing.** Only 19 of 238 setup-account records have 30+ live trades and
  10+ sessions. Early live records barely predict later ones (first 30 trades vs the rest: Spearman +0.20, p 0.23). A
  real +0.20R edge needs about 17-20 sessions to show (day-clustered t 1.5); 10 sessions only catch big failures.
- **The last lane with a minimal gate lost the most.** The Setup Generator account (screen-only gate) averaged −0.284R on 990
  trades 10-21..11-02, against −0.09 to −0.14R in Testing 1/2. A live-first lane must be small, cheap and fail fast.
- **Entry friction is real and measurable:** a live fill is on average 0.041R worse than the next 1-minute open — about half
  of Primary's +0.08R average. The Testing cost filter (CF, from 10-30) targets the same friction; its 10-session review is due
  around 11-12.

**Plain answer to the owner:** what must change is mostly *how we find and judge setups*, not tonight's Primary rules. Every
Primary fix tested tonight either failed on 2 years or failed on live. The honest changes are: put new setups on paper sooner
and judge them on live R (decision LL1), stop reading losing stretches without the day type next to them (FYI REG-2 + REG1),
aim the search at quiet-day and both-direction setups (QDAY), and make the replay trustworthy so it can screen in hours instead
of weeks (RQ1).

## Rule changes in effect inside the windows used (owner rule 2026-11-02, from research/ledger.jsonl)

10-20 scale-out fix, twin cap, per-setup −2R stop in Testing; 10-21 promotion = move, Graveyard opens, L3-fromopen-FD and
CWT14-pdl-p10-lowvol to Primary; 10-22 L3-fromopen-FD, NS3-FD, RW6G1 out of Primary; 10-23 per-setup stop off in T1/T2/Gen;
10-26 CWT13-z05-long and ST7-FD promoted, MF1 demoted; **10-27 GX1 5-minute clock (new record version for every lab setup)**;
10-27 CWT13 demoted; **10-28 Primary size ~$5k then ~$4k**, three Primary setups rotated to Testing 2; **10-29 Primary per-setup
−2R latched stop**, BAR90, Setup Generator paused; **10-30 Testing cost filter CF; L3-gap-slope-rsi5hi-FD and L3-fromopen-FD
promoted to Primary**; 11-02 R2A legs into Testing 2, NS3-FD / RW4-FD to the Graveyard. **All three bad Primary days fall after
the 10-28 size change and the 10-29 −2R stop, and the 11-02 SOXS lots came from the two L3 setups promoted on 10-30.** Primary
went from ~42 trades per session before 10-29 to 12-16 after. R is per trade, so size does not scale it, but the stop and slot
changes change which trades exist: the three bad days are not directly comparable with Primary's earlier record.

## Owner DECISIONS (priority order, at most 6)

### 1. LL1 — Open a small live-first lane for new setups (in Testing 1 / Testing 2, no new account)?
- **What changes:** up to 10 "lane" seats at the end of `setup_order` in Testing 1 and 10 in Testing 2 (equal weight, T1 = T2).
  Entry gate (minimal, costs in): 2-year open-frame expectancy ≥ −0.02R in TRAIN and VALID, 1.5-25 trades/session, module
  matches its scored version, not a duplicate of a live setup. **Fail fast**, automatic via the normal after-close PR: after
  5+ sessions and 45+ trades with avg R ≤ −0.30, or cumulative ≤ −15R. **Verdict at 20 sessions / 40+ trades**: pass needs live
  avg R > 0 with day-clustered t ≥ 1.0, avg R w/o best day > 0 with best-day share < 50%, ≥ −0.05R on each of 3+ up and 3+
  down sessions. A pass stays in Testing on the normal path (never straight to Primary); the owner is asked before any retire.
  A 6th "Live Lab" account (orders `mll-`) is the later option if supply outgrows 20 seats (owner said no new account on 10-27).
- **Evidence (live):** T1 / T2 peak 73 / 89 of 400 slots, 0 buying-power rejects, so ~300 free slots each. Kill rule 45 trades /
  ≤ −0.30R was the only one of 27 that separated setups (9 killed, 0 positive later, later −0.277R vs −0.114R kept; 1 of 27, a
  hint). Generator precedent (screen-only gate) −0.284R on 990 trades — why the lane must stay small and fail fast.
  **Backtest:** none needed for the lane itself; supply today is thin — 3 backlog entries pass the gate cleanly
  (bdi-rw-nm-flowsell-rsi65-gapdn-volume, bdi-vid-envelopes, mh-1029-earnings-sympathy), 6 more need a trade-count check.
- **Scope:** Testing only. **Risk:** expected yield is mostly fails (22% of setups were positive later); at t 1.0 a true 0R setup
  still passes ~16% of the time; lane setups compete for symbols with existing Testing setups (place in line). Paper only.
- **Reply:** "LL1 yes" / "LL1 account" (6th account instead) / "LL1 no".

### 2. REG1 — Keep Primary's setups as they are and shadow-score the 10:00 "fade" switch for 20 sessions?
- **What changes:** no Primary trading change. Each night Primary trades entered at/after 10:00 are tagged *kept* (shorts when
  SPY is at or above its 09:30 open at 10:00, longs when below) or *dropped*, and the running kept-vs-random figure is in the
  brief. After 20 new sessions a Testing trial is proposed only if, on the new sessions alone, kept beats dropped, the
  beat-random t ≥ 1.0, and kept avg R > 0 without its best session.
- **Evidence (live):** Primary 10-06..11-02 kept 53% of trades, +43.3R vs −32.1R for all (t 1.45), but 10-22 alone was +70.6R.
  On the last three days it would have given −4.5R instead of −20R. **Backtest:** TRAIN t 1.04, VALID t 0.62 — **fails** the
  pre-declared bar; kept trades still average below 0R on 2 years. It is the only switch whose sign agrees live, TRAIN, VALID.
- **Scope:** Primary, monitoring only. **Risk:** none to trading; the honest risk is that "no change" feels like inaction —
  but every Primary change tested tonight failed. Rule changes 10-28 / 10-29 sit inside its live window.
- **Reply:** "REG1 yes" / "REG1 no".

### 3. QDAY — Aim BDI's nightly new-setup search at quiet-day and both-direction setups?
- **What changes:** for the next two weeks, BDI's daily new idea (charter: one per weekday) goes first to setups built for
  range / quiet sessions and to hedged forms (e.g. the queued mh-1102-group-laggard-hedged), and every candidate shows its R on
  up / down / quiet days before anything else. No gate changes; the existing "positive in up AND down sessions" rule stays.
- **Evidence (live):** quiet days were 10 of 20 sessions and both sides lost there (−611R); 0 of 68 setups robust across day
  types. **Backtest:** every family tested this week is a direction bet on 2 years; the one precursor with information beyond
  the day's direction (peer-group laggards, +0.075R vs a day-matched random entry, t 2.43, research/bdi/1102) fails as a plain
  setup and is queued as a hedged rework.
- **Scope:** research only. **Risk:** quiet-day edges may be too small to survive costs; this narrows the search for two weeks.
- **Reply:** "QDAY yes" / "QDAY no".

### 4. RW3S — Put the simpler gap-down flow-sell short (RW3 without its RSI line) in Testing as an observation, by owner exception?
- **What changes:** add `RW3S-gapdn-flowsell-short-FD` = the RW3-FD module with the `rsi5 > 80` line removed (heat ≤ −20,
  buyPressure < −0.35, gap < 0, short t1s1, 09:50-15:00, ADV ≥ 95M) to one Testing account, rules frozen. Judge after ≥ 20
  sessions / 60 trades on avg R, avg R w/o best day, and the up-day vs down-day split. Primary's RW3-FD is not touched.
- **Evidence (live re-score, not paper):** 10-06..11-02 1,727 trades +0.110R, t 1.56 (parent +0.093R); w/o best day +0.072R
  (best day 42%); last three days −0.16 / +0.23 / +0.25R vs parent −0.40 / −0.88 / −0.15R. Live up days −0.125R, down days
  +0.327R. **Backtest:** TRAIN −0.071 / VALID −0.026R (better than the parent but negative), does not beat random (0.000),
  **fails BAR90 and the lane gate** (≥ −0.02R). 1 of 89 configurations.
- **Scope:** Testing only (observation). **Risk:** it is a down-day bet and loses on up days; the re-score uses a 1,096-name
  universe with no slot caps, so paper will differ. Thin evidence — recommendation is Optional, not Yes.
- **Reply:** "RW3S yes" / "RW3S no".

### 5. RQ1 — Make the replay pass its audit before anything else uses it (10-session rolling audit + market quotes)?
- **What changes:** research tooling only. Merge the replay input fix (branch `claude/replay-fix-1102`: recorded quotes / borrow,
  full live universe) after the close with its tests; wire historical market quotes taken at the moment live decides (poll start
  + the account's median delay) for setups with no recordings; run the rule-21 audit on 10+ post-fix sessions with a rolling
  store (~30 MB per session, fetch-replay-delete). Per account; Primary, T1, T2 first. Until it passes, replay numbers stay out
  of every decision (rule 21 unchanged).
- **Evidence (live vs replay):** fed what live saw, trade match 70.2% → **95.8%** (10-30 + 11-02; Primary 100%, T1 100%, T2
  98.8%), but avg R still +0.059R optimistic (mostly Gen's 39 unbooked 11-02 entries) and 2 sessions are far too few. Offline,
  the market quote at poll start + delay reproduces live's spread-skip decision 96.3% vs 84.5% for today's synthetic draw.
- **Scope:** research tooling (no live path, config, setup or exit change). **Risk:** may still fail on stop-fill slippage
  (replay stop exits +0.06-0.08R too kind in T2 / Graveyard) and Graveyard path dependence; costs night CPU and ~30 MB disk/night.
- **Reply:** "RQ1 yes" / "RQ1 no".

Not raised as decisions (housekeeping or already decided): REG-2 day-type split in reviews (report-only, ships as housekeeping);
CWT13-tidy (a line that never binds; zero mask diff, merged after the close); OPS-GEN1102 Gen 11-02 unbooked entries (tracked as
HK-RECON-GEN, expected on Tuesday's reconcile); the wide-stop rework and the L3 inverse-ETF skip / underlying-exposure cap
(backlog: losers1102-wide-stop-15-same-dollar, nightly-1102-l3-inverse-etf-skip, bdi-1102-underlying-exposure-cap); DM-N3 (open
since 11-02, unchanged).

## What BDI keeps running each night

1. Move Hunt and the capture rate (charter step 0a), with that day's win named.
2. **Day type next to every result** (REG-2, from tonight's brief): each setup's R split by SPY up / down / quiet day and by SPY
   above / below its open at 10:00, beside the avg-R-without-best-day column, plus the ledger rule changes inside the window.
3. **REG1 shadow line** (if "REG1 yes"): kept / dropped Primary R and running kept-vs-random t; BRAKE-1 shadow line (owner 11-01).
4. **Lane scoring** (if "LL1 yes"): each lane setup's sessions, live R, w/o best day, up/down split, fail-fast state, every night.
5. **Rolling replay audit** (if "RQ1 yes"): one session a night, fetch → replay → compare → delete, per-account match and gap.
6. Watches already open: CF 10-session review (~11-12), PROMO-L3 / PROMO-L3F / PROMO-ST7 Primary watches (L3 reviews 11-12),
   MON-NS4 / MON-GEN03, SO-1A R2A, Gen 11-02 reconcile (HK-RECON-GEN).
7. Backlog reworks with numbers each weekday (rule 18): the L3-only inverse-ETF skip and the count-lots-by-underlying cap
   (11-02 SOXS), the wide-stop-at-same-$ rework, the hedged peer-laggard rework.

## Where the evidence is thin (stated plainly)

- Live windows are 20 sessions (5 up / 5 down / 10 quiet); Primary's last three days are 43 trades.
- Live re-scores (simple) and replays are bar re-simulations on a smaller universe, not paper fills; replays failed their 10-29
  audit and are a diagnosis only.
- The 2-year scans have no slot or lot caps and cover only the lab setups (no L3 / CWT / ST7 / GEN in the losers 2-year test).
- REG1's live gain leans on one session (10-22); RW3S fails every backtest bar; the lane's kill rule is 1 of 27 tried.

Files: this PLAN.md (research/bdi/night1102/PLAN.md), research/bdi/night1102/plan/NOTES.md; workstream notes `research/bdi/night1102/{regime,simple,losers,livelab,replay}/NOTES.md`.
Educational only — not financial advice.
