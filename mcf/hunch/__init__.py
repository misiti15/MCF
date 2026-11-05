"""Hunch: a research-only next-bar guesser (owner-approved research tool, 2026-11-04).

Hunch predicts ONE simple metric of the NEXT 3-minute bar (M1 first: does the next bar close higher than this
bar's close?) from the indicators MCF has, point in time. Every guess is scored right / wrong, every learner
updates on the scored guess (walk-forward, online, never refit on the future), then guesses again. The hit rates of
the single-indicator learners show which indicators can be trusted. A metric is "done" when a learner holds a
consistent 65%+ hit rate (rolling 20-session hit rate >= 65% in >= 90% of VALID windows); the owner then moves the
ladder on (it never advances on its own).

Research tool only: it never places orders and touches nothing in config/ or the trading path.

Design (owner 2026-11-04): each Hunch is ONE combined learner using ALL the indicators together; one Hunch runs per
ticker (20 -> 100 -> 200 tickers), each learning online from its own scored guesses, plus a pooled model that learns
from all tickers at once. Single-indicator learners are a small diagnostic only.

Modules
  data      1-min cache (or live bars) -> 3-min RTH bars -> point-in-time features (rule-19 locked block never read)
  metrics   the metric ladder (config list, one active at a time) and the baselines' rules
  learners  pooled online logistic, per-ticker online logistic, light boosted trees, single-indicator diagnostics
  replay    the walk-forward replay, scoring, statistics and the markdown / PNG report
  live      the live shadow (real guesses on live bars, no orders; .github/workflows/hunch.yml -> mcf-data-hunch)
  scale     the 20 -> 100 -> 200 comparison page
  __main__  CLI: python -m mcf.hunch replay --metric M1 ; live --dry [--loop] ; scale

Educational only - not financial advice.
"""
