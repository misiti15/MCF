# W3-reps — Quality Reps Plan (crunch, 2026-11-18 evening)

_Educational only — not financial advice. Paper accounts. Research and proposals only: no config, runtime, assignment or
ledger change was made, nothing was merged, and every move below waits for an owner reply code. Plan pre-registered in
PLAN.md (16:45 ET, before any number was computed)._

**Data:** live journals (`origin/mcf-data*:journal.db`, live run = runs.kind `paper`; shadow = kind `shadow`, from 11-17),
frozen per-session setup snapshots (`setups/<day>.json`, so benched/away sessions are not counted as live sessions), the
11-18 `docs/live/assignments.json`, and account configs on `origin/claude/charming-mccarthy-i3rhhr`. R is after costs,
`pnl_adj / (|entry − stop| × shares)`. Through the 11-18 close. **Configurations: 3** (inventory 0, one pre-registered
shadow-vs-live pairing, one allocation rule + one variant); bar for any t: max(1.5, √(2 ln 3)) = 1.50. The locked block
was not read in any form, no 2-year data was used, L3-gap-slope-fromopen-FD is untouched, nothing touches Primary's
lineup (promotion hold on).

**Rule changes inside the windows (ledger):** sizing 10-28; Primary −2R latch 10-29; CF 0.15R cost filter in testing 10-29;
ROLL1 11-05; TEAM-6 11-11; restructure + LR3/LR8 + REPV 11-12; ROT1 block 1 11-16..11-19; TSZ1 testing half-size,
promotion hold, shadow mode, 15 WB copies 11-17; GY-BENCH + guests, recorded quotes, SRCV1 11-18. "Current regime" below
= sessions 11-17..11-18 (TSZ1 sizing and caps in force). Per-setup records mix the earlier regimes.

## The short version

