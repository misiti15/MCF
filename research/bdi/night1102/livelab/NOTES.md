Educational only — not financial advice

# night1102 / livelab — a "live-first" vetting lane (plan for the owner, not built)

Owner 2026-11-02 evening: "nothing beats live testing ... live testing rules all". This workstream designs a lane that
puts new setups on paper fast at small constant size and judges them on live R. Research only. No config, setup or exit
change, nothing merged. No bar history was read, so the locked block 2024-11-01..2025-02-28 was never touched. Inputs:
the 5 live journals (run_id 1 = live paper, run_id 2 = what-if), `config/account_*.yaml`, `research/backlog.jsonl`,
`research/ops/blocked_audit.md`. Live R = pnl_adj / (|entry - stop| x shares), with costs and fill-realism in.
Scripts: `livelab.py`, `extra.py`, `extra2.py`, `backlog_lane.py`. Outputs: `results.json`, `extra.json`, `extra2.json`,
`capacity.csv`, `early_vs_later.csv`, `kill_grid.csv`, `gen_screen_vs_live.csv`, `backlog_lane.csv`. The analyses were
declared before any number was computed (PLAN.md). **Configurations scored: 32** (27 kill rules, 3 early-vs-later
correlations, 2 screen-vs-live correlations). Nothing passed or failed a promotion gate here, because this is a design.

**Rule changes inside the live window 10-06..11-02** (`research/ledger.jsonl`, so these results mix several periods):
10-21 Graveyard opens (moves into it continue to 11-03). 10-22 ST-A turns the per-setup daily stop off in Testing and
Gen. 10-26 Gen caps GX2 (200 slots). 10-27 GX1 5-minute lab clock (all accounts). 10-28 Primary ~$4k size. 10-29
Primary -2R per-setup stop, the Setup Generator is paused after its 10-28 run, BAR90. 10-30 Testing cost filter CF
(`max_stop_cost_r` 0.15). 11-02 R2A legs go into Testing 2, and NS3-FD and RW4-FD move to the Graveyard. Several
promotions and demotions fall inside the window too. R is per trade, so size changes do not scale it. The stops, caps
and filters do change which trades exist.

## Failures and warnings first

1. **A live-first lane has already been tried, and it lost the most.** The Setup Generator account (screen-only gate,
   no holdout, from 10-19) is the closest thing to this lane. On the same dates (10-21..11-02) it averaged
   **-0.284R over 990 trades**. Over the same dates Testing 1 averaged -0.144R (1,184), Testing 2 -0.094R (1,416), the
   Graveyard -0.143R (2,942) and Primary +0.110R (341). Its screen did not rank live results: Spearman of the screen
   expectancy vs live avg R was **+0.16 on train and +0.02 on valid** (n = 29 Gen setups with 10 or more trades,
   p = 0.42 / 0.90). The owner paused the generator after its 10-28 run. A minimal gate lets in mostly losers, so the
   lane has to be cheap (small size), short (fast fails), and must never feed Primary without a second confirmation.
2. **Exposure is the bottleneck, not the gate.** Only **19 of 238 setup-account records are "verdict-ready"** (30 or
   more trades and 10 or more sessions): Gen 0 of 65, with 52 setups under 30 trades after 11 sessions. Testing 1 has
   11 of 62, Testing 2 5 of 57, Primary 3 of 26, the Graveyard 0 of 28 (9 sessions). The median setup takes 4-5 trades
   a session (Graveyard 10.8).
3. **Early live records barely predict later live records.** This covers the 36 setups with 8 or more sessions and 40
   or more trades. The first 5 sessions vs the rest give Spearman **-0.07** (p 0.71). The first 30 trades vs the rest
   give **+0.20** (p 0.23). Only 8 of 36 setups were positive on their later trades (22% base rate). Kill rules
   "avg R <= x after K trades" with K = 15/30 and x = -0.1 to -0.3 do **not** separate the setups: killed and kept
   setups had about the same later avg R (for example K 30, x -0.2: later -0.141 vs -0.134R pooled). **One rule did
   separate them:** after 45 trades, avg R <= -0.30. It killed 9 setups. None of the 9 was positive later, and their
   later trades averaged -0.277R against -0.114R for the 41 kept, saving 216R. That is 1 rule out of 27 tried, so treat
   it as a hint, not proof. Early and later trades also fall on different market days (5 up, 5 down and 10 quiet days
   in the window). The low correlation is partly regime, which fits the direction-bet finding (night1102/regime).
