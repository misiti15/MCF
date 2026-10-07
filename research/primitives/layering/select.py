"""Pick up to 8 distinct layered finalists from results.csv, write deployable modules, verify through
mcf.research.setup_lab.evaluate, and compute the time-of-day matched edge and window-shift robustness.

Selection rule (fixed before looking at the ranked list):
  finalist gate passed (layer.py) AND both train halves > 0 AND valid ex-best-day > 0 AND valid day-t at
  production cost >= 1.5 AND valid days >= 8; rank by min(train day-t, valid day-t); greedily keep a setup only if
  its train+valid trade set (symbol-day) overlaps every already-kept setup by Jaccard <= 0.5.
Educational only - not financial advice. Train + valid only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import layer  # noqa: E402
from layer import lab  # noqa: E402

FIN = HERE / "finalists"
FIN.mkdir(exist_ok=True)


def atoms_for(row, pools, xs):
    w = row["window"]
    names = row["atoms"].split("+")
    if ":" in w:   # X composite + atom
        nm = w.split(":")[0]
        X, win, _ = xs[nm]
        pool = {}
        for ww, (wl, wh) in layer.WINDOWS.items():
            if ww != "WALL" and wl < win[1] and wh > win[0]:
                pool.update(pools[ww])
        return [X] + [pool[n] for n in names[1:]], win
    return [pools[w][n] for n in names], layer.WINDOWS[w]


def mask_on(S, atoms, win):
    tod = S.c["tod"]
    m = (tod >= win[0]) & (tod < win[1])
    for a in atoms:
        m &= a.mask(S)
    return m


def module_text(tag, row, atoms, win):
    lines = []
    body = []
    for a in atoms:
        if a.kind == "band":
            lo, hi = a.p
            conds = []
            if np.isfinite(lo):
                conds.append(f"(c('{a.metric}') > {lo!r})")
            if np.isfinite(hi):
                conds.append(f"(c('{a.metric}') <= {hi!r})")
            body.append(" & ".join(conds))
            lines.append(a.text or a.name)
        elif a.kind in ("gt", "lt"):
            body.append(f"(c('{a.metric}') {'>' if a.kind == 'gt' else '<'} {a.p!r})")
            lines.append(a.text)
        elif a.kind == "eq":
            body.append(f"(c('{a.metric}') == {a.p!r})")
            lines.append(a.text)
        elif a.kind == "div":
            body.append(f"(c('rsi') > {a.p[0]}) & (c('rsi5') < {a.p[1]})")
            lines.append(a.text)
        elif a.kind == "X":
            body.append(f"_x_{a.p.__name__.split('lay_')[-1]}(df)")
            lines.append(a.text)
    body.append(f"(c('tod') >= {win[0]}) & (c('tod') < {win[1]})")
    lines.append(f"time window: bar close {win[0]:04d} <= tod < {win[1]:04d} ET")
    xs = [a for a in atoms if a.kind == "X"]
    imp = ""
    for a in xs:
        mod = a.p.__name__.split("lay_")[-1]
        imp += (f"import importlib.util as _u, pathlib as _p\n_s = _u.spec_from_file_location('{mod}', _p.Path(__file__).resolve()"
                f".parents[2] / 'escalation/finalists/{mod}.py')\nimport sys as _sys\n_sys.path.insert(0, str(_p.Path(__file__)"
                f".resolve().parents[2] / 'escalation/finalists'))\n_m = _u.module_from_spec(_s)\n_s.loader.exec_module(_m)\n"
                f"_x_{mod} = _m.mask\n")
    doc = (f'"""{tag} - layered setup (layering stage, research/primitives/layering).\n'
           f"Side {layer.SIDE}, exit {row['geom']}. Lab (1c/side): train exp_r {row['exp_r_train']:+.4f}R (n {int(row['n_train'])}, "
           f"day-t {row['t_dc_train']}), valid exp_r {row['exp_r_valid']:+.4f}R (n {int(row['n_valid'])}, day-t {row['t_dc_valid']}),\n"
           f"valid at approx production cost {row['exp_r_prod_valid']:+.4f}R.\n"
           "Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.\n"
           'Educational only - not financial advice."""\n')
    return (doc + "import numpy as np\n" + imp + f"\nSIDE = \"{layer.SIDE}\"\nGEOM = \"{row['geom']}\"\nLAYERS = " +
            json.dumps(lines, indent=4) + "\n\n\ndef mask(df) -> np.ndarray:\n"
            "    def c(k):\n        return df[k].to_numpy(dtype=float)\n\n    with np.errstate(invalid=\"ignore\"):\n        return (" +
            "\n                & ".join(f"({b})" for b in body) + ")\n")


