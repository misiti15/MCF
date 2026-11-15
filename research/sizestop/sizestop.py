"""SIZESTOP scorer (Scout's PLAN.md frozen 2026-11-14 09:30 ET + Amendment 1 ex-dividend; Builder implementation, pre-score).
Engine = research/stopw (walk / r_of / costs as bt_all) on the BEREPLAY sample (bt_lab1104 + GEN hold lists), unchanged:
the variant is k = 1.5 x the stop distance at the same $ risk, target price unchanged, holdtr trail on D'.
Size g = |(open + cash dividend on its ex-date) / prior close - 1| / ATR%, ATR% = 14-session mean true range / prior close
(sessions < D). Implementation choices (flagged on the board before the score): the TR series and its 14-session window
RESTART after the locked-block gap (stricter than 'NaN on the first session'); primary unit = net R in own-risk units (as
STOPW); gross and ex-market (beta x SPY over each leg's own hold) reported beside it.
Controls: size-cut CTRL = BASE x D/D' (stopw_sizectl); stop effect eff_i = VAR_i - CTRL_i for every trade (any trade can be
widened); conditioning effect = sum over rule-changed trades of eff minus the EXPECTED sum of a same-count random draw within
the trade's setup x month stratum (exact expectation, per day for the day-clustered t), plus 200 random draws for the null.
    python sizestop.py --selftest      python sizestop.py <hold_lists_dir> [procs]  (the ONE score)
Locked block dropped at every read. Educational only - not financial advice."""
import os, sys, subprocess
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(HERE.parent / "stopw")); import stopw as SW  # noqa: E402
HALF_DAYS = {"2025-07-03", "2025-11-28", "2025-12-24"}     # Amendment 2: early-close sessions dropped (checklist 42)
K = 1.5; NDRAW = 200; N_FAMILY = 79; SPLIT = "2025-09-30"; LB0, LB1 = "2024-11-01", "2025-02-28"
CFGS = {"C1": (4, 5), "C2": (5,)}


def walk_ix(o, h, l, c, e, s, D, U, trail=False):
    """stopw.walk plus the exit index (for each leg's own SPY hold) and the give-up-then-recover flag."""
    n = len(c)
    if n == 0: return e, 0, 0, False
    fav = (h - e) if s > 0 else (e - l)
    if trail:
        cb = np.maximum.accumulate(c) if s > 0 else np.minimum.accumulate(c)
        prev = np.r_[e, cb[:-1]]; on = s * (prev - e) >= D
        lev = np.where(on, prev - s * D, e - s * D); lev = np.maximum(lev, e - D) if s > 0 else np.minimum(lev, e + D)
    else:
        lev = np.full(n, e - s * D)
    hit = (l <= lev) if s > 0 else (h >= lev)
    i_s = SW.first(hit); i_t = SW.first(fav >= U) if np.isfinite(U) else 10 ** 9
    if i_s <= i_t and i_s < n:
        rec = bool(np.isfinite(U) and (fav[i_s + 1:] >= U).any())       # stopped, then the target traded in a LATER minute (Skeptic)
        return (o[i_s] if s * (o[i_s] - lev[i_s]) <= 0 else lev[i_s]), 1, i_s, rec
    if i_t < n: return e + s * U, 2, i_t, False
    return c[-1], 0, n - 1, False


def leg(o, h, l, c, e, s, D, U, trail, tier, ecost):
    px, kd, ix, rec = walk_ix(o, h, l, c, e, s, D, U, trail)
    xcost = (0.0 if kd == 2 else SW.SL + px * SW.BP) + (SW.SX if kd == 1 else 0.0)
    return (s * (px - e) - tier * (ecost + xcost)) / D, s * (px - e) / D, kd, ix, rec


