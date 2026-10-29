"""p1_1029: score tasks 2-4 (PLAN.md) on the open two-year history. Parent trades = the rebuilt gates1021 cache
(production R, costs in, x3 extended tier) + trades_p1.parquet (CWT14 pdl longs; task 3 exit variants).
Regime inputs from regime_days.csv (pre-open only). Locked block never loaded (load_sig asserts).
Educational only - not financial advice.

    G21SCR=$SCRATCH/p1/g python research/bdi/p1_1029/evaluate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research" / "bdi" / "gates1021" / "scripts"))
from load import load_sig  # noqa: E402

SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/p1")
TRAIN_END = pd.Timestamp("2025-12-31").date()
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
USD_PER_R = 15.0  # ~ Primary's median live $ risk per trade (10-20..10-28), for the $ column only
RNG = np.random.default_rng(20261029)

CWT14 = ["CWT14-failbrk-pdl-p05-long", "CWT14-failbrk-pdl-p05-lowvol-long", "CWT14-failbrk-pdl-p10-long",
         "CWT14-failbrk-pdl-p10-lowvol-long"]
LONGS = ["NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long", "ST7-rsi50dn-long-pm-t1s1-FD",
         "NS1-rsidip-rsi5pop-long-FD", "NS5-sma50-flush-oversold-long-FD", "ST4-emadn-long-am-t1s05-FD",
         "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD", "LD1-ns1-breadthup-t05s1-long",
         "LD3-st2-idxturn-t05s1-long", "LD4-st4-breadthup-t1s05-long", "LD5-st2-breadthup-t05s1-long",
         "NM-AR-AM-gapdown-capitulation-long", "NM-HL-T75-pm-long"] + CWT14
FADE_SHORT = ["MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell", "MF4-h40-open-flowsell-FD",
              "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
              "L3-gap-slope-fromopen-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD",
              "MF3-open-flowsell-rsi5hi-FD", "NS3-failed-vwap-reclaim-short-FD", "RW4-ns3-adv150-short-FD",
              "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD", "exhaustion_short-FD"]
MOMENTUM = ["LD1-ns1-breadthup-t05s1-long", "LD3-st2-idxturn-t05s1-long", "LD4-st4-breadthup-t1s05-long",
            "LD5-st2-breadthup-t05s1-long", "NM-HL-T75-pm-long"]
FADE_LONG = [s for s in LONGS if s not in MOMENTUM]
FADE = FADE_SHORT + FADE_LONG
LONG_GATES = {"L1": ("SPY prior close > SMA20", lambda R: R["SPY_above_sma20_prev"]),
              "L2": ("QQQ prior close > SMA20", lambda R: R["QQQ_above_sma20_prev"]),
              "L3": ("SPY and QQQ > SMA20", lambda R: (R["SPY_above_sma20_prev"] * R["QQQ_above_sma20_prev"])),
              "L4": ("SPY gap >= -0.25%", lambda R: (R["SPY_gap"] >= -0.25).astype(float).where(R["SPY_gap"].notna())),
              "L5": ("SPY gap >= -0.50%", lambda R: (R["SPY_gap"] >= -0.50).astype(float).where(R["SPY_gap"].notna())),
              "L6": ("prior-day SPY ret > 0", lambda R: (R["SPY_ret_prev"] > 0).astype(float).where(R["SPY_ret_prev"].notna())),
              "L7": ("prior-day QQQ ret > 0", lambda R: (R["QQQ_ret_prev"] > 0).astype(float).where(R["QQQ_ret_prev"].notna())),
              "L8": ("prior-day SPY ret > -0.5%", lambda R: (R["SPY_ret_prev"] > -0.5).astype(float).where(R["SPY_ret_prev"].notna()))}
VOL_GATES = {"V1": ("skip if SPY ATR14 > trailing p70", "hi_atr_70"), "V2": ("skip if SPY ATR14 > trailing p80", "hi_atr_80"),
             "V3": ("skip if SPY ATR14 > trailing p90", "hi_atr_90"), "V4": ("skip if SPY RV20 > trailing p70", "hi_rv_70"),
             "V5": ("skip if SPY RV20 > trailing p80", "hi_rv_80"), "V6": ("skip if SPY RV20 > trailing p90", "hi_rv_90"),
             "V7": ("skip if VXX 5d chg > trailing p80", "hi_vxx5_80")}


def bar(n):
    return max(1.5, float(np.sqrt(2 * np.log(n))))


def met(r, d):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return dict(n=0, avg=np.nan, shrunk=np.nan, win=np.nan, totR=0.0, t=np.nan)
    m = r.mean()
    s = pd.DataFrame({"d": d, "r": r}).groupby("d")["r"].agg(["sum", "size"])
    se = np.sqrt(((s["sum"] - m * s["size"]) ** 2).sum()) / n
    return dict(n=n, avg=m, shrunk=m * n / (n + 20), win=(r > 0).mean(), totR=r.sum(), t=m / se if se > 0 else np.nan)


def exbest(r, d):
    s = pd.Series(r).groupby(np.asarray(d)).agg(["sum", "size"])
    if len(s) < 2:
        return np.nan, np.nan
    b = s["sum"].idxmax()
    ex = (s["sum"].sum() - s.loc[b, "sum"]) / (s["size"].sum() - s.loc[b, "size"])
    share = s.loc[b, "sum"] / s["sum"].sum() if s["sum"].sum() > 0 else np.nan
    return ex, share


def paired(var, par):
    """(sum var - sum parent) per parent trade, same days, day-clustered t."""
    a = par.groupby("date")["r"].agg(["sum", "size"])
    b = var.groupby("date")["r"].sum().reindex(a.index.union(pd.Index(var["date"].unique())), fill_value=0.0)
    a = a.reindex(b.index, fill_value=0)
    D = b - a["sum"]
    n = a["size"].sum()
    dl = D.sum() / n
    se = np.sqrt(((D - dl * a["size"]) ** 2).sum()) / n
    return dl, (dl / se if se > 0 else np.nan)


def rand_day_pct(par, keep_days):
    """Percentile of the gated avg R among 1,000 random removals of the same number of the setup's traded days."""
    s = par.groupby("date")["r"].agg(["sum", "size"])
    days = s.index.to_numpy()
    k = int(np.isin(days, list(keep_days)).sum())
    if k == 0 or k == len(days):
        return np.nan
    obs = s.loc[np.isin(days, list(keep_days)), "sum"].sum() / s.loc[np.isin(days, list(keep_days)), "size"].sum()
    S, N = s["sum"].to_numpy(), s["size"].to_numpy()
    sims = np.empty(1000)
    for i in range(1000):
        idx = RNG.choice(len(days), k, replace=False)
        sims[i] = S[idx].sum() / N[idx].sum()
    return float((sims < obs).mean())


