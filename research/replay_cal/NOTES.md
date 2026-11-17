# Replay calibration (owner "replay calibration yes", 2026-11-16) — results

*Educational only — not financial advice. Session replay (docs/GLOSSARY.md) through the real live runner, calibrated
to each account's live session, scored against the live paper journals with the targets pre-registered in
[TARGETS.md](TARGETS.md) (committed before any scoring; addendum A written after TRAIN and before the held-out run).
Held-out = 11 sessions 2026-11-02..2026-11-16 × Primary, Testing 1, Testing 2, scored once with the frozen code
(commit bce41ba5c) and parameters (`params_v2.json`). Full tables: [heldout/SCORECARD.md](heldout/SCORECARD.md).*

## Answer first: the 98% target does NOT hold on held-out data

| held-out (pooled, 3 accounts × 11 sessions) | result | target | |
|---|---|---|---|
| trade match (same setup + symbol + side + decision bar) | **87.1%** (2,516 of 2,889 live trades; ±1 min: 87.1%) | ≥ 98% | FAIL |
| extra replay trades | **26.2%** (3,272 replay trades vs 2,889 live) | ≤ 2% | FAIL |
| R bias, matched pairs (replay − live, LR8 costs both sides) | **+0.005R**, 95% CI [−0.008, +0.018], session-clustered | within ±0.01R, not optimistic | mean in band, not significantly optimistic; CI wider than the band |
| total R | replay −360.9R vs live −381.7R (+0.007R per live trade: **rosier**) | — | optimistic |
| daily R correlation / sign agreement (33 account-days) | **0.945 / 94%** | ≥ 0.95 / ≥ 90% | FAIL (just) |
| skip-reason match (all live signals) | **77.7%** | ≥ 95% | FAIL |
| worst day | live and replay pick the same worst day for Testing 1 and 2, not Primary (11-10 live −34.8R, replay −24.5R) | all accounts | FAIL |

Per account: Primary **73.9%** match / 23.9% extra / bias −0.016R; Testing 1 **91.0%** / 25.9% / −0.005R; Testing 2
**89.7%** / 27.1% / +0.017R (CI [+0.000, +0.033]: optimistic). Per setup (42 setups with ≥ 10 live trades, all listed in
the scorecard): median match 90%, median extra 23%; 4 reach ≥ 98% match, 1 also meets ≤ 2% extra. Worst:
L3-gap-slope-fromopen-FD (Primary) 44% match.

**Weight earned: 0** (held-out match < 95% → "below" tier, config/effective_sessions.json). Until a later held-out
check passes, replay sessions should count 0 toward promotion (today the config's `uncalibrated_weight` 0.2 applies
while `replay.match` is null). Proposed values for that block, for the owner/ops step (this research change edits no
config): `"replay": {"match": 0.871, "extra": 0.262, "optimism_r": 0.007, "measured": "held-out 2026-11-02..16"}`.
Haircut if replay R is shown anyway: 0.007 + 0.02 = **0.027R per trade** (the larger of the pair bias +0.005 and the
total-R gap +0.007).

## Where the gap is (held-out, share of live trades; heldout/gap_decomposition.csv)

| cause | live trades the replay missed | replay trades live did not take |
|---|---|---|
| **spread / spread-vs-stop quote checks** | 7.1% | **22.1%** |
| loss latch / halt cascade (Primary −2R latch counted in cost R from 11-12, LR3) | 2.7% | 0.1% |
| no signal on the other side (bar data / late-bar differences) | 1.2% | 1.8% |
| caps / lots / position cascade | 1.0% | 0.7% |
| entered on another bar / unfilled | 0.9% | 1.0% |

**The biggest remaining gap is the quote.** The replay has no recorded quotes; it models the spread from October
quotes, and live spreads at signal time widened through November (median 9.3 → 12.1 → 14.5 bps; 90th percentile
31.7 → 45.2 → 57.5 bps for 10-06..21 / 11-02..11 / 11-12..16; share of signals skipped for spread 20% → 25% → 29%,
partly because Testing A moved to the full universe on 11-12). So the replay lets through many entries live refused for
a wide spread — those extras are what makes replay R rosier. Everything else together is about 6% missing / 4% extra.
On TRAIN sessions with complete priors (10-27..10-30) the same replay matched 91.2% with 5.5% extra and bias +0.008R
(train_v1_fullpriors/SCORECARD.md): the quote gap was smaller there, then grew out of sample — exactly the
rose-coloured-glasses risk the owner asked about.

