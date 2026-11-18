"""U4 long-side program: five pre-registered long specs (research/usage/u4_longs/PLAN.md) on one session pack.
usage: python -I engine.py <day> [<day> ...]   (downloads the 1min/1day pack, scores, writes res/<day>.pkl, deletes the pack)
Educational only - not financial advice."""
import os, sys, pickle, subprocess, numpy as np, pandas as pd

S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u4"
LOCK = ("2024-11-01", "2025-02-28")
URL = "https://github.com/misiti15/MCF/releases/download/{tag}/{k}-{d}.parquet"
SEC, TAF = 27.8e-6, 0.000166
CAP = 15
NB = 78                                            # 5-min bars, j -> bar end T = 575 + 5 j
def J(hhmm):
    m = (hhmm // 100) * 60 + hhmm % 100
    return (m - 575) // 5
WIN = {"U4-ODC": (J(945), J(1030)), "U4-VWR": (J(1000), J(1430)), "U4-RSB": (J(1000), J(1500)),
       "U4-MPB": (J(1015), J(1130)), "U4-PMT": (J(1330), J(1330))}
RWIN = dict(WIN, **{"U4-PMT": (J(1030), J(1500))})   # random-bar control window (PMT has a single bar)
EXITS = {"E1": 1.5, "E2": None}


def tag(d):
    return f"bars-{d[:7]}" if d >= "2026-10-06" else f"bars2y-{d[:7]}"


def fetch(d):
    out = {}
    for k in ("1min", "1day"):
        p = f"{S}/packs/{k}-{d}.parquet"
        if not os.path.exists(p):
            subprocess.run(["curl", "-sSfL", "-o", p, URL.format(tag=tag(d), k=k, d=d)], check=True)
        out[k] = p
    return out


def priors(daily, d):
    x = daily.copy()
    x["date"] = x.ts.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    x = x[~x.date.between(*LOCK)]
    x = x[x.date < d].sort_values(["symbol", "date"])
    assert not x.date.between(*LOCK).any()
    g = x.groupby("symbol", sort=False)
    pc = g.close.shift(0)
    x["tr"] = np.maximum(x.high, g.close.shift(1).fillna(x.close)) - np.minimum(x.low, g.close.shift(1).fillna(x.close))
    rows = {}
    agg = g.agg(n=("close", "size"))
    last = g.tail(1).set_index("symbol")
    def tailmean(col, k):
        return g[col].apply(lambda s: s.iloc[-k:].mean())
    P = pd.DataFrame(index=agg.index)
    P["n"] = agg.n
    P["pc"] = last.close; P["pdh"] = last.high
    P["adv_sh"] = g.volume.apply(lambda s: s.iloc[-20:].mean())
    P["adv_d"] = (x.close * x.volume).groupby(x.symbol).apply(lambda s: s.iloc[-20:].mean())
    P["atr"] = g.tr.apply(lambda s: s.iloc[-14:].mean())
    P["sma20"] = g.close.apply(lambda s: s.iloc[-20:].mean())
    P["sma50"] = g.close.apply(lambda s: s.iloc[-50:].mean() if len(s) >= 50 else np.nan)
    P["h20"] = g.high.apply(lambda s: s.iloc[-20:].max())
    P["c20"] = g.close.apply(lambda s: s.iloc[-21] if len(s) >= 21 else np.nan)
    P["ret20"] = P.pc / P.c20 - 1
    return P


def build(m1, P, d):
    et = pd.DatetimeIndex(m1.ts.unique())
    mp = pd.Series(et.tz_convert("America/New_York").hour * 60 + et.tz_convert("America/New_York").minute, index=et)
    m1 = m1.assign(m=m1.ts.map(mp).values)
    m1 = m1[(m1.m >= 570) & (m1.m < 960)]
    uni = P[(P.pc >= 5) & (P.adv_d >= 20e6) & (P.n >= 15) & (P.atr > 0)].index
    keep = set(uni) | {"SPY"}
    m1 = m1[m1.symbol.isin(keep)].copy()
    m1["j"] = (m1.m - 570) // 5
    m1["pv"] = (m1.high + m1.low + m1.close) / 3 * m1.volume
    syms = sorted(set(m1.symbol))
    si = {s: i for i, s in enumerate(syms)}
    m1["si"] = m1.symbol.map(si)
    first = m1.groupby("si").m.min()
    op = m1.sort_values(["si", "m"]).groupby("si").open.first()
    b = m1.groupby(["si", "j"]).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"), v=("volume", "sum"), pv=("pv", "sum"))
    n = len(syms)
    A = {k: np.full((n, NB), np.nan) for k in ("h", "l", "c")}
    V = np.zeros((n, NB)); PV = np.zeros((n, NB))
    ii = b.index.get_level_values(0).values; jj = b.index.get_level_values(1).values
    for k in ("h", "l", "c"):
        A[k][ii, jj] = b[k].values
    V[ii, jj] = b.v.values; PV[ii, jj] = b.pv.values
    C = pd.DataFrame(A["c"]).ffill(axis=1).values
    H = np.where(np.isnan(A["h"]), C, A["h"]); L = np.where(np.isnan(A["l"]), C, A["l"])
    cv = np.cumsum(V, 1); cpv = np.cumsum(PV, 1)
    VW = np.where(cv > 0, cpv / np.maximum(cv, 1), C)
    HOD = np.fmax.accumulate(H, axis=1)
    O = np.full(n, np.nan); O[op.index.values] = op.values
    ok_open = np.zeros(n, bool); ok_open[first.index.values] = first.values <= 575
    # minute paths
    m1 = m1.sort_values(["si", "m"])
    paths = {}
    for s_i, g in m1.groupby("si"):
        paths[s_i] = (g.m.values, g.open.values, g.high.values, g.low.values, g.close.values)
    return dict(syms=syms, si=si, C=C, H=H, L=L, V=V, cv=cv, VW=VW, HOD=HOD, O=O, ok_open=ok_open, paths=paths)


def walk(path, T, atr, tgtR):
    """long entry at the open of the first minute >= T. Returns (R after costs, gross R, exit kind, exit minute) or None."""
    mn, o, h, l, c = path
    k0 = np.searchsorted(mn, T, side="left")
    if k0 >= len(mn) or mn[k0] >= 955 or mn[k0] > T + 5:
        return None
    e = o[k0] + max(0.01, 1e-4 * o[k0]) + 1e-4 * o[k0]
    R = 0.30 * atr
    stop = e - R
    tgt = e + tgtR * R if tgtR is not None else None
    px, kind, xm = None, None, None
    for k in range(k0, len(mn)):
        if mn[k] >= 955:
            px, kind, xm = o[k], "time", mn[k]; break
        if k > k0 or True:
            if l[k] <= stop:
                px, kind, xm = min(o[k], stop) if k > k0 else stop, "stop", mn[k]; break
            if tgt is not None and h[k] >= tgt + 0.01:
                px, kind, xm = tgt, "target", mn[k]; break
    if px is None:
        px, kind, xm = c[-1], "time", mn[-1]
    gross = px - e
    if kind == "stop":
        net = px - max(0.02, 4e-4 * px) - 0.01
    elif kind == "time":
        net = px - max(0.01, 1e-4 * px) - 0.01
    else:
        net = px
    net -= SEC * net + TAF
    return (net - e) / R, gross / R, kind, xm


def signals(D, P, spy_i):
    syms = D["syms"]; C, H, L, VW, HOD, cv, O = D["C"], D["H"], D["L"], D["VW"], D["HOD"], D["cv"], D["O"]
    n = len(syms)
    Pp = P.reindex(syms)
    pc = Pp.pc.values; atr = Pp.atr.values; adv = Pp.adv_sh.values
    frac = (5 * (np.arange(NB) + 1)) / 390.0
    rvol = cv / np.maximum(adv[:, None] * frac[None, :], 1)
    reto = C / O[:, None] - 1
    spyo = C[spy_i] / O[spy_i] - 1
    rs = reto - spyo[None, :]
    gap = O / pc - 1
    valid = D["ok_open"] & np.isfinite(O) & np.isfinite(atr) & (atr > 0)
    valid[spy_i] = False
    out = {}
    jj = np.arange(NB)
    def first_hit(M, spec):
        a, bnd = WIN[spec]
        W = np.zeros_like(M); W[:, a:bnd + 1] = True
        M = M & W & valid[:, None]
        hit = M.any(1)
        j = np.where(hit, M.argmax(1), -1)
        return [(i, j[i]) for i in np.where(hit)[0]]
    # U4-ODC
    orh = np.max(H[:, 0:3], 1)
    M = (gap[:, None] >= 0.02) & (gap[:, None] <= 0.15) & (C > orh[:, None]) & (C > VW) & (rs >= 0.005) & (rvol >= 2.0)
    out["U4-ODC"] = first_hit(M, "U4-ODC")
    # U4-VWR
    tr = (pc > Pp.sma20.values) & (Pp.sma20.values > Pp.sma50.values)
    prev_below = np.zeros_like(C, bool); prev_below[:, 1:] = C[:, :-1] < VW[:, :-1]
    M = (spyo[None, :] >= 0.002) & tr[:, None] & prev_below & (C > VW) & (rvol >= 1.0)
    out["U4-VWR"] = first_hit(M, "U4-VWR")
    # U4-RSB
    r20 = Pp.ret20.values
    q90 = np.nanquantile(r20[valid], 0.9)
    lead = (r20 >= q90) & (pc >= 0.95 * Pp.h20.values)
    lvl = np.fmax(Pp.pdh.values, Pp.h20.values)
    M = lead[:, None] & (spyo[None, :] >= 0) & (C > lvl[:, None]) & (C > VW) & (rs > 0) & (rvol >= 1.5)
    out["U4-RSB"] = first_hit(M, "U4-RSB")
    # U4-MPB
    j10 = J(1000)
    strong = (reto[:, j10] >= 0.015) & (rs[:, j10] >= 0.01) & (rvol[:, j10] >= 2.0)
    M = np.zeros_like(C, bool)
    hod = H[:, 0].copy(); lows = np.full(n, np.inf)
    for j in range(1, NB):
        pb = np.minimum(lows, L[:, j])
        cond = (pb <= hod - 0.4 * (hod - O)) & (pb >= VW[:, j] - 0.1 * atr) & (C[:, j] > H[:, j - 1]) & (C[:, j] > VW[:, j]) & np.isfinite(lows)
        M[:, j] = cond & strong
        newh = H[:, j] > hod
        lows = np.where(newh, np.inf, np.minimum(lows, L[:, j]))
        hod = np.maximum(hod, H[:, j])
    out["U4-MPB"] = first_hit(M, "U4-MPB")
    # U4-PMT
    j1 = J(1330); a = J(1030)
    above = np.all(C[:, a:j1 + 1] > VW[:, a:j1 + 1], 1)
    M = np.zeros_like(C, bool)
    M[:, j1] = (reto[:, j1] >= 0.02) & (C[:, j1] >= HOD[:, j1] - 0.25 * atr) & above & (rvol[:, j1] >= 1.2)
    out["U4-PMT"] = first_hit(M, "U4-PMT")
    return out, dict(rvol=rvol, valid=valid, atr=atr)


def run_day(d):
    f = fetch(d)
    daily = pd.read_parquet(f["1day"])
    P = priors(daily, d)
    m1 = pd.read_parquet(f["1min"], columns=["symbol", "ts", "open", "high", "low", "close", "volume"])
    m1["symbol"] = m1.symbol.astype(str)
    D = build(m1, P, d)
    del m1
    if "SPY" not in D["si"]:
        return None
    spy_i = D["si"]["SPY"]
    sp = D["paths"][spy_i]
    spy = dict(date=d, spy_pc=P.pc.get("SPY"), spy_o=D["O"][spy_i], spy_c=sp[4][-1], n_uni=len(D["syms"]) - 1)
    sig, X = signals(D, P, spy_i)
    rng = np.random.default_rng(int(d.replace("-", "")))
    rows = []
    vidx = np.where(X["valid"])[0]
    for spec, hits in sig.items():
        hits = sorted(hits, key=lambda t: (t[1], -X["rvol"][t[0], t[1]]))[:CAP]
        for i, j in hits:
            T = 575 + 5 * j
            for ex, tg in EXITS.items():
                w = walk(D["paths"][i], T, X["atr"][i], tg)
                if w is None:
                    continue
                r = dict(date=d, spec=spec, exit=ex, symbol=D["syms"][i], T=T, R=w[0], gross=w[1], kind=w[2], xm=w[3],
                         rvol=X["rvol"][i, j])
                ra, rb = [], []
                for s in range(5):
                    k = vidx[rng.integers(len(vidx))]
                    while k == i:
                        k = vidx[rng.integers(len(vidx))]
                    wa = walk(D["paths"][k], T, X["atr"][k], tg); ra.append(wa[0] if wa else np.nan)
                    a, bnd = RWIN[spec]; jr = rng.integers(a, bnd + 1)
                    wb = walk(D["paths"][i], 575 + 5 * jr, X["atr"][i], tg); rb.append(wb[0] if wb else np.nan)
                r["rnd_time"] = np.nanmean(ra) if np.isfinite(ra).any() else np.nan
                r["rnd_bar"] = np.nanmean(rb) if np.isfinite(rb).any() else np.nan
                rows.append(r)
    res = dict(day=spy, trades=pd.DataFrame(rows), nsig={k: len(v) for k, v in sig.items()})
    os.makedirs(f"{S}/res", exist_ok=True)
    pickle.dump(res, open(f"{S}/res/{d}.pkl", "wb"))
    for p in f.values():
        os.remove(p)
    return res


if __name__ == "__main__":
    for d in sys.argv[1:]:
        if os.path.exists(f"{S}/res/{d}.pkl"):
            continue
        try:
            r = run_day(d)
            print(d, None if r is None else (len(r["trades"]), r["nsig"]), flush=True)
        except subprocess.CalledProcessError:
            print(d, "no pack", flush=True)
