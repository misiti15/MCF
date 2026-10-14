# Top 3 primary trades, 2026-10-13: what went right, and what more was available

*Educational only — not financial advice. These are three live paper trades from one session. Treat everything here as a diagnosis that produces hypotheses; none of it is evidence. No locked holdout was scored and 0 configurations were tested on history (rule 7). All "what-if" figures are gross, computed on SIP 1-minute bars, and assume touch fills. A scale-out adds one more exit fill (about 1c/share).*

Sources:
- `journal.db` on `origin/mcf-data`: run 1 "MCF Update (live paper)", trade ids 323, 336 and 322.
- `signals.info` for each trade.
- `research/bdi/nightly1013/trades.csv`.
- Alpaca SIP 1-minute bars, 10-01 to 10-13, read-only.
- Setup modules `research/owner1008/NS2-sma50break-overbought-short.py` and `research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py`.
- Entry features recomputed with `mcf.research.heat.heat_frame` and `setup_lab.extra_features` on 5-minute bars.
- Scratch scripts are in `swarm1013c/` (`an.py`, `alt.py`, `feat.py`, `gf.py`).

## The three trades

| # | trade | entry (ET) | fill | stop / target | R ($/sh) | sh | exit | P/L | MFE / MAE in trade |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SEI NS2-sma50break-overbought-short | 11:00:56 | 77.68 | 78.855 / 76.795 | 1.175 | 24 | target 11:25 at 76.78 | **+$21.60** (+0.77R) | 0.99R / 0.16R |
| 2 | PANW MF5-flowsell-vwapup-rsi5hi | 12:15:43 | 402.78 | 407.07 / 398.61 | 4.29 | 4 | target 15:54:50 at 398.43 | **+$17.40** (+1.01R) | 1.07R / 0.06R |
| 3 | AMD NS2-sma50break-overbought-short | 10:45:30 | 591.23 | 597.12 / 585.91 | 5.89 | 3 | target 11:26 at 585.83 | **+$16.20** (+0.92R) | 0.96R / 0.11R |

All three are shorts with a t1s1 geometry: R = 0.25 × daily ATR, and the target is 1R from the **signal reference price**, not from the fill. All three were market entries, filled at the bid.

### Setup rule values at entry (5-minute decision bar)

| | rsi14 | rsi5 | fromOpen % | gap % | vwapDist % | sma50 dist % | heat | buyPressure | 10-12 close → fill | 3-day return to 10-12 |
|---|---|---|---|---|---|---|---|---|---|---|
| SEI (NS2) | 63.0 | 50.2 | +2.07 | −3.82 | +0.60 | +0.07 (cross) | −13 | +0.47 | 79.28 → 77.68 (**−2.0%**, gap 47% filled) | +3.7% |
| AMD (NS2) | 80.6 | 67.4 | +2.43 | −2.80 | +1.22 | +0.23 (cross) | −37 | +0.25 | 594.13 → 591.23 (**−0.5%**, gap 83% filled) | −8.0% |
| PANW (MF5) | 74.8 | 96.1 | +1.34 | −1.57 | +0.13 | +0.27 | −31 | −0.46 | 403.83 → 402.78 (**−0.3%**, gap 83% filled) | −0.4% (−3.6% on 10-12) |

NS2 needs: a cross above the 5-minute 50-bar SMA on this bar, RSI(14) ≥ 60, fromOpen > 2% and a 09:50–11:30 window. MF5 needs: heat ≤ −30, buyPressure < −0.25, vwapDist > +0.05%, RSI(5) > 70 and a 09:50–15:00 window. Every rule was met.

### Market and sector context (% from the open)

| | 10:45 | 11:00 | 11:25 | 11:35 | 11:47 | 12:15 | 12:30 | 15:54 |
|---|---|---|---|---|---|---|---|---|
| QQQ | +0.45 | +0.30 | +0.20 | +0.06 | +0.14 | +0.39 | +0.57 | +0.51 |
| SMH | +0.83 | +0.44 | +0.14 | −0.27 | +0.15 | +0.72 | +1.42 | +1.53 |
| IGV | +0.70 | +0.54 | +0.74 | +0.66 | +0.38 | +0.73 | +0.83 | +0.37 |
| IWM | −0.57 | −0.66 | −0.61 | −0.71 | −0.80 | −0.64 | −0.61 | −0.37 |

