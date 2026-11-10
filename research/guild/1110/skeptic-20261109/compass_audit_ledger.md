# Skeptic: compass backfill audit + market-state try-count ledger (2026-11-10 ~01:00 ET)

*Educational only — not financial advice.* Code read of research/compassbf/backfill.py and mcf/report/compass_live.py.

## Backfill audit — PASS on construction, one tie to fix before Scout reads tags
- Point-in-time: `snap()` keeps bars with start minute `m < T` (closed by T); `compute(now=16:05)` then emits every mark,
  each from its own prefix of bars. Breadth = research/hunch/universe200.txt via `CL.universe()`; VWAP = typical price x
  volume from 09:30; open = first bar's open — identical to live because it is the live function, imported unchanged.
- Split adjustment: harmless for these fields — fo, VWAP side and breadth are within-day ratios; an adjustment factor
  scales the whole day (prices and the volume weights alike) uniformly.
- Validation: 17/17 fields 100% on 48 marks, but 41 of them were late backfills from the same API and only 2 days exist.
  It proves same code + same data, not live timing. That is acceptable for a research table; the >= 95% rule is met in
  form, and there is no better live record to test against.
- **Tie (fix):** `mark_entry = max(t for t in MARKS if t <= m)` with m = lab entry minute (entry bar close). Lab tods are
  5-min bar ends, so ~1/3 of entries sit exactly on a 15-min mark and get the mark computed from bars that close at the
  same instant. Live publishes mark T no earlier than T + 1 min (`t_now >= T + 1`), and the job runs on a cadence after
  that. Same for the m1030..m1200 tags (`em >= mk`). Use strict `<` (or mark <= entry - 5 min) so the tag is a mark live
  would already have had. Small effect, but it is look-ahead and it sits exactly where flips are measured.
- Survivorship: breadth uses today's Hunch-200 list back to 2024 (mild; note it with any breadth result).

## Try-count ledger for the rolling compass (switch setups on/off by market state)
| lineage | configs |
|---|---|
| regime1022 gate lineage (gates1021 718 + bdi1021 196 + regime1022 340) | 1,254 |
| regime1009 market-signal gates (1,020 gated + 32 signal) | 1,052 |
| GATE1 compass gates | 112 |
| HC1 + COMP15 | 68 |
| FLOW1 book sensor (64 + 16 SPY/VWAP control rules) | 80 |
| GATE2 (15 + 8 reporting looks) | 23 |
| BURST2 compass gates C / C-sym | 5 |
| swing L8 IWM guard | 8 |
| RCOMPASS flip looks | 3 |
- **Broad (same bet: gate setups by market state): N 2,605 -> full 3.97, BAR90 3.57.**
- Narrow (intraday compass readings only: GATE1, HC1/COMP15, FLOW1, GATE2, BURST2 C, RCOMPASS): N 291 -> 3.37 / 3.03.
- My recommendation: the broad N for any Testing move (Lead's "harder bar when in doubt"). That bar is very hard for a gate
  on ~450 sessions, so the realistic route for an owner-directed standby rule is: pre-register ONE rule from the 2-year
  descriptive split, then judge it on >= 20 forward shadow sessions (RESEARCH_RULES 18: past 4 looks, a lineage is judged
  on forward sessions). Say this to the owner up front so expectations match.
