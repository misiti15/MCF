Educational only — not financial advice

# FOOTRACE1: leaders get a little more room, clear laggards leave sooner (proposal, 2026-11-19)

**Status: proposal only.** No config was changed and nothing was committed. It needs the owner's yes on the numbers
in section 2. Data: the live journal export 2026-10-06..11-18 (LR8 cost basis, all accounts pooled), the paper signal
logs 11-12..11-18, `docs/live/arena_reps.json` (11-18), `docs/live/arena_resources.json` (11-17..11-18) and the
account YAMLs at HEAD 100c3caeb. Source: Live only. No 2-year or replay numbers are used here. **Configurations tried
in this design pass: 5.** These are 1 leader score (tier size fixed at 35) and 4 laggard rules (A, B, C, EXIT100),
each scored at 4 walk-forward cut-offs plus one half-split test. Nothing was fitted on any backtest window, and the
locked block was not read. Job N goes from ~1,882 to ~1,887.

**Rule changes inside the window 11-12..11-18** (research/ledger.jsonl):
- LR8 live cost basis from 11-12.
- Graveyard REPV-11/12 caps from 11-12.
- RW6 moved Graveyard → Live Lab on 11-13.
- ROT1 spotlight in Testing D/E 11-16..11-19.
- **TSZ1 testing-account sizing from 11-17:** slots doubled, risk per trade halved, per-setup cap 30/50 → 100. R stays comparable; $ does not.
- GY-BENCH (18 busy Graveyard setups benched, 20 arena guests) from 11-18.
- C3-EXIT100 (20 arena setups → Graveyard), C3-ROT, ROT2 and GY-ARCHIVE-20 (18 archived) from 11-19, after the window.

## 1. What the data says first (it shapes the design)

**Capacity in the arena barely binds.** Since TSZ1 (11-17..11-18) the arena had **0** resource skips for slots,
per-setup cap or halt.

Peak use per session since 11-17 (sim/capacity_1112_1118.csv):

| account (key) | setups enabled | trades/session | peak lots / max | peak buying power used |
|---|---|---|---|---|
| Testing A (testing2) | 21 | 287 | 147 / 800 (18%) | 21% |
| Testing B (explore1) | 24 | 69 | 69 / 400 (17%) | 19% |
| Testing C (livelab) | 25 | 70 | 41 / 400 (10%) | 11% |
| Testing D (testingd) | 23 (6 away as Graveyard guests) | 132 | 69 / 400 (17%) | 19% |
| Testing E (testinge) | 22 (8 away) | 63 | 45 / 400 (11%) | 11% |
| Testing F (testingf) | 24 (1 away) | 150 | 116 / 400 (29%) | 31% |
| Setup Generator (gen) | 17 (5 away) | 168 | 159 / 300 (53%) | 43% |
| **Graveyard** | 31 own + 20 guests + 3 benched | 276 | **300 / 300 (100%) on 11-12, 11-13 and 11-16**; halted on 11-17 | up to 89% |

- Before TSZ1 (11-12..11-16) the arena had 324 resource skips, all of them "max positions for this setup" at the old
  caps of 30/50.
- **The new setups fit easily.** The admissible list from top10/VARIANTS.md is the owner's leg-E + dispersion, 13
  Tier A rows and 4 Tier B rows: **18 setups at ≈ 142 trades/session.** That figure comes from the lab-engine T1
  estimate. About 109 of it is Tier A, and ULT-19/25/21/26 alone add ~59. Total arena load goes up ~15%. Spread
  across Testing A–F, no account's peak passes ~40% of its slots or buying power.
- **The only account that binds is the Graveyard.**

**The live record does not yet rank setups reliably.** This is the honest caveat behind every number below.
- **Half-split test** on 75 setups with ≥ 40 trades and ≥ 8 sessions: the Spearman correlation between first-half and
  second-half avg R is **−0.18**. 79% of all setups were negative in the second half. The top quartile did no better
  (−0.111 vs −0.107 for all).
- **Walk-forward on the arena:** the 35 "leaders" as of Fri 11-13 went **−50.5R on 355 trades (−0.142)** over
  11-16..11-18. The whole arena did −0.138 in the same sessions, so the leaders had no edge.
- **The broad laggard rule A** (≥ 15 active days, ≥ 30 trades, avg R ≤ 0, w/o best day ≤ 0) flags 35 setups today.
  Its earlier flags then did *better* than the rest: forward avg R +0.015 to +0.203 vs −0.03 to −0.09. **Rule A would
  have cut setups that were about to recover, so it is rejected.**
- **Adding a day-clustered t ≤ −1.5 (rule B)** gives the only small, consistent separation. In the half-split, 12% of
  B-flagged setups were positive in the second half, against 25-26% of the others, and their trade-weighted second
  half was −0.133 against −0.099/−0.115. The walk-forward is mixed on tiny samples: at 11-04 and 11-09, B's 2-3
  setups did −0.19/−0.14 forward; at 11-11 and 11-13, B's 4 setups did +0.36/+0.41.

