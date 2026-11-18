# U11 ONE ENGINE — inventory, disagreements, retirement plan (2026-11-18)

*Educational only — not financial advice. Research only: no code, config, runtime, setup or exit change; nothing
merged. Pre-registration: [PLAN.md](PLAN.md). Method and caveats: [NOTES.md](NOTES.md). Source names as in
docs/GLOSSARY.md. Configurations tried: 0 setup configurations (no setup scored; 1 code census). Locked block
2024-11-01..2025-02-28 not read (no bars read).*

## Answer first

- **MCF has six simulation paths, not two.** E1 the old backtester (`mcf/backtest/engine.py` `Backtester`), E2 the
  lab-frame pipeline behind the "2-year backtest" and the Generator's "2-year screen", E3 the session replay through
  the live runner (`mcf/replay`), E3c its calibrated form (`livecal`), E4 per-study bespoke sims (the "Workbench
  engine" and its relatives), E5 Shadow (forward, inside the live runner). Each has its own fill rule, cost model,
  R definition and book (u11_engines.csv, u11_parity.csv).
- **The old backtester cannot simply be deleted:** the LIVE runner imports its helpers (`Costs`, `universe_ok`,
  `in_play_filter`, `rank_contexts`, `is_extended`, `pinned_symbols`, `lot_shares`, `slot_notional`) and uses its
  `simulate()` for the what-if of every untaken signal. Only the `Backtester` class is retireable; the helpers move.
- **Who uses E1 today:** almost nobody in research (1 new study since 11-01) — but the mandated ledger conflict check
  (RESEARCH_RULES 12, `python -m mcf.research.ledger check`) still runs on it, and its output has never been committed.
- **The real sprawl is E4:** 28 study directories added their own simulator in the last 6 sessions (20 Workbench
  setups, l3_bespoke_1117, lr6, sizing_1115, today's U4/U5/U6). Workbench tune verdicts (C3-WB, ODPREP) are decided
  on these, and the Workbench calls its own sim on live sessions "replay" — the same word GLOSSARY uses for E3.
- **Preconditions for retiring the old engine are not met today:** session replay matches live **87.1%** (target
  ≥ 98%) with **26.2%** extra trades (target ≤ 2%) on held-out 11-02..11-16, and the 2-year live-code replay is a
  PLAN with **0** sessions run. Recorded live quotes (the largest gap, 22.1% of the extras) start **today, 11-18**:
  the first fair re-test of the 98% gate is after ~10 quote-recorded sessions (≈ 12-02).
- **Plan:** S0-S8 below, three decision steps **ENG1-A / ENG1-B / ENG1-C**. Two pieces can start without waiting for
  the 98% gate (helper extraction, shared exit walker); deletion waits for every gate in u11_gates.csv.
- Honest limit: one engine removes inconsistency and maintenance; it does **not** create predictive skill. SRCV1 found
  no non-live source ranks setups (all Spearman ≈ 0). Live still wins every disagreement.

## 1. Inventory (full rows: u11_engines.csv)

| id | engine | fills | R | universe | book | used for |
|---|---|---|---|---|---|---|
| E1 | `Backtester` (mcf/backtest/engine.py; `mcf.cli backtest/demo`) | next bar open, stop-first, touch targets | entry−stop × shares | old 1,226-name cache | concurrent / per-setup / trades-day / daily R / 1 per symbol; no quote, cost-filter, latch-in-cost-R, halt, twin, ETB | ledger check, setup_screen, rescore_bt (orb20_a, intraday_momentum) |
| E1p/E1h | `simulate()` + selection / sizing helpers | as E1 | — | — | — | **live runner** what-if + universe / in-play / sizing; replay; team |
| E2 | lab frames (history2y, setup_lab, arena, generator, backlog_lab) | signal-bar close, first touch of fixed geometry | 0.25 × daily ATR | 1,226 survivorship names | none (each setup alone, first bar per symbol-day) | 2-year backtest, 2-year screen (Gen), weekly backlog re-test, most research FIT sets |
| E3 | session replay (harness + broker + fast) | submit-minute open; trade-through limits | as live | full live universe (packs from 10-06) | the account's real limits as traded | dashboard replay columns, Team, Exposure Lab, preval, playtime, fwdrep |
| E3c | calibrated replay (livecal, params_v2) | + poll log, latency weight 0.64, modelled spread | as live | as E3 | as E3 | replay_cal 98% gate, effective-session weight |
| E3y | 2-year replay (research/replay2y) | as E3c, no poll log / quotes | as live | 2-year history packs (point-in-time, delisted incl.) | today's accounts | **planned**, 0 sessions run |
| E4 | bespoke sims (Workbench `code/sim*.py`, l3_bespoke sim4, u4 engine.py, …) | mostly signal-bar close, target through $0.01 | varies | lab frames + live-session bars | own simplified book | Workbench tunes (C3-WB / ODPREP), most usage-plan studies |
| E5 | Shadow (mcf/execution/shadow.py) | fills B (harder than live) | as live | live | none | forward cross-check; not retired |

Out of scope (not intraday setup verdict engines): Discovery miner (feeds Generator seeds), Hunch learner, Longhold.

## 2. Who uses which (u11_consumers.csv, census u11_census.csv)

| consumer | engine today | plan |
|---|---|---|
| Live runner what-if, universe, in-play rank, sizing | E1p / E1h | move helpers to a neutral module, behaviour byte-identical (S2) |
| Ledger conflict check (rule 12) | **E1** | port to E3 over recent live sessions (S6a) |
| `mcf.cli backtest` / `demo`, setup_screen.py, rescore_bt.py, orb20_a mechanic | E1 | redirect / archive (S6f-g) |
| Setup Generator (Gen) | E2 | keep the screen as candidate generator; add an E3 confirm before apply (S6d) |
| Weekly backlog re-test (discover.yml) | E2 | E3 alone-mode on stored live sessions (S6c) |
| "2-year backtest" numbers (dashboard, reviews, Workbench rule) | E2 / E4 | E3y once G2 holds (S6e) |
| Workbench tunes (C3-WB, ODPREP, U7) | **E4** | E3 signals + one shared exit walker (S4, S6b) |
| Dashboard replay, Team, Exposure Lab, fwdrep, replay_cal | E3 / E3c | stays (engine of record) |

Census by study directory and first-add date: E2 87 / 40 / 29 (≤ 10-31 / 11-01..10 / 11-11..18), **E4 20 / 12 / 28**,
E3 5 / 5 / 8, E1 13 / 0 / 1.

## 3. Where they disagree (measured; quoted from committed scorecards, windows differ — not one table)

| comparison | number | window | source |
|---|---|---|---|
| E3c calibrated replay vs live, pooled 3 accounts | match **87.1%**, extra **26.2%**, pair bias **+0.005R** [−0.008, +0.018], total −360.9R vs −381.7R (rosier +0.007R/trade), daily corr 0.945, skip-reason 77.7% | held-out 11-02..11-16 (11 sessions), scored once | research/replay_cal/heldout/SCORECARD.md |
| same, per account | Primary 73.9% / Testing 1 91.0% / Testing 2 89.7% (Testing 2 bias +0.017R, optimistic) | same | same |
| same, protected L3-gap-slope-fromopen-FD (Primary) | **44%** match, 27% extra; live avg R +0.388 vs replay +0.099 | same | same |
| E3c gap causes | spread / spread-vs-stop checks: 7.1% of live trades missed, **22.1%** extra; latch cascade 2.7% missed; the rest ≈ 6% missed / 4% extra | same | heldout/gap_decomposition.csv |
| E3 (uncalibrated, paper fills, lab ∩ live universe) vs live | signals 98.0 / 99.9 / 99.6%, trades 85 / 82 / 91%, matched R diff −0.006 / −0.005 / +0.024 | 10-07..10-21 | research/replay/VALIDATION.md |
| E3 forward replay (Team engine) vs live | 76% of live trades matched; matched R +0.010; whole record rosier **+0.08R/trade** (−0.151 vs −0.230) | to 11-11 | research/fwdrep/NOTES.md |
| E3 snapshot vs LATER live (74 setups) | bias −0.031R [−0.09, +0.03], ratio 0.90, Spearman −0.03 | snapshot to 10-21, live 10-22.. | research/src_value/NOTES.md |
| E2/E1 "2-year backtest" vs LATER live (15 setups) | optimistic **+0.06..+0.09R**, Spearman ≈ 0 | to 10-07 vs 10-08.. | same |
| E2 "2-year screen" vs LATER live (68 GEN setups) | optimistic **+0.157R**, sign right on 34% (naive 69%) | same | same |
| E4 Workbench sim vs live | first signal bar = live on 283 of 286 matched symbol-days (99%; timing only, not trades or R) | 10-12..11-13 | research/workbench/L3-gap-slope-lowdist-FD/RESULTS.md |
| E4 vs E3 on the same parent (L3-gap-slope-fromopen-FD) | Workbench "replay" +0.136R (25 sessions to 11-17; an earlier Workbench book gave +0.059R) vs E3c +0.099R (11-02..11-16) vs live +0.388R | windows differ | l3_bespoke_1117/RESULTS.md, SCORECARD |
| E1 vs E2 vs E3 vs E4 on the same sessions | **never measured** | — | S1 below |

Structural differences behind these (u11_parity.csv): only E3 runs the live code's signals, dedupe / re-entry,
quote checks, cost filter, latches in cost R, halts, twin rules and ETB; E1/E2 lack all of them; E2 also uses a
different R (0.25 × ATR), enters at the signal-bar close and runs on a survivorship universe; E4 re-implements each
setup by hand. Five different entry-fill rules are in use across E1-E5.

Rule changes inside these windows: see NOTES.md (11-03 UNI1, 11-04 low-rep homes, 11-10 TEAM-6, the 11-12 batch incl.
LR3 / LR8 / halt 300 / Testing A full universe, 11-16 TSZ1 / shadow, 11-18 recorded quotes and SRCV1).

## 4. Preconditions (u11_gates.csv — 15 gates, status today)

| gate | target | today |
|---|---|---|
| G1a-f session replay vs live, held-out, per account and pooled | match ≥ 98%, extra ≤ 2%, \|bias\| ≤ 0.01R not optimistic, daily corr ≥ 0.95, skip-reason ≥ 95% | **FAIL** (87.1% / 26.2% / +0.005 / 0.945 / 77.7%) |
| G1g protected L3-gap-slope-fromopen-FD match (added here) | ≥ 95% | **FAIL** (44%) |
| G1h held-out scored with recorded live quotes | ≥ 10 sessions | 0 (recording starts 11-18) |
| G2a/b 2-year replay running + its overlap check | all replayable sessions × accounts; overlap ≥ 98% / ≤ 2% / ≤ 0.01R | PLAN only |
| G3 throughput for a parent + copy tune | ≤ 1 night | unmeasured (Primary alone 133 s/session; Testing 2 ~1,070 s) |
| G4 helper extraction byte-identical | golden replay outputs identical | not started |
| G5 shared exit walker = full replay exits | ≥ 99% same exit, \|ΔR\| ≤ 0.005R | not started |
| G6 decision consumers of E1/E2 ported | 7 of 7 | 0 of 7 |
| G7 replay vs shadow on the same sessions | replay not rosier than shadow beyond the fills-B margin | not measured |

## 5. Retirement plan

Every code step is housekeeping or research tooling, merged only outside 09:30-16:00 ET (setup-freeze), one PR each,
full `pytest -q` green; any step that changes what live does (only S8's optional what-if switch) gets its own ledger
entry and owner decision.

| step | what | test / exit criterion | depends on |
|---|---|---|---|
| **S0** | this inventory (done) | — | — |
| **S1** | one apples-to-apples baseline: E1 (as-traded config), E3c, and the Workbench sims of ~5 live setups on the SAME held-out sessions (11-18 onward, recorded quotes), scored with `research/replay_cal/score.py` (match / extra / pair bias / total R, per setup, improve/worsen counts). Pre-registered, 1 config per engine | report only; this is the "where they disagree" table on one window | quotes recorded ≥ 5 sessions |
| **S2** | move E1h + `simulate()` to a neutral module (e.g. `mcf/core/{selection,sizing,fills}.py`); `mcf/backtest/engine.py` keeps re-exports | `python -m mcf.replay run --as-live` on 3 sessions × Primary / Testing 1 / Testing 2: signals / trades / whatif CSVs **byte-identical** before vs after (G4); full pytest | none (after close) |
| **S3** | nightly drift scoring: replay each new session per account with params_v2 + **recorded quotes**, append `score.py`; spread model refit only on sessions before the scored ones; owner-inbox alert when rolling 10-session numbers miss TARGETS | test: recorded quote overrides the modelled spread when present (extend tests/test_replay_livecal.py); first G1 re-read at 10 quote sessions (≈ 12-02) | quotes from 11-18 |
| **S4** | one shared exit walker (`mcf/replay/walk.py`): re-walks exits for E3 entry events with broker.py's fill functions, for stop / target / time-exit tunes; entry-condition tunes use the existing `python -m mcf.replay run --setup X --module PATH --alone` | G5 on 5 sessions × 3 accounts (≥ 99% same exit, \|ΔR\| ≤ 0.005R); measure G3 | S2 |
| **S5** | 2-year replay (USAGE item 3) runs + overlap check; nightly increment as store-bars adds months | G2a/G2b per research/replay2y/PLAN.md | packs |
| **S6** | port consumers, one PR each: (a) ledger check → E3 on the last 20 live sessions per account, entry reverted vs current, LR8 R; (b) Workbench RULES "replay + 2-year backtest" → "Session replay + 2-year replay" through S4; (c) backlog re-test → E3 alone-mode; (d) Generator: keep the E2 screen for picking, add an E3 alone-mode confirm on stored live sessions before `--apply` (label "Session replay", weight 0); (e) "2-year backtest" column → E3y; (f) `mcf.cli backtest/demo` → wrapper printing the replay command; (g) setup_screen.py, rescore_bt.py, orb20_a mechanic → archived with a pointer | per port: a fixture test (synthetic session) proving the new path runs and reports the same columns; G6 counts ports | S4 (b), S5 (e) |
| **S7** | side-by-side period, 10 sessions: reviews show old and new numbers in separate labelled columns; per setup / family improve-worsen counts; no verdict uses the old number | disagreement report per setup | S6 |
| **S8** | retire: delete `Backtester` / `allocate` and E1-only tests (rewritten on E3 synthetic sessions, test_replay pattern); freeze E4 sims as archives; GLOSSARY "2-year backtest" → "2-year replay" (the "2-year screen" stays as the Generator's candidate pass); RESEARCH_RULES 12 / 21 and Workbench RULES updated; tag `engine-legacy-<date>` for rollback. Optional, separate decision: switch the live what-if from `simulate()` to the S4 walker (live-code change, ledger entry) | full pytest; G1-G7 all green on the latest rolling 10 sessions | G1-G7 |

Rollback at any step: `git revert` of that PR; the legacy engine is tagged before S8.

## 6. Decision code (owner)

- **ENG1-A — adopt the plan + labelling, no code** (recommended now): from today, (1) numbers from E4 sims are
  labelled "Workbench sim (live sessions)", never "replay"; (2) no NEW bespoke simulator is written for a live setup's
  verdict once S4 lands — new studies use E3 / the walker; (3) S1 baseline is queued for after the close once 5 quote
  sessions exist.
- **ENG1-B — housekeeping + ops** (after the close, no behaviour change): S2 helper extraction (byte-identical gate),
  S3 nightly drift scoring with recorded quotes, S4 walker as research tooling.
- **ENG1-C — retirement go** (later): S6-S8, only when every gate in u11_gates.csv is green; Claude reports the gate
  table and asks — never self-approved.

Answer: "ENG1 A", "ENG1 A+B", or "ENG1 no". No setup is promoted, demoted, tuned or moved by this item; the promotion
hold is untouched; L3-gap-slope-fromopen-FD is unaffected (and its 44% replay match is called out as a gate, so no
replay-based verdict on it is trusted until G1g holds).

## Files

PLAN.md, NOTES.md, RESULTS.md, u11_engines.csv (inventory), u11_consumers.csv (who uses which), u11_parity.csv
(feature parity vs live), u11_gates.csv (preconditions with status), u11_census.csv (726 files classified),
code/census.py.

Educational only — not financial advice.
