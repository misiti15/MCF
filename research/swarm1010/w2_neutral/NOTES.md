# W2 market-neutral study (swarm 2026-10-10): hedged scoring of every setup + relative-value setups

*Educational only - not financial advice. Lab backtests on the open two-year history only; nothing here is a live or
paper result.*

Brief (lead, 2026-10-09): every setup tested so far is mostly market direction (longs win up sessions, shorts win down
sessions). Take the market out of the trade: (1) score every existing setup net of SPY / its sector ETF with a beta
from prior sessions only, costs on both legs; (2) basic pure relative-value intraday setups (stock vs SPY / sector,
pairs within a sector); (3) say what the live system needs for a hedged trade and a cheap first step.

**Section 1 (pre-declaration) was written before any hedged or relative-value trade was scored.** The only things seen
beforehand are earlier studies' published numbers (RESCORE.md, timeofday, regime1009, reddit NOTES). Section 1 may
change only by dated amendments.

## 1. Pre-declaration

### 1.1 Data (open history only)
- Lab frames and daily table via `research/history2y/lib.py`; `MCF_HIST_ALLOW_LOCKED` is never set (the rule-19 block
  2024-11-01..2025-02-28 is refused by the loader).
- 5-minute bars 09:35..15:55 (bar-close tod, as `mcf.research.heat`) rebuilt from `data/cache_hist/1Min` with
  `mcf.data.bars.resample` (the history2y pipeline). Locked-block rows are dropped right after each symbol's load,
  before any computation (as research/bdi/timeofday 0.6); only the 426 open sessions of `lib.daily()` are kept.
  Needed because the lab frames stop at 15:00 while the lab exits run to 15:55, and a hedge leg needs the ETF price at
  the stock's exit bar. Dense float32 arrays [symbol, session, bar] in `data/` (git-ignored).
- Integrity checks (declared): rebuilt close == frame close at the same (symbol, date, tod) for >= 99.9% of rows
  sampled; the re-simulated exit reproduces the frame's lab R (`r_{side}_{geom}`) for >= 99% of trades.
- Session regimes: `lib.regimes()` (universe median open-to-close terciles, open history).

### 1.2 Betas, sector map, pairs (prior sessions only)
- Returns: daily open-to-close (%) per symbol from `lib.daily()` (the intraday part of the day, which is what an
  intraday trade is exposed to).
- For session d, window = the previous 60 open sessions (min 30 with data); nothing from d or later. (The window can
  span the locked gap: 2025-03 sessions use 2024-10 sessions; no locked data is used.)
- **beta_SPY** = OLS slope of the stock's o2c on SPY's o2c in the window, clipped to [0, 3].
- **Sector ETF** = the candidate with the highest correlation of o2c in the window. Candidates (26, fixed now):
  XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS (self
  excluded). If the best correlation is < 0.30 the sector hedge falls back to SPY. **beta_SEC** = OLS slope on it,
  clipped to [0, 3].
- **Pair partner** = the non-ETF stock with the same sector ETF whose o2c correlation is highest, if >= 0.60;
  beta_PAIR = OLS slope on the partner, clipped to [0.2, 3].
- ETF list (never a primary leg of a new setup): the broad / sector / country / leveraged / commodity / crypto ETFs of
  the universe (`ETFS` in `common.py`).
- Trades whose beta is undefined (first ~30 open sessions: 2024-10 and early 2025-03) are dropped from BOTH the hedged
  and the unhedged line, so the two lines compare the same trades.

### 1.3 Hedged P/L (both legs' costs)
- Stock leg: unchanged lab trade (entry at the signal bar close, R = 0.25 x daily ATR, fixed geometry, timed exit by
  15:55), production R via `gates.prod_r` (1c + 1 bps per side, exit free on a target fill, +2c on stops).
