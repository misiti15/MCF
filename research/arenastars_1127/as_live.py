"""ARENASTARS-1127 Part A: live audit of G05 / G07 / G37 from the account journals (git show origin/mcf-data*:journal.db,
read-only, copied to a scratch dir and deleted after). Per trade: LR8 R (mcf.costs.cost_r_lr8 = footrace basis),
fill-gross R (fills, no fees, risk from the fill), LIVE-L R (decision-bar close ref_price -> engine exit, minus the
primshorts_1126 LIVE-L cost). De-dup as footrace (setup|symbol|date|entry minute, first account in BRANCHES order).
Usage (cwd repo): python as_live.py SCRATCH OUTDIR. Educational only - not financial advice."""
import json
import math
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, "research/primshorts_1126")
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.research.shadow_calib import BRANCHES  # noqa: E402
import calib_live as CL  # noqa: E402

SC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
CAND = {"GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short": "G05",
        "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short": "G07",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long": "G37"}
PRIMARY_SETUPS = None


def load():
    cfg = load_config(); TP, SG, SK, PR = [], [], [], []
    for acct, br in BRANCHES.items():
        p = SC / f"{acct}.db"
        raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
        if not raw:
            continue
        p.write_bytes(raw); del raw
        con = sqlite3.connect(p)
        x = pd.read_sql("SELECT strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                        "exit_reason, meta, shares, pnl, pnl_adj, r_multiple, broker_order_id, slip_bps FROM trades "
                        "WHERE run_id=1 AND exit_time IS NOT NULL", con)
        if acct == "primary":
            PR.append(x[["strategy", "symbol", "date"]].assign(date=x.date.astype(str).str[:10]))
        x = x[x.strategy.isin(CAND)]
        s = pd.read_sql("SELECT day, symbol, strategy, side, ref_price, stop AS sstop, broker_order_id, status, reason, info FROM signals "
                        "WHERE run_id=1", con)
        con.close(); os.remove(p)
        s = s[s.strategy.isin(CAND)]
        x["account"] = acct; s["account"] = acct
        TP.append(x); SG.append(s)
    t = pd.concat(TP, ignore_index=True); s = pd.concat(SG, ignore_index=True)
    t["date"] = t.date.astype(str).str[:10]
    t["r_lr8"] = cost_r_lr8(t, cfg).astype(float)
    sub = s[(s.status == "submitted") & s.broker_order_id.notna()].copy()
    sub["bar_time"] = sub["info"].str.extract(r'"bar_time": "(\d+)"')[0]
    sub["spread_bps"] = sub["info"].str.extract(r'"spread_bps": ([\d.]+)')[0].astype(float)
    sub = sub.drop_duplicates(["account", "broker_order_id"])
    t = t.merge(sub[["account", "broker_order_id", "ref_price", "sstop", "bar_time", "spread_bps"]],
                on=["account", "broker_order_id"], how="left")
    t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
    t["acct_ord"] = t.account.map({a: i for i, a in enumerate(BRANCHES)})
    t = t.sort_values(["acct_ord"]).drop_duplicates("k").reset_index(drop=True)
    st = s.copy(); st["date"] = st.day.astype(str).str[:10]
    return t, st, pd.concat(PR, ignore_index=True)


def live_l(t):
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    side = t.side.astype(float); ref = t.ref_price.fillna(t.entry).astype(float)
    stop0 = t.sstop.fillna(t.stop).astype(float)
    risk = (ref - stop0).abs()
    kind = t.exit_reason.map({"stop": "stop", "target": "target", "trail": "stop"}).fillna("market")
    initial = (t.exit - stop0).abs() <= 0.25 * risk
    ex = np.where((kind == "stop") & initial, stop0, np.where(kind == "target", t.target.astype(float), t.exit.astype(float)))
    gross = side * (ex - ref) / risk
    t["r_ll_gross"] = gross
    t["livel_cost"] = CL.predict_R(cells, ref.to_numpy(), risk.to_numpy(), kind.to_numpy())
    t["r_livel"] = gross - t.livel_cost
    rf = (t.entry - t.stop).abs() * t.shares.abs()
    t["r_fill"] = t.pnl / rf.replace(0, np.nan)
    t["kind"] = kind
    return t


def day_t(r, d):
    g = r.groupby(d).mean()
    return float(g.mean() / (g.std(ddof=1) / math.sqrt(len(g)))) if len(g) > 2 and g.std(ddof=1) > 0 else float("nan")


def clus_t(r, d):
    m = r.mean(); e = (r - m).groupby(d).sum(); se = math.sqrt(float((e ** 2).sum())) / len(r)
    return float(m / se) if se > 0 else float("nan")


def summ(g, col):
    r, d = g[col], g.date
    day = r.groupby(d).sum().sort_values(ascending=False)
    tot = float(r.sum())
    b1 = day.index[:1]; b2 = day.index[:2]
    n = len(r); avg = float(r.mean())
    return {"n": n, "days": int(day.size), "avg": round(avg, 4), "total": round(tot, 2),
            "t_day": round(day_t(r, d), 2), "t_clus": round(clus_t(r, d), 2),
            "green_pct": round(float((day > 0).mean()), 3),
            "wo_best1": round(float(r[~d.isin(b1)].mean()), 4) if (~d.isin(b1)).any() else None,
            "wo_best2": round(float(r[~d.isin(b2)].mean()), 4) if (~d.isin(b2)).any() else None,
            "best_day": str(day.index[0]), "best_day_R": round(float(day.iloc[0]), 2),
            "best_share": round(float(day.iloc[0] / tot), 3) if tot > 0 else None,
            "top2_share": round(float(day.iloc[:2].sum() / tot), 3) if tot > 0 else None,
            "worst_day_R": round(float(day.iloc[-1]), 2),
            "shrunk": round(n / (n + 150) * avg + 150 / (n + 150) * -0.10, 4),
            "by_day": {k: [int((d == k).sum()), round(float(v), 2)] for k, v in day.sort_index().items()}}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True); SC.mkdir(parents=True, exist_ok=True)
    t, sg, pr = load()
    t = live_l(t)
    reps = json.load(open("docs/live/arena_reps.json"))["setups"]
    pkeys = set(pr.symbol + "|" + pr.date)
    res = {}
    for name, tag in CAND.items():
        g = t[t.strategy == name].copy()
        o = {"name": name, "accounts": g.account.value_counts().to_dict(), "first": g.date.min(), "last": g.date.max(),
             "reps": reps.get(name)}
        for col in ("r_lr8", "r_fill", "r_livel"):
            o[col] = summ(g[g[col].notna()], col)
        ok = g.r_livel.notna()
        o["ref_coverage"] = round(float(g.ref_price.notna().mean()), 3)
        g["pb"] = CL.pbucket(g.ref_price.fillna(g.entry))
        o["by_price"] = {k: {"n": int(len(x)), "lr8": round(float(x.r_lr8.mean()), 4), "livel": round(float(x.r_livel.mean()), 4),
                             "fill": round(float(x.r_fill.mean()), 4)} for k, x in g.groupby("pb")}
        o["sub20_share"] = round(float((g.ref_price.fillna(g.entry) < 20).mean()), 3)
        o["median_price"] = round(float(g.entry.median()), 2)
        o["spread_bps"] = {"median": round(float(g.spread_bps.median()), 2), "p90": round(float(g.spread_bps.quantile(0.9)), 2)}
        o["entry_slip_R"] = round(float((g.side * (g.entry - g.ref_price) / (g.ref_price - g.sstop).abs()).mean()), 4)
        o["livel_cost_avg"] = round(float(g.livel_cost.mean()), 4)
        o["lr8_cost_avg_vs_fill"] = round(float((g.r_fill - g.r_lr8).mean()), 4)
        o["by_exit"] = {k: [int(len(x)), round(float(x.r_livel.mean()), 3)] for k, x in g.groupby("exit_reason")}
        o["by_account"] = {a: summ(x, "r_livel") | {"by_day": None} for a, x in g.groupby("account")}
        o["notional_usd_median"] = round(float((g.entry * g.shares.abs()).median()), 0)
        nov = g[~(g.symbol + "|" + g.date).isin(pkeys)]
        o["non_overlap"] = summ(nov, "r_livel") | {"by_day": None}
        o["primary_overlap_trades"] = int(len(g) - len(nov))
        ss = sg[sg.strategy == name]
        o["signal_status"] = ss.status.value_counts().to_dict()
        reasons = ss[ss.status != "submitted"]["reason"].astype(str).str.replace(r"[\d.]+", "#", regex=True)
        o["skip_reasons_top"] = reasons.str[:48].value_counts().head(8).to_dict()
        res[tag] = o
        print(tag, json.dumps({k: o[k] for k in ("accounts", "first", "last", "reps")}, default=str))
        for col in ("r_lr8", "r_fill", "r_livel"):
            print("  ", col, {k: v for k, v in o[col].items() if k != "by_day"})
        print("   by_price", o["by_price"], "sub20", o["sub20_share"], "spread", o["spread_bps"], "slipR", o["entry_slip_R"])
        print("   by_day", o["r_livel"]["by_day"])
        print("   non_overlap", {k: v for k, v in o["non_overlap"].items() if k in ("n", "avg", "wo_best1", "best_share")},
              "overlap", o["primary_overlap_trades"])
        print("   exits", o["by_exit"], "status", o["signal_status"])
    t[["account", "strategy", "symbol", "date", "entry_time", "side", "entry", "ref_price", "stop", "sstop", "exit",
       "exit_reason", "shares", "spread_bps", "r_lr8", "r_fill", "r_livel"]].assign(
        strategy=lambda x: x.strategy.map(CAND)).to_csv(OUT / "live_trades.csv", index=False)
    json.dump(res, open(OUT / "live_audit.json", "w"), indent=1, default=str)
