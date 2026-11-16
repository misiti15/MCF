# Workbench results: 20-Minute Opening Range Breakout (`orb20_a`)
Mechanic, 2026-11-16 (built during market hours, 14:45-16:00 ET; research files only, no config touched, nothing deployed).
Educational only — not financial advice.

## Verdict
| Copy | Change | Replay avg R (n) | 2-year avg R (n) | W/o best day (replay / 2y) | Worst day R (replay / 2y) | Verdict |
|---|---|---|---|---|---|---|
| parent `orb20_a` | — | +0.072 (209) | -0.031 (2,710) | -0.019 / -0.034 | -8.9 / -8.7 | — |
| `orb20_a-WB1` | P4 stocks in play top 20 -> **top 10** | +0.095 (102) | -0.005 (1,317) | +0.040 / -0.010 | -5.6 / -6.6 | PASS |
| `orb20_a-WB2` | P2 price floor $5 -> **$20** (prior close) | +0.105 (190) | -0.020 (2,447) | +0.016 / -0.024 | -7.8 / -6.7 | PASS |
| **`orb20_a-WB3`** | **WB1 + WB2 (top 10 and price >= $20)** | **+0.118 (91)** | **+0.015 (1,178)** | **+0.059 / +0.011** | **-4.5 / -4.9** | **PASS — recommended** |

Pass rule (RULES.md clarification 2026-11-16): the copy meets or exceeds the parent's avg R after costs in BOTH tests and is
not worse on avg R w/o best day / worst day by more than 0.02R / 10%. All three copies pass; WB3 beats the parent on every
line and is the only one **positive after costs in both tests** (and per dollar traded: +3.8 bps replay, +1.9 bps 2-year;
parent +15.0 / -4.5 bps). Parent and copies went through the identical pipeline; the parent's live record was not used
in the decision (diagnosis only, DIAGNOSIS.md).

## The tests (identical for parent and every copy)
- **Signals: the production pipeline.** `code/ext.py` runs mcf.backtest.engine exactly as research/history2y/rescore_bt.py
  (SymbolHistory priors, universe_ok, in_play_filter, rank_contexts over the 1,226-name research universe, data/cache_hist)
  and stores, per session, every name with rank_rvol20 <= 40 that passes the class liquidity check, with its 1-minute bars.
  **Parity: `code/sim.py` with the production Costs reproduces the production ORB20 + `simulate()` trades exactly —
  2,919 of 2,919 trades, max R difference 0.0** (and the WB3 subset 1,269 of 1,269).
- **Replay of the live sessions:** 2026-10-06..11-10, 26 sessions (11-05..11-10 from the data/team 1-minute files limited to
  the research universe; 11-11..11-13 not on hand — fetching the full universe is after-hours work). Isolated: no caps, no
  latch, no quote / borrow checks, so it holds more trades than live (209 vs 42). Of the 42 live trades, 19 are names in the
  research universe (live ranks ~3,900 names; the replay ranks 1,226), so the replay is the setup's rules on these days,
  not a re-run of the live book.
- **2-year backtest:** 2024-10-01..2026-10-05, 407 sessions; **locked block 2024-11-01..2025-02-28 never read** (ext.py never
  loads a row inside it — the first post-lock chunk warms up from 2025-03-01 and trades from 2025-03-20 — and asserts it;
  sim.py asserts it again). Train = ..2025-12-31, valid = 2026-01-01..10-05.
- Engine: stop order at the 09:30-09:49 extreme +-1c from 09:50 to 11:30, fill = max(open, level) (as simulate()); stop
  0.5 x range and target 0.75 x range from the level; stop checked before target in every bar; time exit 15:50; R = net P/L /
  |fill - stop| (the live R definition). **Costs in (LR8 production model)** on every config: entry (1c + 1 bp) x
  time-of-day multiplier + 1 bp cushion; target 0; stop (1c + 1 bp) + max(2c, 4 bp); time exit (1c + 1 bp) + max(1c, 1 bp);
  SEC / TAF on the sale, CAT both sides.

## Side by side
**Replay of the live sessions 2026-10-06..11-10 (26 sessions)**

