# Owner decisions log

Dated record of what the owner decided and how MCF implements it. Newest first.

## 2026-10-20 evening: MF3 watch + swarm

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| MF3-open-flowsell-rsi5hi-FD (Primary) | **Keep in Primary on watch** — make sure it needs demoting rather than a bad run. | The nightly loop reports its Primary-only record (trades, win vs break-even, avg R, t, last 4) every night; a demotion is suggested only if it stays below break-even. |
| MF3 family | BDI swarm for a more profitable tweak; new variants go to the testing account with the most room, without conflicts. | research/bdi/mf3swarm1020; candidates placed with mcf/research/allocate.py after the owner's yes. |

## 2026-10-20: promotion = move

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Promoted setups' Testing 1 copies | **A promotion is a move**: a promoted setup runs only in Primary. | RW5-FD, RW3-FD, MF2-FD, MF4-FD, NS3-FD and MF3-FD switched off in Testing 1 (no setup runs in two accounts; the leaderboard shows one row per setup with its full combined record) from 2026-10-21; their Testing 1 records stay on the leaderboard ("stats from Testing 1"). Future promotions switch the Testing copy off in the same change and regenerate docs/live/assignments.json. |

## 2026-10-19 evening: owner replies to the nightly brief

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| MF4-h40-open-flowsell (P1) | **Keep in Primary** after its 8 sessions. | No change; stays in Primary. |
| Promotion/demotion rule (R1) | **No firm rule.** Nightly *suggestions* for promotions and demotions, owner decides each. | The nightly loop adds promotion/demotion suggestions (with win rate, break-even win rate, avg R, t, last-4) as DECISION items; nothing moves without the owner's yes. |
| Live scale-out fix (SO1) | **Yes.** Fix the Testing 2 partial exit: cancel the lot's stop+target, sell half, place a new stop (breakeven) + target on the rest; test on paper first. | Built after hours; merged before 09:00 ET only with tests; first live day watched lot by lot. |
| Promotions (effective 2026-10-20) | **Promote** MF2-open-rsimidhi-flowsell-FD, MF4-h40-open-flowsell-FD, NS3-failed-vwap-reclaim-short-FD to Primary. | Enabled in `config/default.yaml` (setup_order "# promoted 2026-10-20"); they keep running in Testing 1; off in Testing 2; gen is exclusive (ledger 2026-10-20-promote-3fd). |
| Demotions (effective 2026-10-20) | **Demote** MF3-open-flowsell-rsi5hi (the windowed original; MF3-...-FD stays in Primary) and MF5-flowsell-vwapup-rsi5hi to Testing 1. | Disabled in Primary; enabled in Testing 1 with `former_primary` markers (rule 20); off in Testing 2 / gen (ledger 2026-10-20-demote-mf3-mf5). |
| Graveyard moves (effective 2026-10-20) | **Move** LIQ-orl-sweep-open15-s25-long, RW2-exhaustion-noon-adv150-short-FD and heat_fade_long (ex-primary) from Testing 1 to Testing 2 ("Graveyard"). | Disabled in Testing 1; full enabled blocks + setup_order entries in `config/account_testing2.yaml`, tagged "moved from Testing 1 2026-10-20 (owner)" (ledger 2026-10-20-graveyard-3). |
| Twin exposure | **Cap twin exposure on the same ticker.** | `RiskManager.check` refuses "twin held" when the symbol has an open/pending lot of the setup's twin (same name without a trailing "-FD"); `live.block_twin_same_symbol` (default true), all accounts; playing time bucket held_by_other (ledger 2026-10-20-twin-cap-setup-loss). |
| Per-setup daily loss | **A safe loss limit that allows the same setup twice a day, more if a trade wins.** | `account.max_setup_daily_loss_r: 2.0` in Testing 1, Testing 2 and gen: a setup stops new entries once its net realized R today <= -2 ("setup daily loss limit"); account-wide `max_daily_loss_r` raised 60 -> 120 there as a backstop. Primary unchanged (20R, no per-setup limit). |

