Educational only — not financial advice.

# OUT-NMETF: frozen forward test for NM-ETF-late-dip-di-long (Primary), pre-registration

## Summary for the owner
- **Primary's own record does not pass yet.** 15 trades over 6 traded days. Avg +0.075R, day-clustered t 1.18. The best day (11-17) is 66% of its R, so it carries the `1 day` tag. Avg R w/o best day is +0.034R.
- The +0.21R / t 3.50 figure people quote is the **whole record**: Testing 2 + Live Lab + Primary, 33 trades over 15 days. Primary is the scoreboard, so the test scores Primary only, over 25 fresh sessions: 2026-11-23 to 2026-12-31.
- **Pass** needs all three: t ≥ 2, avg R w/o best day > 0, best day < 50%. If the true edge is near the whole record (+0.21R), the chance of passing is about 80%. At Primary's current +0.075R it is about 20%.
- **Doubling "risk" from 0.25% to 0.5% would change nothing on its own.** 14 of 15 Primary trades were sized by the ~$3.4k slot, not by risk. So the committed size-up doubles both the risk cap and the notional cap (2 slots).
- **Rule conflict for you to decide:** C3-BAR2 says "per-setup risk stays flat". A yes to this protocol must explicitly allow this one conditional exception.

## Method
- **Rules.** Read from `config/default.yaml` (strategies block, `account`, `live`, `costs`), the module `research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py` and `mcf/strategies/setups.py` (LabStrategy GEOMS: t05s1 = 0.5R target, 1R stop).
- **Baseline.** From `live_trades.pkl` (LR8 cost basis). Cross-checked against the Primary journal: `origin/mcf-data:journal.db`, run_id 1 (paper), read-only.
  - The journal holds 15 trades on 15 signals, all with status `submitted`. There were 0 resource / halt / latch / U9 skips.
  - Primary's shadow rows (run 3) and the `BASE1:*` rows are excluded.
