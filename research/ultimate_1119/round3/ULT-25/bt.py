"""ULT-25 ULTRA-CHEAP backtest (ultimate_1119 round3/PLAN.md sec. 2, 3 "ULT-25", 5, 6). Adapted from round3/ULT-23/bt.py
(stats / sub-halves / SPY day types imported from it unchanged).

Signals: lab frames + context (spy_fo); features, universe and triggers from the LIVE module (modules/ULT-25.py).
A superset (window 10:30-15:00, both sides, shorts easy-to-borrow (data/universe.csv, today's flag) and never LEV) is
built once per half; every grid config is a sub-filter (window) plus an exit.
Chassis (round 2/3): entry at the OPEN of the 1-minute bar that starts at the decision-bar close (LR8 entry cost on it);
brackets around the decision close, walked on 1-minute bars: stop first, then target; stop gap-through at the worse of
open/stop; target at the limit, no exit cost; +2c on stops; time exit at the close of minute entry+44 (45 min) or the
15:49 minute (flat 15:50). Unit Ru = m x atr_d:  H = t05s1 (+0.5 Ru / -1 Ru), T = t1s1 (+1 / -1 Ru), R per Ru;
X = TX-45 with a 2 Ru catastrophic stop, R per 2 Ru. r_u = the same P&L per 0.25-dATR unit.
Costs LR8 (entry (1c + 1bp) x tod mult; exit 1c + 1bp; +2c on stops) + borrow on shorts (1.2 bp of entry notional,
3 bp under $20). One lot per symbol across both sides; refire >= 30 min after the exit; max 2 per symbol-session; day
cap 30 (first by time, ties ADV20 desc); a bar where both sides fire on one name is skipped.
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

_s = importlib.util.spec_from_file_location("ult23bt", HERE.parent / "ULT-23" / "bt.py")
B23 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B23)
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
FIT_MONTHS = B23.FIT_MONTHS
MOD = HERE.parents[1] / "modules" / "ULT-25.py"
SYMF = HERE.parents[1] / "modules" / "ULT-25_symbols.json"
N_CUM = 880
DAY_CAP = 30
MS = (0.25, 0.50)
EXITS = {"H": (0.5, 1.0), "T": (1.0, 1.0), "X": (None, 2.0)}     # (target, stop) in Ru
WINDOWS = {"1030": (1030, 1500), "1300": (1300, 1500)}


def load_mod(name="ult25"):
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


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith("win_") or c.startswith("r_long") or c.startswith("r_short")
                                        or "heat" in c.lower())]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    tod = r["tod"]
    win = (tod >= 1030) & (tod <= 1500)
    etb = f["symbol"].isin(etb_set()).to_numpy()
    L = mod.signal(r, 1) & win
    S = mod.signal(r, -1) & win & etb
    both = L & S
    out = []
    for sgn, mk in ((1, L & ~both), (-1, S & ~both)):
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
        s["side"] = sgn
        for k in ("coll", "dip", "ts1", "ts2", "is_lev", "cost_r", "atrp", "spy_fo", "spy_r60", "spy_950"):
            s[k] = r[k][mk]
        out.append(s)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    nu = int((r["univ"] & win).sum())
    return month, pd.concat(out, ignore_index=True), days, int(both.sum()), nu


# ---------------------------------------------------------------- stage 2: 1-minute walk (6 exits)
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

    def path(ix, j0, s, stop, tgt, tend):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if (s > 0 and Lo[q] <= stop) or (s < 0 and Hh[q] >= stop):
                px, kd, xt = (min(O[q], stop) if s > 0 else max(O[q], stop)), 1, hm_all[q]; break
            if tgt is not None and ((s > 0 and Hh[q] >= tgt) or (s < 0 and Lo[q] <= tgt)):
                px, kd, xt = tgt, 2, hm_all[q]; break
            px, xt = Cc[q], hm_all[q]
        return px, kd, xt

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
                tend = min(int(hhmm(m2(hm[j0]) + 44)), 1549)
                row = [O[ix[j0]], dclose]
                for m in MS:
                    Ru = m * r.atr_d
                    for g, (up, dn) in EXITS.items():
                        px, kd, xt = path(ix, j0, r.side, dclose - r.side * dn * Ru,
                                          None if up is None else dclose + r.side * up * Ru, tend)
                        if px is None:
                            row = None; break
                        row += [px, kd, int(hhmm(m2(xt) + 1))]
                    if row is None:
                        break
        res.append((r.Index,) + tuple(row if row else [np.nan] * 20))
    return res


def exit_keys():
    return [f"{int(m * 100):02d}{g}" for m in MS for g in EXITS]


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
    cols = ["i", "e", "dclose"] + [f"{a}{k}" for k in exit_keys() for a in ("px", "kd", "xt")]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    tod, side, atr = T.tod.to_numpy(), T.side.to_numpy(), T.atr_d.to_numpy()
    for k in exit_keys():
        m, g = int(k[:2]) / 100, k[2]
        unit = EXITS[g][1] * m * atr
        px, kd = T["px" + k].to_numpy(), T["kd" + k].to_numpy()
        T["r" + k] = cost_R(side, tod, T.e.to_numpy(), px, kd, unit)
        T["ru" + k] = cost_R(side, tod, T.e.to_numpy(), px, kd, 0.25 * atr)
        T["rsc" + k] = cost_R(side, tod, T.dclose.to_numpy(), px, kd, unit, with_borrow=False)
        T["xmin" + k] = np.where(T["xt" + k].notna(), m2(T["xt" + k].fillna(0)), np.nan)
        T = T.drop(columns=["px" + k, "xt" + k])
    return T


def bind(T, k):
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"], T["r_u"] = T["r" + k], T["kd" + k], T["xmin" + k], T["rsc" + k], T["ru" + k]
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (12): m {0.25, 0.50} x exit {H t05s1, T t1s1, X TX-45} x window {1030, 1300}; m outer, window inner."""
    out, names = {}, iter("abcdefghijkl")
    lab = {"H": "t05s1", "T": "t1s1", "X": "TX45"}
    for m in MS:
        for g in EXITS:
            for w in WINDOWS:
                out["25" + next(names)] = dict(m=m, exit=g, window=w, key=f"{int(m * 100):02d}{g}",
                                               label=f"m{m:g}-{lab[g]}-{w}")
    return out


