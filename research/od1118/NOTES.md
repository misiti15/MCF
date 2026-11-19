Educational only — not financial advice.

# Owner decisions 2026-11-18 (~19:45 ET) — what was built

Built after the close on `claude/charming-mccarthy-i3rhhr` in one PR (opened, **not merged**: several items touch
Primary's live path, so rule 27's skeptic review comes first; setup-freeze needs a merge outside 09:30-16:00 ET).
Background: research/crunch/WAVE1.md, research/usage/SUMMARY_1118.md, research/graveyard_review_1118/,
research/usage_review_1118/PLAN.md, research/reps2/. Costs in everywhere; no locked-block read; no new scored test
except the pre-set GY exemption check (0 tuned configurations).

**Rule changes around these numbers (ledger):** 10-28 sizing; 10-29 latch + BAR90; 11-12 LR3/LR8 cost batch + REPV;
11-16 ROT1; 11-17 TSZ1 testing half size, promotion hold, shadow mode, 15 WB copies; 11-18 GY-BENCH, SRCV1, recorded
quotes; **from 11-19** C3 Epoch 1 (C3-NS5, C3-EXIT100, C3-ROT, ...) and everything below.

## Runtime / Primary-affecting changes (need the skeptic review)
| Code | Change | Files | Affects |
|---|---|---|---|
| DQ-P4 | Reconcile exports each lot's entry fill; the runner merges it into `_fill_px`, so open marks (`open_r`, poll mtm) and the Primary −20R halt's open term use the fill | mcf/execution/reconcile.py, mcf/execution/runner.py | all accounts' marks; Primary halt input |
| U9-TGT | `live.skip_passed_at_quote: true` — skip an entry already at/through target (fill side) or stop (exit side) at the quote; `u9_skip` + quote side logged in journal info and the quote log | config/default.yaml, mcf/execution/runner.py | every account incl. Primary |
| U9-ETB | `shorts.borrow_prefetch: true`, `borrow_refresh_min: 60` — one bulk shortable/ETB list; one ETB skip row per setup/symbol/day | config/default.yaml, mcf/execution/alpaca_broker.py, mcf/execution/runner.py | every account incl. Primary (same trades expected) |
| DQ-P3 | `with_cost_r` re-costs pre-11-12 rows with LR8 (`cost_r_lr8`) in every report | mcf/costs.py | reports only (live_status status file, brief, review, dashboard build); runner latches untouched |
| UNIT1 | account R next to trade R (status `today.account_r` / `since_start.account_r`, brief scorecard line, dashboard) | mcf/report/live_status.py, mcf/report/c3score.py, docs/live/index.html | display only |
| GY-ARCHIVE-20 | 18 Graveyard blocks `enabled: false` + `archived` marker (bench window dropped); `archived` popped as an account-side key | config/account_graveyard.yaml, mcf/strategies/setups.py | Graveyard only |
| REPS2-LANE | Testing A `shadow_setups_from: research/reps2/fastlane/lane.json` (25 setups, shadow only) | config/account_testing2.yaml, mcf/execution/shadow.py, research/reps2/fastlane.py | Testing A shadow book only |
| ROT2 | caps only above 5% resource skips (none today), rare setups never benched | config/default.yaml, mcf/rotation.py, docs/live/arena_resources.json | arena accounts (no GEN/CWT14 benched from 11-19) |
| RT-UNCAL | `uncalibrated_weight` 0.2 → 0 | config/effective_sessions.json | effective-session display |
| DQ-P1 / DQ-P2 | corrected what-if in the review; since-start $ without the MTUM glitch | mcf/report/c3score.py, mcf/report/daily_review.py, mcf/report/live_status.py, docs/live/index.html | reporting |

## DQ-P4 — is the fill the more conservative choice? Yes
1,441 Primary lots 10-06..11-18 (journal orders × trades): the fill was worse than the signal reference on 66% of lots,
by +0.041R on average. Marked at each lot's exit price, the fill-based open R sums to −41.6R vs +17.1R signal-based and
is lower on 28 of 32 days. So fill-based marks read lower → the −20R halt trips earlier, never later. Bookings unchanged.

## GY-ARCHIVE-20 — owner exception check
Thresholds set before computing (research/od1118/gy_exempt.py, one pass): HIGH volume = whole record >= 15 trades per
active session; BIG-DAY cluster = >= 3 sessions at >= +10R that together make >= +40R. Both → exempt.

| Exempt (kept, KEEP-TESTING) | trades / session | days >= +10R | their R | day types | whole record |
|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-long | 51.5 | 4 | +54.8R | 3 up, 1 quiet | 1,390 tr, −145.1R |
| heat_fade_short-FD | 32.6 | 5 | +86.3R | 3 down, 2 quiet | 848 tr, −85.0R (hindsight up-day −0.61R vs down +0.16R) |

