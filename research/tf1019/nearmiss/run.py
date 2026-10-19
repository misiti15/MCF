"""tf1019/nearmiss runner: the 12 Testing-2 swarm1017 near-miss setups x decision bars 1/3/5/10/15 min x {as-is, TE}.
    python research/tf1019/nearmiss/te_build.py --out $S       # TE indicator columns (scratch)
    python research/tf1019/nearmiss/run.py --scratch $S        # trades -> $S/trades/*.parquet, results.csv here
    python research/tf1019/nearmiss/run.py --scratch $S --parity
See PLAN.md (pre-declared). Educational only - not financial advice."""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mcf.research.arena.indicators as IND  # noqa: E402
from mcf.research import gates  # noqa: E402
from mcf.research import timeframes as tf  # noqa: E402
from te_build import COLS as TE_COLS, SH, W  # noqa: E402

HERE = Path(__file__).resolve().parent
SW = "research/swarm1017/"
#  name: (module, window, min_adv, context, prior lineage N, arena?, key lookbacks {label: (bars, kind)})
SETUPS = {
    "NM-RWN3-ns3-spyup-early-short": (SW + "rework-ns/modules/RWN3-ns3-spyup-early-short.py", (950, 1030), 95e6, True,
                                      165764, False, {"SMA50": (50, "w")}),
    "NM-RWN4-ns2-spyup05-notfri-short": (SW + "rework-ns/modules/RWN4-ns2-spyup05-notfri-t05s1-short.py", (950, 1130),
                                         95e6, True, 165764, False, {"SMA50": (50, "w"), "RSI14": (14, "w")}),
    "NM-RWN5-ns3-mon-weakrs-short": (SW + "rework-ns/modules/RWN5-ns3-mon-weakrs-short.py", (950, 1130), 95e6, True,
                                     165764, False, {"SMA50": (50, "w")}),
    "NM-RWR1-exh150-gapdn-spyup-pm-short": (SW + "rework-rw/modules/RWR1-exh150-gapdn-spyup-pm-short-t05s1.py",
                                            (1300, 1500), 150e6, True, 967000, False,
                                            {"RSI5": (5, "w"), "SMA20": (20, "w"), "div20": (20, "w")}),
    "NM-RWR3-ns3-qqqup-early-short": (SW + "rework-rw/modules/RWR3-ns3-adv150-qqqup-early-short-refire.py",
                                      (950, 1030), 150e6, True, 114000, False, {"SMA50": (50, "w")}),
    "NM-RWR4-ns2-up3-qqqup-slopedn-short": (SW + "rework-rw/modules/RWR4-ns2-up3-qqqup-slopedn-am-short-t05s1.py",
                                            (950, 1100), 95e6, True, 114000, False,
                                            {"SMA50": (50, "w"), "RSI14": (14, "w"), "SMA20slope5": (5, "s")}),
    "NM-ETF-late-dip-di-long": (SW + "arena-index-etf/modules/AR-ETF-late-dip-di-long.py", (1400, 1500), 95e6, False,
                                266882, True, {"ret3": (3, "s"), "DI7": (7, "w")}),
    "NM-AR-AM-gapdown-capitulation-long": (SW + "final/modules/AR-AM-gapdown-capitulation.py", (950, 1100), 95e6,
                                           False, 43100, True, {"ret12": (12, "s"), "VR20": (20, "w")}),
    "NM-AMS-N1-quiet-morning-short": (SW + "final/modules/AMS-N1-downtrend-quiet-bounce.py", (1000, 1100), 95e6,
                                      False, 43100, True, {"SMA20slope5": (5, "s"), "BP19": (19, "w")}),
    "NM-PM-gapdn-above-pdh-rvol-short": (SW + "final/modules/NM-PM-S-gapdn-above-pdh-rvol.py", (1400, 1500), 95e6,
                                         False, 155600, True, {"VR20": (20, "w")}),
    "NM1-cwt09-g10-vwaploss-short": (SW + "final/modules/NM1-cwt09-g10-vwaploss-fodn-slopeup-short.py", (1030, 1500),
                                     1e6, False, 99000, False, {"SMA20slope5": (5, "s")}),
    "NM-HL-T75-pm-long": (SW + "final/modules/NM-HL-T75-pm-t05s1-long.py", (1300, 1500), 125e6, False, 34000, False,
                          {"RSI14": (14, "w"), "range20": (20, "w")}),
}
N_TASK = 108
FIRST_MIN = {1: 590, 3: 591, 5: 590, 10: 590, 15: 600}      # first bar close >= 09:50 (minutes after midnight)
S: Path = Path(".")


