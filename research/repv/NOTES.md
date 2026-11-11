# REPV — rep-velocity audit and unlock plan (2026-11-11)

*Educational only — not financial advice. Research only, written during market hours: **no config, setup, assignment
or ledger change is made here.** Every diff in §5 is applied after the close (≥ 16:05 ET) by a separate step, and only
after the owner's yes. All records are live **paper** results (run_id=1). R = `pnl_adj / (|entry − stop| × shares)`, after
costs. What-if R (run_id=2) is simulated with backtest costs and no fill-realism checks, so it is optimistic.*

Owner ask (11-11): finding setups is no longer the bottleneck — **live reps** are. Make every setup collect live trades as
fast as possible.

## The short version (plain English)

1. **Where reps are lost (all 7 accounts, every live session to 11-10, 47,885 journaled signals):** 39% of signals are
   taken. The rest are lost to:
   - spread / quote checks 14.2%;
   - not shortable (ETB) 13.9%;
   - the Graveyard's per-setup −2R latch 11% (Graveyard only);
   - account halts 6% (four bad days: On Deck 10-15, Testing A 10-14 / 10-16, Gen 11-04 / 11-05);
   - one-position-per-symbol / lot cap 5%;
   - per-setup caps 5%;
   - Alpaca buying-power rejects 3% (Gen and Graveyard);
   - the cost filter 1%, twin blocks 1%, the split-tape gate 1%.
   - **Not in the journals** (measured by replay instead):
     - the Testing A top-500 pool drops about **30-35% of Testing A's potential entries**;
     - the earnings blackout removes **1,240-1,870 names a day** (24-37% of the universe) in this earnings season.
     - The 09:50 rule costs nothing: no signal was journaled as "before 09:50".
2. **The biggest single leak is Gen's buying power.**
   - 11-06..11-10: 348 / 437 / 146 rejects a session, about **240 extra entries a session** over 11-05..11-10. The rejected
     signals are ~neutral in the what-if (−0.08R).
   - Rejects start at **$184k-$256k open notional**, about 2.1-2.9× Gen's $89k equity, with 110-164 lots open.
   - So the fix is **smaller lots, not more slots**: slots never filled (peak 154-173 of 200).
3. **Rep multipliers (potential vs actual live trades per session):**
   - **Median ×1.2 (live-measured) / ×1.3 (replay)** across the 40 focus setups.
   - Large for a few:
     - MF3 ×4.3 (split-tape gate);
     - GEN-261027-01 ×3.0;
     - L3-lowdist-FD ×2.1;
     - GEN-261020-10 ×2.0;
     - L3-rsi5hi-FD ×1.9;
     - ST7Q-FD ×1.9;
     - ST6-FD ×1.65;
     - CWT13-z075-short ×1.6.
   - Whole testing areas, from the no-cap, full-universe replay of 6 sessions against live on the same days:
     - Testing A ×1.76;
     - On Deck ×1.48;
     - Testing B ×2.5;
     - Testing C ×1.6;
     - the 22 Gen picks ×1.64.
4. **The hard truth on time to verdict: for most promising setups, trades are not the bottleneck — traded sessions
   are.**
   - Of the 40 focus setups, 10 already meet 8 traded sessions / 30 trades.
   - For 19 of the other 30, the **8-session** gate binds, not the 30-trade gate. Their own regime gates (SPY / QQQ /
     breadth filters, time windows, gap conditions) make them fire on only 10-50% of sessions.
   - Unlocks move the median time to 8/30 from **16.4 → 12.5 sessions**, and to 15/60 from **36 → 31.5 sessions**.
   - 6 setups stay more than 40 sessions from 8/30 whatever the account rules are. Those are 1-traded-session GENs and the
     CWT09-g10 / ST6 / ST7Q-type setups that need gap-down days.
   - The lever that would really speed these up is **setup design** (more traded days), not account caps. See §6 —
     that part goes to the backlog, per rules 15-17.
5. **Ranked unlocks** (§4): Gen lot size, Testing A full universe, On Deck at Primary rules (cost filter and split-tape
   gate off), Gen per-setup cap, Testing A cost filter, Testing B / C cap, and the Graveyard latch / lots. Together, about
   **+455-480 entries a session** outside the Graveyard and about **+490 in the Graveyard**. Primary is untouched.
