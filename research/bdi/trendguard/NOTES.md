# BDI trend-guard study: owner trend-trap rules as extra layers on the 23 re-scored setups

*Educational only - not financial advice. Lab results on the 2-year history only; nothing here is a live result.*

**Section 1 (pre-declaration) was written on 2026-10-09 03:51 UTC, before any configuration was scored.**
Results are appended below it in section 2 and are not allowed to change section 1.

Source: owner notes on the 10 worst trades of 2026-10-08 (`research/bdi/daily/2026-10-08/OWNER_NOTES.md`,
`owner_trendtrap_rules.jpg`) and the autopsy (`research/bdi/daily/2026-10-08/AUTOPSY.md`).

## 1. Pre-declaration

### 1.1 Data
- Two-year frames `research/history2y/data/frames` via `research/history2y/lib.py` (open months only). The rule-19 locked
  block 2024-11-01..2025-02-28 is never loaded: `MCF_HIST_ALLOW_LOCKED` is never set, `research/history2y/data/locked` is
  never read. The new indicators come from the 1-minute SIP cache `data/cache_hist/1Min` (the frames' own source);
  every row dated inside the locked block is dropped at load, before any computation.
- Sessions scored: the 426 open sessions of `lib.regimes()` (2024-10-01..2026-10-07 minus the locked block).
- Survivorship caveat as RESCORE.md (today's 1,226 names applied to the past).

### 1.2 Features (live parity: 5-minute bars, value known at the bar's close; tod = bar end, as the frames)
5-minute bars = `mcf.data.bars.resample(1-min, "5min")`, RTH, continuous across sessions (LabStrategy sees 40 prior
5-min bars plus today's; EMA/ADX here use the full prior series, a small warm-up difference noted for ADX).
- **VWAP** session-cumulative typical price x volume (as `mcf.research.heat.heat_frame`). **VWAP SD** volume-weighted:
  `sqrt(cum(v*tp^2)/cum(v) - vwap^2)`; bands `vwap +- k*SD`.
- **EMA9 / EMA21** of close (`ewm(span, adjust=False)`). Rising = `EMA[t] - EMA[t-3] > 0`; falling = `< 0`.
- **CMF(20)** = sum20(((c-l)-(h-c))/(h-l) * v) / sum20(v) (0 when h = l). Rising = `CMF[t] > CMF[t-3]`.
- **OBV** = cumsum(sign(c - c_prev) * v); slope = `OBV[t] - OBV[t-3]`.
- **ADX(14), +DI, -DI**: Wilder (ewm alpha 1/14).
- **RSI**: the frames' `rsi` (MarcoFlow simple RSI(14) on 5-min closes, the RSI the setups use).
- **Prior-day VAH / VAL**: prior session's 1-minute bars; 50 equal-width bins between that session's low and high; each
  1-min bar's volume goes to the bin of its typical price; start at the POC (largest bin) and repeatedly add the larger
  of the next bin above / next bin below (tie: above) until >= 70% of the session volume. VAH = upper edge of the top
  included bin, VAL = lower edge of the bottom one. Only the prior session is used. For the first session after the
  locked block (2025-03-03) the prior session is locked: VAH/VAL are missing and G5 does not block.
- **daily ATR** `atr_d` and R = 0.25 x atr_d: from the frames (bt setups: same formula on the 1-min cache).

### 1.3 Guards (short form as the owner wrote them; longs are the exact mirror). block = skip this bar.
| id | variants | short: block the bar if | long mirror: block if |
|---|---|---|---|
| G1 | k = 1, 2 (2) | close > VWAP and, since the last 5-min close <= VWAP in this session (or the open), some close was > VWAP + k*SD (this bar included) | close < VWAP and since the last close >= VWAP some close < VWAP - k*SD |
| G2 | L = 9, 21, 9-or-21 (3) | close > EMA_L and EMA_L rising (9-or-21: either holds) | close < EMA_L and EMA_L falling |
| G3 | a: CMF; b: CMF or OBV (2) | RSI > 70 and [a: CMF > 0 and CMF rising; b: (CMF > 0 and rising) or OBV slope > 0] | RSI < 30 and [a: CMF < 0 and falling; b: (...) or OBV slope < 0] |
| G4 | ADX > 25 / 30 x DI gap > 5 / 10 (4) | ADX > A and (+DI) - (-DI) > D | ADX > A and (-DI) - (+DI) > D |
| G5 | 1 | close > prior-day VAH | close < prior-day VAL |

A guard is a **layer**: entries = setup mask & window & adv & not blocked, first qualifying bar per symbol-day (exactly
the rescore convention). A blocked signal bar can therefore be followed by a later unblocked one ("wait").
**Pairs**: both guards apply (block = blockA or blockB), every cross-family variant combination of G1-G5:
G1xG2 6, G1xG3 4, G1xG4 8, G1xG5 2, G2xG3 6, G2xG4 12, G2xG5 3, G3xG4 8, G3xG5 2, G4xG5 4 = **55 pairs**. All 55 are
scored and counted (no "pick the two best singles", which would be selection after seeing results).

### 1.4 C: confirmation as an entry delay, N in {3, 6, 12} 5-min bars (3)
For each symbol-day the first raw signal bar s opens a wait over bars s+1 .. s+N (never past tod 15:00). Enter at the
close of the first bar j where all hold:
1. lower high: some bar i in s+1..j had high_i < max(high_s .. high_{i-1}) (long: higher low, low_i > min(low_s..low_{i-1}));
2. trigger on bar j: close_j < VWAP_j or close_j < EMA9_j (long: close above VWAP or EMA9);
3. bearish volume divergence on some bar i in s..j: CMF20_i < 0, or (high_i >= max(high_{i-20..i-1}) and volume_i <
   volume of the bar that made that prior 20-bar high) (long: CMF > 0, or a lower low on lower volume).
If not confirmed by s+N the signal is dropped; the next raw signal after s+N may open a new wait. One trade per
symbol-day. C is not combined with G guards (the menu is: none, single G, C, G-pairs).

### 1.5 Exits (3). Path = later 5-min bars up to the 15:55 bar, stop first inside a bar, flat at the 15:55 bar's close
- **cur**: the setup's own geometry (t1s1 / t05s1 / t1s05, R = 0.25 x atr_d), identical to `setup_lab._outcomes_asym`
  (checked: the simulator must reproduce the frames' `r_<side>_<geom>` on the baseline before anything is scored).
- **E1** momentum-shift: as cur, plus once a bar's favourable extreme has reached +0.5R (bars after entry, that bar
  included), the first such armed bar that closes back across EMA9 (short: close > EMA9; long: close < EMA9) and did not
  hit stop or target exits at that close.
- **E2** structure stop: stop = highest high of the last 6 5-min bars up to and including the entry bar + 0.1 x atr_d
  (long: lowest low - 0.1 x atr_d), distance capped at 1.5R; target price unchanged; size to the same $ risk, i.e. the
  result is measured in units of the new stop distance and costs are divided by it.
- Costs (all exits): production, as `gates.prod_r`: 1c + 1 bps per side, the exit side free on target fills, +2c on stop
  fills.

### 1.6 orb20_a and intraday_momentum (production backtester trades, `bt_trades.parquet`)
Guards are evaluated on the last 5-min bar completed at the trade's entry time and act as a filter only (the engine
emits one signal; there is no later bar to wait for). E1 / E2 / C are re-simulated on 1-minute bars from the recorded
fill with the engine's cost model (`mcf.backtest.engine.Costs`, non-extended tier) and the trade's own stop / target;
for C the entry moves to the confirming 5-min bar's close (+ entry cost) with the same stop and target distances; for
these two setups the confirming bar may end any time before 15:55 (intraday_momentum enters at 15:30, so the lab 15:00
cap would remove every trade by construction). E2 keeps the original stop if the structure stop is on the wrong side
of the fill. (1.6 amended 2026-10-09 before scoring.)
The re-simulation of `cur` is compared with the recorded r_multiple and the difference reported.

### 1.7 Configurations
Per setup: guard sets 1 (none) + 12 (singles: G1 2, G2 3, G3 2, G4 4, G5 1) + 3 (C) + 55 (pairs) = **71**, x 3 exits =
**213**, of which 212 are new (none x cur is the rescore baseline). **23 setups x 212 = 4,876 new configurations.**
At p = 0.05 about 244 would look significant by chance.

Per-lineage try count N (feeds `gates.t_required` and the deflated Sharpe) = the lineage's rescore tries + 212 x
the number of setups of that lineage in this study:
| lineage | setups | rescore tries | added | N |
|---|---|---|---|---|
| exhaustion (exhaustion_short 855,600; RW2 934,522) | 2 | own | 424 | 856,024 / 934,946 |
| heat study | heat_fade_short, heat_fade_long | 19,200 | 424 | 19,624 |
| MarcoFlow primitives | MF1-MF5 | 8,012 | 1,060 | 9,072 |
| owner 10-08 scan | NS1-NS5 | 7,374 | 1,060 | 8,434 |
| rework 82,068 | RW1, RW3, RW5, RW7 | 82,068 | 848 | 82,916 |
| rework 81,430 | RW4, RW6, RW8 | 81,430 | 636 | 82,066 |
| setup screen | orb20_a, intraday_momentum | 15 | 424 | 439 |

### 1.8 Gates and verdict (unchanged `mcf/research/gates.py`, fixed in advance)
exp > 0; day-clustered t >= max(1.5, sqrt(2 ln N)); exp > 0 in up AND down sessions (n >= 30 each); walk-forward
share >= 0.6 (3-month train / 1-month test, locked months excluded). Also reported: deflated Sharpe, ex-best-day,
trades/day, flat sessions. **keep** = all gates pass. A setup's reported "best" configuration is the one with the
highest day-clustered t (descriptive only). A guard that mostly removes up-session trades still has to be > 0 in up
AND down sessions. Nothing is scored on the locked block; a keep candidate goes to the lead for its single scoring.

### 1.9 Anecdote (labelled as such)
The 10 trades the owner flagged (IONQ, ACN, Z, PATH, NOW, LDOS, SHW, NLY, VTRS, BABA) plus GEV (E2's motivating case):
guard values at the live signal bar from `data/cache/bdi1008` 1-min bars (same feature code), and E1 / E2 re-walked on
1-minute bars from the live fill with the live R. One session: a diagnosis, not evidence.

### 1.10 Amendment A (lead, 2026-10-09 04:08 UTC, from the owner's trade notes; declared before any configuration was scored)
**(L) Late-entry / chase guard** - a fourth single-guard family, scored on every setup with the same 3 exits and gates
(not paired with G1-G5). Short form (long = mirror: pulled back from today's high / minutes since today's low):
| id | variants | short: block the bar if |
|---|---|---|
| L-rebound | X = 0.5, 1.0 ATR (2) | (close - today's low so far, 5-min lows incl. this bar) / atr_d > X |
| L-late | M = 60, 120 min (2) | minutes from the end of the 5-min bar that set today's high so far to this bar's end > M |
Ids: `Lr05`, `Lr10`, `Lm60`, `Lm120`. Guard sets per setup become 71 + 4 = **75**, x 3 exits = **225**, **224 new**
per setup; 23 x 224 = **5,152** new G/C/E/L configurations. The lineage N of 1.7 is restated with 224 per setup:
exhaustion +448, heat +448, MF +1,120, NS +1,120, rw82068 +896, rw81430 +672, screen +448.

**(P) New long setup: first pullback that holds VWAP after a morning low** (own new lineage, `bdi-tg-p-pullback-long`).
Signal on a 5-min bar (values at its close), window 10:30-14:30 (tod), point-in-time adv20 >= $95M (the lab default),
first qualifying bar per symbol-day, all of:
1. today's low so far was set by a bar ending at or before 11:30 (the morning low still holds);
2. pullback touch: this bar's low <= VWAP x 1.001 or <= EMA9 x 1.001;
3. close > VWAP and close > EMA9;
4. EMA9 rising (EMA9[t] - EMA9[t-3] > 0).
Exits: t1s1, t05s1, t1s05, each with cur and E1 = **6 configurations**, N = 6 (t bar max(1.5, sqrt(2 ln 6)) = 1.89).
Same 5-min simulator, production costs and gates. Computed on every symbol-day of the 1-min cache (locked block dropped
at load); atr_d from the cache with the heat_frame formula; adv20 from `lib.daily()`. Caveat: the idea comes from
looking at three 2026-10-08 charts (ACN, Z, NLY); that day is outside the history (which ends 2026-10-07).
Study total: 5,152 + 6 = **5,158** new configurations.

## 2. Results (written after scoring; section 1 unchanged)

*Educational only - not financial advice. Lab results on 426 open sessions of the 2-year history; no locked block was loaded or scored; nothing here is a live result.*

**Configurations scored: 5175** (23 setups x 225; 5152 new, the rest are the rescore baselines re-simulated). At p = 0.05 about 258 would look significant by chance.

**Keep: 0 setups (0 configurations).** No guard, confirmation delay or exit from the menu turns any of the 23 setups into a keep.

### Verdict and reading
- **No setup reaches keep, under any guard, pair, confirmation delay, late-entry guard or exit.** All 9 'retire' setups stay retire-or-rework with negative or near-zero expectancy; none of the 15 rework-group setups (14 in rescore.csv) passes the t bar, and most fail the regime gate too. P (new long) fails decisively.
- **Why:** the guards mostly remove trades in proportion, not selectively. Averaged over the 23 setups no single guard moves expectancy by more than +0.035R (G2e21/cur), and the up-session losses of the shorts are not fixed: the guards that cut most trades (G1k1, G2) leave the up-session expectancy of the MF/RW gap-down shorts at -0.2 to -0.5R.
- **Strongest result, still a fail:** RW6 (NS2 lineage) with G1k2 (no short while a +2 SD VWAP excursion is unresolved): +0.26R, n 424, t 2.39, up +0.32 / down +0.08, WF 0.625; with G4 as second layer t 2.57, WF 0.71. The bar is 4.76 (N 82,102); G1k1 on the same setup is -0.02R (no plateau), so it is not even a candidate. NS2 with G1k2 shows the same shape (+0.18R, t 1.53).
- **E1 / E2:** on the baseline entries E1 improves 4 of 23 setups (mean -0.011R) and E2 5 of 23 (mean -0.026R). E2 widens the up/down split of the shorts. The 10-08 give-backs E1/E2 would have saved are the hindsight pattern already seen in EXIT_STUDY.
- **Anecdote vs history:** G2 (rising EMA9/21) would have blocked all 10 flagged trades at their signal bar, and G1/G5/Lr05 most of them. On two years the same guards are flat to negative. A rule that catches today's losers also removes yesterday's winners.
- **Count:** 5,152 G/C/E/L + 6 P = 5,158 new configurations; about 258 would pass p = 0.05 by chance. Raw t >= 1.96 with n >= 60 occurs in 18 configurations, all below their try-count bar.
- Nothing was scored on the locked block. No lab module was written: there is no keep candidate to hand to the lead.

### Failures first
- Configurations with exp > 0 in up AND down sessions (n >= 30 each): 474 of 5022 (9 setups). Configurations with walk-forward share >= 0.6: 678. Configurations with t >= their bar: 8.
- Verdict counts over all configurations: retire 2908, rework 2114.

### P: first pullback that holds VWAP after a morning low (new long, amendment A; 6 configurations, N = 6)

| setup | guard | exit | n | /day | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF +share | ex-best-day | DSR | verdict | failed gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P t05s1 | - | E1 | 324943 | 762.78 | -0.079 | -8.12 | 1.893 | +0.053 (116900) | -0.096 | -0.216 (99410) | 0.0 | -0.080 | 0.0 | **rework** | exp<=0; t -8.12 < 1.893; regime (up and down must both be > 0); walk-forward share 0.0 < 0.6 |
| P t05s1 | - | cur | 324943 | 762.78 | -0.079 | -8.12 | 1.893 | +0.053 (116900) | -0.096 | -0.216 (99410) | 0.0 | -0.080 | 0.0 | **rework** | exp<=0; t -8.12 < 1.893; regime (up and down must both be > 0); walk-forward share 0.0 < 0.6 |
| P t1s05 | - | E1 | 324943 | 762.78 | -0.094 | -11.18 | 1.893 | +0.006 (116900) | -0.118 | -0.185 (99410) | 0.0 | -0.096 | 0.0 | **retire** | exp<=0; t -11.18 < 1.893; regime (up and down must both be > 0); walk-forward share 0.0 < 0.6 |
| P t1s05 | - | cur | 324943 | 762.78 | -0.091 | -9.1 | 1.893 | +0.047 (116900) | -0.122 | -0.220 (99410) | 0.0 | -0.093 | 0.0 | **rework** | exp<=0; t -9.1 < 1.893; regime (up and down must both be > 0); walk-forward share 0.0 < 0.6 |
| P t1s1 | - | E1 | 324943 | 762.78 | -0.090 | -7.62 | 1.893 | +0.074 (116900) | -0.117 | -0.254 (99410) | 0.0 | -0.092 | 0.0 | **rework** | exp<=0; t -7.62 < 1.893; regime (up and down must both be > 0); walk-forward share 0.0 < 0.6 |
| P t1s1 | - | cur | 324943 | 762.78 | -0.085 | -5.65 | 1.893 | +0.148 (116900) | -0.121 | -0.321 (99410) | 0.118 | -0.088 | 0.0 | **rework** | exp<=0; t -5.65 < 1.893; regime (up and down must both be > 0); walk-forward share 0.118 < 0.6 |

### Best configuration per setup (highest day-clustered t among configurations with n >= 60; descriptive, not a selection)

Configurations with n < 60 (375) are excluded from the 'best' picks: e.g. NS5 with G1+G2e21 keeps 2 trades and shows t = 603 - a degenerate statistic, not a pass (they fail the regime and walk-forward gates anyway).

| setup | guard | exit | n | /day | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF +share | ex-best-day | DSR | verdict | failed gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | G2e21+G3b | E1 | 203 | 1.78 | -0.011 | -0.15 | 4.271 | -0.228 (101) | +0.176 | +0.218 (65) | 0.714 | -0.031 | 0.0 | **rework** | exp<=0; t -0.15 < 4.271; regime (up and down must both be > 0) |
| MF2-open-rsimidhi-flowsell | Lr05 | cur | 553 | 2.39 | -0.002 | -0.06 | 4.271 | -0.060 (175) | +0.046 | +0.007 (207) | 0.5 | -0.011 | 0.0 | **retire** | exp<=0; t -0.06 < 4.271; regime (up and down must both be > 0); walk-forward share 0.5 < 0.6 |
| MF4-h40-open-flowsell | G4a25d5+G5 | E1 | 1747 | 4.76 | -0.068 | -1.4 | 4.271 | -0.257 (612) | +0.034 | +0.034 (607) | 0.412 | -0.076 | 0.0 | **retire** | exp<=0; t -1.4 < 4.271; regime (up and down must both be > 0); walk-forward share 0.412 < 0.6 |
| NS5-sma50-flush-oversold-long | G1k2+G4a25d10 | cur | 81 | 1.35 | +0.222 | 2.02 | 4.254 | +0.770 (14) | +0.165 | +0.037 (30) | nan | +0.205 | 0.0471 | **rework** | t 2.02 < 4.254; regime (up and down must both be > 0); walk-forward share None < 0.6 |
| RW2 bdi-rw-exhaustion-noon-adv150 | Lr05 | cur | 1544 | 4.75 | +0.013 | 0.31 | 5.244 | -0.127 (582) | +0.022 | +0.172 (484) | 0.412 | -0.010 | 0.0 | **rework** | t 0.31 < 5.244; regime (up and down must both be > 0); walk-forward share 0.412 < 0.6 |
| RW8 bdi-rw-sma50up-spikefade | Lr05 | E2 | 71 | 1.25 | +0.124 | 0.96 | 4.757 | +0.111 (28) | +0.046 | +0.224 (21) | nan | +0.075 | 0.0002 | **rework** | t 0.96 < 4.757; regime (up and down must both be > 0); walk-forward share None < 0.6 |
| exhaustion_short | Lr05 | cur | 1094 | 3.84 | +0.031 | 0.73 | 5.227 | -0.082 (359) | -0.034 | +0.195 (385) | 0.588 | +0.009 | 0.0 | **rework** | t 0.73 < 5.227; regime (up and down must both be > 0); walk-forward share 0.588 < 0.6 |
| intraday_momentum | Lm60 | cur | 147 | 1.65 | +0.108 | 0.9 | 3.504 | -0.111 (55) | +0.178 | +0.297 (47) | 0.333 | +0.027 | 0.0071 | **rework** | t 0.9 < 3.504; regime (up and down must both be > 0); walk-forward share 0.333 < 0.6 |
| orb20_a | Lm60 | E2 | 2650 | 6.26 | +0.014 | 0.88 | 3.504 | +0.039 (906) | -0.026 | +0.026 (889) | 0.588 | +0.011 | 0.0155 | **rework** | t 0.88 < 3.504; walk-forward share 0.588 < 0.6 |
| MF3-open-flowsell-rsi5hi | G2e21+G3a | cur | 203 | 1.64 | -0.031 | -0.41 | 4.271 | -0.229 (68) | -0.150 | +0.260 (72) | 0.556 | -0.057 | 0.0 | **rework** | exp<=0; t -0.41 < 4.271; regime (up and down must both be > 0); walk-forward share 0.556 < 0.6 |
| MF5-flowsell-vwapup-rsi5hi | G2e21+G3b | cur | 97 | 1.43 | -0.089 | -0.95 | 4.271 | -0.506 (35) | +0.292 | +0.082 (43) | nan | -0.123 | 0.0 | **retire** | exp<=0; t -0.95 < 4.271; regime (up and down must both be > 0); walk-forward share None < 0.6 |
| NS1-rsidip-rsi5pop-long | G1k1+G5 | E2 | 267 | 1.67 | +0.066 | 1.67 | 4.254 | +0.111 (108) | +0.017 | +0.061 (70) | 0.667 | +0.058 | 0.0211 | **rework** | t 1.67 < 4.254 |
| NS2-sma50break-overbought-short | G1k1+G4a25d5 | E2 | 317 | 2.81 | +0.150 | 1.97 | 4.254 | +0.097 (215) | +0.184 | +0.321 (58) | 0.286 | +0.066 | 0.0 | **rework** | t 1.97 < 4.254; walk-forward share 0.286 < 0.6 |
| NS3-failed-vwap-reclaim-short | Lm60 | cur | 917 | 3.35 | +0.096 | 1.73 | 4.254 | +0.029 (210) | +0.009 | +0.229 (342) | 0.562 | +0.077 | 0.0217 | **rework** | t 1.73 < 4.254; walk-forward share 0.562 < 0.6 |
| NS4-pm-vwap-reclaim-oversold-short | Lr05 | cur | 221 | 1.7 | +0.023 | 0.46 | 4.254 | -0.066 (114) | +0.157 | +0.069 (47) | 0.875 | +0.011 | 0.0006 | **rework** | t 0.46 < 4.254; regime (up and down must both be > 0) |
| RW1 bdi-rw-gapdn-bounce-flowsell | G1k2+G2e9or21 | E2 | 1029 | 3.51 | +0.038 | 0.8 | 4.759 | -0.250 (364) | +0.082 | +0.291 (364) | 0.588 | +0.027 | 0.0003 | **rework** | t 0.8 < 4.759; regime (up and down must both be > 0); walk-forward share 0.588 < 0.6 |
| RW3 bdi-rw-gapdn-rsi5pop-flowsell | G1k1+G5 | E2 | 168 | 1.45 | -0.017 | -0.12 | 4.759 | -0.209 (53) | -0.197 | +0.286 (64) | 0.571 | -0.128 | 0.0 | **retire** | exp<=0; t -0.12 < 4.759; regime (up and down must both be > 0); walk-forward share 0.571 < 0.6 |
| RW4 bdi-rw-ns3-adv150 | Lm60 | cur | 738 | 3.09 | +0.100 | 1.66 | 4.757 | +0.033 (163) | -0.003 | +0.248 (279) | 0.688 | +0.080 | 0.0045 | **rework** | t 1.66 < 4.757 |
| RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn | G1k2+G5 | E2 | 121 | 1.39 | +0.131 | 0.99 | 4.759 | +0.183 (33) | +0.001 | +0.265 (37) | 1.0 | +0.095 | 0.0003 | **rework** | t 0.99 < 4.759 |
| RW6 bdi-rw-ns2-up3 | G1k2+G4a30d5 | cur | 413 | 3.97 | +0.274 | 2.57 | 4.757 | +0.323 (308) | +0.152 | +0.118 (67) | 0.714 | +0.058 | 0.0 | **rework** | t 2.57 < 4.757 |
| RW7 bdi-rw-gapdn-bounce-early | G2e21+G4a25d10 | E1 | 214 | 1.6 | +0.028 | 0.43 | 4.759 | -0.005 (95) | +0.091 | +0.023 (65) | 0.667 | -0.003 | 0.0 | **rework** | t 0.43 < 4.759; regime (up and down must both be > 0) |
| heat_fade_long | G2e21+G5 | E2 | 73 | 1.78 | +0.257 | 1.37 | 4.447 | +0.106 (16) | +0.672 | -0.086 (28) | 1.0 | +0.101 | 0.0001 | **rework** | t 1.37 < 4.447; regime (up and down must both be > 0) |
| heat_fade_short | G2e21+G4a25d5 | E2 | 1569 | 4.64 | +0.073 | 1.66 | 4.447 | -0.113 (581) | +0.120 | +0.240 (514) | 0.588 | +0.061 | 0.0069 | **rework** | t 1.66 < 4.447; regime (up and down must both be > 0); walk-forward share 0.588 < 0.6 |

### Per setup: baseline and the best of each menu family (by t)

| setup | rescore group | none/cur exp (n, t) | best single G | best C | best G pair | best L | none/E1 | none/E2 | best up&down-positive config |
|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | retire | -0.058 (2389, -2.1) | G2e21/E1: -0.011 (n 203, t -0.15; up -0.228, dn +0.218, WF 0.714) | C3/E2: -0.083 (n 773, t -2.13; up -0.279, dn +0.035, WF 0.312) | G2e21+G4a25d5/E1: -0.011 (n 203, t -0.15; up -0.228, dn +0.218, WF 0.714) | Lr10/E2: -0.095 (n 2356, t -1.82; up -0.431, dn +0.172, WF 0.235) | none/E1: -0.070 (n 2389, t -3.15; up -0.208, dn +0.007, WF 0.176) | none/E2: -0.098 (n 2389, t -1.87; up -0.429, dn +0.166, WF 0.235) | - |
| MF2-open-rsimidhi-flowsell | retire | -0.030 (610, -0.83) | G5/cur: -0.005 (n 497, t -0.12; up -0.136, dn +0.036, WF 0.571) | C3/E2: -0.004 (n 473, t -0.1; up -0.175, dn +0.104, WF 0.533) | G3a+G5/cur: -0.005 (n 497, t -0.12; up -0.136, dn +0.036, WF 0.571) | Lr05/cur: -0.002 (n 553, t -0.06; up -0.060, dn +0.007, WF 0.5) | none/E1: -0.048 (n 610, t -1.4; up -0.070, dn -0.075, WF 0.438) | none/E2: -0.046 (n 610, t -1.1; up -0.215, dn +0.076, WF 0.562) | - |
| MF3-open-flowsell-rsi5hi | rework | -0.074 (4136, -2.5) | G2e21/cur: -0.037 (n 209, t -0.5; up -0.242, dn +0.230, WF 0.556) | C3/cur: -0.096 (n 1307, t -2.69; up -0.242, dn +0.059, WF 0.353) | G2e21+G3a/cur: -0.031 (n 203, t -0.41; up -0.229, dn +0.260, WF 0.556) | Lr10/cur: -0.074 (n 4017, t -2.49; up -0.294, dn +0.152, WF 0.353) | none/E1: -0.070 (n 4136, t -3.17; up -0.224, dn +0.064, WF 0.235) | none/E2: -0.141 (n 4136, t -3.62; up -0.421, dn +0.116, WF 0.235) | - |
| MF4-h40-open-flowsell | retire | -0.089 (3318, -3.02) | G2e9or21/cur: -0.082 (n 1464, t -1.45; up -0.319, dn +0.041, WF 0.353) | C3/cur: -0.050 (n 1918, t -1.74; up -0.157, dn +0.025, WF 0.412) | G3b+G4a30d5/E1: -0.068 (n 1746, t -1.4; up -0.279, dn +0.056, WF 0.412) | Lm60/cur: -0.090 (n 2899, t -2.77; up -0.250, dn +0.037, WF 0.235) | none/E1: -0.089 (n 3318, t -3.02; up -0.245, dn +0.030, WF 0.294) | none/E2: -0.121 (n 3318, t -3.89; up -0.304, dn +0.020, WF 0.294) | - |
| MF5-flowsell-vwapup-rsi5hi | rework | -0.052 (6827, -2.39) | G2e21/cur: -0.081 (n 160, t -1.09; up -0.429, dn +0.089, WF 0.2) | C3/cur: -0.073 (n 1781, t -2.68; up -0.299, dn +0.125, WF 0.353) | G2e21+G3b/cur: -0.089 (n 97, t -0.95; up -0.506, dn +0.082, WF nan) | Lm120/cur: -0.044 (n 5335, t -1.75; up -0.280, dn +0.198, WF 0.353) | none/E1: -0.059 (n 6827, t -3.53; up -0.226, dn +0.074, WF 0.294) | none/E2: -0.147 (n 6827, t -4.77; up -0.430, dn +0.114, WF 0.235) | - |
| NS1-rsidip-rsi5pop-long | rework | +0.034 (444, 0.87) | G1k1/E2: +0.052 (n 392, t 1.48; up +0.124, dn +0.005, WF 0.571) | C3/E2: +0.031 (n 311, t 0.71; up +0.095, dn -0.009, WF 0.75) | G1k1+G5/E2: +0.066 (n 267, t 1.67; up +0.111, dn +0.061, WF 0.667) | Lm120/E2: +0.042 (n 444, t 1.22; up +0.119, dn -0.018, WF 0.571) | none/E1: +0.034 (n 444, t 0.87; up +0.097, dn -0.009, WF 0.5) | none/E2: +0.042 (n 444, t 1.22; up +0.119, dn -0.018, WF 0.571) | G1k1+G5/E2: +0.066 (n 267, t 1.67; up +0.111, dn +0.061, WF 0.667) |
| NS2-sma50break-overbought-short | rework | +0.006 (3124, 0.11) | G1k1/E2: +0.143 (n 335, t 1.88; up +0.088, dn +0.339, WF 0.286) | C3/E1: +0.199 (n 634, t 1.24; up +0.330, dn +0.141, WF 0.308) | G1k1+G4a25d5/E2: +0.150 (n 317, t 1.97; up +0.097, dn +0.321, WF 0.286) | Lr05/E1: +0.042 (n 759, t 1.02; up +0.008, dn +0.166, WF 0.333) | none/E1: -0.014 (n 3124, t -0.38; up -0.041, dn +0.072, WF 0.412) | none/E2: -0.003 (n 3124, t -0.03; up -0.052, dn +0.193, WF 0.353) | G1k1+G4a25d5/E2: +0.150 (n 317, t 1.97; up +0.097, dn +0.321, WF 0.286) |
| NS3-failed-vwap-reclaim-short | rework | +0.056 (1510, 1.26) | G3b/cur: +0.064 (n 1421, t 1.41; up -0.087, dn +0.255, WF 0.625) | C6/cur: +0.026 (n 877, t 0.5; up -0.098, dn +0.221, WF 0.625) | G1k2+G3a/cur: +0.062 (n 1479, t 1.39; up -0.074, dn +0.246, WF 0.647) | Lm60/cur: +0.096 (n 917, t 1.73; up +0.029, dn +0.229, WF 0.562) | none/E1: +0.031 (n 1510, t 0.9; up -0.064, dn +0.116, WF 0.588) | none/E2: +0.026 (n 1510, t 0.46; up -0.155, dn +0.260, WF 0.647) | Lm60/cur: +0.096 (n 917, t 1.73; up +0.029, dn +0.229, WF 0.562) |
| NS4-pm-vwap-reclaim-oversold-short | rework | -0.065 (1469, -2.03) | G5/cur: -0.000 (n 241, t -0.01; up -0.112, dn +0.168, WF 0.444) | C3/E2: -0.070 (n 812, t -1.38; up -0.186, dn +0.120, WF 0.5) | G2e21+G5/cur: +0.003 (n 240, t 0.04; up -0.107, dn +0.168, WF 0.444) | Lr05/cur: +0.023 (n 221, t 0.46; up -0.066, dn +0.069, WF 0.875) | none/E1: -0.058 (n 1469, t -2.53; up -0.141, dn +0.088, WF 0.412) | none/E2: -0.070 (n 1469, t -1.29; up -0.247, dn +0.234, WF 0.529) | - |
| NS5-sma50-flush-oversold-long | retire | -0.038 (1305, -0.47) | G1k2/E2: +0.213 (n 100, t 1.38; up +0.634, dn -0.019, WF nan) | C3/E1: +0.085 (n 163, t 0.91; up +0.053, dn +0.062, WF 0.857) | G1k2+G4a25d10/cur: +0.222 (n 81, t 2.02; up +0.770, dn +0.037, WF nan) | Lr10/E2: -0.014 (n 1038, t -0.12; up +0.164, dn -0.234, WF 0.529) | none/E1: -0.050 (n 1305, t -0.91; up +0.026, dn -0.163, WF 0.353) | none/E2: -0.017 (n 1305, t -0.18; up +0.123, dn -0.228, WF 0.529) | C3/E1: +0.085 (n 163, t 0.91; up +0.053, dn +0.062, WF 0.857) |
| RW1 bdi-rw-gapdn-bounce-flowsell | rework | -0.007 (2489, -0.22) | G2e9/E2: +0.026 (n 1363, t 0.59; up -0.292, dn +0.297, WF 0.588) | C6/E2: -0.009 (n 1856, t -0.25; up -0.240, dn +0.231, WF 0.588) | G1k2+G2e9or21/E2: +0.038 (n 1029, t 0.8; up -0.250, dn +0.291, WF 0.588) | Lr05/cur: +0.004 (n 1713, t 0.12; up -0.288, dn +0.292, WF 0.471) | none/E1: -0.034 (n 2489, t -1.39; up -0.216, dn +0.147, WF 0.353) | none/E2: -0.013 (n 2489, t -0.38; up -0.270, dn +0.258, WF 0.471) | - |
| RW2 bdi-rw-exhaustion-noon-adv150 | retire | -0.009 (7797, -0.35) | G3b/cur: -0.002 (n 4434, t -0.06; up -0.093, dn +0.114, WF 0.353) | C12/E2: -0.049 (n 5230, t -1.51; up -0.131, dn +0.049, WF 0.471) | G3b+G4a25d5/cur: -0.002 (n 2521, t -0.06; up -0.121, dn +0.120, WF 0.471) | Lr05/cur: +0.013 (n 1544, t 0.31; up -0.127, dn +0.172, WF 0.412) | none/E1: -0.012 (n 7797, t -0.58; up -0.045, dn +0.063, WF 0.118) | none/E2: -0.095 (n 7797, t -2.55; up -0.159, dn +0.003, WF 0.235) | - |
| RW3 bdi-rw-gapdn-rsi5pop-flowsell | rework | -0.041 (1816, -1.22) | G1k1/E2: -0.039 (n 176, t -0.28; up -0.246, dn +0.265, WF 0.571) | C3/E2: -0.033 (n 581, t -0.71; up -0.230, dn +0.093, WF 0.353) | G1k1+G5/E2: -0.017 (n 168, t -0.12; up -0.209, dn +0.286, WF 0.571) | Lr10/E2: -0.041 (n 1733, t -0.8; up -0.365, dn +0.310, WF 0.294) | none/E1: -0.050 (n 1816, t -2.04; up -0.228, dn +0.106, WF 0.353) | none/E2: -0.056 (n 1816, t -1.11; up -0.376, dn +0.306, WF 0.294) | - |
| RW4 bdi-rw-ns3-adv150 | rework | +0.054 (1216, 1.13) | G3b/cur: +0.066 (n 1146, t 1.36; up -0.102, dn +0.251, WF 0.5) | C6/E2: +0.023 (n 714, t 0.41; up -0.105, dn +0.227, WF 0.375) | G1k2+G3b/cur: +0.066 (n 1144, t 1.36; up -0.098, dn +0.250, WF 0.5) | Lm60/cur: +0.100 (n 738, t 1.66; up +0.033, dn +0.248, WF 0.688) | none/E1: +0.028 (n 1216, t 0.73; up -0.071, dn +0.122, WF 0.562) | none/E2: +0.025 (n 1216, t 0.41; up -0.134, dn +0.240, WF 0.625) | Lm60/cur: +0.100 (n 738, t 1.66; up +0.033, dn +0.248, WF 0.688) |
| RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn | rework | -0.013 (1294, -0.32) | G1k2/E2: +0.106 (n 156, t 0.85; up +0.016, dn +0.267, WF 0.6) | C3/cur: -0.029 (n 305, t -0.43; up -0.202, dn +0.012, WF 0.5) | G1k2+G5/E2: +0.131 (n 121, t 0.99; up +0.183, dn +0.265, WF 1.0) | Lm60/cur: -0.008 (n 1219, t -0.19; up -0.259, dn +0.273, WF 0.588) | none/E1: -0.041 (n 1294, t -1.29; up -0.199, dn +0.154, WF 0.294) | none/E2: -0.069 (n 1294, t -1.13; up -0.392, dn +0.319, WF 0.471) | G1k2+G5/E2: +0.131 (n 121, t 0.99; up +0.183, dn +0.265, WF 1.0) |
| RW6 bdi-rw-ns2-up3 | rework | +0.057 (1461, 0.77) | G1k2/cur: +0.264 (n 424, t 2.39; up +0.318, dn +0.082, WF 0.625) | C3/E1: +0.337 (n 335, t 1.72; up +0.492, dn +0.111, WF 0.4) | G1k2+G4a30d5/cur: +0.274 (n 413, t 2.57; up +0.323, dn +0.118, WF 0.714) | Lr05/E1: +0.066 (n 243, t 1.17; up +0.050, dn +0.199, WF 0.625) | none/E1: +0.014 (n 1461, t 0.34; up +0.005, dn +0.049, WF 0.471) | none/E2: +0.094 (n 1461, t 0.79; up +0.077, dn +0.206, WF 0.588) | G1k2+G4a30d5/cur: +0.274 (n 413, t 2.57; up +0.323, dn +0.118, WF 0.714) |
| RW7 bdi-rw-gapdn-bounce-early | rework | -0.030 (1590, -0.98) | G2e21/E1: +0.017 (n 216, t 0.27; up -0.016, dn +0.005, WF 0.667) | C3/E1: -0.067 (n 633, t -1.75; up -0.261, dn +0.067, WF 0.312) | G2e21+G4a25d10/E1: +0.028 (n 214, t 0.43; up -0.005, dn +0.023, WF 0.667) | Lr05/cur: -0.032 (n 1090, t -0.87; up -0.293, dn +0.281, WF 0.562) | none/E1: -0.040 (n 1590, t -1.52; up -0.193, dn +0.092, WF 0.353) | none/E2: -0.079 (n 1590, t -1.88; up -0.310, dn +0.192, WF 0.353) | - |
| RW8 bdi-rw-sma50up-spikefade | retire | -0.090 (459, -1.4) | G5/E2: +0.006 (n 113, t 0.05; up -0.065, dn -0.164, WF 0.333) | C3/E1: +0.002 (n 246, t 0.05; up -0.134, dn +0.253, WF 0.545) | G3b+G5/E2: +0.006 (n 113, t 0.05; up -0.065, dn -0.164, WF 0.333) | Lr05/E2: +0.124 (n 71, t 0.96; up +0.111, dn +0.224, WF nan) | none/E1: -0.084 (n 459, t -1.62; up -0.209, dn -0.008, WF 0.5) | none/E2: -0.087 (n 459, t -1.13; up -0.242, dn -0.005, WF 0.625) | - |
| exhaustion_short | retire | -0.010 (5973, -0.32) | G3b/cur: +0.000 (n 3344, t 0.01; up -0.075, dn +0.125, WF 0.412) | C12/E2: -0.080 (n 3583, t -2.08; up -0.132, dn +0.001, WF 0.294) | G3a+G4a25d5/cur: +0.002 (n 2110, t 0.06; up -0.086, dn +0.126, WF 0.588) | Lr05/cur: +0.031 (n 1094, t 0.73; up -0.082, dn +0.195, WF 0.588) | none/E1: -0.018 (n 5973, t -0.64; up -0.043, dn +0.057, WF 0.176) | none/E2: -0.102 (n 5973, t -2.15; up -0.159, dn +0.019, WF 0.235) | - |
| heat_fade_long | rework | -0.046 (14460, -1.16) | G2e21/E2: +0.257 (n 73, t 1.37; up +0.106, dn -0.086, WF 1.0) | C3/E2: -0.025 (n 2614, t -0.4; up +0.163, dn -0.173, WF 0.471) | G2e21+G5/E2: +0.257 (n 73, t 1.37; up +0.106, dn -0.086, WF 1.0) | Lr05/cur: +0.039 (n 1991, t 0.67; up +0.107, dn -0.023, WF 0.294) | none/E1: -0.036 (n 14460, t -1.31; up +0.028, dn -0.102, WF 0.529) | none/E2: -0.064 (n 14460, t -1.32; up +0.045, dn -0.183, WF 0.529) | G1k1+G5/E2: +0.129 (n 157, t 0.94; up +0.166, dn +0.135, WF 0.75) |
| heat_fade_short | rework | +0.017 (14433, 0.68) | G2e21/E2: +0.064 (n 1636, t 1.47; up -0.110, dn +0.219, WF 0.529) | C12/E2: -0.013 (n 9687, t -0.44; up -0.232, dn +0.150, WF 0.529) | G2e21+G4a25d5/E2: +0.073 (n 1569, t 1.66; up -0.113, dn +0.240, WF 0.588) | Lr10/cur: +0.017 (n 14303, t 0.7; up -0.202, dn +0.157, WF 0.706) | none/E1: -0.000 (n 14433, t -0.02; up -0.152, dn +0.091, WF 0.529) | none/E2: +0.014 (n 14433, t 0.55; up -0.218, dn +0.167, WF 0.529) | - |
| intraday_momentum | retire | -0.062 (1149, -2.32) | G3b/E1: -0.057 (n 1040, t -2.09; up -0.071, dn -0.082, WF 0.353) | C12/E2: -0.075 (n 709, t -2.81; up -0.096, dn -0.078, WF 0.25) | G1k1+G2e9or21/E1: -0.071 (n 475, t -2.04; up -0.069, dn -0.064, WF 0.438) | Lm60/E2: +0.106 (n 147, t 0.9; up -0.078, dn +0.156, WF 0.333) | none/E1: -0.062 (n 1149, t -2.39; up -0.066, dn -0.097, WF 0.294) | none/E2: -0.085 (n 1149, t -2.62; up -0.081, dn -0.150, WF 0.294) | - |
| orb20_a | retire | -0.003 (2827, -0.13) | G3b/E2: +0.006 (n 2741, t 0.37; up +0.034, dn +0.014, WF 0.471) | C3/E2: +0.000 (n 2430, t 0.0; up +0.013, dn -0.019, WF 0.471) | G2e9or21+G5/cur: +0.012 (n 2067, t 0.53; up +0.069, dn -0.002, WF 0.529) | Lm60/E2: +0.014 (n 2650, t 0.88; up +0.039, dn +0.026, WF 0.588) | none/E1: -0.021 (n 2827, t -1.22; up +0.009, dn -0.004, WF 0.294) | none/E2: +0.002 (n 2827, t 0.16; up +0.030, dn +0.005, WF 0.471) | Lm60/E2: +0.014 (n 2650, t 0.88; up +0.039, dn +0.026, WF 0.588) |

### Average effect of each guard / exit across setups (mean change in exp R vs none/cur, and mean share of trades kept)

| guard | exit | setups | mean d exp R | median d exp R | setups improved | mean trades kept | mean d up exp | mean d down exp |
|---|---|---|---|---|---|---|---|---|
| none | E1 | 23 | -0.011 | -0.010 | 4 | 1.00 | +0.020 | -0.056 |
| none | E2 | 23 | -0.026 | -0.018 | 5 | 1.00 | -0.055 | +0.007 |
| G1k1 | cur | 23 | -0.008 | -0.004 | 8 | 0.41 | +0.011 | -0.022 |
| G1k1 | E1 | 23 | -0.019 | -0.018 | 8 | 0.41 | +0.024 | -0.073 |
| G1k1 | E2 | 23 | -0.030 | -0.014 | 8 | 0.41 | -0.030 | -0.013 |
| G1k2 | cur | 23 | +0.025 | +0.000 | 11 | 0.52 | +0.038 | -0.013 |
| G1k2 | E1 | 23 | +0.000 | -0.010 | 7 | 0.52 | +0.036 | -0.065 |
| G1k2 | E2 | 23 | +0.014 | -0.024 | 7 | 0.52 | +0.008 | -0.004 |
| G2e9 | cur | 21 | -0.022 | -0.004 | 9 | 0.35 | -0.095 | +0.016 |
| G2e9 | E1 | 21 | -0.025 | -0.004 | 8 | 0.35 | -0.038 | -0.023 |
| G2e9 | E2 | 21 | -0.027 | -0.021 | 7 | 0.35 | -0.119 | +0.049 |
| G2e21 | cur | 23 | +0.035 | -0.004 | 10 | 0.31 | -0.021 | +0.033 |
| G2e21 | E1 | 23 | +0.018 | -0.000 | 11 | 0.31 | -0.011 | -0.001 |
| G2e21 | E2 | 23 | -0.016 | -0.015 | 10 | 0.31 | -0.035 | +0.005 |
| G2e9or21 | cur | 20 | -0.026 | -0.009 | 9 | 0.33 | -0.071 | +0.006 |
| G2e9or21 | E1 | 20 | -0.038 | -0.003 | 9 | 0.33 | -0.035 | -0.037 |
| G2e9or21 | E2 | 20 | -0.036 | -0.018 | 7 | 0.33 | -0.097 | +0.034 |
| G3a | cur | 23 | +0.001 | +0.000 | 11 | 0.88 | +0.003 | -0.001 |
| G3a | E1 | 23 | -0.011 | -0.010 | 4 | 0.88 | +0.019 | -0.052 |
| G3a | E2 | 23 | -0.025 | -0.018 | 6 | 0.88 | -0.048 | +0.007 |
| G3b | cur | 23 | -0.005 | +0.000 | 10 | 0.70 | +0.009 | +0.004 |
| G3b | E1 | 23 | -0.018 | -0.013 | 8 | 0.70 | +0.018 | -0.052 |
| G3b | E2 | 23 | -0.034 | -0.033 | 5 | 0.70 | -0.045 | +0.013 |
| G4a25d5 | cur | 23 | +0.007 | +0.005 | 15 | 0.68 | +0.009 | +0.014 |
| G4a25d5 | E1 | 23 | -0.006 | -0.008 | 11 | 0.68 | +0.027 | -0.039 |
| G4a25d5 | E2 | 23 | -0.022 | -0.008 | 8 | 0.68 | -0.046 | +0.022 |
| G4a25d10 | cur | 23 | +0.001 | +0.002 | 14 | 0.71 | +0.001 | +0.006 |
| G4a25d10 | E1 | 23 | -0.009 | -0.008 | 9 | 0.71 | +0.021 | -0.043 |
| G4a25d10 | E2 | 23 | -0.027 | -0.011 | 6 | 0.71 | -0.051 | +0.014 |
| G4a30d5 | cur | 23 | +0.001 | +0.001 | 12 | 0.79 | -0.000 | +0.008 |
| G4a30d5 | E1 | 23 | -0.009 | -0.010 | 8 | 0.79 | +0.021 | -0.044 |
| G4a30d5 | E2 | 23 | -0.024 | -0.008 | 9 | 0.79 | -0.052 | +0.026 |
| G4a30d10 | cur | 23 | -0.001 | -0.001 | 9 | 0.80 | -0.002 | +0.005 |
| G4a30d10 | E1 | 23 | -0.010 | -0.009 | 7 | 0.80 | +0.020 | -0.047 |
| G4a30d10 | E2 | 23 | -0.026 | -0.008 | 7 | 0.80 | -0.052 | +0.022 |
| G5 | cur | 23 | -0.007 | -0.010 | 9 | 0.55 | -0.008 | -0.014 |
| G5 | E1 | 23 | -0.017 | -0.013 | 5 | 0.55 | +0.017 | -0.068 |
| G5 | E2 | 23 | -0.042 | -0.020 | 8 | 0.55 | -0.058 | -0.026 |
| C3 | cur | 23 | +0.003 | -0.020 | 6 | 0.40 | +0.029 | -0.048 |
| C3 | E1 | 23 | +0.007 | -0.017 | 7 | 0.40 | +0.056 | -0.065 |
| C3 | E2 | 23 | -0.006 | -0.011 | 9 | 0.40 | +0.011 | -0.032 |
| C6 | cur | 23 | -0.021 | -0.026 | 4 | 0.57 | +0.010 | -0.056 |
| C6 | E1 | 23 | -0.018 | -0.023 | 6 | 0.57 | +0.030 | -0.075 |
| C6 | E2 | 23 | -0.023 | -0.026 | 6 | 0.57 | -0.008 | -0.038 |
| C12 | cur | 23 | -0.030 | -0.033 | 3 | 0.77 | -0.011 | -0.047 |
| C12 | E1 | 23 | -0.027 | -0.029 | 5 | 0.77 | +0.012 | -0.068 |
| C12 | E2 | 23 | -0.029 | -0.034 | 4 | 0.77 | -0.027 | -0.023 |
| Lr05 | cur | 23 | +0.016 | +0.003 | 13 | 0.53 | +0.004 | +0.030 |
| Lr05 | E1 | 23 | +0.007 | -0.003 | 11 | 0.53 | +0.032 | -0.029 |
| Lr05 | E2 | 23 | -0.012 | -0.020 | 8 | 0.53 | -0.059 | +0.052 |
| Lr10 | cur | 23 | -0.003 | +0.001 | 15 | 0.88 | -0.010 | +0.010 |
| Lr10 | E1 | 23 | -0.011 | -0.011 | 8 | 0.88 | +0.014 | -0.047 |
| Lr10 | E2 | 23 | -0.030 | -0.029 | 6 | 0.88 | -0.073 | +0.023 |
| Lm60 | cur | 23 | +0.007 | +0.003 | 14 | 0.74 | +0.008 | -0.005 |
| Lm60 | E1 | 23 | -0.004 | -0.009 | 9 | 0.74 | +0.027 | -0.068 |
| Lm60 | E2 | 23 | -0.012 | -0.017 | 8 | 0.74 | -0.031 | -0.008 |
| Lm120 | cur | 23 | +0.004 | +0.000 | 4 | 0.91 | -0.000 | +0.004 |
| Lm120 | E1 | 23 | -0.007 | -0.012 | 6 | 0.91 | +0.021 | -0.055 |
| Lm120 | E2 | 23 | -0.020 | -0.020 | 5 | 0.91 | -0.052 | +0.006 |

### Simulator checks

- Lab exits: the 5-min simulator against the frames' own lab outcome on the baseline (none/cur):
  - MF1-945-flowsell-vwapup: n 2389, max |diff| 0.0, share > 0.01R 0.0
  - MF2-open-rsimidhi-flowsell: n 610, max |diff| 0.0, share > 0.01R 0.0
  - MF3-open-flowsell-rsi5hi: n 4136, max |diff| 0.0, share > 0.01R 0.0
  - MF4-h40-open-flowsell: n 3318, max |diff| 0.0, share > 0.01R 0.0
  - MF5-flowsell-vwapup-rsi5hi: n 6827, max |diff| 0.0, share > 0.01R 0.0
  - NS1-rsidip-rsi5pop-long: n 444, max |diff| 0.0, share > 0.01R 0.0
  - NS2-sma50break-overbought-short: n 3124, max |diff| 0.0, share > 0.01R 0.0
  - NS3-failed-vwap-reclaim-short: n 1510, max |diff| 0.0, share > 0.01R 0.0
  - NS4-pm-vwap-reclaim-oversold-short: n 1469, max |diff| 0.0, share > 0.01R 0.0
  - NS5-sma50-flush-oversold-long: n 1305, max |diff| 0.0, share > 0.01R 0.0
  - RW1 bdi-rw-gapdn-bounce-flowsell: n 2489, max |diff| 0.0, share > 0.01R 0.0
  - RW2 bdi-rw-exhaustion-noon-adv150: n 7797, max |diff| 0.0, share > 0.01R 0.0
  - RW3 bdi-rw-gapdn-rsi5pop-flowsell: n 1816, max |diff| 0.0, share > 0.01R 0.0
  - RW4 bdi-rw-ns3-adv150: n 1216, max |diff| 0.0, share > 0.01R 0.0
  - RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn: n 1294, max |diff| 0.0, share > 0.01R 0.0
  - RW6 bdi-rw-ns2-up3: n 1461, max |diff| 0.0, share > 0.01R 0.0
  - RW7 bdi-rw-gapdn-bounce-early: n 1590, max |diff| 1.44444, share > 0.01R 0.00063
  - RW8 bdi-rw-sma50up-spikefade: n 459, max |diff| 0.0, share > 0.01R 0.0
  - exhaustion_short: n 5973, max |diff| 0.0, share > 0.01R 0.0
  - heat_fade_long: n 14460, max |diff| 0.0, share > 0.01R 0.0
  - heat_fade_short: n 14433, max |diff| 0.0, share > 0.01R 0.0
- orb20_a 1-min re-simulation vs the recorded backtester r: n 2827, median |diff| 0.0, share > 0.05R 0.2204, re-sim exp -0.0026 vs recorded -0.0.
- intraday_momentum 1-min re-simulation vs the recorded backtester r: n 1149, median |diff| 0.0, share > 0.05R 0.0279, re-sim exp -0.0618 vs recorded -0.0674.
- Raw signal bars without a feature row (dropped): max share 0.0.

### Anecdote: the owner's 10 trades of 2026-10-08 (+ GEV). One paper session - a diagnosis, not evidence

Guards at the live signal bar (block = the guard rejects that bar; under the layer rule a later bar of the same day could still have entered). sim_* = the live fill re-walked on 1-min bars with the live stop/target and engine costs (cur, E1, E2). C3/C6/C12 = confirmation entry time and its result with the live geometry, or 'dropped'.

| id | sym | setup | side | vwap % (SD z) | EMA9 % / slope 9,21 | RSI | CMF (rising) | OBV+ | ADX (DI gap) | VAH/VAL | G1k1 | G1k2 | G2e9 | G2e21 | G3a | G3b | G4 25/5 | G4 30/10 | G5 | Lr05 | Lr10 | Lm60 | Lm120 | r live | sim cur | E1 | E2 (stop R) | C3 | C6 | C12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 121 | IONQ | heat_fade_long | L | -2.03 (-1.79) | -0.72 / down,down | 13.0 | -0.168 (down) | no | 26.1 (-24.3) | below VAL | **block** | **block** | **block** | **block** | **block** | **block** | **block** | - | **block** | **block** | - | - | - | -1.00 | -1.05 | +0.36 | -1.14 (0.38) | dropped | dropped | dropped |
| 128 | ACN | exhaustion_short | S | +0.78 (0.49) | +0.78 / up,up | 77.6 | +0.161 (up) | no | 21.1 (+15.9) | above VAH | - | - | **block** | **block** | **block** | **block** | - | - | **block** | **block** | - | **block** | **block** | -1.04 | -1.02 | -1.02 | -1.04 (0.57) | dropped | dropped | dropped |
| 123 | Z | exhaustion_short | S | +1.73 (1.75) | +0.50 / up,up | 76.5 | -0.006 (down) | no | 32.8 (+25.3) | above VAH | **block** | **block** | **block** | **block** | - | - | **block** | **block** | **block** | **block** | **block** | - | - | -1.15 | -1.13 | -1.13 | -1.14 (0.89) | dropped | dropped | 1425: -1.13 |
| 118 | PATH | MF5 | S | +0.21 (0.38) | +0.24 / up,up | 79.1 | +0.010 (up) | yes | 15.4 (+12.4) | inside | - | - | **block** | **block** | **block** | **block** | - | - | - | - | - | **block** | **block** | -0.99 | -1.24 | -0.39 | -1.48 (0.49) | 1250: -1.24 | 1250: -1.24 | 1250: -1.24 |
| 108 | NOW | heat_fade_long | L | -1.58 (-1.53) | -0.37 / down,down | 19.1 | -0.026 (up) | no | 17.7 (-6.6) | below VAL | **block** | **block** | **block** | **block** | - | **block** | - | - | **block** | **block** | **block** | - | - | -1.04 | -1.03 | -1.03 | -1.05 (0.6) | dropped | dropped | 1150: +0.98 |
| 124 | LDOS | exhaustion_short | S | +2.82 (2.87) | +1.25 / up,up | 83.9 | +0.356 (down) | yes | 36.6 (+41.2) | above VAH | **block** | **block** | **block** | **block** | - | **block** | **block** | **block** | **block** | **block** | **block** | - | - | -1.11 | -1.04 | -1.04 | -1.27 (0.46) | dropped | dropped | 1420: -1.07 |
| 112 | SHW | MF3 | S | +0.42 (1.1) | +0.11 / up,up | 82.8 | -0.044 (down) | yes | 19.1 (+6.1) | inside | **block** | **block** | **block** | **block** | - | **block** | - | - | - | **block** | - | - | - | -1.15 | +0.76 | +0.76 | +1.05 (0.72) | 1055: -1.03 | 1055: -1.03 | 1055: -1.03 |
| 126 | NLY | exhaustion_short | S | +1.40 (2.67) | +0.64 / up,up | 77.1 | +0.067 (up) | yes | 43.9 (+30.3) | above VAH | **block** | **block** | **block** | **block** | **block** | **block** | **block** | **block** | **block** | **block** | - | - | - | -1.01 | -1.23 | -1.23 | -1.43 (0.54) | dropped | dropped | dropped |
| 127 | VTRS | exhaustion_short | S | +1.13 (1.88) | +0.45 / up,up | 76.5 | +0.443 (up) | no | 33.6 (+28.9) | below VAL | **block** | **block** | **block** | **block** | **block** | **block** | **block** | **block** | - | **block** | - | **block** | **block** | -1.01 | -1.25 | -1.25 | -1.38 (0.64) | dropped | dropped | dropped |
| 120 | BABA | heat_fade_long | L | -1.34 (-1.43) | -0.35 / down,down | 16.2 | -0.241 (down) | no | 19.6 (-14.2) | below VAL | **block** | **block** | **block** | **block** | **block** | **block** | - | - | **block** | **block** | **block** | - | - | -1.01 | -1.05 | +0.29 | -1.09 (0.58) | dropped | dropped | dropped |
| 113 | GEV | NS4 | S | +0.04 (0.05) | +0.03 / down,down | 29.8 | -0.117 (up) | yes | 21.2 (-0.2) | above VAH | - | - | - | - | - | - | - | - | **block** | **block** | - | - | - | -1.38 | -1.02 | -0.01 | +0.74 (1.5) | 1135: -1.02 | 1135: -1.02 | 1135: -1.02 |

P (amendment A) on 2026-10-08 (anecdote; adv filter not applied): first P bar and its result, R after costs.

| sym | fires | bar end | t1s1 | t1s1+E1 | t05s1 | t05s1+E1 | t1s05 | t1s05+E1 |
|---|---|---|---|---|---|---|---|---|
| ACN | True | 1245 | +0.99 | +0.99 | +0.49 | +0.49 | +0.99 | +0.99 |
| Z | True | 1055 | -1.17 | -1.17 | -1.17 | -1.17 | -0.67 | -0.67 |
| NLY | True | 1210 | +0.90 | +0.90 | +0.40 | +0.40 | +0.90 | +0.90 |
| VTRS | True | 1045 | -1.36 | -1.36 | -1.36 | -1.36 | -0.86 | -0.86 |
