"""ULT-35 EARN-FAIL backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-35", 5, 6). Adapted from round4/ULT-28/bt.py
(same event table, 1-minute walk, costs, stats; only the side rule, window, gap sign and reporting splits differ).

Events: round4/data/earnings_yf.parquet (never the _lockedblock sibling) -> reaction-day table by the LIVE module's
reaction_days(). Signals: lab frames + context (spy_fo); features and side rule from the LIVE module (modules/ULT-35.py).
A superset is built once per half: window 10:15-13:30, |gap| >= 3% AGAINST the trade side, the FAIL cross for D 0 or
D 0.5 (flags x0 / x05), both sides (shorts easy-to-borrow by data/universe.csv, today's flag), on (a) reaction-day rows
(evt = 1) and (b) the non-earnings twin (evt = 0: covered names with d outside every RD-5..RD+1 window).
Chassis and costs exactly as ULT-28 (LR8; x1.5 entry cost when the decision bar is before 10:30 and x1.5 exit cost when
the exit is before 10:30 on reaction days; short borrow 5 bp / 8 bp under $20 on reaction days, 1.2 / 3 bp twin).
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
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
sys.path.insert(0, str(HERE.parents[1] / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

_s = importlib.util.spec_from_file_location("ult23bt", HERE.parents[1] / "round3" / "ULT-23" / "bt.py")
B23 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B23)
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
EARN = HERE.parent / "data" / "earnings_yf.parquet"
FIT_MONTHS = B23.FIT_MONTHS
MOD = HERE.parents[1] / "modules" / "ULT-35.py"
N_CUM = 996
DAY_CAP = 30
MS = (0.25,)
EXITS = {"T": (1.0, 1.0), "X": (None, 2.0)}     # (target, stop) in u
WINDOW = (1015, 1330)
SURCH_T = 1030


def load_mod(name="ult35"):
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


def events():
    """Reaction-day table on the NYSE calendar 2024-08-01..2026-12-31; events with RD in the locked block dropped."""
    mod = load_mod()
    e = pd.read_parquet(EARN)
    d = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e = e[(d >= "2024-08-01") & (d <= "2026-12-31")]
    no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())      # the file holds no locked rows
    sess = mod.sessions("2024-08-01", "2026-12-31")
    ev = mod.reaction_days(e, sess)
    ev = ev[~ev.rd.between(B23.LOCK[0], B23.LOCK[1])].reset_index(drop=True)
    no_locked(ev.rd.unique())
    allrd = e.copy()      # twin exclusion uses EVERY scheduled report (any session type) as a raw RD position
    allrd["report_date"] = d[allrd.index]
    arr = np.array(sess)
    allrd["rd_i"] = np.where(allrd.session.to_numpy() == "amc",
                             np.searchsorted(arr, allrd.report_date.to_numpy(), "right"),
                             np.searchsorted(arr, allrd.report_date.to_numpy(), "left"))
    return ev, allrd[["symbol", "rd_i"]], sess


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    ev, allrd, sess = events()
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
    emap = dict(zip(evm.symbol.astype(str) + "|" + evm.rd, evm.surprise_pct))
    f["e_rd"] = k.isin(emap.keys()).to_numpy()
    f["e_surp"] = k.map(emap).astype(float).to_numpy()
    covered = set(allrd.symbol.astype(str))
    di = f["date"].map(sidx).to_numpy()
    bad = set()
    for sym, ri in zip(allrd.symbol.astype(str), allrd.rd_i.to_numpy()):
        for dd in range(ri - 5, ri + 2):
            bad.add((sym, dd))
    twin = np.array([(s in covered) and ((s, d) not in bad) for s, d in zip(f["symbol"].to_numpy(), di)])
    r = mod.features(f.drop(columns=["e_rd"]).assign(e_rd=True))
    tod = r["tod"]
    win = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    etb = f["symbol"].isin(etb_set()).to_numpy()
    evt = f["e_rd"].to_numpy()
    out = []
    for sgn in (1, -1):
        x0, x05 = mod.signal(r, sgn, 3.0, 0.0), mod.signal(r, sgn, 3.0, 0.5)
        mk = (x0 | x05) & win & (evt | twin)
        if sgn < 0:
            mk &= etb
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "e_surp"]].copy()
        s["side"] = sgn
        s["evt"] = evt[mk].astype(np.int8)
        s["x0"], s["x05"] = x0[mk], x05[mk]
        s["cost_r"] = r["cost_r"][mk]
        out.append(s)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    # point-in-time event counts in the lab universe (no outcomes)
    rdk = f.loc[f.tod == 1015, ["symbol", "date", "e_rd", "adv20", "gap"]]
    nev = rdk.groupby("date").e_rd.sum().to_dict()
    nev_int = rdk[rdk.e_rd & (rdk.adv20 >= 30e6) & (rdk.gap.abs() >= 3) & (rdk.gap.abs() < 20)].groupby("date").size().to_dict()
    return month, pd.concat(out, ignore_index=True), days, nev, nev_int


# ---------------------------------------------------------------- stage 2: 1-minute walk (ULT-26's)
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
        res.append((r.Index,) + tuple(row if row else [np.nan] * (2 + 3 * len(EXITS) * len(MS))))
    return res


def exit_keys():
    return [f"{int(m * 100):02d}{g}" for m in MS for g in EXITS]


def borrow(side, e, evt):
    bp = np.where(evt > 0, np.where(e < 20, 8e-4, 5e-4), np.where(e < 20, 3e-4, 1.2e-4))
    return np.where(side < 0, bp * e, 0.0)


def cost_R(side, tod, e, px, kd, unit, evt, xt, fixes=True):
    """fixes=False: the bias diagnostic (no borrow, no reaction-day surcharge)."""
    sur_e = np.where((evt > 0) & (np.asarray(tod) < SURCH_T), 1.5, 1.0) if fixes else 1.0
    sur_x = np.where((evt > 0) & (np.nan_to_num(np.asarray(xt, float), nan=9999) < SURCH_T), 1.5, 1.0) if fixes else 1.0
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod) * sur_e
    xc = (np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)) * sur_x
    bf = borrow(side, e, evt) if fixes else 0.0
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
    tod, side, atr, evt = T.tod.to_numpy(), T.side.to_numpy(), T.atr_d.to_numpy(), T.evt.to_numpy()
    for k in exit_keys():
        m, g = int(k[:2]) / 100, k[2]
        unit = EXITS[g][1] * m * atr
        px, kd, xt = T["px" + k].to_numpy(), T["kd" + k].to_numpy(), T["xt" + k].to_numpy()
        T["r" + k] = cost_R(side, tod, T.e.to_numpy(), px, kd, unit, evt, xt)
        T["ru" + k] = cost_R(side, tod, T.e.to_numpy(), px, kd, 0.25 * atr, evt, xt)
        T["rsc" + k] = cost_R(side, tod, T.dclose.to_numpy(), px, kd, unit, evt, xt, fixes=False)
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
    """Grid (8): 35a-h = G {3, 6} x D {0, 0.5} x exit {t1s1 cap45, TX-45} (G outer, D, exit inner)."""
    out, names = {}, iter("abcdefgh")
    for g in (3.0, 6.0):
        for d in (0.0, 0.5):
            for ex in ("T", "X"):
                out["35" + next(names)] = dict(g=g, d=d, exit=ex, key="25" + ex,
                                               label=f"G{g:g}-D{d:g}-" + ("t1s1cap45" if ex == "T" else "TX45"))
    return out


def select(S, cfg, cap=DAY_CAP, evt=1, side=None):
    S = bind(S, cfg["key"])
    m = ((S.evt == evt) & (S.tod >= WINDOW[0]) & (S.tod <= WINDOW[1]) & (-S.side * S.gap >= cfg["g"]) & S.r.notna())
    m &= (S.x05 if cfg["d"] >= 0.5 else S.x0).astype(bool)
    if side is not None:
        m &= S.side == side
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


SEASON = None


def full_stats(t, n, work=None, half=None):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    ag = -t.side * t.gap
    o["by_gap"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
                   for nm, x in (("gap_3_6", t[ag < 6]), ("gap_6_10", t[(ag >= 6) & (ag < 10)]), ("gap_10_plus", t[ag >= 10]))}
    o["by_surprise"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
                        for nm, x in (("surprise_with_trade_side", t[np.sign(t.e_surp) == t.side]),
                                      ("surprise_with_gap", t[np.sign(t.e_surp) == -t.side]),
                                      ("missing_or_zero", t[t.e_surp.isna() | (t.e_surp == 0)]))}
    o["by_entry_time"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}
                          for nm, x in (("1015_1055", t[t.tod < 1100]), ("1100_1155", t[(t.tod >= 1100) & (t.tod < 1200)]),
                                        ("1200_1330", t[t.tod >= 1200]))}
    if SEASON is not None:
        ss = t.date.map(SEASON).fillna(False).astype(bool)
        o["season"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                            "total_r": round(float(x.r.sum()), 2)} for nm, x in (("season", t[ss]), ("off", t[~ss]))}
    return o


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in 10:15-13:30."""
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(WINDOW[0]), m2(WINDOW[1]) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side", "evt"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    W = walk(R, random=True)
    return bind(W, cfg["key"])