6. **Extra Alpaca paper accounts:**
   - An extra account adds **parallel setups, not faster verdicts for existing ones**. A setup sees the same signals in
     any account, and a copy in two accounts duplicates trades rather than adding independent reps.
   - Rough estimate: about **+10-35 trades a session** per extra account hosting 20 low-rep candidates (the Testing B / C
     rate is 0.55-0.85 trades per setup-session), or **+100-200** for 20 busy ones (the Testing A rate is about 9 per
     setup-session).
   - A "Gen 2" that splits Gen's 93 setups would recover the same ~240-290 a session as the lot-size fix, without
     shrinking lots.

## Rule / config changes inside the windows used (owner rule 2026-11-02, from `research/ledger.jsonl`)
- **All accounts:**
  - per-lot stacking from 10-13, same-setup re-entry from 10-14;
  - twin cap from 10-20 (twin_group from 10-21).
- **On Deck (Testing 1):**
  - split-tape short gate from about 10-14;
  - per-setup −2R stop 10-19/20, off from 10-23;
  - **CF cost filter 0.15R from 10-30.**
- **Testing A:**
  - CF from 10-30;
  - **UNI1 top-500 pool from 11-04.**
- **Testing B / C:** live from 11-05 (ROLL1: 10 positions per setup, twin block off, CF 0.15R).
- **Gen:**
  - 200 slots from 10-26 (GX2);
  - per-setup cap 48;
  - −2R per-setup stop off from 10-22;
  - temporary moves of 5 GENs into Testing 1/2 on 11-09 / 11-10 (`2026-11-09-expo1109-gen-temp-moves`).
- **Primary:**
  - about $4k lots from 10-28;
  - −2R latch from 10-29;
  - TEAM-6 from 11-11 (after the window).
- So "current regime" rates use **11-05..11-10** (after UNI1 and ROLL1). Whole-record rates mix the regimes above.

## 1. Where reps are lost (step 1) — `audit.py` → `audit_reasons_by_account.csv`, `audit_by_account.csv`, `live_daily.csv`

Share of journaled signals by outcome, every live session to 11-10 (run_id=1). The taxonomy is in `audit.py:bucket`.

| account | sessions | signals | taken | borrow/ETB | spread/xcheck | halt | 1-per-symbol | setup cap | buying power | latch | cost filter | twin | split gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary | 26 | 3,654 | 30.2% | 46.1% | 11.2% | 2.6% | 2.6% | 0 | 0 | 5.2% | 0 | 2.0% | 0 |
| On Deck | 23 | 9,399 | 40.9% | 21.3% | 10.5% | 9.3% | 7.2% | 0 | 0 | 2.8% | 2.1% | 0.8% | 4.6% |
| Testing A | 22 | 9,929 | 50.5% | 9.5% | 16.5% | 8.5% | 6.9% | 2.9% | 0 | 0.7% | 2.4% | 0.4% | 0 |
| Testing B | 4 | 332 | 21.4% | 33.4% | 13.3% | 0 | 0.3% | **25.9%** | 0 | 0 | 5.7% | 0 | 0 |
| Testing C | 4 | 159 | 28.9% | **52.2%** | 9.4% | 0 | 0.6% | 0 | 0 | 0 | 8.2% | 0 | 0 |
| Setup Generator | 17 | 7,393 | 38.1% | 5.8% | 18.4% | **14.4%** | 3.0% | 6.6% | **13.1%** | 0 | 0 | 0 | 0 |
| Graveyard | 15 | 17,019 | 35.0% | 8.1% | 14.0% | 0 | 3.3% | 8.1% | 2.6% | **26.8%** | 0 | 1.8% | 0 |

- **Slots: 0 everywhere.** No account ever hit max concurrent positions.
- **Time window: 0.** No signal was journaled as before 09:50. Setup windows are part of each setup's definition and
  are never journaled as skips.
- **Universe / pool and earnings blackout** are applied before any setup scans, so they cannot appear in the journals.
  They are measured in §2.
