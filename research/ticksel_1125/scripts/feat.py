"""TICKSEL: point-in-time ticker traits per symbol-day (prior days only, plus today's open for the gap).
Locked block 2024-11-01..2025-02-28 is never read (pyarrow filter + assert). Educational only - not financial advice."""
import json, re
import numpy as np, pandas as pd
import pyarrow.dataset as pads
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"
T = S + "ticksel/"
LOCK = ("2024-11-01", "2025-02-28")

def load_hist():
    ds = pads.dataset("/home/user/MCF/research/history2y/data/daily.parquet")
    f = pads.field("date")
    probe = ds.head(1).to_pandas()["date"].iloc[0]
    if isinstance(probe, str):
        flt = (f < LOCK[0]) | (f > LOCK[1])
    else:
        flt = (f < pd.Timestamp(LOCK[0]).date()) | (f > pd.Timestamp(LOCK[1]).date())
    d = ds.to_table(filter=flt, columns=["symbol", "date", "open", "high", "low", "close", "volume"]).to_pandas()
    d["date"] = d["date"].astype(str)
    assert not d.date.between(*LOCK).any()
    return d

def load_fresh():
    d = pd.read_parquet("/home/user/MCF/data/cache_fresh/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    d["date"] = d["date"].astype(str)
    return d

def load_live():
    return pd.read_parquet(T + "live_daily.parquet")

def traits(d):
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    d["dv"] = d.close * d.volume
    g = d.groupby("symbol", sort=False)
    pc = g.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    d["tr"] = tr
    d["ret"] = d.close / pc - 1
    g = d.groupby("symbol", sort=False)
    out = pd.DataFrame({"symbol": d.symbol, "date": d.date})
    out["prev_close"] = pc
    out["gap"] = (d.open / pc - 1) * 100
    out["adv20"] = g.dv.transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    out["atrp"] = g.tr.transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean()) / pc * 100
    out["ret1"] = g.ret.shift(1) * 100
    out["ret5"] = (pc / g.close.shift(6) - 1) * 100
    out["rvol1"] = g.dv.shift(1) / out["adv20"]
    spy = d[d.symbol == "SPY"][["date", "ret"]].rename(columns={"ret": "spy"})
    x = d[["symbol", "date", "ret"]].merge(spy, on="date", how="left")
    x["xy"] = x.ret * x.spy; x["yy"] = x.spy ** 2
    gx = x.groupby("symbol", sort=False)
    m = lambda c: gx[c].transform(lambda s: s.shift(1).rolling(60, min_periods=30).mean())
    cov = m("xy") - m("ret") * m("spy"); var = m("yy") - m("spy") ** 2
    x["beta"] = cov / var
    out = out.merge(x[["symbol", "date", "beta"]], on=["symbol", "date"], how="left")
    return out

def static():
    u = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"]).drop_duplicates("symbol")
    nm = u.set_index("symbol").name.fillna("")
    etf = nm.str.contains(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Invesco QQQ|Grayscale|iPath|Bitcoin Trust|Ether", case=False, regex=True)
    lev = nm.str.contains(r"\b[23]X\b|Ultra|Bull|Bear|Inverse|Short|Leveraged|2x|3x|VIX", regex=True)
    sec = json.load(open(S + "pyramid/L1/secmap.json"))
    spr = json.load(open(S + "spreads-fresh.json"))
    sp = {k: float(np.median(v)) for k, v in spr.items() if len(v)}
    etb = pd.read_parquet(S + "pyramid/S/etb_rate.parquet").rate
    st = pd.DataFrame({"symbol": sorted(set(nm.index) | set(sec) | set(sp) | set(etb.index))})
    st["etf"] = st.symbol.map(etf).fillna(False).astype(bool)
    st["levinv"] = st.symbol.map(lev).fillna(False).astype(bool) & st.etf
    st["sector"] = st.symbol.map(sec)
    st.loc[st.etf, "sector"] = "ETF"
    st["sector"] = st.sector.fillna("other")
    st["spread"] = st.symbol.map(sp)
    st["etb"] = st.symbol.map(etb)
    return st

if __name__ == "__main__":
    st = static(); st.to_parquet(T + "static.parquet")
    print(st.etf.sum(), st.levinv.sum(), st.sector.value_counts().to_dict(), st.spread.notna().sum())
    for nm, fn in (("t1", load_hist), ("t2", load_fresh), ("live", load_live)):
        x = traits(fn()); x.to_parquet(T + f"tr_{nm}.parquet"); print(nm, x.shape, x.date.min(), x.date.max())
