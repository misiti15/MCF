"""ARENASTARS-1127 Part C: Primary book (E5 = e4nb with a 5th slot), P4 lineup vs ADD-G (candidate added, slot 4 =
lowest priority on same-minute ties) and REP-X-G (candidate replaces L3 / RW3 / RW5), BASE and LO, FIT / CHECK / T2.
Controls: ADD vs 100 size-matched random adds (RND pool lots, same count per day as the candidate's lots, same side /
window / geometry); REP vs X-out. Usage (cwd repo): python as_book.py W OUTDIR. Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/arenastars_1127")
import e5nb as E  # noqa: E402

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "NM-ETF-late-dip-di-long"]
SHORTN = {"L3": 0, "RW3": 1, "RW5": 2}
NR = 100


def load():
    C = pd.read_parquet(W / "cand.parquet")
    C["date"] = C.date.astype(str)
    E.no_locked(C.date.unique())
    C["si"] = C.setup.map({s: i for i, s in enumerate(P4)}).fillna(4).astype(int)
    C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
    C["sym"] = C.groupby("date").symbol.transform(lambda s: pd.factorize(s)[0])
    days = C.date.drop_duplicates().tolist()
    st = np.r_[np.flatnonzero(C.date.ne(C.date.shift()).to_numpy()), len(C)].astype(np.int64)
    PATH = np.load(W / "paths.npy").astype(np.float64)
    A = dict(si=C.si.to_numpy(np.int64), sym=C.sym.to_numpy(np.int64), side=C.side.to_numpy(np.float64),
             ent=C.entry.to_numpy(np.float64), risk=C.risk.to_numpy(np.float64), lc=C.lcost.to_numpy(np.float64),
             em=C.em.to_numpy(np.int64), xm=C.xm.to_numpy(np.int64), rr=C.r.to_numpy(np.float64),
             off=C.off.to_numpy(np.int64), n=C.n.to_numpy(np.int64))
    return C, days, st, PATH, A


def ptest(d):
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 0 else 0.0


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    C, DAYS, ST, PATH, A = load()
    PER = np.array([C.per.iloc[ST[i]] for i in range(len(DAYS))])
    ALL = np.arange(len(DAYS))
    isP4 = C.si.to_numpy() < 4
    setup = C.setup.to_numpy()
    rng = np.random.default_rng(1127)
    rows, out = [], {"lots": C.setup.value_counts().to_dict()}
    for cx, lo in (("BASE", False), ("LO", True)):
        Rk, Nk, TK = E.run(A, ST, PATH, ALL, isP4, lo)
        keep = Rk.sum(1)
        out[f"keep_{cx}"] = {p: round(float(keep[PER == p].mean()), 3) for p in ("FIT", "CHECK", "T2")}
        print(cx, "keep R/day", out[f"keep_{cx}"], flush=True)
        xout = {}
        for xn, xi in SHORTN.items():
            m = isP4 & (C.si.to_numpy() != xi)
            xout[xn] = E.run(A, ST, PATH, ALL, m, lo)[0].sum(1)
        for tag in ("G05", "G07", "G37"):
            g = setup == tag
            Ra, Na, TA = E.run(A, ST, PATH, ALL, isP4 | g, lo)
            add = Ra.sum(1)
            # random adds: per day, the candidate's lot count drawn from the day's RND pool
            pool = setup == "RND-" + tag
            cnt = pd.Series(C.date[g]).value_counts()
            pidx = pd.Series(np.flatnonzero(pool)).groupby(C.date.to_numpy()[pool]).apply(np.asarray).to_dict()
            rnd = np.zeros((NR, len(DAYS)))
            for i in range(NR):
                km = isP4.copy()
                for d, k in cnt.items():
                    ix = pidx.get(d)
                    if ix is None:
                        continue
                    km[rng.choice(ix, min(k, len(ix)), replace=False)] = True
                rnd[i] = E.run(A, ST, PATH, ALL, km, lo)[0].sum(1)
            for p in ("FIT", "CHECK", "T2"):
                q = PER == p
                d = (add - keep)[q]
                rd = (rnd[:, q] - keep[q]).mean(1)
                tot = d.sum(); bi = int(np.argmax(d))
                own = Ra[q, 4]
                rows.append(dict(ctx=cx, config=f"ADD-{tag}", period=p, days=int(q.sum()), ref="keep", dR=d.mean(), t=ptest(d),
                                 best_share=(d[bi] / tot) if tot > 0 else np.nan, dR_wo_best=np.delete(d, bi).mean(),
                                 own_R_day=own.mean(), own_lots_day=Na[q, 4].mean(), ctrl_mean=rd.mean(),
                                 ctrl_p95=np.percentile(rd, 95), pct=(rd < d.mean()).mean() * 100,
                                 p4_spill_day=(Ra[q, :4].sum(1) - keep[q]).mean()))
            for xn, xi in SHORTN.items():
                m = (isP4 & (C.si.to_numpy() != xi)) | g
                Rr, Nr, _ = E.run(A, ST, PATH, ALL, m, lo)
                rep = Rr.sum(1)
                for p in ("FIT", "CHECK", "T2"):
                    q = PER == p
                    d = (rep - keep)[q]; d2 = (rep - xout[xn])[q]
                    tot = d.sum(); bi = int(np.argmax(d))
                    rows.append(dict(ctx=cx, config=f"REP-{xn}-{tag}", period=p, days=int(q.sum()), ref="keep", dR=d.mean(),
                                     t=ptest(d), best_share=(d[bi] / tot) if tot > 0 else np.nan,
                                     dR_wo_best=np.delete(d, bi).mean(), own_R_day=Rr[q, 4].mean(),
                                     own_lots_day=Nr[q, 4].mean(), dR_vs_xout=d2.mean(), t_vs_xout=ptest(d2),
                                     xout_dR=(xout[xn] - keep)[q].mean()))
            print(cx, tag, "done", flush=True)
    df = pd.DataFrame(rows)
    def passed(r):
        if r.config.startswith("ADD"):
            return bool(r.dR > 0 and r.t >= 2.8 and r.dR > r.ctrl_p95 and (r.best_share < 0.25))
        return bool(r.dR > 0 and r.t >= 2.8 and r.dR_vs_xout > 0 and r.t_vs_xout >= 2.0)
    df["bar"] = df.apply(passed, axis=1)
    df.round(4).to_csv(OUT / "book_results.csv", index=False)
    ver = {}
    for cfg, g in df[df.period.isin(["CHECK", "T2"])].groupby("config"):
        ver[cfg] = bool(g.bar.all())
    out["config_pass"] = ver
    json.dump(out, open(OUT / "book_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(df[df.period != "FIT"].round(3).to_string())
    print(ver)
