"""FREQ 2-year candidates for every set symbol. Cached symbols: research/history2y frames (as the parent's first pass).
Fetched symbols (fetch2y.py): frames built with the SAME pipeline (research/history2y/build_frames.py: 1-minute -> 5min ->
mcf.research.setup_lab.build, adv20 from the 1-minute dollar volume of the prior 20 sessions). Arena indicators
(compute(context=False), as the module) + SPY/QQQ change since 09:50. Wide pre-filter so looser copies can be scored:
bar close 13:00-15:00, adv20 >= $30M, ret3 <= -0.30%. Then 1-minute paths 13:00-16:00. Open months only; the locked block
2024-11..2025-02 is never read (fetched data never contains it; cached frames from the open directory only; asserted).
Educational only - not financial advice."""
import sys, os, json, glob, pickle, numpy as np, pandas as pd, pyarrow.dataset as ds
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lib import months, DATA
from mcf.data.bars import resample
from mcf.data.store import BarStore
from mcf.research.setup_lab import build
from mcf.research.arena.indicators import compute
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/"
LOCK = ("2024-11-01", "2025-02-28")
IND = ["ret3", "di_diff7", "atr_d_pct", "adx7", "vwap_atr", "day_pos", "fromOpen_atr", "rvol_day", "ret12", "ret6",
       "ret_since950_atr", "rsi7", "z12"]
sets = json.load(open(S + "sets.json"))
ALL = sorted({s for k, v in sets.items() if k != "VIX" for s in v} | {"SPY", "QQQ"})
FET = sorted(os.path.basename(p)[:-8] for p in glob.glob(S + "cache/1Min/*.parquet"))
CACHED = sorted(set(ALL) - set(FET))
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "fromOpen", "volume"]

def frames_fetched(sym):
    df = BarStore(S + "cache").load(sym)
    if df.empty: return None
    dv = (df.close * df.volume).groupby(df.index.date).sum()
    adv = dv.shift(1).rolling(20, min_periods=5).mean()
    x = build({sym: resample(df, "5min")}, log=lambda *_: None)
    if x is None or not len(x): return None
    x = x.reset_index(drop=True)
    x["adv20"] = pd.to_datetime(x["date"]).dt.date.map(adv).astype("float32")
    x["date"] = pd.to_datetime(x["date"]).dt.strftime("%Y-%m-%d")
    return x

def month_cands(m):
    d = ds.dataset(str(DATA / "frames" / f"month={m}"), format="parquet")
    a = d.to_table(filter=ds.field("symbol").isin(CACHED)).to_pandas()
    a["date"] = pd.to_datetime(a["date"]).dt.strftime("%Y-%m-%d")
    f = pd.read_parquet(S + f"fr2y/{m}.parquet") if os.path.exists(S + f"fr2y/{m}.parquet") else None
    df = pd.concat([a, f], ignore_index=True) if f is not None else a
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    x = compute(df, names=IND, context=False)
    df = pd.concat([df[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20"]], x], axis=1)
    ix = {}
    for e in ("SPY", "QQQ"):
        g = df[df.symbol == e][["date", "tod", "close"]]; b = g[g.tod == 950].set_index("date").close
        ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
    r = df[(df.tod >= 1300) & (df.tod <= 1500) & (df.adv20 >= 30e6) & (df.ret3 <= -0.30)].copy()
    k = pd.MultiIndex.from_arrays([r.date, r.tod])
    r["spy950"] = ix["SPY"].reindex(k).to_numpy(); r["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
    r["src"] = np.where(r.symbol.isin(FET), "fetched", "cache")
    return r

def arr(g):
    hm = g.index.hour * 100 + g.index.minute
    g = g[(hm >= 1300) & (hm < 1600)]
    return ((g.index.hour * 100 + g.index.minute).to_numpy(), g.open.to_numpy(float), g.high.to_numpy(float),
            g.low.to_numpy(float), g.close.to_numpy(float))

def per_sym_paths(a):
    sym, dates = a
    p = S + f"cache/1Min/{sym}.parquet" if sym in FET else f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet"
    try: df = pd.read_parquet(p)
    except Exception: return {}
    ds_ = df.index.strftime("%Y-%m-%d")
    df = df[~((ds_ >= LOCK[0]) & (ds_ <= LOCK[1])) & np.isin(ds_, list(dates))]
    return {(sym, d): arr(g) for d, g in df.groupby(df.index.strftime("%Y-%m-%d"))}

if __name__ == "__main__":
    step = sys.argv[1]
    if step == "frames":
        os.makedirs(S + "fr2y", exist_ok=True)
        with Pool(4) as p:
            res = p.map(frames_fetched, FET)
        x = pd.concat([r for r in res if r is not None], ignore_index=True)
        assert not x.date.between(*LOCK).any()
        x = x[(x.date >= "2024-10-01") & (x.date <= "2026-10-16")]
        for m, g in x.groupby(x.date.str[:7]):
            g.to_parquet(S + f"fr2y/{m}.parquet", index=False)
        print("fetched frames", len(x), x.symbol.nunique())
    elif step == "cands":
        ms = [m for m in months() if m not in ("2024-11", "2024-12", "2025-01", "2025-02")]
        with Pool(3) as p:
            parts = p.map(month_cands, ms)
        c = pd.concat(parts, ignore_index=True)
        c = c[c.date <= "2026-10-16"]
        assert not c.date.between(*LOCK).any()
        c.to_parquet(S + "cand2y.parquet"); print(len(c), c.symbol.nunique(), c.date.min(), c.date.max())
    elif step == "paths":
        c = pd.read_parquet(S + "cand2y.parquet")
        c = c[(c.atr_d_pct >= 1.5)]
        sd = c.groupby("symbol").date.apply(set).to_dict()
        with Pool(4) as p:
            res = p.map(per_sym_paths, list(sd.items()))
        P = {k: v for r in res for k, v in r.items()}
        pickle.dump(P, open(S + "paths2y.pkl", "wb")); print(len(P))
    elif step == "rpaths":
        m = pd.read_parquet(S + "replay_1min.parquet")
        P = {(s, d): arr(g.set_index(g.index) if False else g) for (s, d), g in m.groupby(["symbol", "date"])}
        pickle.dump(P, open(S + "paths_replay.pkl", "wb")); print(len(P))
