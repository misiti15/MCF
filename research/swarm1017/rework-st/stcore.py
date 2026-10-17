"""Parameterised re-implementation of the ST1-ST8 (stack1009 -FD) masks and the L3 cores, over plain numpy arrays.
Semantics copied 1:1 from research/bdi/fullday/ST*-FD.py (checked bar-for-bar in verify.py). Educational only - not
financial advice."""
import itertools

import numpy as np

# parent definitions: side, geom, trigger, filters (as in the FD modules)
ST = {
    "ST1": ("long", "t05s1", ("or", "dn", None), [("fo_against", 3.0), ("vol", 1.5), ("pd_inside", None)]),
    "ST2": ("long", "t05s1", ("slope20", "up", None), [("fo_against", 3.0), ("bp_with", None), ("stretch_small", 0.5)]),
    "ST3": ("short", "t1s1", ("rsi5", "up", 20), [("fo_with", 3.0), ("vwap_against", None), ("gap_against", 1.0)]),
    "ST4": ("long", "t1s05", ("ema", "dn", None), [("fo_against", 3.0), ("rsi50_with", None), ("rsi5_ext", 80)]),
    "ST5": ("short", "t05s1", ("pdbrk", "up", None), [("fo_with", 3.0), ("sma50_against", None)]),
    "ST6": ("short", "t1s1", ("volspike", "up", 2.0), [("fo_with", 3.0), ("gap_against", 1.0)]),
    "ST7": ("long", "t1s1", ("rsi50", "dn", None), [("rsi_ext", 70), ("fo_against", 1.0), ("bp_with", None)]),
    "ST8": ("long", "t1s1", ("volspike", "dn", 2.0), [("fo_against", 3.0), ("macd_with", None), ("flow3_with", None)]),
}
SRCWIN = {"L3a": "1300-1430", "L3b": "1300-1430", "L3c": "1300-1430", "ST1": "1335-1500", "ST2": "0950-1130",
          "ST3": "1335-1500", "ST4": "0950-1130", "ST5": "1135-1330", "ST6": "1135-1330", "ST7": "1335-1500",
          "ST8": "1335-1500"}
PSIDE = {"L3a": "short", "L3b": "short", "L3c": "short", **{k: v[0] for k, v in ST.items()}}
PGEOM = {"L3a": "t1s1", "L3b": "t1s1", "L3c": "t05s1", **{k: v[1] for k, v in ST.items()}}

# Stage A grids: tuple of axis values per parent; PARENT gives the parent point. None = layer off.
AXES = {
    "ST1": [(1, 2, 3, 4), (None, 1.5, 2.0), (True, False)],
    "ST2": [(1, 2, 3, 4), (True, False), (0.3, 0.5, 0.75, None)],
    "ST3": [(10, 20, 30), (1, 2, 3, 4), (True, False), (0.5, 1.0, None)],
    "ST4": [(1, 2, 3, 4), (True, False), (70, 80, 90, None)],
    "ST5": [(1, 2, 3, 4), (True, False)],
    "ST6": [(1.5, 2.0, 3.0), (1, 2, 3, 4), (0.5, 1.0, None)],
    "ST7": [(60, 70, 80), (0.5, 1, 2, 3), (True, False)],
    "ST8": [(1, 2, 3, 4), (True, False), (True, False)],
    "L3a": [(-2.0, -2.657, -3.5), (0.2, 0.3724, 0.5965, 0.8), (2.5, 3.46, 4.5, None)],
    "L3b": [(-2.0, -2.657, -3.5), (0.2, 0.3724, 0.5965, 0.8), ((0.6, 0.8), (0.7817, 0.9765), (0.95, 1.2), (0.7817, 99.0), None)],
    "L3c": [(-2.0, -2.657, -3.5), (0.2, 0.3724, 0.5965, 0.8), (60, 70, 80, None)],
}
PARENT = {"ST1": (3, 1.5, True), "ST2": (3, True, 0.5), "ST3": (20, 3, True, 1.0), "ST4": (3, True, 80),
          "ST5": (3, True), "ST6": (2.0, 3, 1.0), "ST7": (70, 1, True), "ST8": (3, True, True),
          "L3a": (-2.657, 0.3724, 3.46), "L3b": (-2.657, 0.3724, (0.7817, 0.9765)), "L3c": (-2.657, 0.5965, 70)}
