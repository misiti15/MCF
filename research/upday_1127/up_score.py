"""UPDAY_1127 scoring (PREREG.md). Stage 'req' writes the random-control requests; stage 'score' scores the 16 configs,
the bars, day types, the random control and the Primary hedge view. Usage (repo root):
  python research/upday_1127/up_score.py W req     -> W/req.parquet
  python research/upday_1127/up_score.py W score PRIMARY_DAYS_CSV   (needs W/rand.parquet from up_rand.py)
Locked block 2024-11-01..2025-02-28 asserted absent. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "."); sys.path.insert(0, "research/primshorts_1126")
import calib_live as CL  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

W = Path(sys.argv[1]); STAGE = sys.argv[2]
HERE = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28")
NDRAW = 20
TBAR = 2.96
CELLS = json.load(open("research/primshorts_1126/cells_live.json"))


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def livel(entry, risk, px, kind):
    kd = np.where(np.asarray(kind) == 1, "stop", "market")
    return (np.asarray(px) - entry) / risk - CL.predict_R(CELLS, np.asarray(entry), np.asarray(risk), kd)


def lr8(entry, risk, px, kind, em, gap):
    em = np.asarray(em, int); tod = (9 * 60 + 30 + em) // 60 * 100 + (9 * 60 + 30 + em) % 60
    tier = np.where((np.abs(gap) >= 0.20) | (entry < 5), 3.0, 1.0)
    ec = (0.01 + entry * 1e-4) * tod_cost_mult(tod)
    xc = 0.01 + px * 1e-4 + np.where(kind == 1, 0.02, 0.0)
    return ((px - entry) - tier * (ec + xc)) / risk


CONFIGS = {
    "S1": dict(fam="SQZ", crowd=True, gap_max=-0.01, trail=False, desc="SQZ core: gap<=-1%, ret20 bottom 30%, below VWAP 09:50-10:29, reclaim 10:30-13:30"),
    "S2": dict(fam="SQZ", crowd=False, gap_max=-0.01, trail=False, desc="S1 without crowding proxy"),
    "S3": dict(fam="SQZ", crowd=True, gap_max=-0.03, trail=False, desc="S1 gap<=-3%"),
    "S4": dict(fam="SQZ", crowd=True, gap_max=-0.01, vratio=2.0, trail=False, desc="S1 + reclaim-bar volume >=2x"),
    "S5": dict(fam="SQZ", crowd=True, gap_max=-0.01, trail=True, desc="S1 TRAIL exit"),
    "S6": dict(fam="SQZ", crowd=True, gap_max=-0.01, sig_max=150, trail=False, desc="S1 window 10:30-12:00"),
    "R1": dict(fam="RSL", spy_max=-0.002, rs_min=0.005, trail=False, desc="RSL core: SPY<=-0.20% at 09:49, RS>=+0.5%, dipped below open, reclaim open by 11:30"),
    "R2": dict(fam="RSL", spy_max=None, rs_min=0.005, trail=False, desc="R1 without weak-open gate"),
    "R3": dict(fam="RSL", spy_max=-0.002, rs_min=0.010, trail=False, desc="R1 RS>=+1.0%"),
    "R4": dict(fam="RSL", spy_max=-0.002, rs_min=0.005, trail=True, desc="R1 TRAIL exit"),
    "R5": dict(fam="RSL", spy_max=-0.004, rs_min=0.005, trail=False, desc="R1 weak open SPY<=-0.40%"),
    "G1": dict(fam="GUP", gap_min=0.02, trail=False, desc="GUP core: gap>=+2%, above VWAP, VWAP pullback hold 10:00-12:00"),
    "G2": dict(fam="GUP", gap_min=0.04, trail=False, desc="G1 gap>=+4%"),
    "G3": dict(fam="GUP", gap_min=0.02, rvol=2.0, trail=False, desc="G1 + rvol>=2"),
    "G4": dict(fam="GUP", gap_min=0.02, trail=True, desc="G1 TRAIL exit"),
    "G5": dict(fam="GUP", gap_min=0.02, spy_max=-0.002, trail=False, desc="G1 on weak-open days (SPY<=-0.20%)"),
}


def prep():
    C = pd.read_parquet(W / "cands.parquet"); E = pd.read_parquet(W / "elig.parquet")
    no_locked(C.date.unique()); no_locked(E.date.unique())
    C["per"] = C.date.map(period); C = C[C.per != "none"].copy()
    E["per"] = E.date.map(period); E = E[E.per != "none"].copy()
    E["crank"] = E.groupby("date").ret20.rank(pct=True)
    C = C.merge(E[["symbol", "date", "crank"]], on=["symbol", "date"], how="left")
    return C, E


def select(C, k):
    c = CONFIGS[k]; x = C[C.fam == c["fam"]]
    if c.get("crowd"):
        x = x[x.crank <= 0.30]
    if "gap_max" in c:
        x = x[x.gap <= c["gap_max"]]
    if "gap_min" in c:
        x = x[x.gap >= c["gap_min"]]
    if c.get("vratio"):
        x = x[x.vratio >= c["vratio"]]
    if c.get("sig_max"):
        x = x[x.sig_mm <= c["sig_max"]]
    if c.get("rvol"):
        x = x[x.rvol >= c["rvol"]]
    if c.get("spy_max") is not None:
        x = x[x.spy_r50 <= c["spy_max"]]
    if c.get("rs_min"):
        x = x[x.rs >= c["rs_min"]]
    if c["fam"] == "RSL":
        x = x.sort_values(["date", "rs"], ascending=[True, False]).groupby("date").head(10)
    else:
        x = x.sort_values(["date", "em", "adv20"], ascending=[True, True, False]).groupby("date").head(10)
    x = x.copy()
    t = c["trail"]
    px, kd = (x.px_t, x.k_t) if t else (x.px_h, x.k_h)
    x["px"], x["kind"] = px.to_numpy(), kd.to_numpy()
    x["r_gross"] = (x.px - x.entry) / x.risk
    x["r"] = livel(x.entry.to_numpy(), x.risk.to_numpy(), x.px.to_numpy(), x.kind.to_numpy())
    x["r_lr8"] = lr8(x.entry.to_numpy(), x.risk.to_numpy(), x.px.to_numpy(), x.kind.to_numpy(), x.em, x.gap.to_numpy())
    pxs, ks = (x.px_ts, x.k_ts) if t else (x.px_hs, x.k_hs)
    rs_ = x.e_s - x.stop
    ok = x.e_s.notna() & (rs_ > 0)
    st = livel(x.e_s.fillna(x.entry).to_numpy(), np.where(ok, rs_, x.risk), pxs.fillna(x.px).to_numpy(),
               ks.fillna(x.kind).to_numpy()) - 4e-4 * x.e_s.fillna(x.entry).to_numpy() / np.where(ok, rs_, x.risk)
    x["r_stress"] = np.where(ok, st, x.r - 4e-4 * x.entry / x.risk)
    x["cfg"] = k
    return x


def stats(x, col="r"):
    if not len(x):
        return dict(n=0)
    dm = x.groupby("date")[col].mean(); ds = x.groupby("date")[col].sum()
    nd = len(dm)
    t = float(dm.mean() / (dm.std(ddof=1) / np.sqrt(nd))) if nd > 2 and dm.std(ddof=1) > 0 else None
    tot = float(x[col].sum()); bd = ds.idxmax()
    wo = x[x.date != bd][col]
    return dict(n=int(len(x)), days=nd, mean=round(float(x[col].mean()), 4), t=None if t is None else round(t, 2),
                hit=round(float((x[col] > 0).mean()), 3), total=round(tot, 1),
                best_day=bd, best_share=round(float(ds.max() / tot), 3) if tot > 0 else None,
                wo_best=round(float(wo.mean()), 4) if len(wo) else None, per_day=round(float(ds.mean()), 3))


def make_req():
    C, E = prep()
    rng = np.random.default_rng(1127)
    pool = {d: g.symbol.to_numpy() for d, g in E[E.open >= 5].groupby("date")}
    reqs = []; rid = 0
    for k in CONFIGS:
        x = select(C, k)
        for r in x.itertuples():
            cand = pool[r.date]
            for dr in range(NDRAW):
                s = cand[rng.integers(len(cand))]
                if s == r.symbol:
                    s = cand[rng.integers(len(cand))]
                reqs.append((rid, k, dr, r.Index, s, r.date, r.tag, r.em, r.risk / r.entry, CONFIGS[k]["trail"], r.per))
                rid += 1
    R = pd.DataFrame(reqs, columns=["rid", "cfg", "draw", "src", "symbol", "date", "tag", "em", "rp", "trail", "per"])
    R.to_parquet(W / "req.parquet"); print("requests", len(R), R.groupby("cfg").size().to_dict())


def score(prim_csv):
    C, E = prep()
    S = pd.read_csv(W / "spy_days.csv"); S["per"] = S.date.map(period)
    S["dtype"] = np.where(S.oc > 0.0025, "UP", np.where(S.oc < -0.0025, "DOWN", "FLAT"))
    S["vday"] = (S.r50 <= -0.002) & (S.oc > 0)
    dtype = dict(zip(S.date, S.dtype)); vday = dict(zip(S.date, S.vday))
    P = pd.read_csv(prim_csv, dtype={"date": str}).set_index("date"); no_locked(P.index)
    req = pd.read_parquet(W / "req.parquet"); rnd = pd.read_parquet(W / "rand.parquet").merge(req, on="rid")
    rnd["r"] = livel(rnd.entry.to_numpy(), rnd.risk.to_numpy(), rnd.px.to_numpy(), rnd.kind.to_numpy())
    res = {"configs": {}, "n_configs": len(CONFIGS), "t_bar": TBAR}
    allx = []
    for k in CONFIGS:
        x = select(C, k); allx.append(x)
        o = {"desc": CONFIGS[k]["desc"]}
        oos = x[x.per.isin(["CHECK", "T2"])]
        for nm, g in [("FIT", x[x.per == "FIT"]), ("CHECK", x[x.per == "CHECK"]), ("T2", x[x.per == "T2"]), ("OOS", oos)]:
            o[nm] = stats(g); o[nm]["lr8"] = round(float(g.r_lr8.mean()), 4) if len(g) else None
            o[nm]["stress"] = round(float(g.r_stress.mean()), 4) if len(g) else None
            o[nm]["gross"] = round(float(g.r_gross.mean()), 4) if len(g) else None
        o["OOS_stress"] = stats(oos, "r_stress")
        # random control on OOS
        rr = rnd[(rnd.cfg == k) & rnd.per.isin(["CHECK", "T2"])]
        dm = rr.groupby("draw").r.mean().reindex(range(NDRAW))
        o["rand"] = dict(mean=round(float(dm.mean()), 4), p95=round(float(dm.quantile(0.95)), 4),
                         max=round(float(dm.max()), 4), beats=int((o["OOS"].get("mean", -9) > dm).sum()),
                         fill=round(float(len(rr) / max(1, len(oos) * NDRAW)), 3))
        # day types
        x["dtype"] = x.date.map(dtype); x["vday"] = x.date.map(vday).fillna(False)
        dt = {}
        for per in ("FIT", "CHECK", "T2"):
            g = x[x.per == per]; days = S[S.per == per]
            dd = {}
            for ty in ("UP", "FLAT", "DOWN"):
                gg = g[g.dtype == ty]; nday = int((days.dtype == ty).sum())
                dd[ty] = dict(n=len(gg), mean=round(float(gg.r.mean()), 3) if len(gg) else None,
                              R_per_mkt_day=round(float(gg.r.sum() / max(1, nday)), 3), mkt_days=nday)
            gg = g[g.vday]; nday = int(days.vday.sum())
            dd["V"] = dict(n=len(gg), mean=round(float(gg.r.mean()), 3) if len(gg) else None,
                           R_per_mkt_day=round(float(gg.r.sum() / max(1, nday)), 3), mkt_days=nday)
            dt[per] = dd
        o["daytype"] = dt
        # Primary hedge view (FIT+CHECK days)
        ds = x.groupby("date").r.sum().reindex(P.index).fillna(0.0)
        pr = P.prim_R
        q = pr <= pr.quantile(0.2)
        o["primary"] = dict(days=int(len(P)), corr=round(float(np.corrcoef(pr, ds)[0, 1]), 3),
                            corr_check=round(float(np.corrcoef(pr[P.index >= "2025-10-01"], ds[P.index >= "2025-10-01"])[0, 1]), 3),
                            R_on_prim_worst20=round(float(ds[q].mean()), 3), R_on_prim_other=round(float(ds[~q].mean()), 3),
                            prim_worst20_mean=round(float(pr[q].mean()), 2),
                            combined_worst20=round(float((pr + ds)[q].mean()), 2))
        a, ch, t2 = o["OOS"], o["CHECK"], o["T2"]
        bars = {"a_pos_check_t2": ch.get("n", 0) >= 30 and t2.get("n", 0) >= 30 and ch["mean"] > 0 and t2["mean"] > 0,
                "b_t_oos": (a.get("t") or 0) >= TBAR,
                "c_conc": a.get("best_share") is not None and a["best_share"] < 0.5 and (a.get("wo_best") or -9) > 0,
                "d_rand": a.get("n", 0) > 0 and a["mean"] > o["rand"]["p95"],
                "e_stress": (o["OOS"].get("stress") or -9) > 0}
        o["bars"] = bars
        if all(bars.values()):
            v = "PASS"
        elif bars["a_pos_check_t2"] and bars["c_conc"] and bars["e_stress"] and (a.get("t") or 0) >= 2.0:
            v = "LEAD"
        else:
            v = "FAIL"
        o["verdict"] = v
        res["configs"][k] = o
        print(k, v, "CHECK", ch.get("n"), ch.get("mean"), "T2", t2.get("n"), t2.get("mean"), "OOS t", a.get("t"),
              "stress", o["OOS"].get("stress"), "rand p95", o["rand"]["p95"], "corrP", o["primary"]["corr"], flush=True)
    X = pd.concat(allx); no_locked(X.date.unique())
    X[["cfg", "symbol", "date", "per", "em", "entry", "stop", "risk", "px", "kind", "r", "r_lr8", "r_stress", "gap"]] \
        .to_csv(W / "trades.csv.gz", index=False)
    json.dump(res, open(HERE / "results.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    if STAGE == "req":
        make_req()
    else:
        score(sys.argv[3])
