"""BEG-RULES prep: one trade table (BEG base book + Primary live run 1, LR8) with the S7 / S8 inputs.
  python prep.py OUT_DIR      -> OUT_DIR/trades.parquet, OUT_DIR/sessions.json
Locked block 2024-11-01..2025-02-28 is never read (filters + asserts). Educational only - not financial advice."""
import json, sqlite3, subprocess, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402
from mcf import costs  # noqa: E402

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
HIST, FRESH, TEAM = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min"), Path("/home/user/MCF/data/team/1Min")
FILES = {"BEG-01": ["beg01w/booked_t1_base_fit.parquet", "beg01w/booked_t1_base_check.parquet", "beg01w/booked_t2_base_t2.parquet"],
         "BEG-02": ["beg02w/bk_base_t1.parquet", "beg02w/bk_base_t2.parquet"], "BEG-03": ["beg03w/bk_base_all.parquet"],
         "BEG-04": ["beg04w/bk_base_all.parquet"],
         **{f"BEG-{i:02d}": [f"beg{i:02d}w/bk_base_{h}.parquet" for h in ("fit", "check", "t2")] for i in (5, 6, 7, 8)},
         "BEG-09": ["beg09w/bk_base_t1.parquet", "beg09w/bk_base_t2.parquet"], "BEG-10": ["beg10w/bk_base_all.parquet"]}
COLS = ["book", "setup", "symbol", "date", "side", "em", "xm", "entry", "stop", "r", "r_gross", "stopout", "seg"]
LAST_T1 = "2026-11-04"


def seg_of(d):
    d = pd.Series(d).astype(str)
    h = pd.Series(B.half(d), index=d.index)
    return np.where(d <= B.T2_HI, "t2", np.where(d <= LAST_T1, h, "none"))


def beg():
    out = []
    for s, fs in FILES.items():
        t = pd.concat([pd.read_parquet(S / f) for f in fs], ignore_index=True)
        t = t.drop_duplicates(["symbol", "date", "em", "side", "entry"])
        t["setup"], t["book"] = s, "BEG"
        t["stopout"] = t.r_gross <= -0.9
        t["seg"] = seg_of(t.date)
        t = t[t.seg != "none"]
        out.append(t[COLS])
    T = pd.concat(out, ignore_index=True)
    B.no_locked(T.date.unique())
    return T


def primary():
    db = S / "rr1120/j_primary.db"
    if not db.exists():
        db.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", "origin/mcf-data:journal.db"], capture_output=True, check=True).stdout)
    t = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(db))
    t["r"] = costs.cost_r_lr8(t, costs._report_cfg())
    t["r_gross"] = t.r_multiple
    et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert(B.TZ)
    xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert(B.TZ)
    t["em"], t["xm"] = et.dt.hour * 60 + et.dt.minute, xt.dt.hour * 60 + xt.dt.minute
    t["setup"], t["book"], t["seg"] = t.strategy, "PRIMARY", "live"
    t["stopout"] = t.exit_reason == "stop"
    return t[COLS]


def bars(sym, dates):
    """1-minute RTH bars for sym on the given dates (locked block filtered)."""
    parts = []
    lo = min(dates)
    if lo <= B.T2_HI and (FRESH / f"{sym}.parquet").exists():
        parts.append(pd.read_parquet(FRESH / f"{sym}.parquet"))
    if max(dates) > B.T2_HI and (HIST / f"{sym}.parquet").exists():
        parts.append(pd.read_parquet(HIST / f"{sym}.parquet"))
    if not parts:
        return None
    b = pd.concat(parts)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    d = b.index.date.astype(str)
    keep = np.isin(d, list(dates)) & ~((d >= B.LOCK[0]) & (d <= B.LOCK[1]))
    return b[keep]


def team_bars(dates):
    out = []
    for d in sorted(dates):
        p = TEAM / f"{d}.parquet"
        if p.exists():
            x = pd.read_parquet(p, columns=["ts", "symbol", "close", "volume"])
            out.append(x)
    return pd.concat(out) if out else None


def dv5_table(b):
    """b: bars with DatetimeIndex (ET). -> dict (date, minute) -> mean close*vol of the 5 prior minutes."""
    m = b.index.hour * 60 + b.index.minute
    d = b.index.date.astype(str)
    df = pd.DataFrame({"d": d, "m": m, "dv": (b.close * b.volume).to_numpy()})
    df = df[(df.m >= 570) & (df.m < 960)]
    res = {}
    for day, g in df.groupby("d"):
        a = np.zeros(390)
        a[g.m.to_numpy() - 570] = g.dv.to_numpy()
        cs = np.r_[0, np.cumsum(a)]
        k = np.arange(390)
        prev = (cs[k] - cs[np.maximum(k - 5, 0)]) / 5.0   # minutes k-5..k-1
        prev[k < 5] = np.nan
        res[day] = prev
    return res