# exact parent thresholds (the module literals)
L3EXACT = {-2.657: -2.6573517322540283, 0.3724: 0.37244729995727527, 0.5965: 0.5964763522148127, 3.46: 3.460294628143309,
           0.7817: 0.7816761255264282, 0.9765: 0.9764953255653381}


def points(p):
    """Stage A points. The L3 'third layer off' point is shared by L3a/b/c; it is enumerated under L3a only."""
    pts = list(itertools.product(*AXES[p]))
    if p in ("L3b", "L3c"):
        pts = [t for t in pts if t[2] is not None]
    return pts


def st_spec(p, th):
    """(trigger, filters) of ST parent p at Stage A point th."""
    side, geom, trig, filt = ST[p]
    if p == "ST1":
        fo, vol, pdi = th
        f = [("fo_against", fo)] + ([("vol", vol)] if vol else []) + ([("pd_inside", None)] if pdi else [])
        return trig, f
    if p == "ST2":
        fo, bp, st = th
        f = [("fo_against", fo)] + ([("bp_with", None)] if bp else []) + ([("stretch_small", st)] if st else [])
        return trig, f
    if p == "ST3":
        lv, fo, vw, gp = th
        f = [("fo_with", fo)] + ([("vwap_against", None)] if vw else []) + ([("gap_against", gp)] if gp else [])
        return ("rsi5", "up", lv), f
    if p == "ST4":
        fo, r50, r5 = th
        f = [("fo_against", fo)] + ([("rsi50_with", None)] if r50 else []) + ([("rsi5_ext", r5)] if r5 else [])
        return trig, f
    if p == "ST5":
        fo, sm = th
        return trig, [("fo_with", fo)] + ([("sma50_against", None)] if sm else [])
    if p == "ST6":
        lv, fo, gp = th
        return ("volspike", "up", lv), [("fo_with", fo)] + ([("gap_against", gp)] if gp else [])
    if p == "ST7":
        rx, fo, bp = th
        return trig, [("rsi_ext", rx), ("fo_against", fo)] + ([("bp_with", None)] if bp else [])
    if p == "ST8":
        fo, mc, fl = th
        return trig, [("fo_against", fo)] + ([("macd_with", None)] if mc else []) + ([("flow3_with", None)] if fl else [])
    raise KeyError(p)


