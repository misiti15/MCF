# Workbench: Big Gainer Fade, VWAP Band Guard (all day) (`RW6G1-ns2-up3-vwap2sd-short-FD`)

Teardown copies of `RW6G1-ns2-up3-vwap2sd-short-FD` (Graveyard). Each copy is a new setup (new id, parent link); the parent is never edited. Copies are research only until deployed under research/workbench/RULES.md.

## Log
- 2026-11-16 `RW6G1-ns2-up3-vwap2sd-short-FD-WB1`: P6/P7 `window` [950, 1500] -> [1100, 1500]. Status: PASS (contained in WB3).
- 2026-11-16 `RW6G1-ns2-up3-vwap2sd-short-FD-WB2`: NEW sensor — the reclaim bar closes >= VWAP + 0.5 SD (module clause `vwap_z`). Status: PASS (contained in WB3).
- 2026-11-16 `RW6G1-ns2-up3-vwap2sd-short-FD-WB3`: start 11:00 + close >= VWAP + 0.5 SD + ADV >= $150M + opening gap <= +2%. Status: PASS, recommended for Testing A (pending after close, not applied).

Files: DIAGNOSIS.md (every part P1..P26, 5 worst + 5 best live trades, all-trades analysis), RESULTS.md (all 52 configurations, side by side, deploy plan), variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (bench reused from the RW5 / L3 Workbench jobs), results_all.csv, extras.csv, component_analysis.txt, PNGs (engine, worst1-5, best1-5). The blueprint markdown `RW6G1-ns2-up3-vwap2sd-short-FD.md` names the trade charts trade1-5 (= worst1-5 here).

Educational only — not financial advice.
