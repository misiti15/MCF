# Diagnosis: Monday Weak-RS NS3 Short (near-miss) `NM-RWN5-ns3-mon-weakrs-short` (Testing D; SHORT)
Mechanic, 2026-11-16 (Workbench batch). Educational only — not financial advice.

**Very few live trades: 8 closed in 3 sessions (Mondays 10-19, 11-02, 11-16; the brief counted 7 — IONS closed in Testing D
today). With fewer than 10 trades there is no "5 worst + 5 best": all 8 are charted (worst4 + best4 = every trade), and only
one of them lost. The diagnosis therefore rests on the 2-year backtest (248 parent trades on 58 Mondays) and says so.**

Engine view: `NM-RWN5-ns3-mon-weakrs-short_engine.png` (P1-P29). Trade teardowns: `..._worst1_LITE_2026-10-19.png`,
`..._worst2_ARM_...`, `..._worst3_CIFR_...`, `..._worst4_CRCL_...`, `..._best1_IONS_2026-11-16.png`, `..._best2_FCEL_...`,
`..._best3_HPE_...`, `..._best4_COHR_...`. Threshold curve for the new sensor: `..._wb1_volratio_curve.png`.

## The machine (parts that bind)
Short a stock that is > 2% below its open (P11), weaker than SPY from the open (P13), above its 5-minute SMA50 (P10), on the
5-minute bar whose close crosses back ABOVE VWAP (P9: the "reclaim" that is expected to fail), Mondays only (P12), bar close
09:50-11:30 (P6/P14), adv20 >= $95M (P2). Exit t1s1: 1R = 0.25 x daily ATR (P23), stop and target 1R either side of the signal
close (P26/P27), flat 15:55 (P29). Testing D cost filter 0.15R (P20). First qualifying bar per symbol-day (P8).

## Rule changes inside the live window (10-19..11-16; ledger effective dates)
10-23 ST-A per-setup daily stop off (testing accounts); 10-29 cost filter CF 0.15R on testing accounts (the 10-19 trades ran
without it — all 5 would have passed it); 11-05 move Testing 2 -> Explore 1 (ROLL1); 11-12 move Explore 1 -> Testing D, LR1
flatten at min(15:55, close - 5 min), LR5 position check; 11-16 Testing D max_positions_per_strategy 30 -> 50 (ROT1). None of
these changes the entry rules; the replay applies today's rules (CF on) to every session.

## Every live trade (what happened -> which part -> what a tweak would have done)
| Trade | R | What happened | Part responsible | Tweak effect on THIS trade |
|---|---|---|---|---|
| LITE 10-19 10:20 (the only loser) | −1.11 stop | $852 name; the reclaim held VWAP and the rising SMA20, chopped 10:25-11:10, then ran to the stop at 11:31 (MFE +0.19R) | P9/P10 sensors on a high-priced, still-strong name; P26 stop | WB1/WB2/WB3 all KEEP it (reclaim volume 0.65x, 10:20). A price cap <= $300 would skip it (tested: passes, but weaker than WB3) |
| ARM 10-19 11:05 | +0.53 flatten | faded slowly, flattened 15:55 short of target (MFE +0.84R) | P29 time exit | WB1/WB3 SKIP it (reclaim volume 0.39x) — a winner lost |
| CIFR 10-19 10:00 | +0.72 target | fast fade after the reclaim | — | WB2/WB3 SKIP it (before 10:05); the replay's WB2 takes CIFR at 10:15 instead (+1.21R) |
| CRCL 10-19 11:05 | +0.77 target | clean fade | — | WB1/WB3 SKIP it (volume 0.42x) |
| COHR 10-19 10:20 | +0.78 flatten | faded to +0.96R MFE, flattened | P27 target just out of reach | kept by all copies |
| HPE 11-02 10:10 | +0.80 target | clean fade | — | kept by all copies |
| FCEL 11-02 10:10 | +0.87 target | clean fade | — | WB1/WB3 SKIP it (volume 0.39x) |
| IONS 11-16 11:05 | +0.99 target | clean fade (SPY −0.30% since 09:50) | — | WB1/WB3 SKIP it (volume 0.36x); the SPY-since-09:50 gate would also skip it |

