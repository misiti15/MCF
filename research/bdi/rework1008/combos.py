"""F4 (pairs of weak, uncorrelated components), F5 (re-entry / stop-and-reverse), F6 (ADV tiers).
Components are chosen on TRAIN only (NOTES.md section 0). Writes data/extra.parquet.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gates import NEIGH, key  # noqa: E402
from grid import WINDOWS, evaluate, namespace  # noqa: E402
from lib import GEOMS, Split, baseline, exit_bar, stats  # noqa: E402

KEYS = ["n", "exp", "t", "green", "h1", "h2", "exbest", "tpd", "win"]
OPP = {"long": "short", "short": "long"}


def conds_of(row):
    return tuple(c for c in (row.c0, row.c1, row.c2, row.c3) if isinstance(c, str) and c not in ("", "none"))


class Ctx:
    def __init__(self, extra=None):
        self.sp = {s: Split(s, extra) for s in ("train", "valid")}
        self.ns = {s: namespace(self.sp[s].col, self.sp[s].prev) for s in self.sp}
        adv = pd.read_parquet(HERE / "data" / "adv.parquet")
        a = adv.set_index(["symbol", "date"])["adv"]
        for s, sp in self.sp.items():
            k = pd.MultiIndex.from_arrays([sp.sym, sp.df.date.astype(str).to_numpy()])
            sp.adv = a.reindex(k).to_numpy()

    def rowmask(self, s, conds, w):
        lo, hi = WINDOWS[w] if isinstance(w, str) else w
        sp = self.sp[s]
        return evaluate(conds, self.ns[s]) & (sp.tod >= lo) & (sp.tod <= hi)

    def entries(self, s, conds, w, extra=None):
        m = self.rowmask(s, conds, w)
        if extra is not None:
            m &= extra
        return self.sp[s].first_per_day(np.flatnonzero(m))


def plateau(lut, fam, cs, w, side, g):
    cs = list(cs) + [""] * (4 - len(cs))
    nb = []
    for dim, mp in NEIGH[fam].items():
        if dim == "w":
            nb += [key(fam, tuple(cs), w2, side, g) for w2 in mp.get(w, [])]
        else:
            for v in mp.get(cs[dim], []):
                c2 = list(cs)
                c2[dim] = v
                nb.append(key(fam, tuple(c2), w, side, g))
    vals = [lut[k] for k in nb if k in lut and np.isfinite(lut[k][1])]
    if len(vals) < 2:
        return False, len(vals), np.nan, np.nan
    te = np.array([v[0] for v in vals]); ve = np.array([v[1] for v in vals])
    return bool(te.mean() > 0 and ve.mean() > 0 and (ve > 0).mean() >= 2 / 3), len(vals), te.mean(), ve.mean()


def record(cx, fam, label, ent, side, g, win, parents, pl_ok):
    a = stats(cx.sp["train"], ent["train"], side, g)
    b = stats(cx.sp["valid"], ent["valid"], side, g)
    if a is None or a["n"] < 60:
        return None
    b = b or {"n": 0}
    row = {"family": fam, "conds": label, "window": f"{win[0]}-{win[1]}", "side": side, "geom": g, "parents": parents}
    row.update({f"tr_{x}": a.get(x, np.nan) for x in KEYS})
    row.update({f"va_{x}": b.get(x, np.nan) for x in KEYS})
    row["tr_base"] = baseline(cx.sp["train"], side, g, *win)
    row["va_base"] = baseline(cx.sp["valid"], side, g, *win)
    row["g_plateau"] = pl_ok
    return row


def main():
    r = pd.read_parquet(HERE / "data" / "gated.parquet")
    r["c3"] = r["c3"].fillna("")
    lut = {key(f, (a, b, c, d), w, s, g): (te, ve) for f, a, b, c, d, w, s, g, te, ve in
           zip(r.family, r.c0, r.c1, r.c2, r.c3, r.window, r.side, r.geom, r.tr_exp, r.va_exp)}
    cx = Ctx()
    tr = cx.sp["train"]

    def pl_of(x):
        cs = [x.c0, x.c1, x.c2, x.c3]
        return plateau(lut, x.family, cs, x.window, x.side, x.geom)[0]

    # ---- train-only component selection, de-duplicated by train symbol-day Jaccard < 0.5
    cand = r[(r.tr_n >= 60) & (r.tr_exp > 0) & (r.tr_h1 > 0) & (r.tr_h2 > 0)].sort_values("tr_t", ascending=False)
    picks, sets = [], []
    for _, x in cand.iterrows():
        e = cx.entries("train", conds_of(x), x.window)
        s = set(zip(tr.sid[e].tolist()))
        if any(len(s & t) / max(1, len(s | t)) >= 0.5 for t in sets):
            continue
        picks.append(x); sets.append(s)
        if len(picks) == 20:
            break
    comp = pd.DataFrame(picks)
    comp.to_csv(HERE / "data" / "components.csv", index=False)
    print("components:\n", comp[["family", "conds", "window", "side", "geom", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t"]].to_string())

    rows, tried = [], {"F4": 0, "F5": 0, "F6": 0}
    # ---- F4 pairs (same side + geom): OR, SEQ a->b, SEQ b->a
    for i in range(len(comp)):
        for j in range(i + 1, len(comp)):
            A, B = comp.iloc[i], comp.iloc[j]
            if A.side != B.side or A.geom != B.geom:
                continue
            plA, plB = pl_of(A), pl_of(B)
            wa, wb = WINDOWS[A.window], WINDOWS[B.window]
            for kind in ("OR", "SEQab", "SEQba"):
                tried["F4"] += 1
                ent = {}
                for s in cx.sp:
                    sp = cx.sp[s]
                    ma, mb = cx.rowmask(s, conds_of(A), A.window), cx.rowmask(s, conds_of(B), B.window)
                    if kind == "OR":
                        m = ma | mb
                    else:
                        first, second = (ma, mb) if kind == "SEQab" else (mb, ma)
                        cs = np.cumsum(first)
                        start = np.flatnonzero(sp.first)
                        base = np.repeat(cs[start] - first[start], np.diff(np.r_[start, sp.n]))
                        before = (cs - first - base) > 0
                        m = second & before
                    ent[s] = sp.first_per_day(np.flatnonzero(m))
                win = (min(wa[0], wb[0]), max(wa[1], wb[1])) if kind == "OR" else (wb if kind == "SEQab" else wa)
                lab = f"{kind}[{A.family}:{A.conds}@{A.window}] [{B.family}:{B.conds}@{B.window}]"
                row = record(cx, "F4", lab, ent, A.side, A.geom, win, f"{i},{j}", bool(plA and plB))
                if row:
                    rows.append(row)
    # ---- F5 managed: re-entry, stop-and-reverse x3, first+re-entry, on the top 10 components
    for i in range(min(10, len(comp))):
        P = comp.iloc[i]
        plP = pl_of(P)
        w = WINDOWS[P.window]
        ent = {k: {} for k in ("RE", "SARt1s1", "SARt05s1", "SARt1s05", "BOTH")}
        for s in cx.sp:
            sp = cx.sp[s]
            pm = cx.rowmask(s, conds_of(P), P.window)
            pr = np.flatnonzero(pm)
            e1 = sp.first_per_day(pr)
            xb, isstop = exit_bar(sp, e1, P.side, P.geom)
            has = xb >= 0
            pos = np.searchsorted(pr, xb[has] + 1)
            okp = pos < len(pr)
            cand_i = pr[np.minimum(pos, len(pr) - 1)]
            okp &= sp.sid[cand_i] == sp.sid[e1[has]]
            re = np.sort(cand_i[okp])
            ent["RE"][s] = re
            sar = np.sort(xb[has & isstop])
            sar = sar[sp.tod[sar] <= 1500]
            for g in GEOMS:
                ent["SAR" + g][s] = sar
            ent["BOTH"][s] = np.sort(np.r_[e1, re])
        lab0 = f"[{P.family}:{P.conds}@{P.window}]"
        for k, e in ent.items():
            tried["F5"] += 1
            side = OPP[P.side] if k.startswith("SAR") else P.side
            g = k[3:] if k.startswith("SAR") else P.geom
            win = (w[0], 1500) if k.startswith("SAR") else w
            row = record(cx, "F5", f"{k}{lab0}", e, side, g, win, str(i), plP)
            if row:
                rows.append(row)
    # ---- F6 ADV tiers on the 50 best near-passers
    base_ok = r.g_pos & r.g_n & r.g_t & r.g_halves
    top = pd.concat([r[base_ok].sort_values("score", ascending=False),
                     r[~base_ok].sort_values("score", ascending=False)]).head(50)
    for _, x in top.iterrows():
        plx = pl_of(x)
        for tier in (150e6, 300e6):
            tried["F6"] += 1
            ent = {s: cx.entries(s, conds_of(x), x.window, extra=cx.sp[s].adv >= tier) for s in cx.sp}
            row = record(cx, "F6", f"ADV>={int(tier / 1e6)}M[{x.family}:{x.conds}@{x.window}]", ent, x.side, x.geom,
                         WINDOWS[x.window], x.family, plx)
            if row:
                rows.append(row)
    e = pd.DataFrame(rows)
    e["g_pos"] = (e.tr_exp > 0) & (e.va_exp > 0)
    e["g_n"] = e.va_n >= 30
    e["g_t"] = e.va_t >= 1.5
    e["g_halves"] = (e.tr_h1 > 0) & (e.tr_h2 > 0)
    e["g_base"] = (e.tr_exp > e.tr_base) & (e.va_exp > e.va_base)
    e["g_all"] = e.g_pos & e.g_n & e.g_t & e.g_halves & e.g_base & e.g_plateau
    e["score"] = np.minimum(e.tr_t, e.va_t)
    e.to_parquet(HERE / "data" / "extra.parquet")
    pd.Series(tried).to_json(HERE / "data" / "extra_counts.json")
    print("tried", tried, "scored", len(e))
    print(e.groupby("family")[["g_pos", "g_t", "g_all"]].sum())
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 120)
    show = ["family", "conds", "side", "geom", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t", "va_tpd", "g_plateau", "g_all"]
    print(e.sort_values("score", ascending=False)[show].head(40).to_string())


if __name__ == "__main__":
    main()
