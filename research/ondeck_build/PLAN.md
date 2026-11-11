# On Deck build (ONDECK) — plan, 2026-11-11

*Educational only — not financial advice. Research and plan only: **no config, setup, assignment or ledger change is made
here** (written during market hours). Every change below is applied after the close (≥ 16:05 ET) by a separate step, and only
after the owner's yes. All records are live **paper** results (rule 7); R is after costs (`pnl_adj / (|entry − stop| × shares)`).*

Owner direction 2026-11-11:
- **Accounts renamed; internal keys unchanged:**
  - `testing` = **On Deck**;
  - `testing2` = **Testing A**;
  - `explore1` = **Testing B**;
  - `livelab` = **Testing C**.
  - Primary, Setup Generator and Graveyard are unchanged.
- **Tier flow:** testing areas → On Deck → Primary.
- **On Deck size:** about 2-3× Primary (TEAM-6 = 6 setups, frozen to Fri 11-13), so about 12-18 to start. It must stay small
  enough that every setup gets full exposure.
- **Switch experiments** run only in the testing areas.
- **Promotion = move.** Gen and Graveyard are out of scope.

Basis: `research/rotation_design/PROPOSAL.md` (ROT). Its tiers map onto the new accounts like this:
- its *Reps / Contender* tiers now live in Testing A / B / C;
- its *Candidate / On deck* tiers now live in the On Deck account, as tags (see §1.4).

## The short version (plain English)

1. **Entry rule (OD-IN, "semi-worthy"):** a setup enters On Deck when all of these hold:
   - **≥ 5 traded sessions and ≥ 15 trades;**
   - **shrunk avg R > −0.02** (at least break-even after costs);
   - **avg R without its best day ≥ −0.20** (not a clear loser once the best day is taken out);
   - **last-5-traded-session avg R > −0.30** (not collapsing right now);
   - **2-year backtest ≥ −0.15** (not strongly negative).

   **Exit rule (OD-OUT):** once a setup has had **6 traded sessions in On Deck**, it goes back to a testing area if, **at 2
   re-tiers in a row**, either:
   - its whole record fails OD-IN; or
   - its On Deck segment alone has avg R < 0 *and* avg R without its best day < −0.10.

   Re-tiers happen every 2 sessions after the close.
2. **Today 11 setups qualify** (the target was 12-18). Next in line:
   - **#1** is Panic Flush Reversal (5x volume), which is **one trade short** (14 of 15). Seat 12 is offered to it as an
     owner option.
   - Then: CWT13-z075-short, MF2-FD, L3-rsi5hi-FD and NS4-FD.
3. **Be honest about how "worthy" these are:**
   - Only 6 of the 11 have a positive avg R. The other 5 are at break-even (−0.03 to 0).
   - **All 6 positive records are `1 day` records** (best session ≥ 50% of total R).
   - Only Gap-Down VWAP Loss Short (10% gap) (+0.227R) and RW1-FD (+0.036R) stay positive without their best day.
   - That is why the bar is "semi-worthy" and not "proven": On Deck is for **reps**, not proof.
   - The walk-forward check shows the rule separates setups only modestly. Setups that passed it at 8 past checkpoints averaged
     **−0.034R** per trade over the next 5 sessions, against **−0.107R** for the rest (3,235 vs 20,981 trades). The passers were
     ahead at 5 of 8 checkpoints.
4. **Moves (19 in all, applied after a close):**
   - 7 setups go into On Deck;
   - 10 leave On Deck for Testing B / C;
   - 2 dual-home copies are switched off in On Deck: MF5 and exhaustion_short-FD now run in Testing A only (ROT-A moves 5-6).
   - **Counts after: On Deck 11, Testing A 13, Testing B 25, Testing C 23** (72 setups, each in exactly one account).
   - **Rule 20 (demoted 11-11):**
     - MF4 and NS1 qualify, so they go to On Deck.
     - MF2-FD, MF4-FD and L3-rsi5hi-FD fail OD-IN, so they go to Testing B / C.
     - All five stay in testing accounts and stay protected to about 11-25.
5. **Exposure is not limited by slots or buying power:**
   - Roster peak: **63 concurrent lots of 400 slots** (p90 38).
   - At the peak that is about **$57k of $361k buying power**, about 16%.
   - Per-setup peak: 56 lots (RW7-FD) against a cap of 150.
   - **What did cost exposure** for these 11 setups:
     - borrow (not shortable: 26% of their signals);
     - the **split-tape short gate**, which is on only in Testing 1 / On Deck (9% overall; 12-28% of RW7-FD, L3-lowdist, MF3 and
       ST6 signals);
     - spread checks;
     - twin blocks (MF4 lost 50% of its signals to its twin MF4-FD in Primary).
   - **Tweaks (after the close, owner yes):**
     - **ODX-1:** split-tape short gate **off** in On Deck. It is an on/off switch, so under the owner's rule it belongs in a
       testing area, never in On Deck. Primary runs without it.
     - **ODX-4:** per-setup cap in Testing B / C **10 → 30**. Five busy setups (p90 10-16 open lots) arrive there.
     - Slots, buying power, universe (On Deck is already the full universe, the same as Primary) and the per-setup cap of 150:
       **no change needed.**
6. **Switch field test (SW-A, a proposal):**
   - **Rule:** GAP-U-OFF (longs off on a SPY gap-down below −0.25%, shorts off on a gap-up above +0.25%).
   - **Where:** Testing A, on the 3 setups where GAP-U helped in VALID, FWD *and* live:
     - CWT14-failbrk-pdl-p10-long;
     - CWT14-failbrk-pdl-p10-lowvol-long;
     - exhaustion_short-FD.
   - **Control:** every switched signal is journaled with a what-if simulation, and `shadow.py` runs the same rule in shadow
     everywhere else.
   - **Re-scored after 20 sessions** against a pre-registered pass rule.
   - **Why not Testing C:** its setups are low-rep, GAP-U would take about 28% of their sessions, and the effect would be too
     small to measure.

