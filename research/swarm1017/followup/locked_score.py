"""Q9: score RST1, AR-ETF-late-dip-adx-long and AR-AM-gapdown-capitulation ONCE on the rule-19 locked block
(2024-11-01..2025-02-28), exactly as frozen (PLAN.md). Run once, on the lead's behalf:
    MCF_HIST_ALLOW_LOCKED=1 python research/swarm1017/followup/locked_score.py
Educational only - not financial advice."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from mcf.research.arena import data as D  # noqa: E402
from research.history2y import lib  # noqa: E402

assert os.environ.get("MCF_HIST_ALLOW_LOCKED") == "1"
OUT = HERE / "locked_look1.json"
assert not OUT.exists(), "look 1 already spent - never re-score"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S17 = ROOT / "research" / "swarm1017"
RST1 = load(S17 / "rework-st/modules/RST1-l3fromopen-spyup-pm-t05s1-short.py", "rst1")
ETF = load(S17 / "arena-index-etf/near_miss/AR-ETF-late-dip-adx-long.py", "etfadx")
AM = load(S17 / "final/modules/AR-AM-gapdown-capitulation.py", "amgap")
RST1_META = json.load(open(S17 / "rework-st/modules/index.json"))["RST1-l3fromopen-spyup-pm-t05s1-short"]

rows = {"RST1": [], "RST1_x3": [], "ETF-ADX": [], "AM-GAPDN": []}
for mo in lib.LOCKED_MONTHS:
    d = lib.load_month(mo)
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    d = d.merge(spy, on=["date", "tod"], how="left")
    d = d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = d.tod.to_numpy()
    out = D.outcomes(d)                     # arena production R with x3 extended tier
    key = pd.MultiIndex.from_arrays([pd.Index(d["date"]), tod])
    uni = (d.adv20.to_numpy(float) >= 95e6) & (tod >= 950) & (tod <= 1500)
    etfu = uni & d.symbol.astype(str).isin(ETF.SYMBOLS).to_numpy()

    def ctrl(v, sel):
        return pd.Series(np.where(sel, v, np.nan), index=key).groupby(level=[0, 1]).mean().reindex(key).to_numpy()

    # ---- RST1: rework-st/verify_modules.py procedure (frozen scorer) + x3-tier cost variant
    g, s = RST1.GEOM, RST1.SIDE
    ok = (d.adv20.to_numpy(float) >= RST1_META["min_adv"]) & (d.atr_d.to_numpy(float) > 0) & np.isfinite(d[f"r_{s}_{g}"].to_numpy(float))
    ok &= (tod >= RST1_META["window"][0]) & (tod <= RST1_META["window"][1])
    ok &= d.gap.to_numpy(float) <= float(RST1_META["prefilter"].split(":")[1])
    m = np.asarray(RST1.mask(d), bool) & ok
    idx = gates.first_per_symbol_day(d.symbol.to_numpy(), d.date.to_numpy(), m)
    r = gates.prod_r(d[f"r_{s}_{g}"].to_numpy(float)[idx], d[f"win_{s}_{g}"].to_numpy(float)[idx], d.close.to_numpy(float)[idx],
                     d.atr_d.to_numpy(float)[idx], g, tod=tod[idx].astype(float))
    allok = (d.atr_d.to_numpy(float) > 0) & np.isfinite(d[f"r_{s}_{g}"].to_numpy(float))
    prod_all = gates.prod_r(d[f"r_{s}_{g}"].to_numpy(float), d[f"win_{s}_{g}"].to_numpy(float), d.close.to_numpy(float),
                            d.atr_d.to_numpy(float), g, tod=tod.astype(float))
    c0 = ctrl(prod_all, allok)[idx]          # b0 control: all names (min_adv 0), same minute
    base = dict(date=d.date.to_numpy()[idx], symbol=d.symbol.to_numpy()[idx], tod=tod[idx])
    rows["RST1"].append(pd.DataFrame({**base, "r": r, "ctrl": c0}))
    rx = out[f"{s}_{g}"][idx]
    rows["RST1_x3"].append(pd.DataFrame({**base, "r": rx, "ctrl": ctrl(out[f"{s}_{g}"], allok)[idx]}))

    # ---- arena modules: combine.trades semantics on build_month rows
    for nm, M in (("ETF-ADX", ETF), ("AM-GAPDN", AM)):
        o = f"{M.SIDE}_{M.GEOM}"
        v = out[o]
        c = ctrl(v, uni)
        mm = np.asarray(M.mask(d), bool) & uni & np.isfinite(v) & np.isfinite(c)
        idx = gates.first_per_symbol_day(d.symbol.to_numpy(), d.date.to_numpy(), mm)
        t = pd.DataFrame({"date": d.date.to_numpy()[idx], "symbol": d.symbol.to_numpy()[idx], "tod": tod[idx],
                          "r": v[idx], "ctrl": c[idx]})
        if nm == "ETF-ADX":
            t["ctrl_etf"] = ctrl(v, etfu)[idx]
        rows[nm].append(t)
    print(mo, {k: sum(len(x) for x in v) for k, v in rows.items()}, flush=True)
    del d, out

reg = lib.regimes(include_locked=True)
res = {"scored_on": "2024-11-01..2025-02-28 (rule-19 locked block), look 1, 2026-10-17", "versions": {}}
for nm, v in rows.items():
    t = pd.concat(v, ignore_index=True)
    t["date"] = pd.to_datetime(t["date"]).dt.date
    t.to_csv(HERE / f"locked_trades_{nm}.csv", index=False)
    s = gates.summary(t[["date", "r"]])
    x = gates.summary(t[["date"]].assign(r=t["r"] - t["ctrl"]))
    rs = gates.regime_split(t[["date", "r"]], reg)
    g = t.groupby("date")["r"].sum().sort_values(ascending=False)
    top3 = float(g.head(3).sum() / g.sum()) if g.sum() != 0 else None
    mo = t.groupby(pd.to_datetime(t.date).dt.strftime("%Y-%m"))["r"].agg(["size", "mean"]).round(4)
    e = {"overall": s, "excess_vs_random": {"exp": x.get("exp_r"), "t": x.get("t")}, "regime": rs, "top3_day_share": top3,
         "per_month": {k: {"n": int(a), "exp": float(b)} for k, (a, b) in mo.iterrows()}}
    if "ctrl_etf" in t:
        xe = gates.summary(t[["date"]].assign(r=t["r"] - t["ctrl_etf"]))
        e["excess_vs_etf_random"] = {"exp": xe.get("exp_r"), "t": xe.get("t")}
    gl = {"n>=30": s.get("n", 0) >= 30, "exp>0": (s.get("exp_r") or -1) > 0, "t>=1.0": (s.get("t") or 0) >= 1.0,
          "regime_up_down": bool(rs.get("pass")), "beats_random": (x.get("exp_r") or -1) > 0}
    e["gates"] = gl
    e["pass_look1"] = all(gl.values())
    res["versions"][nm] = e
    print(nm, s, e["excess_vs_random"], {k: (rs[k].get("n"), rs[k].get("exp_r")) for k in ("up", "flat", "down")}, gl, flush=True)
res["versions"]["RST1"]["pass_look1_both_costs"] = res["versions"]["RST1"]["pass_look1"] and res["versions"]["RST1_x3"]["pass_look1"]
OUT.write_text(json.dumps(res, indent=1, default=str))
