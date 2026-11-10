Educational only — not financial advice. Live = paper fills.

## live walk-forward (descriptive)
| run | sessions | rule R/setup-session | static | diff | t | swaps |
|---|---|---|---|---|---|---|
| live h=3 | 14 | -0.060 | +0.239 | -0.299 | -1.69 | 3 |
| live h=5 | 14 | -0.054 | +0.239 | -0.293 | -1.63 | 1 |
| live LIGHT h=3 | 14 | +0.224 | +0.239 | -0.015 | -0.58 | 3 flags |
| live LIGHT h=5 | 14 | +0.222 | +0.239 | -0.017 | -1.73 | 1 flags |

## rule vs Team vs Primary set (live R per setup-session)
| day | rule (8) | Team (n) | Primary set |
|---|---|---|---|
| 2026-11-05 | +0.765 | +2.419 (9) | +0.588 |
| 2026-11-06 | -0.848 | -0.104 (9) | +0.834 |

## Monday 11-09 light version (live, 20 sessions through 11-06)
| setup | trades | avg R | green | wob | worst | flag |
|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 44 | -0.056 | 0.47 | -0.127 | -2.68 | keep |
| L3-gap-slope-rsi5hi-FD | 46 | -0.006 | 0.50 | -0.081 | -2.42 | keep |
| MF2-open-rsimidhi-flowsell-FD | 53 | +0.316 | 0.50 | +0.205 | -2.43 | keep |
| MF4-h40-open-flowsell | 14 | +0.233 | 0.80 | +0.143 | -0.79 | keep |
| MF4-h40-open-flowsell-FD | 68 | +0.010 | 0.65 | -0.047 | -2.86 | keep |
| NS1-rsidip-rsi5pop-long | 15 | -0.131 | 0.38 | -0.211 | -1.10 | FLAG (sit out) |
| NS5-sma50-flush-oversold-long | 23 | -0.001 | 0.45 | -0.097 | -2.42 | keep |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 62 | +0.232 | 0.58 | +0.106 | -2.29 | keep |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 60 | +0.293 | 0.68 | +0.237 | -2.34 | keep |
| ST7-rsi50dn-long-pm-t1s1-FD | 32 | +0.186 | 0.67 | +0.067 | -2.66 | keep |

shadow S2 top-10 on live (all live, qualify >= 30 trades): [('MF4-h40-open-flowsell', np.float64(0.98), 14, np.float64(0.143)), ('RW5-heat30-flowsell-rsi5pop-gapdn-short-FD', np.float64(0.94), 60, np.float64(0.237)), ('RW3-gapdn-rsi5pop-flowsell-short-FD', np.float64(0.908), 62, np.float64(0.106)), ('MF2-open-rsimidhi-flowsell-FD', np.float64(0.842), 53, np.float64(0.205)), ('ST7-rsi50dn-long-pm-t1s1-FD', np.float64(0.82), 32, np.float64(0.067)), ('RW1-gapdn-bounce-flowsell-short-FD', np.float64(0.798), 69, np.float64(0.002)), ('L3-gap-slope-rsi5hi-FD', np.float64(0.748), 46, np.float64(-0.081)), ('CWT09-gapdn-bounce-g5-lowerhalf-short', np.float64(0.74), 43, np.float64(-0.06)), ('heat_fade_long', np.float64(0.732), 65, np.float64(-0.028)), ('MF4-h40-open-flowsell-FD', np.float64(0.73), 68, np.float64(-0.047))]
weakest 3 Primary by S2: [('NS1-rsidip-rsi5pop-long', np.float64(0.525)), ('L3-gap-slope-fromopen-FD', np.float64(0.585)), ('NS5-sma50-flush-oversold-long', np.float64(0.685))]
