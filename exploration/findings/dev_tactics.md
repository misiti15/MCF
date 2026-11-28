# Track 7: development tactics (how MCF can learn faster with its 10 accounts)

Educational only — not financial advice.

Window: live record 10-23..11-27 (25 sessions), all 10 journals, run 1, LR8 R after costs, identical signals once
(35,540 live rows; only 21 cross-account duplicates). Scripts and outputs: `exploration/sandbox/dev_tactics/`.
This track ran no new trading configurations. The statistical checks are diagnostics, not setup searches: 0 configs
added to the ~9,363.

**Rule changes inside the window** (ledger): 10-28 Primary size; 10-29 −2R latch; 10-30 testing cost filter;
11-11 TEAM-6; 11-12 LR8 costs and the account restructure; 11-17 TSZ1 half lots; 11-19 C3 Epoch 1 and U9-TGT;
11-20 stop rounding and FOOTRACE-EXIT; 11-21 cost-basis fix; 11-23 ST7 out, BRAKE-BURST and PSHADOW; 11-27 GYH,
ROT-B3 and the GEN seed. Next: 11-30 AV50 for NM-ETF plus the Friday-review moves. Over the whole window there are
**23 distinct effective dates in 25 sessions** (finding 4), so every live window in this report mixes rule regimes.

## Bottom line (numbers first)

1. **A setup's live record says almost nothing about the setup at today's sample sizes.**
   - True spread between setups: tau = 0.03-0.06R per trade. Day-clustered standard error of a typical record: 0.14-0.16R.
   - A typical record is therefore **3-12% signal** (reliability).
   - Split-half: a setup's first half does not predict its second half (Spearman −0.11 to −0.23, inside the shuffle band).
   - Weekly: last week's top 10 did worse than the field the next week in 4 of 5 weeks (−0.258 vs −0.120 R/trade on average).
   - **Promotions:** the 10 setups that reached Primary with at least 20 earlier live trades averaged **+0.190R before and −0.197R in Primary**. Only 2 of 10 stayed positive. This is the winner's curse the reliability numbers predict.
2. **Most of the noise is one shared day-and-side factor, and it can be removed.**
   - Scoring each trade against the same-day, same-side average ("residual R") cuts the standard error by about 30% (0.158 → 0.114).
   - It roughly triples reliability (0.12 → 0.32), so about 2x fewer sessions are needed for the same t.
   - Paired tests (both arms on the same trades) remove the factor completely. On the real 10-account flow, a paired test needs **3x fewer sessions** than a split-account A/B. For one setup it needs about **10x fewer**.
3. **The shadow run is good enough to carry most of the testing load, and the journals already hold 2.2x more outcomes than live.**
   - Shadow vs live, 11-17..11-27, 11,171 live entries: **98.8% matched**, daily R correlation **0.99**, bias **−0.037R per pair**. Shadow is pessimistic, which is the safe direction.
   - It fails one target: extra entries are 12.3% against a 2% target (mostly On Deck).
   - The trust check (research/shadow/SUMMARY.md, last generated 11-16) still shows 0 entries. The calibration data exists but has never been reported.
   - What-if rows (run 2, signals not taken) number 58,128 against 28,799 live trades. With them counted, 41 of the 90 setups below 30 live trades would reach 30 outcomes.
4. **Rule churn makes every live window a mix of regimes.**
   - About 202 ledger entries took effect from 10-19 to 11-30, about 34 a week.
   - 37 of them touched Primary/default, on 14 distinct dates.
   - A clean 10-session window for any account has not existed since mid-October.
5. **Resources are not the bottleneck.** Account resource skips are 0.2-2.4% of signals (arena_resources 11-17..18).
   - Since 11-20, 72% of signals were skipped. Nearly all skips came from guards: halted (5,802, mostly Primary on 11-25), spread cap 4,231, burst brake 3,162, ETB 2,089, setup daily loss 1,433, cost filter 1,384.
   - Their what-if outcomes are already logged.

**Challenge to the framing.** "More reps per setup" and "more accounts" will not produce decisive verdicts on their own.
- **Sessions are the clock, and the day factor is the noise.** A setup that makes 6 trades a session needs about 35 sessions to show a +0.10R edge at t 2, and about 160 sessions at the lineage bar of 4.3.
- What can be decided quickly is a **paired comparison**: rule A vs rule B on the same signals, on residual R.
- Entry-level edges must be decided on the 2-year bench. Live data can only confirm that it is **not inconsistent** with the bench.

