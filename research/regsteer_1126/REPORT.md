Educational only — not financial advice
# REGSTEER-1126: C's REGSTEER-1 protocol for steering Primary by regime (research only; nothing changed)
Pre-registered: PREREG.md (sha256 f5717830…882, addendum A before any score). The owner's 11-26 request lifts the rule-26 guard for this research. Configs tried: 1 (Step 1) + 6 (Step 2, side-level only, per the gate) = 7. Lineage N corrected from C's ~400 to ~8,891 (market-context gates 4,129 on file + compass_rd_1126's 4,762 cells), so the bar is t ≥ 4.26 (C's 3.46 is shown too). Locked block never read or scored. Engine: bench10 lots (unchanged; hold/holdtr added in a wrapper for the GEN contenders), Primary book rules, LIVE-L costs; base CHECK −3.20 / T2 −1.80 R/day against primshorts −3.03 / −1.75 (open marks not modelled).
**Verdict: FAIL. Do not build it.** Steering mostly turns off a losing list. It is not regime skill.
## Failures first
- **Step 1, rank agreement (bench vs live, 8 setups, 43 cells, 32 live sessions):** demeaned Spearman ρ = −0.08 (90% CI −0.30..+0.24); raw −0.17; per split T2 −0.09 / FIT +0.01 / CHECK +0.05; Primary 4 alone +0.27 (29 cells); contenders −0.51. Pooled aligned effects agree in sign in 4 of 9 cells (ρ −0.57). ρ is below 0.2, so the run **stopped at a side-level rule**: only the 6 pooled configs were scored and the hierarchical per-setup steering was not run. This is the third time labels fail to carry over (REGX 31% vs 32%).
- **Step 2, walk-forward:** monthly and expanding; 40 OOS months, 811 sessions, 18,024 base lots. Best config **S1 (SPY gap) pooled OFF**:
  - Excess over a random switch of the same share: **+0.073R/day, t 2.04** (needs ≥ +0.5R/day and t ≥ 4.26 / 3.46).
  - Against a constant cut to the same exposure (mean weight 0.148): +0.118R/day, t 1.23 (needs t ≥ 2). It does not beat a plain size cut.
  - **PBO 0.13** (passes). **Hansen SPA p 0.061**, White RC p 0.083 (fail). Deflated Sharpe ≈ 0 at both N = 2,271 and N = 8,897.
  - It passes both halves (+0.04 / +0.10), 24 of 40 months positive, worst-5 vs unsteered, and no setup worse by more than 2R/month (RW5 −0.11 vs constant). It fails the best-day share (13.7% against < 10%).
- **The other 5 configs:**
  - S1 OFF/HALF: +0.057 (t 1.81).
  - S2 (W60) OFF: +0.033 (t 1.05). S2 OFF/HALF: +0.034 (t 1.13; vs constant t 2.45).
  - S1+S2 OFF: −0.114 (t −2.35). S1+S2 OFF/HALF: −0.080 (t −1.99).
  - S2 sets L3 and RW3 weight to about 0 almost everywhere, because the rule cuts cells by their absolute mean and the shorts lose in nearly every cell.
## Goal metrics (OOS, Primary book; the steered book trades 4–30% of lots, so its red-day count mostly counts days it sat out)
| Book | Mean R/day | Red days / 21 | Worst-5 sum | Worst trailing-60 worst-5 | 20-session floor | Avg w/o best day |
|---|---|---|---|---|---|---|
| Unsteered | −2.73 | 12.8 | −215.3 | −194.1 | −257.6 | −2.80 |
| Constant cut 0.148 | −0.40 | 12.8 | −31.8 | −28.6 | −38.0 | −0.41 |
| S1 pooled OFF | −0.29 | 5.5 | −90.5 | −88.8 | −83.9 | −0.30 |
| S2 pooled OFF/HALF | −0.02 | 3.3 | −31.4 | −24.4 | −34.6 | −0.03 |
Every arm stays negative. The steered tails are no better than the size cut's, and S1's are worse.
## Compass point-in-time (information only; compass_info.json)
- **The W60 compass can be rebuilt point-in-time on the 2023–26 bench.** Checked against `compute()` itself: 300 of 300 marks match. The only proxy is breadth on 177 of the 200 Hunch names, the ones present in both caches. Against live `compute()` on 22 overlap days, levels match 96.7% and the confirmed side 98.5%.
- **First-confirmed side vs the close side:** right on 70.4% of 875 days, against a 53.3% base rate. Right in 41 of 43 months; by half-year 0.61–0.77. Median confirmation is 10:00. By confirmation time: ≤10:00 0.67 (488 days), 10:15–10:30 0.74, 10:45–11:30 0.77, 11:45–13:00 0.63, 13:15+ 0.82 (11 days).
- **Entries vs confirmation (REGSTEER rules):** 81.8% of base entries come after the day's first confirmation, and 57.4% have a confirmed side at the entry mark (27.9% aligned, 29.5% against). Even so, S2 adds no edge beyond the cut in exposure. The compass reads where the day stands, not the R that follows an entry (as compass_rd_1126 found).
## Caveats and rule-change context
- Live data is 10-06..11-25; 11-13 has no SPY gap row.
- GEN short contenders have no T2 lots, because their breadth context columns are missing from the T2 frames.
- Ledger changes inside the live window: 10-28 sizing, 10-29 −2R latch, 11-11 TEAM-6, 11-12 LR8/LR3, 11-17 TSZ1, 11-19 Epoch 1, 11-20 stop rounding, 11-21 cost-basis fix, 11-23 burst brake / ST7 out.
- Read for the owner: the lever is the edge per lot and the hedge or size balance (A's HEDGE-B, squeeze B8), not on/off by state. No DECISION draft. Scripts: rs_*.py.
