"""COMPASSBF (guild Builder, Lead lead-20261109-2300-2; 0 configs, shared data for RCOMPASS): backfill the LIVE compass
(mcf/report/compass_live.py, imported and called unchanged: compute(bars, day, now)) over the 2-year 1-minute SIP cache
for SPY / QQQ / IWM + the 200 Hunch breadth names, every open-window session, point-in-time (compute() only reads bars
that START before each mark). Locked block 2024-11-01..2025-02-28 dropped at read (asserted).
Outputs: compass_2y.parquet (+ .csv.gz), validation vs the recorded live marks on mcf-data-compass (match rate per field),
and trade lists tagged with the compass at entry and at the 10:30 / 11:00 / 11:30 / 12:00 marks.
    python backfill.py [procs]          Educational only - not financial advice."""
import os, subprocess, sys
from io import StringIO
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.report import compass_live as CL
HERE = Path(__file__).resolve().parent
NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SYMS = ["SPY", "QQQ", "IWM"] + [s for s in CL.universe() if s not in ("SPY", "QQQ", "IWM")]
FIELDS = ["spy_fo", "qqq_fo", "iwm_fo", "spy_vwap", "breadth_open", "breadth_n", "v_fo", "v_vwap", "v_breadth", "v_agree",
          "v_persist", "votes", "w60", "agreement", "c30", "checkpoint", "gate1_state"]
BY = {}


def load(sym):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    df.index = pd.DatetimeIndex(df.index).tz_convert(NY)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()[["open", "high", "low", "close", "volume"]]
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m < 960)]
    return {str(d): g for d, g in df.groupby(df.index.date)}


def init():
    for s in SYMS: BY[s] = load(s)


def day_job(day):
    bars = {s: BY[s][day] for s in SYMS if day in BY[s]}
    if "SPY" not in bars: return []
    rows = CL.compute(bars, day, pd.Timestamp(f"{day} 16:05", tz=NY), names=CL.universe())
    for r in rows: r.pop("computed_at", None); r.pop("backfilled", None)
    return rows


def main():
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    spy = load("SPY"); days = sorted(spy)
    print(f"days {len(days)} ({days[0]}..{days[-1]}, locked absent); breadth names {len(SYMS) - 3}", flush=True)
    with Pool(procs, initializer=init) as p:
        rows = [r for rs in p.imap(day_job, days, chunksize=8) for r in rs]
    C = pd.DataFrame(rows)
    C.to_parquet(HERE / "compass_2y.parquet", index=False); C.to_csv(HERE / "compass_2y.csv.gz", index=False)
    print(f"compass rows {len(C)} ({C.date.nunique()} days x up to {len(CL.MARKS)} marks)", flush=True)

    # ---- validation vs recorded live marks (mcf-data-compass)
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "--depth=1", "origin", CL.BRANCH], check=True)
    files = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", "FETCH_HEAD", "compass/"], capture_output=True,
                           text=True, check=True).stdout.split()
    live = []
    for f in files:
        if f.endswith(".csv"):
            live.append(pd.read_csv(StringIO(subprocess.run(["git", "-C", str(ROOT), "show", f"FETCH_HEAD:{f}"], capture_output=True,
                                                             text=True, check=True).stdout)))
    L = pd.concat(live, ignore_index=True).drop_duplicates(["date", "T"], keep="last")
    J = L.merge(C, on=["date", "T"], suffixes=("_live", "_bf"))
    print(f"\nvalidation: {len(L)} live marks on {L.date.nunique()} days {sorted(L.date.unique())}; matched rows {len(J)}"
          f" (live rows tagged backfilled: {int(L.get('backfilled', pd.Series(dtype=int)).sum())})")
    out = []
    for c in FIELDS:
        a, b = J[c + "_live"], J[c + "_bf"]
        if c in ("spy_fo", "qqq_fo", "iwm_fo", "spy_vwap"):
            ok = (a - b).abs() <= 2e-4                      # 2 bp (rounding to 5 dp + bar revisions)
        elif c == "breadth_open":
            ok = (a - b).abs() <= 0.0101                    # within 2 names of 200
        else:
            ok = a.fillna("").astype(str).str.replace(r"\.0$", "", regex=True) == b.fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
        out.append(dict(field=c, match=round(float(ok.mean()), 4), n=int(len(ok)), first_miss=None if ok.all() else f"{J.date[~ok].iloc[0]} {J['T'][~ok].iloc[0]}: live {a[~ok].iloc[0]} vs bf {b[~ok].iloc[0]}"))
    V = pd.DataFrame(out); print(V.to_string(index=False)); V.to_csv(HERE / "validation.csv", index=False)
    print(f"fields >= 95%: {int((V.match >= .95).sum())} of {len(V)}")

    # ---- tag the 2-year lab trades (entry at or after 12:00 for every family; all coil trades)
    BT = ROOT / "research/history2y/data/bt_lab1104"
    T = pd.concat(pd.read_parquet(p) for p in sorted(BT.glob("sig_*.parquet")))
    T["date"] = pd.to_datetime(T.date).dt.date.astype(str); T["tod"] = T.tod.astype(int)
    T = T[(T.tod >= 1200) | T.setup.str.startswith("CWT12")].reset_index(drop=True)
    em = T.tod // 100 * 60 + T.tod % 100
    C["Tm"] = C["T"].str[:2].astype(int) * 60 + C["T"].str[3:].astype(int)
    keep = ["spy_fo", "votes", "w60", "c30", "checkpoint", "gate1_state", "agreement", "breadth_open"]
    Ci = C.set_index(["date", "Tm"])[keep]
    T["mark_entry"] = [max([t for t in CL.MARKS if t <= m], default=-1) for m in em]   # mark known at the entry bar close
    for tag, mk in [("e", None), ("m1030", 630), ("m1100", 660), ("m1130", 690), ("m1200", 720)]:
        key = list(zip(T.date, T.mark_entry if mk is None else np.where(em >= mk, mk, -1)))
        sub = Ci.reindex(pd.MultiIndex.from_tuples(key, names=["date", "Tm"]))
        for c in keep: T[f"{tag}_{c}"] = sub[c].to_numpy()
    T.to_parquet(HERE / "trades_tagged.parquet", index=False)
    coil = T[T.setup.str.startswith("CWT12")]
    coil.to_csv(HERE / "coil_tagged.csv.gz", index=False)
    print(f"\ntagged trades: {len(T)} (entries >= 12:00, all families) + all CWT12 coil; coil rows {len(coil)}, setups "
          f"{sorted(coil.setup.unique())}; untagged (no mark <= entry) {int((T.mark_entry < 0).sum())}")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
