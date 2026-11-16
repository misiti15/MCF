# Workbench results: Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (`CWT14-failbrk-pdl-p10-lowvol-long`)
Mechanic, 2026-11-16, built after the close. Research files only: no config changed, nothing deployed. Educational only — not financial advice.

## Verdict
Parent and copies were run through the identical pipeline. The parent's live record is NOT used in the decision; it is used for diagnosis only (DIAGNOSIS.md).

| Copy | Change | Replay avg R | 2-year avg R | W/o best day (replay / 2y) | Worst day R (replay / 2y) | Trades (replay / 2y) | Verdict |
|---|---|---|---|---|---|---|---|
| parent | — | -0.079 | -0.114 | -0.104 / -0.118 | -19.1 / -86.4 | 1263 / 25439 | — |
| `...-WB1` | P19 stop 0.25 -> 0.45 x ATR, target unchanged (+0.125 ATR) | -0.047 | -0.058 | -0.062 / -0.060 | -16.8 / -54.0 | 1263 / 25439 | PASS |
| `...-WB2` | P1 intake: gap <= -0.5% | -0.059 | -0.110 | -0.090 / -0.117 | -16.5 / -40.6 | 634 / 9819 | PASS (narrowly: the 2-year gain is +0.004R and valid is -0.115 vs -0.113) |
| **`...-WB3`** | **WB1 + WB2** | **-0.034** | **-0.046** | **-0.053 / -0.050** | **-11.4 / -34.4** | 634 / 9819 | **PASS — recommended** |
| alt (not spawned) | WB3 + reclaim >= 0.05 ATR | -0.033 | -0.042 | -0.051 / -0.047 | -4.6 / -11.7 | 280 / 4301 | pass; not chosen (halves trades again; the reclaim part is neutral over 2 years, paired +0.000R) |
| alt (not spawned) | stop 0.60 ATR + gap <= -0.5% | -0.031 | -0.029 | -0.046 / -0.032 | -10.1 / -27.2 | 634 / 9819 | pass; not chosen (target = 0.21 of a 0.60 ATR stop; the extra gain is mostly the denominator; replay -7.1 bps vs WB3 -6.4) |
| sibling WB5 parts | cost/R <= 0.10 + SPY since 09:50 >= -0.20% + stop 0.45 / target 0.15 ATR | -0.070 | -0.046 | -0.091 / -0.049 | -12.2 / -27.2 | 643 / 12551 | beats the parent, but replay far below WB3; not used |

**Pass rule (RULES.md clarification 2026-11-16):**
- The copy meets or exceeds the parent's avg R after costs in both tests.
- It is not worse on w/o best day or worst day by more than 0.02R / 10%.

WB3 beats the parent on every one of these, in both tests and in both 2-year halves. It also beats WB1 and WB2 on every column.

**Read this before deploying: WB3 still loses after costs in both tests** (-0.034R replay, -0.046R over 2 years). It is better than the parent, not profitable.
- **Day type, 2-year (up / flat / down):** parent -0.004 / -0.105 / -0.231 -> WB3 +0.051 / -0.068 / -0.165.

## Configurations counted: 104
Counted as: parent + 43 one-part configs + 57 combinations + gap plateau -0.3 / -0.75 + WB2 alone.
- **One-part configs (43):**
  - 24 intake / timer / sensor / gate configs on base exits.
  - 19 exit configs: target 0.10 / 0.175 / 0.25 ATR, stop 0.20 / 0.375 / 0.45 / 0.60 ATR with targets, max hold 60 / 120, flat 13:30, levels from the fill, +3 min latency, breakeven.
- **Combinations (57):** 4 rounds, in `configs_combos.csv`.
- **Bar:** max(1.5, sqrt(2 ln 104)) = **3.05**, reported only; it is no longer a pass hurdle. Paired by day vs the parent:
  - WB3: t 3.47 over 2 years (clears the bar), t 1.0 on the 22-session replay (does not).
  - WB1: t 6.35 / 1.55.
  - WB2: t -1.59 / -0.06.
- **What the WB2 t says:** the gap intake's gain is day mix, not better trades on a given day (DIAGNOSIS.md).
- **Gap plateau on the wider stop, 2-year / replay:**

  | Gap cut | 2-year | Replay |
  |---|---|---|
  | -0.3% | -0.048 | -0.041 |
  | -0.5% | -0.046 | -0.034 |
  | -0.75% | -0.034 | -0.044 |
  | -1.0% | -0.024 | -0.042 |

  -0.5% is the best on the replay and no edge case. Deeper cuts are better over 2 years and worse on the replay.

