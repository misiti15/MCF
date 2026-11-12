"""FWDCAL stop-slip check (Lead 11-12 05:00, Observer stopslip2, Skeptic checklist 34): matched stop-out pairs (live stop
exit AND replay stop exit), live exits better than the ORIGINAL stop dropped (moved stops), adverse tails kept. Gap
(replay R - live R) per quintile of live entry spread / stop distance, for each book variant given.
    python stopq.py --dates A..B --variants q0,qs0          Educational only - not financial advice."""
import argparse, json, os, sqlite3, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
sys.argv_ = sys.argv; sys.argv = [sys.argv[0]]
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import mirror as M  # noqa: E402
sys.argv = sys.argv_


def live_spread_stop(days):
    rows = []
    for acc, br in M.RUN.BRANCH.items():
        raw = M.RUN.git("show", f"origin/{br}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            fh.write(raw)
        try:
            c = sqlite3.connect(fh.name); q = ",".join("?" * len(days))
            t = pd.read_sql(f"select date, strategy as setup, symbol, side, entry_time, entry, stop, exit from trades where run_id=1 and date in ({q})", c, params=list(days))
            s = pd.read_sql(f"select day as date, ts, strategy as setup, symbol, info from signals where run_id=1 and status='submitted' and day in ({q})", c, params=list(days))
            c.close()
        finally:
            os.unlink(fh.name)
        def spr(i):
            try:
                d = json.loads(i[: i.rindex("}") + 1]); return float(d["ask"]) - float(d["bid"])
            except Exception:
                return np.nan
        s["spr"] = s["info"].map(spr); s["ts"] = pd.to_datetime(s.ts, utc=True, format="mixed")
        t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed")
        t = t.sort_values("et"); s = s.sort_values("ts")
        t = pd.merge_asof(t, s[["ts", "setup", "symbol", "spr"]], left_on="et", right_on="ts", by=["setup", "symbol"], direction="backward",
                          tolerance=pd.Timedelta("10min"))
        t["acct"] = acc; rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    T["ss"] = T.spr / (T.entry - T.stop).abs()
    T["better_than_stop"] = T.side * (T.exit - T.stop) > 0
    return T[["acct", "date", "setup", "symbol", "side", "entry_time", "ss", "better_than_stop"]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dates"); ap.add_argument("--variants", default="q0,qs0"); a = ap.parse_args()
    days = M.RUN.trading_days(*a.dates.split(".."))
    L = M.live_trades_x(); L = L[L.date.isin(days)].copy()
    L = L.merge(live_spread_stop(days), on=["acct", "date", "setup", "symbol", "side", "entry_time"], how="left")
    L["et"] = pd.to_datetime(L.entry_time, utc=True, format="mixed")
    out = []
    for v in a.variants.split(","):
        fs = [f for f in (M.OUT / "books" / v).glob("*/*.json") if f.parent.name in days]
        reps = [json.loads(f.read_text()) for f in fs]
        X = pd.DataFrame([{"date": r["day"], "acct": r["acc"], "setup": t["strategy"], "symbol": t["symbol"], "side": int(t["side"]),
                           "entry_time": t["entry_time"], "R": t["r"], "xk": M.xkind(t.get("exit_reason"))} for r in reps if not r.get("skipped") for t in r["trades"]])
        X["et"] = pd.to_datetime(X.entry_time, utc=True, format="mixed")
        for (d, ac), x in X.groupby(["date", "acct"]):
            l = L[(L.date == d) & (L.acct == ac)]
            for i, j in M.REP.match(x, l, 5.0):
                if x.loc[i, "xk"] == "stop" and l.loc[j, "xk"] == "stop":
                    out.append(dict(variant=v, date=d, acct=ac, ss=l.loc[j, "ss"], better=bool(l.loc[j, "better_than_stop"]),
                                    gap=x.loc[i, "R"] - l.loc[j, "R"]))
    P = pd.DataFrame(out); P = P[~P.better.fillna(False)]
    P = P[np.isfinite(P.ss)]
    edges = np.quantile(P[P.variant == P.variant.iloc[0]].ss, [0, .2, .4, .6, .8, 1])
    P["q"] = pd.cut(P.ss, np.unique(edges), labels=False, include_lowest=True) + 1
    R = P.groupby(["variant", "q"]).agg(n=("gap", "size"), ss_med=("ss", "median"), gap_mean=("gap", "mean")).round(4).reset_index()
    T = P.groupby("variant").agg(n=("gap", "size"), gap_mean=("gap", "mean"), gap_p05=("gap", lambda g: g.quantile(.05)),
                                 gap_p95=("gap", lambda g: g.quantile(.95))).round(4).reset_index()
    pd.set_option("display.width", 200)
    print(f"stop-out pairs (both stop exits; live better-than-stop exits dropped), {a.dates}:")
    print(T.to_string(index=False)); print(R.pivot(index="q", columns="variant", values="gap_mean").join(R.groupby("q").ss_med.first()).to_string())
    print("gap = replay R - live R (+ = replay optimistic). Simulated only. Educational only - not financial advice.")


if __name__ == "__main__":
    main()
