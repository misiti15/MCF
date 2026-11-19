# REPS2 — faster, usable reps (shadow score, real-quote replay, low-rep fast lane, early decisions)

*Educational only — not financial advice. Research and display only: no setup, exit, account, config or ledger change.
Owner: REPS2 yes (2026-11-17: "we have to be able to more quickly identify the 0 or low trade setups that could have
high potential that would otherwise take a month to test out through live"); USAGE items 1-3 yes (2026-11-18). Data:
every mcf-data* journal as of the 11-18 close (16:00 ET push); live R after costs (LR8, `mcf.costs.cost_r`).*

Nightly (one scripted scorer, USAGE1 3f): `python research/reps2/nightly.py --replay` after the data branches are
fetched → `research/reps2/nightly/<day>.md` (one inbox block) + `history.jsonl`. Without `--replay` it skips the ~1 h replay.

## 1. Shadow score (shadow-of-live vs live, 11-17 + 11-18) — `research/reps2/shadow/`

| | 11-17 | 11-18 | pooled | target |
|---|---|---|---|---|
| match (same setup/symbol/side, decision bar ±1) | 98.2% | 99.2% | **98.6%** (2,646 of 2,683 live entries) | ≥ 98% |
| extra (shadow entries live did not take, not resource-blocked) | 0 | 1 | **0.0%** (509 more were blocked live by slots/caps — expected, not extra) | ≤ 2% |
| R bias, matched pairs (shadow − live, both after costs) | −0.036R | −0.066R | **−0.049R** (t −12.0, 2,646 pairs) | \|bias\| ≤ 0.01R, never optimistic |
| daily R correlation (setup-days) | | | **0.993** | ≥ 0.95 |

Per account: match 94.0% Graveyard, 95.8% Primary, 99.8% Testing A, 100% elsewhere; bias −0.014R (On Deck) to −0.081R
(Primary). Per family (58, all in `SUMMARY.md`): CWT14 96.5%, L3 94.7%, RW3S 93.9%, every other family with entries 100%.

**Reading.**
- Shadow reproduces live *entries* almost perfectly. That is partly by construction: shadow-of-live is handed the same
  signals at the same polls. The real information is the R gap.
- Shadow is **pessimistic, by −0.049R per trade**. That is the conservative "fills B" profile working as designed
  (the owner expected −0.02 to −0.03R). It is outside the ±0.01R band of TARGETS T3, but not optimistic, and the tier
  rule (config/effective_sessions.json) only blocks optimism.
- Two families are optimistic: MF2 (+0.063R) and LIQ (+0.043R, 2 trades). MF2 is held at the 0.2 "partial" tier.
- Once 3 days are scored, the fill check will most likely say "harsher than needed → ease to A". That stays the
  owner's call; no change is proposed tonight.

**Tier and earliest date.** Today every family is `uncalibrated` (config: ≥ 3 held-out days AND ≥ 30 live entries per
family). The earliest is **after the 11-19 close (3rd day)**. Families with ≥ 30 live entries that are on track then:
- 0.35 "calibrated": 15 families, including GEN, RW7, RW1, exhaustion_short, CWT13, MF4, NM.
- 0.2 "partial": 3 families (CWT14 96.5%, MF2 +0.063R and heat_fade_long +0.011R optimistic).
- "below" (weight 0): 2 families (L3 94.7%, RW3S 93.9%).
- Families with fewer entries need 2 to 58 more sessions; 10 have no live entries at all (`projection.json`).

**SRCV1 still governs the blend.** Shadow stays a separate column, with blend weight 0, until
`research/src_value/score.py` shows that shadow predicted *later* live results. Its first possible measurement is the
monthly run on **Mon 2026-12-07**, once there are ~10 shadow sessions with later live trades. Fidelity (this table) is
necessary but not sufficient.

## 2. Replay with real quotes (11-18) — `research/reps2/replay_quotes/2026-11-18/`

This is the same frozen calibrated replay (params_v2, commit as in research/replay_cal) used for the held-out run. It
was run on 11-18 for Primary, Testing 1 (On Deck) and Testing 2 (Testing A), with a full-universe session pack built
locally from the same Alpaca SIP source as the store-bars workflow. It was run once with the recorded quotes and once
with the modelled ones, and each run was scored with `research/replay_cal/score.py`.

| 11-18, 3 accounts, 377 live trades | **real quotes** | modelled quotes | held-out 11-02..16 (modelled) | target |
|---|---|---|---|---|
| trade match | **100.0%** (377/377) | 85.9% | 87.1% | ≥ 98% |
| extra replay trades | **1.1%** (4; all Testing A) | 31.6% | 26.2% | ≤ 2% |
| R bias, matched pairs | **+0.018R** (CI −0.009..+0.044) | +0.014R (CI +0.002..+0.026) | +0.005R | \|bias\| ≤ 0.01R, not optimistic |
| skip-reason match | **99.6%** | 79.1% | 77.7% | ≥ 95% |

Per account (real vs modelled):
- Primary: 100% vs 57.1%.
- On Deck: 100% vs 85.5%.
- Testing A: 100% / 1.5% extra / +0.031R vs 91.4% / 34.6% / +0.019R.

Every quote check in the real-quote run found a recorded quote: 694 real, 0 modelled.

**Reading.**
- **The quote was the gap.** With the quotes live actually saw, the replay takes exactly the trades live took on 11-18.
- What is left is R per trade: +0.018R, rosier, inside noise for one day but outside the ±0.01R band. Testing A
  (+0.031R) carries it, so the next lever is fills/exits, not entries.
- **Limit (stated plainly):** recorded quotes exist only where a live account checked a quote. So the 100% applies to
  replaying the setups an account ran live. For a setup that never ran live (the low-rep use case), the replay still
  falls back to the model, and the modelled number (85.9% / 31.6% extra) is the honest one.
- Closing that would need a per-poll spread snapshot for the names near a trigger (research/replay_cal/NOTES.md next
  steps). That is a live-code change, for the backlog.
- One session is not a held-out test, so nothing changes in config: replay weight stays 0, haircut 0.027R.

**Sessions needed to re-score the 98% target.** TARGETS.md fixed the held-out size at 11 sessions, about 2,900 live
trades.
- Sample size: to show match ≥ 98% at 95% one-sided confidence, assuming design effect ~3,
  - true match 99.5% needs ~180 trades (1 session);
  - true match 99% needs ~800 (3 sessions);
  - true match 98.5% needs ~4,800 (~13 sessions).
- The bias band is the slower one: at about ±0.013R SE per session, showing \|bias\| ≤ 0.01R needs about 7-11 sessions
  if the true bias is near 0.
- **Plan:** re-score nightly (rolling file `replay_quotes/rolling.json`). The formal held-out score comes once **11
  recorded-quote sessions** exist: 11-18..**12-03** (Thanksgiving 11-26 is closed). Its result is what the owner sees
  for the `replay` block of config/effective_sessions.json.
- An early read after 5 sessions (11-24) shows only whether the trend holds.
- Nightly cost is about 1 h of compute for the 6 runs. The script skips the replay until the day's pack is on the
  Release (store-bars ~16:40 ET).

## 3. Low-rep fast lane — `research/reps2/fastlane/LIST.md` (daily)

There are **65 current setups with 0-10 live trades** (all accounts pooled; 15 with 0).

**How the list is ranked:**
- Score = live record + shadow record (−0.02R haircut) + non-live evidence, shrunk together (10-trade prior).
- The evidence is each source less its measured optimism: 2-year screen −0.157R, 2-year backtest −0.064R, replay snapshot as is.
- **Caveat SRCV1:** none of these sources has predicted later live results (Spearman ~0). The score only orders who gets
  exposure first. It is never a verdict and never counts as reps.

Each setup gets the route its own live signal record points to (signals since it joined its current account):

| route | setups | meaning / fastest exposure |
|---|---|---|
| full-universe (rare trigger) | 25 | < 0.5 signals per session where it lives. Slots are not the bottleneck: **shadow-only in a full-universe account** (config `shadow_setups`, no orders, no slots) gives every signal a conservative shadow trade from the next session |
| just-moved (wait) | 17 | joined its account on 11-18/11-19 (C3-EXIT100 / GY-LIFE moves): no record there yet |
| fix-gate | 12 | ≥ 50% of its signals refused by spread / cost filter / ETB. More exposure will not help. Gate review instead (e.g. NM1-cwt09-g10: 69 of 79 signals not shortable/ETB; the U9-ETB bulk borrow list may fix part of this) |
| as-is | 9 | its signals enter; it gets reps where it is |
| check-wiring | 2 | 0 signals although its 2-year screen expects ≥ 3 by now (GEN-261028-04 in Testing F, GEN-261028-01 in Testing A, full universe) |
| spotlight / Graveyard filler | 0 | no low-rep setup loses ≥ 30% of its signals to slots or caps today. Spotlight and filler slots help the *blocked* setups, not the rare ones |

**Fastest route: shadow-only.**
- Shadow already matches live entries 98.6% of the time and is pessimistic, so a shadow-only rep is a fair, cheap,
  conservative preview of the live trade.
- Spotlight and filler slots only reorder slots, and the low-rep setups mostly do not fire, so they gain little.
- Full-universe *live* testing adds risk and slots for setups that fire < 0.5 times a session.
- Proposal REPS2-LANE: the full-universe-route setups go into `shadow_setups` of Testing A (full universe since 11-12),
  re-picked nightly from this list.
  - Shadow reps stay a separate column (SRCV1) and never count toward the On Deck / Primary minimums.
  - A setup whose shadow record looks strong gets a live slot (spotlight / C3-EXIT100 freed slots), where live decides.
  - The shadow CPU budget (`budget_frac` 0.10) is the limit to watch.

## 4. Early decisions — pre-registered SPRT (`PREREG_SPRT.md`, committed and pushed before scoring; `sprt/`)

**The design:**
- Two Wald SPRTs per setup, run on its live, cost-in record with sessions as the unit (same-day correlation ρ = 0.117,
  per-trade σ² = 0.737).
- FAILS tests H1 μ = −0.20R against break-even; WORKS tests H1 μ = +0.20R against break-even.
- α = 0.05, β = 0.20. WORKS is subject to the one-big-day guard. Each test is truncated at 60 sessions / 600 trades.

| true avg R | P(FAIL) parametric / **bootstrap** | P(WORKS) parametric / **bootstrap** | avg trades to stop (bootstrap) |
|---|---|---|---|
| −0.30 | 0.97 / **0.91** | 0.00 / 0.00 | 165 |
| −0.20 | 0.78 / **0.71** | 0.00 / 0.01 | 253 |
| 0 | 0.037 / **0.104** | 0.038 / **0.070** | 396 |
| +0.20 | 0.00 / 0.01 | 0.77 / **0.63** | 279 |
| +0.30 | 0.00 / 0.00 | 0.97 / **0.87** | 192 |

(Bootstrap = 59 setups with ≥ 15 sessions, sessions re-drawn from their own record. That keeps the real fat tails and
day effects.)

**Pre-registered verdict: v1 is NOT fit for decisions.** Its bootstrap false-FAIL rate at break-even is **10.4%**, above
the 10% bar set in advance. Wald's Gaussian bounds hold on the parametric check (3.7%) but not on real records.

**What it would decide now (v1, for information only):**
- Of 207 current setups, **8 FAIL and 1 WORKS**; 198 continue.
- The 8 FAIL are 5 in the Graveyard, 1 each in Testing A, B and E. The 3 testing ones are GEN-261020-03 (Testing B),
  NM-AR-AM-gapdown-capitulation-long (Testing A) and GEN-261026-05 (Testing E).
- The WORKS is RW3-gapdn-rsi5pop-flowsell-short-FD in Primary. It was called 11-06, it has been −0.20R per trade
  since, and its record is now a `1 day` record (best day 73%).
- **Low-rep (0-10 trades): 0 decided.** The test only calls big effects, so it cannot be the low-rep tool. That job
  belongs to §3.

**Walk-forward on history:**
- FAIL calls: 11 of 15 right (73%, Wilson CI 48-89%) against a 72% base rate of later-negative setups. In other words,
  no better than the base rate.
- WORKS calls: 0 of 1 right.

**Salvage: Addendum A (v2, post hoc, NOT for decisions).**
- The call boundary was raised until the bootstrap false-call rate is ≤ 5%. That gave A = 4.5 (7 boundaries tried).
- Power at ±0.20R drops to 53% (FAIL) and 46% (WORKS).
- It decides **0** current setups now.
- It is logged nightly as a forward check. It is offered as a decision only if its calls hold up on sessions after
  11-18. Read: a sound early stop exists only for |avg R| ≳ 0.3R; the C3-ROT 15-day / 30-trade floor is not the binding
  constraint for real-sized edges.

**Configurations tried:** 3 pre-registered (δ = ±0.15, ±0.20 primary, ±0.30) plus 7 boundary values in Addendum A.
Every one is in `sprt/summary.json`.
- δ = 0.15: 4 FAIL, 0 WORKS.
- δ = 0.30: 12 FAIL, 2 WORKS.

## Rule / config changes inside the windows (research/ledger.jsonl)

Live records span 10-06..11-18. Changes inside that span:
- Sizing: TSZ1 testing sizing (11-16) and the 11-12 batch (LR3 / LR8 costs, account halt 300, Testing A full universe,
  testing generic cap 30).
- 11-16: kill-flat-open and shadow mode.
- From 11-18: SRCV1 and ODPREP.
- Plus the earlier moves listed in research/fastdec/NOTES.md.

The shadow window (11-17..18) has no setup/exit change between its two days. The C3 batch (EXIT100 moves, ROT,
NS5 out of Primary, BASE1) and U9-TGT / U9-ETB take effect **from 11-19**. So the 11-19 shadow and replay scores are
the first under them, and the fast lane's "just-moved" rows come from these moves.

Files: data.py, nightly.py, fastlane.py, sprt.py, PREREG_SPRT.md, shadow/, replay_quotes/, fastlane/, sprt/, nightly/.

Educational only — not financial advice.
