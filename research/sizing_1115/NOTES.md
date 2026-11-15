Educational only — not financial advice.

# Sizing-up study 1115 — +5 / +10 / +15% size for Primary's less-traded setups (owner, chat 2026-11-15)

Owner: "explore sizing up some of the more lowly traded setups ... our number one setup [L3-gap-slope-fromopen-FD]
traded very frequently — keep sizing appropriate — but some of the other setups ... have more green days or more
consistent R and don't have as much risk of really bad days. Something like a 5, 10, 15% increase."

**Research only: no config, sizing, setup or ledger change.** Paper trading (Alpaca paper). Small samples throughout.

## Data / method
- Live journals of every account (`journal.db` on mcf-data, -testing (On Deck), -testing2 (Testing A), -livelab,
  -explore1, -testingd/e/f, -gen, -graveyard; EOD 11-13 / 11-14), run_id = 1, closed trades.
  R after costs = pnl_adj / (|entry − stop| × shares). Each setup's record is pooled over every account it ran in;
  session R = sum of its R on that date. Scripts: `load.py`, `stats.py`, `sim.py` (run from the repo root with
  `MCF_JOURNALS=<folder of <branch>.db copies>`); table `stats.csv`.
- No backtest re-run (not quick for the lab / NM setups); the live record is the evidence. Prior work: SZ-PROOF
  (research/ops/sizing_proof.md, 2026-10-27) — tiered 0.5x / 1x / 1.5x sizing failed its bar (12 configs).
- **Configurations tried: 6** = 2 qualifying rules (A strict, B loose) × 3 sizes (+5 / +10 / +15%). All reported.

## Rule-change context (owner rule 2026-11-02)
- **TEAM-6 in Primary from 11-11** (ledger 2026-11-10-team6-primary); before that NM-ETF ran in Testing 2 (to 11-04)
  and Live Lab (11-05..11-10); ST7 / NS5 / RW3 / RW5 / L3 ran in Primary and On Deck under earlier rosters.
- **LR3 + LR8 from 11-12:** live cost model (~−0.04R/trade, exit-linked) and cost-in latch / halt. Trades before 11-12
  were NOT rewritten, so every record below mixes two cost bases; the pre / post 11-12 split is shown.
- 11-13 Primary started late (09:46). TEAM-6 now open-ended (owner 11-15, ledger 2026-11-15-team6-open-ended).

## How sizing works now (Primary, config/default.yaml `account:`)
- shares = min(risk$ / |entry − stop|, slot$ / price), risk$ = 0.25% of equity (~$209 at $83.6k), slot$ = equity ×
  3.2 / 77 (~$3,480 now; 77 slots ≈ $306k of ~$321k buying power at full equity), per-setup cap 30 lots.
- **The slot (notional) cap binds on almost every Primary trade**, so actual $ risk per trade is far below 0.25%:
  mean $ risk on TEAM-6 days — NM-ETF $154 (73% of nominal; 3x ETFs, wide stops), L3 $76, NS5 $69, ST7 $41, RW3 $37,
  RW5 $25. Raising risk_per_trade_pct would change almost nothing; a size-up has to scale the lot itself.
- **There is no per-setup size multiplier** (grep mcf/execution, mcf/backtest: none; `mcf/report/team.py` SIZING_KEYS
  already lists `size_mult` / `risk_mult` only so the Team ignores such keys). See "Code needed" below.

