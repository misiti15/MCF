Educational only — not financial advice.

# TSZ1 — testing-account sizing change (owner 2026-11-16, effective session 2026-11-17)

Owner: "Implement this immediately across all testing accounts. So long as R stays the same and we can compare R with
any other account as we scale, promote and demote — reorganize the caps and sizing to allow for more trades per account.
Only Testing accounts. NOT On Deck, NOT Primary, NOT Graveyard."

Scope: Testing A-F = `testing2`, `explore1`, `livelab`, `testingd`, `testinge`, `testingf`. On Deck (`testing`), Primary
(`default.yaml`), Graveyard, Gen untouched (`tests/test_testing_sizing_1116.py` pins them).

## Evidence (live journals, run_id = 1, sessions 2026-11-09..11-16; `signals.py`, `costs.py` here, run beside the
journal copies `<account>.db` of each mcf-data-* branch)
| account | submitted/day | skipped: per-setup cap /day | skipped: size < 1 share /day | slots / max positions skips | peak open lots (of slots) | peak open notional |
|---|---|---|---|---|---|---|
| Testing A (testing2) | 125 | 4.3 (one GEN setup) | 3.2 | 0 | 136 / 400 | $109k of ~$380k BP |
| Testing B (explore1) | 22 | 9.2 (one GEN setup) | 0.3 | 0 | 71 / 200 | $67k of ~$200k |
| Live Lab (livelab) | 16 | 0 | 0 | 0 | 56 / 200 | $53k |
| Testing D (testingd, 3 sessions) | 63 | 33.3 (one GEN setup) | 0.7 | 0 | 69 / 200 | $65k |
| Testing E (testinge, 3 sessions) | 47 | 0 | 0.3 | 0 | 42 / 200 | $38k |
| Testing F (testingf, 3 sessions) | 66 | 47.7 (RW7 19.7, NM-RWN4 18.0, GEN-261020-05 10.0) | 1.3 | 0 | 54 / 200 | $50k |

Reading: in the testing accounts the slot ($) is ~$950-1,000 (not Primary's ~$3.5k) and **slots / buying power never
bound**; the losses come from the **per-setup cap** (and a few pricey names that round to 0 shares). Other skips
(not shortable/ETB, opposite side held, spread, cost filter) are unrelated to sizing and unchanged.

## Change (per account, before -> after)
- risk_per_trade_pct 0.25 -> 0.125 (inherited default before; the slot cap binds on ~every lot either way).
- slots = max_concurrent_positions: A 400 -> 800 (slot ~$950 -> ~$475); B / Live Lab / D / E / F 200 -> 400 (~$1,000 -> ~$500).
  Buying power multiple unchanged, so the book's $ capacity is unchanged; twice the lots fit.
- max_positions_per_strategy -> 100 in all six (A 50, B 30, Live Lab 30, D 50, E 50, F 30). Same share of slots as
  A's old 50/400 x 2; covers every per-setup-cap skip seen (largest: ~48/day in F over three setups, ~33/day one setup in D).
- New opt-in floor `min_shares: 3` + `min_shares_notional_pct` = the old slot (% of equity): a lot under 3 shares is
  raised to 3 if that fits the old slot $ and the risk budget, so the smaller slot does not drop pricey names (a plain
  halving would have dropped 6.1% of the lots, the ones priced over ~$475-500) or cut lots to 1-2 shares.
- Unchanged: -300R account halt, cost filter (max_stop_cost_r 0.15), per-setup max_lots logic, max_trades_per_day, setups.

## R and costs (2,395 closed testing-account lots, 11-02..11-16)
- R is identical by construction: each trade's R = P/L / its own risk (shares x stop distance); share count cancels.
- Live cost model is per share / per notional (entry bps, stop max($0.02, 4 bp), market exits max($0.01, 1 bp), SEC per $,
  TAF / CAT per share): **cost per R unchanged at 0.0170R mean** (0.0097 median) at the new size.
- Broker cent rounding of SEC + TAF (<= $0.02 / lot) is the only size-dependent cost: 0.0020R -> 0.0033R per lot
  (+0.0013R), immaterial. Whole-share rounding changes a lot's $ risk (avg lot $849 -> ~$530, median $ risk $12.4 ->
  $7.5) but not its R, so no trade is skipped for rounding; the 3-share floor keeps the rounding coarse-ness bounded
  (25% of lots stay at their old size: names over ~$160).
- $ P/L in testing accounts is NOT comparable before / after 11-17 (about 0.6x per lot); R is.

## Expected extra trades / session (per-setup-cap skips recovered; upper bound, signals still face every other check)
A +4, B +9, Live Lab 0, D +33, E 0, F +48 (and up to +0.3-3 pricey names per account from the share floor).
Configurations tried: 3 floors (1-share drop vs 3 / 5 / 8 shares) at one size (half); 3 chosen (closest to half the $).
