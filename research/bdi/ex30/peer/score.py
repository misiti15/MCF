"""ex30/peer: peer / sympathy / dispersion setups (5 primaries + 10 neighbours = 15 configs) on the two-year open history.
PLAN.md was written and committed (441e43fa6) before this ran. Harness = ex30/xsec + night1102/simple (gates.lab_trades:
production costs + time-of-day entry; day-matched random control). Features are computed here independently of the
modules (numpy segment cumsums vs the modules' pandas groupby) and compared bar by bar on 2026-09 (parity.csv).
The rule-19 locked block (2024-11..2025-02) is never loaded (asserted).

    python score.py <scratch>   -> <scratch>/trades.parquet, <scratch>/ctrl.parquet, parity.csv here
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
VALID_END = "2026-09-15"
for m in TRAIN + VALID:
    assert m not in lib.LOCKED_MONTHS and m in lib.months(), m
ADV = 95e6
COLS = ["symbol", "date", "tod", "close", "atr_d", "adv20", "fromOpen", "vwapDistPct"] + \
       [f"{a}_{s}_t{g}" for a in ("r", "win") for s in ("long", "short") for g in ("1s1", "05s1")]


def col(df, k):
    return df[k].to_numpy(float)


def seg_lag(x, seg, n=1):
    p = np.r_[np.full(n, np.nan), x[:-n]]
    ps = np.r_[np.full(n, -1), seg[:-n]]
    p[ps != seg] = np.nan
    return p


def seg_cumsum(x, seg):
    c = np.cumsum(x)
    start = np.r_[True, seg[1:] != seg[:-1]]
    base = np.where(start, c - x, np.nan)
    base = pd.Series(base).ffill().to_numpy()
    return c - base


def feats(df, new):
    seg = np.cumsum(new)
    c, atr, fo, tod = col(df, "close"), col(df, "atr_d"), col(df, "fromOpen"), col(df, "tod")
    F = dict(c=c, tod=tod, vwd=col(df, "vwapDistPct"), spy=col(df, "spy_fo"), qqq=col(df, "qqq_fo"),
             bo=col(df, "breadth_open"))
    pc, pt = seg_lag(c, seg), seg_lag(tod, seg)
    with np.errstate(invalid="ignore", divide="ignore"):
        rs = (c / pc - 1) * 100
        ok = (tod >= 955) & (pt >= 950)
        for ix in ("spy", "qqq"):
            fi = F[ix]
            ri = ((1 + fi / 100) / (1 + seg_lag(fi, seg) / 100) - 1) * 100
            v = ok & np.isfinite(rs) & np.isfinite(ri)
            x, y = np.where(v, ri, 0.0), np.where(v, rs, 0.0)
            n = seg_cumsum(v.astype(float), seg)
            sx, sy = seg_cumsum(x, seg), seg_cumsum(y, seg)
            sxx, syy, sxy = seg_cumsum(x * x, seg), seg_cumsum(y * y, seg), seg_cumsum(x * y, seg)
            cov = sxy / n - (sx / n) * (sy / n)
            vx, vy = sxx / n - (sx / n) ** 2, syy / n - (sy / n) ** 2
            F["n_" + ix], F["corr_" + ix], F["beta_" + ix] = n, cov / np.sqrt(vx * vy), cov / vx
        atrp = atr / c * 100
        F["move"] = (c - c / (1 + fo / 100)) / atr
        F["res_spy"] = (fo - F["beta_spy"] * F["spy"]) / atrp
        F["res_qqq"] = (fo - F["beta_qqq"] * F["qqq"]) / atrp
        F["prev_res_qqq"] = seg_lag(F["res_qqq"], seg)
        F["prev_c"] = pc
        F["s2"] = (c / seg_lag(c, seg, 2) - 1) * 100
        F["q2"] = ((1 + F["qqq"] / 100) / (1 + seg_lag(F["qqq"], seg, 2) / 100) - 1) * 100
        cm = pd.Series(c).groupby(seg).cummin().to_numpy()   # frames start at 09:50 = the modules' tod >= 950 rule
        F["low_before"] = seg_lag(cm, seg)
    return F


def pr1(F, res=-0.50, cr=0.50):
    return (F["n_spy"] >= 8) & (F["spy"] >= 0.30) & (F["corr_spy"] >= cr) & (F["beta_spy"] >= 0.50) & \
        (F["res_spy"] <= res) & (F["c"] > F["prev_c"])


def pr2(F, mv=-1.0, cr=0.15):
    return (F["n_spy"] >= 8) & (np.abs(F["spy"]) <= 0.25) & (np.abs(F["corr_spy"]) <= cr) & (F["move"] <= mv) & \
        (F["vwd"] < 0) & (F["c"] <= F["low_before"])


def pr3(F, bo=0.45, sp=0.30):
    return (F["spy"] >= sp) & (F["bo"] <= bo) & (F["qqq"] >= F["spy"]) & (F["move"] <= -0.50) & (F["vwd"] < 0)


def pr4(F, res=1.25):
    return (F["n_qqq"] >= 12) & (F["corr_qqq"] >= 0.40) & (F["res_qqq"] >= res) & \
        (F["res_qqq"] < F["prev_res_qqq"]) & (F["c"] < F["prev_c"])


def pr5(F, q=0.20):
    return (F["n_qqq"] >= 6) & (F["corr_qqq"] >= 0.50) & (F["beta_qqq"] >= 0.80) & (F["q2"] >= q) & \
        (F["s2"] <= 0.25 * F["beta_qqq"] * F["q2"])


SETUPS = {
    "PR1-sympathy-laggard-long": ("long", "t1s1", (1030, 1330), pr1, [dict(res=-0.35), dict(cr=0.35)]),
    "PR2-decoupled-quiet-breakdown-short": ("short", "t1s1", (1030, 1430), pr2, [dict(mv=-0.75), dict(cr=0.30)]),
    "PR3-narrow-rally-laggard-short": ("short", "t1s1", (1030, 1430), pr3, [dict(bo=0.40), dict(sp=0.20)]),
    "PR4-qqq-residual-stretch-revert-short": ("short", "t05s1", (1100, 1500), pr4, [dict(res=1.0), dict(res=1.5)]),
    "PR5-qqq-impulse-leadlag-long": ("long", "t05s1", (1020, 1500), pr5, [dict(q=0.15), dict(q=0.30)]),
}


def newflag(df):
    s, d = df["symbol"].to_numpy(), df["date"].to_numpy()
    return np.r_[True, (s[1:] != s[:-1]) | (d[1:] != d[:-1])]


def configs(df, new):
    F = feats(df, new)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    with np.errstate(invalid="ignore"):
        for name, (side, geom, w, fn, nbs) in SETUPS.items():
            base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
            yield name, "primary", side, geom, w, fn(F) & base
            for nb in nbs:
                yield name, "nb " + ",".join(f"{k}={v}" for k, v in nb.items()), side, geom, w, fn(F, **nb) & base


def run_frame(df, split):
    if split == "VALID":
        df = df[df["date"].astype(str) <= VALID_END].reset_index(drop=True)
    new = newflag(df)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    trades, keys = [], set()
    for name, form, side, geom, w, m in configs(df, new):
        t = G.lab_trades(df, m, side, geom)
        t["setup"], t["form"], t["side"] = name, form, side
        trades.append(t)
        keys.add((side, geom, w))
    ctrl = []
    for side, geom, w in keys:
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
        rr = df[f"r_{side}_{geom}"].to_numpy(float)
        ok = base & np.isfinite(rr) & (col(df, "atr_d") > 0)
        r = G.prod_r(rr[ok], col(df, f"win_{side}_{geom}")[ok], col(df, "close")[ok], col(df, "atr_d")[ok], geom, tod=tod[ok])
        c = pd.DataFrame({"date": pd.to_datetime(df["date"].to_numpy()[ok]).date, "r": r}).groupby("date").r.mean()
        ctrl.append(c.rename("ctrl").reset_index().assign(side=side, geom=geom, win=str(w)))
    tr = pd.concat(trades, ignore_index=True)
    tr["split"] = split
    return tr, pd.concat(ctrl, ignore_index=True).assign(split=split)


def parity(df):
    """Harness masks == module masks on one month (bar by bar, inside window and ADV)."""
    mine = {n: m for n, f, *_, m in configs(df, newflag(df)) if f == "primary"}
    out = {}
    for name, (side, geom, w, *_r) in SETUPS.items():
        spec = importlib.util.spec_from_file_location("m_" + name.replace("-", "_"), HERE / "modules" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.SIDE == side and mod.GEOM == geom and tuple(mod.WINDOW) == w, name
        ref = np.asarray(mod.mask(df), bool) & (np.nan_to_num(col(df, "adv20")) >= ADV)
        a = mine[name]
        out[name] = dict(harness=int(a.sum()), module=int(ref.sum()), both=int((a & ref).sum()))
    return out


def main():
    t0 = time.time()
    (S / "cache").mkdir(parents=True, exist_ok=True)
    allt, allc = [], []
    only = sys.argv[2] if len(sys.argv) > 2 else None
    for split, months in (("TRAIN", TRAIN), ("VALID", VALID)):
        for mo in months:
            if only and mo != only:
                continue
            ct = S / "cache" / f"{mo}.parquet"
            if ct.exists():
                allt.append(pd.read_parquet(ct)); allc.append(pd.read_parquet(S / "cache" / f"{mo}_ctrl.parquet"))
                continue
            df = lib.load_month(mo, columns=COLS, context=True)
            if mo == "2026-09":
                par = parity(df)
                print("parity 2026-09:", par, flush=True)
                pd.DataFrame(par).T.to_csv(HERE / "parity.csv")
            tr, c = run_frame(df, split)
            tr.to_parquet(ct, index=False); c.to_parquet(S / "cache" / f"{mo}_ctrl.parquet", index=False)
            allt.append(tr); allc.append(c)
            print(mo, split, len(tr), tr.groupby(["setup", "form"]).size().to_dict() if only else "", f"{time.time() - t0:.0f}s", flush=True)
            del df
    if only:
        return
    pd.concat(allt, ignore_index=True).to_parquet(S / "trades.parquet", index=False)
    pd.concat(allc, ignore_index=True).to_parquet(S / "ctrl.parquet", index=False)
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
