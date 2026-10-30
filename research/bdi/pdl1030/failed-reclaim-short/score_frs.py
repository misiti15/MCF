"""pdl1030/failed-reclaim-short: score the PLAN.md rows (TRAIN / VALID only) on the structure-exit cache.
Short the failed PDL reclaim of the CWT14 p05 long signal. Costs as swarm15 / top5_1028 sim.
HOLD months and the locked block are never loaded. Educational only - not financial advice.
"""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
os.environ["NUMBA_CACHE_DIR"] = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030/failed-reclaim-short/numba_cache"
from pathlib import Path
import numpy as np, pandas as pd, numba
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), "/home/user/MCF", "/home/user/MCF/research/history2y"]
import se_score as SE  # verbatim copy of pdl1030/structure-exit/score.py (load / sim2 / stats)
from se_score import _mult  # noqa
from mcf.research import gates  # noqa
import lib  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SE.C = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030/structure-exit/cache")
TF = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030/tape-flip/cache")
MONTHS = SE.MONTHS
N_PRIOR, N_ME = 121512, 17
BAR = max(0.9 * max(1.5, math.sqrt(2 * math.log(N_PRIOR + 3 * N_ME))), 1.35)
PAR = dict(train=-0.0677, valid=-0.0675)


@numba.njit(cache=True)
def trig(off, H, L, Cc, TOD, lvl, start_ok):
    """First bar after the signal bar (path row 0) with tod <= 1500 and close < lvl. Returns (k abs index or -1, RH)."""
    n = len(lvl)
    kk = np.full(n, -1, np.int64)
    rh = np.full(n, np.nan)
    for q in range(n):
        a, b = off[q], off[q + 1]
        m = H[a]
        for k in range(a + 1, b):
            if TOD[k] > 1500:
                break
            m = max(m, H[k])
            if Cc[k] < lvl[q]:
                kk[q] = k
                rh[q] = m
                break
    return kk, rh


@numba.njit(cache=True)
def sim_short(off, H, L, Cc, TOD, K, tier, stop0, tgt, spx, be, sof):
    """Short from the close of path row K[q] to the end of trade q's path. Stop first (on the high), then target (on the
    low, limit, free), then scale-out at spx (stop to entry), then break-even after MFE >= be R. Flatten at the last close.
    Codes 1 target, 2 stop, 3 moved stop, 6 flatten. r in units of R = stop0 - e."""
    n = len(K)
    r = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    for q in range(n):
        k0 = K[q]
        if k0 < 0:
            continue
        b = off[q + 1]
        e = Cc[k0]
        R = stop0[q] - e
        if not (R > 0):
            continue
        ec = (0.01 + e * 1e-4) * _mult(TOD[k0])
        stop = stop0[q]
        scaled = False
        mfe = 0.0
        x, cd = 0.0, 0
        for k in range(k0 + 1, b):
            if H[k] >= stop:
                x = stop
                cd = 2 if stop > e + 0.999 * R else 3
                break
            mfe = max(mfe, (e - L[k]) / R)
            if tgt[q] > 0 and L[k] <= tgt[q]:
                x, cd = tgt[q], 1
                break
            if be[q] > 0 and mfe >= be[q]:
                stop = min(stop, e)
            if (not scaled) and spx[q] > 0 and L[k] <= spx[q]:
                scaled = True
                stop = min(stop, e)
        if cd == 0:
            x, cd = Cc[b - 1], 6
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0))
        g = (e - x) / R
        if scaled:
            g = sof * (e - spx[q]) / R + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - tier[q] * (ec + xc) / R
        code[q] = cd
    return r, code


def context():
    cs = []
    for m in MONTHS:
        c = lib.load_context(m)
        c = c[c["date"].astype(str) <= "2026-09-15"]
        cs.append(c)
    c = pd.concat(cs, ignore_index=True)
    d = c["date"].astype(str)
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not ((d >= "2026-04-01") & (d <= "2026-06-30")).any()
    return {(a, int(b)): (x, y) for a, b, x, y in zip(d, c["tod"], c["spy_fo"], c["breadth"])}


def prep(T, P, CTX):
    """Per-signal trigger fields for TP / TL (all known at the trigger bar's close)."""
    out = {}
    pdl, lod = T["pdl"].to_numpy(float), T["lod"].to_numpy(float)
    for name, lvl in (("TP", pdl), ("TL", lod)):
        k, rh = trig(P["off"], P["H"], P["L"], P["C"], P["TOD"], lvl, 0)
        ok = k >= 0
        ks = np.where(ok, k, 0)
        e = np.where(ok, P["C"][ks], np.nan)
        tk = np.where(ok, P["TOD"][ks], -1)
        bars = np.where(ok, k - P["off"][:-1], -1)
        dates = T["date"].astype(str).to_numpy()
        sf = np.array([CTX.get((d, int(t)), (np.nan, np.nan))[0] if o else np.nan for d, t, o in zip(dates, tk, ok)])
        br = np.array([CTX.get((d, int(t)), (np.nan, np.nan))[1] if o else np.nan for d, t, o in zip(dates, tk, ok)])
        out[name] = dict(k=k, rh=rh, e=e, tod=tk, bars=bars, spy_fo=sf, breadth=br)
    return out


