"""eu1103/open Part 2: four busy live setups with the window start at 09:40 / 09:45 vs the live 09:50 (PLAN.md).
Frame = lab rows 09:50-15:00 (lib.load_month, locked block refused) + the rebuilt early rows 09:35-09:45
(build_early.py, same pipeline). Masks = the live modules' own mask(); first signal per symbol-day inside the window;
costs gates.lab_trades (production + time-of-day entry multiplier: 2.1x for 09:40 / 09:45 closes).
TRAIN sessions 2025-03-01..03-21 are dropped for every variant (early-row indicators restart after the locked gap).
    python rescore.py <scratch>
Educational only - not financial advice."""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(ROOT / "research/bdi/cwt/live")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1])
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
for mo in TRAIN + VALID:
    assert mo not in lib.LOCKED_MONTHS
SETUPS = {  # name: (module, end, min_adv)
    "CWT14-failbrk-pdl-p05-long": ("research/bdi/cwt/live/CWT14-failbrk-pdl-p05-long.py", 1500, 95e6),
    "CWT14-failbrk-pdh-p10-short": ("research/bdi/cwt/live/CWT14-failbrk-pdh-p10-short.py", 1200, 95e6),
    "RW7-gapdn-bounce-early-short-FD": ("research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py", 1500, 95e6),
    "L3-gap-slope-fromopen-FD": ("research/bdi/fullday/L3-gap-slope-fromopen-FD.py", 1500, 0.0),
}
STARTS = (940, 945, 950)


def load(path):
    spec = importlib.util.spec_from_file_location("m_" + Path(path).stem.replace("-", "_"), ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MODS = {k: load(v[0]) for k, v in SETUPS.items()}
EARLY = pd.concat([pd.read_parquet(p) for p in sorted((S / "early").glob("early_*.parquet"))], ignore_index=True)
EARLY["date"] = pd.to_datetime(EARLY["date"]).dt.date
EARLY["symbol"] = EARLY["symbol"].astype(str)


def frame(mo, split):
    f = lib.load_month(mo)
    if split == "VALID":
        f = f[f["date"].astype(str) <= "2026-09-15"]
    f["symbol"] = f["symbol"].astype(str)
    a = pd.Timestamp(mo + "-01").date()
    b = (pd.Timestamp(mo + "-01") + pd.offsets.MonthBegin(1)).date()
    e = EARLY[(EARLY.date >= a) & (EARLY.date < b)]
    par = e[e.tod == 950].merge(f[f.tod == 950], on=["symbol", "date"], suffixes=("", "_lab"))
    cols = ["close", "heat", "rsi", "sma20_slope_pct", "dist_pdl_atr", "r_long_t1s1", "r_short_t05s1"]
    mism = {c: float(np.nanmax(np.abs(par[c].to_numpy(float) - par[c + "_lab"].to_numpy(float)))) for c in cols}
    e = e[e.tod < 950]
    x = pd.concat([f.drop(columns=["ts"]), e], ignore_index=True)
    x = x[(np.nan_to_num(x["adv20"].to_numpy(float)) >= 20e6) & (x["atr_d"].to_numpy(float) > 0)]
    x = x[~((x["date"].astype(str) >= "2025-03-01") & (x["date"].astype(str) <= "2025-03-21"))]
    x = x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    return x, len(par), mism


def main():
    out, par_log = [], []
    for split, ms in (("TRAIN", TRAIN), ("VALID", VALID)):
        for mo in ms:
            x, npar, mism = frame(mo, split)
            par_log.append(dict(month=mo, parity_rows=npar, **{f"maxdiff_{k}": v for k, v in mism.items()}))
            tod = x["tod"].to_numpy(float)
            adv = np.nan_to_num(x["adv20"].to_numpy(float))
            for name, (path, end, madv) in SETUPS.items():
                mod = MODS[name]
                with np.errstate(invalid="ignore", divide="ignore"):
                    m0 = np.asarray(mod.mask(x), bool)
                if name.startswith("L3-"):
                    m0 &= x["gap"].to_numpy(float) <= -2.6573517322540283
                m0 &= adv >= madv
                for st in STARTS:
                    m = m0 & (tod >= st) & (tod <= end)
                    t = G.lab_trades(x, m, mod.SIDE, mod.GEOM)
                    t["setup"], t["start"], t["split"] = name, st, split
                    out.append(t)
            print(mo, split, flush=True)
    t = pd.concat(out, ignore_index=True)
    t.to_parquet(S / "rescore_trades.parquet", index=False)
    pl = pd.DataFrame(par_log)
    pl.to_csv(ROOT / "research/bdi/eu1103/open/parity.csv", index=False, float_format="%.6f")
    report(t)


def report(t):
    d = lib.daily()
    spy = d[d.symbol == "SPY"].set_index("date")
    oc = (spy.close / spy.open - 1) * 100
    t["dtype"] = t["date"].map(lambda z: "up" if oc.get(z, 0) > 0.25 else ("down" if oc.get(z, 0) < -0.25 else "quiet"))
    nses = {}
    for split, ms in (("TRAIN", TRAIN), ("VALID", VALID)):
        s = d[d.symbol == "SPY"].date.astype(str)
        mm = s.str.slice(0, 7).isin(ms) & ~((s >= "2025-03-01") & (s <= "2025-03-21"))
        if split == "VALID":
            mm &= s <= "2026-09-15"
        nses[split] = int(mm.sum())
    rows = []
    for (name, split), g in t.groupby(["setup", "split"]):
        base = g[g.start == 950].set_index(["date", "symbol"])
        for st in STARTS:
            u = g[g.start == st]
            dm = u.groupby("date").r.mean()
            day = u.groupby("date").r.sum()
            j = u.set_index(["date", "symbol"])
            early = j[j.tod < 950]
            moved = early[early.index.isin(base.index)]
            new = early[~early.index.isin(base.index)]
            rr = dict(setup=name, split=split, start=st, sessions=nses[split], n=len(u), per_session=len(u) / nses[split],
                      avgR=u.r.mean(), totR_per_session=u.r.sum() / nses[split],
                      day_t=dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm))),
                      wo_best=u[u.date != day.idxmax()].r.mean(), n_early=len(early), early_avgR=early.r.mean(),
                      n_moved=len(moved), moved_avgR=moved.r.mean(),
                      moved_base_avgR=base.loc[moved.index].r.mean() if len(moved) else np.nan,
                      n_new=len(new), new_avgR=new.r.mean())
            for dt in ("up", "down", "quiet"):
                rr[f"{dt}_R"] = u[u.dtype == dt].r.mean()
                rr[f"early_{dt}_R"] = early[early.dtype == dt].r.mean() if len(early) else np.nan
            rows.append(rr)
    r = pd.DataFrame(rows)
    r.to_csv(ROOT / "research/bdi/eu1103/open/rescore_results.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250)
    print("Educational only - not financial advice.")
    print(r[["setup", "split", "start", "n", "per_session", "avgR", "totR_per_session", "day_t", "n_early", "early_avgR",
             "n_moved", "moved_avgR", "moved_base_avgR", "n_new", "new_avgR", "up_R", "down_R", "quiet_R"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "report":
        report(pd.read_parquet(S / "rescore_trades.parquet"))
    else:
        main()
