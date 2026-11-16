"""Mechanic orb20_a: candidate extraction with the PRODUCTION context pipeline (mcf.backtest.engine: SymbolHistory,
universe_ok, in_play_filter, rank_contexts - as research/history2y/rescore_bt.py). For every session and every name with
rank_rvol20 <= 40 that passes the ORB20 liquidity check, store the 09:49 features and the day's 1-minute bars, plus the
production ORB20 (variant A) trade for parity. Locked block 2024-11-01..2025-02-28: never simulated and its rows are
never loaded (warm-up of the first post-lock chunk starts 2025-03-01). Educational only - not financial advice.
    python ext.py <chunk-tag> <first-month> <last-month> [sim_from]
"""
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.backtest.engine import Backtester, SymbolHistory, in_play_filter, is_extended, rank_contexts, simulate, universe_ok
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.base import t
from mcf.strategies.setups import build_strategies
from mcf.strategies.research_setups import _liquid
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-orb20/"
LOCK_LO, LOCK_HI = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-03-01")
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]


def main(tag, m0, m1, sim_from=None):
    cfg = load_config()
    for k, v in cfg["strategies"].items():
        v["enabled"] = k == "orb20_a"
    strats = build_strategies(cfg)
    assert [s.name for s in strats] == ["orb20_a"]
    st = strats[0]
    bt = Backtester(strats, cfg)
    flat = t(cfg["session"]["flatten_by"])
    store = BarStore("/home/user/MCF/data/cache_hist")
    syms = store.symbols()
    lo = pd.Period(m0, "M").start_time
    hi = (pd.Period(m1, "M") + 1).start_time
    warm = lo - pd.Timedelta(days=62)
    if lo >= LOCK_HI and warm < LOCK_HI:
        warm = LOCK_HI
    assert not (warm < LOCK_HI and hi > LOCK_LO), "chunk touches the locked block"
    t0 = time.time()
    data = store.load_many(syms, start=warm.strftime("%Y-%m-%d"), end=hi.strftime("%Y-%m-%d"))
    if m1 >= "2026-11":
        tm = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
        tm["ts"] = pd.to_datetime(tm.ts, utc=True).dt.tz_convert("America/New_York")
        tm = tm[tm.symbol.isin(set(syms))]
        for s, g in tm.groupby("symbol"):
            g = g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
            g = g[(g.index.time >= t("09:30")) & (g.index.time < t("16:00"))]
            if s in data:
                d0 = data[s]
                g.index = g.index.astype(d0.index.dtype)
                data[s] = pd.concat([d0[d0.index < g.index[0]], g])
    for s, df in data.items():
        assert not ((df.index >= pd.Timestamp(LOCK_LO, tz=df.index.tz)) & (df.index < pd.Timestamp(LOCK_HI, tz=df.index.tz))).any()
    hist = {s: SymbolHistory(s, df) for s, df in data.items() if len(df)}
    del data
    print(tag, "loaded", len(hist), f"{time.time() - t0:.0f}s", flush=True)
    dates = sorted({d for h in hist.values() for d in h.by_day if m0 <= str(d)[:7] <= m1})
    if sim_from:
        dates = [d for d in dates if str(d) >= sim_from]
    feats, bars, prod = [], [], []
    for d in dates:
        ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
        orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
        ctxs, _ = in_play_filter(ctxs, orv, cfg)
        rank_contexts(ctxs)
        for c in ctxs:
            if c.symbol == "SPY":
                b = c.bars.copy(); b["symbol"] = "SPY"; b["date"] = str(d); bars.append(b)
            if c.rank_rvol20 is None or c.rank_rvol20 > 40 or not _liquid(c):
                continue
            times = c.times()
            hit = np.flatnonzero(times == t("09:49"))
            if not len(hit) or hit[0] + 1 >= len(c.bars):
                continue
            i = int(hit[0])
            rng = c.bars.iloc[: i + 1]
            ext = is_extended(c, cfg)
            feats.append(dict(symbol=c.symbol, date=str(d), i49=i, rank20=c.rank_rvol20, rank5=c.rank_rvol,
                              rv20=float(c.rvol().iloc[i]), hi=float(rng.high.max()), lo=float(rng.low.min()),
                              op=float(rng.open.iloc[0]), c49=float(rng.close.iloc[-1]), vw49=float(c.vwap().iloc[i]),
                              atr=c.atr, pc=c.prev_close, ph=c.prev_high, pl=c.prev_low, adv=c.avg_dollar_volume,
                              sma20=c.sma20, ext=ext, vol20=float(rng.volume.sum())))
            b = c.bars.copy(); b["symbol"] = c.symbol; b["date"] = str(d); bars.append(b)
            costs = bt.costs_ext if ext else bt.costs
            if st.eligible(c):
                for sig in st.signals(c):
                    tr = simulate(sig, c.bars, flat, costs)
                    if tr:
                        prod.append(dict(symbol=tr.symbol, date=str(d), side=tr.side, entry=tr.entry, stop=tr.stop,
                                         target=tr.target, entry_time=str(tr.entry_time), exit_time=str(tr.exit_time),
                                         exit=tr.exit, reason=tr.exit_reason, r=tr.r_multiple))
    pd.DataFrame(feats).to_parquet(OUT + f"feat_{tag}.parquet", index=False)
    bb = pd.concat(bars)
    bb.index.name = "ts"
    bb.reset_index().to_parquet(OUT + f"bars_{tag}.parquet", index=False)
    pd.DataFrame(prod).to_parquet(OUT + f"prod_{tag}.parquet", index=False)
    print(tag, len(dates), "sessions", len(feats), "cands", len(prod), "prod trades", f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
