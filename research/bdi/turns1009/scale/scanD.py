"""Stage D (amendment A2): percent turn labels (0.5% move, adverse 0.25% / 0.35%), extended panel (70 conditions,
singles + pairs), lines pct t0.5/s0.35, pct t0.5/s0.25 (bps) and t1s1 (R), raw and SPY-hedged.
    python scanD.py [limit]  -> data/aggD.npz, data/turnstatsD.npz
Educational only - not financial advice."""
import sys
import time
from itertools import combinations

import numpy as np

from common import (DATA, ETFS, I0, I1, MIN_ADV, NB, NCX, TODS, conditions, exits, exits_pct, fill, load_bars,
                    market_features, open_dates, prod_lines, symbols, tod_cost_mult, turn_labels)

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None
syms, dates = symbols(), open_dates()
dates64 = np.array([np.datetime64(str(x)) for x in dates], dtype="datetime64[us]")
D = len(dates)
gapday = np.r_[True, np.diff(dates64).astype("timedelta64[D]").astype(int) > 5]   # previous open session not adjacent
aux = dict(np.load(DATA / "aux.npz"))
ctxz = dict(np.load(DATA / "context.npz"))
si = {s: i for i, s in enumerate(syms)}
U = 0.001                                         # label unit: 0.1% in log price
XS = (2.5, 3.5)                                   # adverse 0.25%, 0.35%


def mkt(name):
    j = si[name]
    b = {k: ctxz[f"{name}_{k}"].astype(np.float64) for k in ("O", "H", "L", "C")}
    return market_features(b, aux["atr"][:, j].astype(np.float64))


ctx = {"spy": mkt("SPY"), "qqq": mkt("QQQ"), "breadth": ctxz["breadth"].astype(np.float64)}
spyC = ctxz["SPY_C"].astype(np.float64)
todm = tod_cost_mult(TODS)[None, :]
UNIT = np.full(D, U)
spl, _ = turn_labels(np.log(ctxz["SPY_H"].astype(np.float64)), np.log(ctxz["SPY_L"].astype(np.float64)), UNIT,
                     ks=(5,), m=5, tols=(0.0,))
spy_dil = {}
for side in ("long", "short"):
    for key, t in (("pct", spl[(side, 5, 0.0)]), ("R2", ctxz[f"spyturn_{side}_2"])):
        d = t.copy()
        for sh in (1, 2):
            d[:, sh:] |= t[:, :-sh]
            d[:, :-sh] |= t[:, sh:]
        spy_dil[(side, key)] = d
spy_rate = {k: float(v.mean()) for k, v in spl.items()}

combos = [(i, NCX, NCX) for i in range(NCX)] + [(i, j, NCX) for i, j in combinations(range(NCX), 2)]
NF = 14   # 0 fires,1 Y25,2 Y35,3 fires_bdef,4 craw35,5 cres35,6 n,7-9 raw sums (p035,p025,t1s1),10 n_h,11-13 hedged
agg = {s: np.zeros((len(combos), NF, D), np.float64) for s in ("long", "short")}
base = {s: np.zeros((NF, D), np.float64) for s in ("long", "short")}
WIN = np.zeros(NB, bool)
WIN[I0:I1 + 1] = True
TWIN = TODS >= 950                                 # turn statistics window (extreme bar close >= 09:50)
HB = np.arange(0, 10.05, 0.05)
TB = np.array([950, 1000, 1030, 1100, 1130, 1200, 1230, 1300, 1330, 1400, 1430, 1500, 1530, 1600])
ts = {"stock_days": 0, "sessions": np.zeros(D)}
for side in ("long", "short"):
    for x in ("x0", "x25", "x35"):
        ts[f"n_{side}_{x}"] = 0
    ts[f"hist_{side}"] = np.zeros(len(HB) - 1)
    ts[f"tod_{side}"] = np.zeros(len(TB) - 1)
    for key in ("pct", "R2"):
        ts[f"coin_{side}_{key}"] = 0
        ts[f"chance_{side}_{key}"] = 0.0
    ts[f"bydate_{side}"] = np.zeros(D)


def ahead(x):
    y = x.copy()
    y[:, :-1] |= x[:, 1:]
    y[:, :-2] |= x[:, 2:]
    return y


