import sys, re, sqlite3, json, numpy as np, pandas as pd
W = sys.argv[1]
ET = "America/New_York"
u = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]
NAME = dict(zip(u.symbol, u.name))

def itype(sym):
    n = str(NAME.get(sym, ""))
    nl = n.lower()
    etf = bool(re.search(r"\betf\b|trust|fund|shares|ishares|proshares|direxion|spdr|invesco|vaneck|graniteshares|tradr|defiance|leverage shares|t-rex|volatility", nl))
    lev = bool(re.search(r"\b[23]x\b|ultra|leveraged|daily .*(bull|bear)|1\.5x|2x|3x", nl))
    inv = bool(re.search(r"bear|short|inverse|-1x|-2x|-3x", nl)) and etf
    if inv: return "inverse ETF"
    if lev and etf: return "leveraged ETF"
    if etf: return "ETF"
    return "stock" if n else "unknown"

recent = pd.read_parquet(f"{W}/bars_recent.parquet")
recent["t"] = pd.to_datetime(recent.t, utc=True).dt.tz_convert(ET)
RB = {k: g.set_index("t")[["o", "h", "l", "c", "v"]].rename(columns=dict(o="open", h="high", l="low", c="close", v="volume"))
      for k, g in recent.groupby(["day", "symbol"])}
_hc = {}
def bars(sym, day):
    if (day, sym) in RB: return RB[(day, sym)]
    if sym not in _hc:
        try: _hc[sym] = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")
        except Exception: _hc[sym] = None
    h = _hc[sym]
    if h is None: return None
    if day >= "2024-11-01" and day <= "2025-02-28": return None   # locked block never read
    b = h.loc[day] if day in h.index.strftime("%Y-%m-%d") else None
    if b is None or len(b) == 0: return None
    return b

def load(db, acct):
    c = sqlite3.connect(db)
    d = pd.read_sql("select * from trades where run_id=1", c)
    s = pd.read_sql("select ts,symbol,strategy,ref_price,broker_order_id,info from signals where run_id=1 and status='submitted'", c)
    d["acct"] = acct
    return d, s

rows = []
SETS = [("journal.db", "Primary"), ("j_testing.db", "Testing1")]
for db, acct in SETS:
    d, s = load(f"{W}/{db}", acct)
    d = d[d.strategy.isin(["ST7-rsi50dn-long-pm-t1s1-FD", "L3-gap-slope-fromopen-FD"]) |
          ((d.strategy == "RW3-gapdn-rsi5pop-flowsell-short-FD") & (d.date == "2026-11-19") & (acct == "Primary"))]
    s["coid"] = s["info"].str.extract(r'"coid": "([^"]+)"')
    d["coid"] = d["meta"].str.extract(r'"coid": "([^"]+)"')
    d = d.merge(s[["coid", "ref_price", "ts"]].drop_duplicates("coid"), on="coid", how="left")
    rows.append(d)
