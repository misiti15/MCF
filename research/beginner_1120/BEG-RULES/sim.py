"""BEG-RULES overlay simulation (PLAN.md). python sim.py PREP_DIR -> results.json here.
Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28")
MOM = {"BEG-01", "BEG-02", "BEG-03", "BEG-06", "BEG-09", "BEG-10"}
SLOT = {"BEG-05", "BEG-07"}
RULES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
NSEED = 200


def calendar(trading_days):
    c = json.loads((HERE / "calendar.json").read_text())
    td = pd.Series(sorted(trading_days))
    mo = td.str[:7]
    ism = set(td.groupby(mo).nth(0)) | set(td.groupby(mo).nth(2))
    return set(c["cpi"]) | set(c["nfp"]), ism, set(c["fomc"])


def simulate(T, rules, cal, primary=False):
    """T: trades of one account-day set (columns em, xm, setup, symbol, side, r, stopout, ...). Returns weight array."""
    cpinfp, ism, fomc = cal
    w = np.zeros(len(T))
    T = T.assign(ix_=np.arange(len(T)))
    for (acct, d), g in T.groupby(["acct", "date"], sort=False):
        g = g.sort_values(["em", "ix_"])
        real, streak, pause_until = 0.0, 0, -1
        n_ent, per_sym, stopped, latch = 0, {}, set(), {}
        open_ = []   # (xm, side, wr, setup, symbol, stopout, r)
        bl = []
        if "S6" in rules:
            if d in cpinfp: bl.append((510, 615))
            if d in ism: bl.append((595, 610))
            if d in fomc: bl.append((825, 870))
        for row in g.itertuples(index=False):
            em = row.em
            # process exits up to em
            open_.sort(key=lambda x: x[0])
            while open_ and open_[0][0] <= em:
                xm, side, wr, st, sy, so, r = open_.pop(0)
                real += wr
                latch[st] = latch.get(st, 0.0) + wr
                if r < 0:
                    streak += 1
                    if streak >= 3 and "S5" in rules:
                        pause_until = xm + 30
                        streak = 0
                else:
                    streak = 0
                if so:
                    stopped.add((sy, st))
            ok = True
            if "S1" in rules and real <= -3: ok = False
            if ok and "S2" in rules and (n_ent >= 6 or per_sym.get(row.symbol, 0) >= 2 or (row.symbol, row.setup) in stopped): ok = False
            if ok and "S3" in rules:
                if row.setup in SLOT: ok = 925 <= em <= 930
                else: ok = 590 <= em <= 930
            if ok and "S4" in rules:
                if len(open_) >= 4 or sum(1 for o in open_ if o[1] == row.side) >= 3: ok = False
            if ok and "S5" in rules and em < pause_until: ok = False
            if ok and bl and any(a <= em < b for a, b in bl): ok = False
            if ok and "S7" in rules and (primary or row.setup in MOM):
                if row.spy_tape != 0 and np.sign(row.spy_tape) != row.side: ok = False
            if ok and "S8" in rules:
                pct = abs(row.entry - row.stop) / row.entry
                if pct < 0.0025 or pct > 0.03 or (not np.isnan(row.dv5) and row.dv5 < 150e3): ok = False
            if ok and "MCF" in rules and (real <= -20 or latch.get(row.setup, 0.0) <= -2): ok = False
            if not ok:
                continue
            wt = 0.5 if ("S5" in rules and real >= 4) else 1.0
            w[row.ix_] = wt
            n_ent += 1
            per_sym[row.symbol] = per_sym.get(row.symbol, 0) + 1
            open_.append((row.xm, row.side, wt * row.r, row.setup, row.symbol, row.stopout, row.r))
    return w


def day_series(T, w, sessions):
    return pd.Series(w * T.r.to_numpy(), index=T.index).groupby(T.date).sum().reindex(sessions, fill_value=0.0)


def metrics(T, w, sessions):
    k = w > 0
    t = T[k]
    rr = (w * T.r.to_numpy())[k]
    ds = day_series(T, w, sessions)
    traded = pd.Series(rr, index=t.index).groupby(t.date).sum()
    o = {"trades": int(k.sum()), "total_r": round(float(rr.sum()), 2), "avg_r_session": round(float(ds.mean()), 4),
         "avg_r_trade": round(float(rr.mean()), 4) if k.any() else None, "worst_day": round(float(ds.min()), 2),
         "green_pct": round(float((traded > 0).mean()), 3) if len(traded) else None}
    if len(traded) > 1:
        best = traded.idxmax()
        o["avg_r_wo_best_day"] = round(float(rr[t.date.to_numpy() != best].mean()), 4)
        o["best_day_share"] = round(float(traded.max() / rr.sum()), 3) if rr.sum() > 0 else None
    return o


def paired(base_ds, ds):
    d = ds - base_ds
    n = len(d)
    t = float(d.mean() / (d.std(ddof=1) / np.sqrt(n))) if n > 1 and d.std(ddof=1) > 0 else 0.0
    return {"d_avg_r_session": round(float(d.mean()), 4), "d_total": round(float(d.sum()), 2), "t": round(t, 2),
            "helped": int((d > 1e-9).sum()), "hurt": int((d < -1e-9).sum())}


def random_ctrl(T, w_base, w, sessions, rng):
    """Remove (or halve) the same number of baseline trades per day at random; return the delta avg R/session per seed."""
    base_on = w_base > 0
    Tb = T[base_on]
    rb = Tb.r.to_numpy()
    nrem = pd.Series(((w_base > 0) & (w == 0)).astype(int), index=T.index).groupby(T.date).sum()
    nhalf = pd.Series(((w_base > 0) & (w == 0.5)).astype(int), index=T.index).groupby(T.date).sum()
    days = Tb.date.to_numpy()
    kr = pd.Series(days).map(nrem).fillna(0).to_numpy()
    kh = pd.Series(days).map(nhalf).fillna(0).to_numpy()
    codes, uniq = pd.factorize(days)
    out = []
    for _ in range(NSEED):
        key = rng.random(len(rb))
        order = np.lexsort((key, codes))
        rank = np.empty(len(rb), int)
        # rank within day
        starts = np.r_[0, np.flatnonzero(np.diff(codes[order])) + 1]
        pos = np.arange(len(rb)) - np.repeat(starts, np.diff(np.r_[starts, len(rb)]))
        rank[order] = pos
        wt = np.where(rank < kr, 0.0, np.where(rank < kr + kh, 0.5, 1.0))
        out.append((wt * rb).sum() - rb.sum())
    return np.asarray(out) / len(sessions)


def setup_effect(T, w_base, w):
    a = pd.Series(w_base * T.r.to_numpy(), index=T.index).groupby(T.setup).sum()
    b = pd.Series(w * T.r.to_numpy(), index=T.index).groupby(T.setup).sum()
    nb = pd.Series((w_base > 0).astype(int), index=T.index).groupby(T.setup).sum()
    nk = pd.Series((w > 0).astype(int), index=T.index).groupby(T.setup).sum()
    d = (b - a)
    return {s: {"base_r": round(float(a[s]), 2), "rule_r": round(float(b[s]), 2), "delta": round(float(d[s]), 2),
                "base_n": int(nb[s]), "kept_n": int(nk[s]),
                "base_avg": round(float(a[s] / nb[s]), 4) if nb[s] else None,
                "rule_avg": round(float(b[s] / nk[s]), 4) if nk[s] else None} for s in a.index}


if __name__ == "__main__":
    P = Path(sys.argv[1])
    T0 = pd.read_parquet(P / "trades.parquet")
    d = T0.date.astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    sess = json.loads((P / "sessions.json").read_text())
    cal = calendar(set(sum(sess.values(), [])) | set(T0.date))
    rng = np.random.default_rng(1120)
    res = {"n_configs": 0, "books": {}}
    overlays = RULES + ["ALL"]
    books = {"BEG_book": (T0[T0.book == "BEG"].assign(acct="BEG"), ["fit", "check", "t2"], overlays + ["MCF"], False),
             "BEG_alone": (T0[T0.book == "BEG"].assign(acct=lambda x: x.setup), ["fit", "check", "t2"], overlays, False),
             "Primary": (T0[T0.book == "PRIMARY"].assign(acct="PRIMARY"), ["live"], overlays, True)}
    for bname, (TB, segs, ovs, prim) in books.items():
        res["books"][bname] = {}
        res["n_configs"] += len(ovs)
        for sg in segs:
            T = TB[TB.seg == sg].reset_index(drop=True)
            S = sess[sg]
            wb = np.ones(len(T))
            base_ds = day_series(T, wb, S)
            R = {"sessions": len(S), "base": metrics(T, wb, S), "rules": {}}
            for ov in ovs:
                rs = set(RULES) if ov == "ALL" else {ov}
                w = simulate(T, rs, cal, primary=prim)
                ds = day_series(T, w, S)
                rc = random_ctrl(T, wb, w, S, rng)
                p = paired(base_ds, ds)
                p["beats_random_pct"] = round(float((p["d_avg_r_session"] > rc).mean()), 3)
                p["random_mean_d"] = round(float(rc.mean()), 4)
                se = setup_effect(T, wb, w)
                R["rules"][ov] = {"m": metrics(T, w, S), "paired": p, "setups": se,
                                  "setups_improved": sum(1 for v in se.values() if v["delta"] > 0.01),
                                  "setups_worse": sum(1 for v in se.values() if v["delta"] < -0.01)}
                print(bname, sg, ov, R["rules"][ov]["m"]["trades"], p, flush=True)
            res["books"][bname][sg] = R
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
