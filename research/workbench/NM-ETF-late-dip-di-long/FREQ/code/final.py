"""FREQ final: parent vs WB4 (and the closest alternatives) on both tests; splits, families, paired-by-day, added/removed
trades, per-ETF counts, blocked-signal what-if R. Educational only - not financial advice."""
import sys, json, sqlite3
from sim2 import *
from scipy import stats as st
D = load(); C2, P2, d2 = D["y2"]; RC, RP, dr = D["rep"]
WB4 = {"di": -5.0, "ret3": -0.75, "refire": True, "cool": 1, "lots": 3, "extra": (("ret12", ">=", -1.0),)}
V = {"parent": {}, "WB4": WB4}
T = {(n, k): trades(*D[k][:2], v) for n, v in V.items() for k in ("y2", "rep")}
out = {}
for k, days in (("y2", d2), ("rep", dr)):
    p, w = T[("parent", k)], T[("WB4", k)]
    out[k] = {n: stats(T[(n, k)], len(days)) for n in V}
    a = w.groupby("date").r.sum().reindex(days).fillna(0); b = p.groupby("date").r.sum().reindex(days).fillna(0); dd = a - b
    out[k]["paired"] = dict(mean=round(dd.mean(), 3), t=round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(days))), 2))
    for n in V:
        t = T[(n, k)]; d = t.groupby("date").r.sum()
        out[k][n]["green_days"] = int((d > 0).sum()); out[k][n]["red_days"] = int((d < 0).sum())
        out[k][n]["avgw"] = round(t.r[t.r > 0].mean(), 3); out[k][n]["avgl"] = round(t.r[t.r <= 0].mean(), 3)
        out[k][n]["hold"] = float(np.median([mdiff(x, y) for x, y in zip(t.xt, t.ent)]))
        out[k][n]["gross_avg"] = round(trades(*D[k][:2], {**V[n], "gross": True}).r.mean(), 3)
