"""Layering stage (key: layering): pair the best primitive performers into L2 setups, then L3 from the best pairs.

Educational only - not financial advice. Backtest on the setup-lab frame (research/setups2/data train + valid ONLY;
nothing dated >= 2026-09-16 is read). Costs: lab 1c/share/side in every number; *_prod columns subtract an approximate
production surcharge (+1 bps/side, +2c on stop exits; the 3c extended-tier surcharge is not modelled).

Rules fixed BEFORE the run (see NOTES.md):
  atoms   = every SHORT layer-1 survivor of the primitives stage, in its own window (decile/tail bands, lo < x <= hi)
            + the MarcoFlow ingredient layers (window-free thresholds)
            + the escalation X composites (each in its own window, paired with one extra atom)
  pairs   = two atoms of different metrics, same side, evaluated in a window where both may live, all 3 geometries
  keep    = (a) beats BOTH single layers on train by a real margin:
                pair_tr - max(single_tr) >= max(0.03R, 0.5 x pair train day-clustered SE)
            (b) holds on valid: valid exp_r >= max(single valid exp_r)
            (c) finalist gate: train > 0, valid > 0, valid n >= 30, valid day-t >= 1.5, plateau mean > 0 on train
                AND valid (one-step neighbour of each atom, the other atom(s) fixed), beats the same-side same-window
                random baseline on train and valid
  L3      = the 25 best kept pairs (min(train t, valid t)) + one more atom from the same window pool; same rules with
            "single layers" replaced by the three sub-pairs (AB, AC, BC).
Run from the repo root:  python research/primitives/layering/layer.py      (~1.5 GB, one process)
"""
from __future__ import annotations

import gc
import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research/primitives/escalation"))
sys.path.insert(0, str(ROOT / "research/primitives/escalation/finalists"))
import lab  # noqa: E402

GEOMS = ("t1s1", "t05s1", "t1s05")
SIDE = "short"
WINDOWS = {"W1": (950, 1030), "WO": (950, 1100), "W2": (1030, 1130), "W3": (1130, 1300), "W4": (1300, 1430),
           "W5": (1430, 1501), "WALL": (950, 1501)}
WLABEL = {"W1": "09:50-10:30", "WO": "09:50-11:00", "W2": "10:30-11:30", "W3": "11:30-13:00", "W4": "13:00-14:30",
          "W5": "14:30-15:00", "WALL": "09:50-15:00"}
EXTRA = ["atrPct", "dist_round_atr"]
for c in EXTRA:
    if c not in lab.FEAT:
        lab.FEAT.append(c)

# ---------------------------------------------------------------------------------------------- atoms
MM = json.load(open(ROOT / "research/primitives/primitives/metric_map.json"))
BANDS = {m: {b["band"]: (float(b["lo"]), float(b["hi"])) for b in v["bands"]} for m, v in MM["bands"].items()}


def band_neighbours(band: str, have: dict) -> list[str]:
    if band.startswith("D"):
        i = int(band[1:])
        out = [f"D{i - 1}", f"D{i + 1}"]
    else:
        out = {"V1": ["V2"], "V2": ["V1", "D2"], "V19": ["D9", "V20"], "V20": ["V19"]}[band]
    return [b for b in out if b in have]


class Atom:
    """One layer: a boolean condition over lab columns. kind band: lo < x <= hi; gt: x > v; lt: x < v (MarcoFlow uses
    strict inequalities, as in research/primitives/marcoflow); eq: x == v; div: rsi > a and rsi5 < b; X: module mask."""

    def __init__(self, name, metric, kind, p, nbrs=(), text=""):
        self.name, self.metric, self.kind, self.p, self.nbrs, self.text = name, metric, kind, p, list(nbrs), text

    def mask(self, S):
        c = S.c
        with np.errstate(invalid="ignore"):
            if self.kind == "band":
                x = c[self.metric].astype(np.float64)
                return (x > self.p[0]) & (x <= self.p[1])
            if self.kind == "gt":
                return c[self.metric].astype(np.float64) > self.p
            if self.kind == "lt":
                return c[self.metric].astype(np.float64) < self.p
            if self.kind == "eq":
                return c[self.metric] == self.p
            if self.kind == "div":
                return (c["rsi"] > self.p[0]) & (c["rsi5"] < self.p[1])
            if self.kind == "X":
                return np.asarray(self.p.mask(_Shim(c)), bool)
        raise ValueError(self.kind)


class _Shim:
    def __init__(self, c):
        self.c = c

    def __getitem__(self, k):
        return pd.Series(self.c[k], copy=False)


