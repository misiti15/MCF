"""Video-digest setup rules (BDI 2026-10-08): triggers and layers over the lab frame + features.py columns.
numpy only, so a `type: lab` module can call them live with the same code the scanner used.
Educational only - not financial advice."""
import numpy as np

GEOMS = ("t1s1", "t05s1", "t1s05")
ANCH = ("open", "pdhv", "pdh", "pdl", "tdhv")

# ------------------------------------------------------------------ triggers (params p; base values in BASE)
BASE = {"MP": {"tol": 0.02, "vthr": 1.0}, "VT": {"w": 0.5, "vr": 2.0}, "JD": {"tol": 0.02, "strong": 0.8},
        "VA": {"pct": 70}, "BLK": {}, "LVN": {"k": 50}, "AVR": {"d": 30}, "AVF": {},
        "IC": {}, "ENVF": {"k": 2.0}, "ENVC": {"strong": 0.8, "surge": 1.5}, "SWP": {"dmin": 0.0},
        "OFP": {"hvn": 0.5, "lvn": 0.3, "dag": 0.3}, "BK": {"tol": 0.02}, "VA30": {"pct": 70}, "PINCH": {}, "PWR": {"d": 30}}
ANCH2 = ("pwh", "pwl", "gap", "qop")
VARS = {
    "MP": [dict(touch=t, kmax=k, vol=v) for t in ("e9", "vw", "any") for k in (1, 2, 3) for v in ("any", "light")],
    "VT": [dict(kind=k) for k in ("peak", "vr2")],
    "JD": [dict(trend=t) for t in ("any", "strong")],
    "VA": [dict(kind=k) for k in ("cross1", "cross2", "inside")],
    "BLK": [dict(L=L, c=c, e=25) for L in (6, 12) for c in (30, 50)],
    "LVN": [dict(a=a) for a in (0.15, 0.30)],
    "AVR": [dict(anchor=a, delta=d) for a in ANCH for d in ("any", "green")],
    "AVF": [dict(anchor=a, k=k) for a in ANCH for k in (2.0, 2.5)],
    "IC": [dict(anchor=a, tol=t, kind=k) for a in ANCH2 for t in (0.1, 0.2, 0.3) for k in ("bounce", "break")],
    "ENVF": [dict(drop=d) for d in ("1bar", "vr")],
    "ENVC": [dict(level=lv, surge=sg) for lv in ("sd1", "vw") for sg in ("cum", "bar")],
    "SWP": [dict(x=x, m=m) for x in (5, 10, 20) for m in (1, 2, 3)],
    "OFP": [dict(where=w, when=t) for w in ("hvnedge", "lvnedge") for t in ("aggr", "absorb")],
    "BK": [dict(trend=t) for t in ("e20", "e20vw")],
    "VA30": [dict(kind=k) for k in ("close", "full")],
    "PINCH": [dict(p=p) for p in (0.25, 0.5)],
    "PWR": [dict(anchor=a, delta=d) for a in ("pwh", "pwl") for d in ("any", "green")],
}
_X4 = list(GEOMS) + ["jd", "e9c1", "tx"]
EXITS = {"MP": list(GEOMS) + ["jd", "e9c1", "vt", "vt9", "tx", "c9", "trail9"], "VT": list(GEOMS) + ["jd", "e9c1", "tx"],
         "JD": list(GEOMS) + ["jd", "e9c1", "vt9", "tx", "c9", "trail9"], "VA": list(GEOMS) + ["poc", "poc2", "jd", "tx"],
         "BLK": list(GEOMS) + ["blk"], "LVN": list(GEOMS) + ["jd", "e9c1", "tx"], "AVR": list(GEOMS) + ["jd", "e9c1", "tx"],
         "AVF": list(GEOMS) + ["avw", "e9c1"],
         "IC": _X4, "ENVF": list(GEOMS) + ["avw", "e9c1"], "ENVC": list(GEOMS) + ["jd", "c9", "trail9", "tx"], "SWP": _X4,
         "OFP": _X4, "BK": list(GEOMS) + ["trail9", "c9", "tx"], "VA30": list(GEOMS) + ["poc2", "poc", "tx"], "PINCH": _X4,
         "PWR": _X4}


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
        if fam == "IC":
            a = v["anchor"]
            av, vw = c[f"av_{a}"], c["vw5"]
            conf = np.abs(vw - av) / vw * 100 <= p.get("tol", v["tol"])
            lvl = np.maximum(vw, av) if s > 0 else np.minimum(vw, av)
            if v["kind"] == "bounce":
                hit = ((c["c_p1"] > lvl) & (c["l5"] <= lvl) & (c["c5"] > lvl)) if s > 0 else \
                      ((c["c_p1"] < lvl) & (c["h5"] >= lvl) & (c["c5"] < lvl))
            else:
                hit = ((c["c_p1"] <= lvl) & (c["c5"] > lvl)) if s > 0 else ((c["c_p1"] >= lvl) & (c["c5"] < lvl))
            return conf & hit
        if fam == "ENVF":
            k = p["k"]
            drop = (c["v5"] < c["v_p1"]) if v["drop"] == "1bar" else (c["volumeRatio"] < 1)
            ok = c["sd1"] > 0
            if s < 0:
                return ok & (c["h5"] >= c["vw1"] + k * c["sd1"]) & drop
            return ok & (c["l5"] <= c["vw1"] - k * c["sd1"]) & drop
        if fam == "ENVC":
            tol = 0.02 * c["atr_b"]
            lvl = c["vw1"] + s * c["sd1"] if v["level"] == "sd1" else c["vw1"]
            surge = (c["rvol"] >= p["surge"]) if v["surge"] == "cum" else (c["volumeRatio"] >= p["surge"])
            if s > 0:
                return (c["pct_abv"] >= p["strong"]) & (c["l5"] <= lvl + tol) & (c["c5"] > lvl) & surge
            return (c["pct_blw"] >= p["strong"]) & (c["h5"] >= lvl - tol) & (c["c5"] < lvl) & surge
        if fam == "SWP":
            nm = "L" if s > 0 else "S"
            x, m = p.get("x", v["x"]), p.get("m", v["m"])
            return (c[f"sw{nm}_{x}_{m}"] > 0) & (s * c["dlt"] > p["dmin"])
        if fam == "OFP":
            if s > 0:
                dn, air = c["dlo"], c["aDlo"]
                upper = c["c5"] >= (c["h5"] + c["l5"]) / 2
            else:
                dn, air = c["dhi"], c["aUhi"]
                upper = c["c5"] <= (c["h5"] + c["l5"]) / 2
            where = ((dn >= p["hvn"]) & (air < p["lvn"])) if v["where"] == "hvnedge" else ((dn < p["lvn"]) & upper)
            when = (s * c["dlt"] >= p["dag"]) if v["when"] == "aggr" else ((s * c["dlt"] <= 0) & (s * (c["c5"] - c["o5"]) >= 0))
            return where & when
        if fam == "BK":
            tol = p["tol"] * c["atr_b"]
            if s > 0:
                m = (c["e9"] > c["e20"]) & (c["l5"] <= c["e9"] + tol) & (c["c5"] >= c["e9"])
                return m & (c["c5"] > c["vw5"]) if v["trend"] == "e20vw" else m
            m = (c["e9"] < c["e20"]) & (c["h5"] >= c["e9"] - tol) & (c["c5"] <= c["e9"])
            return m & (c["c5"] < c["vw5"]) if v["trend"] == "e20vw" else m
        if fam == "VA30":
            P = p["pct"]
            lo, hi = c[f"pval{P}"], c[f"pvah{P}"]
            opened = (c["day_open"] < lo) if s > 0 else (c["day_open"] > hi)
            if v["kind"] == "close":
                ins = (c["c30a"] > lo) & (c["c30a"] < hi) & (c["c30b"] > lo) & (c["c30b"] < hi)
            else:
                ins = (c["l30a"] >= lo) & (c["h30a"] <= hi) & (c["l30b"] >= lo) & (c["h30b"] <= hi)
            ahead = (c["c5"] < hi) if s > 0 else (c["c5"] > lo)
            return opened & ins & ahead
        if fam == "PINCH":
            a1, a2 = c["av_qop"], c["av_gap"]
            pinch = np.abs(a1 - a2) / c["c5"] * 100 <= p.get("p", v["p"])
            lvl = np.maximum(a1, a2) if s > 0 else np.minimum(a1, a2)
            brk = ((c["c_p1"] <= lvl) & (c["c5"] > lvl)) if s > 0 else ((c["c_p1"] >= lvl) & (c["c5"] < lvl))
            return pinch & brk & (s * c["dlt"] > 0)
        if fam == "PWR":
            nm = "L" if s > 0 else "S"
            m = c[f"rt{nm}_{v['anchor']}_{p['d']}"] > 0
            if v["delta"] == "green":
                m &= (s * (c["c5"] - c["o5"]) > 0)
            return m
    raise KeyError(fam)


# ------------------------------------------------------------------ layers
LAYERS = ["rvol15", "rvol2", "vwap_with", "vwap_against", "e9_with", "m15_with", "rsi5_hi", "rsi5_lo", "flowsell",
          "flowbuy", "gap_with", "gap_against", "gapper", "orb_with", "dsma20_with", "pdroom", "dcn", "vslope"]
LBASE = {"rvol15": 1.5, "rvol2": 2.0, "rsi5_hi": 70, "rsi5_lo": 30, "flowsell": -0.25, "flowbuy": 0.25, "gap_with": 1.0,
         "gap_against": 1.0, "gapper": 2.0, "pdroom": 0.5, "dcn": 0.2, "vslope": 0.03}



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
        if name == "dcn":
            return np.abs(c["vw5"] - c["spoc"]) / c["vw5"] * 100 <= t
        if name == "vslope":
            return c["vsl"] >= t
    raise KeyError(name)


