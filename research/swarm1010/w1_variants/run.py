"""W1 coordinate search (NOTES.md 1.4): per base list, stage 1 = base + one-axis variants, stage 2 = pairs of the 3 best
axes by robust score (min of up / down day-clustered t; n >= 150), plateau neighbours of every configuration meeting
the other probation conditions. Every evaluated configuration is written to data/configs.csv (one row each).

    python research/swarm1010/w1_variants/run.py [--only NAME_SUBSTR] [--base-only]
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eng  # noqa: E402
import families as FM  # noqa: E402

OUT = HERE / "data" / "configs.csv"
STAT_KEYS = ["n", "per_day", "exp", "win", "t", "n_up", "exp_up", "t_up", "n_flat", "exp_flat", "t_flat", "n_down",
             "exp_down", "t_down", "robust", "both_pos", "spread", "ex_best_day", "maxday", "wf", "wf_folds"]


def pkey(P):
    return json.dumps({k: v for k, v in sorted(P.items()) if k != "_own"}, default=str)


def diff(P, P0):
    return ";".join(f"{k}={P[k]}" for k in sorted(P) if k != "_own" and P.get(k) != P0.get(k))


def neighbours(spec, P):
    """One-step neighbours on every ordered axis (numbers, rsi bands, vband / ma of the same type)."""
    out = []
    for ax, vals in spec["axes"].items():
        v = P.get(ax)
        if v is None or ax in ("geom", "gate", "ema"):
            continue
        if isinstance(v, str):                       # vband / ma: same type, adjacent k
            pre = "".join(ch for ch in v if ch.isalpha())
            same = [x for x in vals if isinstance(x, str) and "".join(ch for ch in x if ch.isalpha()) == pre]
        else:
            same = [x for x in vals if x is not None and not isinstance(x, str)]
        if v not in same:
            continue
        i = same.index(v)
        for j in (i - 1, i + 1):
            if 0 <= j < len(same):
                out.append(dict(P, **{ax: same[j]}))
    return out


class Runner:
    def __init__(self, D):
        self.D = D
        self.seen = {}
        self.rows = []

    def ev(self, spec, P, stage):
        k = spec["name"] + "|" + pkey(P)
        if k in self.seen:
            return self.seen[k]
        D = self.D
        s = 1 if spec["side"] == "long" else -1
        m = spec["fn"](D, P, s)
        m = FM.common(D, P, s, m)
        idx, r = D.trades(m, spec["side"], P["geom"], spec["min_adv"])
        st = D.stats(idx, r)
        row = {"family": spec["name"], "group": spec["group"], "lineage": spec["lineage"], "side": spec["side"],
               "stage": stage, "variant": diff(P, spec["P0"]) or "BASE", "geom": P["geom"]}
        row.update({k2: st.get(k2) for k2 in STAT_KEYS})
        row["params"] = pkey(P)
        self.seen[k] = row
        self.rows.append(row)
        return row

    def search(self, spec, base_only=False):
        P0 = spec["P0"]
        base = self.ev(spec, P0, "base")
        if base_only:
            return
        s1 = []
        for ax, vals in spec["axes"].items():
            for v in vals:
                if v == P0.get(ax) or (v is None and P0.get(ax) is None):
                    continue
                r = self.ev(spec, dict(P0, **{ax: v}), "ofat")
                s1.append((ax, v, r))
        best = {}
        for ax, v, r in s1:
            if r["n"] >= 150 and r["robust"] > -99 and (ax not in best or r["robust"] > best[ax][1]["robust"]):
                best[ax] = (v, r)
        top = sorted(best.items(), key=lambda kv: -kv[1][1]["robust"])[:3]
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                (a1, (v1, _)), (a2, (v2, _)) = top[i], top[j]
                self.ev(spec, dict(P0, **{a1: v1, a2: v2}), "pair")
        # plateau for every configuration meeting the other probation conditions
        for row in [x for x in self.rows if x["family"] == spec["name"] and x["stage"] != "plateau"]:
            if eng.probation(row) and "plateau" not in row:
                P = json.loads(row["params"])
                P = _restore(spec, P)
                nb = [self.ev(spec, q, "plateau") for q in neighbours(spec, P)]
                ex = [x["exp"] for x in nb if x["n"] and np.isfinite(x["exp"])]
                row["plateau"] = float(np.mean(ex)) if ex else np.nan
                row["plateau_n"] = len(ex)
        # asymmetry check (NOTES 1.6): both regimes positive with min(t_up, t_down) >= 1 -> neighbours' regime means
        for row in [x for x in self.rows if x["family"] == spec["name"] and x["stage"] != "plateau"]:
            if row["n"] >= 150 and row.get("both_pos") and row["robust"] >= 1.0 and "nb_up" not in row:
                P = _restore(spec, json.loads(row["params"]))
                nb = [self.ev(spec, q, "plateau") for q in neighbours(spec, P)]
                nb = [x for x in nb if x["n"] and np.isfinite(x.get("exp_up", np.nan)) and np.isfinite(x.get("exp_down", np.nan))]
                row["nb_up"] = float(np.mean([x["exp_up"] for x in nb])) if nb else np.nan
                row["nb_down"] = float(np.mean([x["exp_down"] for x in nb])) if nb else np.nan
                if "plateau" not in row:
                    row["plateau"] = float(np.mean([x["exp"] for x in nb])) if nb else np.nan
                    row["plateau_n"] = len(nb)


def _restore(spec, P):
    """JSON round trip turns tuples into lists; restore the axis values' types from the spec."""
    out = dict(spec["P0"])
    for k, v in P.items():
        cand = spec["axes"].get(k, [spec["P0"].get(k)])
        match = [x for x in cand if json.dumps(x, default=str) == json.dumps(v, default=str)]
        out[k] = match[0] if match else (tuple(v) if isinstance(v, list) and k not in ("filters",) else v)
    out["filters"] = spec["P0"].get("filters", out.get("filters"))
    if "trig" in spec["P0"]:
        out["trig"] = spec["P0"]["trig"]
    out["_own"] = spec["P0"].get("_own", ())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--base-only", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    D = eng.D()
    specs = FM.all_specs()
    if a.only:
        specs = [s for s in specs if any(x in s["name"] for x in a.only.split(","))]
    R = Runner(D)
    t0 = time.time()
    for i, sp in enumerate(specs):
        n0 = len(R.rows)
        R.search(sp, a.base_only)
        b = R.rows[n0]
        print(f"[{i + 1}/{len(specs)}] {sp['name']}: {len(R.rows) - n0} configs, base n {b['n']} exp {b['exp']:+.4f} "
              f"t {b['t']:.2f} ({time.time() - t0:.0f}s)", flush=True)
        if (i + 1) % 10 == 0:
            pd.DataFrame(R.rows).to_csv(a.out, index=False)
    pd.DataFrame(R.rows).to_csv(a.out, index=False)
    print("configs", len(R.rows))


if __name__ == "__main__":
    main()