- **What-if R of the lost signals** (`audit_whatif_by_reason.csv`, optimistic): this is the P/L-noise price of unlocking
  each one.

  | lost to | what-if avg R | signals |
  |---|---|---|
  | account halts | **−0.24** | 2,880 |
  | twin | **−0.25** | 479 |
  | cost filter | −0.13 | 462 |
  | split gate | −0.11 | 426 |
  | latch | −0.07 | 5,134 |
  | borrow | −0.04 | 6,531 |
  | one-per-symbol | −0.04 | 2,090 |
  | buying power | −0.03 | 1,423 |
  | setup cap | +0.00 | 2,163 |
  | spread | −0.00 | 6,674 |

  - So the cap-type losses (buying power, setup cap) are ~neutral reps.
  - The filter-type losses (cost filter, split gate, twin, halts) are below average: unlocking them adds reps *and*
    drags P/L. That is acceptable in paper testing areas, and it is the honest Primary-rules record.
- **Per-account detail in the current regime** (11-05..11-10): `unlock_base.csv`.

## 2. Potential (step 2) — `potential.py` → `potential/<day>.csv`, `all_multipliers.csv`

**Engine:** the as-live replay (`mcf.report.team` → `mcf.replay.harness.run_session`, fills=costs, limit_fill=through).
- **Cached data only:** `data/team` bars and priors. No Alpaca calls.
- **Sessions:** 10-28, 10-30, 11-03, 11-05, 11-09 and 11-10.
- **Setups:** 94 = every enabled setup in On Deck / Testing A / B / C plus 22 Gen picks.
- **Universe:** Primary's full universe, minus PTP and the live earnings blackout.
- **No caps:** slots, per-setup caps, lot cap, twin block, latch, halt, cost filter, split-tape gate and trades/day are all
  off.
- **Kept:** ETB, the replay's spread / quote realism and the 09:50 rule.
- Signals blocked only because another setup held the symbol count as potential entries, since each setup would take
  them in its own account.
- Post-hoc flags:
  - in Testing A's top-500 pool (the UNI1 rule, from that day's priors);
  - stop-exit cost in R (CF 0.15R).
- Runtime: 24-43 min per session, 2 jobs.
- **Run-only guard:** `LD1-ns1-breadthup-t05s1-long`'s vectorised mask raised on a 1-row frame (2 symbols on 11-09 and
  11-10). Those symbols get no LD1 signal in the replay. No repo code was changed.

**Potential vs live, same 94 setups, same 6 sessions** (potential entries per session vs live trades per session):

| current home | live | potential (no caps, full universe) | ratio | potential entries inside top-500 | passing CF 0.15R |
|---|---|---|---|---|---|
| Testing A | 136.5 | 240.5 | ×1.76 | 70% | 79% |
| On Deck | 84.3 | 125.0 | ×1.48 | 63% | 71% |
| Gen (22 picks) | 89.3 | 146.2 | ×1.64 | 60% | 74% |
| Testing B | 10.2 | 25.7 | ×2.5 | 60% | 73% |
| Testing C | 5.7 | 9.2 | ×1.6 | 67% | 85% |

**Fidelity caveat — the replay is a lower bound for some setups.**
- On 11-10 the replay missed 69 symbols on which GEN-261028-02 fired live, most at 09:55. Those are low-ADV ETFs and small
  names.
- The replay's known differences (no fetch latency, synthetic quotes, lab-universe breadth) are listed in
  `mcf/replay/harness.py`.
- So the **headline multiplier per setup is live-measured** (`analyze.py:live_unlock`):
  - (live entries + signals lost to unlockable blocks × the account's downstream pass rate + the Testing A top-500 share
    from the replay) / live entries.
  - The replay ratio is kept beside it as a cross-check (`replay_multiplier`).

## 3. Time to verdict (step 3) — `analyze.py` → `focus_multipliers.csv`

**Focus set (40 setups):**
- the 11 On Deck roster setups and the 7 next in line (`research/ondeck_build/PLAN.md` §2.1-2.2);
- the Gen top 20 by live total R (≥ 5 trades);
- GEN-261021-02 and GEN-261020-10 (the exposure-lab set).

**How it is computed:**
- Records are merged across all accounts (run_id=1, to 11-10).
- **Now:** trades per live session and traded-session share over each setup's live sessions.
- **Unlocked:**
  - trades per session × the live multiplier;
  - traded share + the sessions with signals but no entry where an unlockable block took a signal.