class Frame:
    """Derived arrays of one frame block (sorted by symbol, date, tod)."""

    def __init__(self, cols: dict, new: np.ndarray):
        self.c = cols
        self.new = new
        n = len(new)
        self.n = n
        c, atr, tod = cols["close"], cols["atr_d"], cols["tod"]
        vw = c / (1 + cols["vwapDistPct"] / 100)
        self.z = (c - vw) / atr
        hod = c + cols["dist_hod_atr"] * atr
        lod = c - cols["dist_lod_atr"] * atr
        self.pdh = c + cols["dist_pdh_atr"] * atr
        self.pdl = c - cols["dist_pdl_atr"] * atr
        self.orl = self.ffill(np.where(tod == 1000, lod, np.nan))
        self.orh = self.ffill(np.where(tod == 1000, hod, np.nan))

    def prev(self, x):
        p = np.r_[np.nan, x[:-1]]
        p[self.new] = np.nan
        return p

    def ffill(self, x):
        n, new = self.n, self.new
        idx = np.where(np.isfinite(x), np.arange(n), -1)
        idx = np.maximum.accumulate(idx)
        out = np.where(idx >= 0, x[np.maximum(idx, 0)], np.nan)
        start = np.maximum.accumulate(np.where(new, np.arange(n), 0))
        out[idx < start] = np.nan
        return out

    def up(self, x, lvl=0.0):
        return (x > lvl) & (self.prev(x) <= lvl)

    def dn(self, x, lvl=0.0):
        return (x < lvl) & (self.prev(x) >= lvl)

    def trig(self, fam, d, p):
        col, c, tod = self.c, self.c["close"], self.c["tod"]
        with np.errstate(invalid="ignore"):
            if fam == "or":
                return (self.up(c - self.orh) if d == "up" else self.dn(c - self.orl)) & (tod > 1000)
            if fam == "slope20":
                return self.up(col["sma20_slope_pct"]) if d == "up" else self.dn(col["sma20_slope_pct"])
            if fam == "rsi5":
                return self.up(col["rsi5"], p) if d == "up" else self.dn(col["rsi5"], 100 - p)
            if fam == "ema":
                return self.up(col["emaDiff"]) if d == "up" else self.dn(col["emaDiff"])
            if fam == "pdbrk":
                return self.up(c - self.pdh) if d == "up" else self.dn(c - self.pdl)
            if fam == "volspike":
                return self.up(col["volumeRatio"], p) & ((self.z > 0) if d == "up" else (self.z < 0))
            if fam == "rsi50":
                return self.up(col["rsi"], 50) if d == "up" else self.dn(col["rsi"], 50)
        raise KeyError(fam)

    def filt(self, name, p, s):
        col, z, c = self.c, self.z, self.c["close"]
        with np.errstate(invalid="ignore"):
            if name in ("vwap_with", "vwap_against"):
                return (s if name.endswith("with") else -s) * z > 0
            if name in ("gap_with", "gap_against"):
                return (s if name.endswith("with") else -s) * col["gap"] > (1.0 if p is None else p)
            if name in ("rsi50_with",):
                return s * (col["rsi"] - 50) > 0
            if name in ("bp_with", "macd_with", "flow3_with", "sma50_against"):
                base, how = name.rsplit("_", 1)
                sg = s if how == "with" else -s
                k = {"bp": "buyPressure", "macd": "macdPct", "flow3": "flow3", "sma50": "sma50_dist_pct"}[base]
                return sg * col[k] > 0
            if name == "vol":
                return col["volumeRatio"] >= p
            if name == "fo_with":
                return s * col["fromOpen"] > p
            if name == "fo_against":
                return s * col["fromOpen"] < -p
            if name == "rsi_ext":
                return (col["rsi"] >= p) if s < 0 else (col["rsi"] <= 100 - p)
            if name == "rsi5_ext":
                return (col["rsi5"] >= p) if s < 0 else (col["rsi5"] <= 100 - p)
            if name == "stretch_small":
                return np.abs(z) < p
            if name == "pd_inside":
                return (c >= self.pdl) & (c <= self.pdh)
        raise KeyError(name)

    def st(self, p, th):
        trig, filt = st_spec(p, th)
        s = 1.0 if ST[p][0] == "long" else -1.0
        m = self.trig(*trig)
        for name, q in filt:
            m = m & self.filt(name, q, s)
        return np.asarray(m, bool)


def l3(cols, p, th):
    """L3 core over arrays (gap, sma20_slope_pct, fromOpen, dist_lod_atr, rsi5)."""
    g, sl, x = th
    g = L3EXACT.get(g, g)
    sl = L3EXACT.get(sl, sl)
    with np.errstate(invalid="ignore"):
        m = (cols["gap"] <= g) & (cols["sma20_slope_pct"] > sl)
        if x is None:
            return m
        if p == "L3a":
            return m & (cols["fromOpen"] > L3EXACT.get(x, x))
        if p == "L3b":
            lo, hi = L3EXACT.get(x[0], x[0]), L3EXACT.get(x[1], x[1])
            return m & (cols["dist_lod_atr"] > lo) & (cols["dist_lod_atr"] <= hi)
        if p == "L3c":
            return m & (cols["rsi5"] > x)
    raise KeyError(p)
