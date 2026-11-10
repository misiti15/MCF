Educational only — not financial advice

# STOPLAB — is -2R the right daily stop, and the right stop per setup? (owner 2026-11-09)

## The question
Owner 2026-11-09: "There's no way -2R is a perfect stop … maybe -2.25 / -1.75 / -1.8 / -1.6 / -2.01 is a little better, and maybe some setups need a tighter or looser stop. Run a swarm on all of our setups, all live sessions."
Two different stops were tested:
- **Daily stop** (Primary, `account.max_setup_daily_loss_r: -2.0`, latched since 2026-10-29): once a setup's realised R that day is <= -2, no new entries for it; open trades run to their own stops. Testing / Gen run it off.
- **Per-trade stop width**: each trade's own stop distance (k = 1.0 = the setup's own stop).

## Plan (research/stoplab/PLAN.md)
- Data: live journals of all 7 accounts (run_id=1, 17,584 live trades) plus 4,959 what-if trades that the latch / halts blocked (run_id=2), 1,590 setup-days, sessions 10-06..11-09. R = pnl_adj / (|entry-stop| x shares), costs in. Two-year lab (917k trades, 119 setups) as a second opinion. Locked block 2024-11-01..2025-02-28 never read.
- Judge on a time split per setup (first ~60% of its sessions = choose, last ~40% = validate), look for plateaus, day-clustered t, avg R without the best day, Remedies count (setups up / down and by how much).
- **A** daily-stop level (global, per account, per setup, per family, give-back), **B** per-trade stop width k = 0.75 / 0.9 / 1.0 / 1.25 / 1.5, **C** variants (open-loss latch, time stop, give-back / break-even).
- Skeptic re-ran A from trades.csv.gz independently (research/stoplab/VERIFY.md).