- Dates count NYSE sessions from 11-12 (11-26 closed).

| setup | trades / traded sessions | trades / session now → unlocked | traded sessions / week | multiplier live (replay) | 8/30: now → unlocked | 15/60: now → unlocked |
|---|---|---|---|---|---|---|
| CWT09-gapdn-vwaploss-g10-short | 15 / 8 | 0.68 → 0.71 | 1.8 | 1.05 (0.96) | 12-14 → 12-14 | 02-12 → 02-10 |
| RW1-gapdn-bounce-flowsell-short-FD | 116 / 21 | 5.27 → 7.11 | 4.8 | 1.35 (1.85) | met | met |
| L3-gap-slope-lowdist-FD | 73 / 15 | 3.32 → 6.81 | 3.4 | 2.05 (2.85) | met | met |
| CWT09-gapdn-bounce-g10-lowerhalf-short | 19 / 7 | 0.86 → 0.95 | 1.6 | 1.11 (1.44) | 12-01 → 11-30 | 01-19 → 01-12 |
| NS1-rsidip-rsi5pop-long | 26 / 11 | 1.08 → 1.08 | 2.3 | 1.00 (0.92) | 11-17 | 12-28 |
| MF4-h40-open-flowsell | 22 / 7 | 0.92 → 0.92 | 1.5 | 1.00 (–) | 11-24 | 01-11 |
| NM-HL-T75-pm-long | 52 / 10 | 3.06 → 3.06 | 2.9 | 1.00 (1.11) | met | 11-24 |
| RW7-gapdn-bounce-early-short-FD | 493 / 20 | 22.4 → 31.4 | 4.6 | 1.40 (1.31) | met | met |
| MF3-open-flowsell-rsi5hi | 44 / 10 | 1.83 → 7.78 | 2.1 | **4.25** (3.63) | met | 11-30 → **11-19** |
| ST6-volspikeup-short-mid-t1s1-FD | 15 / 6 | 0.68 → 1.12 | 1.4 | 1.65 (2.08) | 12-14 → **12-02** | 02-12 → 01-08 |
| orb20_a | 38 / 17 | 1.52 → 1.99 | 3.4 | 1.31 (1.41) | met | 12-03 → 11-30 |
| CWT05-flush-m05-v5-long | 14 / 8 | 0.64 → 0.70 | 1.8 | 1.09 (0.84) | 12-18 → 12-15 | 02-23 → 02-12 |
| CWT13-vwapstretch-z075-short | 25 / 7 | 1.14 → 1.85 | 1.6 | 1.62 (–) | 11-18 → 11-16 | 12-25 → 12-10 |
| MF2-open-rsimidhi-flowsell-FD | 134 / 20 | 6.09 → 6.27 | 4.6 | 1.03 (1.05) | met | met |
| L3-gap-slope-rsi5hi-FD | 98 / 18 | 4.45 → 8.63 | 4.1 | 1.94 (2.59) | met | met |
| NS4-pm-vwap-reclaim-oversold-short-FD | 33 / 14 | 1.50 → 2.19 | 3.2 | 1.46 (1.33) | met | 12-08 → 12-01 |
| ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD | 9 / 5 | 0.69 → 1.30 | 1.9 | 1.89 (0.71) | 12-25 → **12-07** | 02-24 → 01-07 |
| NM-MF3-qqqdn-gapdn-FD | 34 / 6 | 2.27 → 2.79 | 2.0 | 1.23 (2.08) | 11-18 | 12-15 |
| GEN-261022-07 (Z12, short) | 55 / 7 | 3.93 → 4.48 | 2.5 | 1.14 (4.30) | 11-13 | 12-04 |
| GEN-261020-05 (ORBfailDn, long) | 75 / 7 | 4.69 → 7.04 | 2.2 | 1.50 (1.17) | 11-16 → 11-13 | 12-09 → 12-04 |
| GEN-261019-04 (EMAdChg, long) | 71 / 6 | 4.18 → 6.52 | 1.8 | 1.56 (1.23) | 11-19 → 11-18 | 12-18 → 12-14 |
| GEN-261019-03 (Ret15m, long) | 25 / 6 | 1.47 → 2.03 | 1.8 | 1.38 (1.40) | 11-19 → 11-18 | 12-18 → 12-14 |
| GEN-261027-07 (RSI14, short) | 22 / 5 | 2.00 → 2.12 | 2.3 | 1.06 (0.92) | 11-20 | 12-14 |
| GEN-261027-01 (MACDh, long) | 14 / 5 | 1.27 → 3.84 | 2.3 | **3.02** (2.67) | 12-01 → **11-19** | 01-04 → **12-09** |
| GEN-261026-03 (NewLOD, short) | 21 / 5 | 1.75 → 2.13 | 2.1 | 1.22 (0.90) | 11-23 → 11-19 | 12-16 → 12-09 |
| GEN-261021-02 (BarRng, long) | 245 / 5 | 16.3 → 23.2 | 1.7 | 1.42 (1.28) | 11-24 | 12-24 |
| GEN-261028-02 (VWAPxDn, long) | 58 / 4 | 5.80 → 6.09 | 2.0 | 1.05 (0.31*) | 11-25 | 12-22 |
| GEN-261027-04 (VWAPatr, short) | 21 / 4 | 1.91 → 2.83 | 1.8 | 1.48 (2.67) | 11-27 | 12-25 |
| GEN-261019-10 (FlowShift, short) | 55 / 8 | 3.24 → 3.43 | 2.4 | 1.06 (1.46) | met | 12-03 |
| GEN-261026-06 (NewLOD, long) | 35 / 3 | 2.92 → 3.50 | 1.3 | 1.20 (1.65) | 12-10 | 01-19 |
| GEN-261020-09 (EMAdChg, long) | 73 / 3 | 4.56 | 0.9 | 1.00 (1.11) | 12-21 | 02-10 |
| GEN-261027-08 (ORBfailDn, short) | 37 / 2 | 3.36 | 0.9 | 1.00 (1.08) | 12-29 | 02-22 |
| GEN-261019-08 (NewHOD, short) | 12 / 4 | 0.71 | 1.2 | 1.00 (0.89) | 12-18 | 02-16 |
| GEN-261023-08 (RSIslope, long) | 17 / 2 | 1.31 → 1.41 | 0.8 | 1.08 (0.80) | 01-06 → 12-18 | 03-11 → 02-01 |
| GEN-261020-10 (BBpct, short) | 58 / 2 | 3.62 → 7.28 | 0.6 | 2.01 (2.13) | 01-19 | 04-07 |
| GEN-261028-07 (Z12, short) | 5 / 2 | 0.50 | 1.0 | 1.00 (1.20) | 01-21 | 04-15 |
| GEN-261028-06 (RSI5, short) | 7 / 1 | 0.70 → 0.80 | 0.5 | 1.14 (1.03) | 02-18 → 12-31 | 05-27 → 02-18 |
| GEN-261029-05 (BearDiv, long) | 8 / 1 | 0.89 → 1.00 | 0.6 | 1.12 (0.37) | 02-09 | 05-07 |
| GEN-261026-02 (VolRatio, long) | 10 / 1 | 0.83 → 1.20 | 0.4 | 1.44 (1.60) | 03-10 → 01-11 | 07-06 → 03-10 |
| GEN-261023-09 (ORBfailDn, short) | 10 / 1 | 0.77 → 1.46 | 0.4 | 1.90 (2.00) | 03-19 | 07-26 |

