# Low-rep rotation 2026-11-04 (owner): Explore 1 + Live Lab

Owner 2026-11-04: both new paper accounts (Explore 1 `mx1-`, Live Lab `mll-`) are homes for setups with low or no live
trade history, to give them reps. Keys added 11-04; both accounts trade from the **2026-11-05** session. Re-evaluated
every ~2 sessions (separate scheduled task). Setup Generator stays paused; Gen keeps its own setups.
Ledger: `2026-11-04-lowrep-explore1-livelab`. Paper results. Educational only - not financial advice.

## Rule used
- Candidates: every setup enabled in Testing 1 or Testing 2 with **< 20** live trades, or in the Graveyard with **< 10**
  live trades (owner addition 11-04), counted across ALL accounts (journal.db on mcf-data, -testing, -testing2,
  -graveyard, -gen; `trades` run_id=1; pulled 2026-11-04 ~14:50 ET, so 11-04 is partly counted).
- Excluded: Primary setups, GEN-* setups, and setups mid-observation by owner decision:
  - `RW3S-gapdn-flowsell-short-FD` (Testing 2, 5-session observation from 11-03; 46 live trades anyway)
  - `CWT14-failbrk-pdl-p05-R2A-long` (39 live) / `CWT14-failbrk-pdl-p05-R2A-short` (11 live) (Testing 2, PDL-1a R2A legs from 11-02)
  - `ST4-emadn-long-am-t1s05-FD` (Graveyard since 11-04, 15 live trades: not < 10) - stays in the Graveyard. No Graveyard setup qualifies.
- Split: balance expected trades/session (lab rate: `exp_per_session` from the INACT audit, `mcf/report/playing_time.expected_rates`
  - two-year lab with the 5 busiest days out, config notes, idxdip1015 / swarm notes), keep long/short mixed and put
  twins / family members in different accounts (IDX1 trail vs hold, CWT04 a15 vs a25, CWT05 variants, NM1-cwt09 vs CWT09
  vwaploss-g10, each LD twin_group pair LD-NS1 / LD-ST2 / LD-SPXL, LD / ST / NM-RW families alternated).
- 42 setups move: **21 to Explore 1, 21 to Live Lab**; 12 from Testing 1, 30 from Testing 2 (6 + 15 each).

| Account | Setups | Expected trades/session (lab) | Live trades/session so far (old account) | Long / short |
|---|---|---|---|---|
| Explore 1 | 21 | 26.1 | 5.8 | 11 / 10 |
| Live Lab | 21 | 25.7 | 6.0 | 11 / 10 |

Live rates run far below lab rates for most of these (LAB-RATE-PARITY: 0.00-0.50x), so expect a few trades a session per account at first.

