"""Part A (PLAN.md): how well do early-session features predict the rest-of-day (C -> close) and afternoon (12:00 -> close)
return of SPY / QQQ / IWM? Day-level table from 1-min SIP bars (data/cache_hist/1Min) + lab breadth context. Locked
block 2024-11-01..2025-02-28 dropped on load and asserted absent. Writes features.parquet (scratch), predict_cells.csv,
predict_terciles.csv, predict_asym.csv, predict_out.txt. Usage: python predict.py <scratch>.
Educational only - not financial advice."""
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
S = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "research/history2y"))
from lib import load_context, months, regimes  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
LOCK = ("2024-11-01", "2025-02-28")
TZ = "America/New_York"
CHECK = {1000: 600, 1015: 615, 1030: 630, 1100: 660}          # checkpoint tod -> minute of day
FEATS = ["fo", "gap", "gapstate", "rpos", "vwap", "breadth", "breadth_open", "drive", "drive_cont", "prev1", "prev5",
         "vxx_fo", "comp"]
N_CELLS = 3 * 4 * 13 * 2
BAR = max(1.5, math.sqrt(2 * math.log(N_CELLS)))


def bars(sym):
    b = pd.read_parquet(ROOT / "data/cache_hist/1Min" / f"{sym}.parquet", columns=["open", "high", "low", "close", "volume"])
    ix = pd.to_datetime(b.index)
    b.index = ix.tz_convert(TZ) if ix.tz is not None else ix.tz_localize(TZ)
    d = b.index.strftime("%Y-%m-%d")
    b = b[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    m = b.index.hour * 60 + b.index.minute
    b = b[(m >= 570) & (m < 960)].copy()
    b["day"] = b.index.strftime("%Y-%m-%d")
    b["m"] = b.index.hour * 60 + b.index.minute
    assert not ((b.day >= LOCK[0]) & (b.day <= LOCK[1])).any()
    return b


def day_table(sym):
    b = bars(sym)
    rows = []
    for day, g in b.groupby("day"):
        if g.m.iloc[0] != 570 or g.m.iloc[-1] < 955:          # need the 09:30 bar; drop half days
            continue
        mm = g.m.to_numpy()
        c = pd.Series(g.close.to_numpy(), index=mm)
        o = float(g.open.iloc[0])
        tp = ((g.high + g.low + g.close) / 3 * g.volume).cumsum().to_numpy() / g.volume.cumsum().replace(0, np.nan).to_numpy()
        hi, lo = np.maximum.accumulate(g.high.to_numpy()), np.minimum.accumulate(g.low.to_numpy())
        close = float(g.close.iloc[-1])
        def at(minute):                                       # last bar starting before `minute` (closes by `minute`)
            k = np.searchsorted(mm, minute) - 1
            return k if k >= 0 else None
        r = dict(date=day, open=o, close=close)
        k45 = at(585); r["p0945"] = float(c.iloc[k45])
        k12 = at(720); r["p1200"] = float(c.iloc[k12])
        for C, M in CHECK.items():
            k = at(M)
            p = float(c.iloc[k])
            r[f"p{C}"] = p
            r[f"vw{C}"] = tp[k]
            r[f"hi{C}"], r[f"lo{C}"] = hi[k], lo[k]
            r[f"dhi{C}"] = float(g.high.iloc[:k + 1].max())
        rows.append(r)
    D = pd.DataFrame(rows)
    D["dt"] = pd.to_datetime(D.date)
    gapd = D.dt.diff().dt.days
    D["prevc"] = np.where(gapd <= 4, D.close.shift(1), np.nan)               # never bridge the locked block
    span5 = (D.dt - D.dt.shift(6)).dt.days
    D["prev1"] = np.where(gapd.shift(1) <= 4, D.close.shift(1) / D.close.shift(2) - 1, np.nan) * 100
    D.loc[gapd > 4, "prev1"] = np.nan
    D["prev5"] = np.where(span5 <= 10, D.close.shift(1) / D.close.shift(6) - 1, np.nan) * 100
    return D


def build():
    tabs = {s: day_table(s) for s in ("SPY", "QQQ", "IWM", "VXX")}
    ctx = pd.concat([load_context(m) for m in months()], ignore_index=True)
    ctx["date"] = ctx.date.astype(str)
    assert not ((ctx.date >= LOCK[0]) & (ctx.date <= LOCK[1])).any()
    V = tabs["VXX"].set_index("date")
    out = []
    for sym in ("SPY", "QQQ", "IWM"):
        D = tabs[sym]
        for C in CHECK:
            p = D[f"p{C}"]
            f = pd.DataFrame({"date": D.date, "sym": sym, "C": C})
            f["fo"] = (p / D.open - 1) * 100
            f["gap"] = (D.open / D.prevc - 1) * 100
            filled = np.where(D.open > D.prevc, D[f"lo{C}"] <= D.prevc, D[f"hi{C}"] >= D.prevc)
            f["gapstate"] = np.where(f.gap.abs() < 0.10, 0, np.where(filled, -np.sign(f.gap), np.sign(f.gap)))
            f.loc[f.gap.isna(), "gapstate"] = np.nan
            rng = D[f"hi{C}"] - D[f"lo{C}"]
            f["rpos"] = np.where(rng > 0, (p - D[f"lo{C}"]) / rng - 0.5, 0.0)
            f["vwap"] = (p / D[f"vw{C}"] - 1) * 100
            cx = ctx[ctx.tod == C].set_index("date")
            f["breadth"] = D.date.map(cx.breadth).to_numpy() - 0.5
            f["breadth_open"] = D.date.map(cx.breadth_open).to_numpy() - 0.5
            f["drive"] = (D.p0945 / D.open - 1) * 100
            leg = np.sign(p / D.p0945 - 1)
            f["drive_cont"] = leg.to_numpy() if C > 945 else 0.0     # sign of the post-09:45 leg (cont if == sign(drive))
            f["drive_isrev"] = (np.sign(f.drive) * leg < 0).astype(float)
            f["prev1"], f["prev5"] = D.prev1, D.prev5
            vx = D.date.map(V[f"p{C}"] / V["open"] - 1).to_numpy() * 100
            f["vxx_fo"] = -vx
            f["comp"] = (np.sign(f.fo) + np.sign(f.vwap) + np.sign(f.breadth) + np.sign(f.rpos)) / 4
            f["ROD"] = (D.close / p - 1) * 100
            f["AFT"] = (D.close / D.p1200 - 1) * 100
            f["OC"] = (D.close / D.open - 1) * 100
            out.append(f)
    F = pd.concat(out, ignore_index=True)
    assert not ((F.date >= LOCK[0]) & (F.date <= LOCK[1])).any()
    F["split"] = np.where(F.date <= "2025-12-31", "train", "valid")
    rg = regimes().reset_index(); rg["date"] = rg["date"].astype(str)
    F = F.merge(rg[["date", "regime"]], on="date", how="left")
    F.to_parquet(S / "features.parquet", index=False)
    return F


def corr_t(r, n):
    return r * math.sqrt(max(n - 2, 1)) / math.sqrt(max(1 - r * r, 1e-12))


if __name__ == "__main__":
    F = build()
    out = []
    P = lambda *x: out.append(" ".join(str(y) for y in x))
    P(f"days per split (SPY, C=1000): {F[(F.sym == 'SPY') & (F.C == 1000)].split.value_counts().to_dict()}; "
      f"range {F.date.min()}..{F.date.max()}; cells {N_CELLS}, bar {BAR:.2f}")
    cells, terc = [], []
    for (sym, C), g0 in F.groupby(["sym", "C"]):
        for feat in FEATS:
            for tgt in ("ROD", "AFT"):
                tr = g0[g0.split == "train"].dropna(subset=[feat, tgt])
                cuts = np.nanquantile(tr[feat], [1 / 3, 2 / 3]) if tr[feat].nunique() > 3 else None
                for sp in ("train", "valid"):
                    g = g0[g0.split == sp].dropna(subset=[feat, tgt])
                    x, y = g[feat].to_numpy(float), g[tgt].to_numpy(float)
                    n = len(g)
                    r = np.corrcoef(x, y)[0, 1] if n > 3 and x.std() > 0 else np.nan
                    rs = pd.Series(x).rank().corr(pd.Series(y).rank()) if n > 3 else np.nan
                    nz = x != 0
                    hit = (np.sign(x[nz]) == np.sign(y[nz])).mean() if nz.any() else np.nan
                    up = (y > 0).mean()
                    trup = (tr[tgt] > 0).mean()
                    base_major = up if trup >= 0.5 else 1 - up
                    # P&L of trading the index in the feature's sign for the target window (bp/day, no costs; descriptive)
                    pnl = np.sign(x) * y * 100
                    cells.append(dict(sym=sym, C=C, feature=feat, target=tgt, split=sp, n=n, n_signal=int(nz.sum()),
                                      pearson=round(r, 4), t=round(corr_t(r, n), 2) if r == r else np.nan, spearman=round(rs, 4),
                                      hit=round(hit, 4), hit_se=round(math.sqrt(hit * (1 - hit) / max(nz.sum(), 1)), 4),
                                      base_always_long=round(up, 4), base_train_majority=round(base_major, 4),
                                      sign_bp=round(pnl.mean(), 2), sign_bp_t=round(pnl.mean() / (pnl.std(ddof=1) / math.sqrt(n)), 2) if n > 2 else np.nan))
                    if cuts is not None:
                        lab = np.digitize(x, cuts)
                        for k, nm in enumerate(("low", "mid", "high")):
                            yy = y[lab == k] * 100
                            if len(yy) > 2:
                                se = yy.std(ddof=1) / math.sqrt(len(yy))
                                terc.append(dict(sym=sym, C=C, feature=feat, target=tgt, split=sp, tercile=nm, n=len(yy),
                                                 mean_bp=round(yy.mean(), 2), ci_lo=round(yy.mean() - 1.96 * se, 2),
                                                 ci_hi=round(yy.mean() + 1.96 * se, 2)))
    Cz = pd.DataFrame(cells); Tz = pd.DataFrame(terc)
    Cz.to_csv(OUT / "predict_cells.csv", index=False); Tz.to_csv(OUT / "predict_terciles.csv", index=False)
    # asymmetry: continuation rate of the from-open move into the rest of day
    asy = []
    for (sym, C, sp), g in F.groupby(["sym", "C", "split"]):
        for side, m in (("fo>0", g.fo > 0), ("fo<0", g.fo < 0)):
            for lo, hi in ((0, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 99)):
                mm = m & (g.fo.abs() >= lo) & (g.fo.abs() < hi)
                y = g.ROD[mm]; s = np.sign(g.fo[mm])
                if len(y) == 0:
                    continue
                cont = (np.sign(y) == s).mean()
                v = (s * y * 100)
                asy.append(dict(sym=sym, C=C, split=sp, side=side, absfo=f"{lo}-{hi}", n=len(y), cont_rate=round(cont, 3),
                                cont_bp=round(v.mean(), 1), cont_bp_se=round(v.std(ddof=1) / math.sqrt(len(v)), 1) if len(v) > 2 else np.nan))
        for reg in ("up", "flat", "down"):
            gg = g[g.regime == reg]
            asy.append(dict(sym=sym, C=C, split=sp, side=f"regime={reg} (hindsight)", absfo="all", n=len(gg),
                            cont_rate=round((np.sign(gg.ROD) == np.sign(gg.fo)).mean(), 3),
                            cont_bp=round((np.sign(gg.fo) * gg.ROD * 100).mean(), 1), cont_bp_se=np.nan))
        # opening drive continuation vs reversal at C
        for st, m in (("drive continued by C", g.drive_isrev == 0), ("drive reversed by C", g.drive_isrev == 1)):
            gg = g[m]
            asy.append(dict(sym=sym, C=C, split=sp, side=st, absfo="all", n=len(gg),
                            cont_rate=round((np.sign(gg.ROD) == np.sign(gg.fo)).mean(), 3),
                            cont_bp=round((np.sign(gg.fo) * gg.ROD * 100).mean(), 1),
                            cont_bp_se=round((np.sign(gg.fo) * gg.ROD * 100).std(ddof=1) / math.sqrt(max(len(gg), 2)), 1)))
    Az = pd.DataFrame(asy); Az.to_csv(OUT / "predict_asym.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 2000)
    key = Cz[Cz.feature.isin(["fo", "vwap", "breadth", "comp", "rpos", "gapstate", "vxx_fo", "prev1"])]
    P("\n== key cells (ROD) ==")
    P(key[key.target == "ROD"].pivot_table(index=["sym", "feature", "C"], columns="split", values=["pearson", "t", "hit", "sign_bp"]).round(3).to_string())
    P("\n== key cells (AFT) ==")
    P(key[key.target == "AFT"].pivot_table(index=["sym", "feature", "C"], columns="split", values=["pearson", "t", "hit", "sign_bp"]).round(3).to_string())
    big = Cz[(Cz.t.abs() >= BAR)]
    P(f"\n== cells with |t| >= {BAR:.2f} ==\n" + big.to_string(index=False))
    both = Cz.pivot_table(index=["sym", "C", "feature", "target"], columns="split", values="t")
    P("\n== same-sign t >= 2 in both train and valid ==\n" + both[((both.train >= 2) & (both.valid >= 2)) | ((both.train <= -2) & (both.valid <= -2))].round(2).to_string())
    P("\n== asymmetry (QQQ/SPY, fo buckets) ==")
    P(Az[Az.sym.isin(["SPY", "QQQ"])].to_string(index=False))
    open(OUT / "predict_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
    print("\n".join(out[:3]))
