# Scout run log (archived from roles/scout.md on 2026-11-15; newest last)

Educational only - not financial advice.

## State as of 2026-11-10 (run 18-21)
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

## Runs 22-55
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
- Run 37 (11-12 07:30 ET) ICCSET-4: group prior fails a time holdout (-2%); groups were post hoc -> withdrawn; keep pooled shrink.
  Lesson: a grouping drawn after seeing the values needs an out-of-time test before it is recommended.
- Run 38 (11-13 23:20 ET) NEWSMID scored once: FAIL (excess -0.024 ATR, t -1.83); 46% of events' volume peak precedes the
  vendor stamp -> mid-session analyst headlines are priced at publication. Missed the 11-12 slot (no run fired after that close).
- Run 39 (11-14 02:10 ET) LEAD20 (up-day track): top-20 leadership at 10:30 raises the hit rate (82 vs 72%) but not
  rest-of-day return (+6bps, t 0.37); closed. Up-day info that only describes the past move has no continuation value.
  Data cached: scratch lead20/m5.csv.gz (SPY QQQ SPXL TQQQ + 20 mega caps, 5-min, 2024-10..2026-11, locked block absent).
- Run 40 (11-14 03:30 ET) ETFTIER: 3x ETF long on up readings, tiered vs plain: both negative net; tiered raises the median
  (+0.09R) but lowers the mean (-0.02R vs plain). Prior held (exits can't create expectancy).
- Run 41 (11-14 06:30 ET) SHORTUP: strongest stock in strongest sector, 10:30->11:30 on up readings: excess +0.007 ATR (t 0.30),
  net +0.2bps; closed. Up-day thread: all tracks = null. Data cached: scratch shortup/ (489 names 30-min + daily, 2025-03..2026-11).
- Run 42 (11-14 07:30 ET) SIZETREND: gap-predicted size raises afternoon range 14% but not path efficiency (0.452 flat) ->
  no direction-free bracket edge from size. Breakout family = 169 backlog lines.
- Run 43 (11-14 09:30 ET) D1 SIZESTOP plan frozen for Builder (after MOMSIDE): primary = conditioning effect vs random-day
  widening, net of size-cut control; family 79, BAR90 2.66.
- Run 44 (11-14 11:30 ET) SIZESTOP Amendment 1: ex-div gaps negligible (1.1% of Q5; 10 of 206k days change Q4-5), gap now
  dividend-adjusted. Alpaca corporate-actions endpoint works (v1/corporate-actions, cash_dividend).
- Run 45 (11-14 13:30 ET) ANCHOR950: index null re-run on the owner's 09:50 anchor (new CLAUDE.md rule): dip-then-turn, range
  position, early-range breaks all ~0 after 09:50 (40 cells, none |t| >= 2). Future direction work: reference 09:50 + early range.
- Run 46 (11-14 15:40 ET) COMPCAL950: 09:50-referenced M1 line calibrated (slightly conservative), Brier ~ open-referenced
  (VALID 0.129 vs 0.124, t 0.54); better after 14:00. Display option for the owner's COMPCAL decision.
- Run 47 (11-14 17:30 ET) REPS1b re-checked under checklist #39 (pooled ratio, clustered SE): low-rep borrow t -2.38 -> -0.22,
  Gen BP 1.71 -> 2.28, twin -1.33 -> -2.30; conclusions unchanged. Lesson: never average per-day bin means.
- Run 48 (11-14 19:30 ET) 11-18 staging: iccset.py takes the LR8 CSV (recompute_pnl_adj.py); 100% match; ICC 0.196 -> 0.201.
  Agreed Builder's SIZESTOP choices.
- Run 49 (11-14 21:30 ET) refresh.py: journal pull with Skeptic's timing guard (last commit from session, >= 10 min old); tested.
- Run 50 (11-14 23:30 ET) DIPTURN plan frozen (owner dip-then-turn as a day condition on setup trades; shared-day null; family
  2,611). ANCHOR950 power (Skeptic): rules out SPY > ~15-20bps only -> 'not large; small unknown'.
- Run 51 (11-15 01:20 ET) DIPTURN Amendment 1 (tod >= 955; MDE printed). research/SCOUT_MDE.md: MDE for all my closures
  (trade-level ~0.04-0.09 ~= costs; index-level only excludes tens of bps). Standard: every close prints 'nothing above X'.
- Run 52 (11-15 03:40 ET) IMOM (published intraday momentum, JFE 2018): absent in 2024-26 (slope -0.016, t -1.10; C2 -0.9bps,
  MDE80 3.3bps ~ the paper's size). Published index anomalies: test with power first; decay likely.
- Run 53 (11-15 05:30 ET) checklist #42: half days (07-03, 11-28, 12-24 2025) dropped from LEAD20/ETFTIER/SHORTUP/SIZETREND;
  no change. halfday_clean.py (afternoon/morning SPY volume < 0.2) for all future bar caches.
- Run 54 (11-15 07:30 ET) checklist #43: purged scout-qp1 cache (only block-carrying cache); locked-block request guard
  (urlopen wrapper) in all 11 Scout fetch scripts; qp1 fetch split in two ranges. Any NEW fetch script: copy the guard block.
- Run 55 (11-15 09:15 ET) famc_shadow.py reader now pyarrow-filtered to the scored session (+ asserts); other Scout cache
  readers already filter. Switch to Builder's research/guild_read.py when posted.
