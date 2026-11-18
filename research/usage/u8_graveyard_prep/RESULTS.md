Educational only — not financial advice

# U8 — Graveyard revival prep: results (2026-11-18, research only)

Plan: PLAN.md (pre-registered before any tune was scored). Data: live journals run_id 1, all ten state branches,
sessions 10-06..11-17, R after costs (LR8), identical signals across accounts counted once. Locked block not read; no 2-year
or replay data used. FIT = 10-06..10-30, CHECK = 11-02..11-17 (12 sessions).

**Configurations tried: 1,100** (18 single changes + up to 17 conditional second changes per setup, on the FIT half of
every resident with >= 20 FIT trades, the 11 closed CWT12/CWT14 residents included for the ranking).
Bar t >= max(1.5, sqrt(2 ln 1100)) = **3.74**.

**Rule changes inside the window (research/ledger.jsonl):** 10-20 twin-symbol block; 10-21 Graveyard opens with the
per-setup -2R latch; 10-22/23 latch off in Testing 1/2, -2R latch back 10-29 (BAR90 same day); 10-27 slot cut; 11-12 LR8
after-cost R, Graveyard REPV-11/12 (300 smaller slots), RW6/ST4 leave the Graveyard for Testing C/B (from 11-13); 11-13
RW3S moved in (from 11-16); 11-16 ROT1; 11-17 KILL-FLAT, TSZ1; 11-18 GY-BENCH (18 residents benched 11-18..11-24, 20
guests in). R is per unit of risk, so sizing does not move it; latches and slot counts change which trades exist.

## Headline

- **0 PASS, 0 LEAD, 10 FAIL.** No pre-registered revival tune cleared the CHECK half; **no Testing-copy proposal and no
  decision code** comes out of this item.
- No Graveyard resident is positive w/o its best day over its whole live record (best: RW6G1 -0.053R, 66 trades).
  Four are positive w/o best day in at least one period: RW6G1 (CHECK +0.234, Graveyard +0.133), RW6 (CHECK +0.111,
  Graveyard +0.008; already left for Testing C on 11-13), RW3S (Graveyard-only +0.022, n 55), ST4 (Graveyard +0.027,
  n 23; already left for Testing B on 11-13).
- Tunes chosen on FIT mostly did not carry: on CHECK, total R improved for 7 of 10 (+44.7R summed, mostly by dropping
  trades of a losing setup), but **avg R improved for 5 of 10 and avg R w/o best day for only 3 of 10**; 0 of the gates
  beat 95% of random same-size subsets of the parent's own trades (best 92%: MF1, MF3).
- Day-type gates (SPY gap / SPY direction) were picked on FIT for 6 of 10 setups and flipped sign on CHECK for 3 of them
  (LIQ S1+G2: random-subset percentile 0.6%, RW6 T3+G2 1.6%) — the same instability Part 3 P2 found.

## Top-10 tunes, FIT vs CHECK (parent re-scored on the identical trades)