## Rule / config changes inside the stats window (owner rule 2026-11-02)
Records run 10-06 → 11-10 (26 live sessions, run_id=1, all accounts merged by setup id). Changes in force before or after a date
inside that window (from `research/ledger.jsonl`):
- **All accounts:**
  - per-lot stacking (3 lots per symbol) from 10-13, same-setup re-entry from 10-14;
  - twin cap from 10-20 (twin_group from 10-21).
- **Testing 1 (= On Deck):**
  - split-tape short gate (Testing 1 only, from about 10-14);
  - per-setup −2R stop on 10-19/20, then **off from 10-23** (ST-A);
  - **CF cost filter 0.15R from 10-30** (Testing 1 and 2, later also Explore 1 / Live Lab).
- **Testing 2:**
  - the same CF filter;
  - **UNI1 top-500 universe from 11-04**;
  - NS3V1 twin group from 10-23.
- **Explore 1 / Live Lab:** went live **11-05** (ROLL1: about $1,000 lots, 10 lots per setup, no scale-out, twin block off).
- **Primary:**
  - about $4,000 lots from 10-28;
  - **−2R per-setup latch from 10-29**;
  - TEAM-6 from 11-11 (after the window).
- **Per pick:**
  - NS1 and MF4 (base) have records that are **mostly from Primary**: NS1 23 of 26 trades, MF4 21 of 22, under Primary's
    sizing, plus its latch after 10-29.
  - RW1-FD: Testing 1 to 10-20 (−6.8R), then Testing 2 (+15.8R, top-500 universe from 11-04).
  - Gap-Down VWAP Loss Short (10% gap) and Gap-Down Bounce Rejection Short (10% gap): Testing 2 until 11-04, then Live Lab /
    Explore 1.
  - ST6-FD: Testing 1 to 10-28 (+2.0R), then Live Lab (−2.4R).
  - MF3 and orb20_a: their early trades were in Primary (to 10-19 / 10-09).
- So each record mixes sizing, caps, universes and stop rules. Every move below starts a new record segment (rule 22
  versioning).

---

## 1. On Deck entry and exit rules

### 1.1 The rule chosen: OD-IN = E5 below

| gate | value | why |
|---|---|---|
| experience | **≥ 5 traded sessions and ≥ 15 trades** | Lower than the Candidate minimum (8 / 30), because On Deck is for reps. It is also the pair with the strongest early signal in ROT §2.2: correlation +0.24, permutation p = 0.02. |
| level | **shrunk avg R > −0.02** | "At least break-even after costs". Shrunk = avg R × n / (n + 20). |
| one-big-day | **avg R without best day ≥ −0.20** | Lets in setups whose record leans on one day, but not ones that are clearly negative without it. |
| form | **last-5 avg R > −0.30** | Keeps out records collapsing right now. |
| 2y | **2-year backtest ≥ −0.15** (when there is one) | "Not strongly negative". Most 2y lab lists sit between −0.13 and +0.04. |

- **Capacity: at most 18 setups** (3× Primary). If more qualify, rank by shrunk avg R, then by traded sessions; the rest wait as
  "next in line".
- If fewer than 12 qualify, On Deck simply runs smaller. Seats are not filled with failing setups, except as an explicit owner
  option (§2.2).

**The trade-off, plainly:**
- **A strict rule** (the owner's example, E0) lets in only **2 setups** today. In the walk-forward its passers did best (+0.081R
  next 5 sessions), but over only 493 trades and 9 setups, and only 3 of those 9 were positive afterwards.
- **A loose rule** (E3 / E7) gives 9-14 setups, but the passers did worse (−0.05R).
- **E5** sits between them:
  - it gives the most reps to records that are at least break-even and not collapsing;
  - its walk-forward is close to the best loose rules (−0.034R vs −0.026R for "positive only");
  - it keeps a one-day guard and a form guard, which "positive only" (E6) does not have.

  E6 would admit MF2-FD (−0.557 last 5), L3-rsi5hi-FD (−0.437) and NS4-FD (−0.562). All three are collapsing now, and
  MF2-FD / L3-rsi5hi-FD were just demoted from Primary for that.

### 1.2 Exit rule OD-OUT (back to a testing area)
- **Fair-chance floor:** a setup is not judged until it has **6 traded sessions in On Deck**. It always plays every session
  (no benching in On Deck; ROT §4.4).
- **After the floor, it leaves** when either of these holds **at 2 re-tiers in a row** (re-tier = every 2 sessions after the
  close):
  - (a) its **whole record fails OD-IN**; or
  - (b) its **On Deck segment** has avg R < 0 **and** avg R without its best day < −0.10.
- **Destination:**
  - the testing area it came from;
  - a busy, full-universe record goes to Testing B / C;
  - a top-500-native record goes to Testing A.
- On Deck exits never go straight to the Graveyard. A Graveyard move is proposed only from a testing area (ROT floor), and the
  owner decides.
- Rule-20 setups follow the same rule; they simply cannot leave the testing accounts before their 10 sessions are up.
- **Untested:** the exit rule could not be walk-forward tested on 26 sessions (6 On Deck sessions plus 2 re-tiers would leave
  almost no forward window). Revisit at about 40 sessions.

### 1.3 Configurations tried (8 rule variants, all reported)
**Walk-forward method:**
- 8 checkpoints, after sessions 10, 12, …, 24 (10-19 → 11-06).
- Every non-GEN setup with a live record is included, Primary and Graveyard too, so setups promoted earlier are not lost.
  The 2y value comes from the ROT inventory where known; when it is unknown the 2y gate is passed.
