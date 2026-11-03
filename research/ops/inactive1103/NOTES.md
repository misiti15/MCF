Educational only — not financial advice

# inactive1103 — which setups have gone quiet, why, and a balanced alarm rule (2026-11-03 ~11:05 ET)

Owner 2026-11-03 ~11:00 ET: "An extensive and tough audit: how many setups have gone inactive for X sessions. Inactive
5 sessions is alarming; 2 sessions maybe less — find a balance. Diagnose what is happening so everything gets as much
playing time as possible, but factor in the load the system can carry. We may need a better plan."

Research / ops only. Nothing in config/, no setup, exit or live-path change, nothing merged. Number of configurations
tried: 0 (an audit; the alarm thresholds below were fixed before the table was read: 5% watch, 1% alarm).

**Answer first.**
- **207 setups are enabled today** (Primary 10, Testing 1 28, Testing 2 46, Graveyard 30, Generated 93).
- **By sessions since the last signal** (completed sessions through 11-02, counted only while the setup was enabled in
  that account; 11-03 counts only as "active today", to ~11:05 ET):

  | | active today | fired last session (not yet today) | quiet 1-2 | quiet 3-4 | quiet 5+ | never fired since enabled | total |
  |---|---|---|---|---|---|---|---|
  | Primary | 7 | 2 | 1 | 0 | 0 | 0 | 10 |
  | Testing 1 | 10 | 9 | 2 | 1 | 1 | 5 | 28 |
  | Testing 2 | 12 | 12 | 9 | 4 | 2 | 7 | 46 |
  | Graveyard | 27 | 3 | 0 | 0 | 0 | 0 | 30 |
  | Generated | 11 | 26 | 25 | 6 | 0 | 25 | 93 |
  | **all** | **67** | **52** | **37** | **11** | **3** | **37** | **207** |

  By sessions since the last *trade*: traded today 50, last session 52, quiet 1-2 50, quiet 3-4 10, quiet 5+ 6, never
  traded since enabled 39.
- **A fixed bar flags too many or too few.** "Quiet ≥ 2" flags 62 setups, "quiet ≥ 5" flags 29 (Gen 15, T2 8, T1 6). For
  the expected-rate rule below (flag only when the streak would happen < 5% of the time at the setup's own expected
  rate), **0 setups are on alarm (P < 1%) and 0 on watch (P < 5%)**. Three are just above the line, at P 5.0-5.4%:
  CWT04-backside-vwaptest-a25-short (T2, 0 in 16), GEN-261027-01 (0 in 3 at about 12/day) and GEN-261029-03 (0 in 3, QQQ-up
  gate met 1 of 3).
- **Diagnosis of the 50 setups quiet ≥ 3 sessions on signals:**
  - **truly broken: 0.** All 5 accounts build every enabled setup with 0 load failures (today's config). Every module
    file exists. Every context column that a quiet setup reads (`breadth`, `breadth_open`, `spy_fo`, `qqq_fo`, `qqq_vwap`,
    `spy_prng`) is also read by a setup that fired on 11-02 or today, so the column is being fed.
  - **not evaluated: 0.** Decision minutes polled: 99.8% for 10-27..10-29 and 98.6% for 10-30 / 11-02 (blocked_audit.md;
    the only misses were 14:40 / 14:45 in every account on 10-30, the hand-over, and the Graveyard at 14:30 on 11-02).
    Today it is 20 of 20 in every account to ~11:05. The full-coverage replay of 10-22 / 10-23 / 10-26
    (blocked1026_replay.json) also gave 0 for the same never-fired names (IDX ×5, LD1-LD8, CWT04 a25 ×2, NM-RWR1,
    GEN-261019-06 / -07).
  - **rare by design: 48.**
    - 12 are index-gated, and their gate was met on at most 1 of the quiet sessions. The window since 10-27 has had no
      up-tape: SPY has not closed a minute > +0.5% from the open in any 13:00-15:00 window since 10-26, and QQQ has not
      been > +0.6% from the open after 10-27 (regime.csv).
    - 36 have P(this streak | expected rate) ≥ 5%. Examples: the IDX index-dip setups fire on ~1-3% of days (P of 12
      quiet = 0.65-0.88); LD1-LD8 run at 0.05-0.42/day; the young GEN setups are breadth / window gated.
  - **blocked: 2 on signals** (LD3 and LD5 each fired once, an opposite-side skip, what-if +0.5R each). There are also
    **4 that still signal but have not traded for ≥ 3 sessions**:
    - **MF4-h40-open-flowsell** (Primary): 10 sessions. 22 of 38 signals were skipped as "twin held" by its own -FD
      copy, plus ETB 7 and spread 9. What-if −6.7R over 31.
    - **NS2-sma50break-overbought-short** (Graveyard): 5 sessions. Twin held by NS2-FD 15 of 31. What-if +4.9R over 19.
    - **ST5-pdbrkup-short-mid-FD** (Testing 1): 8 sessions. Not shortable 5 of 6. What-if −7.1R.
    - **ST3-rsi5up-short-pm-FD** (Testing 1): 3 sessions. ETB / spread / cost filter. What-if +2.9R over 3.
  - **crowded out: 0 setups made inactive by their account's load.** The account-level blocks only trim busy setups that
    already trade a lot, and every such block since 10-27 lost money or was flat in what-if (net of costs):
    - Graveyard per-setup cap: 461 skips, −79.2R.
    - Graveyard buying power: 42 rejects, −0.1R.
    - Generated per-setup cap: 14 skips, −7.4R.
    - The one exception is Generated buying power, 12 rejects at +8.0R. That is the HK-RECON-GEN booking lag.
    - Place in line (a different setup holds the symbol): −14.1 / −28.5 / −36.2 / −59.2 / −6.9R in P / T1 / T2 / GY /
      Gen.
- **The real playing-time problem is not inactivity, it is slow verdicts.** 78 of 207 setups average < 0.5 trades a
  session over their enabled life. 145 are under 3 a session, which is the pace the "20 sessions / 60 trades" judging
  rule needs (median 0.93). Seven are expected under 0.1 a session (IDX1 ×2, IDX2, IDX3, IDX5, LD4, LD5): about 1-2
  trades in 20 sessions, so they can never be judged live in that window.
- **Load: which accounts have room.**
  - **Testing 1 has room**: 28 setups, polls 97-100% and 20 / 20 decisions today, peak 73 of 400 positions, 0
    buying-power rejects.
  - **Primary** is small by design (promotions only).
  - **Testing 2 is CPU-crowded**: 46 setups, 77-94% of 1-minute polls (its lab decisions are all taken).
  - **Generated is CPU-crowded**: 93 setups, 66-85% of polls, peak 144 of 200.
  - **The Graveyard is capital-crowded.** Peak 147-155 of 200, cash $39k of $93k equity at 11:10 ET. It ran out of
    buying power at **10:40 on 11-02 and 10:50 today** (34 rejects by 11:05, 14 of them the two setups that moved in
    today, MF3-FD and MF5-FD). DM-N3 adds 3 more tomorrow.
  - The new accounts (`claude/accounts-3new`, capacity1103 rollout) are where real room comes from.
- **Plan (owner decisions below, codes INACT1 / INACT2 / GY-BP):**
  - a nightly "inactive setups" check with the P-rule: one FYI line, and a DECISION only when a fix needs the owner;
  - rare setups are judged on trade count, not sessions;
  - an optional Graveyard per-setup-cap replay before its buying power binds earlier.
  - No one-off move is recommended. A move adds playing time only when a setup is blocked by its account, and no
    quiet setup is.

**Rule / config changes inside the window** (10-06..11-03, `research/ledger.jsonl` effective dates; they change counts
and blocks, so streaks that cross them are not one regime):
- Graveyard opened 10-21.
- Gen caps GX2 10-26.
- GX1 5-minute lab clock 10-27 (all accounts; the earlier sessions had poll-coverage gaps).
- Primary size ~$4k 10-28.
- Primary −2R per-setup stop and generator paused 10-29 (no GEN setup is younger than 10-29).
- BAR90 10-29.
- Testing 1/2 cost filter CF 10-30.
- L3 pair to Primary 10-30.
- R2A legs into T2 and NS3-FD / RW4-FD to the Graveyard 11-02.
- MF3-FD / MF5-FD to the Graveyard, SO-1A and RW3S into T2 11-03.
- DM-N3 (NS5-FD, ST4-FD, RW6G1-FD → Graveyard) from 11-04.

The ET clock moved from EDT to EST on 11-01.

## Method

Script `audit.py` (`python research/ops/inactive1103/audit.py <scratch> [<today>]`); output `table.csv` (one row per
enabled setup × account, 207 rows, all columns) and `results.json` (counts, causes, alarms). `regime.py` writes
`regime.csv` (SPY / QQQ % from the open per session, SIP 1-minute bars).

- **Enabled sessions**: each account's frozen `setups/<day>.json` on its data branch (the runner's snapshot, so every
  move / promotion is already in it) plus 11-03 from the config at the last commit before 09:30 ET (f2c27966: it
  includes RW3S, and not DM-N3, which starts 11-04). A setup's life = its current run of consecutive enabled sessions
  in that account ("since" in the table; for a moved setup this is the first session in the new account, the same as
  `docs/live/assignments.json` first_session).
