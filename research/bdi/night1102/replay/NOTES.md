Educational only — not financial advice

# Night 2026-11-02 — workstream "replay": can the replay become a trustworthy, fast, live-like vetting step?

Research only. Nothing in `config/`, setups, exits, the ledger or the backlog was changed. Nothing was merged. The locked block
2024-11-01..2025-02-28 was never loaded (only sessions 2026-10-27..2026-11-02 were replayed). Costs: the production cost layer
(1 bp + $0.01/share per side, +$0.02/share on stop exits, no exit cost on target fills) is applied to live and replay trades in
the same way, on top of the Alpaca-paper fill model (`fills="paper"`, `limit_fill="touch"`).

## Short answer

1. **The 10-29 audit's 75.9% match was mostly an input problem, not a runner problem.** It had two causes: the replay drew
   synthetic spreads, and it ran on a 1,226-name universe while live trades from about 4,700 names. Feeding the replay **what
   live actually recorded** fixes most of it: the NBBO journaled at each signal, the runner's own borrow (ETB) answer of the
   session, and the **full live universe** with the live-prep priors. On the two sessions replayed that way (10-30 and 11-02,
   all five accounts, 1,612 live trades), **trade match goes from 70.2% to 95.8%**: Primary 100%, T1 100%, T2 98.8%,
   Gen 98.8%, Graveyard 92.3%.
2. **The audit still fails on avg R.** The pooled gap is +0.059R (optimistic). Almost all of it comes from one place. On 11-02
   the live Gen journal has **39 submitted market entries with no trade row**. The replay fills them, and they average
   +1.16R. That is a live journaling gap (an ops issue, below), not a replay error. Leave out those 39 and Gen's 12
   broker-reject extras, and the per-account gaps are Primary −0.078 (27 trades; pessimistic), T1 +0.013, T2 +0.034,
   Graveyard +0.017, Gen +0.008. Two sessions are far too few for the ±0.03R band (rule 21 asks for ≥ 10).
