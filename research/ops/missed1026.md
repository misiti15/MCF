# Missed window 2026-10-26 (Primary) - replay estimate

Educational only - not financial advice.

GitHub fired no scheduled trade.yml run on 2026-10-26; the session was started by hand at 10:30 ET and Primary's live
loop took its first signal at 10:40 ET. This replays Primary's setups for the window it missed (entries 09:50-10:39 ET;
nothing may enter before 09:50).

How: `python -m mcf.replay run --account primary --dates 2026-10-26 --universe live --fills costs|paper`, run from the
base branch at 86ef7c7c (the exact config Primary traded today; the day's frozen setups were not on mcf-data yet). Bars
fetched read-only from Alpaca SIP up to 11:47 ET; every replayed trade in the window had closed by 11:42 ET (none open).
Replay fidelity (research/replay/VALIDATION.md): 98% of live signals reproduced, 85% of live trades, matched trades
within ~0.01 R.

| fills | trades | wins | total R | avg R | P/L |
|---|---|---|---|---|---|
| research cost model (conservative) | 27 | 17 | -1.52 | -0.056 | -$26.44 |
| paper fills (what Alpaca paper does) | 27 | 17 | +0.24 | +0.009 | +$8.17 |

By setup (cost model): CWT14-failbrk-pdl-p10-lowvol-long 19 trades -4.08 R; MF4-h40-open-flowsell-FD 3, +1.59 R;
RW3-gapdn-rsi5pop-flowsell-short-FD 3, +1.00 R; RW5-heat30-flowsell-rsi5pop-gapdn-short-FD 2, -0.03 R.

Conservative figure used: **-$26 (-1.5 R)**; stress with a further -0.05 R/trade: about -2.9 R (~ -$50).

Caveats: synthetic quotes (the replay rarely skips on spread - after 10:40 it took DDS at -20.5 R, which live skipped
for a 104 bps spread; no such outlier is in the missed window, worst trade -1.32 R); the morning positions would have
used slots that live used later, so live's own 10:40+ trades would have differed somewhat. Not added to the live
record: the account history stays the real fills only.