*\* The replay misses this setup's live 09:55 burst on low-ADV ETFs (see the §2 caveat).*

**Reading it:**
- **Already at 8/30 (10):** RW1-FD, L3-lowdist-FD, NM-HL-T75, RW7-FD, MF3, orb20_a, MF2-FD, L3-rsi5hi-FD, NS4-FD and
  GEN-261019-10. **At 15/60:** RW1-FD, L3-lowdist-FD, RW7-FD, MF2-FD and L3-rsi5hi-FD.
- **For 19 of the 30 still short of 8/30, the 8-traded-session gate binds, not the 30 trades.** Many GENs already have
  35-245 trades but only 1-3 traded sessions (GEN-261021-02: 245 trades on 5 days). They fire in bursts on regime days.
  No account cap fixes that.
- **Where unlocks matter most:**
  - **MF3:** On Deck's split-tape gate blocked it on 10 sessions → 15/60 from 11-30 to 11-19.
  - **GEN-261027-01:** Gen buying power and halts → 8/30 from 12-01 to 11-19.
  - **ST6-FD and ST7Q-FD:** the cost filter / per-setup cap → 8/30 from mid/late December to early December.
  - **L3-lowdist-FD and L3-rsi5hi-FD:** about ×2 more trades a session (cost filter, split gate, halts).
