"""stoplab grid B: score the stop-width multipliers (PLAN.md, pre-registered). Lab: TRAIN <= 2025-12 (choose), VALID
2026-01..03 + 2026-07-01..09-15 (validate); HOLD (2026-04..06, 2026-09-16 on) dropped, never read here.
Live (approximate, B2): per setup sessions sorted, first ceil(60%) choose / rest validate.
Writes lab_setup_k.csv, lab_summary.csv, live_setup_k.csv, global_k.csv, priority.csv, out.txt.
Educational only - not financial advice."""
import glob, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent; SCR = Path("/dev/shm/stopw_b")
KS = (0.75, 0.9, 1.0, 1.1, 1.25, 1.5); ALT = [k for k in KS if k != 1.0]
N_STUDY = 64; BAR = max(1.5, math.sqrt(2 * math.log(N_STUDY)))          # 2.88
BAR_SET = max(1.5, math.sqrt(2 * math.log(len(ALT))))                   # 1.79 per-setup choice of 5
PRI_TEAM = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "L3-gap-slope-fromopen-FD",
            "ST7-rsi50dn-long-pm-t1s1-FD", "NS5-sma50-flush-oversold-long", "CWT09-gapdn-vwaploss-g10-short",
            "NM-ETF-late-dip-di-long"]
PRI_PREFIX = ["GEN-261027-01", "MF2", "MF4", "CWT12-coil"]
OUT = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.append(s)


def split_lab(d):
    d = pd.to_datetime(d)
    tr = d <= "2025-12-31"
    va = ((d >= "2026-01-01") & (d <= "2026-03-31")) | ((d >= "2026-07-01") & (d <= "2026-09-15"))
    return np.where(tr, "train", np.where(va, "valid", "hold"))


def tday(x, dates):
    s = pd.Series(np.asarray(x, float)).groupby(np.asarray(dates)).sum()
    if len(s) < 3 or s.std(ddof=1) == 0:
        return np.nan
    return float(s.mean() / (s.std(ddof=1) / math.sqrt(len(s))))


def wo_best(x, dates):
    s = pd.Series(np.asarray(x, float)).groupby(np.asarray(dates)).sum()
    if not len(s):
        return np.nan, np.nan
    b = s.idxmax(); tot = s.sum()
    n = len(x) - int((np.asarray(dates) == b).sum())
    return (tot - s[b]) / max(n, 1), (s[b] / tot if tot > 0 else np.nan)


