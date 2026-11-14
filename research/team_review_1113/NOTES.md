Educational only — not financial advice.

# TEAM-REVIEW 1113 — Primary on TEAM-6, Wed 11-11 .. Fri 11-13 (owner "Team yes", ledger 2026-11-10-team6-primary)

Read-only review: **no config, setup, assignments or ledger change.** Paper trading (Alpaca paper). Three sessions is a
very small sample; one of them (11-12) carries the whole result.

**Data / method.** Live Primary journal origin/mcf-data `journal.db` (238b6537a, EOD 11-13), run_id=1, closed trades,
R after costs = pnl_adj / (|entry − stop| × shares). Dollars: journal `pnl` and `status.json` history `alpaca_day_pl`.
Skips: `signals` table (run_id=1). Cap what-if: run_id=2 (what-if of signals not taken; gross R, simulated exits).
Pre-trial record: the same 6 setups' live trades 10-16..11-10 (18 sessions with trades in the 20-session window) pooled over
every account they ran in (Primary `mcf-data`, Testing 1 `mcf-data-testing`, Testing 2 `mcf-data-testing2`, Live Lab
`mcf-data-livelab`), same R formula. Configurations compared: TEAM-6 live (3 days), TEAM-6 pre-trial record, L3 cap 30/40/50/60
what-if (4) — nothing else tuned.

## Rule-change context (owner rule 2026-11-02)
- **11-11:** TEAM-6 lineup starts (move: NM-ETF Live Lab → Primary; MF2-FD, MF4-FD, MF4, L3-rsi5hi-FD, NS1 out).
  Old loss stops: −2R per-setup latch and −20R account halt on **closed gross R**.
- **From 11-12 (mid-trial):** LR3 (latch and −20R halt on R after costs, halt includes open marks), LR8 (live cost model in
  pnl_adj: stops max($0.02, 4 bps), market exits max($0.01, 1 bp)), LR1 (flatten min(15:55, close − 5 min); no effect on
  full days), LR2 (R after costs on every screen — reporting only). So 11-11 is reported apart from 11-12/13.
- **11-13:** session started late (manual dispatch 09:46) → the first 16 minutes of the gap-down short window were missed;
  hand-over run at ~15:41 (no Primary close-out issue; the Gen/Graveyard close-out failure did not touch Primary).
- Pre-trial window 10-16..11-10 contains earlier moves (L3-fromopen re-promoted to Primary 10-30, NM-ETF in Testing 2 then
  Live Lab, UNI1 top-500 pool in Testing 2 from 11-03) — the pooled record mixes accounts and these periods.

## Totals — TEAM-6 live Primary
| window | trades | R after costs | avg R | win% | journal $ | Alpaca $ (day P/L) |
|---|---|---|---|---|---|---|
| 11-11 (old latch / cost model) | 43 | **−26.63** | −0.619 | 14% | −$670.08 | −$672.98 |
| 11-12 | 75 | **+39.88** | +0.532 | 89% | +$2,843.11 | +$2,838.22 |
| 11-13 (late start) | 13 | **−1.44** | −0.111 | 54% | −$104.65 | −$104.65 |
| 11-12/13 (LR3/LR8 in force) | 88 | +38.44 | +0.437 | 83% | +$2,738.46 | +$2,733.57 |
| **3 days** | **131** | **+11.81** | **+0.090** | 60% | **+$2,068.38** | **+$2,060.59** |

- **One-big-day check:** best day 11-12 = **338% of total R**; without it TEAM-6 is −28.07R / 56 trades = **−0.501R avg**
  (`1 day`). Worst day 11-11 −26.63R. Green days 1/3 (11-13 near flat). The 3-day plus is one L3 burst day.
- Primary equity 81,519.57 (11-10 close) → 83,580.16 (11-13 close).