def row(fam, setup, vid, knob, par, var, extra=None, kept_days=None):
    tr = lambda x: x[x.date <= TRAIN_END]  # noqa: E731
    va = lambda x: x[x.date > TRAIN_END]  # noqa: E731
    P, V = met(par.r, par.date), met(var.r, var.date)
    Pt, Pv, Vt, Vv = met(tr(par).r, tr(par).date), met(va(par).r, va(par).date), met(tr(var).r, tr(var).date), met(va(var).r, va(var).date)
    d, t = paired(var, par)
    dtr, ttr = paired(tr(var), tr(par)) if len(tr(par)) else (np.nan, np.nan)
    dva, tva = paired(va(var), va(par)) if len(va(par)) else (np.nan, np.nan)
    ex, sh = exbest(var.r.to_numpy(), var.date.to_numpy())
    out = dict(family=fam, setup=setup, var=vid, knob=knob, n_par=P["n"], n=V["n"], kept=V["n"] / max(P["n"], 1),
               par_avg=P["avg"], avg=V["avg"], par_shrunk=P["shrunk"], shrunk=V["shrunk"], par_win=P["win"], win=V["win"],
               par_totR=P["totR"], totR=V["totR"], pnl_usd=V["totR"] * USD_PER_R, par_t=P["t"], t=V["t"],
               train_par=Pt["shrunk"], train=Vt["shrunk"], valid_par=Pv["shrunk"], valid=Vv["shrunk"],
               train_avg=Vt["avg"], valid_avg=Vv["avg"], d=d, t_imp=t, d_train=dtr, d_valid=dva, t_imp_train=ttr,
               t_imp_valid=tva, exbest=ex, best_share=sh)
    if kept_days is not None:
        out["rand_pct"] = rand_day_pct(par, kept_days)
    if extra:
        out.update(extra)
    return out


def judge(df, nfam):
    b = bar(nfam)
    beats = (df.train > df.train_par) & (df.valid > df.valid_par) & (df.t_imp >= b) & (df.d_train > 0) & (df.d_valid > 0)
    df["bar"] = round(b, 2)
    df["beats_parent"] = beats & (df["var"] != "P")
    fin = df.beats_parent & (df.train_avg > 0) & (df.valid_avg > 0) & (df.exbest > 0)
    if "rand_pct" in df:
        fin &= df.rand_pct.fillna(0) >= 0.95
    df["finalist"] = fin
    return df


