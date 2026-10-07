"""Steps 2-4: green-then-red days, portfolio rules (train -> valid), entry features of good vs bad stretches,
30-minute time-of-day expectancy per setup. Production costs are already inside every trade and every forced
flatten (1c + 1 bps per side, 3c on extended-tier names; forced flattens pay market slippage).
Train = 2026-07-15..08-25, valid = 2026-08-26..09-15. Educational only - not financial advice."""
import itertools
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
OUT = "research/primitives/winning_periods/"
tr = pd.read_csv(OUT + "trades_enriched.csv")
mark = np.load(OUT + "minute_marks.npy").astype(float)
fav = np.load(OUT + "minute_fav_r.npy").astype(float)
for c in ("signal_time", "entry_time", "exit_time"):
    tr[c] = pd.to_datetime(tr[c], utc=True).dt.tz_convert("America/New_York")
tr["date"] = pd.to_datetime(tr["date"]).dt.date
VALID0 = pd.Timestamp("2026-08-26").date()
tr["split"] = np.where(tr.date >= VALID0, "valid", "train")
mi = lambda ts: ts.dt.hour * 60 + ts.dt.minute - 570  # noqa: E731
tr["m0"], tr["m1"] = mi(tr.entry_time), mi(tr.exit_time)
tr["risk_usd"] = (tr.entry - tr.stop).abs() * tr.shares
NMIN = mark.shape[1]
days = sorted(tr.date.unique())
idx_by_day = {d: tr.index[tr.date == d].to_numpy() for d in days}
res = {"n_trades": int(len(tr)), "n_days": len(days),
       "train_days": int(sum(d < VALID0 for d in days)), "valid_days": int(sum(d >= VALID0 for d in days))}


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else np.nan


# ---------------------------------------------------------------- 1. day shape
path = {d: np.nansum(mark[idx_by_day[d]], axis=0) for d in days}
dd = []
for d in days:
    p = path[d]
    k = int(np.argmax(p))
    dd.append(dict(date=str(d), split="valid" if d >= VALID0 else "train", close=p[-1], peak=p.max(), peak_min=k,
                   peak_time=f"{(570 + k) // 60:02d}:{(570 + k) % 60:02d}", trough=p.min(),
                   n=len(idx_by_day[d])))
dd = pd.DataFrame(dd)
dd.to_csv(OUT + "day_summary.csv", index=False)
shape = {}
for thr in (0, 50, 100, 200):
    g = dd[dd.peak > thr]
    shape[f"peak_gt_{thr}"] = dict(days=int(len(g)), ended_red=int((g.close < 0).sum()),
                                   share_ended_red=round(float((g.close < 0).mean()), 3) if len(g) else None,
                                   mean_giveback=round(float((g.peak - g.close).mean()), 1) if len(g) else None)