def size_quintiles(daily, div):
    """(date, symbol) -> quintile 1-5 of g across all lab names that day; NaN where undefined (first sessions after the gap)."""
    d = daily.sort_values(["symbol", "date"]).copy()
    col = "rate_adj" if "rate_adj" in div.columns else "rate"            # split-adjusted dividend (Skeptic 11-14 18:50)
    d = d.merge(div.rename(columns={col: "div"})[["symbol", "date", "div"]], on=["symbol", "date"], how="left")
    d["div"] = d["div"].fillna(0.0)
    g_ = d.groupby("symbol")
    pc = g_.close.shift(1); gapd = (pd.to_datetime(d.date) - pd.to_datetime(g_.date.shift(1))).dt.days
    brk = (gapd > 5) | pc.isna()                                         # restart after the locked hole (checklist 8)
    seg = brk.groupby(d.symbol).cumsum()
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())); tr[brk] = np.nan
    d["seg"] = seg
    atr = tr.groupby([d.symbol, d.seg]).transform(lambda v: v.shift(1).rolling(14, min_periods=14).mean())   # sessions < D
    atrp = atr / pc; atrp[brk] = np.nan
    g = ((d.open + d["div"]) / pc - 1).abs() / atrp
    d["g"] = g.where(~brk)
    d["q"] = d.groupby("date").g.transform(lambda v: np.ceil(v.rank(method="first") / v.notna().sum() * 5).clip(1, 5))
    return d.set_index(["date", "symbol"]).q


def cond_effect(T, eff, rule):
    """conditioning effect: per trade eff x (1[rule] - k_s/n_s) in its setup x month stratum, summed per day."""
    st = T.setup + "|" + T.date.str[:7]
    k = pd.Series(rule.astype(float)).groupby(st.to_numpy()).transform("sum").to_numpy()
    n = pd.Series(1.0, index=range(len(T))).groupby(st.to_numpy()).transform("sum").to_numpy()
    c = eff * (rule.astype(float) - k / n)
    days = pd.Series(c).groupby(T.date.to_numpy()).sum()
    t = days.mean() / (days.std(ddof=1) / np.sqrt(len(days))) if len(days) > 2 and days.std() > 0 else np.nan
    return days, t


def null_draws(T, eff, rule, rng):
    """200 draws of NAME-DAYS (not trades; checklist 31, Skeptic): within each setup x month stratum pick as many of the
    stratum's name-days as the rule widens, and widen every trade of that setup on them. Returns the drawn effect sums."""
    st = (T.setup + "|" + T.date.str[:7]).to_numpy(); nd = (T.symbol.astype(str) + "|" + T.date).to_numpy()
    df = pd.DataFrame(dict(st=st, nd=nd, eff=eff, rule=rule))
    per = df.groupby(["st", "nd"]).agg(eff=("eff", "sum"), rule=("rule", "max")).reset_index()
    groups = {s: (g.eff.to_numpy(), int(g.rule.sum())) for s, g in per.groupby("st")}
    out = np.empty(NDRAW)
    for b in range(NDRAW):
        out[b] = sum(e[rng.choice(len(e), k, replace=False)].sum() for e, k in groups.values() if k)
    return out


def load_daily():
    """Named OHLC daily input (Skeptic ask 3): research/history2y/data/daily.parquet (lab list, Alpaca SIP, split-adjusted),
    locked block filtered OUT at read with a pyarrow predicate (rule 19)."""
    import pyarrow.dataset as pds, datetime as dt
    t = pds.dataset(str(ROOT / "research/history2y/data/daily.parquet"), format="parquet")
    f = (pds.field("date") < dt.date(2024, 11, 1)) | (pds.field("date") > dt.date(2025, 2, 28))
    d = t.to_table(filter=f, columns=["symbol", "date", "open", "high", "low", "close"]).to_pandas()
    d["date"] = pd.to_datetime(d.date).dt.strftime("%Y-%m-%d"); d["symbol"] = d.symbol.astype(str)
    assert not ((d.date >= LB0) & (d.date <= LB1)).any()
    return d


