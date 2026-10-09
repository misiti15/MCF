"""W1 families: every setup family as a parameterised mask over the engine's rows, with its pre-declared variant axes
(NOTES.md 1.2-1.3). Each base reproduces the full-day module (research/bdi/fullday, rework1008 RW8), the Reddit rule
(research/bdi/reddit/strategies.py, no filter, t1s1) or the stack1009 trigger (ST modules' trig()).
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "bdi" / "reddit"))

GEOMS = ["t1s1", "t05s1", "t1s05", "t15s1", "t1s075"]
VBAND = [None, "ext1", "ext1.5", "ext2", "ext2.5", "in1", "in1.5", "in2", "in2.5"]
MA = [None, "w20", "w50", "w100", "a20", "a50", "a100"]
VOL = [None, 1.25, 1.5, 2.0, 3.0]
IO = [None, 1.0, 2.0, 3.0, 4.0]
RSI_COL = {5: "rsi5", 9: "rsi9", 14: "rsi", 21: "rsi21"}
EMA_COL = {(9, 21): "emaDiff", (8, 21): "ed8_21", (13, 21): "ed13_21", (9, 20): "ed9_20", (8, 20): "ed8_20",
           (13, 20): "ed13_20"}
EMA_PAIRS = [(9, 21), (8, 21), (13, 21), (9, 20), (8, 20), (13, 20)]
SMA_COL = {20: "sma20_dist_pct", 50: "sma50_dist_pct", 100: "sma100"}


# ------------------------------------------------------------------------------------------------ helpers
def up(D, x, lvl=0.0):
    with np.errstate(invalid="ignore"):
        return (x > lvl) & (D.prev(x) <= lvl)


def dn(D, x, lvl=0.0):
    with np.errstate(invalid="ignore"):
        return (x < lvl) & (D.prev(x) >= lvl)


def rsi_heat(r):
    r = np.nan_to_num(r, nan=50.0)
    return np.select([r >= 80, r >= 70, r <= 20, r <= 30, r < 45, r > 55],
                     [-25, -((r - 70) / 10) * 20, 25, ((30 - r) / 10) * 20, (45 - r) / 15 * 10, (55 - r) / 15 * 10],
                     0).astype(np.float32)


def common(D, P, s, m):
    with np.errstate(invalid="ignore"):
        if P.get("vol") is not None and "vol" not in P.get("_own", ()):
            m = m & (D.F("volumeRatio") >= P["vol"])
        vb = P.get("vband")
        if vb:
            k = float(vb[3:] if vb.startswith("ext") else vb[2:])
            z = D.F("zsd")
            m = m & ((s * z <= -k) if vb.startswith("ext") else (np.abs(z) < k))
        if P.get("io") is not None:
            m = m & (np.abs(D.F("fromOpen")) >= P["io"])
        ma = P.get("ma")
        if ma:
            x = D.F(SMA_COL[int(ma[1:])])
            m = m & ((s * x > 0) if ma[0] == "w" else (s * x < 0))
    return m


# ------------------------------------------------------------------------------------------------ lab families
def f_heat_short(D, P):
    base = rsi_heat(D.F(RSI_COL[P["rsi_len"]])) + np.nan_to_num(D.F("rest3"))
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (base + P["k"] * 8.0 / D.F("atr_d") <= P["thr"]) & np.isfinite(D.F("atr_d"))
        if P["gate"] == "fo-":
            m &= D.F("fromOpen") < -P["fo"]
    return m


def f_heat_long(D, P):
    base = (rsi_heat(D.F(RSI_COL[P["rsi_len"]])) + np.nan_to_num(D.F("rest3"))
            - np.clip(np.nan_to_num(D.F("fromOpen")), -3, 3) * 5)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (base - P["k"] * 8.0 / D.F("atr_d") >= P["thr"]) & np.isfinite(D.F("atr_d"))
        if P["gate"] == "gap+":
            m &= D.F("gap") > P["gap"]
    return m


def f_exh(D, P):
    with np.errstate(invalid="ignore"):
        return (D.F(RSI_COL[P["rsi_len"]]) > P["lvl"]) & (D.F(SMA_COL[P["sma"]]) > P["sthr"]) & (D.F("bear_div") > 0)


def f_mf(D, P):
    """MF / RW flow-sell family: heat <= h & buyPressure < b [& vwapDistPct > v] [& RSI > lvl | RSI in band]
    [& gap < -g]."""
    with np.errstate(invalid="ignore"):
        m = (D.F("heat") <= P["heat"]) & (D.F("buyPressure") < P["bp"])
        if P.get("vwap") is not None:
            m &= D.F("vwapDistPct") > P["vwap"]
        if P.get("lvl") is not None:
            m &= D.F(RSI_COL[P["rsi_len"]]) > P["lvl"]
        if P.get("band") is not None:
            r = D.F(RSI_COL[P["rsi_len"]])
            m &= (r >= P["band"][0]) & (r <= P["band"][1])
        if P.get("gap") is not None:
            m &= D.F("gap") < -P["gap"]
    return m


def f_rsicross(D, P):
    """NS1: RSI crosses below L, rsi5 >= L2, fromOpen > F (long)."""
    r = D.F(RSI_COL[P["rsi_len"]])
    with np.errstate(invalid="ignore"):
        return (r <= P["L"]) & (D.prev(r) > P["L"]) & (D.F("rsi5") >= P["L2"]) & (D.F("fromOpen") > P["F"])


def f_smacross(D, P):
    """NS2 / RW6 / RW8 (short, cross up) and NS5 (long, cross down): close crosses its SMA, RSI condition, fromOpen."""
    x = D.F(SMA_COL[P["sma"]])
    r = D.F(RSI_COL[P["rsi_len"]])
    fo = D.F("fromOpen")
    with np.errstate(invalid="ignore"):
        cr = up(D, x) if P["dir"] == "up" else dn(D, x)
        rc = (r >= P["L"]) if P["rsi_side"] == "ge" else (r <= P["L"])
        fc = (fo > P["F"]) if P["fo_side"] == "gt" else (fo < -P["F"])
        m = cr & rc & fc
        if P.get("guard") is not None:
            from eng import _band_block
            m &= ~_band_block(np.nan_to_num(D.F("zsd"), nan=0.0).astype(np.float64), D.new, float(P["guard"]))
    return m


def f_vwapcross(D, P):
    """NS3 / RW4 (short: VWAP cross up, SMA > 0, fromOpen < -F) and NS4 (short t1s05: RSI <= L, fromOpen > F)."""
    v = D.F("vwapDistPct")
    fo = D.F("fromOpen")
    with np.errstate(invalid="ignore"):
        m = up(D, v)
        if P.get("sma") is not None:
            m &= D.F(SMA_COL[P["sma"]]) > 0
        if P.get("L") is not None:
            m &= D.F(RSI_COL[P["rsi_len"]]) <= P["L"]
        m &= (fo > P["F"]) if P["fo_side"] == "gt" else (fo < -P["F"])
    return m


# ------------------------------------------------------------------------------------------------ stack (ST) engine
GENERIC = {"vwap_with", "vwap_against", "ema_with", "ema_against", "sma50_with", "sma50_against", "slope20_with",
           "slope20_against", "macd_with", "macd_against", "bp_with", "bp_against", "flow3_with", "flow3_against",
           "rsi50_with", "gap_with", "gap_against"}


def st_trig(D, P, s):
    fam, d, p = P["trig"]
    c = D.F("close")
    z = D.F("z")
    rl = P.get("rsi_len")
    with np.errstate(invalid="ignore"):
        if fam == "vwap":
            return up(D, z) if d == "up" else dn(D, z)
        if fam == "ema":
            e = D.F(EMA_COL[P.get("ema", (9, 21))])
            return up(D, e) if d == "up" else dn(D, e)
        if fam == "macd":
            return up(D, D.F("macdPct")) if d == "up" else dn(D, D.F("macdPct"))
        if fam == "rsi14":
            r = D.F(RSI_COL[rl or 14])
            return up(D, r, p) if d == "up" else dn(D, r, 100 - p)
        if fam == "rsi5":
            r = D.F(RSI_COL[rl or 5])
            return up(D, r, p) if d == "up" else dn(D, r, 100 - p)
        if fam == "or":
            return (up(D, c - D.F("orh")) if d == "up" else dn(D, c - D.F("orl"))) & (D.tod > 1000)
        if fam in ("sma50", "sma20"):
            x = D.F(SMA_COL[P.get("sma", int(fam[3:]))])
            return up(D, x) if d == "up" else dn(D, x)
        if fam == "pdbrk":
            return up(D, c - D.F("pdh")) if d == "up" else dn(D, c - D.F("pdl"))
        if fam == "pdfail":
            return up(D, c - D.F("pdl")) if d == "up" else dn(D, c - D.F("pdh"))
        if fam in ("band05", "band10"):
            return up(D, z, -p) if d == "up" else dn(D, z, p)
        if fam == "hodlod":
            x = D.F("dist_hod_atr") if d == "up" else D.F("dist_lod_atr")
            return (x <= 0) & (D.prev(x) > 0)
        if fam == "rsi50":
            r = D.F(RSI_COL[rl or 14])
            return up(D, r, 50) if d == "up" else dn(D, r, 50)
        if fam == "volspike":
            return up(D, D.F("volumeRatio"), p) & ((z > 0) if d == "up" else (z < 0))
        if fam == "fo3":
            return up(D, D.F("fromOpen"), p) if d == "up" else dn(D, D.F("fromOpen"), -p)
        if fam == "slope20":
            return up(D, D.F("sma20_slope_pct")) if d == "up" else dn(D, D.F("sma20_slope_pct"))
        if fam == "flow3":
            return up(D, D.F("flow3"), p) if d == "up" else dn(D, D.F("flow3"), -p)
    raise KeyError(fam)


def st_filt(D, P, name, p, s):
    c = D.F("close")
    z = D.F("z")
    rl = P.get("rsi_len")
    with np.errstate(invalid="ignore"):
        if name in GENERIC:
            base, how = name.rsplit("_", 1)
            sg = s if how == "with" else -s
            if base == "rsi50":
                return sg * (D.F(RSI_COL[rl or 14]) - 50) > 0
            if base == "gap":
                return sg * D.F("gap") > (1.0 if p is None else p)
            if base == "vwap":
                return sg * z > 0
            if base == "ema":
                return sg * D.F(EMA_COL[P.get("ema", (9, 21))]) > 0
            if base == "sma50":
                return sg * D.F(SMA_COL[P.get("sma", 50)]) > 0
            k = {"slope20": "sma20_slope_pct", "macd": "macdPct", "bp": "buyPressure", "flow3": "flow3"}[base]
            return sg * D.F(k) > 0
        if name == "vol":
            return D.F("volumeRatio") >= p
        if name == "fo_with":
            return s * D.F("fromOpen") > p
        if name == "fo_against":
            return s * D.F("fromOpen") < -p
        if name == "rsi_ext":
            r = D.F(RSI_COL[rl or 14])
            return (r >= p) if s < 0 else (r <= 100 - p)
        if name == "rsi5_ext":
            r = D.F(RSI_COL[rl or 5])
            return (r >= p) if s < 0 else (r <= 100 - p)
        if name == "stretch_small":
            return np.abs(z) < p
        if name == "near_ext":
            return (D.F("dist_hod_atr") < p) if s > 0 else (D.F("dist_lod_atr") < p)
        if name == "pd_out_with":
            return (c > D.F("pdh")) if s > 0 else (c < D.F("pdl"))
        if name == "pd_inside":
            return (c >= D.F("pdl")) & (c <= D.F("pdh"))
    raise KeyError(name)


def f_st(D, P, s):
    m = st_trig(D, P, s)
    for name, p in P["filters"]:
        m = m & st_filt(D, P, name, p, s)
    return m


# ------------------------------------------------------------------------------------------------ Reddit families
class V:
    """Variant view of the data for the Reddit builders: column / attribute overrides."""

    def __init__(self, D, cols=None, attrs=None):
        self._D, self._cols, self._attrs = D, cols or {}, attrs or {}

    def F(self, k):
        return self._D.F(self._cols.get(k, k))

    def __getattr__(self, k):
        if k in self._attrs:
            return self._attrs[k](self._D)
        return getattr(self._D, k)


def f_reddit(D, P, s):
    import strategies as RS
    fn = RS.STRATS[P["rule"]][0]
    cols, attrs = {}, {}
    if P.get("ema") and tuple(P["ema"]) != (9, 21):
        cols["emaDiff"] = EMA_COL[tuple(P["ema"])]
    if P.get("rsi_len") and P["rsi_len"] != 14:
        cols["rsi"] = RSI_COL[P["rsi_len"]]
    if P.get("sma") and P["sma"] != 20:
        col = SMA_COL[P["sma"]]
        cols["sma20_dist_pct"] = col
        attrs["sma20"] = lambda DD, col=col: DD.F("close") / (1 + DD.F(col) / 100)
    p = P["p"]
    if P.get("unit_sd") is not None:      # R03: VWAP band in SD units instead of daily ATR
        cols["z"] = "zsd"
        p = P["unit_sd"]
    view = V(D, cols, attrs) if (cols or attrs) else D
    o = fn(view, s, p)
    return np.asarray(np.nan_to_num(o["ev"]), bool)


# ------------------------------------------------------------------------------------------------ specs
def _lab(name, lineage, side, geom, min_adv, fn, P0, axes, own=(), tries=0):
    return {"name": name, "group": "lab", "lineage": lineage, "side": side, "geom": geom, "min_adv": min_adv,
            "fn": (lambda D, P, s, fn=fn: fn(D, P)), "P0": P0, "axes": axes, "own": tuple(own), "prior_tries": tries}


def _common_axes(spec):
    ax = dict(spec["axes"])
    ax["geom"] = GEOMS
    if "vol" not in spec["own"]:
        ax["vol"] = VOL
    ax["vband"] = VBAND
    if "fo" not in spec["own"]:
        ax["io"] = IO
    if "ma" not in spec["own"]:
        ax["ma"] = MA
    spec["axes"] = ax
    spec["P0"] = dict(spec["P0"]) | {"geom": spec["geom"], "vol": spec["P0"].get("vol"), "vband": None, "io": None,
                                      "ma": None, "_own": spec["own"]}
    return spec


RL = [5, 9, 14, 21]
HEAT3 = lambda h: [h + 10, h, h - 10]  # noqa: E731


def lab_specs():
    S = []
    S.append(_lab("heat_fade_short", "heat", "short", "t1s1", 125e6, f_heat_short,
                  {"rsi_len": 14, "k": 8.0, "thr": -11.3, "gate": "fo-", "fo": 0.0},
                  {"thr": [-17.3, -14.3, -11.3, -8.3, -5.3], "rsi_len": RL, "k": [4.0, 8.0, 12.0], "gate": ["fo-", "none"],
                   "fo": [0.0, 1.0, 2.0, 3.0, 4.0]}, own=("fo", "ma"), tries=19200))
    S.append(_lab("heat_fade_long", "heat", "long", "t1s1", 125e6, f_heat_long,
                  {"rsi_len": 14, "k": 4.0, "thr": 57.5, "gate": "gap+", "gap": 0.0},
                  {"thr": [51.5, 54.5, 57.5, 60.5, 63.5], "rsi_len": RL, "k": [2.0, 4.0, 6.0], "gate": ["gap+", "none"],
                   "gap": [0.0, 0.5, 1.0, 2.0, 3.0]}, own=("ma",), tries=19200))
    for nm, adv, tr in (("exhaustion_short", 95e6, 855600), ("RW2-exhaustion-noon-adv150-short", 150e6, 934522)):
        S.append(_lab(nm, "exhaustion", "short", "t1s1", adv, f_exh, {"rsi_len": 5, "lvl": 90, "sma": 20, "sthr": 1.0},
                      {"rsi_len": RL, "lvl": [70, 75, 80, 85, 90], "sma": [20, 50, 100], "sthr": [0.5, 1.0, 1.5, 2.0]},
                      own=("ma",), tries=tr))
    BP = [-0.15, -0.25, -0.35]
    VW = [0.0, 0.05, 0.25, 0.5]
    BANDS = [(50, 60), (55, 65), (60, 70), (65, 75)]
    mf = [("MF1-945-flowsell-vwapup", "t1s05", {"heat": -30, "bp": -0.25, "vwap": 0.05}, {"vwap": VW}),
          ("MF2-open-rsimidhi-flowsell", "t1s05", {"heat": -30, "bp": -0.25, "band": (55, 65), "rsi_len": 14},
           {"band": BANDS, "rsi_len": RL}),
          ("MF3-open-flowsell-rsi5hi", "t1s1", {"heat": -30, "bp": -0.25, "lvl": 70, "rsi_len": 5},
           {"lvl": [70, 75, 80], "rsi_len": RL}),
          ("MF4-h40-open-flowsell", "t05s1", {"heat": -40, "bp": -0.25}, {}),
          ("MF5-flowsell-vwapup-rsi5hi", "t1s1", {"heat": -30, "bp": -0.25, "vwap": 0.05, "lvl": 70, "rsi_len": 5},
           {"vwap": VW, "lvl": [70, 75, 80], "rsi_len": RL})]
    for nm, g, P0, ax in mf:
        S.append(_lab(nm, "MF", "short", g, 95e6, f_mf, P0, {"heat": HEAT3(P0["heat"]), "bp": BP} | ax, tries=8012))
    GAP = [0.0, 0.5, 1.0, 2.0]
    rw = [("RW1-gapdn-bounce-flowsell-short", {"heat": -20, "bp": -0.35, "band": (55, 65), "rsi_len": 14, "gap": 0.0},
           {"bp": [-0.25, -0.35, -0.45], "band": BANDS, "rsi_len": RL}, 82068),
          ("RW3-gapdn-rsi5pop-flowsell-short", {"heat": -20, "bp": -0.35, "lvl": 80, "rsi_len": 5, "gap": 0.0},
           {"bp": [-0.25, -0.35, -0.45], "lvl": [70, 75, 80, 85], "rsi_len": RL}, 82068),
          ("RW5-heat30-flowsell-rsi5pop-gapdn-short", {"heat": -30, "bp": -0.15, "lvl": 80, "rsi_len": 5, "gap": 0.0},
           {"bp": [-0.05, -0.15, -0.25], "lvl": [70, 75, 80, 85], "rsi_len": RL}, 82068),
          ("RW7-gapdn-bounce-early-short", {"heat": -20, "bp": -0.15, "band": (55, 65), "rsi_len": 14, "gap": 0.0},
           {"bp": [-0.05, -0.15, -0.25], "band": BANDS, "rsi_len": RL}, 82068)]
    for nm, P0, ax, tr in rw:
        S.append(_lab(nm, "RW-flow", "short", "t1s1", 95e6, f_mf, P0, {"heat": HEAT3(P0["heat"]), "gap": GAP} | ax,
                      tries=tr))
    FO = [1.0, 2.0, 3.0, 4.0]
    SM = [20, 50, 100]
    S.append(_lab("NS1-rsidip-rsi5pop-long", "NS", "long", "t05s1", 95e6, f_rsicross,
                  {"rsi_len": 14, "L": 40, "L2": 80, "F": 2.0},
                  {"rsi_len": RL, "L": [30, 35, 40, 45], "L2": [70, 75, 80, 85], "F": FO}, own=("fo",), tries=7374))
    sc = [("NS2-sma50break-overbought-short", "NS", "short", "t1s1", 95e6,
           {"dir": "up", "rsi_side": "ge", "L": 60, "fo_side": "gt", "F": 2.0}, [60, 65, 70, 75, 80], 7374),
          ("RW6-ns2-up3-short", "RW-sma", "short", "t1s1", 95e6,
           {"dir": "up", "rsi_side": "ge", "L": 60, "fo_side": "gt", "F": 3.0}, [60, 65, 70, 75, 80], 81430),
          ("RW6G1-ns2-up3-vwap2sd-short", "RW-sma", "short", "t1s1", 95e6,
           {"dir": "up", "rsi_side": "ge", "L": 60, "fo_side": "gt", "F": 3.0, "guard": 2.0}, [60, 65, 70, 75, 80], 81430),
          ("RW8-sma50up-spikefade-short", "RW-sma", "short", "t1s1", 95e6,
           {"dir": "up", "rsi_side": "le", "L": 30, "fo_side": "gt", "F": 3.0}, [20, 25, 30, 35], 81430),
          ("NS5-sma50-flush-oversold-long", "NS", "long", "t1s1", 95e6,
           {"dir": "dn", "rsi_side": "le", "L": 30, "fo_side": "lt", "F": 2.0}, [20, 25, 30, 35], 7374)]
    for nm, lin, side, g, adv, P0, LL, tr in sc:
        ax = {"sma": SM, "rsi_len": RL, "L": LL, "F": FO}
        if "guard" in P0:
            ax["guard"] = [1.0, 1.5, 2.0, 2.5]
        S.append(_lab(nm, lin, side, g, adv, f_smacross, {"sma": 50, "rsi_len": 14} | P0, ax, own=("fo", "ma"), tries=tr))
    for nm, adv, tr in (("NS3-failed-vwap-reclaim-short", 95e6, 7374), ("RW4-ns3-adv150-short", 150e6, 81430)):
        S.append(_lab(nm, "NS" if nm.startswith("NS") else "RW-vwap", "short", "t1s1", adv, f_vwapcross,
                      {"sma": 50, "fo_side": "lt", "F": 2.0}, {"sma": SM, "F": FO}, own=("fo", "ma"), tries=tr))
    S.append(_lab("NS4-pm-vwap-reclaim-oversold-short", "NS", "short", "t1s05", 95e6, f_vwapcross,
                  {"L": 30, "rsi_len": 14, "fo_side": "gt", "F": 2.0},
                  {"L": [20, 25, 30, 35], "rsi_len": RL, "F": FO}, own=("fo",), tries=7374))
    S += st_specs()
    return [_common_axes(s) for s in S]


ST = [("ST1-ordn-long-pm-t05s1", "long", "t05s1", ("or", "dn", None),
       [("fo_against", 3.0), ("vol", 1.5), ("pd_inside", None)]),
      ("ST2-slope20up-long-am-t05s1", "long", "t05s1", ("slope20", "up", None),
       [("fo_against", 3.0), ("bp_with", None), ("stretch_small", 0.5)]),
      ("ST3-rsi5up-short-pm-t1s1", "short", "t1s1", ("rsi5", "up", 20),
       [("fo_with", 3.0), ("vwap_against", None), ("gap_against", 1.0)]),
      ("ST4-emadn-long-am-t1s05", "long", "t1s05", ("ema", "dn", None),
       [("fo_against", 3.0), ("rsi50_with", None), ("rsi5_ext", 80)]),
      ("ST5-pdbrkup-short-mid-t05s1", "short", "t05s1", ("pdbrk", "up", None),
       [("fo_with", 3.0), ("sma50_against", None)]),
      ("ST6-volspikeup-short-mid-t1s1", "short", "t1s1", ("volspike", "up", 2.0),
       [("fo_with", 3.0), ("gap_against", 1.0)]),
      ("ST7-rsi50dn-long-pm-t1s1", "long", "t1s1", ("rsi50", "dn", None),
       [("rsi_ext", 70), ("fo_against", 1.0), ("bp_with", None)]),
      ("ST8-volspikedn-long-pm-t1s1", "long", "t1s1", ("volspike", "dn", 2.0),
       [("fo_against", 3.0), ("macd_with", None), ("flow3_with", None)])]
FILT_GRID = {"fo_against": [1.0, 2.0, 3.0, 4.0], "fo_with": [1.0, 2.0, 3.0, 4.0], "vol": [1.25, 1.5, 2.0, 3.0],
             "gap_against": [0.5, 1.0, 2.0, 3.0], "rsi_ext": [60, 65, 70, 75, 80], "rsi5_ext": [70, 75, 80, 85, 90],
             "stretch_small": [0.25, 0.5, 0.75, 1.0]}
TRIG_GRID = {"rsi5": [15, 20, 25], "rsi14": [25, 30, 35], "band05": [0.25, 0.5, 0.75], "band10": [0.75, 1.0, 1.25],
             "volspike": [1.25, 1.5, 2.0, 3.0], "fo3": [1.0, 2.0, 3.0, 4.0], "flow3": [0.25, 0.5, 0.75]}


def _st_axes(trig, filters):
    ax, own = {}, []
    fam = trig[0]
    if fam in TRIG_GRID:
        ax["tp"] = TRIG_GRID[fam]
        if fam == "volspike":
            own.append("vol")
        if fam == "fo3":
            own.append("fo")
    names = [f for f, _ in filters]
    if fam in ("rsi5", "rsi14", "rsi50") or any(f in ("rsi_ext", "rsi5_ext", "rsi50_with") for f in names):
        ax["rsi_len"] = RL
    if fam == "ema" or any(f.startswith("ema_") for f in names):
        ax["ema"] = EMA_PAIRS
    if fam in ("sma50", "sma20") or any(f.startswith("sma50_") for f in names):
        ax["sma"] = SM_ST
        own.append("ma")
    for i, (f, p) in enumerate(filters):
        if f in FILT_GRID:
            ax[f"f{i}"] = FILT_GRID[f]
            if f == "vol":
                own.append("vol")
            if f.startswith("fo_"):
                own.append("fo")
    return ax, own


SM_ST = [20, 50, 100]


def _st_P(trig, filters):
    P = {"trig": trig, "filters": filters}
    fam = trig[0]
    if fam in TRIG_GRID:
        P["tp"] = trig[2]
    names = [f for f, _ in filters]
    dflt = {"rsi5": 5, "rsi14": 14, "rsi50": 14, "rsi_ext": 14, "rsi5_ext": 5, "rsi50_with": 14}
    lay = {dflt[x] for x in [fam] + names if x in dflt}
    if lay:
        P["rsi_len"] = lay.pop() if len(lay) == 1 else None   # None: each RSI layer keeps its own length
    if fam == "ema" or any(f.startswith("ema_") for f in names):
        P["ema"] = (9, 21)
    if fam in ("sma50", "sma20") or any(f.startswith("sma50_") for f in names):
        P["sma"] = 20 if fam == "sma20" else 50
    for i, (f, p) in enumerate(filters):
        if f in FILT_GRID:
            P[f"f{i}"] = p
    return P


def f_st_resolved(D, P, s):
    """Apply the axis values (tp, f<i>) to the trigger / filter tuple, then the ST engine."""
    fam, d, p = P["trig"]
    if "tp" in P:
        p = P["tp"]
    filters = [(f, P.get(f"f{i}", q)) for i, (f, q) in enumerate(P["filters"])]
    Q = dict(P, trig=(fam, d, p), filters=filters)
    if fam == "rsi14" and Q.get("rsi_len") is None:
        Q["rsi_len"] = 14
    return f_st(D, Q, s)


def st_specs():
    out = []
    for nm, side, g, trig, filters in ST:
        ax, own = _st_axes(trig, filters)
        out.append({"name": nm, "group": "lab", "lineage": "ST", "side": side, "geom": g, "min_adv": 95e6,
                    "fn": f_st_resolved, "P0": _st_P(trig, filters), "axes": ax, "own": tuple(own),
                    "prior_tries": 120500})
    return out


TRIG_FAMS = ["vwap", "ema", "macd", "rsi14", "rsi5", "or", "sma50", "sma20", "pdbrk", "pdfail", "band05", "band10",
             "hodlod", "rsi50", "volspike", "fo3", "slope20", "flow3"]
TRIG_DEF = {"rsi14": 30, "rsi5": 20, "band05": 0.5, "band10": 1.0, "volspike": 2.0, "fo3": 3.0, "flow3": 0.5}


def trig_specs():
    out = []
    for fam in TRIG_FAMS:
        for d in ("up", "dn"):
            for side in ("long", "short"):
                trig = (fam, d, TRIG_DEF.get(fam))
                ax, own = _st_axes(trig, [])
                out.append(_common_axes({"name": f"T-{fam}-{d}-{side}", "group": "trigger", "lineage": "stack-trigger",
                                         "side": side, "geom": "t1s1", "min_adv": 95e6, "fn": f_st_resolved,
                                         "P0": _st_P(trig, []), "axes": ax, "own": tuple(own),
                                         "prior_tries": 120500}))
    return out


def reddit_specs():
    import strategies as RS
    out = []
    for rule, (fn, p0, grid, _k) in RS.STRATS.items():
        for side in ("long", "short"):
            P0 = {"rule": rule, "p": p0}
            ax = {"p": sorted(set(grid) | {p0})}
            own = []
            if rule in ("R09-ema20-pullback",):
                P0["ema"], ax["ema"] = (9, 21), EMA_PAIRS
                P0["sma"], ax["sma"] = 20, [20, 50, 100]
                own.append("ma")
            if rule == "R10-ema-cross":
                P0["ema"], ax["ema"] = (9, 21), EMA_PAIRS
            if rule == "R11-rsi-os":
                P0["rsi_len"], ax["rsi_len"] = 14, RL
                ax["p"] = [20, 25, 30, 35]
            if rule == "R20-sma-macd":
                P0["sma"], ax["sma"] = 20, [20, 50, 100]
                own.append("ma")
            if rule == "R03-vwap-fade":
                P0["unit_sd"], ax["unit_sd"] = None, [None, 1.0, 1.5, 2.0, 2.5]
            out.append(_common_axes({"name": f"{rule}-{side}", "group": "reddit", "lineage": "reddit", "side": side,
                                     "geom": "t1s1", "min_adv": 95e6, "fn": f_reddit, "P0": P0, "axes": ax,
                                     "own": tuple(own), "prior_tries": 2551 + 800}))
    return out


def all_specs():
    return lab_specs() + reddit_specs() + trig_specs()