1. **The arena is signal-limited, not resource-limited.** In the current regime the six testing accounts skip only
   **0.2-2.4% of signals for account resources** (slots, buying power, per-setup cap, halt, crowding) and peak at
   **10-29% of their slots** (On Deck 18%). What removes signals is setup-side: spread (30 bps / 25% of stop), the 0.15R
   cost filter, and borrow (ETB) on shorts. So **session rotation cannot buy reps for low-rep setups today**: benching a
   busy setup frees slots nobody is short of. Rotation caps (C3-ROT's 2 CWT14 + 6 GEN) are worth it only for drag, not
   playing time.
2. **Low-rep high-potential setups are slow because they rarely signal, or their signals fail spread/borrow.** Their time
   to the C3-ROT/C3-BAR2 minimum (30 trades AND 15 active days) is set by **active days**, not trades:
   GEN-261027-08 ~9 sessions, GEN-261019-02 ~11, GEN-261027-01 ~22, NM-RWN3 ~27, NM-RWR3 ~30, GEN-261026-03 ~45,
   NM1-cwt09-g10 ~55, NM-RWN4 ~65, NM-RWN5 ~110. CWT09-vwaploss-g10 (On Deck) ~4. L3-lowdist / L3-rsi5hi already meet it.
3. **Shadow is ready to serve as an activity rep source, not yet as an R source.** Paired on the decision bar over
   11-17..11-18 (2,683 live trades, 10 accounts): **match 98.6%, extra 0.4%** (both pass the trust targets), setup-day R
   correlation 0.958, account-day 0.989, but **R bias −0.049R per trade, t −12.0** (pessimistic, from fill profile B; it
   fails a two-sided ±0.01R reading, passes "never optimistic"). Only 2 held-out days (< 3).
4. **Shadow of live setups adds almost no reps** (only resource-blocked signals: 14 extra non-resource + 496 resource-blocked
   lots in 2 sessions, 450 of them the Graveyard's latch). **The rep source is `shadow_setups`, which no account uses
   today.** It can run setups that are not live (benched, archived, queued Workbench tunes) and run candidates under
   **Primary's own context** at zero orders, slots or risk.
5. **Workbench copies are paired A/B, not new reps.** Live copies share 64-100% of their symbol-days with their parent
   since 11-17 (RW1-WB3 97%, MF2-WB3 95%, RW7-WB3 85%, L3/RW5/NM-ETF copies 67-100%). Counting both inflates a family's
   reps (pseudo-replication).
6. **14 GEN setups moved to Testing A-F on 11-16 have been silent for 3 sessions** (0 signals; 1-19 signals/session in
   Gen before). All 14 carry an up-market gate (spy_fo > 0/0.25/0.5, qqq_fo > 0/0.6, breadth(_open) > 0.5/0.65) while
   the down-gated GEN setups in the same accounts fire — **regime silence in a weak tape, not a transfer bug.** Benching or
   re-shuffling these costs them their rare matching days.

## 1. Inventory — signals, fills, skips (files: inventory_by_account.csv.gz, setups.csv, triage.csv)

**Accounts (current regime 11-17..11-18):**

| Account | Enabled setups (11-18) | Fills / session | Peak open lots 11-17 / 11-18 (slots) | Resource skips | Main signal losses |
|---|---|---|---|---|---|
| Primary | 6 | 35.5 | 9 / 33 (77) — 43% | 10.5% (L3 −2R latch, RW3/RW5 latch, crowding) | borrow 220, spread 33 |
| On Deck | 13 | 91.0 | 70 / 35 (400) — 18% | 0.5% | borrow 84, spread 83, cost filter 59 |
| Testing A | 25 | 287.0 | 147 / 114 (800) — 18% | 1.4% | spread 354, borrow 168, cost filter 144 |
| Testing B | 25 | 69.0 | 69 / 35 (400) — 17% | 2.4% | spread 77, cost filter 44 |
| Testing C | 25 | 70.0 | 31 / 41 (400) — 10% | 0.8% | spread 65, cost filter 35 |
| Testing D | 19 | 131.5 | 48 / 69 (400) — 17% | 0.2% | spread 137, cost filter 63 |
| Testing E | 17 | 63.0 | 45 / 25 (400) — 11% | 0.8% | spread 77, cost filter 26 |
| Testing F | 24 | 150.5 | 116 / 69 (400) — 29% | 0.9% | spread 114, cost filter 106 |
| Gen | 18 | 167.5 | 159 / 104 (300) — 53% | 1.0% | spread 106, borrow 31 |
| Graveyard | 34 (20 guests) | 276.5 | 239 / 87 (300) — 80% | **65.8%** (account halt 1,531 on 11-17 from 10:50; −2R latch 715) | spread 431 |

Before TSZ1 the picture was different: over the whole record the per-setup cap (Primary L3 648, Graveyard CWT12/CWT14,
Gen GEN-261021-02/-22-09/-20-10), Gen's broker buying-power rejects (1,215) and account halts (Gen 1,065, On Deck 878,
Testing A 845) were the resource losses. TSZ1 (800/400 slots, cap 100) removed them in Testing A-F.

**Triage of the 206 setups enabled on 11-18** (triage.csv; rules in triage.py): OK 86, BLOCKED (≥ 60% of signals
skipped) 50, NEW (< 3 sessions in the account) 40, DORMANT (≤ 0.1 signals/session) 23, SLOW (< 0.5 fills/session) 7.
- *DORMANT by design* — index / breadth-gated IDX1/2/3/5 and LD2-8 (0-0.6 signals/session; one trade per ~10 sessions,
  so 30 trades take more than a year), CWT04-backside a15/a25 (borrow), NM-PM-gapdn-above-pdh.
- *DORMANT this week (regime)* — the 14 up-gated GEN setups in point 6 of the short version.
- *BLOCKED by borrow* — the CWT09 g10 pair and NM1-cwt09-g10 (86-95% ETB), L3-lowdist / L3-rsi5hi (77-86%), L3-fromopen
  in Primary (94%). These are real: Primary faces the same borrow list, so the ETB subset is the honest record.
- *BLOCKED by spread* — NM-RWR3 (65%), NM-RWN3 (67%), GEN-261027-01 (75%), MF1, several GEN. Also real for Primary.
- *BLOCKED by per-setup cap* (history, mostly pre-TSZ1) — NM-RWN4 (Testing F, 54), GEN-261029-06 (Testing D, 100),
  CWT13-z075-long (Testing B, 67), MF2 base (Testing B, 19).

## 2. Quality reps

A rep is "quality" when it is (a) a real fill under rules close to Primary's, (b) on a separate day (active days are the
binding minimum), (c) not a duplicate of another lot on the same move (stacked lots, sibling copies), and (d) not one
day's burst. quality.csv lists trades, distinct symbol-days, active days, trades per active day and the largest one-day
share of trades per assigned setup. Examples: NM-RWN4 40 trades on 2 days (20 per day, 80% in one day) — 2 quality
days, not 40 reps; GEN-261027-08 78 trades on 6 days (13 per day); NM-ETF-late-dip 30 trades on 14 days (2.1 per day).

