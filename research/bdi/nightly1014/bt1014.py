"""nightly1014 backtest of two hypotheses queued tonight (open two-year history, production + time-of-day costs).
Educational only - not financial advice.

PRE-DECLARATION (written 2026-10-14 before any configuration below was scored; results go in NOTES.md and may not
change this block):

Data: research/history2y frames via lib.load_month (open months only; the rule-19 locked block 2024-11-01..2025-02-28
is refused by the loader and MCF_HIST_ALLOW_LOCKED is never set), plus the 09:35-09:45 head / 15:05-15:55 tail rows
exactly as research/bdi/refire1014/scan.py builds them (its month_hits code is reused, setups filtered).
Costs: production R and time-of-day entry costs (gates.prod_r with tod; structural exits as scan.structural_r).
Live semantics: one signal per setup per symbol-day = the FIRST qualifying decision bar inside the window.

H1 nightly-1014-cwt14-skip-first-bar (Testing 2, 10 CWT14 setups):
   rule: the setup may not fire on the 09:50 decision bar (first live bar); its first qualifying bar at >= 09:55
   fires instead. 1 rule x 10 setups = 10 configurations, plus the pooled CWT14 book (reported, not a config).
H2 nightly-1014-liq-orl-index-confirm (Testing 1, LIQ-orl-sweep-open15-s25-long):
   rule a: fire only when SPY fromOpen > 0 at the decision bar; rule b: only when SPY is above its session VWAP.
   The first qualifying bar that passes the gate fires. 2 configurations.
N = 12 configurations in this study (lineage counts: H1 parent cwt-b-b3; H2 parent LIQ lineage reddit1012liq).

Pass bar per configuration (all must hold): variant exp_r after costs > 0; variant minus baseline exp_r > 0 in the
train half (open months <= 2025-12) and in the later half (2026-01..), and in up and down sessions separately
(gates.session_regimes); day-clustered t of the variant (gates.summary) >= max(1.5, sqrt(2 ln N)) = 2.23.
A pass only moves the idea to "finalist"-style evidence for the lead; no holdout is scored here, nothing goes live.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
WANT = lambda n: n.startswith("CWT14-") or n == "LIQ-orl-sweep-open15-s25-long"  # noqa: E731


def month_job(args):
    month, sts = args
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    spy = f[f["symbol"] == "SPY"][["date", "tod", "fromOpen", "vwapDistPct"]].rename(
        columns={"fromOpen": "spy_fo", "vwapDistPct": "spy_vw"})
    rows, _ = scan.month_hits(month, sts)
    out = []
    for x in rows:
        x = x.merge(spy, on=["date", "tod"], how="left")
        out.append(x)
    return pd.concat(out, ignore_index=True)


def first(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["r"].notna()].sort_values(["key", "symbol", "date", "tod"])
    return d.groupby(["key", "symbol", "date"], sort=False).head(1)


def score(t: pd.DataFrame, reg: pd.DataFrame) -> dict:
    t = t.copy()
    t["date"] = pd.to_datetime(t["date"]).dt.date
    s = gates.summary(t)
    rs = gates.regime_split(t, reg)
    late = pd.to_datetime(t["date"]) >= "2026-01-01"
    return {"n": s["n"], "exp": s["exp_r"], "t": s["t"], "train_exp": round(float(t.r[~late].mean()), 4),
            "late_exp": round(float(t.r[late].mean()), 4), "up": rs.get("up", {}).get("exp_r"), "down": rs.get("down", {}).get("exp_r")}


def main():
    sts = [s for s in scan.account_setups() if WANT(s["name"])]
    for s in sts:
        m = scan.load_mod(s)
        s["side"], s["geom"], s["family"] = m.SIDE, m.GEOM, scan.family(s)
    names = {s["key"]: s["name"] for s in sts}
    print(len(sts), "setups:", list(names.values()), flush=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(3) as p:
        hits = pd.concat(p.map(month_job, [(mo, sts) for mo in months]), ignore_index=True)
    hits["name"] = hits["key"].map(names)
    hits.to_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/n1014/bt_hits.parquet")
    # session regimes from the universe median open-to-close (as gates.session_regimes expects a daily frame)
    reg = lib.regimes()                       # open sessions only (include_locked False)
    reg.index = pd.to_datetime(reg.index).date
    rows = []
    for k, g in hits.groupby("key"):
        n = names[k]
        base = first(g)
        if n.startswith("CWT14-"):
            var = {"skip0950": first(g[g["tod"] >= 955])}
        else:
            var = {"spy_fo_pos": first(g[g["spy_fo"] > 0]), "spy_above_vwap": first(g[g["spy_vw"] > 0])}
        b = score(base, reg)
        rows.append({"setup": n, "variant": "baseline", **b})
        for vn, v in var.items():
            s = score(v, reg)
            rows.append({"setup": n, "variant": vn, **s, "d_exp": round(s["exp"] - b["exp"], 4),
                         "d_train": round(s["train_exp"] - b["train_exp"], 4), "d_late": round(s["late_exp"] - b["late_exp"], 4),
                         "d_up": None if s["up"] is None or b["up"] is None else round(s["up"] - b["up"], 4),
                         "d_down": None if s["down"] is None or b["down"] is None else round(s["down"] - b["down"], 4)})
    # pooled CWT14 book
    c = hits[hits["name"].str.startswith("CWT14-")]
    pb, pv = first(c), first(c[c["tod"] >= 955])
    rows.append({"setup": "CWT14 pooled (10)", "variant": "baseline", **score(pb, reg)})
    rows.append({"setup": "CWT14 pooled (10)", "variant": "skip0950", **score(pv, reg)})
    res = pd.DataFrame(rows)
    treq = gates.t_required(12)
    v = res[res.variant != "baseline"].copy()
    v["pass"] = (v.exp > 0) & (v.d_train > 0) & (v.d_late > 0) & (v.d_up.fillna(-1) > 0) & (v.d_down.fillna(-1) > 0) & (v.t >= treq)
    res = res.merge(v[["setup", "variant", "pass"]], on=["setup", "variant"], how="left")
    res.to_csv(OUT / "bt1014_results.csv", index=False)
    pd.set_option("display.width", 250)
    print("t required", treq)
    print(res.to_string())
    # share of first-bar (09:50) trades in the baseline
    print("baseline share at 09:50:", (first(c)["tod"] == 950).mean().round(3),
          "exp at 09:50:", round(float(first(c).query("tod == 950").r.mean()), 4), "after:", round(float(first(c).query("tod > 950").r.mean()), 4))


if __name__ == "__main__":
    main()
