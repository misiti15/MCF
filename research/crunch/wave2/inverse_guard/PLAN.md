Educational only — not financial advice

# inverse_guard (code INV) — pre-registered plan (written 2026-11-19 ~22:15 ET, before any scoring)

Root-cause remedy R1 (research/rootcause_1119/FINDINGS.md): short setups never short index-inverse or long-volatility
products. Research only; no config, setup, exit or order change; nothing committed by this stage.

## Classes (frozen; research/forward/compass_gate/shadow.py as of b38a16981, not edited)
- INVERSE (101 names incl. single-stock and crypto inverse) and LONG_VOL (VXX UVXY VIXY UVIX VIXM VXZ).
- IDX-row = first row of the INVERSE literal (broad, sector and country index inverse + SARK, BTAL).
- BROAD = SH SDS SPXU SPXS SPDN PSQ QID SQQQ DOG DXD SDOW RWM TWM TZA SRTY MZZ SMDD SBB.

## Configurations (7, all counted)
| # | code | rule | role |
|---|---|---|---|
| 1 | G1 INV-FULL | shorts skip INVERSE ∪ LONG_VOL | main config (the R1 wording) |
| 2 | G2 INV-IDX | shorts skip IDX-row ∪ LONG_VOL (no single-stock / crypto inverse) | Skeptic's narrower form |
| 3 | G3 INV-BROAD | shorts skip BROAD ∪ LONG_VOL | narrowest |
| 4 | M1 mirror | longs skip INVERSE ∪ LONG_VOL | is the long side a leak? (diagnostic) |
| 5 | G1+M1 | both sides | broad version, for contrast |
| 6 | G1-ETBp | G1 on the 2-year lab after an ETB proxy | lab read closer to live |
| 7 | G2-ETBp | G2 likewise | |

ETB proxy (lab only): a symbol counts as hard-to-borrow when >= 50% of its live short signals in all accounts
(signals table, all runs) were skipped "not shortable/ETB"; lab shorts on such symbols are dropped from BOTH base and
guard arms (ETB would skip them anyway), so the guard is scored only on what ETB lets through.

## Data
- Live: journals origin/<branch>:journal.db for the 10 accounts in shadow.BRANCHES, run_id 1 (live paper), closed
  trades with risk > 0, R on the LR8 basis (mcf.costs.with_cost_r). Window 2026-10-06..2026-11-19 (whatever is closed).
- Live what-if (run 2) rows skipped "not shortable/ETB": ETB interaction only (what ETB already blocks in class).
- 2-year lab: research/rootcause_1119/sl_work/family_trades.parquet (118 enabled lab setups, first-per-symbol-day,
  production costs, 2024-10-01..2026-11-04, locked block 2024-11-01..2025-02-28 absent — verified 0 rows). Halves:
  early = before 2025-11-01, late = on/after. Reported as a separate source (SRCV1 weight 0).
- cache_fresh not used. Locked block never read.

## Metrics (every config, live and lab)
- Per setup (live: setup x account): trades removed, R removed, base total R, guarded total R, delta; avg R and avg R w/o
  best day before/after, best-day share; better / worse counts and summed sizes; largest worsenings.
- Per family (shadow.family_of): same aggregates.
- Live totals with and without 11-19; days the removed trades were red / green.
- ETB interaction: class pass-through of ETB (taken vs ETB-skipped) before 11-19 vs 11-19 (U9-ETB effective 11-19);
  what-if R of ETB-skipped in-class shorts; which symbols got through.
- Playing-time check: share of trades removed per setup; any low-rep (Explore 1 / Live Lab) setup losing > 25% of its trades.

## Decision bar (proposal only; owner decides)
Propose G-x for backlog + forward shadow only if, live: net > 0 with and without 11-19, >= 60% of affected setups not
worse, no setup worse by > 3R; lab (ETB proxy): net >= 0 in both halves. Otherwise report and stop.
The mirror is proposed only if it passes the same bar on its own.
