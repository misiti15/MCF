"""BREADTHGATE-1127 scoring (PREREG.md): 6 side-aware breadth gates on the lot table from bg_build.py.
Usage (cwd = repo): python bg_score.py W -> research/breadthgate_1127/{results.json, per_setup.csv, score_out.txt via tee}.
Locked block never read (asserted). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1]); H = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28")
INFO = {"GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long",
        "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short"}
P4 = {"L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "NM-ETF-late-dip-di-long"}
CFGS = {  # id: (column, short keep test, long keep test)
    "VW-M": ("breadth", lambda b: b < 0.50, lambda b: b > 0.50),
    "VW-S": ("breadth", lambda b: b < 0.40, lambda b: b > 0.60),
    "OP-M": ("breadth_open", lambda b: b < 0.50, lambda b: b > 0.50),
    "OP-S": ("breadth_open", lambda b: b < 0.35, lambda b: b > 0.65),
    "VW-V": ("breadth", lambda b: ~(b > 0.70), lambda b: ~(b < 0.30)),
    "OP-V": ("breadth_open", lambda b: ~(b > 0.65), lambda b: ~(b < 0.35)),
}
SPL = ["FIT", "CHECK", "T2"]
NDRAW = 500


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def keep_mask(x, cid):
    col, fs, fl = CFGS[cid]
    b = x[col].to_numpy(float)
    with np.errstate(invalid="ignore"):
        k = np.where(x.side.to_numpy() < 0, fs(b), fl(b))
    return k | np.isnan(b)   # missing breadth: gate cannot fire (kept)


def tstat(v):
    v = np.asarray(v, float)
    return float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))) if len(v) > 1 and v.std(ddof=1) > 0 else float("nan")


def day_series(x, skip, rcol, sessions):
    z = x[rcol] - x.groupby("setup")[rcol].transform("mean")
    d = (-(z.where(skip, 0.0))).groupby(x.date).sum()
    return d.reindex(sessions, fill_value=0.0)


def concentration(d):
    tot = d.sum(); best = d.max()
    share = float(best / tot) if tot > 0 else float("nan")
    wo = float((tot - best) / (len(d) - 1)) if len(d) > 1 else float("nan")
    return share, wo


def random_raw(x, nskip_by_setup, rcol, rng):
    """size-matched random skip: per setup, skip the same number of lots uniformly; returns NDRAW pooled RAW gains."""
    out = np.zeros(NDRAW)
    for s, g in x.groupby("setup"):
        k = nskip_by_setup.get(s, 0)
        if k == 0:
            continue
        r = g[rcol].to_numpy(float); n = len(r)
        if k >= n:
            out -= r.sum(); continue
        u = rng.random((NDRAW, n))
        idx = np.argpartition(u, k - 1, axis=1)[:, :k]
        out -= r[idx].sum(axis=1)
    return out


def score(x, sessions, cid, rcol, rng, with_rand=True):
    res = {}
    for sp in SPL:
        g = x[x.per == sp]
        if not len(g):
            continue
        sk = ~keep_mask(g, cid)
        d = day_series(g, pd.Series(sk, index=g.index), rcol, sessions[sp])
        z_tot = float(d.sum()); share, wo = concentration(d)
        raw = float(-(g[rcol][sk]).sum())
        e = dict(lots=int(len(g)), skipped=int(sk.sum()), skip_share=float(sk.mean()), raw_gain=raw, z_gain=z_tot,
                 z_t=tstat(d.to_numpy()), best_day_share=share, avg_wo_best=wo, sessions=int(len(d)),
                 base_R=float(g[rcol].sum()), kept_R=float(g[rcol][~sk].sum()),
                 base_avg=float(g[rcol].mean()), kept_avg=float(g[rcol][~sk].mean()) if (~sk).any() else float("nan"))
        if with_rand:
            ns = pd.Series(sk, index=g.index).groupby(g.setup).sum().to_dict()
            rr = random_raw(g, ns, rcol, rng)
            e.update(rand_mean=float(rr.mean()), rand_p95=float(np.percentile(rr, 95)),
                     rand_pct=float((rr < raw).mean()))
        e["_daily"] = d
        res[sp] = e
    return res


def per_setup(x, cid, rcol):
    rows = []
    for (s, sp), g in x.groupby(["setup", "per"]):
        sk = ~keep_mask(g, cid)
        z = g[rcol] - g[rcol].mean()
        rows.append(dict(cfg=cid, basis=rcol, setup=s, per=sp, side=int(g.side.iloc[0]), lots=len(g), skipped=int(sk.sum()),
                         z_gain=float(-z[sk].sum()), z_per_lot=float(-z[sk].sum() / len(g)), raw_gain=float(-g[rcol][sk].sum()),
                         base_avg=float(g[rcol].mean()), kept_avg=float(g[rcol][~sk].mean()) if (~sk).any() else np.nan,
                         skip_avg=float(g[rcol][sk].mean()) if sk.any() else np.nan))
    return rows


def bars(res, res_lr8, ps):
    c, t = res["CHECK"], res["T2"]
    comb = tstat(np.r_[c["_daily"].to_numpy(), t["_daily"].to_numpy()])
    b = {}
    b["1_z"] = bool(c["z_gain"] > 0 and t["z_gain"] > 0 and c["z_t"] >= 1.5 and t["z_t"] >= 1.5 and comb >= 2.64)
    b["2_rand"] = bool(c["raw_gain"] > c["rand_p95"] and t["raw_gain"] > t["rand_p95"])
    b["3_oneday"] = bool(all(e["best_day_share"] < 0.5 and e["avg_wo_best"] > 0 for e in (c, t)))
    ok = True; worst = {}
    for sp in ("CHECK", "T2"):
        q = ps[(ps.per == sp) & (ps.skipped >= 30)]
        if len(q) == 0 or (q.z_gain > 0).sum() < np.ceil(2 / 3 * len(q)):
            ok = False
    w = ps[ps.per.isin(["CHECK", "T2"])].pivot_table(index="setup", columns="per", values="z_per_lot")
    if ((w["CHECK"] < -0.02) & (w["T2"] < -0.02)).any():
        ok = False
    b["4_targeted"] = bool(ok)
    b["5_not_blanket"] = bool(c["skip_share"] <= 0.5 and t["skip_share"] <= 0.5)
    b["6_lr8"] = bool(res_lr8["CHECK"]["z_gain"] > 0 and res_lr8["T2"]["z_gain"] > 0)
    return b, comb


def strip(r):
    return {sp: {k: v for k, v in e.items() if k != "_daily"} for sp, e in r.items()}


if __name__ == "__main__":
    x = pd.read_parquet(W / "lots.parquet")
    no_locked(x.date.unique())
    ctx_dates = {"T2": sorted(pd.read_parquet(W / "ctx_t2.parquet").date.astype(str).unique())}
    t1 = sorted(set(x[x.per.isin(["FIT", "CHECK"])].date))
    import glob
    c1 = pd.concat([pd.read_parquet(p, columns=["date"]) for p in glob.glob("/home/user/MCF/research/history2y/data/context/*.parquet")])
    c1 = sorted(pd.to_datetime(c1.date).dt.date.astype(str).unique())
    no_locked(c1)
    sessions = {"FIT": [d for d in c1 if (d[:7] == "2024-10" or "2025-03" <= d[:7] <= "2025-09")],
                "CHECK": [d for d in c1 if "2025-10-01" <= d <= "2026-11-04"], "T2": ctx_dates["T2"]}
    J = x[~x.setup.isin(INFO)].copy(); I = x[x.setup.isin(INFO)].copy()
    rng = np.random.default_rng(1127)
    out = {"sessions": {k: len(v) for k, v in sessions.items()}, "configs": {}, "subsets": {}, "info_gens": {}}
    rows = []
    print("sessions", out["sessions"], "| judged lots", len(J), "| breadth missing", float(J.breadth.isna().mean()))
    print(J.groupby(["per"]).r_live.agg(["count", "mean", "sum"]).round(3).to_string())
    for cid in CFGS:
        r = score(J, sessions, cid, "r_live", rng)
        r8 = score(J, sessions, cid, "r_lr8", rng, with_rand=False)
        ps = pd.DataFrame(per_setup(J, cid, "r_live")); rows += ps.to_dict("records")
        rows += per_setup(J, cid, "r_lr8")
        b, comb = bars(r, r8, ps)
        out["configs"][cid] = dict(live=strip(r), lr8=strip(r8), comb_t=comb, bars=b, PASS=all(b.values()))
        c, t = r["CHECK"], r["T2"]
        print(f"\n== {cid} PASS={all(b.values())} bars={b} combined t={comb:.2f}")
        for sp in SPL:
            e = r[sp]
            print(f"  {sp:5s} skip {e['skipped']:6d}/{e['lots']:6d} ({e['skip_share']:.0%}) RAW {e['raw_gain']:+8.1f} "
                  f"(rand mean {e['rand_mean']:+8.1f} p95 {e['rand_p95']:+8.1f} pct {e['rand_pct']:.2f}) Z {e['z_gain']:+7.1f} "
                  f"t {e['z_t']:+.2f} best {e['best_day_share']:.2f} wo {e['avg_wo_best']:+.3f} | kept avg {e['kept_avg']:+.4f} "
                  f"vs base {e['base_avg']:+.4f} | LR8 Z {r8[sp]['z_gain']:+.1f}")
        q = ps[ps.per.isin(["CHECK", "T2"])].pivot_table(index="setup", columns="per", values=["z_per_lot", "skipped"])
        print(q.round(4).to_string())
        # salvage subsets (bars 1-3 only)
        for nm, sel in {"shorts": J.side < 0, "longs": J.side > 0, "P4": J.setup.isin(P4), "arena8": ~J.setup.isin(P4)}.items():
            rs = score(J[sel], sessions, cid, "r_live", rng)
            cs = tstat(np.r_[rs["CHECK"]["_daily"].to_numpy(), rs["T2"]["_daily"].to_numpy()])
            bb = dict(z=bool(rs["CHECK"]["z_gain"] > 0 and rs["T2"]["z_gain"] > 0 and rs["CHECK"]["z_t"] >= 1.5 and rs["T2"]["z_t"] >= 1.5 and cs >= 2.64),
                      rand=bool(rs["CHECK"]["raw_gain"] > rs["CHECK"]["rand_p95"] and rs["T2"]["raw_gain"] > rs["T2"]["rand_p95"]),
                      oneday=bool(all(rs[s]["best_day_share"] < 0.5 and rs[s]["avg_wo_best"] > 0 for s in ("CHECK", "T2"))))
            out["subsets"][f"{cid}|{nm}"] = dict(res=strip(rs), comb_t=cs, bars=bb, lead=all(bb.values()))
            print(f"  subset {nm:6s} Z CHECK {rs['CHECK']['z_gain']:+7.1f} (t {rs['CHECK']['z_t']:+.2f}) T2 {rs['T2']['z_gain']:+7.1f} "
                  f"(t {rs['T2']['z_t']:+.2f}) comb t {cs:+.2f} | RAW vs p95 CHECK {rs['CHECK']['raw_gain']:+.1f}/{rs['CHECK']['rand_p95']:+.1f} "
                  f"T2 {rs['T2']['raw_gain']:+.1f}/{rs['T2']['rand_p95']:+.1f} lead={all(bb.values())}")
        ri = score(I, sessions, cid, "r_live", rng, with_rand=False)
        out["info_gens"][cid] = strip(ri)
        rows += per_setup(I, cid, "r_live")
    pd.DataFrame(rows).to_csv(H / "per_setup.csv", index=False, float_format="%.5f")
    json.dump(out, open(H / "results.json", "w"), indent=1, default=float)
    print("\nPASS:", [c for c, v in out["configs"].items() if v["PASS"]], "| leads:", [k for k, v in out["subsets"].items() if v["lead"]])