- **One-big-day check (owner 10-25):** this audit is about reps, not edge. The edge columns for these setups (avg R
  without the best day, `1 day` tags) are in `research/ondeck_build/PLAN.md` §2.1 and in `audit_by_account.csv`
  (`avg_r_wo_best_day`, `best_day_share`). Faster reps do not make a one-day record any better — they only get to the
  answer sooner.

## 4. Concrete unlocks, ranked by reps gained vs risk (step 4)

**How the gains are estimated:**
- Extra entries per session are measured in the current regime (11-05..11-10, `unlock_base.csv`).
- Each risk-stage block is converted at the account's downstream pass rate (taken / (taken + spread + CF + BP)).
- Buying-power rejects count 1:1, since they had already passed every check.
- What-if R is the noise price per extra entry.
- All of this is paper and testing-area only; Primary is untouched.

| # | account | unlock | extra entries / session | setups mainly helped | what-if R of the extra | risk |
|---|---|---|---|---|---|---|
| 1 | **Gen** | **lot size ↓, slots ↑** (bpm 3.8 → 1.8, slots 200 → 300: about $536 per lot; peak 300 lots ≈ $161k, under the lowest reject level seen, $184k) | **+240** (BP rejects; 50 setups hit) | GEN-261026-10, -261029-01, -261029-03, -261019-07, -261027-01, -261019-04, -261020-05 … | −0.08 | low. Entries above $536 (about 2-3%) become "size < 1" skips. R is per-trade, so smaller lots do not change R. |
| 2 | **Testing A** | **drop the top-500 pool** (UNI1) | **+60-85** (×1/0.70 on about 159 taken; replay: 30% of potential entries are outside the pool) | RW1-FD, CWT14 pdl, NM-HL, NM-MF3, MF4 … | n/a (not journaled) | low-medium: thinner names cost more. This **reverses an owner rule from 11-04 (UNI1)**; it gives the full universe that On Deck and Primary use. |
| 3 | **On Deck** | **cost filter off** | **+32** | RW7-FD, CWT05-v3, NS1-FD, orb20, exhaustion | −0.23 | medium P/L noise, but **Primary runs without CF**, so On Deck records become Primary-comparable. |
| 4 | **On Deck** | **split-tape short gate off** (= PLAN ODX-1) | **+27** | RW7-FD, MF3, L3-lowdist-FD, MF5, MF1, exhaustion-FD | −0.38 (up-tape days for shorts) | medium; again Primary parity. |
| 5 | **Gen** | per-setup cap 48 → 150 | **+50** | GEN-261021-02, GEN-261022-09, GEN-261020-10 | −0.24 | medium: three busy setups get more weight in Gen's day. |
| 6 | **Testing A** | cost filter off | **+26** | CWT13-z05-long, RW3S-FD, CWT14-pdl-p10 (± lowvol), RW1-FD | −0.05 | low |
| 7 | **Testing B / C** | per-setup cap 10 → 30 (= PLAN ODX-4) | **+11** | CWT13-z075-long (67 blocks in 4 sessions), MF2 base | −0.29 | low |
| 8 | **Testing B / C** | cost filter off | **+5 / +3** | 7 + 5 setups | −0.44 / −0.30 | low (small) |
| 9 | **On Deck, Testing A, Gen** | account halt 120R → 300R | +29 on average in Gen (halts are 1-2 days a month, with 800-1,060 lost signals on such a day) | whatever is live that day | −0.56 (On Deck), −0.27 (Testing A), +0.00 (Gen) | **high noise on blow-up days**. Keep a halt as the bug backstop; this is an owner option only. |
| 10 | **Graveyard** | per-setup −2R latch off | **+324** | the CWT14 orl / pdl / pdh families, RW2-FD | −0.11 | medium. Graveyard reps count for less (rotation homes), but the latch cuts a quarter of its signals. **Needs #11.** |
| 11 | **Graveyard** | lot size ↓, slots ↑ (bpm 3.8 → 1.6, slots 200 → 300: about $500 per lot) | **+89** (BP) | 29 setups | +0.04 | low |
| 12 | **Graveyard** | per-setup cap 25 → 75 | **+79** | CWT12-coil-k4, CWT14-orl-p05 (± lowvol) | +0.45 (optimistic) | low |
| 13 | **On Deck, Graveyard** | twin block off | +2 / +14 | MF3 / heat_fade_short-FD | −0.25 | low reps, negative R. **Not recommended.** |
| 14 | **testing areas** | earnings blackout 4 → 1 day (owner rule 10-07) | **unmeasured; tradable universe +32-67%** in this earnings season | gap / heat setups most | unknown | **owner option.** It changes what a record measures (earnings names behave differently), so the trades would need tagging. To measure it: after 16:00, fetch 1-minute bars for the blackout names and replay. |
| — | **entry windows** | extend | 0 journaled | — | — | Windows are part of each setup's definition: new variants (the -FD copies already exist) go to the backlog, not to config. |
| — | **Primary** | none | — | — | — | frozen to Fri 11-13 (TEAM-6) |

