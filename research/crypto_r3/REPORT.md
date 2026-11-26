Educational only — not financial advice
# Crypto round 3: clean traded-only bars, daily trend vs buy-and-hold, vol-regime hours (2026-11-26)
**Verdict: no survivor, nothing to the backlog.** 0 of 17 configs is FIT-eligible (best day t 2.22 vs bar 3.82). LOCKED stays sealed. Crypto is not live, so no rule, config or ledger change applies inside any window. Pre-registered in `PREREG.md` (sha256 d05b1d37…, commit e91c942964) before scoring; FIT outputs committed (db3e992eeb) before CHECK ran. **N_cum = 1,460 + 17 = 1,477; noise bar 3.82.** CHECK (2025-01..2026-05-25) is on its **third look**, so its bar was raised to t ≥ 1.5.
- **Clean data:** signal bars use only minutes with a real trade (after the Amendment-1 bad-print filter); fills as in round 2. Traded minutes since 2023: BTC 51/12/22/35% (2023/24/25/26), ETH 49/7/14/25%, SOL 68/2/10/16%. A trades-endpoint probe on zero-volume minutes returned no trades, so trades add nothing beyond the volume > 0 bars. 0 MB downloaded (optional step cut).
- **Near-miss re-check on clean bars (information only, not counted):** 8 of 10 round-2 near-misses lose FIT strength (515 t 2.61→2.10, 743 2.44→2.04; 869 rises 1.38→1.95, 688 flat). On CHECK: 515 −0.21R, 743 −0.05R, 545 +0.13R (−0.65R w/o its best day), 863 +0.02R (t 1.19), the other 6 negative. Round-1 ids 31/477/459 get worse: FIT −0.12/−0.28/−0.20R, CHECK −0.61/−0.54/−0.33R. Clean bars rescue none of them.
- **Daily trend (9 configs, BTC+ETH+SOL in 3 equal sleeves, long only, maker entry at the close, taker exit, tier 1).** This is **swing/daily, outside MCF's intraday charter** unless the owner widens scope.

| id | rule (close > SMA L) | FIT ret | FIT Sharpe | FIT maxDD | CHECK ret | CHECK Sharpe | CHECK maxDD | CHK expo | CHK n | CHK avgR (t) | FIT t | CHK Sharpe pct vs random |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | **buy-and-hold** | **+3,546%** | **0.86** | **95%** | **−37.6%** | **−0.25** | **59%** | 100% | — | — | — | — |
| 980 | A regime, L50 | +285% | 0.89 | 56% | +7.6% | 0.32 | 32% | 44% | 47 | +0.03 (0.48) | 1.66 | 97% |
| 981 | A regime, L100 | +19% | 0.33 | 68% | −5.6% | 0.04 | 27% | 41% | 36 | +0.00 (−0.34) | 1.03 | 69% |
| 982 | A regime, L200 | +222% | 0.96 | 51% | −23.6% | −0.39 | 34% | 39% | 21 | −0.19 (−0.95) | 2.22 | 39% |
| 983 | B 20d breakout / 10d low, L50 | +190% | 0.87 | 50% | +10.9% | 0.42 | 23% | 30% | 29 | +0.10 (0.68) | 2.00 | 93% |
| 984 | B, L100 | +54% | 0.50 | 53% | +4.5% | 0.25 | 21% | 22% | 22 | +0.01 (−0.05) | 1.92 | 84% |
| 985 | B, L200 | +148% | 1.05 | 34% | +3.8% | 0.24 | 18% | 15% | 15 | +0.03 (0.10) | 2.11 | 79% |
| 986 | C RSI3<20 pullback, L50 | +7% | 0.19 | 28% | −3.7% | −0.19 | 13% | 4% | 16 | −0.09 (0.01) | 1.54 | 62% |
| 987 | C, L100 | −36% | −0.54 | 41% | +6.4% | 0.41 | 10% | 7% | 19 | +0.06 (0.77) | −1.34 | 89% |
| 988 | C, L200 | −8% | −0.03 | 21% | −2.6% | −0.01 | 16% | 10% | 23 | −0.00 (0.56) | −0.27 | 73% |

- **Reading:** the trend filter does its real job, **cutting drawdown**: CHECK max DD 10-34% vs 59% for buy-and-hold, and 8 of 9 configs beat buy-and-hold's CHECK Sharpe (−0.25). In the 2025-26 decline 980 and 983 beat 93-97% of random entries with the same exposure. **On return, buy-and-hold wins FIT by a mile** (+3,546% vs at most +285%, nearly all SOL at ~100×, a survivor-biased winner). No config has a trade-level t near the bar (best 2.22), and the CHECK edge is thin on 15-50 trades (980 avg R w/o best day −0.07, 983 +0.01).
- **Maker entries starve a trend system:** realistic maker fills are 34-68% for rule A on FIT because the limit misses the runaway days. FIT 980 makes +285% with maker entries vs +2,050% with taker entries (sensitivity only); on CHECK the two are close (+7.6% vs +4.3%). Fee tier 3 changes CHECK by ≤ +3 points.
- **Vol-regime hours (8 configs: top 1%/2% |1h move| vs a trailing 30-day distribution, cont/rev long, maker 60 min, stop max(3 ATR, 3%), hold 4/24 h):** **all 8 lose on FIT** (−0.03 to −0.21R, t −1.1 to −6.1) **and CHECK** (−0.16 to −0.28R, 126-330 trades). Continuation has a small gross edge (FIT +0.10R at 24 h on top-1% hours, beating 96-100% of random hours) but costs 0.12-0.14R; reversal is gross-negative. Best FIT: 990 (cont, top 1%, 24 h) −0.03R.
- **Biases:** survivorship (BTC/ETH/SOL are 2021-26's winners, which flatters longs and buy-and-hold most); SOL traded in only 2% of 2024 minutes; trend exits are at daily decisions only, with no intraday stop.
- **Tests:** `tests/test_crypto.py` 26 pass. Full suite: 951 pass, 1 skip; `test_poll_log` overhead (a 0.25 s wall-clock assert, unrelated to crypto) failed in both full runs and passes alone.
- **Next:** (1) **Owner decision:** is swing/daily crypto in scope? If yes, pre-register ONE trend-overlay hypothesis (980/983-style, taker or hybrid entry), judge it by Sharpe and max DD vs buy-and-hold rather than trade t, and score it once on LOCKED. (2) Intraday: continuation after top-1% hours is the only gross-positive lead (+0.10R vs 0.13R cost); it needs cheaper exits (maker target, tier 3) or a tighter venue. (3) Otherwise park crypto intraday on Alpaca: 1,477 configs, no edge after costs.
