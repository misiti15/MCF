"""ULT-16 COST-GEO backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-16", 5, 6).

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo); features and
triggers from the LIVE module itself (modules/ULT-16.py: features(), trigger(), vol_ok()). Superset = both sides, ADV20
>= $150M, intake cost_r <= 0.10 (u = 0.25 dATR), shorts ETB only; every grid config is a sub-filter / exit variant.
Exits (walked on 1-minute bars, data/cache_hist/1Min), for m in {0.5, 1.0}: Ru = m x atr_d; bracket +1 Ru limit /
-1 Ru stop around the decision close (as the module's stop_price / target_price); stop first, then target; stop
gap-through at the worse of open/stop; target at the limit with no exit cost; time exit at the close of minute
entry+44 (45 min) or the 15:49 minute (flat 15:50). R per Ru; r_u = the same trade in 0.25-dATR units.
Entry MKT: OPEN of the 1-minute bar that starts at the decision-bar close, LR8 entry cost.
Entry LMT: limit = decision close - side x 0.1u (u = 0.25 dATR), working for the 10 minutes starting at the decision
close; filled only in a minute that trades THROUGH the limit by >= $0.01 (long: low <= limit - 0.01; short: high >=
limit + 0.01); fill at the limit; entry cost 0. In the fill minute only the stop is checked (if the same minute also
reaches the stop, the trade stops out at the stop: costlier assumption); target from the next minute. Unfilled = no
trade; the symbol is blocked until the order expires; an unfilled order does not count toward the 2 per symbol-session.
Costs LR8 (entry (1c + 1bp) x tod mult; exit 1c + 1bp except target; +2c stops) + 1.2 bp of entry notional borrow fee
on every short. One lot per symbol (both sides share it); refire only >= 30 min after the exit; max 2 per
symbol-session; day cap 30 filled trades over both sides (first by decision time, ties ADV20 desc).
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
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
MOD = HERE.parents[1] / "modules" / "ULT-16.py"
N_CUM = 774
DAY_CAP = 30
BORROW = 1.2e-4
LMT_OFF = 0.1          # x u better than the decision close
LMT_VALID = 10         # minutes
MS = (0.5, 1.0)
VARS = [(m, e) for m in MS for e in ("M", "L")]       # walk variants


def vname(m, e):
    return f"{'05' if m == 0.5 else '10'}{e}"


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult16", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


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
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower())]]
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    adv = f["adv20"].fillna(0).to_numpy()
    base = adv >= mod.MIN_ADV
    etb = f["symbol"].isin(etb_set()).to_numpy()
    tl = mod.trigger(r, 1) & base
    ts_all = mod.trigger(r, -1) & base
    ts = ts_all & etb
    out = []
    for sgn, mk in ((1, tl), (-1, ts)):
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
        s["side"] = sgn
        for k in ("atrp", "cost_r", "rsi", "rsi5", "spy950", "spy_r30"):
            s[k] = r[k][mk]
        out.append(s)
    s = pd.concat(out, ignore_index=True)
    n_not_etb = int((ts_all & ~etb).sum())
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, s, days, n_not_etb


# ---------------------------------------------------------------- stage 2: 1-minute walk (4 variants, side-aware)
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
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}

    def path(ix, j0, sgn, stop, tgt, tend):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if sgn > 0:
                if Lo[q] <= stop:
                    px, kd, xt = min(O[q], stop), 1, hm_all[q]; break
                if Hh[q] >= tgt:
                    px, kd, xt = tgt, 2, hm_all[q]; break
            else:
                if Hh[q] >= stop:
                    px, kd, xt = max(O[q], stop), 1, hm_all[q]; break
                if Lo[q] <= tgt:
                    px, kd, xt = tgt, 2, hm_all[q]; break
            px, xt = Cc[q], hm_all[q]
        return px, kd, xt

    def one(ix, tod, atr, dclose, sgn):
        hm = hm_all[ix]
        j0 = np.searchsorted(hm, tod)
        if j0 >= len(ix) or m2(hm[j0]) - m2(tod) > 4 or hm[j0] >= 1550:
            return None
        if dclose is None:          # random control: decision close = close of the minute before tod
            if j0 == 0 or m2(hm[j0 - 1]) < m2(tod) - 5:
                return None
            dclose = Cc[ix[j0 - 1]]
        u = 0.25 * atr
        res = [dclose]
        lim = dclose - sgn * LMT_OFF * u
        # LMT fill search (minutes starting tod .. tod+9, before 15:50)
        jf = None
        for jj in range(j0, len(ix)):
            if m2(hm[jj]) > m2(tod) + LMT_VALID - 1 or hm[jj] >= 1550:
                break
            q = ix[jj]
            if (sgn > 0 and Lo[q] <= lim - 0.01) or (sgn < 0 and Hh[q] >= lim + 0.01):
                jf = jj; break
        for m, ent in VARS:
            stop, tgt = dclose - sgn * m * atr, dclose + sgn * m * atr
            if ent == "M":
                e, em = O[ix[j0]], hm[j0]
                tend = min(int(hhmm(m2(em) + 44)), 1549)
                p, k, x = path(ix, j0, sgn, stop, tgt, tend)
                if p is None:
                    return None
            else:
                if jf is None:
                    res += [np.nan, np.nan, -2, np.nan, np.nan]   # unfilled
                    continue
                q = ix[jf]
                e, em = lim, hm[jf]
                tend = min(int(hhmm(m2(em) + 44)), 1549)
                if (sgn > 0 and Lo[q] <= stop) or (sgn < 0 and Hh[q] >= stop):
                    p, k, x = stop, 1, em                          # stopped in the fill minute (costlier)
                elif jf + 1 < len(ix) and hm[jf + 1] <= tend:
                    p, k, x = path(ix, jf + 1, sgn, stop, tgt, tend)
                    if p is None:
                        p, k, x = Cc[q], 0, em
                else:
                    p, k, x = Cc[q], 0, em
            res += [e, p, k, int(hhmm(m2(x) + 1)), int(em)]
        return tuple(res)

    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        a = None if ix is None else one(ix, r.tod, r.atr_d, None if r.random else r.close, int(r.side))
        res.append((r.Index,) + (a if a else (np.nan,) * (1 + 5 * len(VARS))))
    return res


def cost_R(side, tod, e, px, kd, unit, lmt, borrow=True):
    ec = np.where(lmt, 0.0, (0.01 + e * 1e-4) * tod_cost_mult(tod))
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    bf = np.where((side < 0) & borrow, BORROW * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / unit


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    cols = ["i", "dclose"]
    for m, ent in VARS:
        v = vname(m, ent)
        cols += [f"e{v}", f"px{v}", f"kd{v}", f"xt{v}", f"em{v}"]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    tod = T.tod.to_numpy()
    sd = T.side.to_numpy()
    for m, ent in VARS:
        v = vname(m, ent)
        unit = m * T.atr_d.to_numpy()
        lmt = ent == "L"
        T["r" + v] = cost_R(sd, tod, T["e" + v].to_numpy(), T["px" + v].to_numpy(), T["kd" + v].to_numpy(), unit, lmt)
        e_sc = T.dclose.to_numpy() if not lmt else T["e" + v].to_numpy()
        T["rsc" + v] = cost_R(sd, tod, e_sc, T["px" + v].to_numpy(), T["kd" + v].to_numpy(), unit, lmt, borrow=False)
        T["xmin" + v] = np.where(T["xt" + v].notna(), m2(T["xt" + v].fillna(0)), np.nan)
        T["emin" + v] = np.where(T["em" + v].notna(), m2(T["em" + v].fillna(0)), np.nan)
    return T


def bind(T, cfg):
    """Expose the config's variant under the generic names stats() reads."""
    v = vname(cfg["m"], cfg["entry"])
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T["r" + v], T["kd" + v], T["xmin" + v], T["rsc" + v]
    T["r_u"] = T["r"] * 4 * cfg["m"]                     # same trade in 0.25-dATR units
    T["hold"] = T["xmin"] - T["emin" + v]
    T["filled"] = T["kd"] != -2
    T["valid"] = T["dclose"].notna()
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    out, names = {}, iter("abcdefgh")
    for m in MS:
        for ent in ("M", "L"):
            for vf in (0.0, 2.5):
                out["16" + next(names)] = dict(m=m, entry=ent, vol=vf,
                                               label=f"m{m:g}-{'MKT' if ent == 'M' else 'LMT'}-{'vol2.5' if vf else 'novol'}")
    return out


