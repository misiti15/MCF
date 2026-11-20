Educational only — not financial advice

# Inverse-direction shadow: frozen rule (2026-11-20, journal-only)

Frozen file: research/owner1120/inverse/shadow.py (classes, underlying map, SHORT_KEEP, LONG_BLOCK, verdict()). Do not
edit after 2026-11-20. A change means a new shadow with a new frozen date. **Nothing here changes trading.** It reads
the journals after the close and writes forward.csv.

## 1. Classes
inv_broad, inv_sector, inv_single, inv_crypto, long_vol (together = INVERSE ∪ LONG_VOL, beta sign -1), lev_long
(information only), neutral. Every inverse fund carries an underlying and its leverage (UNDERLYING).

## 2. Per-trade verdict (every account, every setup)
- SHORT on an inverse/long-vol symbol -> **block**. The trade is long the market, so a short thesis cannot be expressed.
  Exception: setups in SHORT_KEEP (7) -> keep.
- LONG on an inverse/long-vol symbol -> **keep**. The signal is computed on the fund's own bars, which are the inverted,
  levered underlying. Exception: setups in LONG_BLOCK (10, mostly CWT14) -> block. This exception is a separate column
  and is not part of any live proposal without the owner's nod.
- A short signal on an underlying that has an inverse fund, skipped for borrow, spread, cost or size -> logged as an
  `inverse_buy_opportunity` with no R. Information only: the backtest showed -20.6R, so it is not adopted.
- Leveraged long funds: verdict `none`. They are listed only to watch them.

## 3. Pass bar (fixed now; counted from 2026-11-20)
- At least 10 sessions.
- Blocked inverse shorts: net R < 0 (the guard helps).
- At least 60% of affected setup x accounts not worse (not worse = their blocked trades net <= 0).
- No setup x account worse by more than 3R.
- Kept inverse longs: net R >= 0 over the same sessions. If they fail, review the long side.
- The LONG_BLOCK column is read separately: its blocked longs net R < 0.

## 4. Route if it passes
Backlog entry -> owner decision -> live only outside 09:30-16:00 ET; Primary only in the Friday epoch window. Exposure
checks count an inverse short as long-market. Then a ledger entry and `python -m mcf.research.ledger check`. The locked
holdout is scored once, at that decision.

Run: `python research/owner1120/inverse/shadow.py --since 2026-11-20` after each close, then `--score`.

## 5. Amendment before the first forward session (2026-11-19 ~22:30 ET, Skeptic F3/F5)
- 19 inverse funds missing from the lists were added with their underlyings (METD METQ IONZ RKLZ RGTZ QBTZ GGLS ORCZ ORCS
  RAMZ APLZ SMZ PALD ASTN WNTR FIAT DRV OILD HDGE). TTT moved to neutral. None had a trade, so no result changes.
- Name rule: a data/universe.csv fund whose name reads Bear / Inverse / Short / -Nx (treasury, bond, duration and VIX
  names excluded) is classed `inv_name` (beta -1), so new launches are caught when the universe is rebuilt.
- `--score` counts the pass bar on the default columns only (blocked shorts, kept longs). SHORT_KEEP and LONG_BLOCK are
  printed as separate exception columns: both were picked partly on check data, so only this forward record tests them.
No forward session had been recorded when this was made. The frozen date stays 2026-11-20.

Educational only — not financial advice.
