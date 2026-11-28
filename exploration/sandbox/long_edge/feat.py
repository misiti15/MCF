"""Long-edge features per live lot (point-in-time at entry unless marked OUTCOME). Usage: python feat.py <scratch>
Writes <scratch>/longs.parquet. Educational only - not financial advice."""
import sys, re
import numpy as np, pandas as pd
S = sys.argv[1]
t = pd.read_parquet(f"{S}/trades.parquet")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
L = t[t.side > 0].drop_duplicates("k").copy()
d = pd.read_parquet(f"{S}/daily.parquet").sort_values(["symbol", "date"])
g = d.groupby("symbol")
d["pc"] = g.close.shift(1); d["pc2"] = g.close.shift(2)
tr = np.maximum(d.high - d.low, np.maximum((d.high - d.pc).abs(), (d.low - d.pc).abs()))
d["atr14"] = tr.groupby(d.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=8).mean())
d["gap"] = (d.open / d.pc - 1) * 100
d["prev_ret"] = (d.pc / d.pc2 - 1) * 100
d["ret5"] = (d.pc / g.close.shift(6) - 1) * 100
d["atr_pct"] = d.atr14 / d.pc * 100
d["day_oc_stock"] = (d.close / d.open - 1) * 100  # OUTCOME
d["dvol20"] = (d.close * d.volume).groupby(d.symbol).transform(lambda s: s.shift(1).rolling(20, min_periods=8).mean())
L = L.merge(d[["symbol", "date", "open", "pc", "gap", "prev_ret", "ret5", "atr_pct", "day_oc_stock", "dvol20"]],
            on=["symbol", "date"], how="left")
L["from_open"] = (L.entry / L.open - 1) * 100            # stock move open -> entry (point in time)
L["from_open_atr"] = L.from_open / L.atr_pct
# SPY context at entry minute (minute bars, point in time) and day outcome
b = pd.read_parquet(f"{S}/spy.parquet"); b.index = pd.to_datetime(b.index)
b = b.tz_convert("America/New_York") if b.index.tz is not None else b.tz_localize("America/New_York")
b["date"] = b.index.strftime("%Y-%m-%d"); b["mn"] = b.index.hour * 60 + b.index.minute
op = b.groupby("date").open.first(); cl = b.groupby("date").close.last()
dd = d[d.symbol == "SPY"].set_index("date")
spy = pd.DataFrame({"spy_open": op, "spy_close": cl}); spy["spy_oc"] = (spy.spy_close / spy.spy_open - 1) * 100
spy["spy_gap"] = dd.gap.reindex(spy.index)
L = L.merge(spy, left_on="date", right_index=True, how="left")
key = b.set_index(["date", "mn"]).close
idx = list(zip(L.date, L.emin - 1))
L["spy_at"] = key.reindex(idx).values
L["spy_from_open"] = (L.spy_at / L.spy_open - 1) * 100
L["spy_after"] = (L.spy_close / L.spy_at - 1) * 100       # OUTCOME
L["rs_from_open"] = L.from_open - L.spy_from_open
u = pd.read_csv("/home/user/MCF/data/universe.csv")
m = pd.read_csv("/home/user/MCF/research/swarm1010/w3_daily/assets_meta.csv")
pat = re.compile(r"\bETF\b|\bETN\b|iShares|ProShares|Direxion|SPDR|Invesco QQQ|Trust, Series|Index Fund|Select Sector|VanEck|Global X|WisdomTree|Vanguard|GraniteShares|Leverage Shares|Tradr|Defiance|YieldMax|T-Rex|MicroSectors", re.I)
etf = set(m.loc[m.is_etf, "symbol"]) | set(u.loc[u.name.fillna("").str.contains(pat), "symbol"])
etf -= {"MU"}
L["etf"] = L.symbol.isin(etf)
L["book"] = np.where(L.account == "primary", "primary", np.where(L.account == "graveyard", "graveyard", "arena"))
L.to_parquet(f"{S}/longs.parquet")
print(len(L), L.gap.notna().mean().round(3), L.spy_at.notna().mean().round(3), L.etf.mean().round(3))
