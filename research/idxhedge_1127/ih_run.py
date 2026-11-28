"""IDXHEDGE-1127 (PREREG.md): one-shot SPY/QQQ long hedge sleeve on Primary's E4 bench book (LO main, BASE alongside).
12 configs = trigger {A, B6, B10} x {SPY, QQQ} x k {0.25, 0.5}; controls C-RAND (500), C-CONST, C-ALWAYS; IDX-L costs,
LR8-IDX and stress alongside. Usage (cwd repo): python research/idxhedge_1127/ih_run.py W IDXDIR OUTDIR.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/cfprimary_1127"); sys.path.insert(0, "research/idxhedge_1127")
import e4nb as E  # noqa: E402
import ih_e4 as X  # noqa: E402

W, IX, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
NR, SEED = 500, 1127
SIDE_BP, SEC, CAT, TAF = 1e-4, 20.60e-6, 0.00005, 0.000195

C, DAYS, ST, PATH, A = E.load(W)
E.no_locked(DAYS)
PER = np.array([C.per.iloc[ST[i]] for i in range(len(DAYS))])
BB = (C.side * C.beta * 0.01 * C.entry / C.risk).to_numpy(np.float64)
meta = pd.read_csv(IX / "idx_meta.csv"); meta["date"] = meta.date.astype(str)
E.no_locked(meta.date)
SPY = np.load(IX / "spy.npy"); QQQ = np.load(IX / "qqq.npy")
IPOS = {d: i for i, d in enumerate(meta.date)}
miss = [d for d in DAYS if d not in IPOS]
print("bench days", len(DAYS), "missing index days", len(miss), miss[:5], flush=True)
assert len(miss) <= 3
fitgd = meta.set_index("date").gd_share.reindex([d for d, p in zip(DAYS, PER) if p == "FIT"]).dropna()
Q67 = float(np.quantile(fitgd, 0.67))
print("q67 gd_share (FIT) = %.4f on %d FIT days" % (Q67, len(fitgd)), flush=True)


def day_idx(d):
    i = IPOS.get(d)
    if i is None:
        return None
    r = meta.iloc[i]
    return dict(S=SPY[i, 0], V=SPY[i, 1], Q=QQQ[i], flat=int(r.close_min) - 6 - 570, last=int(r.close_min) - 60 - 570,
                gd=r.gd_share, bq=float(r.beta_qqq))


IDXD = [day_idx(d) for d in DAYS]
for g in IDXD:   # next bar (strictly after j) with SPY close < VWAP; 999 if none
    if g is None:
        continue
    below = g["S"] < g["V"]; nb = np.full(391, 999, np.int64); nxt = 999
    for j in range(389, -1, -1):
        nb[j] = nxt
        if below[j]:
            nxt = j
    g["nb"] = nb


def trig(cfg, g, TB, EE):
    """trigger bar index (m - 570) or -1."""
    S, V = g["S"], g["V"]
    if cfg["t"] == "A":
        if not (g["gd"] >= Q67):
            return -1
        for i in range(60, g["last"] + 1):
            if S[i] > V[i] and S[i - 1] <= V[i - 1] and EE[i] < 0:
                return i
        return -1
    for i in range(15, g["last"] + 1):
        if TB[i] <= -cfg["X"] + 1e-12 and S[i] > V[i] and EE[i] < 0:
            return i
    return -1


def sleeve(g, i, notional_fn, inst, delay=1, vwexit=True, extra_bp=0.0):
    """returns gross, cost_idxl, cost_lr8, notional, bars held, fill bar."""
    P = g["S"] if inst == "SPY" else g["Q"]
    fi = i + delay; flat = g["flat"]
    if fi >= flat:
        return None
    if vwexit:
        j = g["nb"][fi]
        xi = min(j + delay, flat) if j < 999 else flat
    else:
        xi = flat
    Nn = notional_fn(i, fi)
    if Nn <= 0:
        return None
    pf, px = P[fi], P[xi]
    gross = Nn * (px / pf - 1)
    sh = Nn / pf   # share count in R-units (same both legs)
    c_l = Nn * SIDE_BP + Nn * px / pf * SIDE_BP + SEC * Nn * px / pf + TAF * sh + 2 * CAT * sh + extra_bp * 1e-4 * (Nn + Nn * px / pf)
    c_8 = (2 * (0.01 + pf * 1e-4) + 0.02) * sh
    return gross, c_l, c_8, Nn, xi - fi, fi


CFGS = []
for t, X_ in (("A", None), ("B6", 6.0), ("B10", 10.0)):
    for inst in ("SPY", "QQQ"):
        for k in (0.25, 0.5):
            CFGS.append(dict(id=f"{t}-{inst}-k{k}", t=t[0], X=X_, inst=inst, k=k))


def w5(x):
    return np.sort(x)[:5].mean()


def metrics(book, sl, n_days):
    """book: daily R (Primary alone); sl: daily sleeve net R (0 on no-hedge days)."""
    nb = book + sl
    hd = sl != 0
    s = sl[hd]
    tot = s.sum()
    t = s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std(ddof=1) > 0 else np.nan
    wi = np.argsort(book)[:5]
    s5 = sl[wi]; pos5 = s5[s5 > 0]
    return dict(n=n_days, hedge_days=int(hd.sum()), book=book.mean(), new=nb.mean(), dR=sl.mean(), dR_yr=sl.mean() * 252,
                sleeve_t=t, sleeve_per_hday=s.mean() if len(s) else np.nan, hit=(s > 0).mean() if len(s) else np.nan,
                w5_ref=w5(book), w5_new=w5(nb), w5_impr=(w5(nb) - w5(book)) / abs(w5(book)),
                le10_ref=int((book <= -10).sum()), le10_new=int((nb <= -10).sum()),
                red_ref=(book < 0).mean() * 21, red_new=(nb < 0).mean() * 21,
                floor_ref=pd.Series(book).rolling(20).sum().min(), floor_new=pd.Series(nb).rolling(20).sum().min(),
                best_share=(s.max() / tot) if tot > 0 else np.nan,
                wo_best=(tot - s.max()) / max(len(s) - 1, 1) if len(s) else np.nan,
                tail_best_share=(pos5.max() / s5.sum()) if s5.sum() > 0 else np.nan, sleeve_on_w5=s5.sum(),
                w20_share=float(np.isin(np.flatnonzero(hd), np.argsort(book)[:max(int(0.2 * len(book)), 1)]).mean()) if hd.any() else np.nan)


if __name__ == "__main__":
    res = {"q67": Q67, "configs": len(CFGS)}
    # extended engine + parity vs e4nb on every day
    books = {}
    for cx, lo in (("LO", True), ("BASE", False)):
        R0, _, _ = E.run(A, ST, PATH, np.arange(len(DAYS)), np.ones(len(C), bool), lo)
        R, TB, EE, ES = X.run_days(ST, A["si"], A["sym"], A["side"], A["ent"], A["risk"], A["lc"], A["em"], A["xm"],
                                   A["rr"], A["off"], A["n"], BB, lo, PATH)
        par = float(np.abs(R - R0).max()); res[f"parity_{cx}"] = par
        print(cx, "parity max |dR| by setup-day", par, "TB end vs R", float(np.abs(TB[:, -1] - R.sum(1)).max()), flush=True)
        assert par < 1e-9
        books[cx] = (R, TB, EE, ES)
    rows, prs, daily = [], [], {}
    for cx, (R, TB, EE, ES) in books.items():
        book = R.sum(1)
        for cfg in CFGS:
            inst, k = cfg["inst"], cfg["k"]
            out = {v: np.zeros(len(DAYS)) for v in ("gross", "cl", "c8", "net", "stress", "net8", "nmin", "notional")}
            alloc = np.zeros((len(DAYS), 4)); tbar = np.full(len(DAYS), -1)
            for d, g in enumerate(IDXD):
                if g is None:
                    continue
                i = trig(cfg, g, TB[d], EE[d])
                if i < 0:
                    continue
                bI = 1.0 if inst == "SPY" else g["bq"]
                nf = lambda i_, fi_: k * (-EE[d, i_]) / 0.01 / bI  # noqa: E731
                r = sleeve(g, i, nf, inst)
                if r is None:
                    continue
                rs = sleeve(g, i, nf, inst, delay=2, extra_bp=2.0)
                gross, cl, c8, Nn, held, fi = r
                tbar[d] = i
                out["gross"][d] = gross; out["cl"][d] = cl; out["c8"][d] = c8; out["net"][d] = gross - cl
                out["net8"][d] = gross - c8; out["nmin"][d] = Nn * held; out["notional"][d] = Nn
                out["stress"][d] = (rs[0] - rs[1]) if rs is not None else 0.0
                alloc[d] = (gross - cl) * ES[d, :, i] / EE[d, i]
            daily[(cx, cfg["id"])] = out
            for p in ("FIT", "CHECK", "T2"):
                ix = np.flatnonzero(PER == p); nd = len(ix)
                m = metrics(book[ix], out["net"][ix], nd)
                ms = metrics(book[ix], out["stress"][ix], nd); m8 = metrics(book[ix], out["net8"][ix], nd)
                row = dict(ctx=cx, cfg=cfg["id"], per=p, **m, gross_day=out["gross"][ix].mean(),
                           cost_yr=out["cl"][ix].mean() * 252, cost8_yr=out["c8"][ix].mean() * 252,
                           dR_stress=ms["dR"], w5_stress=ms["w5_new"], dR_lr8=m8["dR"], w5_lr8=m8["w5_new"],
                           avg_notional=out["notional"][ix][out["notional"][ix] > 0].mean() if (out["notional"][ix] > 0).any() else 0,
                           setup_alloc_month=list(alloc[ix].sum(0) / nd * 21),
                           avg_trig_min=float(np.mean(tbar[ix][tbar[ix] >= 0]) + 570) if (tbar[ix] >= 0).any() else np.nan)
                if p != "FIT" and m["hedge_days"] > 0:
                    # C-CONST: constant notional, same notional-minutes, 10:30 bar close -> flat
                    tot_nmin = out["nmin"][ix].sum()
                    span = np.array([IDXD[d]["flat"] - 60 if IDXD[d] is not None else 0 for d in ix])
                    Nc = tot_nmin / max(span.sum(), 1)
                    cc = np.zeros(nd); ca = np.zeros(nd)
                    for jj, d in enumerate(ix):
                        g = IDXD[d]
                        if g is None:
                            continue
                        r = sleeve(g, 59, lambda a_, b_: Nc, inst, vwexit=False)
                        if r is not None:
                            cc[jj] = r[0] - r[1]
                        if EE[d, 60] < 0:
                            bI = 1.0 if inst == "SPY" else g["bq"]
                            r = sleeve(g, 60, lambda a_, b_: k * (-EE[d, 60]) / 0.01 / bI, inst, vwexit=False)
                            if r is not None:
                                ca[jj] = r[0] - r[1]
                    mc = metrics(book[ix], cc, nd); ma = metrics(book[ix], ca, nd)
                    row.update(const_dR=mc["dR"], const_w5=mc["w5_new"], const_le10=mc["le10_new"], const_notional=Nc,
                               always_dR=ma["dR"], always_w5=ma["w5_new"], always_le10=ma["le10_new"])
                    # C-RAND
                    elig = []
                    for d in ix:
                        g = IDXD[d]
                        if g is None:
                            elig.append(None); continue
                        bars = np.flatnonzero(EE[d, 60:g["last"] + 1] < 0) + 60
                        elig.append(bars if len(bars) else None)
                    pool = [jj for jj, e in enumerate(elig) if e is not None]
                    gr = np.random.default_rng(SEED + len(rows))
                    rd, rw = np.zeros(NR), np.zeros(NR)
                    for q in range(NR):
                        sl = np.zeros(nd)
                        for jj in gr.choice(pool, min(m["hedge_days"], len(pool)), replace=False):
                            d = ix[jj]; g = IDXD[d]; i = int(gr.choice(elig[jj]))
                            bI = 1.0 if inst == "SPY" else g["bq"]
                            r = sleeve(g, i, lambda a_, b_: k * (-EE[d, i]) / 0.01 / bI, inst)
                            if r is not None:
                                sl[jj] = r[0] - r[1]
                        rd[q] = sl.mean(); rw[q] = w5(book[ix] + sl) - m["w5_ref"]
                    wimp = m["w5_new"] - m["w5_ref"]
                    row.update(rand_dR_med=float(np.median(rd)), rand_w5_p90=float(np.percentile(rw, 90)),
                               rand_w5_med=float(np.median(rw)), pct_dR=float((rd < m["dR"]).mean() * 100),
                               pct_w5=float((rw < wimp).mean() * 100))
                    ok = [m["dR"] >= -0.20 and ms["dR"] >= -0.25,
                          m["w5_impr"] >= 0.10 and m["le10_new"] <= m["le10_ref"],
                          m["red_new"] - m["red_ref"] <= 0.5,
                          wimp > row["rand_w5_p90"] and m["dR"] >= row["rand_dR_med"],
                          m["w5_new"] > mc["w5_new"] and m["dR"] >= mc["dR"] - 0.05,
                          (not np.isnan(m["tail_best_share"])) and m["tail_best_share"] < 0.5]
                    row.update({f"bar{j + 1}": bool(v) for j, v in enumerate(ok)}, all_bar=bool(all(ok)),
                               full=bool(all(ok) and m["dR"] > 0 and (m["sleeve_t"] or 0) >= 2.23))
                rows.append(row)
                print({kk: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for kk, v in row.items()
                       if kk != "setup_alloc_month"}, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "results.csv", index=False)
    verdict = {}
    for cfg in CFGS:
        sub = df[(df.cfg == cfg["id"]) & (df.ctx == "LO") & (df.per != "FIT")]
        if len(sub) < 2 or sub.hedge_days.min() == 0:
            verdict[cfg["id"]] = "FAIL"; continue
        if sub.full.all():
            verdict[cfg["id"]] = "PASS"
        elif sub.all_bar.all():
            verdict[cfg["id"]] = "PASS-REMEDY"
        elif (sub.bar1 & sub.bar2).all():
            verdict[cfg["id"]] = "LEAD"
        else:
            verdict[cfg["id"]] = "FAIL"
    res["verdict"] = verdict
    for cx, (R, TB, EE, ES) in books.items():
        pd.DataFrame(R, columns=E.SETUPS).assign(date=DAYS, per=PER).to_parquet(OUT / f"book_{cx}.parquet")
    pd.DataFrame({f"{cx}|{c}": v["net"] for (cx, c), v in daily.items()}).assign(date=DAYS, per=PER).to_parquet(OUT / "sleeve_net.parquet")
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