**Conclusion.** The leader advantage should be *small and only active when resources bind*, and the rotate-out should
need clear evidence (rule B), not just a negative average.

## 2. FOOTRACE1: the three pieces (exact numbers for the owner's yes)

**Scope:** the testing arena (Testing A–F + Setup Generator), **156 enabled setups** today. On Deck, Primary and the
Graveyard keep their own rules.

### (a) Leader tier: 35 setups, re-ranked every session from the nightly data

**Score.** Each setup's whole live record is used (all accounts, LR8). The score is the mean of two ranks:
- total R *without its best session*, which is owner-style total R that respects the one-big-day check;
- shrunk avg R without the best session = Σ R (w/o best day) / (trades + 30).

A setup needs **≥ 10 live trades** to be eligible (93 of 156 qualify today). The **top 35** form the leader tier, and
the `1 day` tag is shown beside every leader.

**What leaders get.** All of it only matters when something binds:
1. **Place in line.** In each arena account's `live.setup_order`: leaders first (narrowest-first among themselves),
   then setups below the minimum reps, then the rest. The narrowest-first order inside each group is kept.
2. **Per-setup cap 125 instead of 100** in Testing A–F, and **175 instead of 150** in the Generator. This needs a
   small per-setup override in `mcf/execution/risk.py` (today the cap is account-wide). It is not a size tilt: risk
   per trade is unchanged.
3. **Benching order.** When C3-ROT/ROT2 or GY-BENCH must bench, a leader is benched last and a below-minimum-reps
   setup is never benched for a leader.

**The leaders as of 11-18** (sim/arena_table_1118.csv): 35 setups, 1,491 trades, +38.7R in total, 18.2% of arena
trades on 11-17..11-18.
- Only **6** have a positive total R w/o best day. They are led by GEN-261026-03 (+10.6R, 25 trades), NM-RWR3 and
  GEN-261027-08.
- **17 carry the `1 day` tag.**
- The other 29 lead only by losing least. Today the tier is "least bad", not "proven".

**Expected shift.** 0 extra trades at today's load: there were no skips since 11-17. In the 11-12..11-16 regime, 180
leader signals were skipped by per-setup caps. Their R cannot be known because they were never traded.

### (b) Stricter rotate-out: FOOTRACE-EXIT, checked at the Friday-after-close review

An arena setup goes to the Graveyard (a performance move, as with EXIT100) when **all** of these hold:
- ≥ **15 active days** and ≥ **30 live trades** (the C3-ROT verdict floor, so no early kill);
- **avg R ≤ 0** and **avg R w/o best day ≤ 0**;
- **day-clustered t ≤ −1.5**;
- ≥ 0.5 signals per active day. Rare or day-gated setups are judged on eligible days only and are never moved before
  they reach the floor there.

Two exemptions:
- Workbench copies in their first 15 active days.
- Setups with a pre-registered test pending.

**EXIT100 stays as it is** (≥ 100 trades, avg ≤ −0.05R, w/o best day ≤ 0).

**Today (data to 11-18):**
- FOOTRACE-EXIT flags **9** setups: 8 GEN plus intraday_momentum. They hold 6.0% of arena trades, about 26 trades
  per active day, and made −40.5R on 171 trades since 11-12.
  - Testing B: 2 (GEN-261020-03, −48.7R, t −3.7; GEN-261029-02)
  - Testing C: 3 (GEN-261026-10, GEN-261027-04, GEN-261027-09)
  - Testing E: 1 (GEN-261022-08)
  - Testing F: 2 (intraday_momentum, t −2.6; GEN-261022-06)
  - Gen: 1 (GEN-261020-01)
- EXIT100 flags another 3: exhaustion_short, GEN-261020-10, GEN-261029-01.
- **Friday 11-20: 12 moves in all, against 3 under EXIT100 alone.**
- The other 41 verdict-ready setups and the **106 setups below minimum reps are not touched.**

### (c) Graveyard capacity and Friday archive

**The Graveyard has no room to host new testing setups.**
- It ran at 300/300 slots on 3 of 5 sessions and was halted on 11-17.
- GY-ARCHIVE-20 freed ~500 trades/session from 11-19, but the 20 C3-EXIT100 entrants arrived the same day (~400
  trades/session on their past rate).
- With 11 older residents (~106), up to 20 guests (≤ 47) and Friday's 12 movers (~44), the estimated load is
  **~550-600 trades/session**. On 11-17, 374 trades already peaked at 80% of slots.
- 3 GY-BENCH residents (~95 trades/session) return on 11-25.

**Proposal for the Graveyard:**
- **No new testing setups go to the Graveyard.** They take arena seats.
- At the **Friday 11-20 GY-LIFE review**, 4 residents meet archive conditions 1-4 on data to 11-18. Each is archived
  only if condition 5 (no test pending) and Friday's data still hold. Together they free ~79 trades/session.
  - CWT14-failbrk-orl-p05-long: 1,027 Graveyard trades, −0.106, last 10 sessions −50.8R, not exempt (1 big day).
    It may be held by a pending CWT14 family test.
  - MF3-open-flowsell-rsi5hi-FD
  - NS3-failed-vwap-reclaim-short-FD
  - MF1-945-flowsell-vwapup-FD
