"""Scan: per symbol, factor panel + turn labels + exits; aggregate per (condition, session). NOTES 1.2-1.5.
    python scan.py A        singles + pairs (also turn statistics and parity)
    python scan.py B        triples listed in data/triples.json (chosen on train by select_triples.py)
Output (git-ignored): data/agg{A,B}.npz. Educational only - not financial advice."""
import json
import sys
import time
from itertools import combinations

import numpy as np
import pandas as pd

from common import (DATA, ETFS, I0, I1, KS, MIN_ADV, NB, NC, TODS, conditions, exits, fill, load_bars,
                    market_features, open_dates, prod_lines, symbols, tod_cost_mult, turn_labels)

STAGE = sys.argv[1] if len(sys.argv) > 1 else "A"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else None
syms, dates = symbols(), open_dates()
dates64 = np.array([np.datetime64(str(x)) for x in dates], dtype="datetime64[us]")
D = len(dates)
aux = dict(np.load(DATA / "aux.npz"))
ctxz = dict(np.load(DATA / "context.npz"))
si = {s: i for i, s in enumerate(syms)}


def mkt(name):
    j = si[name]
    b = {k: ctxz[f"{name}_{k}"].astype(np.float64) for k in ("O", "H", "L", "C")}
    return market_features(b, aux["atr"][:, j].astype(np.float64))


ctx = {"spy": mkt("SPY"), "qqq": mkt("QQQ"), "breadth": ctxz["breadth"].astype(np.float64)}
spyC = ctxz["SPY_C"].astype(np.float64)
spy_dil = {}
for side in ("long", "short"):
    for k in KS:
        t = ctxz[f"spyturn_{side}_{k}"]
        d = t.copy()
        for sh in (1, 2):
            d[:, sh:] |= t[:, :-sh]
            d[:, :-sh] |= t[:, sh:]
        spy_dil[(side, k)] = d
todm = tod_cost_mult(TODS)[None, :]

if STAGE == "A":
    combos = [(i, NC, NC) for i in range(NC)] + [(i, j, NC) for i, j in combinations(range(NC), 2)]
    combos = {"long": combos, "short": combos}
else:
    tj = json.loads((DATA / "triples.json").read_text())
    combos = {s: [tuple(c) for c in tj[s]] for s in ("long", "short")}
NF = 19        # 0 fires,1-3 Y2-4,4 fires_bdef,5 craw3,6 cres3,7 craw2,8 cres2,9 n,10-13 raw sums,14 n_hedged,15-18 hedged
agg = {s: np.zeros((len(combos[s]), NF, D), np.float64) for s in ("long", "short")}
base = {s: np.zeros((NF, D), np.float64) for s in ("long", "short")}       # all eligible bars (random-bar baseline)
first = {s: np.zeros((NF, D), np.float64) for s in ("long", "short")}      # first eligible bar per symbol-day
# turn statistics (stage A)
HB = np.arange(0, 60.25, 0.25)
tstats = {"stock_days": 0, "stock_days_by_date": np.zeros(D)}
for side in ("long", "short"):
    for k in KS:
        for w in ("all", "win"):
            tstats[f"n_{side}_{k}_{w}"] = 0
            tstats[f"coin_{side}_{k}_{w}"] = 0
            tstats[f"chance_{side}_{k}_{w}"] = 0.0
            tstats[f"hist_{side}_{k}_{w}"] = np.zeros(len(HB) - 1)
        tstats[f"bydate_{side}_{k}"] = np.zeros(D)
        tstats[f"diag_n_{side}_{k}"] = 0
