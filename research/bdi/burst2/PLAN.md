# BURST2 — short-burst remedy re-test with 11-05 + 11-06 live evidence (pre-registered 2026-11-06, before any scoring)

*Educational only — not financial advice.* Research only: nothing in config/, mcf/ or the trading path changes.
Locked block 2024-11-01..2025-02-28 is never read (`lib.load_month` refuses it; MCF_HIST_ALLOW_LOCKED unset).
Lineage: BURST1 (research/bdi/burst1, 16 configs, 0 pass). Owner Remedies rule (2026-11-05): targeted at the failure
where it occurs, not tailored to one setup, not over-broad; every remedy reports per setup / family how many improve,
how many worsen and by how much.

## Failure situation (live, Primary)
- 11-05: MF4-FD 13 shorts 11:00-11:10 at the QQQ low, 12 stopped 11:10-11:18 in the bounce.
- 11-06: MF2-FD 28 shorts, 23 of them 10:30-10:40 (14 in the 10:40 poll alone; semis / tech ETPs) after QQQ fell
  from +0.68% (10:00) to -0.21% (10:30) while SPY stayed **above** its open (+0.46%); 20 stopped 10:44-10:52 together
  (-21.6R); MF4-FD 10 shorts 10:35-10:40, -5.5R. The realised -2R latch fired 10:46 / 10:52 (after the last entry);
  the -20R account halt fired 10:55.

## Remedies (13 configurations; each acts only in the failure situation)
Per setup-day in entry order (ties: file order); a blocked signal is simply not taken. Kept entries are the only ones
that count toward any rule. "Burst entry" = an entry that would be the setup's (B+1)-th kept same-side entry within
15 minutes (t-15, t].
- **A open-loss latch** L in {-2, -3, -4}: setup daily R = realised R of kept trades exited by t + 5-min mark-to-market
  R of its open kept trades; once <= L, no new entries that day. Scored vs the live realised -2R latch and vs no latch.
  (-2 / -3 are second looks of BURST1 b; -4 is new.) (3)
- **B same-family burst gate** N in {4, 6, 8}: per account, family (setup prefix letters: MF, RW, L, NS, ST, CWT, GEN,
  NM, ...) and side, block a new entry if >= N kept same-family same-side entries entered in (t-15, t]. (3)
- **C compass for burst shorts** B in {2, 3} x x in {0, +0.25%}: a burst short entry is blocked if SPY's from-open
  return (close of the last 1-min bar before entry vs the 09:30 open) is > x, i.e. SPY is not on the short side.
  Longs and non-burst entries untouched. (4)
- **C-sym** B = 2, x = 0: as C, plus burst longs blocked when SPY is below its open. (1)
- **D flush gate for burst shorts** B = 2, y in {0.4%, 0.7%}: a burst short entry is blocked if QQQ's 30-minute return
  at entry is <= -y (the selling already happened). (2)

## Data and windows
- 2-year: `research/history2y/data/bt_lab1104` trade lists (95 setups, uncapped, production costs) re-enriched with 5-min
  marks (burst1/enrich.py). TRAIN = open dates <= 2026-02-28; VALID = 2026-03-01..2026-10-05. Index paths from
  data/cache_hist/1Min SPY / QQQ.
- Live = all 7 accounts' journals 2026-10-06..2026-11-06 (run_id 1; latch- and halt-blocked what-ifs from run_id 2 kept
  for the latch-off sequence), 5-min and 1-min SIP bars (GET only). Windows: LIVE_all, LIVE_primary, P_11-04, P_11-05,
  P_11-06.
- Excess delta as in BURST1 (blocked trades valued against their setup's TRAIN mean R) so "trading less of a losing
  book" is not counted as a fix.

## Decision rule (fixed now)
Lineage N = 16 + 13 = 29 -> bar = max(1.5, sqrt(2 ln 29)) = 2.60 (BAR90 2.34 shown for reference only: a Primary risk
rule needs the full bar). Passes only if (1) VALID raw delta day-t >= 2.60 AND VALID excess day-t >= 1.0, (2) TRAIN raw
and excess > 0, (3) LIVE_all delta > 0, (4) no family materially harmed (VALID family delta < 0 at t <= -1.0, or more
than 2:1 setups worse than improved with a family loss > 5% of its |R|). Pass -> DECISION; else the best near-miss is
logged as a forward shadow + FYI, and every config is reported with its per-setup / per-family table.