def selftest():
    SW.selftest()
    rng = np.random.default_rng(3); n = 6000
    T = pd.DataFrame(dict(setup=rng.choice(["A", "B", "C"], n), date=[f"2025-0{m}-{d:02d}" for m, d in zip(rng.integers(3, 9, n), rng.integers(1, 28, n))]))
    q = rng.integers(1, 6, n); rule = q >= 4
    for planted in (0.15, 0.0):
        eff = rng.normal(0.02, 0.3, n) + planted * rule
        days, t = cond_effect(T, eff, rule)
        print(f"selftest conditioning planted {planted}: effect {days.sum():+.1f} t {t:+.2f}")
        assert (t > 5) if planted else abs(t) < 3
    T2 = T.assign(symbol=rng.choice([f"N{i}" for i in range(40)], n))
    nd_rule = (T2.symbol.str[1:].astype(int) % 3 == 0).to_numpy()          # rule set at the name level
    dr = null_draws(T2, rng.normal(0, 0.3, n), nd_rule, np.random.default_rng(5))
    print(f"selftest name-day null: {len(dr)} draws, mean {dr.mean():+.1f}, sd {dr.std():.1f}")
    # size quintiles: gap restart and dividend add-back
    dates = [str(x.date()) for x in pd.bdate_range("2024-09-02", "2024-10-31")] + [str(x.date()) for x in pd.bdate_range("2025-03-03", "2025-04-30")]
    rows = []
    for s in range(20):
        p = 100.0
        for i, dt in enumerate(dates):
            o = p * (1 + (0.002 * s if i % 7 == 0 else 0.0005)); rows.append(dict(symbol=f"S{s}", date=dt, open=o, high=o * 1.01, low=o * .99, close=o)); p = o
    dq = size_quintiles(pd.DataFrame(rows), pd.DataFrame(dict(symbol=["S0"], date=[dates[30]], rate=[5.0])))
    first_post = dq.xs("2025-03-03", level=0); assert first_post.isna().all()
    assert dq.xs(dates[15], level=0).notna().all()                       # 15th session: 14 TRs available
    assert dq.xs("2025-03-14", level=0).isna().all()                     # < 14 TRs after the restart
    print("selftest ok: stopw engine, conditioning effect (planted / null), size quintile restart after the gap")


JOB = {}


def sym_job(args):
    """per symbol (as stopw.sym_job): BASE and k=1.5 legs for every trade, with each leg's exit minute for its SPY hold."""
    sym, tr = args
    import pyarrow.dataset as pds
    if not JOB:
        sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE.parent / "bereplay"))
        from mcf.research import gates as G
        import bereplay as BR
        JOB.update(G=G, BR=BR)
    G, BR = JOB["G"], JOB["BR"]
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < BR.TL0) | (pds.field(ix) >= BR.TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    assert not ((df.index >= BR.TL0) & (df.index < BR.TL1)).any()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    df = df[keep]; mm = mm[keep]; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1] if len(dd) else np.array([], int); en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span: continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        o, h, l, c = O[j:b], H[j:b], L[j:b], C[j:b]
        if not len(c): continue
        e = float(r.close); Rr = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * Rr; U = up * Rr
        if not (np.isfinite(e) and e > 0 and D > 0): continue
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (SW.SL + e * SW.BP) * float(G.tod_cost_mult(np.array([r.tod]))[0]); trail = r.geom == "holdtr"
        nb, gb, kb, ib, rb = leg(o, h, l, c, e, r.side, D, U, trail, tier, ecost)
        nv, gv, kv, iv, rv = leg(o, h, l, c, e, r.side, K * D, U, trail, tier, ecost)
        out.append((r.setup, r.side, r.geom, sym, str(r.date), r.tod, int(mm[j]), int(mm[j + ib]), int(mm[j + iv]),
                    nb, gb, kb, rb, nv, gv, kv, rv))
    return out


COLS = ["setup", "side", "geom", "symbol", "date", "tod", "m_entry", "m_xb", "m_xv",
        "base_net", "base_gross", "base_kind", "base_rec", "var_net", "var_gross", "var_kind", "var_rec"]


