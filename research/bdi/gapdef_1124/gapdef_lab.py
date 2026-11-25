"""GAPDEF-1124 part (ii): the pre-registered family-wide gap-definition remedy on the 2-year lab, through the bench10
pipeline (research/ultimate_1119/top10/bench10.py: live config masks, windows, min_adv, prefilters, refire chains, home
account book, 1-minute exits, LR8 research costs). Only the setup list differs: the gap-down short family.
Locked block 2024-11-01..2025-02-28 is never read (bench10 refuses it and asserts on every load).

Gap re-measure: gapV = 09:30 1-min bar typical price (H+L+C)/3 (cache_hist has no VWAP column; the pre-registered
fallback) vs the prior close, prior close = 09:30 open / (1 + lab gap/100) (the lab gap is the 09:30 print vs prior close).
ATR% = atr_d / prior close x 100, atr_d = risk / 0.25 (t1s1 geometry: stop = 0.25 x daily ATR).
Configs (pre-declared, 3 in total, shared with gapdef_live.py):
  A  keep if gapV <= min(own threshold, -1.0%)
  B  keep if gapV <= min(own threshold, -0.5 x ATR%)
  C  comparison arm: no entries before 12:00 ET (gap unchanged)
Usage: python gapdef_lab.py WORK sig|walk|score.  Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("L3-gap-slope-lowdist-FD", "account_testing.yaml", "testing"),
            ("L3-gap-slope-rsi5hi-FD", "account_testing.yaml", "testing"),
            ("RW1-gapdn-bounce-flowsell-short-FD", "account_testing.yaml", "testing"),
            ("RW7-gapdn-bounce-early-short-FD", "account_testingf.yaml", "testingf"),
            ("RW3S-gapdn-flowsell-short-FD", "account_graveyard.yaml", "graveyard")]
OWN = {s: (-2.6573517322540283 if s.startswith("L3-") else 0.0) for s, _, _ in B.SETUPS}


def walk_job(args):
    sym, T = args
    b = B.hist_bars(sym)
    res = B.walk_trades(T, b)
    f = b[(b.index.hour == 9) & (b.index.minute == 30)]
    fm = pd.DataFrame({"date": f.index.date.astype(str), "o930": f.open.values,
                       "tp930": ((f.high + f.low + f.close) / 3).values, "v930": f.volume.values})
    return res, fm.assign(symbol=sym)


def score(W):
    t = pd.read_parquet(W / "trades_fam.parquet")
    t = B.add_r(t)
    etb = pd.Series(1.0, index=t.symbol.unique())   # bench10 etb_rate.parquet is not in the repo: ETB filter off (all shorts kept)
    out = []
    for s, _, acct in B.SETUPS:
        out.append(B.book(t[t.setup == s], B.BOOK.get(acct, B.TESTING_RULES), etb))
    t = pd.concat(out, ignore_index=True)
    t["pc"] = t.o930 / (1 + t.gap / 100)
    t["gapV"] = (t.tp930 / t.pc - 1) * 100
    t["atr_pct"] = t.risk / 0.25 / t.pc * 100
    t["half"] = B.half(t.date)
    t["own"] = t.setup.map(OWN)
    miss = t.gapV.isna()
    t.loc[miss, "gapV"] = t.loc[miss, "gap"]
    t["is_own"] = np.where(t.setup.str.startswith("L3-"), t.gapV <= t.own, t.gapV < 0)
    keep = {"A": t.is_own & (t.gapV <= -1.0), "B": t.is_own & (t.gapV <= -0.5 * t.atr_pct), "C": t.em >= 720}
    print(f"lab trades booked {len(t)} on {t.date.nunique()} sessions; 09:30 bar missing (lab gap used) {int(miss.sum())}; "
          f"sign/threshold flip by gapV alone (own rule fails) {int((~t.is_own).sum())}")
    rows = []
    for cfg, k in keep.items():
        for s in [x for x, _, _ in B.SETUPS] + ["ALL"]:
            x = t if s == "ALL" else t[t.setup == s]
            kk = k.loc[x.index]
            rm = x[~kk]; kp = x[kk]
            d = {"cfg": cfg, "setup": s, "n": len(x), "kept": int(kk.sum()), "removed": len(rm),
                 "rm_avgR": round(rm.r.mean(), 3) if len(rm) else None, "dR": round(-rm.r.sum(), 2)}
            for h in ("fit", "check"):
                z = rm[rm.half == h]
                d[f"dR_{h}"] = round(-z.r.sum(), 2); d[f"rm_avg_{h}"] = round(z.r.mean(), 3) if len(z) else None; d[f"n_rm_{h}"] = len(z)
            d["avgR_before"] = round(x.r.mean(), 4) if len(x) else None
            d["avgR_after"] = round(kp.r.mean(), 4) if len(kp) else None
            dd = (-rm.r).groupby(rm.date).sum()
            d["dR_wo_best_day"] = round(dd.sum() - dd.max(), 2) if len(dd) else 0.0
            d["best_day_share"] = round(dd.max() / dd.sum(), 3) if len(dd) and dd.sum() > 0 else None
            if len(kp):
                day = kp.groupby("date").r.sum(); b = day.idxmax()
                d["kept_avg_wo_best"] = round(kp.loc[kp.date != b, "r"].mean(), 4)
                d["kept_best_share"] = round(day.max() / day.sum(), 3) if day.sum() > 0 else None
            # day-clustered t of removed-trades delta (per session)
            if len(dd) > 2 and dd.std() > 0:
                full = (-rm.r).groupby(rm.date).sum().reindex(sorted(x.date.unique()), fill_value=0.0)
                d["t_day"] = round(full.mean() / (full.std(ddof=1) / np.sqrt(len(full))), 2)
            rows.append(d)
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "lab_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.to_string(index=False))
    for cfg in "ABC":
        x = R[(R.cfg == cfg) & (R.setup != "ALL") & (R.removed > 0)]
        print(f"{cfg}: setups improve {int((x.dR > 0).sum())} (+{x.loc[x.dR > 0, 'dR'].sum():.2f}R), worse {int((x.dR < 0).sum())} "
              f"({x.loc[x.dR < 0, 'dR'].sum():.2f}R), largest worsening {x.dR.min():+.2f}R")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True); st = sys.argv[2]
    if st == "sig":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif st == "walk":
        sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
        B.no_locked(sig["date"].unique())
        jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            rr = list(p.imap_unordered(walk_job, jobs, chunksize=4))
        a = pd.DataFrame([x for r, _ in rr for x in r], columns=["i", "px", "kind", "xt"]).set_index("i")
        fm = pd.concat([f for _, f in rr], ignore_index=True)
        sig = sig.join(a).merge(fm, on=["symbol", "date"], how="left")
        sig.to_parquet(W / "trades_fam.parquet")
        print(len(sig), "signals;", int((sig.kind.isna() | (sig.kind < 0)).sum()), "without path;", int(sig.tp930.isna().sum()), "without 09:30 bar")
    elif st == "score":
        score(W)
