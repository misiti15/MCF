"""Test C: Workbench Mechanic pass, 21 one-knob variants of the parent, scored with the -2R latch (Primary rule)."""
import numpy as np, pandas as pd, json
import load4 as L, sim4
P = sim4.P
sig = sim4.signals(L.C, P); tr = sig[sig.date.map(L.split) == "TRAIN"]
Q = dict(fo80=float(tr.fromOpen.quantile(.8)), vw80=float(tr.vwapDistPct.quantile(.8)), vr80=float(tr.volumeRatio.quantile(.8)),
         rsi20=float(tr.rsi5.quantile(.2)))
print("TRAIN quantiles", {k: round(v, 3) for k, v in Q.items()}, "n TRAIN signals", len(tr))
V = {"PARENT": {},
     "C01 target 1.25R": dict(up=1.25), "C02 target 1.5R": dict(up=1.5), "C03 target 2.0R": dict(up=2.0),
     "C04 stop 0.8R": dict(dn=0.8), "C05 stop 1.25R": dict(dn=1.25),
     "C06 BE after +0.5R": dict(be_at=0.5, be_to=0.0), "C07 BE after +0.75R": dict(be_at=0.75, be_to=0.0),
     "C08 stop to -0.5R after +0.5R": dict(be_at=0.5, be_to=-0.5),
     "C09 60-min stop if MFE<0.25R": dict(ts_min=60, ts_r=0.25), "C10 max hold 75 min": dict(maxhold=75),
     "C11 30-min stop if MFE<0.25R": dict(ts_min=30, ts_r=0.25),
     "C12 half +1R, half 2R, BE after 1R": dict(so_at=1.0, so_up=2.0, so_be=True),
     "C13 half +0.5R, half 1.5R, BE after 0.5R": dict(so_at=0.5, so_up=1.5, so_be=True),
     "C14 trail 0.75R after MFE 1R, cap 3R": dict(up=3.0, trail_after=1.0, trail=0.75),
     "C15 fromOpen <= TRAIN p80": dict(fomax=Q["fo80"]), "C16 vwapDist <= TRAIN p80": dict(vwmax=Q["vw80"]),
     "C17 volumeRatio <= TRAIN p80": dict(vrmax=Q["vr80"]), "C18 rsi5 >= TRAIN p20": dict(rsi5min=Q["rsi20"]),
     "C19 1R >= 0.5% of price": dict(rpct=0.5), "C20 no re-entry after a stop": dict(noreentry_after_stop=True),
     "C21 <= 2 lots per symbol": dict(symcap=2)}
rows, books = [], {}
for test, (c, g) in L.TESTS.items():
    days = L.DAYS[test]; base = None
    for name, ch in V.items():
        v = dict(P, **ch)
        b = sim4.book(sim4.trades(c, v, g), v, -2.0)
        books[(test, name)] = b
        if base is None:
            base = b; thr = b.r.quantile(0.9); top = set(zip(b.symbol[b.r >= thr], b.date[b.r >= thr], b.em[b.r >= thr]))
            topR = b.r[b.r >= thr].sum()
        kb = set(zip(b.symbol, b.date, b.em)); kept = top & kb
        bi = b.set_index(["symbol", "date", "em"]).r
        segs = [("ALL", b, base, days)]
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                segs.append((sp, b[b.date.map(L.split) == sp], base[base.date.map(L.split) == sp], [d for d in days if L.split(d) == sp]))
        for seg, bb, bs, dd in segs:
            t, dr = sim4.paired_t(bs, bb, dd)
            r = dict(test=test, seg=seg, cfg=name, **sim4.stats(bb, dd), t_vs_parent=t, dR_vs_parent=dr)
            if seg == "ALL":
                r["trades_kept_pct"] = len(b) / len(base); r["top_decile_kept_pct"] = len(kept) / len(top)
                r["top_decile_R_captured"] = bi.reindex(list(top)).fillna(0).sum() / topR
            rows.append(r)
    print(test, "done", flush=True)
df = pd.DataFrame(rows); df.to_csv("C_workbench.csv", index=False, float_format="%.4f")
pd.to_pickle(books, "C_books.pkl"); json.dump(Q, open("C_quantiles.json", "w"))
pd.set_option("display.width", 260)
print(df[["test", "seg", "cfg", "trades", "win", "avg", "avg_wo_best", "best_share", "worst_day", "wl", "pf", "t_vs_parent", "dR_vs_parent", "trades_kept_pct", "top_decile_kept_pct", "top_decile_R_captured"]].round(3).to_string())
