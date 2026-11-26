"""SQUEEZE_1125 live replay: Primary journal lots 2026-10-23..11-25 (run 1, LR8 cost-R as footrace.live_trades), Alpaca
SIP 1-min bars (open marks, SPY open/VWAP), Alpaca daily bars (60-session betas). Configs as sim.py (PREREG.md).
Usage (cwd repo): python live.py LIVEDIR. Educational only - not financial advice."""
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, ".")
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402

L = Path(sys.argv[1]); L.mkdir(parents=True, exist_ok=True); TZ = "America/New_York"
LO_D, HI_D = "2026-10-23", "2026-11-25"
CFGS = ["BASE", "LO", "B8", "B12", "B16", "SV", "SO", "LO+B8", "LO+B12", "LO+B16", "LO+SV", "LO+SO"]

# ---------------------------------------------------------------- lots
lp = L / "lots.parquet"
if not lp.exists():
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", "origin/mcf-data:journal.db"], capture_output=True).stdout
    p = L / "j.db"; p.write_bytes(raw)
    con = sqlite3.connect(p)
    t = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, "
                    "shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    con.close(); os.remove(p)
    t["date"] = t["date"].astype(str).str[:10]
    t = t[(t.date >= LO_D) & (t.date <= HI_D)].copy()
    t["r"] = cost_r_lr8(t, load_config()).astype(float)
    t = t[t["r"].notna()]
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

# ---------------------------------------------------------------- 1-min grids (close; SPY also vwap)
gp = L / "grid.npz"
if not gp.exists():
    dc = _client(); G = {}
    for d, g in T.groupby("date"):
        syms = sorted(set(g.symbol) | {"SPY"})
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
            c = np.full(390, np.nan); tp = np.zeros(390); v = np.zeros(390)
            c[k[ok]] = x.close.to_numpy()[ok]
            tp[k[ok]] = ((x.high + x.low + x.close) / 3).to_numpy()[ok]; v[k[ok]] = x.volume.to_numpy()[ok]
            c = pd.Series(c).ffill().bfill().to_numpy()
            cv = np.cumsum(v); vw = np.where(cv > 0, np.cumsum(tp * v) / np.maximum(cv, 1e-9), c)
            G[f"{s}|{d}"] = np.concatenate([[x.open.to_numpy()[ok][0]], c, vw]).astype(np.float64)
        print(d, len(syms), flush=True)
    np.savez_compressed(gp, keys=np.array(list(G)), arr=np.stack(list(G.values())))
z = np.load(gp, allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))

# ---------------------------------------------------------------- betas (daily, 60 sessions, PREREG)
bp = L / "beta.parquet"
if not bp.exists():
    syms = sorted(set(T.symbol) | {"SPY"})
    raw = _bars(_client(), syms, datetime(2026, 6, 15), datetime(2026, 11, 26), None, "sip")
    x = raw.reset_index()[["symbol", "timestamp", "close"]]
    x["date"] = pd.to_datetime(x.timestamp, utc=True).dt.tz_convert(TZ).dt.date.astype(str)
    x = x.sort_values(["symbol", "date"])
    x["ret"] = x.groupby("symbol").close.pct_change()
    spy = x[x.symbol == "SPY"].set_index("date").ret
    x["m"] = x.date.map(spy)
    out = []
    for s, g in x.groupby("symbol"):
        r, m = g.ret, g.m
        mu = lambda v: v.rolling(60, min_periods=20).mean()  # noqa: E731
        beta = ((mu(r * m) - mu(r) * mu(m)) / (mu(m * m) - mu(m) ** 2)).shift(1)
        out.append(pd.DataFrame({"symbol": s, "date": g.date, "beta": beta}))
    pd.concat(out).to_parquet(bp)
BB = pd.read_parquet(bp)
T = T.merge(BB, on=["symbol", "date"], how="left")
T["beta"] = np.where(T.beta.notna(), np.clip(0.67 * T.beta + 0.33, -3, 3), 1.0)
T["b"] = T.side_n * T.beta * 0.01 * T.entry / T.risk
T = T.sort_values(["date", "e_ns"]).reset_index(drop=True)


def parse(name):
    lo = False; bud = None; sq = None
    for p in name.split("+"):
        if p == "LO":
            lo = True
        elif p.startswith("B") and p != "BASE":
            bud = float(p[1:])
        elif p in ("SV", "SO"):
            sq = "vwap" if p == "SV" else "open"
    return lo, bud, sq