| # | Setup | Tune (<= 2) | FIT parent avg / w/o best | FIT tuned n, avg / w/o best | CHECK parent n, avg / w/o best, total | CHECK tuned n, avg / w/o best, total, best-day share | ΔR total | t (paired by day) | Random pct | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RW6G1-ns2-up3-vwap2sd-short-FD | X1 tgt 0.5R + T3 >= 11:30 | -0.277 / -0.317 | 25, -0.104 / -0.156 | 39, +0.229 / +0.234, +8.9R | 35, +0.103 / +0.079, +3.6R, 62% | -5.4 | -2.78 | 0% | FAIL (tune hurts a positive-CHECK parent) |
| 2 | NS3-failed-vwap-reclaim-short-FD | G2 SPY gap <= +0.2% + V1 above VWAP | -0.147 / -0.270 | 32, +0.118 / +0.022 | 146, -0.143 / -0.243, -20.9R | 25, -0.201 / -0.569, -5.0R | +15.8 | 1.31 | 34% | FAIL |
| 3 | RW6-ns2-up3-short-FD (left 11-13) | T3 + G2 | -0.438 / -0.481 | 26, -0.121 / -0.157 | 129, +0.341 / +0.111, +44.0R (87% one day) | 34, +0.145 / +0.036, +4.9R, 90% | -39.1 | -1.17 | 1.6% | FAIL |
| 4 | CWT09-gapdn-bounce-g5-lowerhalf-short | S2 SPY down + G2 | -0.253 / -0.431 | 40, +0.269 / +0.185 | 79, +0.013 / -0.138, +1.0R | 41, +0.150 / -0.131, +6.1R, >100% | +5.1 | 0.22 | 72% | FAIL (one-day) |
| 5 | RW4-ns3-adv150-short-FD | S1 SPY up + X1 | -0.246 / -0.354 | 45, +0.060 / +0.041 | 101, -0.114 / -0.208, -11.6R | 53, -0.079 / -0.221, -4.2R | +7.4 | 0.74 | 70% | FAIL |
| 6 | CWT13-vwapstretch-z05-short | X1 + G1 SPY gap > +0.2% | -0.159 / -0.228 | 38, +0.102 / +0.025 | 87, -0.129 / -0.213, -11.2R | 67, -0.174 / -0.241, -11.6R | -0.4 | -0.06 | 21% | FAIL |
| 7 | MF3-open-flowsell-rsi5hi-FD | T3 + V2 below VWAP | -0.209 / -0.250 | 42, +0.234 / +0.141 | 156, -0.091 / -0.165, -14.1R | 46, +0.063 / -0.113, +2.9R, >100% | +17.0 | 0.70 | 92% | FAIL (one-day) |
| 8 | LIQ-orl-sweep-open15-s25-long | S1 + G2 | -0.149 / -0.252 | 76, +0.197 / +0.093 | 154, -0.214 / -0.370, -33.0R | 31, -0.537 / -0.550, -16.6R | +16.4 | 0.49 | 0.6% | FAIL (gate picks the worst trades) |
| 9 | heat_fade_long | C1 spread <= 10 bps + S1 | -0.259 / -0.288 | 46, -0.041 / -0.105 | 101, -0.003 / -0.165, -0.3R | 46, +0.073 / -0.253, +3.4R, >100% | +3.7 | 0.24 | 77% | FAIL (one-day) |
| 10 | MF1-945-flowsell-vwapup-FD | K2 stock gap < 0 | -0.066 / -0.184 | 23, +0.364 / +0.202 | 72, -0.314 / -0.426, -22.6R | 17, +0.092 / -0.068, +1.6R, >100% | +24.2 | 1.66 | 92% | FAIL (closest) |

RW3S (rank 7) was skipped for a tune: no FIT trades (first live trade 11-03); the next eligible setup (MF1, rank 11) took
its slot, as PLAN.md says ("top 10 eligible"). ">100%" share = the best day is larger than the (small) positive total.

Per-setup effect on CHECK (remedy rule): total R better 7 / worse 3 (RW6 -39.1R, RW6G1 -5.4R, CWT13 -0.4R); avg R better
5 / worse 5 (largest gain MF1 +0.406R, largest loss LIQ -0.322R); avg R w/o best day better 3 / worse 7 (largest loss NS3
-0.326R). The total-R gains are mostly "fewer trades of a losing setup", which random removal also gives.

## What the deep dive can use (detail in CANDIDATES.md)

1. **RW6G1-ns2-up3-vwap2sd-short-FD** is the only resident whose recent raw record is positive in both CHECK (+0.229R,
   w/o best day +0.234R, best day 45%, 39 trades) and its Graveyard stint (+0.179R, 36 trades); FIT was -0.277R. Tuning it
   made it worse. Revival path = untouched, more reps (twin of RW6, which is now in Testing C — never the same account).
2. **MF1 / MF3 flow-sell shorts**: both FIT-chosen gates improved CHECK avg R (+0.41R, +0.15R; 92nd random percentile),
   but each tuned record is carried by one day and below the bar. This is the same family as C3-WB5 item 3 (MF2-FD /
   MF4-FD with NM-MF3's gate); do not open a separate MF1/MF3 copy before that item reads out.
3. **No revival case** for NS3-FD (its gate is already C3-WB5 item 2), RW4, CWT13, LIQ, heat_fade_long, CWT09-bounce
   on this evidence.
4. CWT12/CWT14 residents (11 setups, -1,211.5R on 8,973 trades, negative w/o best day in every period: whole record, FIT, CHECK and Graveyard-only): closed to new
   variants; no tune tried for revival. Whether they keep running is the deep dive's / owner's call (rule 20: nothing
   deleted; retiring is the owner's decision).

## Caveats

12 CHECK sessions; one big day carries several tuned records. Gates are scored on the trades that happened (freed slots
not modelled; latched-away trades cannot come back). The ranking used CHECK-period positivity (asked for by the item), so
the absolute CHECK level of RW6G1 / RW6 is selection-biased; the paired tune effects are clean because tunes were chosen
on FIT only. For the three tunes that combine a gate with an exit, the random-subset control compares against parent
trades without the exit (slightly lenient). The ranking's correlation points use |rho|; LIQ's -0.53 with Primary scored
-1 although it is a negative correlation (hedge-like; hedges are a guardrail item, so not pursued). RW6 and ST4 had already
left the Graveyard on 11-13 (ledger 2026-11-13-gy-rw6-st4-arena); RW6's tune is reported but informational.
