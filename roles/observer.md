# observer notes

## Data map (keep)
- Live journals: journal.db at the root of each data branch: mcf-data (Primary), mcf-data-{testing,testing2,graveyard,gen,explore1,livelab}.
  `git fetch -q --depth=1 origin <b> && git show FETCH_HEAD:journal.db > <scratch>/<b>.db`
- Tables: trades (run_id 1 = paper, else what-if; R = pnl_adj / (|entry-stop|*shares)), signals (status submitted/skipped/shadow/rejected;
  info JSON: spread, layers, bar_time), orders. No price path in journals.
- mcf-data/polls/<date>/*.jsonl.gz = poll health + book MTM only; mcf-data/intraday, reports, reviews, setups, earnings also there.
- Move Hunt: research/bdi/moves/moves.csv (default branch). Bars: none in this container; Builder rebuilds cache after 16:00 (research/bdi/1104/DATA.md).
- No Alpaca bar GETs in market hours (shares the live runner's budget).

(Learned / failed / next — keep this current; it is your memory between runs.)

## Run 1 — 2026-11-09 ~08:00 ET (pre-market)
**Learned**
- Move Hunt library: `research/bdi/moves/moves.csv` (default branch), 50 movers/side/day x 2 sets (`all`, `tradable`), 10-29..11-05. Script `research/bdi/moves/moves.py`; bars at cov/days/D/bars.parquet (not in this container — no local bar cache, `data/` holds only universe.csv + marcoflow_export).
- 47% of tradable big movers start at the 09:35 decision; `config/default.yaml` no_entry_before=09:50 blocks them (pre-09:50 signals are journaled as shadow). Capture 5% (09:35 starts) vs 23% (later). 74% of 09:35 movers peak after 10:20.
- Already done, don't re-suggest: eu1103/open (existing setups started at 09:40/09:45 -> worse, 16 cfg), timeofday/NOTES.md section 3 (09:30-09:50 exploratory).
- Wrong-direction trades on tradable movers: 112 trades -85.5R vs +8.2R captured (selection-biased; descriptive).
- 70% of the `all` set movers are earnings-blackout names.
**Failed / caveats**
- 90-min move window caps extremes near 11:05, inflating "peaks after 10:20"; 11-05 crash day is 47/141 of the 09:35 rows.
**Next**
- ASSIGNED by Lead (lead-20261109-0758-5): short bursts + why longs lose on up days. Posted first takes (risk-share bursts as one bet; burst = GATE2 mirror; laggard-long hypothesis). Next run: measure (a) bad-burst timing vs SPY prior-15-min move, (b) up-day long R by name fromOpen - SPY fromOpen tercile. Needs live journals (find where they live).
- Check Builder's answer on move-left-at-09:50 + control (observer-20261109-0757-2).
- Find which setups own the wrong-side trades (needs live journals — locate the journal data branch / docs/live/leaderboard.json).
- Check whether Move Hunt ran for 11-06.

## Run 2 — 2026-11-09 ~09:45 ET (market hours, read-only)
**Learned**
- Live journals: journal.db at root of mcf-data (Primary), mcf-data-{testing,testing2,graveyard,gen,explore1,livelab}. `git fetch --depth=1 origin <b>; git show FETCH_HEAD:journal.db`. No price path inside; trades.pnl_adj / (|entry-stop|*shares) = R (as moves.py).
- Wrong-way trades on movers: 76% Graveyard+GEN, Primary ~0. Diffuse (~50 setups). Only family pattern: CWT14 failbrk-long = 21%.
- Guild standard (Lead 09:00): judge gates/filters on EXCESS t over matched control; lineage N in every result post.
**Failed**
- Morning "10:1 wrong-side" framing overstated it for the core book; corrected on the board.
- Laggard/leader long split blocked: needs 1-min bars; Alpaca GETs in market hours share the live budget -> wait for 16:00 / Builder's cache rebuild.
**Next**
- After Builder's cache rebuild: laggard-vs-leader split of up-day longs (name fo - SPY fo tercile), per account, excess vs SPY direction (Skeptic's standing ask).
- Read Builder's 09:50 measurement result; challenge the control choice if needed.
- moves.csv n_wrong 112 vs my 144 - reconcile (maybe accounts/journal timing).

## Run 3 — 2026-11-09 ~11:45 ET
**Learned**: long movers caught 14% (3/67 at 09:35); catchers are dip reversals (fromOpen -1.7%, RSI 23); typical missed mover is flat, near HOD, RSI 49 -> no near-HOD continuation long exists. Late longs after the top -23.2R (GEN). Lead logged run-2 result; CWT14 skip queued with Builder tonight.
**Failed**: nothing broke; caution n=21 caught, 6 days.
**Next**: (a) tonight/next: laggard-vs-leader split once Builder's fromOpen column lands; (b) check backlog for near-HOD/ORB long family N before Scout writes a rule; (c) read Builder's 09:50 measurement; (d) reconcile moves.csv n_wrong 112 vs 144.

## Run 4 — 2026-11-09 ~13:45 ET
**Learned**: late-buying is not a GEN trait. GEN longs never-worked = non-GEN (20.8%), but GEN gives back: 45% reach +0.5R, 31% of those close <= 0 (-168R = 49% of GEN long loss); `hold` exits worst. CWT14 longs = 5,148 trades / -708R (biggest long drain). GEN module source: research/generator/modules/<name>.py; registry.jsonl is hashed.
**Failed**: no bars -> mfe_r proxies only (peak-vs-stop order unknown); name parsing of GEN conditions is crude.
**Next**: (a) tonight: laggard-vs-leader long split on 2y from Builder's fromOpen column (check "cache up" note); (b) Builder's 09:50 measurement result; (c) reconcile moves.csv n_wrong 112 vs 144; (d) maybe: CWT14 long drain by account/regime — is it one variant or the family?

## Run 5 — 2026-11-09 ~15:45 ET
**Learned**: GEN rules recoverable: config/account_gen.yaml strategies.<name>.module -> research/generator/modules/*.py mask(df); gen.spec/gen.screen in yaml; geoms in mcf/research/generator/spec.py. GEN 2y screen does NOT predict live (Spearman valid -0.21; top tercile worst). Screen-to-live gap ~0.16R recurs (GEN, COMBO1-C3, MarcoFlow) -> asked whether lab costs are too light.
**Failed**: scipy not installed (use rank().corr()). genlate.py date cap added.
**Next**: tonight: read Builder's cache note + GATE2 / 09:50 results and be the outside voice; laggard-vs-leader 2y split from Builder's fromOpen column; watch for answer on lab-vs-live fill pairing; reconcile moves.csv n_wrong 112 vs 144.

## Run 6 — 2026-11-09 ~17:50 ET
**Learned**: tonight 0 of ~47 configs passed (09:50 continuation closed: gross ~0 per decile; laggard family 0/92 parked; GATE2 0/11 but pullback timing t 7-12 vs control; SC1 underpowered, longs lean +; NH1 0/8 = market direction; CWT14SKIP X1.5 passes bar but effect tiny). Skeptic: lab costs HEAVIER than paper (0.218R vs ~0.06R) -> screen-to-live gap is winner's curse. GEN feature tally: no condition carries w/o best day; drains = short-horizon momentum words; tight brackets worst.
**Failed**: genfeat meta filter bug (">=" contains "=") caught and fixed before posting.
**Next**: laggard-vs-leader 2y split if Builder's fromOpen column exists (check research/ on guild for name-minus-SPY fo); watch Skeptic's C1 verdict on GATE2 and argue for GATE2 x STOPW combo; reconcile moves.csv 112 vs 144.

## Run 7 — 2026-11-09 ~19:50 ET
**Learned**: BEREPLAY: BE hurts 27/27 families; mfe-based giveback overstates exit fixes ~10x (my GEN giveback framing was an upper bound, now measured). Cost thread: 71/91 setups lose BEFORE costs live; tight-stop quartile has favourable paper entries (-0.125R) vs lab +0.42R; STOPW volume = CWT14 (gross-negative), cost-killed = MF flow-sell, RW7, RW1, L3, NS4. Live Owner CF cost filter (Testing 1/2, 10-30) already exists. touch_fill = target exits.
**Failed**: first stopcost draft double counted (lab cost added on top of net that already holds paper cost); fixed before posting. Lesson: gross = net + paper cost, never net + lab cost.
**Next**: Skeptic's answer on tight-quartile favourable fills; GATE2 C1m verdict (my combo depends on it); Scout's HODSEP attack outcome (own-30m-return near HOD: connects to 'don't buy extension' + late-buying); laggard-vs-leader 2y split still owed (check Builder's cache column).

## Run 8 — 2026-11-09 ~22:30 ET
**Learned**: today's closes: CWT14SKIP (earnings), STOPW (85% size cut), HODSEP (look-ahead wrap bug). GATE2 timing survives C1m in ATR units but tiny (~0.02-0.03 ATR); rework = mid-day failed-hold exit. Owner standing focus 11-10: rolling compass / condition-based on-off (coil setups) — Scout taking it.
Extension split (live, 18 days): EXT not worse book-wide (NOT a remedy); loss sits in PB entries (59%, -0.177 gross); longs at fresh high +0.058 gross (only positive cell); shorts at fresh low -0.189; MF2/MF4/RW3 flow-sell shorts at fresh lows clearly worse.
**Data**: I now have 1-min SIP bars 10-06..11-06 for 1,522 traded symbols + SPY in /home/user/MCF/data/cache_hist/1Min (downloaded 22:00 ET via guild dl.py, 4 workers, ~3 min). Use for the laggard-vs-leader split (still owed) — now doable myself.
**Failed**: nothing broke; first scoring run ran >120s (move to background).
**Next**: laggard-vs-leader split of up-day longs (name fo - SPY fo tercile) on live trades with these bars; support owner's rolling-compass thread with a live-journal angle (setup R by midday SPY flip) once Scout posts the descriptive split.

## Run 9 — 2026-11-10 ~00:00 ET
**Learned**: GATE2 closed (rework gross negative; SPY-back-at-open exit hurts: SPY recovers too often). P1 now = owner's rolling compass (Scout RCOMPASS plan, Builder backfill, Skeptic audit). Skeptic's challenge held: 'longs at fresh high' = up-day + one day (11-06 = 82%), CWT12/14 75% -> withdrawn. MF fresh-low skip written as backlog entry; RW dropped (composition artifact).
**Failed**: twice now a family-level grouping misled me (RW3 vs RW3S). Lesson: always cut within setup before claiming a family pattern; and check best-day share before posting a positive cell.
**Next**: outside voice on rolling compass: from live journals, which setups lose most in afternoons after a morning-direction flip (descriptive, flip known at flip time; coil CWT12 first), to answer Lead's 'which setups does the owner most need switched off'. Bars on disk: data/cache_hist/1Min (10-06..11-06, 1,522 syms + SPY); need QQQ/IWM? check.

## Run 10 — 2026-11-10 ~02:00 ET
**Learned**: compass backfill up (17/17 fields match live code; Skeptic fix strict < re-tag pending); rolling-compass family N 2,605 (BAR90 3.57) -> realistic route = one standby rule + >= 20 forward shadow sessions. Live: only 1 F1/F2 flip day in 25 (11-02, -85R aligned post-flip); counter-to-morning afternoon trades on held days -95.5R/14 days; CWT12 coil fires mostly pre-noon (5 afternoon live trades) -> needs a morning condition.
**Failed**: non-unique index after pd.concat of journals duplicated rows in a join (5,156 > 4,682) -> fixed with ignore_index + assert. Lesson: always ignore_index when concatenating journals; assert counts.
**Next**: once Builder re-tags, look at coil_tagged by e_checkpoint (morning reading at entry) descriptively IF Scout doesn't (avoid duplicating a counted look: ask first); keep the outside voice on RCOMPASS results; laggard split now moot (long cell withdrawn) — drop it.

## Run 11 — 2026-11-10 ~04:00 ET
**Learned**: RCOMPASS stage 1 closed (coin flips); coil has no afternoon trades on 2y; MFFRESHLOW closed (0/2 on 2y). My counter-to-morning row had look-ahead (held_day = no flip all day) and vanishes ex-market -> withdrawn. Morning map script built; coil shows no consistent sign (TRAIN -0.030 / VALID +0.051).
**Failed**: (1) third claim undone by a control this week; adopted a pre-post checklist: label known at entry, within-setup cut, best-day share, ex-market. (2) Same-day contrast impossible for one-side families (one reading/day) -> between-day Welch. (3) Forking-path risk: my coil look touched COILAM's split before Builder's independent score; disclosed and counted.
**Next**: read Builder's all-family map if run; read COILAM result; keep looking for a positive GROSS edge source (Lead's standard) rather than more filters — maybe revisit what the Move Hunt says about precursors that are known at the decision bar (gap + rvol + sector) with ex-market framing.

## Pre-posting routine (adopted by the guild, Lead 2026-11-10)
Before posting ANY split, cell, or 'pattern':
1. **Label known at entry**: every class / state / day label uses only information available strictly before the entry
   (no 'held all day', no close-based day type in a rule, marks usable from T+1 min).
2. **Within-setup cut**: confirm a family pattern inside each setup; family pooling can be a mix artefact (RW3 vs RW3S).
3. **Best-day share**: print the best day's share of the total; > 50% = one-day record, say so.
4. **Ex-market**: remove beta x SPY move over the hold (and split up/down/quiet days); a raw split is often SPY direction.
Plus: concatenate journals with ignore_index and assert counts; gross = net + paper cost (never net + lab cost); count every look.

## Run 12 — 2026-11-10 ~06:00 ET
**Learned**: COILAM fails (my preview held); morning map chance-level -> compass on/off route empty on 2y; SIZEBKT: predicted size = noise; XA-PBO tool (read PBO as 'selection informative?', p_oos_loss as 'does the pick earn?'). Found a HISTORICAL earnings calendar on research-data (earnings_yf: 7,420 events 2y with surprise; earnings_cal: 33,554 rows) that the team believed did not exist.
**Next**: if Scout takes D1, help with the descriptive check (event-day direction from surprise x gap); else run D2's first number myself (premarket bars, outside market hours only).

## Run 13 — 2026-11-10 ~07:50 ET (pre-market, no data GETs)
**Learned**: D1 -> Scout (EVD1 frozen, N 858, waits for Builder's alignment table; AMC reacts next session); D3 -> Builder; D2 mine after 16:00. FLOW1-2Y closed. XA-EPROC: 20 sessions ~never confirms a realistic edge (power 0-19%); 40-60 needed -> Skeptic proposes success-line change (owner's call).
D2PM: plan frozen + pm_fetch.py (time-guarded) + d2pm.py (selftest ok). data/cache_hist/1Min holds RTH only, so premarket needs its own fetch into data/cache_pm.
**Failed**: day-demeaning bug (demeaned the signed product -> every day mean = global mean, t infinite); caught by the selftest. Lesson: demean the return per day, then sign; always include a planted-vs-null selftest.
**Next (after 16:00 ET)**: python ../guild/research/d2pm/pm_fetch.py 2026-09-24 2026-11-09 <syms> 3 (norm needs ~10 prior sessions; also extend RTH cache to 11-09 with dl.py for the 1,522 names: delete or re-fetch, since fetch() skips existing files!), then d2pm.py <earnings_yf>. Address Skeptic's audit first.

## Run 14 — 2026-11-10 ~09:45 ET (market hours: no data GETs)
**Learned**: earnings calendar aligned (AMC next session 5.7x normal gap); EVD1 mixed (VALID fade, TRAIN ~0) pending Scout's read; D3GEN: worst-quarter screen ranks live GEN (rho +0.24, p 0.037) -> forward-test hypothesis, no GEN change. D2PM family N 229 (BAR90 2.97). Added Skeptic's 3 reporting cuts (pm $vol + trade-count terciles, SPY day, --universe lab list).
**After 16:00 ET checklist**: (1) RTH bars: dl.py SKIPS existing files -> fetch 2026-09-24..2026-11-11 for union(1,522 traded + 102 lab extras) into a FRESH dir or move data/cache_hist/1Min aside first; (2) pm_fetch.py 2026-09-24 2026-11-11 union 3; (3) earnings_yf from research-data (scratch rd/); (4) d2pm.py rd/earnings_yf.parquet, then with --universe research/lab_symbols.txt; (5) post failures first; kill line.

## Run 15 — 2026-11-10 ~11:50 ET (market hours)
**Learned**: EVD1 closed (mixed, by Scout's own rule). FAMC = forward-only AMC fade shadow (no surprise; cap 0.40R; e-process). D3GEN: worst-quarter screen ranks but doesn't rescue. Plumbing: api.nasdaq.com blocked by the proxy here; live earnings snapshots (mcf-data/earnings/<day>.json, ±4 trading days, ~1,400 symbols) store dates only (no BMO/AMC) because mcf/data/earnings.py drops 'time'. Proposed housekeeping fix (A) to Lead.
**Next**: after 16:00 ET run D2PM per the checklist (run 14). If Lead picks (B) or (C) for FAMC and asks me, build the nightly row.

## Run 16 — 2026-11-10 ~14:15 ET (market hours; committed files only)
**Learned**: owner priority = COMPASS improvements (5/10-min glue; continuous conditional stats). Main-session COMPASS-5M: direction 5-90 min = coin flip for all 10 states; 5-min data predicts SIZE (vol clustering) both ways. My break: the rest-of-day hold rate is arithmetic (empirical-distribution benchmark, +0.4 pt, t 0.38); 'beats normal RW' = fat tails; compass adds ~1-2 pt (hint); prev-close side ~2.4 pt. Suggested a continuous calibrated line for the owner's card.
**Pattern across the guild**: intraday predictability we keep finding is SIZE/volatility (SIZEBKT, HODSEP rvol, COMPASS-5M) and close-SIDE arithmetic, never direction.
**Next (after 16:00)**: D2PM run (checklist run 14) + Alpaca news count for AMC coverage (Lead's ask, option C).

## Run 17 — 2026-11-10 ~16:00-17:00 ET
**Learned**: COMPCAL adopted my continuous line (beats cell table OOS, Brier VALID t -2.21); vol-scaled M1 pending. D2PM closed by its kill line (premarket direction doesn't beat the gap; size AUC 0.60). Option C viable: Alpaca news 16-20h rule catches 79% of AMC at ~91% precision, no live-code change.
**Failed**: (1) guild dl.py stop guard had expired (11-10 12:30 UTC) -> would have silently 'stopped' every symbol; made d2pm/dl_rth.py with a new guard. Always check a guard's date before reuse. (2) terc() crash on tiny event-day groups -> per-day guard. (3) background chain exit code 1 came from 'tail -2' on two files (use tail -n).
**Data on disk**: data/cache_hist/1Min = RTH 2026-09-24..11-10 for 1,623 names (traded live U lab list) + data/cache_pm premarket same span. Old cache deleted.
**Next**: if Lead wants FAMC via option C, write the nightly news-based calendar builder (point-in-time, 20:00 ET) for Scout's famc_shadow.py; otherwise outside voice on COMPCAL vol-scaled result.

## Run 18 — 2026-11-10 ~18:00 ET
**Learned**: Day-2 closes: D2PM, vol-scaled M1 (keep M1); COMPCAL M1 to owner as DECISION. Option C on full denominator: news-only precision 0.58 (Skeptic right; my 0.91 was a selected denominator). HYBRID (fresh evening earnings headline AND listed for D in live pre-open snapshot mcf-data/earnings/<D>.json) precision 0.887, recall 0.756 over 7 evenings. Yahoo earnings_yf: AMC after 11-02 are 'dmh' placeholders (stale fetch) -> unusable as reference/label for recent dates.
**Failed**: precision measured on a pre-selected denominator (only calendar names) — lesson: measure a classifier on the population it will scan live.
**Next**: if Lead/Scout say go, write research/evd1/famc_calendar_build.py (nightly ~20:00 ET, outside market hours, appends famc_calendar.csv with snapshot_at); else fresh direction sources with Scout (OPTFLOW pilot under way).

## Run 19 — 2026-11-10 ~20:00 ET
**Learned**: PVSCALE adopted for the SIZE line (alpha 0.8); close-side stays M1. OPTFLOW and NEWSDIR closed (direction already in the gap by 09:50). Hybrid approved; I built build_famc_cal.py; first row 11-10 = ALC, RGTI. The live job commits mcf-data state at day END (~14:3x ET) -> git commit times are never pre-open; use 'job HH:MM done D' subject + single-commit check.
**Duty**: nightly after 20:00 ET run build_famc_cal.py --date <D> (until someone else takes it); post the health line when reaction sessions close.
**Next**: 11-11 evening: build row for D=11-11; health line for 11-10 flags; outside voice on Scout's next direction source.

## Run 20 — 2026-11-10 ~22:00 ET
**Learned**: Day 3 effort shifts to execution/sizing on gross-positive setups (Lead). Cost-killed table (to 11-09): 17 setups; live paper cost ~1/3 of lab (0.065 vs 0.192R); only RW7-FD and RW1-FD positive w/o best day, and both only after 10-30 (Owner CF cost filter era = the 11-04/05 sell-off; shorts) -> filter and regime confounded. UNGAP closed (wrong sign). Builder's append_day.py feeds FAMC nightly. Skeptic's assert added (source nasdaq + complete, else UNBUILDABLE).
**Next**: 11-11 after 20:00 ET: build_famc_cal.py --date 2026-11-11; post health for 11-10 flags. Outside voice on Builder's limit-entry plan (missed-trade selection bias: limit fills skip the runaway winners — insist on reporting what missed trades would have earned).

## Run 21 — 2026-11-10 ~23:45 ET
**Learned**: LIMEX closed (limits adversely selected: missed +0.22R vs filled -0.07R) -> CONFIRM (stop-entry) next. Skeptic: RW7 lost -28.7R on 11-10, killing it as a survivor; RW1 thin. WHATWORKS: one row (RW1-FD in T2) clears all three checks. Wrote research/obs-synthesis/DAY1-3.md for the owner (Lead attaches to PR).
**Next**: 11-11 after 20:00 ET: FAMC calendar build for D=11-11 + health line for 11-10 flags; read CONFIRM plan/score with the ATR-first and whipsaw lens.

## Run 22 — 2026-11-11 ~01:45 ET
**Learned**: WHATWORKS lab join: every live survivor negative on 2y, a market-direction bet (down +0.08..+0.27, up -0.09..-0.32). BOTHDAYS: no all-weather setup; intercepts at chance -> beta-hedging won't harvest. CONFIRM plan frozen with Skeptic's volume-cut amendments (timing vs skip split). DAY1-3.md item 6 updated with the lab join.
**Next**: 11-11 after 20:00 ET: build_famc_cal.py --date 2026-11-11 + health line; read CONFIRM result (timing part, ATR first).

## Run 23 — 2026-11-11 ~04:15 ET
**Learned**: CONFIRM closed as entry; skip-part t 19 = path continuity. DISP1 closed. Live minute-10 check: untriggered = martingale after minute 10 (exit adds cost); triggered trades give back -0.03/-0.04 ATR after minute 10 (path-conditioned, flagged to Builder).
**Failed**: split-adjusted bars vs unadjusted live prices (SOXX 3:1 etc.) -> wild means; ALWAYS price-match bars to fills (3% guard) when joining journals to the cache.
**Next**: 11-11 after 20:00 ET FAMC calendar + health; read Builder's 2y minute-10 numbers.

## Run 24 — 2026-11-11 ~06:00 ET
**Learned**: minute-10 exit closed (2y martingale); my live 'triggered give back' did not replicate on 2y (window-specific). Skeptic checklist adopted (item 22 = my split guard). Horizon ladder: only weekly/monthly momentum (longhold S6) clears costs in the lab, thinly; live S6 -18.2% in 22 sessions, rebalance halted at -25% DD -> book frozen (flagged as owner question).
**Next**: tonight after 20:00 ET FAMC calendar for 11-11 + health for ALC/RGTI; outside voice on NEWSMID plan.

## Run 25 — 2026-11-11 ~07:45 ET (pre-open, no GETs)
**Learned**: Builder: rotating model book is ~7% BEHIND the frozen live S6 book (model_equity/te blank) -> owner FYI via Lead. NEWSMID frozen (scores 11-12).
**Posted**: MOMSIDE idea to Scout (intraday trades aligned vs counter to the name's 12-1 momentum decile; slow direction as an intraday condition; not in backlog).
**Next**: tonight after 20:00 ET: build_famc_cal.py --date 2026-11-11 + health line for ALC/RGTI.

## Run 26 — 2026-11-11 ~10:00 ET (market hours, no GETs)
**Learned**: owner priority REGSW (setup on/off): Phase 1 0/74; GAP-U survivor under Skeptic re-break (shared-day null). COILGAP closed. I wrote RCOMPASS v2 (PLAN_V2.md + rcompass_v2.py): post-flip vs not-yet-flipped (no future label), ex-market gross, shared-day permutation null, pass rule frozen; Builder runs tonight.
**Next**: tonight after 20:00 ET: FAMC calendar for 11-11 + health for ALC/RGTI; read RCOMPASS v2 output.

## Run 27 — 2026-11-11 ~12:30 ET
**Learned**: owner P1 = quality live reps faster (Scout levers, Builder calibrated replays, me verdicts). Verdict rules on excess (day x side removed) do no better than base (demote worse than base: excess mean-reverts over 5 sessions); EPROC silent in 26 sessions. ICC within setup-session ~0.185 -> a session ~4.8 effective trades, ceiling ~5.4: information scales with SESSIONS. Account renames (CLAUDE.md 11-11): On Deck = testing, Testing A/B/C = testing2/explore1/livelab.
**Next**: tonight after 20:00 ET FAMC calendar (11-11) + health for ALC/RGTI; read GAP-U re-break, REGSW-2, RCOMPASS v2 outputs. Outside voice on repv/fwdrep (read their NOTES) next run.

## Run 28 — 2026-11-11 ~15:45 ET
**Learned**: Lead adopted setup-day as unit. REPS1b/REPS2 lever ranking; Skeptic promo-luck (11% zero-edge pass, 40% for +0.10R at 20 sessions) -> two-stage promotion DECISION. Wrote research/obs-reps/MEMO.md for tonight's PR.
**Next**: after 20:00 ET FAMC calendar 11-11 + health for ALC/RGTI; read GAP-U re-break, REGSW-2, RCOMPASS v2, FWDCAL.

## Run 29 — 2026-11-11 ~15:45 ET (quiet board)
Pre-check for tonight's FAMC build: earnings/2026-11-11.json = one commit ('job 08:55 done 2026-11-11', committed 14:35 ET), source nasdaq,
complete true, 60 names listed for 11-11 -> passes the builder's asserts. Build at the first wake after 20:00 ET (21:40 ET run):
`python ../guild/research/obs-amcnews/build_famc_cal.py --date 2026-11-11` + health line for ALC/RGTI (reaction session 11-11).

## Run 30 — 2026-11-11 ~17:50 ET
**Learned**: RCOMPASS v2 (mine) closed 0/3 — post-flip aligned trades BETTER in VALID. GAP-U fails the shared-day null. REGSW-2: counter-state trades better, ~70% SPY reversion (ex-market t -3.05 < 3.57). PR #184 merged (memo + PROMO2 decision). FAMC session 1 run by Builder (2 events, +0.61R raw, K 1/1).
**Next**: next wake after 20:00 ET: build_famc_cal.py --date 2026-11-11 (pre-check passed) + health for ALC/RGTI.

## Run 31 — 2026-11-11 ~19:45-20:05 ET
**Learned**: market-state on/off thread CLOSED (Lead). PROMO2 middle option P>=0.80 (Skeptic). Unrated-39: ~40 setup-days/week from 25 rated (39.4 from 22 Gen); Gen screen per_day calibrated vs live (ratio 0.94). Testing A top-500 lever not visible in journals (pre-signal filter) -> needs FWDCAL replay.
FAMC: 11-11 row = CTVA, ENS, FNV; health 2/2 of 11-10 flags > 2x normal gap (3.9x, 3.2x).
**Next**: nightly FAMC build (after 20:00 ET) + health; read FWDCAL rule-21 result.

## Run 32 — 2026-11-11 ~21:40-22:10 ET
**Learned**: FWDCAL rule 21 FAILED (5-min ALL 0.694; exact-minute ALL 0.386). Live entry_time = broker fill clock;
decision->fill median 0.5 min (Primary/On Deck/Testing A), 0.73 Graveyard, 1.24 Gen. Exact-minute ceiling with one D =
modal offset share (pooled 0.578) and Builder's shares sit at it -> exact-minute miss is latency, not replay (obs-fillclock).
Suggested scoring on decision bar. Lead closed market-state thread; NEWSMID look runs 11-12.
**Failed**: FWDCAL books are not on mcf-guild, so per-trade replay offsets could not be checked directly (ceiling argument only).
**Next**: FAMC build for 11-12 after 20:00 ET on 11-12; repv/fwdrep/fastdec outside read; Gen fill-lag R cost (cheap, journals).

## Run 33 — 2026-11-11 ~23:40 ET
**Learned**: Scout's FILLCOST: order->fill ~2 s; my 'broker routing' wording WRONG -> corrected publicly. The decision->fill time is
decision->order created inside the poll (median 26-41 s, Gen 73 s). Entry drift vs decision price ~+0.04R in every account,
flat in lag (slopes mixed). Lead sending RULE21-DB (decision-bar matching) to the owner with Skeptic's guards; Builder
re-scores fresh 11-12..11-13. UNRATED14 ~7 days/week (Builder).
**Failed**: called a cause (broker latency) from a timing gap without splitting it into its legs first. Rule for me:
split any latency into legs (bar close -> decision -> order -> fill) using orders.created_at before naming the cause.
**Next**: FAMC build for 11-12 after 20:00 ET on 11-12; repv/fwdrep/fastdec outside read.

## Run 34 — 2026-11-12 ~01:40 ET
**Learned**: Lead accepted the latency corrections; meta-parse trap = checklist #33 (parse meta.split(';')[0]). Scout ICCSET:
per-setup ICC median 0.196, 10-90% 0.07-0.45, high-ICC 'survivors' have n_eff ~26-34. FWDCAL with live quotes: 5-min match
0.743 -> 0.869 (diagnostic); next lever halt timing. OBS-HALTFLIP: Graveyard -2R latch = two full stop-outs; 25/89 latches
within 0.10R of -2, 0 near-misses -> replay with slightly kinder stops skips latches (matches 182 replay-after-halt trades).
Gen account halt 120 -> 300R from 11-12.
**Failed**: first halt scan used regex 'daily_loss|loss_limit' and missed 'setup daily loss limit' / 'halted' (reported 0
Graveyard halt days). Rule: list the distinct skip reasons first, then categorise.
**Next**: FAMC build for 11-12 after 20:00 ET; repv/fwdrep/fastdec outside read.

## Run 35 — 2026-11-12 ~03:40 ET
**Learned**: Builder's halt lever: latch-minute feed lifts sel-window match to 0.903; Gen's early replay halt = sim broker
never rejects on buying power (101 extra trades). Skeptic/Lead: count-rule latch is owner's, not a replay fix (agreed, dropped).
ICCSET-2 shrunk table ready (tau 0.134). OBS-STOPSLIP: live stop slip +0.045R per stop-out, all accounts, = 0.012 + 0.34 x
spread/stop; Gen 'stop' exits include moved stops (trades.stop = original stop) -> raw means misleading.
**Failed**: first pass reported raw means (Gen -0.075R) before looking at the distribution; quantiles first next time.
**Next**: FAMC build for 11-12 after 20:00 ET; repv/fwdrep/fastdec outside read.

## Run 36 — 2026-11-12 ~05:40 ET
**Learned**: Builder's buying-power cap rejected by its own check; Gen early halt not BP-driven (moot at 300R). Lead: replace
sim stop slip with my spread/stop form, refit with Skeptic's side split. Refit: mean +0.059R, p95 0.20, p99 0.38, fit
-0.003 + 0.63 x spread/stop; window-unstable (sell-off 0.079 vs holdout 0.044). Scout ICCSET-3: group shrink targets
(CWT 0.10, flow 0.18, heat 0.39, GEN 0.07).
**Failed**: symmetric |slip| trim cut the adverse tail too (Skeptic's catch, checklist 34). Trim by direction relative to
the rule's mechanism, never symmetrically.
**Next**: FAMC build for 11-12 after 20:00 ET; repv/fwdrep/fastdec outside read.

## Run 37 — 2026-11-12 ~07:41 ET (pre-market, light)
**Learned**: Scout withdrew ICCSET-3 group shrink (groups drawn after seeing ICCs; out-of-time -2%); ICCSET-2 stays.
Lead: day-speed term only as ONE pre-declared variable. Housekeeping: Gen 7.8% of 'stop' exits are trailing winners
(+82R); stop_exit_share in live_status/daily_review overstated for Gen.
**Next**: after 20:00 ET: FAMC build for 11-12 + health; read the fresh rule-21 audit and NEWSMID one look as outside voice.

## Run 38 — 2026-11-13 ~23:05 ET (catch-up)
**Learned**: board silent 11-12 07:50 -> 11-13 23:10 (Skeptic resumed 23:10; my first pull had failed silently - check pull output). FAMC 11-12 built (8 flags); 11-13 UNBUILDABLE
(snapshot written by the 09:53 job). Health ratio 6/13 > 2x, but base on 292 known AMC = 74% > 2x (random 21%); headline
audit: 11/11 flags genuine releases -> precision intact, ratio is weak. Builder: my stop fit as replacement failed his
quintile check; max(sim, fit) proposed (pending Lead).
**Failed**: built a health line (open-gap ratio) without its base rate on known events first. Base rate before monitor.
**Next**: nightly FAMC (11-16 after 20:00 ET) + switch health to headline audit; read fresh rule-21 audit when it lands.

## Run 39 — 2026-11-13 ~23:40 ET
**Learned**: the 11-12..11-13 silence was an owner pause; guild restarted 11-13 ~23:00 ET with the UP-DAY / leveraged-ETF
blitz as main thread (Lead brief pending on the board). FAMC 11-12 rows built after reaction -> Builder's frozen check
rejects session 3; 11-13 unbuildable. NEWSMID FAIL (Scout; 46% of headlines follow the volume peak).
OBS-UPDAY-NULL: SPY up-day 55%; sign-so-far right 69% at open -> 80% at 11:00; return t->close ~0 in all 40 cells.
**Next**: score up-day tracks vs the null as they land; nightly FAMC 11-16 after 20:00 ET (build the same night or it is unscorable).
