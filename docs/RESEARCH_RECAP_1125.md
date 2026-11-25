# MCF research recap, 10-05 to 11-25

Educational only — not financial advice.

Every study so far, one line each: what it tested, and what came of it. Near-duplicates and nightly runs are merged.

**Backlog (1,144 ideas):** 468 parked, 314 rework, 226 idea, 38 testing, 26 lane-candidate, 23 holdout_failed, 14 finalist, 14 probation, 6 retired, 5 live, 4 forward_wait, 4 failed_locked, 1 holdout_passed, 1 proposed.

**Rule changes to keep in mind when reading live numbers:**
- 10-28: Primary position size ~$4k.
- 10-29: −2R per-setup daily stop in Primary.
- 10-30: cost filter in Testing 1/2.
- 11-11: TEAM-6 lineup in Primary.
- 11-12: LR8 cost model and the account restructure.
- 11-17: half-size testing lots; promotion hold.
- 11-19: C3 Epoch 1.
- 11-20: stop-rounding fix.
- 11-23: burst brake; ST7 out of Primary (4 setups left).

## Setups & discovery
| Study (date) | What it tested | Result |
|---|---|---|
| Literature review + setup screen (10-05/06) | Published intraday edges (ORB, noise band, VWAP and others), costs in. | ORB-5 and noise band off (−0.33R / −0.49R); orb20_a on (+0.021R, 443 trades). Adopted. |
| Heat score + layered swarm (10-06) | Re-weighted MarcoFlow heat score; layered overbought/oversold, VWAP and MA stacks. | heat_fade and exhaustion setups added to paper; dips-in-trend failed its test half. All later went to the Graveyard. |
| Apr–Jun holdout + finalists audit (10-07/08) | The 5 live setups on the locked holdout; 8 new finalists. | All 5 failed and were kept on probation (owner). 0 of 8 finalists confirmed. |
| MarcoFlow stacks (10-07/08) | Single metrics and MF/NS top-5 stacks. | Owner added MF1-5 / NS1-5 to Primary. Later shown to fail; most were demoted by 11-03. |
| 2-year re-score (10-09) | All live setups on 426 sessions of history. | Keep 0, rework 14, retire 9. Set up the 2-year history and the locked block. |
| Swarm 10-10 + testing staging | Variants, market-neutral, daily-bar, exit and sizing ideas. | Market-neutral 0 of 530. 15 setups (ST1-8, RW1-7) went to Testing; RW3/RW5/L3 descend from this line. |
| Chat with Traders catalog (10-12) | Setups described by podcast guests, coded as CWT families. | 19+ went to Testing 2; by 11-18 CWT14 was 37% of arena trades and losing. Most went to the Graveyard. |
| Weekend swarm + timeframes (10-17/19) | Rework of every family; 1/3/10/15-minute bars. | 0 quality setups; 0 of 640 timeframe configs. Near-misses went to Testing 2 as observation only. |
| Long-side hunts (10-12..11-21) | Dip, breakout, momentum and relative-strength longs. | 0 passed in every round (e.g. 0 of 367). Observation copies only. |
| Index / SPY dip ideas (10-15..11-17) | Index open-dip bounce, drop-rebound, morning-low turn, dip accumulation. | 5 index-dip setups added to Testing 1. Others failed; morning-low became the late-turn forward rule. |
| Setup Generator (10-19..10-28) | Machine-generated setups, 10 a day. | Paused 10-29. Now 10 of the top 20 front-runners, but all GEN trades total −1,222R. Restart approved 11-25 (10, then 5 a week). |
| Outside-idea mining (10-09..now) | Reddit, podcast, YouTube and paper ideas. | pod1022 0 of 464; rdt1030 0 of 137. The scouts now mostly feed the backlog. |
| Earnings reaction (10-11, 11-18, 11-19) | Trading after earnings gaps (EARN-GO). | Looked good on recent data (+0.35R) but failed the 2-year test (−0.070R). Closed by the owner 11-19. |
| Order flow (10-11) | Tape and aggression signals to time turns. | 0 of 240 positive after costs. |
| Variant swarms on live setups (10-20..11-03) | Parameter variants of the most-traded setups. | 0 of 287, 0 of 24, 0 of 15. A couple went to testing as owner exceptions. |
| Research Guild (11-09..11-18) | A daily team of small idea studies. | 77 ideas, 174 configs, 0 passes. Redesigned into targeted gap teams. |
| Usage items U4-U8 (11-18) | Longs, day-type cues, mechanisms, tunes, Graveyard revivals. | 1,418 configs, 0 passes; earlier-picked tunes later lost −45.6R. |
| Ultimate setup job (11-18/19) | 35 candidates for a high-volume edge. | None beat the benchmark. ETFDISP + 8 variants went to testing, later trimmed. |
| Beginner textbook setups (11-20) | 10 textbook setups + 8 session rules. | None beats the top 10. BEG-ORB and BEG-GNG admitted to testing. |
| Final-push consultant (11-21) | 128 configs over 6 tracks. | Nothing passed; April 2025 carried most "strong" lab edges. |
| Move Hunt MH4 (11-22) | Crypto names follow bitcoin; peer laggards. | Peer laggards beat random but lose after costs (−0.037R). |
| Project Pyramid (11-24/25) | The "ultimate 5" (3 long / 2 short), 7 teams. | ~70 configs, 0 reach the bar. Shortlist: L3-fromopen, GEN-261029-06, NM-ETF with a SPY gate. Round 3 running. |
| Ticker selection (11-25) | Do stock traits or past ticker results predict R? | No: traits keep their sign about half the time. Lead: L3 in high-ATR% stocks (+0.33R live). |
| BDI nightly runs (10-08..now) | Nightly autopsy, Move Hunt capture, small reworks. | Usually 0-18 configs a night, 0 passes; they feed most of the backlog. |
| Long-hold S6 (10-10) | Slow daily-bar strategies. | 12-1 momentum with a reversal filter is the only holdout-passed item; S6 paper since 10-12. |