## 2026-10-19: Setup Generator account; live funds on hold

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Setup Generator account | A 5th Alpaca **paper** account, "Setup Generator", fed by a BDI Setup Generator that produces **10 new setups per day**. It switches on automatically once the secrets exist; nothing changes for Primary, Testing 1, Testing 2 or the long-hold (S6) account. | `config/account_gen.yaml` (`MCF_ACCOUNT=gen`, orders `mcg-`, state branch `mcf-data-gen`, secrets `ALPACA_GEN_API_KEY` / `ALPACA_GEN_SECRET_KEY`; market data stays on the primary SIP keys). `strategies_exclusive: true`: only GEN-* setups run there. Generator: `python -m mcf.research.generator run --date YYYY-MM-DD --n 10 --apply` (docs/OPERATIONS.md). |
| Slots | **80 slots**, $100,000 paper. | `slots: 80`, capital per slot = equity × 3.8 ÷ 80 (same rule as every account, equal increments), max 16 positions per setup, `max_daily_loss_r: 60` (as Testing). |
| Leaderboard | Generated setups get their **own leaderboard**, visually distinct; never mixed with the main setup leaderboard. | Dashboard card "Generated setups leaderboard" (violet accent, GENERATED badge); the main leaderboard drops GEN-* rows. |
| Promotion | **No promotion rules** for GEN setups. The owner may promote one himself, e.g. after about 20 trades/day for 2 days. | The generator records each setup's screen stats honestly (negative ones too) in `gen.screen`; it never promotes anything. |
| Keep every generated setup (owner, restated 2026-10-19) | **Every setup generated each day goes into the Setup Generator account and trades live (paper).** **No generated setup is ever deleted, demoted, disabled or removed without the owner's consent.** | `--apply` adds all picks to `config/account_gen.yaml` enabled; no code path disables or removes GEN-* setups; `tests/test_gen_keep.py` fails if any generated setup in the registry is missing or disabled. Routines may only *propose* changes to GEN setups as DECISION items in research/owner_inbox/. |
| Emails | EOD emails only for Primary and S6. | The gen EOD report is built and saved (`--no-send`), no email. |
| Live funds | **On hold** until Primary has **3 positive days in a row**; then a serious conversation before any real money. | No live-funds work until then. |

## 2026-10-14: evening decisions (demotions, Testing philosophy)

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| NS3 | Demote to Testing 1. | Disabled in Primary; runs in Testing 1 in its primary form next to NS3-FD, `former_primary` marker (ledger 2026-10-14-demote-ns3). |
| MF4 | Keep in Primary for 8 sessions total, not more. | Re-evaluate after the 2026-10-19 session (keep or demote). |
| Testing 2 flagged setups and CWT14 | Run two more sessions before any deletion; more data first. | CWT14-pdl-p05-long, CWT13-z05-short, CWT12-coil-k6-long and the CWT14 family reviewed after the 2026-10-16 session; removal only on the owner's word. |
| Testing caps | A cap should not itself make or lose money; Testing exists to collect data from as many *efficient* executions as possible. | Testing caps stay high. Note: the daily loss limit (in R) fills faster with more trades, so caps and the limit interact. |
| Win rate | Treat win rate as success to build on, not a discredited metric. | Reports show win rate next to the break-even win rate; research looks for ways to turn high win rates into profit (smaller losses, earlier partial exits) alongside expectancy. |
| Top-5 tuning goal | Improve execution of the most-used setups for more quality executions and data, not to rank by profit (profit ranking is a real-funds topic). | Daily top-5 run aims at execution quality and win-rate-to-profit conversion. |
| Failure patterns | Treat recurring loser patterns (RW2 never-worked, ST2 already-down) as possible opportunities (continuation or rebound), not only filters. | Each such pattern is also tested as a setup in the opposite or follow-up direction (same day and next day). |

