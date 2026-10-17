# Q8 follow-up: near-misses the new lab features make live-runnable (proposal for Testing 2)

*Educational only — not financial advice. Paper only. Nothing here is applied: config/account_testing2.yaml is not
touched. None of these is a candidate: every one fails its try-count bar (RESEARCH_RULES 3/4/14). This work did not
load the locked block.*

**Locked look (found, not made here):** a parallel session's uncommitted `research/swarm1017/followup/locked_look1.json`
scored look 1 on the locked block for RST1 (n 125, −0.170R, t −2.63), ETF-ADX (n 89, −0.285R, t −1.77) and AM-GAPDN
(n 88, −0.254R, t −1.74). All three failed. **RST1 and ETF-late-dip-adx are therefore left out of the YAML below**
(and AM-GAPDN, already in Testing 2 as NM-AR-AM-gapdown-capitulation-long, deserves a second look).

## 1. What was built (owner 2026-10-17, Q8 = A; ledger `2026-10-17-lab-features-q8`, housekeeping: features)

All opt-in per `type: lab` setup; existing setups are unchanged.

| feature | YAML | notes |
|---|---|---|
| index context | `context: [spy_fo]`, `[qqq_fo]` | SPY/QQQ % from today's first 5-min open to this 5-min bar's close (= the frames' SPY/QQQ `fromOpen` at the same date/tod). Live: SPY/QQQ are added to every poll (not traded unless in the universe). |
| breadth | `context: [breadth]` / `[breadth_open]` | share of the universe above its session VWAP / above its open at this bar (5-min bars, heat_frame definitions). Live: polled universe; backtest: session symbols; history: lab-frame universe. |
| allow-list | `symbols: [..]` or `symbols: module` | mask evaluated only on these names. Restricts only; `pin_symbols: true` (with a list) also pins them into the universe. |
| geometries | `geom:` (or module GEOM) `t05s05`, `hold`, `holdtr` | t05s05 = +0.5R / −0.5R; hold = 1R stop, no target, flat 15:55; holdtr = hold + 1R trail once +1R (setup `trail_r`/`trail_after_r`, re-armed after restarts). |

History: `python research/history2y/build_frames.py --context-only` (built for the 21 open months; the locked block was
not loaded) and `lib.load_month(m, context=True)`. With it the modules reproduce their documented history exactly:
RWR4 n 645 +0.1185R, RWR1 n 654 +0.1522R, RWN4 n 899 +0.1149R, RST1 n 1662 +0.1764R.

## 2. swarm1017 near-miss modules (`research/swarm1017/*/modules`, plus `arena-index-etf/near_miss`)

**Now live-runnable thanks to Q8 (8 modules + 1 ETF near-miss):**

| setup (proposed name) | module | needs | history (open 2y, after costs) | bar | flags |
|---|---|---|---|---|---|
| NM-RWN3-ns3-spyup-early-short | rework-ns/RWN3 | spy_fo | n 388, +0.167R, t 2.69 | 4.90 | filtered NS3 |
| NM-RWN4-ns2-spyup05-notfri-short | rework-ns/RWN4 | spy_fo | n 899, +0.115R, t 2.29; WF 1.0 | 4.90 | filtered NS2; **day-of-week cut (not Fri)** |
| NM-RWN5-ns3-mon-weakrs-short | rework-ns/RWN5 | spy_fo | n 295, +0.202R, t 2.17 | 4.90 | **Mondays only** (no known mechanism) |
| NM-RWR1-exh150-gapdn-spyup-pm-short | rework-rw/RWR1 | spy_fo | n 654, +0.152R, t 3.83 | 5.25 | 654 trades on 78 sessions (clustered) |
| NM-RWR3-ns3-qqqup-early-short | rework-rw/RWR3 | qqq_fo, refire | n 355, +0.206R, t 2.97; up/down both > 0 | 4.83 | filtered RW4 |
| NM-RWR4-ns2-up3-qqqup-slopedn-short | rework-rw/RWR4 | qqq_fo | n 645, +0.118R, t 3.15 | 4.83 | filtered RW6 |
| NM-RST1-l3fromopen-spyup-pm-short | rework-st/RST1 | spy_fo | n 1662, +0.176R, t 4.70 | 5.03 | top-3 days = 73% of R; **locked look 1 failed: not proposed** |
| NM-ETF-late-dip-adx-long | arena-index-etf/near_miss | symbols | train +0.139R n 362 t 2.41 / valid +0.126R n 248 t 2.97 | 5.00 | **locked look 1 failed: not proposed** |
| NM-ETF-late-dip-di-long | arena-index-etf/AR-ETF-late-dip-di | symbols | train +0.250R t 5.10 / valid +0.029R t 0.50 | 5.00 | best day 31%; valid down −0.11R |

**Runnable, not proposed:** CWT14x-pdl-p05-lowvol-brdlo-fo1-long reads `breadth` meaning *share above the open* over
the adv ≥ $95M universe. Live that is `breadth_open` over the polled universe (a wider universe), so the module would
need a copy that reads `breadth_open`, and its history is weak (t 1.24 vs bar 5.07, ex-top-5-days −0.003R).

**Already runnable before Q8, no new feature used** (not part of this proposal): RWN1, RWN2 (Wednesday cut), RWN6
(they define `_spy_fo` but do not use it), RWR2, RST2, RST3, MFR1, NM-HL-atrhi-fri, NM-HS-fo1-mon, NM2-cwt05,
CWT14x-orl-p10/-p20, and the 5 already in Testing 2. No module needs t05s05 / hold / holdtr: those geometries were in
the grids, but no near-miss used them. They are there for future forward tests.

Testing 2 runs only its own batch (Primary and Testing 1 setups are off there), so the "filtered copy of a live
setup" overlap does not stack positions within the account. Mutual overlap between the 7 proposed was **not** computed.

## 3. Proposed YAML (`config/account_testing2.yaml`) — only after the owner says yes; merge outside 09:30–16:00 ET

```yaml
live:
  setup_order:            # append (narrowest first, by open-history trades/day)
    - NM-RWN5-ns3-mon-weakrs-short            # 0.69/day
    - NM-RWR3-ns3-qqqup-early-short           # 0.83/day
    - NM-RWN3-ns3-spyup-early-short           # 0.91/day
    - NM-ETF-late-dip-di-long                 # ~1.1/day on 152 of 426 sessions
    - NM-RWR4-ns2-up3-qqqup-slopedn-short     # 1.5/day
    - NM-RWR1-exh150-gapdn-spyup-pm-short     # 1.5/day (clustered)
    - NM-RWN4-ns2-spyup05-notfri-short        # 2.11/day

strategies:
  # ---- swarm1017 near-misses runnable after Q8 (owner 2026-10-17): forward observation, NOT candidates;
  #      judge on >= 20 sessions / 60 trades
  NM-RWN3-ns3-spyup-early-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-ns/modules/RWN3-ns3-spyup-early-short.py
    context: [spy_fo]
    min_adv: 95000000
    window: [950, 1030]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8]
  NM-RWN4-ns2-spyup05-notfri-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-ns/modules/RWN4-ns2-spyup05-notfri-t05s1-short.py
    context: [spy_fo]
    min_adv: 95000000
    window: [950, 1130]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8, day-of-week]
  NM-RWN5-ns3-mon-weakrs-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-ns/modules/RWN5-ns3-mon-weakrs-short.py
    context: [spy_fo]
    min_adv: 95000000
    window: [950, 1130]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8, day-of-week]
  NM-RWR1-exh150-gapdn-spyup-pm-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-rw/modules/RWR1-exh150-gapdn-spyup-pm-short-t05s1.py
    context: [spy_fo]
    min_adv: 150000000
    window: [1300, 1500]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8]
  NM-RWR3-ns3-qqqup-early-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-rw/modules/RWR3-ns3-adv150-qqqup-early-short-refire.py
    context: [qqq_fo]
    min_adv: 150000000
    window: [950, 1030]
    refire: true
    refire_cooldown: 1
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8]
  NM-RWR4-ns2-up3-qqqup-slopedn-short:
    enabled: true
    type: lab
    module: research/swarm1017/rework-rw/modules/RWR4-ns2-up3-qqqup-slopedn-am-short-t05s1.py
    context: [qqq_fo]
    min_adv: 95000000
    window: [950, 1100]
    refire: false
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8]
  NM-ETF-late-dip-di-long:
    enabled: true
    type: lab
    module: research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py
    symbols: module
    min_adv: 95000000
    window: [1400, 1500]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation, q8, etf, fragile]
```

Notes:
- `refire` is explicit only where the module was scored that way (RWR3 refire, cooldown 1). Set `refire: false` on
  the others too if Testing 2 ever turns `live.lab_refire` on. Today it is off there; check before merging.
- The Testing 2 universe drops SPY, VOO, IVV, VTI, RSP, SPLG, SH and DOG (daily ATR < 1%). The ETF modules also need
  ATR ≥ 3.6% (di) or are late-day 3x-fund trades in practice, so nothing is lost. Do not use `pin_symbols`.
- `setup_names.yaml` display names and the `test_testing2` setup_order check must be updated with the config.
- Draft ledger line (append on approval, merged after the close):
  `{"id": "2026-10-19-t2-q8-near-misses", "title": "Testing 2: 7 swarm1017 near-misses made runnable by Q8 features (forward observation)", "patch": {"testing2.strategies": [null, ["NM-RWN3-ns3-spyup-early-short", "NM-RWN4-ns2-spyup05-notfri-short", "NM-RWN5-ns3-mon-weakrs-short", "NM-RWR1-exh150-gapdn-spyup-pm-short", "NM-RWR3-ns3-qqqup-early-short", "NM-RWR4-ns2-up3-qqqup-slopedn-short", "NM-ETF-late-dip-di-long"]]}, "approved_by": "owner (pending)"}`
