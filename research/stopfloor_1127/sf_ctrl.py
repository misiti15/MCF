"""STOPFLOOR-1127 widen controls (PREREG bar 2): for each widen config, the lots' widening multipliers (risk'/risk) are
permuted at random across lots within setup x split (200 reps); each permuted lot is re-walked on 1-min bars with the
BASE rule at its new risk; dR (LIVE-L) summed per rep x split. Usage (repo root): python research/stopfloor_1127/sf_ctrl.py WALK_DIR.
Locked block never read. Educational only - not financial advice."""
import json, os, sys
from collections import defaultdict
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sf_common import lot_R, no_locked  # noqa: E402
from sf_walk import load, HIST, FRESH, TGT_MULT  # noqa: E402

CFGS = ["W50", "W75", "W100", "Wc10", "Wc20"]
REPS = 200


def walk_multi(s, e, risks, tmult, tod, hm, O, H, Lo, C):
    sel = np.flatnonzero((hm >= tod) & (hm < 1555)); after = np.flatnonzero(hm >= 1555)
    if not len(sel):
        return None
    Os, Hs, Ls, Cs = O[sel], H[sel], Lo[sel], C[sel]
    stop = (e - s * risks)[:, None]; tgt = (e + s * tmult * risks)[:, None]
    if s == 1:
        st, tg = Ls[None, :] <= stop, Hs[None, :] >= tgt + 0.01
    else:
        st, tg = Hs[None, :] >= stop, Ls[None, :] <= tgt - 0.01
    ev = st | tg; anyev = ev.any(1); j = ev.argmax(1)
    flat = O[after[0]] if len(after) else Cs[-1]
    rows = np.arange(len(risks))
    isst = st[rows, j]
    sp = np.where(s == 1, np.minimum(Os[j], stop[:, 0]), np.maximum(Os[j], stop[:, 0]))
    px = np.where(~anyev, flat, np.where(isst, sp, tgt[:, 0]))
    kind = np.where(~anyev, 0, np.where(isst, 1, 2))
    return px, kind


def job(args):
    sym, T = args            # T rows: lot fields + list of (cfg_i, rep, risk')
    acc = defaultdict(float)
    for src, sub in ((HIST, T[T.date >= "2024-09-16"]), (FRESH, T[T.date < "2024-09-16"])):
        if not len(sub):
            continue
        b = load(sym, src)
        if b is None:
            continue
        day = b.index.date.astype(str); hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        for d, g in sub.groupby("date"):
            ix = np.flatnonzero(day == d)
            if not len(ix):
                continue
            hm = hhmm[ix]
            for r in g.itertuples():
                jobs = r.jobs
                if not len(jobs):
                    continue
                risks = np.array([q[2] for q in jobs])
                w = walk_multi(int(r.side), float(r.entry), risks, TGT_MULT[r.setup], int(r.tod), hm, O[ix], H[ix], Lo[ix], C[ix])
                if w is None:
                    continue
                n = len(risks)
                _, ll, _ = lot_R(np.full(n, r.entry), w[0], risks, w[1], np.full(n, r.side), np.full(n, r.tod), np.full(n, r.gap))
                for (ci, rep, _), x in zip(jobs, ll - r.ll_BASE):
                    acc[(ci, rep, r.per)] += float(x)
    return dict(acc)


if __name__ == "__main__":
    W = sys.argv[1]
    c = pd.read_parquet(W + "/walk.parquet")
    no_locked(c.date.unique())
    _, c["ll_BASE"], _ = lot_R(c.entry.to_numpy(), c.px_BASE.to_numpy(), c.risk.to_numpy(), c.kind_BASE.to_numpy(),
                               c.side.to_numpy(), c.tod.to_numpy(), c.gap.to_numpy())
    rng = np.random.default_rng(1127)
    jobs = [[] for _ in range(len(c))]
    for ci, v in enumerate(CFGS):
        mult = (c[f"rk_{v}"] / c.risk).to_numpy()
        for _, g in c.groupby(["setup", "per"]):
            ii = g.index.to_numpy(); mm = mult[ii]
            for rep in range(REPS):
                pm = rng.permutation(mm)
                for k in np.flatnonzero(pm > 1.0 + 1e-12):
                    jobs[ii[k]].append((ci, rep, float(c.risk.iat[ii[k]] * pm[k])))
    c["jobs"] = jobs
    print("walks", sum(len(j) for j in jobs), flush=True)
    acc = defaultdict(float)
    with Pool(4) as p:
        for a in p.imap_unordered(job, [(s, g) for s, g in c.groupby("symbol")], chunksize=4):
            for k, x in a.items():
                acc[k] += x
    out = {}
    for ci, v in enumerate(CFGS):
        out[v] = {}
        for per in ("FIT", "CHECK", "T2"):
            out[v][per] = [round(acc.get((ci, rep, per), 0.0), 3) for rep in range(REPS)]
    json.dump(out, open(HERE + "/ctrl_widen.json", "w"))
    print({v: {p: (round(np.mean(x), 1), round(np.percentile(x, 95), 1)) for p, x in d.items()} for v, d in out.items()})
