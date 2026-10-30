Educational only — not financial advice.

# pdl1030 / entry-confirm — PLAN (written before any variant was scored, 2026-10-30 ~05:10 UTC)

Lineage: Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-*). Family: entry confirmation / timing.
Data: open two-year frames, TRAIN (2024-10, 2025-03..12) + VALID (2026-01..03, 2026-07..09-15) only. 348 sessions.
HOLD months (2026-04..06, 2026-09-16..10-07) and the locked block (2024-11-01..2025-02-28) are never loaded.

## Common to every config (unchanged from parent p05)
- Signal kernel: `S6.b3_any` PD long, p = 0.05 ATR poke under PDL, reclaim close > PDL within 3 bars, any volume
  (= live CWT14-failbrk-pdl-p05-long). Signal bar 09:50-15:00, adv20 >= 95M, daily ATR > 0.
- Exit = top5_1028 `sim` mechanics: R = 0.25 x daily ATR, stop entry - 1R (stop checked first), target +0.5R,
  scale-out half at +0.25R with stop to break-even (p05 live), flat 15:55. Costs: 1c/share + 1 bp per side x tod
  multiplier, +2c on stop exits, x3 extended tier (|gap| >= 20% or price < $5).
- One trade per symbol-day. A signal whose confirmation fails RE-ARMS: the next reclaim signal that day may trigger
  (keeps exposure; shifts entry rather than removes trades). Per symbol-day the confirmed candidate with the earliest
  entry bar is taken.
- Limit fills are conservative: the bar's low must trade 1c THROUGH the limit; the fill bar is checked for the stop,
  never the target (same as sim lim).
- Parent parity first: p05 TRAIN+VALID must match swarm15 (n 53,326, -0.0677R) within 0.005R, and my
  generalized simulator (given entry bar/price) must reproduce the original sim exactly for the parent.

## Configurations (18; each scored on TRAIN and VALID; all counted)
Bars are 5-minute; i = reclaim (signal) bar. "Known at" = when the condition is known.
| id | rule | entry | known at |
|---|---|---|---|
| C01 hold1 | bar i+1 closes > PDL | close i+1 | close of i+1 |
| C02 hold2 | bars i+1, i+2 close > PDL | close i+2 | close of i+2 |
| C03 hold3 | bars i+1..i+3 close > PDL | close i+3 | close of i+3 |
| C04 hold6_nolow | bars i+1..i+6 close > PDL and no bar low < day low as of i | close i+6 | close of i+6 |
| C05 hold2_strict | bars i+1, i+2 lows >= PDL (never back under) | close i+2 | close of i+2 |
| C06 followthru3 | first bar in i+1..i+3 closing > high of bar i, all closes before it > PDL | that close | that close |
| C07 retest6 | first bar in i+1..i+6 with low <= PDL + 0.05 ATR, close > PDL, low > day low as of i (all prior closes > PDL) | that close | that close |
| C08 lim_pdl | buy limit PDL + 0.02 ATR, valid bars i+1..i+3 | limit | limit resting from close of i |
| C09 lim_mid | buy limit (close_i + PDL)/2, valid i+1..i+3 | limit | close of i |
| C10 lim_025R | buy limit close_i - 0.25R, valid i+1..i+3 | limit | close of i |
| C11 lim_mid_fallback | C09; if unfilled by i+3 and close i+3 > PDL, buy close i+3 | limit / close i+3 | close of i+3 |
| C12 hold2_spy | C02 and SPY close at i+2 >= SPY close at i | close i+2 | close of i+2 |
| C13 hold1_spy | C01 and SPY close at i+1 >= SPY close at i | close i+1 | close of i+1 |
| C14 skip_far | skip reclaim if close_i > PDL + 0.15 ATR (re-arms) | close i | close of i |
| C15 = C04 + entry cost <= 5% of R | | | entry bar (price, tod, tier known) |
| C16 = C12 + entry cost <= 5% of R | | | entry bar |
| C17 = C08 + entry cost <= 5% of R (cost at limit price / fill tod) | | | order time (limit price, fill bar tod; conservative: tod of i+1 mult) |
| C18 = C02 + entry cost <= 5% of R | | | entry bar |

Entry cost fraction = tier x (0.01 + price x 1e-4) x tod-multiplier / R (swarm15 K1 definition).

## Bar (rule 22 BAR90)
N = 121,459 + 3 x 18 = 121,513 -> 0.9 x sqrt(2 ln N) = 4.355. Pass needs: day-clustered t(TRAIN+VALID) >= 4.355,
walk-forward >= 54% months positive, avg R > 0 on TRAIN and on VALID separately, beats p05 parent on both, exposure
>= 76.6 trades/session (50% of p05's 153.2) or >= 25/session. Also reported: up/down SPY-session R, avg R without
the best session and its share.

## Addendum (written after C01-C18 were scored, before C19 was scored; disclosed, counted)
C01-C18 all failed. One more config, chosen BECAUSE C13 was the best pure entry-confirm row (so it is a
post-hoc pick and counted): C19 = C13 (hold1 + SPY not lower at i+1) + entry cost <= 5% of R. Total configs = 19,
N = 121,459 + 3 x 19 = 121,516, bar 4.355.
