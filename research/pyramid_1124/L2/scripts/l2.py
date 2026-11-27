"""PYRAMID L2 harness on the bench10 pipeline. Stages: sig1 | walk1 | t2 | fit | check. Educational only - not financial advice."""
from __future__ import annotations
import importlib.util, json, os, re, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

INBOX = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(INBOX / "research/ultimate_1119/top10"))
sys.path.insert(0, str(INBOX))
sys.path.insert(0, str(HERE / "modules"))
import bench10 as B  # noqa
from l2common import gate_g  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
W = HERE / "work"
SEED = INBOX / "research/swarm1017/final/modules/AR-AM-gapdown-capitulation.py"
ETF = INBOX / "research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py"
C2 = HERE / "modules/C2_gapdn_orh_reclaim.py"
C3 = HERE / "modules/C3_flush_spring.py"
# name: (module, params, gate, cwt, window, min_adv, geom)
CFG = {
    "C1a": (SEED, {}, False, False, (950, 1100), 95e6, "t1s1"),
    "C1b": (SEED, {}, True, False, (950, 1100), 95e6, "t1s1"),
    "C1c": (SEED, {"WINDOW": (950, 1200)}, False, False, (950, 1155), 95e6, "t1s1"),
    "C2a": (C2, {"GAP_PCT": -1.5, "GAP_ATR": -0.5}, False, True, (1000, 1200), 95e6, "t1s1"),
    "C2b": (C2, {"GAP_PCT": -1.5, "GAP_ATR": -0.5}, True, True, (1000, 1200), 95e6, "t1s1"),
    "C2c": (C2, {"GAP_PCT": -3.0, "GAP_ATR": -1.0}, False, True, (1000, 1200), 95e6, "t1s1"),
    "C2d": (C2, {"GAP_PCT": -3.0, "GAP_ATR": -1.0}, True, True, (1000, 1200), 95e6, "t1s1"),
    "C3a": (C3, {"VR": 2.0}, False, True, (1000, 1430), 95e6, "t1s1"),
    "C3b": (C3, {"VR": 2.0}, True, True, (1000, 1430), 95e6, "t1s1"),
    "C3c": (C3, {"VR": 3.0}, False, True, (1000, 1430), 95e6, "t1s1"),
    "C3d": (C3, {"VR": 3.0}, True, True, (1000, 1430), 95e6, "t1s1"),
    "C4a": (ETF, {}, True, False, (1400, 1500), 95e6, "t05s1"),
    "C4bench": (ETF, {}, False, False, (1400, 1500), 95e6, "t05s1"),
}
BASEMOD = HERE / "modules/BASE.py"
if os.environ.get("L2_BASE"):
    CFG = {f"BASE-{k}": (BASEMOD, {"KIND": k}, False, k == "C2" or k == "C3", w, 95e6, "t05s1" if k == "C4" else "t1s1")
           for k, w in (("C1", (950, 1100)), ("C2", (1000, 1200)), ("C3", (1000, 1430)), ("C4", (1400, 1500)))}
    W = HERE / "work_base"
PRIMARY = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]


def _load(name, path, params):
    spec = importlib.util.spec_from_file_location("l2_" + re.sub(r"\W", "_", name), path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for k, v in params.items():
        setattr(m, k, v)
    return m


class Wrap:
    def __init__(self, base, gate, rnd, win):
        self.base, self.gate, self.rnd, self.win = base, gate, rnd, win
        self.SIDE, self.GEOM = base.SIDE, getattr(base, "GEOM", "t1s1")

    def mask(self, df):
        m = np.asarray(self.base.mask(df), bool)
        if self.gate:
            m &= gate_g(df)
        if not self.rnd:
            return m
        key = (df["symbol"].astype(str) + "|" + df["date"].astype(str)).to_numpy()
        tod = df["tod"].to_numpy(int)
        okw = (tod >= self.win[0]) & (tod <= self.win[1]) & np.isfinite(df["atr_d"].to_numpy(float))
        hitk = set(key[m])
        out = np.zeros(len(df), bool)
        if not hitk:
            return out
        idx = pd.Series(np.arange(len(df)))[okw & pd.Series(key).isin(hitk).to_numpy()]
        for k, g in idx.groupby(key[idx.values]):
            r = np.random.default_rng(zlib.crc32(k.encode())).integers(len(g))
            out[g.values[r]] = True
        return out


def inventory():
    inv, mods = [], {}
    for nm, (p, prm, gate, cwt, win, adv, geom) in CFG.items():
        base = _load(nm, p, prm)
        if nm == "BASE-C4":
            base.ETF = _load("etf", ETF, {}).SYMBOLS
        for rnd in ((False,) if os.environ.get("L2_BASE") else (False, True)):
            name = ("RND-" if rnd else "") + nm
            mods[name] = Wrap(base, gate, rnd, (max(950, win[0]), min(1500, win[1])))
            inv.append(dict(setup=name, module=str(p), side=1, geom=geom, w_lo=win[0], w_hi=win[1], min_adv=adv, refire=False,
                            cooldown=1, prefilter="", account="testing", cfg="", struct=False, cwt=cwt))
    for st in ([] if os.environ.get("L2_BASE") else B.inventory()):
        if st["setup"] in PRIMARY:
            inv.append(st); mods[st["setup"]] = B.load_mod(st["setup"], st["module"])
    return inv, mods


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    inv, mods = inventory()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str); f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f["date"].unique())
    fx = B.with_head(f, B.head_rows_t1(month, f))
    o = B.signals(f, fx, inv, mods)
    o.to_parquet(W / f"sig1_{month}.parquet")
    return month, len(o)


def t2_job(sym):
    import research.history2y.build_frames as BF
    p = B.FRESH / "1Min" / f"{sym}.parquet"
    b = pd.read_parquet(p); b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ); b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, None
    if "ctx" not in B.WCTX:
        c = pd.read_parquet(B.FRESH / "ctx.parquet"); c["date"] = c["date"].astype(str); B.WCTX["ctx"] = c
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    h = B.head_rows_from_1min(sym, b)
    fx = B.with_head(f, h) if len(h) else f
    inv, mods = inventory()
    o = B.signals(f, fx, inv, mods)
    if not len(o):
        return sym, None
    w = B.walk_trades(o, b)
    a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
    return sym, o.join(a)


if __name__ == "__main__":
    W.mkdir(exist_ok=True)
    st = sys.argv[1]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, ms):
                print(r, flush=True)
    elif st == "walk1":
        sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
        B.no_locked(sig["date"].unique())
        jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            out = [x for r in p.imap_unordered(B.walk1_job, jobs, chunksize=4) for x in r]
        a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
        sig.join(a).to_parquet(W / "trades_t1.parquet"); print(len(sig))
    elif st == "t2":
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        out = []
        with Pool(3) as p:
            for i, (sym, o) in enumerate(p.imap_unordered(t2_job, syms)):
                if o is not None:
                    out.append(o)
                if i % 50 == 0:
                    print(i, flush=True)
        pd.concat(out, ignore_index=True).to_parquet(W / "trades_t2.parquet")