- **Signals / trades**: journal `signals` run_id 1 (any status) and `trades` run_id 1. Blocks come from the signal
  reasons (`mcf.report.playing_time.classify`). What-if R is run_id 2, net of the production cost model ($0.01/sh + 1 bps
  per side, +$0.02/sh on stops), as in blocked_audit.md.
- **Expected rate**, in this order:
  - the generator screen (`research/generator/expected_live.json` counts60: share of zero-signal sessions in its last 60
    screen sessions);
  - `research/bdi/playingtime/expected_rates.json` / time-of-day study / validation (via
    `mcf.report.playing_time.expected_rates`);
  - "X/day" notes in the account configs (order-list comments);
  - `research/**/verify*.json` per_day;
  - hand-read notes for IDX (idxdip1015: dip days in 2 years) and the swarm1017 near-misses (n over ~480 sessions;
    NM-RWR1 "654 trades on 78 sessions").
  - Only RW3S (day 1) has none. R2A-short is a regime leg with no single rate.
- **P(quiet streak)**:
  - With a zero-day share z (screen, or days-with-a-signal from the research note), P = z^N.
  - With a rate λ only, signals come in clusters, so P = exp(−λ/3)^N (a day with signals carries ~3 of them). This is
    deliberately less alarmed than plain Poisson exp(−λN).
  - The live estimate (zero-signal share before the streak, Laplace-smoothed) is in `p_quiet_live` for reference. It is
    noisy at ≤ 18 sessions and is not used for the flag.
- **Index gate**: the gate written in the setup name (SPYgt0p5, QQQgt0p6, SPYltm0p25, spyup05, qqqup ...) checked on
  SPY / QQQ 1-minute closes inside the setup's window for each quiet session.
  - This is an upper bound on qualifying sessions, because the other conditions also apply.
  - "≤ 1 qualifying session" counts as rare by design.

## 1. The balanced rule: quiet sessions that would be surprising at the setup's own rate

Flag a setup when its quiet streak N (completed sessions enabled in that account with 0 signals) has
P(N quiet | expected rate) below a threshold:
- **watch** when P < 5% (FYI line);
- **alarm** when P < 1% (diagnose the same night).

A setup whose index gate (from its name) was met on ≤ 1 of the quiet sessions is exempt, because its condition never
happened. The same rule runs on the trade streak for setups that still signal (blocked, see §2).

What this means in sessions (clustered rate, P = exp(−λ/3)^N):

| expected signals / session λ | watch after (P < 5%) | alarm after (P < 1%) | examples |
|---|---|---|---|
| 20 | 1 session | 1 | busiest FD / GEN setups |
| 10 | 1 | 2 | GEN-261020-05 (9.3) |
| 5 | 2 | 3 | NS2-sma50break (5.7) |
| 3 | 3 | 5 | GEN-261028-06 (3.0) |
| 2 | 5 | 7 | NM-RWN4 (index gated) |
| 1 | 9 | 14 | NS1-rsidip (0.9); NM-RWR1 1.4 but zero-day share 0.84 → 17 / 26 |
| 0.3 | 30 | 46 | LD1, CWT04 a25 |
| 0.1 | 90 | 138 | IDX ×5, LD4, LD5 |

The owner's instinct holds: "5 sessions is alarming" is right for a 2-3/day setup, and "2 sessions" for a 5-10/day one.
But no single number fits a book where expected rates run from 0.01 to 49 a session. With a fixed 5 the check would
call 29 setups alarming today, and every one of them is explained by rate or regime.

**What to do, per cause (in this order):**

| cause | test | action | who |
|---|---|---|---|
| broken | module missing / load failure / exception in the job log / a context column that no setup can read / replay fires but live does not | fix the bug the same night | housekeeping (no decision) |
| not evaluated | its decision minutes missed (poll log), outside the universe or watchlist (min_adv), NaN features | fix (OPS-HANDOVER, universe) | housekeeping; DECISION only if a timing rule changes |
| blocked — place in line | ≥ 50% of its streak's signals lost to "twin held" / lot cap / already in symbol / opposite side | own twin: leave alone, report the pair as one; another setup: adjust setup_order if the what-if of the lost signals is ≥ 0 over ≥ 10 signals | owner DECISION (setup_order) |
| blocked — account load | slots full / buying power / per-setup cap / trades cap | move to an account with room only if the what-if of the blocked signals is ≥ 0 over ≥ 10 signals | owner DECISION (move) |
| blocked — intended filter | ETB / HTB, spread, split-tape gate, cost filter CF, −2R setup stop | leave alone; FYI only | — |
| rare by design | P ≥ 5%, or index gate not met | leave alone; count it in the slow-verdict list (INACT2) | — |
| unexplained | P < 1% and none of the above | one-session replay with `python -m mcf.replay run --as-live` for that account; if replay fires → broken, if not → rare | housekeeping |

## 2. Diagnosis of every setup quiet ≥ 3 sessions (signals or trades)

| account | setup | quiet sig / trade | expected / session | P(streak) | cause | detail |
|---|---|---|---|---|---|---|
| Primary | MF4-h40-open-flowsell | 0 / **10** | 7.2 | — | blocked: place in line (own twin) | 38 streak signals: twin held 22 (MF4-h40-FD 18), spread 9, ETB 7; what-if −6.7R / 31 |
| Testing 1 | IDX1 trail / IDX1 hold / IDX2 / IDX3 / IDX5 | 12 / 12 (never) | 0.01-0.04 | 0.65-0.88 | rare by design | index dip by 09:45-09:55 on 5-17 of ~480 days; checked on SIP bars: the deepest dip by 09:55 in 10-16..11-03 was SPY −0.30% (needs ≥ 0.5-0.75%) and QQQ −0.65% (needs ≥ 1.0%), so the condition never occurred |
| Testing 1 | ST5-pdbrkup-short-mid-FD | 1 / **8** | 0.78 | — | blocked: borrow | 6 streak signals: not shortable 5, spread 1; what-if −7.1R |
| Testing 1 | ST3-rsi5up-short-pm-FD | 0 / 3 | 1.35 | — | blocked: intended filters | ETB 1, spread 1, cost filter 1; what-if +2.9R / 3 |
| Testing 1 | ST6-volspikeup-short-mid-FD | 3 / 3 | 1.24 | 0.29 | rare by design | 23 signals in 16 sessions |
| Testing 1 | LIQ-pdl-sweep-open15-vwap-long | 11 / 11 | 0.38 | 0.25 | rare by design | 1 signal in 15 sessions (live z 0.99) |
| Testing 2 | NM-RWN4-ns2-spyup05-notfri-short | 5 / 5 | 2.11 | 0.03 | rare: index gate | SPY > +0.5% in 09:50-11:30 on 1 of 5 (11-02, 0.57%) |
| Testing 2 | NM-RWR4-ns2-up3-qqqup-slopedn-short | 5 / 5 | 1.5 | 0.08 | rare by design | QQQ-up gate met 4 of 5, other conditions not |
| Testing 2 | NM-RWR1-exh150-gapdn-spyup-pm-short | 11 / 11 (never) | 1.36 | 0.14 | rare by design | 654 trades on 78 of ~480 sessions |
| Testing 2 | LD1 / LD4 / LD8 | 9 / 9 (never) | 0.05-0.31 | 0.39-0.86 | rare by design | breadth-up / index-turn gates |
| Testing 2 | LD3 / LD5 | 3 / 9 (1 signal each) | 0.07-0.17 | 0.84-0.93 | rare; the one signal hit an opposite-side hold | what-if +0.5R each |
| Testing 2 | LD6 / LD7 | 3-4 / 3-4 | 0.24-0.42 | 0.57-0.79 | rare by design | 2 / 1 signals in 9 |
| Testing 2 | CWT04-backside-lh-a25 / vwaptest-a25 | 16 / 16 (never) | 0.36 / 0.56 | 0.15 / **0.051** | rare by design (edge) | the a15 twins fire (2.85 / 4.76 lab); a25 is the stricter cut; replay 10-22/23/26 also 0 |
| Testing 2 | CWT14-pdl-p05-R2A-short | 1 / 1 (never) | regime leg | — | rare by design (regime leg) | 11-02 was a long-leg day (long leg 31 signals) |
| Graveyard | NS2-sma50break-overbought-short | 0 / 5 | 5.7 | — | blocked: place in line (own twin) | 31 streak signals: twin held 15 (NS2-FD 12), ETB 6, opposite 4; what-if +4.9R / 19 |
| Generated | 25 never fired + 6 quiet 3-4 | 3-11 | 0.1-14 | 0.05-0.81 | rare by design (12 index gate met ≤ 1 of the streak) | young (10-19..10-29), breadth / SPY / QQQ gated; 0 below 5% |

