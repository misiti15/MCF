"""ULT-33 EARN-GEO backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-33", 5, 6). Built on round4/ULT-28/bt.py
(event table, calendar, stats, sub-halves, locked-block guards, costs/borrow/surcharge reused unchanged).

Superset per half: HOLD bars (ULT-33 module: G 3%, S any, ADV20 >= $100M, cost_r(m=1) <= 0.08) in 09:50-12:30, both
sides (shorts ETB), on reaction-day rows (evt 1) and on the non-earnings twin (evt 0, as ULT-28).
Walk on 1-minute bars, per row, for m {0.25, 0.5, 1.0} x K {1, 2} (stop 1 Ru, target K Ru, Ru = m x atr_d):
  MKT: entry = OPEN of the minute starting at the decision close; brackets around the decision close (ULT-28 chassis).
  LMT: limit L = VWAP_decision + s x 0.05 x atr_d, working the 15 minutes from the decision close. If the first minute
       opens through L (marketable) the fill is that open; otherwise a fill at L on the first minute that trades
       strictly through L (long: low < L; short: high > L). Brackets around the fill price. On the fill minute only the
       stop is checked (the target is checked from the next minute: conservative intrabar order). Cap 45 min from the
       fill, flat 15:49. LR8 entry cost still charged (tod multiplier and x1.5 surcharge at the fill minute).
Exit cost / stop +2c / target free / borrow / surcharge as ULT-28. R per Ru (actual risk) and per 0.25 x atr_d.
Chassis: one lot per symbol; refire >= 30 min after exit; an unfilled LMT order blocks the symbol for its 15 minutes and
is not an entry; max 2 entries per symbol-session; day cap 30 (fills, first by time, ADV desc).
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK fit|fitrandom|check|plateau
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

_s = importlib.util.spec_from_file_location("ult28bt", HERE.parent / "ULT-28" / "bt.py")
B28 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B28)
B23 = B28.B23
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha
DATA, CACHE, EARN = B28.DATA, B28.CACHE, B28.EARN
MOD = HERE.parents[1] / "modules" / "ULT-33.py"
N_CUM = 996
DAY_CAP = 30
MS = (0.25, 0.5, 1.0)
KS = (1, 2)
WINDOW = (950, 1230)
SURCH_T = 1030
LMT_OFF, LMT_VALID = 0.05, 15


def load_mod(name="ult33"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    ev, allrd, sess = B28.events()
    sidx = {d: i for i, d in enumerate(sess)}
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "vwapDistPct", "fromOpen", "rsi5"]
    f = lib.load_month(month, columns=cols, context=True)
    f = f[[c for c in f.columns if not (c.startswith("win_") or c.startswith("r_long") or c.startswith("r_short")
                                        or "heat" in c.lower())]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    evm = ev[ev.rd.str[:7] == month]
    k = f["symbol"] + "|" + f["date"]
    f["e_rd"] = k.isin(set(evm.symbol.astype(str) + "|" + evm.rd)).to_numpy()
    covered = set(allrd.symbol.astype(str))
    di = f["date"].map(sidx).to_numpy()
    bad = set()
    for sym, ri in zip(allrd.symbol.astype(str), allrd.rd_i.to_numpy()):
        for dd in range(ri - 5, ri + 2):
            bad.add((sym, dd))
    twin = np.array([(s in covered) and ((s, d) not in bad) for s, d in zip(f["symbol"].to_numpy(), di)])
    r = mod.features(f.drop(columns=["e_rd"]).assign(e_rd=True), m=1.0)     # loosest cost cap; m applied in select
    tod = r["tod"]
    win = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    etb = f["symbol"].isin(B28.etb_set()).to_numpy()
    evt = f["e_rd"].to_numpy()
    out = []
    for sgn in (1, -1):
        mk = mod.signal(r, sgn) & win & (evt | twin)
        if sgn < 0:
            mk &= etb
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "vwapDistPct"]].copy()
        s["side"] = sgn
        s["evt"] = evt[mk].astype(np.int8)
        s["cost_r1"] = r["cost_r"][mk]                   # cost_r at m = 1; cost_r(m) = cost_r1 / m
        s["lmt"] = mod.limit_price(s.close.to_numpy(), s.vwapDistPct.to_numpy(), s.atr_d.to_numpy(), sgn)
        out.append(s)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, pd.concat(out, ignore_index=True), days


# ---------------------------------------------------------------- stage 2: 1-minute walk
def walk_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    dmin = pd.Timestamp(min(T.date), tz=tz)
    dmax = pd.Timestamp(max(T.date), tz=tz) + pd.Timedelta(days=1)
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= dmin) & (fld < dmax)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hm_all = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}

    def path(ix, j0, s, stop, tgt, tend, tgt_from=None):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if (s > 0 and Lo[q] <= stop) or (s < 0 and Hh[q] >= stop):
                px, kd, xt = (min(O[q], stop) if s > 0 else max(O[q], stop)), 1, hm_all[q]; break
            if q != tgt_from and tgt is not None and ((s > 0 and Hh[q] >= tgt) or (s < 0 and Lo[q] <= tgt)):
                px, kd, xt = tgt, 2, hm_all[q]; break
            px, xt = Cc[q], hm_all[q]
        return px, kd, xt

    nk = len(MS) * len(KS)
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        row = None
        if ix is not None:
            hm = hm_all[ix]
            j0 = np.searchsorted(hm, r.tod)
            ok = j0 < len(ix) and m2(hm[j0]) - m2(r.tod) <= 4 and hm[j0] < 1550
            dclose, lmt = r.close, r.lmt
            if ok and r.random:
                if j0 == 0 or m2(hm[j0 - 1]) < m2(r.tod) - 5:
                    ok = False
                else:
                    dclose = Cc[ix[j0 - 1]]
                    pv = ix[:j0]
                    tp = (Hh[pv] + Lo[pv] + Cc[pv]) / 3
                    vw = float((tp * V[pv]).sum() / V[pv].sum()) if V[pv].sum() > 0 else dclose
                    lmt = vw + r.side * LMT_OFF * r.atr_d
            if ok:
                s = r.side
                tend = min(int(hhmm(m2(hm[j0]) + 44)), 1549)
                row = [O[ix[j0]], dclose]
                for m in MS:
                    Ru = m * r.atr_d
                    for kk in KS:
                        px, kd, xt = path(ix, j0, s, dclose - s * Ru, dclose + s * kk * Ru, tend)
                        row += [px, kd, int(hhmm(m2(xt) + 1)) if xt is not None else np.nan]
                # LMT fill
                jf, fpx = None, None
                lim_end = m2(hm[j0]) + LMT_VALID - 1
                for jj in range(j0, len(ix)):
                    q = ix[jj]
                    if m2(hm_all[q]) > lim_end or hm_all[q] >= 1550:
                        break
                    if jj == j0 and ((s > 0 and O[q] <= lmt) or (s < 0 and O[q] >= lmt)):
                        jf, fpx = jj, O[q]; break
                    if (s > 0 and Lo[q] < lmt) or (s < 0 and Hh[q] > lmt):
                        jf, fpx = jj, lmt; break
                if jf is None:
                    row += [np.nan, np.nan] + [np.nan] * (3 * nk)
                else:
                    ftm = hm_all[ix[jf]]
                    tend_l = min(int(hhmm(m2(ftm) + 44)), 1549)
                    marketable = jf == j0 and fpx == O[ix[j0]]
                    row += [fpx, ftm]
                    for m in MS:
                        Ru = m * r.atr_d
                        for kk in KS:
                            px, kd, xt = path(ix, jf, s, fpx - s * Ru, fpx + s * kk * Ru, tend_l,
                                              tgt_from=None if marketable else ix[jf])
                            row += [px, kd, int(hhmm(m2(xt) + 1)) if xt is not None else np.nan]
                if any(v is None for v in row):
                    row = None
        res.append((r.Index,) + tuple(row if row else [np.nan] * (2 + 3 * nk + 2 + 3 * nk)))
    return res


def ekeys():
    return [f"{int(m * 100):03d}k{k}" for m in MS for k in KS]


def cost_R(side, tod, e, px, kd, unit, evt, xt, fixes=True):
    """B28.cost_R (LR8 + surcharge + borrow); tod = entry-cost time (decision bar for MKT, fill minute for LMT)."""
    return B28.cost_R(side, tod, e, px, kd, unit, evt, xt, fixes=fixes)


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    if "lmt" not in T:
        T["lmt"] = np.nan
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    cols = ["i", "e", "dclose"] + [f"{a}M{k}" for k in ekeys() for a in ("px", "kd", "xt")] + ["fpx", "ftm"] + \
        [f"{a}L{k}" for k in ekeys() for a in ("px", "kd", "xt")]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    tod, side, atr, evt = T.tod.to_numpy(), T.side.to_numpy(), T.atr_d.to_numpy(), T.evt.to_numpy()
    ftm = T.ftm.to_numpy()
    # LMT entry-cost time: the bar-close clock of the fill minute (minute start + 1)
    ftod = np.where(np.isnan(ftm), 9999, hhmm(m2(np.nan_to_num(ftm, nan=0)) + 1))
    for k in ekeys():
        m = int(k[:3]) / 100
        unit = m * atr
        for en, e, ct in (("M", T.e.to_numpy(), tod), ("L", T.fpx.to_numpy(), ftod)):
            px, kd, xt = T[f"px{en}{k}"].to_numpy(), T[f"kd{en}{k}"].to_numpy(), T[f"xt{en}{k}"].to_numpy()
            T[f"r{en}{k}"] = cost_R(side, ct, e, px, kd, unit, evt, xt)
            T[f"ru{en}{k}"] = cost_R(side, ct, e, px, kd, 0.25 * atr, evt, xt)
            if en == "M":
                T[f"rsc{en}{k}"] = cost_R(side, ct, T.dclose.to_numpy(), px, kd, unit, evt, xt, fixes=False)
            else:
                T[f"rsc{en}{k}"] = cost_R(side, ct, e, px, kd, unit, evt, xt, fixes=False)
            T[f"xmin{en}{k}"] = np.where(T[f"xt{en}{k}"].notna(), m2(T[f"xt{en}{k}"].fillna(0)), np.nan)
            T = T.drop(columns=[f"px{en}{k}", f"xt{en}{k}"])
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (12): 33a..33l = m {0.25, 0.5, 1.0} x exit {t1s1, t2s1} x entry {MKT, LMT} (m outer, entry inner)."""
    out, names = {}, iter("abcdefghijkl")
    for m in MS:
        for kk in KS:
            for en in ("MKT", "LMT"):
                out["33" + next(names)] = dict(m=m, k=kk, entry=en, key=f"{'M' if en == 'MKT' else 'L'}{int(m * 100):03d}k{kk}",
                                               label=f"m{m:g}-t{kk}s1-{en}")
    return out


