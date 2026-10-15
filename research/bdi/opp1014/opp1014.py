"""OPP 2026-10-14/15: recurring loser patterns (RW2 never-worked, ST2 wrong-side) tested as opportunities.
Pre-declaration: PLAN.md (written before scoring). Educational only - not financial advice.

    python research/bdi/opp1014/opp1014.py      # -> results.csv, summary.json (trade files stay in scratch)

The rule-19 locked block 2024-11-01..2025-02-28 is never loaded: lib.months() lists open months only, lib.load_month
refuses locked months, the head/tail file is read with a per-open-month date filter, lib.daily() drops locked dates,
and MCF_HIST_ALLOW_LOCKED is never set.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/opp1014")
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
MINS = np.arange(9 * 60 + 35, 15 * 60 + 56, 5)
TODS = (MINS // 60) * 100 + MINS % 60              # 935 .. 1555, 77 bars
COL = {int(t): i for i, t in enumerate(TODS)}
C1500 = COL[1500]
XS = (3, 4, 5, 6)
N_A, N_B = 23, 42
N_STUDY = N_A + N_B
N_LIN_A = 934_970 + N_A
N_LIN_B = 120_500 + N_B
FRAME_G = ("t05s1", "t1s1", "t1s05")
LOCKED = set(lib.LOCKED_MONTHS)


# ------------------------------------------------------------------------------------------------ path + costs
def entry_cost(px, tod, tier):
    return (gates.SLIP_PS + px * gates.SLIP_BPS) * gates.tod_cost_mult(tod) * tier


def exit_cost(px, kind, tier):
    c = np.where(kind == 1, 0.0, gates.SLIP_PS + px * gates.SLIP_BPS)          # 1 target, 0 flat, 2 stop
    return (c + np.where(kind == 2, gates.STOP_EXTRA, 0.0)) * tier


def sim(Hm, Lm, Cm, rows, k, s, px, R, tm, sm, etod, tier):
    """Vectorised 5-minute path: bars after column k, stop-first, flat at the last bar <= 15:55.
    s = +1 long / -1 short; tm = target multiple (None = no target); sm = stop multiple (None = no stop).
    Returns (production R, exit kind, exit column)."""
    n = len(rows)
    if n == 0:
        return np.array([]), np.array([], int), np.array([], int)
    h, l, c = Hm[rows], Lm[rows], Cm[rows]
    after = np.arange(len(TODS))[None, :] > k[:, None]
    BIG = 10_000
    if sm is not None:
        st = px - s * sm * R
        hit = after & ((l <= st[:, None]) if s == 1 else (h >= st[:, None]))
        si = np.where(hit.any(1), hit.argmax(1), BIG)
    else:
        st, si = np.full(n, np.nan), np.full(n, BIG)
    if tm is not None:
        tg = px + s * tm * R
        hit = after & ((h >= tg[:, None]) if s == 1 else (l <= tg[:, None]))
        ti = np.where(hit.any(1), hit.argmax(1), BIG)
    else:
        tg, ti = np.full(n, np.nan), np.full(n, BIG)
    fin = after & np.isfinite(c)
    li = np.where(fin.any(1), len(TODS) - 1 - fin[:, ::-1].argmax(1), -1)
    flat_px = np.where(li >= 0, c[np.arange(n), np.maximum(li, 0)], px)
    kind = np.where((si < BIG) & (si <= ti), 2, np.where(ti < BIG, 1, 0))
    ex = np.where(kind == 2, st, np.where(kind == 1, tg, flat_px))
    xc = np.where(kind == 2, si, np.where(kind == 1, ti, li))
    r = (s * (ex - px) - entry_cost(px, etod, tier) - exit_cost(ex, kind, tier)) / R
    return r, kind, xc


# ------------------------------------------------------------------------------------------------ month job
_DAILY = None


def daily_prev():
    """Per symbol-day: the previous open market date's open/close/adv20, only when it is the true previous session."""
    global _DAILY
    if _DAILY is None:
        d = lib.daily()[["symbol", "date", "open", "close", "adv20"]].copy()
        d["symbol"] = d["symbol"].astype(str)
        cal = np.array(sorted(set(d["date"])))
        prev_cal = dict(zip(cal[1:], cal[:-1]))
        d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
        g = d.groupby("symbol", sort=False)
        for k in ("date", "open", "close", "adv20"):
            d["p_" + k] = g[k].shift(1)
        d["cal_prev"] = d["date"].map(prev_cal)
        ok = (d["p_date"] == d["cal_prev"]) & d["cal_prev"].notna()
        ok &= pd.to_datetime(d["date"]).sub(pd.to_datetime(d["cal_prev"])).dt.days <= 4   # no jump over the locked block
        _DAILY = d[ok].set_index(["symbol", "date"])
    return _DAILY