## Configurations counted
A 30 grid configs (A1 12, A2 12, A3 1, A4 1, A5 4) + B 5 multipliers (x 119 setups = 595 per-setup cells) + C 39 → study-wide **N = 79, bar t 2.96** (the skeptic's corrected figure; A was written against 2.88 at N = 64). Live stop-width diagnostic (5 x 110) not counted.

## Results in plain words

### A — daily stop level
- **-1.25R to -2.01R is one flat plateau.** On validate every level in that range is within +8..+15R of -2.0 (t <= 0.67). The owner's -1.6, -1.75, -1.8 and -2.01 behave the same as -2.0 on this data.
- **Looser is worse.** -2.25 gives -91R vs -2.0 on validate (t -1.91); -2.5 / -3 / -4 give -80..-169R; the 2-year lab agrees (t -2.7..-4.1). But this is because most setups lose — a looser stop just lets losing setups trade more — not because -2.0 is a special number.
- **-1.0R beats -2.0 by +110R on validate and fails.** t 2.39 < 2.96, it sits on the grid edge, 82% of the +110R comes from 4 dates (11-04..11-09), and its daily gain moves opposite to the book's day R (corr -0.67). Avg R per trade is -0.120 at every level: a tighter daily stop does not pick better trades, it only trades fewer of them. The gain beyond "trading losing setups less" is ~0 (+6R live, -776R on 2-year validate).
- **Per-setup levels fail.** 0 of 111 setups with >= 20 trades hold up. Of the 56 own picks that differ from -2.0, 24 improve (+98R) and 15 get worse (-143R); as a rule across all setups -34R.
- **Families:** only gap-down shorts with the stop off show something (+47R validate, t 2.14, 5 setups up / 2 down) — see the skeptic's notes below. Every other family fails.
- **Give-back stop** (G = 1.5R off the day's peak): +83R, t 1.47 — fails.
- Sim matches live: simulated -2.0 baseline gives Primary -62.3R vs -57.2R actual, Graveyard -619.7R vs -625.0R.

### B — per-trade stop width
- **Wider stops look better but it is size, not the stop.** At k = 1.5 (same $ risk) +0.025R/trade on valid, 80 of 117 setups better — but same $ risk on a wider stop means fewer shares on mostly losing books. Against a same-trade smaller-size control the stop effect itself is only +0.003..+0.006R, ~0 on SPY-down days.
- **Tighter stops (0.75 / 0.9) are worse** for 98 / 90 of 117 setups.
- **Per-setup choice is noise.** Of the 45 setups profitable at k = 1 on train, the train-best k improves on valid in 17 and worsens in 28; none pass. The 21 "passes" are losing setups whose best k is the grid edge 1.5.
- **One lead:** Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Primary, ADD8): k = 1.5 is positive on lab train and valid (stop-effect t 2.5). The live approximation disagrees.
- Not covered by the lab: 57 setups (hold / holdtr / S geometries, symbol lists). The full 1-min live re-walk (B1) was not run. The guild study STOPW (research/guild/1109/stopw/) reached the same verdict.

### C — variants
- **Open-loss latch** (counts open losses too, k = 2/3/4): +219R vs the current latch at k = 2, all of it from trading losing setups less; adjusted ~-50R at every k; -28R on winning setups; worse than the current rule in Primary at every k. Best validate t 1.50.
- **Time stop:** +196R live in total because 125 of 180 setups lose; on winning setups it costs up to -233R (13 better, 37 worse). Validate t <= 1.83; in the lab every threshold above 0R is worse (15 min / +0.5R: 86 of 117 setups worse).
- **Give-back / break-even:** arming at +0.5R hurts in the lab. Break-even after +1R is the only one with the same sign everywhere (live +7R validate t 1.44, lab t 1.21) but its neighbours do not back it up.

## Skeptic's verdicts (VERIFY.md)
The skeptic's own replay matches A exactly (-2,702.9 / -1,850.0 / -1,545.8R at off / -2.0 / -1.0 on the same trade counts), and B's 17 up / 28 down and C's +196 / -233R.
- **Confirmed:** the -1.25..-2.01 plateau; looser is worse (because most setups lose); -1.0 fails (t 2.39 vs 2.96, 82% from 4 dates, corr -0.67 with the book's day R); per-setup levels, stop width as a size effect, open-loss latch, time stop and give-back all fail.
- **Plausible but thin, weaker than written:** gap-down shorts with the stop off (84 of the +111R are latch what-ifs priced at backtest costs with no cap checks, 51R from one day in Testing 1, validate +47R rests on 4 days; 58% from 10-22, Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD`); `L3-gap-slope-fromopen-FD` k = 1.5 (negative on validate without its best day, grid edge, t about what the best of 119 setups shows by chance); break-even after +1R (loses R on winning setups).
- **Caveats:** the per-setup split lets the choice see some validate-period calendar days (a calendar split is needed); what-ifs flatter "off"; study windows differ (A 10-06..11-09, C live 10-06..11-04).

## Recommendation (per category)
| Category | Call |
|---|---|
| Daily stop level | **Keep -2.0R.** -1.25..-2.01 are the same on this data; looser is worse; -1.0 fails the bar and is 4 days. |
| Different global level | None. |
| Per-setup daily-stop levels | None (0 of 111 hold up). Gap-down shorts with the stop off → forward shadow only (stopL-gapdn-off). |
| Per-trade stop width | **Keep k = 1.0 for every setup.** Wider = smaller size, not a better stop; tighter is worse. `L3-gap-slope-fromopen-FD` k = 1.5 → forward shadow + backlog for the 1-min re-walk (stopL-l3-k15). |
| Variants | None. Break-even after +1R → forward shadow for hold-style setups (stopL-be1r). |

No config change. Rule-change context for the window: Primary's -2R latch effective 2026-10-29 (ledger), NS3-FD / RW4-FD to the Graveyard 11-02, MF3-FD / MF5-FD to the Graveyard 11-03, low-rep rotation into Explore 1 / Live Lab from 11-05 — the replay re-applies each stop rule to all trades, so these moves change which setups are in which account, not the comparison.

Files: research/stoplab/{PLAN.md, VERIFY.md, A_daily_stop/RESULTS.md, B_stop_width/RESULTS.md, C_variants/RESULTS.md}.

Educational only — not financial advice.