## Evidence

### E1. Verdict status of every setup (10-23..11-27, live, LR8)
| Class | Setups | Trades |
|---|---|---|
| Too few reps (< 30 trades or < 15 traded days) | 178 | 11,889 |
| Unresolved (|day t| < 2) | 45 | 10,286 |
| Decisive negative (day t ≤ −2) | 14 | 6,624 |
| Decisive positive (day t ≥ 2) | **0** | 0 |

- About 2.8 decisive verdicts a week, all negative.
- **Out of sample**, setups already "settled" as losers did not lose more than the rest. `settled_oos.py` classifies a setup as settled if it has ≥ 150 trades and avg R w/o best day ≤ −0.10, or day t ≤ −2. It uses only data up to the cutoff, then scores the next week:

| Cutoff → next week | Settled setups | Share of next week's trades | R/trade settled | R/trade rest | Daily diff t |
|---|---|---|---|---|---|
| 11-06 → 11-13 | 18 | 43% | −0.041 | −0.126 | +1.19 |
| 11-13 → 11-20 | 31 | 34% | −0.144 | −0.164 | +0.53 |
| 11-19 → 11-27 | 45 | 16% | −0.247 | −0.216 | −0.19 |

(The in-sample version said settled setups held 55% of the 11-20..27 trades and 95% of the loss. That number was pure look-ahead. It is reported here only so nobody re-derives it.)

### E2. How real is the spread between setups? (`tau.py`, DerSimonian-Laird, day-clustered SE)
| Metric | Setups | Observed SD of avg R | Median SE | tau (true SD) | Reliability |
|---|---|---|---|---|---|
| Raw R, n ≥ 30 | 108 | 0.212 | 0.158 | 0.059 | 0.12 |
| Raw R, n ≥ 100 | 69 | 0.180 | 0.141 | 0.025 | 0.03 |
| Residual R (minus same-side day mean), n ≥ 30 | 108 | 0.199 | 0.114 | 0.079 | 0.32 |
| Residual R, n ≥ 100 | 69 | 0.146 | 0.094 | 0.067 | 0.34 |

What follows for promotion, using the shrunk estimate = field mean + reliability × (observed − field mean):
- On raw R, a setup must beat the field by about 1R per trade before its expected true edge is even +0.1R above the field. **No live record can justify a promotion by itself.**
- The day-and-side factor explains 13% of trade-R variance and 16% of setup-day variance. The median setup's daily mean correlates 0.52 with its side's daily mean. The 60 setups with ≥ 15 live days behave like about **11 independent bets** (participation ratio; PC1 21%).

### E3. Persistence (`persist.py`, 1,000 shuffles)
| Metric | Min trades | Setups | Spearman H1→H2 | Null 95% band | Top quartile H1 → H2 (all H2) |
|---|---|---|---|---|---|
| Raw | 30 | 89 | −0.233 | −0.204..+0.198 | +0.126 → −0.177 (−0.126) |
| Raw | 60 | 75 | −0.164 | −0.220..+0.217 | +0.114 → −0.198 (−0.156) |
| Raw | 150 | 45 | −0.110 | −0.289..+0.304 | +0.095 → −0.181 (−0.162) |
| Residual | 30 | 89 | +0.061 | −0.211..+0.205 | +0.305 → +0.021 (+0.020) |
| Residual | 60 | 75 | +0.101 | −0.229..+0.225 | +0.297 → +0.005 (+0.000) |
| Residual | 150 | 45 | +0.110 | −0.277..+0.283 | +0.266 → +0.028 (−0.005) |

- On raw R the sign is negative: picking last half's winners loads the next half's losing side and days.
- On residual R the sign turns positive but stays inside noise.
- Weekly top 10 → next week: −0.195 / −0.249 / −0.562 / −0.210 / −0.074, against the field's −0.173 / −0.124 / −0.136 / −0.087 / −0.079.