def month_job(month: str):
    assert month not in LOCKED
    rc = [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in FRAME_G]
    cols = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap", "fromOpen", "vwapDistPct",
            "rsi5", "sma20_dist_pct", "bear_div"]
    f = lib.load_month(month, columns=cols + rc)
    f["symbol"] = f["symbol"].astype(str)
    f = f[(f["atr_d"] > 0) & np.isfinite(f["close"])].reset_index(drop=True)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    assert not any(str(x)[:7] in LOCKED for x in ht["date"].unique())
    ht = ht[(ht["tod"] < 950) | (ht["tod"] > 1500)].rename(columns={"h": "high", "l": "low", "c": "close"})

    # symbol-day matrices (09:35..15:55)
    sd = f[["symbol", "date"]].drop_duplicates().reset_index(drop=True)
    sd["sdi"] = np.arange(len(sd))
    f = f.merge(sd, on=["symbol", "date"], how="left")
    ht = ht.merge(sd, on=["symbol", "date"], how="inner")
    nsd = len(sd)
    Hm, Lm, Cm, Vm = (np.full((nsd, len(TODS)), np.nan, dtype=np.float64) for _ in range(4))
    for src, vw in ((f, f["close"] / (1 + f["vwapDistPct"] / 100)), (ht, ht["vwap"])):
        ci = src["tod"].map(COL).to_numpy()
        ok = ~pd.isna(ci)
        r_, c_ = src["sdi"].to_numpy()[ok], ci[ok].astype(int)
        Hm[r_, c_], Lm[r_, c_], Cm[r_, c_] = (src[k].to_numpy(float)[ok] for k in ("high", "low", "close"))
        Vm[r_, c_] = np.asarray(vw, float)[ok]
    day = f.groupby("sdi")[["atr_d", "gap", "adv20"]].first()

    sdi = f["sdi"].to_numpy()
    new = np.r_[True, sdi[1:] != sdi[:-1]]
    tod = f["tod"].to_numpy(float)
    c = f["close"].to_numpy(float)
    atr = f["atr_d"].to_numpy(float)
    R_all = 0.25 * atr
    tier_all = np.where((np.abs(f["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        p[new] = np.nan
        return p

    # same-minute controls (frame geometries), per universe threshold
    prod = {}
    for s in ("long", "short"):
        for g in FRAME_G:
            p_ = gates.prod_r(f[f"r_{s}_{g}"].to_numpy(float), f[f"win_{s}_{g}"].to_numpy(float), c, atr, g, tod=tod)
            gross = f[f"r_{s}_{g}"].to_numpy(float) + 2 * gates.SLIP_PS / R_all
            prod[(s, g)] = gross - tier_all * (gross - p_)        # x3 costs on the extended tier (rule 1)
    ctrl = {}
    for thr in (95e6, 150e6):
        u = f["adv20"].to_numpy(float) >= thr
        cf = pd.DataFrame({"date": f["date"][u], "tod": tod[u]})
        for (s, g), v in prod.items():
            cf[f"{s}_{g}"] = v[u]
        ctrl[thr] = cf.groupby(["date", "tod"]).mean()

    def ctrl_of(thr, dates, tods, s, g):
        key = pd.MultiIndex.from_arrays([pd.Index(dates), pd.Index(np.asarray(tods, float))])
        return ctrl[thr][f"{s}_{g}"].reindex(key).to_numpy(float)

    out = {}
    # ---------------------------------------------------------------- Part A: RW2-FD signals
    with np.errstate(invalid="ignore"):
        m = ((f["adv20"].to_numpy(float) >= 150e6) & (f["rsi5"].to_numpy(float) > 90)
             & (f["sma20_dist_pct"].to_numpy(float) > 1.0) & (f["bear_div"].to_numpy(float) > 0)
             & (tod >= 950) & (tod <= 1500))
    idx = gates.first_per_symbol_day(f["symbol"].to_numpy(), f["date"].to_numpy(), m)
    A = pd.DataFrame({"symbol": f["symbol"].to_numpy()[idx], "date": f["date"].to_numpy()[idx], "tod": tod[idx]})
    rows, k = sdi[idx], np.array([COL[int(t)] for t in tod[idx]], int)
    px, R, tier = c[idx], R_all[idx], tier_all[idx]
    base, kind, ks = sim(Hm, Lm, Cm, rows, k, -1, px, R, 1.0, 1.0, tod[idx], tier)
    A["base"], A["base_frame"] = base, prod[("short", "t1s1")][idx]
    for g in FRAME_G:                                   # A1: long at the RW2 signal
        A[f"A1_{g}"] = prod[("long", g)][idx]
        A[f"A1_{g}_ctrl"] = ctrl_of(150e6, A["date"], A["tod"], "long", g)
    stopped = kind == 2
    A["stopped"] = stopped
    ks_tod = TODS[np.clip(ks, 0, len(TODS) - 1)]
    A["stop_tod"] = np.where(stopped, ks_tod, -1)
    # never worked: best favourable excursion of the short through the stop bar < 0.25R
    after = np.arange(len(TODS))[None, :] > k[:, None]
    upto = np.arange(len(TODS))[None, :] <= ks[:, None]
    lmin = np.nanmin(np.where(after & upto, Lm[rows], np.inf), axis=1)
    A["nw"] = stopped & ((px - lmin) < 0.25 * R)
    # A2/A3: long at the stop bar's close
    sel = np.flatnonzero(stopped & (ks_tod <= 1550))
    lp = Cm[rows[sel], ks[sel]]
    ok = np.isfinite(lp)
    sel, lp = sel[ok], lp[ok]
    for g, (tm, sm) in {"t05s1": (0.5, 1.0), "t1s1": (1.0, 1.0), "t2s1": (2.0, 1.0), "eods1": (None, 1.0)}.items():
        r, _, _ = sim(Hm, Lm, Cm, rows[sel], ks[sel], 1, lp, R[sel], tm, sm, ks_tod[sel], tier[sel])
        col = np.full(len(A), np.nan)
        col[sel] = r
        A[f"A2_{g}"] = col
        cg = g if g in FRAME_G else "t1s1"
        cc = np.full(len(A), np.nan)
        cc[sel] = ctrl_of(150e6, A["date"].to_numpy()[sel], ks_tod[sel], "long", cg)
        A[f"A2_{g}_ctrl"] = cc
    # A4: continuation short after the stop (first VWAP loss / lower low, bar close <= 15:00)
    sel = np.flatnonzero(stopped & (ks < C1500))
    cols_ = np.arange(len(TODS))[None, :]
    win = (cols_ > ks[sel][:, None]) & (cols_ <= C1500)
    Cs, Vs, Ls = Cm[rows[sel]], Vm[rows[sel]], Lm[rows[sel]]
    Lprev = np.c_[np.full(len(sel), np.nan), Ls[:, :-1]]
    for trg, hit in (("VL", win & (Cs < Vs)), ("LL", win & (Cs < Lprev))):
        has = hit.any(1)
        j = hit.argmax(1)
        s2, j2 = sel[has], j[has]
        ep = Cm[rows[s2], j2]
        for g, (tm, sm) in {"t1s1": (1.0, 1.0), "t2s1": (2.0, 1.0), "eods1": (None, 1.0)}.items():
            r, _, _ = sim(Hm, Lm, Cm, rows[s2], j2, -1, ep, R[s2], tm, sm, TODS[j2], tier[s2])
            col = np.full(len(A), np.nan)
            col[s2] = r
            A[f"A4{trg}_{g}"] = col
            cc = np.full(len(A), np.nan)
            cc[s2] = ctrl_of(150e6, A["date"].to_numpy()[s2], TODS[j2], "short", "t1s1")
            A[f"A4{trg}_{g}_ctrl"] = cc
    out["A"] = A

    # ---------------------------------------------------------------- Part B1: same-day rebound longs
    fo = f["fromOpen"].to_numpy(float)
    vw = c / (1 + f["vwapDistPct"].to_numpy(float) / 100)
    z = (c - vw) / atr
    hi = f["high"].to_numpy(float)
    pfo, phi, pz, pc, pvw = prev(fo), prev(hi), prev(z), prev(c), prev(vw)
    runmin = pd.Series(fo).groupby(sdi).cummin().to_numpy()
    u95 = f["adv20"].to_numpy(float) >= 95e6
    wnd = u95 & (tod >= 1030) & (tod <= 1500)
    B1, BR = [], []
    with np.errstate(invalid="ignore"):
        h5 = c > phi
        vwr = (c > vw) & (pc <= pvw)
        for X in XS:
            cond = wnd & (pfo <= -X)
            trig = {"H5": cond & h5, "VW": wnd & (runmin <= -X) & vwr, "MR": cond & h5 & (pz <= -0.5)}
            for g in ("t05s1", "t1s1"):
                v = prod[("long", g)]
                okv = cond & np.isfinite(v)
                br = pd.DataFrame({"date": f["date"][okv], "r": v[okv]}).groupby("date")["r"].agg(["sum", "size"])
                br["X"], br["g"] = X, g
                BR.append(br.reset_index())
                cc = pd.DataFrame({"date": f["date"][okv], "tod": tod[okv], "r": v[okv]}).groupby(["date", "tod"])["r"].mean()
                for tn, mm in trig.items():
                    ii = gates.first_per_symbol_day(f["symbol"].to_numpy(), f["date"].to_numpy(), mm & np.isfinite(v))
                    if not len(ii):
                        continue
                    d = pd.DataFrame({"X": X, "trig": tn, "g": g, "symbol": f["symbol"].to_numpy()[ii],
                                      "date": f["date"].to_numpy()[ii], "tod": tod[ii], "r": v[ii]})
                    d["ctrl"] = ctrl_of(95e6, d["date"], d["tod"], "long", g)
                    key = pd.MultiIndex.from_arrays([pd.Index(d["date"]), pd.Index(d["tod"].astype(float))])
                    d["ctrl_cond"] = cc.reindex(key).to_numpy(float)
                    B1.append(d)
    out["B1"] = pd.concat(B1, ignore_index=True) if B1 else pd.DataFrame()
    out["BR"] = pd.concat(BR, ignore_index=True)

    # ---------------------------------------------------------------- Part B2/B3: next-day longs (d+1 in this month)
    dp = daily_prev()
    key = pd.MultiIndex.from_frame(sd[["symbol", "date"]])
    pv = dp.reindex(key)
    N = pd.DataFrame({"symbol": sd["symbol"], "date": sd["date"], "open": pv["open"].to_numpy(float),
                      "p_open": pv["p_open"].to_numpy(float), "p_close": pv["p_close"].to_numpy(float),
                      "p_adv20": pv["p_adv20"].to_numpy(float)})
    N["ret_d"] = (N["p_close"] / N["p_open"] - 1) * 100
    N["gap_next"] = (N["open"] / N["p_close"] - 1) * 100
    ok = np.isfinite(N["ret_d"].to_numpy()) & np.isfinite(N["open"].to_numpy()) & (N["p_adv20"].to_numpy() >= 95e6)
    N = N[ok].reset_index(drop=True)
    rows = sd.set_index(["symbol", "date"]).loc[pd.MultiIndex.from_frame(N[["symbol", "date"]]), "sdi"].to_numpy()
    Rn = 0.25 * day["atr_d"].to_numpy(float)[rows]
    gp = day["gap"].to_numpy(float)[rows]
    for ent in ("open", "0950"):
        if ent == "open":
            px, kk, et = N["open"].to_numpy(float), np.full(len(N), -1), np.full(len(N), 930.0)
        else:
            px, kk, et = Cm[rows, COL[950]], np.full(len(N), COL[950]), np.full(len(N), 950.0)
        tier = np.where((np.abs(gp) >= 20) | (px < 5), 3.0, 1.0)
        good = np.isfinite(px) & (Rn > 0)
        for ex, (tm, sm) in {"eod": (None, None), "t1s1": (1.0, 1.0)}.items():
            r = np.full(len(N), np.nan)
            gi = np.flatnonzero(good)
            r[gi], _, _ = sim(Hm, Lm, Cm, rows[gi], kk[gi], 1, px[gi], Rn[gi], tm, sm, et[gi], tier[gi])
            N[f"{ent}_{ex}"] = r
    out["N"] = N
    out["parity"] = float(np.corrcoef(A["base"], A["base_frame"])[0, 1]) if len(A) > 2 else np.nan
    print(month, len(A), len(out["B1"]), len(N), flush=True)
    return out


# ------------------------------------------------------------------------------------------------ scoring
def score(name, part, d, ctrl_col=None, extra=None):
    d = d[np.isfinite(d["r"])]
    s = gates.summary(d)
    rs = gates.regime_split(d, REG)
    wf = gates.walk_forward(d, exclude_months=lib.LOCKED_MONTHS)
    late = pd.to_datetime(d["date"]) >= "2026-01-01"
    row = {"config": name, "part": part, "n": s.get("n", 0), "days": s.get("days"), "exp": s.get("exp_r"),
           "t": s.get("t"), "win": s.get("win_rate"), "ex_best_day": s.get("ex_best_day"),
           "train_exp": round(float(d.r[~late].mean()), 4) if (~late).any() else None, "train_n": int((~late).sum()),
           "valid_exp": round(float(d.r[late].mean()), 4) if late.any() else None, "valid_n": int(late.sum()),
           "up": rs["up"].get("exp_r"), "flat": rs["flat"].get("exp_r"), "down": rs["down"].get("exp_r"),
           "up_n": rs["up"].get("n"), "down_n": rs["down"].get("n"), "wf": wf.get("share_positive")}
    if ctrl_col is not None:
        e = d.assign(r=d["r"] - d[ctrl_col]).dropna(subset=["r"])
        se = gates.summary(e)
        row.update({"ctrl_exp": round(float(d[ctrl_col].mean()), 4), "excess": se.get("exp_r"), "excess_t": se.get("t")})
    if extra:
        row.update(extra)
    return row


def base_rate(br: pd.DataFrame) -> dict:
    n = br["size"].sum()
    mu = br["sum"].sum() / n
    se = np.sqrt(((br["sum"] - br["size"] * mu) ** 2).sum()) / n
    return {"base_rate": round(float(mu), 4), "base_rate_t": round(float(mu / se), 2), "base_rate_n": int(n)}


REG = None


def main():
    global REG
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & LOCKED
    fA, fB, fR, fN = (SCR / f"{k}.parquet" for k in ("A", "B1", "BR", "N"))
    if not fA.exists():
        with Pool(3) as p:
            res = p.map(month_job, months)
        for key, fp in (("A", fA), ("B1", fB), ("BR", fR), ("N", fN)):
            pd.concat([r[key] for r in res], ignore_index=True).to_parquet(fp)
        (SCR / "parity.json").write_text(json.dumps({m: r["parity"] for m, r in zip(months, res)}))
    A, B1, BR, N = (pd.read_parquet(fp) for fp in (fA, fB, fR, fN))
    for d in (A, B1, BR, N):
        d["date"] = pd.to_datetime(d["date"]).dt.date
    REG = lib.regimes()
    REG.index = pd.to_datetime(REG.index).date
    rows = []
    # Part A
    base = score("A0 RW2-FD base short t1s1 (reference, not counted)", "A-ref", A[["date"]].assign(r=A["base"]))
    rows.append(base)
    for g in FRAME_G:
        rows.append(score(f"A1 long@RW2 signal {g}", "A1", A[["date"]].assign(r=A[f"A1_{g}"], c=A[f"A1_{g}_ctrl"]), "c",
                          {"trig": "signal", "geom": g, "X": None}))
    for sub, msk in (("A2", A["stopped"]), ("A3", A["nw"])):
        for g in ("t05s1", "t1s1", "t2s1", "eods1"):
            d = A[msk][["date"]].assign(r=A.loc[msk, f"A2_{g}"], c=A.loc[msk, f"A2_{g}_ctrl"])
            rows.append(score(f"{sub} long@RW2 stop ({'all stops' if sub == 'A2' else 'never-worked stops'}) {g}", sub, d, "c",
                              {"trig": "stop", "geom": g, "X": None}))
    for sub, msk in (("all", A["stopped"]), ("nw", A["nw"])):
        for trg in ("VL", "LL"):
            for g in ("t1s1", "t2s1", "eods1"):
                d = A[msk][["date"]].assign(r=A.loc[msk, f"A4{trg}_{g}"], c=A.loc[msk, f"A4{trg}_{g}_ctrl"])
                rows.append(score(f"A4 cont-short after stop {trg} ({sub}) {g}", "A4", d, "c",
                                  {"trig": f"{trg}-{sub}", "geom": g, "X": None}))
    # Part B1
    for X in XS:
        for tn in ("H5", "VW", "MR"):
            for g in ("t05s1", "t1s1"):
                d = B1[(B1.X == X) & (B1.trig == tn) & (B1.g == g)]
                ex = {"trig": tn, "geom": g, "X": X, **base_rate(BR[(BR.X == X) & (BR.g == g)]),
                      "ctrl_cond_exp": round(float(d["ctrl_cond"].mean()), 4) if len(d) else None}
                rows.append(score(f"B1 same-day long {tn} down>={X}% {g}", "B1", d[["date", "r", "ctrl"]], "ctrl", ex))
    # Part B2/B3 (excess vs the same-day universe mean of the same entry/exit)
    for ent in ("open", "0950"):
        for exn in ("eod", "t1s1"):
            col = f"{ent}_{exn}"
            um = N.groupby("date")[col].transform("mean")
            NN = N.assign(r=N[col], c=um)
            ub = gates.summary(NN[["date", "r"]].dropna())
            for X in XS:
                d = NN[NN["ret_d"] <= -X]
                gd, gu = d[d.gap_next < 0], d[d.gap_next >= 0]
                rows.append(score(f"B2 next-day long after day<=-{X}% entry {ent} exit {exn}", "B2", d[["date", "r", "c"]], "c",
                                  {"trig": f"nextday-{ent}", "geom": exn, "X": X, "base_rate": ub.get("exp_r"), "base_rate_t": ub.get("t"),
                                   "base_rate_n": ub.get("n"),
                                   "gapdn_exp": round(float(gd.r.mean()), 4) if len(gd) else None, "gapdn_n": int(gd.r.notna().sum()),
                                   "gapup_exp": round(float(gu.r.mean()), 4) if len(gu) else None, "gapup_n": int(gu.r.notna().sum())}))
            if ent == "open":
                d = NN[NN["gap_next"] <= -2.0]
                rows.append(score(f"B3 gap-fade long gap<=-2% entry open exit {exn}", "B3", d[["date", "r", "c"]], "c",
                                  {"trig": "gapfade", "geom": exn, "X": None, "base_rate": ub.get("exp_r"), "base_rate_t": ub.get("t"),
                                   "base_rate_n": ub.get("n")}))
    Rz = pd.DataFrame(rows)
    counted = Rz[Rz.part != "A-ref"]
    assert len(counted) == N_STUDY, len(counted)

    def neighbours(r):
        same = Rz[(Rz.part == r.part) & (Rz.trig == r.trig) & (Rz.config != r.config)]
        if r.part in ("B1", "B2"):
            same = same[((same.geom == r.geom) & ((same.X - r.X).abs() == 1)) | ((same.X == r.X) & (same.geom != r.geom))]
        return same

    Rz["plateau"] = [bool(len(nb := neighbours(r)) and (nb.exp > 0).all()) if r.part != "A-ref" else None for r in Rz.itertuples()]
    Rz["lineage_N"] = np.where(Rz.part.str.startswith("A"), N_LIN_A, N_LIN_B)
    Rz["t_bar_lineage"] = [gates.t_required(n) for n in Rz["lineage_N"]]
    Rz["t_bar_study"] = gates.t_required(N_STUDY)
    common = ((Rz.exp > 0) & (Rz.train_exp > 0) & (Rz.valid_exp > 0) & (Rz.up > 0) & (Rz.down > 0) & (Rz.wf >= 0.6)
              & (Rz.ex_best_day > 0) & (Rz.excess > 0) & (Rz.plateau == True))  # noqa: E712
    Rz["testing_pass"] = common & (Rz.t >= 2.0) & (Rz.part != "A-ref")
    Rz["research_pass"] = Rz["testing_pass"] & (Rz.t >= Rz.t_bar_lineage)
    Rz["study_bar_pass"] = Rz["testing_pass"] & (Rz.t >= Rz.t_bar_study)
    Rz.to_csv(OUT / "results.csv", index=False)
    par = json.loads((SCR / "parity.json").read_text())
    summ = {"configs_scored": int(len(counted)), "N_study": N_STUDY, "N_lineage_A": N_LIN_A, "N_lineage_B": N_LIN_B,
            "t_bar_study": gates.t_required(N_STUDY), "t_bar_lineage_A": gates.t_required(N_LIN_A),
            "t_bar_lineage_B": gates.t_required(N_LIN_B), "rw2_signals": int(len(A)),
            "rw2_stopped_share": round(float(A.stopped.mean()), 3), "rw2_never_worked_share_of_stops": round(float(A.nw.sum() / A.stopped.sum()), 3),
            "rw2_base_sim_vs_frame_corr_min": round(min(par.values()), 4),
            "rw2_base_sim_mean": round(float(A.base.mean()), 4), "rw2_base_frame_mean": round(float(A.base_frame.mean()), 4),
            "positive_exp": int((counted.exp > 0).sum()), "testing_pass": int(Rz.testing_pass.sum()),
            "study_bar_pass": int(Rz.study_bar_pass.sum()), "research_pass": int(Rz.research_pass.sum()),
            "locked_block_loaded": False}
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 320)
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.max_colwidth", 60)
    print(json.dumps(summ, indent=1))
    print(Rz[["config", "n", "days", "exp", "t", "win", "train_exp", "valid_exp", "up", "down", "wf", "ex_best_day",
              "ctrl_exp", "excess", "excess_t", "plateau", "testing_pass"]].to_string())
    print(Rz[Rz.part.isin(["B1", "B2", "B3"])][["config", "base_rate", "base_rate_t", "ctrl_cond_exp", "gapdn_exp", "gapdn_n", "gapup_exp", "gapup_n"]].to_string())


if __name__ == "__main__":
    main()