**Failures and not-kept configs** (full tables below; parent 2-year -0.114 / replay -0.079):
- **Exits:**
  - Tighter stop 0.20 ATR: -0.163 / -0.108.
  - Target 0.175 / 0.25 ATR: -0.119 / -0.141 over 2 years.
  - Target 0.10 ATR: -0.110 / -0.095.
  - +3 min fill: -0.251 (the setup is very fill-sensitive).
  - Max hold 60 / 120, flat 13:30 and levels from the fill: all within ±0.004 of the parent over 2 years.
  - Breakeven on the wide stop: -0.064 vs -0.058.
- **Timer:**
  - End 12:00 / 13:00 / 11:00: -0.116 / -0.114 / -0.113 over 2 years. The live afternoon loss is not confirmed.
  - Start 10:00: -0.123.
- **Sensors:**
  - Poke 0.15 / 0.08 ATR: -0.120 / -0.121.
  - Lowvol off: -0.114 (replay -0.095).
  - Below-VWAP, RSI(5) <= 30, range <= 1.2 ATR, reclaim <= 0.10: within ±0.016 and mixed.
  - Gap >= 0: -0.113 / -0.132.
- **Intake that passed alone but was not kept:**
  - ADV >= $150M: -0.104 / -0.064. On the wider stop it adds nothing: -0.057 / -0.041 vs -0.058 / -0.047, and combined with the gap and reclaim parts it is worse.
  - ATR% >= 2.0: -0.092 / -0.085 (replay worse).
  - Cost/R <= 0.10: -0.080 / -0.083. On the wider stop, -0.046 / -0.068 (replay worse).
  - Cost/R <= 0.05: -0.029 / -0.066 on the wider stop (replay worse).
- **Gates after 09:50:**
  - SPY since 09:50 >= -0.20%: -0.116 / -0.064.
  - SPY >= 0: -0.104 / -0.044.
  - SPY >= VWAP: -0.107 / -0.052.
  - SPY range position >= 0.3: -0.108 / -0.048.
  - All are weaker than the gap intake on the wider stop (-0.053 / -0.035 at best), and stacking them on WB3 lowers the 2-year result (-0.052 / -0.053).

## The tests (identical for parent and copies)
- **Replay of the live sessions:** 2026-10-12..11-10, 22 sessions. 11-11..11-16 have no 1-minute bars cached; fetching is after-hours only.
  - Signals come from the research/history2y lab frames up to 11-04, and from the sibling job's rebuilt frames (same setup_lab pipeline) for 11-05..11-10.
  - Parity on 11-02..11-04: 186 of 186 rebuilt signals are identical. 69 stored signals are of symbols missing from the team day files.
  - Isolated run: no caps, latches or quote checks. That gives 1,263 trades against 315 live in those sessions; P14 quote checks blocked 25% of live signals.
- **2-year backtest:** 2024-10-01..2026-10-09, 427 sessions.
  - **The locked block 2024-11-01..2025-02-28 was never read.** Frames come from the open months; 1-minute rows inside the block are dropped on read; an assert checks the signals.
  - Train = ..2025-12-31, valid = 2026-01-01..10-09.
- **Engine** (as `research/workbench/CWT14-failbrk-orl-p10-long/code2/sim2.py`):
  - Signal: `cwt_live_lib.b3(level='PD', p=0.10, lowvol=True, side='long')`, point-in-time ADV20 >= $95M, price >= $5, ATR >= 1%, window 09:50-15:00 on the 5-minute bar close, first qualifying bar per symbol-day.
  - Fill: open of the 1-minute bar one minute after the signal bar closes.
  - Stop and target are set from the signal close. When stop and target hit in the same minute, the stop counts first. Flat at 15:55.
  - R = net P/L / |fill - stop| (the live definition).
- **Costs: LR8 model** (sibling code) for every config.
- **Code:** `code/`:
  - sig.py: signals
  - ctx.py: SPY state after 09:50
  - sim.py: 1-minute exits
  - ana.py, exp.py, combo.py, final.py: scoring
  - live.py, livecomp.py: live trades
