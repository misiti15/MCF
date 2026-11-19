"""ULT-23 COLLAPSE-BASKET backtest (ultimate_1119 round3/PLAN.md sec. 2, 3 "ULT-23", 5, 6). Adapted from round2/ULT-13/bt.py.

Signals: lab frames + context (spy_fo); features, universe flags and trigger from the LIVE module (modules/ULT-23.py).
A superset (RMAX 35, window 10:15-15:00, cost_r <= 0.08, universe Q (EQB, ADV20 >= $30M) or M (non-fund, ADV20 >= $1B,
price >= $20), universal SPY long filter) is built once per half; every grid config is a sub-filter.
Chassis (round 2/3): entry at the OPEN of the 1-minute bar that starts at the decision-bar close (LR8 entry cost on it);
exits around the decision close (u = 0.25 x prior-day daily ATR), walked on 1-minute bars: stop first, then target;
stop gap-through at the worse of open/stop; target at the limit with no exit cost; +2c on stops; time exit at the close
of minute entry+44 (45 min) or the 15:49 minute (flat 15:50).
  T = t1s1 cap45 (ST7's): +1u limit / -1u stop.   H = t05s1 cap45: +0.5u limit / -1u stop.   R per u (actual risk).
Long only -> no borrow fee. One lot per symbol; refire only >= 30 min after the exit; max 2 per symbol-session; day cap
30 (first by time, ties ADV20 desc). Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest.
Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK fit|fitrandom|check|plateau
Educational only - not financial advice."""
from __future__ import annotations

import hashlib
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
sys.path.insert(0, str(HERE.parents[1] / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
MOD = HERE.parents[1] / "modules" / "ULT-23.py"
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")
N_CUM = 880
DAY_CAP = 30


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult23", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(mins):
    mins = np.asarray(mins, int)
    return (mins // 60) * 100 + mins % 60


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(FORBIDDEN[:3]) or "heat" in c.lower())]]   # forbidden cols dropped
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    tod = r["tod"]
    adv = f["adv20"].fillna(0).to_numpy()
    tr = mod.trigger(r, 35.0)
    base = r["intake"] & (tod >= mod.WINDOW[0]) & (tod <= mod.WINDOW[1]) & mod.in_universe(r, "QM")
    mk = base & r["univ_ok"] & tr
    s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
    for k in ("rsi", "rsi_prev", "spy_fo", "spy_r30", "is_q", "is_m", "fromOpen", "fo_thr", "bp", "cost_r"):
        s[k] = r[k][mk]
    nf = int((base & ~r["univ_ok"] & tr).sum())     # bars removed only by the universal SPY long filter
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, s, days, nf


# ---------------------------------------------------------------- stage 2: 1-minute walk (both exits)
def walk_job(args):
    sym, T, seed = args
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
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}

    def path(ix, j0, stop, tgt, tend):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if Lo[q] <= stop:
                px, kd, xt = min(O[q], stop), 1, hm_all[q]; break
            if tgt is not None and Hh[q] >= tgt:
                px, kd, xt = tgt, 2, hm_all[q]; break
            px, xt = Cc[q], hm_all[q]
        return px, kd, xt

    def one(ix, tod, u, dclose):
        hm = hm_all[ix]
        j0 = np.searchsorted(hm, tod)
        if j0 >= len(ix) or m2(hm[j0]) - m2(tod) > 4 or hm[j0] >= 1550:
            return None
        e = O[ix[j0]]
        if dclose is None:          # random control: decision close = close of the minute before tod
            if j0 == 0 or m2(hm[j0 - 1]) < m2(tod) - 5:
                return None
            dclose = Cc[ix[j0 - 1]]
        tend = min(int(hhmm(m2(hm[j0]) + 44)), 1549)
        pT, kT, xT = path(ix, j0, dclose - u, dclose + u, tend)
        pX, kX, xX = path(ix, j0, dclose - u, dclose + 0.5 * u, tend)      # H = t05s1 (kept in the X columns)
        if pT is None or pX is None:
            return None
        return e, dclose, pT, kT, int(hhmm(m2(xT) + 1)), pX, kX, int(hhmm(m2(xX) + 1))

    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        u = 0.25 * r.atr_d
        a = None if ix is None else one(ix, r.tod, u, None if r.random else r.close)
        res.append((r.Index,) + (a if a else (np.nan,) * 8))
    return res


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g, 1119 + i) for i, (s, g) in enumerate(T.groupby("symbol")) if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "pxT", "kdT", "xtT", "pxX", "kdX", "xtX"]).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    u = 0.25 * T.atr_d.to_numpy()
    tod = T.tod.to_numpy()
    for g, unit in (("T", 1.0), ("X", 1.0)):
        T["r" + g] = cost_R(tod, T.e.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), unit * u)
        T["rsc" + g] = cost_R(tod, T.dclose.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), unit * u)
        T["xmin" + g] = np.where(T["xt" + g].notna(), m2(T["xt" + g].fillna(0)), np.nan)
    return T


