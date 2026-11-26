"""HEDGE-B live replay: Primary journal lots 2026-10-23..11-25 (run 1, LR8 cost-R as footrace.live_trades; journal from
origin/mcf-data copied to LIVEDIR and deleted after reading), Alpaca SIP 1-min bars (open marks, SPY, IWM), Alpaca daily
bars (60-session betas to SPY and IWM). Live REF = actual lots with the -2R latch (BASE) or LATCH-OPEN and the -20R halt as
what-if (squeeze_1125/live.py engine); the hedge overlay (hedge_core.py) adds H8 / H4. Lineups: P4 = every Primary lot,
L3OUT = without L3-gap-slope-fromopen-FD. Usage (cwd repo): python live.py LIVEDIR. Educational only - not financial advice."""
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402
from hedge_core import hedge  # noqa: E402

L = Path(sys.argv[1]); L.mkdir(parents=True, exist_ok=True); TZ = "America/New_York"
LO_D, HI_D = "2026-10-23", "2026-11-25"
L3 = "L3-gap-slope-fromopen-FD"

lp = L / "lots.parquet"
if not lp.exists():
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", "origin/mcf-data:journal.db"], capture_output=True).stdout
    p = L / "j.db"; p.write_bytes(raw)
    try:
        con = sqlite3.connect(p)
        t = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                        "meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    finally:
        os.remove(p)
    t["date"] = t["date"].astype(str).str[:10]
    t = t[(t.date >= LO_D) & (t.date <= HI_D)].copy()
    t["r"] = cost_r_lr8(t, load_config()).astype(float)
    t = t[t["r"].notna()]
    t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
    t = t.drop_duplicates("k")
    t["side_n"] = np.where(t.side.astype(str).str.lower().isin(["1", "long", "buy"]), 1, -1)
    t["risk"] = (t.entry - t.stop).abs()
    t = t[t.risk > 0].copy()
    t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
    for c, s in (("em", "entry_time"), ("xm", "exit_time")):
        tt = pd.to_datetime(t[s], utc=True, format="mixed").dt.tz_convert(TZ)
        t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
    t["e_ns"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").astype("int64")
    t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
    t = t[(t.em >= 570) & (t.em < 960)]
    t[["strategy", "symbol", "date", "side_n", "entry", "stop", "exit", "risk", "cost", "r", "em", "xm", "e_ns"]].to_parquet(lp)
T = pd.read_parquet(lp)
print("lots", len(T), "days", T.date.nunique(), "R", round(T.r.sum(), 1))

gp = L / "grid.npz"
if not gp.exists():
    dc = _client(); G = {}
    for d, g in T.groupby("date"):
        syms = sorted(set(g.symbol) | {"SPY", "IWM"})
        a = datetime.fromisoformat(d) + timedelta(hours=13); b = a + timedelta(hours=9)
        raw = _bars(dc, syms, a, b, 1, "sip")
        for s, x in raw.groupby(level=0):
            x = rth(normalize(x.droplevel(0)))
            x.index = pd.DatetimeIndex(x.index).tz_convert(TZ)
            x = x[x.index.date.astype(str) == d]
            if not len(x):
                continue
            k = (x.index.hour * 60 + x.index.minute).to_numpy() - 570
            ok = (k >= 0) & (k < 390)
            c = np.full(390, np.nan); c[k[ok]] = x.close.to_numpy()[ok]
            G[f"{s}|{d}"] = np.concatenate([[x.open.to_numpy()[ok][0]], pd.Series(c).ffill().bfill().to_numpy()])
        print(d, len(syms), flush=True)
    np.savez_compressed(gp, keys=np.array(list(G)), arr=np.stack(list(G.values())))
z = np.load(gp, allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))

bp = L / "beta.parquet"
if not bp.exists():
    syms = sorted(set(T.symbol) | {"SPY", "IWM"})
    raw = _bars(_client(), syms, datetime(2026, 6, 15), datetime(2026, 11, 26), None, "sip")
    x = raw.reset_index()[["symbol", "timestamp", "close"]]
    x["date"] = pd.to_datetime(x.timestamp, utc=True).dt.tz_convert(TZ).dt.date.astype(str)
    x = x.sort_values(["symbol", "date"])
    x["ret"] = x.groupby("symbol").close.pct_change()
    out = []
    for mk in ("SPY", "IWM"):
        mret = x[x.symbol == mk].set_index("date").ret
        x["m"] = x.date.map(mret)
        for s, g in x.groupby("symbol"):
            r, m = g.ret.where(g.m.notna()), g.m.where(g.ret.notna())
            mu = lambda v: v.rolling(60, min_periods=20).mean()  # noqa: E731
            beta = ((mu(r * m) - mu(r) * mu(m)) / (mu(m * m) - mu(m) ** 2)).shift(1)
            out.append(pd.DataFrame({"mkt": mk, "symbol": s, "date": g.date, "beta": beta}))
    pd.concat(out).to_parquet(bp)