# ------------------------------------------------------------------ arena grid: one slot = one m-minute bar
@contextlib.contextmanager
def arena_grid(m: int):
    first = FIRST_MIN[m]
    nslots = (900 - first) // m + 1
    old = IND.STEP, IND.N_SLOTS, IND.tod_slot

    def tod_slot(tod):
        t = np.asarray(tod, float)
        mins = np.floor(t / 100) * 60 + np.mod(t, 100)
        s = (mins - first) / m
        ok = np.isfinite(s) & (s >= 0) & (s < nslots) & (np.mod(s, 1) == 0)
        return np.where(ok, s, -1).astype(int)

    IND.STEP, IND.N_SLOTS, IND.tod_slot = m, nslots, tod_slot
    try:
        yield
    finally:
        IND.STEP, IND.N_SLOTS, IND.tod_slot = old


def _ret_k(df, k):
    p = IND.Panel(df)
    C = p.mat(df["close"].to_numpy(float))
    with np.errstate(invalid="ignore", divide="ignore"):
        return p.rows((C / IND._shift(C, k) - 1) * 100).astype(float)


def _di_diff(df, n):
    """arena di_diff7 with length n (same code, 7 -> n)."""
    p = IND.Panel(df)
    C, H, L = (p.mat(df[c].to_numpy(float)) for c in ("close", "high", "low"))
    with np.errstate(invalid="ignore", divide="ignore"):
        up, dn = H - IND._shift(H, 1), IND._shift(L, 1) - L
        pdm = np.where((up > dn) & (up > 0), up, 0.0)
        ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
        pdm[np.isnan(up) | np.isnan(dn)] = np.nan
        ndm[np.isnan(up) | np.isnan(dn)] = np.nan
        tr = np.fmax(H - L, np.fmax(np.abs(H - IND._shift(C, 1)), np.abs(L - IND._shift(C, 1))))
        tr[np.isnan(IND._shift(C, 1))] = np.nan
        atr = IND._roll(tr, n, np.mean)
        pdi, ndi = 100 * IND._roll(pdm, n, np.mean) / atr, 100 * IND._roll(ndm, n, np.mean) / atr
        return p.rows(pdi - ndi).astype(float)


def arena_te_mask(mod, df, m):
    """The arena module's CONDS/WINDOW on TE columns: bar-count columns already swapped in df; ret3/ret12/di_diff7
    recomputed at the scaled length; the rest via arena compute (clock/session based or swapped columns)."""
    names = [c[0] for c in mod.CONDS]
    special = {"ret3": lambda: _ret_k(df, SH(3, m)), "ret12": lambda: _ret_k(df, SH(12, m)),
               "di_diff7": lambda: _di_diff(df, W(7, m))}
    plain = [n for n in names if n not in special]
    x = IND.compute(df, names=plain, context=False) if plain else pd.DataFrame(index=df.index)
    tod = df["tod"].to_numpy(dtype=float)
    lo, hi = mod.WINDOW
    msk = (tod >= lo) & ((tod < hi) | ((hi >= 1500) & (tod <= 1500)))
    with np.errstate(invalid="ignore"):
        for nm, op, v in mod.CONDS:
            a = special[nm]() if nm in special else x[nm].to_numpy(dtype=float)
            msk &= {"<=": a <= v, "<": a < v, ">=": a >= v, ">": a > v}[op]
    if hasattr(mod, "SYMBOLS") and "symbol" in df.columns:
        msk &= df["symbol"].astype(str).isin(mod.SYMBOLS).to_numpy()
    return np.asarray(msk, bool)


def te_swap(df, m):
    mos = sorted(set(pd.Series(df["date"]).astype(str).str[:7]))
    te = pd.concat([pd.read_parquet(S / f"te_{m}min" / f"{mo}.parquet") for mo in mos], ignore_index=True)
    te["date"] = te["date"].astype(str)
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": pd.Series(df["date"]).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy().astype("int16")})
    j = k.merge(te, on=["symbol", "date", "tod"], how="left")
    assert len(j) == len(df)
    d2 = df.copy()
    for c in TE_COLS:
        d2[c] = j[c].to_numpy()
    return d2


def wrap(mod, m, variant, arena):
    def mask(df):
        with arena_grid(m):
            if variant == "asis":
                return mod.mask(df)
            d2 = te_swap(df, m)
            return arena_te_mask(mod, d2, m) if arena else mod.mask(d2)
    return types.SimpleNamespace(SIDE=mod.SIDE, GEOM=getattr(mod, "GEOM", "t1s1"), mask=mask)


def job(args):
    name, m, variant = args
    path, win, adv, ctx, _, arena, _ = SETUPS[name]
    mod = wrap(tf.load_module(path), m, variant, arena)
    t = tf.run_module_tf(mod, m, window=win, split="open", symbols="core", min_adv=adv, context=ctx)
    t.to_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet", index=False)
    return name, m, variant, len(t)


