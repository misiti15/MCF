"""FWDCAL matched-gap decomposition (Skeptic 11-14 02:50, Lead 03:00; diagnostic, the fresh window is already scored): for
matched pairs, replay R - live R split into ENTRY price gap = side x (live entry - replay entry) / live stop distance
(+ = replay entered better) and EXIT price gap = side x (replay exit - live exit) / distance (+ = replay exited better),
by exit kind. Live entry/exit from the journals. If the entry gap is ~+0.04R (Observer's decision-to-fill drift) the
engine prices trades right once that drift is charged.
    python matchgap.py --dates A..B --variant q0          Educational only - not financial advice."""
import argparse, json, os, sqlite3, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
_a = sys.argv; sys.argv = [sys.argv[0]]
sys.path.insert(0, str(Path(__file__).resolve().parent)); import mirror as M  # noqa: E402
sys.argv = _a


def live_px(days):
    rows = []
    for acc, br in M.RUN.BRANCH.items():
        raw = M.RUN.git("show", f"origin/{br}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
            fh.write(raw)
        try:
            c = sqlite3.connect(fh.name); q = ",".join("?" * len(days))
            t = pd.read_sql(f"select date, strategy as setup, symbol, side, entry_time, entry as l_entry, stop as l_stop, exit as l_exit "
                            f"from trades where run_id=1 and exit is not null and date in ({q})", c, params=list(days)); c.close()
        finally:
            os.unlink(fh.name)
        t["acct"] = acc; rows.append(t)
    return pd.concat(rows, ignore_index=True)


_CFG = {}


def lr8_r(t, day, acc):
    """The replay trade's R on live's LR8 basis (Lead/Skeptic: like with like): (pnl - live cost model) / risk, via
    mcf.costs.pnl_adj with that day's mirrored config (the model applies to trades dated >= its effective_from)."""
    from mcf.costs import pnl_adj, parts_from_row
    if (day, acc) not in _CFG:
        _CFG[(day, acc)] = M.mirror_cfg(acc, day)
    cfg = _CFG[(day, acc)]
    risk = abs(float(t["entry"]) - float(t["stop"])) * abs(float(t["shares"]))
    if not risk or cfg is None:
        return np.nan
    parts = parts_from_row({"exit_reason": t.get("exit_reason"), "shares": abs(float(t["shares"])), "exit": t["exit"], "meta": ""})
    adj, _ = pnl_adj(float(t["pnl"]), int(t["side"]), float(t["entry"]), abs(float(t["shares"])), parts,
                     float(t["exit"]) if M.xkind(t.get("exit_reason")) == "target" else None, day, cfg)
    return adj / risk


ap = argparse.ArgumentParser(); ap.add_argument("--dates"); ap.add_argument("--variant", default="q0"); a = ap.parse_args()
days = M.RUN.trading_days(*a.dates.split(".."))
L = M.live_trades_x(); L = L[L.date.isin(days)].copy()
L = L.merge(live_px(days).drop_duplicates(["acct", "date", "setup", "symbol", "side", "entry_time"]),
            on=["acct", "date", "setup", "symbol", "side", "entry_time"], how="left")
L["et"] = pd.to_datetime(L.entry_time, utc=True, format="mixed")
reps = [json.loads(f.read_text()) for f in (M.OUT / "books" / a.variant).glob("*/*.json") if f.parent.name in days]
X = pd.DataFrame([{"date": r["day"], "acct": r["acc"], "setup": t["strategy"], "symbol": t["symbol"], "side": int(t["side"]),
                   "entry_time": t["entry_time"], "R": t["r"], "r_entry": t["entry"], "r_exit": t["exit"], "xk": M.xkind(t.get("exit_reason")),
                   "R_lr8": lr8_r(t, r["day"], r["acc"])}
                  for r in reps if not r.get("skipped") for t in r["trades"]])
X["et"] = pd.to_datetime(X.entry_time, utc=True, format="mixed")
out = []
for (d, ac), x in X.groupby(["date", "acct"]):
    l = L[(L.date == d) & (L.acct == ac)]
    for i, j in M.REP.match(x, l, 5.0):
        xr, lr = x.loc[i], l.loc[j]
        dist = abs(lr.l_entry - lr.l_stop)
        if not (dist > 0 and np.isfinite(lr.l_exit)):
            continue
        out.append(dict(acct=ac, xk_live=lr.xk, xk_rep=xr.xk, rdiff=xr.R - lr.R, rdiff_lr8=xr.R_lr8 - lr.R, same_min=xr.et.floor("min") == lr.et.floor("min"),
                        entry_gap=xr.side * (lr.l_entry - xr.r_entry) / dist, exit_gap=xr.side * (xr.r_exit - lr.l_exit) / dist))
P_ = pd.DataFrame(out); P_["resid"] = P_.rdiff - P_.entry_gap - P_.exit_gap
pd.set_option("display.width", 200)
f = lambda g: pd.Series(dict(n=len(g), rdiff=g.rdiff.mean(), rdiff_lr8=g.rdiff_lr8.mean(), entry_gap=g.entry_gap.mean(), exit_gap=g.exit_gap.mean(), resid=g.resid.mean()))
print(f"matched pairs {len(P_)} ({a.variant}, {a.dates}); gaps in R of the live stop distance, + = replay better")
print("ALL:"); print(f(P_).round(4).to_string())
print("\nby exit kind (live x replay):"); print(P_.groupby(["xk_live", "xk_rep"]).apply(f).round(4).to_string())
print("\nby same entry minute:"); print(P_.groupby("same_min").apply(f).round(4).to_string())
print("\nby account:"); print(P_.groupby("acct").apply(f).round(4).to_string())
print("resid = rdiff - entry - exit (costs / R basis differences). Diagnostic. Educational only - not financial advice.")