BB = pd.read_parquet(bp)
bs = BB[BB.mkt == "SPY"].drop(columns="mkt"); bi = BB[BB.mkt == "IWM"].drop(columns="mkt").rename(columns={"beta": "bi"})
IWB = bs[bs.symbol == "IWM"].set_index("date").beta.to_dict()
T = T.merge(bs, on=["symbol", "date"], how="left").merge(bi, on=["symbol", "date"], how="left")
T["beta"] = np.where(T.beta.notna(), np.clip(0.67 * T.beta + 0.33, -3, 3), 1.0)
T["bi"] = np.where(T.bi.notna(), np.clip(0.67 * T.bi + 0.33, -3, 3), 1.0)
T["b"] = T.side_n * T.beta * 0.01 * T.entry / T.risk
T["bI"] = T.side_n * T.bi * 0.01 * T.entry / T.risk
T["g"] = T.entry / T.risk
T = T.sort_values(["date", "e_ns"]).reset_index(drop=True)
SH = {}


def run_day(g, d, lo, shift, H=20.0):
    S = sorted(g.strategy.unique()); si = g.strategy.map({s: k for k, s in enumerate(S)}).to_numpy(); N = len(S)
    em, xm = g.em.to_numpy(), g.xm.to_numpy()
    side, ent, risk, cost, bb, bbi, gg = (g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float),
                                          g.cost.to_numpy(float), g.b.to_numpy(float), g.bI.to_numpy(float), g.g.to_numpy(float))
    shk = g.strategy.map(shift).fillna(0.0).to_numpy(float) if shift else np.zeros(len(g))
    rr = g.r.to_numpy(float) - shk
    dur = np.maximum(xm - em, 1).astype(float)
    grids = []
    for q, s in enumerate(g.symbol):
        a = G.get(f"{s}|{d}")
        if a is not None:
            c = a[1:391].copy(); g0 = c[min(389, max(0, em[q] - 570))]
            if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                c = c * (ent[q] / g0)
            a = c
        grids.append(a)
    realized = np.zeros(N); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; halted = False
    E = np.zeros(390); EI = np.zeros(390); ES = np.zeros((N, 390)); GR = np.zeros(390); OPN = np.zeros(390, bool)
    by_m = {}
    for k in range(len(g)):
        by_m.setdefault(em[k], []).append(k)

    def mark(k, m):
        a = grids[k]
        if a is None:
            return 0.0
        return side[k] * (a[min(389, max(0, m - 570))] - ent[k]) / risk[k] - cost[k] - shk[k] * min(1.0, max(0.0, (m - em[k]) / dur[k]))
    def realize(m):
        nonlocal open_
        kp = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]
            else:
                kp.append(k)
        open_ = kp
    for m in range(min(by_m), 960):
        if m > max(by_m) and not open_:
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            if halted or latched[si[k]] or olat[si[k]]:
                continue
            open_.append(k)
        realize(m)
        ps = realized.copy()
        for k in open_:
            ps[si[k]] += mark(k, m)
        if open_ and m < 960:
            o = np.array(open_); q = m - 570
            E[q] = bb[o].sum(); EI[q] = bbi[o].sum(); ES[:, q] = np.bincount(si[o], weights=bb[o], minlength=N)
            GR[q] = gg[o].sum(); OPN[q] = True
        if lo:
            olat |= ps <= -2.0 + 1e-12
        if ps.sum() <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return S, realized, E, EI, ES, GR, OPN


rows = []
for lineup in ("P4", "L3OUT"):
    TT = T if lineup == "P4" else T[T.strategy != L3]
    for book in ("RAW", "Z"):
        shift = None
        if book == "Z":
            shift = TT.groupby("strategy").r.mean().to_dict()
        for lo in (False, True):
            for d, g in TT.groupby("date"):
                S, r, E, EI, ES, GR, OPN = run_day(g.reset_index(drop=True), d, lo, shift)
                row = dict(lineup=lineup, book=book, lo=lo, date=d, R=r.sum(), Emax=np.abs(E).max())
                a, b = G.get(f"SPY|{d}"), G.get(f"IWM|{d}")
                row["spy_oc"] = a[-1] / a[0] - 1
                for B in (8.0, 4.0):
                    g_, c_, nr, tv, pv, pg, al = hedge(E, EI, ES, GR, OPN, a[1:], b[1:], float(IWB.get(d, 1.2) or 1.2), B)
                    t = f"H{int(B)}"
                    row.update({f"{t}_g": g_, f"{t}_c": c_, f"{t}_nreb": nr, f"{t}_tr": tv, f"{t}_pkv": pv, f"{t}_pkg": pg})
                    for s, v in zip(S, al):
                        row[f"{t}_a|{s}"] = v
                rows.append(row)
X = pd.DataFrame(rows)
X.to_csv(Path(__file__).resolve().parent / "live_days.csv", index=False)
for (ln, bk, lo), x in X.groupby(["lineup", "book", "lo"]):
    print(ln, bk, "LO" if lo else "BASE", "REF %.1f  H8 %+.1f (cost %.1f)  H4 %+.1f (cost %.1f)  worst5 %.1f / %.1f / %.1f" % (
        x.R.sum(), (x.H8_g - x.H8_c).sum(), x.H8_c.sum(), (x.H4_g - x.H4_c).sum(), x.H4_c.sum(),
        x.R.nsmallest(5).mean(), (x.R + x.H8_g - x.H8_c).nsmallest(5).mean(), (x.R + x.H4_g - x.H4_c).nsmallest(5).mean()))