def build(hold_dir, procs):
    from multiprocessing import Pool
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y")); sys.path.insert(0, str(HERE.parent / "bereplay"))
    import bereplay as BR
    t = BR.load_lists(hold_dir)
    rows = []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, list(t.groupby("symbol")), chunksize=4)):
            if res: rows += res
            if k % 200 == 0: print(f"symbols {k}", flush=True)
    return pd.DataFrame(rows, columns=COLS)


def spy_moves(X):
    import pyarrow.dataset as pds
    NY = "America/New_York"; ix = "__index_level_0__"
    TL0, TL1 = pd.Timestamp(LB0, tz=NY), pd.Timestamp("2025-03-01", tz=NY)
    s = pds.dataset(str(ROOT / "data/cache_hist/1Min/SPY.parquet"), format="parquet").to_table(
        filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in s.columns: s = s.set_index(ix)
    s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")]
    key = pd.Series(s.close.values, index=pd.MultiIndex.from_arrays([s.index.strftime("%Y-%m-%d"), s.index.hour * 60 + s.index.minute]))
    a = key.reindex(pd.MultiIndex.from_arrays([X.date, X.m_entry])).to_numpy()
    X["spy_b"] = (key.reindex(pd.MultiIndex.from_arrays([X.date, X.m_xb])).to_numpy() / a - 1) * 100
    X["spy_v"] = (key.reindex(pd.MultiIndex.from_arrays([X.date, X.m_xv])).to_numpy() / a - 1) * 100
    return X


def main():
    st = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "PLAN.md", "sizestop.py"], capture_output=True, text=True).stdout
    assert not st.strip(), "PLAN.md and sizestop.py must be committed before the score"
    hold_dir = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    sys.path.insert(0, str(ROOT)); from mcf.research import gates as G
    T90 = round(max(1.35, 0.9 * G.t_required(N_FAMILY)), 2)
    X = spy_moves(build(hold_dir, procs))
    q = size_quintiles(load_daily(), pd.read_parquet(HERE / "data/cash_div.parquet"))
    X["q"] = q.reindex(pd.MultiIndex.from_arrays([X.date, X.symbol])).to_numpy()
    nh = int(X.date.isin(HALF_DAYS).sum()); print(f"half-day sessions dropped: {nh} trades")
    X = X[np.isfinite(X.q) & np.isfinite(X.spy_b) & np.isfinite(X.spy_v) & ~X.date.isin(HALF_DAYS)].reset_index(drop=True)
    X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
    X["per"] = np.where(X.date <= SPLIT, "TRAIN", "VALID")
    beta = {s: (np.polyfit(g.spy_b, g.base_gross, 1)[0] if len(g) >= 30 else float(g.side.iloc[0])) for s, g in X[X.per == "TRAIN"].groupby("setup")}
    b = X.setup.map(beta).fillna(X.side.astype(float)).to_numpy()
    X["eff_net"] = X.var_net - X.base_net / K                               # size-cut CTRL = BASE x D/D'
    X["eff_gross"] = X.var_gross - X.base_gross / K
    X["eff_exm"] = (X.var_gross - b * X.spy_v / K) - (X.base_gross - b * X.spy_b) / K
    D_ = load_daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
    dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
    X.to_parquet(HERE / "data/sizestop_trades.parquet", index=False)
    rng = np.random.default_rng(20261116); out = []
    print(f"SIZESTOP (PLAN + Amendment 1, one score): {len(X)} trades with a size quintile, {X.setup.nunique()} setups, "
          f"{X.family.nunique()} families, {X.date.nunique()} days; family N {N_FAMILY}, BAR90 {T90}")
    for c, qs in CFGS.items():
        rule = X.q.isin(qs).to_numpy()
        row = dict(config=c, changed_share=round(rule.mean(), 3))
        for col in ("eff_net", "eff_gross", "eff_exm"):
            days, t = cond_effect(X, X[col].to_numpy(), rule)
            row[f"{col}_cond"] = round(days.sum(), 1); row[f"{col}_t"] = round(t, 2) if np.isfinite(t) else np.nan
        days, t = cond_effect(X, X.eff_net.to_numpy(), rule)
        row["wo_best"] = round(days.sum() - days.max(), 1)
        se = abs(days.sum() / t) if t and np.isfinite(t) and t != 0 else np.nan
        row["MDE80_per_changed"] = round(2.8 * se / max(int(rule.sum()), 1), 4)            # guild standard 2026-11-15
        row["MDE_bar_per_changed"] = round((T90 + 0.84) * se / max(int(rule.sum()), 1), 4)
        for p_ in ("TRAIN", "VALID"):
            m = (X.per == p_).to_numpy(); dp, tp = cond_effect(X[m].reset_index(drop=True), X.eff_net.to_numpy()[m], rule[m])
            row[f"{p_}_cond"] = round(dp.sum(), 1); row[f"{p_}_t"] = round(tp, 2) if np.isfinite(tp) else np.nan
        bydt = days.groupby(days.index.map(dtype)).sum(); row.update({f"sess_{k}": round(bydt.get(k, 0.0), 1) for k in ("up", "down", "quiet")})
        row["stop_effect_changed"] = round(X.eff_net[rule].mean(), 4)
        fam = {}
        for f_, g in X.groupby("family"):
            ii = g.index.to_numpy(); dfm, _ = cond_effect(g.reset_index(drop=True), X.eff_net.to_numpy()[ii], rule[ii])
            fam[f_] = dfm.sum() / len(g)
        fam = pd.Series(fam); row.update(fam_better=int((fam > 0).sum()), fam_worse=int((fam < 0).sum()), worst_fam=round(fam.min(), 4))
        stopped = X.base_kind.to_numpy() == 1
        recr = X.base_rec.to_numpy()[rule & stopped].mean() if (rule & stopped).any() else np.nan
        stv = (X.setup + "|" + X.date.str[:7]).to_numpy()
        rec_s = pd.Series(np.where(stopped, X.base_rec.to_numpy().astype(float), np.nan)).groupby(stv).transform("mean").to_numpy()
        recn = np.nanmean(rec_s[rule])          # random-day expectation: each rule trade's stratum recover share among BASE stop-outs
        row.update(stopout_base=round(stopped[rule].mean(), 3), stopout_var=round((X.var_kind.to_numpy()[rule] == 1).mean(), 3),
                   recover_rule=round(recr, 3), recover_random=round(recn, 3))
        nd = null_draws(X, X.eff_net.to_numpy(), rule, rng)
        row["null95"] = round(np.percentile(nd, 95), 1); row["rule_sum"] = round(X.eff_net[rule].sum(), 1)
        row["pass"] = bool((row["eff_net_t"] or 0) >= T90 and row["TRAIN_cond"] > 0 and row["VALID_cond"] > 0 and row["sess_down"] >= 0
                           and row["fam_better"] >= 0.6 * len(fam) and row["wo_best"] > 0 and (row["recover_rule"] or 0) > (row["recover_random"] or 1))
        out.append(row)
        fam.round(4).rename("cond_per_trade").to_csv(HERE / f"sizestop_family_{c}.csv")
    R = pd.DataFrame(out); pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    print(R.T.to_string()); R.to_csv(HERE / "sizestop_results.csv", index=False)
    for r in out:                          # Skeptic's pre-registered red flag
        if r["stop_effect_changed"] > 0 and abs(r["eff_net_t"] or 0) < 1.0:
            print(f"{r['config']}: RED FLAG - stop effect positive ({r['stop_effect_changed']:+.4f}R/changed trade) but conditioning ~0 "
                  f"(t {r['eff_net_t']}): known unconditional widening (STOPW), not the gap condition")
        if not r["pass"]:
            print(f"{r['config']}: CLOSED - nothing above {r['MDE_bar_per_changed']:.4f}R per changed trade at the bar (MDE80 {r['MDE80_per_changed']:.4f}R); smaller unknown")
    print(f"configs shown: {len(out)} (family N {N_FAMILY})")
    print("conditioning effect = sum over rule-widened trades of (VAR - BASE x D/D') minus its same-count random-name-day "
          "expectation within setup x month; net R own-risk units; null95 = 95th pct of 200 name-day draws of the raw rule sum.")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
