"""hardstop_1123 step 3: live Primary replay 10-23..11-23 (run 1, LR8 cost-R) of the 17 rules on SIP 1-minute marks, and
the 11-23 pattern (win rate vs R, holds, MFE/MAE, entries while red). Blocked entries -> R 0; flattened lots exit at that
minute's close less max(1c, 1bp); freed slots are not refilled.
Usage: python live_replay.py WORKDIR.  Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
sys.path.insert(0, str(W))
from sim import CFGS  # noqa: E402

TZ = "America/New_York"
T = pd.read_parquet(W / "live.parquet")
B = pd.read_parquet(W / "livebars.parquet")
B["ts"] = pd.to_datetime(B.ts, utc=True).dt.tz_convert(TZ)
B["m"] = B.ts.dt.hour * 60 + B.ts.dt.minute
for c in ("entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
T["em"] = T.entry_time.dt.hour * 60 + T.entry_time.dt.minute
T["xm"] = T.exit_time.dt.hour * 60 + T.exit_time.dt.minute
T["rps"] = (T.entry - T.stop).abs()
T = T[T.rps > 0].sort_values(["date", "entry_time"]).reset_index(drop=True)
GRID = {}
for (s, d), g in B.groupby(["symbol", "date"]):
    a = np.full(390, np.nan)
    mm = g.m.values - 570
    ok = (mm >= 0) & (mm < 390)
    a[mm[ok]] = g.close.values[ok]
    GRID[(s, d)] = pd.Series(a).ffill().bfill().to_numpy()
# Alpaca bars come split-adjusted: rescale a symbol-day to the journal's raw prices when its close at the first entry
# minute is > 15% away from the fill (BITO 11-13, SNDK 11-05/06, ROM 11-12, EMBJ 10-26)
NSCALED = 0
for (s, d), g in T.groupby(["symbol", "date"]):
    a = GRID.get((s, d))
    if a is None:
        continue
    r0 = g.iloc[0]
    k = r0.entry / a[min(max(int(r0.em) - 570, 0), 389)]
    if abs(np.log(k)) > np.log(1.15):
        GRID[(s, d)] = a * k
        NSCALED += 1
print("rescaled symbol-days", NSCALED)
spy_days = sorted(d for (s, d) in GRID if s == "SPY")
SPYPCT = {}
for i, d in enumerate(spy_days):
    if i:
        pc = GRID[("SPY", spy_days[i - 1])][-1]
        SPYPCT[d] = (GRID[("SPY", d)] / pc - 1) * 100
SET = sorted(T.strategy.unique())


def mark(r, m):
    g = GRID.get((r.symbol, r.date))
    if g is None:
        return 0.0
    c = g[min(max(m - 570, 0), 389)]
    return (r.side * (c - r.entry) - max(0.01, 1e-4 * c)) / r.rps


def replay(day, cfg):
    rows = list(day.itertuples())
    out, st = {}, {}
    stopped = noentry = False
    latch = set()
    prev_open, fire = 0.0, None
    spy = SPYPCT.get(day.date.iloc[0])
    m0, m1 = day.em.min(), max(day.xm.max(), day.em.max())
    for m in range(m0, min(m1, 959) + 1):
        for r in rows:
            if r.em != m:
                continue
            ok = not (stopped or noentry or r.strategy in latch)
            if ok and cfg.get("spy_x") is not None and r.side < 0 and spy is not None:
                sp = spy[min(max(m - 1 - 570, 0), 389)]
                if sp > cfg["spy_x"] and prev_open < -cfg["open_y"]:
                    ok = False
            st[r.Index] = "in" if ok else "blocked"
            if not ok:
                out[r.Index] = 0.0
        op = [r for r in rows if st.get(r.Index) == "in" and r.xm > m]
        realized = {s: 0.0 for s in SET}
        for r in rows:
            if st.get(r.Index) == "in" and r.xm <= m:
                realized[r.strategy] += r.r
            elif st.get(r.Index) == "flat":
                realized[r.strategy] += out[r.Index]
        mk = {r.Index: mark(r, m) for r in op}
        tot = sum(realized.values()) + sum(mk.values())
        flat = set()
        if cfg.get("acct_stop") and not stopped and tot <= -cfg["acct_stop"]:
            stopped, flat, fire = True, set(mk), fire or m
        if cfg.get("no_new") and not noentry and tot <= -cfg["no_new"]:
            noentry, fire = True, fire or m
        if cfg.get("set_latch"):
            for s in SET:
                if s in latch:
                    continue
                v = realized[s] + sum(v for k, v in mk.items() if T.at[k, "strategy"] == s)
                if v <= -cfg["set_latch"]:
                    latch.add(s)
                    fire = fire or m
                    if cfg.get("set_flat"):
                        flat |= {k for k in mk if T.at[k, "strategy"] == s}
        for k in flat:
            st[k], out[k] = "flat", mk[k]
        prev_open = sum(v for k, v in mk.items() if k not in flat)
    for r in rows:
        if st.get(r.Index, "in") == "in":
            out[r.Index] = r.r
    return out, fire


if __name__ == "__main__":
    res = []
    for name, cfg in CFGS.items():
        for d, day in T.groupby("date"):
            out, fire = replay(day, cfg) if cfg else ({i: r for i, r in zip(day.index, day.r)}, None)
            for k, v in out.items():
                res.append((name, d, T.at[k, "strategy"], k, v, fire))
    R = pd.DataFrame(res, columns=["cfg", "date", "setup", "trade", "r", "fire_m"])
    R.to_csv(W / "live_replay.csv.gz", index=False)
    day = R.groupby(["cfg", "date"]).r.sum().unstack(0)
    base = day["base"]
    summ = []
    for c in CFGS:
        d = day[c] - base
        f = R[R.cfg == c].groupby("date").fire_m.first().notna().sum()
        summ.append(dict(cfg=c, fires=int(f), total=round(day[c].sum(), 2), dR=round(d.sum(), 2), worst=round(day[c].min(), 2),
                         worst_date=day[c].idxmin(), days_better=int((d > 1e-6).sum()), days_worse=int((d < -1e-6).sum()),
                         r_1123=round(day.loc["2026-11-23", c], 2)))
    S = pd.DataFrame(summ)
    S.to_csv(W / "live_summary.csv", index=False)
    print(S.to_string(index=False))
    day.round(2).to_csv(W / "live_by_day.csv")
    # ---------------------------------------------------------------- 11-23 pattern
    D = "2026-11-23"
    t = T[T.date == D].copy()
    mfe, mae, tl = [], [], []
    for r in t.itertuples():
        g = GRID[(r.symbol, D)]
        seg = g[r.em - 570:max(r.xm - 570, r.em - 570 + 1)]
        ex = r.side * (seg - r.entry) / r.rps
        mfe.append(ex.max())
        mae.append(ex.min())
    t["mfe_close"], t["mae_close"] = mfe, mae
    t["hold"] = t.xm - t.em
    t["tgt_R"] = (t.target - t.entry).abs() / t.rps
    cur = []
    for m in range(t.em.min(), 960):
        closed = t[t.xm <= m].r.sum()
        op = t[(t.em <= m) & (t.xm > m)]
        o = sum(mark(r, m) for r in op.itertuples())
        cur.append(dict(m=m, hhmm=f"{m // 60:02d}:{m % 60:02d}", closed=closed, open=o, n_open=len(op), total=closed + o,
                        spy=SPYPCT[D][m - 570] if D in SPYPCT else np.nan))
    cur = pd.DataFrame(cur)
    cur.round(3).to_csv(W / "d1123_curve.csv", index=False)
    pre = []
    for r in t.itertuples():
        st = cur[cur.m == r.em - 1]
        pre.append((float(st.open.iloc[0]) if len(st) else 0.0, float(st.total.iloc[0]) if len(st) else 0.0))
    t["book_open_at_entry"], t["book_total_at_entry"] = [p[0] for p in pre], [p[1] for p in pre]
    cols = ["strategy", "symbol", "side", "em", "xm", "hold", "exit_reason", "r", "tgt_R", "mfe_close", "mae_close",
            "book_open_at_entry", "book_total_at_entry"]
    t[cols].round(3).to_csv(W / "d1123_trades.csv", index=False)
    print(t[cols].round(2).to_string(index=False))
    lo = cur.loc[cur.total.idxmin()]
    print("min total", lo.hhmm, round(lo.total, 2), "open", round(lo.open, 2), "closed", round(lo.closed, 2))
    lo = cur.loc[cur.open.idxmin()]
    print("min open", lo.hhmm, round(lo.open, 2), "closed", round(lo.closed, 2), "n_open", lo.n_open)
    print("close", round(cur.total.iloc[-1], 2))
    # all live days: win rate, avg win / loss, holds, target R
    T["win"] = T.r > 0
    T["hold"] = T.xm - T.em
    T["tgt_R"] = (T.target - T.entry).abs() / T.rps
    g = T.groupby(T.date == D)
    print(g.apply(lambda x: pd.Series(dict(n=len(x), win=x.win.mean(), avg_win=x[x.win].r.mean(), avg_loss=x[~x.win].r.mean(),
                                            hold_win=x[x.win].hold.median(), hold_loss=x[~x.win].hold.median(),
                                            tgt_R=x.tgt_R.median(), avg_r=x.r.mean()))).round(3).to_string())
    T.groupby("strategy").apply(lambda x: pd.Series(dict(n=len(x), win=x.win.mean(), avg_win=x[x.win].r.mean(),
                                                         avg_loss=x[~x.win].r.mean(), hold_win=x[x.win].hold.median(),
                                                         hold_loss=x[~x.win].hold.median(), tgt_R=x.tgt_R.median(),
                                                         avg_r=x.r.mean()))).round(3).to_csv(W / "live_conversion.csv")