4. **Live noise, measured.** For the 36 setups above, the median standard deviation of the daily mean R is
   **0.53R** (9 trades a day). Trades on the same day are correlated (design effect 3.2), so 30 trades over 3 days carry
   far less information than 30 trades over 10 days. To reach a day-clustered t of 1.5:
   - a true **+0.30R** takes **8 sessions**;
   - **+0.20R** takes **17** (11 at 5+ trades a day, 27 at 2-5);
   - **+0.10R** takes **65**.

   So 10 sessions can confirm a failure or a very large edge, never an ordinary one. A promote verdict needs about 20.
5. **The what-if engine already shadows blocked signals, but as a backtest fill.** It covers **14,353 of 14,722
   blocked or rejected signals (97.5%)**. The 369 missing signals are mostly ETB 94, opposite side 85, spread 73 and
   lot cap 67, where no bars came back or the simulation returned nothing. `Runner.what_if` simulates on the day's bars
   with backtest costs, not on live quotes, so under rule 7 shadow R is labelled separately from live R. Its accuracy
   against live has not been audited. The replay audit failed on 10-29 for similar reasons.

## The plan (1 page)

**Entry gate (minimal, costs in).** A setup enters the lane only if all of these hold:
- On the open two-year frames with production costs, expectancy is >= -0.02R on train and on valid.
- The expected rate is 1.5 to 25 trades a session (rule 21's "normal" tier, with a ceiling so one setup cannot take
  the account).
- The live module matches its scored version trade for trade.
- It does not duplicate a setup already live.

There is no t bar, no holdout and no regime gate at entry. The locked block is not used.

**Account: a new paper account "Live Lab"** (orders `mll-`, branch `mcf-data-livelab`, secrets
`ALPACA_LIVELAB_API_KEY` / `_SECRET_KEY`, 6th row of the trade.yml matrix). Why not Testing 1 or 2:
- Lab setups would compete for symbols with the current setups (place in line), which muddies both records.
- It keeps Testing 1 = Testing 2 parity untouched.
- The lane needs one-position-per-symbol across setups switched off.

**Fallback if the owner wants no new account:** split the lane evenly between Testing 1 and Testing 2, at most 10 seats
in each, at the end of `setup_order`. Over the last 5 sessions their peak open lots were 73 and 89 of 400, so about
300 slots are free in each. Their buying power is equity x 3.8 = ~$369k / ~$361k, and neither had a buying-power
reject. The Graveyard is full (peak 155 of 200, 42 buying-power rejects). The Gen account should not be used: its
GEN setups cannot be removed without the owner's consent, and it peaks at 144 of 200 with 12 buying-power rejects.

