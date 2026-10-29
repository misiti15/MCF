"""p2_1029 report: two-year parent rates vs live, binding knob (diag stage -> binding.json), grid acceptance (grid stage).
    python report.py diag     -> diag_out.txt, binding.json
    python report.py grid     -> grid_out.txt, results.csv
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(Path(__file__).resolve().parent)]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
import bt2y as B  # noqa: E402

OUT = Path(__file__).resolve().parent
SCR = B.SCR
NSESS = len(lib.regimes())            # open-history sessions (locked block excluded)
MPS = 21.0                            # sessions per month


def stats(t):
    t = t[np.isfinite(t.r)]               # A7 structural stop at/below entry (no risk) -> no trade
    o = G.summary(t) if len(t) else {"n": 0}
    return dict(n=o.get("n", 0), per_day=round(o.get("n", 0) / NSESS, 3), per_month=round(o.get("n", 0) / NSESS * MPS, 1),
                avgR=o.get("exp_r"), t=o.get("t"), exbest=o.get("ex_best_day"),
                avgR_frame=round(float(t.r_frame.mean()), 4) if len(t) and t.r_frame.notna().any() else None)


def poisson_le(k, lam):
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(int(k) + 1))


def diag():
    T = pd.read_parquet(SCR / "trades_diag.parquet")
    D = pd.read_csv(OUT / "diag_diag.csv")
    tiers = pd.read_csv(OUT / "live_signals.csv")
    Dn = D.groupby(["setup", "config"]).n.sum()
    rows, bind = [], {}
    for s, d in B.SET.items():
        P = stats(T[(T.setup == s) & (T.config == "P")])
        PT = stats(T[(T.setup == s) & (T.config == "P+TS")])
        lv = tiers[tiers.setup == s].iloc[0]
        el = {}
        for kn, dr in d["knobs"]:
            cid = f"D:{kn}x{'1.2' if dr == 'up' else '0.8'}"
            el[kn] = Dn.get((s, cid), 0) / max(1, P["n"])
        kn = max(el, key=el.get) if el else None
        label = kn
        if kn and kn.startswith("flt"):
            label = f"{d['p']['filters'][int(kn[3:])][0]} {d['p']['filters'][int(kn[3:])][1]}"
        elif kn:
            label = f"{kn} {d['p'][kn]}"
        bind[s] = dict(knob=kn, label=label, elasticity_20pct=round(el.get(kn, 0), 3), all={k: round(v, 3) for k, v in el.items()})
        exp_live = P["per_day"] * lv.sessions
        rows.append(dict(setup=s, acct=d["acct"], tier=lv.tier, sessions=lv.sessions, live_trades=lv.trades, live_per_sess=lv.per_sess,
                         live_sigdays_per_sess=lv.symdays_per_sess, bt_per_day=P["per_day"], bt_per_month=P["per_month"],
                         live_over_bt=round(lv.per_sess / P["per_day"], 2) if P["per_day"] else None,
                         p_le_live=round(poisson_le(lv.trades, exp_live), 4), bt_n=P["n"], bt_avgR=P["avgR"], bt_avgR_frame=P["avgR_frame"],
                         bt_t=P["t"], bt_exbest=P["exbest"], TS_avgR=PT["avgR"], TS_t=PT["t"], binding=label,
                         binding_x=bind[s]["elasticity_20pct"], other_knobs=json.dumps(bind[s]["all"])))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "diag_table.csv", index=False)
    json.dump(bind, open(OUT / "binding.json", "w"), indent=1)
    loo = D[D.config.str.startswith(("LOO", "pass"))].groupby(["setup", "config"]).agg(n=("n", "sum"), bars=("bars", "sum"))
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
    txt = (f"open-history sessions {NSESS}; costs in; my 5-min path sim (avgR) vs frame 1-min outcome (avgR_frame)\n"
           + R.to_string(index=False) + "\n\nstack funnels (LOO = signals with that filter removed; pass = in-window bars passing):\n"
           + loo.to_string() + "\n\nEducational only - not financial advice.\n")
    open(OUT / "diag_out.txt", "w").write(txt)
    print(txt)


def grid():
    T0 = pd.read_parquet(SCR / "trades_diag.parquet")
    T1 = pd.read_parquet(SCR / "trades_grid.parquet")
    D = pd.read_csv(OUT / "diag_diag.csv")
    n_cfg = T0.groupby(["setup", "config"]).ngroups + D.groupby(["setup", "config"]).ngroups + T1.groupby(["setup", "config"]).ngroups
    bar = round(max(1.5, math.sqrt(2 * math.log(n_cfg))), 2)
    rows = []
    for s in B.SET:
        P = stats(T0[(T0.setup == s) & (T0.config == "P")])
        for cid in ["P", "P+TS"] + sorted(T1[T1.setup == s].config.unique()):
            g = (T0 if cid in ("P", "P+TS") else T1)
            st = stats(g[(g.setup == s) & (g.config == cid)])
            up = (st["per_month"] / P["per_month"] - 1) if P["per_month"] else np.nan
            ok_f = up >= 0.25
            ok_r = st["avgR"] is not None and P["avgR"] is not None and st["avgR"] >= P["avgR"]
            tt = st["t"] if st["t"] is not None else -9
            verdict = "QUALIFIES" if ok_f and ok_r and tt >= bar else ("near-miss" if ok_f and ok_r and tt >= bar - 0.3 else "fails")
            why = ",".join(x for x, ok in (("freq", ok_f), ("avgR", ok_r), ("t", tt >= bar)) if not ok)
            rows.append(dict(setup=s, config=cid, **st, trades_month_change=round(up * 100, 1) if up == up else None,
                             parent_avgR=P["avgR"], verdict=verdict if cid != "P" else "parent", failed=why if cid != "P" else ""))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "results.csv", index=False)
    best = (R[R.config != "P"].assign(key=lambda x: x.avgR.fillna(-9)).sort_values(["setup", "key"], ascending=[True, False])
            .groupby("setup").head(1))
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 400)
    txt = (f"configurations in this study N = {n_cfg}; bar t >= max(1.5, sqrt(2 ln N)) = {bar}; near-miss >= {bar - 0.3:.2f}\n"
           + R.to_string(index=False) + "\n\nbest variant per setup (highest avg R among the non-parent configs):\n"
           + best.drop(columns="key").to_string(index=False) + "\n\nEducational only - not financial advice.\n")
    open(OUT / "grid_out.txt", "w").write(txt)
    print(txt)


if __name__ == "__main__":
    {"diag": diag, "grid": grid}[sys.argv[1]]()