- **Totals:**
  - **#1-#8:** about +455-480 entries a session (Gen +290, Testing A +86-111, On Deck +59, Testing B / C +19).
  - **#10-#12:** Graveyard about +490.
- **Not unlockable:**
  - ETB / borrow (14% of all signals; Alpaca paper only shorts easy-to-borrow);
  - spread / quote checks (14%). These keep paper fills honest. Relaxing them would add reps whose costs the paper fills
    do not show, so they stay as they are.

### Gen buying power: lot ↓ or slots ↑? (owner question)
- Every BP-reject day had **open lots below the 200-slot limit** when the first reject came:
  - 11-05: 164 lots;
  - 11-06: 110;
  - 11-09: 153;
  - 11-10: 148.
- Peak lots on those days were 154-173. **More slots alone gains nothing.**
- At the first reject, open notional was:
  - 11-06: **$184k**;
  - 11-09: **$256k**;
  - 11-10: **$246k**.
- Gen's equity was **$89.3k**, so rejects come at about 2.1-2.9× equity. Alpaca's intraday buying-power use runs ahead of
  the 3.8× the sizing assumes (open orders and short margin count against it).
- **Lots must shrink.**
  - At bpm 1.8 / 300 slots, a lot is about $536, and even 300 open lots (about $161k) stay under the lowest reject level
    seen.
  - The 50 more slots then absorb the recovered demand: 346 taken + 239 rejected a session ≈ 1.7× today's peak lots.