shape["all_days"] = dict(days=len(dd), green_close=int((dd.close > 0).sum()), total=round(float(dd.close.sum()), 1),
                         mean=round(float(dd.close.mean()), 1), mean_peak=round(float(dd.peak.mean()), 1),
                         median_peak_time=str(dd.peak_time.sort_values().iloc[len(dd) // 2]),
                         hindsight_sum_of_peaks=round(float(dd.peak.clip(lower=0).sum()), 1))
res["day_shape"] = shape


# ---------------------------------------------------------------- 2. portfolio rules
def apply_rule(d, rule):
    """Return day P/L under the rule. Triggers are read on the minute-close marked path (everything that the rule
    has not changed before the trigger is identical, so the trigger is causal); the flatten fills at the NEXT
    minute's marked price (market exit, slippage in)."""
    ix = idx_by_day[d]
    sub = tr.loc[ix]
    m = mark[ix]
    kind = rule[0]
    if kind in ("lock", "giveback", "nonew", "loss", "lock_r"):
        p = np.nansum(m, axis=0)
        pk = np.maximum.accumulate(p)
        if kind == "lock":
            hit = np.flatnonzero(p >= rule[1])
        elif kind == "lock_r":     # lock in units of the day's average risk per trade (R)
            hit = np.flatnonzero(p >= rule[1] * sub.risk_usd.mean())
        elif kind == "giveback":
            hit = np.flatnonzero((pk >= rule[1]) & (p <= pk * (1 - rule[2])))
        elif kind == "nonew":
            hit = np.flatnonzero(p >= rule[1])
        else:
            hit = np.flatnonzero(p <= -rule[1])
        if not len(hit):
            return float(sub.pnl.sum())
        k = int(hit[0])
        out = 0.0
        for j, (_, r) in enumerate(sub.iterrows()):
            if r.m0 > k:                                     # not yet entered: skipped
                continue
            if kind == "nonew" or r.m1 <= k + 1:             # already closed (or rule only blocks new entries)
                out += r.pnl
            else:
                out += m[j, min(k + 1, NMIN - 1)]
        return out
    if kind == "timestop":     # per trade: at entry+N minutes, exit at market if MFE so far < q R
        N, q = rule[1], rule[2]
        out = 0.0
        for j, (_, r) in enumerate(sub.iterrows()):
            k = r.m0 + N
            if r.m1 <= k or k >= NMIN - 1:
                out += r.pnl
                continue
            mf = np.nanmax(fav[ix[j], r.m0:k + 1]) if np.isfinite(fav[ix[j], r.m0:k + 1]).any() else 0
            out += m[j, k + 1] if mf < q else r.pnl
        return out
    if kind == "clock":        # no new entries after HH:MM (open trades run)
        return float(sub.loc[sub.m0 < rule[1], "pnl"].sum())
    if kind == "cold":         # stop a setup for the day once its CLOSED trades sum <= -K R
        K = rule[1]
        out = 0.0
        for s, g in sub.groupby("strategy"):
            g = g.sort_values("m0")
            for _, r in g.iterrows():
                closed = g[(g.m1 <= r.m0)]
                if closed.r_multiple.sum() <= -K:
                    continue
                out += r.pnl
        return out
    if kind == "hot":          # stop a setup for the day once its CLOSED trades sum >= +K R (bank the good stretch)
        K = rule[1]
        out = 0.0
        for s, g in sub.groupby("strategy"):
            g = g.sort_values("m0")
            for _, r in g.iterrows():
                closed = g[(g.m1 <= r.m0)]
                if closed.r_multiple.sum() >= K:
                    continue
                out += r.pnl
        return out
    raise ValueError(kind)


grid = []
for X in (50, 100, 150, 200, 300, 400, 600):
    grid += [("lock", X), ("nonew", X)]
for X in (1, 2, 3, 4, 6, 8):
    grid.append(("lock_r", X))
for A, G in itertools.product((50, 100, 200, 300), (0.3, 0.5, 0.7)):
    grid.append(("giveback", A, G))
for L in (100, 200, 300, 500, 800):
    grid.append(("loss", L))
for N, q in itertools.product((15, 30, 45, 60, 90, 120), (0.25, 0.5)):
    grid.append(("timestop", N, q))
for hh in (60, 90, 120, 150, 180, 210, 240):
    grid.append(("clock", hh))
for K in (2, 3, 4, 6):
    grid += [("cold", K), ("hot", K)]

base = {d: float(tr.loc[idx_by_day[d], "pnl"].sum()) for d in days}
rows = []
for rule in grid:
    diff = {d: apply_rule(d, rule) - base[d] for d in days}
    tr_d = [diff[d] for d in days if d < VALID0]
    va_d = [diff[d] for d in days if d >= VALID0]
    rows.append(dict(rule="-".join(map(str, rule)), kind=rule[0],
                     train_gain=round(sum(tr_d), 1), train_gain_per_day=round(np.mean(tr_d), 2), train_t=round(tstat(tr_d), 2),
                     train_days_helped=int(sum(x > 0 for x in tr_d)), train_days_hurt=int(sum(x < 0 for x in tr_d)),
                     valid_gain=round(sum(va_d), 1), valid_gain_per_day=round(np.mean(va_d), 2), valid_t=round(tstat(va_d), 2),
                     valid_days_helped=int(sum(x > 0 for x in va_d)), valid_days_hurt=int(sum(x < 0 for x in va_d)),
                     ex_best_day_valid=round(sum(va_d) - max(va_d), 1)))
rules = pd.DataFrame(rows)
rules.to_csv(OUT + "rules_grid.csv", index=False)
res["rules_tried"] = len(grid)
res["base"] = dict(train=round(sum(base[d] for d in days if d < VALID0), 1),
                   valid=round(sum(base[d] for d in days if d >= VALID0), 1))


# per-setup time windows (30 min) - same rule family, chosen on train only
def win30(m):
    return (m // 30)


tr["w30"] = win30(tr.m0)
tod = tr.groupby(["strategy", "split", "w30"]).agg(n=("r_multiple", "size"), exp_r=("r_multiple", "mean"),
                                                   pnl=("pnl", "sum")).reset_index()
tod["window"] = tod.w30.map(lambda w: f"{(570 + 30 * w) // 60:02d}:{(570 + 30 * w) % 60:02d}")
# day-clustered t per strategy x window (train+valid pooled and per split)
tt = []
for (s, w), g in tr.groupby(["strategy", "w30"]):
    for sp, gg in [("all", g)] + list(g.groupby("split")):
        dsum = gg.groupby("date").r_multiple.sum()
        dn = gg.groupby("date").size()
        mu = gg.r_multiple.mean()
        se = np.sqrt(((dsum - dn * mu) ** 2).sum()) / len(gg)
        tt.append(dict(strategy=s, window=f"{(570 + 30 * w) // 60:02d}:{(570 + 30 * w) % 60:02d}", split=sp,
                       n=len(gg), days=len(dsum), exp_r=round(mu, 3), t_day=round(mu / se, 2) if se > 0 else None,
                       pnl=round(gg.pnl.sum(), 1)))
tt = pd.DataFrame(tt)
tt.to_csv(OUT + "tod_by_setup.csv", index=False)
# drop setup-window cells with train exp_r < 0 AND train n >= 20; score on valid
trw = tt[(tt.split == "train")]
drop = trw[(trw.exp_r < 0) & (trw.n >= 20)][["strategy", "window"]]
keyset = set(map(tuple, drop.values))
tr["window"] = tr.w30.map(lambda w: f"{(570 + 30 * w) // 60:02d}:{(570 + 30 * w) % 60:02d}")
dropped = tr[[(s, w) in keyset for s, w in zip(tr.strategy, tr.window)]]
res["window_rule"] = dict(cells_dropped=sorted(map(list, keyset)),
                          train_pnl_removed=round(float(dropped[dropped.split == "train"].pnl.sum()), 1),
                          valid_pnl_removed=round(float(dropped[dropped.split == "valid"].pnl.sum()), 1),
                          valid_n_removed=int((dropped.split == "valid").sum()),
                          valid_exp_r_removed=round(float(dropped[dropped.split == "valid"].r_multiple.mean()), 3)
                          if (dropped.split == "valid").any() else None)

# ---------------------------------------------------------------- per-setup summary + MFE/MAE profile
ss = []
for (s, sp), g in tr.groupby(["strategy", "split"]):
    dsum = g.groupby("date").r_multiple.sum()
    dn = g.groupby("date").size()
    mu = g.r_multiple.mean()
    se = np.sqrt(((dsum - dn * mu) ** 2).sum()) / len(g)
    best = dsum.idxmax()
    ss.append(dict(strategy=s, split=sp, n=len(g), days=len(dsum), exp_r=round(mu, 3), t_day=round(mu / se, 2) if se > 0 else None,
                   win=round(float((g.r_multiple > 0).mean()), 3), pnl=round(g.pnl.sum(), 1),
                   green_days=round(float((dsum > 0).mean()), 3),
                   ex_best_day=round(float((dsum.sum() - dsum[best]) / max(1, len(g) - dn[best])), 3),
                   mfe_med=round(g.mfe_r.median(), 2), mae_med=round(g.mae_r.median(), 2),
                   never_worked_share=round(float((g.mfe_r < 0.25).mean()), 3),
                   never_worked_r=round(float(g.loc[g.mfe_r < 0.25, "r_multiple"].sum()), 1),
                   reached_1r_then_red=int(((g.mfe_r >= 0.75) & (g.r_multiple < 0)).sum()),
                   ttm_med_min=round(g.time_to_mfe_min.median(), 1), hold_med_min=round(g.hold_min.median(), 1)))
pd.DataFrame(ss).to_csv(OUT + "setup_summary.csv", index=False)

# ---------------------------------------------------------------- 3. entry features: good vs bad stretches
pk = dd.set_index("date")
tr["peak_min"] = tr.date.astype(str).map(pk.peak_min)
tr["day_peak"] = tr.date.astype(str).map(pk.peak)
tr["stretch"] = np.where((tr.day_peak > 0) & (tr.m0 <= tr.peak_min), "before_peak",
                         np.where(tr.m0 > tr.peak_min, "after_peak", "other"))
# portfolio P/L at entry (the easiest live metric)
tr["port_pnl_at_entry"] = [float(path[d][max(0, m - 1)]) for d, m in zip(tr.date, tr.m0)]
tr["setup_closed_r_at_entry"] = 0.0
for (d, s), g in tr.groupby(["date", "strategy"]):
    for i, r in g.iterrows():
        tr.loc[i, "setup_closed_r_at_entry"] = g.loc[g.m1 <= r.m0, "r_multiple"].sum()
tr["open_same_side_at_entry"] = 0
for d, ix in idx_by_day.items():
    g = tr.loc[ix]
    for i, r in g.iterrows():
        tr.loc[i, "open_same_side_at_entry"] = int(((g.m0 < r.m0) & (g.m1 > r.m0) & (g.side == r.side)).sum())

FEATS = ["rsi", "rsi5", "momentum", "vwapDistPct", "fromOpen", "gap", "volumeRatio", "atrPct", "heat",
         "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct", "sma20_slope_pct", "flow3", "pricePosition", "buyPressure"]
cols = ["symbol", "date", "tod"] + FEATS
lab = pd.concat([pd.read_parquet(f"research/setups2/data/{s}.parquet", columns=cols) for s in ("train", "valid")])
lab["date"] = pd.to_datetime(lab["date"]).dt.date
# market context per (date, tod): breadth = share of the universe above its open; median move from open
mkt = lab.groupby(["date", "tod"]).agg(breadth=("fromOpen", lambda x: float((x > 0).mean())),
                                        mkt_fromopen=("fromOpen", "median"),
                                        mkt_vwap=("vwapDistPct", "median")).reset_index()
lab = lab[lab.symbol.isin(set(tr.symbol))]
st = tr.signal_time - pd.Timedelta(minutes=0)
tr["tod"] = (st.dt.hour * 100 + (st.dt.minute // 5) * 5).astype(int)
tr = tr.merge(lab, on=["symbol", "date", "tod"], how="left").merge(mkt, on=["date", "tod"], how="left")
tr["mkt_with_side"] = tr.side * tr.mkt_fromopen          # >0 = the market is moving the trade's way
tr["breadth_with_side"] = np.where(tr.side == 1, tr.breadth, 1 - tr.breadth)
tr.to_csv(OUT + "trades_with_features.csv", index=False)
res["feature_join_rate"] = round(float(tr.heat.notna().mean()), 3)

ALLF = FEATS + ["breadth_with_side", "mkt_with_side", "port_pnl_at_entry", "setup_closed_r_at_entry",
                "open_same_side_at_entry", "m0"]
fx = []
for s, g in tr[tr.split == "train"].groupby("strategy"):
    a, b = g[g.stretch == "before_peak"], g[g.stretch == "after_peak"]
    for f in ALLF:
        x = g[f].astype(float)
        if x.notna().sum() < 30:
            continue
        sd = x.std()
        # rank correlation of the feature (signed by side for directional ones) with the realised R
        rho = g[[f, "r_multiple"]].astype(float).corr(method="spearman").iloc[0, 1]
        fx.append(dict(strategy=s, feature=f, before_peak_mean=round(a[f].mean(), 3), after_peak_mean=round(b[f].mean(), 3),
                       std_diff=round((a[f].mean() - b[f].mean()) / sd, 2) if sd > 0 else None,
                       spearman_with_r=round(rho, 3), n_before=len(a), n_after=len(b)))
fx = pd.DataFrame(fx)
fx.to_csv(OUT + "features_good_vs_bad.csv", index=False)

# quintile check (train -> valid) for the top features per setup by |spearman|
qx = []
for s, g in tr.groupby("strategy"):
    gt = g[g.split == "train"]
    for f in ALLF:
        if gt[f].notna().sum() < 100:
            continue
        try:
            edges = np.unique(np.nanquantile(gt[f].astype(float), [0, .2, .4, .6, .8, 1]))
        except Exception:
            continue
        if len(edges) < 4:
            continue
        for sp, gg in g.groupby("split"):
            q = pd.cut(gg[f].astype(float), edges, include_lowest=True, labels=False)
            for qq, h in gg.groupby(q):
                qx.append(dict(strategy=s, feature=f, split=sp, quintile=int(qq), n=len(h), exp_r=round(h.r_multiple.mean(), 3),
                               lo=round(edges[int(qq)], 3), hi=round(edges[int(qq) + 1], 3)))
pd.DataFrame(qx).to_csv(OUT + "feature_quintiles.csv", index=False)
json.dump(res, open(OUT + "results.json", "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
