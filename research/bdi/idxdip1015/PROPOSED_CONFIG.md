# Proposed Testing-1 config — index open-dip bounce, 3x only (NOT applied)

*Educational only — not financial advice.* Prepared 2026-10-15 during market hours; **apply after 16:00 ET** (rule 9,
`setup-freeze`). Evidence: `NOTES.md` (sections "Owner change: 3x only" and the per-instrument grid below it).
The research bar (t >= 3.75 for the 1,134-config lineage) is **not met**; this is the owner's forward paper test in Testing 1.
Supersedes the earlier 21-setup proposal (owner change 2026-10-15): each variant trades only the highest-leveraged,
most-traded ETF that day. SSO / SPUU / QLD and the 1x ETFs are not traded by these setups.

## What to apply
1. `config/account_testing.yaml`, under `strategies:` — 5 setups. V2/V3/V5 use `trade_candidates: [SPXL, UPRO]` with
   `pick: max_dollar_volume` (the one with more dollar volume from 09:30 through the trigger bar trades; the other
   gets no signal). V1 trades TQQQ with two exits (trail, hold). `scale_out_r: null` is required (the global
   `exits.scale_out_r: 1.0` would otherwise bank half at +1R). Clock times stay quoted.
2. `config/account_testing.yaml`, `live.setup_order` — prepend the 5 names.
3. `config/setup_names.yaml` — the 5 entries below; then sync `docs/live/setup_names.json`
   (`tests/test_setup_names.py::test_dashboard_copy_in_sync`).
4. `research/ledger.jsonl` — the line below; then `python -m mcf.research.ledger check`.
5. Code is in place: `mcf/strategies/index_dip.py` (`trade_candidates` / `pick`; `symbols` still works),
   `pinned_symbols` adds `trade_candidates` (so SPXL and UPRO are always in the universe and priors, and their bars are
   in `DayContext.peers` for the pick). Tests: `tests/test_index_dip.py`; full suite 214 passed.
   Parity: `scripts/make_config.py` builds these 5 through `build_strategies` and reproduces `pick3x_trades.csv` (5/5).

Checks before the first session: `data/universe.csv` / priors contain SPXL, UPRO, TQQQ, SPY, QQQ (pinned).
The chosen ETF is in the signal meta (`picked`, `pick`, `dv_SPXL`, `dv_UPRO`) of the journal row and the trade's symbol.

