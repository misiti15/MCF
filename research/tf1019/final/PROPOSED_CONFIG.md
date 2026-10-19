# Proposed config from the timeframe swarm 2026-10-19

*Educational only — not financial advice.*

## Survivors: none

0 of 640 configurations passed the pre-declared gates (lineage-scaled t, train > 0, valid > 0, regime up AND down > 0
with n >= 30, walk-forward share >= 0.6, excess over the random same-minute baseline > 0). See `TIMEFRAMES.md`.

**There is no Testing 2 YAML to add and no ledger line to write.** `config/*.yaml`, `research/backlog.jsonl` and
`research/ledger.jsonl` were not touched. The live setups keep running on 5-minute decision bars as today.

## The live `bar_minutes` option was not added — code that would be needed

A survivor on 1/3/10/15-minute bars could not be deployed today. `LabStrategy` (`mcf/strategies/setups.py`) only
receives `DayContext.prior5` (the last `PRIOR5_BARS = 60` prior-session 5-minute bars, `mcf/strategies/base.py`),
so indicators on other bar sizes would warm up differently live than in research. The work, if a future survivor
justifies it (it is not justified by this swarm; see backlog `tf1019-primary-no-bar-minutes`):

1. `mcf/strategies/base.py`: add `prior1: pd.DataFrame | None` (prior sessions' 1-minute bars, enough for the
   longest lookback at the largest bar size, e.g. 750 minutes for SMA50 on 15m) to `DayContext`.
2. `mcf/execution/session.py` `prep` / `mcf/data/priors.py`: fetch and cache those 1-minute prior bars
   (SIP, same feed as live) alongside `prior5`.
3. `mcf/backtest/engine.py` `SymbolHistory.context`: fill `prior1` the same way, so the backtester and live agree.
4. `LabStrategy`: accept `bar_minutes: m` from config; resample today's 1-minute bars plus `prior1` with
   `resample(df, f"{m}min")`, apply the same (m-5)-minute tod shift as `research/tf1019/data/build_tf.py`
   so `tod` is the true bar-close HHMM, and decide only on m-minute bar closes.
5. Tests: live/backtest parity on a recorded day for m in {1,3,10,15}, and m=5 identical to today's path.

This is a strategy-affecting change (rule 16): it would go through the backlog and a swarm first, and could only be
merged outside 09:30-16:00 ET (`setup-freeze`).

## Template, for the record only (do not apply)

What a survivor entry would have looked like in `config/account_testing2.yaml`, once step 4 exists:

```yaml
# NOT PROPOSED — no survivor. Shape only.
- name: <setup>-<m>m
  type: lab
  module: <research module path>
  bar_minutes: <m>          # requires the DayContext.prior1 work above
  window: [<hhmm>, <hhmm>]
  geom: <t1s1|t05s1|t1s05>
  min_adv: <usd>
```

Ledger lines: none.

*Educational only — not financial advice.*