## Per-setup live record (all accounts, run_id = 1, R after costs; to 2026-11-13)
| setup | trades | sessions | trades / session | green ses % | avg R / session | worst session R | std ses R | avg R/trade | avg R w/o best day (best share) | avg R pre / post 11-12 (n post) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Primary (TEAM-6)** | | | | | | | | | | |
| L3-gap-slope-fromopen-FD | 340 | 21 | 16.2 | 57 | +3.61 | −13.52 | 11.10 | +0.223 | +0.163 (44%) | +0.156 / +0.595 (52) |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 171 | 24 | 7.1 | 54 | +1.44 | −9.68 | 6.94 | +0.202 | +0.070 (70% `1 day`) | +0.204 / +0.183 (17) |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 185 | 24 | 7.7 | 58 | +0.96 | −14.54 | 6.54 | +0.125 | +0.022 (85% `1 day`) | +0.109 / +0.444 (9) |
| ST7-rsi50dn-long-pm-t1s1-FD | 43 | 15 | 2.9 | 67 | +0.43 | −2.66 | 1.72 | +0.150 | +0.061 (63% `1 day`) | +0.184 / −0.109 (5) |
| NS5-sma50-flush-oversold-long | 39 | 15 | 2.6 | 53 | +0.07 | −2.42 | 1.57 | +0.026 | −0.029 (211% `1 day`) | +0.020 / +0.128 (2) |
| **NM-ETF-late-dip-di-long** | 21 | 11 | 1.9 | **91** | +0.59 | **−0.61** | 0.56 | +0.311 | **+0.281 (22%)** | +0.327 / +0.217 (3) |
| **On Deck (second table)** | | | | | | | | | | |
| CWT09-gapdn-vwaploss-g10-short | 18 | 11 | 1.6 | 82 | +0.49 | −1.35 | 1.10 | +0.301 | +0.215 (48%) | +0.329 / +0.081 (2) |
| L3-gap-slope-lowdist-FD | 105 | 16 | 6.6 | 44 | +1.49 | −2.14 | 5.36 | +0.227 | +0.077 (76% `1 day`) | +0.077 / +0.569 (32) |
| L3-gap-slope-rsi5hi-FD | 138 | 20 | 6.9 | 55 | +0.77 | −3.58 | 4.15 | +0.111 | +0.021 (86% `1 day`) | +0.032 / +0.304 (40) |
| CWT05-flush-m05-v5-long | 18 | 10 | 1.8 | 50 | +0.14 | −1.46 | 1.27 | +0.076 | −0.016 (117%) | +0.006 / +0.322 (4) |
| NS1-rsidip-rsi5pop-long | 27 | 12 | 2.3 | 50 | +0.14 | −1.10 | 1.09 | +0.061 | −0.065 (183%) | +0.049 / +0.372 (1) |
| orb20_a | 42 | 19 | 2.2 | 53 | −0.03 | −2.92 | 1.92 | −0.012 | −0.145 (total red) | −0.029 / +0.322 (2) |
| CWT09-gapdn-bounce-g10-lowerhalf-short | 21 | 8 | 2.6 | 50 | −0.07 | −2.36 | 2.10 | −0.025 | −0.268 (total red) | +0.087 / −1.091 (2) |
| RW1-gapdn-bounce-flowsell-short-FD | 140 | 24 | 5.8 | 54 | +0.03 | −5.83 | 2.79 | +0.004 | −0.038 (862%) | +0.039 / −0.217 (19) |
| MF2-open-rsimidhi-flowsell-FD | 139 | 22 | 6.3 | 36 | +0.08 | −21.62 | 8.70 | +0.013 | −0.237 (1649%) | +0.055 / −1.121 (5) |
| ST6-volspikeup-short-mid-t1s1-FD | 37 | 8 | 4.6 | 63 | −0.45 | −3.70 | 1.90 | −0.097 | −0.132 (total red) | −0.029 / −0.144 (22) |
| NM-HL-T75-pm-long | 54 | 11 | 4.9 | 64 | −0.06 | −9.86 | 3.55 | −0.013 | −0.080 (total red) | −0.013 / – (0) |
| MF3-open-flowsell-rsi5hi | 63 | 12 | 5.3 | 58 | −0.78 | −10.42 | 3.78 | −0.148 | −0.236 (total red) | −0.185 / +0.582 (3) |
| MF4-h40-open-flowsell-FD | 170 | 25 | 6.8 | 44 | −1.71 | −17.09 | 4.56 | −0.251 | −0.295 (total red) | −0.251 / −0.236 (6) |

NM-ETF sessions: 10-19 +0.68, 10-22 +1.35, 10-28 +0.67, 11-02 +0.53, 11-04 −0.61 (Testing 2); 11-05 +1.46, 11-06
+0.36, 11-09 +0.90, 11-10 +0.54 (Live Lab); 11-12 +0.21, 11-13 +0.44 (Primary). Only 3 Primary trades; 10 symbols
(mostly SOXL / SOXS / TECL). The Guild (research/guild/1114, 11-14) found a small edge vs dipping ETF peers in
validation (+0.058R, t 2.36) but called it "found after the fact — a lead at most".

## Qualifying rules (2 tried)
- **A (strict):** ≤ 3 trades per traded session, ≥ 10 sessions and ≥ 15 trades, green sessions ≥ 60%, worst session
  ≥ −3R, avg R w/o best day > 0 and best-day share < 50% (no `1 day` tag).
- **B (loose):** as A, but best-day share < 70% (lets a `1 day` record in).
- Set after the table above was built (stated honestly; the thresholds follow the owner's words: low activity, more
  green days, no really bad days).
- **Primary result — A: NM-ETF only. B: NM-ETF + ST7.** NS5 fails (53% green, negative w/o best day); RW3 / RW5 / L3
  fail on frequency (7-16 trades a session; L3 is the setup the owner wants kept as is). ST7 fails A on its 63%
  best-day share (10-12 +4.05R) and is −0.109R on its 5 trades since 11-12.
- **On Deck — A: CWT09-gapdn-vwaploss-g10-short only** (82% green, worst −1.35R, +0.215 w/o best day, share 48% —
  borderline, 18 trades). It trades in On Deck (paper testing, ~$1k-lot rules), so a size-up there changes nothing
  that matters; it is the next candidate only if it is promoted.

