"""Targets class, live (descriptive): replay each run-1 trade on 1-min SIP bars from the minute after entry to the
15:55 open, parent bracket vs C1..C6 (PLAN.md), paired. Live LR8 cost (gross journal R - R) is subtracted from both
arms; early exits pay extra (half spread + $0.01 + 1 bp) / risk per share exited.
Usage: python live_walk.py live_paths.parquet live_bars.parquet OUT.parquet. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
d = pd.read_parquet(sys.argv[1]); B = pd.read_parquet(sys.argv[2]); OUT = sys.argv[3]
M0, M1 = 570, 960; FL = 955 - M0
GR = {}
for (day, sym), g in B.groupby(["day", "symbol"]):
    a = np.full((4, M1 - M0), np.nan, dtype=np.float64); i = g.m.to_numpy() - M0; ok = (i >= 0) & (i < M1 - M0)
    for k, col in enumerate("ohlc"): a[k, i[ok]] = g[col].to_numpy()[ok]
    GR[(day, sym)] = a
VARS = ["P", "C1", "C2", "C3", "C4", "C5", "C6"]
def thr(px): return max(0.01, 3e-4 * px)
rows = []
for r in d.itertuples():
    a = GR.get((r.date, r.symbol)); rps = abs(r.entry - r.stop); s = int(np.sign(r.side))
    if a is None or not rps > 0 or r.m_in >= 955 or r.R != r.R: rows.append([r.id, r.account] + [np.nan] * 8); continue
    e = r.entry
    i0 = r.m_in - M0 + 1
    o, h, l, c = a[0, i0:FL], a[1, i0:FL], a[2, i0:FL], a[3, i0:FL]
    fo = a[0, FL] if a[0, FL] == a[0, FL] else pd.Series(a[3, :FL + 1]).ffill().iloc[-1]
    n = len(o)
    hit = np.nan_to_num((l <= r.stop) if s > 0 else (h >= r.stop), nan=0).astype(bool) if n else np.zeros(0, bool)
    fav = np.nan_to_num(((h - e) if s > 0 else (e - l)) / rps, nan=-9) if n else np.zeros(0)
    i_s = int(np.argmax(hit)) if hit.any() else 10 ** 9
    if i_s < n:
        oo = o[i_s] if o[i_s] == o[i_s] else r.stop
        stop_px = min(oo, r.stop) if s > 0 else max(oo, r.stop)
    gross_live = s * (r.exit - e) / rps; cost = gross_live - r.R
    xc = ((r.spread_bps if r.spread_bps == r.spread_bps else 5) / 2e4 * e + 0.01 + 1e-4 * e) / rps
    def g_at(px): return s * (px - e) / rps
    def lvl_idx(L):
        if not np.isfinite(L): return 10 ** 9
        px = e + s * L * rps; need = (fav * rps >= L * rps + thr(px))
        return int(np.argmax(need)) if need.any() else 10 ** 9
    def bracket(L, early):
        it = lvl_idx(L)
        if i_s <= it and i_s < n: return g_at(stop_px)
        if it < n: return L - (xc if early else 0.0)
        return g_at(fo)
    Tu = abs(r.target - e) / rps if r.target == r.target else np.inf
    gp = bracket(Tu, False); res = [gp]
    for Lp in (0.6, 0.8):
        ip = lvl_idx(Lp) if Lp < Tu else 10 ** 9
        res.append(0.5 * (Lp - xc) + 0.5 * gp if ip < min(i_s, n) else gp)
    for Lc in (1.0, 1.5):
        res.append(bracket(Lc, True) if (Lc < Tu and np.isfinite(Tu)) else gp)
    res.append(g_at(stop_px) if i_s < n else g_at(fo))
    hz = 120
    if i_s < min(hz, n): res.append(g_at(stop_px))
    elif n > hz:
        cc = c[hz - 1] if c[hz - 1] == c[hz - 1] else pd.Series(c[:hz]).ffill().iloc[-1]
        res.append(g_at(cc) - xc)
    else: res.append(g_at(fo))
    rows.append([r.id, r.account, Tu] + [x - cost for x in res])
X = pd.DataFrame(rows, columns=["id", "account", "TuF"] + VARS)
P = d[["id", "account", "strategy", "family", "side", "date", "R", "exit_reason", "tgtR"]].merge(X, on=["id", "account"])
P.to_parquet(OUT, index=False)
ok = P.P.notna()
print("trades", len(P), "replayed", ok.sum(), "calib |P-R|<=0.10:", ((P.P - P.R).abs() <= 0.10)[ok].mean().round(3), "mean P-R", (P.P - P.R)[ok].mean().round(3))
print((P.loc[ok, VARS].sub(P.loc[ok, "P"], axis=0)).mean().round(4).to_dict())