par = pd.read_parquet(DATA / "parity_frames.parquet") if STAGE == "A" else None
par_out = []
WIN = np.zeros(NB, bool)
WIN[I0:I1 + 1] = True
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
    H, L, C = (f[k].astype(np.float64) for k in ("H", "L", "C"))
    R = np.where(okday, 0.25 * atr, np.nan)
    beta = aux["beta_spy"][:, j].astype(np.float64)
    E = f["present"] & okday[:, None] & WIN[None, :]
    if not E.any():
        continue
    done += 1
    sday = okday & f["present"].any(1)
    # ---------------- labels
    labs, sizes = turn_labels(H, L, R, tols=(1.0, 0.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        lnC = np.log(C)
        Rlog = R / aux["pclose"][:, j]
        bdef = np.isfinite(beta)
        res = lnC - np.where(bdef, beta, 0)[:, None] * np.log(spyC)
    craw, _ = turn_labels(lnC, lnC, Rlog, ks=(2, 3))
    cres, _ = turn_labels(res, res, Rlog, ks=(2, 3))

    def ahead(x):
        y = x.copy()
        y[:, :-1] |= x[:, 1:]
        y[:, :-2] |= x[:, 2:]
        return y

    bd = bdef[:, None] & np.ones((1, NB), bool)
    Ys = {}
    for side in ("long", "short"):
        cols = [np.ones((D, NB), bool)] + [ahead(labs[(side, k, 1.0)]) for k in KS] + [bd]
        cols += [ahead(craw[(side, 3, 1.0)]) & bd, ahead(cres[(side, 3, 1.0)]) & bd,
                 ahead(craw[(side, 2, 1.0)]) & bd, ahead(cres[(side, 2, 1.0)]) & bd]
        Ys[side] = np.stack(cols, -1).astype(np.float32)                     # [D, NB, 9]
    # ---------------- turn statistics (strict labels, distinct turns)
    if STAGE == "A":
        tstats["stock_days"] += int(sday.sum())
        tstats["stock_days_by_date"] += sday
        for side in ("long", "short"):
            for k in KS:
                lab = labs[(side, k, 0.0)] & sday[:, None] & f["present"]
                tstats[f"bydate_{side}_{k}"] += (lab & WIN[None]).sum(1)
                frac = spy_dil[(side, k)].mean(1)
                for w, wm in (("all", np.ones(NB, bool)), ("win", WIN)):
                    lw = lab & wm[None]
                    tstats[f"n_{side}_{k}_{w}"] += int(lw.sum())
                    tstats[f"coin_{side}_{k}_{w}"] += int((lw & spy_dil[(side, k)]).sum())
                    tstats[f"chance_{side}_{k}_{w}"] += float((lw.sum(1) * frac).sum())
                    tstats[f"hist_{side}_{k}_{w}"] += np.histogram(np.clip(sizes[(side, k)][lw], 0, 59.99), HB)[0]
    # ---------------- exits
    ex = exits(C, H, L, R)
    lines = prod_lines(ex, C, R, todm, beta, spyC)
    if par is not None and s in set(par["symbol"]):
        p = par[par["symbol"] == s]
        di = {d: i for i, d in enumerate(dates)}
        ii = p["date"].map(di).to_numpy()
        bi = ((p["tod"].to_numpy() // 100) * 60 + p["tod"].to_numpy() % 100 - 575) // 5
        ok = ~pd.isna(ii)
        ii, bi, p = ii[ok].astype(int), bi[ok], p[ok]
        for side, g, col in (("long", "t1s1", "r_long_t1s1"), ("short", "t1s1", "r_short_t1s1"),
                             ("long", "t05s1", "r_long_t05s1"), ("short", "t1s05", "r_short_t1s05")):
            mine = ex[(side, g)][0][ii, bi]
            par_out.append(pd.DataFrame({"symbol": s, "line": f"{side}_{g}", "frame": p[col].to_numpy(float),
                                         "mine": mine.astype(float), "present": f["present"][ii, bi]}))
    # ---------------- conditions
    Lc, Sc = conditions(f, {"atr": atr, "pclose": aux["pclose"][:, j].astype(np.float64),
                            "pdh": aux["pdh"][:, j].astype(np.float64), "pdl": aux["pdl"][:, j].astype(np.float64)},
                        ctx, beta)
    for side, M in (("long", Lc), ("short", Sc)):
        Mx = np.concatenate([M & E[None], E[None]], 0).reshape(NC + 1, D * NB)
        lin = lines[side].reshape(8, D * NB)
        Y = Ys[side]
        # baselines
        Ef = E.astype(np.float32)
        base[side][:9] += np.einsum("db,dbk->kd", Ef, Y)
        base[side][9] += E.sum(1)
        base[side][10:14] += np.nansum(np.where(E[None], lines[side][:4], np.nan), 2)
        hv = E[None] & np.isfinite(lines[side][4:])
        base[side][14] += hv[0].sum(1)
        base[side][15:19] += np.where(hv, lines[side][4:], 0).sum(2)
        anyE = E.any(1)
        fi = np.arange(D) * NB + E.argmax(1)
        v = lin[:, fi]
        first[side][9] += anyE
        first[side][10:14] += np.where(anyE, v[:4], 0)
        hok = anyE & np.isfinite(v[4])
        first[side][14] += hok
        first[side][15:19] += np.where(hok, v[4:], 0)
        cb = combos[side]
        for a in range(0, len(cb), 128):
            ch = np.array(cb[a:a + 128])
            B = Mx[ch[:, 0]] & Mx[ch[:, 1]] & Mx[ch[:, 2]]
            nb = len(ch)
            B3 = B.reshape(nb, D, NB)
            st = np.matmul(B3.astype(np.float32).transpose(1, 0, 2), Y)        # [D, nb, 9]
            agg[side][a:a + nb, :9] += st.transpose(1, 2, 0)
            anyb = B3.any(2)
            fi = np.arange(D)[None, :] * NB + B3.argmax(2)
            v = lin[:, fi]                                                      # [8, nb, D]
            agg[side][a:a + nb, 9] += anyb
            agg[side][a:a + nb, 10:14] += np.where(anyb[None], v[:4], 0).transpose(1, 0, 2)
            hok = anyb & np.isfinite(v[4])
            agg[side][a:a + nb, 14] += hok
            agg[side][a:a + nb, 15:19] += np.where(hok[None], v[4:], 0).transpose(1, 0, 2)
    if done % 25 == 0:
        print(done, j, s, round(time.time() - t0), flush=True)

tag = STAGE if not LIMIT else f"{STAGE}_test"
np.savez(DATA / f"agg{tag}.npz", long=agg["long"].astype(np.float32), short=agg["short"].astype(np.float32),
         base_long=base["long"], base_short=base["short"], first_long=first["long"], first_short=first["short"],
         combos_long=np.array(combos["long"]), combos_short=np.array(combos["short"]))
if STAGE == "A":
    np.savez(DATA / f"turnstats{'' if not LIMIT else '_test'}.npz", **{k: np.asarray(v) for k, v in tstats.items()}, hb=HB)
    if par_out:
        pd.concat(par_out).to_parquet(DATA / f"parity{'' if not LIMIT else '_test'}.parquet", index=False)
print("done", done, round(time.time() - t0), flush=True)
