"""Video-digest setup rules (BDI 2026-10-08): triggers and layers over the lab frame + features.py columns.
numpy only, so a `type: lab` module can call them live with the same code the scanner used.
Educational only - not financial advice."""
import numpy as np

GEOMS = ("t1s1", "t05s1", "t1s05")
ANCH = ("open", "pdhv", "pdh", "pdl", "tdhv")

# ------------------------------------------------------------------ triggers (params p; base values in BASE)
BASE = {"MP": {"tol": 0.02, "vthr": 1.0}, "VT": {"w": 0.5, "vr": 2.0}, "JD": {"tol": 0.02, "strong": 0.8},
        "VA": {"pct": 70}, "BLK": {}, "LVN": {"k": 50}, "AVR": {"d": 30}, "AVF": {}}
VARS = {
    "MP": [dict(touch=t, kmax=k, vol=v) for t in ("e9", "vw", "any") for k in (1, 2, 3) for v in ("any", "light")],
    "VT": [dict(kind=k) for k in ("peak", "vr2")],
    "JD": [dict(trend=t) for t in ("any", "strong")],
    "VA": [dict(kind=k) for k in ("cross1", "cross2", "inside")],
    "BLK": [dict(L=L, c=c, e=25) for L in (6, 12) for c in (30, 50)],
    "LVN": [dict(a=a) for a in (0.15, 0.30)],
    "AVR": [dict(anchor=a, delta=d) for a in ANCH for d in ("any", "green")],
    "AVF": [dict(anchor=a, k=k) for a in ANCH for k in (2.0, 2.5)],
}
EXITS = {"MP": list(GEOMS) + ["jd", "e9c1", "vt", "vt9", "tx"], "VT": list(GEOMS) + ["jd", "e9c1", "tx"],
         "JD": list(GEOMS) + ["jd", "e9c1", "vt9", "tx"], "VA": list(GEOMS) + ["poc", "poc2", "jd", "tx"],
         "BLK": list(GEOMS) + ["blk"], "LVN": list(GEOMS) + ["jd", "e9c1", "tx"], "AVR": list(GEOMS) + ["jd", "e9c1", "tx"],
         "AVF": list(GEOMS) + ["avw", "e9c1"]}


