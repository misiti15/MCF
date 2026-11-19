"""swing1119-L16 NTBE 'near-target break-even' - ONE pre-registered 2-year backtest (BDI 2026-11-19; rule fixed in
research/bdi/swings/hypotheses.jsonl before this run; configs 1, lineage N 31).
Engine: E4 one-off on the Guild BEREPLAY 1-minute engine - load_lists() and walk() are imported unchanged from
research/guild/1109/bereplay/bereplay.py; costs exactly as there (bt_all model). Only the BE trigger differs:
k = 0.8 x target / stop distance (t1s1 0.8, t05s1 0.4, t1s05 1.6, t05s05 0.8); hold / holdtr geometries are n/a.
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted in the engine).
Usage: python ntbe_bt.py [procs] -> ntbe_bt_out.txt next to this file. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/guild/1109/bereplay"))
import bereplay as BR  # noqa: E402  (engine: load_lists, walk, costs, GK)
from bereplay import G, lib  # noqa: E402
HERE = Path(__file__).resolve().parent
N = 31; TF = G.t_required(N); B90 = round(max(1.35, 0.9 * TF), 2); FRAC = 0.8
SPLIT = pd.Timestamp("2025-09-30").date(); LATE = pd.Timestamp("2026-10-06").date()
PRIM = ("ST7-rsi50dn-long-pm-t1s1-FD", "L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long")


def sym_job(args):
    sym, tr = args
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < BR.TL0) | (pds.field(ix) >= BR.TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= BR.TL0) & (df.index < BR.TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    df = df[keep]; mm = mm[keep]; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span or r.geom in ("hold", "holdtr"): continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        o, h, l, c = O[j:b], H[j:b], L[j:b], C[j:b]
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * R; U = up * R
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (BR.SL + e * BR.BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        res = []
        for mode, k in (("fixed", None), ("be", FRAC * U / D)):
            px, kd = BR.walk(o, h, l, c, e, r.side, D, U, mode, k)
            xcost = (0.0 if kd == 2 else BR.SL + px * BR.BP) + (BR.SX if kd == 1 else 0.0)
            res += [(r.side * (px - e) / R - tier * (ecost + xcost) / R) / dn, kd]
        trig = bool(len(c) and np.max((h - e) if r.side > 0 else (e - l)) >= FRAC * U)
        out.append((r.setup, r.side, r.geom, sym, r.date, r.tod, res[0], res[1], res[2], res[3], trig))
    return out


def main():
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    t = BR.load_lists(None)
    t = t[~t.geom.isin(["hold", "holdtr"])]
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    rows = []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, jobs, chunksize=4)):
            if res: rows += res
            if k % 200 == 0: print(f"symbols {k}/{len(jobs)}", flush=True)
    X = pd.DataFrame(rows, columns=["setup", "side", "geom", "symbol", "date", "tod", "BASE", "kb", "NTBE", "kn", "trig"])
    X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
    X["r"] = X.NTBE - X.BASE
    out = []
    def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
    D_ = lib.daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
    dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
    s_ = G.summary(X); tr_, va_ = G.summary(X[X.date <= SPLIT]), G.summary(X[X.date > SPLIT]); la_ = G.summary(X[X.date >= LATE])
    ty = X.groupby(X.date.map(dtype)).r.sum()
    fam = X.groupby(["family", "side"]).agg(n=("r", "size"), trig=("trig", "sum"), delta=("r", "mean"), base=("BASE", "mean"))
    fam = fam[fam.n >= 300]
    better, worse, worst = int((fam.delta > 0).sum()), int((fam.delta < 0).sum()), fam.delta.min()
    tg = X[X.trig]; lost = int(((tg.kb == 2) & (tg.kn != 2)).sum()); saved = int(((tg.kb == 1) & (tg.kn == 1) & (tg.NTBE > tg.BASE)).sum())
    p(f"swing1119-L16 NTBE | E4 on BEREPLAY engine | configs 1, lineage N {N}: full t {TF}, BAR90 {B90}")
    p(f"trades {len(X)} ({X.setup.nunique()} setups, {X.date.nunique()} days); reached trigger {len(tg)} ({len(tg)/len(X):.1%}); "
      f"of those: target hits lost to BE {lost}, full stops turned into BE exits {saved}")
    p(f"BASE avg {X.BASE.mean():+.4f}R  NTBE avg {X.NTBE.mean():+.4f}R  delta {s_['exp_r']:+.4f}R/trade, total {X.r.sum():+.1f}R, "
      f"day-t {s_.get('t')}, w/o best day {s_.get('ex_best_day')}")
    p(f"TRAIN delta {tr_.get('exp_r')} (t {tr_.get('t')}) | VALID {va_.get('exp_r')} (t {va_.get('t')}) | LATE {la_.get('exp_r')} (t {la_.get('t')}, n {la_.get('n')})")
    p(f"by SPY day type (total R): " + ", ".join(f"{k} {v:+.1f}" for k, v in ty.items()))
    p(f"family-sides (n >= 300): {better} better / {worse} worse; worst {worst:+.4f}R/trade")
    pd.set_option("display.width", 300)
    p((fam.assign(delta=fam.delta.round(4), base=fam.base.round(4)).sort_values("delta")).to_string())
    sv = X.groupby("setup").r.agg(["count", "sum", "mean"]); sv = sv[sv["count"] >= 300]
    p(f"setups (n >= 300): {int((sv['sum'] > 0).sum())} better ({sv.loc[sv['sum'] > 0, 'sum'].sum():+.1f}R) / "
      f"{int((sv['sum'] <= 0).sum())} worse ({sv.loc[sv['sum'] <= 0, 'sum'].sum():+.1f}R)")
    for s in PRIM:
        x = X[X.setup == s]
        if len(x):
            dd = x.groupby("date").r.sum()
            p(f"Primary {s}: n {len(x)} base {x.BASE.mean():+.4f} ntbe {x.NTBE.mean():+.4f} delta {x.r.sum():+.1f}R "
              f"(TRAIN {x[x.date <= SPLIT].r.sum():+.1f} / VALID {x[x.date > SPLIT].r.sum():+.1f} / LATE {x[x.date >= LATE].r.sum():+.1f}); "
              f"w/o best day {dd.sum() - dd.max():+.1f}R")
    ok = ((s_.get("t") or 0) >= B90 and (tr_.get("exp_r") or -1) > 0 and (va_.get("exp_r") or -1) > 0 and ty.get("up", -1) > 0
          and ty.get("down", -1) > 0 and (s_.get("ex_best_day") or -1) > 0 and better > worse and worst >= -0.03)
    p(f"PASS {bool(ok)}"); p("Educational only - not financial advice.")
    (HERE / "ntbe_bt_out.txt").write_text("\n".join(out) + "\n")
    X.groupby(["family", "side", "setup"]).agg(n=("r", "size"), delta=("r", "sum")).reset_index().to_csv(HERE / "ntbe_setups.csv", index=False)


if __name__ == "__main__":
    main()