3. **For a NEW setup the recorded quotes do not exist.** Live only journals a quote when one of its own signals reaches the
   quote check. A replay with only what a new setup would have gets no better than the old one: 74.1% vs 72.8% on 5 lab
   sessions. That replay uses recorded quotes of the same symbol ≥ 2 minutes away plus the other accounts' borrow answers
   (config C below). Spreads move too fast minute to minute. **The general fix is historical SIP quotes at the live decision
   second** (poll start + the account's median processing delay). Offline, on 300 live quoted signals, that reproduces live's
   spread-skip decision **96.3%** of the time. The current synthetic draw gets 84.5%, and the quote at the poll start 92.6%.
   This is not wired into the replay yet (next step, below).
4. **Speed.** One session through the real runner on one core takes 80–450 s on the lab universe and 300–1,640 s on the full
   universe (Primary → Gen). A new setup replayed alone over 10–20 sessions is therefore a matter of **hours, not weeks**,
   once item 3 is wired in. Until the audit passes on ≥ 10 sessions, rule 21 still says **no replay result may be used, not even
   as a filter**. Tonight's numbers are a diagnosis, not a clearance.

## What was run (every configuration counted)

Sessions are the post-GX1-fix ones with recordings: 10-27, 10-28, 10-29, 10-30 and 11-02 (lab universe), plus 10-30 and 11-02
(full universe; there was no disk for more: ~30 MB per full session). All five accounts, the real `PaperRunner` via
`mcf.replay.harness.run_session`, frozen `setups/<d>.json` (`--as-live`), and the account config committed before the open.

| conf | universe | quotes | borrow (ETB) | account-sessions |
|---|---|---|---|---|
| A (= 10-29 audit) | lab ∩ live (≈ 570–1,190 names) | synthetic draw from journaled spreads | session `universe.csv` flags | 25 |
| B | lab ∩ live | **recorded** live NBBO at symbol + minute (±1), else nearest same-day recording ≤ 30 min, else draw | **recorded**: own answer, else other accounts' | 25 |
| C ("new setup") | lab ∩ live | recorded quotes of the symbol only ≥ 2 min from its own minute, else draw | other accounts' answers only | 25 |
| FA | **full live universe** (≈ 4,700 names, live-prep priors via the real historical client) | draw | flags | 10 |
| FB | full | recorded (as B) | recorded (as B) | 10 |
| FC | full | as C | as C | 10 |

**Total: 6 replay configurations, 105 account-sessions, 0 errors.** Separately, there were 6 offline quote predictors (no
replay; see the quote section). Nothing was tuned on the results. Every configuration is reported.

## Results

Match = live trades with a replay trade of the same setup + symbol + decision minute / all live trades. Gap = replay − live
avg R after costs. Rule-21 bar: match ≥ 95%, |gap| ≤ 0.03 per account and overall, never optimistic.

### Lab universe, 5 sessions (10-27..11-02; 4,369 live trades)

| account | live trades | A match | A gap | **B match** | B gap | C match | C gap |
|---|---|---|---|---|---|---|---|
| Primary | 115 | 78.3% | −0.054 | **93.9%** (in-univ 99.1%) | −0.003 | 82.6% | −0.086 |
| Testing 1 | 605 | 78.2% | +0.017 | **88.3%** (99.3%) | +0.004 | 79.3% | −0.001 |
| Testing 2 | 904 | 82.0% | +0.002 | **89.6%** (97.5%) | +0.016 | 82.6% | +0.011 |
| Graveyard | 1,847 | 70.0% | +0.053 | **85.8%** (93.4%) | +0.051 | 72.1% | +0.051 |
| Gen | 898 | 65.0% | +0.071 | **72.0%** (90.4%) | +0.068 | 64.9% | +0.066 |
| **overall** | 4,369 | **72.8%** (in-univ 81.7%) | +0.043 | **84.3%** (in-univ 94.7%) | +0.044 | **74.1%** | +0.040 |

With B, every remaining Primary / T1 miss is a symbol outside the lab universe (6 and 67 trades). Spread misses fall from
378 (A) to 22 (B).

### Full live universe, 2 sessions (10-30 + 11-02; 1,612 live trades)

| account | live trades | lab A | lab B | FA match / gap | **FB match** | FB gap | FC match / gap |
|---|---|---|---|---|---|---|---|
| Primary | 27 | 74.1% / +0.097 | 88.9% / −0.005 | 85.2% / +0.048 | **100.0%** | −0.078 | 88.9% / +0.044 |
| Testing 1 | 80 | 80.0% / +0.026 | 92.5% / +0.032 | 87.5% / −0.003 | **100.0%** | +0.013 | 91.2% / −0.011 |
| Testing 2 | 247 | 84.2% / −0.045 | 91.1% / +0.006 | 89.5% / −0.024 | **98.8%** | +0.034 | 88.7% / +0.007 |
| Graveyard | 756 | 66.5% / +0.068 | 82.9% / +0.054 | 73.9% / +0.066 | **92.3%** | +0.029 | 76.1% / +0.034 |
| Gen | 502 | 66.9% / +0.150 | 73.7% / +0.129 | 89.6% / +0.148 | **98.8%** | +0.134 | 90.0% / +0.153 |
| **overall** | 1,612 | 70.2% / +0.075 | 81.9% / +0.070 | 82.1% / +0.072 | **95.8%** | **+0.059** | 83.3% / +0.064 |

Each input separately, same 2 sessions: the full universe alone (FA, quotes still drawn) takes overall match from 70.2% to
82.1%, mostly for Gen (66.9 → 89.6%). Recorded quotes + borrow alone (lab B) take it to 81.9%. Both together (FB) give 95.8%.
Neither alone is enough.

FB residuals, from `compare.py` and the extras breakdown:
- **Gen +0.134 is a live journal gap.** On 11-02, 39 of Gen's 265 submitted entries (all market orders, 09:55–12:35,
  mostly held to the flatten in the replay) have no row in the live `trades` table. No other account has a single such case
  10-27..11-02. The replay's versions of them average **+1.16R**, and 12 live broker rejects (Alpaca) average +0.68R in the
  replay. Leave out both and Gen's gap is **+0.008**. So Gen's reported 11-02 live R (−75R raw) is probably missing these
  trades. **This needs an ops check of the Gen account's 11-02 fills / reconcile.** It is not a replay fix.
