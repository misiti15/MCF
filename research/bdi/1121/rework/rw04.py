"""Rework BEG-04 (PLAN.md): the beginner runner's own functions (research/beginner_1120/BEG-04-quiet-gap-fade/run.py:
cand_days, sym_job; bench10 add_r / book / stats) with this folder's variants, all variants in one pass over the
1-minute bars (each symbol's bars loaded once). T1 only (day table rebuilt by build04days.py).
    python rw04.py fit|check NAME [NAME ...]          -> beg04/results.json, ../scratch/beg04/bk_<name>_<part>.parquet
Educational only - not financial advice."""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[3] / "research/beginner_1120/BEG-04-quiet-gap-fade"
sys.path.insert(0, str(SRC))
import run as R  # noqa: E402
B, G = R.B, R.G
SCR = HERE.parent / "scratch"
R.DAYS = {"t1": SCR / "beg02w/days_t1.parquet"}
R.ETB = SCR / "etb_rate.parquet"
V = {"base": {}, **json.loads((HERE / "beg04/variants.json").read_text())}
_C = {}


def _bars(test, sym, _orig=R.load_bars):
    if _C.get("k") != sym:
        _C["k"], _C["b"] = sym, _orig(test, sym)
    return _C["b"]


R.load_bars = _bars


def job(a):
    sym, per = a
    return {v: R.sym_job(("t1", sym, rows, p, None, None, {})) for v, (rows, p) in per.items()}


if __name__ == "__main__":
    part, names = sys.argv[1], sys.argv[2:]
    P = {v: dict(G.P, **{k: x for k, x in V[v].items() if k in G.P}) for v in names}
    D = {v: R.cand_days("t1", P[v]) for v in names}
    for v in names:
        D[v] = D[v][B.half(D[v].date) == part]
    syms = sorted(set().union(*[set(d.symbol) for d in D.values()]))
    jobs = []
    for s in syms:
        per = {}
        for v in names:
            g = D[v][D[v].symbol == s]
            if len(g):
                per[v] = (g.to_dict("records"), P[v])
        jobs.append((s, per))
    out = {v: [] for v in names}
    with Pool(3) as pool:
        for res in pool.imap_unordered(job, jobs, chunksize=4):
            for v, rows in res.items():
                out[v].extend(rows)
    etb = pd.read_parquet(R.ETB).rate
    spy1 = B.spy_t1(); spy1 = spy1[spy1.index <= "2026-11-04"]
    n = int((B.half(pd.Series(spy1.index)) == part).sum())
    rp = HERE / "beg04/results.json"
    allres = json.loads(rp.read_text()) if rp.exists() else {}
    (SCR / "beg04").mkdir(parents=True, exist_ok=True)
    for v in names:
        T = pd.DataFrame(out[v], columns=R.COLS)
        B.no_locked(T.date.unique())
        T["setup"] = "BEG-04"
        T = B.add_r(T)
        bk = B.book(T, B.TESTING_RULES, etb)
        st = B.stats(bk, n, spy1)
        st["raw_trades"] = int(len(T))
        bk.to_parquet(SCR / "beg04" / f"bk_{v}_{part}.parquet")
        allres[f"{v}_{part}"] = st
        print(v, part, json.dumps({k: st.get(k) for k in ("trades", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day",
              "best_day_share", "total_r", "total_r_per_session", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat",
              "avg_r_spy_down")}, default=float), flush=True)
    rp.write_text(json.dumps(allres, indent=1, default=float))