## 1. strategies (append under `strategies:`)
```yaml
  # ---- Index open-dip bounce V1: QQQ down >= 1.0% from the open by 09:55 (owner 2026-10-15, research/bdi/idxdip1015). Long only.
  IDX1-qqq100-0955-TQQQ-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [TQQQ]
    signal_symbol: QQQ
    dip_pct: 1.0
    dip_by: "09:55"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20
    stop_buffer_frac: 0.10
    target: null
    trail_r: 1.0
    trail_after_r: 1.0
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/idxdip1015", variant: V1, bar: "forward test (owner request); research bar not met"}
  IDX1-qqq100-0955-TQQQ-hold:
    enabled: true
    class: index_dip_bounce
    symbols: [TQQQ]
    signal_symbol: QQQ
    dip_pct: 1.0
    dip_by: "09:55"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20
    stop_buffer_frac: 0.10
    target: null
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/idxdip1015", variant: V1, bar: "forward test (owner request); research bar not met"}
  # ---- Index open-dip bounce V2: SPY down >= 0.75% from the open by 09:45 (owner 2026-10-15, research/bdi/idxdip1015). Long only.
  IDX2-spy075-0945-3x-trail:
    enabled: true
    class: index_dip_bounce
    trade_candidates: [SPXL, UPRO]
    pick: max_dollar_volume
    signal_symbol: SPY
    dip_pct: 0.75
    dip_by: "09:45"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20
    stop_buffer_frac: 0.10
    target: null
    trail_r: 1.0
    trail_after_r: 1.0
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/idxdip1015", variant: V2, bar: "forward test (owner request); research bar not met"}
  # ---- Index open-dip bounce V3: SPY down >= 0.75% from the open by 09:55 (owner 2026-10-15, research/bdi/idxdip1015). Long only.
  IDX3-spy075-0955-3x-trail:
    enabled: true
    class: index_dip_bounce
    trade_candidates: [SPXL, UPRO]
    pick: max_dollar_volume
    signal_symbol: SPY
    dip_pct: 0.75
    dip_by: "09:55"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20
    stop_buffer_frac: 0.10
    target: null
    trail_r: 1.0
    trail_after_r: 1.0
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/idxdip1015", variant: V3, bar: "forward test (owner request); research bar not met"}
  # ---- Index open-dip bounce V5: SPY down >= 0.5% from the open by 09:45 (owner 2026-10-15, research/bdi/idxdip1015). Long only.
  IDX5-spy050-0945-3x-trail:
    enabled: true
    class: index_dip_bounce
    trade_candidates: [SPXL, UPRO]
    pick: max_dollar_volume
    signal_symbol: SPY
    dip_pct: 0.5
    dip_by: "09:45"
    entry_from: "09:50"
    entry_until: "10:05"
    trigger: recovery
    recovery_frac: 0.20
    stop_buffer_frac: 0.10
    target: null
    trail_r: 1.0
    trail_after_r: 1.0
    scale_out_r: null
    testing: {added: "2026-10-16", source: "research/bdi/idxdip1015", variant: V5, bar: "forward test (owner request); research bar not met"}
```

## 2. live.setup_order (prepend)
```yaml
  setup_order:
    - IDX1-qqq100-0955-TQQQ-trail
    - IDX1-qqq100-0955-TQQQ-hold
    - IDX2-spy075-0945-3x-trail
    - IDX3-spy075-0955-3x-trail
    - IDX5-spy050-0945-3x-trail
    # ... existing entries unchanged ...
```

## 3. config/setup_names.yaml
```yaml
IDX1-qqq100-0955-TQQQ-trail:
  name: Index Dip Bounce 1 TQQQ
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy TQQQ (3x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under TQQQ's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX1-qqq100-0955-TQQQ-hold:
  name: Index Dip Bounce 1 TQQQ (hold)
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy TQQQ (3x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under TQQQ's morning low; no target, no trail; out by 15:55."
IDX2-spy075-0945-3x-trail:
  name: Index Dip Bounce 2 3x S&P
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy whichever of SPXL / UPRO (3x S&P) has traded more dollars since 09:30 (one trade; the journal shows which) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under the traded ETF's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-3x-trail:
  name: Index Dip Bounce 3 3x S&P
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy whichever of SPXL / UPRO (3x S&P) has traded more dollars since 09:30 (one trade; the journal shows which) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under the traded ETF's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-3x-trail:
  name: Index Dip Bounce 5 3x S&P
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy whichever of SPXL / UPRO (3x S&P) has traded more dollars since 09:30 (one trade; the journal shows which) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under the traded ETF's morning low; trail 1R behind the best once +1R; out by 15:55."
```

