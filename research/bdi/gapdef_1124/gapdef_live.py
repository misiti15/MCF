"""GAPDEF-1124 part (i): the pre-registered family-wide gap-definition remedy on all 10 live journals since 10-23.
Merges backlog nightly-1124-gapdn-min-real-gap + nightly-1124-thin-open-print-guard (consultant check-in 11-24).

Family (short setups whose rule has a 'gapped down' layer; every variant / account copy): RW1-gapdn, RW3-gapdn,
RW5-...-gapdn, RW7-gapdn, RW3S-gapdn (own rule gap < 0; RW7-WB3 gap < -0.5), NM-MF3-qqqdn-gapdn (gap <= 0), L3-gap-slope
fromopen / lowdist / rsi5hi (gap <= -2.657; L3-fromopen-WB4 <= -3.2). Not in scope: CWT09 (gap <= -5 / -10 already),
NM-RWR1 / NM-PM (1-3 trades), longs.
Gap re-measure (Alpaca SIP, market-data GET only): gapV = 09:30 1-min bar VWAP (typical price if VWAP missing) vs the
prior regular-session close (SIP daily close of the previous session). ATR% = 14-session mean true range / prior close.
Configs (pre-declared before any result, 3 in total, same as gapdef_lab.py):
  A  keep if gapV <= min(own threshold, -1.0%)
  B  keep if gapV <= min(own threshold, -0.5 x ATR%)
  C  comparison arm: no entries before 12:00 ET (gap unchanged)
Trades: run 1, date >= 2026-10-23, R = pnl_adj / $ risk (journal costs = LR8 live basis); identical signals counted once
(same date, symbol, strategy, entry minute in two accounts -> first kept). Blocked entries (signals not submitted)
are counted for how many the rule would also have removed (no R).
Usage: python gapdef_live.py <scratch with <acct>/journal.db>.  Educational only - not financial advice."""
import re, sqlite3, sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.priors import _client
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
ACC = dict(p="Primary", od="On Deck", ta="Testing A", tb="Testing B", tc="Testing C", td="Testing D", te="Testing E",
           tf="Testing F", gen="Gen", gy="Graveyard")
FAM = re.compile(r"^(RW1-gapdn|RW3-gapdn|RW5-heat30-flowsell-rsi5pop-gapdn|RW7-gapdn|RW3S-gapdn|NM-MF3-qqqdn-gapdn|L3-gap-slope-)")


def own(s):
    if s.startswith("L3-gap-slope-fromopen-FD-WB4"): return -3.2
    if s.startswith("L3-"): return -2.6573517322540283
    if s.startswith("RW7-gapdn-bounce-early-short-FD-WB3"): return -0.5
    return 0.0


T, G = [], []
for a in ACC:
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where run_id=1 "
                    "and date>='2026-10-23' and side=-1", c); t["acct"] = a; T.append(t[t.strategy.str.match(FAM)])
    g = pd.read_sql("select day date, symbol, strategy, side, ts, status, reason from signals where run_id=1 and day>='2026-10-23' "
                    "and side=-1 and status!='submitted'", c); g["acct"] = a; G.append(g[g.strategy.str.match(FAM)])
T = pd.concat(T, ignore_index=True); G = pd.concat(G, ignore_index=True)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["em"] = T.et.dt.hour * 60 + T.et.dt.minute
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
n0 = len(T); T = T.drop_duplicates(["date", "symbol", "strategy", "em"]).reset_index(drop=True)
print(f"family trades {n0}, after identical-signal dedupe {len(T)}; blocked family signals {len(G)} "
      f"({G[['date', 'symbol']].drop_duplicates().shape[0]} symbol-days)")

# ---------------------------------------------------------------- Alpaca SIP: daily (prior close, ATR14) + 09:30 bar
dc = _client(); keys = pd.concat([T[["date", "symbol"]], G[["date", "symbol"]]]).drop_duplicates()
syms = sorted(keys.symbol.unique())
D = []
for i in range(0, len(syms), 200):
    x = dc.get_stock_bars(StockBarsRequest(symbol_or_symbols=syms[i:i + 200], timeframe=TimeFrame.Day, start=datetime(2026, 9, 20),
                                           end=datetime(2026, 11, 25), feed="sip", adjustment="raw")).df
    D.append(x)
D = pd.concat(D).reset_index(); D["date"] = D.timestamp.dt.tz_convert(TZ).dt.date.astype(str)
D = D.sort_values(["symbol", "date"])
D["pc"] = D.groupby("symbol").close.shift(1)
tr = np.maximum(D.high - D.low, np.maximum((D.high - D.pc).abs(), (D.low - D.pc).abs()))
D["atr14"] = tr.groupby(D.symbol).transform(lambda s: s.shift(1).rolling(14).mean())
M = []
for d, k in keys.groupby("date"):
    a0 = pd.Timestamp(f"{d} 09:30", tz=TZ); ss = sorted(k.symbol.unique())
    for i in range(0, len(ss), 400):
        x = dc.get_stock_bars(StockBarsRequest(symbol_or_symbols=ss[i:i + 400], timeframe=TimeFrame.Minute, start=a0.to_pydatetime(),
                                               end=(a0 + timedelta(minutes=1)).to_pydatetime(), feed="sip")).df
        if len(x):
            x = x.reset_index(); x = x[x.timestamp.dt.tz_convert(TZ) == a0]; x["date"] = d; M.append(x)
M = pd.concat(M)[["symbol", "date", "open", "high", "low", "close", "volume", "vwap"]].rename(
    columns={"open": "o930", "vwap": "vw930", "volume": "v930"})