Two places where testing reps differ from what Primary would see:
- **Cost filter.** Testing carries the 0.15R stop-cost filter; Primary does not. Across the high-potential list it
  removed 136 signals against 1,180 fills (~10%) — trades Primary would have taken and the testing record never shows.
- **Overlap with Primary's book.** C3-BAR2 wants the record on trades that do not overlap Primary; testing accounts
  cannot measure crowding or latch interaction with Primary's six.

## 3. Time to a verdict for the high-potential list

High potential (pre-defined in PLAN.md): consultant P2/P3 contender or low-rep lists, C3-WB5 queue parents, or
w/o-best-day > 0 with ≥ 10 trades. Rate = live fills and active days per enabled session in the current home over its
last ≤ 10 sessions; ETA = sessions until 30 trades AND 15 active days (whole-record counts merged across accounts).
Records are context only (W2 owns promotion scoring); the "1 day" tag marks best-day share ≥ 50%.

| Setup | Home | Trades / active days | Avg R / w/o best day (best-day share) | Signals / fills per session (home, last ≤ 10) | Active-day rate | Sessions to 30 trades + 15 days | Main loss of signals |
|---|---|---|---|---|---|---|---|
| `NS3-failed-vwap-reclaim-short-FD` | Graveyard | 264 / 24 | -0.153 / -0.199 (-) | 84.7 / 14.6 | 0.9 | met | setup -2R latch:293 |
| `RW6G1-ns2-up3-vwap2sd-short-FD` | Graveyard | 67 / 22 | 0.02 / -0.055 (2.97) **1 day** | 8.1 / 3.7 | 0.9 | met | borrow/short-gate:35 |
| `L3-gap-slope-lowdist-FD` | On Deck | 109 / 19 | 0.252 / 0.12 (0.66) **1 day** | 18.9 / 5.0 | 0.7 | met | borrow/short-gate:228 |
| `L3-gap-slope-rsi5hi-FD` | On Deck | 158 / 23 | 0.101 / 0.024 (0.82) **1 day** | 61.8 / 7.5 | 0.9 | met | borrow/short-gate:340 |
| `MF2-open-rsimidhi-flowsell-FD` | On Deck | 187 / 25 | -0.151 / -0.351 (-) | 16.2 / 6.2 | 0.8 | met | spread:43 |
| `MF4-h40-open-flowsell-FD` | On Deck | 221 / 28 | -0.245 / -0.278 (-) | 19.9 / 8.1 | 1.0 | met | borrow/short-gate:53 |
| `NS3-failed-vwap-reclaim-short` | Test E | 89 / 16 | -0.211 / -0.327 (-) | 8.2 / 3.4 | 1.0 | met | spread:17 |
| `CWT09-gapdn-vwaploss-g10-short` | On Deck | 24 / 13 | 0.228 / 0.15 (0.48) | 19.4 / 1.6 | 0.8 | 4 | borrow/short-gate:86 |
| `MF4-h40-open-flowsell` | Test A | 41 / 11 | -0.092 / -0.144 (-) | 10.17 / 3.17 | 0.67 | 6 | spread:33 |
| `GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short` | Test B | 78 / 6 | 0.112 / 0.03 (0.79) **1 day** | 16.0 / 12.33 | 1.0 | 9 | cost filter:5 |
| `GEN-261019-02-BBpctle0p017-SMA20slopege0p46-PM-QQQdn-t05s1-long` | Test F | 13 / 7 | 0.231 / 0.142 (0.53) **1 day** | 2.67 / 1.67 | 1.0 | 11 | cost filter:3 |
| `MF2-open-rsimidhi-flowsell-FD-WB3` | Test A | 22 / 2 | -0.867 / -0.837 (-) | 19.5 / 11.0 | 1.0 | 13 | spread:6 |
| `CWT09-gapdn-bounce-g10-lowerhalf-short` | On Deck | 23 / 9 | 0.004 / -0.207 (n/m) **1 day** | 20.0 / 0.8 | 0.4 | 15 | borrow/short-gate:89 |
| `MF2-open-rsimidhi-flowsell` | Test B | 19 / 9 | -0.443 / -0.561 (-) | 6.0 / 1.4 | 0.4 | 15 | per-setup cap:19 |
| `RW6G1-ns2-up3-vwap2sd-short` | Test E | 9 / 5 | 0.096 / -0.107 (1.86) **1 day** | 2.2 / 1.0 | 0.6 | 21 | borrow/short-gate:4 |
| `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long` | Test E | 17 / 7 | 0.201 / 0.16 (0.35) | 2.4 / 0.6 | 0.4 | 22 | spread:7 |
| `NM-RWN3-ns3-spyup-early-short` | Test B | 14 / 7 | 0.279 / -0.268 (1.55) **1 day** | 2.4 / 0.8 | 0.3 | 27 | spread:8 |
| `L3-gap-slope-rsi5hi-FD-WB4` | Test B | 3 / 1 | -0.153 / - (-) | 9.5 / 1.5 | 0.5 | 28 | borrow/short-gate:14 |
| `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB1` | Test E | 2 / 1 | 0.342 / - (1.0) **1 day** | 1.0 / 1.0 | 0.5 | 28 | - |
| `NM-RWR3-ns3-qqqup-early-short` | Test C | 11 / 6 | 0.41 / 0.133 (0.76) **1 day** | 2.0 / 0.7 | 0.3 | 30 | spread:7 |
| `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` | Test D | 25 / 6 | 0.454 / 0.288 (0.54) **1 day** | 0.8 / 0.8 | 0.2 | 45 | - |
| `NM1-cwt09-g10-vwaploss-short` | Test B | 8 / 5 | 0.441 / 0.33 (0.44) | 7.9 / 0.4 | 0.3 | 55 | borrow/short-gate:69 |
| `L3-gap-slope-lowdist-FD-WB4` | Test F | 1 / 1 | 0.834 / - (1.0) **1 day** | 6.5 / 0.5 | 0.5 | 58 | borrow/short-gate:6 |
| `NM-RWN4-ns2-spyup05-notfri-short` | Test F | 40 / 2 | 0.228 / -0.043 (1.04) **1 day** | 21.0 / 6.4 | 0.2 | 65 | per-setup cap:54 |
| `NM-RWN5-ns3-mon-weakrs-short` | Test D | 8 / 3 | 0.543 / 0.884 (0.39) | 0.2 / 0.2 | 0.2 | 110 | - |
| `GEN-261021-01-BearDiv-RVolDayle0p47-BarsSinceHODle0-LAM-SPYltm0p25-t1s1-short` | Graveyard | 15 / 2 | 0.335 / 0.561 (0.89) **1 day** | 3.0 / 0.0 | 0.0 | n/a (no fill yet) | cost filter:3 |
| `RW6G1-ns2-up3-vwap2sd-short-FD-WB3` | Test A | 0 / 0 | - / - (-) | 4.5 / 0.0 | 0.0 | n/a (no fill yet) | borrow/short-gate:9 |
| `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB5` | Test D | 0 / 0 | - / - (-) | 0.0 / 0.0 | 0.0 | n/a (no fill yet) | - |
| `NM-RWN5-ns3-mon-weakrs-short-WB3` | Test E | 0 / 0 | - / - (-) | 0.0 / 0.0 | 0.0 | n/a (no fill yet) | - |
| `CWT09-gapdn-vwaploss-g10-short-WB4` | Test F | 0 / 0 | - / - (-) | 0.5 / 0.0 | 0.0 | n/a (no fill yet) | borrow/short-gate:1 |

