"""Part 0: SPY / QQQ morning dip-then-bounce statistics and 10:00 predictors (descriptive, no configurations).
Outputs: dip_buckets.csv, predictors.csv, dipdays.csv. Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

from common import HERE, SCR, regimes, split_of


def sessions(sym):
    d = pd.read_parquet(SCR / "idx1" / f"{sym}.parquet")
    d["date"] = d.index.date
    m = d.index.hour * 60 + d.index.minute - 570
    d["m"] = m
    rows = []
    for day, g in d.groupby("date"):
        o = g["open"].iloc[0]
        w = g[g.m < 90]
        if len(w) < 30:
            continue
        il = w["low"].to_numpy().argmin()
        low = w["low"].iloc[il]
        lm = int(w["m"].iloc[il])
        aft = g[(g.m > lm) & (g.m < 150)]
        bmax = aft["high"].max() if len(aft) else low
        orr = g[g.m < 15]
        rows.append(dict(date=day, open=o, low=low, low_min=lm, dip=(low / o - 1) * 100,
                         bounce_x=(bmax - low) / (o - low) if o > low else np.nan,
                         close=g["close"].iloc[-1], o2c=(g["close"].iloc[-1] / o - 1) * 100,
                         or_rng=(orr["high"].max() - orr["low"].min()) / o * 100))
    return pd.DataFrame(rows)


def auc(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok].astype(bool)
    if y.sum() < 5 or (~y).sum() < 5:
        return np.nan
    r = pd.Series(x).rank().to_numpy()
    return (r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum())


def main():
    etf = pd.read_parquet(SCR / "etf_rows.parquet")
    etf["date"] = pd.to_datetime(etf["date"]).dt.date
    reg = regimes()
    out_b, out_p, dd_all = [], [], []
    idx5 = pd.read_parquet(SCR / "idx5.parquet")
    idx5["date"] = pd.to_datetime(idx5["date"]).dt.date
    ctx = pd.read_parquet(SCR / "ctx.parquet")
    ctx["date"] = pd.to_datetime(ctx["date"]).dt.date
    summ = {}
    for sym in ("SPY", "QQQ"):
        S = sessions(sym)
        a = etf[(etf.symbol == sym)].groupby("date").agg(atr_d=("atr_d", "first"), gap=("gap", "first"), c0=("close", "first"))
        S = S.merge(a, left_on="date", right_index=True, how="left")
        S["atr_pct"] = S["atr_d"] / S["c0"] * 100
        S["dip_atr"] = S["dip"] / S["atr_pct"]
        S["dip_or"] = S["dip"] / S["or_rng"]
        S["split"] = split_of(S["date"])
        S["regime"] = S["date"].map(reg)
        S["early"] = (S.low_min >= 5) & (S.low_min <= 45)        # 09:35..10:15
        S["back_to_open"] = S["bounce_x"] >= 1
        S["sym"] = sym
        dd_all.append(S)
        bins = [-99, -1, -0.5, -0.25, -0.1, 0.01]
        lab = [">1%", "0.5-1%", "0.25-0.5%", "0.1-0.25%", "<0.1%"]
        S["bucket"] = pd.cut(S["dip"], bins, labels=lab)
        for (sp, b), g in S.groupby(["split", "bucket"], observed=True):
            out_b.append(dict(sym=sym, split=sp, bucket=b, sessions=len(g), early_low_share=round(g.early.mean(), 3),
                              back_to_open_by_12=round(g.back_to_open.mean(), 3), med_bounce_x=round(g.bounce_x.median(), 2),
                              close_above_open=round((g.o2c > 0).mean(), 3), med_low_time=int(g.low_min.median())))
        for sp, g in S.groupby("split"):
            e = g[g.early & (g.dip <= -0.1)]
            summ[f"{sym}_{sp}"] = dict(sessions=len(g), early_low_share=round(g.early.mean(), 3),
                                       early_dip_ge010=len(e), early_dip_back_to_open=round(e.back_to_open.mean(), 3),
                                       early_dip_med_bounce_x=round(e.bounce_x.median(), 2),
                                       early_dip_close_above_open=round((e.o2c > 0).mean(), 3),
                                       early_dip_close_above_low_plus_half=round(((e.close - e.low) / (e.open - e.low) >= 0.5).mean(), 3))
        # ---- predictors at 10:00
        X = idx5[idx5.sym == sym].set_index(["date", "tod"])
        I = idx5[idx5.sym == "IWM"].set_index(["date", "tod"])
        Q = idx5[idx5.sym == ("QQQ" if sym == "SPY" else "SPY")].set_index(["date", "tod"])
        rows = []
        dates = sorted(set(S.date))
        vol30 = idx5[(idx5.sym == sym) & (idx5.tod <= 1000)].groupby("date")["v"].sum()
        vavg = vol30.rolling(20, min_periods=10).mean().shift(1)
        cl = idx5[(idx5.sym == sym) & (idx5.tod == 1600)].set_index("date")["c"]
        op = idx5[(idx5.sym == sym) & (idx5.tod == 935)].set_index("date")["open"]
        dl = pd.Series(dates)
        for i, day in enumerate(dates):
            try:
                r10 = X.loc[(day, 1000)]
                r12 = X.loc[(day, 1200)]
            except KeyError:
                continue
            if r10["runmin"] > -0.10:
                continue
            g = X.loc[day]
            low10 = g.loc[:1000, "l"].min()
            after = g.loc[1005:1200]
            Y = int((after["l"].min() > low10) and (r12["c"] > r10["c"]))
            orw = g.loc[:945]
            prev1 = prev5 = np.nan
            if i >= 1 and (pd.Timestamp(day) - pd.Timestamp(dates[i - 1])).days <= 4:
                prev1 = (cl.get(dates[i - 1]) / op.get(dates[i - 1]) - 1) * 100
            if i >= 5 and (pd.Timestamp(day) - pd.Timestamp(dates[i - 5])).days <= 9:
                prev5 = (cl.get(dates[i - 1]) / cl.get(dates[i - 5]) - 1) * 100
            c10 = ctx[(ctx.date == day) & (ctx.tod <= 1000)]
            srow = S[S.date == day].iloc[0]
            rows.append(dict(date=day, Y=Y, ret_10_12=(r12["c"] / r10["c"] - 1) * 100,
                             dip=r10["runmin"], dip_atr=r10["lowfo"] / srow["atr_pct"] if srow["atr_pct"] > 0 else np.nan,
                             recovery=(r10["fo"] - r10["runmin"]) / abs(r10["runmin"]), gap=srow["gap"],
                             vs_vwap=(r10["c"] / r10["vwap"] - 1) * 100,
                             or_pos=(r10["c"] - orw["l"].min()) / max(1e-9, orw["h"].max() - orw["l"].min()),
                             prev1=prev1, prev5=prev5,
                             iwm_minus=I.loc[(day, 1000), "fo"] - r10["fo"] if (day, 1000) in I.index else np.nan,
                             other_minus=Q.loc[(day, 1000), "fo"] - r10["fo"] if (day, 1000) in Q.index else np.nan,
                             breadth=c10["breadth"].iloc[-1] if len(c10) else np.nan,
                             dbreadth=(c10["breadth"].iloc[-1] - c10["breadth"].min()) if len(c10) else np.nan,
                             vol_ratio=vol30.get(day) / vavg.get(day) if vavg.get(day) else np.nan,
                             low_by_0945=int(g.loc[:945, "l"].min() <= low10 + 1e-9)))
        P = pd.DataFrame(rows)
        P["split"] = split_of(P["date"])
        P["regime"] = P["date"].map(reg)
        P.to_csv(HERE / f"predictors_rows_{sym}.csv", index=False)
        feats = ["dip", "dip_atr", "recovery", "gap", "vs_vwap", "or_pos", "prev1", "prev5", "iwm_minus", "other_minus",
                 "breadth", "dbreadth", "vol_ratio", "low_by_0945"]
        for f in feats:
            rec = dict(sym=sym, feature=f)
            for sp in ("train", "valid"):
                g = P[P.split == sp]
                x = g[f].to_numpy(float)
                rec[f"n_{sp}"] = int(np.isfinite(x).sum())
                rec[f"auc_{sp}"] = round(auc(x, g["Y"].to_numpy()), 3)
                rec[f"spearman_ret_{sp}"] = round(pd.Series(x).corr(g["ret_10_12"].reset_index(drop=True), method="spearman"), 3)
                q = pd.qcut(pd.Series(x), 3, labels=False, duplicates="drop") if np.isfinite(x).sum() > 10 else None
                if q is not None:
                    m = g["ret_10_12"].reset_index(drop=True).groupby(q).mean()
                    rec[f"ret_lo_{sp}"] = round(m.iloc[0], 3)
                    rec[f"ret_hi_{sp}"] = round(m.iloc[-1], 3)
                    yy = g["Y"].reset_index(drop=True).groupby(q).mean()
                    rec[f"Y_lo_{sp}"] = round(yy.iloc[0], 3)
                    rec[f"Y_hi_{sp}"] = round(yy.iloc[-1], 3)
            rec["stable"] = bool(np.sign(rec["auc_train"] - 0.5) == np.sign(rec["auc_valid"] - 0.5))
            out_p.append(rec)
        summ[f"{sym}_pred_base"] = {sp: dict(n=int((P.split == sp).sum()), Y=round(P[P.split == sp].Y.mean(), 3),
                                             ret=round(P[P.split == sp].ret_10_12.mean(), 3)) for sp in ("train", "valid")}
    pd.DataFrame(out_b).to_csv(HERE / "dip_buckets.csv", index=False)
    pd.DataFrame(out_p).to_csv(HERE / "predictors.csv", index=False)
    pd.concat(dd_all).to_csv(HERE / "dipdays.csv", index=False)
    json.dump(summ, open(HERE / "dipstats.json", "w"), indent=1, default=str)
    print(json.dumps(summ, indent=1, default=str))
    print(pd.DataFrame(out_b).to_string())
    print(pd.DataFrame(out_p).to_string())


if __name__ == "__main__":
    main()
