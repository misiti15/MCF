# Live-funds readiness for Tuesday 2026-10-20

*Educational only — not financial advice.*

## Verdict: NOT READY. Recommendation: do not put real funds in on Tuesday. Stay on paper (QUESTIONNAIRE Q1 = A).

## 1. Is there a demonstrated edge after costs?

**In history: no.**
- 1,054,906 configurations were scored this weekend on the open 2-year history, with costs in.
- Not one clears its try-count bar together with the regime, walk-forward and same-minute-random gates.
- 0 of about 30 near-misses survived adversarial re-verification.
- The current live families are all **negative** on 2y history:
  - MF FD versions: −0.047 to −0.082R
  - NS: −0.028 to −0.068R
  - RW and exhaustion: −0.005 to −0.069R
  - ST and L3: −0.04 to −0.10R
  - heat and orb: below 0
  - CWT14: −0.084 to −0.094R, and no better than random entries at the same minute
- This repeats swarm1010 (about 1.3M configurations, no stock-specific edge after costs) and the BDI charter's
  conclusion.

**Live (paper): no.**
- Every account lost money over 10-06..10-16:
  - Primary: −0.175R last week, −0.210R this week
  - T1: −0.149R
  - T2: −0.180R
  - Broker P/L: −$688.81, −$768.59, −$2,262.52 and −$4,189.23
- Of the 52 setups with n ≥ 10, only 10 are positive, and none has more than 35 trades except RW7-FD (+0.03R, n 156)
  and CWT14-pdl-p10-lowvol (+0.03R, n 77).
- Paper fills are also optimistic: limit exits are flagged `touch_fill`.

**The config's own funding gate** (`gates:` in config/default.yaml) requires all of the following out of sample:
- ≥ 200 trades
- expectancy > 0
- profit factor ≥ 1.2
- win rate ≥ 65%
- ≥ 6 months

No setup meets it.

With negative expectancy, more capital means larger expected losses. Risk controls limit how fast that happens; they
do not create edge.

## 2. Risk controls that exist (paper-tested)

| control | status |
|---|---|
| Outage plan: stale-data detection, pause entries at 5 min, breakeven-protect winners at 15, flatten at 30; broker-down flatten | built (2026-10-15/16), drills in `tests/test_outage.py` and `mcf.execution.drill` |
| Pre-entry quote cross-check (2% / 300 s / 10 min) | built 10-16 |
| Independent watchdog (`.github/workflows/watchdog.yml`) | built, but runs in **dry mode** (only logs) |
| Daily loss limit `max_daily_loss_r: 20` | built; counts only **closed** trades |
| Per-trade risk 0.25% of equity; per-setup sleeve; max concurrent; trades/day | built |
| PTP exclusion (`universe.exclude_ptp`, §1446(f) 10% withholding) | built 10-16 (T2 lost −$374.72 / −$178.63 to withholding before it) |
| Prefix isolation (`mcf-`/`mct-`/`mt2-`; never touches others) | built |
| Setup freeze during market hours + `setup-freeze` PR check | built |

## 3. Missing before any real funds (docs/DECISIONS.md "before live" items, plus what this review found)

1. **An edge.** This is the blocking item; nothing below matters until it exists.
2. **Backup market-data feed.** Deferred "until real funds". Today a stale feed can only pause or flatten.
3. **Watchdog armed.** `MCF_WATCHDOG_MODE=act` is not set. Its dry-run summaries have not been reviewed.
4. **Daily loss limit including open P/L.** Today it counts closed trades only. And 20R × 0.25% means up to about 5%
   of equity per day before the halt, which is too loose for real money.
5. **Residual-lot rule review** (`lot_cap_ignore_residual_frac` 0.25). This is real exposure with real money.
6. **Tax / CPA (open, must be resolved before funding):**
   - short-term ordinary-income treatment
   - the wash-sale rule under constant re-trading
   - trader tax status and the 475(f) election
   - a reserve of about 30–35%
   - IRA limits
   - PTP withholding credits
7. **Profit-skim rule** (30% above the high-water mark, monthly) is not finalized.
8. **A separate account.** MCF shares the Alpaca paper account history with MarcoFlow, and real funds need their own
   account and keys.
9. **Journal/broker reconciliation gap.** T2 journal −$3,690.53 vs broker −$4,189.23 this week, partly PTP
   withholding. Unexplained gaps must be zero before funding.
10. **Fill realism.** Real limit-exit fills will be worse than paper touch fills, so live R would be lower than paper R.

## 4. On the owner's targets

- **"160 quality setups live-testable by Tuesday":** not achievable under the research rules. Quality setups found
  this weekend: 0 out of 1.05M configurations.
  - Reaching 160 would mean relabelling near-misses that are mostly noise. Rules 3, 4 and 14 forbid presenting them
    as quality.
  - What is possible: Testing-account forward observation of 5 well-behaved near-misses (PROPOSED_CONFIG §2, Q3).
    That is paper data, not quality.
- **"Better than last week / last 3 days":** no on both counts (see SUMMARY.md).

## 5. Recommendation

- **Tuesday:** no real funds. Keep all three accounts on paper.
- Clean out the losing setups through the rule-20 owner prompts (Q4–Q6).
- Build the missing live features (spy_fo, qqq_fo, breadth, symbols allow-list, trail/no-target geometries, Q8).
  Several near-misses cannot be tested forward without them.
- Run the pre-declared index-trend-filter study (Q10).
- Keep research effort on longer holding periods (research/longhold), as the 2026-10-10 charter already directs.
- **If the owner still wants real money on Tuesday** (Q1 = B), the least-bad form is a capped "plumbing pilot":
  - its purpose is to measure real fills and slippage, and it should be expected to lose money
  - a small fixed amount the owner is fully willing to lose
  - watchdog set to `act`
  - a hard daily dollar stop
  - only the watch-list setups
  - CPA items acknowledged
  This is not recommended.