## Gaps closed (mcf/replay/livecal.py, `python -m mcf.replay run ... --live-cal research/replay_cal/params_v2.json`)

1. **Full live universe per day + its history.** Found: a full-universe replay built the priors (5-minute volume
   profiles, warm-up bars) from no prior-session bars. `store.build_priors_for` now downloads the 24 days of session
   packs first. Before the fix Primary matched 33-56% on the first sessions; after it the signals themselves agree.
2. **Config as traded.** The shared clone was shallow, so `config_at` silently used today's limits for older sessions
   (e.g. the 10-29 Primary −2R latch on 10-22). Deepened; worth a guard (fail loudly when the config snapshot is missing).
3. **Live poll schedule** from the account's poll logs: live poll times (outages / late polls = no decisions), the
   fetch time before decisions and orders, bars that had not arrived at that poll hidden (`late`).
4. **Quotes:** per-symbol / time-of-day table + regression (ADV, price, last-minute range and dollar volume), TRAIN only.
5. **Order latency / fills:** market fills inside the minute bar at open + 0.64 × (close − open) (fit on 2,358 TRAIN
   live market entries, median fill 36 s into the minute) plus half the modelled spread.
6. **Shortability / ETB** from that session's universe.csv. **Caps / lots / twin cascade, halts, latches**: the real
   runner code with the account limits committed before that session's open. **LR8 costs** on each side's own fills.

Not closed: real quotes; revised vs real-time bars; open lots carried across sessions (intraday accounts start flat).

## Next steps (each aimed at the gap measured above)

- **Record quotes live** (largest lever): the runner already queries the quote for every signal it checks; also log a
  spread snapshot per poll for the names any setup is close to triggering on (or the whole universe, one multi-symbol
  quote call), so the replay reads real spreads. Live-code change → backlog / owner, not shipped here.
- **Rolling spread model:** refit the quote model nightly on the last ~5 live sessions (still out of sample for the
  next day) instead of a fixed October table.
- **Nightly drift report (anti-rose-colored-glasses rule 2):** each evening replay the new session with the frozen
  params and append `research/replay_cal/score.py` output; alert in the owner inbox when the rolling held-out numbers
  are below target. The scorer is ready; wiring it into the nightly workflow is an ops step.
- Re-score once quotes are recorded: the target is reachable only if the quote gap closes (the rest is ~6% / 4%).

## Rule / config changes inside the windows (owner rule 2026-11-02, research/ledger.jsonl)

TRAIN 10-22..10-30: MF1-D / D2 moves 10-26; ST-P Primary per-setup −2R latch from 10-29; CF cost filter 0.15R (On Deck,
Testing A) from 10-30. HELD-OUT 11-02..11-16: Testing 2 top-500 pool (UNI1) 11-03; low-rep homes 11-04; Gen temporary
moves 11-09 (reverted 11-10); TEAM-6 Primary 11-10; **11-12 batch** — LR3 Primary loss stops in cost R with open marks,
LR8 live cost model, account halt 300, Testing A full universe, testing generic cap 30, On Deck split-tape gate off,
Gen / Graveyard sizing caps; 11-16 TSZ1 testing sizing, kill-flat-open, shadow mode. The replay uses the setups and
account limits as traded each session, so these sit on both sides of the comparison; the 11-12 batch is where Primary's
latch cascade and the wider-spread universe (Testing A) start.

## Counts and files

Configurations tried on TRAIN: 2 replay runs (v1 calibrated, scored; uncalibrated started and stopped, not scored),
2 spread models compared offline, 1 fill-weight fit; 1 held-out run, scored once. Testing 2 TRAIN covers 4 sessions
(memory limit on 10-28..30). Files: TARGETS.md, params.json / params_v2.json, fit.py, score.py, report.py,
train_v1/, train_v1_fullpriors/, heldout/ (scorecard.json, per_account.csv, per_setup.csv, daily.csv,
gap_decomposition.csv, SCORECARD.md); tests/test_replay_livecal.py.

Educational only — not financial advice.
