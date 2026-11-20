Educational only — not financial advice

# BEG-04 Quiet gap fade toward the prior close: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg04.py`, DESIGN.md B04 implemented as written. Plainest readings are marked [R] in the module docstring:
  - price >= $15 and ADV20 >= $50M on the prior close / point-in-time ADV20; gap = 09:30 open / prev_close - 1;
  - no unusual volume = rank_rvol20 > 100 AND RVOL20 < 1.5 (RVOL20 = 09:30-09:49 volume / mean of the prior 14
    sessions, rank in the day's U0 universe; the BEG-02 day table, read only). A day with no RVOL20 is not traded;
  - trigger on the close of a decision bar 09:50..11:59, fill at the next bar's open (DESIGN global convention);
  - only the first trigger of a symbol-day counts; if it fails the 1.2R test the day is skipped (no second look);
  - stop = the other side of R20 -/+ $0.02, capped at 0.35 x daily ATR(14) from the decision-bar close;
  - target = prev_close; the 1.2R test uses the decision-bar close; otherwise flat at the 15:55 open;
  - shorts: ETB only (bench10 E90 proxy) and never an inverse / volatility fund.
- Engine: `run.py`. 1-minute bars read straight from the caches. Costs, book and `stats()` imported unchanged from
  `research/ultimate_1119/top10/bench10.py`: LR8 costs (+1.2 bp borrow on shorts, x3 extended tier), stop first, target
  only when traded through by $0.01, testing-arena book (TESTING_RULES: cap 100, <= 3 lots/symbol, price >= $5,
  stop-cost filter 0.15R).

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the
  FIT-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data, reference only). The locked block 2024-11-01..2025-02-28
  is never read.

## Controls (fit nothing)
- `same`: the setup's booked symbol-days, a random decision bar in 09:50..11:59, same side, same $ stop distance,
  target prev_close when still on the profit side, 15:55 exit. 3 seeds.
- `univ`: every universe day (same filter), random decision bar, fade side, the setup's stop rule, no trigger and no
  1.2R test. 3 seeds.

## Tweaks (step 3)
- At most 3 one-part tweaks chosen after a FIT-only diagnosis of the base's worst losers, written below before they
  are scored. Pick = best FIT avg R with >= 20 booked FIT trades (ties: higher FIT avg R w/o best day). The pick is
  scored once on CHECK and on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: every Tier A leg holds (T1 combined avg R >= -0.0383; T1 check >= -0.0464; avg R w/o best day >= -0.0674 /
  -0.0781; total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and T2).
- NEAR: not MEETS, but each failing avg-R leg is within 0.02R of its threshold (R/session legs judged the same way).
- FAIL: everything else. REALLY BAD reported as defined there.
- Configurations: base 1, controls 0 fitted, tweaks <= 3.

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis in diag.py and before any tweak was scored)
FIT diagnosis of the base (1,860 booked, avg R +0.106, gross +0.166; but avg R w/o best day −0.0005: the best day
2025-04-08 is 100% of FIT total R, and 2025-04-07/04-30 add another +267R; the FIT record is a tariff-crash record):
- Exits: 709 full stops −768R (median hold 70 min; only 33 within 10 min), 403 targets +713R, 748 15:55 time exits
  +253R (+0.34 each, 69% positive). The time exit and target are not where the loss is.
- The 25 worst losers are all full stops (−1.16..−1.22R incl. costs), 19 of them shorts after gap ups, many with a
  tight R20 stop (0.12-0.25 ATR).
- **Stop:** by stop size (w/o best day): R20 stop <= 0.25 ATR −0.167 (339), 0.25-0.35 −0.061 (430), capped at
  0.35 ATR +0.084 (980). The tight structural stop is the clearest loser bucket.
- **Window:** decisions 11:15-11:59 −0.223 (226 trades, −50R; −0.214 with the best day).
- **Filter:** |gap| 1.5-2.5% −0.078 (822, −64R w/o best day); 2.5-6% +0.07.
- Side: shorts −0.258 w/o best day vs longs +0.174 (a side split is not a one-part tweak of the written rule set
  and would halve the idea; not tested).

The three one-part tweaks:
- **T1 `stopatr`** (stop): stop = 0.35 x ATR from the decision close always (drop the R20 stop).
- **T2 `win1114`** (window): decision bars 09:50..11:14 (instead of ..11:59).
- **T3 `gap25`** (filter): |gap| >= 2.5% (instead of 1.5%).
Pick = best FIT avg R with >= 20 booked FIT trades; scored once on CHECK and T2. Configurations: 1 base + 3 = 4.
