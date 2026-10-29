Educational only — not financial advice

# BDI p3_1029 (owner Prompt 3: funding-gate push): Primary loser autopsy, funding-gate math, 3 hypotheses on two years

*Live numbers are **paper** trades (rule 7) from Primary's journal (origin/mcf-data `journal.db`, run 1), sessions
2026-10-15..10-28 (10). Two-year numbers are **backtests** on the open history (train <= 2025-12-31, valid
2026-01-01..2026-10-07). Costs are in everywhere. **Configurations tried: 11** on two years (iteration 1 of the bounded loop;
iterations 2-3 were not needed). The lineage count adds 8 prior related configs (sat1024-late-profit-lock 6,
nightly-1027-flatten-1545 2), so **N = 19 and the bar is t >= 2.43** (`counts.json`). The grids were fixed in `PLAN.md`
before scoring. **One locked-block look** was taken, for finalist A3 (section 3). No config, setup, exit, twin group,
assignment or ledger entry was changed. Nothing was committed. Replays were not used as evidence.*

## Failures first
1. **Primary's 8 current setups lose money on two years after costs.** The portfolio sim gives −0.070R per trade
   (n 29,285, day-clustered t −4.60). Train −0.087R, valid −0.053R, up sessions −0.224R, down +0.053R. Only 4.6% of
   rolling 10-session windows pass the funding gate. Per setup: only ST7-FD (+0.022R) and NS1 (+0.029R) are above zero.
   MF2-FD −0.095R, MF4 −0.087R, MF4-FD −0.081R, RW3-FD −0.068R, RW5-FD −0.060R, NS5 −0.018R.
   The live record is far better: +0.451R on 203 trades. But 10-22 alone is 82% of that R.
2. **No hypothesis makes the book positive.** The best one (A3, a cost filter) still loses −0.026R on two years and
   −0.053R on the locked block.
3. **Type B (correlation caps) fails its gate.** All 4 caps lose R in down sessions. **Type C (late exits) fails.** It
   was also tiny live (−1.6R in 10 sessions).
4. **A3's two-year gain is cost avoidance, not better selection.** The trades it removes have the same gross edge as the
   ones it keeps (+0.012R vs +0.016R). Live, it would have hurt: current-8 trades with cost above 0.15R made +43.7R and
   +$471 over the 10 sessions, mostly on 10-22.
5. **Live type B, as measured, comes mostly from setups that have since left Primary:** NS2 on 10-15 and NS3-FD on
   10-21. For the current 8, type B was only 16 losers, −12.8R.

## 1. Autopsy: Primary's losers, 10-15..10-28 (`autopsy.py` → `autopsy_out.txt`, `losers.csv`)
489 trades, of which 216 lost (pnl_adj < 0): −200.0R, −$3,870.78. All trades together: +11.9R, −$33.24.
Each loser gets one type, checked in the order A → B → C → Other.

| type | definition | losers | R | $ | share of loser $ |
|---|---|---|---|---|---|
| A execution | stop filled > 2c/share beyond the stop, or the spread was within 80% of a spread gate (>= 24 bps or >= 20% of the stop distance) | 49 | −54.4 | −964 | 25% |
| B correlated | another Primary loser on the same symbol, or the same sector ETF and side, entered within 30 min | 99 | −95.6 | −2,017 | 52% |
| C late reversal | open at 15:30 at >= 0R (SIP 15:29 close), then lost by the stop or the 15:55 flatten | 9 | −1.6 | −26 | 1% |
| Other | | 59 | −48.3 | −864 | 22% |

- **Overlapping tags:**
  - A_slip: 43 losers, −$929.
  - A_spread: 16 losers, −$281.
  - B on the same symbol: 74 losers, −$1,185.
  - B on the same sector: 116 losers, −$2,436.
  - C: 13 losers, −$49.
- **Stop exits (all 158):** median 0.8c and mean 3.5c beyond the stop; 8.8% were more than 2c beyond. The slippage
  above 2c cost only $47 in all. So type A is mostly the spread or cost load, not bad fills.
- **Where type B was concentrated:**
  - 10-15: NS2 + RW6G1, 35 shorts across IGV, SOXX, XLK and XME, about −$1,100.
  - 10-21: NS3-FD and L3 on the crypto miners and software names.
  - 10-16 and 10-19: MF1/MF3/MF5 shorting the same name 2-3 times.
