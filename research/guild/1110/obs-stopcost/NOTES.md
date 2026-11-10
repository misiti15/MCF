Educational only — not financial advice.

# obs-stopcost — where would a minimum stop width bite, and is it cost that loses? (Observer, 2026-11-09 ~19:50 ET)

Lead's request lead-20261109-1910-4. Descriptive, **0 configs**. `stopcost.py <journal_dir>` -> `stopcost_out.txt`.
16,615 live paper trades joined to their signals (all 7 accounts, run_id 1, 10-06..11-06; same join and lab cost model as
Skeptic's research/skeptic-20261109/costgap.py). 91 setups with >= 30 trades.
- gross = net + the paper cost already inside net (entry slip vs signal + stop-exit slip + realism haircut)
- net_lab = gross - lab cost model (what the same trades would net under our heavier research costs)

**Rule changes inside the window** (research/ledger.jsonl, 141 entries effective 10-06..11-06). The ones touching cost, stops
or sizing: 10-12 tod-costs (research scoring only); 10-20 twin cap; 10-23 per-setup stop latch, then OFF in Testing/GEN (ST-A);
10-26 GEN caps 80->200; 10-28 Primary size ~$5k then ~$4k; 10-29 Primary per-setup -2R stop; **10-30 Owner CF: Testing 1/2 skip
entries whose stop-exit round-trip cost > 0.15R** (a live cost filter already exists — STOPW is its "widen instead of skip"
alternative).

## Failures / corrections first
- **Live, it is mostly not cost.** 71 of 91 setups (13,568 of 15,665 trades) lose BEFORE costs (gross <= 0). A wider stop cannot
  rescue them on cost grounds. It may still change gross by stopping out less, which STOPW measures and this table cannot.
- **Tight stops get FAVOURABLE paper entries.** Stop quartile Q1 (median 44bp) has paper cost **-0.125R** (fills better than the
  signal price; 48% of entries have negative slip), lab charge +0.421R, gross -0.297R, net -0.172R. Q4 (222bp): paper +0.058,
  lab +0.092, gross -0.042, net -0.100. Likely the ~1.2-min signal-to-fill delay on reversion setups (price comes back in favour).
  Whether a real book gets that is open. So the lab's 0.42R charge on tight stops is not what paper shows.
- My first draft added the lab charge to net (double counting paper cost). It was caught and fixed before posting.
- (touch_fill in trades.meta = target exits, reconcile.py: winners by construction, not a fill-quality tag.)

## Where STOPW bites (share of trades with stop < 100bp), by trades affected
The CWT14 failed-break family dominates: orl-p05 908 trades (66% < 100bp), orl-p05-lowvol 810 (71%), pdl-p05 832 (65%),
orl-p10-lowvol 540, pdl-p05-lowvol 593, orl-p10 526, pdl-p10 530, pdh-p10-short 454, pdh-p05-lowvol-short 438. Then CWT12-coil-k4 673,
heat_fade_short-FD 651, RW7 436, RW2 408. **All CWT14 variants are gross-negative** (-0.09..-0.19R before costs).

## Cost-killed (gross > 0, net under lab costs < 0): 14 setups — where a cost/stop remedy could matter
MF3-open-flowsell-rsi5hi (58bp, 91% < 100bp), MF5-flowsell-vwapup-rsi5hi (55bp), MF2-open-rsimidhi-flowsell-FD (70bp; live net +0.121),
NS4-pm-vwap-reclaim-oversold-short (67bp), GEN-261021-02 (95bp), RW7-gapdn-bounce-early-short-FD (95bp, 436 trades, live net +0.061),
RW1-gapdn-bounce-flowsell-short-FD, L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD, NS5, ST4, CWT09-lowerhalf, 2 GEN. Mostly Primary /
Testing core names, so the MF flow-sell family is the natural first STOPW target, not CWT14.