- **Numbers:** `results.csv` (the final side by side), `configs_onepart.csv`, `configs_combos.csv`.

## Side by side (avg R after costs)
| Test | Copy | Trades | Win % | Avg R | W/o best day | W/o worst day | Worst day | Avg win / loss | $-weighted (bps per $ traded) | Paired vs parent (t) |
|---|---|---|---|---|---|---|---|---|---|---|
| replay | parent | 1263 | 66.3 | -0.079 | -0.104 | -0.067 | -19.1 | +0.443 / -1.109 | -5.4 | — |
| replay | WB1 | 1263 | 73.2 | -0.047 | -0.062 | -0.034 | -16.8 | +0.244 / -0.841 | -8.0 | +0.027 (1.55) |
| replay | WB2 | 634 | 67.5 | -0.059 | -0.090 | -0.035 | -16.5 | +0.437 / -1.089 | -3.4 | -0.003 (-0.06) |
| replay | **WB3** | 634 | 73.8 | **-0.034** | -0.053 | -0.016 | -11.4 | +0.244 / -0.816 | -6.4 | +0.028 (1.00) |
| 2-year | parent | 25439 | 62.7 | -0.114 | -0.118 | -0.111 | -86.4 | +0.477 / -1.105 | -7.4 | — |
| 2-year | WB1 | 25439 | 70.7 | -0.058 | -0.060 | -0.056 | -54.0 | +0.253 / -0.807 | -6.8 | +0.054 (6.35) |
| 2-year | WB2 | 9819 | 63.2 | -0.110 | -0.117 | -0.107 | -40.6 | +0.466 / -1.099 | -6.8 | -0.030 (-1.59) |
| 2-year | **WB3** | 9819 | 71.3 | **-0.046** | -0.050 | -0.043 | -34.4 | +0.257 / -0.799 | -5.8 | +0.046 (3.47) |

**Train / valid split:**

| Copy | Train | Valid |
|---|---|---|
| parent | -0.115 | -0.113 |
| WB1 | -0.060 | -0.056 |
| WB2 | -0.104 | -0.115 |
| WB3 | -0.043 | -0.049 |

**Exit mix, 2-year:**

| Copy | Target | Stop | Time |
|---|---|---|---|
| parent | 64% | 33% | 3% |
| WB3 | 73% | 17% | 10% |

Median hold is 18-19 minutes for both.

## Supervisor sign-off — WB3
- **What changed (vs the parent):**
  1. Brakes: the stop sits at 0.45 x daily ATR under the signal close instead of 0.25. The target is unchanged in price (+0.125 x ATR).
  2. Intake: only names that opened at least 0.5% below yesterday's close.

  Signal, window 09:50-15:00, first bar per symbol-day, ADV floor and the 15:55 flat are unchanged.
- **Why:**
  - The 0.25 ATR stop sat inside the noise: 33% of trades stopped, and 38% of those reached the target later the same day; 29 of 120 live stops had first been at least +0.3R.
  - Poke-and-reclaims of yesterday's low in names that gapped down are the ones that hold, mostly on days the market recovers.
- **Overall before -> after (parent -> WB3):**
  - Avg R: replay -0.079 -> -0.034; 2-year -0.114 -> -0.046 (train -0.115 -> -0.043, valid -0.113 -> -0.049).
  - W/o best day: -0.104 -> -0.053 (replay), -0.118 -> -0.050 (2-year).
  - Worst day: -19.1 -> -11.4R (replay), -86.4 -> -34.4R (2-year).
  - Win %: 66 -> 74% (replay), 63 -> 71% (2-year).
  - Loss per dollar traded, 2-year: -7.4 -> -5.8 bps.
  - Better on every 2-year day type.
- **Where it gives a little back:**
  - **About 61% fewer trades:** 2-year 60 -> 23 per session; replay 57 -> 29.
  - **Average win in R halves** (+0.48 -> +0.26R), because the stop is wider.
  - **Per dollar traded the replay is slightly worse** (-5.4 -> -6.4 bps). The replay R gain is partly the bigger R denominator; the 2-year per-dollar gain is real.
  - **Up-gap and flat-open reversal names are dropped.** On this evidence that includes 4 of the 5 best live trades (TEVA, PPL, UBER, IP), and only 1 of the 3 scorable worst (RIG).
  - **The gap intake's gain is day mix, not better trades on a given day** (paired vs WB1 by day -0.009R). It works like an up-day tilt known at the open.
  - **Still negative after costs in both tests.**