- **Current 8 setups only:** 54 losers, −43.3R, −$675. By type: A 10 (−10.7R), B 16 (−12.8R), C 3 (−0.4R), Other 25
  (−19.4R).

## 2. Funding-gate math (`autopsy_out.txt`, `gate_sim.py` → `gate_sim_out.txt`)
The gate is 7 of 10 sessions green, with no day above 50% of the 10-session net.

**Primary as it actually ran (live paper, after costs):**
- Green days: **3 of 10 in R, 4 of 10 in $**.
- Net: **−$33.24, +11.9R**.
- Best day 10-22: +$1,369 and +65.8R. That is 79% of the gross green $, and 552% of the net R. The net $ is negative,
  so a share of net $ cannot be computed. **The gate is failed on both counts.**

**Current 8 setups only (what Primary runs now):**
- 7 of 10 days green in R and in $; +91.6R, +$1,935.
- But 10-22 is 82% of the net: +74.8R and +$1,596. **This passes the 7-of-10 part and fails the 50% part.**
- Without 10-22: 115 trades, +0.146R per trade, +$339.

**What would pass.** The table gives P(pass) when daily R is normal with mean mu and standard deviation sd:

| mu \ sd | 1 | 2 | 3 | 4 | 6 |
|---|---|---|---|---|---|
| 0.5 | 0.55 | 0.28 | 0.21 | 0.18 | 0.15 |
| 1.0 | 0.93 | 0.54 | 0.36 | 0.29 | 0.21 |
| 2.0 | 1.00 | 0.93 | 0.71 | 0.55 | 0.36 |
| 3.0 | 1.00 | 1.00 | 0.93 | 0.78 | 0.54 |

- A pass chance of about 80% needs a daily mean of about **0.75× the daily sd**.
- The current 8 without 10-22 run at 1.69R/day with sd 3.14 (ratio 0.54). That gives **P(pass) ≈ 0.45**, from a
  trade bootstrap that treats trades as independent, which is optimistic.
- Reaching 0.80 needs about **+0.15R more per trade** (+0.30R per trade at ~11 trades/day: mu 3.4, sd 3.8).
- A day bootstrap of the 10 actual current-8 days passes 39% of the time. The miss is almost all the 50% rule, because
  of 10-22.
- **On two years**, the 8 setups pass 4.6% of rolling windows, and the best filter (A3) 5.8%.

## 3. Hypotheses on two years (`bt.py` signals, `evalp.py` → `eval1_out.txt` / `results.csv`; `decomp.py`)
**Setup of the test:**
- Portfolio sim of the 8 setups: setup_order priority, 3 same-side lots per symbol, no opposite side, 30 lots per setup
  and 77 in all.
- Path: 5-minute bars, stop checked first, flatten at 15:55.
- Not modelled: ST-P, and the spread / ETB skips.
- R is in live units (per unit of stop distance).
- My path simulation matches the frame outcome: corr 0.99, win flag agreement 100% (2025-06 check).

**Pass rule (fixed in PLAN.md):** paired daily delta t >= 2.43; delta > 0 in train, valid, up and down sessions; shrunk
avg R >= the parent's in train and valid.

| config | n | avg R | train / valid | delta R/day | delta t | delta train / valid | delta up / down | gate10 | pass |
|---|---|---|---|---|---|---|---|---|---|
| parent | 29,285 | −0.070 | −0.087 / −0.053 | | | | | 4.6% | |
| A1 stop distance >= $0.10/share | 28,408 | −0.056 | −0.070 / −0.043 | +1.07 | 8.12 | +1.19 / +0.91 | +0.99 / +1.31 | 4.6% | yes |
| A2 stop distance >= $0.15/share | 27,137 | −0.046 | −0.058 / −0.034 | +1.88 | 9.84 | +2.02 / +1.70 | +2.53 / +1.49 | 5.3% | yes |
| **A3 stop-exit cost <= 0.15R** | 21,426 | −0.026 | −0.035 / −0.018 | +3.49 | 8.17 | +3.76 / +3.15 | +6.51 / +0.55 | 5.8% | yes |
| B1 1 lot per symbol | 21,460 | −0.069 | −0.094 / −0.047 | +1.29 | 3.65 | +1.10 / +1.51 | +3.80 / **−0.97** | 4.8% | no |
| B2 1 entry per symbol per day | 20,670 | −0.071 | −0.097 / −0.046 | +1.35 | 3.38 | +1.08 / +1.67 | +4.07 / **−1.32** | 4.3% | no |
| B3 <= 2 same-side lots per sector | 18,060 | −0.065 | −0.085 / −0.045 | +2.02 | 3.12 | +1.98 / +2.07 | +5.02 / **−1.46** | 4.6% | no |
| B4 <= 3 entries per poll | 21,790 | −0.063 | −0.079 / −0.049 | +1.54 | 3.09 | +1.67 / +1.39 | +3.82 / **−0.12** | 4.6% | no |
| C1 flatten 15:45 | 29,285 | −0.070 | | +0.01 | 0.05 | +0.04 / −0.04 | | 4.1% | no |
| C2 flatten 15:30 | 29,285 | −0.069 | | +0.02 | 0.08 | +0.08 / −0.06 | | 4.1% | no |
| C3 15:00 stop tighten 0.5R | 29,285 | −0.071 | | −0.10 | −1.07 | | | 4.3% | no |
| C4 flatten 15:45, longs only | 29,285 | −0.070 | | −0.00 | −0.16 | | | 4.6% | no |

