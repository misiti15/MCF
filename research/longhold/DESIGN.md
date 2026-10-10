# Long-hold runner ("mcl"): design spec

*Educational only - not financial advice. This is a spec; nothing in `mcf/execution`, `mcf/strategies` or `config/`
was changed. The only code is the pure core `research/longhold/runner_core.py` (rebalance calendar, target diffing,
deterministic order ids, risk caps, kill switch) with `tests/test_longhold_core.py`.*

Goal (owner 2026-10-10): an efficient, autonomous system that holds positions for weeks to months and rebalances
weekly or monthly. Minimal moving parts: one job a day, one paper account, one state branch, orders only on
rebalance days.

## 1. What makes it different from the intraday runner
| | intraday runner (`mcf/execution/runner.py`) | long-hold runner (`mcf/longhold/`, to build) |
|---|---|---|
| holding | minutes, flat by 15:55 | weeks to months |
| data | SIP 1-minute bars | SIP daily bars (same endpoint as `research/swarm1010/w3_daily/download_daily.py`), ~400 sessions |
| orders | bracket market orders with resting stops | MOO (`time_in_force=OPG`) whole-share orders, no stops |
| job | 08:35..15:55 ET, polling every minute | once after the close + one morning check; seconds of work |
| order prefix / state | `mcf-` / `mcf-data`, `mct-` / `mcf-data-testing` | **`mcl-` / `mcf-data-longhold`** |
| account | primary / Testing paper | **its own (third) paper account** |

## 2. Account separation (required, not optional)
Alpaca nets positions **per symbol per account**. On a shared account the intraday code would break the long book:
- `flatten_mcf` collects every symbol MCF traded today and calls `AlpacaBroker.close_mcf_position`, which ends in
  `client.close_position(symbol)`: that closes the **whole** position, including mcl shares in the same symbol.
- An intraday short in a name the long book holds nets against it (the position shrinks; bracket legs then hold
  shares the long book thinks it owns).
- The intraday universe includes liquid ETFs and large caps, so overlap with a momentum / ETF book is certain.

So: **a third Alpaca paper account** (an Alpaca login can hold several paper accounts), secrets
`ALPACA_LONGHOLD_API_KEY` / `ALPACA_LONGHOLD_SECRET_KEY` used as `ALPACA_TRADE_*` (the existing broker adapter already
routes orders to `ALPACA_TRADE_*` and data to `ALPACA_API_KEY`). The intraday runner then needs **no change**.

Fallback only if a third account is impossible (needs an `mcf/execution` change, out of scope here, and its own PR
outside market hours): (a) the intraday runner skips any symbol in `state/longhold/positions.json`; (b) `flatten_mcf`
closes only the intraday quantity (a sized market order with an `mcf-flatten-` id) instead of `close_position`;
(c) `tests/test_flatten.py` gets a case with an mcl position in the same symbol that must survive the 15:55 flatten.

## 3. Daily job (GitHub Actions `longhold.yml`, own concurrency group `mcf-longhold`)
Schedule: 18:20 ET (after the consolidated daily bar is final) and a backstop at 08:50 ET; duplicate UTC lines cover
EDT/EST like `trade.yml`. Every run is idempotent, so a late, doubled or skipped trigger is harmless.

Evening run (`python -m mcf.longhold run`):
1. **Calendar.** `GET /v2/calendar` (next 10 sessions). `runner_core.rebalance_due(days, today, freq)` decides; not a
   rebalance day -> write the daily mark (equity, positions) and exit. Holidays and early closes come from the broker
   calendar, never from a hard-coded list.
2. **Data sanity (skip, do not guess).** Daily bars for the universe up to today. Skip the rebalance and alert if the
   last bar date is not today, SPY (or any ETF in the strategy) is missing, or more than 10 % of yesterday's eligible
   names have no bar.
3. **Signal.** The frozen strategy module computes target weights exactly as the backtest (`research/longhold/study.py`
   functions, moved into `mcf/longhold/signals.py` with a parity test, see 8).
4. **Risk check** (`runner_core.check_targets`, caps in 5). Any violation -> no orders, alert.
5. **Kill switch** (`runner_core.kill_switch`): manual halt file `state/longhold/HALT` on the state branch, or the book
   drawdown beyond the cap -> no new buys, alert; holdings are kept (a long-hold book is not dumped at a low by an
   automatic rule; the owner decides).
6. **Diff.** `runner_core.diff_orders(targets, holdings, equity, ...)`: only trade names that enter or leave, or drift
   beyond the band; sells first; skip orders under $25.
7. **Orders.** Whole shares `floor(notional / last close)` as **MOO (OPG)** - the backtest fills at the official open.
   Alpaca accepts OPG orders from 19:00 ET the evening before until 09:28; the evening run waits until 19:00 or the
   morning run submits. Fractional shares: Alpaca fractional orders are DAY-only, so the sub-share remainder is not
   traded (cash drag ~0.5 % at $25k / 20 names; negligible at $100k). Client order id
   `mcl-<strategy>-<signal day>-<symbol>-<b|s>` (deterministic; Alpaca rejects a duplicate id, so a rerun cannot
   double an order).
