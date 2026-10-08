"""Declared grid for the 2026-10-08 rework (see NOTES.md section 0). Expressions are numpy expressions over the
names built by `namespace()`, so the very same strings are written into the LabStrategy modules.
Educational only - not financial advice."""
from __future__ import annotations

import itertools

import numpy as np

# ---------------------------------------------------------------- expressions (live-lab-frame columns only)
EXPR = {
    # F1 triggers
    "rsi_x40dn": "(rsi <= 40) & (p_rsi > 40)",
    "rsi_x60up": "(rsi >= 60) & (p_rsi < 60)",
    "x_sma20_up": "(sma20 > 0) & (p_sma20 <= 0)",
    "x_sma20_dn": "(sma20 < 0) & (p_sma20 >= 0)",
    "x_sma50_up": "(sma50 > 0) & (p_sma50 <= 0)",
    "x_sma50_dn": "(sma50 < 0) & (p_sma50 >= 0)",
    "vwap_reclaim": "(vwap > 0) & (p_vwap <= 0)",
    "vwap_loss": "(vwap < 0) & (p_vwap >= 0)",
    "hod_break": "(hod - p_hod > 0.005)",
    "lod_break": "(p_lod - lod > 0.005)",
    # F1 states
    "rsi>=60": "(rsi >= 60)", "rsi>=70": "(rsi >= 70)", "rsi<=30": "(rsi <= 30)", "rsi<=40": "(rsi <= 40)",
    "rsi5>=80": "(rsi5 >= 80)", "rsi5<=20": "(rsi5 <= 20)", "above_sma50": "(sma50 > 0)", "below_sma50": "(sma50 < 0)",
    "vol>=2x": "(vr >= 2)", "gap_up": "(gap >= 0.5)", "gap_dn": "(gap <= -0.5)",
    # F2
    "heat<=-20": "(heat <= -20)", "heat<=-30": "(heat <= -30)", "heat<=-40": "(heat <= -40)",
    "bp<-0.15": "(bp < -0.15)", "bp<-0.25": "(bp < -0.25)", "bp<-0.35": "(bp < -0.35)",
    "vwap>0.05": "(vwap > 0.05)", "rsi5>70": "(rsi5 > 70)", "rsi5>80": "(rsi5 > 80)",
    "rsi55-65": "((rsi >= 55) & (rsi <= 65))", "rsi>65": "(rsi > 65)", "fo>1": "(fo > 1)", "fo<-1": "(fo < -1)",
    "gap>0": "(gap > 0)", "gap<0": "(gap < 0)",
    # F3
    "rsi5>85": "(rsi5 > 85)", "rsi5>90": "(rsi5 > 90)", "rsi5>95": "(rsi5 > 95)",
    "sma20>0.5": "(sma20 > 0.5)", "sma20>1.0": "(sma20 > 1.0)", "sma20>1.5": "(sma20 > 1.5)",
    "bear_div": "(bdiv > 0)", "uwick>=0.5": "(uw >= 0.5)",
    "rsi5<15": "(rsi5 < 15)", "rsi5<10": "(rsi5 < 10)", "rsi5<5": "(rsi5 < 5)",
    "sma20<-0.5": "(sma20 < -0.5)", "sma20<-1.0": "(sma20 < -1.0)", "sma20<-1.5": "(sma20 < -1.5)",
    "bull_div": "(udiv > 0)", "lwick>=0.5": "(lw >= 0.5)",
}
for _p in (1, 2, 3, 4):
    EXPR[f"up>{_p}%"] = f"(fo > {_p})"
    EXPR[f"dn>{_p}%"] = f"(fo < -{_p})"
for _a in (0.5, 0.75, 1.0, 1.5):
    EXPR[f"up>{_a}atr"] = f"(mv >= {_a})"
    EXPR[f"dn>{_a}atr"] = f"(mv <= -{_a})"

DESC = {"rsi_x40dn": "RSI(14) crosses below 40 on this bar", "rsi_x60up": "RSI(14) crosses above 60 on this bar",
        "x_sma20_up": "close crosses above the 5-min SMA20", "x_sma20_dn": "close crosses below the 5-min SMA20",
        "x_sma50_up": "close crosses above the 5-min SMA50", "x_sma50_dn": "close crosses below the 5-min SMA50",
        "vwap_reclaim": "close crosses above VWAP", "vwap_loss": "close crosses below VWAP",
        "hod_break": "new high of day on this bar", "lod_break": "new low of day on this bar"}