**Live evidence disagrees with WB1/WB3:** WB3 keeps 3 of the 8 live trades (+0.16R avg, incl. the LITE loss) and skips 5
(+0.78R avg, all winners). Eight trades are far too few to decide on, and the pass rule does not use the parent's live record,
but the supervisor must see it: on the live sample the low-volume reclaims were the winners.

## All trades (2-year backtest, 248 parent trades on 58 Mondays, costs in; code/ana_out.txt)
- **One big day:** 2025-04-14 (25 trades, +24.1R) is 48% of the 2-year total R (`1 day` tag); avg R w/o it +0.117 (with it
  +0.202). Over 2025-03..04 the setup made 33R of its 50R. The replay (21 sessions) is effectively two Mondays (10-19: 29
  trades +4.8R; 11-02: 19 trades +0.5R).
- **Monday part (P12):** the same rules on Tue/Wed/Thu/Fri average +0.030 / −0.052 / −0.047 / −0.027R. The Monday filter
  carries the whole edge and has no known mechanism (the module itself calls it "likely selection noise"); it is the biggest
  fit risk and no copy changes it.
- **P13 (weaker than SPY):** never binds in either test (a stock already > 2% below its open is almost always below SPY's
  move); removing it changes nothing. Kept (the live context needs it anyway).
- **Timer (P6):** entries 09:50-10:00 −0.04R (37 trades, 38% stops), 10:00-11:00 +0.31R, 11:00-11:30 −0.09R; the 09:50-10:00
  crosses are still the opening chop. -> WB2.
- **Reclaim-bar volume (new sensor):** lowest quartile (<= 0.47x its 20-bar average) +0.07R vs +0.25R above; in the valid
  half −0.27R. -> WB1 (curve: 0.35-0.55 all above the parent in both tests; peak 0.45).
- **SPY since the 09:50 close (owner-compliant gate):** lowest quartile (SPY falling since 09:50, <= −0.07%) −0.11R (valid
  −0.31R); tested as a gate (fails the replay alone; counted).
- **Price / 1R in dollars:** names above $300 −0.14R (37 trades, both halves negative); price cap tested (passes at $300,
  fails at $250 on the replay).
- **Stop (P26):** 75 stops (30%); only 28% had first reached +0.5R -> the stop is not a noise problem; 1.25R stop fails the
  2-year, 0.8R fails w/o best day.
- **Target (P27):** 141 targets at +0.92R; 32 time exits at +0.06R (median MFE 0.65R). Target 1.25R passes both tests
  (+0.241 / +0.191) but needs a new lab geometry in live code (`t125s1` is not in LabStrategy.GEOMS) — not spawned.
- **Day type (end-of-day regime, info only):** down +0.388 / flat +0.119 / up +0.018R.
- **Cost filter (P20):** worth +0.02R (off: +0.182R); keep.

## Which part is most responsible for the losses
Entry timing and entry quality, not the exhaust: the 72 parent trades WB3 removes averaged −0.067R (train +0.069 / valid
−0.293), the 176 it keeps +0.312R (train +0.289 / valid +0.338); Welch t 2.83. Exhaust tweaks (stop, BE, max hold, flat
13:00, trail, no target) all cut the 2-year avg R except a slightly wider target.

## Candidate tweaks (one part each)
1. **WB1 — new sensor P9b:** reclaim-bar volume >= 0.45 x its 20-bar average.
2. **WB2 — Timer P6/P14:** window start 09:50 -> 10:05.
3. **WB3 — combo WB1 + WB2** (each passed alone), counted as its own config.
