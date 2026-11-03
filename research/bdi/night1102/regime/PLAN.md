Educational only — not financial advice.

# regime (night1102) — pre-declaration, written after the LIVE scoring and BEFORE any two-year switch was scored

Live switch scan (switch_live.csv): 57 rule x state combinations x 5 books = 285 configurations on 20 live sessions.
Carried to the two-year check (chosen on live only, by largest "vs random thinning" on the Primary / core books):

- **A  fade@10:00** — after 10:00 ET, new shorts only if SPY is at or above its 09:30 open at 10:00; new longs only if
  SPY is below its open. (best on Primary live: kept 53%, +43.3R vs -32.1R, vs-random t 1.45)
- **B  calm-open short skip** — after 09:50, no new shorts when SPY's 09:30-09:50 range is below 0.30 x its prior
  20-session median daily range. (best on core7 live: kept 81%, +179.0R vs +168.6R, vs-random t 2.15)
- **C  fade@09:50 VWAP** — after 09:50, shorts only if SPY is at/above its session VWAP at 09:50; longs only if below.
  (best on all-account and short books live)

Pass test on two years (fixed now): in BOTH TRAIN and VALID, on the book it is proposed for, kept avg R > parent avg R,
vs-random-thinning > 0 with day-clustered t >= 1.0, and kept avg R positive in at least 2 of 3 EOD types.
The full 57-rule two-year table is also produced and reported, but no rule is chosen from it.