print(json.dumps(out, indent=1, default=str))
p, w = T[("parent", "y2")], T[("WB4", "y2")]
for n, t in (("parent", p), ("WB4", w)):
    sp = t.groupby(np.where(t.date <= "2025-12-31", "train", "valid")).r.agg(["count", "mean", "sum"]).round(3)
    na = t[~t.date.str.startswith("2025-04")].r
    print(f"\n## {n} split {sp.to_dict()} | w/o Apr-2025 n {len(na)} avg {na.mean():.3f} total {na.sum():.1f}")
    for lab, m in (("inverse", t.symbol.isin(INVERSE)), ("non-inverse", ~t.symbol.isin(INVERSE)), ("3x", t.symbol.isin(LEV3)), ("1x/2x", ~t.symbol.isin(LEV3))):
        print(f"   {lab}: n {m.sum()} avg {t[m].r.mean():.3f} total {t[m].r.sum():.1f}")
    print("   by entry hour", t.groupby(t.tod // 100 * 100 + (t.tod % 100 >= 30) * 30).r.agg(["count", "mean"]).round(3).to_dict())
    print("   exits", t.groupby("why").r.agg(["count", "mean"]).round(3).to_dict())
key = lambda d: set(zip(d.symbol, d.date, d.ent))
kp, kw = key(p), key(w)
keep = w[[x in kp for x in zip(w.symbol, w.date, w.ent)]]; add = w[[x not in kp for x in zip(w.symbol, w.date, w.ent)]]
rem = p[[x not in kw for x in zip(p.symbol, p.date, p.ent)]]
print(f"\n2y: kept {len(keep)} avg {keep.r.mean():.3f} | added {len(add)} avg {add.r.mean():.3f} total {add.r.sum():.1f} | removed {len(rem)} avg {rem.r.mean():.3f} total {rem.r.sum():.1f}")
first = add.merge(p[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="left", indicator=True)
print("   added on a symbol-day the parent also traded (refire / later bar):", (first._merge == "both").sum(), first[first._merge == "both"].r.mean().round(3),
      "| new symbol-days:", (first._merge == "left_only").sum(), first[first._merge == "left_only"].r.mean().round(3))
print("   added vs removed Welch t", round(st.ttest_ind(add.r, rem.r, equal_var=False).statistic, 2))
# per-symbol (remedy rule: how many symbols improve / worsen)
ps = p.groupby("symbol").r.sum(); ws = w.groupby("symbol").r.sum(); j = pd.concat([ps, ws], axis=1, keys=["parent", "WB4"]).fillna(0)
j["d"] = j.WB4 - j.parent
print(f"   per symbol (2y total R): {len(j)} symbols; better {int((j.d > 0.05).sum())}, worse {int((j.d < -0.05).sum())}, same {int((j.d.abs() <= 0.05).sum())}; worst changes", j.d.sort_values().head(5).round(2).to_dict(), "best", j.d.sort_values().tail(5).round(2).to_dict())
cnt = pd.concat([p.groupby("symbol").size(), w.groupby("symbol").size(), p.groupby("symbol").r.mean().round(3), w.groupby("symbol").r.mean().round(3)], axis=1, keys=["par_n", "wb4_n", "par_avg", "wb4_avg"]).fillna(0)
cnt.sort_values("par_n", ascending=False).to_csv(SC + "out/per_etf_2y.csv")
rp, rw = T[("parent", "rep")], T[("WB4", "rep")]
pd.concat([rp.groupby("symbol").size(), rw.groupby("symbol").size()], axis=1, keys=["par_n", "wb4_n"]).fillna(0).to_csv(SC + "out/per_etf_rep.csv")
print("\n2y per-ETF (parent n>0):", (cnt.par_n > 0).sum(), "symbols of", len(SETS["PAR"]), "; top 12:", cnt.sort_values("par_n", ascending=False).head(12).par_n.astype(int).to_dict())
print("replay WB4 trades:\n", rw[["symbol", "date", "tod", "r", "why"]].round(3).to_string())
pd.to_pickle(T, SC + "out/final_trades.pkl")
# blocked / missed signals: replay what-if (net LR8 and gross)
g = trades(RC, RP, {"gross": True})
miss = [("GDXU", "2026-10-28", "skipped: spread 34bps > 30 max (Testing 2)"), ("LABD", "2026-11-02", "skipped: cost filter stop-exit 0.24R > 0.15R (Testing 2)"),
        ("SOXL", "2026-11-05", "skipped: opposite side held (CWT09 short, Testing C)"), ("GDXU", "2026-11-10", "skipped: spread 34bps > 30 max (Testing C)"),
        ("GDXU", "2026-10-20", "silent: no live signal (pre-GX1 clock gate / no poll log)"), ("SOXS", "2026-10-20", "silent: 15:00 bucket never evaluated (last signal of any setup 14:51)"),
        ("GDXU", "2026-10-22", "silent: pre-GX1 clock gate (4 missing minute bars; no 14:05 evaluations for any setup)"),
        ("LABU", "2026-10-22", "silent: pre-GX1 clock gate (LABU ~80 missing minute bars)"), ("LABU", "2026-10-28", "silent: data (LABU minute bars late / missing at 14:55-15:00)")]
rows = []
for s, d, why in miss:
    a = rp[(rp.symbol == s) & (rp.date == d)]; b = g[(g.symbol == s) & (g.date == d)]
    rows.append(dict(symbol=s, date=d, tod=int(a.tod.iloc[0]), net=round(a.r.iloc[0], 3), gross=round(b.r.iloc[0], 3), why=why))
B = pd.DataFrame(rows); print(B.to_string()); B.to_csv(SC + "out/blocked.csv", index=False)
print("skipped net", B.net[:4].sum().round(2), "gross", B.gross[:4].sum().round(2), "| silent net", B.net[4:].sum().round(2), "gross", B.gross[4:].sum().round(2))
