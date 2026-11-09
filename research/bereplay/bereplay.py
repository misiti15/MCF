"""BEREPLAY (guild Builder, plan PLAN.md frozen 2026-11-09 before any score). One 1-minute engine walks every 2-year lab
trade (bt_lab1104 lists + bt_hold.py GEN hold/holdtr lists) under: BASE (live geometry), BE50, BE75 (stop to entry
from the minute after the trade first reaches +0.5 / +0.75 x stop distance), and for GEN geom hold: HOLDTR (1R trail
on minute closes once +1R; holdtr setups are walked with their trail in BASE). Costs exactly as bt_all.
    python bereplay.py <hold_lists_dir> [procs] > bereplay_out.txt
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted). Educational only - not financial advice."""
import os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
HERE = Path(__file__).resolve().parent
TZ = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
N_FAMILY = 30; T_FULL = G.t_required(N_FAMILY); T90 = round(max(1.35, 0.9 * T_FULL), 2)
SL, BP, SX = 0.01, 1e-4, 0.02
GK = {**G.GEOMK, "hold": (np.inf, 1.0), "holdtr": (np.inf, 1.0)}
VARS = ["BASE", "BE50", "BE75", "HOLDTR"]


def load_lists(hold_dir):
    a = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
    b = pd.concat(pd.read_parquet(p) for p in sorted(Path(hold_dir).glob("sig_*.parquet"))) if hold_dir else a.iloc[:0]
    t = pd.concat([a, b], ignore_index=True)
    t["date"] = pd.to_datetime(t["date"]).dt.date; t["tod"] = t.tod.astype(int); t["symbol"] = t.symbol.astype(str)
    assert not ((t.date >= LK0) & (t.date <= LK1)).any()
    t = t.drop_duplicates(["setup", "symbol", "date", "tod"]).reset_index(drop=True)
    # entry = lab close at the signal bar, R = 0.25 x atr_d, gap for the cost tier (as bt_all)
    parts = []
    for m in sorted(pd.to_datetime(t.date).dt.strftime("%Y-%m").unique()):
        f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"])
        f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
        parts.append(t[pd.to_datetime(t.date).dt.strftime("%Y-%m") == m].merge(f, on=["symbol", "date", "tod"], how="left"))
    t = pd.concat(parts, ignore_index=True)
    print(f"trades {len(t)}, setups {t.setup.nunique()}, frame-join missing {t.close.isna().mean():.2%}", flush=True)
    return t.dropna(subset=["close", "atr_d"]).reset_index(drop=True)


def first(mask):
    return int(np.argmax(mask)) if mask.any() else 10 ** 9


def walk(o, h, l, c, e, s, D, U, mode, k=None):
    """-> (exit price, kind 0 flat / 1 stop / 2 target). mode: fixed | be | trail. Stop-first inside a minute."""
    n = len(c)
    if n == 0: return e, 0
    fav = (h - e) if s > 0 else (e - l)
    if mode == "trail":
        cb = np.maximum.accumulate(c) if s > 0 else np.minimum.accumulate(c)
        prev = np.r_[e, cb[:-1]]
        on = s * (prev - e) >= D
        lev = np.where(on, prev - s * D, e - s * D)
        lev = np.maximum(lev, e - D) if s > 0 else np.minimum(lev, e + D)
    elif mode == "be":
        tb = first(fav >= k * D)
        lev = np.full(n, e - s * D)
        if tb < n - 1: lev[tb + 1:] = e
    else:
        lev = np.full(n, e - s * D)
    hit = (l <= lev) if s > 0 else (h >= lev)
    i_s = first(hit)
    i_t = first(fav >= U) if np.isfinite(U) else 10 ** 9
    if i_s <= i_t and i_s < n:
        px = o[i_s] if s * (o[i_s] - lev[i_s]) <= 0 else lev[i_s]
        return px, 1
    if i_t < n: return e + s * U, 2
    return c[-1], 0


