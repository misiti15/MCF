"""Score every package A configuration with the pre-declared gates (NOTES.md section 1).

    python research/bdi/cwt/test_a/score.py
Writes data/results.csv (all 566 configurations) and results.csv (same, committed; small). Educational only - not
financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from mcf.research.gates import regime_split, summary, t_required, walk_forward  # noqa: E402
from research.history2y.lib import LOCKED_MONTHS, regimes  # noqa: E402
from a5 import A5_CONFIGS  # noqa: E402

DATA = HERE / "data"
PLAN_N = {"A1": 68, "A2": 96, "A3": 72, "A4": 32, "A5": 18, "A6": 64, "A7": 64, "A8": 80, "A9": 72}
# overlapping backlog lineages named in TESTPLAN (configs_tried in research/backlog.jsonl; A9's heat_fade_long count
# is backed out of its RESCORE t bar 4.441 -> exp(4.441^2/2) ~ 19,200; A4's ORB lineages ~700 per the plan)
OVERLAP_N = {"A1": 128, "A2": 274247 + 128, "A3": 128 + 128 + 120375, "A4": 700, "A5": 0, "A6": 128,
             "A7": 82068 + 324, "A8": 128 + 36, "A9": 19200}
OVERLAP_SRC = {"A1": "bdi-rdt-r06-red-green 128", "A2": "P1/L2 gap shorts 274,247 + r05 128 (+heat_fade_short, uncounted)",
               "A3": "r17 128 + r07 128 + ST5 (bdi-st-st5) 120,375", "A4": "ORB lineages ~700 (plan)", "A5": "none (new)",
               "A6": "r05 128", "A7": "RW1/RW3/RW7 82,068 + er-react 324", "A8": "r04 128 + er-react-gap 36",
               "A9": "heat_fade_long ~19,200 (from its RESCORE bar)"}
PARAMS = {"A1": ["univ", "trig", "exit", "win"], "A2": ["gap", "hset", "trig", "exit", "win"],
          "A3": ["q", "cat", "side", "exit", "win"], "A4": ["var", "k", "rvol", "side", "exit", "win"],
          "A5": ["k", "H", "hedge"], "A6": ["g", "ref", "side", "exit", "win"], "A7": ["gap", "E", "trig", "exit", "win"],
          "A8": ["gap", "E", "c", "exit", "win"], "A9": ["gap", "E", "k", "trig", "exit", "win"]}
EXIT_IX = {"t1s1": 0, "t05s1": 1, "t1s05": 2}


def busiest(tr):
    return float(tr.groupby("date").size().max() / len(tr)) if len(tr) else np.nan


def day_t(x: pd.DataFrame, col: str):
    if len(x) < 2:
        return np.nan
    mu = x[col].mean()
    g = x.groupby("date")[col].agg(["sum", "size"])
    se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(x)
    return float(mu / se) if se > 0 else np.nan


def score_one(tr: pd.DataFrame, reg, fam: str) -> dict:
    s = summary(tr)
    out = {"n": s.get("n", 0)}
    if not s.get("n"):
        return out
    rs = regime_split(tr, reg)
    wf = walk_forward(tr, exclude_months=LOCKED_MONTHS)
    out.update({"days": s["days"], "win": s["win_rate"], "exp": s["exp_r"], "se": s["se"], "t": s["t"],
                "ex_best_day": s["ex_best_day"], "busiest": round(busiest(tr), 4),
                "up_exp": rs["up"].get("exp_r"), "up_n": rs["up"].get("n", 0), "flat_exp": rs["flat"].get("exp_r"),
                "down_exp": rs["down"].get("exp_r"), "down_n": rs["down"].get("n", 0), "regime_pass": rs["pass"],
                "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"]})
    if "ctl" in tr:
        c = tr.dropna(subset=["ctl"])
        out["ctl_exp"] = round(float(c["ctl"].mean()), 4) if len(c) else None
        c = c.assign(diff=c["r"] - c["ctl"])
        out["diff_exp"] = round(float(c["diff"].mean()), 4) if len(c) else None
        out["diff_t"] = round(day_t(c, "diff"), 2) if len(c) > 1 else None
    tod = tr["tod"].to_numpy()
    out["share_pre950"] = round(float((tod < 950).mean()), 3)
    out["share_pre1030"] = round(float((tod < 1030).mean()), 3)
    q = pd.PeriodIndex(pd.to_datetime(tr["date"]), freq="Q").astype(str)
    out["quarters"] = "; ".join(f"{k} {v:+.3f} ({n})" for k, (v, n) in tr.groupby(q)["r"].agg(["mean", "size"]).iterrows())
    return out


def main():
    cfg = pd.read_csv(DATA / "configs.csv")
    tr = pd.read_parquet(DATA / "trades.parquet")
    tr["date"] = pd.to_datetime(tr["date"]).dt.date
    tr["tod"] = ((570 + tr["m0"].astype(int)) // 60) * 100 + (570 + tr["m0"].astype(int)) % 60
    # same-time controls
    z = np.load(DATA / "controls.npz", allow_pickle=True)
    cs, cn, cd = z["s"], z["n"], list(z["dates"])
    with np.errstate(invalid="ignore", divide="ignore"):
        cm = cs / cn
    dpos = {pd.Timestamp(str(d)).date(): i for i, d in enumerate(cd)}
    di = tr["date"].map(dpos).to_numpy()
    kk = np.clip(np.round((tr["m0"].to_numpy() - 5) / 5).astype(int), 0, 65)
    si = np.where(tr["side"].to_numpy() > 0, 0, 1)
    xi = tr["exit"].map(EXIT_IX).fillna(3).astype(int).to_numpy()
    ok = ~pd.isna(di)
    ctl = np.full(len(tr), np.nan)
    ctl[ok] = cm[di[ok].astype(int), kk[ok], si[ok], xi[ok]]
    tr["ctl"] = ctl
    reg = regimes()
    rows = []
    for cid, g in tr.groupby("cid"):
        c = cfg.loc[cid].to_dict()
        r = score_one(g[["date", "symbol", "tod", "r", "ctl", "ext", "blackout"]].reset_index(drop=True), reg, c["family"])
        r.update({k: c.get(k) for k in ["cid", "family"] + PARAMS[c["family"]] if k in c})
        r["ext_share"] = round(float((g["ext"] > 1).mean()), 3)
        r["px_lt5_share"] = round(float((g["price"] < 5).mean()), 3)
        r["blackout_share"] = round(float(g["blackout"].mean()), 3)
        r["side_n"] = f"{int((g['side'] > 0).sum())}L/{int((g['side'] < 0).sum())}S"
        rows.append(r)
    seen = set(tr["cid"].unique())
    for _, c in cfg.iterrows():
        if c["cid"] not in seen:
            rows.append({"cid": c["cid"], "family": c["family"], "n": 0, **{k: c.get(k) for k in PARAMS[c["family"]] if k in c}})
    # A5
    a5 = pd.read_parquet(DATA / "a5_trades.parquet")
    a5["date"] = pd.to_datetime(a5["date"]).dt.date
    a5ctl = pd.read_parquet(DATA / "a5_ctl.parquet")
    a5ctl["date"] = pd.to_datetime(a5ctl["date"]).dt.date
    cmap = {(d, h): v for d, h, v in zip(a5ctl["date"], a5ctl["H"], a5ctl["gross_long"])}
    for ci, (k, H, hedge) in enumerate(A5_CONFIGS):
        g = a5[a5["ci"] == ci].copy()
        g["tod"] = 930
        cost = g["gross"] - g["r"]
        g["ctl"] = np.array([g_side * cmap.get((d, H), np.nan) for d, g_side in zip(g["date"], g["side"])]) - cost.to_numpy()
        r = score_one(g[["date", "symbol", "tod", "r", "ctl"]].reset_index(drop=True), reg, "A5")
        r.update({"cid": 1000 + ci, "family": "A5", "k": k, "H": H, "hedge": hedge, "exit": f"{H}min", "win": "open",
                  "side_n": f"{int((g['side'] > 0).sum())}L/{int((g['side'] < 0).sum())}S"})
        rows.append(r)
    res = pd.DataFrame(rows)
    # gates
    res["t_bar_plan"] = res["family"].map(lambda f: t_required(PLAN_N[f]))
    res["t_bar_lineage"] = res["family"].map(lambda f: t_required(PLAN_N[f] + OVERLAP_N[f]))
    res["t_bar_round"] = t_required(1051)

    def fails(r):
        f = []
        if not r.get("n") or r["n"] < 150:
            f.append(f"n {r.get('n', 0)} < 150")
        if not r.get("n"):
            return f
        if not (r["exp"] > 0):
            f.append("exp<=0")
        if not (r["t"] is not None and r["t"] >= 2.0):
            f.append(f"t {r['t']} < 2.0")
        if not r["regime_pass"]:
            f.append("regime")
        if r["wf_share"] is None or not (r["wf_share"] >= 0.6):
            f.append(f"wf {r['wf_share']}")
        if not (r["ex_best_day"] > 0):
            f.append("ex-best-day")
        if not (r["busiest"] <= 0.10):
            f.append(f"busiest {r['busiest']}")
        if not (r.get("plateau") is not None and r["plateau"] > 0):
            f.append(f"plateau {r.get('plateau')}")
        return f

    # plateau: same family, exactly one grid parameter different (side excluded), mean exp of neighbours
    plats = []
    for _, r in res.iterrows():
        ps = [p for p in PARAMS[r["family"]] if p != "side"]
        fam = res[(res["family"] == r["family"]) & (res["cid"] != r["cid"]) & (res["n"] > 0)]
        if "side" in PARAMS[r["family"]]:
            fam = fam[fam["side"] == r["side"]]
        diff = sum((fam[p].astype(str) != str(r[p])).astype(int) for p in ps if p in fam)
        nb = fam[diff == 1]
        plats.append(round(float(nb["exp"].mean()), 4) if len(nb) else None)
    res["plateau"] = plats
    res["fails"] = res.apply(lambda r: "; ".join(fails(r)), axis=1)
    res["probation_pass"] = res["fails"] == ""
    res["t_pass_plan"] = res["t"].fillna(-9) >= res["t_bar_plan"]
    res["t_pass_lineage"] = res["t"].fillna(-9) >= res["t_bar_lineage"]
    res = res.sort_values(["family", "cid"]).reset_index(drop=True)
    res.to_csv(DATA / "results.csv", index=False)
    res.drop(columns=["quarters"]).to_csv(HERE / "results.csv", index=False)
    print(res.groupby("family").agg(configs=("cid", "size"), with_trades=("n", lambda x: int((x > 0).sum())),
                                    pos=("exp", lambda x: int((x > 0).sum())), t2=("t", lambda x: int((x >= 2).sum())),
                                    probation=("probation_pass", "sum"), best_t=("t", "max")))
    print("total configurations:", len(res))


if __name__ == "__main__":
    main()
