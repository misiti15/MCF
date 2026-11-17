# scout notes

(Learned / failed / next - keep this current; it is your memory between runs. Run-by-run history: roles/scout_log.md.)

## State (2026-11-15 run 56, Sunday ~11:15 ET)
- Guild P1 = quality live reps faster (owner 11-11). Direction work only on a named new rule / new data (Lead).
- Owner rules to remember: direction research anchored AFTER ~09:50 (reference = 09:50 state + 09:30-09:50 range); testing arena
  = Testing A-F + Gen treated as one; account names Primary / On Deck / Testing A-F / Gen / Graveyard.
- Queued (Builder runs, Monday 11-16 after 16:30 ET, in order): FWDCAL fresh 11-16..11-17 -> MOMSIDE -> SIZESTOP (my plan, D1)
  -> DIPTURN (my plan). Half days dropped; LR8 basis; MDE printed; journal timing guard on.
- Mine due: 11-18 after 16:30 ET REPS3 score + ICCSET refresh (commands in Next). FAMC nightly runs (Builder); my famc_shadow
  reader is block-safe via guild_read.py (verified identical on 11-12).
- Guild standards I must apply: checklist (research/SKEPTIC_CHECKLIST.md, now ~43 items), every close prints 'nothing above MDE;
  smaller unknown' (research/SCOUT_MDE.md), pooled ratio estimator not per-day bin means (#39), half days dropped (#42),
  locked block never requested or loaded (#43: guard block in every fetch script; read via research/guild_read.py).

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
- (11-11..11-15) Live journals: setup-day is the unit (ICC ~0.19; per-setup 0.07-0.45, shrink toward pooled 0.19 by own se;
  a post-hoc grouping failed its time holdout). Journal meta strings carry outcome-linked suffixes (';touch_fill'): parse the
  JSON prefix only. LR8 (11-12) moved live pnl_adj to a new cost basis: put every trade on one basis
  (scripts/recompute_pnl_adj.py) before crossing 11-12. Journals are final only >= 10 min after the last 16:0x push.
- (11-11..11-15) Direction: every up-day / market-state track matched the null (index continuation after any reading ~0;
  scale-outs raise the median but lower the mean; published intraday momentum gone post-2018). Index-level tests only exclude
  large effects; trade-level tests exclude down to ~costs. Plan with power in mind (MDE) before spending a look.
- (11-11..11-15) Vendor news timestamps lag the market (46% of analyst-action events peak in volume > 5 min before created_at):
  check stamp lag on a sample before any intraday-news plan. Alpaca also serves corporate actions (v1/corporate-actions).
- Caches with extended hours: on half days the 'afternoon' is after-hours; detect half days by SPY afternoon/morning volume
  < 0.2 (research/halfday_clean.py). Alpaca multi-name fetches > 30 min: run with a start index in parts, background.

## Failed / closed (mine; each with its MDE in research/SCOUT_MDE.md where scored)
- Day 1-3: QP1, SC2, SC1, NH1, STOPW, HODSEP, RCOMPASS-1, COILAM, SIZEBKT, EVD1 (mixed -> FAMC shadow), OPTFLOW, NEWSDIR, UNGAP.
- 11-11..11-15: BOTHDAYS (0/74 all-weather), DISP1, COILGAP, NEWSMID, LEAD20, ETFTIER, SHORTUP, SIZETREND, ANCHOR950 (null
  table), IMOM. Withdrawn: ICCSET-3 group prior (post hoc; failed time holdout).
- Useful outputs kept: REPS1/1b lever table (Gen halt + buying power the only good blocks; borrow virtual-only), REPS2 slot yield
  (median 2.7 setup-days/week; p_day = 1 - exp(-0.193 x lab trades/day)), REPS3 frozen forecast (482.8/week), ICCSET-2 shrunk
  table (LR8 basis), COMPCAL950 display line (owner option), FILLCOST (latency ~free).

## Next
- (11-17 03:20) Shortlist: A3 side x miss-reason counts in; B marked weak (stop-charge parity). Final after 11-18.
- (11-17 01:30) Shortlist A detailed (Move Hunt: 62% blackout; ~13/day other movers, 14% caught, 80% start < 10:00). A2 needs per-decision rows (moves.py rows.parquet) or a Session replay. Use GLOSSARY names (Live / Shadow / Session replay / 2-year backtest).
- (11-16 23:30) Monday closed: MOMSIDE (t 0.96, up-day cell, FWD reverses), SIZESTOP (my D1: conditioning ~0), DIPTURN (mine: t 0.92).
  Lead's ask: shortlist of 2-3 next studies from the backlog after 11-18 (ranked by setup-days or Move-Hunt capture; family N,
  BAR90, MDE; ex-market control up front). Draft: research/shortlist/DRAFT.md (A capture gap, B cost-per-R, C spotlight rotation).
- (11-15 21:10) Standard (Lead/Skeptic): if refresh.py refuses an account for a quiet day with no commit after 15:55 ET, WAIT or name the account in the post; never loosen the threshold or use --allow-stale for a scored run. Board quiet until Mon 16:30 ET.
- (11-15 19:20) refresh.py: session-day commit must be >= 15:55 ET (pre-close commit refused). Order: Mon MOMSIDE/SIZESTOP/DIPTURN, Tue FWDCAL, Wed REPS3.
- (11-15 17:20) refresh.py refuses future sessions, accepts later commits; score.py --end excludes later sessions (Skeptic's FWDCAL hole). Monday order (Lead fix): MOMSIDE -> SIZESTOP -> DIPTURN on 11-16; FWDCAL on 11-17.
- (11-15 15:15 ET) Lead: nothing more until Monday's scores (all readings pre-registered; Builder's scorers print Skeptic's audit items, verified fa05e86f9). Lab/live disagreements or red flags go to the board and Lead first; nothing is re-scored.
- (11-15) SIZESTOP / DIPTURN carry a pre-registered reading table (end of each PLAN.md): read Builder's results against it.
- 11-16/17: read Builder's FWDCAL, MOMSIDE, SIZESTOP and DIPTURN results; answer anything about SIZESTOP / DIPTURN (my plans).
- 11-18 after 16:30 ET: `python3 -I research/reps3/refresh.py /home/user/MCF <scratch>/jr18 2026-11-18` (refuses non-final
  journals), then `python3 -I research/reps3/score.py <scratch>/jr18 research/reps3/forecast_setups.csv --end 2026-11-18`, then the ICCSET LR8
  commands at the end of research/iccset/NOTES.md (header 'LR8 basis, all trades'). Post realized vs forecast + shrunk table.
- New fetch script? Copy the checklist-#43 guard block; new cache reader? use research/guild_read.py; bar cache? halfday_clean.py.
- Direction ideas only with a named new rule or new data, frozen, powered (MDE stated), one look. Untested sources left:
  overnight futures (not on Alpaca), Hunch, borrow/short-interest data, intraday halts (no Alpaca endpoint).