- **Graveyard 92.3%** comes from path dependence. The −2R per-setup latch fires at a different time once one earlier trade
  differs (43 live-only, 97 replay-only), plus 32 live broker rejects that the simulated broker accepts. Without the
  reject extras the gap is +0.017.
- **Fills on matched trades:** the R difference is +0.000 to +0.011 for T1 / T2 / Gen, +0.033 for Graveyard and −0.054 for
  Primary (27 trades). On the 5 lab sessions, matched **stop** exits are where the replay is too kind: T2 +0.061R and
  Graveyard +0.081R per stop exit (live stop fills slip more than the model's stop-or-open fill). Primary / T1 / Gen stops:
  −0.002 to +0.030. That is the next fill-model item (a live-calibrated stop slippage); it was not changed tonight.
- Exit reason agrees on 96–99% of matched trades.

## Diagnosis of the 10-29 75.9% (causes, now measured)

| cause | 10-29 audit share of misses | tonight | fix |
|---|---|---|---|
| **universe** (lab 1,226 vs live ~4,700; Gen and Graveyard trade many non-lab names) | 283 / 663 | fixed in FB (full universe + live-prep priors; also fixes Gen breadth / ranking contexts: Gen "no replay signal at the minute" 44 → 0) | `prep_full.py`; store universe file |
| **spread** (synthetic draw vs real NBBO) | 228 / 663 | fixed in B/FB with recorded quotes (spread misses 378 → 22 lab, → 6 full) | recorded quotes; for new setups: historical NBBO at the decision second (offline 96.3%) |
| **borrow / ETB** (live asks the broker intraday) | inside "other" | recorded answers per account-session (B: 37–241 overrides per session) | recorded borrow |
| −2R latch / caps path dependence | 93 | remains (Graveyard) | none possible without identical upstream trades; shrinks as the upstream match improves |
| broker rejects / unfilled | 20 extras | remains (Graveyard 32, Gen 12 rejects + 39 journal gap) | model Alpaca rejects; ops check of Gen 11-02 |
| **poll timing** | not measured on 10-29 | live submits 22–80 s (median; p90 38–143 s) after the poll start: Primary 28 s, T1 22, T2 56, Graveyard 42, Gen 80. The replay decides at hh:mm:03 with zero latency. It hardly moves matched R (above) but it sets **when** the live quote is taken | use poll start + delay for historical quotes |

## Quotes for signals with no recording (what a new setup needs)

On 6,209 live quoted signals 10-27..11-02 (26.2% spread skips), live's spread-skip decision (> 30 bps or > 25% of the stop) was
predicted from:

| predictor | coverage | decision agreement |
|---|---|---|
| current replay draw from the symbol's journaled spreads (the pool includes the true value) | 100% | 84.5% |
| nearest recorded quote of the same symbol, 2–30 min away | 36.5% | 85.1% (draw on the same rows 82.3%) |
| nearest recorded quote, 2–5 min away | 7.1% | 79.5% |
| historical SIP NBBO at the journaled poll-start time (`hist_quote_check.py`, 398 quotes) | 100% | 89.9% (identical bid+ask only 10.3%) |
| historical NBBO at poll start (`hist_quote_delay.py`, 300 quotes) | 99% | 92.6% |
| **historical NBBO at poll start + the account's median delay** | 100% | **96.3%** |
| (oracle: first quote equal to the journaled one) | 100% | 100% |

The live quote is taken 0–120 s after the journaled poll time (median ~25 s, from matching the journaled bid/ask in the tape).
So a historical quote at the right second is close to the real thing, and nearby recorded quotes are not.

## Can replays vet a new setup in hours instead of weeks?

**Not yet. Within reach.** What it needs, in order:
1. **Wire historical quotes in** (two-pass replay: pass 1 lists the (symbol, minute) quote requests, then a read-only fetch of
   the SIP NBBO at poll start + account delay, then pass 2). Expected to bring the "new setup" configuration from C's ~74% up
   to around FB's level on spread decisions. About 700 quote requests per Graveyard session; minutes, not hours.
2. **Re-run this audit (FB-style inputs, plus the step-1 quotes as the FC equivalent) on ≥ 10 post-fix sessions.** The disk
   needed is about 30 MB per full-universe session (bars + priors), so this needs ~300 MB or a rolling store (fetch, replay,
   delete).
3. Fill-model items: live-calibrated stop slippage (T2 / Graveyard stop exits +0.06 to +0.08R too kind) and Alpaca bracket
   rejects. Plus the ops check of Gen 11-02 before Gen's live R is used for anything.
4. Then judge rule 21 per account. Primary / T1 / T2 are already at 98.8–100% match with recorded inputs. They are the first
   candidates to clear.

Speed per session on one core: lab universe 80 s (Primary) to 450 s (Gen); full universe 300–600 s (Primary..Graveyard) and
1,640 s (Gen, all setups). A single new setup replayed **alone** carries far fewer setups than an account. 20 sessions is
therefore a few CPU-hours at most, against 2–4 weeks of live exposure in a testing account. It still cannot replace live:
live remains the judge. The replay would only screen out setups before they take a testing slot.

## Rule / config changes in effect inside the window (research/ledger.jsonl)

All replays use each session's own frozen setups and the config committed before that session's open, so the replay and live
always run under the same rules. Live R across these days still mixes rule changes:
- 10-27: GX1 5-minute clock gate for lab setups (all accounts). This is why the judged window starts 10-27. Session guard;
  setup-load guard; D3 / Z05 moves.
- 10-28: Primary position size ~$4k (slots 77); rotations CWT14-pdl-p10-lowvol, NS4-pm, MF2-base.
- 10-29: Primary per-setup −2R daily stop (latched); Generator paused after the 10-28 run; BAR90 testing bar; K4-2 move.
- 10-30: Testing 1/2 cost filter CF (skip stop-exit cost > 0.15R); promotions L3-rsi5hi-FD and L3-fromopen-FD to Primary;
  D1/D2 graveyard moves.
- 11-02: PDL-1a R2A legs into Testing 2; DM-NS3 graveyard moves. 11-03 (after the window): DM-MF, SO-1A.

Live raw paper R (journal `r_multiple`, before the cost layer) 10-27 / 28 / 29 / 30 / 11-02:
Primary +7.6 / +5.6 / −10.7 / −2.2 / −6.0; T1 −54.0 / −31.2 / +2.5 / +2.9 / −16.3; T2 −31.9 / −37.3 / +9.6 / −13.1 / −32.2;
Graveyard −38.9 / −61.4 / −9.7 / −41.1 / −75.3; Gen +15.9 / −4.9 / −125.4 / −67.7 / −75.1 (11-02 Gen: see the journal gap
above).

## Code

- Research (this folder): `recorded.py` (recorded quotes + borrow per session, a `SimDataClient` subclass monkeypatched into the
  harness per process), `run.py` (configs A/B/C/FA/FB/FC), `prep_full.py` (full-universe store), `compare.py` (wraps
  `research/bdi/replay_audit1029/compare.py`), `spread_predict.py`, `hist_quote_check.py`, `hist_quote_delay.py`
  (+ `hist_quote_delay_sample.csv`), `results.json` (every configuration, per account and per day), `spread_predict_out.txt`.
- **mcf/replay change on branch `claude/replay-fix-1102`** (not merged; research tooling only, no live path):
  `SimDataClient(recorded=...)` uses the journaled NBBO at symbol + minute (±1) before the draw; `store.recorded_inputs(day,
  account)` builds quotes + borrow from the five journals; `harness.run_session(recorded=...)` wires both in and reports quote
  sources in the stats; `store.symbols(day)` reads a store's `universe/<day>.txt`, so a store built for the full live universe
  replays it. Tests: `tests/test_replay_recorded.py` (4 tests, plus `test_replay*.py` all green: 12 passed). The branch omits
  the research-only "nearest recording" fallback (config B used it for 4–27 quotes per session; exact-minute recordings were
  88–99% of the recorded quotes used).

Reproduce: `MCF_REPLAY_STORE=<lab store> python research/bdi/replay_audit1029/prep.py 2026-10-27 2026-11-02`;
`MCF_REPLAY_STORE=<full store> python prep_full.py <lab store> 2026-10-30 2026-11-02`; `run.py A,B,C 2026-10-27..2026-11-02
--journals <dir of the five journal.db copies>`; `run.py FB,FC,FA 2026-11-02,2026-10-30 ...` on the full store;
`compare.py <run dir> <confs> [--full-universe <store>/universe]`.