- Forward = the setup's trades over the next 5 sessions, R after costs.
- Script: `ondeck.py` → `walkforward.csv`, `walkforward_summary.csv`.

| rule | gates (sessions / trades, shrunk >, w/o best ≥, share ≤, last-5 >, 2y ≥) | qualify today | setup-dates | next-5 trades | next-5 avg R in | rest avg R | checkpoints ahead | passers positive afterwards |
|---|---|---|---|---|---|---|---|---|
| E0 owner example | 5/15, 0, 0, 60%, –, −0.10 | 2 | 20 | 493 | **+0.081** | −0.101 | 6 of 8 | 3 of 9 |
| E1 positive, loose one-day | 5/15, 0, −0.10, –, –, −0.10 | 5 | 78 | 2,290 | −0.027 | −0.104 | 6 of 8 | 6 of 18 |
| E2 near-even | 5/15, −0.02, −0.10, –, −0.30, −0.10 | 6 | 79 | 2,686 | −0.023 | −0.106 | 6 of 8 | 7 of 21 |
| E3 near-even, wider | 5/15, −0.05, −0.15, –, −0.30, −0.15 | 9 | 106 | 3,876 | −0.053 | −0.105 | 6 of 8 | 10 of 31 |
| E4 E2 + 8 sessions | 8/15, −0.02, −0.10, –, −0.30, −0.10 | 5 | 60 | 2,235 | −0.086 | −0.098 | 5 of 7 | 6 of 18 |
| **E5 (chosen)** | **5/15, −0.02, −0.20, –, −0.30, −0.15** | **11** | 100 | 3,235 | **−0.034** | −0.107 | 5 of 8 | 10 of 26 |
| E6 positive only | 5/15, 0, none, –, –, −0.15 | 10 | 109 | 2,833 | −0.026 | −0.106 | 6 of 8 | 8 of 25 |
| E7 E5 without last-5 | 5/15, −0.02, −0.20, –, –, −0.15 | 14 | 109 | 3,441 | −0.052 | −0.104 | 5 of 8 | 8 of 26 |

**Reading:**
- **Every variant's passers did better than the rest, by about +0.05 to +0.18R per trade.** "Not losing so far" is a weak but
  real ranking signal, as in ROT §2.2.
- **No variant's passers were positive on average afterwards**, except the 2-setup E0.
- So On Deck should be read as "the best reps pool", not as a pool of proven setups. Promotion to Primary still needs the
  higher bar (§1.4).

### 1.4 How the ROT bars fit inside On Deck (tags, no extra account)
- **`CANDIDATE` tag:** ROT balanced Candidate bar (8 / 30, shrunk ≥ +0.03, w/o best day > 0, share ≤ 60%, …).
- **`PRIMARY-READY` tag:** ROT balanced On-deck bar (15 / 60, shrunk ≥ +0.07, w/o best day > +0.03, share ≤ 50%, day-t ≥ 0.5m,
  …), **plus** a Primary-rules Team replay over the last 10 traded sessions that is greater than 0, **plus** the owner's yes.
- **Today:**
  - 0 setups reach balanced Candidate. Under the lenient Candidate bar, RW1-FD and Gap-Down VWAP Loss Short (10% gap) would
    (both are in the roster).
  - 0 reach `PRIMARY-READY`.

## 2. Applied to today's records (journals through 11-10, run_id=1)

### 2.1 On Deck roster: 11 qualify
How to read the table:
- **Peak p90** = 90th-percentile concurrent open lots per session (all accounts merged).
- **One-big-day column** = avg R without the best session, with that session's share of total R; **1 day** = 50% or more.
  "neg" = total R < 0, so a share is not defined.

| # | setup | id | from → to | side | traded sessions / trades | avg R | shrunk | **w/o best day (share)** | best day | last-5 | ex-mkt | 2y | Primary-rules R | entries / session | peak p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Gap-Down VWAP Loss Short (10% gap) | `CWT09-gapdn-vwaploss-g10-short` | Testing C → On Deck | short | 8 / 15 | +0.327 | +0.140 | **+0.227 (54%, 1 day)** | 10-30 +2.63 of +4.90R | +0.390 | +0.272 | +0.040 | +0.327 | 0.68 | 2.9 |
| 2 | Gap-Down Bounce Short, Heavy Selling (all day) | `RW1-gapdn-bounce-flowsell-short-FD` | Testing A → On Deck | short | 21 / 116 | +0.078 | +0.066 | **+0.036 (59%, 1 day)** | 10-22 +5.37 of +9.03R | +0.193 | −0.086 | −0.047 | +0.084 | 5.27 | 7.0 |
| 3 | Gap-Down Recovery Fade, Low Distance (all day) | `L3-gap-slope-lowdist-FD` | stays in On Deck | short | 15 / 73 | +0.077 | +0.060 | −0.060 (166%, **1 day**) | 10-20 +9.34 of +5.62R | +0.108 | −0.096 | −0.127 | +0.077 | 3.32 | 8.2 |
| 4 | Gap-Down Bounce Rejection Short (10% gap) | `CWT09-gapdn-bounce-g10-lowerhalf-short` | Testing B → On Deck | short | 7 / 19 | +0.087 | +0.043 | −0.158 (243%, **1 day**) | 10-30 +4.02 of +1.66R | +0.163 | −0.106 | +0.141 | +0.087 | 0.86 | 4.8 |
| 5 | Big Gainer Dip-and-Pop ex-P, **rule 20** | `NS1-rsidip-rsi5pop-long` | Testing A → On Deck | long | 11 / 26 | +0.049 | +0.028 | −0.087 (237%, **1 day**) | 10-09 +3.02 of +1.27R | −0.067 | +0.060 | +0.028 | +0.049 | 1.04 | 3.0 |
| 6 | Early Sellers, Strong Heat ex-P, **rule 20** | `MF4-h40-open-flowsell` | Testing A → On Deck | short | 7 / 22 | +0.052 | +0.027 | −0.029 (148%, **1 day**) | 10-14 +1.69 of +1.14R | +0.258 | +0.061 | −0.099 | +0.052 | 0.88 | 3.8 |
| 7 | Afternoon Higher-Low Long (near-miss) | `NM-HL-T75-pm-long` | Testing A → On Deck | long | 10 / 52 | −0.002 | −0.002 | −0.071 (neg) | 11-05 +3.12R | −0.069 | +0.072 | +0.044 | **+0.230** | 3.06 | 8.3 |
| 8 | Gap-Down Early Bounce Short (all day) | `RW7-gapdn-bounce-early-short-FD` | stays in On Deck | short | 20 / 493 | −0.004 | −0.004 | −0.036 (neg) | 11-05 +14.27R | −0.003 | −0.089 | −0.060 | −0.012 | 22.41 | 29.0 |
| 9 | Early Sellers into a Pop ex-P | `MF3-open-flowsell-rsi5hi` | stays in On Deck | short | 10 / 44 | −0.015 | −0.011 | −0.116 (neg) | 11-03 +3.39R | −0.051 | −0.038 | −0.034 | −0.015 | 1.76 | 6.3 |
| 10 | Volume-Spike-Up Short, Midday (all day) | `ST6-volspikeup-short-mid-t1s1-FD` | Testing C → On Deck | short | 6 / 15 | −0.029 | −0.012 | −0.112 (neg) | 10-13 +1.02R | −0.112 | −0.172 | – | −0.029 | 0.68 | 4.5 |
| 11 | 20-Minute Opening Range Breakout | `orb20_a` | stays in On Deck | both | 18 / 40 | −0.029 | −0.019 | −0.172 (neg) | 10-22 +4.69R | +0.222 | +0.019 | −0.040 | −0.029 | 1.50 | 3.6 |