def run_short(T, P, TR, cfg):
    tr = TR[cfg["trig"]]
    A = T["A"].to_numpy(float)
    e = tr["e"]
    st = cfg["stop"]
    if st == "F25":
        stop = e + 0.25 * A
    elif st == "F75":
        stop = e + 0.75 * A
    elif st == "SR":
        stop = np.maximum(tr["rh"] + 0.02 * A, e + 0.10 * A)
    R = stop - e
    n = len(T)
    ex = cfg.get("exit", "default")
    tgt, spx, be = np.full(n, -1.0), np.full(n, -1.0), np.zeros(n)
    if ex == "default":
        tgt, spx = e - 0.5 * R, e - 0.25 * R
    elif ex == "B1":
        tgt = e - 1.0 * R
    elif ex == "B2":
        tgt = e - 2.0 * R
    elif ex == "B3":
        pass
    elif ex == "B4":
        be = np.ones(n)
    tgt = np.where(np.isfinite(tgt), tgt, -1.0)
    spx = np.where(np.isfinite(spx), spx, -1.0)
    K = np.where(np.isfinite(e) & (tr["k"] >= 0), tr["k"], -1)
    tier = T["tier"].to_numpy(float)
    # gates (known at the trigger close)
    g = cfg.get("gate", [])
    keep = np.ones(n, bool)
    with np.errstate(invalid="ignore"):
        cst = ((0.01 + e * 1e-4) * np.array([_mult(int(t)) if t >= 0 else 1.0 for t in tr["tod"]]) + 0.01 + e * 1e-4) * tier / R
        if "cost5" in g:
            keep &= cst <= 0.05
        if "spy" in g:
            keep &= tr["spy_fo"] < 0
        if "br" in g:
            keep &= tr["breadth"] < 0.5
        if "fast" in g:
            keep &= (tr["bars"] >= 1) & (tr["bars"] <= 6)
    K = np.where(keep, K, -1)
    r, code = sim_short(P["off"], P["H"], P["L"], P["C"], P["TOD"], K.astype(np.int64), tier,
                        np.where(np.isfinite(stop), stop, 0.0), tgt, spx, be, 0.5)
    o = T[["date", "symbol", "split", "month", "spy_day"]].copy()
    o["r"], o["code"], o["Ru_A"] = r, code, R / A
    o["etod"] = tr["tod"]
    return o[np.isfinite(r)]


def verdict(st):
    return bool(st["t_tv"] is not None and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0
                and st["avg_valid"] > 0 and st["avg_train"] > PAR["train"] and st["avg_valid"] > PAR["valid"]
                and st["per_session"] >= 25)


