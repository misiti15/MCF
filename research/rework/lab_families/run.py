"""Rule-18 rework of the failed layered-setup families (key lab_families).

Educational only -- not financial advice.
Grid pre-declared in NOTES.md. Train + valid only (research/setups2/data); the test split is never touched.
    python research/rework/lab_families/run.py
"""
from __future__ import annotations

import gc
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research.setup_lab import load  # noqa: E402

OUT = Path(__file__).resolve().parent
GEOMS = ("t1s1", "t05s1", "t1s05")
TOL = 1e-9

BASE_COLS = ["close", "low", "atr_d", "tod", "symbol", "date", "rsi", "rsi5", "fromOpen", "vwapDistPct", "sma50_dist_pct",
             "sma20_dist_pct", "sma20_slope_pct", "gap", "macdPct", "emaDiff", "momentum", "rsiSlope", "dist_pdh_atr",
             "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "dist_round_atr", "flow3", "flow9prev", "vol_climax",
             "bear_div", "bull_div", "upper_wick", "lower_wick", "volumeRatio", "buyPressure"]
OUT_COLS = [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in GEOMS]


# ------------------------------------------------------------------------------------------------- data
class Split:
    def __init__(self, name: str):
        df = load(name, data_dir=str(ROOT / "research/setups2/data"), columns=BASE_COLS + OUT_COLS)
        assert str(max(df["date"])) < "2026-09-16", "locked dates present"
        atr = df["atr_d"].to_numpy(np.float64)
        close = df["close"].to_numpy(np.float64)
        self.c = {}
        for k in BASE_COLS:
            if k not in ("symbol", "date", "close", "low", "atr_d"):
                self.c[k] = df[k].to_numpy()
        self.c["lowpdl"] = ((df["low"].to_numpy(np.float64) - close) / atr + df["dist_pdl_atr"].to_numpy(np.float64)).astype(np.float32)
        for k, src in (("vwap_atr", "vwapDistPct"), ("sma20_atr", "sma20_dist_pct"), ("sma50_atr", "sma50_dist_pct")):
            self.c[k] = (df[src].to_numpy(np.float64) * close / 100 / atr).astype(np.float32)
        self.c["flowflip"] = (df["flow3"].to_numpy(np.float64) - df["flow9prev"].to_numpy(np.float64)).astype(np.float32)
        d = pd.factorize(df["date"], sort=True)
        self.date_id, self.dates = d[0].astype(np.int32), d[1]
        sd = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        ids = np.r_[0, np.cumsum(sd[1:] != sd[:-1])].astype(np.int32)  # data is sorted by symbol, date, tod
        self.symday = ids
        tod = df['tod'].to_numpy()
        assert not np.any((ids[1:] == ids[:-1]) & (tod[1:] <= tod[:-1])), 'not sorted'
        del sd
        self.r, self.w, self.ctrl = {}, {}, {}
        key = self.date_id.astype(np.int64) * 10000 + self.c["tod"].astype(np.int64)
        for s in ("long", "short"):
            for g in GEOMS:
                r = df[f"r_{s}_{g}"].to_numpy(np.float32)
                self.r[(s, g)] = r
                self.w[(s, g)] = df[f"win_{s}_{g}"].to_numpy(np.float32)
                ok = np.isfinite(r)
                cm = pd.Series(r[ok]).groupby(key[ok]).mean()
                self.ctrl[(s, g)] = cm.reindex(key).to_numpy(np.float32)
        del df
        gc.collect()
        self.n = len(self.symday)


def cond_mask(S: Split, col: str, op: str, val) -> np.ndarray:
    x = S.c[col]
    with np.errstate(invalid="ignore"):
        if op == "<":
            return x < val
        if op == ">":
            return x > val
        if op == "<=":
            return x <= val + TOL
        if op == ">=":
            return x >= val - TOL
        if op == "==":
            return x == val
        if op == "in":
            return (x >= val[0]) & (x <= val[1])
    raise ValueError(op)


