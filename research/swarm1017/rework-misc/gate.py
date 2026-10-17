"""Screen + quality gates for every family scan (PLAN.md 'Gates'). Usage: python gate.py <FAM> [FAM ...].
Re-derives the trades of each screened configuration, then applies the regime gate, walk-forward share, same-minute
random baseline, ex-best-day and plateau checks, and the lineage t bar. Writes <fam>_gated.parquet in scratch.
Educational only - not financial advice."""
import itertools
import json
import math
import sys

import numpy as np
import pandas as pd

from common import SCR, Fam, load
from mcf.research import gates
from research.history2y import lib

CUTS = json.load(open(SCR / "cuts.json"))["atr"]
PRIOR = {"HS": 19236, "HL": 19236, "ORB": 15, "IM": 15, "LIQ": 7718}
STUDY = {"HS": 7116, "HL": 7740, "ORB": 6816, "IM": 1098, "LIQ": 8892}
LINEAGE = {"HS": PRIOR["HS"] + STUDY["HS"] + STUDY["HL"], "HL": PRIOR["HL"] + STUDY["HS"] + STUDY["HL"],
           "ORB": PRIOR["ORB"] + STUDY["ORB"], "IM": PRIOR["IM"] + STUDY["IM"], "LIQ": PRIOR["LIQ"] + STUDY["LIQ"]}
OPP = {"long": "short", "short": "long"}
REG = lib.regimes()


def screen(df):
    return df[(df.n_tr >= 150) & (df.n_va >= 50) & (df.n_all >= 200) & (df.exp_tr > 0) & (df.exp_va > 0)]


def parts_for(fam, FM, row, extra=None):
    """Rebuild the (idx, side, geom) parts of one scan row."""
    c, g = FM.col, row["geom"]
    w = tuple(int(x) for x in row["window"].split("-")) if "-" in str(row["window"]) else None
    rf = bool(row.get("refire", 0))
    F = dict(FM.F)
    if extra:
        F.update(extra)
    fl = [row[k] for k in ("f1", "f2") if k in row and isinstance(row[k], str)]
    if fam in ("HS", "HL"):
        sc = c["hs_score" if fam == "HS" else "hl_score"]
        with np.errstate(invalid="ignore"):
            gm = {"none": np.ones(len(sc), bool), "fo-": c["fromOpen"] < 0, "fo+": c["fromOpen"] > 0,
                  "gap-": c["gap"] < 0, "gap+": c["gap"] > 0}[row["gate"]]
            m = (sc >= row["T"]) & gm & FM.win(*w)
        for f in fl:
            m = m & F[f]
        return [(FM.pick(m, row["side"], g, rf), row["side"], g)]
    if fam == "ORB":
        ev = c["ev"]
        m = FM.win(*w)
        if row["stage"] == "A":
            dr, vw, rv = row["dr"], row["vw"], row["rv"]
        else:
            dr, vw, rv = "agree", "on", "1.5"
        with np.errstate(invalid="ignore"):
            if dr == "agree":
                m = m & (ev == np.sign(c["fo950"]))
            if vw == "on":
                m = m & (ev * c["vw950"] > 0)
            if rv != "none":
                m = m & (c["rv950"] >= float(rv))
        for f in fl:
            m = m & F[f]
        out = []
        for e, s in ((1, "long"), (-1, "short")):
            side = s if row["side"] == "with" else OPP[s]
            out.append((FM.pick(m & (ev == e), side, g, rf), side, g))
        return out
    if fam == "IM":
        e = int(row["window"])
        r30, sr30 = c["r30"], c["spy_r30"]
        em = FM.tod == e
        with np.errstate(invalid="ignore"):
            if row["stage"] == "A-etf":
                etf = FM.S["symbol"].isin(["SPY", "QQQ", "IWM", "DIA"]).to_numpy()
                ml, ms = etf & em & (r30 >= row["T"]), etf & em & (r30 <= -row["T"])
            else:
                thr = row["T"] if row["stage"] == "A-univ" else 0.25
                rule = row["rule"] if row["stage"] == "A-univ" else "same"
                rl, rs = {"any": (True, True), "same": (r30 > 0, r30 < 0), "strong": (r30 >= 1, r30 <= -1)}[rule]
                ml, ms = em & (sr30 >= thr) & rl, em & (sr30 <= -thr) & rs
        for f in fl:
            ml, ms = ml & F[f], ms & F[f]
        out = []
        for m, s in ((ml, "long"), (ms, "short")):
            side = s if row["side"] == "with" else OPP[s]
            out.append((FM.pick(m, side, g), side, g))
        return out
    if fam == "LIQ":
        SETS = list(itertools.product(("OR", "PD"), ("low", "high"), (0.05, 0.10, 0.15, 0.25), ("open", "lvl"), (5, 15)))
        CORES = {"ORL": ("OR", "low", 0.15, "open", 15), "PDL": ("PD", "low", 0.05, "open", 15)}
        if row["stage"] in ("A", "A-refire"):
            p = row["cfg"].split("|")
            s = (p[0], p[1], float(p[2]), p[3], int(p[4]))
        else:
            s = CORES[row["core"]]
        bits = FM.S["bits"].to_numpy(np.int64)
        m = ((bits >> SETS.index(s)) & 1).astype(bool) & FM.win(*w)
        for f in fl:
            m = m & F[f]
        return [(FM.pick(m, row["side"], g, rf), row["side"], g)]
    raise ValueError(fam)


