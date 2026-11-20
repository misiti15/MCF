# Protected list (WW-PROTECT)

Educational only — not financial advice.

Owner decision **WW-PROTECT, 2026-11-20** ("YES"): the things that work in MCF are protected by an **evidence gate, not a
freeze**. Any of them may still be changed, but only with the evidence named in its "Change guard" column, the owner's
approval, the Friday epoch window for anything in Primary (rule 25), and a per-setup report of how many setups improve and
how many get worse (Remedies rule, owner 2026-11-05).

Source and full evidence: `research/whatworks_1120/REPORT.md`, section 2 "Protected list" (ordered by strength, then by
impact on Primary). Owner answer: `research/owner_inbox/2026-11-20.md` "Owner answers — What works decisions".

## The gate (enforced by `tests/test_protected.py`)

Every entry in `research/ledger.jsonl` dated **2026-11-21 or later** whose patch keys, title, `moves` or `setups` touch
a protected item (a config key or setup name in the table below, or a listed term in the title) must carry:

- `protected_ids`: the PROT ids it touches, e.g. `["PROT-01"]`;
- `guard_evidence`: the path (in the repo) of the evidence that meets that item's change guard;
- `owner_approval`: who approved and when, e.g. `"owner 2026-11-28 (chat)"`.

Matching is deliberately simple:

- a dotted config key (`live.max_spread_bps`) matches a patch key that is that path or starts with it (an account
  suffix such as ` (testingd)` is fine), and the title when it names the key or its leaf (`max_spread_bps`);
- an undotted key with an underscore (`max_stop_cost_r`) matches any patch-key segment of that name and the title;
- a setup name matches only as a whole name in patch keys, title, `moves` and `setups` (a Workbench copy `NAME-WB3`
  is a different setup and does not match);
- any other term (`C3-BAR2`, `promotion hold`) matches as whole words in the title (case-insensitive).

A false match is fixed by adding the three fields, never by weakening the list.

## Table

Columns "Keys / terms" and "Setups" are what the test matches on (backticked, comma-separated; `—` = none).