## Exits & stops
| Study (date) | What it tested | Result |
|---|---|---|
| Exit / time-in-trade (10-06) | 489 exit rules on the 5 live setups. | Keep current exits; none passed. |
| Giveback programme (10-19, 11-19, 11-20) | Time cuts, trails, partials, profit locks, breakeven stops. | ~22,000 configs, 0 pass. Holding beats cutting at every checkpoint. |
| Stoplab (11-09) | Per-setup daily stop and stop width. | Per-setup choice is noise. Keep −2R and current widths. |
| RW3/RW5 wider target (11-19) | Take-profit 1.25× on the two gap-down shorts. | +0.044R per trade, t 2.58, 6 of 6 weeks up. Its watch-only test was deferred and never started. |
| NM-ETF burst stop (11-22/23) | Half stop on burst entries. | Halves the worst days. AV50 approved 11-24 for the Friday window. |
| SPY-exit copies (11-17) | Exit when SPY moves against the trade. | Running; needs 120 paired trades. |

## Risk & account limits
| Study (date) | What it tested | Result |
|---|---|---|
| −2R per-setup stop (10-22..11-25) | Whether the daily stop helps, and at what level. | In Primary since 10-29. No better than a random trim overall; hurts gap-down shorts. Per-setup rolling caps: no stable level. |
| Hard stop → scaled stop (11-23, 11-25) | −12R account stop, then a lineup-scaled stop + glitch failsafe. | −12R fires too often. HS-SCALE recommended; decision open. |
| Burst limits + burst brake (11-05/06, 11-23) | Limits on runaway bursts of entries. | Brake adopted 11-23; never binds in Primary. |
| L3 leash (11-10) | Market-based leash on Gap-Down Recovery Fade. | 0 of 12 pass; 2 run as watch-only tests. |
| Stacking caps (11-19) | Capping same-stock stacks. | Every cap costs the gap-down trio 13-21R; stacking kept. |
| Inverse-ETF short guard (11-19/20) | Skip shorting inverse/vol funds. | Promising (+55.9R live without 11-19); watch-only first. |
| Live-readiness LR1-LR8 (11-11) | Flatten timing, costs, kill switch, lot checks. | Adopted 11-12; LR6 (entry execution) "not now". |

## Sizing
| Study (date) | What it tested | Result |
|---|---|---|
| Primary sizing + $ vs R (10-28, 11-22) | ~$4k cap; why $ and R disagree. | Adopted. Half the gap is costs, half uneven $ risk. |
| Size-up / tiers (11-15..11-21) | Bigger size for strong setups. | Lost 33-47R on the test half; declined. |
| Half-size testing lots TSZ1 (11-16) | Half lots, 2× slots in testing. | Adopted 11-17. |

## Market regime / gates
| Study (date) | What it tested | Result |
|---|---|---|
| Regime / direction gates (10-09..11-12) | Switching setups on/off by market state. | All failed (e.g. 0 of 74, 0 of 112); 3 run as watch-only tests. |
| Market Compass + Hunch (11-05..) | Can models call direction or volume? | Direction is a coin flip; volume is predictable (67.7% vs 51%). |
| Time of day (10-09, 11-20, 11-24) | Entry-time costs and cut-off windows. | Time-of-day cost multipliers adopted; cut-offs weak; the fake-gap fix failed. |
| Day type / gap-up days (11-18, 11-23) | Protecting Primary on gap-up and quiet days. | 0 of 67 setups positive on gap-up days in both halves. Still uncovered. |

