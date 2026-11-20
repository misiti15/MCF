Educational only — not financial advice

# Owner item 2 (2026-11-20): extensive breakeven (stop-to-entry) test — PLAN (pre-registered before any score)

Frozen 2026-11-20 before the engine was run. Research only; no live / config change. Locked block
2024-11-01..2025-02-28 is filtered at read and asserted absent in every file read.

## Priors (stated, not re-scored)
- swing1119-L16 NTBE (stop to entry at 80% of target): -0.007R/trade on 2 years, 1 of 35 family-sides better (research/bdi/1119).
- BEREPLAY BE50 / BE75 (stop to entry after +0.5 / +0.75 stop units): -0.0128 / -0.0069R/trade, 0 / 2 of 27 families better.
- Giveback 11-19 stages (breakeven, trails, partials): 0 of 3,836 configs passed (research/giveback_1119/REPORT.md).
- Expectation: most of the grid loses. The test looks for any pocket where it helps, honestly scored.

## Data
- **Lab:** bt_lab1104 lists (95 setups, fixed geometries t1s1 / t05s1 / t1s05 / t05s05), every signal as in L16
  (uncapped chains, the same set the L16 test used), walked on cache_hist 1-minute bars with the BEREPLAY engine
  conventions: entry = signal-bar close, stop unit D = stop distance, stop-first inside a minute, a stop that the bar opens
  through fills at the open, flat at 15:54. GEN `hold` geometry is not in the lab lists (no target) and is out of scope here
  (GB-GENTRAIL is its own item).
- **Costs:** bt_all model (SL $0.01 + 1 bp each side, stop slippage $0.02, x3 tier for gap >= 20% or price < $5, time-of-day
  multiplier on entry). A breakeven exit is a stop exit and pays the stop slippage. Shorts: the lab cost model has no
  borrow; borrow is noted for shorts and for inverse / leveraged funds (decay is a hold-overnight effect, not intraday,
  but their wider spreads are inside the tier only when price < $5) — a breakeven rule does not change borrow days, so
  borrow is identical in BASE and variant and cancels in the paired delta.
- **Live:** run 1 of all 10 journals (origin/mcf-data* journal.db, read-only copies in scratch), 10-06..11-19, LR8 R; 1-minute
  SIP bars from Alpaca market data (read-only GET, keys from env, bars kept in scratch). The variant replays each live trade
  from the minute after entry to its actual exit; if the BE stop fires first, the exit is replaced by the BE fill
  (level, or the bar open if it opened through) less $0.01 + 1 bp stop slippage. Live hold trades are included for the
  MFE triggers (no target-% trigger).

## Grid (all paired on each parent's own signals, WB2)
| Dimension | Values | Count |
|---|---|---|
| Trigger | MFE +0.3 / +0.5 / +0.75 / +1.0 stop units; 50% / 80% of the distance to target | 6 |
| Stop level | entry (BE0); entry + round-trip costs (BEC); entry - 0.25 stop units ("soft BE", BES) | 3 |
| Activation | immediate (the minute after the trigger, D0); 10 min after the trigger (D10); not before 30 min in the trade (D30); after the first confirmed swing low (long) / high (short) after the trigger: a 2-bar-each-side pivot of the bar's adverse extreme, active the minute after confirmation (SW) | 4 |
| Condition | always (ALL); only from 13:00 ET (PM); only once SPY's move since the entry minute is >= 0.10% against the trade (SPY) | 3 |
| Size | whole position (F); half the position (H = 0.5 x the F delta, linear in costs) | 2 |
| **Rule configs** | | **432** |

A stop moved above the market (long) on activation fills at the activation bar's open (as a live stop would).

**Scopes** (each rule config applied to): the whole book (1); per side (2); per instrument type (3: stock / ETF incl.
leveraged long and neutral / inverse + long-vol, from research/forward/compass_gate/shadow.py frozen sets); per mechanism
family-side with n >= 300 (L16 had 36). **Configs counted N = 432 x (1 + 2 + 3 + #family-sides)** (about 18,000);
bar = max(1.5, sqrt(2 ln N)) (about 4.4). The live replay is descriptive and adds no configs.

## Split and scoring
- Fit = sessions <= 2025-09-30; check = after (scored once, only for fit candidates). LATE (>= 2026-10-06) descriptive.
- Delta = variant R - BASE R per trade (stop units, costs in). Day-clustered t (gates.summary method).
- Every scope cell reports: n, delta/trade, total, t (full / fit / check), avg delta w/o the best day and the best day's
  share, up / down / quiet SPY day-type totals, units better / worse (families, or setups inside a family) and their sizes.
- **Big winning days:** the delta on the book's top-decile BASE days (and on each family's own best 5 days), i.e. what the
  rule costs on the days that make the year.

## Pass bar (all must hold)
1. Fit: delta > 0 and fit t >= 2.0 (candidate). Only candidates are looked at on check.
2. Check: delta > 0 and check t >= 1.5.
3. Full-sample t >= max(1.5, sqrt(2 ln N)).
4. Avg delta w/o the best day > 0 and best-day share of the total delta < 50%.
5. Up-day and down-day totals both > 0.
6. Units better > units worse, worst unit >= -0.03R/trade (families for book / side / instrument scopes; setups with n >= 300 for a family scope).
7. Live: if the scope has >= 100 live trades, live delta >= 0 (else reported only).
8. Big winning days: reported; a rule that passes 1-7 but costs > 25% of its gain on top-decile days is flagged.

A pass is a research finding only. Any adoption would be a new tweaked copy (11-18), Primary only in the Friday epoch
window, a GB-NOEXIT conflict for the owner to decide, and a 15-session journal-only shadow first.

Educational only — not financial advice.
