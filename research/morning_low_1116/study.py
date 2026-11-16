"""Morning-low study (owner 2026-11-16, "10:25 study" widened to 25-minute windows 09:50-11:25).

Q1 where is the 09:50-11:30 SPY low; Q2 does buying a point-in-time "turn" at the end of each window pay;
Q3 every cell reported with the try-count bar max(1.5, sqrt(2 ln N)).
Locked block 2024-11-01..2025-02-28 is never read. TRAIN <= 2025-12-31, VALID 2026-01-01 onward.
Inputs: data/cache_hist/1Min/{SPY,QQQ,SPXL,TQQQ}.parquet + a read-only fetch of later sessions (argv[1], optional).
Educational only - not financial advice.
"""
import sys, json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
import os
ROOT = Path(os.environ.get("MCF_ROOT", HERE.parents[1]))
SYMS = ["SPY", "QQQ", "SPXL", "TQQQ"]
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TRAIN_END = pd.Timestamp("2025-12-31").date()
M0 = 9 * 60 + 30                      # minute index 0 = 09:30 bar
D0, D1 = 20, 120                      # 09:50 .. 11:29 bar (low window 09:50-11:30)
WSTARTS = list(range(20, 95, 5))      # 09:50 .. 11:00 starts, 25-min windows -> 15
HOR = [30, 60, 90, "1555"]
RNG = np.random.default_rng(1116)


def load():
    rec = pd.read_parquet(sys.argv[1]) if len(sys.argv) > 1 else None
    out = {}
    for s in SYMS:
        d = pd.read_parquet(ROOT / "data/cache_hist/1Min" / f"{s}.parquet")
        d.index = d.index.tz_convert("America/New_York")
        if rec is not None:
            r = rec[rec.symbol == s].set_index("ts")[["open", "high", "low", "close", "volume"]]
            r.index = r.index.tz_convert("America/New_York")
            d = pd.concat([d, r[r.index > d.index.max()]])
        d = d[(d.index.hour * 60 + d.index.minute >= M0) & (d.index.hour * 60 + d.index.minute < 16 * 60)]
        out[s] = d
    return out


def to_grid(d, min_bars=380):
    """day -> 390x4 array (o,h,l,c) + volume, forward-filled; None if < 380 real bars."""
    g = {}
    for day, x in d.groupby(d.index.date):
        if LOCK[0] <= day <= LOCK[1]:
            continue                                   # locked block: never read
        if len(x) < min_bars:
            continue
        m = (x.index.hour * 60 + x.index.minute - M0).values
        a = np.full((390, 5), np.nan)
        a[m] = x[["open", "high", "low", "close", "volume"]].values
        v = np.nan_to_num(a[:, 4])
        a = pd.DataFrame(a).ffill().bfill().to_numpy(copy=True)
        a[:, 4] = v
        g[day] = a
    return g


def low_minute(a, lo=D0, hi=D1):
    return lo + int(np.argmin(a[lo:hi, 2]))


def shuffle_null(a, n=200):
    """Permute the 09:50-11:29 bars as relative moves (close-to-close, low offset) within the day."""
    c_prev = a[D0 - 1:D1 - 1, 3]
    r = a[D0:D1, 3] / c_prev
    lo = a[D0:D1, 2] / c_prev
    out = np.zeros(D1 - D0)
    for _ in range(n):
        p = RNG.permutation(D1 - D0)
        path = np.concatenate([[1.0], np.cumprod(r[p])[:-1]])
        out[np.argmin(path * lo[p])] += 1
    return out / n


def arcsine_null(T=D1 - D0):
    """Discrete random-walk argmin law (arcsine), lows on bar lows ~ argmin over T bars."""
    t = np.arange(T + 1) / T
    F = 2 / np.pi * np.arcsin(np.sqrt(t))
    return np.diff(F)


