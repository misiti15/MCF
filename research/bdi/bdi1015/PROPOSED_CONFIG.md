# Proposed for 2026-10-16 (NOT applied) - BDI 2026-10-15

*Educational only - not financial advice.* Nothing here was written to `config/` or `mcf/`. Apply only after 16:00 ET
(rule 9, `setup-freeze`), only with the owner's decision, and only after the code change in section 1b has landed
(another agent is editing the runner / reconcile now).

## 1. Testing 1: IDX6 gap-down + early-low bounce on TQQQ (optional; weak evidence)
Evidence: `NOTES.md` Part B, `pcdip_results.csv` (row fam gl, QQQ, 0.5, 09:55, TRAIL, 3x), `pcdip_trades_dev.csv`,
`today1015_out.txt`. It is the only one of the 80 new configurations that passed the pre-declared comparison rule
against the open-based version (`PLAN.md`).
- DEV: n 43, +0.160R, t 0.89. IDX1 TRAIL: +0.003R (n 8). 42 of the 43 days are days IDX1 did not trade.
- Holdout, scored once: n 10, +0.007R.
- The research bar is **not** met (t 3.77).
- It **fails** the rule-19 regime gate: down sessions -0.65R, up sessions +0.96R.
- It is fading: H2 +0.001R, 2026Q1 -0.11R, 2026Q3 -0.22R.
- This would be a forward paper test only. My recommendation is to add it only if the owner wants the prior-close
  family watched forward. The SPY version of the owner's idea did **not** qualify (section B of `NOTES.md`).

### 1a. `config/account_testing.yaml`, under `strategies:` (after IDX5)
```yaml
  # ---- Index gap-down + early-low bounce V6: QQQ opens >= 0.5% below the prior close and prints a low >= 0.10% below the open by 09:55 (bdi1015). Long only.
  IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [TQQQ]
    signal_symbol: QQQ
    dip_ref: prior_close        # NEW option (default "open"): dip, recovery and stop buffer measured from the prior close
    dip_pct: 0.0                # vs the prior close; the two gates below do the selecting
    gap_min_pct: 0.5            # NEW: QQQ open <= prior close x (1 - 0.5%)
    below_open_pct: 0.10        # NEW: QQQ running low <= open x (1 - 0.10%) on a bar that has closed by dip_by
    dip_by: "09:55"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20         # of (QQQ prior close - QQQ running low)
    stop_buffer_frac: 0.10      # of (TQQQ prior close - TQQQ running low)
    target: null
    trail_r: 1.0
    trail_after_r: 1.0
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/bdi1015", variant: V6-GL, bar: "forward test; research bar not met (t 0.89 vs 3.77); holdout once n 10 +0.007R; regime gate fails"}
```
`live.setup_order`: insert `- IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail` after `- IDX5-spy050-0945-3x-trail`.
IDX1 trail and IDX1 hold also trade TQQQ. Their days overlap with IDX6 on 1 of 43 DEV days, and
`max_lots_per_symbol: 3` covers all three.

`config/setup_names.yaml`, then sync `docs/live/setup_names.json`:
```yaml
IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail:
  name: Index Gap-Down Bounce 6 TQQQ
  side: long
  what: "QQQ opens >= 0.5% below yesterday's close and dips >= 0.10% below its open by 09:55; buy TQQQ (3x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of its drop from yesterday's close. Stop just under TQQQ's morning low; trail 1R behind the best once +1R; out by 15:55."
```