def prim_atom(metric, band):
    lo, hi = BANDS[metric][band]
    nb = []
    for b in band_neighbours(band, BANDS[metric]):
        nlo, nhi = BANDS[metric][b]
        nb.append(Atom(f"{metric}_{b}", metric, "band", (nlo, nhi)))
    txt = f"{'' if lo == -np.inf else f'{lo:.4g} < '}{metric}{'' if hi == np.inf else f' <= {hi:.4g}'} ({band})"
    return Atom(f"{metric}_{band}", metric, "band", (lo, hi), nb, txt)


def mf_atoms():
    def thr(name, metric, kind, v, step, text):
        return Atom(name, metric, kind, v, [Atom(f"{name}~{v - step:g}", metric, kind, v - step),
                                            Atom(f"{name}~{v + step:g}", metric, kind, v + step)], text)
    out = [
        thr("heat30", "heat", "lt", -29.999, 5, "heat <= -30 (MarcoFlow bearish heat signal)"),
        thr("heat40", "heat", "lt", -39.999, 5, "heat <= -40"),
        thr("bp25", "buyPressure", "lt", -0.25, 0.1, "buyPressure < -0.25 (flow-sell)"),
        thr("bp15", "buyPressure", "lt", -0.15, 0.1, "buyPressure < -0.15 (flow-aligned)"),
        thr("vwapup", "vwapDistPct", "gt", 0.05, 0.1, "vwapDistPct > +0.05% (above VWAP)"),
        thr("rsi5hi", "rsi5", "gt", 70, 5, "RSI(5) > 70"),
        thr("rsiob", "rsi", "gt", 65, 5, "RSI(14) > 65"),
        thr("momfall", "rsiSlope", "lt", -1.0, 1.0, "RSI(14) 3-bar slope < -1"),
    ]
    out.append(Atom("rsidivbear", "rsidiv", "div", (65, 60),
                    [Atom("rsidivbear~60/55", "rsidiv", "div", (60, 55)), Atom("rsidivbear~70/65", "rsidiv", "div", (70, 65))],
                    "RSI(14) > 65 and RSI(5) < 60 (bearish RSI divergence)"))
    return out