- **Rule-change context:**
  - The live window 10-12..11-16 holds the Testing 2 -> Primary move (10-21), the Primary -> Testing 2 move and resize (10-28), the Primary -2R latch (10-29), LR1 / LR3 / LR5 / LR7 / LR8 (11-12) and the move to Testing D (11-12).
  - The backtests run with fixed rules (no caps, no latches, LR8 costs), so none of these affect the verdict.

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session. One copy only: **WB3**, which contains WB1 and WB2; deploying those too would run twins. The parent stays in Testing D, unchanged.

**Account choice: Testing F** (`config/account_testingf.yaml`).
- Not the parent's account (twins rule).
- No CWT14 setup runs there.
- Testing E is left for the GEN-261026-03 copy recommended today.
- Testing A-F carry equal weight.

1. **Module:** copy `research/workbench/CWT14-failbrk-pdl-p10-lowvol-long/modules/CWT14-failbrk-pdl-p10-lowvol-long-WB3.py` to `research/bdi/cwt/live/CWT14-failbrk-pdl-p10-lowvol-long-WB3.py`. GEOM "S" with `stop_price` / `target_price`, the same path as the ORL WB5 module.
2. **Config:** in `config/account_testingf.yaml` under `strategies:` add
   ```yaml
   CWT14-failbrk-pdl-p10-lowvol-long-WB3:
     # Workbench copy of CWT14-failbrk-pdl-p10-lowvol-long (Testing D), Mechanic 2026-11-16: stop 0.45 ATR (target +0.125 ATR) + gap <= -0.5% intake;
     # research/workbench/CWT14-failbrk-pdl-p10-lowvol-long/RESULTS.md.
     enabled: true
     type: lab
     module: research/bdi/cwt/live/CWT14-failbrk-pdl-p10-lowvol-long-WB3.py
     min_adv: 95000000
     window: [950, 1500]
     scale_out_r: null
     live_scale_out: false
     tags: [workbench, "parent:CWT14-failbrk-pdl-p10-lowvol-long"]
   ```
   Then put it FIRST in `live.setup_order` (RULES.md 5).
3. **Setup name:** in `config/setup_names.yaml` add `CWT14-failbrk-pdl-p10-lowvol-long-WB3: {name: "Failed Prior-Day-Low Break Long (0.1 ATR, low vol) — WB3: stop 0.45 ATR + gap-down >= 0.5%", side: long, what: "as the parent, stop 0.45 x daily ATR under the signal close (target unchanged +0.125 ATR), only names that opened >= 0.5% below yesterday's close"}`.
4. **Ledger:** in `research/ledger.jsonl`:
   - id: `2026-11-16-wb-cwt14-pdl-p10-lowvol-wb3`
   - title: "Workbench copy CWT14-failbrk-pdl-p10-lowvol-long-WB3 added to Testing F, first in setup_order (Mechanic pass)"
   - effective: the next session
   - patch: `{"strategies.CWT14-failbrk-pdl-p10-lowvol-long-WB3 (testingf)": [null, "added, enabled"], "live.setup_order (testingf)": ["...", "WB3 first"]}`
   - evidence: this file
   - approved_by: "owner rule research/workbench/RULES.md 5"

   Then run `python -m mcf.research.ledger check`.
5. **Finish:** run `python -m mcf.report.assignments` (in the same commit), then `pytest -q`. Commit and push after 16:05 ET (setup-freeze).

---
## Full config tables
### One-part configs (base exits unless EX)