def trig(D, fam, s, v, p, ex):
    c = D
    with np.errstate(invalid="ignore"):
        if fam == "MP":
            nm = "L" if s > 0 else "S"
            ln = c[f"pb{nm}_len"]
            m = (ln >= 1) & (ln <= v["kmax"]) & (c[f"pb{nm}_hold"] >= 0)
            te, tv = c[f"pb{nm}_de9"] <= p["tol"], c[f"pb{nm}_dvw"] <= p["tol"]
            m &= {"e9": te, "vw": tv, "any": te | tv}[v["touch"]]
            if v["vol"] == "light":
                m &= c[f"pb{nm}_vr"] < p["vthr"]
            if s > 0:
                m &= (c["h5"] > c["h_p1"]) & (c["c5"] > c["e9"]) & (c["c5"] > c["vw5"]) & (c["e9"] > c["vw5"])
            else:
                m &= (c["l5"] < c["l_p1"]) & (c["c5"] < c["e9"]) & (c["c5"] < c["vw5"]) & (c["e9"] < c["vw5"])
            return m
        if fam == "VT":
            vol = (c["v5"] >= c["vpk_p"]) if v["kind"] == "peak" else (c["volumeRatio"] >= p["vr"])
            if s < 0:
                return (c["h5"] >= c["hod_p"]) & (c["uw"] >= p["w"]) & vol
            return (c["l5"] <= c["lod_p"]) & (c["lw"] >= p["w"]) & vol
        if fam == "JD":
            tol = p["tol"] * c["atr_b"]
            if s > 0:
                m = (c["c5"] > c["vw5"]) & (c["e9"] > c["vw5"]) & (c["l5"] <= c["e9"] + tol) & (c["c5"] >= c["e9"])
                return m & (c["pct_abv"] >= p["strong"]) if v["trend"] == "strong" else m
            m = (c["c5"] < c["vw5"]) & (c["e9"] < c["vw5"]) & (c["h5"] >= c["e9"] - tol) & (c["c5"] <= c["e9"])
            return m & (c["pct_blw"] >= p["strong"]) if v["trend"] == "strong" else m
        if fam == "VA":
            P = p["pct"]
            if s > 0:
                lvl = c[f"pval{P}"]
                m = (c["day_open"] < lvl) & (c["c5"] > lvl) & (c["c5"] < c["ppoc"])
                out = lambda x: x <= lvl
                ins = lambda x: x > lvl
            else:
                lvl = c[f"pvah{P}"]
                m = (c["day_open"] > lvl) & (c["c5"] < lvl) & (c["c5"] > c["ppoc"])
                out = lambda x: x >= lvl
                ins = lambda x: x < lvl
            if v["kind"] == "cross1":
                m &= out(c["c_p1"])
            elif v["kind"] == "cross2":
                m &= ins(c["c_p1"]) & out(c["c_p2"])
            return m
        if fam == "BLK":
            nm = "L" if s > 0 else "S"
            key = f"{v['L']}_{v['c']}_{p.get('e', v['e'])}"
            return c[f"{'bp' if ex == 'blk' else 'bk'}{nm}_{key}"] > 0
        if fam == "LVN":
            a = p.get("a", v["a"])
            if s > 0:
                return (c["c5"] > c["hh6"]) & (c[f"airU_{p['k']}"] < a)
            return (c["c5"] < c["ll6"]) & (c[f"airD_{p['k']}"] < a)
        if fam == "AVR":
            nm = "L" if s > 0 else "S"
            m = c[f"rt{nm}_{v['anchor']}_{p['d']}"] > 0
            if v["delta"] == "green":
                m &= (s * (c["c5"] - c["o5"]) > 0)
            return m
        if fam == "AVF":
            a = v["anchor"]
            k = p.get("k", v["k"])
            sd = c[f"sd_{a}"]
            ok = sd > 0
            if s < 0:
                return ok & ((c["h5"] - c[f"av_{a}"]) / sd >= k) & (c["v5"] < c["v_p1"])
            return ok & ((c["l5"] - c[f"av_{a}"]) / sd <= -k) & (c["v5"] < c["v_p1"])
    raise KeyError(fam)


# ------------------------------------------------------------------ layers
LAYERS = ["rvol15", "rvol2", "vwap_with", "vwap_against", "e9_with", "m15_with", "rsi5_hi", "rsi5_lo", "flowsell",
          "flowbuy", "gap_with", "gap_against", "gapper", "orb_with", "dsma20_with", "pdroom"]
LBASE = {"rvol15": 1.5, "rvol2": 2.0, "rsi5_hi": 70, "rsi5_lo": 30, "flowsell": -0.25, "flowbuy": 0.25, "gap_with": 1.0,
         "gap_against": 1.0, "gapper": 2.0, "pdroom": 0.5}
def layer(D, name, s, th=None):
    c = D
    t = LBASE.get(name) if th is None else th
    with np.errstate(invalid="ignore"):
        if name in ("rvol15", "rvol2"):
            return c["rvol"] >= t
        if name == "vwap_with":
            return s * c["vwapDistPct"] > 0
        if name == "vwap_against":
            return s * c["vwapDistPct"] < 0
        if name == "e9_with":
            return s * (c["c5"] - c["e9"]) > 0
        if name == "m15_with":
            return c["m15"] == s
        if name == "rsi5_hi":
            return c["rsi5"] >= t
        if name == "rsi5_lo":
            return c["rsi5"] <= t
        if name == "flowsell":
            return c["buyPressure"] < t
        if name == "flowbuy":
            return c["buyPressure"] > t
        if name == "gap_with":
            return s * c["gap"] >= t
        if name == "gap_against":
            return s * c["gap"] <= -t
        if name == "gapper":
            return np.abs(c["gap"]) >= t
        if name == "orb_with":
            return (c["c5"] > c["orh"]) if s > 0 else (c["c5"] < c["orl"])
        if name == "dsma20_with":
            return s * (c["c5"] - c["d_sma20"]) > 0
        if name == "pdroom":
            d = c["dist_pdh_atr"] if s > 0 else c["dist_pdl_atr"]
            return (d < 0) | (d >= t)
    raise KeyError(name)