### E4. Promotions (`promo.py`)
- 10 setups had ≥ 20 live trades before their first Primary session. Before: +0.190R per trade. In Primary: −0.197R.
- Only RW3 (+0.274 → +0.076) and RW5 (+0.380 → +0.049) stayed positive, and both are `1 day` records.
- MF4: +0.262 → −0.406 (−51R). L3-fromopen: +0.172 → −0.046. NM-ETF: +0.301 → −0.230.

### E5. Paired vs split testing on the real flow (`paired_power.py`)
- Illustration rule only, not a proposal (stops are settled research): exit at −0.75R when the MAE reaches it.
- 28,561 trades over 25 sessions.

| Design | Day-clustered SE | Sessions to t 2 at +0.03R/trade | at +0.05 | at +0.10 |
|---|---|---|---|---|
| Paired (same trades, both rules) | 0.0074 | 6 | 2.2 | 0.5 |
| Split A/B (half the flow per arm) | 0.0122 | 17 | 6 | 1 |
| One setup, 6 trades/session, paired | — | — | ~38 | ~10 |
| One setup, 6 trades/session, split | — | — | ~400 | ~100 |

- Per-trade SD of the paired difference: 0.38R. Per-trade SD of R itself: 0.77R.
- Paired tests are only possible for **rule changes on existing signals** (exits, stops, filters, sizing, skips). New entry logic cannot be paired. It has to clear the bench, then a live non-inferiority check.

### E6. Shadow calibration (`mcf.research.shadow_calib.branch_rows`, recomputed tonight, read-only)
| Account | Live entries | Match | Extra shadow entries | Bias (shadow − live) |
|---|---|---|---|---|
| All | 11,171 | 98.8% | 1,740 (12.3%) | −0.037R (t −18; pessimistic) |
| Primary | 241 | 97.9% | 0 | −0.033 |
| On Deck | 957 | 100% | 571 | +0.010 |
| Testing A | 1,627 | 99.9% | 181 | −0.048 |
| Graveyard | 2,641 | 95.0% | 257 | −0.047 |

- Daily R correlation between live and shadow is 0.99.
- Targets: match ≥ 98% passes. Bias never optimistic passes everywhere except On Deck (+0.010). Extra ≤ 2% fails.
- The fix needed is the extra-entry definition or logic, not the fills.

### E7. Free counterfactuals by skip reason (`whatif.py`, 11-12..11-27, GROSS r_multiple)
What-if rows carry no cost basis and their fills are not calibrated, so compare rows only to each other.

| Reason | n | Gross avg R | Day t |
|---|---|---|---|
| Taken (live) | 15,901 | −0.122 | −2.34 |
| Halted | 7,332 | −0.281 | −1.80 |
| Spread cap | 7,220 | −0.142 | −1.49 |
| Not shortable/ETB | 4,974 | −0.219 | −1.66 |
| Setup daily loss limit | 4,879 | −0.120 | −0.69 |
| Burst brake | 3,160 | −0.377 | −2.69 |
| Cost filter | 2,365 | −0.283 | −2.03 |
| Max positions for this setup | 1,576 | **+0.275** | +1.52 |
| Max concurrent positions | 865 | −0.220 | −4.37 |

- The burst brake and the cost filter skip trades that are worse than the trades taken, so as guards they look right.
- The per-setup position cap skipped 1,576 signals from 16 setups that averaged +0.275 gross (t 1.52). That is a lead for the backlog, not a change.
- Every guard can be scored like this each night at no cost, but no report does it today.

### E8. Where the reps go (11-20..11-27, `accounts.py`)
| Account | Trades/session | Setups | R/trade |
|---|---|---|---|
| Graveyard | 344 | 54 | −0.162 |
| Testing E | 202 | 23 | −0.059 |
| Testing A | 171 | 23 | −0.092 |
| Testing F | 153 | 23 | −0.380 |
| On Deck | 147 | 13 | −0.536 |
| Testing D | 121 | 17 | −0.014 |
| Testing C | 115 | 24 | −0.552 |
| Testing B | 113 | 25 | −0.171 |
| Gen | 90 | 15 | −0.139 |
| Primary | 28 | 5 | −0.407 |

- The Graveyard alone takes 23-51% of all live trades each week. Out of sample, its R/trade matches the rest of the field.
- The whole 10-account flow is about 1,150 trades a session. Primary is about 38 (943 / 25).

