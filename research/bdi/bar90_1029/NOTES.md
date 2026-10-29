Educational only — not financial advice

# bar90_1029: BAR90 (rule 22) re-screen of every previously tried setup and variant. Result: nothing clears, batch empty

*Backtests on the open two-year history (2024-10 + 2025-03..2026-10-07; train ≤ 2025-12-31, valid 2026). Costs are in
everywhere: 1c + 1 bp × time-of-day entry, +2c on stops, ×3 on the extended tier. **The locked block
2024-11-01..2025-02-28 was never loaded**, because no candidate cleared BAR90 under live conditions. Nothing here is a paper
or live result. No config, engine, setup, exit, docs/live, ledger or backlog file was changed, and nothing was committed.
Proposed backlog lines are in `backlog_proposed.jsonl`.*

## Failures first
1. **0 candidates clear BAR90 under live conditions, so the batch is empty.** It needs 0 trades/day and 0 accounts.
   On today's evidence, opening two new paper accounts for a BAR90 batch is not justified.
2. **Two stored rows cleared BAR90 on paper.** Both are L3-lineage variants from swarm1017 rework-st. The lineage has
   N ≈ 316,000, so the full bar is 5.03 and BAR90 is **4.529**. Both were re-run, and neither survives:
   - **RST1** (`RST1-l3fromopen-spyup-pm-t05s1-short`): t 4.70.
     - This exact version **already failed locked look 1** on 2026-10-17: −0.170R on n 125. A version is scored
       once, so it is excluded.
     - With the live earnings blackout, t drops to 3.83.
     - Picking one of its SPY-threshold neighbours now would mean tuning on the locked result, so none was picked.
   - **RST2** (`RST2-l3fromopen-mon-rsi5dip-long-t1s1`, long, Monday only):
     - In its native harness it reproduces exactly (n 836, +0.1632R) and clears **by 0.03** (t 4.56). That harness
       does not apply the 4-day earnings blackout that live trading uses (`config/default.yaml`
       `earnings_blackout_days: 4`).
     - **With the blackout, it fails BAR90:** n 734, t **4.25 < 4.529**, and down sessions **−0.097R** (n 37). Rule 19
       needs both up and down sessions positive.
     - The pass depends on ~100 earnings-window trades that live would never take. Under rule 14 it is reported as
       a fail, and **no locked look was spent.** The L3/ST lineage stays at 1 look used; the next look would need
       t ≥ 1.5.
     - It is also concentrated:
       - 2025-04-07 alone holds 399 of its 836 trades and 42% of total R.
       - The top 3 days hold 78% of total R.
       - 399 entries in one session would not fit in a 400-slot account.
     - It is a day-of-week rule, and its Tue–Fri version is negative.
     - It overlaps the live `CWT14-failbrk-pdl-p05-long` on 48% of symbol-days.
3. **Every other stored candidate is below its BAR90 bar or fails another gate.** The large lineages (CWT14, RW, NS,
   ST, L3, arenas, generator) carry N between 27k and 935k, so BAR90 sits at 4.07–4.72. The best regime-clean rows
   outside L3 reach t 3.6–3.9. See the table below.
4. **Method warning for the lead.** Most stored results (swarm1017, tf1019, arena, top5 and others) were scored
   without the live earnings blackout. For gap-day setups this makes the stored t optimistic: RST2 lost 0.31 of t
   and its down-session sign. No stored BAR90 pass should be accepted without a blackout re-score.

## Configurations
- **Candidate table** (`candidates.csv`, `build_table.py`): **1,725 rows.**
  - 984 are stored result rows (best or finalist per study and setup) from swarm1017 reworks and arena stored-passes,
    tf1019, trendguard, cutoff, history2y rescore, swarm1010 w1/w2, swarm15_1029, top5_1014..1028, and 540 generator
    finalists and picks.
  - 741 are backlog entries, with status, N, looks and the largest t their text quotes. That parsed t is often a
    train-only or improvement t, so it was triaged by hand. 116 parsed rows sat above a bar and were all checked:
    filters, exits and risk rules are not setups; daily strategies are out of scope; the rest have negative parents
    or failed looks.
  - 251 rows are setups already live and were excluded.
- **Screened directly on stored numbers:**
  - 242,370 swarm1017 arena configurations (`screen_arena.py`, `arena_bar90.csv`);
  - 13,167 result rows with t ≥ 1.35, taken from 607 research CSVs (`harvest.py`, `harvest_raw.csv`);
  - the generator registry: 27,228 specs, whose best regime-clean screen t is 2.95 against BAR90 4.07.