def full_gates(fam, FM, row, extra=None):
    parts = parts_for(fam, FM, row, extra)
    r, ex, d, tr, ix = FM.trades(parts)
    t = pd.DataFrame({"date": np.asarray(FM.dates)[d], "r": r})
    s = gates.summary(t)
    rg = gates.regime_split(t, REG)
    wf = gates.walk_forward(t, exclude_months=lib.LOCKED_MONTHS)
    bar = gates.t_required(LINEAGE[fam])
    res = {"t_bar": bar, "t_sum": s.get("t"), "ex_best_day": s.get("ex_best_day"), "green_days": s.get("green_days"),
           "days": s.get("days"), "up_exp": rg["up"].get("exp_r"), "up_n": rg["up"].get("n"),
           "flat_exp": rg["flat"].get("exp_r"), "down_exp": rg["down"].get("exp_r"), "down_n": rg["down"].get("n"),
           "regime_pass": bool(rg["pass"]), "wf_share": wf.get("share_positive"), "wf_folds": wf.get("n_folds"),
           "per_day": len(r) / FM.nd}
    res["beat_random"] = bool(row["xs_tr"] > 0 and row["xs_va"] > 0 and (row["xt_all"] or 0) >= 2)
    res["quality"] = bool(res["regime_pass"] and (res["wf_share"] or 0) >= 0.6 and res["beat_random"]
                          and (res["ex_best_day"] or -1) > 0)
    res["passes_bar"] = bool(res["quality"] and (row["t_all"] or 0) >= bar)
    return res, ix


if __name__ == "__main__":
    for fam in sys.argv[1:]:
        sc = pd.read_parquet(SCR / f"{fam}_scan.parquet")
        scr = screen(sc).copy()
        print(fam, "configs", len(sc), "screen", len(scr), flush=True)
        src = {"HS": ("hs", 125), "HL": ("hl", 125), "ORB": ("orb", 95), "IM": ("im", 95), "LIQ": ("liq", 95)}[fam]
        FM = Fam(load(*src), CUTS)
        extra = None
        if fam == "LIQ":
            c = FM.col
            with np.errstate(invalid="ignore"):
                extra = {"vroom>=0.5": c["close"] * (1 / (1 + c["vwapDistPct"] / 100) - 1) / c["atr_d"] >= 0.5}
        out = []
        for _, row in scr.iterrows():
            res, _ = full_gates(fam, FM, row.to_dict(), extra)
            out.append({**row.to_dict(), **res})
        g = pd.DataFrame(out)
        g.to_parquet(SCR / f"{fam}_gated.parquet", index=False)
        if len(g):
            print(fam, "quality", int(g.quality.sum()), "passes bar", int(g.passes_bar.sum()), "bar", g.t_bar.iloc[0])
