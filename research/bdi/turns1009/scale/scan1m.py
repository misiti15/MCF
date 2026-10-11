"""Stage C (NOTES amendment A1): T1 confluence signatures S1-S5 on 1-minute bars, fixed-1R and trail-after-1R exits,
'all' (15-min refractory, one open trade per symbol-side) and 'first' per symbol-day, raw and SPY-hedged.
    python scan1m.py [limit]   -> data/trades1m.parquet
Educational only - not financial advice."""
import sys
import time

import numpy as np
import pandas as pd

from common import (DATA, ETFS, MIN_ADV, NB, ROOT, conditions, fill, lib, market_features, open_dates, rsi_simple,
                    symbols)
from mcf.data.store import BarStore
from mcf.research.gates import prod_r, tod_cost_mult

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None
NM = 390
MIN_CLOSE = np.arange(NM) + 571                         # bar close minute of day
TOD1 = (MIN_CLOSE // 60) * 100 + MIN_CLOSE % 60
W0, W1 = int(np.flatnonzero(TOD1 == 950)[0]), int(np.flatnonzero(TOD1 == 1500)[0])
XI = int(np.flatnonzero(TOD1 == 1555)[0])               # timed exit bar
SECTOR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS".split()
syms, dates = symbols(), open_dates()
si = {s: i for i, s in enumerate(syms)}
D = len(dates)
dates64 = np.array([np.datetime64(str(x)) for x in dates], dtype="datetime64[us]")
aux = dict(np.load(DATA / "aux.npz"))
secmap = np.load(ROOT / "research/swarm1010/w2_neutral/data/betas.npz")["sec"]
ctxz = dict(np.load(DATA / "context.npz"))
store = BarStore(ROOT / "data" / "cache_hist")
lo64, hi64 = np.datetime64(lib.LOCKED[0], "us"), np.datetime64(lib.LOCKED[1], "us")


def load1(sym):
    df = store.load(sym)
    if df.empty:
        return None
    day = df.index.tz_localize(None).normalize().to_numpy()
    df = df[~((day >= lo64) & (day <= hi64))]                        # locked block dropped first
    day = df.index.tz_localize(None).normalize().to_numpy()
    keep = np.isin(day, dates64)
    df, day = df[keep], day[keep]
    m = np.asarray(df.index.hour * 60 + df.index.minute) - 570
    ok = (m >= 0) & (m < NM)
    df, day, m = df[ok], day[ok], m[ok]
    dd = np.searchsorted(dates64, day)
    out = {}
    for k, col in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"), ("V", "volume")):
        a = np.full((D, NM), np.nan, np.float64)
        a[dd, m] = df[col].to_numpy(np.float64)
        out[k] = a
    pres = np.isfinite(out["C"])
    c = pd.Series(out["C"].ravel()).ffill().to_numpy().reshape(D, NM)
    out["C"] = c
    for k in ("O", "H", "L"):
        out[k] = np.where(pres, out[k], c)
    out["V"] = np.where(pres, out["V"], 0)
    out["present"] = pres
    return out


def to5(b):
    """5-minute bars from the 1-minute dense arrays (same as resample: bar b = minutes 5b..5b+4)."""
    r = lambda a: a[:, :NB * 5].reshape(D, NB, 5)
    pres = r(b["present"]).any(2)
    o = {"O": r(b["O"])[:, :, 0], "H": r(b["H"]).max(2), "L": r(b["L"]).min(2), "C": r(b["C"])[:, :, 4],
         "V": r(b["V"]).sum(2)}
    raw = {k: np.where(pres, v, np.nan).astype(np.float32) for k, v in o.items()}
    return fill(raw)


def last5(x5):
    """Value of the last completed 5-minute bar at each 1-minute bar close (NaN before the first)."""
    idx = np.minimum((np.arange(NM) - 4) // 5, NB - 1)
    out = np.full((x5.shape[0], NM), np.nan)
    ok = idx >= 0
    out[:, ok] = x5[:, idx[ok]]
    return out


def prior_q(X, q, ndays=20, mind=10):
    """Per session: quantile q of X over the previous ndays sessions (rows), NaN when < mind sessions with data."""
    out = np.full(D, np.nan)
    has = np.isfinite(X).any(1)
    for d in range(D):
        lo = max(0, d - ndays)
        if has[lo:d].sum() < mind:
            continue
        v = X[lo:d][np.isfinite(X[lo:d])]
        if len(v):
            out[d] = np.quantile(v, q)
    return out


def back_any(x, n):
    """True if x was true on any of the last n bars (incl. this one), within the session."""
    y = x.copy()
    for k in range(1, n):
        y[:, k:] |= x[:, :-k]
    return y


def confirmed_swings(b):
    """Causal 30-min swing confirmation (A1 S4), any in the last 6 bars. Returns (low_conf, high_conf) [D, NM]."""
    H, L, C = b["H"], b["L"], b["C"]
    pad = lambda a, v: np.concatenate([np.full((D, 30), v), a], 1)
    from numpy.lib.stride_tricks import sliding_window_view as sw
    Lp, Hp = pad(L, np.inf), pad(H, -np.inf)
    min30 = sw(Lp, 30, axis=1)[:, :NM]          # window for bar u covers u-30..u-1 (padded index)
    max30 = sw(Hp, 30, axis=1)[:, :NM]
    lowprev = np.concatenate([np.full((D, 1), np.nan), L[:, :-1]], 1)
    highprev = np.concatenate([np.full((D, 1), np.nan), H[:, :-1]], 1)
    hh3 = sw(Hp, 3, axis=1)[:, 27:27 + NM].max(2)
    ll3 = sw(Lp, 3, axis=1)[:, 27:27 + NM].min(2)
    with np.errstate(invalid="ignore"):
        lc = (lowprev <= min30.min(2)) & (L > lowprev) & (C > hh3)
        hc = (highprev >= max30.max(2)) & (H < highprev) & (C < ll3)
    lc[:, :2] = False
    hc[:, :2] = False
    return back_any(lc, 6), back_any(hc, 6)


# ---------------------------------------------------------------- market context
spy1 = load1("SPY")
spyC1 = spy1["C"]
etf_conf = {"SPY": confirmed_swings(spy1)}
for e in SECTOR:
    be = load1(e)
    if be is not None:
        etf_conf[e] = confirmed_swings(be)


def mkt(name):
    j = si[name]
    bb = {k: ctxz[f"{name}_{k}"].astype(np.float64) for k in ("O", "H", "L", "C")}
    return market_features(bb, aux["atr"][:, j].astype(np.float64))


ctx = {"spy": mkt("SPY"), "qqq": mkt("QQQ"), "breadth": ctxz["breadth"].astype(np.float64)}


def macd_hist(c):
    s = pd.Series(c.ravel())
    m = s.ewm(span=12, adjust=False).mean() - s.ewm(span=26, adjust=False).mean()
    return (m - m.ewm(span=9, adjust=False).mean()).to_numpy().reshape(c.shape)


def simulate(b, d, i, side, R, beta):
    """Fixed 1R and trail-after-1R from the close of 1-minute bar i on session d. Returns dict of results."""
    s = 1 if side == "long" else -1
    e = b["C"][d, i]
    H, L, O, C = b["H"][d, i + 1:XI + 1], b["L"][d, i + 1:XI + 1], b["O"][d, i + 1:XI + 1], b["C"][d, i + 1:XI + 1]
    n = len(H)
    fav, adv = (H, L) if s == 1 else (-L, -H)
    ee = s * e
    # fixed 1R (lab convention)
    ht = np.flatnonzero(fav >= ee + R)
    hs = np.flatnonzero(adv <= ee - R)
    ft = ht[0] if len(ht) else n + 1
    fs = hs[0] if len(hs) else n + 1
    if ft < fs:
        val, win, xi = 1.0, 1.0, ft
    elif fs < n + 1:
        val, win, xi = -1.0, 0.0, fs
    else:
        val, win, xi = s * (C[-1] - e) / R, 0.0, n - 1
    fixed = (val - 0.02 / R, win, xi)
    # trail after 1R
    runmax = np.maximum.accumulate(fav)
    prevmax = np.concatenate([[-np.inf], runmax[:-1]])
    stop = np.where(prevmax >= ee + R, np.maximum(ee - R, prevmax - R), ee - R)
    hit = np.flatnonzero(adv <= stop)
    if len(hit):
        j = hit[0]
        op = s * O[j]
        px = min(stop[j], op)
        tr = ((px - ee) / R, True, j)
    else:
        tr = (s * (C[-1] - e) / R, False, n - 1)
    return fixed, tr


rows = []
t0 = time.time()
done = 0
W = np.zeros(NM, bool)
W[W0:W1 + 1] = True
tm1 = tod_cost_mult(TOD1)
for j, sym in enumerate(syms):
    if sym in ETFS:
        continue
    if LIMIT and done >= LIMIT:
        break
    atr = aux["atr"][:, j].astype(np.float64)
    adv = aux["adv20"][:, j]
    okday = np.isfinite(atr) & (atr > 0) & (adv >= MIN_ADV)
    if not okday.any():
        continue
    b = load1(sym)
    if b is None:
        continue
    done += 1
    beta = aux["beta_spy"][:, j].astype(np.float64)
    R = 0.25 * atr
    O, H, L, C = b["O"], b["H"], b["L"], b["C"]
    E = b["present"] & okday[:, None] & W[None]
    # 1-minute features
    with np.errstate(invalid="ignore", divide="ignore"):
        hist = macd_hist(C)
        histp = np.concatenate([np.full((D, 1), np.nan), hist[:, :-1]], 1)
        xup, xdn = back_any((hist > 0) & (histp <= 0), 3), back_any((hist < 0) & (histp >= 0), 3)
        Op = np.concatenate([np.full((D, 1), np.nan), O[:, :-1]], 1)
        Cp = np.concatenate([np.full((D, 1), np.nan), C[:, :-1]], 1)
        body, rng = np.abs(C - O), H - L
        lw, uw = np.minimum(O, C) - L, H - np.maximum(O, C)
        trig = {"long": xup | ((C > O) & (Cp < Op) & (C >= Op) & (O <= Cp)) | ((lw >= 2 * body) & (uw <= body) & (rng > 0)),
                "short": xdn | ((C < O) & (Cp > Op) & (C <= Op) & (O >= Cp)) | ((uw >= 2 * body) & (lw <= body) & (rng > 0))}
        C10 = np.concatenate([np.full((D, 10), np.nan), C[:, :-10]], 1)
        roc = (C - C10) / atr[:, None]
        rsi2 = rsi_simple(pd.Series(C.ravel()), 2).to_numpy().reshape(D, NM)
        e9 = pd.Series(C.ravel()).ewm(span=9, adjust=False).mean().to_numpy().reshape(D, NM)
        lowx = back_any(rsi2 <= 10, 3) & back_any(C < e9, 3)
        rocq10, rocq90 = prior_q(roc, 0.10), prior_q(roc, 0.90)
        # 5-minute features from the 1-minute bars
        f5 = to5(b)
        C5 = f5["C"].astype(np.float64)
        tp = (f5["H"] + f5["L"] + f5["C"]).astype(np.float64) / 3
        V5 = f5["V"].astype(np.float64)
        cv = np.cumsum(V5, 1)
        vw = np.cumsum(tp * V5, 1) / np.where(cv > 0, cv, np.nan)
        vsd = np.sqrt(np.maximum(np.cumsum(tp * tp * V5, 1) / np.where(cv > 0, cv, np.nan) - vw * vw, 0))
        vz5 = (C5 - vw) / np.where(vsd > 0, vsd, np.nan)
        r14_5 = rsi_simple(pd.Series(C5.ravel()), 14).to_numpy().reshape(D, NB)
        vzq10, vzq90, rq10, rq90 = prior_q(vz5, .1), prior_q(vz5, .9), prior_q(r14_5, .1), prior_q(r14_5, .9)
        Lc, Sc = conditions(f5, {"atr": atr, "pclose": aux["pclose"][:, j].astype(np.float64),
                                 "pdh": aux["pdh"][:, j].astype(np.float64), "pdl": aux["pdl"][:, j].astype(np.float64)},
                            ctx, beta)
        litL, litS = Lc[:59].sum(0).astype(float), Sc[:59].sum(0).astype(float)
        litL[~f5["present"]], litS[~f5["present"]] = np.nan, np.nan
        lq, sq = prior_q(litL, .97), prior_q(litS, .97)
        vz1, r141, litL1, litS1 = last5(vz5), last5(r14_5), last5(litL), last5(litS)
        # levels
        lod = np.fmin.accumulate(L, 1)
        hod = np.fmax.accumulate(H, 1)
        lod30 = np.concatenate([np.full((D, 30), np.nan), lod[:, :-30]], 1)
        hod30 = np.concatenate([np.full((D, 30), np.nan), hod[:, :-30]], 1)
        dop = O[:, :1]
        a1 = 0.10 * atr[:, None]
        pcl, pdh, pdl = (aux[k][:, j].astype(np.float64)[:, None] for k in ("pclose", "pdh", "pdl"))
        lvlL = ((np.abs(L - lod30) <= a1) | (np.abs(L - dop) <= a1) | (np.abs(L - pcl) <= a1) | (np.abs(L - pdl) <= a1)
                | (np.abs(L - np.round(L / 5) * 5) <= a1))
        lvlS = ((np.abs(H - hod30) <= a1) | (np.abs(H - dop) <= a1) | (np.abs(H - pcl) <= a1) | (np.abs(H - pdh) <= a1)
                | (np.abs(H - np.round(H / 5) * 5) <= a1))
        # market confirmation: SPY or own sector ETF
        sec = secmap[:, j]
        mL, mS = etf_conf["SPY"][0].copy(), etf_conf["SPY"][1].copy()
        for k, e in enumerate(SECTOR):
            if e in etf_conf:
                dm = sec == k
                if dm.any():
                    mL[dm] |= etf_conf[e][0][dm]
                    mS[dm] |= etf_conf[e][1][dm]
        S = {}
        s2L = (roc <= rocq10[:, None]) & trig["long"] & lowx
        s2S = (roc >= rocq90[:, None]) & trig["short"]
        S["long"] = {"S1": (vz1 <= vzq10[:, None]) & (r141 <= rq10[:, None]) & trig["long"], "S2": s2L,
                     "S3": s2L & lvlL, "S4": s2L & mL, "S5": (litL1 >= lq[:, None]) & trig["long"]}
        S["short"] = {"S1": (vz1 >= vzq90[:, None]) & (r141 >= rq90[:, None]) & trig["short"], "S2": s2S,
                      "S3": s2S & lvlS, "S4": s2S & mS, "S5": (litS1 >= sq[:, None]) & trig["short"]}
    for side in ("long", "short"):
        sgn = 1 if side == "long" else -1
        for sig, M in S[side].items():
            M = M & E
            dd, ii = np.nonzero(M)
            if not len(dd):
                continue
            cur_d, last_on, busy_until, first_done = -1, -99, -1, False
            for d, i in zip(dd, ii):
                if d != cur_d:
                    cur_d, last_on, busy_until, first_done = d, -99, -1, False
                is_first = not first_done
                take_all = (i - last_on >= 15) and (i > busy_until)
                if not (is_first or take_all):
                    continue
                Rd = R[d]
                (fv, fw, fx), (tv, tstop, tx) = simulate(b, d, i, side, Rd, beta[d])
                px = C[d, i]
                tod = TOD1[i]
                rf = float(prod_r(np.array([fv]), np.array([fw]), np.array([px]), np.array([atr[d]]), "t1s1",
                                  tod=np.array([tod]))[0])
                cost_t = ((0.01 + px * 1e-4) * tm1[i] + (0.01 + px * 1e-4) + (0.02 if tstop else 0.0)) / Rd
                rt = tv - cost_t
                bt = beta[d]
                se0 = spyC1[d, i]
                hed = []
                for r_, x_ in ((rf, fx), (rt, tx)):
                    if np.isfinite(bt):
                        sx = spyC1[d, i + 1 + x_]
                        hed.append(r_ - sgn * bt * px * (sx / se0 - 1) / Rd - 2 * bt * px * (0.01 / se0 + 1e-4) / Rd)
                    else:
                        hed.append(np.nan)
                rows.append((d, j, side, sig, tod, is_first, take_all, rf, rt, hed[0], hed[1], fw))
                if is_first:
                    first_done = True
                if take_all:
                    last_on, busy_until = i, i + 1 + max(fx, tx)
    if done % 25 == 0:
        print(done, j, sym, len(rows), round(time.time() - t0), flush=True)

df = pd.DataFrame(rows, columns=["d", "sym", "side", "sig", "tod", "first", "all", "r_fixed", "r_trail",
                                 "h_fixed", "h_trail", "win_fixed"])
df["date"] = [dates[k] for k in df["d"]]
df.to_parquet(DATA / f"trades1m{'_test' if LIMIT else ''}.parquet", index=False)
print("done", done, len(df), round(time.time() - t0), flush=True)