## Execution & costs
| Study (date) | What it tested | Result |
|---|---|---|
| Cost filter + BAR90 (10-29) | Skip trades whose costs eat 15%+ of the stop. | Adopted; about +0.04R per trade. |
| LR6 entry execution (11-11) | Best entry style per setup. | All per-setup rules failed; re-check due 11-27. |
| Execution leaks U9 (11-18/19) | Target fills, borrow rejects, stop rounding. | Fixes adopted (one leak was −65R). |
| Skipped signals / spread (11-18, 11-25) | Do the filters block good trades? | Skipped signals would have lost −2,211R. SPRD (11-25): a wider spread cap adds nothing after real costs. |
| Replay / backtest fidelity (10-29..11-19) | Replay vs live. | Replay matches 87% of live trades (target 98%). |
| Data quality / cost bug (11-21) | Cost basis, fills, journals. | Older records were under-costed; fixed to one basis. |

## Accounts / rotation / reps
| Study (date) | What it tested | Result |
|---|---|---|
| Playing time (10-12..11-05) | Starved low-activity setups. | Led to the testing accounts and low-rep homes. |
| Promotion standard (10-26..11-19) | Promote/demote rules. | Last week's rank doesn't predict next week's. C3-BAR2 adopted; promotion hold since 11-17. |
| TEAM-6 lineup (11-07..11-13) | Re-pick the Primary lineup. | Adopted 11-11; most of its R came from one day. Now 4 setups. |
| Rotation & reps (11-11, 11-25) | Is rotation giving setups reps? | Reps up (0.29 → 0.51); the spotlight added nothing and was stopped 11-25. |
| Graveyard / exits (11-18..11-25) | Kill and revival rules. | 0 revivals; losers keep losing. 12 retired 11-20; GYH adopted 11-25. |
| Workbench tunes (11-16/17) | One-change tuned copies. | 60 of 60 passed in-sample, then lost; 1 of 5 later passed. |

## Big reviews
| Study (date) | What it tested | Result |
|---|---|---|
| Outside consultant (11-18) | Whole-operation review. | Only the gap-down trio earns; C3 package adopted 11-19. |
| Crunch waves (11-18..20) | ~26,000 configs of "obvious fixes". | All failed except narrow items. |
| Root cause 11-19 | Why Primary lost that day. | ST7 indicator glitch + L3 shorting inverse ETFs; ST7 moved out 11-23. |
| Outsider pressure test (11-20) | Is there an edge at all? | Not yet: 28,097 trades at −0.125R. Clean rule epoch adopted. |
| What works / protect list (11-20) | What to protect from change. | Trio +73.4R but −9.7R without its 2 best days; protected. |
| QA + 4-week progress (11-21, 11-24) | Audit numbers; compare with 4 weeks ago. | Operations and efficiency better; profit not proven. |

## Possibly missed / worth a second look
1. **RW3/RW5 wider target:** the only exit idea that passed (+0.044R, t 2.58), deferred and never started.
2. **AV50 burst stop:** approved, still needs its log entry and a re-check after it goes live.
3. **HS-SCALE still open:** Primary has no automatic flatten for a disaster day or a glitch.
4. **LR6 entry-cost re-check is due now:** overlaps the spread study.
5. **Real signals not yet tried as setups:** L3 in very volatile stocks, peer-laggard picks, Hunch volume prediction.
6. **Adopted rules with weak replay evidence:** the burst brake and the −2R stop on gap-down shorts.
7. **Older forward tests never formally scored:** the split-tape short gate (10-14) and the cost filter (10-30).
8. **Smaller items:** S6 long-hold has no recent review; ODP2 still open.

## Still running
| Forward test | Pass bar | Due |
|---|---|---|
| NM-ETF frozen Primary test | t ≥ 2; positive without best day; best day < 50% | 25 sessions, by 12-31 |
| Compass gate (watch-only) | Blocked trades lose; gated beats ungated; best day < 50% | ~mid-December |
| Inverse-short guard (watch-only) | ≥ 10 sessions; blocked shorts lose; few setups worse | ~12-04 |
| L3 leash K11/K12 | Re-score at 20 sessions | ~12-09 |
| Regime switches (GAP-U etc.) | ΔR > 0 overall and on Primary's setups | ~12-10 |
| Dip-day log | Dip days beat other days, t ≥ 1.5 | 10 dip days (6 so far) |
| Late-turn rule | 20 signal days, t ≥ 1.5 | 0 signals so far |
| Rule epoch + Primary shadows | Paired comparison | Rolling (to 12-18) |
| Labelled live copies (Remedy-Q, BEG, ULT, WB) | 40+ paired trades over 5+ sessions | No fixed date |
| PRIM-ADD2 review | — | After the 11-27 close |
