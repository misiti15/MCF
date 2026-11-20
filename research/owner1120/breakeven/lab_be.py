"""Owner item 2 (2026-11-20) extensive breakeven grid - 2-year lab engine (PLAN.md frozen before this ran).
Walks every bt_lab1104 signal (the L16 set, geometries t1s1/t05s1/t1s05/t05s05) on cache_hist 1-minute bars with the
BEREPLAY conventions (bereplay.load_lists and its cost constants imported unchanged) and scores 216 whole-position
breakeven rules per trade = 6 triggers x 3 stop levels x 4 activations x 3 conditions (half-size = 0.5 x delta).
Aggregates per (setup, instrument type, date): n, BASE sum, delta sum and changed-trade count per rule.
Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent.
Usage: python lab_be.py OUT.parquet [procs] [max_symbols]. Educational only - not financial advice."""
import re, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/guild/1109/bereplay"))
import bereplay as BR  # noqa: E402
from bereplay import G  # noqa: E402
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/forward/compass_gate")
from shadow import INVERSE, LONG_VOL  # noqa: E402

TRIG = ["m0.3", "m0.5", "m0.75", "m1.0", "t50", "t80"]
LEVL = ["BE0", "BEC", "BES"]
ACT = ["D0", "D10", "D30", "SW"]
COND = ["ALL", "PM", "SPY"]
CFG = [f"{t}|{l}|{a}|{c}" for t in TRIG for l in LEVL for a in ACT for c in COND]   # shape (6,3,4,3) C-order
BIG = 10 ** 6
SPYTH = 0.001
SPY = {}
u = pd.read_csv(ROOT / "data/universe.csv")[["symbol", "name"]]; NAME = dict(zip(u.symbol, u.name))


def itype(sym):
    s = str(sym).upper()
    if s in INVERSE or s in LONG_VOL: return "invvol"
    nl = str(NAME.get(sym, "")).lower()
    etf = bool(re.search(r"\betf\b|trust|fund|shares|ishares|proshares|direxion|spdr|invesco|vaneck|graniteshares|tradr|defiance|"
                         r"leverage shares|t-rex|volatility", nl))
    return "etf" if etf else "stock"