| Config | 2y avg R | replay avg R | train / valid | 2y trades | worst day 2y / replay |
|---|---|---|---|---|---|
| EX F1330 | -0.116 | -0.085 | -0.117 / -0.115 | 25439 | -89.1 / -18.9 |
| EX FA | -0.111 | -0.071 | -0.114 / -0.108 | 25439 | -70.8 / -18.5 |
| EX L4 | -0.251 | -0.099 | -0.200 / -0.299 | 25439 | -1784.0 / -25.8 |
| EX MH120 | -0.113 | -0.077 | -0.114 / -0.111 | 25439 | -87.0 / -19.9 |
| EX MH60 | -0.113 | -0.082 | -0.118 / -0.107 | 25439 | -85.4 / -17.8 |
| EX S20 | -0.163 | -0.108 | -0.172 / -0.155 | 25439 | -101.6 / -20.5 |
| EX S30T15 | -0.103 | -0.062 | -0.112 / -0.095 | 25439 | -72.8 / -20.9 |
| EX S375 | -0.073 | -0.051 | -0.076 / -0.070 | 25439 | -64.7 / -17.7 |
| EX S45 | -0.058 | -0.047 | -0.060 / -0.056 | 25439 | -54.0 / -16.8 |
| EX S45BE | -0.064 | -0.057 | -0.069 / -0.059 | 25439 | -53.3 / -13.8 |
| EX S45F1330 | -0.058 | -0.049 | -0.060 / -0.055 | 25439 | -59.5 / -15.0 |
| EX S45MH120 | -0.055 | -0.043 | -0.056 / -0.054 | 25439 | -59.2 / -15.4 |
| EX S45T10 | -0.056 | -0.054 | -0.058 / -0.053 | 25439 | -50.5 / -14.7 |
| EX S45T15 | -0.060 | -0.046 | -0.062 / -0.058 | 25439 | -54.2 / -17.7 |
| EX S60 | -0.042 | -0.036 | -0.044 / -0.040 | 25439 | -44.1 / -12.8 |
| EX S60T15 | -0.043 | -0.033 | -0.045 / -0.041 | 25439 | -46.5 / -14.1 |
| EX T10 | -0.110 | -0.095 | -0.112 / -0.108 | 25439 | -78.8 / -19.3 |
| EX T175 | -0.119 | -0.088 | -0.122 / -0.116 | 25439 | -90.4 / -27.1 |
| EX T25 | -0.141 | -0.101 | -0.154 / -0.129 | 25439 | -92.3 / -29.1 |
| G SPY rpos>=0.3 | -0.108 | -0.048 | -0.108 / -0.108 | 16520 | -44.9 / -12.7 |
| G SPY since0950>=-0.20 | -0.116 | -0.064 | -0.116 / -0.115 | 21106 | -47.8 / -15.5 |
| G SPY since0950>=0 | -0.104 | -0.044 | -0.100 / -0.107 | 15122 | -44.9 / -15.2 |
| G SPY>=VWAP | -0.107 | -0.052 | -0.107 / -0.107 | 14814 | -41.1 / -14.7 |
| P1 ATR%<=4.0 | -0.130 | -0.077 | -0.127 / -0.134 | 19367 | -55.8 / -14.7 |
| P1 ATR%>=1.5 | -0.106 | -0.077 | -0.104 / -0.108 | 23714 | -79.6 / -19.3 |
| P1 ATR%>=2.0 | -0.092 | -0.085 | -0.085 / -0.097 | 19503 | -65.4 / -17.9 |
| P13 cost/R<=0.10 | -0.080 | -0.083 | -0.074 / -0.084 | 15127 | -52.2 / -15.7 |
| P2 ADV>=150M | -0.104 | -0.064 | -0.101 / -0.107 | 18576 | -62.6 / -17.8 |
| P3 price>=10 | -0.112 | -0.077 | -0.114 / -0.110 | 25190 | -83.7 / -16.1 |
| P5 end 11:00 | -0.113 | -0.064 | -0.110 / -0.117 | 19668 | -89.0 / -14.7 |
| P5 end 12:00 | -0.116 | -0.072 | -0.115 / -0.117 | 22591 | -88.7 / -18.2 |
| P5 end 13:00 | -0.114 | -0.081 | -0.114 / -0.115 | 23917 | -85.9 / -19.4 |
| P5 start 10:00 | -0.123 | -0.079 | -0.133 / -0.113 | 21088 | -69.9 / -18.9 |
| P8 below VWAP | -0.116 | -0.090 | -0.116 / -0.116 | 11988 | -44.7 / -18.8 |
| P8 gap<0 | -0.115 | -0.057 | -0.119 / -0.110 | 16849 | -70.3 / -18.2 |
| P8 gap>=0 | -0.113 | -0.132 | -0.106 / -0.119 | 8590 | -46.5 / -14.4 |
| P8 lowvol off | -0.114 | -0.095 | -0.114 / -0.114 | 39100 | -133.1 / -28.5 |
| P8 poke 0.08 | -0.121 | -0.104 | -0.120 / -0.122 | 33114 | -97.5 / -26.4 |
| P8 poke 0.15 | -0.120 | -0.093 | -0.115 / -0.125 | 13242 | -63.9 / -15.7 |
| P8 range<=1.2ATR | -0.111 | -0.073 | -0.110 / -0.113 | 24575 | -86.7 / -18.2 |
| P8 reclaim<=0.10 | -0.111 | -0.087 | -0.107 / -0.115 | 22160 | -60.9 / -20.7 |
| P8 reclaim>=0.05 | -0.106 | -0.035 | -0.119 / -0.093 | 10806 | -47.8 / -7.0 |
| P8 rsi5<=30 | -0.098 | -0.117 | -0.101 / -0.096 | 4109 | -16.3 / -9.4 |
| parent | -0.114 | -0.079 | -0.115 / -0.113 | 25439 | -86.4 / -19.1 |