M["vw930"] = M.vw930.where(M.vw930 > 0, (M.high + M.low + M.close) / 3)
K = keys.merge(D[["symbol", "date", "pc", "atr14"]], on=["symbol", "date"], how="left").merge(
    M[["symbol", "date", "o930", "vw930", "v930"]], on=["symbol", "date"], how="left")
K["gap_print"] = (K.o930 / K.pc - 1) * 100; K["gapV"] = (K.vw930 / K.pc - 1) * 100; K["atr_pct"] = K.atr14 / K.pc * 100
K.to_csv(HERE / "live_gaps.csv", index=False, float_format="%.4f")
T = T.merge(K, on=["date", "symbol"], how="left"); G = G.merge(K, on=["date", "symbol"], how="left")
for X in (T, G):
    X["own"] = X.strategy.map(own)
    X["is_own"] = np.where(X.strategy.str.startswith(("L3-", "RW7-gapdn-bounce-early-short-FD-WB3")), X.gapV <= X.own,
                           np.where(X.strategy.str.startswith("NM-MF3"), X.gapV <= 0, X.gapV < 0))
    X["miss"] = X.gapV.isna()
    X.loc[X.miss, "is_own"] = True
print(f"gap re-measured: trades {int((~T.miss).sum())}/{len(T)} (missing 09:30 bar or prior close: {int(T.miss.sum())}, kept as is)")
flip = T[~T.miss & ((T.gap_print < 0) != (T.gapV < 0))]
print(f"first print vs first-minute VWAP: sign differs on {len(flip)} trades ({flip[['date','symbol']].drop_duplicates().shape[0]} symbol-days), "
      f"|diff| > 1pp on {int(((T.gap_print - T.gapV).abs() > 1).sum())}; own rule fails on VWAP gap: {int((~T.is_own).sum())} trades, "
      f"{flip.R.sum() if len(flip) else 0:+.2f}R on sign flips")
print(T.loc[~T.is_own, ["date", "acct", "symbol", "strategy", "gap_print", "gapV", "R"]].round(2).to_string(index=False)[:3000])


def keepmask(X, cfg):
    if cfg == "A": return X.is_own & (X.miss | (X.gapV <= -1.0))
    if cfg == "B": return X.is_own & (X.miss | (X.gapV <= -0.5 * X.atr_pct))
    return X.em >= 720


if "ts" in G:
    gt = pd.to_datetime(G.ts, utc=True, format="mixed").dt.tz_convert(TZ); G["em"] = gt.dt.hour * 60 + gt.dt.minute
rows = []
for cfg in "ABC":
    k = keepmask(T, cfg)
    for s in sorted(T.strategy.unique()) + ["ALL"]:
        x = T if s == "ALL" else T[T.strategy == s]
        kk = k.loc[x.index]; rm = x[~kk]; kp = x[kk]
        d = {"cfg": cfg, "setup": s, "accts": ",".join(sorted(x.acct.unique())), "n": len(x), "kept": int(kk.sum()),
             "removed": len(rm), "rm_avgR": round(rm.R.mean(), 3) if len(rm) else None, "dR": round(-rm.R.sum(), 2),
             "avgR_before": round(x.R.mean(), 3), "avgR_after": round(kp.R.mean(), 3) if len(kp) else None}
        dd = (-rm.R).groupby(rm.date).sum()
        d["dR_wo_best_day"] = round(dd.sum() - dd.max(), 2) if len(dd) else 0.0
        d["dR_best_day"] = (f"{dd.idxmax()[5:]} {dd.max() / dd.sum():.0%}" if len(dd) and dd.sum() > 0 else "")
        for lab, z in (("before", x), ("after", kp)):
            if len(z):
                day = z.groupby("date").R.sum(); b = day.idxmax()
                d[f"wo_best_{lab}"] = round(z.loc[z.date != b, "R"].mean(), 3) if (z.date != b).any() else None
                d[f"best_share_{lab}"] = round(day.max() / day.sum(), 2) if day.sum() > 0 else None
        if s == "ALL":
            full = (-rm.R).groupby(rm.date).sum().reindex(sorted(T.date.unique()), fill_value=0.0)
            d["t_day"] = round(full.mean() / (full.std(ddof=1) / np.sqrt(len(full))), 2) if full.std() > 0 else None
            d["sessions_pos"] = f"{int((full > 0).sum())}/{int((full != 0).sum())}"
            gk = keepmask(G, cfg); d["blocked_also_removed"] = f"{int((~gk).sum())}/{len(G)}"
        rows.append(d)
R = pd.DataFrame(rows); R.to_csv(HERE / "live_results.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
for cfg in "ABC":
    x = R[(R.cfg == cfg)]
    print(f"\n== config {cfg}"); print(x.drop(columns=["cfg"]).to_string(index=False))
    y = x[(x.setup != "ALL") & (x.removed > 0)]
    print(f"{cfg}: setups improve {int((y.dR > 0).sum())} (+{y.loc[y.dR > 0, 'dR'].sum():.2f}R), worse {int((y.dR < 0).sum())} "
          f"({y.loc[y.dR < 0, 'dR'].sum():.2f}R), largest worsening {y.dR.min():+.2f}R")
    day = T[~keepmask(T, cfg)].groupby("date").R.sum()
    print(f"{cfg}: removed R by date: " + ", ".join(f"{d[5:]} {v:+.1f}" for d, v in day.items()))
    if cfg != "C":
        p = T[(T.acct == "p") & ~keepmask(T, cfg)]
        print(f"{cfg}: Primary removed {len(p)} tr, {p.R.sum():+.2f}R (dR {-p.R.sum():+.2f}); 11-24 Primary removed "
              f"{len(p[p.date == '2026-11-24'])} tr {p[p.date == '2026-11-24'].R.sum():+.2f}R")
print("Educational only - not financial advice.")