Reading it: for every low-rep setup the slower clock is **active days** (rate 0.2-0.6), and every one of them sits in an
account with < 3% resource skips. **No placement change shortens these ETAs**; keeping them enabled every session does.
The −WB copies with 0 fills (RW6G1-WB3, GEN-261027-01-WB5, NM-RWN5-WB3, CWT09-vwaploss-WB4) have the same rare signals
as their parents, so they cannot reach a paired verdict faster than the parent does.

## 4. Shadow as a rep source (shadow_vs_live.py, shadow_vs_live.txt)

Pairing key: account, setup, symbol, date, decision bar (live `coid` bar vs shadow `bar_time`), 11-17..11-18.

| Account | Live trades | Matched | Match | Extra (non-resource) | Paired R diff (shadow − live), t |
|---|---|---|---|---|---|
| Primary | 71 | 68 | 95.8% | 0 | −0.081, −5.75 |
| On Deck | 182 | 182 | 100% | 5 (2.6%) | −0.014, −1.35 |
| Testing A | 574 | 573 | 99.8% | 4 | −0.045, −6.00 |
| Testing B | 138 | 138 | 100% | 0 | −0.075, −4.36 |
| Testing C | 140 | 140 | 100% | 1 | −0.072, −4.24 |
| Testing D | 263 | 263 | 100% | 1 | −0.048, −4.49 |
| Testing E | 126 | 126 | 100% | 1 | −0.047, −3.15 |
| Testing F | 301 | 301 | 100% | 2 | −0.058, −7.08 |
| Gen | 335 | 335 | 100% | 0 | −0.044, −2.23 |
| Graveyard | 553 | 520 | 94.0% | 0 (+450 resource-blocked) | −0.046, −5.27 |
| **All** | **2,683** | **2,646** | **98.6%** | **14 (0.4%)** | **−0.049, −12.0** |

