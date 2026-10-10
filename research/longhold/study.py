"""Longhold study: scores the pre-declared grid in NOTES.md section 1 (105 configurations + benchmarks + diagnostics).

Single process, numpy, ~1.2k symbols x 2.7k sessions. Every daily return inside the rule-19 locked block
(2024-11-01..2025-02-28) is set to 0 BEFORE any simulation, and those days are dropped before any statistic.
Outputs: results.csv (config x period), gates.csv (one row per config with its verdict), data/daily_returns.parquet
(git-ignored; net daily returns per config, locked days = 0). Educational only - not financial advice.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
W3 = ROOT / "research" / "swarm1010" / "w3_daily"

LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
SPLITS = {"train": ("2017-01-01", "2020-12-31"), "valid": ("2021-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
N_TOTAL = 105
T_REQ = math.sqrt(2 * math.log(N_TOTAL))
BORROW = 0.03
E_RISK = ["SPY", "QQQ", "IWM", "EFA", "EEM", "VNQ", "TLT", "IEF", "GLD"]
E_SECTOR = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]

# ---------------------------------------------------------------------------------------------- data
raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "high", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
extra = pd.read_parquet(HERE / "data" / "etf_extra.parquet", columns=["symbol", "date", "open", "high", "close", "volume"])
raw = pd.concat([raw, extra[~extra.symbol.isin(raw.symbol.unique())]], ignore_index=True)
meta = pd.read_csv(W3 / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"]) | set(extra.symbol.unique())


def wide(col):
    return raw.pivot(index="date", columns="symbol", values=col).sort_index()


C = wide("close"); O = wide("open"); H = wide("high"); V = wide("volume")
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
col = {s: i for i, s in enumerate(syms)}
T, NS = C.shape
print("matrix", T, NS, flush=True)
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))

Cn, On = C.to_numpy(), O.to_numpy()
prevC = np.vstack([np.full(NS, np.nan), Cn[:-1]])
R_cc = np.nan_to_num(Cn / prevC - 1)
R_co = np.nan_to_num(On / prevC - 1)
R_oc = np.nan_to_num(Cn / On - 1)
for R in (R_cc, R_co, R_oc):
    R[locked] = 0.0                                   # locked block: no outcome enters any simulation
COST_O = 0.01 / On + 0.0001                           # per traded $ at the open (NaN = no open -> cannot trade)
caldays = np.r_[1, np.diff(dates.values).astype("timedelta64[D]").astype(int)]

# ---------------------------------------------------------------------------------------------- features (inputs)
is_etf = np.array([s in etf for s in syms])
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]
first_bar = C.notna().idxmax()
COHORT = np.asarray(first_bar.values == dates[0])
print("eligible per day median", np.median(ELIG[252:].sum(1)), flush=True)

ret = C.pct_change(fill_method=None)
lr = np.log(C / C.shift(1))
m = lr["SPY"]
var_m = m.rolling(252, min_periods=200).var()
cov_rm = lr.rolling(252, min_periods=200).cov(pd.DataFrame({s: m for s in C.columns}), pairwise=False)
var_r = lr.rolling(252, min_periods=200).var()
beta252 = cov_rm.div(var_m, axis=0)
resid_sd = np.sqrt((var_r - beta252.pow(2).mul(var_m, axis=0)).clip(lower=1e-10))
del cov_rm


def resmom(n):  # formation window [t-n+1, t-21]
    w = n - 21
    sr = lr.rolling(w, min_periods=int(w * 0.8)).sum().shift(21)
    sm = m.rolling(w, min_periods=int(w * 0.8)).sum().shift(21)
    return ((sr - beta252.mul(sm, axis=0)) / resid_sd).to_numpy()


FEAT = {
    "mom12_1": (C.shift(21) / C.shift(252) - 1).to_numpy(),
    "mom6_1": (C.shift(21) / C.shift(126) - 1).to_numpy(),
    "res12_1": resmom(252),
    "res6_1": resmom(126),
    "h52": (C / H.rolling(252, min_periods=200).max()).to_numpy(),
    "lowvol63": -ret.rolling(63, min_periods=50).std().to_numpy(),
    "lowvol252": -ret.rolling(252, min_periods=200).std().to_numpy(),
    "lowbeta": -beta252.to_numpy(),
}
RET21 = (C / C.shift(21) - 1).to_numpy()
VOL63 = ret.rolling(63, min_periods=50).std().to_numpy()
del lr, var_r, resid_sd, beta252, ret

dser = pd.Series(np.arange(T), index=dates)
MONTH_END = dser.groupby([dates.year, dates.month]).max().to_numpy()
iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
REB = {"M": MONTH_END, "W": WEEK_END}


# ---------------------------------------------------------------------------------------------- simulator
def simulate(targets: dict[int, np.ndarray]):
    """targets: {signal row t: weight vector (len NS, sums to 1 long-only or 0 long-short)}; executed at open t+1.
    Returns daily net return, turnover (one-way, fraction of equity), cost (fraction of equity)."""
    h = np.zeros(NS); cash = 1.0; E_prev = 1.0
    out_r = np.zeros(T); out_to = np.zeros(T); out_c = np.zeros(T)
    started = False
    for d in range(1, T):
        w = targets.get(d - 1)
        if w is not None:
            started = True
            h *= 1 + R_co[d]
            E = cash + h.sum()
            tgt = w * E
            co = COST_O[d]
            bad = np.isnan(co)
            if bad.any():                          # cannot trade a name without an open print: keep it as is
                tgt = np.where(bad, h, tgt)
            trade = tgt - h
            cost = np.nansum(np.abs(trade) * co)
            cash -= trade.sum() + cost
            h = tgt * (1 + R_oc[d])
            out_to[d] = np.abs(trade).sum() / 2 / E
            out_c[d] = cost / E_prev
        elif started:
            h *= 1 + R_cc[d]
        if started:
            short = -h[h < 0].sum()
            if short > 0 and not locked[d]:
                cash -= BORROW / 365 * caldays[d] * short
            E = cash + h.sum()
            out_r[d] = E / E_prev - 1
            E_prev = E
    return out_r, out_to, out_c


# ---------------------------------------------------------------------------------------------- target builders
def stock_targets(feat, n, reb, side="long", filt_rev=False, cohort=False):
    F = FEAT[feat]
    out = {}
    for t in REB[reb]:
        if t < 252 or t >= T - 1:
            continue
        ok = ELIG[t] & ~np.isnan(F[t])
        if cohort:
            ok &= COHORT
        if filt_rev:
            r21 = RET21[t]
            okr = ok & ~np.isnan(r21)
            if okr.sum() > 10:
                ok &= ~(r21 >= np.nanquantile(r21[okr], 0.9))
        idx = np.flatnonzero(ok)
        if len(idx) < 2 * n:
            continue
        order = idx[np.argsort(-F[t, idx], kind="stable")]
        w = np.zeros(NS)
        w[order[:n]] = 1.0 / n
        if side == "ls":
            w[order[-n:]] = -1.0 / n
        out[t] = w
    return out


def ew_universe_targets(cohort=False):
    out = {}
    for t in MONTH_END:
        if t < 252 or t >= T - 1:
            continue
        ok = ELIG[t] & (COHORT if cohort else True)
        w = np.zeros(NS)
        w[ok] = 1.0 / ok.sum()
        out[t] = w
    return out


def bh_targets(names, weights=None):
    out = {}
    for t in MONTH_END:
        if t < 252 or t >= T - 1:
            continue
        avail = [s for s in names if not np.isnan(Cn[t, col[s]])]
        w = np.zeros(NS)
        for s in avail:
            w[col[s]] = 1.0 / len(avail) if weights is None else weights[s]
        out[t] = w
    return out


ME_C = C.iloc[MONTH_END]                                  # month-end closes (ETF signals)
ME_ROW = {t: i for i, t in enumerate(MONTH_END)}


def kret(sym, t, k):
    i = ME_ROW[t]
    if i - k < 0:
        return np.nan
    return ME_C[sym].iloc[i] / ME_C[sym].iloc[i - k] - 1


def etf_targets(rule, universe, k=None, weighting="eq"):
    out = {}
    bil = col["BIL"]
    for t in MONTH_END:
        if t < 252 or t >= T - 1:
            continue
        i = ME_ROW[t]
        w = np.zeros(NS)
        avail = [s for s in universe if not np.isnan(Cn[t, col[s]]) and ME_C[s].iloc[: i + 1].notna().sum() > (k or 0)]
        if rule == "faber":
            for s in avail:
                sma = ME_C[s].iloc[max(0, i - k + 1): i + 1].mean()
                w[col[s] if Cn[t, col[s]] > sma else bil] += 1.0 / len(avail)
        elif rule == "gem":
            rs = {s: kret(s, t, k) for s in universe}
            best = max(rs, key=lambda s: rs[s])
            w[col[best] if rs[best] > kret("BIL", t, k) else col["AGG"]] = 1.0
        elif rule == "relmom":
            rs = {s: kret(s, t, k) for s in avail}
            rb = kret("BIL", t, k)
            for s in sorted(rs, key=lambda s: -rs[s])[:3]:
                w[col[s] if rs[s] > rb else bil] += 1.0 / 3
        elif rule == "tsmom":
            rb = kret("BIL", t, k)
            iv = {s: 1 / VOL63[t, col[s]] for s in avail}
            tot = sum(iv.values())
            for s in avail:
                ws = 1.0 / len(avail) if weighting == "eq" else iv[s] / tot
                w[col[s] if kret(s, t, k) > rb else bil] += ws
        elif rule == "rp":
            iv = {s: 1 / VOL63[t, col[s]] for s in avail}
            tot = sum(iv.values())
            for s in avail:
                w[col[s]] = iv[s] / tot
        out[t] = w
    return out


BIL_R = R_cc[:, col["BIL"]]


def vol_overlay(base_r, base_to, base_c, target):
    """Weekly s = min(1, target / realised vol over the last 63 non-locked sessions), applied from the next session."""
    r = np.zeros(T); to = np.zeros(T); c = np.zeros(T)
    s = 1.0
    open_days = np.flatnonzero(~locked)
    week_end = set(WEEK_END.tolist())
    pending = None
    started = False
    for d in range(1, T):
        if pending is not None:
            ds = abs(pending - s)
            s = pending
            pending = None
            c[d] += ds * 0.0002
            to[d] += ds / 2
        if base_r[d] != 0 or base_to[d] != 0:
            started = True
        if started:
            r[d] = s * base_r[d] + (1 - s) * BIL_R[d] - c[d]
            to[d] += s * base_to[d]
            c[d] += s * base_c[d]
        if d in week_end and started:
            hist = open_days[open_days <= d][-63:]
            hist = hist[base_r[hist] != 0]
            if len(hist) >= 40:
                vol = base_r[hist].std() * math.sqrt(252)
                pending = min(1.0, target / vol) if vol > 0 else 1.0
    return r, to, c


# ---------------------------------------------------------------------------------------------- grid
CONFIGS: list[dict] = []


def add(cid, fam, bench, params, fn):
    CONFIGS.append({"id": cid, "family": fam, "bench": bench, "params": params, "fn": fn})


for fam, feats in [("S1", ["mom12_1", "mom6_1"]), ("S2", ["res12_1", "res6_1"]), ("S3", ["h52"]),
                   ("S4", ["lowvol63", "lowvol252"]), ("S5", ["lowbeta"])]:
    for f in feats:
        for n in (10, 20, 50):
            for reb in ("M", "W"):
                add(f"{fam}_{f}_N{n}_{reb}", fam, "BENCH_EW", {"feat": f, "N": n, "reb": reb},
                    lambda f=f, n=n, reb=reb, **kw: stock_targets(f, n, reb, **kw))
for n in (10, 20, 50):
    for reb in ("M", "W"):
        add(f"S6_mom12_1rev_N{n}_{reb}", "S6", "BENCH_EW", {"feat": "mom12_1", "N": n, "reb": reb},
            lambda n=n, reb=reb, **kw: stock_targets("mom12_1", n, reb, filt_rev=True, **kw))
for fam, feats in [("L1", ["mom12_1", "mom6_1"]), ("L2", ["res12_1", "res6_1"]), ("L3", ["h52"]),
                   ("L4", ["lowvol252"]), ("L5", ["lowbeta"])]:
    for f in feats:
        for n in (20, 50):
            add(f"{fam}_{f}_N{n}_M_LS", fam, "CASH", {"feat": f, "N": n},
                lambda f=f, n=n: stock_targets(f, n, "M", side="ls"))
for uni_name, uni, bench in [("SPY", ["SPY"], "BH_SPY"), ("Erisk", E_RISK, "ERISK"), ("Esector", E_SECTOR, "ESECTOR")]:
    for k in (6, 10, 12):
        add(f"E1_faber{k}_{uni_name}", "E1", bench, {"uni": uni_name, "k": k}, lambda uni=uni, k=k: etf_targets("faber", uni, k))
for setname, rs in [("SPY_EFA", ["SPY", "EFA"]), ("SPY_QQQ_IWM_EFA", ["SPY", "QQQ", "IWM", "EFA"])]:
    for k in (6, 12):
        add(f"E2_gem{k}_{setname}", "E2", "BH_SPY", {"set": setname, "k": k}, lambda rs=rs, k=k: etf_targets("gem", rs, k))
for uni_name, uni, bench in [("Erisk", E_RISK, "ERISK"), ("Esector", E_SECTOR, "ESECTOR")]:
    for k in (3, 6, 12):
        add(f"E3_relmom{k}_top3_{uni_name}", "E3", bench, {"uni": uni_name, "k": k},
            lambda uni=uni, k=k: etf_targets("relmom", uni, k))
for k in (3, 6, 12):
    for wt in ("eq", "iv"):
        add(f"E4_tsmom{k}_{wt}_Erisk", "E4", "ERISK", {"k": k, "wt": wt}, lambda k=k, wt=wt: etf_targets("tsmom", E_RISK, k, wt))
add("E5_rp_Erisk", "E5", "ERISK", {"uni": "Erisk"}, lambda: etf_targets("rp", E_RISK))
add("E5_rp_SPY_TLT_GLD", "E5", "ERISK", {"uni": "STG"}, lambda: etf_targets("rp", ["SPY", "TLT", "GLD"]))
V_BASES = {"SPY": "BH_SPY", "EW": "BENCH_EW", "S1mom": "S1_mom12_1_N20_M", "S3h52": "S3_h52_N20_M",
           "S4lv": "S4_lowvol252_N50_M"}
for bname, bid in V_BASES.items():
    for tg in (10, 15):
        add(f"V_{bname}_vt{tg}", "V", bid, {"base": bname, "tg": tg}, None)
assert len(CONFIGS) == N_TOTAL, len(CONFIGS)

# ---------------------------------------------------------------------------------------------- run
SER: dict[str, tuple] = {}
CACHE = HERE / "data" / "sim_cache.npz"     # git-ignored; delete to re-simulate
if CACHE.exists():
    z = np.load(CACHE)
    SER = {k: tuple(z[k]) for k in z.files}
    print("loaded", len(SER), "simulations from cache", flush=True)
else:
    print("benchmarks", flush=True)
    SER["BH_SPY"] = simulate(bh_targets(["SPY"]))
    SER["BENCH_EW"] = simulate(ew_universe_targets())
    SER["BENCH_EW_cohort2016"] = simulate(ew_universe_targets(cohort=True))
    SER["ERISK"] = simulate(bh_targets(E_RISK))
    SER["ESECTOR"] = simulate(bh_targets(E_SECTOR))
    for s in ("RSP", "MTUM", "USMV", "QUAL", "BIL", "SPLV"):
        SER[f"BH_{s}"] = simulate(bh_targets([s]))
    SER["CASH"] = (np.zeros(T), np.zeros(T), np.zeros(T))
    for i, c in enumerate(CONFIGS):
        if c["family"] == "V":
            continue
        SER[c["id"]] = simulate(c["fn"]())
        if c["family"].startswith("S"):
            SER[c["id"] + "__cohort2016"] = simulate(c["fn"](cohort=True))
        print(i, c["id"], flush=True)
    np.savez(CACHE, **{k: np.vstack(v) for k, v in SER.items()})
for c in CONFIGS:
    if c["family"] == "V":
        SER[c["id"]] = vol_overlay(*SER[c["bench"]], c["params"]["tg"] / 100)
BENCH_OF = {c["id"]: c["bench"] for c in CONFIGS}
BENCH_OF.update({c["id"] + "__cohort2016": "BENCH_EW_cohort2016" for c in CONFIGS if c["family"].startswith("S")})

# ---------------------------------------------------------------------------------------------- statistics
spy_r = SER["BH_SPY"][0]
ew_r = SER["BENCH_EW"][0]
month_key = dates.year * 100 + dates.month
spy_month = pd.Series(spy_r).groupby(month_key).apply(lambda x: (1 + x).prod() - 1)


def period_mask(name):
    if name in SPLITS:
        a, b = SPLITS[name]
        msk = (dates >= a) & (dates <= b)
    elif name == "trval":
        msk = (dates >= SPLITS["train"][0]) & (dates <= SPLITS["valid"][1])
    elif name == "all":
        msk = dates >= SPLITS["train"][0]
    else:
        y = int(name[1:])
        msk = (dates.year == y) & (dates >= SPLITS["train"][0])
    return np.asarray(msk) & ~locked


def mdd(r):
    eq = np.cumprod(1 + r)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def stats(cid, period):
    r, to, c = SER[cid]
    b = SER[BENCH_OF.get(cid, "CASH")][0]
    msk = period_mask(period)
    rr, bb = r[msk], b[msk]
    n = len(rr)
    yrs = n / 252
    mk = month_key[msk]
    mr = pd.Series(rr).groupby(mk).apply(lambda x: (1 + x).prod() - 1)
    mb = pd.Series(bb).groupby(mk).apply(lambda x: (1 + x).prod() - 1)
    act = mr - mb
    sd = rr.std()
    sdb = bb.std()
    spy = spy_r[msk]
    beta = float(np.cov(rr, spy)[0, 1] / spy.var()) if spy.var() > 0 else np.nan
    sm = spy_month.reindex(act.index)
    return {
        "id": cid, "period": period, "days": n, "months": len(mr),
        "cagr": float(np.prod(1 + rr) ** (1 / yrs) - 1) if yrs > 0 else np.nan,
        "vol": float(sd * math.sqrt(252)), "sharpe": float(rr.mean() / sd * math.sqrt(252)) if sd > 0 else np.nan,
        "bench_sharpe": float(bb.mean() / sdb * math.sqrt(252)) if sdb > 0 else 0.0,
        "maxdd": mdd(rr), "bench_maxdd": mdd(bb),
        "turnover_yr": float(to[msk].sum() / yrs), "cost_drag_yr": float(c[msk].sum() / yrs),
        "hit_month": float((mr > 0).mean()), "hit_vs_bench": float((act > 0).mean()),
        "excess_spy": float((rr.mean() - spy.mean()) * 252), "excess_ew": float((rr.mean() - ew_r[msk].mean()) * 252),
        "active": float((rr.mean() - bb.mean()) * 252),
        "active_t": float(act.mean() / act.std() * math.sqrt(len(act))) if len(act) > 2 and act.std() > 0 else np.nan,
        "active_up_months": float(act[sm > 0].mean() * 12), "active_down_months": float(act[sm <= 0].mean() * 12),
        "beta_spy": beta, "spy_ret": float(np.prod(1 + spy) - 1), "ret": float(np.prod(1 + rr) - 1),
    }


PERIODS = ["train", "valid", "valid2", "trval", "all"] + [f"Y{y}" for y in range(2017, 2027)]
rows = []
for cid in SER:
    if cid == "CASH":
        continue
    for p in PERIODS:
        rows.append(stats(cid, p))
res = pd.DataFrame(rows)


# deflated Sharpe (Bailey & Lopez de Prado 2014), train+valid daily returns, N = 105 trials
def dsr_all(kind):
    tv = period_mask("trval")
    srs, info = {}, {}
    for c in CONFIGS:
        r = SER[c["id"]][0][tv]
        if kind == "active":
            r = r - SER[c["bench"]][0][tv]
        sr = r.mean() / r.std() if r.std() > 0 else 0.0
        z = (r - r.mean()) / r.std() if r.std() > 0 else r * 0
        srs[c["id"]] = sr
        info[c["id"]] = (float((z ** 3).mean()), float((z ** 4).mean()), len(r))
    v = np.var(list(srs.values()), ddof=1)
    g = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - g) * norm.ppf(1 - 1 / N_TOTAL) + g * norm.ppf(1 - 1 / (N_TOTAL * math.e)))
    out = {}
    for k, sr in srs.items():
        sk, ku, n = info[k]
        den = math.sqrt(max(1e-12, 1 - sk * sr + (ku - 1) / 4 * sr ** 2))
        out[k] = float(norm.cdf((sr - sr0) * math.sqrt(n - 1) / den))
    return out, sr0 * math.sqrt(252)


DSR_ABS, SR0_ABS = dsr_all("abs")
DSR_ACT, SR0_ACT = dsr_all("active")

# ---------------------------------------------------------------------------------------------- gates
STEPS = {"N": [10, 20, 50], "reb": ["M", "W"], "k": [3, 6, 10, 12], "tg": [10, 15], "wt": ["eq", "iv"]}
FEAT_NB = {"mom12_1": "mom6_1", "mom6_1": "mom12_1", "res12_1": "res6_1", "res6_1": "res12_1",
           "lowvol63": "lowvol252", "lowvol252": "lowvol63"}


def neighbours(c):
    out = []
    for o in CONFIGS:
        if o["family"] != c["family"] or o["id"] == c["id"]:
            continue
        diff = [k for k in c["params"] if c["params"][k] != o["params"].get(k)]
        if len(diff) != 1:
            continue
        k = diff[0]
        a, b = c["params"][k], o["params"][k]
        if k == "feat":
            ok = FEAT_NB.get(a) == b
        elif k in STEPS:
            vals = [v for v in STEPS[k] if any(x["family"] == c["family"] and x["params"].get(k) == v for x in CONFIGS)]
            ok = abs(vals.index(a) - vals.index(b)) == 1
        else:
            ok = False                      # universe / set / base: not an ordered parameter
        if ok:
            out.append(o["id"])
    return out


R = res.set_index(["id", "period"])
g_rows = []
for c in CONFIGS:
    cid = c["id"]
    g = lambda p, k: R.loc[(cid, p), k]  # noqa: E731
    act = [g(p, "active") for p in SPLITS]
    sh = [g(p, "sharpe") for p in SPLITS]
    bsh = [g(p, "bench_sharpe") for p in SPLITS]
    nb = neighbours(c)
    nb_act = float(np.mean([R.loc[(o, "trval"), "active"] for o in nb])) if nb else np.nan
    nb_sh = float(np.mean([R.loc[(o, "trval"), "sharpe"] - R.loc[(o, "trval"), "bench_sharpe"] for o in nb])) if nb else np.nan
    A1 = all(a > 0 for a in act)
    A2 = g("trval", "active_t") >= T_REQ
    A3 = (not nb) or nb_act > 0
    A4 = g("all", "active_up_months") > 0 and g("all", "active_down_months") > 0
    B1 = all(s > b for s, b in zip(sh, bsh))
    B2 = g("trval", "maxdd") > g("trval", "bench_maxdd")
    B3 = DSR_ABS[cid] >= 0.95
    B4 = (not nb) or nb_sh > 0
    if A1 and A2 and A3 and A4:
        verdict = "A_edge"
    elif B1 and B2 and B3 and B4:
        verdict = "B_risk"
    elif all(s > 0 for s in sh) and sum((a > 0) or (s > b) for a, s, b in zip(act, sh, bsh)) >= 2:
        verdict = "near"
    else:
        verdict = "fail"
    g_rows.append({"id": cid, "family": c["family"], "bench": c["bench"], "verdict": verdict,
                   "A1": A1, "A2": A2, "A3": A3, "A4": A4, "B1": B1, "B2": B2, "B3": B3, "B4": B4,
                   "active_train": act[0], "active_valid": act[1], "active_valid2": act[2],
                   "active_t_trval": g("trval", "active_t"), "sharpe_train": sh[0], "sharpe_valid": sh[1],
                   "sharpe_valid2": sh[2], "bench_sharpe_train": bsh[0], "bench_sharpe_valid": bsh[1],
                   "bench_sharpe_valid2": bsh[2], "cagr_trval": g("trval", "cagr"), "maxdd_trval": g("trval", "maxdd"),
                   "bench_maxdd_trval": g("trval", "bench_maxdd"), "turnover_trval": g("trval", "turnover_yr"),
                   "cost_drag_trval": g("trval", "cost_drag_yr"), "dsr_abs": DSR_ABS[cid], "dsr_active": DSR_ACT[cid],
                   "neighbours": ";".join(nb), "nb_active_trval": nb_act, "nb_sharpe_diff_trval": nb_sh,
                   "active_up_months_all": g("all", "active_up_months"),
                   "active_down_months_all": g("all", "active_down_months")})
gates = pd.DataFrame(g_rows)
gates.to_csv(HERE / "gates.csv", index=False, float_format="%.4f")
res["verdict"] = res["id"].map(gates.set_index("id")["verdict"]).fillna("benchmark/diagnostic")
res.to_csv(HERE / "results.csv", index=False, float_format="%.5f")
pd.DataFrame({k: v[0] for k, v in SER.items()}, index=dates).astype("float32").to_parquet(HERE / "data" / "daily_returns.parquet")
print("SR0 abs", SR0_ABS, "SR0 act", SR0_ACT)
print(gates.verdict.value_counts())
print(gates.groupby(["family", "verdict"]).size().unstack(fill_value=0))
