# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-10 run 18, ~18:45 ET)
- Day 2 closed: EVD1 (mixed), D2PM (Observer), COMPCAL M1 -> owner DECISION (keep M1; vol-scaled lost FWD), SZBAND (VALID
  calibrated, drifts with vol). Lesson: premarket / earnings data tell SIZE, not direction. FAMC: Observer testing option C
  (Alpaca news headlines as point-in-time AMC list, 79% recall) on the full denominator; could start without live-code change.
- Day 3 (mine): fresh direction sources. OPTFLOW pilot (Alpaca option minute bars, unsigned call-share proxy) CLOSED by kill
  line: monotone right sign but Q5-Q1 +0.035 ATR, day-t 1.05 (54 sessions). Signed version = new counted look, Lead's call.
- Run 19: NEWSDIR (headline polarity, Alpaca news, fixed lexicon) CLOSED by kill line: +0.032 ATR t 1.18 vs gap baseline
  +0.028 - the news is already in the gap by 09:50. FAMC starts 11-11 (Observer's hybrid calendar, Builder runs nightly).
  SZBAND fixed by Builder's PVSCALE (alpha 0.8, VALID t -4.48) -> card size line.
- Run 20: UNGAP (unexplained gaps fade?) CLOSED, wrong sign: unexplained gaps drift WITH the gap (+0.039 ATR t 1.49) vs
  explained flat; diff +0.041 t 1.75. Lead (21:00): main effort shifts to execution/sizing on the 14 cost-killed setups; I keep
  ONE direction pilot per day. FAMC first reaction session 11-11 (ALC, RGTI); Builder runs nightly.
- Run 21: Lead paused direction pilots for a day. WHATWORKS (descriptive): of 128 live setup x account rows (>= 20 trades),
  only RW1-gapdn-bounce-flowsell-short-FD (Testing 2) is + after live costs, + w/o best day and best-day share < 50%;
  all 11 near-misses are shorts (gap-down / flow-sell), best days mostly 11-04/11-05. Asked Builder for the 2y lab column.
  CLOSED tonight (others): LIMEX (limits adversely selected), cost-killed execution remedy. Builder next: CONFIRM entries.
- Closed (mine): QP1, SC2, SC1, NH1, STOPW, HODSEP, RCOMPASS-1, COILAM, SIZEBKT, EVD1, OPTFLOW, NEWSDIR, UNGAP. Open: FAMC.

## Learned
- Journals: git fetch --depth=1 origin mcf-data*, git show FETCH_HEAD:journal.db; live paper = runs.kind 'paper';
  R = pnl_adj / (|entry - stop| x shares). Ledger effective dates give the rule-change context per window.
- The 60-name / 63-session pilot kit (scratchpad optflow: stock1m, daily, news, opt30) makes a direction pilot a
  ~30-minute job; its limits (large caps, one regime, ~60 days) mean only a t >= 2 there is worth a 2-year plan.
- By 09:50 public direction information (earnings surprise, headline polarity, premarket drift) is already in the gap;
  every 'new information' source tested so far adds size, not rest-of-day direction. Look for information that is NOT public
  at the open or that arrives DURING the session.
- Alpaca serves historical option minute / 30-min bars (OCC symbols built directly: und + yymmdd + C/P + strike x1000,
  8 digits; Friday expiries; strikes on 1 / 2.5 / 5 grids). 60 names x 54 sessions ~ 1 hour of GETs. Bars are unsigned.
- A prior-N-day percentile band is a base rate, not a today-rate: it is calibrated on average and miscalibrated
  by today's volatility (predictably). Report coverage by today's vol tercile, always.
- Before a forward shadow, test the data plumbing end to end (proxy access, which fields the live snapshot keeps):
  Observer found FAMC unbuildable before a single fake row was written.
- A forward rule may only use inputs that exist before the decision in LIVE: check the live source (here the surprise
  arrives late), and pick the cell that needs nothing else.
- Register how a result's SIGN will be read before the output lands when the outside prior points the other way
  (EVD1: literature favours an intraday fade on earnings days, our test measures continuation).
- Predicted size (rvol, range) at 5-60 min is noise amplitude: brackets get whipsawed MORE on high-size names.
  Don't route size predictors into entries; at most into per-name sizing / stop width (and beat 'trade smaller').
- Any day label ('held', 'flipped', 'quiet') must be known at the entry time; 'no flip all day' peeks past the entry.
  Compare post-event trades with 'not-yet-event at entry', never with 'event never happened'.
- Let another role score a plan I froze when I have not looked: keeps the look honest and the count at one.
- TEMPLATE RULE: every look-back slice goes through a guard (`win(arr, lo, hi)` asserting lo >= 0); numpy wraps
  negative indices to the end of the day = silent look-ahead. HODSEP v1 looked like t 16.8 because of it. Assert the first
  candidate bar >= the longest look-back, and enter at the next bar's open so feature and outcome share no price.
- 'Too strong' is a bug signal: send it to Skeptic before planning (it worked).
- A big-excursion label (max high >= X ATR) rewards volatility features; always check a directional, day-demeaned
  forward return too before calling a feature a selector.
- Alpaca multi-symbol bars: 100 symbols/request, ~1,240 symbols x 33 sessions of 5-min bars ~ 15 min (includes extended
  hours - filter to RTH). Slices like a[b-5:b+1] break at b < 5 (negative index) - guard window starts.
- Before freezing a plan, walk its skip funnel on paper: SC1's own LOD stop + 0.6-ATR cap removed >95% of the very
  trades the rule was built for (names that HOLD their gap are extended above the LOD). Count skips by reason in every script.
- Followers beating same-minute random names is not catch-up: Skeptic's C3 (laggard minus already-moved follower) and the
  driver-hedged R are the right controls for any lead-lag idea.
- Cross-sectional controls over ~500 names x 430 days x 50 bars blow memory if pooled per bar; do signals first, then a
  second streaming pass that trades controls only at the needed (date, bar) keys.
- Write selftest expectations from the rule, not intuition: three times today the code was right and my fixture was wrong
  (z crossing a bar early, Wilder RSI decay ~35, gap-through fill at the open).
- No lab ETP list exists: universe.csv name regex works (202 of 1,225; watch word boundaries - 'Maplebear' hit Bear;
  Sprott 'Physical Gold/Silver Trust' needed adding). Family try-counts: grep backlog configs_tried; ex30 families share one
  count across their 5 setups (e.g. peer family 15), COMBO1's 15 already includes its 9-config first pass.
- Pre-writing for Builder: copy gate2.py conventions (bars(), cost formula, G.summary, dtype, wf months, bar90 row);
  add a --selftest on synthetic bars so logic is checked without the cache. Write test expectations carefully (a partial
  driver move can cross z a bar early - that is correct behaviour).
- Backlog (950 rows) + pod1022 (452 ideas) cover almost every classic family: VWAP, gap, RSI, ORB, SPY gates, PDH/PDL,
  fades, calendar/TOM/OPEX pin, TLT, SSR (rule 201), round numbers, RS vs SPY, lunch/quiet-tape (ex30). Grep both
  (research/backlog.jsonl and research/bdi/pod1022/NOTES.md, research/bdi/ex30/CATALOG.md) before proposing anything.
- Not yet covered (as of 11-09): cross-asset commodity/crypto -> equity lead-lag; intraday event-day (earnings) entries
  (blocked by no historical calendar + live blackout).
- Quiet day at 10:00 is not predictable from tape: QD1 8 + QR1 3 + QP1 4 = 15 configs, best +10..+12 pts vs +15 bar.
  Sector dispersion predicts day SIZE (both splits). Most stable weak flag: SPY crosses open >= 2x by 09:55.
- Quiet-day big movers are ~90% earnings names (2 days, descriptive).
- Data: no bar cache in a fresh container. Alpaca market-data GET works with env keys (urllib, feed=sip); 13 ETFs x 2y
  5-min took ~2 min. No pyarrow -> save CSV. Run scripts with `python3 -I` and use __file__ for output paths.
- Guild worktree: `git fetch origin mcf-guild && git worktree add ../guild origin/mcf-guild`, then
  `git checkout -B mcf-guild origin/mcf-guild` inside it.

## Failed
- QP1: 4 non-SPY quiet predictors, 0 pass (dispersion, VXX, crossings, combo).

- Run 22 (11-11 01:20 ET) BOTHDAYS: 0/74 live setups earn on both SPY up and down days (w/o best day). Median beta
  longs +0.145, shorts -0.134 R per 1% SPY. Builder's lab join had every WHATWORKS survivor negative over 2 years (a direction bet).
- Run 23 (11-11 03:30 ET) DISP1 (Lead's within-sector split pilot): FAIL, -0.028 ATR t -0.70 (443 events/20 days); legs disagree.
  Sector/peer/laggard family now 94 configs, all closed. Corr-based sector map (formation-only) works if a sector map is needed again.
- Run 24 (11-11 05:30 ET) NEWSMID prep: Alpaca news API gives ~1,200 RTH items/session (benzinga + fiscal.ai transcripts),
  created_at stamped; 27,467 items fetched 10-08..11-09 (scratchpad newsmid/). Draft plan + checklist walk; outcomes unread.
  Halts: no Alpaca halt endpoint -> parked.
- Run 25 (11-11 07:50 ET) NEWSMID frozen (A1 Skeptic's six points; A2 lexicon fix from dry-run sanity table). Scorer
  newsmid.py --selftest/--dry/--score; dry funnel 1,341 events / 23 days; re-posts 169. Lesson: a --dry mode that stops at the
  entry bar lets lexicon/funnel bugs be fixed before any outcome is seen.
- Run 26 (11-11 09:45 ET) COILGAP (owner item 3): coil longs off on SPY gap <= -0.25% -> ex-mkt shared-day z -0.01; closed.
  Coil switches from market state now 0/2 (COILAM checkpoint, COILGAP gap). Shared-day random switch code: research/coilgap/coilgap.py.
- Run 27 (11-11 12:30 ET) REPS1 lever table (owner P1 item 1): Gen starved by account halt (66/session) + buying power (60),
  what-if no worse than traded; low-rep starved by borrow (30.6/session vs 19.9 submitted). Simplified exit is +0.071R optimistic
  vs live gross (corr 0.92) -> use relative only. Alpaca 5-min fetch of 2,236 names takes > 30 min: run it with a start index in parts.
- Run 28 (11-11 13:30 ET) REPS1b in setup-days: blocks add <= ~12 good Gen setup-days/week (halt 7.5 on 2 days only, BP 4.7);
  spread filters protective after logged spread (median 0.33R); low-rep limit = signal frequency (median 6/16 days) -> more setups
  live is the scalable lever. Exit-model gap by hour 0.01-0.09R.
- Run 29 (11-11 15:30 ET) REPS2 slot yield: median 2.7 setup-days/week per live slot; p_day = 1-exp(-0.193 x lab/day);
  near-dead twin-blocked slots MF4-h40-open-flowsell (0/14) and MF3 (2/15).
- Run 30 (11-11 17:30 ET) REPS3 frozen forecast for the 11-12 roster: 482.8 setup-days/week = baseline; restructure moves
  setups, adds none by itself; gains must come from unlocks / universe / unrated setups. Owner unlocked halt (300R), Gen x1.8.
- Run 31 (11-11 19:15 ET) REPS3 score.py built + selftest (frozen before data). Asked Lead: NEWSMID one look on 11-12 or hold.
- Run 32 (11-11 21:30 ET) NEWSMID scorer verified on synthetic data: planted +0.4 ATR found (both legs), null not flagged.
- Run 33 (11-11 23:30 ET) FILLCOST: latency equal across accounts (~1.25 min bar->order, ~2 s fill); slip ~half spread
  (+0.01-0.02R). Bug: journal meta has outcome-linked suffix (';touch_fill') -> parse JSON prefix only. Owned exit-model error.
- Run 34 (11-12 01:30 ET) ICCSET: per-setup ICC 0.07-0.45 (null 90th 0.09), not beta; survivors RW3/RW5/CWT09/MF2-FD
  high-ICC (n_eff ~0.25 x n). Bench/rotation log not live -> rotation unmeasurable from journals.
- Run 35 (11-12 03:30 ET) ICCSET-2 shrunk ICC (tau 0.134 real; shrunk 0.09-0.32); table for owner on 11-18.
- Run 36 (11-12 05:30 ET) ICCSET-3: coarse setup groups explain 40% of ICC (CWT 0.10, flow/gap 0.18, heat 0.39, GEN 0.07/n=4);
  11-18 table should shrink toward group ICC.
## Next
- 11-18: refresh ICCSET (iccset.py + shrink.py on fresh journals) beside REPS3.
- Score REPS3 on 11-18 after close: `python3 -I research/reps3/score.py <fresh journal dir> research/reps3/forecast_setups.csv` (refresh journals via git show origin/mcf-data*:journal.db, incl. testingd/e/f).
- 11-12 after 16:00 ET: NEWSMID one look (Lead approved): `cd research/newsmid && python3 -I newsmid.py --score <scratch>/newsmid/news_rth.csv.gz <scratch>/hodsep` in background (slow loops), then post result + close/shadow per kill line.
- P1 (live reps) until further notice; new direction pilots paused (NEWSMID scoring on 11-12 only if Lead re-opens pilots).
- REPS next: per-setup expected setup-days/week for candidates to rotate in (lab signal-day rate x live parity) once the bench
  log / Gen candidate list is on a branch; check repv when pushed.
- One direction pilot per day (Lead). Candidates where information arrives DURING the session: intraday news after 10:00 vs the
  move that follows; halt / resume events; sector-ETF breaks spreading to members mid-session (careful: laggard family closed).
- 11-12 pilot: score NEWSMID once: `python -I research/newsmid/newsmid.py --score <scratch>/newsmid/news_rth.csv.gz <scratch>/hodsep` (slow loops; run in background).
- Read FAMC's first nightly line (11-11) and Observer's live-vs-lab cost table for the 14 cost-killed setups.