Families: CWT14 −0.030 (766 pairs), GEN −0.050 (766), RW7 −0.076, RW3S −0.092, CWT13 −0.106, L3 −0.073, MF2 +0.063
(t 1.77, 63 pairs), exhaustion_short +0.003. Setup-day R correlation 0.958 (236 setup-days), account-day 0.989 (20).

What it means for reps:
- Shadow sees the same signals as live, so it is a faithful **activity** record (which days a setup fires and fills).
  Its R is consistently **conservative** by about 0.05R per trade (profile B was expected to cost 0.02-0.03R).
- With 2 held-out days it is "uncalibrated" by the owner's rule (< 3 days). Under TIER-BIAS **Yes** (two-sided ±0.01R) it
  would not earn the 0.35 tier at today's bias; under **No** it would once it has 3+ days. That choice is the owner's
  (decision TIER-BIAS is open); fill-profile changes are owner-only.
- For live setups shadow adds ~0 extra reps (testing accounts block almost nothing for resources). The Graveyard is the
  exception: 450 latch/halt-blocked lots in 2 sessions.
- Recommended use: shadow trades as a **separate rep column** (active days, fills) that orders rotation and shows
  Primary-context behaviour; promotion stays on live records (SRCV1, C3-BAR2).

## 5. Allocation design (rule REPS-1; variant REPS-1b)