### Combinations

| Config | 2y avg R | replay avg R | train / valid | 2y trades | worst day 2y / replay |
|---|---|---|---|---|---|
| A+c05 | -0.038 | -0.073 | -0.019 / -0.048 | 5874 | -23.6 / -7.9 |
| A+g1 | -0.076 | -0.065 | -0.069 / -0.081 | 5454 | -35.6 / -15.4 |
| A+rc | -0.106 | -0.035 | -0.119 / -0.093 | 10806 | -47.8 / -7.0 |
| S45+adv | -0.057 | -0.041 | -0.055 / -0.058 | 18576 | -39.5 / -12.0 |
| S45+c05 | -0.029 | -0.066 | -0.024 / -0.032 | 5874 | -16.5 / -7.1 |
| S45+c07 | -0.041 | -0.073 | -0.040 / -0.042 | 10383 | -25.3 / -10.3 |
| S45+g05 | -0.046 | -0.034 | -0.043 / -0.049 | 9819 | -34.4 / -11.4 |
| S45+g05+c12 | -0.036 | -0.044 | -0.030 / -0.040 | 7088 | -26.0 / -9.1 |
| S45+g05+g20 | -0.053 | -0.020 | -0.047 / -0.058 | 8548 | -34.2 / -9.2 |
| S45+g05+grp | -0.052 | -0.015 | -0.043 / -0.059 | 7109 | -33.5 / -9.1 |
| S45+g05+grp+rc | -0.051 | -0.041 | -0.053 / -0.050 | 3178 | -14.0 / -4.9 |
| S45+g05+gvw | -0.052 | -0.020 | -0.050 / -0.054 | 6391 | -30.9 / -9.8 |
| S45+g05+rc | -0.042 | -0.033 | -0.048 / -0.036 | 4301 | -11.7 / -4.6 |
| S45+g1 | -0.024 | -0.042 | -0.017 / -0.029 | 5454 | -20.7 / -9.0 |
| S45+g1+rc | -0.028 | -0.048 | -0.033 / -0.024 | 2443 | -9.5 / -4.5 |
| S45+gp | -0.053 | -0.036 | -0.055 / -0.051 | 16849 | -46.8 / -13.6 |
| S45+gp+c10 | -0.040 | -0.053 | -0.037 / -0.042 | 10151 | -26.9 / -10.6 |
| S45+gp+c12 | -0.041 | -0.052 | -0.040 / -0.042 | 11610 | -36.3 / -10.2 |
| S45+gp+rc+c12 | -0.042 | -0.037 | -0.044 / -0.040 | 5036 | -21.4 / -4.2 |
| S45+grp | -0.053 | -0.035 | -0.050 / -0.056 | 16520 | -38.7 / -11.1 |
| S45+grp+c12 | -0.040 | -0.052 | -0.036 / -0.042 | 11302 | -34.1 / -9.4 |
| S45+grp0.2 | -0.054 | -0.035 | -0.053 / -0.055 | 17666 | -56.6 / -11.1 |
| S45+grp0.5 | -0.051 | -0.036 | -0.047 / -0.054 | 14061 | -33.4 / -11.1 |
| S45+r03 | -0.055 | -0.043 | -0.060 / -0.051 | 15530 | -38.7 / -12.3 |
| S45+r08 | -0.061 | -0.043 | -0.068 / -0.055 | 6173 | -21.2 / -5.9 |
| S45+rc | -0.057 | -0.030 | -0.061 / -0.053 | 10806 | -31.7 / -6.3 |
| S45+rc+adv | -0.059 | -0.031 | -0.057 / -0.061 | 7765 | -22.7 / -5.8 |
| S45+rc+c12 | -0.047 | -0.031 | -0.050 / -0.045 | 7437 | -22.8 / -5.2 |
| S45+rc+g20 | -0.058 | -0.041 | -0.062 / -0.054 | 9114 | -17.5 / -6.2 |
| S45+rc+gp | -0.049 | -0.038 | -0.053 / -0.045 | 7230 | -27.4 / -5.6 |
| S45+rc+grp | -0.054 | -0.046 | -0.056 / -0.053 | 7180 | -16.7 / -7.2 |
| S45+rc+p10 | -0.056 | -0.029 | -0.061 / -0.052 | 10728 | -32.2 / -6.3 |
| S45BE+rc | -0.064 | -0.041 | -0.071 / -0.057 | 10806 | -31.2 / -6.9 |
| S45MH120+rc | -0.054 | -0.020 | -0.059 / -0.049 | 10806 | -32.3 / -5.8 |
| S45T15+c08 | -0.043 | -0.074 | -0.043 / -0.043 | 12235 | -29.3 / -11.6 |
| S45T15+c10 | -0.046 | -0.068 | -0.049 / -0.044 | 15127 | -32.7 / -12.2 |
| S45T15+c10+adv | -0.049 | -0.073 | -0.049 / -0.048 | 11728 | -29.1 / -10.8 |
| S45T15+c10+g20 | -0.046 | -0.070 | -0.050 / -0.043 | 12551 | -27.2 / -12.2 |
| S45T15+c10+g20+adv | -0.049 | -0.075 | -0.053 / -0.046 | 9703 | -24.1 / -10.8 |
| S45T15+c10+g20+e12 | -0.046 | -0.064 | -0.052 / -0.041 | 11627 | -25.2 / -12.7 |
| S45T15+c10+g20+gp | -0.045 | -0.063 | -0.046 / -0.044 | 8721 | -26.4 / -10.6 |
| S45T15+c10+g20+rc | -0.045 | -0.046 | -0.054 / -0.037 | 5536 | -15.7 / -4.6 |
| S45T15+c10+gp | -0.042 | -0.068 | -0.042 / -0.042 | 10151 | -28.1 / -10.6 |
| S45T15+c10+grp | -0.042 | -0.066 | -0.042 / -0.043 | 9864 | -30.8 / -12.2 |
| S45T15+c10+grp+adv | -0.048 | -0.070 | -0.048 / -0.048 | 7665 | -27.6 / -10.8 |
| S45T15+c10+gvw | -0.045 | -0.078 | -0.045 / -0.044 | 8806 | -24.9 / -10.1 |
| S45T15+c10+rc | -0.047 | -0.038 | -0.054 / -0.041 | 6522 | -20.2 / -4.6 |
| S45T15+c12 | -0.046 | -0.063 | -0.047 / -0.046 | 17339 | -42.0 / -12.1 |
| S45T15+rc | -0.058 | -0.030 | -0.062 / -0.053 | 10806 | -32.5 / -6.0 |
| S60+c10+g20 | -0.032 | -0.049 | -0.035 / -0.030 | 12551 | -20.9 / -8.9 |
| S60+c10+grp | -0.027 | -0.041 | -0.027 / -0.028 | 9864 | -25.1 / -8.1 |
| S60+g05 | -0.029 | -0.031 | -0.027 / -0.031 | 9819 | -27.2 / -10.1 |
| S60+rc | -0.041 | -0.029 | -0.046 / -0.037 | 10806 | -26.2 / -4.9 |
| X1 S45T15 | -0.060 | -0.046 | -0.062 / -0.058 | 25439 | -54.2 / -17.7 |
| X2 S60 | -0.042 | -0.036 | -0.044 / -0.040 | 25439 | -44.1 / -12.8 |
| X3 S375 | -0.073 | -0.051 | -0.076 / -0.070 | 25439 | -64.7 / -17.7 |
| X4 S45 | -0.058 | -0.047 | -0.060 / -0.056 | 25439 | -54.0 / -16.8 |
| parent | -0.114 | -0.079 | -0.115 / -0.113 | 25439 | -86.4 / -19.1 |

Educational only — not financial advice.