- **Day-clustered t.** Defined as in FOOTRACE-EXIT (rule 24): the t of the per-day mean R over traded days, with df = D−1.
- **Ledger.** Scanned every `research/ledger.jsonl` entry effective on or after 11-19, plus the open backlog items, TAGS1 `rules.json` and the outsider items approved today.
- **Power.** Non-central t with day-mean SD 0.28 (the whole record's 0.284) and 14–18 traded days.
- **Tracker.** Wrote and ran a read-only daily tracker. On 11-11..11-19 it reproduces the baseline exactly.

## Results

### Baseline (R after costs, LR8; live paper)
| Slice | Trades | Traded days | Total R | Avg R | Day-clustered t (one-sided p) | Avg R w/o best day | Best day (share) | Worst day | Shrunk n/(n+150) |
|---|---|---|---|---|---|---|---|---|---|
| **Primary 11-11..11-19 (scored slice)** | 15 | 6 (of 7 sessions) | +1.12 | **+0.075** | **1.18** (0.15) | **+0.034** | 11-17 +0.74 (**66%, `1 day`**) | 11-19 −0.90 | −0.084 |
| Pre-Primary (Testing 2 10-19..11-04, Live Lab 11-05..11-10) | 18 | 9 | +5.88 | +0.327 | 3.74 | +0.294 | 11-05 +1.46 (25%) | 11-04 −0.61 | −0.054 |
| Whole record (all accounts) | 33 | 15 | +7.00 | +0.212 | 3.50 (0.002) | +0.185 | 11-05 +1.46 (21%) | 11-19 −0.90 | −0.044 |

Primary by day:

| Date | Trades | R |
|---|---|---|
| 11-12 | 1 | +0.21 |
| 11-13 | 2 | +0.44 |
| 11-16 | 2 | +0.54 |
| 11-17 | 4 | +0.74 |
| 11-18 | 3 | +0.08 |
| 11-19 | 3 | −0.90 |

- Primary exits: 5 targets, 10 flattens at 15:55, 0 stops. All of Primary's losses are 15:55 flattens on 11-18 / 11-19.
- The record is in decline: Testing 2 / Live Lab +0.33R, then Primary +0.075R.
- Same-day trades are nearly one bet. SOXL, TECL and TQQQ fire together (11-17, 11-18, 11-19), which is why day clustering is required.
- Sizing in Primary: notional per trade was $3.0–3.5k (the slot). Dollar risk was $55–205, against about $208–240 for 0.25% of equity.
- Data-quality note: Primary's shadow book and the live trades differ by up to ~0.3R per trade on 11-17 (different 15:55 flatten prices). The test scores live only.

### Rule-change context inside the baseline window
- **10-17:** entered Testing 2 (2026-10-17-t2-q8-near-misses).
- **11-05:** moved to Live Lab (2026-11-04-lowrep-explore1-livelab).
- **11-11:** moved to Primary (2026-11-10-team6-primary). From then on: Primary sizing (0.25% / ~$4k slot), the −2R per-setup latch, and from 11-12 the LR3 latch/halt counted on cost-in R.
- **11-12:** LR8 costs start. Earlier rows are re-costed (DQ-P3, about −0.04R per trade).
- **11-19:** Epoch 1 / C3-NS5 (Primary runs 5 setups) and U9-TGT quote skip (0 NM-ETF skips so far).
- **11-20:** stop/target cent rounding. It is in effect for the whole test window; the baseline used round-to-nearest.
- **11-17 onward:** the Workbench copies (WB1 in Testing B, WB4 in Testing E) and, from 11-20, the ETFDISP / ULT descendants run in other accounts. They are separate setups and are not counted.

### Power of the frozen test (chance of passing t ≥ 2)
| True avg R | 14 traded days | 16 | 18 |
|---|---|---|---|
| 0.000 | 3% | 3% | 3% |
| +0.075 (Primary so far) | 19% | 20% | 21% |
| +0.150 | 52% | 57% | 61% |
| +0.212 (whole record) | 79% | 84% | 88% |

---

## THE PROTOCOL (frozen text, for the owner's yes)

**OUT-NMETF v1: pre-registered forward test of NM-ETF-late-dip-di-long in Primary**
- Frozen at repo commit 381ccf11c, 2026-11-20.
- To be approved in the 2026-11-20 Friday-after-close window, before the 11-23 open.

### 1. The setup under test (frozen exactly as it runs today)

**Config block** (`config/default.yaml` `strategies.NM-ETF-late-dip-di-long`; sha256 of the JSON-dumped block 59dc73e86a810174):
```
enabled: true, type: lab, module: research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py,
symbols: module, min_adv: 95000000, window: [1400, 1500], scale_out_r: null,
tags: [near-miss, swarm1017, forward-observation, q8, etf, fragile]   (refire: off; geom: module default)
```

**Module** (sha256 6c47c7ec8c7723ed…) and indicator code `mcf/research/arena/indicators.py` (bf2dc920b7726249…):
- **Side:** LONG.
- **When:** decision-bar close between 14:00 and 15:00 ET (15:00 included).
- **All three must hold:**
  - `ret3 ≤ −0.7977%` (15-minute return)
  - `di_diff7 ≥ 0` (+DI(7) ≥ −DI(7), in-day)
  - `atr_d_pct ≥ 3.5968` (daily ATR ≥ 3.6% of price)
- **Symbols:** the module's frozen ETF list (128 symbols, including the 3x funds SOXL/SOXS/TECL/TQQQ/SQQQ/TZA/LABD…).
- **Liquidity:** ADV ≥ $95M.
- **Signals:** first qualifying bar per symbol per day.

**Exits:**
- R = 0.25 × daily ATR (`r_atr_frac` 0.25).
- Stop 1R; target 0.5R (GEOM t05s1).
- Flatten at 15:55 (`flatten_by`). On half days the flatten is at 12:55 (`flatten_lead_min` 5).

**Primary account rules that apply to it, frozen for the window:**
- `risk_per_trade_pct` 0.25.
- Slots 77 × `buying_power_multiple` 3.2 (≈ $3.4–3.9k notional; this cap binds).
- `max_position_notional_pct` 10.
- −2R per-setup daily latch (`max_setup_daily_loss_r` 2.0, cost-in R per LR3).
- `max_lots_per_symbol` 3 with `same_setup_reentry` true.
- `max_positions_per_strategy` 30.
- −20R account halt.
- `skip_passed_at_quote` true.
- Stop rounding per 2026-11-20-stop-rounding.
- Fill profile B (shadow).
- LR8 cost model (`mcf/costs.py` sha 203b8c0a…).
- **Priority:** first in Primary's `live.setup_order`.

### 2. Frozen window
- **The 25 eligible Primary sessions from 2026-11-23 to 2026-12-31 inclusive:**
  - 11-23, 11-24, 11-25, 11-30;
  - 12-01..12-04, 12-07..12-11, 12-14..12-18, 12-21..12-23, 12-28..12-31.
- **Not eligible, not counted:**
  - Closed: 11-26, 12-25.
  - Half days: 11-27 and 12-24. The runner flattens at 12:55, before the 14:00 window opens.
- **Sample floor:** at least 12 traded days AND at least 25 trades.
  - If not reached after session 25, the window extends one eligible session at a time until both are reached, up to 40 eligible sessions (last possible: 2027-01-25).
  - The extension depends only on counts, never on results.
- **Operational misses** (runner or data outage covering 14:00–15:00, or a broker outage) are logged. Each one adds one eligible session to the window.
- **Pre-window sessions are reported but not scored:** 11-11..11-20.

### 3. What is scored
- **Rows:** Primary journal (`origin/mcf-data`, `trades`, run_id = 1, exit_time not null, strategy = NM-ETF-late-dip-di-long), dated inside the window.
- **R:** after costs on the LR8 basis (`mcf.costs.cost_r_lr8`, as `mcf/report/footrace.live_trades`).
- **Never counted:** shadow (run 3), BASE1, what-if rows, other accounts, and the Workbench / ULT / ETFDISP descendants.

### 4. Pass/fail bars
Scored once, after the close of the last window session.
- **(a) Day-clustered t ≥ 2.0** (one-sided). t = mean of per-traded-day mean R ÷ (SD of per-day mean R / √D), df = D−1. This is the FOOTRACE-EXIT definition.
- **(b) Avg R per trade without the best day > 0.** The best day is the session with the highest total R; all of its trades are removed.
- **(c) Best day's share of the window's total R < 50%.** If total R ≤ 0, (c) fails.
- **Report alongside, for information only (not decisive):**
  - avg R, total R, account R;
  - the t of day sums and the cluster-robust t;
  - green-day %;
  - each session's R;
  - every skipped signal by reason;
  - the C3-BAR2 shrunk estimate;
  - the rule-change context per §7.

Outcome:
- **PASS:** all of (a), (b) and (c).
- **FAIL:** anything else. Labelled FAIL-weak if (b) holds, FAIL-negative if not.

### 5. Committed actions

**On PASS (committed now, by the owner's yes to this protocol):**
- From session 2027-01-04, NM-ETF's lot budget doubles: the risk cap goes from 0.25% to **0.50% of equity** AND the notional cap goes from 1 slot to **2 slots** (≈ $7–8k, still under the 10%-of-equity hard cap).
  - Both are needed: today 14 of 15 trades are slot-bound, so a risk change alone would size no trade differently.
- Nothing else changes. Trade R, the −2R latch and the −20R halt arithmetic are per-trade R and stay the same; dollar swings double.
- It is applied in the 12-31 after-close window (the last session of a holiday week; RESEARCH_RULES rule 25) as a new Primary epoch. It goes through a ledger entry, the rule-27 adversarial review, and `assignments.json` is untouched (not a move).
- The per-setup sizing override does not exist in code today (`mcf/execution/risk.py` uses the account-wide `risk_per_trade_pct` and `slot_notional`). It is built and reviewed on a branch during the window and merged only on PASS.
- **Size-down guard (pre-registered):** sizing returns to 1× at the first Friday review where cumulative trade R since the size-up is ≤ −5R. It is otherwise checked once more after 25 sessions at 2×, against the same three bars.
- **Explicit exception:** this overrides C3-BAR2's "per-setup risk stays flat" for this one setup and needs the owner's explicit wording.

**On FAIL (committed now):**
- Size stays at 1× (0.25% / 1 slot). No size-up for this version without a new pre-registered window (look 2, bar t ≥ 2.5), starting no earlier than the next Friday window.
- The setup **stays in Primary**. This test alone never demotes it (consistency over churn). Demotion stays under C3-BAR2 (−10R cumulative since admission on 11-11) or an owner decision.
- FAIL-negative with t ≤ −1.5 (the FOOTRACE-EXIT mirror) is raised at the Friday review as an owner item: "move to On Deck?".
- The result goes in the ledger either way.

**During the window:**
- The tracker is display only ("interim, not a verdict"). No decision is made on interim numbers.
- Only two early actions are allowed:
  - the C3-BAR2 −10R demotion (cumulative since 11-11, currently +1.12R);
  - the BROKEN-setup exception (bug, data, borrow / spread change), raised to the owner at once.

### 6. Protocol violations
**Category A voids the test.** Any of these makes it NO RESULT (size stays 1×; a new window needs a new pre-registration):
1. Any edit to the frozen block, the module, `indicators.py` logic, the symbol list, the window, the geometry, refire, `r_atr_frac`, `min_adv` or `flatten_by` that NM-ETF uses.
2. Any change to NM-ETF's sizing, latch, priority position (it must stay first in Primary's `setup_order`), or its cost model / R definition used for scoring.
3. Adopting any filter or guard that can block NM-ETF entries. Known candidates:
   - the TAGS1 tag **FLAT25** (scope Primary; scored once on/after 12-17, inside the window);
   - backlog **nightly-1117-etp-twin-groups** (one lot per bar across SOXL~TECL~TQQQ);
   - any OUT-BRAKE or Primary halt change that adds a new NM-ETF-specific block.
   Such a change, if adopted, must exempt NM-ETF until 12-31, or wait for the 12-31 after-close window.
4. Promoting any NM-ETF descendant into Primary during the window: WB1, WB4, ETFDISP-late-dip-hidisp-long, ULT-22-wb4-wide-etf-long, ULT-14-snap-long, ULT-HV2. They share symbols and the window, so they would take its fills.
5. Moving NM-ETF out of Primary, benching it for a session, or any manual close or override of its positions (other than the BROKEN exception).
6. Re-defining bars, window or exclusions after 11-23, or scoring a trade that is outside §3.

**Category B is allowed, but logged as rule-change context.** For any of these, the score is shown both with and without the sessions after the change:
- Other Primary epoch changes (lineup, other setups' rules), housekeeping on Primary's live path, account-wide halt changes, runtime fixes.
- A Category B change that causes any NM-ETF signal to be skipped (slots, halt, buying power) must be listed by session.

### 7. Upcoming ledger / backlog items that could touch it (as of 2026-11-20)
| Item | Effect on NM-ETF | Status in protocol |
|---|---|---|
| 2026-11-20-stop-rounding (eff. 11-20) | Broker stop/target cents rounded away from / toward entry; at most 1¢/share | In effect for the whole window (part of the frozen setup); baseline predates it |
| 2026-11-19-u9-tgt-quote-check (eff. 11-19) | Skips entries already through target/stop at the quote | Frozen in; skips counted and reported (0 so far) |
| 2026-11-19-owner-answers-evening INV shadow / INV | Short setups only | Does not touch NM-ETF, which is long-only. An adopted "exposure checks" sub-change (untested) would be Category B. |
| TAGS1 FLAT25 (score on/after 12-17, scope Primary) | Could skip NM-ETF entries | Category A unless NM-ETF is exempt or adoption waits for the 12-31 window |
| Backlog nightly-1117-etp-twin-groups (idea) | Would cut same-bar SOXL/TECL/TQQQ stacking | Category A if live before 12-31 |
| OUT-BRAKE (approved today as a study) | Possible system-wide cost-in stop | Category B unless it adds an NM-ETF-specific block (A) |
| C3-EPOCH Friday windows (11-20, 11-27*, 12-4, 12-11, 12-18, 12-24/12-31) | Other Primary changes | Category B; logged per §6 (*11-27 is a half day) |
| Descendants in the testing arena (WB1, WB4, ETFDISP, ULT-22/14/HV2) | Separate setups | Never counted; promotion to Primary in the window = A4 |
| beginner_1120 admissions (eff. 11-23, Testing B/F) | None | n/a |

### 8. Daily tracking query
Read-only; run from the repo root with `PYTHONPATH=.`. Saved at `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_scratch/nmetf/track.py`. On 11-11..11-19 it reproduces the baseline: n 15, t 1.18, share 66%, w/o best +0.034.
```python
import sqlite3, subprocess, sys, tempfile
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
SETUP, START, END = "NM-ETF-late-dip-di-long", (sys.argv[1:2] or ["2026-11-23"])[0], (sys.argv[2:3] or ["2026-12-31"])[0]
raw = subprocess.run(["git", "show", "origin/mcf-data:journal.db"], capture_output=True, check=True).stdout
with tempfile.NamedTemporaryFile(suffix=".db") as f:
    f.write(raw); f.flush(); con = sqlite3.connect(f.name)
    t = pd.read_sql("SELECT strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj, r_multiple, exit_reason "
                    "FROM trades WHERE run_id=1 AND exit_time IS NOT NULL AND strategy=?", con, params=(SETUP,))
    sg = pd.read_sql("SELECT day, status, reason FROM signals WHERE run_id=1 AND strategy=?", con, params=(SETUP,))
    con.close()
t["date"] = t["date"].astype(str).str[:10]
t = t[(t.date >= START) & (t.date <= END)].copy()
t["r"] = cost_r_lr8(t, load_config()).astype(float)
sg = sg[(sg.day >= START) & (sg.day <= END)]
d = t.groupby("date").r.agg(["size", "sum", "mean"]); n, D = len(t), len(d)
tday = d["mean"].mean() / (d["mean"].std(ddof=1) / np.sqrt(D)) if D > 1 else float("nan")
best = d["sum"].idxmax() if D else None
wo = t[t.date != best].r.mean() if D > 1 else float("nan")
share = d["sum"].max() / t.r.sum() if n and t.r.sum() > 0 else float("nan")
print(d.round(3).to_string())
print(f"{SETUP} {START}..{END}: n={n} traded_days={D} totR={t.r.sum():+.2f} avgR={t.r.mean():+.3f} t_day={tday:.2f} "
      f"best={best} share={share:.0%} avgR_wo_best={wo:+.3f} | signals by status: {sg.status.value_counts().to_dict()}")
print("PASS" if (tday >= 2 and wo > 0 and share < 0.5) else "not passing (yet)", "- bars: t_day>=2, w/o best>0, share<50%")
```

**Daily integrity check** (any diff = a Category A alert):
- `sha256sum research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py` must give `6c47c7ec8c7723ed…`.
- `git log --since=2026-11-21 -- research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py mcf/research/arena/indicators.py` should show nothing.
- The block hash of `strategies.NM-ETF-late-dip-di-long` must be 59dc73e86a810174.
- NM-ETF must be first in Primary's `live.setup_order`.

---

## Recommendation
- **Approve OUT-NMETF v1 as written.** Make it effective from session 2026-11-23 and freeze it before the open. Record it in `research/ledger.jsonl` (kind `research`, no config change) with the hashes above.
- **Say explicitly in the yes** that the PASS size-up (risk 0.5% plus 2 slots) is an approved one-setup exception to C3-BAR2's flat-risk clause.
- **Keep expectations honest.** Primary's own record is +0.075R with a `1 day` tag. The test is fair to the setup at the whole-record edge (~80–88% pass chance) but likely fails if the Primary-era level holds (~20%).
- **Lineage caveat.** The lineage N is unknown: it was a swarm1017 near-miss, chosen after locked look 1. Its 2-year valid period was about +0.03R and 2026Q2 was −0.16R. A pass is evidence for this one forward window, not proof of a durable edge.

## Configurations counted
- **New trading configurations tried: 0.** The frozen test is N = 1.
- **Statistics computed:**
  - 3 record slices (Primary, pre-Primary, whole);
  - 15 power grid points;
  - 1 tracker reproduction check.
- **Lineage try count:** not recorded (outsider_1120 qa.json). Treat the lineage N as unknown or large.

Files: `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_scratch/nmetf/track.py`, `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_scratch/nmetf/base.py`. The temporary journal copy was deleted; scratch is 12 KB.

---

## Addendum 2026-11-27: AV50 splits the record (not part of the frozen text above)

Educational only — not financial advice.

- **What changed:** owner ETF-STOP50 yes (2026-11-24, variant AV50), skeptic cleared it 2026-11-27 (research/etfstop_1123/SKEPTIC_1127.md). From session **2026-11-30**, NM-ETF burst lots (A + B >= 4 by decision bar, see `mcf/burst_tight.py`) get half the stop distance when SPY's m-1 close is below its session VWAP. Shares, target and the R basis (the original stop) are unchanged. Ledger `2026-11-30-etf-stop50-av50`.
- **Protocol status:** this edits the frozen block (§6 A1, an exit change), so by the letter of §6 it would void the test. By owner instruction it is handled as a **split**, not a void, and flagged in every report:
  - **Segment 1:** 2026-11-23..2026-11-25 (3 eligible sessions, unchanged exit).
  - **Segment 2:** 2026-11-30 onward (AV50 exit): the remaining 22 eligible sessions to 2026-12-31; the extension rules of §2 are unchanged.
  - **Scoring:** bars (a)-(c) are computed on segment 2 and on the whole window; both are reported, with the split named. NMETF-SIZE's "pass" must say which one it rests on; the owner decides.
- **Integrity check:** from 2026-11-30 the block hash 59dc73e86a810174 is superseded by the block that carries `burst_tight_stop` (the module and `indicators.py` are unchanged; their hashes still apply).
- **Tracker:** run the §8 query twice: `track.py 2026-11-23 2026-11-25` and `track.py 2026-11-30 2026-12-31`. Note that R stays in original risk units: a tight lot stopped out books about -0.5R.

