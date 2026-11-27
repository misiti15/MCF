"""CF-PRIMARY Part A: score the Testing cost-filter forward test (PREREG.md). Skipped rows = run-1 signals with reason
'cost filter:' 10-30..11-25; outcome = run-2 what-if trade (runner bar replay, backtest costs), first per
(symbol, date, setup); stripped to gross R on the raw signal price and re-costed with LIVE-L.
Usage (cwd repo): python part_a.py JOURNAL_DIR OUT_JSON. Journals are scratchpad copies (deleted after).
Educational only - not financial advice."""
import json
import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/primshorts_1126")
import calib_live as CL  # noqa: E402

JD, OUT = Path(sys.argv[1]), Path(sys.argv[2])
D0, D1 = "2026-10-30", "2026-11-25"
CELLS = json.load(open("research/primshorts_1126/cells_live.json"))
PRIMARY = ("testing", "testing2")


def load(acct):
    c = sqlite3.connect(JD / f"{acct}.db")
    w = pd.read_sql("select t.* from trades t join runs r on r.id=t.run_id where r.kind='whatif' and t.date between ? and ?",
                    c, params=(D0, D1))
    k = pd.read_sql("select t.* from trades t join runs r on r.id=t.run_id where r.kind='paper' and t.date between ? and ? "
                    "and t.exit_time is not null", c, params=(D0, D1))
    c.close()
    w = w[w.meta.fillna("").str.contains("status=skipped;why=cost filter:", regex=False)].copy()
    w = w.sort_values(["entry_time", "id"]).drop_duplicates(["symbol", "date", "strategy"], keep="first")
    return w, k


def recost(w):
    s = w.side.astype(float).to_numpy(); fill = w.entry.to_numpy(float); ex = w.exit.to_numpy(float)
    stop = w.stop.to_numpy(float); why = w.exit_reason.astype(str).to_numpy()
    px0 = (fill - s * 0.01) / (1 + s * 1e-4)
    raw_ex = np.where(why == "target", ex, np.where(why == "stop", (ex + s * 0.03) / (1 - s * 1e-4),
                                                     (ex + s * 0.01) / (1 - s * 1e-4)))
    risk0 = np.abs(px0 - stop)
    gross = s * (raw_ex - px0) / risk0
    kind = np.where(why == "target", "target", np.where(why == "stop", "stop", "market"))
    w = w.assign(R_bt=w.r_multiple.astype(float), R_gross=gross, R_ll=gross - CL.predict_R(CELLS, px0, risk0, kind),
                 cf_formula=(2 * (0.01 + px0 * 1e-4) + 0.02) / risk0)
    return w


def dstats(x, col):
    d = x.groupby("date")[col].sum()
    n = len(d); tot = d.sum()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(n)) if n > 1 and d.std(ddof=1) > 0 else np.nan
    best = d.max() if tot > 0 else d.min()
    return dict(n=int(len(x)), days=n, total=round(float(tot), 2), per_trade=round(float(x[col].mean()), 4),
                t_day=round(float(t), 2), per_trade_wo_best_day=round(float(x[x.date != d.idxmax() if tot > 0 else
                                                                                       x.date != d.idxmin()][col].mean()), 4),
                best_day_share=round(float(best / tot), 3) if tot else None)


def kept_r(k):
    k = k.copy()
    risk = (k.entry - k.stop).abs() * k.shares
    r = np.where(risk > 0, k.pnl_adj.fillna(k.pnl) / risk, np.nan)
    return pd.Series(r).dropna()


if __name__ == "__main__":
    res = {"window": [D0, D1], "accounts": {}}
    allw = []
    for p in sorted(JD.glob("*.db")):
        a = p.stem
        w, k = load(a)
        if not len(w):
            res["accounts"][a] = {"skipped": 0}
            continue
        w = recost(w).assign(acct=a)
        allw.append(w)
        kr = kept_r(k)
        res["accounts"][a] = {"primary": a in PRIMARY, "LIVE-L": dstats(w, "R_ll"), "backtest_cost": dstats(w, "R_bt"),
                              "gross": dstats(w, "R_gross"),
                              "kept_live_trades": int(len(kr)), "kept_live_R_per_trade": round(float(kr.mean()), 4),
                              "skip_share_of_entries": round(len(w) / max(len(w) + len(kr), 1), 3)}
    W = pd.concat(allw)
    P = W[W.acct.isin(PRIMARY)]
    res["pooled_primary"] = {"LIVE-L": dstats(P, "R_ll"), "backtest_cost": dstats(P, "R_bt"), "gross": dstats(P, "R_gross")}
    res["pooled_all"] = {"LIVE-L": dstats(W, "R_ll"), "backtest_cost": dstats(W, "R_bt")}
    ps = P.groupby("strategy").R_ll.agg(["size", "sum", "mean"])
    res["per_setup_primary"] = {"setups": int(len(ps)), "skip_helped (skipped sum<0)": int((ps["sum"] < 0).sum()),
                                "skip_hurt (skipped sum>0)": int((ps["sum"] > 0).sum()),
                                "helped_R": round(float(-ps.loc[ps["sum"] < 0, "sum"].sum()), 1),
                                "hurt_R": round(float(ps.loc[ps["sum"] > 0, "sum"].sum()), 1),
                                "largest_hurt": ps.sort_values("sum").tail(3).round(3).reset_index().values.tolist(),
                                "largest_help": ps.sort_values("sum").head(3).round(3).reset_index().values.tolist()}
    pl = P.assign(half=np.where(P.date < "2026-11-12", "10-30..11-11", "11-12..11-25"))
    res["by_half_primary"] = {h: dstats(g, "R_ll") for h, g in pl.groupby("half")}
    sl = P.assign(b=pd.cut(P.cf_formula, [0, 0.2, 0.3, 0.5, 99]).astype(str))
    res["by_cost_bucket_primary"] = {b: dstats(g, "R_ll") for b, g in sl.groupby("b")}
    lv = pooled = res["pooled_primary"]["LIVE-L"]
    same = all(np.sign(res["accounts"][a]["LIVE-L"]["total"]) == np.sign(lv["total"]) for a in PRIMARY)
    res["confirms_CF"] = bool(lv["total"] < 0 and lv["t_day"] <= -2.0 and same)
    res["contradicts_CF"] = bool(lv["total"] > 0 and lv["t_day"] >= 2.0)
    W[["acct", "date", "symbol", "strategy", "side", "exit_reason", "R_bt", "R_gross", "R_ll", "cf_formula"]].to_csv(
        OUT.with_suffix(".csv"), index=False)
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res, indent=1))
