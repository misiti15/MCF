"""S6 protection study (PLAN.md, pre-declared 2026-10-14): per-name stops (A), book-level overlays (B), breadth and
sector cap (C), stress windows (D) and a 2008 factor proxy, all on S6_mom12_1rev_N20_W.

Data block copied from research/longhold/study.py (same file, eligibility, features, costs, locked-block zeroing); the
study module itself is not imported (it rewrites its own outputs). Every return inside 2024-11-01..2025-02-28 is 0
and those days are dropped from every statistic. Educational only - not financial advice.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LH = HERE.parent
ROOT = LH.parents[1]
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "_scratch"
SCR.mkdir(parents=True, exist_ok=True)

LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
SPLITS = {"train": ("2017-01-01", "2020-12-31"), "valid": ("2021-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
E_SECTOR = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
STOP_SLIP = 0.0005
BIL_COST = 0.0001

# ---------------------------------------------------------------------------------------------- data (study.py copy)
raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "high", "low", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
extra = pd.read_parquet(LH / "data" / "etf_extra.parquet", columns=["symbol", "date", "open", "high", "close", "volume"])
raw = pd.concat([raw, extra[~extra.symbol.isin(raw.symbol.unique())]], ignore_index=True)
meta = pd.read_csv(W3 / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"]) | set(extra.symbol.unique())


def wide(c):
    return raw.pivot(index="date", columns="symbol", values=c).sort_index()


C = wide("close"); O = wide("open"); V = wide("volume"); L = wide("low")
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
col = {s: i for i, s in enumerate(syms)}
T, NS = C.shape
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))
Cn, On, Ln = C.to_numpy(), O.to_numpy(), L.to_numpy()
prevC = np.vstack([np.full(NS, np.nan), Cn[:-1]])
R_cc = np.nan_to_num(Cn / prevC - 1)
R_co = np.nan_to_num(On / prevC - 1)
R_oc = np.nan_to_num(Cn / On - 1)
R_lo = np.nan_to_num(Ln / prevC - 1)        # low vs previous close (intraday stop check)
for R in (R_cc, R_co, R_oc, R_lo):
    R[locked] = 0.0                           # locked block: no outcome enters any simulation
COST_O = 0.01 / On + 0.0001
is_etf = np.array([s in etf for s in syms])
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]
MOM = (C.shift(21) / C.shift(252) - 1).to_numpy()
RET21 = (C / C.shift(21) - 1).to_numpy()
RET = C.pct_change(fill_method=None).to_numpy()   # real daily returns: feature input (sector map), study convention
dser = pd.Series(np.arange(T), index=dates)
MONTH_END = dser.groupby([dates.year, dates.month]).max().to_numpy()
iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
WEEK_SET = set(WEEK_END.tolist()); MONTH_SET = set(MONTH_END.tolist())
BIL_R = R_cc[:, col["BIL"]]
# return index per name (locked block flat), open and low index
PI = np.cumprod(1 + R_cc, axis=0)
PIprev = np.vstack([np.ones(NS), PI[:-1]])
PO = PIprev * (1 + R_co)
PL = np.minimum(np.minimum(PIprev * (1 + np.where(np.isnan(Ln), np.inf, R_lo)), PO), PI)
PL[np.isnan(Ln) | locked[:, None]] = np.inf
print("matrix", T, NS, flush=True)

# ---------------------------------------------------------------------------------------------- rankings
RANK = {}
for t in WEEK_END:
    if t < 252 or t >= T - 1:
        continue
    ok = ELIG[t] & ~np.isnan(MOM[t])
    r21 = RET21[t]
    okr = ok & ~np.isnan(r21)
    if okr.sum() > 10:
        ok &= ~(r21 >= np.nanquantile(r21[okr], 0.9))
    idx = np.flatnonzero(ok)
    RANK[t] = idx[np.argsort(-MOM[t, idx], kind="stable")]

# statistical point-in-time sector (PLAN 2): residual-return correlation with SPDR sector ETFs, 252 sessions
SEC_IDX = [col[s] for s in E_SECTOR]
spy_i = col["SPY"]
SECTOR = {}


def _resid(X, m):
    Xc = X - np.nanmean(X, 0); mc = m - m.mean()
    b = np.nansum(Xc * mc[:, None], 0) / (mc ** 2).sum()
    return Xc - b * mc[:, None]


for t, order in RANK.items():
    w = slice(t - 251, t + 1)
    m = np.nan_to_num(RET[w, spy_i])
    cand = order[:150]
    S = RET[w][:, SEC_IDX]
    okS = (~np.isnan(S)).sum(0) >= 200
    Sr = np.nan_to_num(_resid(np.where(np.isnan(S), np.nan, S), m))
    Xr = np.nan_to_num(_resid(RET[w][:, cand], m))
    num = Xr.T @ Sr
    den = np.sqrt((Xr ** 2).sum(0))[:, None] * np.sqrt((Sr ** 2).sum(0))[None, :] + 1e-12
    cor = np.where(okS[None, :], num / den, -9)
    SECTOR[t] = dict(zip(cand.tolist(), np.argmax(cor, 1).tolist()))


def pick(t, n, cap=None, barred=None):
    order = RANK.get(t)
    if order is None or len(order) < 2 * n:
        return None
    sel, cnt = [], {}
    for i in order:
        if barred is not None and barred[i]:
            continue
        if cap is not None:
            s = SECTOR[t].get(int(i), -1)
            if cnt.get(s, 0) >= cap:
                continue
            cnt[s] = cnt.get(s, 0) + 1
        sel.append(i)
        if len(sel) == n:
            break
    return np.array(sel)


# ---------------------------------------------------------------------------------------------- simulator
def level(rule, ent, peak):
    if rule is None:
        return np.full(NS, -np.inf)
    kind = rule[0]
    if kind == "fix":
        return ent * (1 - rule[1])
    if kind == "trail":
        return peak * (1 - rule[1])
    _, P, mode, X = rule                          # lock
    act = peak >= ent * (1 + P)
    lv = {"trail": peak * (1 - (X or 0)), "be": ent, "p10": ent * 1.10}[mode]
    return np.where(act, lv, -np.inf)


def sim(n=20, cap=None, rule=None, trig="C", reent="cash"):
    """Weekly S6 with optional per-name stops. Returns dict of daily arrays + exit records."""
    h = np.zeros(NS); cash = 1.0; bil = 0.0; E_prev = 1.0
    ent = np.full(NS, np.nan); peak = np.full(NS, np.nan)
    flag = np.zeros(NS, bool); barred = np.zeros(NS, bool)
    r = np.zeros(T); r_on = np.zeros(T); to = np.zeros(T); cst = np.zeros(T); traded = 0.0
    exits = []
    started = False
    with np.errstate(invalid="ignore"):
        for d in range(1, T):
            tsig = d - 1 in RANK
            sel = None
            if tsig:
                bar = barred | flag if reent == "repl" else None
                sel = pick(d - 1, n, cap, bar)
            if sel is not None:
                started = True
                bil *= 1 + BIL_R[d]
                r_on[d] = (h * R_co[d]).sum() / E_prev
                h *= 1 + R_co[d]
                E = cash + bil + h.sum()
                w = np.zeros(NS); w[sel] = 1.0 / n
                tgt = w * E
                co = COST_O[d]
                bad = np.isnan(co)
                if bad.any():
                    tgt = np.where(bad, h, tgt)
                trade = tgt - h
                cost = np.nansum(np.abs(trade) * co) + bil * BIL_COST
                traded += np.abs(trade).sum()
                cash += bil - trade.sum() - cost
                bil = 0.0
                new = (h <= 0) & (tgt > 0)
                ent[new] = PO[d, new]; peak[new] = PO[d, new]
                gone = tgt <= 0
                ent[gone] = np.nan; peak[gone] = np.nan
                h = tgt * (1 + R_oc[d])
                to[d] = np.abs(trade).sum() / 2 / E
                cst[d] = cost / E_prev
                flag[:] = False; barred[:] = False
                if trig == "L" and rule is not None and not locked[d]:
                    lv = level(rule, ent, peak)
                    hit = (h > 0) & (PL[d] <= lv)
                    if hit.any():
                        fill = np.minimum(PO[d], lv)
                        for i in np.flatnonzero(hit):
                            val = h[i] / (1 + R_oc[d, i]) * fill[i] / PO[d, i]
                            px = Cn[d - 1, i] * fill[i] / PIprev[d, i]
                            c = val * (0.01 / px + 0.0001 + STOP_SLIP)
                            bil += val - c; cst[d] += c / E_prev; to[d] += val / 2 / E; traded += val
                            exits.append((d, i, fill[i]))
                            h[i] = 0.0; ent[i] = np.nan; peak[i] = np.nan; barred[i] = True
            elif started:
                bil *= 1 + BIL_R[d]
                r_on[d] = (h * R_co[d]).sum() / E_prev
                E0 = E_prev
                if flag.any():
                    co = COST_O[d]
                    fl = flag & ~np.isnan(co)
                    for i in np.flatnonzero(fl):
                        val = h[i] * (1 + R_co[d, i])
                        c = val * co[i]
                        bil += val - c; cst[d] += c / E0; to[d] += val / 2 / E0; traded += val
                        exits.append((d, i, PO[d, i]))
                        h[i] = 0.0; ent[i] = np.nan; peak[i] = np.nan; barred[i] = True
                    flag &= ~fl
                if trig == "L" and rule is not None and not locked[d]:
                    lv = level(rule, ent, peak)
                    hit = (h > 0) & (PL[d] <= lv)
                    if hit.any():
                        fill = np.minimum(PO[d], lv)
                        for i in np.flatnonzero(hit):
                            val = h[i] * fill[i] / PIprev[d, i]
                            px = Cn[d - 1, i] * fill[i] / PIprev[d, i]
                            c = val * (0.01 / px + 0.0001 + STOP_SLIP)
                            bil += val - c; cst[d] += c / E0; to[d] += val / 2 / E0; traded += val
                            exits.append((d, i, fill[i]))
                            h[i] = 0.0; ent[i] = np.nan; peak[i] = np.nan; barred[i] = True
                h *= 1 + R_cc[d]
            if started:
                held = h > 0
                peak[held] = np.fmax(peak[held], PI[d, held])
                if rule is not None and trig == "C" and not locked[d]:
                    lv = level(rule, ent, peak)
                    flag = held & (PI[d] <= lv)
                E = cash + bil + h.sum()
                r[d] = E / E_prev - 1
                E_prev = E
    return {"r": r, "r_on": r_on, "to": to, "c": cst, "exits": exits, "cpu": float(cst.sum() / max(2 * to.sum(), 1e-9))}


# ---------------------------------------------------------------------------------------------- overlays (B)
def overlay(base_r, base_on, base_to, base_c, cpu, kind, p, spy_c, sma, week_set, month_set, bil_r, lockd,
            month_c=None):
    """Exposure s in [0,1] on the base, rest in bil_r. Decision at close d, applied from the next open
    (overnight part of day d+1 at the old s, open-to-close part at the new s)."""
    n = len(base_r)
    r = np.zeros(n); to = np.zeros(n); c = np.zeros(n); S = np.ones(n)
    r_id = (1 + base_r) / (1 + base_on) - 1
    s = 1.0; pend = None; Eo = 1.0; hwm = 1.0; exit_d = -10 ** 9; started = False
    open_idx = np.flatnonzero(~lockd)
    for d in range(1, n):
        s_new = pend if pend is not None else s
        pend = None
        if base_r[d] != 0 or base_to[d] != 0:
            started = True
        ds = abs(s_new - s)
        r[d] = s * base_on[d] + s_new * r_id[d] + (1 - s_new) * bil_r[d] - ds * cpu
        to[d] = s_new * base_to[d] + ds / 2
        c[d] = s_new * base_c[d] + ds * cpu
        if s_new > s and kind == "dd":
            hwm = Eo * (1 + r[d])               # reset the high-water mark at re-entry
        s = s_new
        S[d] = s
        Eo *= 1 + r[d]
        if not started or lockd[d]:
            continue
        if kind == "dd":
            X, re = p
            if s == 1.0:
                hwm = max(hwm, Eo)
                if Eo / hwm - 1 <= -X:
                    pend = 0.0; exit_d = d
            elif d in week_set:
                ok = {"4w": d - exit_d >= 20, "8w": d - exit_d >= 40,
                      "s50": spy_c[d] > sma[50][d], "s200": spy_c[d] > sma[200][d]}[re]
                if ok:
                    pend = 1.0
        elif kind == "trend":
            if p == "d200":
                pend = 1.0 if spy_c[d] > sma[200][d] else 0.0
            elif p in ("w200", "w200_half") and d in week_set:
                pend = 1.0 if spy_c[d] > sma[200][d] else (0.5 if p == "w200_half" else 0.0)
            elif p == "m10" and d in month_set:
                pend = 1.0 if month_c[d] > 0 else 0.0
        elif kind == "vt":
            tg, daily = p
            if daily or d in week_set:
                hist = open_idx[open_idx <= d][-20:]
                v = base_r[hist].std() * math.sqrt(252)
                pend = min(1.0, tg / v) if v > 0 else 1.0
        if pend is not None and pend == s:
            pend = None
    return {"r": r, "to": to, "c": c, "s": S}


spy_c = Cn[:, spy_i]
SMA = {k: pd.Series(spy_c).rolling(k, min_periods=k).mean().to_numpy() for k in (50, 200)}
_me = pd.Series(spy_c[MONTH_END], index=MONTH_END)
_m10 = (_me - _me.rolling(10, min_periods=10).mean())
M10 = np.full(T, np.nan); M10[MONTH_END] = _m10.to_numpy()

# ---------------------------------------------------------------------------------------------- grid
CONF = []          # (id, block, params)
RULES = [("fix", x) for x in (0.10, 0.15, 0.20, 0.25, 0.30)] + [("trail", x) for x in (0.10, 0.15, 0.20, 0.25)]
for P in (0.20, 0.30, 0.50):
    RULES += [("lock", P, "trail", x) for x in (0.10, 0.15, 0.20)] + [("lock", P, "be", None), ("lock", P, "p10", None)]


def rname(rule):
    if rule[0] in ("fix", "trail"):
        return f"{rule[0]}{int(rule[1] * 100)}"
    return f"lock{int(rule[1] * 100)}_" + (f"trail{int(rule[3] * 100)}" if rule[2] == "trail" else rule[2])


for rule in RULES:
    for trig in ("C", "L"):
        for re in ("cash", "repl"):
            CONF.append((f"A_{rname(rule)}_{trig}_{re}", "A", {"rule": rule, "trig": trig, "reent": re}))
for X in (0.10, 0.15, 0.20):
    for re in ("4w", "8w", "s50", "s200"):
        CONF.append((f"B_dd{int(X * 100)}_{re}", "Bdd", {"X": X, "re": re}))
for p in ("d200", "w200", "m10", "w200_half"):
    CONF.append((f"B_trend_{p}", "Btr", {"p": p}))
for tg, daily in ((0.20, False), (0.30, False), (0.40, False), (0.30, True)):
    CONF.append((f"B_vt{int(tg * 100)}_20d" + ("_daily" if daily else ""), "Bvt", {"tg": tg, "daily": daily}))
for n in (30, 40):
    CONF.append((f"C_N{n}", "C", {"n": n}))
for k in (3, 4, 5):
    CONF.append((f"C_N20_cap{k}", "C", {"n": 20, "cap": k}))
N_STUDY = len(CONF)
assert N_STUDY == 121, N_STUDY
N_LINEAGE = 105 + 7 + 18 + N_STUDY
T_BAR = math.sqrt(2 * math.log(N_LINEAGE))
print("configs", N_STUDY, "lineage", N_LINEAGE, "bar", round(T_BAR, 2), flush=True)

# ---------------------------------------------------------------------------------------------- run
SER, EXITS = {}, {}
base = sim()
ref = pd.read_parquet(LH / "data" / "daily_returns.parquet")
par = np.abs(base["r"] - ref["S6_mom12_1rev_N20_W"].to_numpy()).max()
print("parity max abs diff vs study S6:", par, flush=True)
assert par < 1e-6, par
SER["BASE_S6_N20"] = base
SER["REF_N50"] = sim(n=50)
par50 = np.abs(SER["REF_N50"]["r"] - ref["S6_mom12_1rev_N50_W"].to_numpy()).max()
print("parity N50", par50, flush=True)
EW = ref["BENCH_EW"].to_numpy()
SPY_R = ref["BH_SPY"].to_numpy()
for cid, blk, p in CONF:
    if blk == "A":
        SER[cid] = sim(rule=p["rule"], trig=p["trig"], reent=p["reent"])
    elif blk == "C":
        SER[cid] = sim(n=p["n"], cap=p.get("cap"))
    else:
        kind = {"Bdd": "dd", "Btr": "trend", "Bvt": "vt"}[blk]
        pp = (p["X"], p["re"]) if blk == "Bdd" else p["p"] if blk == "Btr" else (p["tg"], p["daily"])
        SER[cid] = overlay(base["r"], base["r_on"], base["to"], base["c"], base["cpu"] + BIL_COST, kind, pp,
                           spy_c, SMA, WEEK_SET, MONTH_SET, BIL_R, locked, M10)
    print(cid, flush=True)

# ---------------------------------------------------------------------------------------------- statistics
month_key = dates.year * 100 + dates.month


def pmask(name):
    if name in SPLITS:
        a, b = SPLITS[name]; m = (dates >= a) & (dates <= b)
    elif name == "trval":
        m = (dates >= SPLITS["train"][0]) & (dates <= SPLITS["valid"][1])
    elif name == "all":
        m = dates >= SPLITS["train"][0]
    elif name.startswith("Y"):
        y = int(name[1:]); m = (dates.year == y) & (dates >= SPLITS["train"][0])
    else:
        a, b = STRESS[name]; m = (dates >= a) & (dates <= b)
    return np.asarray(m) & ~locked


STRESS = {"Q4_2018": ("2018-10-01", "2018-12-24"), "covid_crash": ("2020-02-19", "2020-03-23"),
          "covid_crash_rebound": ("2020-02-19", "2020-06-30"), "nov2020_momrev": ("2020-11-01", "2020-11-30"),
          "y2022_H1": ("2022-01-03", "2022-06-16"), "y2022_full": ("2022-01-01", "2022-12-31"),
          "tariff_2025": ("2025-03-01", "2025-04-08")}
G4_WIN = ["Q4_2018", "covid_crash", "nov2020_momrev", "y2022_H1", "y2022_full", "tariff_2025"]


def mdd(r):
    eq = np.cumprod(1 + r)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def stats(cid, per):
    s = SER[cid]; m = pmask(per)
    rr = s["r"][m]; yrs = len(rr) / 252
    sd = rr.std()
    mr = pd.Series(rr).groupby(month_key[m]).apply(lambda x: (1 + x).prod() - 1)
    out = {"id": cid, "period": per, "days": int(m.sum()), "ret": float(np.prod(1 + rr) - 1),
           "cagr": float(np.prod(1 + rr) ** (1 / yrs) - 1) if yrs > 0.5 else np.nan,
           "vol": float(sd * math.sqrt(252)), "sharpe": float(rr.mean() / sd * math.sqrt(252)) if sd > 0 else np.nan,
           "maxdd": mdd(rr), "worst_month": float(mr.min()) if len(mr) else np.nan,
           "turnover_yr": float(s["to"][m].sum() / yrs) if yrs > 0 else np.nan,
           "cost_yr": float(s["c"][m].sum() / yrs) if yrs > 0 else np.nan,
           "active_ew": float((rr.mean() - EW[m].mean()) * 252)}
    if "s" in s:
        out["avg_exposure"] = float(s["s"][m].mean())
    return out


PERIODS = ["train", "valid", "valid2", "trval", "all"] + [f"Y{y}" for y in range(2017, 2027)] + list(STRESS)
rows = [stats(cid, p) for cid in SER for p in PERIODS]
# benchmarks for the stress table
for nm, arr in (("BENCH_EW", EW), ("BH_SPY", SPY_R)):
    SER[nm] = {"r": arr, "to": np.zeros(T), "c": np.zeros(T)}
    rows += [stats(nm, p) for p in PERIODS]
res = pd.DataFrame(rows)
res.to_csv(HERE / "results.csv", index=False, float_format="%.5f")
Rx = res.set_index(["id", "period"])

# stop diagnostics
srows = []
for cid, blk, p in CONF:
    if blk != "A":
        continue
    ex = SER[cid]["exits"]
    tv = pmask("trval"); al = pmask("all")
    prem, fwd = [], []
    for d, i, f in ex:
        if not al[d] or d + 20 >= T:
            continue
        later = PI[d + 20, i]
        prem.append(later > f); fwd.append(later / f - 1)
    yrs = al.sum() / 252
    srows.append({"id": cid, "stops": len(ex), "stops_per_yr": len(ex) / yrs,
                  "stops_per_name_yr": len(ex) / yrs / 20,
                  "premature_rate": float(np.mean(prem)) if prem else np.nan,
                  "median_fwd20_after_exit": float(np.median(fwd)) if fwd else np.nan,
                  "mean_fwd20_after_exit": float(np.mean(fwd)) if fwd else np.nan})
stops = pd.DataFrame(srows)
stops.to_csv(HERE / "stops.csv", index=False, float_format="%.4f")


# bootstrap t of the train+valid Sharpe difference (20-day blocks, 1000 draws)
def boot_t(cid, rng):
    m = pmask("trval")
    a = SER[cid]["r"][m]; b = base["r"][m]
    n = len(a); bl = 20; k = n // bl
    diffs = []
    starts_all = rng.integers(0, n - bl, size=(1000, k))
    for st in starts_all:
        ix = (st[:, None] + np.arange(bl)[None, :]).ravel()
        aa, bb = a[ix], b[ix]
        diffs.append(aa.mean() / aa.std() - bb.mean() / bb.std())
    d0 = a.mean() / a.std() - b.mean() / b.std()
    sd = np.std(diffs)
    return float(d0 * math.sqrt(252)), float(d0 / sd) if sd > 0 else np.nan


# neighbours (PLAN 5)
def neighbours(cid, blk, p):
    ids = {c[0]: c for c in CONF}
    out = []
    if blk == "A":
        rule, trig, re = p["rule"], p["trig"], p["reent"]
        alt = []
        if rule[0] in ("fix", "trail"):
            grid = [r[1] for r in RULES if r[0] == rule[0]]
            i = grid.index(rule[1])
            alt += [(rule[0], grid[j]) for j in (i - 1, i + 1) if 0 <= j < len(grid)]
        else:
            Ps = [0.20, 0.30, 0.50]; i = Ps.index(rule[1])
            alt += [("lock", Ps[j], rule[2], rule[3]) for j in (i - 1, i + 1) if 0 <= j < 3]
            if rule[2] == "trail":
                Xs = [0.10, 0.15, 0.20]; i = Xs.index(rule[3])
                alt += [("lock", rule[1], "trail", Xs[j]) for j in (i - 1, i + 1) if 0 <= j < 3]
            else:
                alt.append(("lock", rule[1], "p10" if rule[2] == "be" else "be", None))
        out = [f"A_{rname(a)}_{trig}_{re}" for a in alt]
        out.append(f"A_{rname(rule)}_{trig}_{'repl' if re == 'cash' else 'cash'}")
    elif blk == "Bdd":
        Xs = [10, 15, 20]; i = Xs.index(int(p["X"] * 100))
        out = [f"B_dd{Xs[j]}_{p['re']}" for j in (i - 1, i + 1) if 0 <= j < 3]
        pair = {"4w": "8w", "8w": "4w", "s50": "s200", "s200": "s50"}[p["re"]]
        out.append(f"B_dd{int(p['X'] * 100)}_{pair}")
    elif blk == "Btr":
        out = {"d200": ["B_trend_w200"], "w200": ["B_trend_d200", "B_trend_w200_half", "B_trend_m10"],
               "w200_half": ["B_trend_w200"], "m10": ["B_trend_w200"]}[p["p"]]
    elif blk == "Bvt":
        out = {"B_vt20_20d": ["B_vt30_20d"], "B_vt30_20d": ["B_vt20_20d", "B_vt40_20d", "B_vt30_20d_daily"],
               "B_vt40_20d": ["B_vt30_20d"], "B_vt30_20d_daily": ["B_vt30_20d"]}[cid]
    elif blk == "C":
        out = {"C_N30": ["BASE_S6_N20", "C_N40"], "C_N40": ["C_N30", "REF_N50"], "C_N20_cap3": ["C_N20_cap4"],
               "C_N20_cap4": ["C_N20_cap3", "C_N20_cap5"], "C_N20_cap5": ["C_N20_cap4"]}[cid]
    return [o for o in out if o in SER]


rng = np.random.default_rng(20261014)
B = lambda per, k: Rx.loc[("BASE_S6_N20", per), k]  # noqa: E731
grows = []
for cid, blk, p in CONF:
    g = lambda per, k: Rx.loc[(cid, per), k]  # noqa: E731
    G1 = all(g(s, "maxdd") >= B(s, "maxdd") + 0.05 for s in ("train", "valid"))
    G2 = all(g(s, "cagr") >= B(s, "cagr") - 0.03 for s in ("train", "valid"))
    G3 = all(g(s, "sharpe") >= B(s, "sharpe") for s in SPLITS)
    n_better = sum(g(w, "ret") > B(w, "ret") for w in G4_WIN)
    G4 = n_better >= 4
    nb = neighbours(cid, blk, p)
    nb_dsh = float(np.mean([Rx.loc[(o, "trval"), "sharpe"] - B("trval", "sharpe") for o in nb])) if nb else np.nan
    nb_ddd = float(np.mean([Rx.loc[(o, "trval"), "maxdd"] - B("trval", "maxdd") for o in nb])) if nb else np.nan
    G5 = bool(nb) and nb_dsh >= 0 and nb_ddd > 0
    yrs = [f"Y{y}" for y in range(2017, 2027)]
    yshare = float(np.mean([g(y, "sharpe") >= B(y, "sharpe") for y in yrs]))
    G6 = yshare >= 0.6
    dsh, bt = boot_t(cid, rng)
    row = {"id": cid, "block": blk, "G1_dd": G1, "G2_cagr": G2, "G3_sharpe": G3, "G4_stress": G4, "G5_plateau": G5,
           "G6_years": G6, "pass": G1 and G2 and G3 and G4 and G5 and G6,
           "stress_better_of_6": n_better, "year_share": yshare, "nb": ";".join(nb), "nb_dsharpe_trval": nb_dsh,
           "nb_dmaxdd_trval": nb_ddd, "dsharpe_trval": dsh, "boot_t_dsharpe": bt, "sharpe_claim": bt >= T_BAR}
    for s in ("train", "valid", "valid2", "trval"):
        row[f"cagr_{s}"] = g(s, "cagr"); row[f"sharpe_{s}"] = g(s, "sharpe"); row[f"maxdd_{s}"] = g(s, "maxdd")
    row["turnover_trval"] = g("trval", "turnover_yr"); row["worst_month_all"] = g("all", "worst_month")
    grows.append(row)
gates = pd.DataFrame(grows)
gates.to_csv(HERE / "gates.csv", index=False, float_format="%.4f")
print(gates[["G1_dd", "G2_cagr", "G3_sharpe", "G4_stress", "G5_plateau", "G6_years", "pass"]].sum())
print("passes:", gates.loc[gates["pass"], "id"].tolist())
st = res[res.period.isin(STRESS)].pivot(index="id", columns="period", values="ret")
st.to_csv(HERE / "stress.csv", float_format="%.4f")
np.savez_compressed(SCR / "series.npz", **{k: v["r"] for k, v in SER.items()}, base_on=base["r_on"],
                    dates=dates.values.astype("datetime64[D]").astype(str))
print("cpu", base["cpu"])
