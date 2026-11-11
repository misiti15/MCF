# builder notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09, run 1)
- Data: the container had NO 2-year cache (data/cache_hist), lab frames (research/history2y/data), open frame
  (research/bdi/timeofday/data/open), o5_hist or bt_lab1104 lists. All git-ignored. Rebuild recipe: MCF
  research/bdi/1104/DATA.md (download wrapper dl_wrapper.py, build_frames.py --context, build_open.py, build_o5.py,
  bt_all.py). Do it after 16:00 ET only: download.py's STOP_UTC guard exists to keep the live 08:35 job's Alpaca
  rate budget; keys are in the env (never print them). Needs `pip install -e ".[dev,alpaca]"` + `pip install pyarrow` (installed 11-09; the combined command timed out once in the background, run them separately).
- Plans frozen (no scores yet): research/gate2/PLAN.md (Lead P1, 11 configs, N 123 with GATE1's looks, BAR90 2.79),
  research/c3fr/PLAN.md + c3fr.py (6 configs, N 21, BAR90 2.22; simulator unit-checked on synthetic paths),
  Observer's 09:50 opening-drive measurement (pre-declared on the board, builder-20261109-0820-3).

- Run 2 (08:40 ET): gate2.py written + synthetic-checked (trigger, E1, E2 trail, gap stop). Scout pre-writes SC2
  (research/sc2/); tonight's order: rebuild -> GATE2 -> Observer 09:50 -> SC2 -> C3FR.
- Run 3 (10:25 ET): GATE2 Amendment 1 (Skeptic audit) in PLAN.md + gate2.py, sizing block synthetic-tested.
  Queue tonight: rebuild -> GATE2 -> Observer 09:50 -> SC2 (Scout's research/sc2/sc2.py, PLAN frozen) -> C3FR ->
  Observer CWT14 'already >= X ATR below open' skip (2 configs, plan first) ; SC1 script pending from Scout.
- Run 4 (12:30 ET): GATE2 Amendment 2 (strict < tie); CWT14SKIP PLAN + script (synthetic-tested). Lead's order
  tonight: rebuild -> GATE2 -> 09:50 opening-drive -> SC2 (Scout amended, family N 76) -> CWT14SKIP -> C3FR if time ->
  long-laggard column (name - SPY fromOpen at entry) for Observer. SC1 (Scout sc1.py) after.
- Family try-count standard (Lead 11-09): a pass at a study's own bar = 'lead worth pursuing'; a Testing move must
  clear the family's summed N (laggard catch-up family N 76 -> BAR90 2.65).
- Run 5 (14:25 ET): CWT14SKIP Amendment 1 (within-variant control etc.), null + planted synthetic checks;
  research/data/rebuild.sh + dl.py (stop guard 07:30 ET 11-10). Evening: run rebuild.sh FIRST (background, ~1h+), post
  'cache up/not up', then GATE2 -> 09:50 -> SC2 -> CWT14SKIP -> SC1 -> C3FR; queue: Observer GEN exit replay (plan first).
- Evening 11-09: cache UP (1-min bars 1,226 syms to 11-09; frames, context, daily). Scored: OD0950 (closed),
  GATE2 11/11 (0 pass), SC2 (0/12), SC1 (0/8, underpowered), NH1 (0/8), C3FR (0/6), CWT14SKIP (X1.5 passes own bar
  1.93: t 2.05, tiny, VALID weak), BEREPLAY (0/3). All data rebuilt and present in this container; bt_lab1104 lists +
  GEN hold lists (scratchpad/hold/bt, rebuild with bereplay/bt_hold.py) exist.

## Learned
- 11-11: a per-setup random null is too narrow for day-level switches; GAP-U's edge vanished with a shared-day null.
  Against-the-market-state entries beat their setup-day peers book-wide, mostly SPY intraday reversion (ex-market ~30% left).
- The 2-year lab book is negative (~-0.06R VALID), so gates/blocks get raw t for free: always score excess over a
  control (Skeptic), report kept avg R.
- Lag/peer signals pick names (COMBO1 C3 +0.096R vs random) but opening friction (0.16-0.23R at R 0.25 ATR) kills them;
  friction in R scales with 1/R — the targeted remedy is wider R, not a new filter.
- Tags so far mostly restate SPY direction (L1/L2/L3/L6): always split by SPY up/down/quiet and compare to a
  same-side control.

- Dict lookups with a default (I.get(tod, 999)) can silently leak look-ahead; compare times numerically and assert.
- Sizing / gate deltas on a losing book score positive from volume alone: demean by the setup's period mean and
  compare to random relabelings.

- GATE2: pullback timing after a confirmed SPY reading beats a random post-reading bar by +0.1..+0.2R (t up to 11.9),
  but failed holds (stop at the open, ~-1R) eat it: break-even hold 83-94% vs 72-86% observed on traded days.
- Pattern tonight: names "picked" vs same-minute random names usually add ~0..+0.02R; most raw R is SPY direction (up
  days +, down days -). Always print up/down/quiet and a same-minute control first; it saves reading noise as edge.
- SC2: follower-vs-random was positive (t 2.4-5.4) only because the driver kept moving; the laggard-vs-non-laggard
  control (Skeptic) is the one that tells catch-up from momentum.
- Ops: never edit a shell script while bash is running it (bash reads it incrementally) - run a frozen copy.
- gates GD._blackout silently returns all-False without research/bdi/earnings/data/earnings_yf.parquet (copy from the
  research-data branch, open rows only).

- mfe-based giveback overstates exit fixes ~10x: BE50 upper bound +176,671R, bar replay -16,000R (dip-then-win trades).
- Next-bar entry matters: COMBO1-C3's gross halved (+0.083 -> +0.042R) when entry moved from the signal close.
- Check helper filters against how config stores fields (GEN geom lives in the module, not the yaml) - print counts.

- Equal-$-risk changes (wider stop, fewer shares) shrink losses in R on a losing book by size alone: always add the
  size-cut control (BASE x D/D'); STOPW's 'pass' was 85% size cut.
- GATE2 pullback timing survives a matched control in ATR units (t 4-32) but is ~0.02-0.03 ATR/trade.

- An exit keyed to SPY returning to its open fires on ~39% of trades and cuts recoveries; SPY revisits its open often.
  Index-based 'invalidation' exits need a hysteresis or time component, or they just add churn.

- Tag time-alignment: lab tod is a bar END; a compass/state mark at the same minute is not yet published (T+1). Use strict <.

- PBO (research/xapbo): stable ranking != edge (STOPW PBO 0, loses OOS 100%); single-study PBO sd ~0.22.

- Winner's curse is measurable: GEN lab mean vs live rho -0.23; worst-quarter (robustness) is the only screen with + rank.

- Lookup tables fitted on one period can't follow base-rate drift; a rolling empirical benchmark stays calibrated.

- Volatility scaling helps SIZE forecasts strongly (alpha ~0.8) but not close-SIDE probabilities (alpha 0): size
  scales with vol; whether the day holds its side depends on distance vs remaining variance, already in M1.

- Limit entries on these setups fill the losers and miss the runners (adverse selection): always report filled vs missed.

- Board posts: assert ALL messages' length before writing ANY (a later assert left duplicates of earlier posts).
- A move through a level after the signal is a strong selector (t 19) but entering AT it pays the move: use it as an exit.

## Failed
- MFFRESHLOW 2: 0 pass (live 53-trade pattern did not carry to 2y).
- GATE2-R 4 (MX failed-hold exit, MXH half size): 0 pass; gross negative; GATE2 closed.
- STOPW 4 (plan bar 'pass', size-cut control: stop effect fails down days), CWT14SKIP closed (blackout-free t 1.05).
- SC1-R 4 (Amendment 3): 0 pass; more trades erased the +0.355R small-sample lean.
- C3FR 6, BEREPLAY 3, GATE2 sizing 3: 0 pass.
- OD0950 (09:50 continuation, control -0.10R in every decile), GATE2 8 setup configs, SC2 12, SC1 8, NH1 8: 0 pass.

## Next
- 11-11 18:00: DONE tonight: FAMC s1 (2 events, +0.611R raw, K 1/1); GAP-U re-test (fails vs shared-day null, VALID
  +4,538 vs 95th +4,905; ETB off same; posted); REGSW-2 0/4 (base 11 frozen 57911e03c; S2-S4 negative = against-state
  better; full base t -6, ex-market removes ~70%, residual < 3.57); RCOMPASS v2 0/3 (VALID post-flip BETTER).
  RUNNING: run_fwdcal.sh (Gen books ~25 min each; D1 sel -> D0 sel -> holdout). Post rule-21 result when it lands
  (out/audit_d*_sel.csv, out/chosen_delay.txt, out/audit_dD_hold.csv, causes, exitkind).
  LESSONS: never `git stash -u` while jobs write into the worktree (it unlinked live output files; recovered via
  /proc/<pid>/fd and reruns). run_evening.sh's --depth=1 data fetches truncate history (fwdcal re-deepens).
  Don't put `timeout 1500` on rcompass_v2 (~35 min).
- 11-11 14:45: FWDCAL takes Skeptic's 4 points: config per day via git archive of the default-branch commit at 09:30
  (needs git fetch --shallow-since=2026-10-28 origin claude/intraday-trading-system-witis4), live equity from status.json,
  D picked on 11-04..11-06, rule 21 once on 11-10..11-11, exit-kind gap table. EVENING ORDER: run_evening.sh, then
  bash research/fwdcal/run_fwdcal.sh, then REGSW-2 / RCOMPASS v2. Engine code = today's (not mirrored) - say so.
- 11-11 12:40: OWNER P1 item 2 (Lead lead-20261111-1100-3): FWDCAL mirror-live calibration built
  (research/fwdcal/mirror.py; vendor/ = fwdrep run.py + report.py from charming-mccarthy d3901f7e, ROOT line only).
  Each account replays with its own snapshot (enabled setups, live/shorts/exits) and caps, twin block, -R halt, Testing A
  top-500 pool from 11-04, and --delay D for entries (unit-tested: D=1 fills at the next bar's open). Audit = rule 21 per
  account plus a cause for every unmatched trade. EVENING after run_evening.sh: bash research/fwdcal/run_fwdcal.sh
  (11-04..11-11, D=1 then D=0). Limits: account yaml = today's (shallow clone has no config history); equity = config
  starting_equity, not the live balance (buying power differs, mainly Gen).
- NIGHTLY from 11-11 after 16:00 ET: python research/evd1/famc_shadow.py --date D --calendar research/evd1/famc_calendar.csv
  (Observer's build_famc_cal.py fills the calendar after 20:00 ET for D-1's after-close reporters); post one line:
  n events, rule vs control raw mean, K_edge / K_harm. First: python research/data/append_day.py D (after 16:05 ET; adds D's 1-min bars + daily row).
  Cache + daily now end 2026-11-10 (backup of the 11-09 daily table in the scratchpad).
- 11-11 10:45: EVENING (>= 16:05 ET): bash research/regsw_rebreak/run_evening.sh (FAMC s1 + GAP-U re-break ETB on/off
  + gapdays). Then REGSW-2 (shared-day null, copy GAP from score.py, live labelled in-sample, by side) and RCOMPASS v2
  (python research/rcompass/rcompass_v2.py ../compassbf/trades_tagged.parquet ../compassbf/compass_2y.csv.gz rcompass_v2).
  OWNER TOP PRIORITY now: faster quality reps (research/repv, fwdrep, fastdec on claude/charming-mccarthy-i3rhhr).
- 11-11 08:45: OWNER TASK REGSW-2 plan frozen (winning base = lab TRAIN gross > 0 AND live net > 0; 4 switches, N 103).
  Next: base stage (--base-only) commit, Skeptic audit, then score. FAMC tonight.
- 11-11 06:35: S6 long-hold: model book $76.0k vs live $81.5k (frozen live ahead), model_equity/te blank -> flagged as
  housekeeping for the main session. Checklist: run research/SKEPTIC_CHECKLIST.md before posting any frozen plan.
- 11-11 04:30: minute-10 exit CLOSED (untriggered post-10 ~0 / slightly +; live giveback of triggered trades doesn't
  replicate on 2y). Next: FAMC nightly from 11-11 16:05 ET (append_day.py, then famc_shadow.py).
- 11-11 03:00: CONFIRM 0/2 as entry (timing t -18), but the trigger selects (skip excess t 19): proposed a 10-min
  confirmation EXIT (market entry, flat at min 10 if no k x D move) - awaiting Lead.
- 11-11 00:40: CONFIRM plan + script frozen, waiting for Skeptic's attack before scoring. WHATWORKS lab join: all
  live survivors negative on 2y, down-day positive / up-day negative (market direction).
- 11-10 23:05: LIMEX 0/3: limit entry at the signal close is adversely selected (missed = winners); market entry stays.
- 11-10 18:45: PVSCALE: size band vol-scaled alpha 0.8 adopts (VALID pinball t -4.48, tercile coverage fixed);
  close-side M1 alpha* 0 (unchanged).
- 11-10 16:30: COMPCAL Amendment 1 vol-scaled M1: VALID better (t -0.78) but FWD worse (t +2.14) -> keep M1;
  full-ratio vol scaling over-corrects low-vol days.
- 11-10 14:45: owner COMPASS task part 2: COMPCAL - continuous remaining-move line (M1) beats the cell table out of
  sample (Brier VALID t -2.21, FWD t -0.93), calibrated; prior-close side adds nothing OOS. Recommended for the card.
- 11-10 12:35: FAMC data: Nasdaq calendar snapshot (research-data earnings_cal, fetch_public.py on Actions) carries
  AMC timing weeks ahead, labels right 81% on gaps; needs a fresh fetch (Lead's call). Yahoo 15:00 'dmh' = placeholder.
- 11-10 10:30: D3GEN robustness: CI [+0.04,+0.44], LOO +0.18..+0.31; ranks but top third still -0.10R live. EVD1 run
  posted to Scout (no surprise-direction signal). Next: on request; D2PM is Observer's after 16:00.
- 11-10 09:25: earnings alignment table (BMO/AMC aligned 5.6-5.7x; dmh reacts next day), D3GEN (worst-quarter screen ranks
  live GEN rho +0.24, p 0.04; old screen ~0), EVD1 running for Scout (added 'session' as a timing column name).
- 11-10 07:20: FLOW1-2Y closed (restates SPY), XA-EPROC built (daily-peeked t = 27% false holds; 20 sessions ~no power).
- 11-10 05:00: COILAM 0/1, all-family morning map chance-level, XA-PBO tool built + tested.
- Done 11-10 night: compass re-tag (strict <, +gross/spy_move), RCOMPASS stage 1 run (flips don't separate),
  MFFRESHLOW 0/2. Queue empty -> wait for Lead / Scout's RCOMPASS verdict.
- Compass backfill done (research/compassbf): compass_2y + tagged trades (local parquet). Next: Observer's MF fresh-low
  skip (research/obs-extension/BACKLOG_ENTRY_mf_freshlow.md) on 2y lists; family cuts for RCOMPASS on request.
- (11-10) Lead/owner focus = rolling compass (Scout descriptive first). Be ready to build the backfilled compass
  (SPY/QQQ/IWM, 2y) x setup-family afternoon gross split once Scout posts a clear split; gross first, size-cut control.
0. (11-10) Answer Skeptic on CWT14SKIP; forward tally from 11-10 if Lead wants it; SC1 done (0/12, closed unless new idea);
   Observer's lab-vs-live cost pairing (plan first) if Lead slots it.
1. After 16:00 ET: rebuild cache + frames + open frame + o5 (+ bt_all lists for GATE2 sizing).
2. Run gate2.py per PLAN (report all 11, failures first), then Observer measurement, then c3fr.py.
