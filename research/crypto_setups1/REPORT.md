Educational only — not financial advice
# Crypto setups round 1: the first 8 hand-built setups (14 configs, 2026-11-26)
**Verdict: no testing candidate and no near-miss** (under the pre-declared definition). 0 of 14 configs is FIT-eligible (best FIT t +1.16 vs bar 3.82). Nothing goes to the backlog; LOCKED stays sealed. Crypto is not live, so no rule, config or ledger change falls inside any window.
- **Pre-registered** in `PREREG.md` (sha256 db0fb19e…, commit cb84327dd8) before scoring; FIT frozen in f3818d0159 before CHECK (4th look, bar t ≥ 1.5). **N_cum = 1,477 + 14 = 1,491; noise bar 3.82.** Cards: `SETUPS.md`. Engine: `mcf/crypto/setups1.py` (maker limits filled only when traded through; absolute stop and target levels).
- **Columns:** share = best-day share ("—" when total R ≤ 0). Years = avg R 2021/22/23/24 (FIT) and 2025-26 (CHECK). "rand %" = share of 100 same-exposure, same-geometry random-entry reps beaten on FIT. "act %" = days with a position (in brackets: BTC-below-SMA50 days).

| id | setup / var | FIT n | fill | FIT avgR | w/o best (share) | FIT t | win | cost R | maxDD R | yrs + : 21/22/23/24/25-26 | rand % | CHK n | CHK avgR | w/o best | CHK t | act % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1478 | FLUSH-1 a BTC ETH | 262 | 80% | −0.264 | −0.277 (—) | −3.21 | 37% | 0.16 | 72 | 0: −.17/−.40/−.14/−.36/−.27 | 2 | 77 | −0.269 | −0.306 | −1.96 | 16 (9) |
| 1479 | FLUSH-1 b alts | 268 | 80% | −0.084 | −0.099 (—) | +0.10 | 47% | 0.13 | 35 | 0: −.02/−.15/−.05/−.24/−.27 | 78 | 81 | −0.274 | −0.310 | −2.07 | 12 (7) |
| 1480 | SHOCK-1 alts | 238 | 73% | −0.046 | −0.074 (—) | +0.16 | 49% | 0.12 | 23 | 1: −.01/−.15/+.09/−.14/−.17 | 94 | 53 | −0.166 | −0.196 | −1.13 | 14 (8) |
| 1481 | REV12-1 a | 37 | 54% | −0.306 | −0.356 (—) | −2.10 | 38% | 0.15 | 13 | 0: −.16/−.80/−.68/−.01/−.09 | 18 | 13 | −0.089 | −0.195 | −0.20 | 3 (3) |
| 1482 | REV12-1 b | 88 | 57% | −0.176 | −0.218 (—) | −1.40 | 42% | 0.13 | 20 | 2: +.03/−.62/−.38/+.04/−.03 | 40 | 18 | −0.030 | −0.186 | +0.07 | 4 (3) |
| 1483 | UPDIP-1 a | 13 | 23% | +0.070 | −0.081 (>1) | +0.00 | 54% | 0.14 | 4 | 3 on 1-6 trades/yr | 81 | 2 | +0.215 | −0.222 | +0.49 | 1 (0.3) |
| 1484 | UPDIP-1 b | 32 | 39% | −0.202 | −0.270 (—) | −1.24 | 44% | 0.11 | 6 | 1: −.94/−.33/+.02/−.29/−.46 | 28 | 1 | −0.460 | — | — | 3 (0.6) |
| 1485 | DAY2-1 a reclaim | 36 | 49% | −0.065 | −0.189 (—) | −0.59 | 56% | 0.08 | 7 | 2: +.06/−.14/–/–/+.32 | 54 | 14 | +0.323 | +0.062 | +0.49 | 2 (4) |
| 1486 | DAY2-1 b open | 92 | 64% | +0.091 | +0.025 (0.75) | +1.16 | 60% | 0.06 | 18 | 2: +.35/−.45/–/+.61/−.21 | 92 | 29 | −0.209 | −0.543 | −1.69 | 4 (7) |
| 1487 | WKND-1 a | 17 | 57% | +0.046 | −0.076 (>1) | +0.23 | 59% | 0.12 | 4 | 1: +.18/–/−.24/−.45/– | 71 | 0 | — | — | — | 1 (0.6) |
| 1488 | WKND-1 b | 33 | 59% | +0.132 | +0.013 (0.91) | +0.16 | 61% | 0.10 | 5 | 2: +.26/–/+.01/−.42/−1.15 | 93 | 1 | −1.146 | — | — | 2 (1) |
| 1489 | CPI-1 | 11 | 58% | −0.215 | −0.421 (—) | −0.24 | 36% | 0.24 | 3 | 1: −.69/−.04/+1.85/−1.26/−.20 | 58 | 2 | −0.201 | −1.275 | −0.19 | 0.5 (0.7) |
| 1490 | DIP-1 a | 104 | 87% | −0.198 | −0.232 (—) | +0.46 | 40% | 0.16 | 26 | 1: −.50/−.78/−.00/+.00/−.27 | 32 | 30 | −0.266 | −0.342 | −1.27 | 8 (3) |
| 1491 | DIP-1 b | 128 | 81% | −0.137 | −0.175 (—) | −0.10 | 40% | 0.12 | 22 | 1: +.05/−.27/−.01/−.32/−.34 | 53 | 40 | −0.338 | −0.400 | −1.69 | 9 (3) |

