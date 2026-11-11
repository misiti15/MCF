# UNGAP — do UNEXPLAINED gaps (no news, no earnings, no sector move) behave differently from explained ones? (Scout, FROZEN 2026-11-10 21:20 ET, before any outcome)

*Educational only — not financial advice. Direction pilot of the day (Lead lead-20261110-2100-4). One look, kill line. Reuses the
OPTFLOW / NEWSDIR pilot data (60 top-adv names, 2026-08-04..11-06) + sector ETF daily bars (HODSEP download).*

## Family
Every gap-titled backlog entry with a recorded count (147 entries, 6,279 configs) + OD0950 2 + D2PM 3 + this 1:
**N ~6,285 -> full 4.18, BAR90 3.76.** (Huge swarm lineages > 5,000 excluded from the sum; it is a floor.)

## Hypothesis
A gap with a reason (news / earnings / a sector moving the same way) is information; a gap without one is more likely order
imbalance / noise and should FADE more during the session. Gaps carry direction that is 'already in the price'; the
question is whether the absence of a reason tells us the gap overshot.

## Definitions (fixed now)
- Gap = 09:30 open / prior close - 1; candidates |gap| >= 1%.
- **Explained** if ANY: (a) >= 1 Alpaca news item listing the name (single- or multi-symbol) published from the prior 16:00 to
  09:25 ET; (b) the name's sector ETF (SPDR with the highest daily-return correlation over 2026-06-01..08-01) gapped the same
  way with |sector gap| >= 0.4 x |stock gap|. **Unexplained** otherwise.
- Outcome: 09:50 one-minute open -> 15:55 close, ATR14 units, gross; ex-market minus beta1 x SPY; day-demeaned over the 60 names;
  signed by the GAP (positive = continuation, negative = fade).
- **The one look:** UNEXPLAINED minus EXPLAINED gap-signed outcome (same days where both exist; day-clustered t), and the
  unexplained fade itself (minus the gap-signed mean).
- **Kill line:** unexplained not below explained, or day-t > -2 for (unexplained - explained), or the unexplained fade <= 0 -> close.

## Pilot result (2026-11-10 ~21:30 ET) — CLOSED by the kill line (wrong sign)
3,777 name-days, 1,841 gaps >= 1% (explained 1,500: news 1,189, sector 828; unexplained 341). Gap-signed day-demeaned ex-market
09:50->15:55: explained -0.002 ATR (t -0.11); **unexplained +0.039 (t 1.49) - it CONTINUES, it does not fade.** THE LOOK, unexplained
minus explained: **+0.041 ATR, day-t 1.75** (unexplained lower on only 25 of 63 days) -> opposite to the hypothesis; kill line met.
After the look, not evidence: 'no-news gaps drift with the gap' could be informed flow, but n 341, t 1.49, one regime, 60 large caps.
