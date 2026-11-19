"""ULT-32 FLOW-DIP backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-32", 4, 5, 6).
Reuses round4/ULT-28/bt.py (1-minute walk + LR8 cost_R; long only -> no borrow, no reaction-day surcharge because the
blackout keeps M / D off reaction days and E trades ETFs) and round3/ULT-23/bt.py (stats, sub-halves, SPY day types).

Signals: lab frames + context (spy_fo); features and leg triggers from the LIVE module (modules/ULT-32.py).
One superset per half holds every row any config can use, with flag columns:
  * ST7-FD dissection rows (all lab names, ADV20 >= $95M, 09:50-15:00, cost_r <= 0.15, >= 3 of its 4 layers);
  * NM-ETF / WB4 dissection rows (EQB ETFs, ADV20 >= $95M, 10:30-15:00, cost_r <= 0.10, >= 3 of WB4's 4 layers);
  * book legs E / M (ADV20 >= $500M superset, RMAX 35) / D;  earnings blackout flag (report date or reaction day
    within +-4 sessions; dates only, scheduled ahead).
Exits per row (walked once): T = t1s1 cap45, H = t05s1 cap45 (R per u), X = TX-45 with a 2u catastrophic stop (R per 2u).
Chassis: entry = OPEN of the 1-minute bar starting at the decision-bar close; brackets around the decision close; stop
first, then target; stop gap-through at the worse of open/stop; target at the limit (no exit cost); +2c on stops;
flat 15:50. One lot per symbol (across legs); refire >= 30 min after the exit; max 2 per symbol-session; day cap 30.
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK fit|dissect|fitrandom|check|plateau
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parents[1] / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"

_s = importlib.util.spec_from_file_location("ult28bt", HERE.parent / "ULT-28" / "bt.py")
B28 = importlib.util.module_from_spec(_s)
sys.modules["ult28bt"] = B28
_s.loader.exec_module(B28)
B28.EXITS = {"T": (1.0, 1.0), "H": (0.5, 1.0), "X": (None, 2.0)}      # (target, stop) in u; walked in the workers
B28.MS = (0.25,)
B23 = B28.B23
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha
DATA, EARN = B28.DATA, B28.EARN

MOD = HERE.parents[1] / "modules" / "ULT-32.py"
SYMF = HERE.parents[1] / "modules" / "ULT-32_symbols.json"
N_CUM = 998          # 996 pre-registered + 2 dissection reference bases (amendment, see RESULTS.md)
DAY_CAP = 30
XK = {"T": "25T", "H": "25H", "X": "25X"}


def load_mod(name="ult32"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def blackout_set():
    """{(symbol, session)} within +-4 sessions of a report date or its reaction day (dates are scheduled ahead)."""
    m28 = B28.load_mod()
    e = pd.read_parquet(EARN)
    d = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e = e[(d >= "2024-08-01") & (d <= "2026-12-31")].copy()
    no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())
    sess = np.array(m28.sessions("2024-08-01", "2026-12-31"))
    rep = d[e.index].to_numpy()
    rep_i = np.searchsorted(sess, rep, "left")
    rd_i = np.where(e.session.to_numpy() == "amc", np.searchsorted(sess, rep, "right"), rep_i)
    out = set()
    for sym, a, b in zip(e.symbol.astype(str), rep_i, rd_i):
        for k in range(min(a, b) - 4, max(a, b) + 5):
            if 0 <= k < len(sess):
                out.add((sym, sess[k]))
    return out


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    U = json.loads(SYMF.read_text())
    eqb, lev = set(U["EQB"]), set(U["LEV_INV"])
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower())]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f, adv_md=500e6)
    tod, adv = r["tod"], f["adv20"].fillna(0).to_numpy()
    sym = f["symbol"].to_numpy()
    key = (f["symbol"] + "|" + f["date"]).to_numpy()
    new = np.r_[True, key[1:] != key[:-1]]
    rp = np.r_[np.nan, r["rsi"][:-1]]
    rp[new] = np.nan                                   # ST7: previous row of the same symbol-session
    with np.errstate(invalid="ignore"):
        L = np.c_[(r["rsi"] < 50) & (rp >= 50), r["rsi"] <= 30, r["fromOpen"] < -1.0, r["bp"] > 0]
        N = np.c_[r["ret3"] <= mod.E_RET3, r["di7"] >= mod.E_DI, r["ret12"] >= mod.E_RET12, r["atrp_ind"] >= mod.E_ATR]
        gate = r["intake"] & r["univ_ok"] & (adv >= 95e6)
        st7 = gate & (r["cost_r"] <= 0.15) & (tod >= 950) & (tod <= 1500) & (L.sum(1) >= 3)
        is_eqb = np.isin(sym, list(eqb))
        nm = gate & is_eqb & (r["cost_r"] <= 0.10) & (tod >= 1030) & (tod <= 1500) & (N.sum(1) >= 3)
        legE = mod.leg_mask(r, "E")
        legM = mod.leg_mask(r, "M", rmax=35.0)
        legD = mod.leg_mask(r, "D", d_on=True)
    mk = st7 | nm | legE | legM | legD
    s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
    for j in range(4):
        s[f"L{j + 1}"] = L[mk, j]
        s[f"N{j + 1}"] = N[mk, j]
    s["st7"], s["nm"], s["legE"], s["legM"], s["legD"] = st7[mk], nm[mk], legE[mk], legM[mk], legD[mk]
    s["is_w"] = np.isin(s.symbol.to_numpy(), list(mod.W))
    s["is_eqb"] = is_eqb[mk]
    s["is_lev"] = np.isin(s.symbol.to_numpy(), list(lev))
    for k in ("rsi", "rsi_prev", "cost_r", "spy_fo"):
        s[k] = r[k][mk]
    s["rsi_prev_row"] = rp[mk]
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, s, days


# ---------------------------------------------------------------- stage 3: selection
def bind_rows(S, ex):
    """ex: array of exit letters per row (T/H/X) -> generic columns stats() reads."""
    S = S.copy()
    ex = np.asarray(ex)
    for col in ("r", "ru", "rsc", "kd", "xmin"):
        v = np.full(len(S), np.nan)
        for g, k in XK.items():
            q = ex == g
            if q.any():
                v[q] = S[col + k].to_numpy(float)[q]
        S[{"ru": "r_u", "rsc": "r_sigclose"}.get(col, col)] = v
    S["exit"] = ex
    S["hold"] = S["xmin"] - m2(S.tod)
    return S


def chain(S, cap=DAY_CAP):
    s = S[S.r.notna()].sort_values(["symbol", "date", "tod"], kind="mergesort")
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


def configs():
    """Grid (8): 32a..h = A {$1B, $500M} x RMAX {30, 35} x leg D {off, on} (A outer, RMAX, D inner)."""
    out, names = {}, iter("abcdefgh")
    for a in (1e9, 500e6):
        for rm in (30.0, 35.0):
            for d in (False, True):
                out["32" + next(names)] = dict(adv=a, rmax=rm, d_on=d,
                                               label=f"A{a / 1e6:.0f}M-RMAX{rm:g}-D{'on' if d else 'off'}")
    return out


def book(S, cfg, cap=DAY_CAP, blackout=True):
    """Leg E (t05s1) | leg M (t1s1) | leg D (t05s1); M wins a bar it shares with D; one lot per symbol across legs."""
    adv = S.adv20.fillna(0).to_numpy()
    bo = S.blackout.to_numpy(bool) if blackout else np.zeros(len(S), bool)
    e = S.legE.to_numpy(bool)
    mm = S.legM.to_numpy(bool) & (S.rsi.to_numpy() <= cfg["rmax"]) & (adv >= cfg["adv"]) & ~bo
    dd = (S.legD.to_numpy(bool) & (adv >= cfg["adv"]) & ~bo) if cfg["d_on"] else np.zeros(len(S), bool)
    use = e | mm | dd
    leg = np.where(e, "E", np.where(mm, "M", "D"))
    ex = np.where(leg == "M", "T", "H")
    T = bind_rows(S[use], ex[use])
    T["leg"] = leg[use]
    return chain(T, cap)


def dissect_configs():
    """23 FIT-only ablations + 2 reference bases (ST7-FD and WB4 through the round-4 chassis)."""
    c = {"ST7-base": dict(fam="st7", drop=None, win=(950, 1500), adv=(95e6, np.inf), exit="T")}
    for j, nm in enumerate(("cross50", "rsi30", "fo1", "bp"), 1):
        c[f"ST7-drop-{nm}"] = dict(fam="st7", drop=j, win=(950, 1500), adv=(95e6, np.inf), exit="T")
    for lo, hi in ((950, 1055), (1100, 1325), (1330, 1500)):
        c[f"ST7-hour-{lo}-{hi}"] = dict(fam="st7", drop=None, win=(lo, hi), adv=(95e6, np.inf), exit="T")
    for lo, hi in ((95e6, 300e6), (300e6, 1e9), (1e9, np.inf)):
        c[f"ST7-adv-{lo / 1e6:.0f}-{hi / 1e6:.0f}"] = dict(fam="st7", drop=None, win=(950, 1500), adv=(lo, hi), exit="T")
    for x in ("H", "X"):
        c[f"ST7-exit-{x}"] = dict(fam="st7", drop=None, win=(950, 1500), adv=(95e6, np.inf), exit=x)
    c["WB4-base"] = dict(fam="nm", drop=None, win=(1400, 1500), univ="W", exit="H")
    for j, nm in enumerate(("dip", "di", "fallhour", "atr"), 1):
        c[f"WB4-drop-{nm}"] = dict(fam="nm", drop=j, win=(1400, 1500), univ="W", exit="H")
    for lo, hi in ((1030, 1225), (1230, 1355), (1400, 1500)):
        c[f"WB4-hour-{lo}-{hi}"] = dict(fam="nm", drop=None, win=(lo, hi), univ="W", exit="H")
    c["WB4-univ-otherEQB"] = dict(fam="nm", drop=None, win=(1400, 1500), univ="Q-W", exit="H")
    c["WB4-univ-unlev"] = dict(fam="nm", drop=None, win=(1400, 1500), univ="W-unlev", exit="H")
    for x in ("T", "X"):
        c[f"WB4-exit-{x}"] = dict(fam="nm", drop=None, win=(1400, 1500), univ="W", exit=x)
    return c


def dissect_sel(S, cfg, cap=DAY_CAP):
    p = "L" if cfg["fam"] == "st7" else "N"
    lay = np.c_[[S[f"{p}{j}"].to_numpy(bool) for j in range(1, 5)]].T
    keep = [j for j in range(4) if cfg["drop"] != j + 1]
    m = S[cfg["fam"]].to_numpy(bool) & lay[:, keep].all(1)
    tod = S.tod.to_numpy()
    m &= (tod >= cfg["win"][0]) & (tod <= cfg["win"][1])
    if cfg["fam"] == "st7":
        adv = S.adv20.fillna(0).to_numpy()
        m &= (adv >= cfg["adv"][0]) & (adv < cfg["adv"][1])
    else:
        w, lv = S.is_w.to_numpy(bool), S.is_lev.to_numpy(bool)
        m &= {"W": w, "Q-W": ~w, "W-unlev": w & ~lv, "W-lev": w & lv}[cfg["univ"]]
    T = bind_rows(S[m], np.full(int(m.sum()), cfg["exit"]))
    return chain(T, cap)


# ---------------------------------------------------------------- stage 4: statistics
def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    if "leg" in t:
        o["by_leg"] = {lg: {k: v for k, v in stats(t[t.leg == lg], n).items()
                            if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                     "t_day_clustered", "avg_r_ex_0403_0409", "first_half_avg_r", "second_half_avg_r")}
                       for lg in ("E", "M", "D") if (t.leg == lg).any()}
    return o


KEYS = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
        "total_r_wo_best_day", "total_r_per_session", "worst_day", "worst_day_per_trade_session", "t_day_clustered",
        "avg_r_ex_0403_0409", "A_avg_r", "B_avg_r", "first_half_avg_r", "second_half_avg_r", "median_hold_min",
        "exit_mix", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down")


def short(o):
    x = {k: o.get(k) for k in KEYS}
    if "by_leg" in o:
        x["by_leg"] = {k: {kk: v.get(kk) for kk in ("trades_per_session", "avg_r", "total_r")} for k, v in o["by_leg"].items()}
    return x


def random_control(sel, seed=1119):
    """Same symbol-sessions, legs, exits and count; a random decision bar inside the trade's leg window."""
    rng = np.random.default_rng(seed)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "adv20"]].copy()
    R["side"], R["evt"] = 1, 0
    win = {"E": (1400, 1500), "M": (1015, 1500), "D": (1400, 1500)}
    lg = sel["leg"].to_numpy() if "leg" in sel else np.full(len(sel), "E")
    tods = []
    for g in lg:
        lo, hi = win[g]
        tods.append(int(hhmm(rng.choice(np.arange(m2(lo), m2(hi) + 1, 5)))))
    R["tod"] = tods
    Wk = B28.walk(R, random=True)
    out = bind_rows(Wk, sel["exit"].to_numpy())
    return out