## Per setup — 3 days (R after costs)
| setup | trades | R | avg R | win% | avg R w/o best day (share) | worst day | 11-11 R (n) | 11-12/13 R (n) | journal $ |
|---|---|---|---|---|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD (Gap-Down Pop Fade, Heavy Selling) | 31 | −6.57 | −0.212 | 45% | −0.641 (best 11-12, total red) | −9.68 (11-11) | −9.68 (14) | +3.11 (17) | −$378 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (Gap-Down Pop Fade) | 30 | −10.54 | −0.351 | 30% | −0.628 (best 11-12, total red) | −14.54 (11-11) | −14.54 (21) | +4.00 (9) | −$254 |
| L3-gap-slope-fromopen-FD (Gap-Down Recovery Fade) | 55 | **+27.45** | +0.499 | 87% | −1.173 (113% `1 day`) | −3.52 (11-11) | −3.52 (3) | +30.97 (52; 0 on 11-13) | +$2,422 |
| ST7-rsi50dn-long-pm-t1s1-FD | 6 | +0.46 | +0.077 | 50% | −0.109 (218% `1 day`) | −1.07 (11-12) | +1.01 (1) | −0.54 (5) | +$29 |
| NS5-sma50-flush-oversold-long | 6 | +0.37 | +0.061 | 50% | +0.028 (70% `1 day`) | +0.11 (11-11) | +0.11 (4) | +0.26 (2) | +$107 |
| NM-ETF-late-dip-di-long | 3 | +0.65 | +0.217 | 67% | +0.213 (67% `1 day`) | +0.21 (11-12) | – (0) | +0.65 (3) | +$142 |

- 11-11 was a gap-down-short wipe: RW3 + RW5 −24.22R on 35 trades (1 + 2 winners), most exits stop / flatten. They are one
  bet taken twice on a bad short day (preval_1110: corr 0.79 on 11-10). 11-12 they recovered +9.52R on 19 (17 winners).
- NM-ETF had no 11-11 signal; ST7 / NS5 / NM-ETF together: 15 trades, +1.48R — small, positive, low-rep.

## Latch / halt events
- **11-11 (old rules):** −2R latch blocked 6 L3-fromopen and 1 RW5 signals (`setup daily loss limit`). RW3 / RW5 still lost
  −9.68 / −14.54R: the old latch counted closed gross R only, and the losses came as simultaneous stops + flatten of lots
  already open. The day closed at −26.63R, past the −20R halt level (the halt stops new entries only; open lots ran on).
- **11-12:** no latch, no halt.
- **11-13 (LR3):** RW3-FD −2R latch in effect by 15:52 (intended; RW3 −2.50R on 5 that day; 4 RW3 skips that day were spread, not latch). No halt.
- LR3 would have tripped RW3 / RW5 earlier on 11-11 (open marks count) — not replayed here; it cannot be scored without a
  1-minute replay.

## L3-fromopen cap (30 open lots) — the owner's 11-13 question
- 11-12: L3 took 52 trades (peak 30 open at once); **648 signals skipped `max positions for this setup`** (135 symbols,
  mostly repeats of the same names) plus 557 `not shortable/ETB`. 11-11 and 11-13 were borrow-bound (29 and 42 ETB skips),
  not cap-bound. **11-12 is the only session in Primary's history where the L3 cap bound** (run_id=2 shows no other day).
- What-if (run_id=2 exits, gross R, one lot per symbol, live lots kept as they were): extra trades / extra gross R over the
  cap-30 baseline (the sim itself re-admits 8 trades / +6.9R at cap 30 because what-if exits differ from live — that is the
  noise floor):

| cap | extra trades vs 30 | extra gross R vs 30 |
|---|---|---|
| 40 | +12 | +7.2 |
| 50 | +26 | +17.5 |
| 60 | +41 | +25.8 |

- Costs (~0.02–0.05R/trade) barely move this. But it is **one green burst day**: on a red L3 day (10-21 −5.42R on 5, 11-02
  −4.03R on 4, 11-11 −3.52R on 3) a bigger cap adds lots on the same wrong-way tape, and L3's record is burst-day driven
  (w/o-best-day share 113% in the trial, 54% pre-trial). With the account at −20R halt and correlated shorts, the cap is the
  only limit on how much one setup can put on in one direction.
- Reading: the data supports a cap (keep one), and does **not** yet support a size change — one observation, all upside.
  **Keep 30**; revisit when L3 has hit the cap on ≥ 3 sessions including a red one (cap-40 option given below).

