# W8 — Data & accounting quality (crunch 2026-11-18)

Educational only — not financial advice. Paper results. Research and proposals only: no config or runtime change was
made and nothing was merged. Each fix is a patch in `patches/` with tests; reply codes are at the end.

**Scope.** All 10 live journals (state branches `mcf-data*` as of 2026-11-18 close: Primary, On Deck, Testing A–F,
Gen, Graveyard), live run only (`runs.kind = 'paper'`, run 1; what-if = run 2; shadow = run 3, excluded). 32,972 live
trades, 45,419 what-if rows. R = pnl_adj / (|entry − stop| × shares). Primary was also checked against Alpaca
(read-only GET: account and activities; this session only has the Primary keys). Reproduce with `audit.py`
(output in `audit_out.txt`). Data-quality checks, not a strategy search: **0 strategy configurations tried**. No
setup is scored for promotion here.

**Rule changes inside the window (ledger):** Primary sizing ~$5k → ~$4k per position (10-28); LR2 / LR3 / LR8 (R after
costs everywhere, Primary loss stops on cost R, live cost model) from **11-12**; Gen / Graveyard sizing caps 11-12;
TSZ1 testing-account half-size lots (0.125 % risk) from 11-17 ("R comparable, $ not"); shadow run from 11-17; GY-BENCH
11-18. The cost-basis change on 11-12 is itself finding B2.

## Verdict in one paragraph

The core bookkeeping is clean. On every journal: r_multiple = pnl / risk exactly, pnl = side × (exit − entry) × shares,
no duplicate broker ids, every post-11-12 row is tagged `costs=lr8`, and re-costing every row with today's
`mcf/costs.py` gives exactly the booked pnl_adj (0 mismatches in 32,972). Submitted signals = booked trades every day,
no stale open orders, no partial-lot quantity or VWAP errors (284 multi-part lots), and no duplicate entries around the
14:15 handover, so the handover does not double count. Journal $ matches Alpaca to within the next-morning regulatory
fees ($1–5 a day) on 9 of 10 accounts. **What is wrong is how the numbers are labelled and compared.** Five
misstatements affect decisions, one runtime-adjacent bug feeds the Primary halt, and a few smaller label issues follow.

## Findings (bugs and misstatements), ranked by impact

