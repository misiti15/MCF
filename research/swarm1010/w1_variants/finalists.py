"""W1 finalists: for every probation passer and the top robust variant of each family (results.csv), re-generate the
trades and report time of day (timeofday buckets B1-B5), per-quarter expectancy, halves (H1 / H2 at the median
session) and a gates.py cross-check (summary / regime_split / walk_forward). Writes finalists.json.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import lib  # noqa: E402
import eng  # noqa: E402
import families as FM  # noqa: E402
from mcf.research import gates  # noqa: E402
from run import _restore  # noqa: E402


def trades_for(D, spec, P):
    s = 1 if spec["side"] == "long" else -1
    m = FM.common(D, P, s, spec["fn"](D, P, s))
    return D.trades(m, spec["side"], P["geom"], spec["min_adv"])


def detail(D, spec, P):
    idx, r = trades_for(D, spec, P)
    day = D.day[idx]
    dates = pd.to_datetime(np.array(D.dates)[day]).date
    tr = pd.DataFrame({"date": dates, "r": r, "tod": D.tod[idx]})
    out = {"n": len(r)}
    out["gates_summary"] = gates.summary(tr)
    rg = gates.regime_split(tr, D.reg)
    out["gates_regime"] = {k: rg[k] for k in ("up", "flat", "down")} | {"pass": rg["pass"]}
    out["gates_wf_share"] = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)["share_positive"]
    out["buckets"] = {b: {"n": int(((tr.tod >= a) & (tr.tod <= z)).sum()),
                          "exp": round(float(tr.r[(tr.tod >= a) & (tr.tod <= z)].mean()), 4)
                          if ((tr.tod >= a) & (tr.tod <= z)).any() else None} for b, (a, z) in eng.BUCKETS.items()}
    out["quarters"] = gates.per_quarter(tr)
    med = sorted(set(D.day))[len(set(D.day)) // 2 - 1]
    h1 = day <= med
    out["H1"] = {"n": int(h1.sum()), "exp": round(float(r[h1].mean()), 4) if h1.any() else None}
    out["H2"] = {"n": int((~h1).sum()), "exp": round(float(r[~h1].mean()), 4) if (~h1).any() else None}
    return out


def main():
    res = pd.read_csv(HERE / "results.csv")
    prm = pd.read_csv(HERE / "data" / "params.csv")
    res["params"] = prm["params"]
    specs = {s["name"]: s for s in FM.all_specs()}
    pick = res[res["probation"]].copy()
    top = (res[(res["n"] >= 150) & (res["robust"] > -99) & res["family"].isin(specs) & (res["stage"] != "plateau")]
           .sort_values("robust", ascending=False).groupby("family").head(1))
    pick = pd.concat([pick, top]).drop_duplicates(subset=["family", "variant"])
    D = eng.D()
    out = []
    for _, row in pick.iterrows():
        sp = specs.get(row["family"])
        if sp is None:
            continue
        P = _restore(sp, json.loads(row["params"]))
        d = detail(D, sp, P)
        d.update(family=row["family"], variant=row["variant"], probation=bool(row["probation"]), robust=row["robust"])
        out.append(d)
        print(row["family"], row["variant"], d["n"], d["gates_summary"].get("exp_r"), d["gates_summary"].get("t"),
              d["gates_regime"]["pass"], d["gates_wf_share"], flush=True)
    (HERE / "finalists.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