*Display names: the dashboard names where set. `L3-gap-slope-lowdist-FD`, `ST6-volspikeup-short-mid-t1s1-FD`,
`NS1-rsidip-rsi5pop-long-FD`, `NS4-pm-vwap-reclaim-oversold-short-FD` and `exhaustion_short-FD` have no dashboard name yet; the
plain names given for them in this plan are descriptive only.*

**One-big-day check (CLAUDE.md 10-25), called out:**
- **All 6 positive records are carried by one day:**
  - Gap-Down VWAP Loss Short (10% gap) 54% (10-30);
  - RW1-FD 59% (10-22);
  - L3-lowdist 166% (10-20);
  - CWT09-bounce-g10 243% (10-30);
  - NS1 237% (10-09);
  - MF4 148% (10-14).
- Only the first two stay positive without their best day.
- RW7-FD's 11-05 (+14.27R) is larger than its whole record (−1.85R) in absolute terms. Its 493 trades are worth about 102
  independent ones (ROT §2.1, design effect 4.8).

**Side and family mix:**
- 8 short / 2 long / 1 both.
- Five are gap-down shorts: RW1-FD, RW7-FD, the two CWT09 g10s and L3-lowdist. That is the same family risk ROT §7 flagged.
- There is no long close to the bar: the nearest long is #1 in line.

### 2.2 Next in line (closest to OD-IN first)
| # | setup | id | now → after | traded sessions / trades | shrunk | w/o best day (share) | last-5 | 2y | fails on |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Panic Flush Reversal (5x volume) | `CWT05-flush-m05-v5-long` | Testing B (stays) | 8 / 14 | +0.002 | −0.139 (1 day) | +0.153 | −0.111 | **1 trade short** (14 / 15) |
| 2 | Stretched Above VWAP Fade (far) | `CWT13-vwapstretch-z075-short` | Testing A (stays) | 7 / 25 | −0.023 | −0.198 | +0.031 | −0.081 | shrunk −0.023 vs > −0.02 |
| 3 | Early Sellers, Mid-High RSI (all day) ex-P, rule 20 | `MF2-open-rsimidhi-flowsell-FD` | On Deck → Testing C | 20 / 134 | +0.048 | −0.197 (396%, 1 day) | **−0.557** | −0.088 | last-5 |
| 4 | Gap-Down Rebound Overbought Short (all day) ex-P, rule 20 | `L3-gap-slope-rsi5hi-FD` | On Deck → Testing B | 18 / 98 | +0.027 | −0.061 (254%, 1 day) | **−0.437** | −0.040 | last-5 |
| 5 | Afternoon VWAP Reclaim Fade (all day) | `NS4-pm-vwap-reclaim-oversold-short-FD` | On Deck → Testing B | 14 / 33 | +0.026 | −0.115 (332%, 1 day) | **−0.562** | −0.119 | last-5 |
| 6 | RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day) | `ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD` | Testing B (stays) | 5 / 9 | +0.041 | −0.182 (1 day) | +0.133 | – | trades 9 / 15 |
| 7 | Early Sellers into a Pop (index down, no gap up) | `NM-MF3-qqqdn-gapdn-FD` | Testing A (stays) | 6 / 34 | +0.062 | **−0.524** (351%, 1 day) | −0.524 | −0.010 | one-day, last-5 |

- **Owner option OD-FILL:** start On Deck at 12 by seating #1 now. It is one trade short and a long, so it would help the side
  mix.
- Without OD-FILL, #1 enters automatically at the first re-tier at which it has 15 trades.

### 2.3 Move list (exact; applied after a close, effective the next session after the owner's yes)
**A. Into On Deck (7):**