# ---------------------------------------------------------------- dimensions
F1_T = ["rsi_x40dn", "rsi_x60up", "x_sma20_up", "x_sma20_dn", "x_sma50_up", "x_sma50_dn", "vwap_reclaim", "vwap_loss",
        "hod_break", "lod_break"]
F1_M = ["none"] + [f"{d}>{p}%" for d in ("up", "dn") for p in (1, 2, 3, 4)] + \
       [f"{d}>{a}atr" for d in ("up", "dn") for a in (0.5, 0.75, 1.0, 1.5)]
F1_S = ["none", "rsi>=60", "rsi>=70", "rsi<=30", "rsi<=40", "rsi5>=80", "rsi5<=20", "above_sma50", "below_sma50",
        "vol>=2x", "gap_up", "gap_dn"]
F1_W = {"early": (950, 1030), "am": (950, 1130), "mid": (1030, 1300), "pm": (1130, 1500), "all": (950, 1500)}

F2_H = ["none", "heat<=-20", "heat<=-30", "heat<=-40"]
F2_B = ["bp<-0.15", "bp<-0.25", "bp<-0.35"]
F2_E = ["none", "vwap>0.05", "rsi5>70", "rsi5>80", "rsi55-65", "rsi>65", "fo>1", "fo<-1"]
F2_G = ["none", "gap>0", "gap<0"]
F2_W = {"w0950_1030": (950, 1030), "w0950_1100": (950, 1100), "w0950_1130": (950, 1130), "w1100_1300": (1100, 1300),
        "w1300_1500": (1300, 1500), "w0950_1500": (950, 1500)}

F3_BEAR = (["rsi5>85", "rsi5>90", "rsi5>95"], ["sma20>0.5", "sma20>1.0", "sma20>1.5"], ["bear_div", "none"],
           ["uwick>=0.5", "none"])
F3_BULL = (["rsi5<15", "rsi5<10", "rsi5<5"], ["sma20<-0.5", "sma20<-1.0", "sma20<-1.5"], ["bull_div", "none"],
           ["lwick>=0.5", "none"])
F3_W = {"w0950_1130": (950, 1130), "w1100_1300": (1100, 1300), "w1200_1500": (1200, 1500), "w1300_1500": (1300, 1500),
        "w0950_1500": (950, 1500)}

WINDOWS = {**F1_W, **F2_W, **F3_W}


def combos():
    """Yield (family, conds tuple incl. 'none', window name) - each x 2 sides x 3 geoms = configs."""
    for t, m, s in itertools.product(F1_T, F1_M, F1_S):
        for w in F1_W:
            yield "F1", (t, m, s), w
    for h, b, e, g in itertools.product(F2_H, F2_B, F2_E, F2_G):
        for w in F2_W:
            yield "F2", (h, b, e, g), w
    for dims, tag in ((F3_BEAR, "bear"), (F3_BULL, "bull")):
        for c in itertools.product(*dims):
            for w in F3_W:
                yield "F3" + tag, c, w


def namespace(get, prev) -> dict:
    """get(col) -> float array; prev(x) -> previous bar within the symbol-day."""
    close, atr = get("close"), get("atr_d")
    fo = get("fromOpen")
    hod = close + get("dist_hod_atr") * atr
    lod = close - get("dist_lod_atr") * atr
    ns = {"rsi": get("rsi"), "rsi5": get("rsi5"), "sma20": get("sma20_dist_pct"), "sma50": get("sma50_dist_pct"),
          "vwap": get("vwapDistPct"), "vr": get("volumeRatio"), "fo": fo, "gap": get("gap"), "heat": get("heat"),
          "bp": get("buyPressure"), "hod": hod, "lod": lod, "bdiv": get("bear_div"), "udiv": get("bull_div"),
          "uw": get("upper_wick"), "lw": get("lower_wick"), "tod": get("tod")}
    ns["mv"] = (close - close / (1 + fo / 100)) / atr
    for k in ("rsi", "sma20", "sma50", "vwap", "hod", "lod"):
        ns["p_" + k] = prev(ns[k])
    return ns


def cond_expr(conds) -> str:
    return " & ".join(EXPR[c] for c in conds if c != "none") or "np.ones(len(tod), bool)"


def evaluate(conds, ns) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.asarray(eval(cond_expr(conds), {"np": np}, ns), dtype=bool)


def cfg_id(fam, conds, w, side, geom) -> str:
    return f"{fam}|{'+'.join(c for c in conds if c != 'none') or 'none'}|{w}|{side}|{geom}"
