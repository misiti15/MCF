"""COMPASS-RD-1126 bench cross-check: bench10 trades (home-account book, LR8 research costs) tagged with point-in-time
index state at entry; avg R by condition per split; aligned contrasts (day-clustered t); OFF what-ifs.
Splits: FIT 2024-10 + 2025-03..09, CHECK 2025-10..2026-11-04, T2 2023-01..2024-09. Locked block never read.
Educational only - not financial advice."""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad"); W = S / "crd/bench"
sys.path.insert(0, str(S / "cp1")); sys.path.insert(0, str(S / "cp1/research/ultimate_1119/top10")); sys.path.insert(0, str(S / "cp1/research/forward/compass_gate"))
sys.argv = [sys.argv[0], str(S / "cp1"), str(W), "x"]
import bench_run as BR  # sets B.SETUPS
B = BR.B
import shadow as CG
etb = pd.read_parquet(S / "pyramid/R3C/etb_rate.parquet").rate
TZ = "America/New_York"

def idx_tables():
    out = {}
    for s in ("SPY", "QQQ", "IWM"):
        a = B.hist_bars(s)
        f = pd.read_parquet(B.FRESH / "1Min" / f"{s}.parquet"); f.index = pd.DatetimeIndex(f.index).tz_convert(TZ)
        b = pd.concat([f[f.index < a.index.min()], a]).sort_index()
        b = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
        b["date"] = b.index.date.astype(str); b["m"] = b.index.hour * 60 + b.index.minute
        B.no_locked(b.date.unique())
        out[s] = b
    return out

def tag(t, I):
    t = t.copy(); em = t.em.values
    for s, b in I.items():
        arrs = {}
        for dd, g in b.groupby("date"):
            a_ = np.full(400, np.nan); mm = g.m.values - 570; ok = (mm >= 0) & (mm < 390)
            a_[mm[ok] + 1] = g.close.values[ok] / g.open.values[0] - 1
            arrs[dd] = pd.Series(a_).ffill().fillna(0).values
        ix = np.clip(em - 570, 0, 389)
        t[s.lower() + "_fo"] = [arrs[d][i] if d in arrs else 0.0 for d, i in zip(t.date, ix)]
        if s == "SPY":
            d = b.groupby("date").agg(o=("open", "first"), c=("close", "last"), lo=("low", "min"), hi=("high", "max"))
            d["pc"] = d.c.shift(); d["gap"] = d.o / d.pc - 1; d["oc"] = d.c / d.o - 1
            d["lo"] = d.lo / d.o - 1; d["hi"] = d.hi / d.o - 1
            dt = np.where((d.oc >= .0025) & (d.lo <= -.005), "V-up", np.where((d.oc <= -.0025) & (d.hi >= .005), "V-down",
                 np.where(d.oc >= .0025, "up", np.where(d.oc <= -.0025, "down", "flat"))))
            d["dtype"] = dt
            t["gap"] = t.date.map(d.gap); t["dtype"] = t.date.map(d.dtype)
            # 30-min checkpoint state (from 10:30): SPY >= 0.30% from open at the latest checkpoint <= entry
            cps = list(range(630, 931, 30))
            cpv = {}
            for dd, g in b.groupby("date"):
                oo = g.open.iloc[0]; mm = g.m.values; cc = g.close.values
                cpv[dd] = {T: (cc[mm <= T - 1][-1] / oo - 1) if (mm <= T - 1).any() else 0 for T in cps}
            st = []
            for dd, e in zip(t.date, t.em):
                v = cpv.get(dd, {}); ok = [T for T in cps if T <= e]
                f = v.get(ok[-1], 0) if ok else 0
                st.append(1 if f >= .003 else (-1 if f <= -.003 else 0))
            t["cp30"] = st
    th = lambda v, k: np.where(v > k, 1, np.where(v < -k, -1, 0))
    a, q, w = th(t.spy_fo, .001), th(t.qqq_fo, .001), th(t.iwm_fo, .001)
    t["idx3"] = np.where((a == q) & (q == w), a, 0)
    t["expo"] = t.side * t.symbol.map(CG.beta_sign)
    e = t.expo.values
    t["spyo_al"] = e * th(t.spy_fo, .001); t["idx3_al"] = e * t.idx3; t["gap_al"] = e * th(t.gap.fillna(0), .0025)
    t["cp30_al"] = e * t.cp30
    t["day_al"] = e * np.where(t.dtype.isin(["up", "V-up"]), 1, np.where(t.dtype.isin(["down", "V-down"]), -1, 0))
    t["spyb"] = pd.cut(t.spy_fo, [-np.inf, -.005, -.001, .001, .005, np.inf], labels=["<-0.5", "-0.5..-0.1", "flat", "+0.1..+0.5", ">+0.5"]).astype(str)
    return t

def split(d):
    d = pd.Series(d)
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    return np.where(d < "2024-10-01", "T2", np.where(fit, "FIT", np.where(d >= "2025-10-01", "CHECK", "none")))

if __name__ == "__main__":
    T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet")); T2 = B.add_r(pd.read_parquet(W / "trades_t2.parquet"))
    B.no_locked(T1.date.unique()); B.no_locked(T2.date.unique())
    acct = {s: a for s, _, a in B.SETUPS}
    parts = []
    for s in acct:
        rules = B.BOOK["primary"] if acct[s] == "primary" else B.TESTING_RULES
        for T in (T1, T2):
            x = B.book(T[T.setup == s], rules, etb)
            parts.append(x)
    t = pd.concat(parts, ignore_index=True); t["split"] = split(t.date.values); t = t[t.split != "none"]
    t = tag(t, idx_tables())
    t.to_parquet(W / "bench_tagged.parquet")
    print(t.groupby(["setup", "split"]).r.agg(["size", "mean"]).round(3).to_string())
