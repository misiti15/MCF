# Skeptic pre-score audit of SC2 (research/sc2/PLAN.md + sc2.py), 2026-11-09 ~10:50 ET

*Educational only — not financial advice.* Code read only (no cache in this container); nothing scored.
Clean: 15-min driver return and sigma from closed bars and prior sessions only; fresh-crossing logic; beta-to-driver from
the prior 20 sessions; next-bar-open entry; stop-first; gap fills; hold = exactly H minutes; locked block filtered and
asserted at both reads; ret/TR NaN after the locked gap (the GATE2 A3 fix is already in); selftest covers the trade path.

1. **The controls do not test the stated mechanism (lag catch-up).** A trade wins if the follower catches up OR if the
   driver simply keeps going (15-min momentum in USO / GLD / IBIT) and drags every follower with it. C1 (random
   non-group name) and C2 (same follower, event-free bar) both pass a pure driver-momentum effect. Add, reporting only:
   (a) **driver-hedged R** = r - beta_drv x s x driver move over the same hold / R x entry (costs on the hedge leg);
   (b) **C3 non-laggard control** = same event, same group, followers that already moved >= L x beta x |rD|, same
   entry/exit; excess r - mean r(C3) per event; (c) **the driver itself** traded on the event, same stop/target in its
   own ATR. If laggards do not beat non-laggards and driver-hedged R is ~0, it is driver momentum, and the cheaper
   trade is the driver (that would be a new config, counted).
2. **Lineage N is understated.** Laggard catch-up has been tried several times and parked (ix-leadlag, ex30-PR1
   sympathy laggard, ex30-PR5 QQQ lead-lag, mh-1102 MH4 group laggard, combo1-C3, and C3FR runs tonight). SC2's driver is
   new, the bet ("the follower that lagged catches up") is not. Report the family's summed config count next to N 12,
   and use the family bar for any promotion; N 12 / BAR90 2.01 is fine for the "lead worth pursuing" label only.
3. **One event = one bet.** An OIL event can open up to 15 correlated trades. Day-clustered t covers it, but report
   n events per group and per side, and R per event (mean over its followers), so a 300-trade result from 25 events
   reads as 25.
4. **Costs on small names.** CIFR / WULF / HUT / CLSK / AG / CDE can have spreads well above 4.4 bp at adv20 $60M; R is
   only 0.25 ATR. Report median cost/R per group and the CRYPTO result with 2x spread (reporting only).
5. **Survivorship:** today's lab list, and 2025's crypto miners rallied hard; report per-group per-side, and long-only
   vs short-only, so a one-direction drift in a group is visible.
6. Minor: GATE2 A2 compares the reading bar close to the lab entry minute with <= (same-minute ties counted as
   known). The lab enters at the signal bar close, so it is consistent; strict < would cost nothing and removes doubt.

Would convince me: C1-excess t >= 2.01 AND laggard-minus-non-laggard (C3) excess > 0 with t >= 1.5 AND driver-hedged
R > 0, in TRAIN and VALID, on >= 2 of 3 groups, avg R w/o best day > 0; then the family bar before any Testing move.
