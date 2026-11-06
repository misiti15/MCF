# SQZ1 — "scalp the chase burst" (lead swing1106-L10), pre-registered 2026-11-06 ~22:50 ET, before any two-year number

*Educational only — not financial advice. Research only: nothing in config/, the trading path or docs/live changes.*

**Where it comes from (swing autopsy 11-05 + 11-06, one merged swing type "momentum burst into a squeeze").**
On both days the losing legs were bursts of the same setup entering *after* the index had already moved hard in the
entry's direction: 11-06 MF2-FD 14 shorts at 10:40 after QQQ −0.9% in 30 min (stopped 10:44–10:52 in the squeeze), then
Gen / Graveyard long bursts 10:46–10:53 bought the squeeze top; 11-05 MF4-FD / RW3S / GEN-261022-09 shorts 10:55–11:10 at
the low. BURST1 / BURST2 tried to *block* these entries (latches, family gate, compass, QQQ-flush gate): on two years the
blocked trades are not losers on average (MF family −57R when blocked), so blocking fails. Their live loss pattern is
different: they go in the money quickly and then all stop together (11-06 MF2 wave median MFE 0.57R, time to MFE 2 min).
So the salvage is an **exit** for those entries, not a block.

**Rule (one configuration, no grid).**
- Class A = an entry that is at least the **3rd same-side entry of its setup within 15 minutes** (inclusive window
  [t−15 min, t], all symbols, same day) **and** whose QQQ 30-minute return at the entry (last closed 1-minute bar vs the
  bar 30 minutes earlier) is **≤ −0.40 % for a short / ≥ +0.40 % for a long** (the index move already happened in the
  entry's direction).
- Class A trades take a **+0.5 × stop-distance target**; stop and the 15:55 flatten unchanged. Every other trade unchanged.
  Setups whose target is already ≤ 0.5 stop units (geometry t05s1) are unchanged.

**Two-year test (ONE run).** Lab trade lists `research/history2y/data/bt_lab1104` with the BURST1 enrichment (entry price,
stop %, 5-minute MFE path in stop units; `research/bdi/burst1/enrich.py`), open months only, **locked block 2024-11-01..
2025-02-28 never read** (asserted). TRAIN ≤ 2026-02-28, VALID 2026-03-01..2026-10-05 (as BURST2). Scalp filled when the
MFE path reaches +0.5 on a 5-minute bar *strictly before* the exit bar for stop exits (stop-first on the exit bar), on any
bar up to the exit for target / flatten exits; scalp R = 0.5 − the trade's entry cost in stop units (limit exit, no exit
cost, as bt_all targets). QQQ from `data/cache_hist/1Min/QQQ.parquet`.

**Pass (all required):** VALID day-clustered t of ΔR ≥ **2.61** (BURST lineage 29 + 1 = 30 configs, max(1.5, √(2 ln 30)));
TRAIN ΔR > 0; VALID **excess** > 0 (class A per-trade Δ minus the per-trade Δ the same scalp would give the same setups'
non-A trades — i.e. class A must be special, not just "+0.5R targets are better"); at most 1 family harmed in VALID
(family Δ < −5R). Testing / Live Lab suggestion if VALID t ≥ BAR90 (2.35) with the other conditions.
**Reported regardless:** per-setup and per-family better / worse counts and R (owner Remedies rule), QDAY split by SPY day
type (open-to-close > +0.25 % up / < −0.25 % down / else quiet) and by SPY vs its open at 10:00, live check on 11-05 /
11-06 (in-sample — the lead came from these days; descriptive only).

**Forward shadow:** from 11-09 tag live class A entries (all accounts, run 1) and log live R vs the +0.5R what-if
(research/bdi/swings/forward.csv, hyp `swing1106-L10`); bar: ≥ 5 sessions with class A trades, Δ > 0 on ≥ 60 % of them.