### 1b. Code change needed (describe only; not made here)
1. `mcf/strategies/index_dip.py`:
   - Change the signature to `find_trigger(idx, dip_pct, dip_by, entry_from, entry_until, trigger, recovery_frac,
     ref=None, gap_min_pct=None, below_open_pct=None)`.
   - `ref` defaults to the session open (today's behaviour). The threshold becomes `ref x (1 - dip_pct/100)`.
   - With `gap_min_pct` set, return None unless `open <= ref x (1 - gap_min_pct/100)`.
   - With `below_open_pct` set, the dip also needs `run_low <= open x (1 - below_open_pct/100)` by `dip_by`.
   - Recovery becomes `close >= run_low + recovery_frac x (ref - run_low)`. Add `gap_pct` to the returned dict.
2. `IndexDipBounce`:
   - New param `dip_ref` in {`open` (default), `prior_close`}. Raise on any other value.
   - With `prior_close`, the signal reference is the signal symbol's prior close: `ctx.prev_close` when the signal
     symbol is the traded symbol, otherwise `ctx.peer_prev_close[signal_symbol]`. If that value is missing, there is
     no signal.
   - `build_signal(..., ref=ctx.prev_close)` uses `drop = ref - running low` for the stop buffer.
   - Meta gets `dip_ref` and `idx_gap_pct`.
3. `mcf/strategies/base.py` `DayContext`: add `peer_prev_close: dict | None = None`. It is filled by the backtester
   (`SymbolHistory.prev_close` of the pinned peers) and by the live runner (the priors' previous daily close for
   pinned `signal_symbol`s, which already includes SPY and QQQ). This touches the runner, so it waits for the other
   agent's runner and reconcile edits.
4. Tests (`tests/test_index_dip.py`):
   - A synthetic gap-down session fires with `dip_ref: prior_close` and not with `open`.
   - With the default, the IDX1-IDX5 trades do not change.
   - Parity: `build_strategies` on the YAML above reproduces the 43 DEV trades of `pcdip_trades_dev.csv`
     (fam gl, QQQ, 0.5, 09:55, TRAIL, instr 3x).
5. Prior close is the previous session's last RTH close. That is the backtester's `prev_close`, and the research used
   the same definition.

### 1c. `research/ledger.jsonl` (only if approved), then `python -m mcf.research.ledger check`
```json
{"id": "2026-10-16-testing-idx6-gapdn", "date": "2026-10-16", "title": "Testing 1: add IDX6 gap-down + early-low index bounce on TQQQ (dip_ref prior_close)", "patch": {"testing.strategies.IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail": [null, "added (class index_dip_bounce, dip_ref prior_close, gap_min_pct 0.5, below_open_pct 0.10, dip_by 09:55, rec 0.20, trail 1R after 1R)"], "testing.live.setup_order": ["...", "IDX6 after IDX5"]}, "evidence": ["research/bdi/bdi1015/PLAN.md", "research/bdi/bdi1015/NOTES.md", "research/bdi/bdi1015/pcdip_results.csv", "research/bdi/bdi1015/pcdip_trades_dev.csv"], "metrics_at_approval": {"configs_tried": 80, "lineage_configs": 1214, "bar_t": 3.77, "bar_met": false, "dev": {"n": 43, "exp_r": 0.160, "t": 0.89, "ex_best": 0.079, "H1": 0.621, "H2": 0.001, "down": -0.65, "up": 0.96}, "open_based_IDX1_trail_dev": {"n": 8, "exp_r": 0.003}, "holdout_once": {"n": 10, "r": 0.007}}, "approved_by": "owner (pending)", "notes": "Forward paper test only; regime gate fails; fading in 2026. Educational only - not financial advice."}
```

## 2. Primary: NS2 review (owner decision; scorecard flag, not a new test)
`NS2-sma50break-overbought-short` is flagged "below backtest - review":
- Live: 52 trades, -0.500R, -$825.79, against +0.021R expected.
- History (nightly1015 `bt1015_results.csv`): +0.004R, t 0.07, n 3,124. Up sessions -0.06R, down +0.16R, so it fails
  the rule-19 regime gate.
- Today: 42 shorts, -$788.87.

If the owner demotes it, this mirrors NS3 (ledger `2026-10-14-demote-ns3`):
- `config/default.yaml` `NS2-sma50break-overbought-short`: `enabled: false   # DEMOTED to Testing 1 2026-10-15 (owner; ledger 2026-10-16-demote-ns2): 4 sessions -0.500R/trade (n 52), backtest +0.004R`
- `config/account_testing.yaml`: replace `NS2-sma50break-overbought-short: {enabled: false}   # replaced by ...-FD`
  with
  ```yaml
  NS2-sma50break-overbought-short:
    enabled: true
    former_primary: {demoted: "2026-10-15", first_testing_session: "2026-10-16", review_after_sessions: 10}
  ```
  and add `- NS2-sma50break-overbought-short   # former primary (demoted 2026-10-15)` to `live.setup_order` after
  `- NS2-sma50break-overbought-short-FD`.
- Add the `former_primary` marker in `config/setup_names.yaml`, and a ledger entry.
- Caveat: the nightly's H1 test found that NS2's clustered first signals are historically its better half. Today's
  burst is one bad outcome of a basket that is flat on history. Demoting it is a risk call, not an edge finding.