- Add the Graveyard to `arena_resources.json` (monitor only). Above 5% resource skips, the existing GY-BENCH valve
  (> 150 Graveyard trades → 5 sessions off) runs busiest-first.

### Seats for the new setups

**Seat cap: 25 enabled setups per testing account (A–F).** This is new: today there is no cap, and capacity is not
the limit.
- Free today: A 4, B 1, C 0, D 2, E 3, F 1 = **11**.
- After Friday's 12 moves, 8 more in A–F (19 in all), plus 1 Gen seat.
- **Placement:**
  - **Fri 11-20:** leg-E + dispersion and the 13 Tier A rows. 11 take free seats; 3 are temporary overflow until
    Friday's moves take effect.
  - **Mon 11-23:** the 4 Tier B rows, labelled "debatable / derived from <parent>".
  - Each goes to the lightest account (E, C, B first), with twins kept apart. leg-E is not placed in Testing E (WB4
    is there).

## 3. Standing rules this amends (owner's yes needed on each)

1. **Playing time (2026-11-03), "never in-session throttling in Primary/Testing":** amended for the arena only. Leaders
   get place-in-line and +25 lots of per-setup cap *only when slots, buying power or the per-setup cap bind*. A setup
   below the minimum reps never loses its place to a non-leader, and it is never benched for a leader. Primary and On
   Deck are unchanged.
2. **C3-EXIT100 (rule 24):** adds FOOTRACE-EXIT as a second Friday exit. EXIT100 is kept unchanged.
3. **C3-ROT / ROT2 (rule 24):** the `pick()` order becomes below-minimum-reps first, then leaders, then the rest. The
   ROT2 5% trigger and the never-bench rule for rare setups are unchanged.
4. **Testing arena (2026-11-12), "all treated the same":** leaders now differ only in the tie-break order. Exposure
   balance is kept with the seat cap of 25.
5. **GY-LIFE (rule 29):** unchanged, plus a capacity monitor line and "no hosting new testing setups while load is
   above 80% of slots".

Guardrails (rule 26) are checked:
- This is not a sizing tilt (risk per trade is unchanged).
- It is not an early kill (it respects the 15-active-day / 30-trade floor).
- It uses active days, not trade counts, as reps.

## 4. Simulation on the live record since 11-12 (honest version)

| | number |
|---|---|
| Arena R 11-12..11-18 (all setups that sat in arena accounts) | −307.2R on 3,779 trades |
| Moves at a Fri 11-13 review (walk-forward) | FOOTRACE-EXIT 6 (EXIT100 2; rule A would have moved 21) |
| Those 6 over 11-16..11-18 | **+9.6R on 78 trades (+0.123)**: moving them would have taken +9.6R out of the arena |
| EXIT100's 2 over the same sessions | +30.7R on 228 trades |
| Leaders (as of 11-13) over 11-16..11-18 | −50.5R on 355 trades (−0.142) vs arena −0.138 |
| Exposure shifted to leaders since 11-17 | 0 trades (no resource skips) |
| Moves at Fri 11-20 (data to 11-18) | 12 (9 FOOTRACE-EXIT + 3 EXIT100) vs 3 today |

**Effect on MCF's total R.** It is roughly 0 by design. Movers keep trading in the Graveyard, which still counts in
end-of-day totals, as long as the Graveyard has room. Today it often does not, so a move can turn into fewer trades
for the mover.

**Effect on new-setup exposure.** It is the real gain: about 19 seats in Testing A–F, at under 40% peak load.

**There is no evidence yet that the leader tier earns more R.** The 6-session forward windows are tiny and
overlapping, and one regime (−R on 11-17) dominates. Re-check at session 20 of FOOTRACE (pre-registered):
- if FOOTRACE-EXIT movers keep beating the arena average forward, drop the rule;
- if leaders do not beat the arena by ≥ 0.02R/trade, drop the cap bonus.

## 5. Build (after the owner's yes; never intraday)

- Nightly `python -m mcf.report.footrace` writes `docs/live/footrace.json` (leaders, score, `1 day` tag,
  FOOTRACE-EXIT watch list).
- The config loader reorders `setup_order` and applies the leader cap override at session start.
- `risk.check` gets a per-setup `max_positions` override.
- Tests, a ledger entry, assignments regenerated with every move, merge after 16:00 ET.
- Earliest effective date: Mon 11-23. The first FOOTRACE-EXIT review is Fri 11-20 after the close.

**Files:** `sim/score.py`, `sim/wf.py`, `sim/lag2.py`, `sim/sim.py`, `sim/persist.py`, `sim/arena_table_1118.csv`
(156 arena setups with score, flags and t), `sim/capacity_1112_1118.csv`. The scripts read the scratchpad journal
export (`ev1119/w/trades.parquet`).
