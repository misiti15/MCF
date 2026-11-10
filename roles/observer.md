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