| Copy | Trades | Win % | Avg R | W/o best day | W/o worst day | Total R | Worst day | Best day share | Avg win / loss | Per $ traded | Median hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 209 | 52.2 | +0.072 | -0.019 | +0.122 | +15.0 | -8.9 | 124% (`1 day`) | +1.03 / -0.97 | +15.0 bps | 79 min |
| WB1 top 10 | 102 | 53.9 | +0.095 | +0.040 | +0.161 | +9.7 | -5.6 | 61% (`1 day`) | +0.97 / -0.93 | -18.1 bps | 83 min |
| WB2 price >= $20 | 190 | 53.7 | +0.105 | +0.016 | +0.155 | +20.0 | -7.8 | 86% (`1 day`) | +1.03 / -0.96 | +28.2 bps | 90 min |
| **WB3** | 91 | 54.9 | **+0.118** | **+0.059** | +0.180 | +10.8 | **-4.5** | 55% (`1 day`) | +0.95 / -0.89 | +3.8 bps | 99 min |

**2-year backtest 2024-10..2026-10-05 (407 sessions, locked block excluded)**

| Copy | Trades | Win % | Avg R | W/o best day | W/o worst day | Total R | Worst day | Avg win / loss | Per $ traded | Paired-by-day vs parent (t) | Train / valid avg R | Up / flat / down days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 2,710 | 44.9 | -0.031 | -0.034 | -0.028 | -83.2 | -8.7 | +1.06 / -0.92 | -4.5 bps | — | -0.006 / -0.056 | +0.030 / -0.062 / -0.058 |
| WB1 | 1,317 | 45.1 | -0.005 | -0.010 | -0.000 | -6.8 | -6.6 | +1.06 / -0.88 | -5.6 bps | +0.028 (1.86) | +0.050 / -0.060 | +0.046 / -0.034 / -0.027 |
| WB2 | 2,447 | 45.4 | -0.020 | -0.024 | -0.018 | -49.8 | -6.7 | +1.05 / -0.91 | -0.7 bps | +0.012 (1.88) | +0.000 / -0.041 | +0.041 / -0.056 / -0.046 |
| **WB3** | 1,178 | 46.1 | **+0.015** | **+0.011** | +0.020 | +18.1 | **-4.9** | +1.06 / -0.88 | **+1.9 bps** | +0.037 (2.32) | **+0.055 / -0.024** | **+0.046 / +0.007 / -0.007** |

(Paired-by-day = per-session total-R difference, scaled per parent trade. It counts fewer trades as less total R, so on the
26-session replay it reads -0.021 (t -0.22) for WB3 although WB3's avg R per trade is higher; reported, not a pass hurdle.
Day types = research/history2y session regimes, 2-year test only.)

## Configurations counted: 70 (parent + 69)
Every part P1..P20 was inspected; the testable ones were scored one change at a time on the parent (43), then 18 finer
grid / combination configs, then 8 around the finalists (code/ana.py, combo.py, final.py; results_single.csv,
results_combo.csv, results_final.csv). Bar max(1.5, sqrt(2 ln 70)) = **2.91**: WB3's paired 2-year t (2.32) does **not**
clear it, so the gain is consistent across train, valid, replay and every day type but not proven by significance alone.
Selection honesty: the shortlist was picked with the 2-year AND the replay numbers in view (the train split alone points
the same way for top 10 and price, not for every finalist), so neither test is a clean holdout for the copy.

Parts not testable in a backtest (reported, no config): P3 earnings blackout (not in the history pipeline), P11 caps /
latch (account-level), P13 quote / spread checks (no quotes), P14 borrow (no ETB history), P16 size (R is size-free).
P8 refire is one order per day by design.

