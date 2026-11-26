# Crypto intraday research plan

*Educational only — not financial advice.*

**Status:** research only (owner 2026-11-25: "start building the foundation for crypto trading including massive
research and random setup generation"). No live or paper trading. No account or config changes. No Alpaca trading
or account endpoints.

## Purpose
The equity north star is finding big intraday moves beforehand and turning them into setups (docs/BDI_CHARTER.md).
Crypto adds about 30 more names that trade 24/7 with large intraday ranges. This plan builds a foundation (data,
costs, a 24/7 engine and a random setup generator) to test whether any of those moves pays **after Alpaca's costs**.

## Data
- **Source:** Alpaca's public crypto market data, `https://data.alpaca.markets/v1beta3/crypto/us/{bars,quotes,latest/*}`.
  We use GET only, send no keys, and code only allow-listed paths (`mcf/crypto/data.py`).
- **Bars:** 1-minute bars for the USD pairs listed with a live print on 2026-11-26 (stablecoins excluded), from
  2021-01-01 or each pair's first bar, up to 2026-11-25.
- **Cache:** `data/crypto/1Min/<PAIR>/<year>.parquet`. The folder is gitignored and capped at 1.5 GB.
  - Rebuild it with `python -m mcf.crypto.data`.
  - See what is cached with `python -m mcf.crypto.data --coverage`.
- **Thin minutes:** Alpaca's venue is thin, so a minute with no trade has no bar.
  - The loader resamples only real prints.
  - Empty buckets carry the last close and are flagged `filled`.
  - Signals require a real print on the decision bar.
  - An entry on an empty bar pays 3× slippage.
- **Survivorship:** pairs delisted before 2026-11 (MATIC, NEAR, ALGO, TRX, MKR) are left out.
- **Late listings:** several pairs (ADA, ARB, HYPE, TRUMP, PEPE, ...) list late, so they appear only in CHECK and LOCKED.

## Costs (`mcf/crypto/costs.py`)
Costs are charged per side in every result, in R, using each trade's own stop distance.

| Item | Taker (default) | Maker-entry variant |
|---|---|---|
| Fee | 0.25% per side | 0.15% entry, 0.25% exit |
| Half-spread | from sampled Alpaca historical quotes (median per pair and year) | none on the entry |
| Slippage | 2 bps per side, +5 bps on stop exits, ×3 on an entry bar with no print | 2 bps per side on the exit only |

- **Fees:** Alpaca tier 1 (0–100k USD 30-day volume). Source: docs.alpaca.markets/docs/crypto-fees, via WebSearch on 2026-11-26.
- **Spread table:** `research/crypto_r1/spreads.json`.
  - Sampled on FIT and CHECK windows only, with seed 20261126.
  - Years before quote history (pre-2023) use the pair's earliest sampled year.
  - Pairs with no sample use a 30 bps spread.
- **Maker variant:** it assumes the limit order fills. No adverse-selection penalty is modelled, so it is an upper bound.
- **Order types:** Alpaca crypto takes market, limit and stop_limit orders only. A live stop would be a stop_limit, which can fail to fill in a fast drop. The backtest fills stops at the stop level, or at the bar's open on a gap, plus extra slippage.

## Engine (`mcf/crypto/backtest.py`, engine label "E5 crypto")
- **Fills:**
  - Entry at the next bar's open.
  - Stop and target in ATR(14) units of the bar timeframe.
  - Stop checked first when both are inside one bar.
  - A gap through the stop fills at the bar's open.
  - Time stop.
  - One open trade per pair.
- **Results:** R-based like the equity engine. Day clustering uses the UTC day.
- **Sessions:** UTC days, plus configurable windows: Asia 00:00–08:00, EU 07:00–15:30, US 13:30–20:00, US open 13:30–15:00 UTC, weekday or weekend.
- **Long only:** Alpaca crypto has no shorting and no margin. Short results are research only, for a venue that allows them, and are flagged `S*`. Only long setups can become finalists.

## Splits (fixed 2026-11-26, before any setup was scored; `mcf/crypto/splits.py`)

| Split | Dates (UTC, inclusive) | Use |
|---|---|---|
| FIT | 2021-01-01 .. 2024-12-31 | generator search and ranking |
| CHECK | 2025-01-01 .. 2026-05-25 | frozen finalists, scored ONCE |
| **LOCKED** | **2026-05-26 .. 2026-11-25** | most recent 6 months; **never read in round 1** |

- Loaders clip at 2026-05-26 unless `MCF_CRYPTO_ALLOW_LOCKED=1`, which only the lead sets for a once-per-version holdout score.
- Each look at LOCKED follows the rule-18 rising bar: look 1 needs t ≥ 1.0, look 2 needs t ≥ 1.5, and so on.

## Rules (docs/RESEARCH_RULES.md applies in full)
- **Costs:** always in.
- **Counting:** every draw is counted and scored. Reports give N and the noise bar `sqrt(2 ln N)` (≈ 3.5 for N = 400).
- **Finalist eligibility on FIT:**
  - long side;
  - at least 100 trades;
  - best-day share below 0.5;
  - avg R without the best day above 0;
  - ranked by min(avg R, avg R without the best day).
  - The top 10 are frozen before CHECK is read.
- **Reporting:** every finalist is reported with FIT, CHECK, avg R without the best day and its trade count, along with the random-entry baseline in the same windows.
- **Survivors:** a survivor goes to `research/backlog.jsonl` as an `idea` tagged `crypto`. It never goes straight to trading.

## Path to live (not started)
1. A candidate passes CHECK and then LOCKED, scored once, with the rising bar.
2. It is re-tested with the maker-entry and stop_limit fill realism.
3. **The owner says yes.**
4. It runs in a **separate paper account** dedicated to crypto. Paper does not charge crypto fees, so fees are charged in our own P/L.
5. A forward record is collected under the same rules as the equity testing accounts.

**Open question for the owner:** crypto trades 24/7, so the equity setup-freeze window (09:30–16:00 ET, no setup
or exit changes) has no natural "after the close". Proposal to decide: change crypto setups only in a fixed weekly
window, for example Saturday 00:00–04:00 UTC, the thinnest hours. The `setup-freeze` check would need a crypto variant.

*Educational only — not financial advice.*