| ID | Area | What to protect | Keys / terms | Setups | Strength | Change guard |
|---|---|---|---|---|---|---|
| PROT-01 | Protective rule | `max_spread_risk_frac 0.25` on the live SIP quote (G1, LW4, EX7) | `live.max_spread_risk_frac` | — | strong | Blocked-signal replay over >= 20 Primary sessions, spread in, at or above the taken average without the best day, with most setups improving. Tightening it goes to the backlog |
| PROT-02 | Execution | Order identity and booking: deterministic coid, lot-aware reconcile, newest-first paging (EX4) | `coid`, `reconcile` | — | strong | Reconcile and paging tests pass, plus one replayed session per account with submitted = booked, 0 duplicates and journal P/L = Alpaca |
| PROT-03 | Execution / ops | Flatten at min(15:55, close - 5m), LR7 retries, HK-FLAT adoption, session guard (EX5, OPS-7) | `session.flatten_by`, `session.flatten_lead_min`, `HK-FLAT`, `session guard` | — | strong | Fire drill on every account plus one clean live session. Half days (11-27) checked at 12:55 the first time |
| PROT-04 | Research pipeline | Costs-in scoring at every stage; volume sources stay in the arenas (PIPE-7) | `costs.live_model`, `costs.slippage_per_share`, `costs.stop_slippage_per_share`, `cost haircut` | — | strong | Measure later-live yield (n >= 15, avg > 0, w/o best day > 0) of at least ~10% before expanding a volume source. Never drop the cost haircut |
| PROT-05 | Protective rules | Earnings blackout +-4d, no entry before 09:50, inverse guard, universe cap (G9) | `universe.earnings_blackout_days`, `live.no_entry_before`, `universe.max_symbols`, `universe.stocks_in_play_top_n`, `inverse guard` | — | strong (that they are unmeasured) | A same-signal lab backtest with the guard on and off, costs in, held-out sessions and the configuration count |
| PROT-06 | Primary setup | L3-fromopen's layers as they are: gap <= -2.657, sma20 slope > 0.3724, fromOpen > 3.46, t1s1, min_adv 0, no spread/ADV floor (P4, F1, PIPE-1) | — | `L3-gap-slope-fromopen-FD` | moderate | No filter or gap widening unless the excluded slice is positive w/o best day in both Primary and Testing. The gap > -5 / ATR >= 5 gates go to the backlog as Workbench copies |
| PROT-07 | Primary book | The three core seats, judged on full tenure under the epoch rule (P1, PD5, PIPE-8) | — | `RW3-gapdn-rsi5pop-flowsell-short-FD`, `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`, `L3-gap-slope-fromopen-FD` | moderate (core) / weak (robustness) | Demote or tune only if full-tenure avg <= 0 and w/o best day <= 0 over >= 15 active days, or on the -10R-since-admission trigger. Paired against BASE1, and showing the effect on the three-setup book |
| PROT-08 | Primary timing | Keep the FD window rather than narrowing back to backtest windows; the money is earned before 13:00 (P5, PIPE-3) | `FD window` | `RW3-gapdn-rsi5pop-flowsell-short-FD`, `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`, `L3-gap-slope-fromopen-FD`, `ST7-rsi50dn-long-pm-t1s1-FD` | moderate | No narrowing to a backtest window. A 13:00 cut-off is a backlog remedy (see WW-REMEDY-Q) and is re-checked after LR1 |
| PROT-09 | Families | The "extension" entry conditions: RSI(5) > 80 in RW3/RW5, fromOpen recovery in L3 (F1, PIPE-2) | — | `RW3-gapdn-rsi5pop-flowsell-short-FD`, `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`, `L3-gap-slope-fromopen-FD` | moderate / weak | Paired comparison on the same sessions, >= 40 trades and >= 10 sessions, with both avg R and w/o-best-day R not worse, reporting every family member |
| PROT-10 | Families / stops | Do not narrow short stops; keep CF and U9-TGT where they run (F5) | `live.skip_passed_at_quote`, `max_stop_cost_r`, `short stops` | — | moderate | Net and gross R by stop tercile, per setup, on later sessions only |
| PROT-11 | Execution | Broker-held stop legs, plus the 11-20 rounding direction (EX2) | `stop legs`, `soft stops` | — | moderate | Recorded-quote evidence, per setup, with tail figures (p99, count beyond 0.5R). No soft or polled stops |
| PROT-12 | Execution | Market order with bracket on the deciding poll, SIP feed (EX1) | `data.feed`, `entry order` | — | moderate | Forward test on recorded quotes, net of missed fills. Re-measure on the first real-funds sessions |
| PROT-13 | Ops | Restore halt and latch state at restart; successor-job hand-over (EX6) | `HK-HALT-RESTART`, `live.max_job_minutes` | — | moderate | Restart drill showing restored state = pre-restart state, plus >= 98% of decision minutes polled |
| PROT-14 | Promotion | C3-BAR2 (15 active days, shrunk > 0, best-day share < 50%), the promotion hold, live testing before Primary (PIPE-5, F6, PIPE-4) | `C3-BAR2`, `promotion hold` | — | moderate | Back-test the proposed bar on the 12 promotions and 5 Generator graduates: hit rate > 1 in 3 and w/o best day > 0 in Primary |
| PROT-15 | Research pipeline | Strict swarm design: pre-declared grids, train/valid split, cost haircut, random baseline, plateau and both-halves gates, finalist cap (PIPE-1) | `swarm design` | — | moderate | A new route must show yield >= the swarms' on later live trades before it replaces them |
| PROT-16 | Research pipeline | Off-live sources get 0 ranking weight; holdouts scored once and reported, not a hard gate (PIPE-4) | `src_value`, `SRCV1` | — | moderate | src_value rule passes: Spearman CI low > 0 and sign-hit CI low > naive, on >= 8 setups |
| PROT-17 | Families | Failed families (CWT14, MF open flowsell, Generator ORB-fail, heat-fade, NS2/NS3) return only through a mechanism change (F6) | `family revival` | — | moderate | A mechanism change (not a parameter tweak) plus a split check on later sessions only |
| PROT-18 | Promotion | Demotion is a move; a setup returns only on live evidence (LW1, PD1, PD2) | `re-promotion` | — | moderate / weak | Return requires n >= 50, w/o best day > 0, best-day share < 50%, judged against the same-day arena base, not zero |
| PROT-19 | Protective rule | `max_spread_bps 30` (G3, LW10, SPREAD-5) | `live.max_spread_bps` | — | moderate | Replay charging at least the recorded spread, >= 20 sessions, w/o best day above Primary's taken average |
| PROT-20 | Protective rule | ETB-only shorts (G5) | `shorts.require_easy_to_borrow` | — | moderate | Locate and borrow-fee modelling plus a >= 30-session Primary replay |
| PROT-21 | Brakes | Primary -2R latch (cost R) and -20R halt (G6, LW7, LATCH-3, HALT-4) | `account.max_setup_daily_loss_r`, `account.max_daily_loss_r`, `account.loss_stops_cost_r_accounts` | — | moderate | Judge on worst-day protection over >= 30 sessions. No halt tighter than 20R without saves on >= 2 separate days. No latch in Testing |
| PROT-22 | Brakes | Testing CF 0.15R filter on, and off in Primary (LW8, G7) | `max_stop_cost_r` | — | moderate | Arena removal needs >= 500 blocked trades at >= 0. A Primary extension needs a per-setup test showing it does not cut RW3/L3 |
| PROT-23 | Capacity | Per-setup cap 30, lot cap 3, quote crosscheck; no burst caps beyond the BRAKE-BURST runaway brake (G8, STACK-6, P8 guard) | `account.max_positions_per_strategy`, `live.max_lots_per_symbol`, `live.quote_crosscheck_max_dev_pct`, `live.burst_max_entries`, `live.burst_window_min` | — | moderate | Replay on cluster days (10-22, 11-03, 11-05, 11-12, 11-16) next to the bad days (11-10/11). A cap raise needs >= 3 mass-signal days in both directions |
| PROT-24 | Sizing | Equal-notional slots; R (after costs) as the only verdict unit (SIZE-1) | `account.slots`, `account.buying_power_multiple`, `account.risk_per_trade_pct`, `account.max_position_notional_pct` | — | moderate | State the effect on per-trade R, cost per R and worst-day $. No size-up while Primary R is negative |
| PROT-25 | Concentration | Twin block, kept as a concentration cap and not as an edge (LW3, TWIN-2; G2 rejected) | `live.block_twin_same_symbol`, `twin_group` | — | moderate (arenas) / weak (Primary) | Per-pair replay >= 10 sessions, best-day share < 50%. The guard notes that the effect follows the held twin's quality |
| PROT-26 | Primary setup | RW3/RW5 gap-down layer, heat / buyPressure / RSI thresholds; no gap widening (P2, P3, F3) | — | `RW3-gapdn-rsi5pop-flowsell-short-FD`, `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | weak | No loosening without a 2-year cost-in backtest plus a live Testing copy. Gap <= -1% tightening goes to the backlog |
| PROT-27 | Exits | t1s1 default (1R = 0.25 x ATR, symmetric, no scale-out) (P7) | `exits.scale_out_r`, `exits.scale_out_frac`, `t1s1 default` | — | weak | Beat t1s1 on the same signals, per setup, costs in, >= 15 Testing sessions |
| PROT-28 | Book | No whole-side market-direction gate (P6) | `market-direction gate`, `side gate` | — | weak | Per-setup and whole-book w/o best day improve over >= 20 sessions in Testing |
| PROT-29 | Primary setup | NM-ETF-late-dip unchanged; tweaks only as WB copies (F4) | — | `NM-ETF-late-dip-di-long` | weak | >= 15 more active days of the unchanged version |
| PROT-30 | Primary setup | L3 refire (cooldown 1) and stacking left as configured (LW6, PIPE-6) | `live.same_setup_reentry` | `L3-gap-slope-fromopen-FD` | weak | >= 150 re-entry trades, >= 15 days, w/o best day, before switching it off |
| PROT-31 | Governance | Small book, Friday-only epoch, BASE1 shadow (PD6, LW2, EPOCH-8, PIPE-8) | `baseline.enabled`, `baseline.setups`, `baseline.setup_order`, `BASE1` | — | weak (as evidence) | Paired Primary vs BASE1 difference (> ~2 SE) at a Friday review. Mid-epoch changes only for BROKEN bugs |
| PROT-32 | Protective rules | $5 minimum price; split-tape gate and CF where they run (G4, G7) | `costs.min_price`, `live.split_tape_short_gate`, `max_stop_cost_r` | — | weak | Dedicated low-price study with real spreads. >= 20 sessions of blocked replay for the others |

Note on PROT-23: the WhatWorks report recorded "no burst caps" because the burst-cap *remedies* it tested cut winners.
The owner then approved BRAKE-BURST (2026-11-20; `research/whatworks_1120/brake/REPORT.md`), a runaway-entry brake at
30 entries per setup in 10 minutes that never fired in Primary; its keys are now part of PROT-23, so loosening or
tightening it needs the same guard.