D = pd.concat(rows, ignore_index=True)
D["risk"] = (D.entry - D.stop).abs()
D["R"] = D.pnl_adj / (D.risk * D.shares)
D["itype"] = D.symbol.map(itype)
out = []
for i, t in D.iterrows():
    sd = 1 if t.side > 0 else -1
    et = pd.to_datetime(t.entry_time, utc=True, format="mixed").tz_convert(ET)
    xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").tz_convert(ET) if t.exit_time else None
    st = pd.to_datetime(t.signal_time, utc=True, format="mixed").tz_convert(ET)
    r = dict(idx=i, acct=t.acct, date=t.date, symbol=t.symbol, strategy=t.strategy, itype=t["itype"], side=sd, R=t.R,
             entry=t.entry, stop=t.stop, target=t.target, exit=t.exit, reason=t.exit_reason, ref=t.ref_price,
             entry_et=et.strftime("%H:%M:%S"), exit_et=xt.strftime("%H:%M:%S") if xt is not None else None,
             sig_to_fill_s=(et - st).total_seconds(), risk=t.risk, risk_pct=t.risk / t.entry * 100, mfe_r=t.mfe_r, mae_r=t.mae_r)
    if pd.notna(t.ref_price):
        r["ent_slip_R"] = sd * (t.entry - t.ref_price) / t.risk
        r["ent_slip_bps"] = sd * (t.entry - t.ref_price) / t.ref_price * 1e4
        r["risk_from_ref"] = abs(t.ref_price - t.stop)
    if t.exit_reason == "stop":
        r["exit_slip_R"] = sd * (t.exit - t.stop) / t.risk
    elif t.exit_reason == "target":
        r["exit_slip_R"] = sd * (t.exit - t.target) / t.risk
    b = bars(t.symbol, t.date)
    if b is not None and len(b):
        b = b.sort_index()
        tr = pd.concat([b.high - b.low, (b.high - b.close.shift()).abs(), (b.low - b.close.shift()).abs()], axis=1).max(axis=1)
        em = et.floor("min")
        pre = tr[tr.index < em]
        r["atr1"] = pre.tail(14).mean() if len(pre) >= 5 else np.nan
        b15 = b[b.index < em].resample("15min").agg(dict(open="first", high="max", low="min", close="last")).dropna()
        if len(b15) >= 2:
            tr15 = pd.concat([b15.high - b15.low, (b15.high - b15.close.shift()).abs(), (b15.low - b15.close.shift()).abs()], axis=1).max(axis=1)
            r["atr15"] = tr15.tail(6).mean()
        r["stop_atr1"] = t.risk / r["atr1"] if r.get("atr1") else np.nan
        r["stop_atr15"] = t.risk / r["atr15"] if r.get("atr15") else np.nan
        post = b[b.index >= em]
        post = post[post.index <= post.index[0].normalize() + pd.Timedelta(hours=15, minutes=55)]
        if len(post):
            hit = (post.low <= t.stop) if sd > 0 else (post.high >= t.stop)
            if hit.any():
                hb = post[hit].iloc[0]; ht = post[hit].index[0]
                r["touch_et"] = ht.strftime("%H:%M")
                r["mins_to_stop"] = (ht - em).total_seconds() / 60
                r["gap_through"] = bool((hb.open <= t.stop) if sd > 0 else (hb.open >= t.stop))
                r["close_through"] = bool((hb.close <= t.stop) if sd > 0 else (hb.close >= t.stop))
                # did the 5-min bar containing the touch close beyond the stop?
                b5 = b.resample("5min").agg(dict(open="first", high="max", low="min", close="last")).dropna()
                k5 = b5[b5.index <= ht].iloc[-1]
                r["close5_through"] = bool((k5.close <= t.stop) if sd > 0 else (k5.close >= t.stop))
                aft = post[post.index > ht]
                if len(aft):
                    fav = aft.high.max() if sd > 0 else aft.low.min()
                    adv = aft.low.min() if sd > 0 else aft.high.max()
                    r["post_target"] = bool((fav >= t.target) if sd > 0 else (fav <= t.target))
                    r["post_mfe_R"] = sd * (fav - t.entry) / t.risk
                    r["post_mae_R"] = sd * (adv - t.entry) / t.risk
                    r["close1555_R"] = sd * (aft.close.iloc[-1] - t.entry) / t.risk
                    # wider-stop counterfactual (same target, same $ risk -> R in units of the wider risk)
                for k in (1.5, 2.0):
                    ws = t.entry - sd * k * t.risk
                    wh = (post.low <= ws) if sd > 0 else (post.high >= ws)
                    th = (post.high >= t.target) if sd > 0 else (post.low <= t.target)
                    ti = post.index[th.values][0] if th.any() else None
                    wi = post.index[wh.values][0] if wh.any() else None
                    if ti is not None and (wi is None or ti < wi):
                        rr = sd * (t.target - t.entry) / (k * t.risk)
                    elif wi is not None:
                        rr = -1.0
                    else:
                        rr = sd * (post.close.iloc[-1] - t.entry) / (k * t.risk)
                    r[f"k{k}_R_gross"] = rr
            else:
                r["touch_et"] = None
            # hold-to-close R for all trades
            r["hold_close_R"] = sd * (post.close.iloc[-1] - t.entry) / t.risk
            r["target_ever"] = bool(((post.high >= t.target) if sd > 0 else (post.low <= t.target)).any())
    out.append(r)
A = pd.DataFrame(out)
A.to_csv(f"{W}/audit_trades.csv", index=False)
print(len(A), A.atr1.notna().sum())
