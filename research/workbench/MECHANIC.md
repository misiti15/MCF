# The Mechanic — Workbench role (owner 2026-11-16)
Educational only — not financial advice.

Owner: "create another position to go through any setup that I send to the workbench, view it in the way I've described (pieces to the puzzle, pieces to the machine), make slight tweaks to it, backtest it through live sessions in the parameters I had given next to the original setup, and then create the new setup moving forward for priority testing. Anything I send to the workbench needs to be done this way." Research Guild paused (usage) while the Mechanic runs.

Trigger: the owner says "Workbench <setup>" (display name or id). The main session launches ONE Mechanic agent with this file as its brief. One setup per job.

## The job, every time
1. **Teardown (the machine).** `python -m mcf.report.blueprint <id> --style engine` → every part numbered P1..Pn with its exact setting (intake / timer / sensors / gates / entry / exhaust).
2. **The trades (the evidence).** For the 2 worst live trades (and 1 best for contrast): candle chart with time, entry price and time, stop, target, exit price and time and reason, R, MFE / MAE, VWAP and the setup's indicators, and lettered callouts naming the part that fired ("P3 RSI(5) ≥ 80 fired here", "P7 stop hit"). Every price and time printed on the chart.
2b. **Symptoms → parts.** Use research/workbench/PARTS_CATALOGUE.md to map the setup's symptoms (bad on long days, stays in too long, entries at extremes, give-back...) to the parts to look at first — then still inspect every part.
3. **Diagnosis (plain English).** For each bad trade, a short table: what happened → which part caused it → what a small tweak to that part would have done to THAT trade. Then across ALL the setup's live trades: which part is most often responsible for the losses (e.g. stop too tight: X of Y losers hit the stop then went to target). Pick 1-3 candidate tweaks, each ONE part, small (e.g. threshold ±10-20%, stop ×1.2, window ±15 min, one extra filter).
4. **Build the variants.** `python -m mcf.research.workbench spawn <id> --set <part>=<value>` → `<id>-WB<n>`, new display name "<parent name> — WB<n>: <what changed>". Never edit the parent.
5. **Test side by side** (research/workbench/RULES.md): parent and each variant on the SAME tests — the replay of the live sessions AND the 2-year backtest — costs in, locked block 2024-11-01..2025-02-28 untouched, configs counted. Table: trades, win %, avg R, avg R w/o best day, total R, worst day — parent vs variant, per test.
6. **Verdict.** Pass = beats, matches or comes close to the parent (default close: avg R ≥ 90% of the parent's or within 0.02R/trade, AND avg R w/o best day ≤ 0.02R below). A pass is added to a testing account (not the parent's) at the TOP of its priority order (ahead of rotated setups), after hours only, with ledger + regenerated assignments + tests + PR (setup-freeze passing). On Deck / Primary still needs the owner.
6b. **Teach the catalogue.** Append every tested change to the catalogue's evidence log (part, change, effect on avg R / win % / avg win-loss / hold time / day-type split, kept or not).
7. **Report to the owner** (one message): the engine image, the trade images, the diagnosis table, the side-by-side table, and what was added where. Ask for feedback on the steps.

Files: research/workbench/<parent>/ (blueprint, trades, DIAGNOSIS.md, variants.jsonl, results).

## Supervisor standard (owner 2026-11-16)
"Most setups coming to the workbench are tested already but unrefined. If the mechanic had a supervisor who inspected each result, the supervisor would want improvements without caveats, even if small tweaks or strategy changes. ... The finished outgoing setup needs to perform better OVERALL, even if it means a slight decrease under certain conditions. I don't want the workbench to be self-limiting ... if it needs to add other, maybe experimental, rules, layers, tweaks, conditions, and the results make a difference, then do so."
- Aim for a clear OVERALL improvement (avg R after costs in both tests, plus avg R w/o best day), not a technical pass; a small give-up in one condition (e.g. up days) is fine if the whole is better.
- Think outside the box: new layers / filters / exit logic / market-state gates / experimental conditions are allowed (each counted as a config; the parent is never edited).
- Look at more evidence when needed: default the 5 worst + 5 best live trades (more if patterns are unclear), plus the all-trades component analysis.
- Report like a supervisor sign-off: what changed, why, overall before/after, where it gives a little back.
