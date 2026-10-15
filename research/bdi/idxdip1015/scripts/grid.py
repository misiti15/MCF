"""Pre-declared grid (PLAN.md): 4 variants x 6 triggers x 7 exits x instruments = 756 configurations, run through the
production strategy class (mcf.strategies.index_dip.IndexDipBounce) and the production fill model
(mcf.backtest.engine.simulate, config costs). Plus the rule-6 random-entry controls. Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd
from common import EXITS, EXTENDED, H2_START, OUT, TRIGGERS, VARIANTS, load, sample

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.strategies.base import DayContext, t
from mcf.strategies.index_dip import IndexDipBounce

cfg = load_config()
COST = Costs.from_cfg(cfg["costs"])
COST_EXT = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"]["extended_slippage_per_share"]})
FLAT = t(cfg["session"]["flatten_by"])
SYMS = sorted({s for v in VARIANTS.values() for s in v["symbols"]} | {"SPY", "QQQ"})
DATA = {s: load(s) for s in SYMS}
RNG_SEED = 20261015


def run_sig(sym, sig, bars):
    tr = simulate(sig, bars, FLAT, COST_EXT if sym in EXTENDED else COST)
    if tr is None:
        return None
    return {"R": tr.r_multiple, "bps": (tr.exit / tr.entry - 1) * 1e4, "reason": tr.exit_reason,
            "entry_time": f"{tr.entry_time:%H:%M}", "exit_time": f"{tr.exit_time:%H:%M}"}


def with_exits(strat, sig):
    for k in ("be_at_r", "trail_r", "trail_after_r", "time_stop_min", "time_stop_min_r"):
        if strat.params.get(k) is not None:
            setattr(sig, k, strat.params[k])
    return sig


def window_bars(bars):
    end = np.array((bars.index + pd.Timedelta(minutes=1)).time)
    return np.flatnonzero((end >= t("09:50")) & (end <= t("10:05")))


def stats(r, dates):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return dict(n=0)
    sd = r.std(ddof=1) if n > 1 else np.nan
    best = int(np.argmax(r))
    return dict(n=n, mean_R=r.mean(), t=r.mean() / sd * np.sqrt(n) if n > 1 and sd > 0 else np.nan,
                win=(r > 0).mean(), mean_R_ex_best=np.delete(r, best).mean() if n > 1 else np.nan,
                best_day=str(dates[best]))


trades, rows = [], []
for v, P in VARIANTS.items():
    idx_days = DATA[P["signal_symbol"]]
    for tg, TP in TRIGGERS.items():
        for ex, EP in EXITS.items():
            for sym in P["symbols"]:
                st = IndexDipBounce(symbols=[sym], signal_symbol=P["signal_symbol"], dip_pct=P["dip_pct"],
                                    dip_by=P["dip_by"], stop_buffer_frac=0.10, **TP, **EP)
                for d, bars in DATA[sym].items():
                    ib = idx_days.get(d)
                    if ib is None or len(ib) < 380:
                        continue
                    ctx = DayContext(sym, d, bars, prev_close=1.0, prev_high=1.0, prev_low=1.0, atr=1.0,
                                     avg_dollar_volume=np.nan, peers={P["signal_symbol"]: ib})
                    for sig in st.signals(ctx):
                        res = run_sig(sym, sig, bars)
                        if res:
                            trades.append({"variant": v, "trigger": tg, "exit": ex, "symbol": sym, "date": d,
                                           "sample": sample(d), "bar_index": sig.bar_index, **res})
T = pd.DataFrame(trades)
T.to_csv(OUT / "trades.csv", index=False)
print("trades", len(T))

# ---- rule-6 controls
rng = np.random.default_rng(RNG_SEED)
ctrl_same, ctrl_all = [], []
dipdays = {v: set() for v in VARIANTS}
for v, P in VARIANTS.items():
    from mcf.strategies.index_dip import find_trigger
    for d, ib in DATA[P["signal_symbol"]].items():
        if len(ib) >= 380 and find_trigger(ib, P["dip_pct"], P["dip_by"], "00:00", "23:59", "recovery", 0.0):
            dipdays[v].add(d)      # dip reached by dip_by (any trigger)
for ex, EP in EXITS.items():
    for sym in SYMS:
        st = IndexDipBounce(symbols=[sym], signal_symbol=sym, stop_buffer_frac=0.10, **EP)
        for d, bars in DATA[sym].items():
            if sample(d) != "DEV":
                continue
            w = window_bars(bars)
            if not len(w):
                continue
            in_any = [v for v, P in VARIANTS.items() if sym in P["symbols"] and d in dipdays[v]]
            # (a) same dip days: 20 random entry bars in the window, mean per day
            if in_any:
                rs = []
                for k in rng.choice(w, size=20):
                    sig = st.build_signal(sym, bars, int(k))
                    if sig is not None and (res := run_sig(sym, with_exits(st, sig), bars)):
                        rs.append((res["R"], res["bps"]))
                if rs:
                    for v in in_any:
                        ctrl_same.append({"variant": v, "exit": ex, "symbol": sym, "date": d,
                                          "R": np.mean([a for a, _ in rs]), "bps": np.mean([b for _, b in rs])})
            # (b) all DEV sessions: 3 random entry bars, drop at entry >= 0.05% of the open
            o = bars.open.iloc[0]
            rs = []
            for k in rng.choice(w, size=3):
                if (o - bars.low.iloc[: k + 1].min()) / o < 0.0005:
                    continue
                sig = st.build_signal(sym, bars, int(k))
                if sig is not None and (res := run_sig(sym, with_exits(st, sig), bars)):
                    rs.append((res["R"], res["bps"]))
            if rs:
                ctrl_all.append({"exit": ex, "symbol": sym, "date": d, "R": np.mean([a for a, _ in rs]),
                                 "bps": np.mean([b for _, b in rs])})
CS, CA = pd.DataFrame(ctrl_same), pd.DataFrame(ctrl_all)
CS.to_csv(OUT / "control_samedays.csv", index=False)
CA.to_csv(OUT / "control_alldays.csv", index=False)

N = len(VARIANTS["V1"]["symbols"]) * 6 * 7 + 3 * len(VARIANTS["V2"]["symbols"]) * 6 * 7
for (v, tg, ex, sym), g in T.groupby(["variant", "trigger", "exit", "symbol"]):
    dev = g[g["sample"] == "DEV"].sort_values("date")
    hold = g[g["sample"] == "HOLDOUT"]
    s = stats(dev.R.to_numpy(), dev.date.to_numpy())
    h1, h2 = dev[dev.date < H2_START], dev[dev.date >= H2_START]
    cs = CS[(CS.variant == v) & (CS.exit == ex) & (CS.symbol == sym)]
    ca = CA[(CA.exit == ex) & (CA.symbol == sym)]
    rows.append({"variant": v, "trigger": tg, "exit": ex, "symbol": sym, "index_row": sym in ("SPY", "QQQ"), **s,
                 "mean_bps": dev.bps.mean(), "H1_n": len(h1), "H1_R": h1.R.mean(), "H2_n": len(h2), "H2_R": h2.R.mean(),
                 "ctrl_same_R": cs.R.mean(), "ctrl_same_bps": cs.bps.mean(), "ctrl_all_R": ca.R.mean(),
                 "ctrl_all_bps": ca.bps.mean(), "ctrl_all_n": len(ca),
                 "holdout_n": len(hold), "holdout_R": hold.R.mean() if len(hold) else np.nan})
Rz = pd.DataFrame(rows)
Rz["bar_t"] = max(1.5, np.sqrt(2 * np.log(N)))
Rz.round(4).to_csv(OUT / "results.csv", index=False)
json.dump({"N_grid": N, "N_lineage": N + 126, "N_index_selection": 4 * 6 * 7,
           "bar_t_grid": max(1.5, np.sqrt(2 * np.log(N))), "bar_t_lineage": max(1.5, np.sqrt(2 * np.log(N + 126))),
           "configs_with_trades": int(len(Rz))}, open(OUT / "counts.json", "w"), indent=1)
print("configs", N, "rows", len(Rz))