8. **Plan file.** `state/longhold/plans/<signal day>.json`: targets, diff, orders, data date, code version, config hash.
   Committed to `mcf-data-longhold` before submitting.

Morning backstop (08:50 ET): if today follows a rebalance signal, re-read the plan, list `mcl-` orders for that
signal day, submit only the missing ones (same ids). After 09:35: reconcile fills into the journal
(`fill vs official open` = slippage measure), and any OPG order that did not fill (halt, no auction) is retried once as
a DAY market order with id suffix `-r`, then reported.

## 4. Strategy and sizing
- One frozen strategy per account at first (see NOTES.md section 3 for the recommendation); weights from the backtest.
- **v1 = `S6_mom12_1rev_N20_W`** (pending the lead's locked-block score): on the last trading day of each week, after
  the close, rank eligible stocks ($5, 20-day median dollar volume >= $20M, >= 253 daily bars, not an ETF) by
  `C[t-21]/C[t-252]-1`, drop the top decile of `C[t]/C[t-21]-1`, hold the top 20 at 5 % each, MOO at the next open.
  ~16x one-way turnover a year, ~3 names replaced a week. Universe source: the live liquid list (or
  `research/lab_symbols.txt`), daily bars for ~1,200 symbols x 260 sessions (one batched SIP request set, ~1 minute).
- A survivorship-free ETF control (`E1_faber10_Erisk`, monthly, 9 ETFs + BIL) can run the same code with a different
  signal module if the lead wants one; it is a "near" result, labelled as such.
- Book capital = account equity (no margin). Long-only; no shorts in v1 (the long-short variants were tested and are
  not recommended).
- Rebalance band: 25 % of the target weight (relative). The backtest has **no band** (trades to exact weights); the
  band only skips small drift trades on names that stay. Before enabling it, re-run the study with the band as a
  diagnostic (backlog `lh-band-diag`); until then band = 0 for exact parity.

## 5. Risk caps (defaults in `runner_core.RiskCaps`)
max weight per name 12 % (equal-weight 20 names = 5 %; ETF strategies hold up to 3-9 names -> cap 40 % there);
gross <= 100 % (no margin, cash >= 0 after sells); <= 60 names; <= 150 orders per day; book drawdown 25 % from the
high-water mark -> halt new buys + alert; price >= $5 and 20-day median dollar volume >= $20M re-checked on the signal
day; a name with `tradable = false` or a pending corporate action is held, not bought, and flagged.

## 6. Reporting
- **Daily mark** (every run): equity, cash, positions, day P/L, vs SPY and vs the backtest's same-day return
  (tracking error). Labelled **paper**; backtest numbers are labelled backtest (rule 7).
- **Weekly report** (Saturday, in the EOD/discover workflow): equity curve vs SPY, the EW universe and the backtest
  replay of the same weeks; turnover; costs (commission-free paper, so the report charges the model cost 1c + 1 bps and
  shows measured open-auction slippage); holdings with weight, entry date, P/L; next rebalance date; any skipped
  rebalance or kill-switch event. "Educational only - not financial advice."
- **Dashboard panel** (`mcf/dashboard`): one card "Long-hold (paper)": equity vs SPY sparkline, return since start,
  max drawdown, holdings count, last run status / time, next rebalance date. Built from
  `state/longhold/marks.csv` on `mcf-data-longhold`.

## 7. Coexistence with the intraday system
- Separate account, prefix, state branch, workflow and concurrency group -> no shared state; the intraday flatten and
  risk caps never see mcl positions.
- The EOD report gets a separate long-hold section; long-hold P/L is never added to intraday setup statistics.
- The setup-freeze rule applies: the long-hold strategy file and its config are frozen per session, changes merged
  only outside 09:30-16:00 ET with a ledger entry (rules 9-11).

## 8. Tests to write (with the module)
1. Signal parity: on a frozen slice of `daily_2016.parquet`, `mcf.longhold.signals` reproduces the study's targets
   for 3 rebalance dates exactly.
2. Calendar (done in core): month/week ends, holidays (Good Friday, Thanksgiving week), early close, calendar shorter
   than today -> error.
3. Diff (done in core): band, sells before buys, enter/leave always trade, min notional, no shorts/leverage.
4. Idempotency (core id determinism done): rerunning evening + morning with a fake broker submits each order once;
   a rejected duplicate id is treated as "already placed".
5. Data sanity: stale last bar / missing SPY / too many missing names -> no orders.
6. Kill switch (done in core) and halt file -> no buys, holdings untouched.
7. Fake-broker end-to-end: three months of rebalances on synthetic bars; the book's equity matches the simulator's
   to < 1 bp/day without costs.
8. Separation: the long-hold runner refuses to start when `ALPACA_TRADE_API_KEY` equals the primary or Testing key, and
   never touches orders without the `mcl-` prefix.

## 9. Rollout
1. Lead scores the recommended configs once on the locked block 2024-11..2025-02 (look 1).
2. Two weeks dry-run (plans written, no orders), plan vs backtest targets compared.
3. Paper forward test on the third account. Review after 6 monthly rebalances (monthly strategies give few
   independent observations; judge on tracking vs backtest and drawdown, not on 6 months of return).