| setup | id | from → to | note |
|---|---|---|---|
| Gap-Down VWAP Loss Short (10% gap) | `CWT09-gapdn-vwaploss-g10-short` | Testing C → On Deck | its twin `NM1-cwt09-g10-vwaploss-short` stays in Testing B (different accounts) |
| Gap-Down Bounce Short, Heavy Selling (all day) | `RW1-gapdn-bounce-flowsell-short-FD` | Testing A → On Deck | leaves the top-500 universe for the full one (new segment) |
| Gap-Down Bounce Rejection Short (10% gap) | `CWT09-gapdn-bounce-g10-lowerhalf-short` | Testing B → On Deck | |
| Big Gainer Dip-and-Pop | `NS1-rsidip-rsi5pop-long` | Testing A → On Deck | **rule 20, protected to about 11-25.** Its twin NS1-FD goes to Testing B. |
| Early Sellers, Strong Heat | `MF4-h40-open-flowsell` | Testing A → On Deck | **rule 20, protected to about 11-25.** Its twin MF4-FD goes to Testing B. |
| Afternoon Higher-Low Long (near-miss) | `NM-HL-T75-pm-long` | Testing A → On Deck | |
| Volume-Spike-Up Short, Midday (all day) | `ST6-volspikeup-short-mid-t1s1-FD` | Testing C → On Deck | |

**Stay in On Deck (4):** `L3-gap-slope-lowdist-FD`, `RW7-gapdn-bounce-early-short-FD`, `MF3-open-flowsell-rsi5hi`,
`orb20_a`.

**B. Out of On Deck, fail OD-IN (10).** Busy, full-universe records go to Testing B / C, not to Testing A (top-500), so they
keep their universe:

| setup | id | from → to | why it fails |
|---|---|---|---|
| Gap-Down Rebound Overbought Short (all day) ex-P | `L3-gap-slope-rsi5hi-FD` | On Deck → **Testing B** | last-5 −0.437. **Rule 20:** stays in a testing account. |
| Early Sellers, Strong Heat (all day) ex-P | `MF4-h40-open-flowsell-FD` | On Deck → **Testing B** | shrunk −0.205. **Rule 20.** |
| Early Sellers, Mid-High RSI (all day) ex-P | `MF2-open-rsimidhi-flowsell-FD` | On Deck → **Testing C** | last-5 −0.557. **Rule 20.** |
| Big Gainer Dip-and-Pop (all day) | `NS1-rsidip-rsi5pop-long-FD` | On Deck → Testing B | shrunk −0.061 |
| Afternoon VWAP Reclaim Fade (all day) | `NS4-pm-vwap-reclaim-oversold-short-FD` | On Deck → Testing B | last-5 −0.562 |
| Panic Flush Reversal (3x volume) | `CWT05-flush-m05-v3-long` | On Deck → Testing B | shrunk −0.096 |
| Early Sellers Above VWAP ex-P | `MF1-945-flowsell-vwapup` | On Deck → Testing C | shrunk −0.216 |
| Big Loser VWAP Reclaim Fade | `NS3-failed-vwap-reclaim-short` | On Deck → Testing C | shrunk −0.176 (ROT-GY proposal) |
| Afternoon Blow-off Short | `exhaustion_short` | On Deck → Testing C | shrunk −0.074; its -FD twin is in Testing A |
| Index Last-Half-Hour Momentum | `intraday_momentum` | On Deck → Testing C | shrunk −0.254 (ROT-GY proposal) |

**C. Dual-home fixes (ROT-A moves 5-6): switch off in On Deck, keep Testing A only (2):**
- `MF5-flowsell-vwapup-rsi5hi` (Sellers into Strength, all day);
- `exhaustion_short-FD`.

**Rule 20 flag:**
- MF2-FD, MF4-FD and L3-rsi5hi-FD were moved Primary → Testing 1 on 11-11, so this would move them a second time within two
  sessions (a second new segment).
- **Owner option OD-P20:** keep these three in On Deck until their protection ends (about 11-25), then apply OD-OUT. That makes
  On Deck 14 until then.
- The recommendation is to apply the rule now: On Deck's seats are for setups at least at break-even, and all three are
  collapsing (last-5 −0.44 to −0.56).

**ROT-A moves 1-4 are superseded:**
- They were graduations from Explore 1 / Live Lab to Testing 1 / 2: CWT13-z075-long, ST8-FD, CWT12-flag and CWT05-m075-v3.
- With On Deck as the next step and Testing A / B / C as equal testing areas, those moves only reset segments, so the four stay
  where they are.
- The per-setup cap lift (ODX-4) removes the 10-lot reason for moving them.

### 2.4 Testing A / B / C after the moves

| account | setups | long / short / both (+ index-gated, no trades yet) | live entries per session (sum of current rates) | sum of per-setup p90 open lots | slots / per-setup cap |
|---|---|---|---|---|---|
| **On Deck** (`testing`) | **11** | 2 / 8 / 1 | 41.5 | 81 (real book peak 63) | 400 / 150 |
| **Testing A** (`testing2`) | **13** | 5 / 8 / 0 | 127.6 | 167 | 400 / 50 |
| **Testing B** (`explore1`) | **25** | 10 / 12 / 0 (+3 IDX) | 27.4 | 74 | 200 / 10 → **30** (ODX-4) |
| **Testing C** (`livelab`) | **23** | 8 / 12 / 1 (+2 IDX) | 20.9 | 75 | 200 / 10 → **30** (ODX-4) |

**Balancing rules used:**
1. **Twins and families are split across accounts:**
   - exhaustion_short (C) / -FD (A); MF2 (B) / MF2-FD (C); MF4 (On Deck) / MF4-FD (B); NS1 (On Deck) / NS1-FD (B);
     NS4 (A) / NS4-FD (B);
   - the LD twin groups stay split B / C, and so do the CWT04 a15 / a25 pairs and IDX1 hold / trail;
   - Early Sellers are spread 2 / 2 across B / C (MF2 base + MF4-FD in B; MF2-FD + MF1 in C), plus MF5 and NM-MF3 in A.
