"""Stack study step 2: stage-wise greedy search over basic trigger x filter stacks (NOTES.md 1.3-1.7). Every evaluated
configuration is counted. Reads data/base.npz (prep.py). Writes data/scan_*.csv, counts.json, candidates.json.
    python research/bdi/stack1009/scan.py
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

GEOMS = ("t1s1", "t05s1", "t1s05")
WINDOWS = {"am": (950, 1130), "mid": (1135, 1330), "pm": (1335, 1500)}
B = dict(np.load(HERE / "data" / "base.npz"))
DATES = pd.read_csv(HERE / "data" / "dates.csv").iloc[:, 0].tolist()
REG = lib.regimes().reindex(pd.to_datetime(DATES).date)["regime"].to_numpy()
REGC = np.select([REG == "up", REG == "down"], [1, -1], 0)
ND = len(DATES)
SD = B["sd"]
NEWSD = np.r_[True, SD[1:] != SD[:-1]]
COUNT = {"n": 0}
TOD = B["tod"]


def prev(x):
    p = np.r_[np.nan, x[:-1]].astype(float)
    p[NEWSD] = np.nan
    return p


def F(k):
    return B[k].astype(float)


# ------------------------------------------------------------------ triggers (full-frame event arrays)
def cross_up(x, lvl=0.0):
    p = prev(x)
    with np.errstate(invalid="ignore"):
        return (x > lvl) & (p <= lvl)


def cross_dn(x, lvl=0.0):
    p = prev(x)
    with np.errstate(invalid="ignore"):
        return (x < lvl) & (p >= lvl)


def trig(fam: str, d: str, p=None) -> np.ndarray:
    c = F("close")
    if fam == "vwap":
        return cross_up(F("z")) if d == "up" else cross_dn(F("z"))
    if fam == "ema":
        return cross_up(F("emaDiff")) if d == "up" else cross_dn(F("emaDiff"))
    if fam == "macd":
        return cross_up(F("macdPct")) if d == "up" else cross_dn(F("macdPct"))
    if fam == "rsi14":
        p = 30 if p is None else p
        return cross_up(F("rsi"), p) if d == "up" else cross_dn(F("rsi"), 100 - p)
    if fam == "rsi5":
        p = 20 if p is None else p
        return cross_up(F("rsi5"), p) if d == "up" else cross_dn(F("rsi5"), 100 - p)
    if fam == "or":
        x = c - (F("orh") if d == "up" else F("orl"))
        return (cross_up(x) if d == "up" else cross_dn(x)) & (TOD > 1000)
    if fam == "sma50":
        return cross_up(F("sma50_dist_pct")) if d == "up" else cross_dn(F("sma50_dist_pct"))
    if fam == "sma20":
        return cross_up(F("sma20_dist_pct")) if d == "up" else cross_dn(F("sma20_dist_pct"))
    if fam == "pdbrk":
        return cross_up(c - F("pdh")) if d == "up" else cross_dn(c - F("pdl"))
    if fam == "pdfail":
        return cross_up(c - F("pdl")) if d == "up" else cross_dn(c - F("pdh"))
    if fam in ("band05", "band10"):
        k = (0.5 if fam == "band05" else 1.0) if p is None else p
        return cross_up(F("z"), -k) if d == "up" else cross_dn(F("z"), k)
    if fam == "hodlod":
        x = F("dist_hod_atr") if d == "up" else F("dist_lod_atr")
        with np.errstate(invalid="ignore"):
            return (x <= 0) & (prev(x) > 0)
    if fam == "rsi50":
        return cross_up(F("rsi"), 50) if d == "up" else cross_dn(F("rsi"), 50)
    if fam == "volspike":
        with np.errstate(invalid="ignore"):
            return cross_up(F("volumeRatio"), 2.0) & ((F("z") > 0) if d == "up" else (F("z") < 0))
    if fam == "fo3":
        return cross_up(F("fromOpen"), 3.0) if d == "up" else cross_dn(F("fromOpen"), -3.0)
    if fam == "slope20":
        return cross_up(F("sma20_slope_pct")) if d == "up" else cross_dn(F("sma20_slope_pct"))
    if fam == "flow3":
        return cross_up(F("flow3"), 0.5) if d == "up" else cross_dn(F("flow3"), -0.5)
    raise KeyError(fam)


TRIG_GRID = {"rsi14": [25, 30, 35], "rsi5": [15, 20, 25], "band05": [0.25, 0.5, 0.75], "band10": [0.75, 1.0, 1.25]}
TRIG_DEFAULT = {"rsi14": 30, "rsi5": 20, "band05": 0.5, "band10": 1.0}
FAMS5 = ["hodlod", "rsi50", "volspike", "fo3", "slope20", "flow3"]
FAMS = ["vwap", "ema", "rsi14", "rsi5", "macd", "or", "sma50", "sma20", "pdbrk", "pdfail", "band05", "band10"]


GENERIC = {"vwap_with", "vwap_against", "ema_with", "ema_against", "sma50_with", "sma50_against", "slope20_with",
           "slope20_against", "macd_with", "macd_against", "bp_with", "bp_against", "flow3_with", "flow3_against",
           "rsi50_with", "gap_with", "gap_against"}


# ------------------------------------------------------------------ filters on gathered rows G (dict of arrays)
def filt(name: str, G: dict, s: int, p=None) -> np.ndarray:
    g = lambda k: G[k]  # noqa: E731
    with np.errstate(invalid="ignore"):
        if name in GENERIC:
            base, how = name.rsplit("_", 1)
            sg = s if how == "with" else -s
            col = {"vwap": "z", "ema": "emaDiff", "sma50": "sma50_dist_pct", "slope20": "sma20_slope_pct",
                   "macd": "macdPct", "bp": "buyPressure", "flow3": "flow3", "rsi50": None, "gap": "gap"}[base]
            if base == "rsi50":
                return sg * (g("rsi") - 50) > 0
            if base == "gap":
                return sg * g("gap") > (1.0 if p is None else p)
            return sg * g(col) > 0
        if name == "vol":
            return g("volumeRatio") >= p
        if name == "fo_with":
            return s * g("fromOpen") > p
        if name == "fo_against":
            return s * g("fromOpen") < -p
        if name == "rsi_ext":
            return (g("rsi") >= p) if s < 0 else (g("rsi") <= 100 - p)
        if name == "rsi5_ext":
            return (g("rsi5") >= p) if s < 0 else (g("rsi5") <= 100 - p)
        if name == "stretch_small":
            return np.abs(g("z")) < p
        if name == "near_ext":
            return (g("dist_hod_atr") < p) if s > 0 else (g("dist_lod_atr") < p)
        if name == "pd_out_with":
            return (g("close") > g("pdh")) if s > 0 else (g("close") < g("pdl"))
        if name == "pd_inside":
            return (g("close") >= g("pdl")) & (g("close") <= g("pdh"))
    raise KeyError(name)


FILTERS = [(n, None) for n in ["vwap_with", "vwap_against", "ema_with", "ema_against", "sma50_with", "sma50_against",
                               "slope20_with", "slope20_against", "macd_with", "macd_against", "bp_with", "bp_against",
                               "flow3_with", "flow3_against", "rsi50_with", "pd_out_with", "pd_inside"]]
FILTERS += [("vol", 1.5), ("vol", 2.0), ("fo_with", 1.0), ("fo_with", 3.0), ("fo_against", 1.0), ("fo_against", 3.0),
            ("gap_with", 1.0), ("gap_against", 1.0), ("rsi_ext", 70), ("rsi5_ext", 80), ("stretch_small", 0.5),
            ("near_ext", 0.25)]
FGRID = {"vol": [1.25, 1.5, 2.0, 2.5, 3.0], "fo_with": [0.5, 1.0, 2.0, 3.0, 4.0], "fo_against": [0.5, 1.0, 2.0, 3.0, 4.0],
         "gap_with": [0.5, 1.0, 2.0], "gap_against": [0.5, 1.0, 2.0], "rsi_ext": [60, 65, 70, 75, 80],
         "rsi5_ext": [70, 75, 80, 85, 90], "stretch_small": [0.25, 0.5, 0.75, 1.0], "near_ext": [0.1, 0.25, 0.5]}
GCOLS = ["close", "rsi", "rsi5", "emaDiff", "macdPct", "volumeRatio", "z", "buyPressure", "gap", "fromOpen", "tod",
         "dist_hod_atr", "dist_lod_atr", "sma20_slope_pct", "sma50_dist_pct", "flow3", "pdh", "pdl", "sd", "day", "sym"]


# ------------------------------------------------------------------ evaluation
def tstat(r, day):
    n = len(r)
    if n < 2:
        return 0.0
    mu = r.mean()
    S = np.bincount(day, weights=r, minlength=ND)
    C = np.bincount(day, minlength=ND)
    se = np.sqrt(((S - C * mu) ** 2).sum()) / n
    return float(mu / se) if se > 0 else 0.0


def quick(G, m, side, geom):
    """first qualifying row per symbol-day among gathered rows (frame order) -> stats dict."""
    COUNT["n"] += 1
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return {"n": 0}
    s = G["sd"][idx]
    idx = idx[np.r_[True, s[1:] != s[:-1]]]
    r = G[f"p_{side}_{geom}"][idx].astype(float)
    ok = np.isfinite(r)
    idx, r = idx[ok], r[ok]
    day = G["day"][idx]
    rc = REGC[day]
    out = {"n": len(r), "exp": float(r.mean()) if len(r) else np.nan, "t": tstat(r, day)}
    for k, v in (("up", 1), ("flat", 0), ("down", -1)):
        mm = rc == v
        out[f"n_{k}"] = int(mm.sum())
        out[f"exp_{k}"] = float(r[mm].mean()) if mm.any() else np.nan
        out[f"t_{k}"] = tstat(r[mm], day[mm]) if mm.sum() > 1 else 0.0
    C = np.bincount(day, minlength=ND)
    out["maxday"] = float(C.max() / len(r)) if len(r) else 1.0
    S_ = np.bincount(day, weights=r, minlength=ND)
    def tday(mask_days):
        dm = (S_[mask_days & (C > 0)] / C[mask_days & (C > 0)])
        return float(dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm)))) if len(dm) > 2 and dm.std() > 0 else 0.0
    allday = np.ones(ND, bool)
    out["tday"] = tday(allday)
    out["tday_up"], out["tday_down"] = tday(REGC == 1), tday(REGC == -1)
    ok = out["n_up"] >= 30 and out["n_down"] >= 30 and out["maxday"] <= 0.10
    out["robust"] = min(out["tday_up"], out["tday_down"]) if ok else -9
    out["_idx"] = idx
    return out


def gather(fam, d, side_s, p=None):
    ev = trig(fam, d, p)
    rows = np.flatnonzero(ev)
    G = {k: B[k][rows] for k in GCOLS}
    for s in ("long", "short"):
        for g in GEOMS:
            G[f"p_{s}_{g}"] = B[f"p_{s}_{g}"][rows]
    return G


def wmask(G, w):
    lo, hi = WINDOWS[w]
    return (G["tod"] >= lo) & (G["tod"] <= hi)


def fmask(G, s, flist):
    m = np.ones(len(G["tod"]), bool)
    for n, p in flist:
        m &= filt(n, G, s, p)
    return m


def key(cfg):
    fam, d, side, w, flist, geom = cfg
    fs = "+".join(f"{n}{'' if p is None else p}" for n, p in flist)
    return f"{fam}-{d}|{side}|{w}|{fs or '-'}|{geom}"


def strip(o):
    return {k: v for k, v in o.items() if k != "_idx"}


def main():
    rows = []
    cache = {}

    def G_of(fam, d, p=None):
        k = (fam, d, p)
        if k not in cache:
            cache[k] = gather(fam, d, None, p)
        return cache[k]

    def run(fam, d, side, w, flist, geom, G=None):
        G = G if G is not None else G_of(fam, d)
        s = 1 if side == "long" else -1
        o = quick(G, wmask(G, w) & fmask(G, s, flist), side, geom)
        rows.append({"cfg": key((fam, d, side, w, flist, geom)), "fam": fam, "dir": d, "side": side, "win": w,
                     "filters": json.dumps(flist), "geom": geom, "stage": STAGE[0], **strip(o)})
        return o

    STAGE = [1]
    # stage 1
    for fam in (FAMS5 if "--pass5" in sys.argv else FAMS):
        for d in ("up", "dn"):
            for side in ("long", "short"):
                for w in WINDOWS:
                    for geom in GEOMS:
                        run(fam, d, side, w, [], geom)
    print("stage1", COUNT["n"], flush=True)
    df = pd.DataFrame(rows)
    s1 = df[df.n >= 300].sort_values("robust", ascending=False).drop_duplicates(["fam", "dir", "side", "win"])
    s1 = s1  # pass 3: exhaustive stage 2
    beams = [(r.fam, r.dir, r.side, r.win, []) for r in s1.itertuples()]
    if "--pass4" in sys.argv:
        beams = [(f, d, sd, w, [fo]) for (f, d, sd, w, _) in beams
                 for fo in (("fo_with", 2.0), ("fo_with", 3.0), ("fo_against", 2.0), ("fo_against", 3.0))]
    stages = ((2, 100, 200), (3, 100, 150), (4, 0, 150)) if "--pass4" not in sys.argv else ((3, 100, 150), (4, 0, 150))
    for stage, beam_n, nmin in stages:
        STAGE[0] = stage
        start = len(rows)
        for fam, d, side, w, fl in beams:
            used = {n for n, _ in fl}
            for f in FILTERS:
                if f[0] in used:
                    continue
                for geom in GEOMS:
                    run(fam, d, side, w, fl + [f], geom)
        print(f"stage{stage}", COUNT["n"], flush=True)
        if not beam_n:
            break
        sd_ = pd.DataFrame(rows[start:])
        sd_ = sd_[sd_.n >= nmin].sort_values("robust", ascending=False)
        sd_["fk"] = sd_["filters"].map(lambda x: json.dumps(sorted(json.loads(x))))
        sd_ = sd_.drop_duplicates(["fam", "dir", "side", "win", "fk"])
        sd_ = sd_.groupby(["fam", "side"]).head(8).head(beam_n)
        beams = [(r.fam, r.dir, r.side, r.win, [tuple(x) for x in json.loads(r.filters)]) for r in sd_.itertuples()]
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "data" / ("scan_pass5.csv" if "--pass5" in sys.argv else "scan_pass4.csv" if "--pass4" in sys.argv else "scan_all.csv"), index=False)
    if "--pass5" in sys.argv:
        json.dump({"configs_pass1": 7062, "configs_pass2": 7338, "configs_pass3": 29016, "configs_pass4": 54858,
                   "configs_pass5": COUNT["n"], "configs": 7062 + 7338 + 29016 + 54858 + COUNT["n"]},
                  open(HERE / "counts.json", "w"), indent=1)
    elif "--pass4" in sys.argv:
        json.dump({"configs_pass1": 7062, "configs_pass2": 7338, "configs_pass3": 29016, "configs_pass4": COUNT["n"],
                   "configs": 7062 + 7338 + 29016 + COUNT["n"]}, open(HERE / "counts.json", "w"), indent=1)
    else:
        json.dump({"configs_pass1": 7062, "configs_pass2": 7338, "configs_pass3": COUNT["n"], "configs": 7062 + 7338 + COUNT["n"]}, open(HERE / "counts.json", "w"), indent=1)
    print("total configs", COUNT["n"])


if __name__ == "__main__":
    main()
