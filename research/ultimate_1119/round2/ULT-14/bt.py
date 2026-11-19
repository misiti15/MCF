"""ULT-14 SNAP backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-14", 5, 6).

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo); features and
trigger from the LIVE module itself (modules/ULT-14.py: features(), trigger()); a superset (D 0.20, window 11:00-15:00,
both sides, ADV20 >= $50M, U2 intake with cost_r <= 0.08, shorts ETB only) is built once per half; every grid config is
a sub-filter (D 0.30 / window 14:00-15:00 / exit).
Chassis (round 2): entry at the OPEN of the 1-minute bar that starts at the decision-bar close (LR8 entry cost on it);
bracket around the decision close (u = 0.25 x prior-day daily ATR, as the live LabStrategy sets it), walked on 1-minute
bars (data/cache_hist/1Min): stop first, then target; stop gap-through at the worse of open/stop; target at the limit
with no exit cost; time exit at the close of minute entry+44 (45 min) or the 15:49 minute (flat 15:50).
  A = t05s1 cap45: +0.5u limit / -1u stop; R per u.   B = t1s1 cap45: +1u / -1u; R per u.  (R per u = actual risk;
  R in 0.25-dATR units is the same number.)
Costs LR8 (entry (1c + 1bp) x tod mult; exit 1c + 1bp except target; +2c stops) + 1.2 bp of entry notional borrow fee
on every short. One lot per symbol (both sides share it); refire only >= 30 min after the exit; max 2 per
symbol-session; day cap 30 over both sides (first by time, ties ADV20 desc). Halves: FIT = 2024-10 + 2025-03..09;
CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
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
MOD = HERE.parents[1] / "modules" / "ULT-14.py"
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")
N_CUM = 774
DAY_CAP = 30
BORROW = 1.2e-4
TGT = {"A": 0.5, "B": 1.0}


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult14", MOD)
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
    f = f[[c for c in f.columns if not (c.startswith(FORBIDDEN[:3]) or "heat" in c.lower())]]   # forbidden cols dropped
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    tod = r["tod"]
    adv = f["adv20"].fillna(0).to_numpy()
    base = (tod >= 1100) & (tod <= 1500) & (adv >= mod.MIN_ADV)
    tl = mod.trigger(r, 1, 0.20) & base
    etb = f["symbol"].isin(etb_set()).to_numpy()
    ts_all = mod.trigger(r, -1, 0.20) & base
    ts = ts_all & etb
    out = []
    for sgn, mk in ((1, tl), (-1, ts)):
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
        s["side"] = sgn
        for k in ("r3a", "di7", "atrp", "bp", "rsi5", "spy60", "spy950", "cost_r"):
            s[k] = r[k][mk]
        out.append(s)
    s = pd.concat(out, ignore_index=True)
    n_not_etb = int((ts_all & ~etb).sum())
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, s, days, n_not_etb


# ---------------------------------------------------------------- stage 2: 1-minute walk (both exits, side-aware)
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

    def one(ix, tod, u, dclose, sgn):
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
        res = [e, dclose]
        for g in ("A", "B"):
            p, k, x = path(ix, j0, sgn, dclose - sgn * u, dclose + sgn * TGT[g] * u, tend)
            if p is None:
                return None
            res += [p, k, int(hhmm(m2(x) + 1))]
        return tuple(res)

    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        u = 0.25 * r.atr_d
        a = None if ix is None else one(ix, r.tod, u, None if r.random else r.close, int(r.side))
        res.append((r.Index,) + (a if a else (np.nan,) * 8))
    return res


def cost_R(side, tod, e, px, kd, u, borrow=True):
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    bf = np.where((side < 0) & borrow, BORROW * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / u


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g, 1119 + i) for i, (s, g) in enumerate(T.groupby("symbol")) if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "pxA", "kdA", "xtA", "pxB", "kdB", "xtB"]).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    u = 0.25 * T.atr_d.to_numpy()
    tod = T.tod.to_numpy()
    sd = T.side.to_numpy()
    for g in ("A", "B"):
        T["r" + g] = cost_R(sd, tod, T.e.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), u)
        T["rsc" + g] = cost_R(sd, tod, T.dclose.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), u,
                              borrow=False)                        # bias diagnostic: signal-close fill, no borrow
        T["xmin" + g] = np.where(T["xt" + g].notna(), m2(T["xt" + g].fillna(0)), np.nan)
    return T


def bind(T, g):
    """Expose exit g's columns under the generic names stats() reads (r, kd, xmin, hold, r_sigclose, r_u)."""
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T["r" + g], T["kd" + g], T["xmin" + g], T["rsc" + g]
    T["r_u"] = T["r"]
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    out, names = {}, iter("abcdefgh")
    for w in ((1400, 1500), (1100, 1500)):
        for dd in (0.20, 0.30):
            for ex in ("A", "B"):
                out["14" + next(names)] = dict(window=list(w), d=dd, exit=ex,
                                               label=f"W{w[0]}-{w[1]}-D{dd:.2f}-{'t05s1' if ex == 'A' else 't1s1'}cap45")
    return out


def select(S, cfg, cap=DAY_CAP):
    S = bind(S, cfg["exit"])
    w0, w1 = cfg["window"]
    # long: ret3_atr <= -d ; short: ret3_atr >= +d  <=>  -side * ret3_atr >= d
    m = (S.tod >= w0) & (S.tod <= w1) & (-S.side * S.r3a >= cfg["d"]) & S.r.notna()
    s = S[m].sort_values(["symbol", "date", "tod", "side"], kind="mergesort")
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
         "avg_r": round(avg, 4), "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4)
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
                      if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share",
                               "total_r", "t_day_clustered", "worst_day", "avg_r_ex_0403_0409", "first_half_avg_r",
                               "second_half_avg_r", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down")}
                     if len(x) else {"trades": 0})
    return o


def sub_halves(t):
    a = t[(t.date < "2025-06-01")]
    b = t[(t.date >= "2025-06-01")]
    return {"A_avg_r": round(float(a.r.mean()), 4) if len(a) else None, "A_n": int(len(a)),
            "B_avg_r": round(float(b.r.mean()), 4) if len(b) else None, "B_n": int(len(b))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in the config window; same
    exit."""
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(cfg["window"][0]), m2(cfg["window"][1]) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    W = walk(R, random=True)
    return bind(W, cfg["exit"])


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
        print("walked", len(T), int(T.rA.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = stats(t, n)
            o.update(sub_halves(t))
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), "L", o["long"].get("avg_r"),
                  o["long"].get("trades"), "S", o["short"].get("avg_r"), o["short"].get("trades"), flush=True)
        grid = dict(res)
        elig = {k: v for k, v in grid.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else grid
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(grid).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-14 fit pick, frozen BEFORE any check data is built.",
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
        t = select(S, cfg)
        o = stats(t, n)
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
            t = select(S, cfg)
            o = stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                "first_half_avg_r", "second_half_avg_r")}
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