- **How to read the B rows:** the caps improve the total only because they cut trades from a losing book. In down
  sessions, where these shorts make their money, the caps cost R.
- **Why the loop stopped:** iteration 1 had passes, so the pre-declared loop stopped there.
- **Finalist chosen on valid:** A3.
- **Locked block, the one look** (2024-11-01..2025-02-28, `holdout.py` → `holdout_out.txt`; bar t >= 1.0 for look 1):
  - Parent: −0.112R, n 4,732.
  - A3: −0.053R, n 3,228.
  - Paired delta +4.46R/day, t 4.31. The delta is positive in both halves of the block and in up and down sessions.
  - **The improvement passes. The book stays negative.**
- **Plateau:** A1, A2 and A3 are all positive.
- **Why A3 works (`decomp_out.txt`):** the trades it removes have a gross edge of +0.012R and a cost of 0.199R. The
  trades it keeps have +0.016R and 0.045R. It removes 39% of MF2-FD's signals and 26-30% of MF4's.

## 4. Proposal (NOT applied): nightly "funding-gate tracker" section for the owner brief
```
### Funding gate (Primary, live paper, after costs) — last 10 sessions <first>..<last>
| | value | gate | status |
| green sessions (R after costs) | 7 / 10 | >= 7 | ok / short by k |
| green sessions ($ after costs) | 7 / 10 | (shown) | |
| net R / net $ | +91.6R / +$1,935 | > 0 | |
| best day share of net (R, $) | 82% (10-22) / 82% | <= 50% | FAIL |
| net without best day (R, $) | +16.8R / +$339 | (shown) | |
| needed to pass the next window | e.g. "2 more green days, and the net must grow by $X so 10-22 is <= 50%, or 10-22 must roll out (on 11-05)" |
| P(pass) next 10 (bootstrap of last 20 sessions' per-trade R, iid; and day bootstrap) | 0.45 / 0.39 | | |
| per-day mu / sd (R), needed mu at this sd for P(pass) 0.8 | 1.69 / 3.14 → ~2.4 | | |
Setups changed in the window: <list> (window mixes setup sets).
Educational only — not financial advice.
```
- **Computed from:** the journal (pnl_adj, R = pnl_adj / $ risk). It should also say the date the best day leaves the
  window.
- **"Needed $":** max(0, 2 × best day − net).
- **Scope:** both the actual Primary book and the current-setups-only view, labelled.
- **Housekeeping:** reporting only (rule 15), with no change to trading.
- **Script to adapt:** `gate_sim.py` holds the math.

## 5. Recommended owner decisions
1. **Do not expect the funding gate from these 8 setups as backtested.** They lose −0.070R on two years after costs. The
   live green streak rests on 10-22. Treat the 7-of-10 count as weak evidence until 10-22 rolls out of the window
   (11-05).
2. **A3, the cost filter:** decide whether to queue it for a forward paper test in Testing (backlog
   `p3-1029-cost-r-entry-filter`). It passed the bar and its one holdout look, but only as damage reduction. It would
   have cut +43.7R of live winners in the last 10 sessions. **Not for Primary now.**
3. **Correlation caps and late-exit variants (B / C):** mark them failed (backlog lines proposed). Do not add a 15:45
   flatten or a 15:00 stop tightening to Primary.
4. **Funding-gate tracker:** approve the section in §4 as a housekeeping addition to the nightly brief.

Proposed backlog lines: `backlog_proposed.jsonl` (3). No ledger entry.

Educational only — not financial advice.
