"""nightly1015 backtest of two hypotheses queued tonight (open two-year history, production + time-of-day costs).
Educational only - not financial advice.

PRE-DECLARATION (written 2026-10-15 before any configuration below was scored; results go in NOTES.md and may not
change this block):

Data: research/history2y frames via lib.load_month (open months only; the rule-19 locked block 2024-11-01..2025-02-28
is refused by the loader and MCF_HIST_ALLOW_LOCKED is never set), plus the 09:35-09:45 head / 15:05-15:55 tail rows
exactly as research/bdi/refire1014/scan.py builds them (its month_hits code is reused, setups filtered).
Costs: production R and time-of-day entry costs (gates.prod_r with tod; structural exits as scan.structural_r).
Live semantics: one signal per setup per symbol-day = the FIRST qualifying decision bar inside the window.
Setups (5, the lab-type short setups that lost most on 2026-10-15): NS2-sma50break-overbought-short (Primary),
NS2-sma50break-overbought-short-FD, RW6-ns2-up3-short-FD, RW2-exhaustion-noon-adv150-short-FD (Testing 1),
CWT09-gapdn-bounce-g5-lowerhalf-short (Testing 2). heat_fade_short(-FD) is type "heat", not in the lab frames: not tested.

H1 nightly-1015-short-breadth-cluster-skip: drop every first-signal of a setup that falls on a decision bar where
   >= 5 symbols take their first signal of that same setup (a same-setup breadth cluster = a market move, not a
   stock-specific one). Dropped signals are not replaced. 1 rule x 5 setups = 5 configurations.
H2 nightly-1015-gapdn-reclaim-short-veto: a decision bar does not qualify when SPY gapped down <= -0.30% at the open
   (frame column gap) AND SPY fromOpen > 0 at that bar (index reclaimed its open). The first qualifying bar that
   passes the gate fires. 1 rule x 5 setups = 5 configurations.
N = 10 configurations in this study.

Pass bar per configuration (all must hold): variant exp_r after costs > 0; variant minus baseline exp_r > 0 in the
train half (open months <= 2025-12) and in the later half (2026-01..), and in up and down sessions separately
(lib.regimes); day-clustered t of the variant (gates.summary) >= max(1.5, sqrt(2 ln 10)) = 2.15.
A pass only moves the idea to "finalist"-style evidence for the lead; no holdout is scored here, nothing goes live.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
NAMES = {"NS2-sma50break-overbought-short", "NS2-sma50break-overbought-short-FD", "RW6-ns2-up3-short-FD",
         "RW2-exhaustion-noon-adv150-short-FD", "CWT09-gapdn-bounce-g5-lowerhalf-short"}
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/n1015")


def month_job(args):
    month, sts = args
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    spy = f[f["symbol"] == "SPY"][["date", "tod", "gap", "fromOpen"]].rename(columns={"gap": "spy_gap", "fromOpen": "spy_fo"})
    rows, _ = scan.month_hits(month, sts)
    return pd.concat([x.merge(spy, on=["date", "tod"], how="left") for x in rows], ignore_index=True)


def first(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["r"].notna()].sort_values(["key", "symbol", "date", "tod"])
    return d.groupby(["key", "symbol", "date"], sort=False).head(1)


def score(t: pd.DataFrame, reg: pd.DataFrame) -> dict:
    t = t.copy()
    t["date"] = pd.to_datetime(t["date"]).dt.date
    s = gates.summary(t)
    late = pd.to_datetime(t["date"]) >= "2026-01-01"
    rg = t["date"].map(reg)
    return {"n": s["n"], "exp": s["exp_r"], "t": s["t"], "train_exp": round(float(t.r[~late].mean()), 4),
            "late_exp": round(float(t.r[late].mean()), 4), "up": round(float(t.r[rg == "up"].mean()), 4),
            "down": round(float(t.r[rg == "down"].mean()), 4)}


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    sts = [s for s in scan.account_setups() if s["name"] in NAMES]
    names = {s["key"]: s["name"] for s in sts}
    print(len(sts), "setups:", list(names.values()), flush=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(3) as p:
        hits = pd.concat(p.map(month_job, [(mo, sts) for mo in months]), ignore_index=True)
    hits["name"] = hits["key"].map(names)
    hits.to_parquet(SCR / "bt_hits.parquet")
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    reg = reg["regime"] if isinstance(reg, pd.DataFrame) else reg
    rows = []
    for k, g in hits.groupby("key"):
        base = first(g)
        csize = base.groupby(["date", "tod"])["symbol"].transform("size")
        veto = (g["spy_gap"] <= -0.30) & (g["spy_fo"] > 0)
        var = {"H1_cluster5_skip": base[csize < 5], "H2_gapdn_reclaim_veto": first(g[~veto.fillna(False)])}
        b = score(base, reg)
        rows.append({"setup": names[k], "variant": "baseline", **b,
                     "share_cluster5": round(float((csize >= 5).mean()), 3),
                     "share_veto": round(float(((base["spy_gap"] <= -0.30) & (base["spy_fo"] > 0)).mean()), 3)})
        for vn, v in var.items():
            s = score(v, reg)
            rows.append({"setup": names[k], "variant": vn, **s, "d_exp": round(s["exp"] - b["exp"], 4),
                         "d_train": round(s["train_exp"] - b["train_exp"], 4), "d_late": round(s["late_exp"] - b["late_exp"], 4),
                         "d_up": round(s["up"] - b["up"], 4), "d_down": round(s["down"] - b["down"], 4)})
        # the trades each rule removes (reported, not a configuration)
        rem1 = base[csize >= 5]
        rows.append({"setup": names[k], "variant": "removed_by_H1", **(score(rem1, reg) if len(rem1) else {})})
    res = pd.DataFrame(rows)
    treq = gates.t_required(10)
    v = res[res.variant.str.startswith("H")].copy()
    v["pass"] = (v.exp > 0) & (v.d_train > 0) & (v.d_late > 0) & (v.d_up > 0) & (v.d_down > 0) & (v.t >= treq)
    res = res.merge(v[["setup", "variant", "pass"]], on=["setup", "variant"], how="left")
    res.to_csv(OUT / "bt1015_results.csv", index=False)
    pd.set_option("display.width", 250)
    print("t required", treq)
    print(res.to_string())


if __name__ == "__main__":
    main()
