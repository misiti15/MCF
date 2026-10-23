# Open items register (owner 2026-10-20: "difficult to ensure I can track all suggestions")

Every pending suggestion, follow-up evaluation or owner decision that is not answered the same night lives here
until it is closed. The 19:17 ET brief reads this file every night: items due today or overdue become numbered
DECISIONS; the rest are counted in one line ("Tracking: N open, next due ..."). Close an item by moving it to
"Closed" with the date and the outcome. Routines that create a future evaluation add a row here in the same commit.

**Decisions card (owner 2026-10-22):** the dashboard card "Your decisions" (top of docs/live/index.html) reads
`docs/live/decisions.json` (`[{code, title, what, recommend, numbers, why, link, status: open|answered, answered}]`,
schema guarded by tests/test_decisions_json.py). The nightly brief also refreshes docs/live/decisions.json: every
DECISION it raises is added as `open` (one plain-English line, the recommendation, 2-3 key numbers, the research note),
and every decision the owner answers is set to `answered` with the date and the answer, in the same commit as this file.

## Open

| ID | Item | Owner of the work | Monitored by | Due | Status |
|---|---|---|---|---|---|
| LL-1.5 | Per-setup daily stop: switch -2R to -1.5R? Replay (research/bdi/ll1020) said keep -2R; -1.5R was +41R better over 7 days but not significant. Re-score 1.5 vs 2 on each new session. | nightly loop (step 6c) | nightly FYI line, 10-21..10-23 | brief 2026-10-23 → DECISION | monitoring 2/3 sessions (10-21: −1.5R −0.43R vs −2R; 10-22: +24.33R, +19.5R of it the RW2-FD re-arm, see LL-LATCH; since 10-21 +23.90R; 7-day base +40.56R; 9 days +64.46R, t 2.36, bar 3.01) |
| LL-OPEN | Add an open-risk bound (realized + open lots at -1R <= -3R) on top of the -2R stop; fixes the 10-14 -32.8R overshoot. Needs a replay with slot effects first. | BDI | backlog idea | Saturday deep run 2026-10-24 | 2-year book test done 2026-10-22 (regime1022 Part B): -3R realized+open beats random thinning on Testing 1 but not on Testing 2 / Graveyard, keeps 35-49% of trades; not recommended (R2). R2 answered 2026-10-22: no new stop (owner); Saturday slot-effect replay only if the owner asks again |
| SO-CAP | Lift the live scale-out cap (Testing 2: 2/day). Scale-out worked live on BITO and COIN. | owner | — | when owner decides | waiting on owner |
| N3 | Move NS5-FD, ST4-FD, RW6G1-FD from Testing 1 to the Graveyard | owner | nightly suggestions | owner reviewing | waiting on owner |
| SO-ALLOC | If the 2/day scale-out cap stays: which signals get the 2 scale-outs (first-come spent both by 09:54 on 10-21). Backlog nightly-1021-scaleout-cap-allocation | BDI | backlog idea | with SO-CAP | idea |
| TWIN-GRP | First live check of the twin_group blocks (LD-NS1 / LD-ST2 / LD-SPXL, Testing 2): no LD signal yet (10-21, 10-22); NS3-T2 group (NS3V1 + NS3-FD) checked from 10-23 under OBS-1023 | nightly loop | step 1 | first LD signal day | pending |
| OBS-LD | 8 long near-misses (LD1-LD8, marked *) + M1 observation in Testing 2 from 2026-10-21 | nightly loop | leaderboard | first review 2026-11-04 (10 sessions) | live |
| OBS-POD | 3 pod1022 podcast setups (observation, did NOT pass the merit bar: best-day share high) in the Setup Generator account from 2026-10-26: GEN-POD1022-01 breadth thrust large caps, -02 breadth thrust index ETFs, -03 bull flag breakout or bailout (live exit = BE +0.5R + 10-min time stop unless +0.01R). 5 others not added (need VIX / daily ADX / 20-day levels / SPY VWAP / opening-range history / daily rvol live). research/bdi/pod1022/NOTES.md | nightly loop | leaderboard (Generated card) | first review after 10 sessions (2026-11-06) | added 2026-10-23, merge after 16:00 ET |
| LF-DECAY | Rolling 1/3/6/12-month decay monitor for top setups: 1-month decline → flag; 3- or 6-month decline (size decides) → demotion suggestion. For live funding. Draft in docs/ROADMAP.md Phase 5. | Claude | — | before live funding (needs ~1 month of records to start) | planned |
| UI-DASH | Dashboard upgrades (owner 2026-10-21): inventory guard test, leaderboard "Last session" columns, Replay columns + New setup pipeline card, At-a-glance strip / quick-nav / collapsible cards | Claude | tests/test_dashboard_inventory.py | 2026-10-22 08:00 ET | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr): guard test, Last session, Replay columns + pipeline card (replay.json / pipeline.json are stubs until the replay engine fills them), At a glance / quick-nav / collapsible cards |
| UI-DRILL | Setup drill-down side panel (click any setup: today / yesterday / record / daily R timeline, Prev/Next, #setup= deep link) | Claude | tests/test_dashboard_inventory.py | 2026-10-22 08:00 ET | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr); replay / backtest columns fill once replay.json / pipeline.json have data |
| UI-REGIME | Leaderboard "Best conditions" column + drill-down by-condition table (docs/live/regimes.json, regime1022) | Claude | tests/test_regimes_json.py, tests/test_dashboard_inventory.py | 2026-10-22 | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr); refresh regimes.json when setups move (scripts/make_regimes_json.py) |
| OPS-POLL | Testing 2 / Generated poll 2-3x less often (10-22: 157 / 126 polls vs Primary 379; gaps to 17.5 / 32.6 min): the lab-context cache key walked every polled symbol on every context-setup call (~70 ms x 10,000+ calls per 5-minute bar); slow polls phase-locked past the decision bars (Gen saw 2 of 63, T2 39 of 63; 47% / 36% of symbol decisions skipped). Fix: key once per poll + shared resample (no decision change), offline 5-minute poll Gen 346 s -> 100 s, T2 307 s -> 82 s. research/ops/pollspeed1022.md | Claude | poll log (research/ops/pollspeed1022_missed.py) | merge after the close / before 09:00 ET after owner review; check the first post-fix session | fix committed on claude/charming-mccarthy-i3rhhr, NOT merged (touches the live runner) |
| OBS-1023 | First sessions of the 2026-10-22 answers (effective 2026-10-23): ST7Q (Testing 1, needs the new qqq_vwap context: QQQ must be polled and the column non-NaN), NS3V1 (Testing 2, twin_group NS3-T2 with NS3-FD: check "twin held" skips), CWT14-failbrk-pdh-p10-short trading in the Graveyard with its Testing 1/2 record merged on the leaderboard | nightly loop | step 1 + leaderboard | brief 2026-10-23 | pending |
| PROMO-PDL | Primary watch: CWT14-failbrk-pdl-p10-lowvol-long (promoted 2026-10-21; Primary-only 24 trades -0.09R, -$162 to 10-22; 2-year backtest -0.095R) | nightly loop | nightly suggestions | first review 2026-10-27 | live |
| UI-DATE | Dashboard "date started" column | Claude | — | deferred | deferred |
| UI-LABEL | Setup labeling-system proposal | Claude | — | deferred | deferred |
| HK-LEDGER | Ledger check speed-up (replay only entries with a patch) | Claude | — | housekeeping | queued |
| HK-1 | Testing 2 bracket rejects | Claude | — | housekeeping | queued |
| HK-2 | Hard-to-borrow skip noise | Claude | — | housekeeping | queued |
| REPLAY | Live-test new setups on recorded sessions through the real live runner (mcf/replay, branch claude/replay-build). Pipeline: backtest -> replay (~50 recorded sessions through PaperRunner + simulated broker, costs in, trade-through limits) -> testing account -> primary. Replay vs live agreement tracked per setup and system-wide (docs/live/pipeline.json `agreement`, `drift` when |avg R gap| > 0.25R with >= 10 trades each). Validation numbers: research/replay/VALIDATION.md. Live poll inputs logged from the next session (live.log_poll_inputs; first day 2026-10-22 landed on all 5 data branches, 15.4 MB/day) so replays can be checked against what live actually received. Shipped: poll log, harness + CLI, validation (signals 98-99.9% matched; matched-trade R gap ~0), gap decomposition (5-bar gate drops 30-41% of lab signals), docs/live replay.json + pipeline.json. Open: Testing 2 replay speed (~18 min/session with today's config), 5-bar gate fix as a backlog idea, nightly export wiring. | Claude | nightly export (python -m mcf.replay export) | merge after the close (touches the live runner: poll log only) | shipped on branch claude/replay-build, awaiting merge |

## Closed

| ID | Item | Closed | Outcome |
|---|---|---|---|
| N1 | Demote MF3-open-flowsell-rsi5hi-FD | 2026-10-20 | kept on watch, then demoted by owner 2026-10-20 evening |
| N4 | CWT14-failbrk-orl longs | 2026-10-20 | all four moved to the Graveyard (owner) |
| M1 | Early Sellers into a Pop (index down, no gap up) | 2026-10-20 | yes — Testing 2, observation |
| LL-LATCH | Per-setup -2R stop latches for the day | 2026-10-22 evening | yes — risk.py setup_stopped, from 2026-10-23 (ledger 2026-10-22-setup-stop-latch) |
| D1 | CWT13-vwapstretch-z05-short Testing 2 → Graveyard | 2026-10-22 evening | yes — moved, from 2026-10-23 |
| L1 | LD1 / LD2 longs | 2026-10-20 | yes — with LD3-LD8, Testing 2, observation |
| MOVES-1020 | Owner moves 2026-10-20 evening (2 promotions, MF3-FD demotion, CWT09-g5 + 4 CWT14 orl to Graveyard) + Testing 1/2 reallocation | 2026-10-20 | applied for 2026-10-21 (ledger 2026-10-21-*) |
| L3-1 | Gap-Down Recovery Fade (all day) L3-gap-slope-fromopen-FD | 2026-10-22 | demoted Primary -> Testing 1 for 2026-10-23 (owner); CWT14-failbrk-pdl-p10-lowvol-long stays in Primary, review 10-27 (row PROMO-PDL) |
| N5 / R3 | Demote NS3-failed-vwap-reclaim-short-FD | 2026-10-22 | demoted Primary -> Testing 2 before the 10-22 open (owner); variant research NS3-VAR requested |
| N6 | CWT14 failed prior-day-high break shorts | 2026-10-22 | p05-lowvol (T1) and p10-lowvol (T2) moved to the Graveyard (owner); p10 (T1) stays — rework study CWT14-PDH-RW |
| N2 | Demote RW6G1-ns2-up3-vwap2sd-short | 2026-10-22 | demoted Primary -> Testing 1 before the 10-22 open (owner); its -FD variant stays in Testing 1 |
| LL-2R | Per-setup daily stop ruling | 2026-10-20 | keep -2R (research/bdi/ll1020/NOTES.md); 1.5R re-check = LL-1.5 |
| GY-1 | Graveyard account first session | 2026-10-21 | clean: 50 polls, 347 trades (mgy- orders), flat, EOD + scorecard pushed, journal = report = status (research/bdi/nightly1021/NOTES.md) |
| S1 / ST7-RW | RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day) (ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD) | 2026-10-22 | yes (owner ~11:10 ET) — new Testing 1 setup next to its parent ST7-FD (keeps running), new lab context column qqq_vwap (live == frame on 26,802 of 26,834 QQQ bars), from 2026-10-23; ledger 2026-10-22-st7q-testing1. ST7-RW study done (60 configs) |
| V1 / NS3-VAR | Big Loser VWAP Reclaim Fade, Morning, Wide Stop (NS3V1-am-widestop-short) | 2026-10-22 | yes (owner ~11:10 ET) — new Testing 2 setup before NS3-FD, twin_group NS3-T2 on both (one symbol held by only one of them), from 2026-10-23; ledger 2026-10-22-ns3v1-testing2. NS3-VAR study done (95 configs) |
| P0 / CWT14-PDH-RW | Move Failed Prior-Day-High Break Short (0.1 ATR) (CWT14-failbrk-pdh-p10-short) to the Graveyard | 2026-10-22 | yes (owner ~11:10 ET) — off in Testing 1, on in the Graveyard from 2026-10-23 (10-22 trades stay in Testing 1); leaderboard shows one row, Account = Graveyard, record = Testing 1 + Testing 2; ledger 2026-10-22-graveyard-cwt14-pdh-p10. Rework study done (0 of 47 pass) |
| G1 / R1 | Add the 6 up-tape gated short variants (-g1) / R1 withdraw G1 | 2026-10-22 | R1 yes (owner ~11:30 ET): G1 withdrawn, the 6 -g1 variants are never added (prior-day SPY lookahead; corrected t 0.04-2.17 vs bar 3.78); ledger 2026-10-22-owner-replies-r1-r2 |
| OBS-1022 | First session of the 10-22 morning moves (NS3-FD Primary → Testing 2, RW6G1 Primary → Testing 1, CWT14 pdh p05-lowvol + p10-lowvol → Graveyard) and of the live poll-input log | 2026-10-22 | clean: each traded only in its new account (NS3-FD T2 6 trades; RW6G1 base 0 signals, rare; pdh lowvol shorts GY 13 + 14); twin held worked (P 6, T1 3, GY 12); polls/2026-10-22/ on all 5 branches, 15.4 MB (research/bdi/nightly1022/NOTES.md) |
| R2 / R3 | regime1022: R2 no new daily stop for Primary; R3 demote NS3-FD | 2026-10-22 | R2 yes (owner ~11:30 ET): no new stop; -20R account stop and -2R per-setup stop in the testing accounts stay; B1b cap not adopted. R3 = N5 (demoted 2026-10-22) |

Educational only — not financial advice.