## 3. Load: which accounts have room (measured; capacity1103, livelab_pipeline, journals 10-27..11-03)

| account | enabled | 1-min polls (10-30 / 11-02 / 11-03 am) | decision minutes 11-03 | peak positions / cap (10-27..11-02) | buying-power rejects (10-27..11-02, 11-03 to 11:05) | per-setup cap skips | verdict |
|---|---|---|---|---|---|---|---|
| Primary | 10 | 97 / 100 / 100% | 20 / 20 | 5-21 / 77 | 0 / 0 | 0 | small by design (promotions only) |
| Testing 1 | 28 | 97 / 100 / 100% | 20 / 20 | 16-73 / 400 | 0 / 0 | 0 | **room** (CPU at the 25-28 band where coverage stays 97-100%) |
| Testing 2 | 46 | 79 / 77 / 94% | 20 / 20 | 44-89 / 400 | 1 / 0 | 1 | **CPU-crowded** (slots and capital fine) |
| Graveyard | 30 (+3 on 11-04) | 80 / 91 / 82% | 20 / 20 | 137-155 / 200 | 48 / **34** (from 10:50) | 461 (−79.2R) | **capital-crowded** |
| Generated | 93 | 76 / 66 / 85% | 20 / 20 | 46-144 / 200 | 13 / 0 | 14 | **CPU-crowded** (+ booking lag HK-RECON-GEN) |
| Live Lab / Explore 1-2 (unmerged) | 0 | — | — | — | — | — | the real room: 20 seats each, staged by capacity1103 §4 |

GitHub: steady 5 runners, a measured peak of 15 of 20 (the hand-over). Data: 0 HTTP 429. Adding seats to an account
costs that account's own poll time, not other accounts' (capacity1103).

## 4. Plan

**4a. Nightly "inactive setups" check (proposed: INACT1).** After the close, `audit.py <scratch> <next session>` runs on
the day's journals and freeze files. Its output goes in the nightly brief:
- **always one FYI line**, for example: `FYI | inactive | 207 enabled: 67 active, 52 last session, 37 quiet 1-2, 14 quiet
  3+, 37 never; alarm 0 (P<1%), watch 0 (P<5%); broken 0; blocked ≥3 sessions 4 (2 own twin, 2 borrow); GY buying power
  ran out 10:50`;
- **a DECISION only when the fix needs the owner** (a setup_order change or a move, per the table in §1). Bugs and
  coverage are fixed as housekeeping and reported in the FYI line.
- It also lists the **slow-verdict setups** (INACT2) once a week, not nightly.
- Wiring it into the nightly brief is housekeeping after INACT1 yes. The script reads only and needs no live-path change.

**4b. Slow verdicts (proposed: INACT2).**
- Keep every rare-by-design setup on. They cost almost nothing where they sit: the IDX rule setups in Testing 1 have
  room, and the LD lab setups' decisions are all taken in Testing 2.
- Judge them on **60 trades**, not 20 sessions.
- Report their sessions-to-verdict at the current pace (for example IDX ≈ 1,500-6,000 sessions, LD4 ≈ 1,200) so the
  owner can retire the ones that will never reach a verdict. "INACT2 trim" switches off the 7 setups expected under
  0.1 a session now.

**4c. Reallocation.**
- **No one-off move is recommended.** No quiet setup is quiet because of its account. The blocked ones are behind their
  own twin (MF4-h40, NS2: twin by design, half the record negative in what-if) or behind borrow (ST5-FD, ST3-FD: an
  intended block).
- The **only account-load issue is the Graveyard's buying power** (proposed: GY-BP). Since 11-02 it runs out about 10:40-10:50
  ET, so afternoon setups and new arrivals lose their turn. Today 14 of 34 rejects went to MF3-FD / MF5-FD, the setups
  being observed after their demotion. The blocked signals' what-if is flat (−0.1R / 42), so this costs playing time,
  not R. Before DM-N3 adds 3 more, a research replay of 10-27..11-03 with a lower Graveyard per-setup cap (25 → 12)
  would show whether capital then spreads across all its setups without a worse R. Nothing changes without a later
  owner OK and a ledger line.
- When the Live Lab / Explore accounts open, new setups go there, not into Testing 2 / Gen, which are CPU-crowded.

## 5. Owner decisions (also open in docs/live/decisions.json)

- **INACT1:** Nightly inactive-setups check with the expected-rate rule (watch P < 5%, alarm P < 1%, index-gate exempt),
  one FYI line a night, a DECISION only when a fix needs you? **Recommendation: yes** (report only).
  Reply "INACT1 yes" / "INACT1 fixed" (keep a fixed 5-session bar instead) / "INACT1 no".
- **INACT2:** Keep rare-by-design setups on and judge them on 60 trades rather than 20 sessions, with a weekly
  sessions-to-verdict list? **Recommendation: yes.** Reply "INACT2 yes" / "INACT2 trim" (also switch off the 7 setups
  expected < 0.1 trades a session: IDX1 trail, IDX1 hold, IDX2, IDX3, IDX5, LD4, LD5) / "INACT2 no".
- **GY-BP:** Research replay only: would a lower Graveyard per-setup cap (25 → 12) spread its buying power so that every
  Graveyard setup still gets turns after ~10:45? **Recommendation: optional** (playing time, not R: blocked signals
  −0.1R / 42 what-if). Reply "GY-BP replay" / "GY-BP no".

## 6. Full table (207 enabled setups; all columns in table.csv)

"since" = first session of the setup's current run in that account. "sess" = completed sessions in that run. "quiet
sig / trade" = completed sessions since its last signal / trade. "live R" = gross R of its live trades in the run. P =
P(quiet signal streak | expected rate), blank when the streak is 0 or there is no rate. Educational only — not financial
advice.