- Hedge leg: opposite side, notional = beta x stock notional, entered at the ETF's 5-min close of the entry bar,
  exited at the ETF's close of the stock leg's exit bar (the stock exits intrabar at its target/stop; the hedge is
  priced at that bar's close - up to 5 minutes of mismatch, a known approximation). Hedge P/L in stock-R units:
  -side x beta x stock_px x (H_exit / H_entry - 1) / R. Hedge costs: market orders both sides,
  beta x stock_px x (0.01 / H_entry + 1e-4) per side, no target freebie, no stop extra.
- hedged R = stock production R + hedge P/L - hedge costs.

### 1.4 Task 1 - trade lists scored (no new fitting)
- 33 full-day lists: the 32 `research/bdi/fullday/*-FD.py` modules (30 from `research/bdi/timeofday/data/trades.parquet`
  set `full`; the 3 L3-*-FD regenerated with their FD modules, min_adv 0 as specs.json, first bar per symbol-day,
  09:50-15:00) + RW8 (its window already is 09:50-15:00; timeofday `full`).
- 30 current-window lists (timeofday set `current`) - secondary.
- 40 Reddit base rules (`research/bdi/reddit/strategies.py`: 20 strategies x long/short, no filter, t1s1, full day),
  regenerated with the Reddit engine exactly as `research/bdi/regime1009/gen_reddit.py` (run in row chunks to keep
  memory low; checked against the published n / exp of regime1009).
- 103 lists x 2 hedges (SPY, SEC) = **206 hedged configurations**; the unhedged line on the same trades is a reference.
- Per list and hedge: n, exp R, day-clustered t, ex-best-day, busiest session share, exp/n/t in up / flat / down
  sessions, walk-forward share (`gates.walk_forward`, locked months excluded), verdict vs the live-probation bar.
- t bar per list = max(2.0, sqrt(2 ln(N_lineage + 206))), N_lineage from the source studies: heat 19,200;
  exhaustion 855,600; MF 8,012; NS 7,374; RW1/3/5/7 82,068; RW4/6/6G1/8 81,430; RW2 934,522; ST 120,500;
  L3 11,178 (layering stage only - a lower bound); Reddit 2,551.

### 1.5 Task 2 - relative-value setups (lineage `sw-w2-rv`, new)
- Population: non-ETF symbols, adv20 >= 95M point in time, atr_d > 0, beta / map / partner defined for the session.
- Hedge instrument H by family: **F1 SPY**, **F2 SEC** (sector map 1.2), **F3 PAIR** (partner 1.2).
- Spread at bar close t: S_N(t) = ln(C_t / C_{t-N}) - beta x ln(H_t / H_{t-N}), both from the same session's 5-min
  closes (no signal if t-N is before the 09:35 bar).
- Scale: sigma_bar = mean over the previous 20 open sessions (min 10) of each session's std of 5-min residual
  returns e_b = ln(C_b/C_{b-1}) - beta_d ln(H_b/H_{b-1}) (bars 09:40..15:55, beta_d of that session). z = S_N /
  (sigma_bar x sqrt(N)).
- Rules: **fade** - long when z <= -k (laggard), short when z >= +k (leader); **momentum** - long when z >= +k, short
  when z <= -k. First qualifying bar per symbol-day per side, bar close 09:50..15:00.
- Grid: family {F1, F2, F3} x N {3, 6, 12} x k {1.5, 2.0, 2.5} x {fade, momentum} = 54 rules x 2 sides = 108
  side-configs. Exit: t1s1 on the stock leg, timed exit by 15:55, hedge leg closed at the same bar (1.3).
- Each side-config is scored hedged (the primary score) and single-leg (stock only, what a lab module could trade);
  each rule is also scored as a long+short book (both legs). **N = 108 x 2 + 54 x 2 = 324** -> t bar
  max(2.0, sqrt(2 ln 324)) = **3.40**.
- Plateau neighbours of a config: same family / direction / side / leg-variant with k +- 0.5 and N one step (in the grid).

### 1.6 Bar (RULES.md live-probation bar)
n >= 150; exp > 0 in up AND down sessions (n >= 30 each); day-clustered t >= the bar above; walk-forward positive share
>= 0.6; plateau neighbours' mean exp > 0 (task 2 only; task-1 setups are fixed rules); ex-best-day > 0; busiest session
<= 10% of trades. A single-leg config passing everything -> lab module + staged Testing YAML. A config passing only
hedged -> spec for two-leg execution, no module. Failures reported first.