def x_atoms():
    import importlib.util
    spec = {"Xgapfade": ("x_gapfade_early", (950, 1031)), "Xgapfadeb": ("x_gapfade_early_b", (950, 1031)),
            "Xfailbo": ("x_failbo", (1000, 1101)), "Xvwaploss": ("x_vwaploss_run", (1000, 1301)),
            "Xlodbreak": ("x_lodbreak_early", (950, 1031))}
    out = {}
    for nm, (mod, win) in spec.items():
        p = ROOT / f"research/primitives/escalation/finalists/{mod}.py"
        s = importlib.util.spec_from_file_location(f"lay_{mod}", p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        if m.SIDE != SIDE:
            continue
        out[nm] = (Atom(nm, "X_" + nm, "X", m, [], f"{nm}: " + "; ".join(m.LAYERS)), win, m.GEOM)
    return out


def build_pools():
    r = pd.read_csv(ROOT / "research/primitives/primitives/results.csv")
    s = r[(r.survivor == True) & (r.side == SIDE)]  # noqa: E712
    pools = {w: {} for w in WINDOWS}
    for (w, m, b), _ in s.groupby(["window", "metric", "band"]):
        if m == "vwapReclaim":
            a = Atom("vwapReclaim_-1", "vwapReclaim", "eq", -1.0, [], "vwapReclaim == -1 (crossed below VWAP <= 3 bars ago)")
        else:
            a = prim_atom(m, b)
        pools[w][a.name] = a
    mf = mf_atoms()
    for w in ("W1", "WO", "W2", "W3", "W4", "W5", "WALL"):
        for a in mf:
            pools[w][a.name] = a
    return pools


# ---------------------------------------------------------------------------------------------- scoring
class Win:
    """A split restricted to one time window (rows in order), with atom-mask cache."""

    def __init__(self, S, lo, hi):
        tod = S.c["tod"]
        self.sub = lab.Sub(S, (tod >= lo) & (tod < hi))
        self.cache = {}
        self.base = {g: float(np.nanmean(self.sub.r[(SIDE, g)])) for g in GEOMS}

    def m(self, a: Atom):
        if a.name not in self.cache:
            self.cache[a.name] = a.mask(self.sub)
        return self.cache[a.name]


N_CONFIGS = {"singles": 0, "pairs": 0, "pair_neighbours": 0, "triples": 0, "triple_neighbours": 0, "x_pairs": 0}


def score(wins, atoms, geom, count=None):
    out = {}
    for sp, W in wins.items():
        m = np.ones(W.sub.n, bool)
        for a in atoms:
            m &= W.m(a)
        e = lab.evaluate(W.sub, m, SIDE, geom)
        e["base"] = round(W.base[geom], 4)
        out[sp] = e
    if count:
        N_CONFIGS[count] += 1
    return out


def se_of(e):
    return abs(e["exp_r"] / e["t_dc"]) if e.get("t_dc") else np.inf


def plateau(wins, atoms, geom, count):
    vals = {"train": [], "valid": []}
    for i, a in enumerate(atoms):
        for nb in a.nbrs:
            alt = atoms[:i] + [nb] + atoms[i + 1:]
            r = score(wins, alt, geom, count)
            for sp in vals:
                if r[sp].get("n", 0) > 0:
                    vals[sp].append(r[sp]["exp_r"])
    return {sp: (round(float(np.mean(v)), 4) if v else None, round(float(np.min(v)), 4) if v else None, len(v))
            for sp, v in vals.items()}


def gate(e, pl):
    tr, va = e["train"], e["valid"]
    if tr.get("n", 0) == 0 or va.get("n", 0) == 0:
        return False
    return (tr["exp_r"] > 0 and va["exp_r"] > 0 and va["n"] >= 30 and (va.get("t_dc") or 0) >= 1.5
            and pl["train"][0] is not None and pl["train"][0] > 0 and pl["valid"][0] is not None and pl["valid"][0] > 0
            and tr["exp_r"] > tr["base"] and va["exp_r"] > va["base"])


def margin_ok(e, parents):
    tr, va = e["train"], e["valid"]
    if tr.get("n", 0) < 20 or va.get("n", 0) == 0 or any(p["train"].get("n", 0) == 0 for p in parents):
        return False, None
    best_tr = max(p["train"]["exp_r"] for p in parents)
    best_va = max(p["valid"].get("exp_r", -9) for p in parents)
    need = max(0.03, 0.5 * se_of(tr))
    m = tr["exp_r"] - best_tr
    return (m >= need and va["exp_r"] >= best_va), round(m, 4)


def flat(tag, window, geom, atoms, e, pl, margin, parents_desc, keep, fin):
    row = {"tag": tag, "window": window, "geom": geom, "atoms": "+".join(a.name for a in atoms), "margin_tr": margin,
           "keep": keep, "finalist": fin, "parents": parents_desc}
    for sp in ("train", "valid"):
        for k in ("n", "days", "exp_r", "t_dc", "exp_r_prod", "t_dc_prod", "ex_best_day", "green_days", "ctrl", "base",
                  "half1", "half2", "win_rate"):
            row[f"{k}_{sp}"] = e[sp].get(k)
    if pl:
        row.update({"plat_tr": pl["train"][0], "plat_tr_min": pl["train"][1], "plat_va": pl["valid"][0],
                    "plat_va_min": pl["valid"][1], "plat_k": pl["valid"][2]})
    return row


SHORT = {"heat30": "heat30", "heat40": "heat40", "bp25": "flowsell", "bp15": "flowalign", "vwapup": "vwapup",
         "rsi5hi": "rsi5hi", "rsiob": "rsiob", "momfall": "momfall", "rsidivbear": "rsidiv"}


def tagpart(a):
    return SHORT.get(a.name, a.name.replace("_", ""))


def main():
    t0 = time.time()
    S = {sp: lab.Split(sp) for sp in ("train", "valid")}
    print(f"loaded {time.time() - t0:.0f}s", flush=True)
    pools = build_pools()
    xs = x_atoms()
    rows = []
    singles = {}
    pair_res = {}
    seen3 = set()

    def single(w, wins, a, g):
        k = (w, a.name, g)
        if k not in singles:
            singles[k] = score(wins, [a], g, "singles")
        return singles[k]

    for w, (lo, hi) in WINDOWS.items():
        pool = pools[w]
        if len(pool) < 2:
            continue
        wins = {sp: Win(S[sp], lo, hi) for sp in S}
        names = sorted(pool)
        for g in GEOMS:
            for a1, a2 in combinations(names, 2):
                A, B = pool[a1], pool[a2]
                if A.metric == B.metric:
                    continue
                e = score(wins, [A, B], g, "pairs")
                pair_res[(w, g, frozenset((a1, a2)))] = e
                pa, pb = single(w, wins, A, g), single(w, wins, B, g)
                keep, mg = margin_ok(e, [pa, pb])
                pl, fin = None, False
                if keep and e["valid"].get("n", 0) >= 30 and (e["valid"].get("t_dc") or 0) >= 1.5:
                    pl = plateau(wins, [A, B], g, "pair_neighbours")
                    fin = gate(e, pl)
                tag = f"L2-{tagpart(A)}+{tagpart(B)}-short-{w}-{g}"
                rows.append(flat(tag, w, g, [A, B], e, pl, mg,
                                 f"{a1}: tr {pa['train'].get('exp_r')} va {pa['valid'].get('exp_r')} | "
                                 f"{a2}: tr {pb['train'].get('exp_r')} va {pb['valid'].get('exp_r')}", keep, fin))
        # ---- L3 from this window's best kept pairs (by min train t / valid t)
        kept = [r for r in rows if r["window"] == w and r["keep"] and r["finalist"]]
        kept.sort(key=lambda r: -min(r["t_dc_train"] or -9, r["t_dc_valid"] or -9))
        for r in kept[:25]:
            g = r["geom"]
            a1, a2 = r["atoms"].split("+")
            for a3 in names:
                if a3 in (a1, a2) or pool[a3].metric in (pool[a1].metric, pool[a2].metric):
                    continue
                trio = [pool[a1], pool[a2], pool[a3]]
                key3 = (w, g, frozenset((a1, a2, a3)))
                if key3 in seen3:
                    continue
                seen3.add(key3)
                e = score(wins, trio, g, "triples")
                subs = [pair_res.get((w, g, frozenset(p))) for p in combinations((a1, a2, a3), 2)]
                if any(s is None for s in subs):
                    continue
                keep, mg = margin_ok(e, subs)
                pl, fin = None, False
                if keep and e["valid"].get("n", 0) >= 30 and (e["valid"].get("t_dc") or 0) >= 1.5:
                    pl = plateau(wins, trio, g, "triple_neighbours")
                    fin = gate(e, pl)
                tag = "L3-" + "+".join(tagpart(a) for a in trio) + f"-short-{w}-{g}"
                rows.append(flat(tag, w, g, trio, e, pl, mg, "sub-pairs " + " | ".join(
                    f"tr {s['train'].get('exp_r')} va {s['valid'].get('exp_r')}" for s in subs), keep, fin))
        print(f"{w}: {len(rows)} rows, {N_CONFIGS} {time.time() - t0:.0f}s", flush=True)
        del wins
        gc.collect()

    # ---- X composites + one atom (escalation finalists as a base layer)
    for nm, (X, (lo, hi), xg) in xs.items():
        wins = {sp: Win(S[sp], lo, hi) for sp in S}
        pool = {}
        for w, (wl, wh) in WINDOWS.items():
            if w == "WALL":
                continue
            if wl < hi and wh > lo:
                pool.update(pools[w])
        for g in GEOMS:
            px = score(wins, [X], g, "singles")
            for an, A in sorted(pool.items()):
                e = score(wins, [X, A], g, "x_pairs")
                pa = score(wins, [A], g, "singles")
                keep, mg = margin_ok(e, [px, pa])
                pl, fin = None, False
                if keep and e["valid"].get("n", 0) >= 30 and (e["valid"].get("t_dc") or 0) >= 1.5:
                    pl = plateau(wins, [X, A], g, "pair_neighbours")
                    fin = gate(e, pl)
                rows.append(flat(f"L2-{nm}+{tagpart(A)}-short-{g}", f"{nm}:{lo}-{hi}", g, [X, A], e, pl, mg,
                                 f"{nm}: tr {px['train'].get('exp_r')} va {px['valid'].get('exp_r')} | "
                                 f"{an}: tr {pa['train'].get('exp_r')} va {pa['valid'].get('exp_r')}", keep, fin))
        print(f"{nm}: {len(rows)} rows {time.time() - t0:.0f}s", flush=True)
        del wins
        gc.collect()

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "results.csv", index=False)
    meta = {"configs": dict(N_CONFIGS), "configs_total": int(sum(N_CONFIGS.values())), "kept": int(df.keep.sum()),
            "finalist_gate": int(df.finalist.sum()), "seconds": round(time.time() - t0),
            "educational_only": "Educational only - not financial advice."}
    json.dump(meta, open(OUT / "counts.json", "w"), indent=1)
    print(meta)


if __name__ == "__main__":
    main()
