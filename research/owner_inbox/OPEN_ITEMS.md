# Open items register (owner 2026-10-20: "difficult to ensure I can track all suggestions")

Every pending suggestion, follow-up evaluation or owner decision that is not answered the same night lives here
until it is closed. The 19:17 ET brief reads this file every night: items due today or overdue become numbered
DECISIONS; the rest are counted in one line ("Tracking: N open, next due ..."). Close an item by moving it to
"Closed" with the date and the outcome. Routines that create a future evaluation add a row here in the same commit.

## Open

| ID | Item | Owner of the work | Monitored by | Due | Status |
|---|---|---|---|---|---|
| LL-1.5 | Per-setup daily stop: switch -2R to -1.5R? Replay (research/bdi/ll1020) said keep -2R; -1.5R was +41R better over 7 days but not significant. Re-score 1.5 vs 2 on each new session. | nightly loop (step 6c) | nightly FYI line, 10-21..10-23 | brief 2026-10-23 → DECISION | monitoring 1/3 sessions (10-21: −1.5R −0.43R vs −2R; 7-day base +40.56R) |
| LL-OPEN | Add an open-risk bound (realized + open lots at -1R <= -3R) on top of the -2R stop; fixes the 10-14 -32.8R overshoot. Needs a replay with slot effects first. | BDI | backlog idea | Saturday deep run 2026-10-24 | 2-year book test done 2026-10-22 (regime1022 Part B): -3R realized+open beats random thinning on Testing 1 but not on Testing 2 / Graveyard, keeps 35-49% of trades; not recommended (R2). Saturday: slot-effect replay only if still wanted |
| SO-CAP | Lift the live scale-out cap (Testing 2: 2/day). Scale-out worked live on BITO and COIN. | owner | — | when owner decides | waiting on owner |
| N2 | Demote RW6G1-ns2-up3-vwap2sd-short from Primary to Testing 1 | owner | nightly suggestions | owner reviewing | waiting on owner |
| N3 | Move NS5-FD, ST4-FD, RW6G1-FD from Testing 1 to the Graveyard | owner | nightly suggestions | owner reviewing | waiting on owner |
| G1 | Add the 6 up-tape gated short variants (-g1: MF4-FD, RW5-FD, MF3-FD, RW7-FD, RW3-FD, RW1-FD) to a testing account (research/bdi/gates1021) | owner | nightly suggestions | brief 2026-10-21 | waiting on owner; **regime1022 recommends withdrawing (R1): lookahead bug in prior-day SPY, corrected t 0.04-2.17** |
| N6 | Move the 3 Failed Prior-Day-High Break Shorts (CWT14-failbrk-pdh-p05-lowvol-short, -pdh-p10-short in T1; -pdh-p10-lowvol-short in T2) to the Graveyard | owner | nightly suggestions | brief 2026-10-21 | waiting on owner |
| SO-ALLOC | If the 2/day scale-out cap stays: which signals get the 2 scale-outs (first-come spent both by 09:54 on 10-21). Backlog nightly-1021-scaleout-cap-allocation | BDI | backlog idea | with SO-CAP | idea |
| TWIN-GRP | First live check of the twin_group blocks (LD-NS1 / LD-ST2 / LD-SPXL, Testing 2): no LD signal yet | nightly loop | step 1 | first LD signal day | pending |
| OBS-LD | 8 long near-misses (LD1-LD8, marked *) + M1 observation in Testing 2 from 2026-10-21 | nightly loop | leaderboard | first review 2026-11-04 (10 sessions) | live |
| PROMO-1021 | Promoted to Primary 2026-10-21: L3-gap-slope-fromopen-FD, CWT14-failbrk-pdl-p10-lowvol-long (backtest negative: watch) — Primary-only record | nightly loop | nightly suggestions | first review 2026-10-27 (5 sessions) | live; regime1022: L3-FD keep as is, no gate qualifies; back to Testing at the review if below break-even |
| LF-DECAY | Rolling 1/3/6/12-month decay monitor for top setups: 1-month decline → flag; 3- or 6-month decline (size decides) → demotion suggestion. For live funding. Draft in docs/ROADMAP.md Phase 5. | Claude | — | before live funding (needs ~1 month of records to start) | planned |
| UI-DASH | Dashboard upgrades (owner 2026-10-21): inventory guard test, leaderboard "Last session" columns, Replay columns + New setup pipeline card, At-a-glance strip / quick-nav / collapsible cards | Claude | tests/test_dashboard_inventory.py | 2026-10-22 08:00 ET | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr): guard test, Last session, Replay columns + pipeline card (replay.json / pipeline.json are stubs until the replay engine fills them), At a glance / quick-nav / collapsible cards |
| UI-DRILL | Setup drill-down side panel (click any setup: today / yesterday / record / daily R timeline, Prev/Next, #setup= deep link) | Claude | tests/test_dashboard_inventory.py | 2026-10-22 08:00 ET | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr); replay / backtest columns fill once replay.json / pipeline.json have data |
| R1-R3 | regime1022 decisions: R1 withdraw G1 (lookahead), R2 no new daily stop (alt. B1b insurance), R3 demote NS3-FD (= N5) | owner | nightly suggestions | brief 2026-10-22 | R3 answered (= N5, demoted 2026-10-22); R1/R2 waiting on owner |
| UI-REGIME | Leaderboard "Best conditions" column + drill-down by-condition table (docs/live/regimes.json, regime1022) | Claude | tests/test_regimes_json.py, tests/test_dashboard_inventory.py | 2026-10-22 | shipped 2026-10-22 (branch claude/charming-mccarthy-i3rhhr); refresh regimes.json when setups move (scripts/make_regimes_json.py) |
| NS3-VAR | Thorough variant study of Big Loser VWAP Reclaim Fade (all day) to work in more market conditions (owner 2026-10-22) | BDI | research/bdi/ns3var1022 | brief 2026-10-22 | running |
| UI-DATE | Dashboard "date started" column | Claude | — | deferred | deferred |
| UI-LABEL | Setup labeling-system proposal | Claude | — | deferred | deferred |
| HK-LEDGER | Ledger check speed-up (replay only entries with a patch) | Claude | — | housekeeping | queued |
| HK-1 | Testing 2 bracket rejects | Claude | — | housekeeping | queued |
| HK-2 | Hard-to-borrow skip noise | Claude | — | housekeeping | queued |
| REPLAY | Live-test new setups on recorded sessions through the real live runner (mcf/replay, branch claude/replay-build). Pipeline: backtest -> replay (~50 recorded sessions through PaperRunner + simulated broker, costs in, trade-through limits) -> testing account -> primary. Replay vs live agreement tracked per setup and system-wide (docs/live/pipeline.json `agreement`, `drift` when |avg R gap| > 0.25R with >= 10 trades each). Validation numbers: research/replay/VALIDATION.md. Live poll inputs logged from the next session (live.log_poll_inputs) so replays can be checked against what live actually received. Shipped: poll log, harness + CLI, validation (signals 98-99.9% matched; matched-trade R gap ~0), gap decomposition (5-bar gate drops 30-41% of lab signals), docs/live replay.json + pipeline.json. Open: Testing 2 replay speed (~18 min/session with today's config), 5-bar gate fix as a backlog idea, nightly export wiring. | Claude | nightly export (python -m mcf.replay export) | merge after the close (touches the live runner: poll log only) | shipped on branch claude/replay-build, awaiting merge |

## Closed

| ID | Item | Closed | Outcome |
|---|---|---|---|
| N1 | Demote MF3-open-flowsell-rsi5hi-FD | 2026-10-20 | kept on watch, then demoted by owner 2026-10-20 evening |
| N4 | CWT14-failbrk-orl longs | 2026-10-20 | all four moved to the Graveyard (owner) |
| M1 | Early Sellers into a Pop (index down, no gap up) | 2026-10-20 | yes — Testing 2, observation |
| L1 | LD1 / LD2 longs | 2026-10-20 | yes — with LD3-LD8, Testing 2, observation |
| MOVES-1020 | Owner moves 2026-10-20 evening (2 promotions, MF3-FD demotion, CWT09-g5 + 4 CWT14 orl to Graveyard) + Testing 1/2 reallocation | 2026-10-20 | applied for 2026-10-21 (ledger 2026-10-21-*) |
| N5 / R3 | Demote NS3-failed-vwap-reclaim-short-FD | 2026-10-22 | demoted Primary -> Testing 2 before the 10-22 open (owner); variant research NS3-VAR requested |
| LL-2R | Per-setup daily stop ruling | 2026-10-20 | keep -2R (research/bdi/ll1020/NOTES.md); 1.5R re-check = LL-1.5 |
| GY-1 | Graveyard account first session | 2026-10-21 | clean: 50 polls, 347 trades (mgy- orders), flat, EOD + scorecard pushed, journal = report = status (research/bdi/nightly1021/NOTES.md) |

Educational only — not financial advice.