def cost_R(tod, e, px, kd, u):
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    return (px - e - ec - xc) / u


def bind(T, g):
    """Expose exit g's columns under the generic names stats() reads (r, kd, xmin, hold, r_sigclose, r_u)."""
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T["r" + g], T["kd" + g], T["xmin" + g], T["rsc" + g]
    T["r_u"] = T["r"]
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (12): universe {Q, M, QM} x RMAX {30, 35} x exit {T t1s1 cap45, H t05s1 cap45}; universe outer."""
    out, names = {}, iter("abcdefghijkl")
    for un in ("Q", "M", "QM"):
        for rm in (30.0, 35.0):
            for ex in ("T", "H"):
                out["23" + next(names)] = dict(univ=un, rmax=rm, exit=ex,
                                               label=f"{un}-RMAX{rm:g}-{'t1s1cap45' if ex == 'T' else 't05s1cap45'}")
    return out


def in_univ(S, un):
    q, mg = S.is_q.astype(bool), S.is_m.astype(bool)
    return {"Q": q, "M": mg, "QM": q | mg}[un]


ANCHOR = {}


def select(S, cfg, cap=DAY_CAP):
    S = bind(S, "T" if cfg["exit"] == "T" else "X")
    m = in_univ(S, cfg["univ"]) & (S.rsi <= cfg["rmax"]) & S.r.notna()
    s = S[m].sort_values(["symbol", "date", "tod"], kind="mergesort")
    keep = []
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                keep.append(i); n += 1; free_at = x + 30
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    return s


# ---------------------------------------------------------------- stage 4: statistics
SPY = None


def spy_types():
    global SPY
    if SPY is None:
        from stats import spy_days
        SPY = spy_days()
    return SPY


def stats(t, n_sessions, col="r"):
    t = t[t[col].notna()]
    if not len(t):
        return {"trades": 0, "sessions": int(n_sessions), "trades_per_session": 0.0}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    avg = float(t[col].mean())
    best = day.idxmax()
    dev = (t[col] - avg).groupby(t["date"]).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    tps = len(t) / day.size
    ty = t.date.map(spy_types()["type"])
    o = {"trades": int(len(t)), "sessions": int(n_sessions), "sessions_traded": int(day.size),
         "trades_per_session": round(len(t) / n_sessions, 3), "win": round(float((t[col] > 0).mean()), 3),
         "avg_r": round(avg, 4), "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4)
         if (t.date != best).any() else None, "best_day": str(best),
         "best_day_r": round(float(day.max()), 2),
         "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2),
         "total_r_per_session": round(tot / n_sessions, 4), "worst_day": round(float(day.min()), 2),
         "worst_day_per_trade_session": round(float(day.min()) / tps, 3),
         "t_day_clustered": round(avg / se, 2) if se > 0 else None}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, col]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    ex = t[~t.date.between("2025-04-03", "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    o["n_ex_0403_0409"] = int(len(ex))
    o["avg_r_u025"] = round(float(t["r_u"].mean()), 4) if "r_u" in t else None
    o["median_hold_min"] = float(np.nanmedian(t["hold"]))
    o["exit_mix"] = {k: int(v) for k, v in t.kd.map({0: "time", 1: "stop", 2: "target"}).value_counts().items()}
    d = sorted(t.date.unique())
    if len(d) > 1:
        mid = d[len(d) // 2]
        o["first_half_avg_r"] = round(float(t.loc[t.date < mid, col].mean()), 4)
        o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, col].mean()), 4)
    return o


def sub_halves(t):
    a = t[(t.date < "2025-06-01")]
    b = t[(t.date >= "2025-06-01")]
    return {"A_avg_r": round(float(a.r.mean()), 4) if len(a) else None, "A_n": int(len(a)),
            "B_avg_r": round(float(b.r.mean()), 4) if len(b) else None, "B_n": int(len(b))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions and count as the selected trades; a random decision bar in the config window; same exit."""
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(1015), m2(1500) + 1, 5)   # module window 10:15-15:00
    R = sel[["symbol", "date", "atr_d", "close", "tod"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    W = walk(R, random=True)
    return bind(W, "T" if cfg["exit"] == "T" else "X")


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        mod = load_mod()
        sigs, days, nf = [], [], 0
        with Pool(2) as p:
            for m, s, d, k in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), k, flush=True)
                sigs.append(s); days += d; nf += k
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        print("mega names with a signal:", sorted(S.loc[S.is_m.astype(bool), "symbol"].unique()))
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"spyfilter_{half}.txt").write_text(str(nf))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.rT.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in {**configs(), **ANCHOR}.items():
            t = select(S, cfg)
            o = stats(t, n)
            o.update(sub_halves(t))
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), flush=True)
        grid = dict(res)
        elig = {k: v for k, v in grid.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else grid
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(grid).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        mod_sha = sha(MOD)
        fs = {"note": "Educational only - not financial advice. ULT-23 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": grid[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "rule": "max fit total R minus best fit day among configs >= 2.0/session",
              "fit": grid[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": mod_sha,
              "configs_counted_this_candidate": 13, "configs_note": "12 grid + 1 bias diagnostic (PLAN sec. 4)",
              "sha256_symbols": sha(MOD.parent / "ULT-23_symbols.json"), "check_informed": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, grid[pick]["cfg"]["label"], "eligible:", sorted(elig))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg)
        o = stats(t, n)
        o["bias_diag_sigclose_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = stats(select(S, cfg, cap=0), n)
        Rc = random_control(t, cfg)
        ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
        o["random_avg_r"] = round(float(Rc.r[ok].mean()), 4)
        o["signal_minus_random"] = round(float(t.r.to_numpy()[ok].mean() - Rc.r[ok].mean()), 4)
        o["random_n"] = int(ok.sum())
        o["by_universe"] = {k: stats(t[in_univ(t, k)], n) for k in ("Q", "M")}
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0 and o["trades_per_session"] >= 2.0)
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and o["avg_r"] > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in {**configs(), **ANCHOR}.items():
            t = select(S, cfg)
            o = stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                "first_half_avg_r", "second_half_avg_r")}
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        Rc = random_control(t, fs["cfg"])
        ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
        o = {"random_avg_r": round(float(Rc.r[ok].mean()), 4),
             "signal_minus_random": round(float(t.r.to_numpy()[ok].mean() - Rc.r[ok].mean()), 4), "n": int(ok.sum()),
             "bias_diag_sigclose_avg_r": round(float(t.r_sigclose.mean()), 4), "uncapped": stats(select(S, fs["cfg"], cap=0), n)}
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