2. **Busy setups** (p90 ≥ 10 open lots) go only where the per-setup cap allows them: A, or B / C after ODX-4.
3. **Full-universe records stay full-universe** (B / C). Testing A keeps its top-500-native setups.
4. **Priority = fewest traded sessions first:** `setup_order` in every account is re-sorted ascending by traded sessions (ROT
   §4.3).
   - The On Deck order would be: ST6-FD (6), MF4 (7), CWT09-bounce-g10 (7), CWT09-vwaploss-g10 (8), NM-HL (10), MF3 (10),
     NS1 (11), L3-lowdist (15), orb20_a (18), RW7-FD (20), RW1-FD (21).

**Exposure for the low-rep pool:**
- B / C carry 0.2-0.7 entries per session per low-rep setup, and 0% of their signals were lost to slots or caps.
- What they gain is not slots: it is fewer same-symbol rivals once On Deck takes the busier setups.
- The added busy ex-Testing-1 setups bring about 20 entries per session to each of B / C. That is far inside 200 slots at about
  $1,000 lots ($200k of buying power).

**Pending owner decisions that would change the counts:**
- **ROT-GY** (5 Graveyard proposals: RW3S-FD, CWT13-z05-long and NM-AR-AM in A; NS3 and intraday_momentum now going to C).
  If all are yes: A 10 / C 21.
- MF4-FD meets the Graveyard floor, but is protected to about 11-25.

Files:
- `moves.csv` (19 moves);
- `layout.csv` (all 72 setups by account);
- `candidates.csv` (all 72 with every gate);
- `roster.csv`.

## 3. Exposure check for On Deck (`exposure.py` → `exposure_out.json`, `setup_peaks.csv`)

**Method:**
- Lots open at the same time are computed from the 11 roster setups' live fills, merged across accounts, as if they had all
  run in one account.
- This counts **fills only**, so the skip table below shows what was lost before entry.

**Concurrent positions vs slots and caps:**
- Roster book: **peak 63 concurrent lots** (11-10); p90 38; median 22.
- Entries: median 34 per session, max 80.
- **Slots 400**, so the peak uses 16%.
- **Per-setup cap 150:** the largest per-setup peak is RW7-FD at 56 (p90 29). Next are NM-HL at 20, and L3-lowdist and RW1-FD
  at 12.
- No setup comes near its cap. In the 26 sessions, **0% of roster signals were skipped for slots or setup caps.**

**Buying power** (status.json 11-10):
- On Deck equity **$94,993** × 3.8 = **$360,974**, so the lot is about **$902**.
- At the 63-lot peak that is about **$56.8k (16%)**. Even 3× the peak would fit.
- (Primary for comparison: $81,526 × 3.2 / 77, so about $3,390 lots. R is size-independent, so On Deck R is comparable.)

**Twin / family crowding and one position per symbol:**
- `max_lots_per_symbol` = 3, same side only; `block_twin_same_symbol` = true in On Deck.
- **No two roster setups are twins.** Each twin sits in a testing area.
- **Same-symbol overlaps** among roster setups: 98 in 26 sessions, all but 1 on the same side, so stacking allowed them (no
  signal lost). The pairs:
  - RW1-FD + RW7-FD, 74 times. They are correlated gap-down shorts: watch the combined exposure, not the slots.
  - CWT09-bounce + CWT09-vwaploss, 10 times.
  - MF3 + MF4, 3 times.
- **MF4 lost 50% of its signals to "twin held"** (MF4-FD held the symbol in Primary). With MF4-FD in Testing B, that block goes
  away.
- MF3 lost 31% to crowding (MF3-FD and MF5, which are now in the Graveyard and Testing A respectively). That should recover.

**Where the roster's signals went** (2,536 signals, all accounts):

| outcome | share |
|---|---|
| entered | 36% |
| not shortable / ETB | 26% (CWT09 g10 pair 84-88%: borrow on 10%+ gappers; no config fixes it) |
| split-tape short gate | 9% (L3-lowdist 13%, MF3 23%, RW7-FD 12%, ST6-FD 28%) |
| spread checks | 9% |
| −2R setup latch (old Testing / Primary periods) | 4.5% |
| twin held / same symbol / opposite side / lot cap | 8% |
| cost filter (CF) | 3.6% (RW1-FD 6.8%, RW7-FD 5.9%, orb20_a 5.8%) |
| slots / caps | **0%** |

**On Deck settings for maximum exposure (config changes, after the close, owner yes):**
- **ODX-1: `live.split_tape_short_gate.enabled: false` in `config/account_testing.yaml`.**
  - It is a market on/off switch for shorts, and the owner's rule keeps switch experiments out of On Deck.
  - Primary already runs without it.
  - It gives back 12-28% of the signals of 4 roster shorts. (The gate stays available for a testing-area switch test.)
- **ODX-2 (option, not recommended now): CF cost filter off in On Deck** to match Primary.
  - It would give back 3-7% of signals for RW1-FD, RW7-FD and orb20_a.
  - It is kept because the CF forward test runs across all testing accounts, so On Deck records stay comparable with the pool.
- **ODX-3: no change** to slots (400), buying power multiple (3.8), the per-setup cap (150) or the universe (On Deck =
  Testing 1 = full universe, the same as Primary). The −2R per-setup latch stays **off** (ST-A), so reps are not cut; the nightly
  Primary-rules proxy shows its effect.