t0 = time.time()
done = 0
for j, s in enumerate(syms):
    if s in ETFS:
        continue
    if LIMIT and done >= LIMIT:
        break
    atr = aux["atr"][:, j].astype(np.float64)
    adv = aux["adv20"][:, j]
    okday = np.isfinite(atr) & (atr > 0) & (adv >= MIN_ADV)
    if not okday.any():
        continue
    b = load_bars(s, dates64)
    if b is None:
        continue
    f = fill(b)
    H, L, C, O = (f[k].astype(np.float64) for k in ("H", "L", "C", "O"))
    R = np.where(okday, 0.25 * atr, np.nan)
    beta = aux["beta_spy"][:, j].astype(np.float64)
    E = f["present"] & okday[:, None] & WIN[None, :]
    if not E.any():
        continue
    done += 1
    sday = okday & f["present"].any(1)
    pdopen = np.r_[np.nan, O[:-1, 0]]
    pdopen[gapday] = np.nan
    pdopen[~np.r_[False, f["present"][:-1].any(1)]] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        lH, lL, lC = np.log(H), np.log(L), np.log(C)
        labs, sizes = turn_labels(lH, lL, UNIT, ks=(5,), m=5, tols=XS + (0.0,))
        bdef = np.isfinite(beta)
        res = lC - np.where(bdef, beta, 0)[:, None] * np.log(spyC)
    craw, _ = turn_labels(lC, lC, UNIT, ks=(5,), m=5, tols=(3.5,))
    cres, _ = turn_labels(res, res, UNIT, ks=(5,), m=5, tols=(3.5,))
    bd = bdef[:, None] & np.ones((1, NB), bool)
    Ys = {}
    for side in ("long", "short"):
        cols = [np.ones((D, NB), bool), ahead(labs[(side, 5, 2.5)]), ahead(labs[(side, 5, 3.5)]), bd,
                ahead(craw[(side, 5, 3.5)]) & bd, ahead(cres[(side, 5, 3.5)]) & bd]
        Ys[side] = np.stack(cols, -1).astype(np.float32)
    # turn statistics (extreme bar >= 09:50)
    ts["stock_days"] += int(sday.sum())
    ts["sessions"] += sday
    pres = f["present"] & sday[:, None] & TWIN[None]
    for side in ("long", "short"):
        for x, tol in (("x0", 0.0), ("x25", 2.5), ("x35", 3.5)):
            ts[f"n_{side}_{x}"] += int((labs[(side, 5, tol)] & pres).sum())
        lab = labs[(side, 5, 0.0)] & pres
        ts[f"bydate_{side}"] += lab.sum(1)
        ts[f"hist_{side}"] += np.histogram(np.clip(sizes[(side, 5)][lab] * U * 100, 0, 9.999), HB)[0]
        tt = np.broadcast_to(TODS[None], lab.shape)[lab]
        ts[f"tod_{side}"] += np.histogram(tt, TB)[0]
        for key in ("pct", "R2"):
            dil = spy_dil[(side, key)]
            ts[f"coin_{side}_{key}"] += int((lab & dil).sum())
            ts[f"chance_{side}_{key}"] += float((lab.sum(1) * dil[:, TWIN].mean(1)).sum())
    # trade lines
    ex = exits(C, H, L, R)
    rl = prod_lines(ex, C, R, todm, beta, spyC)
    lines = {}
    for side, sg in (("long", 1), ("short", -1)):
        arr = np.full((6, D, NB), np.nan, np.float32)
        for gi, stp in enumerate((0.0035, 0.0025)):
            val, won, lost, exi = exits_pct(C, H, L, 0.005, stp)[side]
            cost = ((0.01 + C * 1e-4) * todm + np.where(won, 0, 0.01 + C * 1e-4) + np.where(lost, 0.02, 0)) / C * 1e4
            r = val - cost
            r[:, :] = np.where(np.isfinite(R)[:, None], r, np.nan)
            se = spyC[np.arange(D)[:, None], exi]
            with np.errstate(invalid="ignore", divide="ignore"):
                hed = sg * beta[:, None] * (se / spyC - 1) * 1e4 + 2 * beta[:, None] * (0.01 / spyC + 1e-4) * 1e4
            arr[gi] = r
            arr[3 + gi] = r - hed
        arr[2] = rl[side][0]
        arr[5] = rl[side][4]
        lines[side] = arr
    Lc, Sc = conditions(f, {"atr": atr, "pclose": aux["pclose"][:, j].astype(np.float64),
                            "pdh": aux["pdh"][:, j].astype(np.float64), "pdl": aux["pdl"][:, j].astype(np.float64),
                            "pdopen": pdopen}, ctx, beta, extra=True)
    for side, M in (("long", Lc), ("short", Sc)):
        Mx = np.concatenate([M & E[None], E[None]], 0).reshape(NCX + 1, D * NB)
        lin = lines[side].reshape(6, D * NB)
        Y = Ys[side]
        Ef = E.astype(np.float32)
        base[side][:6] += np.einsum("db,dbk->kd", Ef, Y)
        base[side][6] += E.sum(1)
        base[side][7:10] += np.nansum(np.where(E[None], lines[side][:3], np.nan), 2)
        hv = E[None] & np.isfinite(lines[side][3:])
        base[side][10] += hv[0].sum(1)
        base[side][11:14] += np.where(hv, lines[side][3:], 0).sum(2)
        for a in range(0, len(combos), 128):
            ch = np.array(combos[a:a + 128])
            B = Mx[ch[:, 0]] & Mx[ch[:, 1]] & Mx[ch[:, 2]]
            nb = len(ch)
            B3 = B.reshape(nb, D, NB)
            st = np.matmul(B3.astype(np.float32).transpose(1, 0, 2), Y)
            agg[side][a:a + nb, :6] += st.transpose(1, 2, 0)
            anyb = B3.any(2)
            fi = np.arange(D)[None, :] * NB + B3.argmax(2)
            v = lin[:, fi]
            agg[side][a:a + nb, 6] += anyb
            agg[side][a:a + nb, 7:10] += np.where(anyb[None], v[:3], 0).transpose(1, 0, 2)
            hok = anyb & np.isfinite(v[3])
            agg[side][a:a + nb, 10] += hok
            agg[side][a:a + nb, 11:14] += np.where(hok[None], v[3:], 0).transpose(1, 0, 2)
    if done % 25 == 0:
        print(done, j, s, round(time.time() - t0), flush=True)

tag = "" if not LIMIT else "_test"
np.savez(DATA / f"aggD{tag}.npz", long=agg["long"].astype(np.float32), short=agg["short"].astype(np.float32),
         base_long=base["long"], base_short=base["short"], combos=np.array(combos))
np.savez(DATA / f"turnstatsD{tag}.npz", **{k: np.asarray(v) for k, v in ts.items()}, hb=HB, tb=TB,
         spy_rate_long=spy_rate[("long", 5, 0.0)], spy_rate_short=spy_rate[("short", 5, 0.0)])
print("done", done, round(time.time() - t0), flush=True)
