"""arena-am-short search: pairs and triples of arena conditions for SHORT entries 09:50-11:00 (see PLAN.md).
python research/swarm1017/arena-am-short/search.py <scratch rows dir>
Writes results.csv (every configuration), stage3.json (full combine.evaluate_combo on survivors), counts.json.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from mcf.research import gates
from mcf.research.arena import data as D
from mcf.research.arena.combine import cond_mask, evaluate_combo

HERE = Path(__file__).resolve().parent
ROWS = Path(sys.argv[1])
SCREEN = HERE.parent / "arena" / "single_screen.parquet"
ARENA_N = 20282
WINDOWS = [(950, 1100), (1000, 1100), (950, 1030)]
GEOMS = ["t05s1", "t1s1", "t1s05"]
FILTER_INDS = ["gap_atr", "atr_d_pct", "prev_range_atr", "day_vs_prev_range", "rvol_day", "from_pc_atr", "dist_pdh_atr",
               "dist_pdl_atr", "rv12", "day_range_atr", "vwap_atr", "fromOpen_atr", "or_high_dist_atr", "buyPressure",
               "emaDiff", "di_diff7"]
H1_END = pd.Timestamp("2025-07-31").date()


def _cond_from_bin(r):
    if r.op == "between":
        return (r.indicator, "between", (float(r.lo), float(r.hi)))
    return (r.indicator, r.op, float(r.lo))


def pick_conditions():
    s = pd.read_parquet(SCREEN)
    am = s[(s.window == "0950-1100") & (s.geom == "t1s1") & s.live]
    L, S = am[am.side == "short"], am[am.side == "long"]   # L = traded side (short), S = other side
    k = ["indicator", "bin"]
    m = L.merge(S[k + ["excess"]].rename(columns={"excess": "ex_s"}), on=k)
    m["dir"] = (m.excess - m.ex_s) / 2
    m = m[m.n >= 2000]
    a = m.sort_values("excess", ascending=False).drop_duplicates("indicator").head(20)
    b = m[~m.indicator.isin(a.indicator)].sort_values("dir", ascending=False).drop_duplicates("indicator").head(10)
    trig = [(_cond_from_bin(r), "excess" if i < 20 else "dir", float(r.excess), float(r.dir))
            for i, r in enumerate(pd.concat([a, b]).itertuples())]
    filt = []
    for ind in FILTER_INDS:
        q = L[L.indicator == ind].set_index("bin")
        med = float(q.loc["d05", "hi"])
        filt += [(ind, "<=", float(q.loc["le_q20", "lo"])), (ind, "<=", med), (ind, ">=", med),
                 (ind, ">=", float(q.loc["ge_q80", "lo"]))]
    return trig, filt


def load_rows(cols):
    parts = [pd.read_parquet(f, columns=cols) for f in sorted(ROWS.glob("month=*.parquet"))]
    x = pd.concat(parts, ignore_index=True)
    x["date"] = pd.to_datetime(x["date"]).dt.date
    x = x.sort_values(["symbol", "date", "tod"], kind="stable").reset_index(drop=True)
    mo = pd.to_datetime(x["date"]).dt.strftime("%Y-%m")
    x["split"] = np.where(mo <= D.TRAIN_END, "train", "valid")
    x["regime"] = pd.Series(x["date"]).map(D.regimes()).to_numpy()
    return x


class Fast:
    """First-bar-per-symbol-day stats on a row subset (rows sorted by symbol, date, tod)."""

    def __init__(self, A, rowsel):
        self.sel = np.flatnonzero(rowsel)
        sub = A.iloc[self.sel]
        self.gid = pd.factorize(sub["symbol"].astype(str) + "|" + sub["date"].astype(str))[0]
        self.day, self.days = pd.factorize(sub["date"])
        reg = pd.Series(self.days).map(D.regimes()).to_numpy()
        self.up_d = reg == "up"
        self.dn_d = reg == "down"
        self.h1_d = np.array([d <= H1_END for d in self.days])
        self.nd = len(self.days)
        self.tod = sub["tod"].to_numpy()
        self.r = {g: sub[f"r_short_{g}"].to_numpy(np.float64) for g in GEOMS}
        self.c = {g: sub[f"c_short_{g}"].to_numpy(np.float64) for g in GEOMS}
        self.ok = {g: np.isfinite(self.r[g]) & np.isfinite(self.c[g]) for g in GEOMS}

    def win(self, w):
        lo, hi = w
        return (self.tod >= lo) & (self.tod < hi)

    @staticmethod
    def _t(v, day, nd):
        n = len(v)
        if n < 2:
            return np.nan, np.nan
        mu = v.mean()
        s = np.bincount(day, v, nd)
        c = np.bincount(day, None, nd)
        se = np.sqrt(((s - c * mu) ** 2).sum()) / n
        return mu, (mu / se if se > 0 else np.nan)

    def stats(self, m, g):
        m = m & self.ok[g]
        idx = np.flatnonzero(m)
        if len(idx) == 0:
            return {"n": 0}
        gg = self.gid[idx]
        first = idx[np.r_[True, gg[1:] != gg[:-1]]]
        r, c, d = self.r[g][first], self.c[g][first], self.day[first]
        mu, t = self._t(r, d, self.nd)
        ex, tx = self._t(r - c, d, self.nd)
        out = {"n": len(r), "days": int(len(np.unique(d))), "exp": mu, "t": t, "excess": ex, "t_excess": tx}
        for k, dm in (("up", self.up_d), ("down", self.dn_d), ("h1", self.h1_d), ("h2", ~self.h1_d)):
            sel = dm[d]
            out[f"exp_{k}"] = r[sel].mean() if sel.any() else np.nan
            out[f"n_{k}"] = int(sel.sum())
        return out


def screen_gate(s):
    return (s.get("n", 0) >= 150 and s["exp"] > 0 and s["excess"] > 0 and s["exp_up"] > 0 and s["exp_down"] > 0
            and s["exp_h1"] > 0 and s["exp_h2"] > 0)


def key(conds):
    return " & ".join(f"{c[0]} {c[1]} {np.round(c[2], 4).tolist() if isinstance(c[2], tuple) else round(c[2], 4)}" for c in conds)


def main():
    trig, filt = pick_conditions()
    names = sorted({c[0][0] for c in trig} | {f[0] for f in filt})
    cols = ["symbol", "date", "tod"] + [f"{p}_short_{g}" for p in ("r", "c") for g in GEOMS] + names
    A = load_rows(cols)
    print("rows", len(A), "train", (A.split == "train").sum(), flush=True)
    tr = Fast(A, (A["split"] == "train").to_numpy())
    va = Fast(A, (A["split"] == "valid").to_numpy())
    CM = {}
    for c in [t[0] for t in trig] + filt:
        CM[key([c])] = cond_mask(A, c)
    rows = []
    n_conf = 0
    for ti, (tc, src, _, _) in enumerate(trig):
        for w in WINDOWS:
            for g in GEOMS:
                base = CM[key([tc])] [tr.sel] & tr.win(w)
                for f in filt:
                    if f[0] == tc[0]:
                        continue
                    s = tr.stats(base & CM[key([f])][tr.sel], g)
                    n_conf += 1
                    rows.append({"stage": 2, "conds": json.dumps([list(tc), list(f)]), "key": key([tc, f]), "trigger_src": src,
                                 "window": f"{w[0]}-{w[1]}", "geom": g, **{f"tr_{k}": v for k, v in s.items()}})
        print("trigger", ti, tc, "configs", n_conf, flush=True)
    R = pd.DataFrame(rows)
    top = R[R.tr_n >= 150].sort_values("tr_t", ascending=False).head(100)
    rows3 = []
    for r in top.itertuples():
        cs = [tuple(c) if not isinstance(c[2], list) else (c[0], c[1], tuple(c[2])) for c in json.loads(r.conds)]
        w = tuple(int(x) for x in r.window.split("-"))
        base = np.ones(len(tr.sel), bool)
        for c in cs:
            base &= CM[key([c])][tr.sel]
        base &= tr.win(w)
        used = {c[0] for c in cs}
        for f in filt:
            if f[0] in used:
                continue
            s = tr.stats(base & CM[key([f])][tr.sel], r.geom)
            n_conf += 1
            rows3.append({"stage": 3, "conds": json.dumps([list(c) for c in cs] + [list(f)]), "key": key(cs + [f]),
                          "trigger_src": r.trigger_src, "window": r.window, "geom": r.geom, **{f"tr_{k}": v for k, v in s.items()}})
    R = pd.concat([R, pd.DataFrame(rows3)], ignore_index=True)
    N = ARENA_N + n_conf
    print("configs", n_conf, "N_lineage", N, "bar", gates.t_required(N), flush=True)
    # stage 3: valid for survivors of the train screen gate
    surv = [i for i, r in R.iterrows() if screen_gate({k[3:]: r[k] for k in R.columns if k.startswith("tr_")})]
    print("train-gate survivors", len(surv), flush=True)
    full = []
    for i in surv:
        r = R.loc[i]
        cs = [tuple(c) if not isinstance(c[2], list) else (c[0], c[1], tuple(c[2])) for c in json.loads(r.conds)]
        w = tuple(int(x) for x in r.window.split("-"))
        m = np.ones(len(va.sel), bool)
        for c in cs:
            m &= CM[key([c])][va.sel]
        s = va.stats(m & va.win(w), r.geom)
        for k, v in s.items():
            R.loc[i, f"va_{k}"] = v
        if s.get("n", 0) and s["exp"] > 0 and s["excess"] > 0:
            ev = evaluate_combo(A, cs, "short", r.geom, w, n_lineage=N)
            ev["key"] = r.key
            full.append(ev)
    R.to_csv(HERE / "results.csv", index=False, float_format="%.5g")
    (HERE / "stage3.json").write_text(json.dumps(full, indent=1, default=str))
    json.dump({"configs_scored": n_conf, "arena_N": ARENA_N, "N_lineage": N, "bar": gates.t_required(N),
               "triggers": [list(map(str, t)) for t in trig],
               "n_filters": len(filt), "train_gate_survivors": len(surv), "valid_positive_full_eval": len(full),
               "quality_pass": sum(bool(e["quality_pass"]) for e in full)}, open(HERE / "counts.json", "w"), indent=1)
    print("done; valid-positive", len(full), "quality_pass", sum(bool(e["quality_pass"]) for e in full))


if __name__ == "__main__":
    main()
