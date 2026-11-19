"""movehunt_short (ultimate_1119): point-in-time short-fade precursors on the 2-year 1-minute cache, FIT HALF ONLY.

Fit half = 2024-10-01..2024-10-31 and 2025-03-01..2025-09-30. The locked block (2024-11-01..2025-02-28) and the check
half (>= 2025-10-01) are dropped on read and never scored. Signals at every 5-minute bar close 09:50..15:15 ET.
Every feature uses only 1-minute bars that closed before the signal time (prior-day daily ATR / ADV, session so far).

Outcome (short, LR8 live cost model as research/workbench/CWT14.../code/sim.py, adapted to a short):
  fill = open of the 1-minute bar starting 1 minute after the signal close; levels from the signal close c:
  R0 = 0.25 x daily ATR(14, prior days); stop = c + 1*R0; target = c - tk*R0; same-minute stop+target -> stop first;
  time exit at the open of minute (entry + cap) or 15:55, whichever first. R = net P/L / |fill - stop|.
  costs  entry (sale) (1c + 1bp) x TOD mult + 1bp LR8 cushion + SEC 20.60/M + CAT; target exit 0 (+TAF/CAT);
         stop exit (1c + 1bp) + max(2c, 4bp); time exit (1c + 1bp) + max(1c, 1bp). No borrow fee (intraday).
Geometries: g1 = t1 s1 cap45 (primary), g2 = t1.5 s1 cap45, g3 = t1 s1 cap30, g4 = t0.5 s1 cap45.
Swing label (no stop): sw = low of minutes [entry, entry+45) <= c - 1*R0 (the move-hunt "rolls over >= 1R").
Educational only - not financial advice.
"""
import sys, os, numpy as np, pandas as pd
from multiprocessing import Pool

CACHE = "/home/user/MCF/data/cache_hist/1Min"
TMP = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_tmp"
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))
GEOMS = {"g1": (1.0, 45), "g2": (1.5, 45), "g3": (1.0, 30), "g4": (0.5, 45)}
SIG_T = [t for t in range(950, 1516, 5) if t % 100 < 60]


def fit_day(d):
    s = str(d)
    return ("2024-10-01" <= s <= "2024-10-31") or ("2025-03-01" <= s <= "2025-09-30")


def todmult(t):
    for edge, m in TOD_COST:
        if t < edge:
            return m
    return 1.0


