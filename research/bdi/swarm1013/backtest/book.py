"""swarm1013 E5: correlated same-side lot cap, a portfolio replay of the Primary book (PLAN section 1, E5).

Book = every B1 trade of the 11 setups, ordered by signal bar, then config order. A trade is open from its fill bar
(signal bar + 1) to its B1 exit bar; a trade signalled on the same bar earlier in the order counts as open. A new
trade is skipped when >= c open same-side, not-skipped trades have a 20-session 5-minute-return correlation >= rho
with it (prior 20 open sessions, intraday 5-minute log returns, missing returns set to 0 after the session filter;
< 10 sessions with data -> no correlation, no skip). SECT2: >= 2 open same-side trades with the same sector ETF.
Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np

from signals import SCR, SETUPS

ORDER = {x: i for i, x in enumerate(SETUPS)}   # config order: MF1..MF5, NS1..NS5, RW6G1


def _corr_matrix(C5, idxs, ss):
    lo = max(0, ss - 20)
    X = C5[idxs, lo:ss, :].astype(np.float64)            # [m, 20, 78]
    with np.errstate(all="ignore"):
        r = np.diff(np.log(X), axis=2)                   # [m, 20, 77]
    have = np.isfinite(r).all(2).sum(1)                  # sessions with data
    r = np.nan_to_num(r).reshape(len(idxs), -1)
    r = r - r.mean(1, keepdims=True)
    sd = np.sqrt((r * r).sum(1))
    with np.errstate(all="ignore"):
        cm = (r @ r.T) / np.outer(sd, sd)
    bad = have < 10
    cm[bad, :] = np.nan
    cm[:, bad] = np.nan
    return cm


def corr_cap(T, b1, b1_exit, ok, sect):
    z = np.load(SCR / "c5.npz")
    syms = [str(x) for x in z["syms"]]
    C5 = z["C5"]
    si = {x: i for i, x in enumerate(syms)}
    sym_i = T["symbol"].map(si).to_numpy()
    side = T["side"].to_numpy()
    k = T["k"].to_numpy(int)
    sess = T["sess"].to_numpy(int)
    xk = np.where(b1_exit > 0, k + b1_exit, 99)
    order = np.lexsort((T["setup"].map(ORDER).to_numpy(), k, sess))
    variants = {"rho0.35 c2": (0.35, 2), "rho0.50 c2": (0.50, 2), "rho0.35 c1": (0.35, 1), "rho0.50 c1": (0.50, 1),
                "SECT2": (None, 2)}
    kept = {v: np.ones(len(T), bool) for v in variants}
    stats = {v: 0 for v in variants}
    by_sess = {}
    for i in order:
        if ok[i]:
            by_sess.setdefault(sess[i], []).append(i)
    for ss, lst in by_sess.items():
        u = sorted(set(sym_i[lst]))
        cm = _corr_matrix(C5, np.array(u), ss)
        pos = {x: j for j, x in enumerate(u)}
        for v, (rho, c) in variants.items():
            kp = kept[v]
            for a, i in enumerate(lst):
                n = 0
                for jj in lst[:a]:
                    if not kp[jj] or side[jj] != side[i] or xk[jj] <= k[i]:
                        continue
                    if rho is None:
                        hit = sect[jj] == sect[i]
                    else:
                        cv = cm[pos[sym_i[i]], pos[sym_i[jj]]]
                        hit = np.isfinite(cv) and cv >= rho
                    n += hit
                    if n >= c:
                        break
                if n >= c:
                    kp[i] = False
                    stats[v] += 1
    print("E5 skipped", stats, flush=True)
    return kept
