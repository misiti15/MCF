"""Scan every pre-declared configuration of one family (PLAN.md). Usage: python scan.py <HS|HL|ORB|IM|LIQ>.
Writes scratch <fam>_scan.parquet (all configs; summary columns). Educational only - not financial advice."""
import itertools
import json
import sys
import time

import numpy as np
import pandas as pd

from common import SCR, GEOMS, Fam, load

FAM = sys.argv[1]
CUTS = json.load(open(SCR / "cuts.json"))["atr"]
FL = None
W5 = {"0950-1030": (950, 1030), "1030-1130": (1030, 1130), "1130-1300": (1130, 1300), "1300-1500": (1300, 1500),
      "0950-1500": (950, 1500)}
OPP = {"long": "short", "short": "long"}
rows = []
t0 = time.time()


def rec(fam, stage, cfg, parts_fn, **kw):
    """parts_fn(geom) -> list of (idx, side, geom)."""
    for g in GEOMS:
        sc = FM.score(parts_fn(g))
        rows.append({"fam": fam, "stage": stage, "cfg": cfg, "geom": g, **kw, **sc})


if FAM in ("HS", "HL"):
    S = load(FAM.lower(), 125)
    FM = Fam(S, CUTS)
    FL = list(FM.F)
    c = FM.col
    sc_ = c["hs_score" if FAM == "HS" else "hl_score"]
    psid = "short" if FAM == "HS" else "long"
    WS = dict(W5) if FAM == "HS" else {**W5, "1105-1330": (1105, 1330)}
    PW = "0950-1030" if FAM == "HS" else "1105-1330"
    PT, PG = (11.3, "fo-") if FAM == "HS" else (57.5, "gap+")
    TS = [5, 11.3, 15, 20, 25, 30] if FAM == "HS" else [30, 40, 50, 57.5, 65, 75]
    GATES = ["fo-", "none", "gap-", "gap+", "fo+"] if FAM == "HS" else ["gap+", "none", "gap-", "fo+", "fo-"]
    with np.errstate(invalid="ignore"):
        GM = {"none": np.ones(len(S), bool), "fo-": c["fromOpen"] < 0, "fo+": c["fromOpen"] > 0,
              "gap-": c["gap"] < 0, "gap+": c["gap"] > 0}
    WM = {k: FM.win(*v) for k, v in WS.items()}

    def core(T, gt):
        with np.errstate(invalid="ignore"):
            return (sc_ >= T) & GM[gt]

    for T, gt, w, sd in itertools.product(TS, GATES, WS, ("parent", "opp")):
        m = core(T, gt) & WM[w]
        side = psid if sd == "parent" else OPP[psid]
        rec(FAM, "A", f"T{T}|{gt}", lambda g: [(FM.pick(m, side, g), side, g)], T=T, gate=gt, window=w, side=side, refire=0)
    cm = core(PT, PG)
    for f, w, sd in itertools.product(FL, WS, ("parent", "opp")):
        side = psid if sd == "parent" else OPP[psid]
        m = cm & FM.F[f] & WM[w]
        for rf in (0, 1):
            rec(FAM, "B" if not rf else "D", f"core|{f}", lambda g: [(FM.pick(m, side, g, bool(rf)), side, g)],
                T=PT, gate=PG, window=w, side=side, refire=rf, f1=f)
    for (f1, f2), w in itertools.product(itertools.combinations(FL, 2), (PW, "0950-1500")):
        m = cm & FM.F[f1] & FM.F[f2] & WM[w]
        rec(FAM, "C", f"core|{f1}&{f2}", lambda g: [(FM.pick(m, psid, g), psid, g)],
            T=PT, gate=PG, window=w, side=psid, refire=0, f1=f1, f2=f2)

elif FAM == "ORB":
    S = load("orb", 95)
    FM = Fam(S, CUTS)
    FL = list(FM.F)
    c = FM.col
    ev = c["ev"]
    WS = {"0955-1030": (955, 1030), "0955-1130": (955, 1130), "1130-1300": (1130, 1300), "1300-1500": (1300, 1500),
          "0955-1500": (955, 1500)}
    WM = {k: FM.win(*v) for k, v in WS.items()}
    with np.errstate(invalid="ignore"):
        agree = ev == np.sign(c["fo950"])
        vwok = ev * c["vw950"] > 0
    RV = {"none": None, "1": 1.0, "1.5": 1.5, "2": 2.0, "3": 3.0}

    def coremask(dr, vw, rv):
        m = np.ones(len(S), bool)
        if dr == "agree":
            m &= agree
        if vw == "on":
            m &= vwok
        if RV[rv] is not None:
            with np.errstate(invalid="ignore"):
                m &= c["rv950"] >= RV[rv]
        return m

    def parts(m, sd, g, rf=False):
        out = []
        for e, s in ((1, "long"), (-1, "short")):
            side = s if sd == "with" else OPP[s]
            out.append((FM.pick(m & (ev == e), side, g, rf), side, g))
        return out

    for dr, vw, rv, w, sd in itertools.product(("agree", "any"), ("on", "off"), RV, WS, ("with", "fade")):
        m = coremask(dr, vw, rv) & WM[w]
        rec(FAM, "A", f"{dr}|vwap-{vw}|rv{rv}", lambda g: parts(m, sd, g), window=w, side=sd, refire=0, dr=dr, vw=vw, rv=rv)
    cm = coremask("agree", "on", "1.5")
    for f, w, sd in itertools.product(FL, WS, ("with", "fade")):
        m = cm & FM.F[f] & WM[w]
        for rf in (0, 1):
            rec(FAM, "B" if not rf else "D", f"core|{f}", lambda g: parts(m, sd, g, bool(rf)), window=w, side=sd,
                refire=rf, f1=f)
    for (f1, f2), w in itertools.product(itertools.combinations(FL, 2), ("0955-1130", "0955-1500")):
        m = cm & FM.F[f1] & FM.F[f2] & WM[w]
        rec(FAM, "C", f"core|{f1}&{f2}", lambda g: parts(m, "with", g), window=w, side="with", refire=0, f1=f1, f2=f2)

