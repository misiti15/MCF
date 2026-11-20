"""Giveback map, live part: minute paths of every live trade (all 10 accounts, run 1, LR8 R) and account-day MTM curves.
Usage: python live_paths.py live_trades.parquet live_bars.parquet OUTDIR. Educational only - not financial advice."""
import sys, re, numpy as np, pandas as pd
d = pd.read_parquet(sys.argv[1]); B = pd.read_parquet(sys.argv[2]); OUT = sys.argv[3]
CK = (5, 10, 15, 30, 45, 60, 90, 120); M0, M1 = 570, 960
u = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]; NAME = dict(zip(u.symbol, u.name))
def itype(sym):
    nl = str(NAME.get(sym, "")).lower()
    etf = bool(re.search(r"\betf\b|trust|fund|shares|ishares|proshares|direxion|spdr|invesco|vaneck|graniteshares|tradr|defiance|leverage shares|t-rex|volatility", nl))
    lev = bool(re.search(r"\b[23]x\b|ultra|leveraged|daily .*(bull|bear)|1\.5x|2x|3x", nl))
    if bool(re.search(r"bear|short|inverse|-1x|-2x|-3x", nl)) and etf: return "inverse ETF"
    if lev and etf: return "leveraged ETF"
    return "ETF" if etf else ("stock" if nl else "unknown")
# dense minute grids per (day, symbol): o,h,l,c with c forward-filled
G = {}
for (day, sym), g in B.groupby(["day", "symbol"]):
    a = np.full((4, M1 - M0), np.nan, dtype=np.float32); i = g.m.to_numpy() - M0; ok = (i >= 0) & (i < M1 - M0)
    for k, col in enumerate("ohlc"): a[k, i[ok]] = g[col].to_numpy()[ok]
    a[3] = pd.Series(a[3]).ffill().bfill().to_numpy(); G[(day, sym)] = a
d = d[d.exit_time.notna()].copy()
d["m_in"] = d.entry_time.dt.hour * 60 + d.entry_time.dt.minute
d["m_out"] = np.minimum(d.exit_time.dt.hour * 60 + d.exit_time.dt.minute, M1 - 1)
d["itype"] = d.symbol.map(itype)
rows = []
for r in d.itertuples():
    a = G.get((r.date, r.symbol)); spy = G.get((r.date, "SPY"))
    rps = abs(r.entry - r.stop); s = r.side
    rec = dict(id=r.id, account=r.account)
    if a is None or not rps > 0: rows.append(rec); continue
    i0, i1 = r.m_in - M0 + 1, r.m_out - M0          # bars strictly after the entry minute .. exit minute
    h, l, c = a[1, i0:i1 + 1], a[2, i0:i1 + 1], a[3, i0:i1 + 1]
    fav = ((h - r.entry) if s > 0 else (r.entry - l)) / rps; adv = ((r.entry - l) if s > 0 else (h - r.entry)) / rps
    fv = fav[:-1] if (r.exit_reason == "stop" and len(fav) > 1) else fav
    fv = np.nan_to_num(fv, nan=-9); av = np.nan_to_num(adv, nan=-9)
    xr = s * (r.exit - r.entry) / rps
    rec.update(mfe_b=float(max(fv.max() if len(fv) else -9, xr, 0)), mae_b=float(max(av.max() if len(av) else -9, -xr, 0)),
               tmfe=int(fv.argmax()) + 1 if len(fv) and fv.max() >= xr else int(len(fv)))
    if spy is not None:
        e0 = spy[3, max(r.m_in - M0, 0)]; e1 = spy[3, r.m_out - M0]
        rec.update(spy_tr=float(s * (e1 / e0 - 1) * 100), spy_oc=float((spy[3, -1] / spy[0, 0] - 1) * 100),
                   spy_pre=float((e0 / spy[0, 0] - 1) * 100))
    cost = (max(0.01, r.entry * 1e-4) + (r.spread_bps if r.spread_bps == r.spread_bps else 5) / 2e4 * r.entry + 0.01 + r.entry * 1e-4) / rps
    for t in CK:
        j = r.m_in - M0 + t
        if r.m_out - M0 > j and j < M1 - M0:
            mk = s * (a[3, j] - r.entry) / rps
            rec.update({f"mk{t}": float(mk), f"mf{t}": float(np.nanmax(fav[:t])) if t <= len(fav) else np.nan,
                        f"ma{t}": float(np.nanmax(adv[:t])) if t <= len(adv) else np.nan, f"rem{t}": float(r.R - (mk - cost))})
    rows.append(rec)
P = d.merge(pd.DataFrame(rows), on=["id", "account"], how="left")
P.drop(columns=["entry_time", "exit_time"]).assign(et=P.entry_time.astype(str), xt=P.exit_time.astype(str)).to_parquet(f"{OUT}/live_paths.parquet", index=False)
print("trades", len(P), "with path", P.mfe_b.notna().sum())
# account-day MTM curves
cur = []
for (acc, day), g in d.groupby(["account", "date"]):
    real = np.zeros(M1 - M0); unr = np.zeros(M1 - M0); late = np.zeros(M1 - M0); nl = np.zeros(M1 - M0); ns = np.zeros(M1 - M0)
    for r in g.itertuples():
        a = G.get((day, r.symbol)); rps = abs(r.entry - r.stop)
        i0, i1 = r.m_in - M0, r.m_out - M0
        real[i1:] += r.R
        if a is not None and rps > 0 and i1 > i0:
            unr[i0:i1] += r.side * (a[3, i0:i1] - r.entry) / rps
            (nl if r.side > 0 else ns)[i0:i1] += 1
    mtm = real + unr; ip = int(mtm.argmax()); it = int(mtm.argmin())
    after = g[g.m_in - M0 > ip]; at_peak = g[(g.m_in - M0 <= ip) & (g.m_out - M0 > ip)]
    spy = G.get((day, "SPY")); qqq = G.get((day, "QQQ"))
    netdir = np.sign(nl[ip] - ns[ip]) if (nl[ip] + ns[ip]) else 0
    cur.append(dict(account=acc, date=day, n=len(g), close=float(real[-1]), peak=float(mtm[ip]), peak_m=ip + M0, trough=float(mtm[it]),
                    trough_m=it + M0, real_at_peak=float(real[ip]), open_at_peak=len(at_peak), long_at_peak=int(nl[ip]), short_at_peak=int(ns[ip]),
                    openlots_R_close=float(at_peak.R.sum()), openlots_mark_peak=float(unr[ip]), late_n=len(after), late_R=float(after.R.sum()),
                    spy_peak_close=float((spy[3, -1] / spy[3, ip] - 1) * 100) if spy is not None else np.nan,
                    spy_oc=float((spy[3, -1] / spy[0, 0] - 1) * 100) if spy is not None else np.nan,
                    qqq_peak_close=float((qqq[3, -1] / qqq[3, ip] - 1) * 100) if qqq is not None else np.nan, netdir=netdir,
                    same_dir_share=float(max(nl[ip], ns[ip]) / (nl[ip] + ns[ip])) if (nl[ip] + ns[ip]) else np.nan,
                    top_setup_at_peak=at_peak.strategy.value_counts().index[0] if len(at_peak) else ""))
pd.DataFrame(cur).to_csv(f"{OUT}/account_days.csv", index=False); print("account-days", len(cur))