def triggers(d, mode):
    a = G.get(f"SPY|{d}")
    if a is None:
        return -1, -1
    o = a[0]; c = a[1:391]; vw = a[391:781]
    lvl = vw if mode == "vwap" else np.full(390, o)
    sk = lk = -1; lows = his = False
    for k in range(390):
        if k >= 1:
            lows = lows or c[k - 1] <= o * 0.996
            his = his or c[k - 1] >= o * 1.004
        if k < 30 or k > 380:
            continue
        r30 = c[k] / c[k - 30] - 1
        if sk < 0 and lows and c[k] >= lvl[k] and r30 > 0.005:
            sk = k
        if lk < 0 and his and c[k] <= lvl[k] and r30 < -0.005:
            lk = k
    return sk, lk


def run_day(g, d, lo, bud, sq, H=20.0):
    S = sorted(g.strategy.unique()); si = g.strategy.map({s: k for k, s in enumerate(S)}).to_numpy(); N = len(S)
    em, xm = g.em.to_numpy(), g.xm.to_numpy()
    side, ent, risk, cost, rr, bb = (g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float),
                                     g.cost.to_numpy(float), g.r.to_numpy(float), g.b.to_numpy(float))
    grids = []
    for q, s in enumerate(g.symbol):
        a = G.get(f"{s}|{d}")
        if a is not None:
            c = a[1:391].copy(); g0 = c[min(389, max(0, em[q] - 570))]
            if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                c = c * (ent[q] / g0)
            a = c
        grids.append(a)
    sk, lk = triggers(d, sq) if sq else (-1, -1)
    s_m = 570 + sk + 1 if sk >= 0 else 10 ** 6; l_m = 570 + lk + 1 if lk >= 0 else 10 ** 6
    realized = np.zeros(N); latched = np.zeros(N, bool); olat = np.zeros(N, bool); taken = np.zeros(len(g), bool)
    open_ = []; halted = False; nb = 0.0; r1 = r2 = 0; c2 = 0; trough = 0.0
    by_m = {}
    for k in range(len(g)):
        by_m.setdefault(em[k], []).append(k)
    final = np.zeros(len(g))

    def mark(k, m):
        a = grids[k]
        if a is None:
            return None
        return side[k] * (a[min(389, max(0, m - 570))] - ent[k]) / risk[k] - cost[k]
    for m in range(min(by_m), 960):
        if m > max(by_m) and not open_:
            break
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; final[k] = rr[k]; nb -= bb[k]
            else:
                keep.append(k)
        open_ = keep
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if (side[k] < 0 and m >= s_m) or (side[k] > 0 and m >= l_m):
                r2 += 1; continue
            if bud is not None and ((side[k] < 0 and nb <= -bud) or (side[k] > 0 and nb >= bud)):
                r1 += 1; continue
            open_.append(k); taken[k] = True; nb += bb[k]
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; final[k] = rr[k]; nb -= bb[k]
            else:
                keep.append(k)
        open_ = keep
        if m == s_m or m == l_m:
            keep = []
            for k in open_:
                fl = (m == s_m and side[k] < 0) or (m == l_m and side[k] > 0)
                v = mark(k, m)
                if fl and v is not None:
                    realized[si[k]] += v; final[k] = v; nb -= bb[k]; c2 += 1
                else:
                    keep.append(k)
            open_ = keep
        ps = realized.copy()
        for k in open_:
            v = mark(k, m)
            ps[si[k]] += v if v is not None else 0.0
        if lo:
            olat |= ps <= -2.0 + 1e-12
        tot = ps.sum(); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]; final[k] = rr[k]
    return dict(zip(S, realized)), trough, r1, r2, c2, sk, lk, taken, final


rows, lots = [], []
for cfg in CFGS:
    lo, bud, sq = parse(cfg)
    for d, g in T.groupby("date"):
        R, tr, r1, r2, c2, sk, lk, taken, final = run_day(g.reset_index(drop=True), d, lo, bud, sq)
        rows.append(dict(cfg=cfg, date=d, R=sum(R.values()), trough=tr, r1blk=r1, r2blk=r2, r2closed=c2,
                         s_k=sk, l_k=lk, **{f"S|{k}": v for k, v in R.items()}))
pd.DataFrame(rows).to_csv(L / "live_days.csv", index=False)
print(pd.DataFrame(rows).groupby("cfg").R.sum().round(1))
