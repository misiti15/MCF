# Weekend swarm 2026-10-17: no quality setups found, not ready for live funds on Tuesday

*Educational only — not financial advice. Paper trades and history backtests only, with costs always in.*

## Is this week better?
**Than last week: no.**
- Primary did worse per trade: −0.175R → −0.210R. It lost a little less per session (−$185 → −$154). NS2 alone lost −$826 and the rest of Primary made +$57.
- T1 went from −0.041R on its single session (10-09) to −0.149R, −$445 per session.
- T2 started 10-12, so there is no last week to compare. This week it made −0.180R, −$738 per session.

**Last 3 sessions (10-14..16) vs the 3 before: worse in every account.**

| account | prior 3: avg R / P/L per session | last 3: avg R / P/L per session |
|---|---|---|
| Primary | −0.078 / −$72 | −0.340 / −$264 |
| T1 | −0.052 / −$207 | −0.212 / −$542 |
| T2 | −0.076 / −$412 | −0.261 / −$955 |

The cause was two trend-down days and one trend-up day, against setups that trade against the trend. Trades against the index lost −0.24R to −0.63R on those days.

## Search results
- **Configurations scored: 1,054,906** across 13 group studies (7 setup-family reworks and 6 arena runs), plus 15 replays of the live week.
- **Candidates: 0 survived.** About 30 near-miss modules went through adversarial re-checks. Every one fails its multiple-testing bar `max(1.5, sqrt(2 ln N))`, which sits at 4.57–5.25. Many also fail for other reasons:
  - one or two days carry the result (mostly the April 2025 tariff days);
  - they are near-copies of setups already live (over 60% the same trades);
  - the live runner can't compute something they need (SPY/QQQ move from the open, market breadth, an ETF-only list).
- **Final candidates: 0.** There was nothing to score on the locked block, so I never loaded it. It stays clean. On your 160 quality setups: 0 found.
- The best-behaved near-misses are an AM gap-down dip-buy (long), a late-day ETF dip with high ADX (long), and an L3 short while SPY is up in the afternoon. None reaches quality.
- The live families are negative over the 2-year history, and no rework variant clears the bar.

## Readiness for Tuesday 2026-10-20: not ready
- Nothing shows an edge after costs, either in history or in live paper trading. Every account lost money and no setup meets the funding gate in `config/default.yaml`.
- These items are still open before any real funds:
  - the watchdog only logs (dry mode); it doesn't act;
  - there is no backup data feed;
  - the daily loss limit counts closed trades only, and at 20R it allows about 5% of equity per day;
  - the residual-lot rule hasn't been reviewed;
  - the tax/CPA questions are unresolved;
  - the profit-skim rule isn't final;
  - there is no separate live account;
  - T2's journal and broker P/L differ by about $500.
- **Recommendation: stay on paper.** If you insist on real money, the least-bad option is a small capped pilot to measure real fills, expected to lose. I don't recommend it.

## What's proposed, nothing applied
- **Testing 1 (paper only):** 5 tagged near-misses as forward observation, with YAML and a draft ledger line. They are not candidates. I haven't checked how much they overlap with each other.
- **Move to the Graveyard (never delete):**
  - 11 Testing 1 setups (RW6-ns2-FD, NS2-FD, heat_fade_long-FD, ST1-FD, exhaustion_short-FD, two L3-FD, MF1-FD, RW2-FD, heat_fade_short-FD, ST2-FD);
  - the 3 former-primary setups (NS2, heat_fade_long, heat_fade_short) once their 10-session clock runs out;
  - CWT09 (both), CWT13-z05-short and CWT14-orl-p05-lowvol flagged for retirement.
- **Demote from Primary to Testing 1:** MF1, MF3 and MF5, after the 10-19 session.

## Files
All in /home/user/MCF/research/swarm1017/final/:
- PROPOSED_CONFIG.md
- READINESS.md
- QUESTIONNAIRE.md
- BACKLOG_ENTRIES.jsonl (58 entries in the `research/backlog.jsonl` format, no id clashes)
- NOTES.md
- modules/ (the 5 near-miss modules; each imports cleanly)

`research/swarm1017/SUMMARY.md` was **not written**: the harness blocked it. This text holds its content, so you can save it there. No config, ledger or backlog file was touched.

**Questionnaire:** /home/user/MCF/research/swarm1017/final/QUESTIONNAIRE.md has 15 numbered decisions, multiple-choice where possible, with the recommended answer marked on each.