def sym_job(args):
    sym, rows = args   # rows: list of (idx, date, em)
    dates = sorted({r[1] for r in rows})
    b = bars(sym, set(dates))
    out = []
    tab = dv5_table(b) if b is not None and len(b) else {}
    for i, d, em in rows:
        a = tab.get(d)
        out.append((i, float(a[int(em) - 570]) if a is not None and 570 <= em < 960 else np.nan))
    return out


def flag_day(g):
    """g: one day of SPY bars (ET index, high/low/close/volume) -> array over minutes 570..959 of sign(close - VWAP),
    carried forward over empty minutes."""
    m = (g.index.hour * 60 + g.index.minute).to_numpy()
    ok = (m >= 570) & (m < 960)
    g, m = g[ok], m[ok]
    tp = (g.high + g.low + g.close) / 3
    vw = (tp * g.volume).cumsum() / g.volume.cumsum().replace(0, np.nan)
    sg = pd.Series(np.sign((g.close - vw).to_numpy()), index=m - 570)
    sg = sg[~sg.index.duplicated()]
    return sg.reindex(range(390)).ffill().fillna(0).to_numpy()


def spy_flags(dates):
    b = bars("SPY", set(dates))
    return {} if b is None else {day: flag_day(g) for day, g in b.groupby(b.index.date.astype(str))}


def team_extra(T, need_dates):
    """Primary days without cache bars: team 1-minute files (10-23..11-10)."""
    tb = team_bars(need_dates)
    if tb is None:
        return {}, {}
    tb["ts"] = pd.to_datetime(tb.ts).dt.tz_convert(B.TZ)
    dv, spy = {}, {}
    for sym, g in tb.groupby("symbol"):
        g = g.set_index("ts").sort_index()
        if sym == "SPY":
            pass
        for day, a in dv5_table(g).items():
            dv[(sym, day)] = a
    return dv, spy


if __name__ == "__main__":
    OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
    T = pd.concat([beg(), primary()], ignore_index=True)
    T["date"] = T.date.astype(str)
    B.no_locked(T.date.unique())
    print(T.groupby(["book", "seg"]).size())
    jobs = [(s, list(zip(g.index, g.date, g.em))) for s, g in T.groupby("symbol")]
    dv = {}
    with Pool(3) as p:
        for i, res in enumerate(p.imap_unordered(sym_job, jobs, chunksize=8)):
            dv.update(dict(res))
            if i % 200 == 0:
                print("dv", i, len(jobs), flush=True)
    T["dv5"] = pd.Series(dv)
    # Primary days past the cache: team files
    miss = T[(T.book == "PRIMARY") & T.dv5.isna() & (T.date > LAST_T1)]
    tdv, _ = team_extra(T, set(miss.date))
    for i, r in miss.iterrows():
        a = tdv.get((r.symbol, r.date))
        if a is not None and 570 <= r.em < 960:
            T.at[i, "dv5"] = a[int(r.em) - 570]
    # SPY tape flag at bar em-1 (cache SPY; team SPY bars for 11-05..11-10)
    fl = spy_flags(set(T.date))
    for day in sorted({d for d in set(T.date) if d > LAST_T1}):
        p = TEAM / f"{day}.parquet"
        if p.exists():
            hl = pd.read_parquet(p, filters=[("symbol", "==", "SPY")])
            hl.index = pd.to_datetime(hl.ts).dt.tz_convert(B.TZ)
            fl[day] = flag_day(hl.sort_index())
    T["spy_tape"] = [fl[d][int(em) - 571] if d in fl and 571 <= em < 960 else 0.0 for d, em in zip(T.date, T.em)]
    T.to_parquet(OUT / "trades.parquet")
    print(T.groupby(["book", "seg"]).agg(n=("r", "size"), dv_cov=("dv5", lambda x: x.notna().mean()),
                                         spy_cov=("spy_tape", lambda x: (x != 0).mean())))
    # sessions per segment (SPY days)
    spyd = sorted(fl)
    sess = {"fit": [d for d in spyd if seg_of([d])[0] == "fit"], "check": [d for d in spyd if seg_of([d])[0] == "check"],
            "t2": [d for d in spyd if seg_of([d])[0] == "t2"],
            "live": sorted(T[T.book == "PRIMARY"].date.unique().tolist())}
    (OUT / "sessions.json").write_text(json.dumps(sess))
    print({k: len(v) for k, v in sess.items()})