def rand_block(t):
    Rc = random_control(t)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr, rr = t.r.to_numpy()[ok], Rc.r.to_numpy()[ok]
    o = {"random_avg_r": round(float(rr.mean()), 4), "signal_minus_random": round(float(tr.mean() - rr.mean()), 4),
         "random_n": int(ok.sum())}
    lg = t.leg.to_numpy()[ok]
    o["by_leg"] = {g: {"n": int((lg == g).sum()), "signal": round(float(tr[lg == g].mean()), 4),
                       "random": round(float(rr[lg == g].mean()), 4)} for g in ("E", "M", "D") if (lg == g).any()}
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
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days = [], []
        with Pool(2) as p:
            for m, s, d in p.imap_unordered(month_job, B28.half_months(half)):
                print(m, len(s), int(s.st7.sum()), int(s.nm.sum()), int(s.legE.sum()), int(s.legM.sum()),
                      int(s.legD.sum()), flush=True)
                sigs.append(s); days += d
        S = pd.concat(sigs, ignore_index=True)
        no_locked(S.date.unique()); no_locked(days)
        bo = blackout_set()
        S["blackout"] = [(a, b) in bo for a, b in zip(S.symbol, S.date)]
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        S["side"], S["evt"] = 1, 0
        t0 = time.time()
        T = B28.walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r25T.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = book(S, cfg)
            o = full_stats(t, n)
            o["uncapped_trades"] = int(len(book(S, cfg, cap=0)))
            o["no_blackout"] = short(full_stats(book(S, cfg, blackout=False), n))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), o.get("by_leg"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-32 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "fit": res[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "sha256_symbols": sha(SYMF), "sha256_earnings": sha(EARN), "sha256_ult28_bt": sha(HERE.parent / "ULT-28" / "bt.py"),
              "configs_counted_this_candidate": 34,
              "configs_note": "8 grid + 23 dissection ablations + 2 dissection reference bases + 1 bias diagnostic",
              "check_informed": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig))
    elif stage == "dissect":
        half = sys.argv[3] if len(sys.argv) > 3 else "fit"
        S, n = load_half(W, half)
        res = {}
        for name, cfg in dissect_configs().items():
            o = full_stats(dissect_sel(S, cfg), n)
            res[name] = short(o)
            res[name]["cfg"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()}
            print(name, o["trades_per_session"], o.get("avg_r"), o.get("avg_r_wo_best_day"), o.get("total_r"), o.get("A_avg_r"),
                  o.get("B_avg_r"), o.get("t_day_clustered"), flush=True)
        lv = full_stats(dissect_sel(S, dict(fam="nm", drop=None, win=(1400, 1500), univ="W-lev", exit="H")), n)
        res["WB4-univ-lev (complement, description)"] = short(lv)
        (HERE / f"dissect_{half}.json").write_text(json.dumps(res, indent=1, default=float))
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = book(S, fs["cfg"])
        o = rand_block(t)
        o["bias_diag_sigclose_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = book(S, cfg)
        o = full_stats(t, n)
        o["bias_diag_sigclose_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short(full_stats(book(S, cfg, cap=0), n))
        o["no_blackout"] = short(full_stats(book(S, cfg, blackout=False), n))
        o["random"] = rand_block(t)
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
        t[["symbol", "date", "tod", "leg", "exit", "r", "kd", "hold"]].to_csv(HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            res[name] = short(full_stats(book(S, cfg), n))
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name]["trades_per_session"], res[name]["avg_r"], res[name]["t_day_clustered"])
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
