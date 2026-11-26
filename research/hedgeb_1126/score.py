"""HEDGE-B scoring (PREREG.md metrics + memo A pass bar). Usage: python score.py W. Writes results.csv, daytype.csv,
per_setup.csv next to this file. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); H = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28")
CTXS = ["P4_LO", "P4_BASE", "L3OUT_LO", "L3OUT_BASE"]
SH = ["L3", "RW3", "RW5", "NM-ETF"]


def load(ctx, book, cfg):
    x = pd.read_parquet(W / f"day_{ctx}_{book}_{cfg}.parquet")
    assert not ((x.date >= LOCK[0]) & (x.date <= LOCK[1])).any()
    return x.fillna({c: 0.0 for c in x.columns if c[:1] in ("H", "P")})


def series(x, cfg):
    return x.R + x[f"{cfg}_g"] - x[f"{cfg}_c"] if cfg in ("H8", "H4") else x.R


def stats(r, ref, x, cfg):
    n = len(r); yrs = n / 252; d = r - ref
    w5 = np.sort(r.to_numpy())[:5]; w5r = np.sort(ref.to_numpy())[:5]
    out = dict(n=n, avg=r.mean(), red=(r < -1e-9).mean() * 100, red_mo=(r < -1e-9).mean() * 21, w5=w5.mean(), w5sum=w5.sum(),
               le10=int((r <= -10).sum()), floor20=r.rolling(20).sum().min(), tot=r.sum(), dRyr=d.sum() / yrs,
               w5imp=(w5.mean() - w5r.mean()) / abs(w5r.mean()),
               le10cut=1 - (r <= -10).sum() / max((ref <= -10).sum(), 1))
    deep = ref <= -10
    ds = d[deep].sum()
    out["deep_dR"] = ds; out["deep_best_share"] = d[deep].max() / ds if ds > 0 else np.nan
    if cfg in ("H8", "H4"):
        g, c = x[f"{cfg}_g"], x[f"{cfg}_c"]
        out.update(hg_yr=g.sum() / yrs, hc_yr=c.sum() / yrs, hnet_yr=(g - c).sum() / yrs, hg_mean=g.mean(),
                   hg_se=g.std(ddof=1) / np.sqrt(n), nreb=x[f"{cfg}_nreb"].mean(), tr_sess=x[f"{cfg}_tr"].mean(),
                   pkv_p95=x[f"{cfg}_pkv"].quantile(0.95), pkg_p95=x[f"{cfg}_pkg"].quantile(0.95))
        if "PL0" in x:
            pl = [(np.sort((ref + x[f"PL{j}"]).to_numpy())[:5].mean() - w5r.mean()) / abs(w5r.mean()) for j in range(20)]
            out["plac_p90"] = float(np.percentile(pl, 90)); out["plac_med"] = float(np.median(pl))
    return out


rows, dts, pss = [], [], []
for ctx in CTXS:
    for book in ("RAW", "Z", "P"):
        ref = load(ctx, book, "REF")
        b8 = load(ctx, book, "B8") if book != "P" else None
        for cfg in ("REF", "H8", "H4", "B8"):
            if cfg == "B8" and b8 is None:
                continue
            x = b8 if cfg == "B8" else ref
            for per in ("FIT", "CHECK", "T2"):
                m = ref.per == per
                r = series(x[x.per == per].reset_index(drop=True), cfg); rr = ref[m].R.reset_index(drop=True)
                rows.append(dict(ctx=ctx, book=book, cfg=cfg, per=per, **stats(r, rr, x[x.per == per].reset_index(drop=True), cfg)))
                if cfg in ("H8", "H4"):
                    xx = ref[m]
                    dt = np.where(xx.spy_oc > 0.005, "up", np.where(xx.spy_oc < -0.005, "down", "quiet"))
                    dd = (xx[f"{cfg}_g"] - xx[f"{cfg}_c"]).to_numpy()
                    for t in ("up", "quiet", "down"):
                        k = dt == t
                        dts.append(dict(ctx=ctx, book=book, cfg=cfg, per=per, type=t, days=int(k.sum()), dR_day=dd[k].mean(),
                                        ref_day=xx.R.to_numpy()[k].mean()))
        for cfg in ("H8", "H4"):
            pss.append(dict(ctx=ctx, book=book, cfg=cfg, **{SH[s]: ref[f"{cfg}_a{s}"].sum() for s in range(4)}))
R = pd.DataFrame(rows); R.to_csv(H / "results.csv", index=False)
D = pd.DataFrame(dts); D.to_csv(H / "daytype.csv", index=False)
P = pd.DataFrame(pss); P.to_csv(H / "per_setup.csv", index=False)

LV = pd.read_csv(H / "live_days.csv")


def live_check(ctx, cfg):
    ln, lat = ctx.split("_")
    x = LV[(LV.lineup == ln) & (LV.book == "RAW") & (LV.lo == (lat == "LO"))]
    c = x.R + x[f"{cfg}_g"] - x[f"{cfg}_c"]
    return c.nsmallest(5).mean() > x.R.nsmallest(5).mean(), (x.R - c).max()


def verdict(ctx, cfg):
    g = R[(R.ctx == ctx) & (R.cfg == cfg)].set_index(["book", "per"])
    items = {}
    for per in ("CHECK", "T2"):
        z, p = g.loc[("Z", per)], g.loc[("P", per)]
        pref = R[(R.ctx == ctx) & (R.cfg == "REF") & (R.book == "P") & (R.per == per)].iloc[0]
        items[f"1{per}"] = z.w5imp >= 0.30 and z.le10cut >= 0.40
        items[f"2{per}"] = z.dRyr >= -15
        items[f"3{per}"] = p.dRyr >= -15 and p.red - pref.red <= 2
        items[f"4{per}"] = z.w5imp > z.plac_p90 and abs(z.hg_mean) <= z.hg_se
        items[f"5{per}"] = bool(z.deep_best_share < 0.5) if not np.isnan(z.deep_best_share) else False
    ok, worst = live_check(ctx, cfg)
    items["6live"] = ok and worst <= 3
    return items


pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
cols = ["ctx", "book", "cfg", "per", "n", "avg", "red", "red_mo", "w5", "w5sum", "le10", "floor20", "dRyr", "w5imp", "le10cut",
        "deep_best_share", "hg_yr", "hc_yr", "hnet_yr", "hg_mean", "hg_se", "nreb", "tr_sess", "pkg_p95", "plac_p90", "plac_med"]
print(R[cols].round(3).to_string(index=False))
print(D.round(2).to_string(index=False))
print(P.round(1).to_string(index=False))
for (ln, bk, lo), x in LV.groupby(["lineup", "book", "lo"]):
    out = [ln, bk, "LO" if lo else "BASE", len(x), round(x.R.mean(), 2), round((x.R < 0).mean() * 100), round(x.R.nsmallest(5).mean(), 1),
           int((x.R <= -10).sum())]
    for cfg in ("H8", "H4"):
        c = x.R + x[f"{cfg}_g"] - x[f"{cfg}_c"]
        out += [cfg, round(c.mean(), 2), round((c < 0).mean() * 100), round(c.nsmallest(5).mean(), 1), int((c <= -10).sum()),
                round((x.R - c).max(), 1), round(x[f"{cfg}_c"].sum(), 1), round(x[f"{cfg}_g"].sum(), 1)]
    print("LIVE", *out)
for ctx in CTXS:
    for cfg in ("H8", "H4"):
        v = verdict(ctx, cfg)
        print("VERDICT", ctx, cfg, "PASS" if all(v.values()) else "FAIL", {k: bool(b) for k, b in v.items()})