Moves are whole-session only, after the close; nothing throttles inside a session in Primary or Testing.

1. **Rare / regime-gated (< 1 fill per session, or carrying an index/breadth/SPY/QQQ day gate): always on, never benched,
   not moved inside a rotation block.** They cost no resources when silent, and a benched session can be their only
   matching day. Their verdict clock counts *eligible* days (day-type tag from C3-SCORE).
2. **High-potential low-rep: always on in a testing account, plus a Primary-context shadow** (W3-PSHADOW below), so each
   gets a second rep column under Primary's rules (no cost filter, Primary's latch on shadow's own R, overlap with the six).
3. **Bulk (≥ 10 fills per session: CWT14 pdl, RW7, CWT13-z05, GEN-261029-06, GEN-261028-08, GEN-261027-08):** reach 30
   trades in 1-3 sessions; only active days matter. Rotation caps are for drag, not playing time; a benched session runs
   in shadow so its activity record keeps going (W3-BENCHSHADOW).
4. **Copies:** one family count. A −WB copy's trades are reported as a paired difference against the parent on the same
   symbol-days, never as extra family reps.
5. **Account loads:** with peaks at 10-29% of slots, Testing A-F can take ~2x today's setup count before resources bind
   (keep each account's peak under ~60% of slots and resource skips under 5%; re-check after each block). No account
   needs fewer setups. Gen (53%) and the Graveyard (80%, halted 11-17) are the only tight accounts.
6. **Graveyard guests:** do not move testing setups into the Graveyard for exposure. The testing accounts have room,
   and guests share the Graveyard's account halt (11-17: halted 10:50, 1,531 signals skipped). The 20 guests return home by
   rule on 11-25 (GY-BENCH); on 11-18 they produced 3 signals in total.
7. **Variant REPS-1b** = REPS-1 plus C3-ROT's 2 CWT14 + 6 GEN session caps. Expected rep effect for low-rep setups: ~0
   (resource skips 0.2-2.4%); expected drag effect: C3-ROT's own numbers. Owner picks.

**Expected live trades / session by tier (current homes):** rare tier ~0.1-1 each (IDX/LD 0.1-0.6, NM-RWN5 0.2,
GEN-261026-03 0.8, NM1-cwt09-g10 0.4, NM-RWR3 0.7, NM-RWN3 0.8, GEN-261027-01 0.6); high-potential mid tier 1-6
(CWT09-vwaploss-g10 1.6, GEN-261019-02 1.7, L3-lowdist 5.0, L3-rsi5hi 7.5); bulk 10-67 (GEN-261027-08 12.3, CWT14 pdl
p10 39-40, RW7 66.7).

## 6. Proposals (reply codes) — none applied

| Code | What | Evidence | Effect | Needs owner |
|---|---|---|---|---|
| **W3-PSHADOW** | Primary-context shadow of the candidates: `shadow_setups` in config/default.yaml (Primary) = L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD, CWT09-gapdn-vwaploss-g10-short, GEN-261027-08-…, GEN-261027-01-…, GEN-261026-03-…, NM-RWR3-ns3-qqqup-early-short, NM1-cwt09-g10-vwaploss-short, NM-RWN5-ns3-mon-weakrs-short; **`shadow_setups: []` added to every account_*.yaml** (lists are not merged, accounts would otherwise inherit it). After a close. | Shadow match 98.6%, extra 0.4%; testing reps miss ~10% of Primary-eligible trades (cost filter) and cannot see overlap with the six | Per candidate, a Primary-rules activity/R column (conservative ~0.05R) and the overlap record C3-BAR2 asks for; 0 orders, slots, latch or halt. Watch `budget_frac` 0.10: if shadow time exceeds it, shadow-only setups run every other poll (reps silently halve) | Yes |
| **W3-BENCHSHADOW** | A benched setup (GY-BENCH, C3-ROT rotation, any future bench) and an archived one (GY-ARCHIVE-20, if yes) run as `shadow_setups` in its account while off | Benched/archived setups accrue no record today; GY-LIFE graduation/archival needs Graveyard days | Records keep going at 0R drag; the 18 benched Graveyard setups were ~570 trades/session | Yes |
| **W3-WBSHADOW** | Queued Workbench tunes (C3-WB5: CWT09-g10 → g15, NS3 gated short, MF2/MF4 2-part gate, GEN-261027-08 exit, L3-rsi5hi refire off) start as `shadow_strategies` in the parent's account, compared with the parent's own shadow lots (same fill model, so the bias cancels), before any live copy | Live copies share 64-100% of the parent's symbol-days; C3-WB's final gate is paired shadow 40+ trades / 5+ sessions | Reaches the paired gate without a live copy; a live copy only after the shadow pass | Yes |
| **W3-RARE-ON** | Rule: rare / regime-gated setups (< 1 fill per session or a day gate) are never benched or moved inside a rotation block; their clock counts eligible days | 14 up-gated GEN setups silent 3 sessions in a weak tape; IDX/LD 0-0.6 signals/session | Protects the few matching days; no resource cost | Yes |
| **W3-ROT-DRAG** | If C3-ROT is approved, label its CWT14/GEN session caps as a drag control, not a playing-time fix, and re-check the claim each block: apply a cap only where an account's resource skips exceed 5% | Current resource skips 0.2-2.4% in Testing A-F, peaks 10-29% of slots | Avoids benching for a gain that does not exist; keeps C3-ROT's rep columns and triage | Yes |
| **W3-REPCOL** | Reporting only: rep columns on the rotation/dashboard view — active days, symbol-days, trades per active day, max one-day share, Primary-context shadow days, ETA to 30/15, copies shown as paired | quality.csv, setups.csv | Rotation ordered by quality reps, not raw counts (C3-ROT asked for "shadow rep column") | Housekeeping (no trading effect) |
| **W3-NOGUEST** | Rule: no more Graveyard guest moves for exposure; current guests go home 11-25 as scheduled | Guests 3 signals on 11-18; Graveyard halted 11-17 (1,531 skips); testing accounts ≤ 29% of slots | Guests not exposed to Graveyard halt risk | Yes |
| **W3-IDX** (option) | Index/breadth-gated IDX/LD setups (0-0.6 signals/session) get a stated clock ("one verdict per ~N matching days") or are judged on a pre-registered SPY/QQQ replay once FWDCAL is green | ETA 45-290 sessions at today's rates | Stops these sitting unjudged for a year | Yes (SRCV1 keeps replay at weight 0 today) |
| **W3-SHADOW-INFO** | No change: information for TIER-BIAS / fill profile | Bias −0.049R, t −12.0, 2 days; profile B expected −0.02/−0.03 | Owner decides tier rule and profile | Yes (FYI) |

## 7. What was not done / caveats

- Two shadow days only; the shadow numbers may move. Bias is from the same 2 days.
- ETAs assume the last ≤ 10 sessions' rates; a regime change (up-trend) can double or halve them. For setups with 2-3
  sessions in their account (moved 11-16), rates rest on 3 sessions.
- Resource figures are for 11-17..11-18 (TSZ1); a large up day with many longs could load accounts more.
- The −WB copy overlap uses live symbol-days since 11-17 (small counts for some copies).
- Graveyard: 11-17 was a −177R day with the halt at 10:50; that one day dominates its resource-skip share.
- R columns are context, not verdicts; several carry the "1 day" tag (see table).

Code: `code/snapshots.py`, `inventory.py`, `setups.py`, `triage.py`, `recent_skips.py`, `quality.py`,
`shadow_vs_live.py` (run with the journal copies; scratch data deleted afterwards).