Both are big-day-cluster setups a day-type switch (Market Compass) could turn on/off later; they still lose overall, so
they stay in the Graveyard (resting under GY-BENCH to 11-24). Near misses archived: CWT14-orl-p05-lowvol (48.3/session,
2 big days +41.2R), LIQ-orl (15.1/session, 2 big days +28.4R), CWT14-pdl-p05 (39.9/session, 2 big days +30.0R).
**Archived (18):** RW2-exhaustion-noon-adv150-short-FD, LIQ-orl-sweep-open15-s25-long, CWT14-failbrk-orl-p10-lowvol-long,
CWT14-failbrk-orl-p10-long, CWT14-failbrk-orl-p05-lowvol-long, heat_fade_long-FD, ST2-slope20up-long-am-t05s1-FD,
CWT14-failbrk-pdh-p05-lowvol-short, CWT14-failbrk-pdh-p10-lowvol-short, CWT14-failbrk-pdh-p10-short,
CWT13-vwapstretch-z05-short, CWT09-gapdn-vwaploss-g5-short, CWT12-coil-k6-long, CWT12-coil-k4-long,
CWT14-failbrk-pdl-p05-long, CWT14-failbrk-pdl-p05-lowvol-long, RW4-ns3-adv150-short-FD, heat_fade_short.
3 were running (CWT13-z05-short, CWT09-vwaploss-g5, RW4-FD); 15 were benched to 11-24 and now stay off.

## Reading checks (owner: "fine as long as it offers no conflicts to other setups or limits other trading exposure")
- **Gen cap = 6 GEN per arena account per session (C3-ROT):** with ROT2 it applies only where an account's resource
  skips exceed 5%. Current regime (11-17..11-18): On Deck 0.5%, A 1.4%, B 2.4%, C 0.8%, D 0.2%, E 0.8%, F 0.9%,
  Gen 1.0% → **no cap binds; no GEN setup is benched from 11-19.** Slot use: Gen peak 53% of 300 slots on 11-17 (the
  GEN-261022-09 burst) and 35% on 11-18; testing accounts 6-29%; **0 buying-power skips** in any arena account. A cap only
  ever benches GEN setups themselves (it frees slots, never takes them from others), so it cannot limit other setups'
  exposure. Without ROT2 it would have benched 25 GEN setups on 11-19 (A 5, Gen 6, C 3, B 4, D 3, F 4) for no gain.
- **Active days = enabled sessions:** docs/live/arena_reps.json counts a setup's active days from the per-session setup
  snapshots (enabled that session; benched / away / family-capped sessions excluded), so a rotation never charges a
  setup a session it could not trade (tests/test_c3_epoch_rot_score.py).

## Other answers
- **W3-PSHADOW (yes, after On Deck):** rule 34(a) + CLAUDE.md. The mechanism already exists (Primary `shadow_setups`,
  mcf/execution/shadow.py `only` mode). Nothing configured: no candidate has finished its On Deck stage (promotion hold).
- **WB2 / WB2-OVERLAY: HELD** (rule 36).
- **TAGS1:** research/tags1 (rules.json frozen 2026-11-18, tags1.py nightly post-close tagger, score.py refuses before
  20 fresh sessions / 2026-12-17). Not run on a live session yet (first fresh session 11-19).
- **W4-FRAME:** docs/BESPOKE_ENTRY_RULES.md (rule 30). **STOP2:** rule 26 with evidence lines. **ENG1-A:** rule 31.
  **W6-PBO:** rule 33 (the PBO line + try-count t column land in the Wave 2 Friday packet).
- **USAGE1:** research/usage_review_1118/APPLY_1118.md (lean cadence + Guild as targeted gap teams); task edits by the
  parent session.
- **RW7:** keep; re-evaluate after the close of 2026-12-01 (8 more sessions), OPEN_ITEMS RW7-REEVAL.
- **GEN-261019-04:** KEEP (119 trades, +8.8R); monitor row restored in OPEN_ITEMS.
- **W2-HK-GEN09:** research/od1118/GEN09.md.
- **RT-NS5:** keep the move. **RT-EARN:** EARN-GO held until one 2-year earnings-season test. **WBQ1, W3-NOGUEST:** rules
  noted (no config change: current guests go home 11-25 as scheduled).

## WB4 — the explanation the owner asked for (no change made)
`L3-gap-slope-rsi5hi-FD-WB4` is a Workbench COPY of the On Deck setup Gap-Down Rebound Overbought Short
(L3-gap-slope-rsi5hi-FD), running in Testing B since 11-17 (owner "yes to all 15 WB copies", 11-16). It differs from its
parent in three ways: it skips thin-R names (1R must be >= 20x the stop-exit cost), it needs RSI(5) <= 90, and slope <= 1.0.
Two things make it a question:
1. It was built before the C3-WB rule (at most 2 changed parts per copy) — it has 3.
2. Since 11-19 the same parent also has WB5 (refire off) in Testing C, which passed C3-WB5's split check. ODPREP says ONE
   Workbench tune per setup, so the parent now has two tunes running.
Record so far: 3 trades, −0.46R, 1 traded session — far too few to judge. Options: (a) keep both copies as separate
setups with their own testing (matches the owner's WB2 answer: copies are new setups with their own testing), or
(b) stop WB4 to respect one-tune-per-setup and the 2-part limit. Nothing changes until the owner chooses.

## Not done here
- The ledger joint-portfolio check (`python -m mcf.research.ledger check`) could not run here: no stored bar cache in this
  session (IndexError on an empty symbol list). It needs a session with data/cache; the new entries carry no setup-logic patch
  except the 18 archive `enabled` flips (Graveyard) and config flags.
- Scheduled-task edits for USAGE1 (parent session). The Wave 2 Friday packet (PBO / try-count t) is not built here.
