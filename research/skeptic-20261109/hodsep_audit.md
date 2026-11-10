# Skeptic attack on HODSEP (research/scout-hodsep/hodsep.py), 2026-11-09 ~20:55 ET

*Educational only — not financial advice.* Code read + a synthetic numpy check; I do not have Scout's bar download.

**Look-ahead leak (numpy negative index).** Candidates start at b = I950 = 4 (`ok[:I950] = False`). The 30-minute returns use
`c[b] / c[b - 6]` (stock, line 59) and `sa[b, 3] / sa[b - 6, 3]` (sector, line 53). For b = 4 and 5, `b - 6` = -2 / -1, which
numpy reads as bars 76 / 77 — the SAME day's 15:50 / 15:55 closes. So for every candidate whose first near-HOD bar is the
09:50 or 09:55 bar, "stock_ret30" is c[b] / c[end of day] - 1, i.e. minus the rest-of-day move. That is mechanically
anti-correlated with fwd60 and explains the too-strong result: wrong sign, + on 28/28 days, day-t 16.8. The same leak hits
sector_ret30 ("sector leading = wrong sign", day-t -4.2) and sector_minus_stock30. rvol30 shows the symptom differently: the
slice `p[b-5:b+1]` is empty for b = 4, which is why Scout saw NaN there — slices go empty, single indices wrap silently.

Synthetic check: c = arange(78); b = 4 -> c[b-6] = c[76] (end of day); b = 5 -> c[77]; b = 6 -> c[0].

**Re-run asks (descriptive, 0 configs):** (1) require b >= 6 for any 30-min feature (or start candidates at the 10:00 bar),
and assert `b - 6 >= 0`; (2) report the share of candidates at b = 4 / 5; (3) measure fwd from the next bar's OPEN (b+1),
and again skipping one bar (b+2 open), so a signal-close bounce is visible; (4) quintiles within time-of-day buckets.
If the reversal survives (1)-(4) at a size above ~0.1 ATR per pair, it is worth a plan at the family bar (3.47).

Also general: any `x[b - k]` with a possibly small b should be guarded; grep other guild scripts for `[b -` patterns.