- **Re-run: 2 configurations** (RST1, RST2), each in 2 harnesses:
  - native `rescore_native.py`, which matches swarm1017 exactly;
  - pod1022 `score_batch.py` with the live earnings blackout.
  - 7 live long modules were scored for overlap only.
  - Gates were applied with `evaluate.py`, using `mcf/research/gates.py` and rule-19 regimes from `lib.regimes()`.
- **Locked looks taken: 0.**

## Best stored row per family vs BAR90 (t = day-clustered, two-year open history)
| family (lineage N) | best row | t | BAR90 | other gates | verdict |
|---|---|---|---|---|---|
| L3 rework (≈316k) | RST1 / RST2 | 4.70 / 4.56 | 4.53 | see finalists | fail (locked / blackout) |
| NS rework (≈166k) | NS2 + SPY>+0.5% + slope<0 | 4.27 | 4.41 | down n 23 | fail |
| RW6 / NS2 morning shorts (82k) | RW6 breadth>0.65 & slope<0 | 5.25 | 4.34 | down n 8 (up-day only) | fail regime |
| RW2 exhaustion (935k) | gap<−1 & SPY>+0.5%, PM | 3.83 | 4.73 | ok | fail t |
| MISC HL (≈34k) | HL core, Tuesdays | 3.85 | 4.11 | ok | fail t |
| HL-T75 10-min (34k) | NM-HL-T75-pm-long | 3.66 | 4.11 | live | fail t / live |
| CWT14 (121k) | ORH depth ≥ 0.3 | 3.07 | 4.56 | ok | fail t |
| CWT04 backside (≈390k) | a1.5 gap<−2 | 11.35 on 47 days | 4.57 | WF fails, April 2025 | fail |
| arena am-long / am-short | — / AMS-N1 | 3.39 / 4.19 | 4.16 | N1 is live | fail / live |
| arena mid-long / mid-short | from_pc ≤ −3.4% PDL | 4.50 / 2.79 | 4.26 / 4.37 | valid < 0 | fail |
| arena pm-both (189k) | from_pc ≤ −2.3% short | 8.64 | 4.44 | 2025-04-10 = 83% of P/L | fail |
| arena index-ETF (267k) | ETF late dip | 4.38 | 4.50 | live (NM-ETF) | fail |
| ST swarm1010 (227k) | ST6 plateau | 3.29 | 4.35 | ok | fail t |
| reddit R05 gap-fill long | io=3.0 | 4.46 | 3.63 | down n < 30 | fail regime |
| generator (27k) | GEN-261029-10 short | 2.95 | 4.07 | ok | fail t / live |
| swarm15 / p1 / p2 / p3 / top5 / hf / htf / bdi10xx | parents −0.01..−0.10R | ≤ 1.5 | 2.5–4.8 | — | fail |

**Out of scope (multi-day / daily-bar, not runnable in an intraday Testing account that flattens at 15:55):**
- `er-react-runup-tr` (earnings drift long, 20-day hold) is the one numeric BAR90 pass among them.
  - t 3.39 against BAR90 3.12 (lineage N 414).
  - Up and down months +2.26 / +0.16%, WF 0.86, net of a random-name baseline.
  - No look used. It needs a multi-day paper engine (longhold), and the decision is the owner's.
- The Connors RSI daily lineage has already failed locked looks 2 and 3.
- C3 + RS63 fails on excess and on down months.

## Batch
**Empty.** Total expected trades/day: 0. Accounts needed: 0 (each Testing account has 400 slots, about $1k per slot at
0.25% risk). `batch.csv` has the header only. The report says plainly that nothing clears; no bar was loosened.

## Files
- `harvest.py`, `harvest_raw.csv`: stored rows with t ≥ 1.35 from every research CSV.
- `screen_arena.py`, `arena_bar90.csv`: the arena screen.
- `build_table.py`, `candidates.csv`: the candidate table with BAR90 verdicts.
- `modules/`: copies of RST1 and RST2 with `MIN_ADV = 0`, scored as in swarm1017.
- `rescore_native.py` (`rescore_native_out.txt`): the native harness.
- pod1022 `score_batch.py` run: `rescore_rst.jsonl`, `rescore_rst_out.txt`.
- `evaluate.py`: the BAR90 gate check.
- `finalists.csv`: every finalist, failures included.
- `batch.csv`: the batch, which is empty.
- `backlog_proposed.jsonl`: proposed backlog lines.

Educational only — not financial advice
