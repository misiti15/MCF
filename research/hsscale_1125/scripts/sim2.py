"""hsscale step 2: minute-by-minute Primary book for a lineup (cap 30 / setup, <= 3 lots / symbol / setup, 77 slots,
burst 30/10, per-setup -2R closed-R latch (optionally exempting the gap-down short family), -20R halt on closed + open),
recording the account and per-setup closed + open R path every minute; then the pre-registered Layer-2 rules
(PLAN.md) applied walk-forward, Q2.5N and an A12 direct re-simulation check. Layer-1 bench measures too.
Usage: python sim2.py WORK P4|P9 LAT|GDX [noslot]. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); LINE = sys.argv[2]; LAT = sys.argv[3]; NOSLOT = "noslot" in sys.argv[4:]
ACCT3 = "acct3" in sys.argv[4:]
SCALEHALT = "scalehalt" in sys.argv[4:]
HALT = {}
if SCALEHALT:
    _r = pd.read_csv(W / f"rules_{sys.argv[2]}_{sys.argv[3]}.csv.gz", usecols=["rule", "date", "X"])
    HALT = (0.6 * _r[_r.rule == "K4"].set_index("date").X).to_dict()
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "NM-ETF-late-dip-di-long"]
EXTRA = ["L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD", "RW7-gapdn-bounce-early-short-FD", "RW6-ns2-up3-short-FD",
         "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"]
SETUPS = P4 + (EXTRA if LINE == "P9" else [])
N = len(SETUPS)
SH = [x.split("-")[0] + "-" + (x.split("-")[3] if x.startswith("L3") else x.split("-")[1]) for x in SETUPS]
GD = {"L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD", "RW7-gapdn-bounce-early-short-FD"}
LATCH = np.array([not (LAT == "GDX" and s in GD) for s in SETUPS])
SLOTS = 10**9 if NOSLOT else 77
C = pd.read_parquet(W / "cand.parquet")
C = C[C.setup.isin(SETUPS)].copy()
PATH = np.load(W / "paths.npy", mmap_mode="r")
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)


def sim_day(g, flat_at=None, nonew_at=None):
    hl = HALT.get(g.date.iloc[0], 20.0)
    si = g.si.to_numpy(); sym = g.symbol.to_numpy(); side = g.side.to_numpy(float); ent = g.entry.to_numpy(float)
    risk = g.risk.to_numpy(float); tier = g.tier.to_numpy(float); ec = g.ecost.to_numpy(float); bo = g.borrow.to_numpy(float)
    em = g.em.to_numpy(int); xm = g.xm.to_numpy(int); rr = g.r.to_numpy(float); off = g.off.to_numpy(int); n = g.n.to_numpy(int)
    by_m = {}
    for k in range(len(g)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int)
    open_ = []; entered = []
    halted = noentry = stopped = False
    recent = [[] for _ in range(N)]
    acct = np.full(390, np.nan, np.float32); per = np.full((390, N), np.nan, np.float32)
    nopen = np.zeros(390, np.int16); maxsym = np.zeros(390, np.int16); ent_m = np.zeros((390, N), np.int16)
    fire_m = None
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]
            else:
                keep.append(k)
        open_ = keep
    for m in range(m0, 956):
        if m > last and not open_:
            break
        for k in by_m.get(m, ()):
            realize(m)
            s = si[k]
            if halted or noentry or stopped:
                continue
            if LATCH[s] and realized[s] <= -2.0 + 1e-12:
                continue
            if len(open_) >= SLOTS:
                continue
            if sum(1 for q in open_ if si[q] == s) >= 30:
                continue
            if sum(1 for q in open_ if si[q] == s and sym[q] == sym[k]) >= 3:
                continue
            if ACCT3 and (sum(1 for q in open_ if sym[q] == sym[k]) >= 3 or any(sym[q] == sym[k] and side[q] != side[k] for q in open_)):
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); nl[s] += 1; open_.append(k); entered.append(k)
            ent_m[m - 570, s] += 1
        realize(m)
        i = m - 570
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = np.where(n[o] > 0, PATH[off[o] + np.maximum(j, 0)], ent[o])
            mk = (side[o] * (c - ent[o]) - tier[o] * (ec[o] + 0.01 + c * 1e-4) - bo[o]) / risk[o]
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
            from collections import Counter
            maxsym[i] = max(Counter(sym[o]).values())
        else:
            mk = np.zeros(0); ps = realized.copy()
        tot = ps.sum()
        acct[i] = tot; per[i] = ps; nopen[i] = len(open_)
        if tot <= -hl + 1e-12:
            halted = True
        if nonew_at is not None and not noentry and tot <= -nonew_at + 1e-12:
            noentry = True
        if flat_at is not None and not stopped and tot <= -flat_at + 1e-12:
            stopped = True; fire_m = m
            for k, v in zip(open_, mk):
                realized[si[k]] += v
            open_ = []
            # path after the flatten is flat
    for k in open_:
        realized[si[k]] += rr[k]
    return dict(final=realized.copy(), lots=nl, acct=acct, per=per, nopen=nopen, maxsym=maxsym, ent_m=ent_m,
                em_entered=em[entered], si_entered=si[entered], fire_m=fire_m)


if __name__ == "__main__":
    tag = f"{LINE}_{LAT}" + ("_noslot" if NOSLOT else "") + ("_acct3" if ACCT3 else "") + ("_scalehalt" if SCALEHALT else "")
    days = {d: g for d, g in C.groupby("date")}
    D = sorted(days)
    res = {}
    for k, d in enumerate(D):
        res[d] = sim_day(days[d])
        if k % 100 == 0:
            print(tag, k, len(D), flush=True)
    # compact per-day base table + per-minute arrays kept in memory
    rows = []
    for d in D:
        r = res[d]
        a = np.nan_to_num(r["acct"].astype(float), nan=np.nan)
        valid = ~np.isnan(a)
        trough = float(np.nanmin(a)) if valid.any() else 0.0
        rows.append(dict(date=d, final=r["final"].sum(), trough=min(trough, 0.0), lots=int(r["lots"].sum()),
                         peak_open=int(r["nopen"].max()), peak_sym=int(r["maxsym"].max()),
                         max_ent5=int(max(np.convolve(r["ent_m"][:, s], np.ones(5, int), "valid").max() for s in range(N))),
                         **{f"R_{SH[i]}": r["final"][i] for i, s in enumerate(SETUPS)},
                         **{f"L_{SH[i]}": int(r["lots"][i]) for i, s in enumerate(SETUPS)}))
        # R-velocity: worst drop over 2 and 10 minutes (account path, ffill)
        f = pd.Series(a).ffill().fillna(0).to_numpy()
        rows[-1]["drop2"] = float(min(0.0, (f[2:] - np.maximum.accumulate(f)[:-2]).min() if len(f) > 2 else 0.0))
        def wd(w):
            best = 0.0
            for lag in range(1, w + 1):
                best = min(best, (f[lag:] - f[:-lag]).min())
            return best
        rows[-1]["drop2"] = wd(2); rows[-1]["drop10"] = wd(10); rows[-1]["drop1"] = wd(1)
    B = pd.DataFrame(rows)
    B.to_csv(W / f"base_{tag}.csv", index=False)
    print(tag, "base total", round(B.final.sum(), 1), "lots", B.lots.sum(), "days", len(B))
    for i, s in enumerate(SETUPS):
        print("  ", s[:40], round(B[f"R_{SH[i]}"].sum(), 1), B[f"L_{SH[i]}"].sum())
    # ---- walk-forward thresholds (ISO week; trailing <= 250 sessions, min 120)
    dts = pd.to_datetime(B.date)
    wk = (dts.dt.isocalendar().year.astype(str) + "-" + dts.dt.isocalendar().week.astype(str).str.zfill(2)).to_numpy()
    lo, hi = 2.5 * N, 8.0 * N
    X = {r: np.full(len(B), np.nan) for r in ("A12", "A3N", "Q1", "Q2.5", "Q5", "K3", "K4")}
    first = {}
    for i, w in enumerate(wk):
        first.setdefault(w, i)
    for i, w in enumerate(wk):
        j = first[w]
        if j < 120:
            continue
        tr = B.trough.to_numpy()[max(0, j - 250):j]; fi = B.final.to_numpy()[max(0, j - 250):j]
        X["A12"][i] = 12.0; X["A3N"][i] = 3.0 * N
        for q, nm in ((1, "Q1"), (2.5, "Q2.5"), (5, "Q5")):
            X[nm][i] = np.clip(-np.percentile(tr, q), lo, hi)
        sd = fi.std(ddof=1)
        X["K3"][i] = np.clip(3 * sd, lo, hi); X["K4"][i] = np.clip(4 * sd, lo, hi)
    scored = ~np.isnan(X["A12"])
    out = []
    for i, d in enumerate(D):
        if not scored[i]:
            continue
        r = res[d]
        a = r["acct"]
        out.append(dict(rule="none", date=d, X=np.nan, fire_m=None, **{s: float(r["final"][k]) for k, s in enumerate(SETUPS)},
                        lots_after=0))
        f = pd.Series(a.astype(float)).ffill().fillna(0).to_numpy()
        def vel(w, thr):
            best = np.full(len(f), np.inf)
            for lag in range(1, w + 1):
                best[lag:] = np.minimum(best[lag:], f[lag:] - f[:-lag])
            return np.flatnonzero(best <= -thr + 1e-9)
        x4 = X["K4"][i]
        v1 = vel(2, max(8.0, 0.5 * x4)); v2 = vel(10, max(12.0, 0.75 * x4)); k4 = np.flatnonzero(a <= -x4 + 1e-9)
        extra = {"V1": v1, "V2": v2, "K4V": np.sort(np.concatenate([v1[:1], v2[:1], k4[:1]]))}
        for nm, xs in list(X.items()) + [(k, None) for k in extra]:
            x = xs[i] if xs is not None else x4
            hit = extra[nm] if xs is None else np.flatnonzero(a <= -x + 1e-9)
            if len(hit):
                h = hit[0]
                fm = h + 570
                vals = r["per"][h].astype(float)
                la = int((r["em_entered"] > fm).sum())
            else:
                fm, vals, la = None, r["final"], 0
            out.append(dict(rule=nm, date=d, X=x, fire_m=fm, **{s: float(vals[k]) for k, s in enumerate(SETUPS)},
                            lots_after=la))
    # ---- exploratory (post-registration, counted): per-setup disaster cap on closed + open R (flatten + latch that setup)
    for L in (6.0, 8.0):
        for i, d in enumerate(D):
            if not scored[i]:
                continue
            r = res[d]; vals = r["final"].astype(float).copy(); fm = None; la = 0
            for k in range(N):
                h = np.flatnonzero(r["per"][:, k] <= -L + 1e-9)
                if len(h):
                    vals[k] = float(r["per"][h[0], k]); fm = h[0] + 570 if fm is None else min(fm, h[0] + 570)
                    la += int(((r["em_entered"] > h[0] + 570) & (r["si_entered"] == k)).sum())
            out.append(dict(rule=f"S{int(L)}", date=d, X=L, fire_m=fm, **{s: float(vals[k]) for k, s in enumerate(SETUPS)}, lots_after=la))
    # ---- Q2.5N (two-stage) and A12 direct check: re-simulations
    for nm in ("Q2.5N", "A12direct"):
        for i, d in enumerate(D):
            if not scored[i]:
                continue
            x = X["Q2.5"][i] if nm == "Q2.5N" else 12.0
            rr_ = sim_day(days[d], flat_at=x, nonew_at=0.6 * x if nm == "Q2.5N" else None)
            fm = rr_["fire_m"]
            # lots removed vs base (entered lots difference), for the neutral approximation
            la = int(res[d]["lots"].sum() - rr_["lots"].sum())
            # first minute the no-new stage bit (account path <= -0.6x) for reporting
            out.append(dict(rule=nm, date=d, X=x, fire_m=fm if fm is not None else (
                int(np.flatnonzero(res[d]["acct"] <= -0.6 * x + 1e-9)[0] + 570) if nm == "Q2.5N" and (res[d]["acct"] <= -0.6 * x + 1e-9).any() else None),
                **{s: float(rr_["final"][k]) for k, s in enumerate(SETUPS)}, lots_after=la))
    O = pd.DataFrame(out)
    O.to_csv(W / f"rules_{tag}.csv.gz", index=False)
    print(tag, "done", O.groupby("rule")[SETUPS].sum().sum(1).round(1).to_dict())