| # | Finding | Impact | Fix |
|---|---|---|---|
| B1 | **The daily review still quotes raw what-if sums.** `mcf/report/daily_review.py` sums every repeat signal of one name (re-fired each bar while blocked) and counts unfillable skips. On 11-18 it told the owner "'not shortable/ETB' blocked 142 signals that would have made **+24.0R** … before loosening it". You cannot short a name with no borrow (corrected R: none). C3-SCORE (owner yes 11-18) says raw what-if sums are "never quoted alone". | Primary: 62 % of what-if rows are repeats; raw +531.9R vs corrected +56.0R on 457 names (3,183 unfillable). The "rule cost us R" verdict flips on **11 of 51** Primary reason-days (n ≥ 10), with 4 false "loosen this rule" findings; 20 flips across all accounts. "Max positions for this setup", all accounts: raw **+288.8R** vs corrected **−135.3R** (2,920 names). | **P1** (report-only) |
| B1b | **`c3score.whatif_corrected` gives a silent 0 on real journal rows.** What-if rows have shares 0 / pnl 0 / pnl_adj null (R is in r_multiple), and the skip reason sits in `meta`, not in a `reason` column. `trade_r` returns NaN, every row is dropped, and the result is n 0 / R 0.0. The function is called only by its unit test (synthetic rows), so the approved what-if fix is not wired anywhere. | Any brief or post that uses it reports "0 corrected R". | **P1** |
| B2 | **Two cost bases are mixed in every since-start figure.** Trades before 11-12 carry only the flat $0.02 stop allowance; from 11-12 the LR8 model applies (stop 4 bp, target at limit, 1 bp entry, market exits, fees). Re-costing the pre-11-12 trades under LR8 lowers them by **0.035–0.040R per trade** on every journal (Primary −0.040, 1,149 trades, −45.9R; all accounts −742R in total). Leaderboards, the since-start avg R, promotion/demotion records and any before/after-11-12 comparison are therefore flattered in proportion to each setup's pre-11-12 share. | 219 setups: 194 get worse (median −0.020R, p10 −0.043R), 0 improve, 25 unchanged (no pre-11-12 trades). **5 setups flip sign** from + to −: RW7-gapdn-bounce-early-short-FD (767 tr, +0.016 → −0.007), **NS5-sma50-flush-oversold-long** (45 tr, +0.018 → −0.006; C3-NS5 already moves it), GEN-261026-02 (25), CWT09-g10-lowerhalf (23), CWT05-flush (21). One setup crosses the C3-EXIT100 −0.05 line (exhaustion_short, −0.046 → −0.063). Primary book (pooled live): L3-fromopen +0.221 → **+0.204** (protected setup, still clearly positive), RW3-FD +0.167 → +0.139, RW5-FD +0.144 → +0.110, ST7 +0.104 → +0.081, NM-ETF late dip +0.263 → +0.248. | **P3** (report-only helper `cost_r_lr8` + an "R (LR8 basis)" column wherever a record spans 11-12; the booked pnl_adj stays as it is) |
| B3 | **Dashboard "Since start" P/L on Primary includes the MTUM broker glitch.** `status.json since_start.alpaca_pnl` = **−$11,505.57**. It sums Alpaca day P/L, including the bogus MTUM split booking on 11-05 (−$11,456) and its phantom marks on 11-06 (−$184). The daily post removes these (PL1109 `PL_ADJUSTMENTS`); the dashboard (`docs/live/index.html`, 3 places) does not. Trading-only since start ≈ **+$134.66**. Confirmed against Alpaca activities: SPLIT MTUM 11-06; fill cash −$11,637 on MTUM vs journal $0. | Wrong headline P/L for Primary on the dashboard since 11-05. | **P2** (report-only) |
| B4 | **Open marks use the signal price, not the fill** (the 11-17 "+1.71R open on ~$32" anomaly). The runner learns entry fills (`_fill_px`) only on a restart, so `_open_marks` (status `open_r`) and the poll `mtm` snapshot mark new lots from the signal reference price and its stop distance. Re-marking the 11-17 12:32 book from journal fills gives **+1.18R** (before exit costs) vs the logged +1.69R, on the same $36.82 unrealized. The rest of the "$ vs R" gap is real, not a bug: those 7 ETF/large-cap lots risked **$13–55 each ($243 in total)** under the ~$3.4k position cap, against ~$60 median risk for the trades closed earlier that day ($211 per R). Per lot, the ref-vs-fill error averages +0.016R on Primary (p90 0.16R; 22–34 % of lots off by more than 0.1R). | Display, plus the Primary −20R halt: LR3 counts `open_r`, so the halt can trip slightly early or late. | **P4** (runtime-adjacent: needs owner, after hours) |
| B4b | **Live trade management uses the reference price as the entry for lots opened in-process**, and the fill (`avg_entry_price` / `_fill_px`) after a restart or handover. Breakeven moves the stop to the *reference* price. Trail and time-stop-min-R use the reference price and its stop distance. The same lot is managed differently before and after the 14:15 handover. | Small on average (mean ref-vs-fill +0.00 to +0.05R), but a "breakeven" exit on an adversely filled lot is a small loss. Affects setups with be_at_r / trail / time stop / SPY exit. | Described only (exit-logic change: owner decision, after hours; it can reuse P4's fills) |
| B5 | **"R per day" and dollars can disagree in sign**, because per-trade R is equal-weighted while $ risk per trade varies 10× under the position cap. Primary median risk is **$24 per trade vs the nominal 0.25 % = $212** (p10 $9, p90 $83). Tight-stop lots (stop < 25 bps) average **−0.59R after costs** (raw −0.39R, costs 0.19R) across all accounts while risking a few dollars, so they weigh heavily in R and barely in $. Primary days where R and $ disagree: 10-26 (−3.4R / +$34), 11-05 (+4.5R / −$419), **11-18 (−5.5R / +$213)**. Since start: −71.3R in trade R vs −$811 ≈ −3.8 nominal R. | For the owner's "positive R every day" goal, it matters which R is meant. C3-SCORE already adds account R next to dashboard R. This audit confirms that is needed and shows that it is the tight-stop / small-risk tail, not one setup, that drives the gap. | No code change. **Proposal DQ-RDEF** (definition) below. The tight-stop result goes to the conditions / exits workstreams as a lead (a minimum stop distance in bps or a minimum $ risk per lot), via the backlog. |
| B6 | **Unexplained Alpaca − journal $ gaps on On Deck and Testing A** (no keys for those accounts here). On Deck: 11-05 −$1,585 (MTUM-like corporate action?), 11-09 −$124, 10-20 −$92, 10-19 +$78, 11-06 −$57. Testing A: 10-14 −$387 (= PTP withholding, research/bdi/nightly1014), 10-15 −$185, 10-12 +$58. Graveyard: ±$22–45 on 5 days. All other days and accounts are within ±$5 (fees posted next morning). | The R records are unaffected (journal-based). Account $ for On Deck since start is −$5,318 Alpaca vs −$3,415 journal. | Run `python -m mcf.report.reconcile_pl --date <d> --account testing` with that account's keys (lists fills by symbol and non-fill activities). If 11-05 is a corporate action, add it to `PL_ADJUSTMENTS`. **DQ-ODK** |
| B7 | Minor labels: `status.json` `win_rate` and `profit_factor` use raw broker $ while `avg_r` is after costs (a 1-cent winner after costs counts as a win). Testing accounts' halts / latches count raw R while Primary's count cost R (LR3 is Primary only), e.g. Testing D 11-18: raw +4.03R vs after costs −0.58R. What-if R uses the backtest engine's costs, not LR8. | Labelling only. The Testing raw-R latch is mostly off (null in the overlays). | Note in the glossary. No code change proposed now. |

### Checked and clean (no action)

- r_multiple = pnl / risk; pnl recomputed from fills; pnl_adj re-costed with today's code: 0 mismatches on all journals.
- Cost model application by date: 0 pre-11-12 rows tagged lr8, 0 post-11-12 rows untagged; no negative costs.
- Journal vs broker fills on Primary: 11-05 and 11-06 fills match the journal to the cent on every MCF symbol. Only
  MTUM differs (the glitch). Daily differences elsewhere are the CAT and REG fees Alpaca posts the next morning ($0.4–4.9).
- Partial lots: 284 multi-part exits. Part quantities sum to shares and the quantity-weighted exit equals `exit` in
  all of them. No partial entry fills (order qty = filled qty on all 32,972).
- Handover (two trade runs per day): no duplicate signals, orders or trades. Same setup + symbol re-entries within
  10 minutes are no more frequent at 14:00–15:00 than at other hours. Risk-state realized R after the handover equals
  the journal sum on all 10 accounts (11-18).
- Shadow run (run 3) is excluded by every report query (all filter `kind NOT IN ('whatif','shadow')` or `run_id = 1`).
- R outliers: max |R| 16.6 (Gen); 9 trades with |R| > 5 (+52R in total, Gen/Graveyard/Testing). Stop on the wrong side
  of the fill: 1 trade (Gen, −0.7R). Not material.

## Patches (in `patches/`, not merged; tests in `patches/test_w8_dataquality.py`)

All are tested in a scratch worktree of `claude/charming-mccarthy-i3rhhr`: 5 new tests, plus 173 existing tests in
the touched areas (reconcile, lots, costs, c3score, daily post, dashboard, status, scale-out, PL reconcile) pass.
Full-suite result: see the end of this note.

| Patch | Files | Kind | What it does |
|---|---|---|---|
| P1 `P1_whatif_corrected_review.patch` | `mcf/report/c3score.py`, `mcf/report/daily_review.py` | report-only | `whatif_corrected` falls back to r_multiple and reads the skip reason from meta (journal rows). Daily review verdicts and "improvement candidates" use the corrected what-if (unfillable dropped, first signal per name-day-setup, spread + 0.05R haircut), with the raw sum shown beside it. Unfillable reasons show "not tradable". 11-18 Primary after the patch: ETB +24.0R raw → not tradable; lot cap +2.1 → −0.02R (2 names); setup loss limit +6.1 → +5.77R (6 names); spread rules → not tradable. |
| P2 `P2_since_start_glitch.patch` | `mcf/report/live_status.py`, `docs/live/index.html` | report-only | `since_start` gains `alpaca_pnl_trading` and `alpaca_adjustments` from the existing PL1109 list. `alpaca_pnl` stays the raw broker sum. The dashboard shows the trading figure labelled "(excl. broker glitch)". |
| P3 `P3_cost_r_lr8.patch` | `mcf/costs.py` | report-only | `cost_r_lr8(df, cfg)`: R after costs with LR8 on every live row (pre-11-12 rows re-costed; rows from 11-12 keep the booked pnl_adj; what-if keeps r_multiple). For leaderboards, reviews and research. It does not change the journal. |
| P4 `P4_fill_marks_RUNTIME.patch` | `mcf/execution/reconcile.py`, `mcf/execution/runner.py` | **runtime-adjacent** | `reconcile_day` exports the entry fill of every journal lot it sees (`attrs["fills"]`), and the runner merges it into `_fill_px` each pass. Status `open_r`, the poll mtm and the Primary −20R halt's open-marks term then use the fill. Bookings are unchanged (test). |

Apply: `git apply research/crunch/w8_dataquality/patches/P1_*.patch` (etc.), then copy the test file to `tests/`. The
test file covers all four patches. `test_reconcile_exports_entry_fills…` needs P4, `test_whatif…` / `test_daily_review…`
need P1, `test_since_start…` needs P2, `test_cost_r_lr8…` needs P3.

## Proposals (reply codes; no decision is made without the owner)

- **DQ-P1 (yes/no):** merge P1 after hours. The daily review and the C3-SCORE what-if use corrected sums, and raw sums are
  never quoted alone. Report-only.
- **DQ-P2 (yes/no):** merge P2 after hours. The dashboard's Primary since-start P/L excludes the labelled MTUM broker
  glitch (≈ +$134.66 trading vs −$11,505.57 raw, both kept). Report-only.
- **DQ-P3 (yes/no):** merge P3 and show "Avg R (LR8 basis)" next to Avg R on the leaderboard and in every promotion,
  demotion or review record that spans 11-12. It is a display column only, and the booked journal stays untouched.
  Flags: 5 sign flips (RW7-FD, NS5, GEN-261026-02, CWT09-g10-lowerhalf, CWT05-flush) and exhaustion_short crossing
  C3-EXIT100's −0.05.
- **DQ-P4 (yes/no, runtime, after hours only):** merge P4, so open marks use entry fills. It changes the input to
  Primary's −20R halt (LR3 open-marks term) by the ref-vs-fill error (per lot mean +0.016R, p90 0.16R), so it needs a
  ledger entry.
- **DQ-B4b (discuss):** management entry = fill. Breakeven, trail and time-stop-min-R would use the entry fill once
  known, the same before and after the handover. This is an exit-logic change: backlog + owner, after hours. It reuses
  P4's fills.
- **DQ-RDEF (decide the definition):** for "positive R every day", count **both** dashboard R (equal-weight trades) and
  account R ($ after costs / 0.25 % equity), as C3-SCORE shows them, and report days where they disagree (3 of 32 on
  Primary). Recommendation: keep trade R for setup evaluation and add account R as the system-level daily target. Small
  capped lots should not decide the day's sign.
- **DQ-ODK (yes/no):** run the read-only P/L reconcile with On Deck and Testing A keys for the 7 unexplained gap days
  (B6), and add any non-trading corporate action to `PL_ADJUSTMENTS`.
- **Lead for other workstreams (backlog, not a decision):** stop distance < 25 bps averages −0.59R after costs
  (475 live trades, all accounts; 25–50 bps −0.18R; > 400 bps −0.01R). Costs explain 0.19R of it and the rest is
  raw. Test a minimum stop distance (bps or ATR fraction) or a minimum $ risk per lot under RESEARCH_RULES (fit/check
  split, configs counted). This is descriptive live data only, not a tested remedy.

**Full suite with all four patches plus the new tests applied: 778 passed, 1 skipped** (scratch worktree, 2026-11-18
evening). Patches were generated as `git diff` from that worktree. The live code on the branch is unchanged.
