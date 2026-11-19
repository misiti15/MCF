"""ULT-27 PERIODICITY backtest (ultimate_1119 round3/PLAN.md sec. 2, 3 "ULT-27", 5, 6). Walk / costs / stats adapted from
round3/ULT-26/bt.py (stats / sub-halves / SPY day types imported from round3/ULT-23/bt.py unchanged).

Stage x:   per symbol (non-LEV, 1-minute cache) the ATR-scaled same-slot interval returns of every open session of the
           half plus its look-back (module interval_returns / atr_pct; ATR from daily.parquet per contiguous segment, so
           nothing crosses the locked block). CHECK x is built only after fitsel.json is frozen.
Stage sig: P (module scores; the locked block sits in the session sequence as 82 empty sessions, so a look-back never
           reaches into it), pre-open lists per (L, N) (module preopen_ok / rank_lists with the frame adv20, the daily
           previous close, frame atr_d, today's ETB flag for shorts), then the module's in-day filters (features /
           day_ok) at the slot bar. Rows carry one flag per config 27a..27f.
Stage walk: entry at the OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost); TX-30: time exit at
           the close of minute entry+29, catastrophic stop 2u (u = 0.25 x atr_d) beyond the decision close, stop
           gap-through at the worse of open/stop, +2c on stops; R per 2u; r_u per 0.25-dATR unit; flat 15:50.
           Shorts pay borrow (1.2 bp of entry notional, 3 bp under $20).
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK x fit|check ; python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ;
    python bt.py WORK fit|fitrandom|check|plateau
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

_s = importlib.util.spec_from_file_location("ult23bt", HERE.parent / "ULT-23" / "bt.py")
B23 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B23)
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
FIT_MONTHS = B23.FIT_MONTHS
MOD = HERE.parents[1] / "modules" / "ULT-27.py"
SYMF = HERE.parents[1] / "modules" / "ULT-26_symbols.json"
N_CUM = 880
DAY_CAP = 36
HOLD = 30
LS, NS = (5, 10, 20), (2, 3)
TZ = "America/New_York"
SEG = {"fit": [("2024-09-16", "2024-10-31"), ("2025-03-03", "2025-09-30")],
       "check": [("2025-03-03", "2099-12-31")]}          # check x: daily ATR segment B; 1-min from 2025-08-01
X_RANGE = {"fit": [("2024-09-16", "2024-10-31"), ("2025-03-03", "2025-09-30")], "check": [("2025-08-01", "2099-12-31")]}
FORBID = ("win_", "r_long", "r_short")


def load_mod(name="ult27"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def load_daily():
    d = pd.read_parquet(DATA / "daily.parquet", columns=["symbol", "date", "high", "low", "close"])
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d = d[(d.date < "2024-11-01") | (d.date > "2025-02-28")]
    no_locked(d.date.unique())
    return d


# ---------------------------------------------------------------- stage x
def x_job(args):
    sym, half, dly = args
    mod = load_mod()
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    flt = None
    for a, b in X_RANGE[half]:
        f = (fld >= pd.Timestamp(a, tz=TZ)) & (fld < pd.Timestamp(b, tz=TZ) + pd.Timedelta(days=1))
        flt = f if flt is None else (flt | f)
    L0, L1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    b = d.to_table(filter=flt & ((fld < L0) | (fld >= L1))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    if not len(b):
        return None
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    ret = mod.interval_returns(b)
    ap = pd.concat([mod.atr_pct(dly[(dly.date >= a) & (dly.date <= z)]) for a, z in SEG[half]])
    ap = ap[~ap.index.duplicated()]
    xn = ret.mul(100).div(ap.reindex(ret.index), axis=0)
    xn = xn.stack().rename("x").reset_index()
    xn.columns = ["date", "slot", "x"]
    xn["symbol"] = sym
    return xn[np.isfinite(xn.x)]


def session_seq(xdays):
    """Open sessions in order with the locked block as 82 empty placeholder sessions."""
    a = sorted(d for d in xdays if d < "2024-11-01")
    b = sorted(d for d in xdays if d > "2025-02-28")
    return a + [f"LOCKED{k:02d}" for k in range(82)] + b


# ---------------------------------------------------------------- stage sig
def frame_month(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "rsi5"]
    f = lib.load_month(month, columns=cols, context=True)
    assert not any(c.startswith(FORBID) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    mod = load_mod()
    r = mod.features(f)
    keep = np.isin(r["tod"], mod.SLOTS)
    g = f.loc[keep, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
    g["spy_fo"] = r["spy_fo"][keep]
    g["spy_r30"] = r["spy_r30"][keep]
    g["cost_r"] = r["cost_r"][keep]
    g["okL"] = mod.day_ok(r, 1)[keep]
    g["okS"] = mod.day_ok(r, -1)[keep]
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, g, days


def build_sig(work, half):
    mod = load_mod()
    X = pd.read_parquet(Path(work) / f"x_{half}.parquet")
    no_locked(X.date.unique())
    seq = session_seq(set(X.date))
    W = X.pivot_table(index=["symbol", "date"], columns="slot", values="x").reindex(columns=list(mod.SLOTS))
    P = {}
    for Lk in LS:
        parts = []
        for sym, g in W.groupby(level=0):
            g = g.droplevel(0).reindex(seq)
            s = mod.scores(g, Lk)
            s = s[~s.index.str.startswith("LOCKED")]
            s["symbol"] = sym
            parts.append(s.reset_index().rename(columns={"index": "date"}))
        P[Lk] = pd.concat(parts, ignore_index=True).set_index(["date", "symbol"])
    frames, days = [], []
    with Pool(2) as p:
        for m, g, d in p.imap_unordered(frame_month, half_months(half)):
            print("frames", m, len(g), flush=True)
            frames.append(g); days += d
    F = pd.concat(frames, ignore_index=True)
    no_locked(F.date.unique()); no_locked(days)
    dly = load_daily().sort_values(["symbol", "date"])
    dly["prev_close"] = dly.groupby("symbol").close.shift(1)
    dly["prev_date"] = dly.groupby("symbol").date.shift(1)
    # previous close only when it is the immediately previous open session in the same segment
    dly.loc[(dly.date >= "2025-03-01") & (dly.prev_date < "2025-03-01"), "prev_close"] = np.nan
    pc = dly.set_index(["date", "symbol"]).prev_close
    etb = etb_set()
    lev = mod.LEV
    meta = F.groupby(["date", "symbol"]).agg(adv20=("adv20", "first"), atr_d=("atr_d", "first"))
    meta["prev_close"] = pc.reindex(meta.index).to_numpy()
    Fi = F.set_index(["date", "symbol", "tod"])
    rows = []
    for d in sorted(days):
        if d not in meta.index.get_level_values(0):
            continue
        md = meta.loc[d]
        md = md[~md.index.isin(lev)]
        for Lk in LS:
            if d not in P[Lk].index.get_level_values(0):
                continue
            Pd = P[Lk].loc[d].reindex(md.index)
            el = pd.DataFrame({s: mod.preopen_ok(md.adv20, md.prev_close, md.atr_d, s) for s in mod.SLOTS},
                              index=md.index)
            es = el & np.asarray(md.index.isin(list(etb)))[:, None]
            for Nk in NS:
                lists = mod.rank_lists(Pd[list(mod.SLOTS)], el, es, Nk)
                for s, v in lists.items():
                    for side, sg in (("L", 1), ("S", -1)):
                        for rk, sym in enumerate(v[side]):
                            rows.append((d, sym, s, sg, f"L{Lk}N{Nk}", rk, float(Pd.at[sym, s])))
    Lst = pd.DataFrame(rows, columns=["date", "symbol", "tod", "side", "cfgkey", "rank", "P"])
    no_locked(Lst.date.unique())
    # one row per (date, symbol, tod, side) with config flags
    Lst["flag"] = 1
    flags = Lst.pivot_table(index=["date", "symbol", "tod", "side"], columns="cfgkey", values="flag",
                            aggfunc="max", fill_value=0)
    Pv = Lst.groupby(["date", "symbol", "tod", "side"]).P.first()
    S = flags.reset_index()
    S["P"] = Pv.reindex(flags.index).to_numpy()
    j = Fi.reindex(pd.MultiIndex.from_frame(S[["date", "symbol", "tod"]]))
    for k in ("close", "atr_d", "adv20", "gap", "spy_fo", "spy_r30", "cost_r", "okL", "okS"):
        S[k] = j[k].to_numpy()
    S["listed_no_bar"] = S.close.isna()
    S["ok"] = np.where(S.side > 0, S.okL.fillna(False).astype(bool), S.okS.fillna(False).astype(bool))
    meta_out = {"n_days": len(days), "listed_rows": int(len(S)), "listed_no_bar": int(S.listed_no_bar.sum()),
                "listed_fail_inday": int((~S.ok).sum()),
                "listed_per_cfg": {c: int(S[c].sum()) for c in flags.columns},
                "traded_per_cfg": {c: int((S[c].astype(bool) & S.ok).sum()) for c in flags.columns},
                "days_with_lists": {f"L{Lk}": int(Lst[Lst.cfgkey == f'L{Lk}N2'].date.nunique()) for Lk in LS}}
    S = S[S.ok].drop(columns=["okL", "okS", "ok", "listed_no_bar"]).reset_index(drop=True)
    S.to_parquet(Path(work) / f"sig_{half}.parquet")
    pd.DataFrame({"date": sorted(days)}).to_parquet(Path(work) / f"days_{half}.parquet")
    (Path(work) / f"meta_{half}.json").write_text(json.dumps(meta_out, indent=1))
    print(json.dumps(meta_out, indent=1))


# ---------------------------------------------------------------- stage walk (as ULT-26, TX-30 only)
def walk_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    dmin = pd.Timestamp(min(T.date), tz=TZ)
    dmax = pd.Timestamp(max(T.date), tz=TZ) + pd.Timedelta(days=1)
    L0, L1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= dmin) & (fld < dmax)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hm_all = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        row = None
        if ix is not None:
            hm = hm_all[ix]
            j0 = np.searchsorted(hm, r.tod)
            ok = j0 < len(ix) and m2(hm[j0]) - m2(r.tod) <= 4 and hm[j0] < 1550
            dclose = r.close
            if ok and r.random:
                if j0 == 0 or m2(hm[j0 - 1]) < m2(r.tod) - 5:
                    ok = False
                else:
                    dclose = Cc[ix[j0 - 1]]
            if ok:
                tend = min(int(hhmm(m2(hm[j0]) + HOLD - 1)), 1549)
                stop = dclose - r.side * 2.0 * 0.25 * r.atr_d
                px, kd, xt = None, 0, None
                for q in ix[j0:]:
                    if hm_all[q] > tend:
                        break
                    if (r.side > 0 and Lo[q] <= stop) or (r.side < 0 and Hh[q] >= stop):
                        px, kd, xt = (min(O[q], stop) if r.side > 0 else max(O[q], stop)), 1, hm_all[q]; break
                    px, xt = Cc[q], hm_all[q]
                if px is not None:
                    row = [O[ix[j0]], dclose, px, kd, int(hhmm(m2(xt) + 1))]
        res.append((r.Index,) + tuple(row if row else [np.nan] * 5))
    return res


def borrow(side, e):
    return np.where(side < 0, np.where(e < 20, 3e-4, 1.2e-4) * e, 0.0)


def cost_R(side, tod, e, px, kd, unit, with_borrow=True):
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    bf = borrow(side, e) if with_borrow else 0.0
    return (side * (px - e) - ec - xc - bf) / unit


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "px", "kd", "xt"]).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    tod, side, atr = T.tod.to_numpy(), T.side.to_numpy(), T.atr_d.to_numpy()
    e, px, kd = T.e.to_numpy(), T.px.to_numpy(), T.kd.to_numpy()
    T["r"] = cost_R(side, tod, e, px, kd, 2 * 0.25 * atr)
    T["r_u"] = cost_R(side, tod, e, px, kd, 0.25 * atr)
    T["r_sigclose"] = cost_R(side, tod, T.dclose.to_numpy(), px, kd, 2 * 0.25 * atr, with_borrow=False)
    T["r_gross"] = side * (px - e) / (2 * 0.25 * atr)
    T["xmin"] = np.where(T.xt.notna(), m2(T.xt.fillna(0)), np.nan)
    T["hold"] = T["xmin"] - m2(T.tod)
    return T.drop(columns=["px", "xt"])


# ---------------------------------------------------------------- configs + chassis
def configs():
    """Grid (6): L {5, 10, 20} x N {2, 3}; L outer; names 27a..27f."""
    out, names = {}, iter("abcdef")
    for Lk in LS:
        for Nk in NS:
            out["27" + next(names)] = dict(L=Lk, N=Nk, key=f"L{Lk}N{Nk}", label=f"L{Lk}-N{Nk}-TX30")
    return out


def select(S, cfg, cap=DAY_CAP):
    s = S[(S[cfg["key"]] > 0) & S.r.notna()]
    s = s.sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    return s


def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["avg_r_gross"] = round(float(t.r_gross.mean()), 4) if len(t) else None
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    for nm, sg in (("long", 1), ("short", -1)):
        x = t[t.side == sg]
        o["by_side"][nm]["avg_r_gross"] = round(float(x.r_gross.mean()), 4) if len(x) else None
    o["by_slot"] = {str(int(k)): {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4),
                                  "avg_r_gross": round(float(x.r_gross.mean()), 4)} for k, x in t.groupby("tod")}
    return o


def random_control(sel, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar 10:00-15:00 (5-min grid)."""
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(1000), m2(1500) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    return walk(R, random=True)


