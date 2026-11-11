"""MIN10 measurement (0 configs; Lead lead-20261111-0300-1, Skeptic -0301-2, Observer -0348-2), frozen before any score). python limex.py > limex_out.txt     Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
HERE = Path(__file__).resolve().parent; NY = "America/New_York"
TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SPLIT = pd.Timestamp("2025-09-30").date(); N_FAM = 1962; T90 = round(max(1.35, .9 * G.t_required(N_FAM)), 2)
SL, BP, SX = 0.01, 1e-4, 0.02; KS = (0.10, 0.25); NW = 10
POOL = ["MF3-open-flowsell-rsi5hi", "MF5-flowsell-vwapup-rsi5hi", "MF2-open-rsimidhi-flowsell-FD", "NS4-pm-vwap-reclaim-oversold-short",
        "GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long", "NS5-sma50-flush-oversold-long", "ST4-emadn-long-am-t1s05-FD",
        "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD",
        "CWT09-gapdn-bounce-g5-lowerhalf-short", "GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short",
        "GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long"]
L = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
L = L[L.setup.isin(POOL)].copy(); L["date"] = pd.to_datetime(L.date).dt.date; L["tod"] = L.tod.astype(int); L["symbol"] = L.symbol.astype(str)
missing = sorted(set(POOL) - set(L.setup)); print(f"pool: {L.setup.nunique()} of {len(POOL)} setups have 2y lists (missing: {missing}); trades {len(L)}")
parts = []
for m in sorted(pd.to_datetime(L.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"]); f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
    parts.append(L[pd.to_datetime(L.date).dt.strftime("%Y-%m") == m].merge(f, on=["symbol", "date", "tod"], how="left"))
L = pd.concat(parts, ignore_index=True).dropna(subset=["close", "atr_d"])

def walk(o, h, l, c, i0, e, s, D, U):
    """from index i0 (inclusive), stop-first; -> (exit px, kind 0 flat / 1 stop / 2 target)"""
    stop, tgt = e - s * D, e + s * U
    for i in range(i0, len(c)):
        if i > i0 and s * (o[i] - stop) <= 0: return o[i], 1
        if (s > 0 and l[i] <= stop) or (s < 0 and h[i] >= stop): return stop, 1
        if (s > 0 and h[i] >= tgt) or (s < 0 and l[i] <= tgt): return tgt, 2
    return c[-1], 0

def net(e, xp, kd, s, R, dn, ecost, tier):
    xcost = (0.0 if kd == 2 else SL + xp * BP) + (SX if kd == 1 else 0.0)
    g = s * (xp - e) / R
    return (g - tier * (ecost + xcost) / R) / dn, g / dn

def walk3(o, h, l, c, fill, s, stop, tgt):
    for i in range(0, len(c)):
        if i > 0 and s * (o[i] - stop) <= 0: return o[i], i
        if (s > 0 and l[i] <= stop) or (s < 0 and h[i] >= stop): return stop, i
        if (s > 0 and h[i] >= tgt) or (s < 0 and l[i] <= tgt): return tgt, i
    return c[-1], len(c) - 1

out = []
for sym, g in L.groupby("symbol"):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"; ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    df.index = pd.DatetimeIndex(df.index).tz_convert(NY); df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = df.index.hour * 60 + df.index.minute; df = df[(mm >= 570) & (mm < 955)]
    byd = {d: x for d, x in df.groupby(df.index.date)}
    for r in g.itertuples(index=False):
        x = byd.get(r.date)
        if x is None: continue
        m_ = (x.index.hour * 60 + x.index.minute).to_numpy(); t0 = r.tod // 100 * 60 + r.tod % 100
        j = int(np.searchsorted(m_, t0))
        if j + 10 >= len(m_): continue
        o, h, l, c = (x[k].to_numpy(float)[j:] for k in ("open", "high", "low", "close"))
        s = int(r.side); e = float(r.close); atr = float(r.atr_d); R = .25 * atr; up, dn = G.GEOMK[r.geom]; D, U = dn * R, up * R
        eb = o[0]; xp, ie = walk3(o, h, l, c, eb, s, eb - s * D, eb + s * U)
        if ie < 10: continue                                  # exited inside the first 10 minutes: not open at minute 10
        p10 = c[9]                                            # close of the 10th minute after the signal
        row = dict(setup=r.setup, date=r.date, first10=s * (p10 - eb) / atr, post10=s * (xp - p10) / atr,
                   exit_cost=(SL + p10 * BP) / atr)
        for k in (0.10, 0.25):
            trig = e + s * k * D
            row[f"T{k}"] = int(((h[:10] >= trig) if s > 0 else (l[:10] <= trig)).any())
        out.append(row)
X = pd.DataFrame(out); X.to_csv(HERE / "min10_rows.csv.gz", index=False)
SPLIT_ = SPLIT
tt = lambda s_: round(s_.mean() / (s_.std(ddof=1) / np.sqrt(len(s_))), 2) if len(s_) > 2 and s_.std() > 0 else None
print(f"signals open at minute 10: {len(X)} (10 setups, 2y lab lists, split-adjusted cache throughout - no live-price join)")
print(f"median extra exit cost at minute 10 (1c + 1bp, ATR units): {X.exit_cost.median():.4f}")
for k in (0.10, 0.25):
    for lab_, m in (("UNTRIGGERED", X[f"T{k}"] == 0), ("TRIGGERED", X[f"T{k}"] == 1)):
        x = X[m]
        for per, y in (("ALL", x), ("TRAIN", x[x.date <= SPLIT_]), ("VALID", x[x.date > SPLIT_])):
            d = y.groupby("date").post10.mean()
            print(f"  k {k:.2f} {lab_:11s} {per:5s} n {len(y):6d}  first10 {y.first10.mean():+.4f}  post10 gross {y.post10.mean():+.4f} ATR (day-t {tt(d)})")
    ps = X[X[f"T{k}"] == 0].groupby("setup").post10.agg(["mean", "size"])
    print(f"  k {k:.2f} untriggered post10 by setup: " + "; ".join(f"{i[:22]} {v['mean']:+.3f} (n {int(v['size'])})" for i, v in ps.iterrows()))
print("Reading rule (Lead, fixed): ~0 = martingale -> close the minute-10 exit; only clearly negative in TRAIN AND VALID -> counted plan.")
print("Educational only - not financial advice.")
