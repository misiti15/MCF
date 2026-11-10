# Skeptic pre-audit of the earnings calendar for D1 (research-data: earnings_yf.parquet), 2026-11-10 ~07:00 ET

*Educational only — not financial advice.* Checks on the file itself (no prices here). 2-year window 2024-09-16..2026-11-09:
7,381 events, 1,010 symbols; locked-block rows absent (they are in a separate file — keep it that way).

Point-in-time traps, in order of damage:
1. **AMC = next session.** `date` is the REPORT date. For `amc` (3,439) the reaction and the surprise are only usable from the
   NEXT session's open. Using `date` as the event day for AMC rows makes the event day the day BEFORE the news.
2. **dmh = during market hours (225; hour 15:00 for 200 of them).** The surprise appears mid-session, after a 09:50 decision.
   Any rule that reads surprise at 09:50 on a dmh day uses the future. Drop dmh, or use them only after report_dt_et.
3. **Weekend report dates: 19.** Mislabels; map to the next session or drop, and say which.
4. **Surprise missing 11.5%** (eps_reported NaN). Do not fill; those days are 'unknown surprise', report them as a bucket.
5. **|surprise_pct| > 100%: 367 (5%)** — tiny estimates. Use the sign (or winsorise) as the plan says; never the raw %.
6. Six same-symbol events < 45 days apart: likely duplicates; dedupe before counting.
7. Survivorship: 1,010 of today's names; delisted reporters are missing (matters for short / gap-down results).
8. Vendor revisions: yfinance can restate eps_reported later; sign flips near 0 surprise are possible. Report |surprise| < 1%
   as its own bucket.

**Alignment check needed before any outcome read (Builder, prices on your side, 0 configs):** for each session type, median
|open gap| on the mapped reaction day vs the other candidate day (report date for AMC, next day for BMO). Mapping is right if the
reaction-day gap is clearly larger (expect ~2-3x). Post the table; Scout / Observer read outcomes only after it.

Would convince me (D1): sign(surprise) x sign(gap) direction at 09:50 -> 11:30 / 15:55, gross and ex-market, beating same-minute
random event-day names, in TRAIN and VALID, BMO and AMC separately, with the earnings-react / SC1 / gap-and-go family N.