**Capacity: 20 seats at once.**
- 200 slots and a constant ~$1,000 notional per lot (Testing's median lot is $900).
- `buying_power_multiple` 2.0, so $100k x 2 / 200 = $1,000, well inside paper buying power.
- `max_positions_per_strategy` 10. In Testing, a setup-day peaks at a median of 3 lots, p90 16-20.
- 20 seats x 10 = 200 slots, so slots never bind across setups.

Every signal blocked by a portfolio rule goes into the shadow track: per-setup cap, slots, buying power, a symbol held
by another setup, opposite side, twin, lot cap.

**What the verdict is judged on.**
- Live R and the shadow track are reported separately. The shadow track is live fills plus what-if trades for the
  portfolio-blocked signals, at 1R each (backlog `shadow-1102-constant-size-track`).
- Execution rules that would also block in Primary (ETB, spread, halted, price) are **not** shadowed into the verdict.
- Every row shows avg R without the best session and that session's share, with the `1 day` tag at >= 50%, and the R
  split by SPY up, down and quiet days.

**Fixed window and automatic exits** (sessions count from the lane start; the rules are frozen before entry):
- **Fail fast (automatic demotion to "lane-failed", off the next session):**
  - after 5 or more sessions and 45 or more live trades, avg R <= -0.30 (the one separating rule above);
  - or, at any time, cumulative live R <= -15R.
- **Verdict at 20 sessions and 40 or more trades** (if under 40 trades, extend once to 30 sessions, then judge or
  drop as "too rare"). A **pass** needs all of these:
  - live avg R > 0 with day-clustered t >= 1.0;
  - avg R without the best day > 0, with best-day share < 50%;
  - at least 3 up and 3 down sessions seen, and avg R >= -0.05 on each (the diverse-conditions check);
  - shadow-track avg R > 0.

  Otherwise it is a fail.
- A **pass** goes to Testing 1 / 2 on the Testing bar, as a move under the owner rules; it is not a promotion to
  Primary. A **fail** goes to `research/backlog.jsonl` with its numbers. Following the GEN and rule-20 precedent, the
  owner is prompted before any setup is retired.

**Throughput and expected yield.** 20 seats, about a 20-session tenure, and fail-fast exits around session 5-8 come to
roughly **1-1.5 new setups a session, 25-30 a month**. At the observed 22% later-positive base rate, about **5-7 a
month** pass. The 20-session window is coarse. At t 1.0, a true +0.20R passes about 75% of the time, a true +0.10R
about 44%, and a true 0R still passes about 16% (before the other checks).

**Supply from the backlog today** (`backlog_lane.csv`; heuristic parse, every row listed for checking).
374 idea / rework / near-miss entries were checked:
- **3 enter cleanly:** `bdi-rw-nm-flowsell-rsi65-gapdn-volume`, `bdi-vid-envelopes`, `mh-1029-earnings-sympathy`.
- **6 pass the R test but give no trade count**, so they need a check.
- **8 pass but already run live** (NS1, NS5, NS2, NM-AR-AM, NM-AMS-N1, NM-PM, NM1, NM-HL).
- **13 of 163 top-5 exit variants** are not negative. They are twins of live setups, so they belong in the normal
  backlog path, not the lane.
- **62 have no costs-in number yet** and need a module plus a minimal backtest.
- 3 fail as clearly negative, 42 are blocked (not live-runnable, missing data, or review items), and 87 are not new
  setups.

**Realistic supply: 3-9 now**, plus whatever the 62 unbuilt ideas and the nightly BDI families yield. The lane will be
supply-limited, not seat-limited, unless the generator is resumed into it.

## Exact pieces needed (not built)

1. `config/account_livelab.yaml`:
   - `strategies_exclusive: true`;
   - `account: {starting_equity: 100000, slots: 200, buying_power_multiple: 2.0, max_concurrent_positions: 200,
     max_positions_per_strategy: 10, max_daily_loss_r: 60, max_setup_daily_loss_r: null, max_trades_per_day: 1500}`;
   - `live: {block_twin_same_symbol: false, scale_out_max_per_day: 0, max_stop_cost_r: 0.15}`;
   - a per-symbol cross-setup lock switched off, which needs flag 3;
   - a `lane:` block on each setup: `{entered: <date>, gate: {train_exp, valid_exp, tpd}, window: {sessions: 20,
     min_trades: 40}, fail_fast: {after_trades: 45, min_sessions: 5, avg_r_le: -0.30, cum_r_le: -15}}`.
2. `.github/workflows/trade.yml`: a 6th matrix account `livelab` (COID `mll-`, `STATE_BRANCH` `mcf-data-livelab`,
   secrets). The owner creates the paper account and the secrets.
3. `mcf/execution/runner.py`: a config flag `live.cross_setup_symbol_lock` (default true). When false, a symbol held by
   setup A does not block setup B. Same-setup duplicates and opposite-side lots stay blocked.
4. `mcf/execution/runner.py` `what_if`: tag each row `shadow_class` = portfolio | execution (from
   `playing_time.classify`), and write a stub row with `exit_reason='no_sim'` when `simulate` returns None, so the 2.5%
   gap is counted, not silent.
5. `mcf/report/livelab.py` (new): per lane setup it shows sessions, live n and avg R, day-clustered t, avg R w/o best
   day, best share, up/down/quiet R, shadow avg R, and its state (running / fail-fast / pass / fail / extended). It
   writes `docs/live/livelab.json` for a dashboard tab and an EOD line.
6. `mcf/research/lane.py` (new): `gate(module)` runs the minimal two-year check (open frames, production costs, locked
   block refused). `evaluate(date)` applies the frozen exit rules after the close. A failed setup is never switched off
   during market hours, and any switch-off goes through the normal PR (setup-freeze), with assignments regenerated and
   a ledger entry.
7. `tests/test_livelab.py`: the gate refuses the locked block, a fail-fast trigger fires at 45 trades and -0.30R, a
   pass needs both regime splits, and shadow excludes execution blocks.
8. Ledger entry `2026-11-xx-livelab-lane` when approved (`python -m mcf.research.ledger check` after it).

Backlog: `livelab-1102-live-first-lane` (status idea).

Educational only — not financial advice.