### E9. Speed of the loop
- **Idea → bench verdict:** fast. Of the 163 backlog rows with a dated verdict note, 136 were judged the same day they were added (median 0 days).
- **Approval → live:** median 1 day, p90 2.
- **Live → decisive verdict:** never positive so far (E1). Forward bars are 15-25 sessions, and at the effect sizes seen (+0.03..0.05R) even those are underpowered unless paired (E5).
- **Owner queue:** 15 cards open in decisions.json, some open for more than 3 nights (ODP2).
- **Tests:** 1,077 tests in 129 files. Collection takes 5.7 s. A full serial run measured tonight: **1,076 passed / 1 skipped in 637 s (10.6 min)**. The **30 slowest tests (2.8%) take 300 s, about 47% of the run**; one of them (test_pollspeed synthetic day) takes 70 s. The machine has 4 cores and no pytest-xdist; the repo has no CI test workflow.
- Two cheap fixes (housekeeping, not part of the proposals): a `slow` marker so the quick loop skips the slowest 30 (quick loop about 5.6 min; the full suite still runs before merge), and pytest-xdist `-n 4` (about 3 min if the tests are isolated). Either could double the number of merge cycles per hour (`pytest_durations.txt`).

### E10. Overfitting budget (`bar_power.py`; i.i.d. approximation, so day clustering makes it worse)
| Configs N | Median null max |t| | Bonferroni 5% bar |
|---|---|---|
| 1,000 | 3.48 | 4.06 |
| 9,363 (lineage count) | 4.04 | 4.55 |
| 32.9M (sum of backlog `configs_tried`, grid sweeps included) | 5.66 | 6.04 |

Chance that a **real** edge passes t ≥ 4.3 on the bench:

| Bench trades | +0.03R | +0.05R | +0.10R |
|---|---|---|---|
| 500 | 0% | 0.2% | 8% |
| 2,000 | 0.5% | 8% | 93% |
| 5,000 | 6% | 62% | 100% |

- The bar is right about false positives. But it has **under 10% power for the +0.03-0.05R edges this book could realistically have**, unless the setup trades at least 5,000 bench lots.
- The two N counts (9,363 vs 32.9M) give different bars. One N policy is needed.
- A two-stage design restores power without inflating false passes: a bench screen at t ≥ 2.5 on a discovery split, then a **pre-registered, paired** forward on new data, where N = 1 per test.

## Confidence: **medium-high** for findings 1-3, **medium** for the proposals
- The reliability, persistence and promotion results agree with each other and with prior research ("last week's rank does not predict next week's", 60/60 in-sample tunes lost).
- But they rest on 25 sessions, which is about 11 independent bets, in a regime with heavy rule churn.
- The paired-power figures use an MAE-based illustration rule; real exit counterfactuals need minute bars.
- What-if fills are uncalibrated.
- The pytest timing is a single run on a shared machine.

