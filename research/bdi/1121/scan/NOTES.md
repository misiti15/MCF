Educational only — not financial advice.

# Move Hunt week scan 11-17..11-20 (BD&I Saturday 2026-11-21)

Source: research/bdi/moves/moves.csv (the daily Move Hunt library; top 25 long + 25 short per day by move from the
decision point in ATR units, set "all"; 11-16 is not in the library). Live engine, descriptive only; nothing here is
tested. 200 big moves in 4 sessions.

## Capture
| | moves | caught (a live setup traded the right side inside the move) | R captured |
|---|---|---|---|
| long | 100 | **1 (1%)** | +0.2R |
| short | 100 | 10 (10%) | +19.4R |

Miss reasons (all 200): no setup signalled 74, traded the name outside the move 57, earnings blackout 31, wrong side
only 14, caught 11, skipped 13 (spread or stop-cost filter 10, halted 2, per-setup latch 1). Decision times: 65 of 200 decide at 09:35, 103 by
09:45 (entries stay >= 09:50 under the owner rule).

## Recurring precursors seen this week (candidates, filed in research/backlog.jsonl as status "idea")
1. **Peer-group cluster, laggard follows (mh-1121-peer-cluster-laggard).** Managed care moved as one group:
   11-18 UNH, HUM, ELV, MOH, CNC, CVS all top-25 shorts (decided 09:35-09:40); 11-19 CI, UNH; earlier 11-02, 11-06,
   11-11, 11-12. Day-type: >= 3 members of one industry group already >= 0.5 ATR the same way at 09:50; trade the
   members that have not yet moved. Differs from parked mh-1102-open-group-move (traded the group itself; 16 configs
   failed) — must report overlap with it.
2. **Crypto complex follows bitcoin (mh-1121-crypto-complex-follow).** 11-20: IBIT, FBTC, GBTC, BITO, ETHA top-25
   shorts and MSTZ, BTCZ (inverse crypto) top-25 longs; 11-19 MSTZ; miners (MARA, CLSK, RIOT) on 11-03/10/12.
   12 rows on 5 days in the library; 33% caught vs 5% for all moves. Day-type: the spot-BTC ETFs already >= 0.75 ATR
   from the prior close at 09:50; long-only via inverse crypto ETPs on down days (no borrow). Not the cap-etp family
   (index inverse / vol ETPs, do-not-re-run) — different underlying.
3. **Defensive relative strength on weak opens (mh-1121-defensive-rs-weak-open).** The long side caught 1 of 100:
   many long movers were defensives (11-17 CPB, EIX, a SPY-down open; 11-18 EGP, CTRE) plus vol ETPs (out of scope,
   cap-etp). Mirror of parked mh-1106 (up opens), whose only positive pocket was down-close days (+0.158R).
4. **Spread-skipped top movers (mh-1121-spread-skip-execution).** 10 of the 200 big movers were skipped on spread or the
   stop-cost filter in 4 days (STT, CRWD, GME, ELV, MOH, INVH, HNGE, FCNCA, SNAP, FDXF). Execution idea only: limit-at-mid entry for those signals, scored as a
   paired what-if on recorded quotes (U9 quote recording live since 11-18).

Not filed: vol-ETP longs (UVXY / UVIX / VXX, 11-17 and 11-20) — the cap-etp family failed overnight
(research/final1121, do-not-re-run). Single-name news pops (GPN 13:05, WING 14:00, CPRT 14:55) — no shared precursor.
