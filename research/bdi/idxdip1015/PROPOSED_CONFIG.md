# Proposed Testing-1 config — index open-dip bounce (NOT applied)

*Educational only — not financial advice.* Prepared 2026-10-15 during market hours; **apply after 16:00 ET** (rule 9,
`setup-freeze`). Evidence: `NOTES.md`. The research bar (t >= 3.64 for N = 756) is **not met**; this is the owner's
forward paper test in Testing 1.

## What to apply
1. `config/account_testing.yaml`, under `strategies:` — 21 setups (one per instrument so each has its own scorecard
   row; V1 has two exit variants). `scale_out_r: null` is required: the global `exits.scale_out_r: 1.0` would otherwise
   bank half at +1R and move the stop to breakeven, which is not what was tested. Clock times must stay quoted
   (the code also accepts YAML's base-60 reading of an unquoted `10:05`).
2. `config/account_testing.yaml`, `live.setup_order` — prepend the 21 names (they then win same-poll ties on these ETFs
   together with `longs_first_on_ties: true`, already on).
3. `config/setup_names.yaml` — the 21 display names below; then regenerate/sync `docs/live/setup_names.json`
   (`tests/test_setup_names.py::test_dashboard_copy_in_sync`).
4. `research/ledger.jsonl` — the entry below; then `python -m mcf.research.ledger check`.
5. Code is already in place (this change): `mcf/strategies/index_dip.py` (`class: index_dip_bounce`),
   `DayContext.peers`, `pinned_symbols` adds `signal_symbol`, pinned symbols skip the extended-tier in-play filter.
   Tests: `tests/test_index_dip.py`; full suite 204 passed.

Checks before the first session: tomorrow's universe/priors must contain SPUU (it is pinned by these setups, so
`build_universe` keeps it); SPUU will often be skipped live by the participation cap (ADV ~$2.8M, ~21 bars/day).

## 1. strategies (append under `strategies:`)
```yaml
  # ---- Index open-dip bounce V1: QQQ down >= 1.0% from the open by 09:55 (owner 2026-10-15, research/bdi/idxdip1015). Long only.
  IDX1-qqq100-0955-QQQ-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [QQQ]
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
  IDX1-qqq100-0955-QLD-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [QLD]
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
  IDX1-qqq100-0955-QQQ-hold:
    enabled: true
    class: index_dip_bounce
    symbols: [QQQ]
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
  IDX1-qqq100-0955-QLD-hold:
    enabled: true
    class: index_dip_bounce
    symbols: [QLD]
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
  IDX2-spy075-0945-SPY-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPY]
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
  IDX2-spy075-0945-SSO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SSO]
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
  IDX2-spy075-0945-SPUU-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPUU]
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
  IDX2-spy075-0945-SPXL-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPXL]
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
  IDX2-spy075-0945-UPRO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [UPRO]
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
  IDX3-spy075-0955-SPY-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPY]
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
  IDX3-spy075-0955-SSO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SSO]
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
  IDX3-spy075-0955-SPUU-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPUU]
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
  IDX3-spy075-0955-SPXL-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPXL]
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
  IDX3-spy075-0955-UPRO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [UPRO]
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
  IDX5-spy050-0945-SPY-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPY]
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
  IDX5-spy050-0945-SSO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SSO]
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
  IDX5-spy050-0945-SPUU-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPUU]
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
  IDX5-spy050-0945-SPXL-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [SPXL]
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
  IDX5-spy050-0945-UPRO-trail:
    enabled: true
    class: index_dip_bounce
    symbols: [UPRO]
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
    - IDX1-qqq100-0955-QQQ-trail
    - IDX1-qqq100-0955-QLD-trail
    - IDX1-qqq100-0955-TQQQ-trail
    - IDX1-qqq100-0955-QQQ-hold
    - IDX1-qqq100-0955-QLD-hold
    - IDX1-qqq100-0955-TQQQ-hold
    - IDX2-spy075-0945-SPY-trail
    - IDX2-spy075-0945-SSO-trail
    - IDX2-spy075-0945-SPUU-trail
    - IDX2-spy075-0945-SPXL-trail
    - IDX2-spy075-0945-UPRO-trail
    - IDX3-spy075-0955-SPY-trail
    - IDX3-spy075-0955-SSO-trail
    - IDX3-spy075-0955-SPUU-trail
    - IDX3-spy075-0955-SPXL-trail
    - IDX3-spy075-0955-UPRO-trail
    - IDX5-spy050-0945-SPY-trail
    - IDX5-spy050-0945-SSO-trail
    - IDX5-spy050-0945-SPUU-trail
    - IDX5-spy050-0945-SPXL-trail
    - IDX5-spy050-0945-UPRO-trail
    # ... existing entries unchanged ...
```