**All failures** (replay / 2-year avg R vs parent +0.072 / -0.031; a pass needs both):
| Part | Change | Replay | 2-year | Why not kept |
|---|---|---|---|---|
| P1 | core tier only | +0.072 | -0.031 | identical (no extended name passes the class liquidity check) |
| P1 | ADV >= $20M / $50M | +0.072 / +0.072 | -0.030 / -0.020 | passes at $50M but small; in no finalist beat WB3 (top10 + $10 + $50M: +0.095 / +0.013) |
| P1 | ATR >= 2% of price | +0.082 | -0.028 | small; valid -0.066 worse |
| P2 | price >= $10 | +0.076 | -0.023 | weaker than $20 |
| P4 | top 30 / top 15 | +0.064 / +0.048 | -0.036 / -0.022 | top 30 worse both; top 15 fails replay |
| P5 | rvol >= 1.2 / 2.0 / 3.0 | +0.072 / +0.072 / +0.069 | -0.032 / -0.031 / -0.023 | the top-20 rank already implies rvol well above 1.5 |
| P6 | range >= 0.3 / 0.4 / 0.5 ATR | +0.053 / -0.002 / -0.010 | -0.023 / -0.025 / -0.015 | fails the replay (drops good thin-range ETF breaks, e.g. SCZ best5) |
| P6 | range <= 1.5 ATR | +0.110 | -0.039 | fails 2-year |
| P7 | until 10:30 / 11:00 / 12:00 | +0.038 / +0.056 / +0.060 | -0.021 / -0.030 / -0.027 | fails replay |
| P9 | long only / short only | +0.048 / +0.094 | -0.033 / -0.028 | regime bets; short only fails w/o best day (-0.075) |
| P9 | open -> 09:49 move >= 0.25 ATR | -0.016 | -0.017 | fails replay |
| P10 | VWAP off / close in outer third | +0.049 / +0.054 | -0.031 / -0.022 | fails replay |
| P12 | stop cost <= 0.10 / 0.12 / 0.15 / 0.20 R | +0.061 / +0.072 / +0.096 / +0.095 | +0.002 / -0.008 / -0.023 / -0.031 | 0.15 passes alone; adds nothing on top of top 10 (C1 +0.038 / -0.007) |
| Gates | SPY 09:50 position in its 09:30-09:49 range agrees | +0.553 | -0.106 | 2-year much worse (52 replay trades) |
| Gates | SPY since 09:50 not against by > 0.20% / with the trade | +0.425 / +0.341 | -0.027 / -0.047 | replay-only effect; nothing over 2 years |
| P15 | skip 09:50 triggers (as live) / start 09:55 | +0.146 / +0.094 | -0.056 / -0.042 | fails 2-year: the 09:50 breaks are the better ones |
| P17 | stop 0.4 / 0.6 / 0.75 / 1.0 x range | +0.099 / +0.040 / +0.007 / +0.009 | -0.051 / -0.024 / -0.013 / -0.009 | wider stops help 2-year, cost the replay |
| P18 | target 0.5 / 1.0 / 1.5 x range / none | +0.063 / -0.036 / -0.051 / -0.083 | -0.045 / -0.037 / -0.036 / -0.026 | the 0.75 target is the sweet spot |
| P19 | exit 12:00 / 13:30 / 15:00; time stop 60 min < +0.5R | +0.067 / +0.075 / +0.066 / +0.051 | -0.051 / -0.041 / -0.032 / -0.034 | late-day drift is part of the edge |
| P20 | breakeven at +1R / trail 1R after +1R | +0.082 / +0.092 | -0.034 / -0.038 | fails 2-year |
| combos | top10 + cost/R 0.15 (+ $10, + $50M, + stop 0.6 / 0.75, + ATR 2%, + 10:30); top15 + cost/R (+ $10); top10 + cost/R 0.10 | +0.038 .. -0.060 | -0.019 .. +0.012 | all fail the replay |
| finalists | top10 + $10 (+ $50M); top12 / top8 + $10; top10 + $10 + stop 0.75 / + $15 / + cost/R 0.20; $20 + $50M | see results_final.csv | | top8 + $10 is best over 2 years (+0.032) but fails the replay (+0.049); the rest are below WB3 |

## Supervisor sign-off — WB3 (`orb20_a-WB3`)
- **What changed (vs the parent):** intake only — (1) stocks in play: the **top 10** names by 09:30-09:49 relative volume
  instead of the top 20; (2) price floor: prior close **>= $20** instead of $5. Range, direction, VWAP agreement, the
  09:50-11:30 stop order, stop 0.5 x range, target 0.75 x range and the 15:50 exit are unchanged.
- **Why:** the losses sit in the lower half of the in-play list (2-year rank 11-20: -0.055R on 1,393 trades vs rank 1-5
  +0.024R; live: lab rank <= 10 +0.25R on 13 trades, rank > 10 -0.45R on 6) and in cheap names, where the spread and
  stop slippage eat the R (2-year < $20: -0.12R on 263 trades; live worst4 AVPT paid 20 bps on entry). Exits were tested
  exhaustively and the parent's are already the best of those tried.
- **Overall before -> after (parent -> WB3):** replay +0.072 -> **+0.118R**; 2-year -0.031 -> **+0.015R** (train -0.006 ->
  +0.055, valid -0.056 -> -0.024: better in both halves); w/o best day -0.019 -> +0.059 / -0.034 -> +0.011; worst day -8.9 ->
  -4.5R / -8.7 -> -4.9R; per dollar traded +15.0 -> +3.8 bps (replay) and -4.5 -> **+1.9 bps** (2-year); up / flat / down days
  +0.030 / -0.062 / -0.058 -> +0.046 / +0.007 / -0.007 (better on every day type). Of the 5 worst live trades WB3 skips
  IXUS (rank 14), CART (rank 13) and AVPT ($17); ILF and BRZE are outside the research universe (rank unknown).