- **Cost of the smaller lots:**
  - entries priced above $536 (2.2% of Gen's entries in 11-05..11-10) cannot buy 1 share;
  - share rounding is coarser (median 25 shares → about 8).
- R is unchanged: it is per trade, and costs per share in R do not depend on size.

## 5. Ready config diffs (apply only after the close, ≥ 16:05 ET, after the owner's yes)

Each diff is a config change. It needs a `research/ledger.jsonl` entry with an effective date (rule-change context),
then `python -m mcf.research.ledger check`. None moves a setup, so `docs/live/assignments.json` is unchanged. Owner
codes are in brackets.

```yaml
# [REPV-1] config/account_gen.yaml  (Gen buying power: smaller lots, more slots)
account:
  slots: 300                     # was 200
  max_concurrent_positions: 300  # was 200
  buying_power_multiple: 1.8     # was 3.8  -> ~$536/lot at $89.3k equity (was ~$1,697)

# [REPV-2] config/account_gen.yaml
account:
  max_positions_per_strategy: 150   # was 48

# [REPV-3] config/account_testing2.yaml  (Testing A: full universe; reverses UNI1 2026-11-04)
universe:                        # delete the whole block:
  # top_n: 500
  # top_n_min_adv: 95000000

# [REPV-4] config/account_testing2.yaml
live:
  max_stop_cost_r: null          # was 0.15 (CF off)

# [REPV-5] config/account_testing.yaml  (On Deck = Primary rules: no CF, no split-tape gate)
live:
  max_stop_cost_r: null          # was 0.15
  split_tape_short_gate:
    enabled: false               # was true   (= PLAN ODX-1)

# [REPV-6] config/account_explore1.yaml and config/account_livelab.yaml  (Testing B / C)
account:
  max_positions_per_strategy: 30   # was 10   (= PLAN ODX-4)
live:
  max_stop_cost_r: null            # was 0.15

# [REPV-7] config/account_graveyard.yaml
account:
  max_setup_daily_loss_r: null     # was 2.0 (latch off)
  max_positions_per_strategy: 75   # was 25
  slots: 300                       # was 200
  max_concurrent_positions: 300    # was 200
  buying_power_multiple: 1.6       # was 3.8 -> ~$500/lot at $94k equity

# [REPV-8] owner option only: account halt 120R -> 300R in testing / testing2 / gen
account:
  max_daily_loss_r: 300            # was 120

# [REPV-9] owner option only, needs the after-close measurement first: earnings blackout in the testing areas
#          (needs a per-account override of universe.earnings_blackout_days; check that mcf/config.py merges
#          `universe:` per account - it does for testing2's top_n)
universe:
  earnings_blackout_days: 1        # was 4 (owner 2026-10-07)
```

**Interactions:**
- REPV-3 + REPV-4 move Testing A to the same universe and cost rules as On Deck after REPV-5. All three testing tiers
  would then run under Primary's entry rules, and records stay comparable across tiers.
- **New record segment (rule 22) for every setup in an account that changes.**
- REPV-1 changes Gen's dollar sizing only, so Gen R records stay comparable.

**Check on the first session after applying:**
- Gen and Graveyard BP rejects ≈ 0 and "max concurrent positions" skips are rare. If the second is not rare, raise slots,
  not lots.
- Testing A entries go up about ×1.4-1.5.
- On Deck split-gate and CF skips = 0.

## 6. More accounts, and the real bottleneck

**Extra Alpaca paper accounts** (the owner creates them; each needs keys, a data branch and a workflow, like ROLL1
11-04). Per extra account:
- **Testing D** with 20 low-rep candidates (backlog: 26 lane-candidates, 14 finalists): about **+10-35 trades a session**
  (Testing B / C live rate 0.55-0.85 per setup-session).
- **Testing D** with 20 busy setups (the Testing A-like rate is 9.4 per setup-session): about **+100-200** trades a
  session.
- **Gen 2** (Gen's 93 setups split in two): about **+240-290** a session — the same as REPV-1 + REPV-2, but at today's lot
  size. Do REPV-1 first; it costs nothing.
- **What extra accounts cannot do:**
  - speed up the verdict on a setup that already runs, since its signals are the same in any account;
  - add independent reps by copying one setup into two accounts — that duplicates trades.

**The real bottleneck for most promising setups is traded sessions per week** (median about 1.8 for the 30 not yet at
8/30). They come from each setup's own regime / time / gap gates.
- Ideas that would add traded days, for the backlog under rules 15-17, not for config:
  - "ungated twins" of the top Gen / CWT09 setups (the same entry without the SPY / QQQ / breadth gate), run in Gen or a
    testing area, with the verdict split by regime;
  - -FD (full-day) windows for the AM / LUNCH / LATE-only GENs.
- Such variants would be new setups with their own records, judged on their own.

## Files
- `audit.py`: live audit. Writes:
  - `audit_reasons_by_account.csv`;
  - `audit_by_account.csv` (per setup × account);
  - `audit_whatif_by_reason.csv`;
  - `live_daily.csv`.
- `unlocks.py`: current-regime loss per session and the conversion. Writes `unlock_base.csv`.
- `potential.py`: no-cap, full-universe replay. Writes `potential/<day>.csv`, `_trades.csv` and `.json`, from cached
  `data/team` bars / priors.
  - Run it with `MCF_TEAM_CACHE=<repo>/data/team MCF_REPLAY_STORE=<repo>/data/replay`.
- `analyze.py`: multipliers and time to verdict. Writes `focus_multipliers.csv` and `all_multipliers.csv`.
- `gen_top.txt`: the 22 Gen picks.
- **Configurations tried:** 1 potential configuration (no caps) × 6 sessions × 94 setups. There is no setup or exit
  search here, so there is nothing to select.
