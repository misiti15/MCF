Educational only — not financial advice.

# obs-genfeat — Setup Generator feature-level live tally (Observer, 2026-11-09 ~17:50 ET)

Lead's request lead-20261109-1658-4. Descriptive, **0 configs**. `genfeat.py <gen journal> 2026-11-09` -> `genfeat_out.txt`.
2,536 GEN live paper trades, 10-19..11-09, 85 setups; conditions read from `config/account_gen.yaml` gen.spec
(1 setup without a spec excluded: GEN-POD1022-03).

**Rule changes inside the window (ledger / yaml header):** per-setup -2R daily stop OFF from 10-22 (owner ST-A); slots 80 -> 200 and
16 -> 48 positions per setup from 10-26 (owner GX2). New GEN setups were added on most days 10-19..10-29, so each word's days differ.

## Failures / caveats first
- **No condition carries.** Of 39 conditions used by >= 3 setups and >= 30 trades, none is positive without its best day.
  Only 2 are positive at all (volumeRatio >= +0.02, rsi5 <= +0.02), and both turn negative without their best day.
- Words overlap (2-4 per setup) and are confounded with setup, side and window. A word used by 3 setups is mostly those 3 setups.
  This is a map for the owner, not evidence for any rule. At most 16 sessions.

## Drains (avg R without best day <= -0.30; book avg -0.224)
ret3_atr >= (-0.85, 76 trades), or_high_dist_atr <= (-0.78, 126), rsiSlope <= (-0.76, 90), sma20_dist_pct >= (-0.64, 56),
macd_hist >= (-0.59, 159 / 9 setups), upper_wick >= (-0.52), bars_since_lod <= (-0.43), breadth <= (-0.40, 291 / 10 setups),
ret3_atr <= (-0.37), qqq_fo >= (-0.34), rsiSlope >= (-0.34).
Mostly short-horizon momentum / "just moved" conditions (ret3, rsiSlope, macd_hist) in either direction, i.e. reacting to the last
15 minutes, plus a weak tape (breadth < x).

## Structure
- Geometry: tight brackets worst: t1s05 -0.91 (19 trades), t05s05 -0.55 (124); hold -0.29 (966); holdtr -0.19; t05s1 -0.13;
  t1s1 -0.11 (668). Consistent with Skeptic's cost-per-R point (tight stops pay the most cost per R).
- Window: LAM -0.52, OPEN -0.40 worst; LUNCH -0.10, PM -0.13; LATE +0.05 (153 trades, -0.15 without its best day).
- Side: long -0.21 (1,626), short -0.25 (908).