def sym_job(args):
    sym, tr = args
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)    # through the 15:54 minute
    df = df[keep]; mm = mm[keep]; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span: continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))            # first minute after the signal bar close
        o, h, l, c = O[j:b], H[j:b], L[j:b], C[j:b]
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = GK[r.geom]; D = dn * R; U = up * R
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (SL + e * BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        res = {}
        base_mode = "trail" if r.geom == "holdtr" else "fixed"
        for v, mode, k in (("BASE", base_mode, None), ("BE50", "be", .5), ("BE75", "be", .75), ("HOLDTR", "trail", None)):
            if v == "HOLDTR" and r.geom != "hold": res[v] = np.nan; continue
            if v.startswith("BE") and base_mode == "trail": res[v] = np.nan; continue   # BE on a trail = n/a (stated)
            px, kd = walk(o, h, l, c, e, r.side, D, U, mode, k)
            xcost = (0.0 if kd == 2 else SL + px * BP) + (SX if kd == 1 else 0.0)
            res[v] = (r.side * (px - e) / R - tier * (ecost + xcost) / R) / dn
        mfe = float(np.max((h - e) if r.side > 0 else (e - l)) / D) if len(c) else 0.0
        out.append((r.setup, r.side, r.geom, sym, r.date, r.tod, res["BASE"], res["BE50"], res["BE75"], res["HOLDTR"], mfe, float(r.r)))
    return out


def main():
    hold_dir = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t = load_lists(hold_dir)
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    rows = []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, jobs, chunksize=4)):
            if res: rows += res
            if k % 200 == 0: print(f"symbols {k}/{len(jobs)}", flush=True)
    X = pd.DataFrame(rows, columns=["setup", "side", "geom", "symbol", "date", "tod", "BASE", "BE50", "BE75", "HOLDTR", "mfe_stop", "r_5min"])
    X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
    X.to_parquet(HERE / "bereplay_trades.parquet", index=False)
    D_ = lib.daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
    dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
    print(f"\nreplayed {len(X)} trades, {X.setup.nunique()} setups, {X.family.nunique()} families, {X.date.nunique()} days; "
          f"engine check: BASE 1-min avg {X.BASE.mean():+.4f} vs 5-min list avg {X.r_5min.mean():+.4f} (corr {X.BASE.corr(X.r_5min):.3f})")
    print(f"family N {N_FAMILY}: full bar {T_FULL}, BAR90 {T90}")
    rows = []
    for v in ("BE50", "BE75", "HOLDTR"):
        x = X.dropna(subset=[v]).copy(); x["r"] = x[v] - x.BASE
        if not len(x): continue
        s_ = G.summary(x); tr_, va_ = G.summary(x[x.date <= SPLIT]), G.summary(x[x.date > SPLIT])
        ty = x.groupby(x.date.map(dtype)).r.sum()
        k = .5 if v == "BE50" else .75 if v == "BE75" else 1.0
        give = x[(x.mfe_stop >= k) & (x.BASE <= 0)].BASE.sum()
        fam = x.groupby(["family", "side"]).agg(n=("r", "size"), delta=("r", "mean"), base=("BASE", "mean"))
        better, worse = int((fam.delta > 0).sum()), int((fam.delta < 0).sum())
        worst = fam.delta.min()
        row = dict(config=v, n=s_["n"], days=s_["days"], base_avg=round(x.BASE.mean(), 4), var_avg=round(x[v].mean(), 4),
                   delta=s_["exp_r"], delta_t=s_.get("t"), delta_total=round(x.r.sum(), 1), wo_best=s_.get("ex_best_day"),
                   train=tr_.get("exp_r"), train_t=tr_.get("t"), valid=va_.get("exp_r"), valid_t=va_.get("t"),
                   up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1), quiet=round(ty.get("quiet", 0), 1),
                   giveback_ub=round(-give, 1), fam_better=better, fam_worse=worse, worst_fam_delta=round(worst, 4))
        row["pass"] = bool((row["delta_t"] or 0) >= T90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0 and row["up"] > 0
                           and row["down"] > 0 and (row["wo_best"] or -1) > 0 and better > worse and worst >= -0.03)
        rows.append(row)
        fam = fam.assign(delta=fam.delta.round(4), base=fam.base.round(4)).sort_values("delta")
        print(f"\n{v} per family x side (delta = variant - BASE, avg R per trade):\n{fam.to_string()}")
        fam.reset_index().to_csv(HERE / f"bereplay_family_{v}.csv", index=False)
    R = pd.DataFrame(rows); pd.set_option("display.width", 400); pd.set_option("display.max_columns", 40)
    print("\n" + R.to_string(index=False))
    print("\ngiveback_ub = R of BASE trades that reached the trigger and closed <= 0 (upper bound of what BE could save);"
          "\nBE on holdtr setups not applied (n/a); HOLDTR rows = GEN geom hold only. Lists are uncapped chains.")
    print(f"configs 3 (family N {N_FAMILY}), pass {int(R['pass'].sum()) if len(R) else 0}")
    R.to_csv(HERE / "bereplay_results.csv", index=False)
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