## The list
| Setup | Id | From | To | Live trades so far | Expected trades/session (lab) | Live trades/session (old account) | Side |
|---|---|---|---|---|---|---|---|
| Index Dip Bounce 2 3x S&P | `IDX2-spy075-0945-3x-trail` | Testing 1 | Explore 1 | 0 | 0.01 | 0.00 | long |
| Index Dip Bounce 1 TQQQ (hold) | `IDX1-qqq100-0955-TQQQ-hold` | Testing 1 | Explore 1 | 0 | 0.02 | 0.00 | long |
| Index Dip Bounce 5 3x S&P | `IDX5-spy050-0945-3x-trail` | Testing 1 | Explore 1 | 0 | 0.04 | 0.00 | long |
| * Oversold EMA Cross-Down with Breadth Turning Up (near-miss) | `LD4-st4-breadthup-t1s05-long` | Testing 2 | Explore 1 | 0 | 0.05 | 0.00 | long |
| * SPY Dip of 0.30%, Breadth Turn (SPXL, trailing) (near-miss) | `LD8-spy-dip030-breadthturn-spxl-holdtr-long` | Testing 2 | Explore 1 | 0 | 0.16 | 0.00 | long |
| * Oversold Slope Turn after an SPY Dip-Turn (near-miss) | `LD3-st2-idxturn-t05s1-long` | Testing 2 | Explore 1 | 0 | 0.17 | 0.00 | long |
| * Oversold Pop with Breadth Turning Up (near-miss) | `LD1-ns1-breadthup-t05s1-long` | Testing 2 | Explore 1 | 0 | 0.31 | 0.00 | long |
| Big Gainer Fade with VWAP Band Guard | `RW6G1-ns2-up3-vwap2sd-short` | Testing 1 | Explore 1 | 4 | 0.40 | 0.10 | short |
| Gap-Down VWAP Loss Short, Slope Filter (near-miss) | `NM1-cwt09-g10-vwaploss-short` | Testing 2 | Explore 1 | 4 | 0.50 | 0.31 | short |
| Backside VWAP-Test Short (big runner) | `CWT04-backside-vwaptest-a25-short` | Testing 2 | Explore 1 | 0 | 0.56 | 0.00 | short |
| Monday Weak-RS NS3 Short (near-miss) | `NM-RWN5-ns3-mon-weakrs-short` | Testing 2 | Explore 1 | 7 | 0.69 | 0.54 | short |
| Quiet Downtrend Bounce Short (near-miss) | `NM-AMS-N1-quiet-morning-short` | Testing 2 | Explore 1 | 1 | 0.83 | 0.08 | short |
| Early NS3 Short While SPY Up (near-miss) | `NM-RWN3-ns3-spyup-early-short` | Testing 2 | Explore 1 | 6 | 0.91 | 0.46 | short |
| ST8-volspikedn-long-pm-t1s1-FD | `ST8-volspikedn-long-pm-t1s1-FD` | Testing 1 | Explore 1 | 11 | 1.05 | 0.61 | long |
| RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day) | `ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD` | Testing 1 | Explore 1 | 6 | 1.25 | 0.67 | long |
| Early Sellers, Mid-High RSI | `MF2-open-rsimidhi-flowsell` | Testing 2 | Explore 1 | 5 | 1.30 | 0.17 | short |
| Gap-Down Bounce Rejection Short (10% gap) | `CWT09-gapdn-bounce-g10-lowerhalf-short` | Testing 2 | Explore 1 | 17 | 1.38 | 0.94 | short |
| NS2 Up-3 Short, QQQ Up, Slope Down (near-miss) | `NM-RWR4-ns2-up3-qqqup-slopedn-short` | Testing 2 | Explore 1 | 5 | 1.50 | 0.38 | short |
| Backside Lower-High Short | `CWT04-backside-lh-a15-short` | Testing 2 | Explore 1 | 4 | 2.85 | 0.22 | short |
| Panic Flush Reversal (5x volume) | `CWT05-flush-m05-v5-long` | Testing 2 | Explore 1 | 7 | 2.93 | 0.39 | long |
| Stretched Below VWAP Bounce (far) | `CWT13-vwapstretch-z075-long` | Testing 2 | Explore 1 | 16 | 9.23 | 0.89 | long |
| Index Dip Bounce 1 TQQQ | `IDX1-qqq100-0955-TQQQ-trail` | Testing 1 | Live Lab | 0 | 0.02 | 0.00 | long |
| Index Dip Bounce 3 3x S&P | `IDX3-spy075-0955-3x-trail` | Testing 1 | Live Lab | 0 | 0.02 | 0.00 | long |
| * Oversold Slope Turn with Breadth Turning Up (near-miss) | `LD5-st2-breadthup-t05s1-long` | Testing 2 | Live Lab | 0 | 0.07 | 0.00 | long |
| * SPY Dip of 0.2 ATR, Breadth Turn (SPXL, trailing) (near-miss) | `LD6-spy-dip020atr-breadthturn-spxl-holdtr-long` | Testing 2 | Live Lab | 2 | 0.24 | 0.18 | long |
| Backside Lower-High Short (big runner) | `CWT04-backside-lh-a25-short` | Testing 2 | Live Lab | 0 | 0.36 | 0.00 | short |
| * Shallow Nasdaq Dip, Breadth Turn (TQQQ) (near-miss) | `LD2-qqq-dip015-breadthturn-tqqq-t05s1-long` | Testing 2 | Live Lab | 4 | 0.37 | 0.36 | long |
| Prior-Day Low Sweep Reversal to VWAP | `LIQ-pdl-sweep-open15-vwap-long` | Testing 1 | Live Lab | 1 | 0.38 | 0.06 | long |
| * Oversold Pop after an SPY Dip-Turn (trailing) (near-miss) | `LD7-ns1-idxturn-holdtr-long` | Testing 2 | Live Lab | 1 | 0.42 | 0.09 | long |
| ST5-pdbrkup-short-mid-t05s1-FD | `ST5-pdbrkup-short-mid-t05s1-FD` | Testing 1 | Live Lab | 2 | 0.78 | 0.11 | short |
| Early NS3 Short While QQQ Up (near-miss) | `NM-RWR3-ns3-qqqup-early-short` | Testing 2 | Live Lab | 4 | 0.83 | 0.31 | short |
| Gap-Down Reclaim Fade, Afternoon (near-miss) | `NM-PM-gapdn-above-pdh-rvol-short` | Testing 2 | Live Lab | 2 | 0.93 | 0.15 | short |
| Late-Day ETF Dip Buy (near-miss) | `NM-ETF-late-dip-di-long` | Testing 2 | Live Lab | 8 | 1.10 | 0.62 | long |
| ST6-volspikeup-short-mid-t1s1-FD | `ST6-volspikeup-short-mid-t1s1-FD` | Testing 1 | Live Lab | 6 | 1.24 | 0.33 | short |
| Gap-Down VWAP Loss Short (10% gap) | `CWT09-gapdn-vwaploss-g10-short` | Testing 2 | Live Lab | 11 | 1.29 | 0.61 | short |
| ST3-rsi5up-short-pm-t1s1-FD | `ST3-rsi5up-short-pm-t1s1-FD` | Testing 1 | Live Lab | 2 | 1.35 | 0.11 | short |
| Afternoon Exhaustion Short, Gap-Down, SPY Up (near-miss) | `NM-RWR1-exh150-gapdn-spyup-pm-short` | Testing 2 | Live Lab | 1 | 1.36 | 0.08 | short |
| Panic Flush Reversal (deep, 5x volume) | `CWT05-flush-m075-v5-long` | Testing 2 | Live Lab | 4 | 1.37 | 0.22 | long |
| NS2 Short, SPY Up 0.5%, Not Friday (near-miss) | `NM-RWN4-ns2-spyup05-notfri-short` | Testing 2 | Live Lab | 8 | 2.11 | 0.62 | short |
| Panic Flush Reversal (deep, 3x volume) | `CWT05-flush-m075-v3-long` | Testing 2 | Live Lab | 14 | 3.31 | 0.78 | long |
| Spike-Pullback Flag Breakout | `CWT12-flag-s1-long` | Testing 2 | Live Lab | 17 | 3.37 | 0.94 | long |
| Backside VWAP-Test Short | `CWT04-backside-vwaptest-a15-short` | Testing 2 | Live Lab | 7 | 4.76 | 0.39 | short |