## 4. research/ledger.jsonl (one line)
```json
{"id": "2026-10-16-testing-idxdip", "date": "2026-10-16", "title": "Testing 1: add 5 index open-dip bounce setups (owner variants 1,2,3,5; 3x only: day's SPXL/UPRO pick, TQQQ)", "patch": {"testing.strategies.IDX*": [null, "added (5 setups, class index_dip_bounce; V2/V3/V5 trade_candidates [SPXL, UPRO] pick max_dollar_volume; V1 TQQQ trail + hold)"], "testing.live.setup_order": ["...", "IDX setups prepended"]}, "evidence": ["research/bdi/idxdip1015/PLAN.md", "research/bdi/idxdip1015/NOTES.md", "research/bdi/idxdip1015/results.csv", "research/bdi/idxdip1015/pick3x_results.csv", "research/bdi/idxdip1015/pick3x_picks.csv", "research/bdi/idxdip1015/dipstats.json", "research/bdi/idxdip1015/conflicts.csv", "tests/test_index_dip.py"], "metrics_at_approval": {"configs_tried": 1008, "configs_grid_per_instrument": 756, "configs_pick3x": 252, "lineage_configs": 1134, "bar_t": 3.75, "bar_met": false, "dev_rec20": {"V1_TQQQ_trail": {"n": 8, "exp_r": 0.0, "t": 0.01}, "V1_TQQQ_hold": {"n": 8, "exp_r": 0.15, "t": 0.23}, "V2_3x_trail": {"n": 5, "exp_r": 0.78, "t": 0.78}, "V3_3x_trail": {"n": 7, "exp_r": 0.47, "t": 0.64}, "V5_3x_trail": {"n": 14, "exp_r": 0.51, "t": 1.0}}, "dev_rec20_index_etf_trail": {"V1_QQQ": 0.04, "V2_SPY": 0.76, "V3_SPY": 0.44, "V5_SPY": 0.48}, "pick_share_dev": {"SPXL": "85%", "UPRO": "15%"}, "holdout_once": {"V1_trail": {"n": 1, "r": 0.06}, "V1_hold": {"n": 1, "r": 0.76}, "V2": {"n": 0}, "V3": {"n": 2, "r": 0.2}, "V5": {"n": 3, "r": 0.18}}}, "approved_by": "owner request 2026-10-15 (Testing 1 forward test; 3x-only change same day)", "notes": "Forward paper test only; research bar not met (tiny n: 5-14 DEV dip days per variant). Signal on SPY/QQQ; S&P variants trade ONE of SPXL/UPRO per day (larger dollar volume 09:30..trigger bar; meta picked/dv_* in the journal), V1 trades TQQQ. R is the same as on the index ETF (stop scales with leverage); the slot notional cap (~$950) binds, so $ risk/P&L per trade are ~3x the index ETF's (still ~$12-17 risk vs the $250 risk budget). Nested variants: V2 days are also V3/V5 days (up to 3 lots on the picked ETF). heat_fade_short(-FD) loses same-poll ties on these ETFs (longs_first_on_ties). Code: mcf/strategies/index_dip.py (trade_candidates/pick), pinned_symbols adds trade_candidates. Educational only - not financial advice."}
```

## Summary of the choice
| setup | signal | instrument | exit | DEV n / mean R / t | index ETF (same exit) | holdout (once) |
|---|---|---|---|---|---|---|
| IDX1 TQQQ trail | QQQ >= 1.0% below open by 09:55 | TQQQ | TRAIL | 8 / +0.00 / 0.01 | QQQ +0.04 | 1: +0.06 |
| IDX1 TQQQ hold | same | TQQQ | HOLD | 8 / +0.15 / 0.23 | QQQ +0.17 | 1: +0.76 |
| IDX2 3x | SPY >= 0.75% by 09:45 | SPXL/UPRO pick | TRAIL | 5 / +0.78 / 0.78 | SPY +0.76 | no trade |
| IDX3 3x | SPY >= 0.75% by 09:55 | SPXL/UPRO pick | TRAIL | 7 / +0.47 / 0.64 | SPY +0.44 | 2: +0.20 |
| IDX5 3x | SPY >= 0.5% by 09:45 | SPXL/UPRO pick | TRAIL | 14 / +0.51 / 1.00 | SPY +0.48 | 3: +0.18 |
Trigger: 20% recovery off the running low, bar closing 09:50-10:05. TRAIL = stop at the traded ETF's morning low - 10%
of its drop; once +1R, trail 1R behind the best; no target; 15:55 flatten. HOLD = same stop, no trail, 15:55 flatten.
