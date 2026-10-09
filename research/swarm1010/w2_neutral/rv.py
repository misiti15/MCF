"""Task 2 (NOTES 1.5): relative-value intraday setups - stock vs SPY (F1), vs its sector ETF (F2), vs its most
correlated same-sector partner (F3); spread z over the last N 5-min bars; fade or momentum; t1s1 on the stock leg,
hedge leg (beta from prior sessions) closed at the same bar; both legs' costs. Writes rv_results.csv and
data/rv_trades.parquet (git-ignored). Educational only - not financial advice."""
import math

import numpy as np
import pandas as pd

from common import DATA, ETFS, HERE, SECTOR, bars, lib
from hedge import bar_check, hedge_r, score, sim_exit
from mcf.research import gates

B = bars()
syms, dates = B["syms"], B["dates"]
NS_, ND = len(syms), len(dates)
si = {s: i for i, s in enumerate(syms)}
BT = np.load(DATA / "betas.npz")
reg = lib.regimes()
spy = si["SPY"]
secsym = np.array([si[e] for e in SECTOR] + [spy])
NS = (3, 6, 12)
KS = (1.5, 2.0, 2.5)
DIRS = ("fade", "mom")
FAMS = ("SPY", "SEC", "PAIR")
B0, B1 = 3, 65                         # bar index of tod 950 and 1500
N_TRIES = 324
TREQ = round(max(2.0, math.sqrt(2 * math.log(N_TRIES))), 3)

# point-in-time population: adv20 >= 95M, non-ETF, atr_d > 0
dl = lib.daily()
dl = dl[dl["symbol"].isin(si)]
ADV = np.full((ND, NS_), np.nan, np.float32)
dmap = {d: i for i, d in enumerate(dates)}
ADV[dl["date"].map(dmap).to_numpy(), dl["symbol"].map(si).to_numpy()] = dl["adv20"].to_numpy(np.float32)
atr = pd.read_parquet(DATA / "atr.parquet")
ATR = np.full((ND, NS_), np.nan, np.float32)
atr = atr[atr["symbol"].isin(si) & atr["date"].isin(dmap)]
ATR[atr["date"].map(dmap).to_numpy(), atr["symbol"].map(si).to_numpy()] = atr["atr_d"].to_numpy(np.float32)
etf = np.array([s in ETFS for s in syms])


def hedge_of(fam, d):
    if fam == "SPY":
        return np.full(NS_, spy), BT["beta_spy"][d].astype(float)
    if fam == "SEC":
        sec = BT["sec"][d].astype(int)
        h = np.where(sec >= 0, secsym[np.maximum(sec, 0)], np.where(sec == -1, spy, -1))
        return h, BT["beta_sec"][d].astype(float)
    p = BT["partner"][d].astype(int)
    return p, BT["beta_pair"][d].astype(float)


# pass 1: per-session residual std per stock and family
SIG = {f: np.full((ND, NS_), np.nan, np.float32) for f in FAMS}
for d in range(ND):
    lc = np.log(np.asarray(B["C"][:, d, :], float))
    dr = np.diff(lc, axis=1)
    for f in FAMS:
        h, beta = hedge_of(f, d)
        ok = h >= 0
        e = dr - beta[:, None] * dr[np.maximum(h, 0)]
        with np.errstate(invalid="ignore"):
            sd = np.nanstd(np.where(ok[:, None], e, np.nan), axis=1)
        cnt = np.isfinite(e).sum(1)
        SIG[f][d] = np.where(ok & (cnt >= 40), sd, np.nan)
SIGP = {}
for f in FAMS:
    df = pd.DataFrame(SIG[f])
    SIGP[f] = df.rolling(20, min_periods=10).mean().shift(1).to_numpy()
print("sigma done", flush=True)