- **ODX-4: `account.max_positions_per_strategy: 10 → 30` in Testing B and Testing C** (`account_explore1.yaml`,
  `account_livelab.yaml`).
  - MF2-FD (p90 16, max 27), NS3 (12.5), exhaustion_short (12.4), L3-rsi5hi-FD (12) and MF4-FD (9.9) arrive there.
  - 30 = Primary's per-setup sleeve. Low-rep setups are unaffected: none reaches 10 today.
  - B / C keep their other ROLL1 settings: no scale-out, twin block off. These differ from the old Testing 1 conditions of the
    arriving setups (new segment, noted).
- **Benching:** none needed. The ROT triggers (85% of slots, or 25% of signals lost to a sibling) do not fire for the roster
  after MF4-FD leaves.

## 4. Switch field test (proposal SW-A; testing areas only)

**Choice of area and switch:**
- **Testing A** with **GAP-U-OFF**:
  - longs off when SPY opens more than 0.25% *below* the prior close;
  - shorts off when it opens more than 0.25% *above*;
  - decided at the open and sticky for the day.
- Applied only to the 3 Testing A setups where GAP-U helped in **all of VALID, FWD and live** (`research/regime_switch/
  per_setup.csv.gz`, ΔR VALID / FWD / live):
  - `CWT14-failbrk-pdl-p10-long`: +149.8 / +60.6 / +23.3R;
  - `CWT14-failbrk-pdl-p10-lowvol-long`: +202.8 / +30.6 / +7.4R;
  - `exhaustion_short-FD`: +330.9 / +20.9 / +7.9R.
- **Why this is targeted (Remedies rule):**
  - These are the losing lists where the REGSW study found GAP-U's gains. Its "next step 3" asks for exactly this restriction.
  - It leaves out the setups GAP-U hurt in VALID: NM-AR −61R, NS3V1 −8R (and NS1 / RW1-FD, now in On Deck).
  - It leaves out the owner's PDL-1a R2A observation legs, which are already regime-gated.
- **Sample:** the 3 setups make about 44 entries per session. GAP-U switches about 28% of setup-sessions, so expect roughly 12
  switched entries per session, or about 250 in 20 sessions. That is enough to measure.

**Control (so the effect can be measured):**
1. **Journal shadow of every switched signal:**
   - The runner journals it with status `switched (GAP-U)` and a what-if simulation of the trade, as the split-tape gate does
     today.
   - Field effect = −Σ what-if R of the switched trades. Knock-on effects (freed symbols and slots taken by other setups) show
     up as the difference between the account's actual R and the "actual + what-if" book.
2. **Same-rule shadow elsewhere:**
   - `research/regime_switch/shadow.py` keeps scoring GAP-U, IDX3-P and SPYO-P nightly on every account's trades. That is the
     unswitched reference, and it checks that the field result matches the shadow prediction for the same 3 setups.
3. **Random-switch baseline:** the same fraction of setup-sessions switched on random days (permutation, 2,000 draws), as in
   REGSW.

**Pre-registered pass after 20 forward sessions** (new pre-registration, counted in the REGSW lineage):
- ΔR > 0 in total;
- switched avg R < kept avg R in at least 2 of the 3 setups;
- the total beats the random-switch 95th percentile;
- **per-setup report** (how many improve, how many get worse and by how much).

If it passes, the next step is a DECISION (wider list, or Testing B / C). If it fails, the switch goes off.

**Switched sessions:**
- They are logged per side as `switched` and excluded from per-session stats, like benched sessions.
- They do not count as traded sessions, so OD-IN / OD-OUT are not distorted.

**Not chosen:**
- **IDX3-P / SPYO-P:** they switch only 5-7% of trades. In Testing A only CWT13-z075-short, NM-AR-AM and NS3V1 have fits.
  The effect over 20 sessions would be about 1-3R, which cannot be measured. They stay in shadow.