elif FAM == "IM":
    S = load("im", 95)
    FM = Fam(S, CUTS)
    FL = list(FM.F)
    c = FM.col
    etf = S["symbol"].isin(["SPY", "QQQ", "IWM", "DIA"]).to_numpy()
    r30, sr30 = c["r30"], c["spy_r30"]
    EM = {e: FM.tod == e for e in (1030, 1100, 1200, 1300, 1400, 1500)}

    def parts(mlong, mshort, sd, g):
        out = []
        for m, s in ((mlong, "long"), (mshort, "short")):
            side = s if sd == "with" else OPP[s]
            out.append((FM.pick(m, side, g), side, g))
        return out

    with np.errstate(invalid="ignore"):
        for thr, sd, e in itertools.product((0.25, 0.5, 1.0), ("with", "against"), EM):
            ml, ms = etf & EM[e] & (r30 >= thr), etf & EM[e] & (r30 <= -thr)
            rec(FAM, "A-etf", f"etf|thr{thr}", lambda g: parts(ml, ms, sd, g), window=str(e), side=sd, refire=0, T=thr)
        RULE = {"any": (np.ones(len(S), bool), np.ones(len(S), bool)), "same": (r30 > 0, r30 < 0),
                "strong": (r30 >= 1, r30 <= -1)}
        for thr, rule, sd, e in itertools.product((0.25, 0.5, 1.0), RULE, ("with", "against"), EM):
            ml = EM[e] & (sr30 >= thr) & RULE[rule][0]
            ms = EM[e] & (sr30 <= -thr) & RULE[rule][1]
            rec(FAM, "A-univ", f"univ|thr{thr}|{rule}", lambda g: parts(ml, ms, sd, g), window=str(e), side=sd, refire=0,
                T=thr, rule=rule)
        for f, e, sd in itertools.product(FL, (1030, 1300, 1500), ("with", "against")):
            ml = EM[e] & (sr30 >= 0.25) & (r30 > 0) & FM.F[f]
            ms = EM[e] & (sr30 <= -0.25) & (r30 < 0) & FM.F[f]
            rec(FAM, "B", f"univcore|{f}", lambda g: parts(ml, ms, sd, g), window=str(e), side=sd, refire=0, f1=f)

elif FAM == "LIQ":
    S = load("liq", 95)
    FM = Fam(S, CUTS)
    FL = list(FM.F)
    c = FM.col
    bits = S["bits"].to_numpy(np.int64)
    SETS = list(itertools.product(("OR", "PD"), ("low", "high"), (0.05, 0.10, 0.15, 0.25), ("open", "lvl"), (5, 15)))
    WS = {"0950-1100": (950, 1100), "1100-1300": (1100, 1300), "1300-1500": (1300, 1500), "0950-1500": (950, 1500)}
    WM = {k: FM.win(*v) for k, v in WS.items()}
    EVM = {s: ((bits >> i) & 1).astype(bool) for i, s in enumerate(SETS)}
    with np.errstate(invalid="ignore"):
        room = c["close"] * (1 / (1 + c["vwapDistPct"] / 100) - 1) / c["atr_d"]   # (vwap - close) / ATR
    for s, sd, w in itertools.product(SETS, ("rev", "cont"), WS):
        side = ("long" if s[1] == "low" else "short") if sd == "rev" else ("short" if s[1] == "low" else "long")
        m = EVM[s] & WM[w]
        for rf in (0, 1):
            rec(FAM, "A" if not rf else "A-refire", "|".join(map(str, s)), lambda g: [(FM.pick(m, side, g, bool(rf)), side, g)],
                window=w, side=side, refire=rf, sd=sd)
    CORES = {"ORL": ("OR", "low", 0.15, "open", 15), "PDL": ("PD", "low", 0.05, "open", 15)}
    with np.errstate(invalid="ignore"):
        FX = {**FM.F, "vroom>=0.5": room >= 0.5}
    for (cn, s), f, w, sd in itertools.product(CORES.items(), list(FX), WS, ("rev", "cont")):
        side = "long" if sd == "rev" else "short"
        m = EVM[s] & FX[f] & WM[w]
        rec(FAM, "B", f"{cn}|{f}", lambda g: [(FM.pick(m, side, g), side, g)], window=w, side=side, refire=0, f1=f, core=cn)
    for (cn, s), (f1, f2) in itertools.product(CORES.items(), itertools.combinations(FL, 2)):
        m = EVM[s] & FM.F[f1] & FM.F[f2] & WM["0950-1500"]
        rec(FAM, "C", f"{cn}|{f1}&{f2}", lambda g: [(FM.pick(m, "long", g), "long", g)], window="0950-1500", side="long",
            refire=0, f1=f1, f2=f2, core=cn)

out = pd.DataFrame(rows)
out.to_parquet(SCR / f"{FAM}_scan.parquet", index=False)
print(FAM, "configs", len(out), "secs", round(time.time() - t0), flush=True)
print(out.groupby("stage").size().to_dict())