def main():
    rows, count = [], 0
    data = {s: SE.load(s) for s in ("p05", "p10")}
    nsess = data["p05"][0]["date"].nunique()
    CTX = context()
    TRs = {s: prep(*data[s], CTX) for s in data}
    print("sessions", nsess, {s: {k: int((v["k"] >= 0).sum()) for k, v in TRs[s].items()} for s in TRs}, flush=True)
    outs = {}

    def record(id_, setup, rule, o, cfg):
        nonlocal count
        count += 1
        st = SE.stats(o, nsess)
        st.update(id=id_, setup=setup, rule=rule, cfg=json.dumps(cfg), passes=verdict(st))
        rows.append(st)
        outs[id_] = o
        print(id_, setup, rule, {k: st[k] for k in ("n_tv", "avg_train", "avg_valid", "t_tv", "wf_pct", "per_session",
                                                   "up_day_r", "down_day_r", "ex_best", "best_share", "stop_pct",
                                                   "tgt_pct", "Ru_A_med")}, flush=True)
        return st

    def score_short(id_, setup, cfg, rule):
        T, P = data[setup]
        return record(id_, setup, rule, run_short(T, P, TRs[setup], cfg), cfg)

    p05 = record("P05", "p05", "parent p05 long", SE.run(*data["p05"], dict(stop="parent", tgt="parent", so=True)), {})
    p10 = record("P10", "p10", "parent p10 long", SE.run(*data["p10"], dict(stop="parent", tgt="parent")), {})
    par_ok = abs(p05["avg_train"] - PAR["train"]) <= 0.005 and abs(p05["avg_valid"] - PAR["valid"]) <= 0.005 \
        and abs(p10["avg_tv"] - (-0.0880)) <= 0.005
    print("PARITY parents", par_ok, flush=True)
    if not par_ok:
        pd.DataFrame(rows).to_csv(HERE / "results.csv", index=False)
        return
    A = {}
    for a, cfg, rule in [("A1", dict(trig="TP", stop="F25"), "short first close < PDL; stop e+0.25A; 0.5R tgt, half at 0.25R"),
                         ("A2", dict(trig="TL", stop="F25"), "short first close < signal LOD; stop e+0.25A; default exits"),
                         ("A3", dict(trig="TP", stop="SR"), "short first close < PDL; stop reclaim high+0.02A (>=0.10A); default exits"),
                         ("A4", dict(trig="TL", stop="SR"), "short first close < signal LOD; stop reclaim high+0.02A; default exits"),
                         ("A5", dict(trig="TL", stop="F75"), "short first close < signal LOD; stop e+0.75A; default exits")]:
        A[a] = (score_short(a, "p05", cfg, rule), cfg)
    # short-sim parity vs tape-flip Sb leg (top5_1028 sim, side -1), same trades
    tf = pd.concat([pd.read_parquet(TF / f"t_{m}.parquet") for m in MONTHS], ignore_index=True)
    tf = tf[(tf.setup == "p05") & (tf.leg == "Sb") & np.isfinite(tf.r)]
    tf["date"] = tf["date"].astype(str)
    a1 = outs["A1"].assign(date=outs["A1"]["date"].astype(str))
    mg = a1.merge(tf[["date", "symbol", "r"]], on=["date", "symbol"], suffixes=("", "_tf"))
    sp_ok = abs(mg.r.mean() - mg.r_tf.mean()) <= 0.005 and abs(len(a1) - len(tf)) <= 0.01 * len(tf)
    print("PARITY short-sim", sp_ok, "n mine", len(a1), "n tf", len(tf), "matched", len(mg), "mean mine", round(mg.r.mean(), 4),
          "mean tf", round(mg.r_tf.mean(), 4), "exact share", round(float((abs(mg.r - mg.r_tf) < 1e-6).mean()), 3), flush=True)
    if not sp_ok:
        pd.DataFrame(rows).to_csv(HERE / "results.csv", index=False)
        return
    astar = max(A, key=lambda k: A[k][0]["avg_train"])
    print("A*", astar, flush=True)
    E = {astar: A[astar]}
    for b, ex, rule in [("B1", "B1", "target 1R, no scale"), ("B2", "B2", "target 2R, no scale"),
                        ("B3", "B3", "no target, stop only, flatten 15:55"),
                        ("B4", "B4", "no target, stop to entry after MFE >= 1R, flatten 15:55")]:
        cfg = {**A[astar][1], "exit": ex}
        E[b] = (score_short(b, "p05", cfg, f"{astar} + {rule}"), cfg)
    estar = max(E, key=lambda k: E[k][0]["avg_train"])
    print("E*", estar, flush=True)
    base = E[estar][1]
    Cr = {}
    for c_, gl, rule in [("C1", ["cost5"], "round-trip cost <= 5% of R"), ("C2", ["spy"], "SPY below its open at trigger"),
                         ("C3", ["br"], "breadth < 0.5 at trigger")]:
        cfg = {**base, "gate": gl}
        Cr[c_] = (score_short(c_, "p05", cfg, f"{estar} + {rule}"), cfg)
    tape = "spy" if Cr["C2"][0]["avg_train"] >= Cr["C3"][0]["avg_train"] else "br"
    cfg = {**base, "gate": ["cost5", tape]}
    Cr["C4"] = (score_short("C4", "p05", cfg, f"{estar} + cost <= 5% R + {'SPY below open' if tape == 'spy' else 'breadth < 0.5'}"), cfg)
    cfg = {**base, "gate": ["fast"]}
    Cr["C5"] = (score_short("C5", "p05", cfg, f"{estar} + trigger within 6 bars of the signal"), cfg)
    allr = {**A, **{k: v for k, v in E.items() if k.startswith("B")}, **Cr}
    elig = {k: v for k, v in allr.items() if v[0]["per_session"] >= 25}
    best = max(elig, key=lambda k: elig[k][0]["avg_train"])
    print("BEST", best, flush=True)
    score_short("D1", "p10", elig[best][1], f"BEST ({best}) on the p10 signal pool")
    print("count", count, "bar", round(BAR, 3), flush=True)
    Rr = pd.DataFrame(rows)
    Rr.to_csv(HERE / "results.csv", index=False)
    print(Rr[["id", "setup", "n_tv", "avg_train", "avg_valid", "t_tv", "wf_pct", "per_session", "up_day_r", "down_day_r",
              "ex_best", "best_share", "stop_pct", "tgt_pct", "Ru_A_med", "passes"]].to_string())


if __name__ == "__main__":
    main()