- **The bounce is real but thinner than the cost.** FIT gross per trade: FLUSH-1b +0.04R, SHOCK-1 +0.08R; costs 0.12-0.16R, even with maker entries and 3-4 % stops. Adverse selection eats most of ANATOMY's +54 / +106 bps: a limit below the print fills only when price keeps falling, and 28-31 % of flush fills then stop out. The majors' flush beats only 2 % of random entries. The alt flush and shock beat 78-94 % on FIT, but random entries lose too (−0.13R), and CHECK fades to 39-71 %.
- **Event setups are too rare to judge.** UPDIP, WKND, CPI and DAY2-a have 11-37 FIT trades, and their positive means rest on 1-2 days.
- **Closest (not near-misses):** 1486 DAY2-b is FIT +0.09R (w/o best +0.02R, t 1.16), carried by 2021 and 2024; it lost in 2022 and on CHECK (−0.21R). 1485 DAY2-a is CHECK +0.32R on 14 trades but FIT-negative. Both fit ANATOMY's finding that the bounce size depends on the regime.
- **Active now:** on the last readable day (2026-05-25), BTC was above its SMA50 (77.3k vs 76.9k), so all gates were on. In November 2026, BTC is below a falling SMA50 (KNOWLEDGE §0). That switches off FLUSH, SHOCK, REV12 and WKND (down-trend off) and UPDIP and DIP (uptrend gate). Only DAY2 and CPI (no gate) could fire. Historically, the setups held a position on 0.3-9 % of BTC-below-SMA50 days, and 78 % of those days meet the down-trend switch-off.
- **Capacity:** ≤ 1-2 % of daily prints is about $2-3k notional per BTC trade, $1-2k for ETH and $20-900 for the alts (ANATOMY §0). **Biases:** survivorship flatters longs; prices are last trades on a thin venue; the 2021-22 CPI dates are recalled from the BLS schedule [verify].
- **Paper trading a future candidate would need** (the owner decides): a dedicated crypto paper account (fees charged in our own P/L), a 24/7 runner, the failsafes in r1 MARKET_RESEARCH.md §4, a crypto change window (proposal: Sat 00-04 UTC, with a `setup-freeze` crypto variant), and a LOCKED score first.
- **Next:** at N = 1,491 there is still no intraday edge after costs on Alpaca spot. The levers left are outside the setup design: fee tier 3 or a tighter venue, an external liquidation or funding feed (a true liquidation trigger, not a price proxy), and the owner's call on swing scope for the trend overlay.