def m2i(t):  # HHMM -> minute index from 09:30
    return (t // 100) * 60 + t % 100 - 570


def rsi_wilder(x, n=5):
    d = np.diff(x, prepend=x[0])
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    a = 1.0 / n
    au = pd.Series(up).ewm(alpha=a, adjust=False).mean().to_numpy()
    ad = pd.Series(dn).ewm(alpha=a, adjust=False).mean().to_numpy()
    return 100 - 100 / (1 + au / np.where(ad == 0, 1e-12, ad))



def outcomes(o, h, l, c, R0):
    """Vectorised over the signal times of one session: {T: {g: (r, win)}}."""
    Ts = np.array(SIG_T); k = np.array([m2i(t) - 1 for t in SIG_T]); e = k + 2
    ct = c[k]; f = o[e]; stop = ct + R0
    risk = stop - f
    ce = (0.01 + f * 1e-4) * np.array([todmult(t) for t in SIG_T]) + f * 1e-4 + FEE_SEC * f + CAT
    out = {t: {} for t in SIG_T}
    lastc = m2i(1555)
    for gname, (tk, cap) in GEOMS.items():
        tgt = ct - tk * R0
        endi = np.minimum(e + cap, lastc)
        idx = e[:, None] + np.arange(cap)[None, :]
        valid = idx < endi[:, None]
        idc = np.minimum(idx, 389)
        hs = (h[idc] >= stop[:, None]) & valid
        ht = (l[idc] <= tgt[:, None]) & valid
        big = cap + 1
        fs = np.where(hs.any(1), np.argmax(hs, 1), big)
        ft = np.where(ht.any(1), np.argmax(ht, 1), big)
        won = ft < fs
        lost = (fs <= ft) & (fs < big)
        js = np.minimum(e + np.where(fs < big, fs, 0), 389)
        xp = np.where(won, tgt, np.where(lost, np.maximum(stop, o[js]), o[np.minimum(endi, 389)]))
        base = 0.01 + xp * 1e-4
        cx = np.where(won, TAF + CAT, np.where(lost, base + np.maximum(0.02, 4e-4 * xp), base + np.maximum(0.01, 1e-4 * xp)) + TAF + CAT)
        r = (f - xp - ce - cx) / np.where(risk > 0, risk, 1)
        r = np.where(risk > 0, r, -1.0 - ce / R0)
        won = np.where(risk > 0, won, False)
        for i, t in enumerate(SIG_T):
            out[t][gname] = (float(r[i]), int(won[i]))
    return out


SPY = None


def load_grid(sym):
    df = pd.read_parquet(f"{CACHE}/{sym}.parquet")
    if df.empty:
        return None
    df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
    s = df.index.date.astype(str) if hasattr(df.index.date, "astype") else np.array([str(x) for x in df.index.date])
    s = np.array([str(x) for x in df.index.date])
    keep = ~((s >= "2024-11-01") & (s <= "2025-02-28")) & (s < "2025-10-01")   # locked + check half never read
    df = df[keep]
    return df


def spy_table():
    df = load_grid("SPY")
    out = {}
    for d, g in df.groupby(df.index.date):
        mi = (g.index.hour * 60 + g.index.minute - 570).to_numpy()
        c = np.full(390, np.nan); c[mi] = g.close.to_numpy()
        c = pd.Series(c).ffill().bfill().to_numpy()
        out[d] = c
    return out


def init():
    global SPY
    SPY = spy_table()


def one(sym):
    try:
        return _one(sym)
    except Exception as e:  # noqa
        print("ERR", sym, e, flush=True)
        return sym, 0


def _one(sym):
    df = load_grid(sym)
    if df is None or len(df) < 1000:
        return sym, 0
    days = sorted(set(df.index.date))
    # daily table (all available non-locked, non-check days: prior-day stats only)
    g = df.groupby(df.index.date)
    dl = pd.DataFrame({"h": g.high.max(), "l": g.low.min(), "c": g.close.last(), "dv": (df.close * df.volume).groupby(df.index.date).sum()})
    pc = dl.c.shift(1)
    tr = np.maximum(dl.h - dl.l, np.maximum((dl.h - pc).abs(), (dl.l - pc).abs()))
    dl["atr"] = tr.shift(1).rolling(14, min_periods=10).mean()
    dl["adv20"] = dl.dv.shift(1).rolling(20, min_periods=5).mean()
    dl["pc"] = pc
    # note: the locked gap (Nov-Feb) means the first March days use October daily bars as "prior": we drop the first
    # 10 March sessions' ATR/ADV by requiring the prior row to be within 7 calendar days.
    prevd = pd.Series(dl.index, index=dl.index).shift(1)
    gapdays = (pd.to_datetime(pd.Series(dl.index, index=dl.index)) - pd.to_datetime(prevd)).dt.days
    # 5-minute closes for RSI5 (continuous over sessions)
    rows = []
    bars = {}
    for d, gg in g:
        mi = (gg.index.hour * 60 + gg.index.minute - 570).to_numpy()
        o = np.full(390, np.nan); h = o.copy(); l = o.copy(); c = o.copy(); v = np.zeros(390)
        o[mi], h[mi], l[mi], c[mi], v[mi] = gg.open, gg.high, gg.low, gg.close, gg.volume
        c = pd.Series(c).ffill().to_numpy()
        if np.isnan(c[0]):
            c = pd.Series(c).bfill().to_numpy()
        o = np.where(np.isnan(o), c, o); h = np.where(np.isnan(h), c, h); l = np.where(np.isnan(l), c, l)
        bars[d] = (o, h, l, c, v)
    c5_all, key5 = [], []
    for d in days:
        c = bars[d][3]
        for j in range(4, 390, 5):
            c5_all.append(c[j]); key5.append((d, j))
    rsi5 = rsi_wilder(np.array(c5_all), 5)
    rsi_map = {k: r for k, r in zip(key5, rsi5)}
    # prior-day count in run (for adjacency with locked gap)
    for d in days:
        if not fit_day(d):
            continue
        atr, adv, pcl = dl.at[d, "atr"], dl.at[d, "adv20"], dl.at[d, "pc"]
        if not (np.isfinite(atr) and atr > 0 and np.isfinite(adv) and np.isfinite(pcl)):
            continue
        if gapdays.get(d, 99) > 7 and str(d) >= "2025-03-01" and str(d) <= "2025-03-20":
            continue
        o, h, l, c, v = bars[d]
        if c[0] < 5 or adv < 10e6:
            continue
        spy = SPY.get(d)
        if spy is None:
            continue
        R0 = 0.25 * atr
        tp = (h + l + c) / 3
        cv = np.cumsum(v); cpv = np.cumsum(tp * v); cpv2 = np.cumsum(tp * tp * v)
        vw = cpv / np.where(cv == 0, np.nan, cv)
        vsd = np.sqrt(np.clip(cpv2 / np.where(cv == 0, np.nan, cv) - vw ** 2, 0, None))
        hod = np.maximum.accumulate(h); lod = np.minimum.accumulate(l)
        dopen = o[0]
        OUT = outcomes(o, h, l, c, R0)
        for T in SIG_T:
            k = m2i(T) - 1          # last completed minute
            e = k + 2               # entry minute (bar starting T+1)
            ct = c[k]
            if not np.isfinite(ct) or ct <= 0:
                continue
            hk = h[: k + 1]
            ih = k - int(np.argmax(hk[::-1]))   # last occurrence of HOD
            vv = v[: k + 1]
            med = np.median(vv[vv > 0]) if (vv > 0).any() else 0
            w0 = max(0, k - 29)
            jmax = w0 + int(np.argmax(v[w0: k + 1]))
            blow = (med > 0) and (v[jmax] >= 4 * med) and (hod[k] - h[jmax] <= 0.1 * atr) and (h[max(0, k - 4): k + 1].max() < hod[k]) and (jmax < k - 1)
            ret15 = (ct - c[max(0, k - 15)]) / atr
            ret5 = (ct - c[max(0, k - 5)]) / atr
            rv15 = v[max(0, k - 14): k + 1].sum() / max(cv[k] / (k + 1) * 15, 1e-9)
            spy950 = (spy[k] / spy[m2i(950) - 1] - 1) * 100
            spy30 = (spy[k] / spy[max(0, k - 30)] - 1) * 100
            spyfo = (spy[k] / spy[0] - 1) * 100
            res = OUT[T]
            sw_end = min(e + 45, m2i(1555))
            sw = int(l[e:sw_end].min() <= ct - R0) if sw_end > e else 0
            mfe = (ct - l[e:sw_end].min()) / R0 if sw_end > e else 0.0
            mae = (h[e:sw_end].max() - ct) / R0 if sw_end > e else 0.0
            rows.append((d, sym, T, ct, atr / ct * 100, adv / 1e6, (dopen / pcl - 1) * 100, (ct - dopen) / atr, (ct - lod[k]) / atr,
                         (hod[k] - ct) / atr, k - ih, (ct - vw[k]) / vsd[k] if vsd[k] > 0 else np.nan, rsi_map.get((d, (k // 5) * 5 + 4), np.nan) if (k % 5 == 4) else np.nan,
                         rv15, int(blow), ret15, ret5, spy950, spy30, spyfo, R0 / ct * 100,
                         res["g1"][0], res["g1"][1], res["g2"][0], res["g3"][0], res["g4"][0], sw, mfe, mae))
    if not rows:
        return sym, 0
    cols = ["date", "sym", "tod", "px", "atrpct", "adv_m", "gap", "ro_atr", "rl_atr", "dh_atr", "min_hod", "vwz", "rsi5",
            "rv15", "blow", "ret15", "ret5", "spy950", "spy30", "spyfo", "r0pct", "g1", "w1", "g2", "g3", "g4", "sw", "mfe", "mae"]
    x = pd.DataFrame(rows, columns=cols)
    for cc in cols[3:]:
        x[cc] = x[cc].astype("float32")
    x["date"] = x["date"].astype(str)
    x.to_parquet(f"{TMP}/{sym}.parquet", index=False)
    return sym, len(x)


if __name__ == "__main__":
    syms = sorted(f[:-8] for f in os.listdir(CACHE) if f.endswith(".parquet"))
    if len(sys.argv) > 1:
        syms = sys.argv[1:]
    with Pool(4, initializer=init) as p:
        n = 0
        for i, (s, k) in enumerate(p.imap_unordered(one, syms, chunksize=4)):
            n += k
            if i % 100 == 0:
                print(i, s, k, n, flush=True)
    print("done", n)