def bind(T, cfg):
    k = cfg["key"]
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"], T["r_u"] = (T["r" + k], T["kd" + k], T["xmin" + k], T["rsc" + k],
                                                              T["ru" + k])
    T["filled"] = T["r"].notna()
    t_in = np.where(cfg["entry"] == "LMT", m2(np.nan_to_num(T.ftm.to_numpy(), nan=0)), m2(T.tod.to_numpy()))
    T["hold"] = T["xmin"] - t_in
    return T


def select(S, cfg, cap=DAY_CAP, evt=1, attempts=False):
    S = bind(S, cfg)
    m = ((S.evt == evt) & (S.tod >= WINDOW[0]) & (S.tod <= WINDOW[1]) & (S.side * S.gap >= 3.0)
         & (S.cost_r1 / cfg["m"] <= 0.08) & S.e.notna())        # e NaN = no 1-minute path at all
    s = S[m].sort_values(["symbol", "date", "tod"], kind="mergesort")
    keep, n_att = [], 0
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x, fl in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy(), g.filled.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                n_att += 1
                if fl:
                    keep.append(i); n += 1; free_at = x + 30
                else:
                    free_at = t + LMT_VALID
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    if attempts:
        return s, n_att
    return s


SEASON = None


def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    o["by_gap"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
                   for nm, x in (("gap_3_5", t[(t.side * t.gap) < 5]),
                                 ("gap_5_10", t[((t.side * t.gap) >= 5) & ((t.side * t.gap) < 10)]),
                                 ("gap_10_plus", t[(t.side * t.gap) >= 10]))}
    o["by_entry_time"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
                          for nm, x in (("0950_1025", t[t.tod < 1030]), ("1030_1125", t[(t.tod >= 1030) & (t.tod < 1130)]),
                                        ("1130_1230", t[t.tod >= 1130]))}
    if SEASON is not None:
        ss = t.date.map(SEASON).fillna(False).astype(bool)
        o["season"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                            "total_r": round(float(x.r.sum()), 2)} for nm, x in (("season", t[ss]), ("off", t[~ss]))}
    return o


