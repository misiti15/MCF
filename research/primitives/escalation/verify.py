"""Re-score the escalation finalists from their deployable modules (mask(df) over the lab frame).
Educational only - not financial advice. Train + valid only.
    python research/primitives/escalation/verify.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "finalists"))
from lab import Split, evaluate, cond  # noqa: E402
from mcf.research.setup_lab import evaluate as lab_evaluate  # noqa: E402

TAGS = {"X-gapfade-early": "x_gapfade_early", "X-gapfade-early-b": "x_gapfade_early_b", "X-bottom-div": "x_bottom_div",
        "X-failbo": "x_failbo", "X-vwaploss-run": "x_vwaploss_run", "X-lodbreak-early": "x_lodbreak_early"}
WIN = {"X-gapfade-early": (950, 1030), "X-gapfade-early-b": (950, 1030), "X-bottom-div": (1200, 1430),
       "X-failbo": (1000, 1100), "X-vwaploss-run": (1000, 1300), "X-lodbreak-early": (950, 1030)}


def modload(name):
    spec = importlib.util.spec_from_file_location(name, HERE / "finalists" / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


class Frame(dict):
    def __getitem__(self, k):
        return _A(dict.__getitem__(self, k))


class _A:
    def __init__(self, a): self.a = a
    def to_numpy(self, dtype=None): return self.a.astype(dtype) if dtype else self.a


def main():
    out, masks = {}, {}
    for sp in ("train", "valid"):
        S = Split(sp)
        df = Frame(S.c)
        for tag, mn in TAGS.items():
            mod = modload(mn)
            m = np.asarray(mod.mask(df), bool)
            masks[(sp, tag)] = S.first_idx(m & np.isfinite(S.r[(mod.SIDE, mod.GEOM)]))
            ev = evaluate(S, m, mod.SIDE, mod.GEOM)
            a, b = WIN[tag]
            ev["base_window"] = round(S.baseline(mod.SIDE, mod.GEOM, a, b), 4)
            # other geometries for reference
            ev["other_geoms"] = {g: evaluate(S, m, mod.SIDE, g, prod=False)["exp_r"] for g in ("t1s1", "t05s1", "t1s05")}
            if sp == "valid":
                idx = masks[(sp, tag)]
                r = S.r[(mod.SIDE, mod.GEOM)][idx]
                d = S.date_id[idx]
                ev["per_day"] = {str(S.dates[k]): [int((d == k).sum()), round(float(r[d == k].sum()), 2)] for k in np.unique(d)}
                u, k = np.unique(S.symbol[idx], return_counts=True)
                ev["symbols_top"] = [[str(a), int(b)] for a, b in zip(u[np.argsort(-k)][:5], np.sort(k)[::-1][:5])]
            out.setdefault(tag, {})[sp] = ev
        # overlap between finalists (same symbol-day first entries)
        tags = list(TAGS)
        ov = {}
        for i, a in enumerate(tags):
            for b in tags[i + 1:]:
                sa = set(S.symday[masks[(sp, a)]]); sb = set(S.symday[masks[(sp, b)]])
                if sa & sb:
                    ov[f"{a}|{b}"] = len(sa & sb)
        out.setdefault("_overlap", {})[sp] = ov
        del S, df
    (HERE / "finalists.json").write_text(json.dumps(out, indent=1, default=float))
    for tag in TAGS:
        for sp in ("train", "valid"):
            e = out[tag][sp]
            print(tag, sp, {k: e[k] for k in ("n", "days", "win_rate", "exp_r", "t_dc", "ex_best_day", "green_days", "ctrl", "exp_r_prod", "t_dc_prod", "base_window", "half1", "half2")}, e["other_geoms"])
    print(out["_overlap"])


if __name__ == "__main__":
    main()