## 2026-10-14: real-funds planning (applies when real money goes in)

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| S6 crash protection | Insurance that costs 7-21 points a year is too much. | No stops, trend filter or wider book in S6 (study `research/longhold/protect1014/`: 121 configs, 0 pass). Protection is position size: plan for -45% (backtest) to about -60% (2008-type). The -25% halt on new orders stays. |
| Profit skim | Lock in some cash as profits grow, without draining trading capital. **30% of profits**, not 50%. Real-funded accounts only. | Proposed rule, to finalize before funding: per account, a starting capital and a high-water mark; each month, 30% of new profit above the prior high-water mark moves to cash or T-bills outside trading capital; no sweep in a down month. Where the cash sits (same account or a separate one) is still open. |
| Backup data feed (outage plan step 2, owner 2026-10-16) | Deferred until real funds. | **Before live:** add a second market-data source and fail over to it when SIP bars go stale (today a stale feed only pauses, protects and flattens; see `docs/OPERATIONS.md` "Outage plan"). |
| Watchdog mode (owner 2026-10-16) | The independent watchdog runs in dry mode on paper. | **Before live:** set the repository variable `MCF_WATCHDOG_MODE=act` (watchdog.yml), after reviewing its dry-run job summaries. |
| Partial-fill lot-cap rule (owner 2026-10-16, option B) | On paper, a lot left with < 25% of its original quantity after a partial target fill no longer counts toward `live.max_lots_per_symbol`. | **Must be reviewed before live funds** (`live.lot_cap_ignore_residual_frac`, ledger 2026-10-16-lot-cap-residual): with real money a residual lot is still real exposure on the symbol. |
| Taxes | Revisit tax implications before any real-funded account. | **Open item, must be resolved before funding.** Points to take to a CPA: nearly all MCF gains are short-term (held 1 year or less, taxed as ordinary income); wash-sale rule with constant re-trading; trader tax status and the 475(f) mark-to-market election; a reserve (about 30-35% of realized gains) set aside before the skim; whether part goes in an IRA (margin and shorting limits). |
| PTP withholding | (Found 2026-10-16) Selling a publicly traded partnership (ET, EPD, ...; shorts too) makes the broker withhold 10% of gross proceeds (IRS §1446(f)). | Cash leaves the account but is generally a tax credit recoverable at filing, not a trading loss: **CPA list**. MCF now excludes PTPs from the universe (`universe.exclude_ptp`). |

## 2026-10-06: fourth round (research swarm, heat score, daily improvement)

| Topic | Owner request | What was done |
|---|---|---|
| Heat score | Use a bot swarm to tune MarcoFlow's heat score into the best weighted version for viable longs and shorts. | Heat ported and recomputed on SIP data (1,000 names, 63 sessions). Five tuners tried ~19,200 configurations and an auditor checked them; the locked test was scored once. The original is negative everywhere. The surviving version is a *consistent* reversion score, gated by time of day: heat_fade_short (09:50–10:30) and heat_fade_long (11:05–13:30) are paper-only. See `research/heat/HEAT_STUDY.md`. |
| Setup research | Research as many sources as possible for the most common and best intraday setups, and build setups from them. | Four research families (~117 sources, via search summaries because page fetches were blocked), synthesised into 17 ranked specs. Eight setups were built and screened on 63 sessions of SIP 1-minute bars. Only orb20_a passed, and thinly. The previously enabled ORB-5 and noise-band setups lose after costs and are off. See `research/SETUP_SCREEN.md`. |
| Daily improvement | Every live day better than the last. | Not achievable for daily P/L: no documented setup does it, and chasing it overfits. Instead, each close produces a review (`reviews/` on the state branch) scoring execution, data, every rule's what-if cost or saving, and results against yesterday and the 5/20-day averages. Setups change only through the gates. |

## 2026-10-05: third round (go-live)

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Fill realism | Paper fills anything the price touches; results must be as close to real fills as possible. | Before every order: live SIP quote. Skip if the spread is > 30 bps or > 25% of the stop distance; cap size at 10% of the symbol's recent 1-minute volume. Every trade records entry slippage vs the signal price and an adjusted P/L that adds real-book stop slippage; target fills are flagged as touch fills. See `live:` in config. |
| Universe | More tickers only if they are good for the setups. | Two tiers, no fixed count (4,954 today). Extended-tier names ($1–5M ADV) trade only when in play (opening rvol ≥ 3×), at 3× the slippage assumption. |
| 9:30–9:50 | Soft rule: very volatile and hard to capture with any latency; there may be opportunities. | `live.no_entry_before: "09:50"`. Signals in the window are journaled as **shadow** and simulated after the close, so the window's real value is measured before the rule is revisited. Discovery also starts at 09:50. |
| New setups | A built-in way to add setups as they're noticed, e.g. layered rules (RSI14 > 65 + above the 20 SMA). | Weekly `discover` workflow mines 1–3-layer rules on ~1,500 liquid names, 60 sessions: found on the older 2/3, checked on the newest 1/3, first trigger per symbol-day, costs in R. Candidates appear in the dashboard's Setup lab. Promotion is a config entry (`type: rule`), never automatic. |
| Data | Subscribed to Alpaca Algo Trader Plus (SIP). | `data.feed: sip`; real-time SIP bars and quotes verified 2026-10-05. |
| Go-live | Trade and collect data automatically from the 2026-10-06 open; show it live on the dashboard as "MCF Update" against MarcoFlow. | GitHub Actions `trade` workflow (see `docs/OPERATIONS.md`); status every 2 minutes on the `mcf-data` branch; dashboard section "MCF Update" reads it. MCF closes only its own positions (`mcf-` order ids). |