def main():
    d = pd.read_csv(HERE / "results.csv")
    f = d[d.finalist & (d.half1_train > 0) & (d.half2_train > 0) & (d.ex_best_day_valid > 0)
          & (d.t_dc_prod_valid >= 1.5) & (d.days_valid >= 8)].copy()
    f["rank"] = f[["t_dc_train", "t_dc_valid"]].min(axis=1)
    f = f.sort_values("rank", ascending=False)
    pools, xs = layer.build_pools(), layer.x_atoms()
    S = {sp: lab.Split(sp) for sp in ("train", "valid")}
    picked, keys = [], []
    for _, row in f.iterrows():
        atoms, win = atoms_for(row, pools, xs)
        ks = set()
        for sp in S:
            idx = S[sp].first_idx(mask_on(S[sp], atoms, win) & np.isfinite(S[sp].r[("short", row["geom"])]))
            ks |= {(sp, int(i)) for i in S[sp].symday[idx]}
        jac = [len(ks & k) / len(ks | k) for k in keys]
        if jac and max(jac) > 0.5:
            continue
        picked.append((row, atoms, win))
        keys.append(ks)
        if len(picked) == 8:
            break
    # window-shift robustness (+-30 min on both ends) and tod-matched edge
    out = []
    for row, atoms, win in picked:
        tag = row["tag"]
        shifts = {}
        for dl, dh in ((-30, 0), (30, 0), (0, -30), (0, 30)):
            lo = layer.lab  # noqa: F841
            wl = _add(win[0], dl)
            wh = _add(win[1], dh)
            r = {}
            for sp in S:
                e = lab.evaluate(S[sp], mask_on(S[sp], atoms, (wl, wh)), "short", row["geom"])
                r[sp] = e.get("exp_r")
            shifts[f"{wl}-{wh}"] = r
        ctrl = {}
        for sp in S:
            e = lab.evaluate(S[sp], mask_on(S[sp], atoms, win), "short", row["geom"])
            ctrl[sp] = {"exp_r": e["exp_r"], "tod_ctrl": e["ctrl"], "edge_vs_tod": round(e["exp_r"] - e["ctrl"], 4)}
        fn = FIN / f"{tag}.py"
        fn.write_text(module_text(tag, row, atoms, win))
        out.append({"tag": tag, "row": {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in row.items()},
                    "window_shift": shifts, "tod_matched": ctrl, "module": str(fn.relative_to(ROOT))})
    del S
    # verify modules through mcf.research.setup_lab.evaluate on the full frame
    from mcf.research.setup_lab import evaluate, load
    import importlib.util
    cols = sorted(set(lab.FEAT + ["r_short_t1s1", "r_short_t05s1", "r_short_t1s05", "win_short_t1s1", "win_short_t05s1",
                                  "win_short_t1s05"]))
    for sp in ("train", "valid"):
        df = load(sp, data_dir=str(ROOT / "research/setups2/data"), columns=cols)
        assert str(max(df["date"])) < "2026-09-16"
        for o in out:
            s = importlib.util.spec_from_file_location("v", ROOT / o["module"])
            m = importlib.util.module_from_spec(s)
            s.loader.exec_module(m)
            o.setdefault("verify", {})[sp] = evaluate(df, m.mask(df), m.SIDE, m.GEOM)
        del df
    json.dump(out, open(HERE / "finalists.json", "w"), indent=1, default=str)
    for o in out:
        print(o["tag"], {sp: (v["n"], v["exp_r"]) for sp, v in o["verify"].items()},
              "lay:", (o["row"]["n_train"], o["row"]["exp_r_train"], o["row"]["n_valid"], o["row"]["exp_r_valid"]),
              "shift:", o["window_shift"], "tod:", o["tod_matched"])
    print("candidates after filter:", len(f))


def _add(t, m):
    mins = (t // 100) * 60 + t % 100 + m
    return (mins // 60) * 100 + mins % 60


if __name__ == "__main__":
    main()