- **Testing C (the owner's example):** it holds low-rep setups, mostly with no fitted fingerprint. GAP-U would remove about 28%
  of their sessions, which goes against the playing-time rule, for an effect too small to read.

**Needs:**
- Runner support for a per-account `live.regime_switch` block (rule, threshold, setup list, mode off / half, what-if journaling)
  with tests;
- a `research/backlog.jsonl` entry (setup / strategy idea, rules 15-17);
- a ledger entry on approval;
- applied outside 09:30-16:00 only (setup-freeze).

It is a proposal only.

## 5. Ledger, assignments, tests and labels

**Ledger entries** (`research/ledger.jsonl`, then `python -m mcf.research.ledger check`):
1. `2026-11-11-account-labels`:
   - display labels only: testing → On Deck, testing2 → Testing A, explore1 → Testing B, livelab → Testing C;
   - keys, order prefixes (e.g. `mx1-`, `mll-`) and data branches are unchanged;
   - effective from the first session after the change.
2. `2026-11-1x-ondeck-build`:
   - owner yes; the 19 moves in `moves.csv`, with a patch per setup `enabled` and every `setup_order`;
   - the OD-IN / OD-OUT rule text, plus OD-FILL / OD-P20 if chosen;
   - evidence = this folder; metrics at approval = `candidates.csv`;
   - `former_primary` markers unchanged; rule-20 protection dates kept (MF2-FD, MF4-FD, L3-rsi5hi-FD, MF4, NS1 to about 11-25).
3. `2026-11-1x-ondeck-exposure`:
   - ODX-1: split-tape gate off in On Deck;
   - ODX-4: per-setup cap 10 → 30 in Testing B / C (and ODX-2 if chosen).
4. Later, only after pre-registration, code, tests and an owner yes: `2026-11-xx-swa-gapu-testingA` (SW-A), plus its backlog
   entry.
5. If ROT-B-style pre-approval is wanted for OD-IN / OD-OUT moves: one "rule" entry. Each later move still gets its own ledger
   line and an assignments regeneration in the same commit.

**Assignments:**
- `python -m mcf.report.assignments` in the same commit as the config change (CLAUDE.md 10-20), so the dashboard shows the new
  homes and timestamps.
- The dual-home fix removes the two setups that are in two accounts today (MF5, exhaustion_short-FD), so "one account per
  setup" holds.

**Tests likely affected** (update in the same PR, after the close):
- `tests/test_assignments.py`: the file must match the configs; no setup may run in two accounts.
- `tests/test_lowrep_1104.py`:
  - the hard-coded `EXPLORE1` / `LIVELAB` sets: −CWT09-bounce-g10 / +5 for Explore 1; −CWT09-vwaploss-g10, −ST6-FD / +5 for
    Live Lab;
  - `test_twins_split_across_the_two_accounts` asserts NM1-cwt09 and CWT09-vwaploss-g10 are split between Explore 1 and Live
    Lab. Change it to "never in the same account";
  - the label strings "Explore 1" / "Live Lab" in `test_new_account_setups_eligible_for_top2_and_leaderboard`;
  - `test_moves_are_moves` (setups moved into On Deck must leave the 11-04 sets).
- `tests/test_new_accounts_1103.py`:
  - labels in `NEW` ("Live Lab", "Explore 1") and the dashboard strings;
  - `max_positions_per_strategy == 10` (ODX-4).
- `tests/test_split_tape_gate.py`: lines 66-67 assert the gate is enabled for `testing` (ODX-1).
- `tests/test_exposure_1109.py`: its home map (RW1-FD, NS1, MF4, L3-rsi5hi-FD, MF2-FD, CWT09-vwaploss-g10…).
- **Label strings** in `test_testing2.py`, `test_pdl1a.py`, `test_daily_post*.py`, `test_dashboard_inventory.py`,
  `test_inactive_check.py`, `test_lab_context.py`, `test_live_scale_out.py`, `test_lots.py`, `test_graveyard_account.py`,
  `test_twin_and_setup_loss.py`, `test_universe_top_n.py`, `test_playing_time.py`. Each holds "Testing 1/2", "Explore 1" or
  "Live Lab" text; check each.
- `test_gen_*`: Gen is out of scope. They are expected to be unaffected unless they assert the shared label dict. Run them
  anyway.

**Label changes** (report and dashboard side; the runner keys nothing on labels). *Update: the display rename landed on this branch while this plan was being written (commit ac1ad3624, merged here). Check the list below against that commit; only the items it missed are still open, plus ledger entry 1 if it has none.*
- **Report code:**
  - `mcf/report/assignments.py` (`ACCOUNTS` and the livelab / explore1 loop);
  - `mcf/report/daily_post.py` (`ACCOUNTS` list and the account-name map near line 309);
  - `mcf/report/team.py` (`ACCOUNT_TAG`);
  - `mcf/report/playing_time.py` (about line 394);
  - `mcf/research/allocate.py` (`LABEL`).
- **Dashboard:** `docs/live/index.html` (all-accounts cards, account switch, `?account=` links) and `docs/live/report.html`.
- **Comments:** `config/account_*.yaml` header comments, and comments in `mcf/execution/runner.py`, `session_guard.py` and
  `outage.py`.
- **Daily post (owner choice):**
  - Explore 1 / Live Lab account totals are kept out of the daily post today (CLAUDE.md 11-03). Under that rule, Testing B / C
    totals would stay out too, even though they now hold ex-Testing-1 setups.
  - On Deck replaces Testing 1 in the post.

**CLAUDE.md lines that need the owner's wording** (not changed here):
- "Testing 1 = Testing 2" (10-23): On Deck and Testing A are now different tiers.
- "Trimmed setups / low-rep … rotate through Explore 1 / Live Lab" (11-03/04): Gap-Down VWAP Loss Short (10% gap), ST6-FD and
  CWT09-bounce-g10 have fewer than 20 trades but go to On Deck under the new "semi-worthy → On Deck" direction.

## 6. Owner reply codes
- **"ONDECK yes"**:
  - the OD-IN / OD-OUT rules;
  - the 19 moves (§2.3), with re-tiers every 2 sessions after the close.
- **"OD-FILL yes"**: seat Panic Flush Reversal (5x volume) now (On Deck 12).
- **"OD-P20 yes"**: keep MF2-FD, MF4-FD and L3-rsi5hi-FD in On Deck until about 11-25 (On Deck 14 until then).
- **"ODX yes"**: ODX-1 (split-tape gate off in On Deck) and ODX-4 (Testing B / C per-setup cap 30). Add **"ODX-2 yes"** for CF
  off in On Deck.
- **"SW-A yes"**: pre-register and build the GAP-U field test in Testing A (code, tests, backlog, ledger; switched on only after
  the close, once tests pass).

## Files
| file | contents |
|---|---|
| `ondeck.py` | rule variants, today's gates for all 72 setups, walk-forward → `candidates.csv`, `walkforward.csv`, `walkforward_summary.csv`, `dates.json` |
| `exposure.py` | roster concurrency, per-setup peaks, overlaps, skip reasons → `exposure_out.json`, `setup_peaks.csv` |
| `layout.py` | accounts after the moves → `moves.csv`, `layout.csv` |
| `roster.csv` | the 11 OD-IN setups |

**Inputs:**
- the 7 accounts' journals and status from the 11-10 nightly (read-only copies);
- `research/rotation_design/inventory.csv` (2y, ex-market, Primary-rules, playing time);
- `research/regime_switch/per_setup.csv.gz`;
- `docs/live/assignments.json` (TEAM-6 state).

Run order: `python ondeck.py <scratch>`; `roster.csv` (E5 passers); `python exposure.py <scratch>`; `python layout.py`.

*Paper results. Educational only — not financial advice.*