def lab():
    fs = sorted(glob.glob(str(SCR / "w_*.parquet")))
    T = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    T["split"] = split_lab(T.date)
    T = T[T.split != "hold"].copy()           # HOLD never read beyond this line
    p(f"lab rows (train+valid) {len(T):,}  setups {T.setup.nunique()}  months {len(fs)}")
    rows = []
    for s, g in T.groupby("setup"):
        tr, va = g[g.split == "train"], g[g.split == "valid"]
        d = dict(setup=s, geom=g.geom.iloc[0], src=g.src.iloc[0], n_train=len(tr), n_valid=len(va),
                 days_valid=va.date.nunique())
        for k in KS:
            d[f"tr{k}"] = tr[f"r{k}"].mean(); d[f"va{k}"] = va[f"r{k}"].mean()
            if k != 1.0:
                d[f"dtr{k}"] = (tr[f"r{k}"] - tr["r1.0"]).mean(); d[f"dva{k}"] = (va[f"r{k}"] - va["r1.0"]).mean()
                d[f"tva{k}"] = tday(va[f"r{k}"] - va["r1.0"], va.date)
                # size-only control: same trade, old stop, size x 1/k -> r1/k ; stop effect = r_k - r1/k
                d[f"setr{k}"] = (tr[f"r{k}"] - tr["r1.0"] / k).mean(); d[f"seva{k}"] = (va[f"r{k}"] - va["r1.0"] / k).mean()
                d[f"tseva{k}"] = tday(va[f"r{k}"] - va["r1.0"] / k, va.date)
        if len(tr) >= 30:
            best = max(KS, key=lambda k: d[f"tr{k}"])
        else:
            best = np.nan
        d["best_tr"] = best
        if best == best and best != 1.0:
            i = KS.index(best); nb = [KS[j] for j in (i - 1, i + 1) if 0 <= j < len(KS)]
            d["plateau_tr"] = all(d[f"tr{k}"] > d["tr1.0"] or k == 1.0 for k in nb)
            d["plateau_va"] = all((d[f"va{k}"] > d["va1.0"]) if k != 1.0 else True for k in nb) and d[f"dva{best}"] > 0
            x = va[f"r{best}"] - va["r1.0"]
            d["dva_best"] = d[f"dva{best}"]; d["tva_best"] = d[f"tva{best}"]; d["seva_best"] = d[f"seva{best}"]
            d["tseva_best"] = d[f"tseva{best}"]
            d["dva_best_wo_bestday"], d["bestday_share"] = wo_best(x.to_numpy(), va.date.to_numpy())
            d["va_best_wo_bestday"], _ = wo_best(va[f"r{best}"].to_numpy(), va.date.to_numpy())
            d["pass"] = bool(d["dtr" + str(best)] > 0 and d["dva_best"] > 0 and d["tva_best"] >= BAR_SET
                             and d["plateau_tr"] and d["plateau_va"] and d["seva_best"] > 0 and d["dva_best_wo_bestday"] > 0)
            d["pass_study"] = bool(d["pass"] and d["tva_best"] >= BAR)
            # stricter: the stop effect itself (beyond the size-only control) clears the bar
            d["pass_stop"] = bool(d["pass"] and d["tseva_best"] >= BAR_SET)
            d["pass_stop_study"] = bool(d["pass"] and d["tseva_best"] >= BAR)
        elif best == 1.0:
            d.update(dva_best=0.0, pass_=False)
        d["va1.0_wo_bestday"], _ = wo_best(va["r1.0"].to_numpy(), va.date.to_numpy())
        rows.append(d)
    S = pd.DataFrame(rows)
    S.to_csv(HERE / "lab_setup_k.csv", index=False, float_format="%.4f")
    # global k: one k for every setup
    G = []
    for k in ALT:
        dd = S[S.n_valid >= 30]
        dv = dd[f"dva{k}"]; dt = dd[f"dtr{k}"]
        va = T[T.split == "valid"]; x = va[f"r{k}"] - va["r1.0"]; y = va[f"r{k}"] - va["r1.0"] / k
        G.append(dict(k=k, setups=len(dd), pooled_dtr=float((T[T.split == "train"][f"r{k}"] - T[T.split == "train"]["r1.0"]).mean()),
                      pooled_dva=float(x.mean()), t_dva=tday(x, va.date), pooled_stop_effect_va=float(y.mean()),
                      t_stop_effect_va=tday(y, va.date), improve_va=int((dv > 0).sum()), worsen_va=int((dv < 0).sum()),
                      sum_gain_va=float(dv[dv > 0].sum()), sum_loss_va=float(dv[dv < 0].sum()), worst_va=float(dv.min()),
                      improve_both=int(((dv > 0) & (dt > 0)).sum()), worsen_both=int(((dv < 0) & (dt < 0)).sum()),
                      stopeff_improve_va=int((dd[f"seva{k}"] > 0).sum()), stopeff_worsen_va=int((dd[f"seva{k}"] < 0).sum())))
    G = pd.DataFrame(G); G.to_csv(HERE / "global_k.csv", index=False, float_format="%.4f")
    return S, G, T


def live():
    L = pd.read_parquet(SCR / "live_trades_k.parquet")
    rows = []
    for s, g in L.groupby("setup"):
        pri = s in PRIM or s in PRI_TEAM or any(s.startswith(x) for x in PRI_PREFIX)
        if len(g) < 20 and not (pri and len(g) >= 5):
            continue
        ds = sorted(g.date.unique()); nc = math.ceil(0.6 * len(ds)); ch = set(ds[:nc])
        d = dict(setup=s, n_live=len(g), sessions=len(ds), accounts=",".join(sorted(g.account.unique())),
                 avgR=g.R.mean(), lt20=len(g) < 20, null_mae=int(g.mae_r.isna().sum()))
        d["avgR_wo_bestday"], d["live_bestday_share"] = wo_best(g.R.to_numpy(), g.date.to_numpy())
        for k in KS:
            c = g[f"r{k}"]
            d[f"n{k}"] = int(c.notna().sum())
            # compare on rows where both exist
            m = c.notna()
            d[f"lv{k}"] = c[m].mean()
            if k != 1.0:
                d[f"dlv{k}"] = (c[m] - g.R[m]).mean()
                d[f"selv{k}"] = (c[m] - g.R[m] / k).mean()
                gc = g[m & g.date.isin(ch)]; gv = g[m & ~g.date.isin(ch)]
                d[f"dch{k}"] = (gc[f"r{k}"] - gc.R).mean(); d[f"dvl{k}"] = (gv[f"r{k}"] - gv.R).mean()
        d["best_live"] = max(KS, key=lambda k: 0 if k == 1.0 else d[f"dlv{k}"])
        d["best_live_choose"] = max(KS, key=lambda k: 0 if k == 1.0 else (d[f"dch{k}"] if d[f"dch{k}"] == d[f"dch{k}"] else -9))
        rows.append(d)
    V = pd.DataFrame(rows); V.to_csv(HERE / "live_setup_k.csv", index=False, float_format="%.4f")
    return V, L


