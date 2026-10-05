"""Setup discovery: mine layered rules ("RSI > 65" AND "below the 20 SMA" AND ...) from recent data.

MarcoFlow mined a new "best rule" every day from ~29 trades and named 63 different winners in 83 days
— it was fitting noise. This miner keeps the layering idea but adds the guards that were missing:

  * one entry per rule per symbol-day (the FIRST bar where all layers are true) — no counting the
    same move 30 times
  * outcome = +1R before -1R (owner's success model), R = 0.25 x daily ATR, costs charged in R
  * rules are FOUND on the older 2/3 of sessions and must REPLICATE on the newest 1/3 (out of sample)
  * minimum samples, Wilson lower bounds, and the number of rules tried is reported
  * entries before `no_entry_before` (owner's 9:30-9:50 caution) are excluded

Candidates are reported, never traded automatically. Promoting one is a config entry for
`RuleStrategy` (mcf/strategies/setups.py), which uses these exact features live and in backtests.
"""

from __future__ import annotations

import itertools
import json
import os
from datetime import datetime, timedelta
from math import sqrt

import numpy as np
import pandas as pd

from .data.bars import normalize, rth
from .layers import LABELS, LAYERS, PRIOR_BARS, layer_frame

def symbol_frame(d5: pd.DataFrame, rvol_days: int = 14) -> pd.DataFrame:
    """Layer features (mcf.layers.layer_frame, same code as live) for every session of one symbol,
    plus the bar high/low and the prior daily ATR used to size R."""
    days = sorted(set(d5.index.date))
    daily = d5.groupby(d5.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = daily["close"].shift(1)
    tr = pd.concat([daily.high - daily.low, (daily.high - pc).abs(), (daily.low - pc).abs()], axis=1).max(axis=1)
    atr_prev = tr.rolling(14, min_periods=10).mean().shift(1)
    slot = (d5.index.hour * 60 + d5.index.minute - 570) // 5
    cum = d5["volume"].groupby(d5.index.date).cumsum()
    prof = pd.DataFrame({"day": d5.index.date, "slot": slot, "cum": cum.to_numpy()}).pivot_table(
        index="day", columns="slot", values="cum", aggfunc="last")
    base = prof.rolling(rvol_days, min_periods=5).mean().shift(1)      # prior sessions only
    out = []
    for i, day in enumerate(days):
        if i == 0 or not np.isfinite(atr_prev.get(day, np.nan)):
            continue
        today = d5[d5.index.date == day]
        prior = d5[d5.index.date < day].tail(PRIOR_BARS)
        ref = base.loc[day].reindex(slot[d5.index.date == day]).to_numpy() if day in base.index else None
        rv = None if ref is None else today["volume"].cumsum().to_numpy() / np.where(ref > 0, ref, np.nan)
        f = layer_frame(today, prior, float(pc[day]), rv)
        f["high"], f["low"], f["atr_d"] = today["high"].to_numpy(), today["low"].to_numpy(), atr_prev[day]
        out.append(f)
    return pd.concat(out) if out else pd.DataFrame()


def _outcomes(f: pd.DataFrame, r_frac: float, cost_ps: float, close_by: int = 1555) -> pd.DataFrame:
    """For each bar: did +1R come before -1R (long and short) entering at that bar's close, and the
    result in R after costs (exit at +-1R, else at the last bar before `close_by`). A bar that touches
    both counts as a loss. Vectorised per session (<= 78 five-minute bars)."""
    c, h, l = f.close.to_numpy(), f.high.to_numpy(), f.low.to_numpy()
    r = f.atr_d.to_numpy() * r_frac
    tod = f.tod.to_numpy()
    succ = np.full((len(f), 2), np.nan)
    pnl = np.full((len(f), 2), np.nan)
    bounds = np.flatnonzero(np.r_[True, np.array(f.index.date[1:]) != np.array(f.index.date[:-1]), True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        cc, hh, ll, rr = c[a:b], h[a:b], l[a:b], r[a:b]
        m = b - a
        later = np.triu(np.ones((m, m), bool), 1) & (tod[a:b] <= close_by)[None, :]
        last = np.where(later.any(1), m - 1 - np.argmax(later[:, ::-1], 1), np.arange(m))
        for k, side in enumerate((1, -1)):
            up = cc + side * rr
            dn = cc - side * rr
            hit_up = (hh[None, :] >= up[:, None]) if side == 1 else (ll[None, :] <= up[:, None])
            hit_dn = (ll[None, :] <= dn[:, None]) if side == 1 else (hh[None, :] >= dn[:, None])
            hit_up &= later
            hit_dn &= later
            big = m + 1
            fu = np.where(hit_up.any(1), np.argmax(hit_up, 1), big)
            fd = np.where(hit_dn.any(1), np.argmax(hit_dn, 1), big)
            won = fu < fd                      # same bar -> fd <= fu -> loss
            lost = (fd <= fu) & (fd < big)
            val = np.where(won, 1.0, np.where(lost, -1.0, side * (cc[last] - cc) / rr))
            ok = np.isfinite(rr) & (rr > 0)
            succ[a:b, k] = np.where(ok, won.astype(float), np.nan)
            pnl[a:b, k] = np.where(ok, val - 2 * cost_ps / np.where(ok, rr, 1), np.nan)
    return pd.DataFrame({"succ_long": succ[:, 0], "succ_short": succ[:, 1],
                         "r_long": pnl[:, 0], "r_short": pnl[:, 1]}, index=f.index)


def wilson_lb(k: float, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    return (p + z * z / (2 * n) - z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def build_frame(bars: dict[str, pd.DataFrame], cfg: dict, log=print) -> pd.DataFrame:
    d = cfg.get("discovery", {})
    frames = []
    for n, (sym, df) in enumerate(bars.items()):
        if len(df) < 200:
            continue
        f = symbol_frame(df)
        if f.empty:
            continue
        f = f.join(_outcomes(f, d.get("r_atr_frac", 0.25), cfg["costs"].get("slippage_per_share", 0.01)))
        f["symbol"] = sym
        frames.append(f)
        if n % 250 == 0:
            log(f"discover: features {n}/{len(bars)}")
    if not frames:
        return pd.DataFrame()
    x = pd.concat(frames)
    start = int(pd.Timestamp(cfg.get("live", {}).get("no_entry_before", "09:50")).strftime("%H%M"))
    x = x[(x.tod >= start) & (x.tod <= 1500) & x.rsi.notna() & x.sma20.notna()]
    x["date"] = x.index.date
    return x


def mine(x: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    d = cfg.get("discovery", {})
    max_layers = d.get("max_layers", 3)
    min_train, min_test = d.get("min_train", 150), d.get("min_test", 60)
    dates = np.array(sorted(x.date.unique()))
    cut = dates[int(len(dates) * 2 / 3)]
    test = x.date >= cut
    grp = pd.factorize(x.symbol.astype(str) + "|" + x.date.astype(str))[0]
    masks = {lab: np.asarray(fn(x).fillna(False), dtype=bool) for lab, fn in LABELS.items()}
    feats = list(LAYERS)
    base = {s: float(np.nanmean(x[f"succ_{s}"])) for s in ("long", "short")}
    rows, tried = [], 0
    for k in range(1, max_layers + 1):
        for combo in itertools.combinations(feats, k):
            for labs in itertools.product(*[[lab for lab, _ in LAYERS[c]] for c in combo]):
                m = masks[labs[0]].copy()
                for lab in labs[1:]:
                    m &= masks[lab]
                idx = np.flatnonzero(m)
                if len(idx) < min_train:
                    continue
                _, first = np.unique(grp[idx], return_index=True)
                idx = idx[first]                      # first trigger per symbol-day
                for side in ("long", "short"):
                    tried += 1
                    s = x[f"succ_{side}"].to_numpy()[idx]
                    r = x[f"r_{side}"].to_numpy()[idx]
                    te = test.to_numpy()[idx]
                    tr_n, te_n = int((~te).sum()), int(te.sum())
                    if tr_n < min_train:
                        continue
                    tr_s, tr_r = s[~te], r[~te]
                    tr_lb = wilson_lb(np.nansum(tr_s), tr_n)
                    if tr_lb <= base[side] or np.nanmean(tr_r) <= 0:
                        continue
                    te_s, te_r = s[te], r[te]
                    rows.append({
                        "side": side, "layers": list(labs), "n_layers": k,
                        "train_n": tr_n, "train_success": round(float(np.nanmean(tr_s)), 3), "train_lb": round(tr_lb, 3),
                        "train_exp_r": round(float(np.nanmean(tr_r)), 3),
                        "test_n": te_n, "test_success": round(float(np.nanmean(te_s)), 3) if te_n else None,
                        "test_lb": round(wilson_lb(np.nansum(te_s), te_n), 3) if te_n else None,
                        "test_exp_r": round(float(np.nanmean(te_r)), 3) if te_n else None,
                        "symbols": len(set(x.symbol.to_numpy()[idx])),
                    })
    res = pd.DataFrame(rows)
    if len(res):
        # identical trade sets under different names -> keep the simplest rule
        stats = ["side", "train_n", "train_success", "train_exp_r", "test_n", "test_success", "test_exp_r"]
        res = res.sort_values("n_layers").drop_duplicates(stats, keep="first")
        # replicated = beats the baseline with confidence out of sample, and makes money after costs there
        res["replicated"] = (res.test_n >= min_test) & (res.test_exp_r > 0) & (res.test_lb > base_rate(res, base))
        res = res.sort_values(["replicated", "test_lb", "test_exp_r"], ascending=False)
    meta = {"rules_tried": tried, "sessions": len(dates), "train_until": str(cut), "rows": int(len(x)),
            "symbols": int(x.symbol.nunique()), "baseline_success": {k: round(v, 3) for k, v in base.items()}}
    return res, meta


def base_rate(res: pd.DataFrame, base: dict) -> pd.Series:
    return res.side.map(base)


def fetch_5m(symbols: list[str], days: int, feed: str = "sip", batch: int = 200, log=print) -> dict[str, pd.DataFrame]:
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    dc = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
    end = datetime.utcnow() - timedelta(minutes=20)
    start = end - timedelta(days=int(days * 1.5) + 5)
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(symbols), batch):
        req = StockBarsRequest(symbol_or_symbols=symbols[i:i + batch], timeframe=TimeFrame(5, TimeFrameUnit.Minute),
                               start=start, end=end, adjustment=Adjustment.SPLIT, feed=DataFeed(feed))
        df = dc.get_stock_bars(req).df
        for sym, g in (df.groupby(level=0) if not df.empty else []):
            out[sym] = rth(normalize(g.droplevel(0)))
        log(f"discover: fetched {min(i + batch, len(symbols))}/{len(symbols)} symbols")
    return out


def run_discovery(cfg: dict, universe: pd.DataFrame, out_dir: str, log=print) -> dict:
    d = cfg.get("discovery", {})
    core = universe[universe.get("tier", "core") == "core"] if "tier" in universe else universe
    syms = core.sort_values("adv", ascending=False).symbol.head(d.get("max_symbols", 1500)).tolist()
    bars = fetch_5m(syms, d.get("sessions", 60), cfg["data"]["feed"], log=log)
    x = build_frame(bars, cfg, log=log)
    log(f"discover: {len(x):,} decision bars from {x.symbol.nunique() if len(x) else 0} symbols")
    res, meta = mine(x, cfg)
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    top = res.head(d.get("report_top", 40)) if len(res) else res
    payload = {"generated": stamp, "disclaimer": "Educational only — not financial advice.", **meta,
               "candidates": json.loads(top.to_json(orient="records")) if len(top) else [],
               "replicated": int(res.replicated.sum()) if len(res) else 0, "passed_train": int(len(res))}
    with open(os.path.join(out_dir, "latest.json"), "w") as fh:
        json.dump(payload, fh, indent=1)
    with open(os.path.join(out_dir, f"{stamp}.md"), "w") as fh:
        fh.write(report_md(payload))
    return payload


def report_md(p: dict) -> str:
    lines = [f"# Setup discovery — {p['generated']}", "", "*Educational only — not financial advice.*", "",
             f"Tried **{p['rules_tried']:,}** rule/direction combinations on {p['symbols']} symbols, "
             f"{p['sessions']} sessions ({p['rows']:,} decision bars, entries from 09:50). "
             f"Found on sessions up to {p['train_until']}, checked on the sessions after it.", "",
             f"Baseline success (+1R before -1R, any bar): long {p['baseline_success']['long']:.1%}, "
             f"short {p['baseline_success']['short']:.1%}.", "",
             f"{p['passed_train']} distinct rules beat the baseline in the training period; **{p['replicated']} replicated** "
             "out of sample (test-period Wilson lower bound above the baseline and expectancy > 0 after costs). "
             "With this many rules tried, "
             "some will replicate by luck: a candidate needs a full walk-forward backtest and the promotion "
             "gates before it trades.", "",
             "| Replicated | Side | Layers | Train n | Train success | Train exp R | Test n | Test success | Test exp R |",
             "|---|---|---|---|---|---|---|---|---|"]
    for c in p["candidates"]:
        lines.append(f"| {'yes' if c['replicated'] else 'no'} | {c['side']} | {' + '.join(c['layers'])} | {c['train_n']} | "
                     f"{c['train_success']:.1%} | {c['train_exp_r']:+.3f} | {c['test_n']} | "
                     f"{(c['test_success'] or 0):.1%} | {(c['test_exp_r'] or 0):+.3f} |")
    return "\n".join(lines) + "\n"