## 3. config/setup_names.yaml
```yaml
IDX1-qqq100-0955-QQQ-trail:
  name: Index Dip Bounce 1 QQQ
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy QQQ (1x) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under QQQ's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX1-qqq100-0955-QLD-trail:
  name: Index Dip Bounce 1 QLD
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy QLD (2x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under QLD's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX1-qqq100-0955-TQQQ-trail:
  name: Index Dip Bounce 1 TQQQ
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy TQQQ (3x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under TQQQ's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX1-qqq100-0955-QQQ-hold:
  name: Index Dip Bounce 1 QQQ (hold)
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy QQQ (1x) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under QQQ's morning low; no target, no trail; out by 15:55."
IDX1-qqq100-0955-QLD-hold:
  name: Index Dip Bounce 1 QLD (hold)
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy QLD (2x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under QLD's morning low; no target, no trail; out by 15:55."
IDX1-qqq100-0955-TQQQ-hold:
  name: Index Dip Bounce 1 TQQQ (hold)
  side: long
  what: "QQQ down >= 1.0% from the open by 09:55; buy TQQQ (3x Nasdaq-100) at 09:50-10:05 once the QQQ has regained 20% of the drop off its low. Stop just under TQQQ's morning low; no target, no trail; out by 15:55."
IDX2-spy075-0945-SPY-trail:
  name: Index Dip Bounce 2 SPY
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy SPY (1x) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPY's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX2-spy075-0945-SSO-trail:
  name: Index Dip Bounce 2 SSO
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy SSO (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SSO's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX2-spy075-0945-SPUU-trail:
  name: Index Dip Bounce 2 SPUU
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy SPUU (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPUU's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX2-spy075-0945-SPXL-trail:
  name: Index Dip Bounce 2 SPXL
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy SPXL (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPXL's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX2-spy075-0945-UPRO-trail:
  name: Index Dip Bounce 2 UPRO
  side: long
  what: "SPY down >= 0.75% from the open by 09:45; buy UPRO (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under UPRO's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-SPY-trail:
  name: Index Dip Bounce 3 SPY
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy SPY (1x) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPY's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-SSO-trail:
  name: Index Dip Bounce 3 SSO
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy SSO (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SSO's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-SPUU-trail:
  name: Index Dip Bounce 3 SPUU
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy SPUU (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPUU's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-SPXL-trail:
  name: Index Dip Bounce 3 SPXL
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy SPXL (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPXL's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX3-spy075-0955-UPRO-trail:
  name: Index Dip Bounce 3 UPRO
  side: long
  what: "SPY down >= 0.75% from the open by 09:55; buy UPRO (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under UPRO's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-SPY-trail:
  name: Index Dip Bounce 5 SPY
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy SPY (1x) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPY's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-SSO-trail:
  name: Index Dip Bounce 5 SSO
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy SSO (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SSO's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-SPUU-trail:
  name: Index Dip Bounce 5 SPUU
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy SPUU (2x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPUU's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-SPXL-trail:
  name: Index Dip Bounce 5 SPXL
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy SPXL (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under SPXL's morning low; trail 1R behind the best once +1R; out by 15:55."
IDX5-spy050-0945-UPRO-trail:
  name: Index Dip Bounce 5 UPRO
  side: long
  what: "SPY down >= 0.5% from the open by 09:45; buy UPRO (3x S&P) at 09:50-10:05 once the SPY has regained 20% of the drop off its low. Stop just under UPRO's morning low; trail 1R behind the best once +1R; out by 15:55."
```

