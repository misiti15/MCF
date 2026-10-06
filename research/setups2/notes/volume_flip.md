# volume_flip — short bursts of volume going the other way

Educational only — not financial advice.

## Search (train only, 2026-06-30..2026-08-25, 40 sessions)
- Grid: {context: RSI/RSI5 OB-OS, fromOpen in daily ATRs, VWAP distance in daily ATRs, SMA20 distance, pricePosition, near HOD/LOD}
  x up to 2 context layers x {flip: flow3 alone, flow3 vs flow9prev, volume climax + wick, climax + flow3 sign, bear/bull_div,
  rsiSlope turn, wick alone} x 6 time windows, both reversal (fade the move) and continuation (flip in the move's direction).
- 58,752 masks x 3 geometries = **176,256 configurations screened**; 1,013 passed the train viability filters.
- 20 diverse finalists taken to valid (2026-08-26..2026-09-15, 14 sessions). Script copies in the scratchpad, not in repo.

## What carried signal / what did not
- **Survived valid:** afternoon (13:00-15:00) bearish RSI divergence on a stock stretched >1% above its 5-min SMA20 with RSI5 > 90.
  - t1s1 (volume_flip_1): train n=839, 21/day, win 39.7% target-first, exp +0.204R ±0.027, PF 1.79, halves +0.25/+0.16;
    valid n=131, 9.4/day, win 41.2%, exp +0.174R ±0.071, PF 1.61, green days 71%. Valid baseline short t1s1 = +0.020R.
    (Many trades end at the timed exit with partial gains, so target-first win rate understates it; binary breakeven ≈ 51%.)
  - t05s1 (volume_flip_2): train win 66.5%, exp +0.111R, PF 1.54; valid win 62.6%, exp +0.084R ±0.050, PF 1.39.
    Binary breakeven ≈ 68% win; it is profitable only because timed exits add to it — thin margin, prefer the t1s1 version.
  - Valid first half is ~flat (-0.01 / -0.03R); all the valid edge came in the second half. Only 14 valid sessions: t ≈ 2.5, treat as tentative.
- **Failed valid (regime-dependent):** morning "oversold + fresh selling after buying" short continuation (train +0.157R, valid -0.18R);
  long reversals after a >1 ATR drop (lower wick, near-LOD + rsiSlope turn, flow3 flip, climax + buying) — train +0.09..+0.14R,
  valid -0.08..+0.04R; upper-wick/climax fades near HOD — train +0.11..+0.14R, valid negative. These look like products of
  the train period's market direction, not of the volume flip itself.
- Tighter variants (SMA20 > 2% + pricePosition > 0.9) were best on train (+0.30R) but too rare on valid (n=28) and flat.
