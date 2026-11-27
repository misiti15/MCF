"""R3N stage 2: score the frozen finalists ONCE (bench10 pipeline) on FIT / CHECK / T2 + lab-basis random control.
Stages: sig1 | walk1 | t2 | score.  Educational only - not financial advice."""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
from common import *  # noqa

W = HERE / "work"; W.mkdir(exist_ok=True)
PICKS = json.load(open(HERE / "picks.json"))


def inventory():
    inv, mods = [], {}
    for p in PICKS:
        r = p["rule"]; a, b = WINS[r["win"]]
        inv.append(dict(setup=p["name"], module="", side=1 if r["side"] == "long" else -1, geom=r["geom"], w_lo=a, w_hi=b,
                        min_adv=ADV, refire=False, cooldown=1, prefilter="", account="testing", cfg="", struct=False, cwt=False))
        mods[p["name"]] = RuleMod(r)
    return inv, mods


def labside(f, o):
    """lab-basis R of the signals and the day-matched control sums per (setup, date)."""
    f = ensure_cols(f)
    tod = f.tod.to_numpy(int)
    cand, ctl = [], []
    for p in PICKS:
        r = p["rule"]; a, b = WINS[r["win"]]
        lr = lab_r(f, r["side"], r["geom"])
        m = base_ok(f, r["side"]) & (tod >= a) & (tod <= b) & np.isfinite(lr) & (f.atr_d.to_numpy(float) > 0)
        g = pd.DataFrame({"date": f.date.to_numpy()[m], "r": lr[m]}).groupby("date").r.agg(["sum", "count"]).reset_index()
        g["setup"] = p["name"]; ctl.append(g)
        if len(o):
            s = o[o.setup == p["name"]][["symbol", "date", "tod"]]
            k = f[["symbol", "date", "tod"]].assign(lr=lr).merge(s, on=["symbol", "date", "tod"])
            cand.append(k.assign(setup=p["name"]))
    return (pd.concat(cand) if cand else pd.DataFrame()), pd.concat(ctl)


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    inv, mods = inventory()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str); f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f["date"].unique())
    o = B.signals(f, f, inv, mods)
    c, k = labside(f, o)
    o.to_parquet(W / f"sig1_{month}.parquet"); c.to_parquet(W / f"lab1_{month}.parquet"); k.to_parquet(W / f"ctl1_{month}.parquet")
    return month, len(o)


