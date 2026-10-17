"""arena-mid-short search: pairs and triples of arena conditions for SHORT entries 11:00-14:00 (see PLAN.md).
python research/swarm1017/arena-mid-short/search.py <scratch rows dir>
Writes results.csv (every configuration), stage3.json (full combine.evaluate_combo on valid-positive survivors),
counts.json. Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GEOMS, WINDOWS, pick_conditions  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena import data as D  # noqa: E402
from mcf.research.arena.combine import combo_mask, cond_mask, evaluate_combo  # noqa: E402

HERE = Path(__file__).resolve().parent
ROWS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
PRIOR_N = 20282 + 23032 + 30773  # arena screen + arena-am-long + arena-mid-long (same family and design)
OLD_LONG_LINEAGE = 0             # (am-short added at the end in NOTES when known)
H1_END = pd.Timestamp("2025-07-31").date()
REG = D.regimes()
LIBREG = D._lib().regimes()


def load_rows(cols):
    """Months concatenated in order; within a month rows are in frame order (symbol, date, tod), so every symbol-day
    is contiguous and tod-ordered (all Fast needs). No global sort (memory)."""
    from pandas.api.types import union_categoricals

    parts, syms = [], []
    for f in sorted(ROWS.glob("month=*.parquet")):
        x = pd.read_parquet(f, columns=cols)
        syms.append(pd.Categorical(x.pop("symbol")))
        parts.append(x)
    x = pd.concat(parts, ignore_index=True)
    del parts
    x["symbol"] = union_categoricals(syms)
    x["date"] = pd.to_datetime(x["date"]).dt.date
    mo = pd.to_datetime(pd.Series(x["date"])).dt.strftime("%Y-%m")
    x["split"] = np.where(mo <= D.TRAIN_END, "train", "valid")
    x["regime"] = pd.Series(x["date"]).map(REG).to_numpy()
    return x


class Fast:
    """First-bar-per-symbol-day, day-clustered stats on a row subset (rows sorted by symbol, date, tod)."""

    def __init__(self, A, rowsel):
        self.sel = np.flatnonzero(rowsel)
        sub = A.iloc[self.sel]
        self.day, self.days = pd.factorize(sub["date"])
        sc = sub["symbol"].cat.codes.to_numpy().astype(np.int64)
        self.gid = sc * (len(self.days) + 1) + self.day
        reg = pd.Series(self.days).map(REG).to_numpy()
        self.up_d, self.dn_d = reg == "up", reg == "down"
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
        out = {"n": len(r), "days": int(len(np.unique(d))), "exp": mu, "t": t, "excess": ex, "t_excess": tx,
               "per_day": len(r) / self.nd}
        for k, dm in (("up", self.up_d), ("down", self.dn_d), ("h1", self.h1_d), ("h2", ~self.h1_d)):
            sel = dm[d]
            out[f"exp_{k}"] = r[sel].mean() if sel.any() else np.nan
            out[f"n_{k}"] = int(sel.sum())
        return out


def screen_gate(s):
    return (s.get("n", 0) >= 150 and s.get("days", 0) >= 60 and s["exp"] > 0 and s["excess"] > 0 and s["exp_up"] > 0
            and s["exp_down"] > 0 and s["exp_h1"] > 0 and s["exp_h2"] > 0)


def key(conds):
    return " & ".join(f"{c[0]} {c[1]} {np.round(c[2], 4).tolist() if isinstance(c[2], tuple) else round(c[2], 4)}"
                      for c in conds)


def parse(conds_json):
    return [(c[0], c[1], tuple(c[2])) if isinstance(c[2], list) else (c[0], c[1], c[2]) for c in json.loads(conds_json)]


def full_eval(A, cs, geom, w, N, n_sessions):
    """combine.evaluate_combo on the rows where the combo holds (identical trades, much faster); per_day re-based on
    all sessions of the open data."""
    m = combo_mask(A, cs, w)
    ev = evaluate_combo(A.loc[m], cs, "short", geom, w, n_lineage=N, regimes=LIBREG)
    ev["per_day"] = round(ev["all"].get("n", 0) / n_sessions, 3)
    return ev


def main():
    t0 = time.time()
    trig, filt, ctx = pick_conditions()
    names = sorted({c[0][0] for c in trig} | {f[0] for f in filt} | {c[0] for c in ctx})
    cols = ["symbol", "date", "tod"] + [f"{p}_short_{g}" for p in ("r", "c") for g in GEOMS] + names
    A = load_rows(cols)
    n_sessions = pd.Series(A["date"]).nunique()
    print("rows", len(A), "train", (A.split == "train").sum(), "sessions", n_sessions, f"{time.time()-t0:.0f}s", flush=True)
    tr = Fast(A, (A["split"] == "train").to_numpy())
    va = Fast(A, (A["split"] == "valid").to_numpy())
    CM = {key([c]): cond_mask(A, c)[tr.sel] for c in [t[0] for t in trig] + filt + ctx}   # TRAIN rows only
    W = {w: tr.win(w) for w in WINDOWS}
    rows, n_conf = [], 0
    for ti, (tc, src, _, _) in enumerate(trig):
        for w in WINDOWS:
            base = CM[key([tc])] & W[w]
            for f in filt:
                if f[0] == tc[0]:
                    continue
                m = base & CM[key([f])]
                for g in GEOMS:
                    s = tr.stats(m, g)
                    n_conf += 1
                    rows.append({"stage": 1, "branch": "live", "conds": json.dumps([list(tc), list(f)]),
                                 "key": key([tc, f]), "trigger_src": src, "window": f"{w[0]}-{w[1]}", "geom": g,
                                 **{f"tr_{k}": v for k, v in s.items()}})
        print("trigger", ti, tc, "configs", n_conf, f"{time.time()-t0:.0f}s", flush=True)
    R = pd.DataFrame(rows)
    top = R[(R.tr_n >= 150) & (R.tr_days >= 60)].sort_values("tr_t", ascending=False).head(100)
    rows3 = []
    for r in top.itertuples():
        cs = parse(r.conds)
        w = tuple(int(x) for x in r.window.split("-"))
        base = W[w].copy()
        for c in cs:
            base &= CM[key([c])]
        used = {c[0] for c in cs}
        for branch, pool in (("live", filt), ("ctx", ctx)):
            for f in pool:
                if f[0] in used:
                    continue
                s = tr.stats(base & CM[key([f])], r.geom)
                n_conf += 1
                rows3.append({"stage": 2, "branch": branch, "conds": json.dumps([list(c) for c in cs] + [list(f)]),
                              "key": key(cs + [f]), "trigger_src": r.trigger_src, "window": r.window, "geom": r.geom,
                              **{f"tr_{k}": v for k, v in s.items()}})
    R = pd.concat([R, pd.DataFrame(rows3)], ignore_index=True)
    N = PRIOR_N + n_conf
    print("configs", n_conf, "N_lineage", N, "bar", gates.t_required(N), f"{time.time()-t0:.0f}s", flush=True)
    del CM
    trcols = [k for k in R.columns if k.startswith("tr_")]
    surv = [i for i, r in R.iterrows() if screen_gate({k[3:]: r[k] for k in trcols})]
    print("train-gate survivors", len(surv), "live", int((R.loc[surv, "branch"] == "live").sum()), flush=True)
    full = []
    vcache = {}
    for i in surv:
        r = R.loc[i]
        cs = parse(r.conds)
        w = tuple(int(x) for x in r.window.split("-"))
        m = va.win(w).copy()
        for c in cs:
            k = key([c])
            if k not in vcache:
                vcache[k] = cond_mask(A, c)[va.sel]
            m &= vcache[k]
        s = va.stats(m, r.geom)
        for k, v in s.items():
            R.loc[i, f"va_{k}"] = v
        if s.get("n", 0) and s["exp"] > 0 and s["excess"] > 0:
            ev = full_eval(A, cs, r.geom, w, N, n_sessions)
            ev["key"], ev["branch"] = r.key, r.branch
            full.append(ev)
    R.to_csv(HERE / "results.csv", index=False, float_format="%.5g")
    (HERE / "stage3.json").write_text(json.dumps(full, indent=1, default=str))
    live_full = [e for e in full if e["branch"] == "live"]
    json.dump({"configs_scored": n_conf, "configs_live_branch": int((R.branch == "live").sum()),
               "configs_ctx_branch": int((R.branch == "ctx").sum()), "prior_N": PRIOR_N, "N_lineage": N,
               "bar": gates.t_required(N), "bar_with_other_lineage": gates.t_required(N + OLD_LONG_LINEAGE),
               "triggers": [list(map(str, t)) for t in trig], "n_filters": len(filt), "n_ctx_filters": len(ctx),
               "train_gate_survivors": len(surv), "valid_positive_full_eval": len(full),
               "valid_positive_live": len(live_full),
               "quality_pass_live": sum(bool(e["quality_pass"]) for e in live_full),
               "quality_pass_ctx_research_only": sum(bool(e["quality_pass"]) for e in full if e["branch"] == "ctx")},
              open(HERE / "counts.json", "w"), indent=1)
    print("done; valid-positive", len(full), "quality_pass", sum(bool(e["quality_pass"]) for e in full),
          f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