def load_bars(sym):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < BR.TL0) | (pds.field(ix) >= BR.TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= BR.TL0) & (df.index < BR.TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    return df[keep], mm[keep]


def load_spy():
    df, mm = load_bars("SPY"); dd = df.index.date; c = df.close.to_numpy(float)
    for d in np.unique(dd):
        k = dd == d; a = np.full(385, np.nan); a[mm[k] - 570] = c[k]
        SPY[d] = pd.Series(a).ffill().bfill().to_numpy()


def trade(o, h, l, c, m_, e, s, D, u_, tier, ecost, spy, t0):
    n = len(c)
    if s > 0: fv, wv, ov, cv = (h - e) / D, (l - e) / D, (o - e) / D, (c - e) / D
    else: fv, wv, ov, cv = (e - l) / D, (e - h) / D, (e - o) / D, (e - c) / D
    i_s = BR.first(wv <= -1); i_t = BR.first(fv >= u_) if np.isfinite(u_) else BIG
    if i_s <= i_t and i_s < n: xu, kd = min(ov[i_s], -1.0), 1
    elif i_t < n: xu, kd = u_, 2
    else: xu, kd = cv[-1], 0
    px = e + s * xu * D
    xc = 0.0 if kd == 2 else BR.SL + px * BR.BP + (BR.SX if kd == 1 else 0.0)
    base = xu - tier * (ecost + xc) / D
    lim = min(i_s, i_t)
    cm = np.maximum.accumulate(fv)
    ks = np.array([.3, .5, .75, 1.0, .5 * u_, .8 * u_])
    tb = np.searchsorted(cm, ks, "left")                       # n if never
    tb = np.where(tb >= n, BIG, tb)
    # activations (6, 4)
    a0 = tb + 1; a10 = tb + 11; a30 = np.maximum(tb + 1, 30)
    if n >= 5:
        w = np.lib.stride_tricks.sliding_window_view(wv, 5).min(axis=1)       # window k-2..k+2 -> index k-2
        piv = np.flatnonzero(wv[2:n - 2] <= w) + 2
    else:
        piv = np.array([], int)
    if len(piv):
        p = np.searchsorted(piv, tb, "right")
        asw = np.where(p < len(piv), piv[np.minimum(p, len(piv) - 1)] + 3, BIG)
    else:
        asw = np.full(len(tb), BIG)
    A = np.stack([a0, a10, a30, asw], axis=1)                  # (6,4)
    A = np.where(tb[:, None] >= BIG, BIG, A)
    # conditions (3,)
    ipm = int(np.searchsorted(m_, 780, "left"))
    ref = spy[max(t0 - 1 - 570, 0)] if spy is not None else np.nan
    if spy is not None and ref == ref:
        rr = s * (spy[np.clip(m_ - 570, 0, 384)] / ref - 1)
        isp = BR.first(rr <= -SPYTH); isp = isp + 1 if isp < BIG else BIG
    else:
        isp = BIG
    Cn = np.array([0, ipm, isp])
    AA = np.maximum(A[:, :, None], Cn[None, None, :])          # (6,4,3)
    AA = np.minimum(AA, n)
    Lc = tier * (ecost + BR.SL + e * BR.BP + BR.SX) / D
    Ls = np.array([0.0, Lc, -0.25])
    ar = np.arange(n)
    out = np.empty((3,) + AA.shape)
    for li, L in enumerate(Ls):
        idx = np.where(wv <= L, ar, BIG)
        nh = np.r_[np.minimum.accumulate(idx[::-1])[::-1], BIG]
        out[li] = nh[AA]
    ibe = np.moveaxis(out, 0, 1).astype(np.int64)              # (6,3,4,3)
    hit = (ibe <= lim) & (ibe < n)
    Lb = Ls[None, :, None, None]
    xb = np.minimum(ov[np.minimum(ibe, n - 1)], Lb)
    pxb = e + s * xb * D
    vr = xb - tier * (ecost + BR.SL + pxb * BR.BP + BR.SX) / D
    d = np.where(hit, vr - base, 0.0).ravel()
    return base, d, (d != 0)


def sym_job(args):
    sym, tr = args
    r_ = load_bars(sym)
    if r_ is None: return None
    df, mm = r_; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    keys, bases, ds, chs = [], [], [], []
    for r in tr.itertuples(index=False):
        if r.date not in span or r.geom in ("hold", "holdtr"): continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        if j >= b: continue
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * R
        if not D > 0: continue
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (BR.SL + e * BR.BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        base, d, ch = trade(O[j:b], H[j:b], L[j:b], C[j:b], mm[j:b], e, int(r.side), D, up / dn, tier, ecost, SPY.get(r.date), t0)
        keys.append((r.setup, r.date)); bases.append(base); ds.append(d); chs.append(ch)
    if not keys: return None
    K = pd.DataFrame(keys, columns=["setup", "date"]); K["itype"] = itype(sym); K["n"] = 1; K["base"] = bases
    Dm = pd.DataFrame(np.array(ds, dtype=np.float64), columns=[f"d{i}" for i in range(len(CFG))])
    Cm = pd.DataFrame(np.array(chs, dtype=np.int32), columns=[f"c{i}" for i in range(len(CFG))])
    return pd.concat([K, Dm, Cm], axis=1).groupby(["setup", "itype", "date"], as_index=False).sum()


def main():
    OUT = sys.argv[1]; procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else None
    load_spy()
    t = BR.load_lists(None)
    t = t[~t.geom.isin(["hold", "holdtr"])]
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    if mx: jobs = jobs[:mx]
    acc, parts = None, []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, jobs, chunksize=2)):
            if res is not None: parts.append(res)
            if len(parts) >= 150 or (k == len(jobs) - 1 and parts):
                x = pd.concat(([acc] if acc is not None else []) + parts, ignore_index=True)
                acc = x.groupby(["setup", "itype", "date"], as_index=False).sum(); parts = []
            if k % 100 == 0: print(f"symbols {k}/{len(jobs)}", flush=True)
    if parts:
        x = pd.concat(([acc] if acc is not None else []) + parts, ignore_index=True)
        acc = x.groupby(["setup", "itype", "date"], as_index=False).sum()
    for c in acc.columns:
        if c.startswith("d") and c != "date": acc[c] = acc[c].astype("float32")
        if c.startswith("c"): acc[c] = acc[c].astype("int32")
    acc.to_parquet(OUT, index=False)
    print("rows", len(acc), "trades", int(acc.n.sum()), "base avg", acc.base.sum() / acc.n.sum())
    pd.Series(CFG).to_csv(Path(OUT).with_suffix(".cfg.csv"), index=False, header=False)


if __name__ == "__main__":
    main()