## Simulation — Primary pro-forma (TEAM-6 setups' pooled live record, 26 dates)
R in base-size units (a 1.10x lot counts 1.10 × its R); $ = R × that setup's mean Primary $ risk on TEAM-6 days.
Book (all six at 1.00x): avg +5.67R / day, worst −26.63R (11-11), 2 days ≤ −15R; avg +$344, worst −$934
(pooled over accounts, so a pro-forma, not Primary's real history).

| config | Δ avg R / day | worst day | days ≤ −15R | Δ avg $ / day | per setup: green sessions gain / red sessions cost / worst-session extra |
|---|---|---|---|---|---|
| A NM-ETF ×1.05 | +0.013 | −26.63 (same) | 2 | +$1.9 | NM-ETF 10 better +0.36R / 1 worse −0.03R / −0.03R |
| A NM-ETF ×1.10 | +0.025 | −26.63 | 2 | +$3.9 | NM-ETF 10 better +0.71R / 1 worse −0.06R / −0.06R |
| A NM-ETF ×1.15 | +0.038 | −26.63 | 2 | +$5.8 | NM-ETF 10 better +1.07R / 1 worse −0.09R / −0.09R |
| B NM-ETF+ST7 ×1.05 | +0.025 | −26.58 | 2 | +$2.4 | + ST7 10 better +0.64R / 5 worse −0.32R / −0.13R |
| B NM-ETF+ST7 ×1.10 | +0.050 | −26.53 | 2 | +$4.9 | + ST7 10 better +1.28R / 5 worse −0.64R / −0.27R |
| B NM-ETF+ST7 ×1.15 | +0.075 | −26.48 | 2 | +$7.3 | + ST7 10 better +1.92R / 5 worse −0.95R / −0.40R |

- Every other setup is unchanged (0 better / 0 worse). The worst day barely moves (it was an RW3 / RW5 day).
- **−20R halt:** unaffected in practice — NM-ETF's worst session costs −0.09R more at ×1.15. Note the runner's halt
  and −2R latch count each trade's R on its OWN risk, so a 1.15x lot stopped out still counts −1R there while losing
  15% more dollars (see Code needed).
- **Buying power:** peak open notional on TEAM-6 days $113k (11-11, 35 lots), $152k (11-12, 49 lots), $40k (11-13);
  NM-ETF + ST7 held at most ~$20k at the peak (11-13), so ×1.15 adds ≤ $3k; one lot is ≤ $3.5k → ≤ $4.0k at ×1.15.
  At a full 77-slot book ($306k) a handful of 1.15x lots stays under the ~$321k limit (≤ 30 NM-ETF lots × $0.5k
  = $15k worst case would reach the limit, so a 1.15x lot should take the larger size only while open notional leaves room).

## Honest reading
- A 5-15% size-up scales wins and losses alike; the gain is only as real as the setup's edge. NM-ETF's 91% green
  sessions rest on 21 trades / 11 sessions, mostly in other accounts, with a Guild verdict of "a lead at most".
- The effect is small by construction: these setups trade ~2 times a session at ~$40-150 risk. +10% on NM-ETF ≈
  +0.06R / +$9 per session it trades; the whole book moves +$4 / day. It does not change Primary's profile.
- The bigger fact: the slot cap already holds Primary's less-traded setups at 20-35% of the nominal 0.25% risk
  (NM-ETF 73%). A "size by consistency" idea that matters would have to revisit the slot cap, which is a buying-power
  question (SZ-PROOF found tiering mostly balances out).

## Recommendation (decision SIZEUP1, open)
**Yes, NM-ETF-late-dip-di-long +10% in Primary (rule A), nothing else** — reply "SIZEUP1 yes" (= +10%),
"SIZEUP1 5" / "SIZEUP1 15" for another size, "SIZEUP1 B" to add ST7 at the same %, or "SIZEUP1 no". Review at its
20th Primary trade or the Friday TEAM review, step back to 1.00x if its Primary avg R w/o best day turns ≤ 0.
CWT09-gapdn-vwaploss-g10-short is the On Deck name to carry the same size if promoted.

## Code needed on yes (after hours, with ledger + tests; NOT done now)
1. Optional per-setup `size_mult` (strategies.<id>.size_mult, default 1.0, allowed 0.5-1.5) applied in
   `mcf/execution/risk.py` RiskManager.size() to BOTH the risk$ and the slot$ cap (the slot cap is what binds), and the
   same in `mcf/backtest/engine.py` sizing (line ~356) for live / backtest parity.
2. Buying-power guard: take the larger lot only if open notional + lot ≤ the account's buying-power budget, else 1.0x.
3. Halt / latch: decide whether the account −20R halt and the −2R latch count `size_mult × R` (keeps them in dollar
   terms; recommended) — today they count each trade's own R.
4. `mcf/report/team.py` already strips `size_mult` (Team sizes every trade the same) — no change. Tests for 1-3.
