"""CWT package B report: gates per configuration (failures first), plateau, regime split, walk-forward, ex-best-day,
busiest-session share, SPY-hedged control, random baseline, FOMC-week split, time of day.

    python research/bdi/cwt/test_b/report.py          # after score.py -> results.csv, RESULTS.md
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from score import GUEST, PARAMS, cname, grid  # noqa: E402

DATA = HERE / "data"
FAM_N = {"B1": 32, "B2": 64, "B3": 96, "B4": 32, "B5": 64, "B6": 32, "B7": 48}
# overlapping backlog lineages named in TESTPLAN section 3 (cumulative configs_tried in research/backlog.jsonl)
LINEAGE = {"B1": {"bdi-tg-bdi-rw-ns3-adv150 (NS3/RW4)": 82102, "x_vwaploss_run": 274247},
           "B2": {"bdi-rdt-r03-vwap-fade": 128},
           "B3": {"bdi-rdt-r15-sweep": 128, "bdi-st-st1-ordn-long-pm-t05s1 (ST1)": 120375, "bdi-reddit-orb-failed-break": 0},
           "B4": {"bdi-rdt-r08-bull-flag": 128},
           "B5": {"bdi-tg-heat-fade-long": 19648, "bdi-tg-ns5-sma50-flush-oversold-long": 8494},
           "B6": {},
           "B7": {"bdi-rdt-r09-ema20-pullback": 128, "bdi-rdt-r02-vwap-reclaim": 128}}
NEIGH = {"B1": ("a",), "B2": ("z", "U"), "B3": ("p", "V"), "B4": ("k",), "B5": ("m", "v", "D"), "B6": ("u", "wd", "vc"),
         "B7": ("th", "f")}
FOMC = ["2024-11-07", "2024-12-18", "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17",
        "2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16"]
PROB = dict(n=150, t=2.0, wf=0.6, maxday=0.10)


def fomc_week(dates):
    wk = set()
    for s in FOMC:
        d = date.fromisoformat(s)
        mon = d - timedelta(days=d.weekday())
        wk |= {mon + timedelta(days=i) for i in range(5)}
    return np.array([d in wk for d in dates])


def tstat(r, day):
    if len(r) < 2:
        return 0.0
    mu = r.mean()
    g = pd.DataFrame({"d": day, "r": r}).groupby("d")["r"].agg(["sum", "size"])
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    return float(mu / se) if se > 0 else 0.0


def evaluate(c, T, dates, reg, base, fw):
    day, r, rh, tod = T["day"], T["r"], T["rh"], T["tod"]
    n = len(r)
    nfam = FAM_N[c["fam"]] + sum(LINEAGE[c["fam"]].values())
    row = {"id": c["id"], "name": cname(c), "fam": c["fam"], "side": c["side"], "exit": c["exit"], "win": c["win"],
           "n": n, "per_day": round(n / len(dates), 3), "N_family": FAM_N[c["fam"]], "N_lineage": nfam,
           "t_req_family": gates.t_required(FAM_N[c["fam"]]), "t_req_lineage": gates.t_required(nfam)}
    if n < 2:
        return row | {"verdict": "retire", "fails": "n<2", "probation": False}
    dd = np.array(dates)[day]
    tr = pd.DataFrame({"date": dd, "r": r})
    sm = gates.summary(tr)
    rg = gates.regime_split(tr, reg)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    v, fails = gates.verdict(sm, rg, wf, nfam)
    S = tr.groupby("date")["r"].agg(["sum", "size"])
    maxday = float(S["size"].max() / n)
    ok = np.isfinite(rh)
    lo, hi = (950, 1500) if c["win"] == "full" and c["fam"] != "B6" else GUEST[c["fam"]]
    wn = "full" if (lo, hi) == (950, 1500) else f"g{c['fam']}"
    bk = f"{wn}|{c['side']}|{'hold' if c['exit'] == 'S' else c['exit']}"
    fwm = fw[day]
    row |= {"win_rate": sm["win_rate"], "exp": sm["exp_r"], "t": sm["t"], "ex_best_day": sm["ex_best_day"],
            "green_days": sm["green_days"], "maxday_share": round(maxday, 4),
            "up_exp": rg["up"].get("exp_r"), "up_n": rg["up"].get("n"), "flat_exp": rg["flat"].get("exp_r"),
            "down_exp": rg["down"].get("exp_r"), "down_n": rg["down"].get("n"), "regime_pass": rg["pass"],
            "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"],
            "hedged_exp": round(float(rh[ok].mean()), 4) if ok.any() else None,
            "hedged_t": round(tstat(rh[ok], day[ok]), 2) if ok.sum() > 1 else None,
            "base_exp": round(base[bk]["exp"], 4) if bk in base else None,
            "fomc_wk_exp": round(float(r[fwm].mean()), 4) if fwm.any() else None, "fomc_wk_n": int(fwm.sum()),
            "tod_med": int(np.median(tod)), "share_before_1030": round(float((tod < 1030).mean()), 3),
            "share_after_1330": round(float((tod > 1330).mean()), 3),
            "verdict": v, "fails": "; ".join(fails)}
    return row


def main():
    G = grid()
    z = np.load(DATA / "trades.npz", allow_pickle=True)
    meta = json.load(open(DATA / "baseline.json"))
    dates = [date.fromisoformat(d) for d in meta["dates"]]
    reg = lib.regimes()
    fw = fomc_week(dates)
    rows = []
    for c in G:
        T = {k: z[f"{c['id']}|{k}"] for k in ("day", "r", "rh", "tod")} if f"{c['id']}|r" in z.files else \
            {k: np.zeros(0) for k in ("day", "r", "rh", "tod")}
        T["day"] = T["day"].astype(int)
        rows.append(evaluate(c, T, dates, reg, meta["baseline"], fw))
    df = pd.DataFrame(rows)
    # plateau: same family / side / exit / window / other levels, exactly one neighbour dimension one step away
    gd = pd.DataFrame(G)
    pl = []
    for c in G:
        nb = []
        for k in NEIGH[c["fam"]]:
            m = (gd.fam == c["fam"]) & (gd.side == c["side"]) & (gd.exit == c["exit"]) & (gd.win == c["win"])
            for o in PARAMS[c["fam"]]:
                if o != k:
                    m &= (gd[o].astype(str) == str(c.get(o)))
            m &= gd[k].astype(str) != str(c.get(k))
            nb += gd.loc[m, "id"].tolist()
        e = df.set_index("id").loc[nb, "exp"].astype(float) if nb else pd.Series(dtype=float)
        pl.append(round(float(e.mean()), 4) if len(e) and e.notna().any() else None)
    df["plateau_mean"] = pl
    df["probation"] = ((df.n >= PROB["n"]) & (df.exp > 0) & (df.t.fillna(0) >= PROB["t"]) & df.regime_pass.fillna(False)
                       & (df.wf_share.fillna(0) >= PROB["wf"]) & (df.plateau_mean.fillna(-1) > 0)
                       & (df.ex_best_day.fillna(-1) > 0) & (df.maxday_share.fillna(1) <= PROB["maxday"]))
    df["lineage_bar"] = (df.t.fillna(0) >= df.t_req_lineage) & (df.verdict == "keep")
    df["round_bar_3.73"] = df.t.fillna(0) >= 3.73
    df.to_csv(HERE / "results.csv", index=False)
    print(df.groupby("fam").agg(n_cfg=("id", "size"), pos=("exp", lambda x: int((x > 0).sum())),
                                best_t=("t", "max"), probation=("probation", "sum"), keep=("verdict", lambda x: int((x == "keep").sum()))))
    print("parity", meta["parity_mean"], meta["parity_min"])
    cols = ["name", "n", "exp", "t", "up_exp", "down_exp", "wf_share", "plateau_mean", "ex_best_day", "maxday_share",
            "hedged_exp", "hedged_t", "base_exp", "verdict"]
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_rows", 400):
        print(df.sort_values("t", ascending=False)[cols].head(40).to_string(index=False))


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


FAM_TITLE = {"B1": "CWT04 Backside lower-high short", "B2": "CWT13 Stretched-from-VWAP fade (ATR-gated)",
             "B3": "CWT14 Failed breakout / stop-run reversal", "B4": "CWT12 Intraday flag / coil breakout",
             "B5": "CWT05 Panic flush V-reversal long", "B6": "CWT46 Afternoon breakout in a strong mover",
             "B7": "CWT11 VWAP trend pullback (untested variants)"}


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-"
    return f"{x:+.{nd}f}" if isinstance(x, float) else str(x)


def write_md():
    d = pd.read_csv(HERE / "results.csv")
    meta = json.load(open(DATA / "baseline.json"))
    L = ["# CWT package B - results (all 368 configurations, failures first)", "",
         "*Educational only - not financial advice. Backtest on the open two-year history (426 sessions, locked block "
         "2024-11..2025-02 never loaded), production + time-of-day costs, x3 extended tier. Not paper, not live.*", "",
         f"Lab-geometry re-simulation vs the frames' r_* columns: {meta['parity_mean']:.5f} of sampled rows agree (min month "
         f"{meta['parity_min']:.5f}); head/tail rows vs frames at shared bars: close/high/VWAP 100% within 0.1%.", "",
         "## Per family", "",
         "| family | configs | exp > 0 | best t (n >= 30) | t bar family / lineage (N) | probation bar | verdict |",
         "|---|---|---|---|---|---|---|"]
    for f, g in d.groupby("fam"):
        g30 = g[g.n >= 30]
        b = g30.sort_values("t", ascending=False).iloc[0] if len(g30) else None
        best = f"{b['name']} n {int(b['n'])} exp {b['exp']:+.3f} t {b['t']:.2f}" if b is not None else "-"
        L.append(f"| {f} {FAM_TITLE[f]} | {len(g)} | {int((g.exp > 0).sum())} | {best} | {g.t_req_family.iloc[0]} / "
                 f"{g.t_req_lineage.iloc[0]} ({int(g.N_lineage.iloc[0])}) | {int(g.probation.sum())} pass | FAILED |")
    L += ["", "Round-as-one-lineage bar (1,051 configurations): t >= 3.73; package B alone (368): t >= 3.44. "
          "No configuration reaches either.", "",
          "## Every configuration", "",
          "Sorted: retire, then rework (no keep exists), then by t. exp in R (0.25 x daily ATR) after costs; base = random "
          "same-side same-window bar (one per symbol-day, same exit; S exits vs hold-to-15:55 with a 1R stop); hedged = "
          "minus beta60 x SPY over the same bars, SPY costs in; maxday = busiest session's share of trades; "
          "fomc = FOMC-week sessions (reporting only).", "",
          "| config | n | win | exp | t | up | flat | down | WF+ | plateau | ex-best | maxday | hedged (t) | base | fomc (n) | med tod | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    d["vo"] = d.verdict.map({"retire": 0, "rework": 1, "keep": 2})
    for _, r in d.sort_values(["vo", "t"]).iterrows():
        if not r["n"] or r["n"] < 2:
            L.append(f"| {r['name']} | {int(r['n'])} | - | - | - | - | - | - | - | - | - | - | - | - | - | - | {r['verdict']} |")
            continue
        L.append(f"| {r['name']} | {int(r['n'])} | {r['win_rate']:.3f} | {fmt(r['exp'])} | {r['t']:.2f} | {fmt(r['up_exp'])} | "
                 f"{fmt(r['flat_exp'])} | {fmt(r['down_exp'])} | {fmt(r['wf_share'], 2) if pd.notna(r['wf_share']) else '-'} | "
                 f"{fmt(r['plateau_mean'])} | {fmt(r['ex_best_day'])} | {r['maxday_share']:.3f} | {fmt(r['hedged_exp'])} "
                 f"({r['hedged_t'] if pd.notna(r['hedged_t']) else '-'}) | {fmt(r['base_exp'])} | {fmt(r['fomc_wk_exp'])} "
                 f"({int(r['fomc_wk_n'])}) | {int(r['tod_med'])} | {r['verdict']} |")
    (HERE / "RESULTS.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "md":
    write_md()