def main():
    raw = load()
    G = {s: to_grid(raw[s], 380 if s in ("SPY", "QQQ") else 150) for s in SYMS}
    G["SPY_partial"] = to_grid(raw["SPY"], 60)
    days = sorted(set(G["SPY"]) & set(G["QQQ"]))
    full = [d for d in days if d < pd.Timestamp("2026-11-16").date()]   # 11-16 is a partial session
    split = {d: ("TRAIN" if d <= TRAIN_END else "VALID") for d in full}
    print(len(full), "sessions", full[0], full[-1], sum(v == "TRAIN" for v in split.values()), "train")

    # ---------------- Q1 ----------------
    rows = []
    shuf = np.zeros(D1 - D0)
    for d in full:
        a = G["SPY"][d]
        o930 = a[0, 0]; c950 = a[D0 - 1, 3]
        hi20, lo20 = a[:D0, 1].max(), a[:D0, 2].min()
        mid = (hi20 + lo20) / 2
        rows.append(dict(day=d, split=split[d], lowm=low_minute(a), lowm930=low_minute(a, 0, D1),
                         weak_open=c950 < o930, weak_mid=c950 < mid,
                         low_at_950=a[D0:D1, 2].min() <= lo20))
        shuf += shuffle_null(a)
    q1 = pd.DataFrame(rows)
    shuf /= len(full)
    arc = arcsine_null()
    q1.to_csv(HERE / "q1_days.csv", index=False)

    def win_share(lm, s):
        return np.mean((lm >= s) & (lm < s + 25))

    groups = {"all": q1.index == q1.index, "weak_open": q1.weak_open, "strong_open": ~q1.weak_open,
              "weak_mid": q1.weak_mid, "strong_mid": ~q1.weak_mid}
    q1cells = []
    for gname, msk in groups.items():
        sub = q1[msk]
        for s in WSTARTS:
            nul_s = shuf[s - D0:s - D0 + 25].sum(); nul_a = arc[s - D0:s - D0 + 25].sum()
            for sp in ["ALL", "TRAIN", "VALID"]:
                ss = sub if sp == "ALL" else sub[sub.split == sp]
                p = win_share(ss.lowm.values, s); n = len(ss)
                se = math.sqrt(max(nul_s * (1 - nul_s), 1e-9) / n)
                q1cells.append(dict(group=gname, win=f"{(M0+s)//60:02d}:{(M0+s)%60:02d}", split=sp, n=n,
                                    share=round(p, 4), null_shuffle=round(nul_s, 4), null_arcsine=round(nul_a, 4),
                                    z_vs_shuffle=round((p - nul_s) / se, 2)))
    q1c = pd.DataFrame(q1cells)
    q1c.to_csv(HERE / "q1_windows.csv", index=False)
    # 5-min histogram
    b = ((q1.lowm - D0) // 5)
    hist = pd.DataFrame({"bucket": [f"{(M0+D0+5*i)//60:02d}:{(M0+D0+5*i)%60:02d}" for i in range(20)],
                         "share": [np.mean(b == i) for i in range(20)],
                         "null_shuffle": [shuf[5*i:5*i+5].sum() for i in range(20)],
                         "null_arcsine": [arc[5*i:5*i+5].sum() for i in range(20)]})
    b2 = q1.lowm930 // 5
    hist930 = pd.DataFrame({"bucket": [f"{(M0+5*i)//60:02d}:{(M0+5*i)%60:02d}" for i in range(24)],
                            "share": [np.mean(b2 == i) for i in range(24)]})
    hist.to_csv(HERE / "q1_hist5.csv", index=False); hist930.to_csv(HERE / "q1_hist5_from0930.csv", index=False)

    # ---------------- Q2 ----------------
    def fwd(a, e, h):
        ex = 385 - 1 if h == "1555" else e - 1 + h      # close of 15:54 bar = price at 15:55
        return (a[ex, 3] / a[e - 1, 3] - 1) * 1e4
    sig = []
    for d in full:
        a = G["SPY"][d]; q = G["QQQ"][d]
        tp = (a[:, 1] + a[:, 2] + a[:, 3]) / 3
        for s in WSTARTS:
            e = s + 25
            run_lo_before = a[D0:s, 2].min() if s > D0 else np.inf
            wlo = a[s:e, 2].min()
            newlow = wlo < run_lo_before
            c = a[e - 1, 3]
            vw = (tp[D0:e] * a[D0:e, 4]).sum() / max(a[D0:e, 4].sum(), 1)
            defs = {"D1_reclaim_wstart": newlow and c > a[s - 1, 3],
                    "D2_up15bp_off_wlow": newlow and c >= wlo * 1.0015,
                    "D3_above_vwap950": newlow and c > vw}
            r = {f"{sym}_{h}": fwd(x, e, h) for sym, x in (("SPY", a), ("QQQ", q)) for h in HOR}
            # owner 2026-11-16: did price undercut the window low before the horizon exit? (turn failed)
            ll = {f"{sym}_{h}_ll": bool(x[e:(385 if h == "1555" else e + h), 2].min() < x[s:e, 2].min())
                  for sym, x in (("SPY", a), ("QQQ", q)) for h in HOR}
            dip = (a[D0 - 1, 3] - wlo) / a[D0 - 1, 3] * 1e4          # bps below the 09:50 price
            sig.append(dict(day=d, split=split[d], win=s, wlo=wlo, newlow=newlow, dip_bps=dip, **defs, **r, **ll))
    S = pd.DataFrame(sig)
    S.to_csv(HERE / "q2_panel.csv.gz", index=False)

    DEFS = ["D1_reclaim_wstart", "D2_up15bp_off_wlow", "D3_above_vwap950"]
    cells = []
    for s in WSTARTS:
        for dn in DEFS:
            for sym in ["SPY", "QQQ"]:
                for h in HOR:
                    col = f"{sym}_{h}"
                    for sp in ["TRAIN", "VALID", "ALL"]:
                        P = S[(S.win == s)] if sp == "ALL" else S[(S.win == s) & (S.split == sp)]
                        R = S if sp == "ALL" else S[S.split == sp]
                        x = P[P[dn]][col].values
                        null_same = P[col].mean()                    # same minute, all days
                        null_rand = R[col].mean()                    # all 15 decision minutes, all days
                        n = len(x)
                        ex = x.mean() - null_same if n else np.nan
                        t = ex / (x.std(ddof=1) / math.sqrt(n)) if n > 2 else np.nan
                        cells.append(dict(win=f"{(M0+s+25)//60:02d}:{(M0+s+25)%60:02d}",
                                          wstart=f"{(M0+s)//60:02d}:{(M0+s)%60:02d}", defn=dn, sym=sym, h=str(h),
                                          split=sp, n=n, freq=round(n / len(P), 3), mean_bps=round(x.mean(), 2) if n else np.nan,
                                          hit=round((x > 0).mean(), 3) if n else np.nan,
                                          null_same_bps=round(null_same, 2), null_rand_bps=round(null_rand, 2),
                                          excess_bps=round(ex, 2), t=round(t, 2)))
    C = pd.DataFrame(cells)
    C.to_csv(HERE / "q2_cells.csv", index=False)

    N_q1 = len(groups) * len(WSTARTS)
    # ---- owner 2026-11-16 "a failed look is not a failed setup": classify every day x window ----
    # (a) NO-SETUP: W does not make a new 09:50+ low at least X bps below the 09:50 price -> excluded
    # (b) SETUP + TURN WORKED: turn fired, no lower low than W's low before the exit, forward return > 0
    # (c) SETUP + TURN FAILED: turn fired, then a lower low or a loss at the exit
    # (d) SETUP, NO TURN: dip happened but the turn condition never fired by the decision minute (reported only)
    # Pre-declared dip thresholds X = 10 and 25 bps (X = 0, "any new low", is the original Q2 above).
    XS = [10, 25]
    cells2 = []
    for X in XS:
        S[f"setup_X{X}"] = S.newlow & (S.dip_bps >= X)
        for dn in DEFS:
            S[f"{dn}_X{X}"] = S[dn] & S[f"setup_X{X}"]
    for s_ in WSTARTS:
        for X in XS:
            for dn in DEFS:
                for sym in ["SPY", "QQQ"]:
                    for h in HOR:
                        col = f"{sym}_{h}"
                        for sp in ["TRAIN", "VALID", "ALL"]:
                            P = S[S.win == s_] if sp == "ALL" else S[(S.win == s_) & (S.split == sp)]
                            setup = P[P[f"setup_X{X}"]]
                            turn = P[P[f"{dn}_X{X}"]]
                            x = turn[col].values; n = len(x)
                            worked = int(((~turn[f"{col}_ll"]) & (turn[col] > 0)).sum())
                            ex = x.mean() - P[col].mean() if n else np.nan
                            ex_s = x.mean() - setup[col].mean() if n else np.nan
                            t = ex / (x.std(ddof=1) / math.sqrt(n)) if n > 2 else np.nan
                            cells2.append(dict(win=f"{(M0+s_+25)//60:02d}:{(M0+s_+25)%60:02d}",
                                               wstart=f"{(M0+s_)//60:02d}:{(M0+s_)%60:02d}", X_bps=X, defn=dn,
                                               sym=sym, h=str(h), split=sp, days=len(P),
                                               share_a_nosetup=round(1 - len(setup) / len(P), 3),
                                               share_d_setup_no_turn=round((len(setup) - n) / len(P), 3),
                                               n_turn=n, b_worked=worked, c_failed=n - worked,
                                               hit_b_over_bc=round(worked / n, 3) if n else np.nan,
                                               up_at_exit=round((x > 0).mean(), 3) if n else np.nan,
                                               mean_bps=round(x.mean(), 2) if n else np.nan,
                                               null_same_bps=round(P[col].mean(), 2),
                                               null_setup_days_bps=round(setup[col].mean(), 2) if len(setup) else np.nan,
                                               excess_bps=round(ex, 2), excess_vs_setup_bps=round(ex_s, 2),
                                               t=round(t, 2)))
    C2 = pd.DataFrame(cells2)
    C2.to_csv(HERE / "q2_setup_cells.csv", index=False)
    S.to_csv(HERE / "q2_panel.csv.gz", index=False)

    N_q2 = len(WSTARTS) * len(DEFS) * 2 * len(HOR)
    N_q2x = N_q2 * len(XS)
    N = N_q1 + N_q2 + N_q2x
    # also the b/(b+c) classification at X = 0 for the original cells
    for X in [0]:
        pass
    bar = max(1.5, math.sqrt(2 * math.log(N)))
    print("N", N_q1, N_q2, N_q2x, N, "bar", round(bar, 2))
    tr2 = C2[(C2.split == "TRAIN") & (C2.n_turn >= 30)].dropna(subset=["t"]).sort_values("t", ascending=False)
    best2 = tr2.iloc[0]
    best2 = best2.copy(); best2["defn"] = f"{best2.defn}_X{best2.X_bps}"
    print("best TRAIN setup-filtered cell", best2.to_dict())

    # ---------------- 3x trade on best TRAIN cell (SPY-signal cells only for SPXL; QQQ cells -> TQQQ) -------
    # pre-declared: best TRAIN t among cells with >= 30 TRAIN signal days (smaller cells are too noisy to pick from)
    tr = C[(C.split == "TRAIN") & (C.n >= 30)].dropna(subset=["t"]).sort_values("t", ascending=False)
    best = tr.iloc[0]
    print("best TRAIN cell", best.to_dict())
    print(C[(C.win == best.win) & (C.defn == best.defn) & (C.sym == best.sym) & (C.h == best.h)].to_string())

    def lev_trade(cell):
        s = int(WSTARTS[[f"{(M0+w+25)//60:02d}:{(M0+w+25)%60:02d}" for w in WSTARTS].index(cell["win"])]); e = s + 25
        und, lev = ("SPY", "SPXL") if cell["sym"] == "SPY" else ("QQQ", "TQQQ")
        out = []
        for d in full:
            if d not in G[lev]:
                continue
            row = S[(S.day == d) & (S.win == s)].iloc[0]
            if not row[cell["defn"]]:
                continue
            u = G[und][d]; L = G[lev][d]
            ulo = u[s:e, 2].min()
            udist = max(u[e - 1, 3] / ulo - 1, 0.0015) + 0.0005    # stop 5 bp under the underlying's window low
            ent = L[e - 1, 3]
            stop = ent * (1 - 3 * udist)
            risk = ent - stop
            h = cell["h"]; ex_i = 384 if h == "1555" else e - 1 + int(h)
            exit_px, stopped = L[ex_i, 3], False
            for i in range(e, ex_i + 1):
                if L[i, 2] <= stop:
                    exit_px, stopped = min(stop, L[i, 0]), True
                    break
            cost = 0.01 + 1e-4 * ent + 0.01 + 1e-4 * exit_px + (0.02 if stopped else 0)
            out.append(dict(day=d, split=split[d], R=(exit_px - ent - cost) / risk, stopped=stopped,
                            failed=bool(stopped or exit_px - ent - cost <= 0),
                            risk_pct=round(3 * udist * 100, 2)))
        return pd.DataFrame(out)

    trade_rows = {}
    def pick(win, defn, sym, h):
        return C[(C.win == win) & (C.defn == defn) & (C.sym == sym) & (C.h == h) & (C.split == "ALL")].iloc[0]
    # post-hoc (chosen with VALID in sight): the only window positive in both TRAIN and VALID; and the owner's 10:25 window
    lead = pick("11:20", "D1_reclaim_wstart", "SPY", "90")
    anec = pick("10:50", "D2_up15bp_off_wlow", "SPY", "60")
    def pickx(win, defn, X, sym, h):
        c = C2[(C2.win == win) & (C2.defn == defn) & (C2.X_bps == X) & (C2.sym == sym) & (C2.h == h) & (C2.split == "ALL")].iloc[0].copy()
        c["defn"] = f"{defn}_X{X}"
        return c
    for label, cell in [("best_train", best), ("posthoc_1120", lead), ("owner_1025_window", anec),
                        ("best_train_setupX", best2), ("owner_1025_window_X10", pickx("10:50", "D2_up15bp_off_wlow", 10, "SPY", "60")),
                        ("posthoc_1120_X10", pickx("11:20", "D1_reclaim_wstart", 10, "SPY", "90"))]:
        T = lev_trade(cell)
        T.to_csv(HERE / f"trade_{label}.csv", index=False)
        for sp in ["TRAIN", "VALID", "ALL"]:
            x = T if sp == "ALL" else T[T.split == sp]
            if len(x) == 0:
                continue
            srt = x.R.sort_values(ascending=False)
            tot = x.R.sum()
            trade_rows[f"{label}_{sp}"] = dict(n=len(x), avgR=round(x.R.mean(), 3), hit=round((x.R > 0).mean(), 3),
                                               t=round(x.R.mean() / (x.R.std(ddof=1) / math.sqrt(len(x))), 2) if len(x) > 2 else None,
                                               worstR=round(x.R.min(), 2), stop_rate=round(x.stopped.mean(), 3),
                                               avgR_wo_best=round(srt.iloc[1:].mean(), 3) if len(x) > 1 else None,
                                               best_share=round(srt.iloc[0] / tot, 2) if tot > 0 else None,
                                               med_risk_pct=float(x.risk_pct.median()), b_worked=int((~x.failed).sum()),
                                               c_failed=int(x.failed.sum()))
    print(json.dumps(trade_rows, indent=1, default=str))
    # anecdote check
    for d in [pd.Timestamp("2026-11-13").date(), pd.Timestamp("2026-11-16").date()]:
        if d in G["SPY_partial"]:
            a = G["SPY_partial"][d]; m = low_minute(a, D0, D1 if d.day != 16 else 116)
            print("anecdote", d, f"{(M0+m)//60}:{(M0+m)%60:02d}", a[m, 2])
    json.dump(dict(sessions=len(full), first=str(full[0]), last=str(full[-1]), N_q1=N_q1, N_q2=N_q2, N_q2_setup=N_q2x, N=N, best_train_setupX=best2.to_dict(),
                   bar=round(bar, 3), best_train=best.to_dict(), trade=trade_rows),
              open(HERE / "summary.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