def load_half(work, half):
    global SEASON
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    meta = json.loads((Path(work) / f"meta_{half}.json").read_text())
    SEASON = {d: meta["n_events"].get(d, 0) >= 5 for d in days}
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


def short_stats(o):
    keys = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
            "total_r_per_session", "worst_day_per_trade_session", "t_day_clustered", "avg_r_ex_0403_0409", "A_avg_r",
            "B_avg_r", "first_half_avg_r", "second_half_avg_r", "avg_r_u025")
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
        sigs, days, nev, nint = [], [], {}, {}
        with Pool(2) as p:
            for m, s, d, ne, ni in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), "evt rows", int(s.evt.sum()), "RD names/session", round(sum(ne.values()) / max(1, len(d)), 2),
                      "intake RD names/session", round(sum(ni.values()) / max(1, len(d)), 2), flush=True)
                sigs.append(s); days += d; nev.update({k: int(v) for k, v in ne.items()}); nint.update({k: int(v) for k, v in ni.items()})
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"meta_{half}.json").write_text(json.dumps({"n_days": len(days), "n_events": nev, "n_events_intake_g3": nint,
                                                         "rd_names_per_session": sum(nev.values()) / len(days),
                                                         "intake_g3_rd_names_per_session": sum(nint.values()) / len(days)}))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r25T.isna().sum()), "no path", round(time.time() - t0), "s")
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
                  o["by_side"]["long"].get("avg_r"), o["by_side"]["short"].get("avg_r"), o.get("t_day_clustered"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k].get("total_r_wo_best_day", -1e9), -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k].get("total_r", -1e9), -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-35 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__),
              "sha256_module_at_freeze": sha(MOD), "sha256_earnings": sha(EARN), "configs_counted_this_candidate": 9,
              "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)", "check_informed": "PARTLY",
              "needs_owner_blackout_exception": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_nosurcharge_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, fs["cfg"], cap=0), n))
        o["twin_fit"] = short_stats(full_stats(select(S, fs["cfg"], evt=0), n))
        o["long_only_fit"] = short_stats(full_stats(select(S, fs["cfg"], side=1), n))
        o["short_only_fit"] = short_stats(full_stats(select(S, fs["cfg"], side=-1), n))
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "CHECK is scored once"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg)
        o = full_stats(t, n)
        o["bias_diag_sigclose_noborrow_nosurcharge_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, cfg, cap=0), n))
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
        t[["symbol", "date", "tod", "side", "gap", "e_surp", "r", "r_u", "kd", "hold", "evt"]].to_csv(HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            res[name] = short_stats(full_stats(select(S, cfg), n))
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        fs = json.loads((HERE / "fitsel.json").read_text())
        res["twin_check_" + fs["pick"]] = short_stats(full_stats(select(S, fs["cfg"], evt=0), n))
        res["long_only_check_" + fs["pick"]] = short_stats(full_stats(select(S, fs["cfg"], side=1), n))
        res["short_only_check_" + fs["pick"]] = short_stats(full_stats(select(S, fs["cfg"], side=-1), n))
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