def select(S, cfg, cap=DAY_CAP, attempts=False):
    S = bind(S, cfg)
    m = S.valid & (S.atrp >= cfg["vol"] if cfg["vol"] > 0 else S.valid)
    s = S[m].sort_values(["symbol", "date", "tod", "side"], kind="mergesort")
    keep, tried = [], 0
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x, fl in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy(), g.filled.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                tried += 1
                if fl:
                    keep.append(i); n += 1; free_at = x + 30
                else:
                    free_at = t + LMT_VALID
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    if attempts:
        return s, tried
    return s


# ---------------------------------------------------------------- stage 4: statistics
SPY = None


def spy_types():
    global SPY
    if SPY is None:
        from stats import spy_days
        SPY = spy_days()
    return SPY


def stats(t, n_sessions, col="r", sides=True):
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
         "avg_r": round(avg, 4), "avg_r_u": round(float(t["r_u"].mean()), 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4)
         if (t.date != best).any() else None, "best_day": str(best),
         "best_day_r": round(float(day.max()), 2),
         "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2),
         "total_r_per_session": round(tot / n_sessions, 4), "worst_day": round(float(day.min()), 2),
         "worst_day_date": str(day.idxmin()),
         "worst_day_per_trade_session": round(float(day.min()) / tps, 3),
         "t_day_clustered": round(avg / se, 2) if se > 0 else None}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, col]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    ex = t[~t.date.between("2025-04-03", "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    o["n_ex_0403_0409"] = int(len(ex))
    o["median_hold_min"] = float(np.nanmedian(t["hold"]))
    o["exit_mix"] = {k: int(v) for k, v in t.kd.map({0: "time", 1: "stop", 2: "target"}).value_counts().items()}
    d = sorted(t.date.unique())
    if len(d) > 1:
        mid = d[len(d) // 2]
        o["first_half_avg_r"] = round(float(t.loc[t.date < mid, col].mean()), 4)
        o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, col].mean()), 4)
    if sides:
        for nm, sg in (("long", 1), ("short", -1)):
            x = t[t.side == sg]
            o[nm] = ({k: v for k, v in stats(x, n_sessions, col, sides=False).items()
                      if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_u", "avg_r_wo_best_day",
                               "best_day_share", "total_r", "t_day_clustered", "worst_day", "avg_r_ex_0403_0409",
                               "first_half_avg_r", "second_half_avg_r", "avg_r_spy_up", "avg_r_spy_flat",
                               "avg_r_spy_down")}
                     if len(x) else {"trades": 0})
    return o