## Pre-trial record of the same 6, 10-16..11-10 (live, pooled accounts, R after costs)
| setup | trades | R | avg R | win% | w/o best day (share) | worst day | sessions | 3-day trial avg R |
|---|---|---|---|---|---|---|---|---|
| RW3-FD | 112 | +32.51 | +0.290 | 64% | +0.094 (75% `1 day`, 10-22) | −8.83 (11-10) | 17 | −0.212 |
| RW5-FD | 128 | +22.43 | +0.175 | 62% | +0.028 (88% `1 day`, 10-22) | −12.53 (11-10) | 18 | −0.351 |
| L3-fromopen-FD | 252 | +62.10 | +0.246 | 65% | +0.166 (54% `1 day`, 10-20) | −5.75 (10-21) | 16 | +0.499 |
| ST7-FD | 31 | +1.79 | +0.058 | 58% | −0.061 (175% `1 day`, 11-04) | −2.66 (10-21) | 10 | +0.077 |
| NS5 | 23 | −4.64 | −0.202 | 39% | −0.313 (best 10-30, total red) | −2.42 (10-20) | 10 | +0.061 |
| NM-ETF | 18 | +5.88 | +0.327 | 78% | +0.294 (25%, 11-05) | −0.61 (11-04) | 9 | +0.217 |
| **all 6** | 564 | +120.07 | +0.213 | 63% | +0.154 (37%, 10-22) | −15.89 (11-10) | 18 | +0.090 |

- Primary-only slices: L3-fromopen −1.28R / 63 (−0.020; the bulk of its record is Testing 1, 189 trades +63.38R), RW3 +0.304
  (102), RW5 +0.186 (122). NM-ETF from Testing 2 (10) + Live Lab (8).
- The trial (+0.090 avg) is below the record (+0.213) and red without its best day, as the record also leans on burst days
  (10-22 for RW3/RW5, 10-20 for L3). Nothing in three days contradicts the record strongly enough to move a setup:
  RW3 / RW5 lost on one day (11-11) of a kind they already had (11-10); L3 did what its record says (burst-day setup).
- **NS5 is the weak spot on the record** (−0.202 avg over 23, red w/o best day) and was a borderline KEEP in preval_1107
  (long balance); +0.061 in the trial. Watch item, not a move on 6 trades.

## Previous Primary lineup (PV0) — rough data point only
No exposure-lab / Team sim exists for 11-11..11-13, so PV0 is not replayed. The 5 setups that left Primary, live in their
new homes (On Deck / Testing A; different caps, halts and account, 11-11 coverage partial): L3-rsi5hi-FD +12.16R / 40
(+13.18 on 11-12), MF2-FD −5.60 / 5, MF4-FD −6.06 / 12, MF4 −3.13 / 3, NS1 +0.37 / 1 → about −2.3R / 61 together. Not a
like-for-like comparison; it gives no case to bring any of them back.

## Recommendation for Primary from Mon 11-16 (owner decides; DECISION TEAM6-1116)
**Keep TEAM-6 as is, for one more week (11-16 .. 11-20, frozen, review Fri 11-20 after the close). L3-fromopen cap stays 30.**
Reply code: **"TEAM6 keep"**. Alternatives: "TEAM6 keep L3CAP40" (same lineup, L3 cap 30 → 40), "TEAM6 end" (back to rotation
/ the previous process — not recommended).

Why (avg R decides, no over-correction):
1. TEAM-6 is +11.81R / +$2,060 (Alpaca) over 3 days, but only because of 11-12 (338% share; −0.501R w/o it). Three days can
   neither confirm nor reject it; the 20-session record of the same 6 (+0.213, +0.154 w/o best day) is still the best guide.
2. The loss day (11-11) came under the old latch / cost model; 11-12/13 under LR3/LR8 were +38.44R / 88. A clean week under
   the new loss stops is the honest next test.
3. No setup clears a demotion bar on this evidence: RW3 / RW5 are red over 3 days but positive on 17–18 sessions; NS5 is weak
   on the record but the trial is 6 trades. Swapping now would be reacting to one day.
4. L3 cap: one cap-bound day, all upside; a bigger cap is untested on a red burst day → keep 30.

Watch items for 11-20 (no action now): RW3 + RW5 combined day loss on gap-down tape (two setups, one bet); NS5 avg R
(pre-trial −0.202); L3 borrow (11-13: all 42 signals on 4 non-shortable names, 0 trades); 11-16 must start on time (09:30).