def gate_family(fam, setups, gates, T, R, pooled):
    rows = []
    books = [(s, T[T.setup == s]) for s in setups] + [(name, T[T.setup.isin(ss)]) for name, ss in pooled]
    for s, par in books:
        if not len(par):
            rows.append(dict(family=fam, setup=s, var="P", knob="no trades", n_par=0, n=0))
            continue
        rows.append(row(fam, s, "P", "parent", par, par))
        for gid, (lab, col) in gates.items():
            g = col(R) if callable(col) else R[col]
            g = g if fam == "long_gate" else (1 - g)  # vol switch: keep when NOT high-vol
            keep_dates = set(g.index[(g.fillna(1) > 0.5).to_numpy()])  # ungated (NaN) sessions are traded
            var = par[par.date.isin(keep_dates)]
            rows.append(row(fam, s, gid, lab, par, var, kept_days=set(par.date.unique()) & keep_dates))
    return pd.DataFrame(rows)


def main():
    R = pd.read_csv(OUT / "regime_days.csv", parse_dates=["date"])
    R["date"] = R["date"].dt.date
    R = R.set_index("date")
    S = load_sig()
    S = S[["setup", "symbol", "date", "tod", "r"]].copy()
    # cache R is in 0.25-ATR units; convert to live R (= the stop distance) so t1s05 setups match the journal's R
    geom = {r["setup"]: r["geom"] for r in json.load(open(SCR / "g" / "setups.json"))}
    S["r"] = S["r"] / S["setup"].map(lambda s: {"t1s05": 0.5, "t05s05": 0.5}.get(geom.get(s), 1.0))
    P1 = pd.read_parquet(SCR / "trades_p1.parquet")
    P1["date"] = pd.to_datetime(P1["date"]).dt.date
    T = pd.concat([S, P1[(P1["var"] == "P") & P1.setup.isin(CWT14)][["setup", "symbol", "date", "tod", "r"]]],
                  ignore_index=True)
    d = T.date.to_numpy()
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    T = T[np.isfinite(T.r)]
    print("parent trades per setup:\n", T.groupby("setup").r.agg(["size", "mean"]).round(4).to_string())
    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 500)
    # ---- task 2
    A = gate_family("long_gate", LONGS, LONG_GATES, T, R, [("LONG BOOK (pooled)", LONGS)])
    nA = int((A["var"] != "P").sum())
    A = judge(A, nA)
    # ---- task 4
    B = gate_family("vol_switch", FADE, VOL_GATES, T, R,
                    [("FADE BOOK (pooled)", FADE), ("MOMENTUM BOOK (pooled, control)", MOMENTUM)])
    B = B[~((B.setup.isin(MOMENTUM)) & (B["var"] != "P"))]  # momentum only as the pooled control
    nB = int((B["var"] != "P").sum())
    B = judge(B, nB)
    # ---- task 3
    rows = []
    lineage = {"MF2-open-rsimidhi-flowsell-FD": 17, "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": 18,
               "RW3-gapdn-rsi5pop-flowsell-short-FD": 17}
    C = []
    for s, prior in lineage.items():
        x = P1[P1.setup == s]
        par = x[x["var"] == "P"]
        parity = float((par.r - par.cache_r).abs().mean())
        rr = [row("exit_sweep", s, "P", "parent", par, par, extra=dict(parity_mean_abs_d=parity))]
        for (vid, knob), v in x[x["var"] != "P"].groupby(["var", "knob"], observed=True):
            rr.append(row("exit_sweep", s, vid, knob, par, v))
        c = pd.DataFrame(rr)
        c["lineage_N"] = prior + (len(c) - 1)
        C.append(judge(c, prior + len(c) - 1))
    C = pd.concat(C, ignore_index=True)
    allr = pd.concat([A, B, C], ignore_index=True)
    allr.to_csv(OUT / "results.csv", index=False)
    counts = dict(long_gate=nA, vol_switch=nB, exit_sweep=int((C["var"] != "P").sum()))
    counts["total"] = sum(counts.values())
    counts["study_bar"] = round(bar(counts["total"]), 2)
    json.dump(counts, open(OUT / "counts.json", "w"), indent=1)
    cols = ["setup", "var", "knob", "n_par", "n", "kept", "par_avg", "avg", "par_shrunk", "shrunk", "par_win", "win",
            "totR", "pnl_usd", "t", "train_par", "train", "valid_par", "valid", "d", "t_imp", "exbest", "best_share",
            "bar", "beats_parent", "finalist"]
    with open(OUT / "eval_out.txt", "w") as f:
        f.write("Educational only - not financial advice. Two-year backtest (open history, locked block never loaded), costs in.\n")
        f.write(json.dumps(counts) + "\n")
        for name, df in (("TASK 2 long gates", A), ("TASK 4 vol switch", B), ("TASK 3 exit sweep", C)):
            c2 = cols + (["rand_pct"] if "rand_pct" in df else []) + (["parity_mean_abs_d"] if "parity_mean_abs_d" in df else [])
            f.write(f"\n==== {name}\n" + df[[c for c in c2 if c in df]].round(4).to_string(index=False) + "\n")
    print(open(OUT / "eval_out.txt").read())


if __name__ == "__main__":
    main()