def sub_halves(t):
    a = t[(t.date < "2025-06-01")]
    b = t[(t.date >= "2025-06-01")]
    return {"A_avg_r": round(float(a.r.mean()), 4) if len(a) else None, "A_n": int(len(a)),
            "B_avg_r": round(float(b.r.mean()), 4) if len(b) else None, "B_n": int(len(b))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def full_stats(S, cfg, n):
    t, tried = select(S, cfg, attempts=True)
    o = stats(t, n)
    o["orders_tried"] = int(tried)
    o["fill_rate"] = round(float(t.shape[0] / tried), 3) if tried and cfg["entry"] == "L" else None
    return t, o


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in that side's window; same
    entry mode and exit."""
    rng = np.random.default_rng(seed)
    mod = load_mod()
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    tods = []
    for sd in R.side.to_numpy():
        w = mod.WIN_LONG if sd > 0 else mod.WIN_SHORT
        lo = max(m2(w[0]), m2(1020)) if sd > 0 else m2(w[0])   # the long trigger cannot fire before 10:20 (SPY r30)
        tods.append(int(hhmm(rng.choice(np.arange(lo, m2(w[1]) + 1, 5)))))
    R["tod"] = tods
    W = walk(R, random=True)
    return bind(W, cfg)


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def rand_block(t, cfg):
    Rc = random_control(t, cfg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr = t.r.to_numpy()
    o = {"random_avg_r": round(float(Rc.r[ok].mean()), 4),
         "signal_minus_random": round(float(tr[ok].mean() - Rc.r[ok].mean()), 4), "random_n": int(ok.sum())}
    if cfg["entry"] == "L":
        o["random_fill_rate"] = round(float(Rc.filled[Rc.valid].mean()), 3)
    for nm, sg in (("long", 1), ("short", -1)):
        k = ok & (t.side.to_numpy() == sg)
        if k.any():
            o[f"random_avg_r_{nm}"] = round(float(Rc.r[k].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[k].mean() - Rc.r[k].mean()), 4)
    return o


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days, nf = [], [], 0
        with Pool(2) as p:
            for m, s, d, k in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), int((s.side > 0).sum()), int((s.side < 0).sum()), "non-ETB short bars", k, flush=True)
                sigs.append(s); days += d; nf += k
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"nonetb_{half}.txt").write_text(str(nf))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r10M.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t, o = full_stats(S, cfg, n)
            o.update(sub_halves(t))
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_u"], o["avg_r_wo_best_day"],
                  o["total_r"], o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), "fill", o["fill_rate"],
                  "L", o["long"].get("avg_r"), o["long"].get("trades"), "S", o["short"].get("avg_r"),
                  o["short"].get("trades"), flush=True)
        grid = dict(res)
        elig = {k: v for k, v in grid.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else grid
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(grid).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-16 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": grid[pick]["cfg"],
              "eligible_2_per_session": sorted(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "fit": grid[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "configs_counted_this_candidate": 9, "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)",
              "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, grid[pick]["cfg"]["label"], "eligible:", sorted(elig))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t, o = full_stats(S, cfg, n)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, cfg, cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        o.update(rand_block(t, cfg))
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
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            t, o = full_stats(S, cfg, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_u", "avg_r_wo_best_day",
                                                "best_day_share", "total_r", "t_day_clustered",
                                                "worst_day_per_trade_session", "first_half_avg_r",
                                                "second_half_avg_r", "fill_rate")}
            res[name]["long_avg_r"] = o["long"].get("avg_r"); res[name]["long_n"] = o["long"].get("trades")
            res[name]["short_avg_r"] = o["short"].get("avg_r"); res[name]["short_n"] = o["short"].get("trades")
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, fs["cfg"], cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