- **Where it gives a little back:** about 55% fewer trades (2-year 2,710 -> 1,178, ~3 a session; replay 209 -> 91), so
  total R on the replay is lower (+15.0 -> +10.8R) even though every per-trade figure is better; it loses the cheap-name
  winners (live best2 AVEX $10.5, +1.59R); the 2026 valid half is still negative (-0.024R); the replay record is still
  carried by its best day (55% of total R, `1 day` tag — the parent's was 124%); the paired 2-year t of 2.32 is under the
  2.91 bar for 70 configs.
- **Rule-change context:** live window 10-06..11-12 holds the Primary -> Testing demotion (10-12), Testing latch on / off
  (10-20 / 10-23), Primary sizing / latch (10-28 / 10-29), the 0.15R stop-cost filter (10-30) and LR1 / LR3 / LR5 / LR7
  (11-12). The backtests apply one rule set throughout, so no rule change is mixed into the copy-vs-parent numbers.

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session. One copy only:
**WB3** (it contains WB1 and WB2; running them as well would be near-twins). The parent stays in On Deck, unchanged
(rule 1). Destination: **Testing A** (`config/account_testing2.yaml`) — a testing account, not the parent's (twins rule),
not On Deck / Primary (rule 6 needs the owner); Testing A trades the full universe again since 11-12 and already lists
`orb20_a: {enabled: false}`. Priority per RULES.md 5: FIRST in `live.setup_order`; if another Workbench copy has
already claimed the first slot tonight, put WB3 right after it (the main session orders the Workbench copies).
1. Code (setup code, so after hours and through the setup-freeze check): add the one new part to the builtin class so the
   parent is untouched — in `mcf/strategies/research_setups.py`, `ORB20.eligible`, append
   `and ctx.prev_close >= float(self.params.get("min_price", 5.0))` (default $5 = the class's existing `_liquid` floor;
   the parent's trades do not change). Equivalent subclass for reference: `research/workbench/orb20_a/modules/orb20_wb.py`.
   Add a test that `min_price` defaults to the old behaviour.
2. `config/account_testing2.yaml`, under `strategies:` add
   ```yaml
   orb20_a-WB3:
     # Workbench copy of orb20_a (On Deck), Mechanic 2026-11-16: top 10 by 09:30-09:49 rvol (was 20) + prior close >= $20
     # (was $5); research/workbench/orb20_a/RESULTS.md. Effective next session.
     enabled: true
     class: orb20
     variant: A
     min_rvol: 1.5
     top_n: 10
     min_price: 20.0
     entry_until: "11:30"
     scale_out_r: null
     tags: [workbench, "parent:orb20_a"]
   ```
   and put `orb20_a-WB3` first in `live.setup_order` (see priority above).
3. `config/setup_names.yaml`: `orb20_a-WB3: {name: "20-Minute Opening Range Breakout — WB3: top 10 in play + price >= $20", side: both, what: "as the parent (until 11:30, break of the 09:30-09:49 high or low on above-average volume), only the 10 names with the highest 09:30-09:49 relative volume and a prior close of at least $20"}`.
4. `research/ledger.jsonl`: id `2026-11-16-wb-orb20a-wb3`, effective next session, title "Workbench copy orb20_a-WB3 added
   to Testing A, first in setup_order (Mechanic pass)", patch `{"strategies.orb20_a-WB3 (testing2)": [null, "added, enabled"],
   "ORB20.min_price": [null, "new param, default 5.0"], "live.setup_order (testing2)": ["...", "WB3 first"]}`, evidence this
   file, approved_by "owner rule research/workbench/RULES.md 5 (passes go to a testing account at once)"; then
   `python -m mcf.research.ledger check`.
5. Smoke test: build the Testing A strategies (`MCF_ACCOUNT=testing2`) and run orb20_a-WB3 over one cached session;
   `python -m mcf.report.assignments` (regenerates docs/live/assignments.json in the same commit); `pytest -q`; commit, push
   after 16:05 ET (setup-freeze).

Files: DIAGNOSIS.md, `orb20_a_engine.png`, `orb20_a_worst{1-5}_*.png`, `orb20_a_best{1-5}_*.png`, variants.jsonl,
README.md, `orb20_a-WB{1,2,3}.yaml` (stubs, not account configs), modules/orb20_wb.py, code/ (ext.py, sim.py, ana.py,
combo.py, final.py, charts.py, engine_png.py; scratch paths inside), results_single.csv, results_combo.csv, results_final.csv.
