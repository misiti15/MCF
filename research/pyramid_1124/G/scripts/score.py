"""Team G Part 1 scoring (PREREG.md). Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
P = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/"
U = pd.read_csv("/home/user/MCF/data/universe.csv")
ETB = pd.Series(np.where(U.easy_to_borrow.astype(str) == "True", 1.0, 0.0), index=U.symbol)
TEST, PRIM = B.TESTING_RULES, B.BOOK["primary"]
G = pd.read_parquet(P + "G/gate.parquet")[["date", "T", "TT1", "TT0", "spy_vw", "spy30"]].drop_duplicates(["date", "T"])

def gate(t):
    t = t.copy(); t["date"] = t.date.astype(str)
    return t.merge(G.rename(columns={"T": "tod"}), on=["date", "tod"], how="left")

def L1(tag):
    t = pd.read_parquet(P + f"L1/trades_{tag}.parquet")
    return t

def norm(t):
    t = B.add_r(t); t["date"] = t.date.astype(str); return gate(t)

# ---- assemble candidate trade sets: dict cand -> {"sig": {fit,check,T2}, "r1": {...}}
def load_sets():
    S = {}
    l1 = {k: norm(L1(k)) for k in ("fit", "check", "t2")}
    l3a = norm(pd.read_parquet(P + "L3/work/trades_t1.parquet")); l3b = norm(pd.read_parquet(P + "L3/work/trades_t2.parquet"))
    h = B.half(l3a.date); l3a["half"] = h
    def L1sel(t, cfg, geo, kind_): return t[(t.cfg == cfg) & (t.geo == geo) & (t.kind_ == kind_)]
    S["C3"] = {"sig": {"fit": L1sel(l1["fit"], "C3_V25", "G2", "sig"), "check": L1sel(l1["check"], "C3_V25", "G2", "sig"),
                       "T2": L1sel(l1["t2"], "C3_V25", "G2", "sig")},
               "r1": {"fit": L1sel(l1["fit"], "C3_V25", "G2", "ctl"), "check": L1sel(l1["check"], "C3_V25", "G2", "ctl"),
                      "T2": L1sel(l1["t2"], "C3_V25", "G2", "ctl")}}
    nm = "NM-ETF-late-dip-di-long"
    S["NM"] = {"sig": {"fit": L1sel(l1["fit"], nm, "P", "prim"), "check": L1sel(l1["check"], nm, "P", "prim"),
                       "T2": L1sel(l1["t2"], nm, "P", "prim")}, "r1": None}
    for c, cfg in (("A1", "A1"), ("A3", "A3"), ("B3", "B3a")):
        S[c] = {"sig": {"fit": l3a[(l3a.cfg == cfg) & (l3a.ctrl == 0) & (l3a.half == "fit")],
                        "check": l3a[(l3a.cfg == cfg) & (l3a.ctrl == 0) & (l3a.half == "check")],
                        "T2": l3b[(l3b.cfg == cfg) & (l3b.ctrl == 0)]},
                "r1": {"fit": l3a[(l3a.cfg == cfg) & (l3a.ctrl == 1) & (l3a.half == "fit")],
                       "check": l3a[(l3a.cfg == cfg) & (l3a.ctrl == 1) & (l3a.half == "check")],
                       "T2": l3b[(l3b.cfg == cfg) & (l3b.ctrl == 1)]}}
    # primary reference book (L1 method)
    pb = {}
    for k, tag in (("fit", "fit"), ("check", "check"), ("T2", "t2")):
        x = l1[tag][l1[tag].kind_ == "prim"]
        pb[k] = pd.concat([B.book(x[x.cfg == s], PRIM, ETB) for s in x.cfg.unique()])
    return S, pb

def sessions():
    spy = B.spy_t1(); days = [d for d in spy.index if d <= "2026-11-04"]; h = B.half(pd.Series(days))
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    return {"fit": [d for d, x in zip(days, h) if x == "fit"], "check": [d for d, x in zip(days, h) if x == "check"],
            "T2": list(spy2.index)}, {"fit": spy, "check": spy, "T2": spy2}

def card(b, ses, spy):
    s = B.stats(b, len(ses), spy)
    if not len(b): return s
    w, l = b.r[b.r > 0], b.r[b.r <= 0]
    s["be_win"] = round(float(-l.mean() / (w.mean() - l.mean())), 3) if len(w) and len(l) else None
    mid = sorted(ses)[len(ses) // 2]
    s["halves"] = [round(float(b[b.date < mid].r.mean()), 4) if (b.date < mid).any() else None,
                   round(float(b[b.date >= mid].r.mean()), 4) if (b.date >= mid).any() else None]
    return s

def r2_sets():
    R = {}
    for src in ("T1", "T2"):
        t = pd.read_parquet(P + f"G/r2_{src}.parquet")
        t = norm(t)
        if src == "T1":
            t["half"] = B.half(t.date)
        else:
            t["half"] = "T2"
        R[src] = t
    return R

def main():
    S, pb = load_sets(); ses, spy = sessions()
    R2 = r2_sets()
    pday = {k: v.groupby("date").r.sum().reindex(ses[k], fill_value=0.0) for k, v in pb.items()}
    out = {"primary_ref": {k: {"trades": len(v), "avg_r": round(float(v.r.mean()), 4)} for k, v in pb.items()}}
    rows = []
    for c, d in S.items():
        rules = TEST
        for gname in ("none", "TT1", "TT0"):
            e = {}
            for k in ("fit", "check", "T2"):
                x = d["sig"][k]
                xg = x if gname == "none" else x[x[gname].fillna(False).astype(bool)]
                b = B.book(xg, rules, ETB)
                e[k] = card(b, ses[k], spy[k])
                if c == "NM":
                    e[k]["primary_rules_avg_r"] = round(float(B.book(xg, PRIM, ETB).r.mean()), 4) if len(xg) else None
                e[k]["gate_pass_share_of_signals"] = round(len(xg) / max(len(x), 1), 3)
                if d["r1"] is not None:
                    y = d["r1"][k]; yg = y if gname == "none" else y[y[gname].fillna(False).astype(bool)]
                    rb = B.book(yg, rules, ETB); e[k]["R1_avg_r"] = round(float(rb.r.mean()), 4) if len(rb) else None
                src = "T2" if k == "T2" else "T1"
                z = R2[src]; z = z[(z.cand == c) & (z.half == (k if k != "T2" else "T2"))]
                zg = z if gname == "none" else z[z[gname].fillna(False).astype(bool)]
                rb = B.book(zg, rules, ETB)
                e[k]["R2_avg_r"] = round(float(rb.r.mean()), 4) if len(rb) else None
                e[k]["R2_n"] = int(len(rb))
                dr = b.groupby("date").r.sum().reindex(ses[k], fill_value=0.0)
                bk = pday[k]
                e[k]["corr_primary_book"] = round(float(np.corrcoef(dr, bk)[0, 1]), 3) if dr.std() > 0 else None
                w10 = bk.nsmallest(10).index
                e[k]["R_on_book_worst10"] = round(float(dr.reindex(w10).sum()), 2)
                e[k]["book_worst10_R"] = round(float(bk.nsmallest(10).sum()), 1)
            out[f"{c}_{gname}"] = e
            for k in ("fit", "check", "T2"):
                z = e[k]
                rows.append(dict(cfg=f"{c}_{gname}", half=k, n=z.get("trades"), ps=z.get("trades_per_session"),
                                 avg=z.get("avg_r"), wo=z.get("avg_r_wo_best_day"), share=z.get("best_day_share"),
                                 t=z.get("t_day_clustered"), win=z.get("win"), be=z.get("be_win"), halves=z.get("halves"),
                                 R1=z.get("R1_avg_r"), R2=z.get("R2_avg_r"), pas=z.get("gate_pass_share_of_signals"),
                                 corr=z.get("corr_primary_book"), w10=z.get("R_on_book_worst10"), hold=z.get("median_hold_min"),
                                 up=z.get("avg_r_spy_up"), dn=z.get("avg_r_spy_down")))
    json.dump(out, open(P + "G/part1.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 30)
    df = pd.DataFrame(rows); df.to_csv(P + "G/part1_table.csv", index=False)
    print(df.to_string(index=False))
    # R2 baseline by gate
    for src, t in R2.items():
        for c in S:
            z = t[t.cand == c]
            for h, zz in z.groupby("half"):
                if h == "none": continue
                a = B.book(zz, TEST, ETB).r.mean(); g1 = B.book(zz[zz.TT1.fillna(False).astype(bool)], TEST, ETB).r.mean()
                g0 = B.book(zz[zz.TT0.fillna(False).astype(bool)], TEST, ETB).r.mean()
                print("R2", c, h, len(zz), round(a, 4), "TT1", round(g1, 4), "TT0", round(g0, 4))

if __name__ == "__main__":
    main()