## Sources
- Journals origin/mcf-data* (10 accounts, run 1 / 2 / 3)
- docs/live/arena_reps.json, arena_resources.json, pipeline.json, replay.json, assignments.json, decisions.json
- research/shadow/SUMMARY.md, research/ledger.jsonl, research/backlog.jsonl
- mcf/report/footrace.py, mcf/research/shadow_calib.py
- exploration/PRIOR_RESEARCH.md
- Scripts: exploration/sandbox/dev_tactics/*.py, outputs *_out.txt, setup_reps.csv

## PROPOSAL candidates (each subject to owner approval; none touches Primary rules)

### PROPOSAL 1: PAIRED-CARD scoreboard (offline paired counterfactuals for the pending rule cards)
- **What:** each night, a research script replays the actual live trades of all 10 accounts (about 1,150 a session) under each pending rule card, using the stored 1-minute bar packs, and scores the **paired** difference per day on R after costs.
  - Cards: LATCH-OPEN; RW3/RW5 1.25x target; L3 first-lot-only under LATCH-OPEN; spread-floor F6/F8 skip, with a spread term added to the cost.
  - For skip rules, the counterfactual is the existing live or what-if outcome.
- **Baseline:** the same trades as actually executed.
- **Duration:** 10 sessions, 11-30..12-11, reported once on 12-11 (no peeking decisions).
- **Success, per card, pre-registered:**
  - (a) paired day-clustered t ≥ 2 in the bench direction;
  - (b) the sign holds without the best day;
  - (c) at least 60% of the affected setups improve, and the losers are listed with their size (remedies rule);
  - (d) the effect is within 2 SE of the bench estimate.
  - A card with t ≤ 0 is dropped.
- **Expected effect on weekly R:**
  - Direct: 0.
  - Indirect: a real +0.04R/trade change on Primary's ~30-38 lots a session is worth about +1.2-1.5R/week. It gets adopted 3-6 weeks earlier (2-6 sessions paired vs 15-40 now).
  - Range 0 to +1.5R/week per card. Zero if the cards carry no real effect.
- **Risk:** low. No orders and no config changes. A counterfactual on bars is not a live fill; the shadow's −0.037R bias is the yardstick.
- **Monday start:** **yes**. Offline research on journals and bar packs; nothing in the live system changes.

### PROPOSAL 2: RESIDUAL-SHRUNK score as a shadow leaderboard beside FOOTRACE
- **What:** next to the current live ranking, publish each setup's residual R (trade R minus the same-side, same-day mean across all accounts), shrunk by reliability (tau 0.07, per-setup SE), with avg R w/o best day and the best-day share. No setup moves on it yet.
- **Experiment:** freeze two rankings on 12-11 (data 11-30..12-11): (A) FOOTRACE / raw live score, (B) residual-shrunk. Score their top quartiles on 12-14..12-28.
- **Control:** 1,000 random size-matched quartiles.
- **Success:** B's top quartile beats A's by ≥ 0.05R/trade with paired daily t ≥ 2, and sits above the 95th percentile of random. Otherwise drop B and stop live-record promotions until the bench clears them.
- **Expected effect on weekly R:**
  - Direct: 0.
  - If B works, the promotion pick improves by at most about tau × √reliability ≈ +0.03-0.04R/trade over the field. On Primary that is about +1-1.5R/week.
  - It also avoids the past pattern of +0.19 before → −0.20 after promotion. Range 0 to +1.5R/week.
- **Risk:** low (reporting only). Main risk: 10 + 10 sessions is still short, and a null result is likely.
- **Monday start:** **yes**, as a research script on the journals.

### PROPOSAL 3 (structure, proposal only): split information from exposure; "frozen blocks + twin lane"
1. **Testing A-F in frozen 2-week blocks.** At most one rule change per account, only at the Friday epoch. Each block carries one pre-registered question.
   - Today there are 23 effective dates in 25 sessions.
   - Low-rep triage counts calibrated shadow and what-if outcomes. Live reps confirm. 41 of 90 low-rep setups would reach 30 outcomes now.
2. **Graveyard → shadow-only** (no paper orders). Its setups keep full reps through the shadow (95% match, bias −0.047, pessimistic).
   - That frees one paper account and about 23-51% of the live flow.
   - It needs an owner decision, because the Graveyard rules (GY-LIFE, foot race) assume live trades.
3. **The freed account becomes a TWIN lane:** an exact paper copy of Primary's book plus exactly one candidate change per block.
   - This gives a **real-fill paired** test of the change against Primary on identical signals. A +0.10R/trade change on ~30 lots/session reads at t 2 in about 2-4 sessions; +0.05R in about 8-15.
   - It requires the owner to ask for a copy ("Promotion = move" forbids copies otherwise).
- **Expected effect on weekly R:**
  - Direct on Primary: 0.
  - Decisive verdicts per week: from about 0 positive / 2.8 negative (and the negatives not predictive) to about 1 paired verdict per change per block, plus one per frozen testing block.
  - Value depends on how many changes carry real effects; range 0 to +3R/week after 4-6 weeks.
- **Risk:** medium.
  - Organizational: owner rules on copies, the Graveyard and trimmed setups.
  - Turning off Graveyard paper orders loses some execution-cost data. Mitigation: keep 1-2 Graveyard leaders live as a cost sample.
- **Monday start:**
  - Frozen blocks: **yes** for testing accounts, if the owner approves it as a process rule; no Primary change.
  - Graveyard → shadow and the twin lane: **no**. They need owner decisions and a config change outside market hours, so the earliest start is the 12-04 Friday epoch.

Educational only — not financial advice.
