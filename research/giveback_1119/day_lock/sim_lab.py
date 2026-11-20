"""Reference only (PLAN.md): day lock on synthetic lab books (bt_lab1104 first-signal trades; 3 seeded draws of 40 trades per
session; marks linearly interpolated between entry, the 5..120-minute checkpoints and the exit). Replacement exit R =
interpolated mark - 0.08 (entry + exit cost; the PLAN's 0.05 extra plus the entry cost the gross mark lacks).
Usage: python sim_lab.py lab_paths.parquet OUT.csv. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
CK = (5, 10, 15, 30, 45, 60, 90, 120); M0, NM = 570, 390; XC = 0.08
P = pd.read_parquet(sys.argv[1], columns=["setup", "side", "date", "tod", "fin", "xmin"] + [f"mk{t}" for t in CK])
P["date"] = P.date.astype(str)
assert not ((P.date >= "2024-11-01") & (P.date <= "2025-02-28")).any(), "locked block present"
P["i0"] = ((P.tod // 100) * 60 + P.tod % 100 - M0).clip(0, NM - 1); P["i1"] = (P.xmin - M0).clip(0, NM - 1)
P = P[P.i1 > P.i0]
GRID = [(X, Y, A) for X in (5.0, 8.0) for Y in (0.3, 0.5) for A in ("A1block", "A2tighten", "A3half", "A4flatten")]
rows = []
for day, g in P.groupby("date"):
    for seed in range(3):
        b = g.sample(min(40, len(g)), random_state=hash((day, seed)) % 2**32)
        n = len(b); i0 = b.i0.to_numpy(); i1 = b.i1.to_numpy(); fin = b.fin.to_numpy(); side = b.side.to_numpy()
        M = np.zeros((n, NM))  # unrealized marks while open
        for k, r in enumerate(b.itertuples()):
            xs = [r.i0] + [r.i0 + t for t in CK if r.i0 + t < r.i1 and not np.isnan(getattr(r, f"mk{t}"))] + [r.i1]
            ys = [0.0] + [getattr(r, f"mk{t}") for t in CK if r.i0 + t < r.i1 and not np.isnan(getattr(r, f"mk{t}"))] + [r.fin]
            m = np.arange(r.i0, r.i1); M[k, r.i0:r.i1] = np.interp(m, xs, ys)
        real = np.zeros(NM)
        for k in range(n): real[i1[k]:] += fin[k]
        mtm = real + M.sum(0); pk = np.maximum.accumulate(mtm); base = real[-1]
        for X, Y, A in GRID:
            hit = np.where((pk >= X) & (mtm <= pk * (1 - Y)))[0]
            rec = dict(date=day, seed=seed, X=X, Y=Y, A=A, base=base, n=n, fired=False, delta=0.0, nrm=0)
            if len(hit) and hit[0] < NM - 1:
                t = int(hit[0]); op = (i0 <= t) & (i1 > t); late = i0 > t
                nl, ns = (side[op] > 0).sum(), (side[op] < 0).sum()
                dom = (1 if nl > ns else -1) if nl != ns else (side[i0 <= t][np.argmax(i0[i0 <= t])] if (i0 <= t).any() else 1)
                d = 0.0; nrm = 0
                if A in ("A1block", "A4flatten"):
                    blk = late & ((side == dom) | (A == "A4flatten")); d -= fin[blk].sum(); nrm = int(blk.sum())
                for k in np.where(op)[0]:
                    if A in ("A3half", "A4flatten"):
                        px = M[k, t + 1] if t + 1 < i1[k] else fin[k] + XC
                        d += (1.0 if A == "A4flatten" else 0.5) * (px - XC - fin[k])
                    elif A == "A2tighten" and M[k, t] > 0:
                        lock = 0.5 * M[k, t]; w = np.where(M[k, t + 1:i1[k]] <= lock)[0]
                        if len(w): d += lock - XC - fin[k]
                rec.update(fired=True, delta=d, nrm=nrm)
            rows.append(rec)
pd.DataFrame(rows).to_csv(sys.argv[2], index=False); print(len(rows))