## 2026-10-05: second round

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Success model | **Win % first, then tweak setups to hold winners longer.** | Two-stage scorecard. (1) **Success rate** = price reached +1R before −1R, measured to the end of the session whatever the exit did. It is symmetric, so a coin-flip setup scores 50% and target/stop geometry can't inflate it. Setups are selected on this first. (2) Exit tuning (scale-outs, trails, holding longer) then raises P/L on setups that already pass (1). |
| Threshold | **65%** | Gates: success rate ≥ 65% **and** realized win rate ≥ 65% **and** expectancy > 0, out of sample, after costs, ≥ 200 trades. |
| Universe | Scan about 3,500+ tickers often. A bigger pool means more chances; favour liquid names for easy entry and exit. | `mcf universe`: top 3,500 by **consolidated** 20-day $ volume (≥ $10M), price ≥ $5, shortable/ETB flags. `mcf.data.scanner`: snapshot scan of the whole universe every minute (35 requests per pass, within the free 200/min limit). |
| Shorting | Crucial. | Kept as a hard requirement for the execution venue (see `docs/DATA_AND_BROKER.md`). |

## 2026-10-05: first round of answers

| # | Topic | Owner decision | How MCF applies it |
|---|---|---|---|
| 1 | MarcoFlow rules | **No MarcoFlow hard rule carries over** unless it is tested and verified to add value for MCF. | Skipped entry hours, the knife guard, "never cap entries" and so on are all off. Each one can be added back as a toggle once a backtest shows it adds value. |
| 2 | Win rate | 90% isn't required, but **a win rate not well above 50% means the system is too close to failing.** | Every setup must clear **both** gates out of sample, after costs: win rate ≥ 55% **and** expectancy > 0. Scale-out exits (bank half at +1R, stop to breakeven) are on by default. The dashboard shows win % next to break-even win %. |
| 3 | Data / broker | Efficiency first. Use the Robinhood MCP if possible; otherwise pick the cheapest option with better data. Learn from MarcoFlow's data timing and execution. | See `docs/DATA_AND_BROKER.md`. Alpaca now (paper, free → $99 SIP). Robinhood Agentic is kept as a later long-only live option. |
| 4 | Sizing | **100 slots** to start; make full use of funds and don't miss opportunities. | `slots: 100`, capital per slot = equity × 2 ÷ 100. Risk-based cap of 0.25% equity per trade. Each setup can use up to 60 slots. |
| 5 | Shorting | Long **and** short, with as many trading options as possible. | `shorts.enabled: true`. Live shorts only on names the broker flags shortable and easy-to-borrow (no borrow fee intraday at Alpaca). |
| 6 | Automation | Fully automated paper trading from the start, then a move to live funds. | The paper runner places orders with no approval step. Live is the same code with `paper=False`, after the gates in #2 pass. |
| 7 | Reporting | A daily email to misiti15@gmail.com **and** a free hosted page. The owner values an overview of data and process. | `mcf brief --send` (Gmail SMTP app password). Hosted dashboard: https://claude.ai/artifact/LxSZBti7GjRxzKncf4Q1ow (private Claude artifact). |
| 8 | MarcoFlow | MCF runs **independently** of MarcoFlow. Use MarcoFlow's data to learn what to do right or differently, and explore anything worth building on. | MarcoFlow is read-only reference data (`docs/MARCOFLOW_ANALYSIS.md`, a reference source on the dashboard). There is no runtime dependency on it. |