def cfg_stats(S, cfg, n, evt=1):
    t, att = select(S, cfg, evt=evt, attempts=True)
    o = full_stats(t, n)
    o["orders"] = att
    o["fill_rate"] = round(len(select(S, cfg, cap=0, evt=evt)) / att, 3) if att else None
    return t, o


def random_control(sel, cfg, seed=1119):
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(WINDOW[0]), m2(WINDOW[1]) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side", "evt", "adv20", "gap", "cost_r1"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    W = walk(R, random=True)
    return bind(W, cfg)


def load_half(work, half):
    global SEASON
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    meta = json.loads((Path(work) / f"meta_{half}.json").read_text())
    nev = meta.get("n_events", {})
    SEASON = {d: nev.get(d, 0) >= 5 for d in days}
    return S, len(days)


def rand_block(t, cfg):
    Rc = random_control(t, cfg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr, rr = t.r.to_numpy()[ok], Rc.r.to_numpy()[ok]
    sd = t.side.to_numpy()[ok]
    o = {"random_avg_r": round(float(rr.mean()), 4) if ok.any() else None,
         "signal_minus_random": round(float(tr.mean() - rr.mean()), 4) if ok.any() else None,
         "random_n": int(ok.sum()), "random_fill_rate": round(float(Rc.r.notna().mean()), 3)}
    for nm, sg in (("long", 1), ("short", -1)):
        q = sd == sg
        if q.any():
            o[f"random_avg_r_{nm}"] = round(float(rr[q].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[q].mean() - rr[q].mean()), 4)
    return o


def short_stats(o):
    keys = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
            "total_r_wo_best_day", "total_r_per_session", "worst_day_per_trade_session", "t_day_clustered",
            "avg_r_ex_0403_0409", "A_avg_r", "B_avg_r", "first_half_avg_r", "second_half_avg_r", "avg_r_u025",
            "fill_rate", "orders", "median_hold_min")
    x = {k: o.get(k) for k in keys}
    x["long_avg_r"] = o["by_side"]["long"].get("avg_r")
    x["short_avg_r"] = o["by_side"]["short"].get("avg_r")
    return x


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days = [], []
        with Pool(2) as p:
            for m, s, d in p.imap_unordered(month_job, B28.half_months(half)):
                print(m, len(s), "evt rows", int(s.evt.sum()), flush=True)
                sigs.append(s); days += d
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        ev, _, _ = B28.events()
        ev = ev[ev.rd.isin(set(days))]
        (W / f"meta_{half}.json").write_text(json.dumps({"n_days": len(days),
                                                         "n_events": ev.groupby("rd").size().astype(int).to_dict()}))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.e.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t, o = cfg_stats(S, cfg, n)
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("avg_r_u025"), o.get("fill_rate"), o.get("A_avg_r"), o.get("B_avg_r"),
                  o["by_side"]["long"].get("avg_r"), o["by_side"]["short"].get("avg_r"), o.get("t_day_clustered"),
                  flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k].get("total_r_wo_best_day", -1e9), -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k].get("total_r", -1e9), -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-33 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__),
              "sha256_module_at_freeze": sha(MOD), "sha256_earnings": sha(EARN), "configs_counted_this_candidate": 13,
              "configs_note": "12 grid + 1 bias diagnostic (PLAN sec. 4; already inside N 996)",
              "check_informed": "PARTLY", "needs_owner_blackout_exception": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_nosurcharge_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, fs["cfg"], cap=0), n))
        o["twin_fit"] = short_stats(cfg_stats(S, fs["cfg"], n, evt=0)[1])
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "CHECK is scored once"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t, o = cfg_stats(S, cfg, n)
        o["bias_diag_sigclose_noborrow_nosurcharge_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, cfg, cap=0), n))
        o.update(rand_block(t, cfg))
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0
                 and o["trades_per_session"] >= 2.0 and fs["any_eligible"])
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and o["avg_r"] > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        t[["symbol", "date", "tod", "side", "gap", "r", "r_u", "kd", "hold"]].to_csv(HERE / "check_trades.csv.gz",
                                                                                   index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            res[name] = short_stats(cfg_stats(S, cfg, n)[1])
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        fs = json.loads((HERE / "fitsel.json").read_text())
        res["twin_check_" + fs["pick"]] = short_stats(cfg_stats(S, fs["cfg"], n, evt=0)[1])
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