The 7 INACT2 setups (IDX1 trail, IDX1 hold, IDX2, IDX3, IDX5, LD4, LD5) are all in the list (split so IDX1 trail / hold and LD4 / LD5 do not sit together).

## Rule / config context (owner rule 2026-11-02)
- Moved setups trade with the new accounts' settings from 11-05: ~$1,000 lots (200 slots x buying power 2.0), max 10 lots
  per setup, cost filter 0.15R on, no live scale-out, no twin block, full universe. In Testing 2 they traded the UNI1
  top-500 pool on 11-04 only (ledger 2026-11-03-uni1-testing2-top500); Testing 1 shorts had the split-tape short gate.
  So records from 11-05 are a new segment; never mix them with the Testing records without saying so.
- Testing 1 keeps 13 setups, Testing 2 15 (UNI1 trial continues there with fewer setups).
- Leaderboard: their setups show with an "Explore 1" / "Live Lab" tag; a setup that came from the Graveyard would stay
  off (`no_leaderboard` in docs/live/assignments.json; none today). Daily post: the two accounts' totals are left out
  (today card, P/L chart, last sessions, quick facts); their setups can still be a top setup of the day.

## Wiring checked
trade.yml / watchdog.yml / eod.yml matrix entries (key- and setup-gated), data branches `mcf-data-explore1` /
`mcf-data-livelab` created by the trade job on first run, session-guard coverage, CAP1 load reducers unchanged
(research workflows in the `mcf-research` group; trade.yml untouched by them), dashboard / assignments / report labels,
nightly inactive check covers both branches (skips a branch with no journal yet).