# pass 2: signals -> entries per (fam, N, k, dir, side)
ent = {}
for d in range(ND):
    pop = (ADV[d] >= 95e6) & ~etf & (ATR[d] > 0)
    if not pop.any():
        continue
    lc = np.log(np.asarray(B["C"][:, d, :], float))
    for f in FAMS:
        h, beta = hedge_of(f, d)
        ok = pop & (h >= 0) & np.isfinite(beta) & np.isfinite(SIGP[f][d])
        if not ok.any():
            continue
        idx = np.flatnonzero(ok)
        lh = lc[h[idx]]
        ls = lc[idx]
        for N in NS:
            S = np.full((len(idx), lc.shape[1]), np.nan)
            S[:, N:] = (ls[:, N:] - ls[:, :-N]) - beta[idx, None] * (lh[:, N:] - lh[:, :-N])
            z = S / (SIGP[f][d, idx, None] * math.sqrt(N))
            z = z[:, B0:B1 + 1]
            for k in KS:
                with np.errstate(invalid="ignore"):
                    hi, lo = z >= k, z <= -k
                for dr_ in DIRS:
                    for side in ("long", "short"):
                        m = (lo if side == "long" else hi) if dr_ == "fade" else (hi if side == "long" else lo)
                        any_ = m.any(1)
                        if not any_.any():
                            continue
                        first = np.argmax(m, 1)[any_] + B0
                        key = (f, N, k, dr_, side)
                        ent.setdefault(key, []).append(np.stack([idx[any_], np.full(any_.sum(), d), first,
                                                                 h[idx[any_]]], 1).astype(np.int32))
    if d % 50 == 0:
        print("day", d, flush=True)

rows, books = [], {}
keep_tr = []
for key, parts in sorted(ent.items()):
    f, N, k, dr_, side = key
    E = np.concatenate(parts)
    s, d, b, h = (E[:, i].astype(np.int64) for i in range(4))
    sg = np.full(len(s), 1.0 if side == "long" else -1.0)
    R = 0.25 * ATR[d, s].astype(float)
    e_, ex, lab, win = sim_exit(B["C"], B["H"], B["L"], s, d, b, sg, np.ones(len(s)), np.ones(len(s)), R)
    ok = np.isfinite(lab)
    r1 = np.full(len(s), np.nan)
    r1[ok] = gates.prod_r(lab[ok], win[ok], e_[ok], ATR[d, s][ok], "t1s1")
    beta = (BT["beta_spy"] if f == "SPY" else BT["beta_sec"] if f == "SEC" else BT["beta_pair"])[d, s].astype(float)
    r2 = r1 + hedge_r(B["C"], sg, e_, R, beta, h, d, b, ex)
    good = np.isfinite(r1) & np.isfinite(r2)
    dts = np.array(dates, dtype=object)[d[good]]
    for var, rr in (("single", r1[good]), ("hedged", r2[good])):
        tr = pd.DataFrame({"date": dts, "r": rr})
        o = score(tr, reg)
        rows.append({"part": "rv", "family": f, "N": N, "k": k, "dir": dr_, "side": side, "variant": var, **o})
        books.setdefault((f, N, k, dr_, var), []).append(tr)
    if (f, N, k) == ("SEC", 6, 2.0):
        keep_tr.append(pd.DataFrame({"date": dts, "symbol": np.array(syms)[s[good]], "tod": b[good], "hedge": np.array(syms)[h[good]],
                                     "dir": dr_, "side": side, "r_single": r1[good], "r_hedged": r2[good]}))
    print(key, len(s), flush=True)
for (f, N, k, dr_, var), parts in books.items():
    o = score(pd.concat(parts, ignore_index=True), reg)
    rows.append({"part": "rv", "family": f, "N": N, "k": k, "dir": dr_, "side": "book", "variant": var, **o})
res = pd.DataFrame(rows)
# plateau: neighbours k +- 0.5 and N one step, same family / dir / side / variant
plat = []
for _, r in res.iterrows():
    ni = NS.index(r["N"])
    nb = res[(res.family == r.family) & (res.dir == r.dir) & (res.side == r.side) & (res.variant == r.variant)
             & (((res.N == r.N) & ((res.k - r.k).abs().round(2) == 0.5))
                | ((res.k == r.k) & res.N.isin([NS[j] for j in (ni - 1, ni + 1) if 0 <= j < len(NS)])))]
    plat.append(round(float(nb["exp_r"].mean()), 4) if len(nb) else np.nan)
res["plateau"] = plat
res["t_req"] = TREQ
pf = [bar_check(r, TREQ, r["plateau"]) for r in res.to_dict("records")]
res["pass"] = [p for p, _ in pf]
res["fails"] = [";".join(x) for _, x in pf]
res.to_csv(HERE / "rv_results.csv", index=False)
if keep_tr:
    pd.concat(keep_tr).to_parquet(DATA / "rv_trades_sec6_k2.parquet")
print("pass", int(res["pass"].sum()), "of", len(res))