def parity():
    """(1) patched arena grid at m=5 == original compute; (2) arena_te_mask at m=5 == module mask; on 2026-09 core."""
    df = tf.load_tf(5, "2026-09", symbols=tf.universe("core"))
    for name, (path, *_r) in SETUPS.items():
        if not SETUPS[name][5]:
            continue
        mod = tf.load_module(path)
        a = np.asarray(mod.mask(df), bool)
        with arena_grid(5):
            b = np.asarray(mod.mask(df), bool)
            c = arena_te_mask(mod, df, 5)
        assert (a == b).all() and (a == c).all(), (name, int((a != b).sum()), int((a != c).sum()))
        print(name, "parity ok", int(a.sum()))
    # (3) on 1-min, the patched grid gives every row a slot (no silent NaN)
    d1 = tf.load_tf(1, "2026-09", symbols=["SPY"])
    with arena_grid(1):
        assert (IND.tod_slot(d1["tod"].to_numpy()) >= 0).all()
    for m in (3, 10, 15):
        dm = tf.load_tf(m, "2026-09", symbols=["SPY"])
        with arena_grid(m):
            assert (IND.tod_slot(dm["tod"].to_numpy()) >= 0).all(), m
    print("grid ok")


def lookbacks(name, m, variant):
    out = []
    for lab, (n, kind) in SETUPS[name][6].items():
        b = n if (variant == "asis" or m == 5) else (W(n, m) if kind == "w" else SH(n, m))
        out.append(f"{lab}={b}b/{b * m}min")
    return " ".join(out)


def summarize_all():
    reg = tf.regimes()
    rows = []
    for name in SETUPS:
        n_lin = SETUPS[name][4] + N_TASK
        for m in tf.MINUTES:
            for variant in ("asis", "te"):
                if variant == "te" and m == 5:
                    continue
                t = pd.read_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet")
                s = tf.summarize(t, n_lin, reg)
                o, bs = s.get("overall", {}), s.get("by_split", {})
                rnd, rg = s.get("random_same_minute", {}), s.get("regime", {})
                tr, va, fw = bs.get("train", {}), bs.get("valid", {}), bs.get("forward", {})
                fails = list(s.get("fails", [])) if o.get("n") else ["n=0"]
                if (tr.get("exp_r") or -1) <= 0:
                    fails.append("train exp<=0")
                if (va.get("exp_r") or -1) <= 0:
                    fails.append("valid exp<=0")
                if (rnd.get("excess_exp_r") or -1) <= 0:
                    fails.append("excess vs random<=0")
                ndays = t["date"].nunique() if len(t) else 0
                rows.append({"setup": name, "minutes": m, "variant": variant, "lookbacks": lookbacks(name, m, variant),
                             "n": o.get("n", 0), "sessions": ndays, "per_day": round(o.get("n", 0) / max(1, ndays), 2),
                             "exp_r": o.get("exp_r"), "t": o.get("t"), "win": o.get("win_rate"),
                             "n_train": tr.get("n", 0), "exp_train": tr.get("exp_r"), "t_train": tr.get("t"),
                             "n_valid": va.get("n", 0), "exp_valid": va.get("exp_r"), "t_valid": va.get("t"),
                             "n_fwd": fw.get("n", 0), "exp_fwd": fw.get("exp_r"),
                             "ctrl": rnd.get("ctrl_exp_r"), "excess": rnd.get("excess_exp_r"), "excess_t": rnd.get("excess_t"),
                             "up_n": rg.get("up", {}).get("n"), "up_r": rg.get("up", {}).get("exp_r"),
                             "down_n": rg.get("down", {}).get("n"), "down_r": rg.get("down", {}).get("exp_r"),
                             "regime_pass": s.get("regime_pass"), "wf_share": s.get("walk_forward", {}).get("share_positive"),
                             "n_lineage": n_lin, "t_required": s["t_required"], "t_family108": gates.t_required(N_TASK),
                             "pass_all": not fails, "fails": "; ".join(fails)})
    r = pd.DataFrame(rows)
    r.to_csv(HERE / "results.csv", index=False)
    return r


def _init(s):
    global S
    S = Path(s)


def main():
    global S
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--parity", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    S = Path(a.scratch)
    if a.parity:
        parity()
        return
    if not a.summarize_only:
        (S / "trades").mkdir(exist_ok=True)
        jobs = [(n, m, v) for m in (1, 3, 5, 10, 15) for n in SETUPS for v in ("asis", "te") if not (v == "te" and m == 5)]
        assert len(jobs) == N_TASK
        if a.only:
            jobs = [j for j in jobs if j[2] == a.only]
        jobs = [j for j in jobs if not (S / "trades" / f"{j[0]}_{j[1]}_{j[2]}.parquet").exists()]
        with Pool(a.workers, initializer=_init, initargs=(str(S),), maxtasksperchild=4) as pool:
            for res in pool.imap_unordered(job, jobs):
                print(*res, flush=True)
        return
    r = summarize_all()
    print(r[["setup", "minutes", "variant", "n", "exp_train", "exp_valid", "t", "excess", "regime_pass", "wf_share",
             "pass_all"]].to_string())
    print(json.dumps({"configs": len(r), "pass": int(r.pass_all.sum())}))


if __name__ == "__main__":
    main()