def rand_block(t):
    Rc = random_control(t)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr, rr = t.r.to_numpy()[ok], Rc.r.to_numpy()[ok]
    sd = t.side.to_numpy()[ok]
    o = {"random_avg_r": round(float(rr.mean()), 4), "signal_minus_random": round(float(tr.mean() - rr.mean()), 4),
         "random_n": int(ok.sum())}
    for nm, sg in (("long", 1), ("short", -1)):
        q = sd == sg
        if q.any():
            o[f"random_avg_r_{nm}"] = round(float(rr[q].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[q].mean() - rr[q].mean()), 4)
    return o


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    half = sys.argv[3] if len(sys.argv) > 3 else None
    if half == "check" and stage in ("x", "sig", "walk"):
        assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
    if stage == "x":
        mod = load_mod()
        dly = load_daily()
        syms = sorted(p.stem for p in CACHE.glob("*.parquet") if p.stem not in mod.LEV and p.stem != "SPY_ctx")
        dsyms = set(dly.symbol)
        jobs = [(s, half, dly[dly.symbol == s][["date", "high", "low", "close"]]) for s in syms if s in dsyms]
        t0 = time.time()
        out = []
        with Pool(3) as p:
            for k, x in enumerate(p.imap_unordered(x_job, jobs, chunksize=4)):
                if x is not None:
                    out.append(x)
                if k % 200 == 0:
                    print(k, round(time.time() - t0), flush=True)
        X = pd.concat(out, ignore_index=True)
        X["slot"] = X.slot.astype(int)
        X["x"] = X.x.astype("float32")
        no_locked(X.date.unique())
        X.to_parquet(W / f"x_{half}.parquet")
        print("x rows", len(X), "symbols", X.symbol.nunique(), "days", X.date.nunique(), round(time.time() - t0), "s")
    elif stage == "sig":
        build_sig(W, half)
    elif stage == "walk":
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = full_stats(t, n)
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_gross"], o["avg_r_wo_best_day"],
                  o["total_r"], o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"),
                  o["by_side"]["long"].get("avg_r"), o["by_side"]["short"].get("avg_r"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k]["total_r"], -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-27 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__),
              "sha256_module_at_freeze": sha(MOD), "sha256_symbols": sha(SYMF), "configs_counted_this_candidate": 7,
              "configs_note": "6 grid + 1 bias diagnostic (PLAN sec. 4)", "check_informed": False, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "CHECK is scored once"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg)
        o = full_stats(t, n)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o.update(rand_block(t))
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0
                 and o["trades_per_session"] >= 2.0)
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and o["avg_r"] > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        t[["symbol", "date", "tod", "side", "r", "r_u", "kd", "hold"]].to_csv(HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = full_stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_gross", "avg_r_wo_best_day",
                                                "best_day_share", "total_r", "t_day_clustered",
                                                "worst_day_per_trade_session", "first_half_avg_r", "second_half_avg_r",
                                                "avg_r_u025")}
            res[name]["long_avg_r"] = o["by_side"]["long"].get("avg_r")
            res[name]["short_avg_r"] = o["by_side"]["short"].get("avg_r")
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