def main():
    S, G, T = lab()
    V, L = live()
    p(f"\n== Global k (one multiplier for every lab setup with >= 30 VALID trades), d = r_k - r_1.0 per trade ==")
    p(G.round(4).to_string(index=False))
    p(f"\n== Per-setup choice (best k on TRAIN, n_train >= 30), bar per setup t >= {BAR_SET:.2f}, study-wide {BAR:.2f} ==")
    c = S[S.best_tr.notna()]
    p("best-k distribution on TRAIN:", c.best_tr.value_counts().sort_index().to_dict())
    ch = c[c.best_tr != 1.0]
    p(f"setups where TRAIN picks k != 1.0: {len(ch)}; VALID improves {int((ch.dva_best > 0).sum())}, worsens {int((ch.dva_best < 0).sum())}; "
      f"sum gain {ch.dva_best[ch.dva_best > 0].sum():.3f} R/trade, sum loss {ch.dva_best[ch.dva_best < 0].sum():.3f}, worst {ch.dva_best.min():.3f}")
    p(f"  stop effect (vs size-only control) VALID > 0: {int((ch.seva_best > 0).sum())}, < 0: {int((ch.seva_best < 0).sum())}")
    p(f"  pass (all bars, per-setup t): {int(ch['pass'].sum())}; pass at study-wide t {BAR:.2f}: {int(ch['pass_study'].sum())}")
    p(f"  pass incl. stop effect t >= {BAR_SET:.2f} (beyond size-only control): {int(ch['pass_stop'].sum())}; at {BAR:.2f}: {int(ch['pass_stop_study'].sum())}")
    p(f"  best k at the grid edge: 1.5 in {int((c.best_tr == 1.5).sum())}, 0.75 in {int((c.best_tr == 0.75).sum())} (edge = no plateau beyond)")
    for lab_, cc in (("TRAIN-positive (tr1.0 > 0)", ch[ch["tr1.0"] > 0]), ("TRAIN-negative", ch[ch["tr1.0"] <= 0])):
        p(f"  {lab_}: {len(cc)} setups; VALID improves {int((cc.dva_best > 0).sum())}, worsens {int((cc.dva_best < 0).sum())}; "
          f"stop effect > 0 {int((cc.seva_best > 0).sum())}; pass {int(cc['pass'].sum())}; picks {cc.best_tr.value_counts().sort_index().to_dict()}")
    if ch["pass"].any():
        p(ch[ch["pass"]][["setup", "best_tr", "n_train", "n_valid", "tr1.0", "va1.0", "dva_best", "tva_best", "seva_best", "tseva_best",
                          "dva_best_wo_bestday", "bestday_share", "pass_stop"]].round(3).to_string(index=False))
    # merge live
    M = S.merge(V, on="setup", how="outer")
    def agree(r):
        if r.get("best_tr") != r.get("best_tr") or r.get("best_live") != r.get("best_live"):
            return ""
        a = np.sign(r["best_tr"] - 1.0); b = np.sign(r["best_live"] - 1.0)
        return "same" if a == b else "opposite" if a * b < 0 else "one-neutral"
    M["agree_dir"] = M.apply(agree, axis=1)
    M["priority"] = M.setup.apply(lambda s: 1 if s in PRIM else 2 if (s in PRI_TEAM or any(s.startswith(x) for x in PRI_PREFIX)) else 3)
    M["n_all"] = M[["n_live"]].fillna(0).sum(axis=1)
    M = M.sort_values(["priority", "n_all"], ascending=[True, False])
    cols = ["priority", "setup", "geom", "n_train", "n_valid", "tr1.0", "va1.0", "best_tr", "dva_best", "tva_best", "seva_best",
            "plateau_tr", "plateau_va", "dva_best_wo_bestday", "bestday_share", "pass", "pass_stop", "n_live", "lt20", "sessions", "avgR",
            "avgR_wo_bestday", "live_bestday_share", "best_live", "dlv0.75", "dlv0.9", "dlv1.1", "dlv1.25", "dlv1.5", "selv1.5", "agree_dir"]
    M[[c_ for c_ in cols if c_ in M]].to_csv(HERE / "priority.csv", index=False, float_format="%.4f")
    p("\n== Live approximation (B2, APPROXIMATE), setups with >= 20 live trades ==")
    V20 = V[~V.lt20]
    p("(priority setups with 5-19 live trades are listed in priority.csv only, flagged lt20)")
    p("best live k:", V20.best_live.value_counts().sort_index().to_dict(), " setups", len(V20))
    V = V20
    for k in ALT:
        p(f"  k={k}: live d>0 in {int((V[f'dlv{k}'] > 0).sum())}, <0 in {int((V[f'dlv{k}'] < 0).sum())}; mean d {V[f'dlv{k}'].mean():+.4f}; "
          f"stop effect>0 {int((V[f'selv{k}'] > 0).sum())}; choose->validate same sign {int((np.sign(V[f'dch{k}']) == np.sign(V[f'dvl{k}'])).sum())}/{int(V[f'dvl{k}'].notna().sum())}")
    p("lab vs live direction agreement:", M.agree_dir.value_counts().to_dict())
    Path(HERE / "out.txt").write_text("\n".join(OUT) + "\n")
    return S, G, V, M


PRIM = set(pd.read_csv(HERE.parent / "setups.csv").query("account == 'primary'").setup)
if __name__ == "__main__":
    main()