def evaluate(S: Split, m: np.ndarray, side: str, geom: str) -> dict:
    r_all = S.r[(side, geom)]
    m = m & np.isfinite(r_all)
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return {"n": 0}
    ids = S.symday[idx]
    idx = idx[np.r_[True, ids[1:] != ids[:-1]]]
    r = r_all[idx].astype(np.float64)
    w = S.w[(side, geom)][idx].astype(np.float64)
    di = S.date_id[idx]
    n = len(r)
    mu = r.mean()
    sums = np.bincount(di, weights=r, minlength=len(S.dates))
    cnt = np.bincount(di, minlength=len(S.dates))
    act = cnt > 0
    dm = sums[act] - cnt[act] * mu
    se = float(np.sqrt((dm ** 2).sum()) / n) if act.sum() > 1 else float("nan")
    best = int(np.argmax(np.where(act, sums, -np.inf)))
    exb = (r.sum() - sums[best]) / (n - cnt[best]) if n > cnt[best] else float("nan")
    ctrl = S.ctrl[(side, geom)][idx].astype(np.float64)
    days = np.flatnonzero(act)
    half = days[len(days) // 2]
    h1, h2 = r[di < half], r[di >= half]
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    return {"n": n, "days": int(act.sum()), "win_rate": round(float(np.nanmean(w)), 4), "exp_r": round(float(mu), 4),
            "t_dc": round(mu / se, 2) if se and se > 0 else None, "pf": round(float(gw / gl), 3) if gl > 0 else None,
            "green_days": round(float((sums[act] > 0).mean()), 3),
            "ex_best_day": round(float(exb), 4), "ctrl": round(float(np.nanmean(ctrl)), 4),
            "half1": round(float(h1.mean()), 4) if len(h1) else None, "half2": round(float(h2.mean()), 4) if len(h2) else None}


# ------------------------------------------------------------------------------------------------- specs
def P(name, col, op, grid, idx=2):
    return {"name": name, "col": col, "op": op, "grid": list(grid), "idx": idx}


def F(name, col, op, val):
    return {"name": name, "col": col, "op": op, "val": val}


def val(c):
    return c["grid"][c["idx"]] if "grid" in c else c["val"]


FAMILIES = {
    "OL1": ("short", [P("rsi", "rsi", "<", [20, 22.5, 25, 27.5, 30]), F("pdl_break", "lowpdl", "<=", 0.0),
                      F("above_pdl", "dist_pdl_atr", ">", 0.0), P("pdl_dist", "dist_pdl_atr", "<=", [.1, .15, .2, .3, .4]),
                      P("lwick", "lower_wick", ">=", [.3, .4, .5, .6, .7]), P("tod_hi", "tod", "<=", [1030, 1100, 1130, 1200, 1230])]),
    "TP": ("short", [P("fromOpen", "fromOpen", "<", [-1, -.75, -.5, -.25, 0]), P("vwap", "vwapDistPct", "<", [-.4, -.2, 0, .2, .4]),
                     P("sma50", "sma50_dist_pct", "<", [-.4, -.2, 0, .2, .4]), P("sma20", "sma20_dist_pct", ">", [-.2, -.1, 0, .1, .2]),
                     P("tod_hi", "tod", "<=", [1000, 1015, 1030, 1100, 1130])]),
    "WG1": ("short", [P("gap", "gap", "<", [-1, -.7, -.445, -.2, 0]), P("sma50", "sma50_dist_pct", ">", [1.5, 1.85, 2.19, 2.5, 3.0]),
                      P("tod_lo", "tod", ">=", [1200, 1230, 1300, 1330, 1400])]),
    "WG2": ("short", [P("macd", "macdPct", ">", [.2, .3, .399, .5, .6]), P("pdh", "dist_pdh_atr", ">", [.6, .75, .95, 1.15, 1.35]),
                      P("flow3", "flow3", ">", [.2, .3, .376, .45, .55])]),
    "WG3": ("long", [P("macd", "macdPct", "<", [-1.5, -1.25, -1.06, -.85, -.65]), P("rsiSlope", "rsiSlope", ">", [17, 20, 23.7, 27, 30]),
                     P("momentum", "momentum", ">", [.3, .45, .569, .7, .85])]),
    "VF": ("short", [P("rsi5", "rsi5", ">", [80, 85, 90, 93, 95]), P("sma20", "sma20_dist_pct", ">", [.5, .75, 1, 1.25, 1.5]),
                     F("bear_div", "bear_div", "==", 1.0), P("tod_lo", "tod", ">=", [1200, 1230, 1300, 1330, 1400]),
                     F("tod_hi", "tod", "<=", 1500)]),
    "OVM_L": ("long", [P("rsi5", "rsi5", ">", [80, 85, 90, 93, 95]), P("vwap", "vwap_atr", "<", [.25, .1, 0, -.1, -.25]),
                       P("sma50", "sma50_atr", "<", [-.25, -.375, -.5, -.625, -.75])]),
    "OVM_S": ("short", [P("rsi5", "rsi5", ">", [90, 93, 95, 97, 98]), P("vwap", "vwap_atr", ">", [.4, .5, .6, .7, .8]),
                        P("sma20", "sma20_atr", ">", [.3, .4, .5, .6, .7])]),
}

# indicator-length swaps: condition name -> replacement column (grid re-mapped by matching train tail fractions)
SWAPS = {
    "OL1": {"rsi_to_rsi5": {"rsi": "rsi5"}},
    "TP": {"sma20_sma50": {"sma20": "sma50_dist_pct", "sma50": "sma20_dist_pct"}, "sma50_to_ema": {"sma50": "emaDiff"}},
    "WG1": {"sma50_to_sma20": {"sma50": "sma20_dist_pct"}},
    "WG2": {"macd_to_ema": {"macd": "emaDiff"}, "flow3_to_flip": {"flow3": "flowflip"}},
    "WG3": {"macd_to_ema": {"macd": "emaDiff"}},
    "VF": {"rsi5_to_rsi": {"rsi5": "rsi"}, "sma20_to_sma50": {"sma20": "sma50_dist_pct"}},
    "OVM_L": {"rsi5_to_rsi": {"rsi5": "rsi"}, "sma50_to_sma20": {"sma50": "sma20_atr"}},
    "OVM_S": {"rsi5_to_rsi": {"rsi5": "rsi"}, "sma20_to_sma50": {"sma20": "sma50_atr"}},
}

LIBRARY = [
    P("+vwap>0", "vwapDistPct", ">", [-.4, -.2, 0, .2, .4]), P("+vwap<0", "vwapDistPct", "<", [-.4, -.2, 0, .2, .4]),
    P("+vwap>1", "vwapDistPct", ">", [.5, .75, 1, 1.5, 2]), P("+vwap<-1", "vwapDistPct", "<", [-2, -1.5, -1, -.75, -.5]),
    P("+sma20>0", "sma20_dist_pct", ">", [-.2, -.1, 0, .1, .2]), P("+sma20<0", "sma20_dist_pct", "<", [-.2, -.1, 0, .1, .2]),
    P("+sma50>0", "sma50_dist_pct", ">", [-.4, -.2, 0, .2, .4]), P("+sma50<0", "sma50_dist_pct", "<", [-.4, -.2, 0, .2, .4]),
    P("+slope20>0", "sma20_slope_pct", ">", [-.2, -.1, 0, .1, .2]), P("+slope20<0", "sma20_slope_pct", "<", [-.2, -.1, 0, .1, .2]),
    P("+pdh<.25", "dist_pdh_atr", "<", [.1, .175, .25, .375, .5]), P("+pdh>1", "dist_pdh_atr", ">", [.5, .75, 1, 1.25, 1.5]),
    P("+pdl<.25", "dist_pdl_atr", "<", [.1, .175, .25, .375, .5]), P("+pdl>1", "dist_pdl_atr", ">", [.5, .75, 1, 1.25, 1.5]),
    P("+hod<.1", "dist_hod_atr", "<", [.03, .06, .1, .15, .2]), P("+hod>.5", "dist_hod_atr", ">", [.25, .375, .5, .75, 1]),
    P("+lod<.1", "dist_lod_atr", "<", [.03, .06, .1, .15, .2]), P("+lod>.5", "dist_lod_atr", ">", [.25, .375, .5, .75, 1]),
    P("+round<.1", "dist_round_atr", "<", [.03, .06, .1, .15, .2]),
    P("+flow3>.3", "flow3", ">", [.1, .2, .3, .4, .5]), P("+flow3<-.3", "flow3", "<", [-.5, -.4, -.3, -.2, -.1]),
    P("+flip>.5", "flowflip", ">", [.25, .375, .5, .75, 1]), P("+flip<-.5", "flowflip", "<", [-1, -.75, -.5, -.375, -.25]),
    P("+climax>2", "vol_climax", ">", [1.5, 1.75, 2, 2.5, 3]), P("+climax<1", "vol_climax", "<", [.6, .8, 1, 1.2, 1.4]),
    F("+bear_div", "bear_div", "==", 1.0), F("+bull_div", "bull_div", "==", 1.0),
    P("+uwick>=.4", "upper_wick", ">=", [.2, .3, .4, .5, .6]), P("+lwick>=.4", "lower_wick", ">=", [.2, .3, .4, .5, .6]),
    P("+vr>1.5", "volumeRatio", ">", [1.0, 1.25, 1.5, 2, 2.5]), P("+vr<.8", "volumeRatio", "<", [.5, .65, .8, .9, 1.0]),
    P("+bp>.3", "buyPressure", ">", [.1, .2, .3, .4, .5]), P("+bp<-.3", "buyPressure", "<", [-.5, -.4, -.3, -.2, -.1]),
    P("+tod<=1130", "tod", "<=", [1030, 1100, 1130, 1200, 1230]), P("+tod>=1100", "tod", ">=", [1000, 1030, 1100, 1130, 1200]),
    P("+tod>=1300", "tod", ">=", [1200, 1230, 1300, 1330, 1400]), F("+tod1000-1400", "tod", "in", (1000, 1400)),
]
assert len(LIBRARY) == 37


def remap_grid(S: Split, c: dict, newcol: str) -> dict:
    """Same tail fraction on train for the new indicator (keeps selectivity, swaps the length)."""
    x_old = S.c[c["col"]][np.isfinite(S.c[c["col"]])]
    x_new = S.c[newcol][np.isfinite(S.c[newcol])]
    rng = np.random.default_rng(0)
    xo, xn = rng.choice(x_old, 400_000, replace=False), rng.choice(x_new, 400_000, replace=False)
    g = []
    for v in c["grid"]:
        frac = (xo < v).mean() if c["op"] in ("<", "<=") else (xo <= v).mean()
        g.append(round(float(np.quantile(xn, frac)), 4))
    return {**c, "col": newcol, "grid": g, "name": c["name"] + "~" + newcol}


# ------------------------------------------------------------------------------------------------- configs
def key(conds, geom):
    return geom + "|" + "&".join(sorted(f"{c['col']}{c['op']}{val(c)}" for c in conds))


def apply(base, op, S, fam):
    conds = [dict(c) for c in base]
    kind = op[0]
    if kind == "move":
        for c in conds:
            if c["name"] == op[1]:
                c["idx"] = op[2]
    elif kind == "drop":
        conds = [c for c in conds if c["name"] != op[1]]
    elif kind == "add":
        conds.append(dict(next(l for l in LIBRARY if l["name"] == op[1])))
    elif kind == "swap":
        mp = SWAPS[fam][op[1]] if op[1] != "swap_all" else {k: v for d in SWAPS[fam].values() for k, v in d.items()}
        conds = [remap_grid(S, c, mp[c["name"]]) if c["name"] in mp else c for c in conds]
    return conds


def touched(op):
    if op[0] in ("move", "drop"):
        return {op[1]}
    if op[0] == "add":
        return {op[1]}
    if op[0] == "swap":
        return {"swap"}
    return set()


def neighbours(conds):
    out = []
    for i, c in enumerate(conds):
        if "grid" not in c:
            continue
        for d in (-1, 1):
            j = c["idx"] + d
            if 0 <= j < len(c["grid"]):
                nc = [dict(x) for x in conds]
                nc[i]["idx"] = j
                out.append(nc)
    return out


def window(conds):
    lo, hi = 950, 1500
    for c in conds:
        if c["col"] == "tod":
            v = val(c)
            if c["op"] in (">=", ">"):
                lo = max(lo, v)
            elif c["op"] in ("<=", "<"):
                hi = min(hi, v)
            elif c["op"] == "in":
                lo, hi = max(lo, v[0]), min(hi, v[1])
    return lo, hi


def main():
    t0 = time.time()
    TR = Split("train")
    print("train loaded", TR.n, round(time.time() - t0), flush=True)
    VA = Split("valid")
    print("valid loaded", VA.n, round(time.time() - t0), flush=True)
    rows, seen = [], {}
    base_cache = {}

    def mask(S, conds):
        m = np.ones(S.n, bool)
        for c in conds:
            m &= cond_mask(S, c["col"], c["op"], val(c))
        return m

    def wbase(S, side, geom, lo, hi):
        k = (id(S), side, geom, lo, hi)
        if k not in base_cache:
            base_cache[k] = evaluate(S, cond_mask(S, "tod", "in", (lo, hi)), side, geom).get("exp_r")
        return base_cache[k]

    def score(fam, side, label, conds, stage, splits=("train",)):
        """Score one mask in all 3 geometries; returns the rows. Each (mask, geom) not seen before counts as a config."""
        out = []
        ms = {nm: mask(S, conds) for nm, S in (("train", TR), ("valid", VA)) if nm in splits}
        for g in GEOMS:
            k = key(conds, g) + "|" + side
            if k in seen:
                row = seen[k]
                for nm in splits:
                    if nm not in row:
                        S = TR if nm == "train" else VA
                        row[nm] = evaluate(S, ms[nm], side, g)
                        lo, hi = window(conds)
                        row[nm]["window_base"] = wbase(S, side, g, lo, hi)
                out.append(row)
                continue
            row = {"family": fam, "side": side, "geom": g, "label": label, "stage": stage,
                   "conds": [{"col": c["col"], "op": c["op"], "val": val(c), "name": c["name"], **({"grid": c["grid"], "idx": c["idx"]} if "grid" in c else {})} for c in conds]}
            for nm in splits:
                S = TR if nm == "train" else VA
                row[nm] = evaluate(S, ms[nm], side, g)
                lo, hi = window(conds)
                row[nm]["window_base"] = wbase(S, side, g, lo, hi)
            seen[k] = row
            rows.append(row)
            out.append(row)
        return out

    def best_t(rs):
        ts = [r["train"].get("t_dc") or -9 for r in rs if r["train"].get("n", 0) >= 100]
        return max(ts) if ts else -9

    fam_ops = {}
    for fam, (side, base) in FAMILIES.items():
        ops = [("base",)]
        for c in base:
            if "grid" in c:
                for d in (-2, -1, 1, 2):
                    ops.append(("move", c["name"], c["idx"] + d))
        ops += [("drop", c["name"]) for c in base]
        ops += [("swap", s) for s in SWAPS[fam]]
        if len(SWAPS[fam]) > 1:
            ops.append(("swap", "swap_all"))
        names = {c["name"] for c in base}
        ops += [("add", l["name"]) for l in LIBRARY if not any(l["col"] == c["col"] and l["op"] == c["op"] for c in base)]
        single = []
        for op in ops:
            conds = apply(base, op, TR, fam) if op[0] != "base" else [dict(c) for c in base]
            label = ":".join(map(str, op))
            rs = score(fam, side, label, conds, "base" if op[0] == "base" else op[0])
            if op[0] != "base":
                single.append((best_t(rs), op))
        single.sort(key=lambda z: -z[0])
        top = [op for t, op in single[:8]]
        for a, b in itertools.combinations(top, 2):
            if touched(a) & touched(b):
                continue
            conds = apply(apply(base, a, TR, fam), b, TR, fam)
            score(fam, side, ":".join(map(str, a)) + " + " + ":".join(map(str, b)), conds, "pair")
        fam_ops[fam] = top
        print(fam, "done; configs so far", len(rows), round(time.time() - t0), flush=True)

    n_search = len(rows)
    # train eligibility -> valid
    elig = [r for r in rows if r["train"].get("n", 0) >= 100 and r["train"]["exp_r"] > 0 and (r["train"].get("t_dc") or 0) >= 1.5]
    print("eligible on train", len(elig), flush=True)
    for r in elig:
        conds = [dict(c) for c in r["conds"]]
        score(r["family"], r["side"], r["label"], conds, r["stage"], splits=("train", "valid"))
        r["eligible"] = True
    # gate + plateau
    cands = []
    for r in elig:
        v = r["valid"]
        if not (v.get("n", 0) >= 30 and v["exp_r"] > 0 and (v.get("t_dc") or 0) >= 1.5):
            continue
        nb_rows = []
        for nc in neighbours([dict(c) for c in r["conds"]]):
            for x in score(r["family"], r["side"], r["label"] + " [nb]", nc, "plateau", splits=("train", "valid")):
                if x["geom"] == r["geom"]:
                    nb_rows.append(x)
        vals = [x["valid"].get("exp_r", -1) if x["valid"].get("n", 0) else -1 for x in nb_rows]
        r["plateau"] = {"n_nb": len(vals), "mean_valid_exp_r": round(float(np.mean(vals)), 4) if vals else None,
                        "frac_pos": round(float(np.mean([x > 0 for x in vals])), 3) if vals else None}
        r["beats_baseline"] = bool(v["exp_r"] > (v["window_base"] if v["window_base"] is not None else -9) and v["exp_r"] > v["ctrl"])
        r["gate"] = bool(vals and r["plateau"]["mean_valid_exp_r"] > 0 and r["plateau"]["frac_pos"] >= 2 / 3 and r["beats_baseline"])
        cands.append(r)
    cands.sort(key=lambda r: -(r["valid"].get("t_dc") or 0))
    finalists, used = [], set()
    for r in cands:
        if r["gate"] and r["family"] not in used and len(finalists) < 3:
            finalists.append(r)
            used.add(r["family"])
    res = {"key": "lab_families", "configs_tried": len(rows), "configs_search_stage": n_search,
           "eligible_on_train": len(elig), "valid_gate_candidates": len(cands),
           "finalists": [{"family": r["family"], "side": r["side"], "geom": r["geom"], "label": r["label"], "conds": r["conds"],
                          "train": r["train"], "valid": r["valid"], "plateau": r["plateau"]} for r in finalists],
           "top_pairs_per_family": {f: [":".join(map(str, o)) for o in v] for f, v in fam_ops.items()},
           "rows": rows, "note": "Educational only -- not financial advice."}
    (OUT / "results.json").write_text(json.dumps(res, default=str))
    print("configs", len(rows), "eligible", len(elig), "valid-gate", len(cands), "finalists", len(finalists), round(time.time() - t0))
    for r in cands[:30]:
        print(r["family"], r["geom"], r["label"], "T", r["train"]["n"], r["train"]["exp_r"], r["train"]["t_dc"], "V", r["valid"]["n"],
              r["valid"]["exp_r"], r["valid"]["t_dc"], "exb", r["valid"]["ex_best_day"], "wb", r["valid"]["window_base"], "ctrl",
              r["valid"]["ctrl"], r["plateau"], r["gate"])


if __name__ == "__main__":
    main()