## 4. research/ledger.jsonl (one line)
```json
{"id": "2026-10-16-testing-idxdip", "date": "2026-10-16", "title": "Testing 1: add 21 index open-dip bounce setups (owner variants 1,2,3,5; index ETF + leveraged trackers)", "patch": {"testing.strategies.IDX*": [null, "added (21 setups, class index_dip_bounce)"], "testing.live.setup_order": ["...", "IDX setups prepended"]}, "evidence": ["research/bdi/idxdip1015/PLAN.md", "research/bdi/idxdip1015/NOTES.md", "research/bdi/idxdip1015/results.csv", "research/bdi/idxdip1015/dipstats.json", "research/bdi/idxdip1015/conflicts.csv", "tests/test_index_dip.py"], "metrics_at_approval": {"configs_tried": 756, "lineage_configs": 882, "bar_t": 3.64, "bar_met": false, "dev_trail_rec20_index": {"V1_QQQ": {"n": 8, "exp_r": 0.04, "t": 0.06, "hold_exp_r": 0.17}, "V2_SPY": {"n": 5, "exp_r": 0.76, "t": 0.78}, "V3_SPY": {"n": 7, "exp_r": 0.44, "t": 0.61}, "V5_SPY": {"n": 14, "exp_r": 0.48, "t": 0.94}}, "fixed_1030_baseline_exp_r": {"V1": -0.16, "V2": 0.3, "V3": 0.21, "V5": 0.02}, "random_entry_all_days_exp_r": -0.23, "holdout_once_index": {"V1_trail": {"n": 1, "r": 0.05}, "V1_hold": {"n": 1, "r": 0.76}, "V2": {"n": 0}, "V3": {"n": 2, "r": 0.14}, "V5": {"n": 3, "r": 0.11}}}, "approved_by": "owner request 2026-10-15 (Testing 1 forward test)", "notes": "Forward paper test only; research bar not met (tiny n: 5-14 DEV dip days per variant). Signal on SPY/QQQ, trade on the index ETF and SSO/SPUU/SPXL/UPRO (S&P) or QLD/TQQQ (Nasdaq). Read results in R (slot-notional cap binds, so $ risk scales with leverage). Nested variants: V2 days are also V3/V5 days. heat_fade_short(-FD) loses same-poll ties on these ETFs (longs_first_on_ties). Code: mcf/strategies/index_dip.py, DayContext.peers, pinned signal_symbol. Educational only - not financial advice."}
```

## Summary of the choice
| variant | signal | instruments | trigger | exit | DEV n / mean R / t (index ETF) | fixed 10:30 | holdout (once) |
|---|---|---|---|---|---|---|---|
| V1 | QQQ >= 1.0% below open by 09:55 | QQQ, QLD, TQQQ | 20% recovery, 09:50-10:05 | TRAIL and HOLD | 8 / +0.04 / 0.06 (HOLD +0.17 / 0.26) | -0.16 | 1 trade: +0.05 (HOLD +0.76) |
| V2 | SPY >= 0.75% by 09:45 | SPY, SSO, SPUU, SPXL, UPRO | same | TRAIL | 5 / +0.76 / 0.78 | +0.30 | no trade |
| V3 | SPY >= 0.75% by 09:55 | same | same | TRAIL | 7 / +0.44 / 0.61 | +0.21 | 2 trades: +0.14 |
| V5 | SPY >= 0.5% by 09:45 | same | same | TRAIL | 14 / +0.48 / 0.94 | +0.02 | 3 trades: +0.11 |
TRAIL = stop at the traded symbol's morning low - 10% of its drop; once +1R, trail 1R behind the best; no target; 15:55 flatten.
HOLD = same stop, no trail, 15:55 flatten.