- **SEI and AMD were entered as QQQ and SMH began a 45-minute fade** (10:45 → 11:35). Both hit target inside that fade.
- The 11:47 → 12:30 tech rebound is the move that stopped the other four NS2 shorts (SWKS, CORZ, TTMI and CBRS).
- PANW was entered at the IGV mid-day high (+0.73%). IGV gave back half of that by the close.

## Per-trade path and what more was available

### 1. SEI: +$21.60. The target was hit early and the stock kept running, then gave it all back.
- **Fill.** The fill was 0.145 below the reference price (spread 23 bps), so the bracket left the short with **0.885 to target against 1.175 to stop (0.75:1 instead of 1:1)**. That cost about 0.25R before the trade started.
- **Path.**
  - Reached +0.5R at 11:19 (18 min) and the target at 11:21.
  - Kept falling to **75.05 at 11:47 (+2.24R from the fill)**, with only 0.16R adverse along the way.
  - Then reversed with the tech rebound and closed at 77.95 (−0.23R).
- **Alternatives:**
  - 1R from fill: +$28.20.
  - 1.5R: +$42.
  - 2R: +$56.
  - No target, trail 0.5R once at +0.75R or +1R: **+$49.02 (1.74R)**.
  - 50% at target, then trail the rest by 0.5R: +$35.
  - Hold to 15:55: −$9.
  - 50% at target, rest moved to breakeven and held: +$10.6. Breakeven was hit at 13:23.
- **Re-entry** short at 76.53 after the exit, with a 1R target: +1R (it reached 75.05 before the 13:23 stop).
  - NS2 did not re-fire. A re-entry would need a new rule.

### 2. PANW: +$17.40. The best-managed of the three. A fixed target late in the day was close to optimal.
- **Path.**
  - Reached +0.5R at 13:01 (46 min). Spent 220 minutes in the trade with at most **0.06R** adverse.
  - The target filled at 15:54:50. The 15:55 bar printed the day low, 397.05 (+1.33R).
- **Alternatives:**
  - Hold to the flatten: about +$18–23. That is +0.1R to +0.3R more than the target, depending on the 15:55 print.
  - Every trail variant equals the hold.
  - There was no time for a re-entry.
- **What was left.** At most 0.3R. It sat in a slow drift, so no exit rule would have changed much.

### 3. AMD: +$16.20. The fixed target was the right exit. Every "let it run" variant was worse.
- **Path.**
  - Reached +0.5R at 10:52 (7 min) and the target at 11:26.
  - The low was 584.66 at 11:35, only **+1.11R**.
  - Then a +3.2R move against the short: it closed at 603.93, **−2.16R** for a holder.
- **Alternatives:**
  - 1R from fill: +$17.68.
  - 1.5R or more: −$17.68 (stopped at 12:25).
  - Hold: −$17.68.
  - 50% at target, then trail the rest by 0.5R: +$13.4.
  - No target, trail 0.5R after 1R: +$10.9.
  - 50% at target, then trail behind the prior 5-minute high: +$16.0.
- **Re-entry** at 585.68: stopped at 12:00, **−1R**.

### Summary of alternatives (the 3 trades, gross $; actual = $53.88 at the target price)

| exit policy | SEI | PANW | AMD | sum |
|---|---|---|---|---|
| actual (target 1R from reference) | 21.24 | 16.69 | 15.95 | **53.88** |
| target 1R from **fill** | 28.20 | 17.17 | 17.68 | 63.05 |
| target 1.5R | 42.29 | 18.40 | −17.68 | 43.01 |
| hold to 15:55 (stop only) | −9.36 | 18.40 | −17.68 | −8.64 |
| 50% at target, rest breakeven and hold | 10.62 | 17.55 | 7.97 | 36.14 |
| 50% at target, rest trail 0.5R | 35.13 | 17.55 | 13.41 | 66.09 |
| 50% at target, rest trail prior 5-minute high | 34.62 | 17.55 | 16.00 | 68.17 |
| no target, trail 0.5R once MFE ≥ 0.75–1R | 49.02 | 18.40 | 10.87 | **78.29** |
| re-entry after target (1R target) | +28.2 | n/a | −17.7 | +10.5 |

