"""LONGBOOK-1127 book + score (PREREG.md). Builds candidate lots (LIVE-L / LR8 costs) from lb_gen.py walks, runs the E4
Primary book (cfprimary_1127 e4nb.py logic, 5 setup slots, per-setup caps) for REF (P4) and P4 + one long (C30 / C10),
the K=20 random-minute shadow books and the stress book, and scores the PREREG bars. Usage (cwd repo):
python lb_book.py W OUT. Locked block filtered + asserted absent. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
from numba import njit, prange

sys.path.insert(0, "."); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
sys.path.insert(0, "research/cfprimary_1127")
import calib_live as CL  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
LOCK = ("2024-11-01", "2025-02-28")
TZ = "America/New_York"
SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
LONGS = ["CWT14-failbrk-orl-p10-long-WB5", "ULT-05-withgap-cont-long",
         "GEN-261027-10-FlowShiftlem1p2-MACDhge0p079-SMA20dge0p59-LUNCH-BRopgt0p65-holdtr-long",
         "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long"]
SHORT = {LONGS[0]: "L1 CWT14-WB5", LONGS[1]: "L2 ULT-05", LONGS[2]: "L3 GEN-261027-10", LONGS[3]: "L4 GEN-261023-07"}
K = 20
N = 5


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


def m2hm(m):
    m = np.asarray(m, int)
    return (m // 60) * 100 + m % 60


def build():
    parts, paths, base = [], [], 0
    for tag in ("t1", "t2"):
        a = pd.read_parquet(W / f"walk_{tag}.parquet")
        p = np.load(W / f"paths_{tag}.npy")
        a["off"] = a["off"] + base; base += len(p)
        parts.append(a); paths.append(p)
    x = pd.concat(parts, ignore_index=True); PATH = np.concatenate(paths).astype(np.float64)
    x["date"] = x.date.astype(str)
    no_locked(x.date.unique())
    x["per"] = x.date.map(period)
    x = x[(x.per != "none") & x.setup.isin(P4 + LONGS) & x.px.notna()].copy()
    etb = pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    x = x[~(x.setup.isin(P4) & (x.shadow >= 0))]
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    tod = m2hm(x.em.to_numpy())
    tier = np.where((np.abs(x.gap) >= 20) | (x.entry < 5), 3.0, 1.0)
    ecost = (0.01 + x.entry * 1e-4) * tod_cost_mult(tod)
    xcost = np.where(x.kind == 2, 0.0, 0.01 + x.px * 1e-4) + np.where(x.kind == 1, 0.02, 0.0)
    borrow = np.where(x.side < 0, 1.2e-4 * x.entry, 0.0)
    gross = x.side * (x.px - x.entry)
    x["r_gross"] = gross / x.risk
    x["r_lr8"] = (gross - tier * (ecost + xcost) - borrow) / x.risk
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    ll = x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
    x["r"] = np.where(x.setup == P4[3], x.r_lr8, ll)          # NM-ETF LR8 research (as every E4 study)
    # stress for real candidate-long lots: +1 min entry (same levels) + 2 bp per side
    ok = x.px_s.notna() & x.setup.isin(LONGS) & (x.shadow < 0)
    kds = np.where(x.kind_s == 2, "target", np.where(x.kind_s == 1, "stop", "market"))
    rs = (x.px_s - x.entry_s) / x.risk_s - CL.predict_R(cells, x.entry_s.fillna(x.entry).to_numpy(),
                                                        x.risk_s.fillna(x.risk).to_numpy(), kds) \
        - 4e-4 * x.entry_s / x.risk_s
    x["r_stress"] = np.where(ok, rs, np.where(x.setup.isin(LONGS) & (x.shadow < 0), -1.0, x.r))
    x["lcost"] = x.r_gross - x.r
    x["grp"] = x.setup.map({s: i for i, s in enumerate(LONGS)}).fillna(-1).astype(int)
    x["si"] = np.where(x.grp >= 0, 4, x.setup.map({s: i for i, s in enumerate(P4)}).fillna(-1)).astype(int)
    x = x.sort_values(["date", "em", "si", "symbol", "shadow"], kind="mergesort").reset_index(drop=True)
    x["sym"] = x.groupby("date").symbol.transform(lambda s: pd.factorize(s)[0])
    x["xm"] = np.maximum(x.xm, x.em + 1)
    return x, PATH


@njit(cache=True)
def sim_day(a, b, si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, caps, lo, path, outR, outN):
    realized = np.zeros(N); nl = np.zeros(N, np.int64)
    latched = np.zeros(N, np.bool_); olat = np.zeros(N, np.bool_)
    cnt = np.zeros(N, np.int64)
    nsym = 0
    for k in range(a, b):
        if sym[k] + 1 > nsym:
            nsym = sym[k] + 1
    symcnt = np.zeros((N, nsym + 1), np.int64)
    entm = np.zeros((N, 1000), np.int64)
    opn = np.empty(b - a, np.int64); no = 0
    m0 = 10 ** 9; last = -1
    for k in range(a, b):
        if keep[k]:
            if em[k] < m0:
                m0 = em[k]
            if em[k] > last:
                last = em[k]
    if last < 0:
        return
    halted = False
    p = a
    for m in range(m0, 956):
        if m > last and no == 0:
            break
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
            else:
                opn[q] = k; q += 1
        no = q
        for s in range(N):
            if realized[s] <= -2.0 + 1e-12:
                latched[s] = True
        while p < b and em[p] < m:
            p += 1
        while p < b and em[p] == m:
            k = p; p += 1
            if not keep[k]:
                continue
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if no >= 77 or cnt[s] >= caps[s] or symcnt[s, sym[k]] >= 3:
                continue
            rc = 0
            for t in range(max(m - 9, 0), m + 1):
                rc += entm[s, t]
            if rc >= 30:
                continue
            entm[s, m] += 1; nl[s] += 1; opn[no] = k; no += 1; cnt[s] += 1; symcnt[s, sym[k]] += 1
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
            else:
                opn[q] = k; q += 1
        no = q
        ps = realized.copy()
        for i in range(no):
            k = opn[i]
            j = min(m - em[k], n[k] - 1)
            if j < 0:
                j = 0
            c = path[off[k] + j]
            ps[si[k]] += side[k] * (c - ent[k]) / risk[k] - lc[k]
        if lo:
            for s in range(N):
                if ps[s] <= -2.0 + 1e-12:
                    olat[s] = True
        if ps.sum() <= -20.0 + 1e-12:
            halted = True
    for i in range(no):
        k = opn[i]
        realized[si[k]] += rr[k]
    for s in range(N):
        outR[s] = realized[s]; outN[s] = nl[s]


@njit(parallel=True, cache=True)
def run_days(st, si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, caps, lo, path):
    D = len(st) - 1
    R = np.zeros((D, N)); NL = np.zeros((D, N), np.int64)
    for d in prange(D):
        sim_day(st[d], st[d + 1], si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, caps, lo, path, R[d], NL[d])
    return R, NL


def spy_days(days):
    out = {}
    for src, ds in ((Path("/home/user/MCF/data/cache_hist/1Min"), [d for d in days if d >= "2024-09-16"]),
                    (Path("/home/user/MCF/data/cache_fresh/1Min"), [d for d in days if d < "2024-09-16"])):
        f = pads.field("__index_level_0__")
        flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
        b = pads.dataset(str(src / "SPY.parquet"), format="parquet").to_table(filter=flt).to_pandas()
        if "__index_level_0__" in b.columns:
            b = b.set_index("__index_level_0__")
        b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
        mm = b.index.hour * 60 + b.index.minute
        b = b[(mm >= 570) & (mm < 960)]
        no_locked(np.unique(b.index.date.astype(str)))
        g = b.groupby(b.index.date.astype(str)).agg(o=("open", "first"), c=("close", "last"))
        for d in ds:
            if d in g.index:
                out[d] = g.loc[d, "c"] / g.loc[d, "o"] - 1
    return out


def tstat(d):
    s = d.std(ddof=1)
    return float(d.mean() / (s / np.sqrt(len(d)))) if s > 0 else 0.0


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    x, PATH = build()
    DAYS = x.date.drop_duplicates().tolist()
    no_locked(DAYS)
    st = np.r_[np.flatnonzero(x.date.ne(x.date.shift()).to_numpy()), len(x)].astype(np.int64)
    PER = np.array([period(d) for d in DAYS])
    A = {k: x[k].to_numpy(np.int64) for k in ("si", "sym", "em", "xm", "off", "n")}
    F = {k: x[k].to_numpy(np.float64) for k in ("side", "entry", "risk", "lcost", "r", "r_lr8", "r_stress")}
    grp, sh = x.grp.to_numpy(), x.shadow.to_numpy()
    p4 = x.si.to_numpy() < 4

    def run(keep, cap5, rr="r", lc=None):
        caps = np.array([30, 30, 30, 30, cap5], np.int64)
        lcv = F["lcost"] if lc is None else lc
        R, NL = run_days(st, A["si"], A["sym"], F["side"], F["entry"], F["risk"], lcv, A["em"], A["xm"], F[rr],
                         A["off"], A["n"], keep, caps, False, PATH)
        return R, NL

    # parity: 5-slot engine with P4 only vs cfprimary e4nb (4 slots) on the same lots
    import e4nb as E
    sub = np.flatnonzero(p4)
    xs = x.iloc[sub]
    st4 = np.r_[np.flatnonzero(xs.date.ne(xs.date.shift()).to_numpy()), len(xs)].astype(np.int64)
    A4 = dict(si=xs.si.to_numpy(np.int64), sym=xs.sym.to_numpy(np.int64), side=xs.side.to_numpy(np.float64),
              ent=xs.entry.to_numpy(np.float64), risk=xs.risk.to_numpy(np.float64), lc=xs.lcost.to_numpy(np.float64),
              em=xs.em.to_numpy(np.int64), xm=xs.xm.to_numpy(np.int64), rr=xs.r.to_numpy(np.float64),
              off=xs.off.to_numpy(np.int64), n=xs.n.to_numpy(np.int64))
    days4 = xs.date.drop_duplicates().tolist()
    R4, _, _ = E.run(A4, st4, PATH, np.arange(len(days4)), np.ones(len(xs), bool), False)
    REF, NREF = run(p4.copy(), 30)
    ref_by_day = pd.Series(REF.sum(1), index=DAYS)
    par = float(np.abs(ref_by_day.reindex(days4).fillna(0).to_numpy() - R4.sum(1)).max())
    print("parity max abs day diff", par, flush=True)
    assert par < 0.01
    spy = spy_days(DAYS)
    dtype = np.array([("up" if spy.get(d, 0) >= 0.0025 else "down" if spy.get(d, 0) <= -0.0025 else "quiet")
                      if d in spy else "na" for d in DAYS])
    res = {"parity": par, "days": {p: int((PER == p).sum()) for p in ("FIT", "CHECK", "T2")},
           "lots": x[x.shadow < 0].groupby(["setup", "per"]).size().unstack().fillna(0).astype(int).to_dict("index"),
           "raw": {}}
    # raw (unbooked) candidate long stats, first signal rows = real lots
    for L in LONGS:
        for p in ("FIT", "CHECK", "T2"):
            q = x[(x.setup == L) & (x.shadow < 0) & (x.per == p)]
            if len(q):
                dd = q.groupby("date").r.sum()
                e = q.r - q.r.mean(); ec = e.groupby(q.date).sum()
                res["raw"][f"{SHORT[L]}|{p}"] = dict(n=len(q), r=float(q.r.mean()), r_lr8=float(q.r_lr8.mean()),
                                                     gross=float(q.r_gross.mean()),
                                                     t=float(q.r.mean() * len(q) / np.sqrt((ec ** 2).sum())),
                                                     per_day=float(len(q) / max((PER == p).sum(), 1)))
    rows = []
    daily = {"REF": REF}
    for gi, L in enumerate(LONGS):
        for cap in (30, 10):
            name = f"{SHORT[L]} C{cap}"
            keep = p4 | ((grp == gi) & (sh < 0))
            Rc, Nc = run(keep, cap)
            Rl8, _ = run(keep, cap, rr="r_lr8")
            Rst, _ = run(keep, cap, rr="r_stress")
            rnd = np.zeros((K, len(DAYS)))
            for j in range(K):
                Rr, _ = run(p4 | ((grp == gi) & (sh == j)), cap)
                rnd[j] = Rr.sum(1)
            daily[name] = Rc
            for p in ("FIT", "CHECK", "T2"):
                ix = PER == p
                if ix.sum() < 3:
                    continue
                r0, r1 = REF[ix].sum(1), Rc[ix].sum(1)
                d = r1 - r0; nd = len(d)
                short0 = REF[ix][:, :3].sum(1)
                lg = Rc[ix][:, 4]
                tot = d.sum(); bi = int(np.argmax(d)) if tot > 0 else int(np.argmin(d))
                rd = rnd[:, ix].sum(1) / nd - r0.mean()
                w5 = lambda v: float(np.sort(v)[:5].mean())  # noqa: E731
                row = dict(cfg=name, per=p, n_days=nd, lots_long=int(Nc[ix][:, 4].sum()),
                           ref=float(r0.mean()), cfg_R=float(r1.mean()), dR=float(d.mean()), t=tstat(d),
                           dR_lr8=float((Rl8[ix].sum(1) - r0).mean()), dR_stress=float((Rst[ix].sum(1) - r0).mean()),
                           long_R_day=float(lg.mean()), corr_short=float(np.corrcoef(lg, short0)[0, 1]) if lg.std() > 0 else np.nan,
                           w5_ref=w5(r0), w5_cfg=w5(r1), red_ref=float((r0 < 0).mean() * 21), red_cfg=float((r1 < 0).mean() * 21),
                           le10_ref=int((r0 <= -10).sum()), le10_cfg=int((r1 <= -10).sum()),
                           best_share=float(d[bi] / tot) if tot else np.nan,
                           dR_wo_best=float(np.delete(d, int(np.argmax(d))).mean()),
                           rnd_mean=float(rd.mean()), rnd_p95=float(np.percentile(rd, 95)),
                           pctile=float((rd < d.mean()).mean() * 100),
                           setup_dR_month=[float(v) for v in (Rc[ix][:, :4] - REF[ix][:, :4]).sum(0) / nd * 21])
                for dt in ("up", "down", "quiet"):
                    m = dtype[ix] == dt
                    row[f"dR_{dt}"] = float(d[m].mean()) if m.any() else np.nan
                    row[f"n_{dt}"] = int(m.sum())
                    row[f"ref_{dt}"] = float(r0[m].mean()) if m.any() else np.nan
                if p != "FIT":
                    ok = [row["dR"] > 0, row["t"] >= 2.5, row["dR"] > row["rnd_p95"], row["w5_cfg"] >= 1.05 * row["w5_ref"],
                          row["red_cfg"] <= row["red_ref"], row["best_share"] < 0.25 and row["dR_wo_best"] > 0,
                          row["dR_stress"] > 0, min(row["setup_dR_month"]) >= -2.0]
                    row.update({f"bar{i + 1}": bool(v) for i, v in enumerate(ok)}, all_bar=bool(all(ok)))
                    row["lead_core"] = bool(ok[0] and ok[3] and ok[5] and ok[6] and row["t"] >= 1.5)
                rows.append(row)
                print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items() if k != "setup_dR_month"},
                      flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "results.csv", index=False)
    verdict = {}
    for c in df.cfg.unique():
        s = df[(df.cfg == c) & (df.per != "FIT")]
        if s.per.nunique() < 2:
            verdict[c] = "INCOMPLETE"; continue
        verdict[c] = "PASS" if s.all_bar.all() else ("LEAD" if s.lead_core.all() else "FAIL")
    res["verdict"] = verdict
    res["ref"] = {p: dict(R_day=float(REF[PER == p].sum(1).mean()), short_R_day=float(REF[PER == p][:, :3].sum(1).mean()),
                          etf_R_day=float(REF[PER == p][:, 3].mean()),
                          by_type={dt: float(REF[(PER == p) & (dtype == dt)].sum(1).mean()) for dt in ("up", "down", "quiet")})
                  for p in ("FIT", "CHECK", "T2")}
    pd.DataFrame({k: v.sum(1) for k, v in daily.items()}).assign(date=DAYS, per=PER, dtype=dtype).to_csv(OUT / "daily.csv", index=False)
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "lots"}, indent=1, default=float))