def t2_job(sym):
    import research.history2y.build_frames as BF
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ); b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, None, None, None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, None, None, None
    x = x.reset_index(names="ts").merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, None, None, None
    if "ctx" not in B.WCTX:
        c = pd.read_parquet(B.FRESH / "ctx.parquet"); c["date"] = c["date"].astype(str); B.WCTX["ctx"] = c
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    inv, mods = inventory()
    o = B.signals(f, f, inv, mods)
    c, k = labside(f, o)
    if len(o):
        w = B.walk_trades(o, b)
        o = o.join(pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i"))
    return sym, o, c, k


def sessions():
    spy = B.spy_t1(); days = [d for d in spy.index if d <= "2026-11-04"]; h = B.half(pd.Series(days))
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    return {"fit": [d for d, x in zip(days, h) if x == "fit"], "check": [d for d, x in zip(days, h) if x == "check"],
            "T2": list(spy2.index)}, {"fit": spy, "check": spy, "T2": spy2}


def primary_book():
    """Primary reference book daily R (team G method: L1's saved prim rows booked under Primary rules)."""
    P = HERE.parent / "L1"; ETBS = ETB
    out = {}
    for k, tag in (("fit", "fit"), ("check", "check"), ("T2", "t2")):
        x = B.add_r(pd.read_parquet(P / f"trades_{tag}.parquet")); x["date"] = x.date.astype(str)
        x = x[x.kind_ == "prim"]
        out[k] = pd.concat([B.book(x[x.cfg == s], B.BOOK["primary"], ETBS) for s in x.cfg.unique()])
    return out


def score():
    ses, spy = sessions()
    T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet")); T1["half"] = B.half(T1.date)
    T2 = B.add_r(pd.read_parquet(W / "trades_t2.parquet")); T2["half"] = "T2"
    L = {"T1": pd.concat([pd.read_parquet(p) for p in sorted(W.glob("lab1_*.parquet"))]),
         "T2": pd.read_parquet(W / "lab_t2.parquet")}
    K = {"T1": pd.concat([pd.read_parquet(p) for p in sorted(W.glob("ctl1_*.parquet"))]),
         "T2": pd.read_parquet(W / "ctl_t2.parquet")}
    for z in list(L.values()) + list(K.values()):
        z["date"] = z.date.astype(str); B.no_locked(z.date.unique())
    pb = primary_book()
    pday = {k: v.groupby("date").r.sum().reindex(ses[k], fill_value=0.0) for k, v in pb.items()}
    out, rows = {"primary_ref": {k: dict(trades=len(v), avg_r=round(float(v.r.mean()), 4)) for k, v in pb.items()}}, []
    for p in PICKS:
        nm = p["name"]; e = {}
        for k in ("fit", "check", "T2"):
            src = "T2" if k == "T2" else "T1"
            x = (T2 if k == "T2" else T1); x = x[(x.setup == nm) & (x.half == k)]
            bk = B.book(x, B.TESTING_RULES, ETB)
            s = B.stats(bk, len(ses[k]), spy[k])
            if len(bk):
                w_, l_ = bk.r[bk.r > 0], bk.r[bk.r <= 0]
                s["be_win"] = round(float(-l_.mean() / (w_.mean() - l_.mean())), 3) if len(w_) and len(l_) else None
                mid = sorted(ses[k])[len(ses[k]) // 2]
                s["halves"] = [round(float(bk[bk.date < mid].r.mean()), 4) if (bk.date < mid).any() else None,
                               round(float(bk[bk.date >= mid].r.mean()), 4) if (bk.date >= mid).any() else None]
                dr = bk.groupby("date").r.sum().reindex(ses[k], fill_value=0.0); bb = pday[k]
                s["corr_primary_book"] = round(float(np.corrcoef(dr, bb)[0, 1]), 3) if dr.std() > 0 else None
                s["R_on_book_worst10"] = round(float(dr.reindex(bb.nsmallest(10).index).sum()), 2)
                s["book_worst10_R"] = round(float(bb.nsmallest(10).sum()), 1)
            # lab-basis cand vs day-matched universe control (all signals, pre-book, same first-hit rows)
            lc = L[src]; lc = lc[(lc.setup == nm) & lc.date.isin(ses[k])]
            kc = K[src]; kc = kc[(kc.setup == nm)].set_index("date")
            cm = (kc["sum"] / kc["count"]).reindex(lc.date).to_numpy()
            s["lab_cand_avg"] = round(float(lc.lr.mean()), 4) if len(lc) else None
            s["lab_ctrl_matched_avg"] = round(float(np.nanmean(cm)), 4) if len(lc) else None
            s["lab_vs_random"] = round(float(np.nanmean(lc.lr.to_numpy() - cm)), 4) if len(lc) else None
            kk = kc.loc[kc.index.isin(ses[k])]
            s["lab_ctrl_all_bars_avg"] = round(float(kk["sum"].sum() / kk["count"].sum()), 4) if len(kk) else None
            e[k] = s
            rows.append(dict(setup=nm, half=k, n=s.get("trades"), ps=s.get("trades_per_session"), avg=s.get("avg_r"),
                             wo=s.get("avg_r_wo_best_day"), share=s.get("best_day_share"), t=s.get("t_day_clustered"),
                             win=s.get("win"), be=s.get("be_win"), halves=s.get("halves"), Rps=s.get("total_r_per_session"),
                             worst=s.get("worst_day"), up=s.get("avg_r_spy_up"), fl=s.get("avg_r_spy_flat"),
                             dn=s.get("avg_r_spy_down"), hold=s.get("median_hold_min"), lab=s["lab_cand_avg"],
                             ctl=s["lab_ctrl_matched_avg"], vsr=s["lab_vs_random"], corr=s.get("corr_primary_book"),
                             w10=s.get("R_on_book_worst10"), bw10=s.get("book_worst10_R")))
        out[nm] = e
    json.dump(out, open(HERE / "final.json", "w"), indent=1, default=str)
    df = pd.DataFrame(rows); df.to_csv(HERE / "final_table.csv", index=False)
    pd.set_option("display.width", 400); pd.set_option("display.max_columns", 40)
    print(df.to_string(index=False)); print(out["primary_ref"])


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and m <= "2026-11"]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, ms):
                print(r, flush=True)
    elif st == "walk1":
        sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
        B.no_locked(sig["date"].unique())
        jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            out = [x for r in p.imap_unordered(B.walk1_job, jobs, chunksize=4) for x in r]
        a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
        sig.join(a).to_parquet(W / "trades_t1.parquet"); print(len(sig), "signals")
    elif st == "t2":
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        O, Cn, Kt = [], [], []
        with Pool(3) as p:
            for i, (sym, o, c, k) in enumerate(p.imap_unordered(t2_job, syms)):
                if o is not None and len(o): O.append(o)
                if c is not None and len(c): Cn.append(c)
                if k is not None and len(k): Kt.append(k)
                if i % 50 == 0: print(i, flush=True)
        pd.concat(O, ignore_index=True).to_parquet(W / "trades_t2.parquet")
        pd.concat(Cn, ignore_index=True).to_parquet(W / "lab_t2.parquet")
        k = pd.concat(Kt).groupby(["setup", "date"])[["sum", "count"]].sum().reset_index(); k.to_parquet(W / "ctl_t2.parquet")
    elif st == "score":
        score()