**Size.** Shares came out at roughly $1.6–1.9k notional, so dollar risk was uneven: SEI $28 against PANW and AMD about $17. A larger size scales P/L linearly. Three winners chosen after the fact say nothing about whether more size would pay, because the same rule would have enlarged the four NS2 losers too (−$140 on the day).

## What made them right (conditions at entry; descriptive only)
1. **Immediate follow-through.** MAE was 0.06–0.16R in all three. The losers SWKS, CORZ, TTMI and CBRS had MAE of 0.90–1.23R.
2. **A short into the gap-fill retrace, from below the prior close, on a gap-down day.**
   - Gaps were −1.6% to −3.8%. The retrace reached +1.3% to +2.4% from the open, and the fill was 0.3–2.0% below the 10-12 close.
   - Two of four NS2 losers (SWKS and CBRS) were shorted **above** the prior close. CORZ and TTMI were below it, so this does not separate cleanly.
3. **The index was rolling over.** QQQ and SMH were fading 10:45–11:35, when the NS2 winners worked. PANW's sector (IGV) faded into the close.
4. **Not a deep multi-day washout.** The 3-day return to 10-12 was +3.7%, −8.0% and −0.4%. The NS2 losers SWKS, TTMI and CBRS were −10.5%, −14.0% and −16.3%: oversold names that bounced with the 11:47 rebound. Only CORZ (−5.7%) breaks this split.
5. **What did not separate them.** RSI, heat and vwapDist overlap between winners and losers (EBAY, HCA and PBR winners included).

## Testable rule candidates (backlog, train/valid only; no edge claim from n = 3)

| id | rule | why (today) | test |
|---|---|---|---|
| T3-a | **Anchor the bracket on the fill**: target and stop = fill ± R, not reference ± R | SEI lost 0.25R to fill slippage. On the 3 trades: +$9.2 | NS2/MF5/all t1s1 setups, lab with the live spread model |
| T3-b | **Scale-out**: 50% at 1R, then trail the rest by 0.5R from the best price (variant: behind the prior 5-minute bar's high) | +$12–14 over actual on the 3 trades; it is robust to AMD's reversal. Breakeven-and-hold is worse (+$36) | NS2 and MF5 train/valid. Report win%, avg R and the extra fill cost |
| T3-c | **No fixed target**: trail 0.5R once MFE ≥ 0.75R (or ≥ 1R) | Best here (+$78), carried by SEI's 2.24R run | Same as T3-b, and compare against 1R fixed |
| T3-d | **Index-aware runner exit**: close the short's runner when QQQ (or its sector ETF) reclaims its 5-minute VWAP or makes a new 30-minute high | The 11:47 tech rebound erased SEI's 2.2R and AMD's 1.1R | Shorts on all setups. Exit timing only |
| T3-e | **Hold to the flatten after 15:00** when MFE ≥ 0.75R and MAE ≤ 0.25R (target removed, breakeven stop) | PANW: +0.1R to +0.3R | MF5 entries after 12:00 |
| T3-f | **NS2 filter**: skip if the 3-day return is < −10%; variant: require the fill below the prior close on gap-down days | 3 of 4 NS2 losers failed the first condition, all winners passed | NS2 train/valid. Count the trades removed |
| T3-g | **Fast-follow-through scaling**: add a second lot only if +0.5R is reached within 20 minutes with MAE < 0.25R | SEI and AMD (7 and 18 min). PANW was slower (46 min) | All setups. Must also be judged against the stacking losses (nightly1013) |
| T3-h | **Re-entry after a target** only when the index is still below its 5-minute VWAP | Blind re-entry: SEI +1R, AMD −1R (net about 0), so blind re-entry is not supported | Shorts; needs a fresh-signal definition |

Number of configurations tried here: 0 on history. 10 exit variants and 2 re-entries were applied descriptively to 3 trades. Any finalist from this list needs the backlog gates (`mcf/research/backlog.py`) and a single locked-holdout score before it goes live.