| account | setup | since | sess | signal bucket | quiet sig / trade | sig/sess | trades/sess | live R | exp/sess | P(quiet) | cause |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary | NS1-rsidip-rsi5pop-long | 10-08 | 18 | quiet 1-2 | 2 / 2 | 0.83 | 0.67 | +0.5 | 0.92 | 0.541 |  |
| Primary | L3-gap-slope-rsi5hi-FD | 10-30 | 2 | fired last session | 0 / 0 | 45.00 | 1.50 | -1.7 | 13.41 |  |  |
| Primary | ST7-rsi50dn-long-pm-t1s1-FD | 10-26 | 6 | fired last session | 0 / 0 | 2.50 | 1.67 | -2.2 | 2.17 |  |  |
| Primary | L3-gap-slope-fromopen-FD | 10-30 | 2 | active today | 0 / 0 | 129.50 | 2.00 | -4.0 | 11.44 |  |  |
| Primary | MF2-open-rsimidhi-flowsell-FD | 10-20 | 10 | active today | 0 / 0 | 6.80 | 4.00 | +37.2 | 10.09 |  |  |
| Primary | MF4-h40-open-flowsell | 10-08 | 18 | active today | 0 / 10 | 3.78 | 1.17 | +1.5 | 7.24 |  | blocked: place in line |
| Primary | MF4-h40-open-flowsell-FD | 10-20 | 10 | active today | 0 / 0 | 9.10 | 4.00 | -4.5 | 16.45 |  |  |
| Primary | NS5-sma50-flush-oversold-long | 10-08 | 18 | active today | 1 / 1 | 1.17 | 1.00 | +4.6 | 2.41 | 0.448 |  |
| Primary | RW3-gapdn-rsi5pop-flowsell-short-FD | 10-16 | 12 | active today | 0 / 0 | 6.75 | 4.42 | +23.7 | 13.59 |  |  |
| Primary | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 10-16 | 12 | active today | 0 / 0 | 7.75 | 5.92 | +23.7 | 12.79 |  |  |
| Testing 1 | IDX1-qqq100-0955-TQQQ-hold | 10-16 | 12 | never fired since enabled | 12 / 12 | 0.00 | 0.00 | +0.0 | 0.02 | 0.777 | rare by design (P >= 5%) |
| Testing 1 | IDX1-qqq100-0955-TQQQ-trail | 10-16 | 12 | never fired since enabled | 12 / 12 | 0.00 | 0.00 | +0.0 | 0.02 | 0.777 | rare by design (P >= 5%) |
| Testing 1 | IDX2-spy075-0945-3x-trail | 10-16 | 12 | never fired since enabled | 12 / 12 | 0.00 | 0.00 | +0.0 | 0.01 | 0.882 | rare by design (P >= 5%) |
| Testing 1 | IDX3-spy075-0955-3x-trail | 10-16 | 12 | never fired since enabled | 12 / 12 | 0.00 | 0.00 | +0.0 | 0.02 | 0.797 | rare by design (P >= 5%) |
| Testing 1 | IDX5-spy050-0945-3x-trail | 10-16 | 12 | never fired since enabled | 12 / 12 | 0.00 | 0.00 | +0.0 | 0.04 | 0.649 | rare by design (P >= 5%) |
| Testing 1 | LIQ-pdl-sweep-open15-vwap-long | 10-13 | 15 | quiet 5+ | 11 / 11 | 0.07 | 0.07 | -1.0 | 0.38 | 0.248 | rare by design (P >= 5%) |
| Testing 1 | ST6-volspikeup-short-mid-t1s1-FD | 10-12 | 16 | quiet 3-4 | 3 / 3 | 1.44 | 0.38 | +2.0 | 1.24 | 0.289 | rare by design (P >= 5%) |
| Testing 1 | ST5-pdbrkup-short-mid-t05s1-FD | 10-12 | 16 | quiet 1-2 | 1 / 8 | 1.19 | 0.12 | +3.5 | 0.78 | 0.771 | blocked: borrow / short gate |
| Testing 1 | ST8-volspikedn-long-pm-t1s1-FD | 10-12 | 16 | quiet 1-2 | 1 / 1 | 0.75 | 0.62 | +2.1 | 1.05 | 0.705 |  |
| Testing 1 | CWT05-flush-m05-v3-long | 10-21 | 9 | fired last session | 0 / 1 | 3.89 | 2.67 | -0.5 | 4.00 |  |  |
| Testing 1 | NS1-rsidip-rsi5pop-long-FD | 10-12 | 16 | fired last session | 0 / 0 | 3.62 | 2.56 | -4.0 | 5.39 |  |  |
| Testing 1 | NS4-pm-vwap-reclaim-oversold-short-FD | 10-12 | 16 | fired last session | 0 / 1 | 3.50 | 1.62 | +5.7 | 3.57 |  |  |
| Testing 1 | ST3-rsi5up-short-pm-t1s1-FD | 10-12 | 16 | fired last session | 0 / 3 | 1.19 | 0.12 | -0.4 | 1.35 |  | blocked: borrow / short gate |
| Testing 1 | ST4-emadn-long-am-t1s05-FD | 10-12 | 16 | fired last session | 0 / 0 | 1.75 | 0.94 | -7.7 | 2.77 |  |  |
| Testing 1 | ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD | 10-23 | 7 | fired last session | 0 / 0 | 0.43 | 0.43 | -1.3 | 1.25 |  |  |
| Testing 1 | exhaustion_short | 10-12 | 16 | fired last session | 0 / 0 | 6.88 | 3.44 | +3.2 | 12.12 |  |  |
| Testing 1 | exhaustion_short-FD | 10-12 | 16 | fired last session | 0 / 0 | 13.06 | 4.88 | -2.9 | 64.64 |  |  |
| Testing 1 | intraday_momentum | 10-12 | 16 | fired last session | 0 / 0 | 2.00 | 1.94 | -8.5 | 2.37 |  |  |
| Testing 1 | L3-gap-slope-lowdist-FD | 10-12 | 16 | active today | 0 / 0 | 16.81 | 3.69 | +2.8 | 9.76 |  |  |
| Testing 1 | MF1-945-flowsell-vwapup | 10-26 | 6 | active today | 0 / 1 | 3.17 | 0.83 | -5.3 | 5.33 |  |  |
| Testing 1 | MF3-open-flowsell-rsi5hi | 10-20 | 10 | active today | 0 / 9 | 5.30 | 0.30 | +0.9 | 9.19 |  |  |
| Testing 1 | MF5-flowsell-vwapup-rsi5hi | 10-20 | 10 | active today | 0 / 0 | 5.70 | 2.90 | -10.8 | 15.47 |  |  |
| Testing 1 | NS3-failed-vwap-reclaim-short | 10-15 | 13 | active today | 0 / 0 | 5.23 | 2.92 | -4.8 | 3.03 |  |  |
| Testing 1 | NS5-sma50-flush-oversold-long-FD | 10-12 | 16 | active today | 0 / 0 | 3.50 | 2.12 | -12.8 | 6.32 |  |  |
| Testing 1 | RW6G1-ns2-up3-vwap2sd-short | 10-22 | 8 | active today | 8 / 8 | 0.00 | 0.00 | +0.0 | 0.40 | 0.344 |  |
| Testing 1 | RW6G1-ns2-up3-vwap2sd-short-FD | 10-12 | 16 | active today | 0 / 0 | 2.50 | 1.75 | -6.3 | 3.73 |  |  |
| Testing 1 | RW7-gapdn-bounce-early-short-FD | 10-12 | 16 | active today | 0 / 0 | 37.50 | 20.69 | +5.1 | 59.92 |  |  |
| Testing 1 | orb20_a | 10-12 | 16 | active today | 0 / 0 | 3.94 | 1.56 | -1.7 | 6.79 |  |  |
| Testing 2 | CWT04-backside-lh-a25-short | 10-12 | 16 | never fired since enabled | 16 / 16 | 0.00 | 0.00 | +0.0 | 0.36 | 0.147 | rare by design (P >= 5%) |
| Testing 2 | CWT04-backside-vwaptest-a25-short | 10-12 | 16 | never fired since enabled | 16 / 16 | 0.00 | 0.00 | +0.0 | 0.56 | 0.051 | rare by design (P >= 5%) |
| Testing 2 | CWT14-failbrk-pdl-p05-R2A-short | 11-02 | 1 | never fired since enabled | 1 / 1 | 0.00 | 0.00 | +0.0 |  |  |  |
| Testing 2 | LD1-ns1-breadthup-t05s1-long | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.31 | 0.395 | rare by design (P >= 5%) |
| Testing 2 | LD4-st4-breadthup-t1s05-long | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.05 | 0.861 | rare by design (P >= 5%) |
| Testing 2 | LD8-spy-dip030-breadthturn-spxl-holdtr-long | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.16 | 0.619 | rare by design (P >= 5%) |
| Testing 2 | NM-RWR1-exh150-gapdn-spyup-pm-short | 10-19 | 11 | never fired since enabled | 11 / 11 | 0.00 | 0.00 | +0.0 | 1.36 | 0.142 | rare by design (P >= 5%) |
| Testing 2 | NM-RWN4-ns2-spyup05-notfri-short | 10-19 | 11 | quiet 5+ | 5 / 5 | 0.82 | 0.73 | -0.2 | 2.11 | 0.030 | rare by design: index gate met on 1 of 5 quiet sessions |
| Testing 2 | NM-RWR4-ns2-up3-qqqup-slopedn-short | 10-19 | 11 | quiet 5+ | 5 / 5 | 0.55 | 0.45 | -1.6 | 1.50 | 0.082 | rare by design (P >= 5%) |
| Testing 2 | LD3-st2-idxturn-t05s1-long | 10-21 | 9 | quiet 3-4 | 3 / 9 | 0.11 | 0.00 | +0.0 | 0.17 | 0.844 | blocked: place in line |
| Testing 2 | LD5-st2-breadthup-t05s1-long | 10-21 | 9 | quiet 3-4 | 3 / 9 | 0.11 | 0.00 | +0.0 | 0.07 | 0.932 | blocked: place in line |
| Testing 2 | LD6-spy-dip020atr-breadthturn-spxl-holdtr-long | 10-21 | 9 | quiet 3-4 | 3 / 3 | 0.22 | 0.22 | +1.8 | 0.24 | 0.787 | rare by design (P >= 5%) |
| Testing 2 | LD7-ns1-idxturn-holdtr-long | 10-21 | 9 | quiet 3-4 | 4 / 4 | 0.11 | 0.11 | +0.0 | 0.42 | 0.571 | rare by design (P >= 5%) |
| Testing 2 | CWT04-backside-lh-a15-short | 10-12 | 16 | quiet 1-2 | 1 / 2 | 0.38 | 0.12 | -0.1 | 2.85 | 0.387 |  |
| Testing 2 | CWT04-backside-vwaptest-a15-short | 10-12 | 16 | quiet 1-2 | 1 / 2 | 0.88 | 0.44 | -3.6 | 4.76 | 0.205 |  |
| Testing 2 | CWT05-flush-m05-v5-long | 10-12 | 16 | quiet 1-2 | 2 / 2 | 0.69 | 0.38 | -1.1 | 2.93 | 0.142 |  |
| Testing 2 | CWT05-flush-m075-v3-long | 10-12 | 16 | quiet 1-2 | 1 / 1 | 1.12 | 0.75 | +1.4 | 3.31 | 0.332 |  |
| Testing 2 | CWT05-flush-m075-v5-long | 10-12 | 16 | quiet 1-2 | 2 / 2 | 0.44 | 0.25 | -0.5 | 1.37 | 0.401 |  |
| Testing 2 | CWT13-vwapstretch-z075-short | 10-12 | 16 | quiet 1-2 | 1 / 2 | 1.88 | 0.94 | -3.3 | 6.14 | 0.129 |  |
| Testing 2 | LD2-qqq-dip015-breadthturn-tqqq-t05s1-long | 10-21 | 9 | quiet 1-2 | 1 / 1 | 0.44 | 0.44 | -0.6 | 0.37 | 0.884 |  |
| Testing 2 | NM-AMS-N1-quiet-morning-short | 10-19 | 11 | quiet 1-2 | 2 / 2 | 0.18 | 0.09 | -1.1 | 0.83 | 0.574 |  |
| Testing 2 | NM-PM-gapdn-above-pdh-rvol-short | 10-19 | 11 | quiet 1-2 | 2 / 2 | 0.18 | 0.18 | +1.0 | 0.93 | 0.537 |  |
| Testing 2 | CWT12-flag-s1-long | 10-12 | 16 | fired last session | 0 / 0 | 1.25 | 0.94 | -2.8 | 3.37 |  |  |
| Testing 2 | CWT13-vwapstretch-z05-long | 10-27 | 5 | fired last session | 0 / 0 | 25.00 | 17.00 | -15.2 | 42.57 |  |  |
| Testing 2 | CWT13-vwapstretch-z075-long | 10-12 | 16 | fired last session | 0 / 1 | 3.06 | 0.88 | +4.8 | 9.23 |  |  |
| Testing 2 | NM-ETF-late-dip-di-long | 10-19 | 11 | fired last session | 0 / 0 | 0.91 | 0.73 | +3.2 | 1.10 |  |  |
| Testing 2 | NM-HL-T75-pm-long | 10-19 | 11 | fired last session | 0 / 0 | 4.27 | 3.91 | -4.2 | 3.88 |  |  |
| Testing 2 | NM-MF3-qqqdn-gapdn-FD | 10-21 | 9 | fired last session | 0 / 1 | 4.78 | 2.67 | +5.9 | 4.90 |  |  |
| Testing 2 | NM-RWN5-ns3-mon-weakrs-short | 10-19 | 11 | fired last session | 0 / 0 | 1.73 | 0.64 | +3.4 | 0.69 |  |  |
| Testing 2 | NM-RWR3-ns3-qqqup-early-short | 10-19 | 11 | fired last session | 0 / 0 | 1.00 | 0.27 | +0.5 | 0.83 |  |  |
| Testing 2 | NM1-cwt09-g10-vwaploss-short | 10-19 | 11 | fired last session | 0 / 2 | 4.09 | 0.36 | +0.9 | 0.50 |  |  |
| Testing 2 | NS4-pm-vwap-reclaim-oversold-short | 10-28 | 4 | fired last session | 0 / 2 | 3.25 | 2.00 | +0.2 | 3.05 |  |  |
| Testing 2 | NS5-sma50-flush-oversold-long-FD | 10-21 | 9 | fired last session | 0 / 0 | 1.33 | 1.11 | -3.4 | 6.32 |  |  |
| Testing 2 | exhaustion_short-FD | 10-21 | 9 | fired last session | 0 / 0 | 10.33 | 6.78 | -1.5 | 64.64 |  |  |
| Testing 2 | CWT09-gapdn-bounce-g10-lowerhalf-short | 10-12 | 16 | active today | 0 / 1 | 8.69 | 1.06 | +0.9 | 1.38 |  |  |
| Testing 2 | CWT09-gapdn-vwaploss-g10-short | 10-12 | 16 | active today | 0 / 1 | 8.44 | 0.69 | +3.9 | 1.29 |  |  |
| Testing 2 | CWT14-failbrk-pdl-p05-R2A-long | 11-02 | 1 | active today | 0 / 0 | 31.00 | 19.00 | -3.0 | 27.00 |  |  |
| Testing 2 | CWT14-failbrk-pdl-p10-long | 10-12 | 16 | active today | 0 / 0 | 40.88 | 26.44 | -10.6 | 88.03 |  |  |
| Testing 2 | CWT14-failbrk-pdl-p10-lowvol-long | 10-28 | 4 | active today | 0 / 0 | 22.75 | 15.75 | -12.7 | 47.14 |  |  |
| Testing 2 | MF2-open-rsimidhi-flowsell | 10-28 | 4 | active today | 2 / 2 | 0.50 | 0.25 | -1.1 | 1.30 | 0.420 |  |
| Testing 2 | MF5-flowsell-vwapup-rsi5hi | 10-21 | 9 | active today | 0 / 9 | 3.00 | 0.00 | +0.0 | 15.47 |  |  |
| Testing 2 | NM-AR-AM-gapdown-capitulation-long | 10-19 | 11 | active today | 0 / 0 | 5.45 | 3.64 | -12.8 | 3.31 |  |  |
| Testing 2 | NM-RWN3-ns3-spyup-early-short | 10-19 | 11 | active today | 0 / 0 | 1.64 | 0.36 | -0.5 | 0.91 |  |  |
| Testing 2 | NS3V1-am-widestop-short | 10-23 | 7 | active today | 0 / 0 | 6.14 | 2.71 | -10.6 | 5.30 |  |  |
| Testing 2 | RW1-gapdn-bounce-flowsell-short-FD | 10-21 | 9 | active today | 0 / 0 | 8.11 | 4.78 | +10.0 | 17.10 |  |  |
| Testing 2 | RW3S-gapdn-flowsell-short-FD | 11-03 | 0 | active today | 0 / 0 |  |  | +0.0 |  |  |  |
| Graveyard | RW4-ns3-adv150-short-FD | 11-02 | 1 | fired last session | 0 / 0 | 16.00 | 5.00 | -0.3 | 17.34 |  |  |
| Graveyard | ST2-slope20up-long-am-t05s1-FD | 10-21 | 9 | fired last session | 0 / 0 | 12.56 | 9.44 | -2.3 | 24.03 |  |  |
| Graveyard | heat_fade_long | 10-21 | 9 | fired last session | 0 / 0 | 8.44 | 4.89 | -12.3 | 30.36 |  |  |
| Graveyard | CWT09-gapdn-bounce-g5-lowerhalf-short | 10-21 | 9 | active today | 0 / 0 | 38.67 | 7.56 | +11.9 | 9.12 |  |  |
| Graveyard | CWT09-gapdn-vwaploss-g5-short | 10-26 | 6 | active today | 0 / 1 | 58.00 | 6.00 | -12.4 | 8.60 |  |  |
| Graveyard | CWT12-coil-k4-long | 10-29 | 3 | active today | 0 / 0 | 105.67 | 40.00 | -15.6 | 35.00 |  |  |
| Graveyard | CWT12-coil-k6-long | 10-27 | 5 | active today | 0 / 0 | 42.00 | 12.20 | -13.3 | 13.43 |  |  |
| Graveyard | CWT13-vwapstretch-z05-short | 10-23 | 7 | active today | 0 / 0 | 15.29 | 9.00 | +6.2 | 37.95 |  |  |
| Graveyard | CWT14-failbrk-orl-p05-long | 10-21 | 9 | active today | 0 / 0 | 136.67 | 49.22 | -25.2 | 246.53 |  |  |
| Graveyard | CWT14-failbrk-orl-p05-lowvol-long | 10-21 | 9 | active today | 0 / 0 | 96.11 | 40.67 | -16.5 | 173.74 |  |  |
| Graveyard | CWT14-failbrk-orl-p10-long | 10-21 | 9 | active today | 0 / 0 | 51.00 | 27.44 | -8.5 | 93.87 |  |  |
| Graveyard | CWT14-failbrk-orl-p10-lowvol-long | 10-21 | 9 | active today | 0 / 0 | 41.11 | 24.44 | -6.0 | 74.36 |  |  |
| Graveyard | CWT14-failbrk-pdh-p05-lowvol-short | 10-22 | 8 | active today | 0 / 0 | 57.75 | 18.50 | -30.4 | 103.00 |  |  |
| Graveyard | CWT14-failbrk-pdh-p10-lowvol-short | 10-22 | 8 | active today | 0 / 0 | 22.88 | 10.75 | -6.1 | 45.73 |  |  |
| Graveyard | CWT14-failbrk-pdh-p10-short | 10-23 | 7 | active today | 0 / 0 | 43.43 | 19.71 | -40.6 | 42.71 |  |  |
| Graveyard | CWT14-failbrk-pdl-p05-long | 10-30 | 2 | active today | 0 / 0 | 55.00 | 14.00 | -5.6 | 156.98 |  |  |
| Graveyard | CWT14-failbrk-pdl-p05-lowvol-long | 10-30 | 2 | active today | 0 / 0 | 31.50 | 15.00 | -5.4 | 103.35 |  |  |
| Graveyard | LIQ-orl-sweep-open15-s25-long | 10-21 | 9 | active today | 0 / 0 | 16.00 | 11.44 | -20.1 | 31.30 |  |  |
| Graveyard | MF1-945-flowsell-vwapup-FD | 10-21 | 9 | active today | 0 / 0 | 11.44 | 4.44 | +5.8 | 23.94 |  |  |
| Graveyard | MF3-open-flowsell-rsi5hi-FD | 11-03 | 0 | active today | 0 / 0 |  |  | +0.0 | 24.16 |  |  |
| Graveyard | MF5-flowsell-vwapup-rsi5hi-FD | 11-03 | 0 | active today | 0 / 0 |  |  | +0.0 | 15.47 |  |  |
| Graveyard | NS2-sma50break-overbought-short | 10-21 | 9 | active today | 0 / 5 | 5.33 | 0.67 | +1.5 | 5.74 |  | blocked: place in line |
| Graveyard | NS2-sma50break-overbought-short-FD | 10-21 | 9 | active today | 0 / 0 | 11.11 | 5.67 | -10.1 | 17.08 |  |  |
| Graveyard | NS3-failed-vwap-reclaim-short-FD | 11-02 | 1 | active today | 0 / 0 | 24.00 | 4.00 | -0.4 | 22.02 |  |  |
| Graveyard | RW2-exhaustion-noon-adv150-short-FD | 10-21 | 9 | active today | 0 / 0 | 41.33 | 18.22 | -56.0 | 50.34 |  |  |
| Graveyard | RW6-ns2-up3-short-FD | 10-21 | 9 | active today | 0 / 0 | 6.44 | 2.67 | -2.8 | 7.12 |  |  |
| Graveyard | ST1-ordn-long-pm-t05s1-FD | 10-21 | 9 | active today | 0 / 0 | 1.78 | 1.11 | -4.5 | 3.49 |  |  |
| Graveyard | heat_fade_long-FD | 10-21 | 9 | active today | 0 / 0 | 16.33 | 6.56 | -12.0 | 51.74 |  |  |
| Graveyard | heat_fade_short | 10-21 | 9 | active today | 0 / 0 | 20.22 | 9.56 | -43.9 | 31.76 |  |  |
| Graveyard | heat_fade_short-FD | 10-21 | 9 | active today | 0 / 0 | 61.00 | 23.00 | -30.8 | 173.78 |  |  |
| Generated | GEN-261019-06-VWAPxUp-EMAdiffge0p29-PM-SPYgt0p5-holdtr-long | 10-19 | 11 | never fired since enabled | 11 / 11 | 0.00 | 0.00 | +0.0 | 0.80 | 0.167 | rare by design (P >= 5%) |
| Generated | GEN-261019-07-VolRatioge2-UpWickge0p59-DayRngVsPrevge1p5-LATE-SPYgt0p5-t05s1-long | 10-19 | 11 | never fired since enabled | 11 / 11 | 0.00 | 0.00 | +0.0 | 1.38 | 0.256 | rare by design: index gate met on 1 of 11 quiet sessions |
| Generated | GEN-261020-02-RSIslopelem19-BarRngATRge0p14-BuyPressge0p17-LATE-BRvwgt0p7-t05s1-short | 10-20 | 10 | never fired since enabled | 10 / 10 | 0.00 | 0.00 | +0.0 | 0.18 | 0.502 | rare by design (P >= 5%) |
| Generated | GEN-261020-10-BBpctge0p81-ORBfailDn-AM-BRvwlt0p3-hold-short | 10-20 | 10 | never fired since enabled | 10 / 10 | 0.00 | 0.00 | +0.0 | 1.83 | 0.419 | rare by design (P >= 5%) |
| Generated | GEN-261021-01-BearDiv-RVolDayle0p47-BarsSinceHODle0-LAM-SPYltm0p25-t1s1-short | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.87 | 0.134 | rare by design (P >= 5%) |
| Generated | GEN-261021-03-RSI5le34-Ret15mATRge0p12-DayRngVsPrevge1p2-LUNCH-SPYltm0p25-t05s1-short | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.35 | 0.134 | rare by design (P >= 5%) |
| Generated | GEN-261021-08-RSI2le0-Ret15mATRge0p16-ATRdge3p6-LUNCH-QQQgt0p6-holdtr-long | 10-21 | 9 | never fired since enabled | 9 / 9 | 0.00 | 0.00 | +0.0 | 0.13 | 0.457 | rare by design (P >= 5%) |
| Generated | GEN-261022-02-ORBfailUp-EMAdChglem0p094-ADX7ge57-LATE-BRvwgt0p7-t05s1-long | 10-22 | 8 | never fired since enabled | 8 / 8 | 0.00 | 0.00 | +0.0 | 1.50 | 0.371 | rare by design (P >= 5%) |
| Generated | GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short | 10-22 | 8 | never fired since enabled | 8 / 8 | 0.00 | 0.00 | +0.0 | 0.45 | 0.576 | rare by design (P >= 5%) |
| Generated | GEN-261023-01-VWAPxUp-VWAPatrge0p33-LAM-SPYgt0p5-t05s05-short | 10-23 | 7 | never fired since enabled | 7 / 7 | 0.00 | 0.00 | +0.0 | 0.20 | 0.544 | rare by design: index gate met on 1 of 7 quiet sessions |
| Generated | GEN-261023-05-NewLOD-SMA20dlem0p94-ORLdistlem0p24-PM-BRopgt0p65-hold-long | 10-23 | 7 | never fired since enabled | 7 / 7 | 0.00 | 0.00 | +0.0 | 0.10 | 0.698 | rare by design (P >= 5%) |
| Generated | GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short | 10-23 | 7 | never fired since enabled | 7 / 7 | 0.00 | 0.00 | +0.0 | 5.90 | 0.420 | rare by design (P >= 5%) |
| Generated | GEN-261026-09-BBpctle0p3-SMA20slopege0p46-FromPCATRge0p45-LATE-BRvwgt0p6-t05s05-long | 10-26 | 6 | never fired since enabled | 6 / 6 | 0.00 | 0.00 | +0.0 | 0.68 | 0.262 | rare by design (P >= 5%) |
| Generated | GEN-261028-01-MACDhge0p12-Since950ATRlem0p25-LATE-SPYgt0p5-holdtr-long | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 3.05 | 0.314 | rare by design: index gate met on 0 of 4 quiet sessions |
| Generated | GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 2.35 | 0.435 | rare by design: index gate met on 0 of 4 quiet sessions |
| Generated | GEN-261028-03-EMAdChgge0p15-VWAPxUp-Since950ATRlem0p43-LUNCH-SPYgt0p25-hold-long | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 1.24 | 0.253 | rare by design: index gate met on 1 of 4 quiet sessions |
| Generated | GEN-261028-05-EMAdChgge0p093-ORLdistlem0p42-LAM-QQQgt0p6-holdtr-long | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 1.98 | 0.326 | rare by design: index gate met on 0 of 4 quiet sessions |
| Generated | GEN-261028-06-RSI5le13-VWAPatrlem0p15-DayRngVsPrevle0p34-MID-BRoplt0p35-hold-short | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 3.00 | 0.347 | rare by design (P >= 5%) |
| Generated | GEN-261028-10-BarRngATRge0p18-Flow3lem0p54-FromPCATRge0p28-PM-SPYgt0p5-hold-long | 10-28 | 4 | never fired since enabled | 4 / 4 | 0.00 | 0.00 | +0.0 | 5.14 | 0.303 | rare by design: index gate met on 0 of 4 quiet sessions |
| Generated | GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long | 10-29 | 3 | never fired since enabled | 3 / 3 | 0.00 | 0.00 | +0.0 | 14.06 | 0.050 | rare by design: index gate met on 1 of 3 quiet sessions |
| Generated | GEN-261029-04-Ret15mge0p54-RVolDayle0p59-VWAPcrossesle1-LUNCH-SPYgt0p25-hold-long | 10-29 | 3 | never fired since enabled | 3 / 3 | 0.00 | 0.00 | +0.0 | 2.97 | 0.230 | rare by design: index gate met on 1 of 3 quiet sessions |
| Generated | GEN-261029-05-BearDiv-RSI14ge78-Compress6le0p091-AM-BRopgt0p5-t05s05-long | 10-29 | 3 | never fired since enabled | 3 / 3 | 0.00 | 0.00 | +0.0 | 0.32 | 0.809 | rare by design (P >= 5%) |
| Generated | GEN-261029-10-RSIslopege19-Ret5mlem0p21-EMAdiffge0p29-OPEN-BRvwgt0p5-t1s1-short | 10-29 | 3 | never fired since enabled | 3 / 3 | 0.00 | 0.00 | +0.0 | 0.29 | 0.554 | rare by design (P >= 5%) |
| Generated | GEN-POD1022-01-thrasher-breadth-thrust-stocks-holdtr-long | 10-26 | 6 | never fired since enabled | 6 / 6 | 0.00 | 0.00 | +0.0 | 4.96 | 0.717 | rare by design (P >= 5%) |
| Generated | GEN-POD1022-02-breadth-thrust-index-etf-holdtr-long | 10-26 | 6 | never fired since enabled | 6 / 6 | 0.00 | 0.00 | +0.0 | 0.39 | 0.537 | rare by design (P >= 5%) |
| Generated | GEN-261020-01-MACDhge0p12-RSI5le25-PM-BRvwgt0p6-t1s05-long | 10-20 | 10 | quiet 3-4 | 4 / 4 | 0.30 | 0.30 | -3.2 | 2.30 | 0.145 | rare by design (P >= 5%) |
| Generated | GEN-261020-04-MACDhge0p12-BullDiv-MID-SPYgt0p25-t05s1-short | 10-20 | 10 | quiet 3-4 | 4 / 4 | 0.60 | 0.30 | +0.0 | 1.30 | 0.240 | rare by design: index gate met on 1 of 4 quiet sessions |
| Generated | GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long | 10-20 | 10 | quiet 3-4 | 4 / 4 | 4.80 | 4.40 | -1.5 | 9.27 | 0.161 | rare by design: index gate met on 1 of 4 quiet sessions |
| Generated | GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long | 10-27 | 5 | quiet 3-4 | 3 / 3 | 2.80 | 1.80 | +1.6 | 12.09 | 0.054 | rare by design (P >= 5%) |
| Generated | GEN-261028-04-ORBfailUp-RSI14le22-Gaplem1p2-LATE-BRvwgt0p5-holdtr-long | 10-28 | 4 | quiet 3-4 | 3 / 3 | 0.25 | 0.25 | +1.1 | 1.76 | 0.241 | rare by design (P >= 5%) |
| Generated | GEN-POD1022-03-wt-bull-flag-bailout-S-long | 10-26 | 6 | quiet 3-4 | 3 / 3 | 0.33 | 0.17 | +0.6 | 1.87 | 0.465 | rare by design (P >= 5%) |
| Generated | GEN-261019-02-BBpctle0p017-SMA20slopege0p46-PM-QQQdn-t05s1-long | 10-19 | 11 | quiet 1-2 | 2 / 2 | 0.27 | 0.27 | -0.1 | 1.83 | 0.401 |  |
| Generated | GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long | 10-19 | 11 | quiet 1-2 | 1 / 1 | 1.00 | 0.82 | -0.3 | 4.18 | 0.400 |  |
| Generated | GEN-261019-04-EMAdChgge0p15-RSI14le22-MID-BRoplt0p5-t1s1-long | 10-19 | 11 | quiet 1-2 | 1 / 1 | 3.00 | 2.00 | -10.1 | 4.40 | 0.367 |  |
| Generated | GEN-261019-05-RSIslopelem9-PDLdistle0p14-EMAdifflem0p46-OPEN-SPYltm0p5-t1s1-long | 10-19 | 11 | quiet 1-2 | 1 / 1 | 0.09 | 0.09 | -1.0 | 2.47 | 0.917 |  |
| Generated | GEN-261019-08-NewHOD-Slope6ge0p03-DayRngVsPrevge1p5-AM-SPYdn-hold-short | 10-19 | 11 | quiet 1-2 | 1 / 1 | 2.00 | 0.91 | -1.8 | 2.23 | 0.483 |  |
| Generated | GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long | 10-20 | 10 | quiet 1-2 | 1 / 1 | 5.50 | 3.00 | -32.1 | 1.17 | 0.767 |  |
| Generated | GEN-261021-04-NewHOD-PDHdistlem0p65-LAM-QQQltm0p6-hold-short | 10-21 | 9 | quiet 1-2 | 1 / 1 | 0.11 | 0.11 | -1.0 | 1.60 | 0.783 |  |
| Generated | GEN-261021-05-RSIslopelem14-ORHdistge0p42-LAM-BRvwlt0p3-t1s05-long | 10-21 | 9 | quiet 1-2 | 1 / 1 | 0.44 | 0.44 | -1.3 | 1.07 | 0.817 |  |
| Generated | GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long | 10-22 | 8 | quiet 1-2 | 1 / 1 | 7.50 | 4.88 | -3.5 | 3.00 | 0.433 |  |
| Generated | GEN-261022-04-RSI2le0-Eff6ge0p83-SMA20dge0p59-OPEN-BRvwlt0p5-t1s1-short | 10-22 | 8 | quiet 1-2 | 1 / 1 | 1.25 | 0.50 | -0.8 | 1.85 | 0.483 |  |
| Generated | GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short | 10-22 | 8 | quiet 1-2 | 1 / 1 | 3.12 | 2.25 | -18.6 | 2.70 | 0.867 |  |
| Generated | GEN-261023-02-Ret15mATRlem0p068-EMAdChgge0p028-ATRdge6-PM-BRopgt0p65-hold-long | 10-23 | 7 | quiet 1-2 | 2 / 2 | 0.14 | 0.14 | -1.0 | 0.13 | 0.902 |  |
| Generated | GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short | 10-23 | 7 | quiet 1-2 | 1 / 1 | 0.14 | 0.14 | -1.0 | 0.88 | 0.683 |  |
| Generated | GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long | 10-23 | 7 | quiet 1-2 | 2 / 2 | 1.29 | 1.14 | +0.5 | 6.28 | 0.588 |  |
| Generated | GEN-261023-10-MACDhge0p12-VWAPcrossesle0-EMAdiffge0p16-LUNCH-BRvwlt0p4-hold-long | 10-23 | 7 | quiet 1-2 | 1 / 1 | 0.57 | 0.57 | -2.7 | 1.95 | 0.567 |  |
| Generated | GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long | 10-26 | 6 | quiet 1-2 | 1 / 1 | 2.83 | 1.67 | +8.1 | 1.45 | 0.867 |  |
| Generated | GEN-261026-10-ORBfailDn-EMAdChglem0p051-PM-BRopgt0p65-t1s1-long | 10-26 | 6 | quiet 1-2 | 2 / 2 | 1.67 | 1.50 | -2.7 | 5.05 | 0.871 |  |
| Generated | GEN-261027-02-NewLOD-RSI14le35-Gapge2-PM-SPYup-holdtr-long | 10-27 | 5 | quiet 1-2 | 2 / 2 | 0.20 | 0.20 | -1.1 | 1.42 | 0.325 |  |
| Generated | GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long | 10-27 | 5 | quiet 1-2 | 2 / 2 | 7.60 | 6.40 | -6.5 | 5.00 | 0.438 |  |
| Generated | GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long | 10-27 | 5 | quiet 1-2 | 1 / 1 | 3.60 | 3.20 | -1.7 | 7.30 | 0.690 |  |
| Generated | GEN-261027-09-ORBfailDn-Gapge2-Slope6ge0p03-LAM-BRvwlt0p5-t05s05-short | 10-27 | 5 | quiet 1-2 | 1 / 1 | 2.60 | 0.60 | +2.1 | 5.64 | 0.359 |  |
| Generated | GEN-261027-10-FlowShiftlem1p2-MACDhge0p079-SMA20dge0p59-LUNCH-BRopgt0p65-holdtr-long | 10-27 | 5 | quiet 1-2 | 2 / 2 | 4.40 | 3.60 | -14.3 | 9.55 | 0.479 |  |
| Generated | GEN-261028-07-Z12ge1p6-Eff6le0p034-MID-SPYltm0p25-hold-short | 10-28 | 4 | quiet 1-2 | 1 / 1 | 1.00 | 1.00 | +0.1 | 1.07 | 0.709 |  |
| Generated | GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long | 10-28 | 4 | quiet 1-2 | 1 / 1 | 10.00 | 9.00 | -8.7 | 4.22 | 0.718 |  |
| Generated | GEN-261028-09-FlowShiftlem0p65-ADX7le23-AM-BRoplt0p35-t05s1-long | 10-28 | 4 | quiet 1-2 | 1 / 1 | 14.00 | 9.75 | -15.0 | 4.97 | 0.824 |  |
| Generated | GEN-261019-01-VWAPxUp-ATRdge3p6-FromPCATRlem0p68-OPEN-BRvwgt0p7-t05s05-long | 10-19 | 11 | fired last session | 0 / 0 | 1.73 | 1.36 | -3.5 | 1.45 |  |  |
| Generated | GEN-261019-09-EMAdChgge0p15-Since950ATRge0p6-PM-SPYltm0p5-t05s1-short | 10-19 | 11 | fired last session | 0 / 0 | 1.00 | 0.18 | -0.8 | 0.77 |  |  |
| Generated | GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short | 10-19 | 11 | fired last session | 0 / 0 | 5.64 | 3.27 | -11.4 | 15.35 |  |  |
| Generated | GEN-261020-06-VWAPxDn-Slope6lem0p011-BarsSinceHODge35-MID-BRoplt0p5-holdtr-long | 10-20 | 10 | fired last session | 0 / 0 | 0.50 | 0.40 | -0.6 | 1.58 |  |  |
| Generated | GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long | 10-20 | 10 | fired last session | 0 / 0 | 1.00 | 0.90 | -6.9 | 7.87 |  |  |
| Generated | GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long | 10-21 | 9 | fired last session | 0 / 0 | 4.11 | 2.89 | +9.4 | 4.63 |  |  |
| Generated | GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long | 10-21 | 9 | fired last session | 0 / 0 | 3.11 | 2.00 | +15.2 | 2.28 |  |  |
| Generated | GEN-261021-09-RSIslopelem19-ORHdistlem0p73-AM-BRvwgt0p7-t1s1-long | 10-21 | 9 | fired last session | 0 / 2 | 1.11 | 0.56 | -5.3 | 0.30 |  |  |
| Generated | GEN-261022-03-NewHOD-Ret15mATRge0p12-SMA20dge0p59-LATE-QQQdn-t05s1-short | 10-22 | 8 | fired last session | 0 / 0 | 1.75 | 0.75 | -3.0 | 2.85 |  |  |
| Generated | GEN-261022-06-NewLOD-ORBfailUp-BuyPresslem0p49-PM-SPYltm0p5-t1s1-long | 10-22 | 8 | fired last session | 0 / 0 | 2.25 | 1.88 | -0.9 | 0.42 |  |  |
| Generated | GEN-261022-10-EMAdChgge0p15-ORLdistge0p41-PDLdistle0p14-PM-BRoplt0p5-holdtr-short | 10-22 | 8 | fired last session | 0 / 2 | 1.38 | 0.75 | -2.0 | 2.82 |  |  |
| Generated | GEN-261023-03-RSI5le13-VWAPatrlem0p34-OPEN-BRvwgt0p6-holdtr-short | 10-23 | 7 | fired last session | 0 / 0 | 4.00 | 1.57 | -3.3 | 4.12 |  |  |
| Generated | GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long | 10-23 | 7 | fired last session | 0 / 0 | 3.43 | 3.00 | -5.3 | 0.85 |  |  |
| Generated | GEN-261023-08-RSIslopelem5p5-VWAPcrossesge8-SMA50dlem1p7-LATE-SPYltm0p5-t1s1-long | 10-23 | 7 | fired last session | 0 / 0 | 3.43 | 2.43 | +1.5 | 1.67 |  |  |
| Generated | GEN-261026-01-UpWickge0p59-Since950ATRlem0p61-AM-BRopgt0p5-holdtr-short | 10-26 | 6 | fired last session | 0 / 0 | 1.17 | 0.83 | -4.1 | 3.17 |  |  |
| Generated | GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short | 10-26 | 6 | fired last session | 0 / 0 | 3.17 | 2.50 | +6.4 | 3.27 |  |  |
| Generated | GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long | 10-26 | 6 | fired last session | 0 / 0 | 7.67 | 5.67 | +1.1 | 1.47 |  |  |
| Generated | GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short | 10-26 | 6 | fired last session | 0 / 0 | 6.33 | 5.00 | -3.2 | 4.77 |  |  |
| Generated | GEN-261027-03-NewLOD-DayPosle0p19-SMA20dlem0p59-LAM-SPYgt0p5-hold-long | 10-27 | 5 | fired last session | 0 / 0 | 0.40 | 0.40 | +4.8 | 2.75 |  |  |
| Generated | GEN-261027-04-VWAPatrge0-Gaplem2-FromOpenlem2-PM-SPYdn-t1s1-short | 10-27 | 5 | fired last session | 0 / 1 | 4.20 | 0.80 | -4.0 | 3.60 |  |  |
| Generated | GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short | 10-27 | 5 | fired last session | 0 / 1 | 7.20 | 4.60 | +3.7 | 3.26 |  |  |
| Generated | GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long | 10-29 | 3 | fired last session | 0 / 0 | 2.00 | 2.00 | -2.3 | 4.92 |  |  |
| Generated | GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short | 10-29 | 3 | fired last session | 0 / 0 | 22.33 | 14.00 | -7.2 | 15.50 |  |  |
| Generated | GEN-261029-07-UpWickge0p59-DayRngVsPrevle0p42-LATE-SPYltm0p5-t05s1-short | 10-29 | 3 | fired last session | 0 / 0 | 2.33 | 1.67 | -1.6 | 2.36 |  |  |
| Generated | GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short | 10-29 | 3 | fired last session | 0 / 0 | 2.67 | 2.33 | +0.3 | 5.26 |  |  |
| Generated | GEN-261029-09-RangeExpge1p6-Since950ATRlem0p43-OPEN-BRvwgt0p5-hold-short | 10-29 | 3 | fired last session | 0 / 0 | 2.00 | 0.67 | -2.1 | 2.12 |  |  |
| Generated | GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long | 10-20 | 10 | active today | 2 / 2 | 8.70 | 6.60 | -34.1 | 1.55 | 0.723 |  |
| Generated | GEN-261020-08-FlowShiftlem0p41-Compress6le0p077-OPEN-QQQup-t05s05-long | 10-20 | 10 | active today | 0 / 0 | 1.00 | 0.90 | -3.8 | 0.18 |  |  |
| Generated | GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long | 10-21 | 9 | active today | 0 / 0 | 16.33 | 13.44 | -36.4 | 16.07 |  |  |
| Generated | GEN-261021-10-MACDhge0p079-VWAPbarslem7-OPEN-QQQup-t1s05-long | 10-21 | 9 | active today | 0 / 9 | 0.11 | 0.00 | +0.0 | 0.10 |  |  |
| Generated | GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short | 10-22 | 8 | active today | 0 / 0 | 10.50 | 5.12 | +8.1 | 5.45 |  |  |
| Generated | GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short | 10-22 | 8 | active today | 0 / 0 | 4.25 | 2.88 | +11.0 | 1.78 |  |  |
| Generated | GEN-261026-04-ORBfailDn-Ret15mlem0p55-SMA50dlem0p3-OPEN-BRvwgt0p5-holdtr-short | 10-26 | 6 | active today | 0 / 0 | 0.67 | 0.17 | -1.0 | 2.87 |  |  |
| Generated | GEN-261026-05-Ret15mATRge0p042-FromPCATRge0p28-ORHdistlem0p38-OPEN-BRopgt0p5-hold-short | 10-26 | 6 | active today | 0 / 0 | 4.50 | 3.00 | -13.1 | 4.58 |  |  |
| Generated | GEN-261026-08-RSIslopege19-Ret5mge0p063-DayRngVsPrevge1p2-OPEN-SPYup-holdtr-short | 10-26 | 6 | active today | 0 / 0 | 0.67 | 0.50 | -1.5 | 4.80 |  |  |
| Generated | GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short | 10-27 | 5 | active today | 1 / 1 | 9.40 | 1.80 | +5.9 | 2.72 | 0.362 |  |
| Generated | GEN-261029-01-ORBfailUp-RSI14le41-ADX7le29-LAM-QQQgt0p3-hold-long | 10-29 | 3 | active today | 3 / 3 | 0.00 | 0.00 | +0.0 | 20.94 | 0.155 |  |

Educational only — not financial advice.