def select(S, cfg, cap=DAY_CAP):
    S = bind(S, cfg["key"])
    w0, w1 = WINDOWS[cfg["window"]]
    m = (S.tod >= w0) & (S.tod <= w1) & S.r.notna()
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


def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    o["by_trigger"] = {}
    for k in ("coll", "dip", "ts1", "ts2"):
        x = t[t[k].astype(bool)]
        o["by_trigger"][k] = {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
    return o


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in the config window."""
    rng = np.random.default_rng(seed)
    w0, w1 = WINDOWS[cfg["window"]]
    slots = np.arange(m2(w0), m2(w1) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    W = walk(R, random=True)
    return bind(W, cfg["key"])


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def rand_block(t, cfg):
    Rc = random_control(t, cfg)
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


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days, nb, nu = [], [], 0, 0
        with Pool(2) as p:
            for m, s, d, k, u in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), "both-side bars skipped", k, "universe bars", u, flush=True)
                sigs.append(s); days += d; nb += k; nu += u
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"meta_{half}.json").write_text(json.dumps({"both_side_skipped": nb, "universe_bars": nu,
                                                         "symbols": S.symbol.value_counts().head(40).to_dict()}))
        print("symbols:", S.symbol.value_counts().head(30).to_dict())
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r25H.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = full_stats(t, n)
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"),
                  o["by_side"]["long"].get("avg_r"), o["by_side"]["short"].get("avg_r"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k]["total_r"], -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-25 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "sha256_symbols": sha(SYMF), "configs_counted_this_candidate": 13,
              "configs_note": "12 grid + 1 bias diagnostic (PLAN sec. 4)", "check_informed": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = stats(select(S, fs["cfg"], cap=0), n)
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
        o["uncapped"] = stats(select(S, cfg, cap=0), n)
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
        t[["symbol", "date", "tod", "side", "r", "r_u", "kd", "hold"]].to_csv(HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = full_stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                "first_half_avg_r", "second_half_avg_r", "avg_r_u025")}
            res[name]["long_avg_r"] = o["by_side"]["long"].get("avg_r")
            res[name]["short_avg_r"] = o["by_side"]["short"].get("avg_r")
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
