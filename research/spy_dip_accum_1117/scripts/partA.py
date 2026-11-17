"""Part A: dip accumulation in SPXL / UPRO / SSO vs schedule / random / SPY-same-dates / SPY buy-and-hold.
Pre-declared in ../PLAN.md. Usage: python partA.py DAILY.parquet OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ETFS, LEV, SEG, load_daily, load_minute  # noqa: E402

E0 = 100_000.0
CPS, BPS = 0.01, 1e-4                     # $0.01/share + 1 bp per side
XS = [0.005, 0.0075, 0.01]
INSTR = ["SPXL", "UPRO", "SSO"]
EXITS = ["hold", "tp15", "tp30", "n60", "n250"]
SIZES = [0.0025, 0.005]
FAM_D = {"gap": "open", "dayclose": "close", "wkclose": "close", "wkhigh": "close"}
FAM_M = {"m_gap": 930, "m_1015": 1014, "m_1030": 1029, "m_pm1530": 1529}
NRAND = 1000
RNG = np.random.default_rng(1117)


# ------------------------------------------------------------------------------------------------- per-date outcomes
def outcomes(px_fill, close, exit_, same_day_ok):
    """For every session i: (sell index j, multiple per $ deployed after costs). j = len-1 means marked at the end."""
    n = len(close)
    sell_j = np.full(n, n - 1)
    mult = np.full(n, np.nan)
    c = close.values
    for i in range(n):
        p = px_fill[i]
        if not np.isfinite(p):
            continue
        sh = 1.0 / (p * (1 + BPS) + CPS)
        j = n - 1
        if exit_.startswith("tp"):
            y = int(exit_[2:]) / 100
            start = i if same_day_ok else i + 1
            hit = np.nonzero(c[start:] >= p * (1 + y))[0]
            if len(hit):
                j = start + hit[0]
        elif exit_.startswith("n"):
            j = min(i + int(exit_[1:]), n - 1)
        sell_j[i] = j
        mult[i] = sh * (c[j] * (1 - BPS) - CPS)
    return sell_j, mult


def xirr_many(t_buy, t_sell, mult, lo=-0.95, hi=3.0, it=70):
    """Vectorised XIRR: rows = portfolios, cols = buys (equal dollars). t in years. NPV(r) = sum(-v^tb + m v^ts)."""
    t_buy, t_sell, mult = map(np.atleast_2d, (t_buy, t_sell, mult))
    lo_a = np.full(t_buy.shape[0], lo)
    hi_a = np.full(t_buy.shape[0], hi)

    def npv(r):
        lr = np.log1p(r)[:, None]
        return np.nansum(-np.exp(-lr * t_buy) + mult * np.exp(-lr * t_sell), axis=1)
    for _ in range(it):
        mid = (lo_a + hi_a) / 2
        f = npv(mid)
        # NPV decreases in r for a net-investor stream
        lo_a = np.where(f > 0, mid, lo_a)
        hi_a = np.where(f > 0, hi_a, mid)
    return (lo_a + hi_a) / 2


# ------------------------------------------------------------------------------------------------- account simulation
def account(dates, buy_idx, sell_j, mult_px, close_sym, bil_ret, D):
    """Fixed-$ buys from a $100k account, idle cash in BIL. Returns equity series, cash share, skipped count,
    position drawdown vs cost basis."""
    n = len(dates)
    buys = {}
    for i in buy_idx:
        buys.setdefault(i, []).append(i)
    cash = E0
    sh_open = np.zeros(n + 1)       # shares bought on date i still open
    lots = []                       # (sell j, shares, cost)
    eq = np.zeros(n)
    cash_s = np.zeros(n)
    pos_dd = 0.0
    skipped = 0
    c = close_sym
    held, cost_open = 0.0, 0.0
    sells_at = {}
    for i in range(n):
        if i > 0:
            cash *= 1 + bil_ret[i]
        for (sh, cost) in sells_at.pop(i, []):
            cash += sh * (c[i] * (1 - BPS) - CPS)
            held -= sh
            cost_open -= cost
        if i in buys:
            if cash >= D:
                p = mult_px[i]
                sh = D / (p * (1 + BPS) + CPS)
                cash -= D
                held += sh
                cost_open += D
                j = sell_j[i]
                if j < n - 1 or (j == n - 1 and False):
                    sells_at.setdefault(j, []).append((sh, D))
            else:
                skipped += 1
        val = held * c[i]
        if cost_open > 0:
            pos_dd = min(pos_dd, val / cost_open - 1)
        eq[i] = cash + val
        cash_s[i] = cash / eq[i]
    return eq, cash_s.mean(), skipped, pos_dd


def dd_stats(eq):
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1
    under, best, cur = dd < -1e-9, 0, 0
    for u in under:
        cur = cur + 1 if u else 0
        best = max(best, cur)
    return dd.min(), best


def cagr(eq, dates):
    yrs = (dates[-1] - dates[0]).days / 365.25
    return (eq[-1] / eq[0]) ** (1 / yrs) - 1


# ------------------------------------------------------------------------------------------------- triggers
def daily_triggers(d, seg):
    lo, hi = SEG[seg]
    o, h, c = d["open"]["SPY"], d["high"]["SPY"], d["close"]["SPY"]
    idx = c.index[(c.index >= lo) & (c.index <= hi)]
    o, h, c = o[idx], h[idx], c[idx]
    pc = c.shift(1)
    wk = pd.Series(idx.to_period("W-FRI"), index=idx)
    wclose = c.groupby(wk).last()
    whigh = h.groupby(wk).max()
    prev_wk = wk.map(lambda p: p - 1)
    pwc = prev_wk.map(wclose)
    pwh = prev_wk.map(whigh)
    out = {}
    for x in XS:
        out[("gap", x)] = (o <= pc * (1 - x)).values
        out[("dayclose", x)] = (c <= pc * (1 - x)).values
        out[("wkclose", x)] = (c <= pwc * (1 - x)).fillna(False).values.astype(bool)
        out[("wkhigh", x)] = (c <= pwh * (1 - x)).fillna(False).values.astype(bool)
    return idx, out


def minute_fills(d, idx):
    """Per session in idx: SPY trigger price at each clock and every ETF's adjusted fill price there (NaN when no
    minute data)."""
    spy_px, fills, pcs = {}, {}, None
    for sym in ETFS:
        m = load_minute(sym)
        last = m.groupby("day").close.last()                      # raw 15:59 close
        adj = (d["close"][sym].reindex(last.index) / last)        # raw -> adjusted factor that day
        for k, hm in FAM_M.items():
            col = "open" if k == "m_gap" else "close"
            # m_gap: trigger on the 09:30 bar open, fill at the 09:30 bar close
            if k == "m_gap":
                trig = m[m.hm == 930].set_index("day").open
                fill = m[m.hm == 930].set_index("day").close
            else:
                trig = fill = m[m.hm == hm].set_index("day")[col]
            fills[(k, sym)] = (fill * adj.reindex(fill.index)).reindex(idx).values
            if sym == "SPY":
                spy_px[k] = trig.reindex(idx)
        if sym == "SPY":
            prev = last.shift(1)
            # previous close only when the previous session is the previous trading day in the data (no locked gap)
            days = last.index.to_series()
            ok = (days - days.shift(1)).dt.days <= 5
            pcs = prev.where(ok).reindex(idx)
    return spy_px, pcs, fills


# ------------------------------------------------------------------------------------------------- main
def main(daily_path, outdir):
    out = Path(outdir)
    d = load_daily(daily_path)
    rows, curves, tranche_rows = [], {}, []
    for seg in ["A", "B"]:
        idx, trig = daily_triggers(d, seg)
        n = len(idx)
        tyr = np.asarray((idx - idx[0]).days / 365.25)
        bil = d["close"]["BIL"].reindex(idx).pct_change().fillna(0).values
        closes = {s: d["close"][s].reindex(idx) for s in ETFS}
        opens = {s: d["open"][s].reindex(idx).values for s in ETFS}
        fam_fill = {"open": opens, "close": {s: closes[s].values for s in ETFS}}
        mfill, mtrig = {}, {}
        if seg == "B":
            spy_px, pcs, fills = minute_fills(d, idx)
            for k in FAM_M:
                for x in XS:
                    trig[(k, x)] = (spy_px[k] <= pcs * (1 - x)).fillna(False).values.astype(bool)
                mfill[k] = {s: fills[(k, s)] for s in ETFS}
        # precompute outcomes per (fill type, symbol, exit)
        oc = {}
        fill_types = {"open": fam_fill["open"], "close": fam_fill["close"], **mfill}
        for ft, fd in fill_types.items():
            for s in ETFS:
                for ex in EXITS:
                    oc[(ft, s, ex)] = outcomes(fd[s], closes[s], ex, same_day_ok=(ft != "close"))
        # leverage decay over all start dates
        for s in ["SPXL", "UPRO", "SSO"]:
            for h in (20, 60, 250):
                e = closes[s].pct_change(h).shift(-h)
                b = closes["SPY"].pct_change(h).shift(-h)
                diff = (e - LEV[s] * b).dropna()
                rows.append(dict(kind="decay", seg=seg, instr=s, horizon=h, mean=diff.mean(), median=diff.median(),
                                 n=len(diff)))
        fams = list(FAM_D) + (list(FAM_M) if seg == "B" else [])
        for fam in fams:
            ft = FAM_D.get(fam, fam)
            elig = np.isfinite(fill_types[ft]["SPY"])
            elig_idx = np.nonzero(elig)[0]
            for x in XS:
                b_idx = np.nonzero(trig[(fam, x)] & elig)[0]
                nb = len(b_idx)
                if nb == 0:
                    continue
                k = max(1, len(elig_idx) // nb)
                for s in INSTR:
                    for ex in EXITS:
                        sj, mu = oc[(ft, s, ex)]
                        sjs, mus = oc[(ft, "SPY", ex)]
                        r_rule = xirr_many(tyr[b_idx], tyr[sj[b_idx]], mu[b_idx])[0]
                        r_spy = xirr_many(tyr[b_idx], tyr[sjs[b_idx]], mus[b_idx])[0]
                        # random draws
                        draws = np.array([np.sort(RNG.choice(elig_idx, nb, replace=False)) for _ in range(NRAND)])
                        r_rand = xirr_many(tyr[draws], tyr[sj[draws]], mu[draws])
                        # schedule offsets
                        sched = [elig_idx[o::k][:nb] for o in range(k)]
                        sched = [q for q in sched if len(q) == nb] or [elig_idx[0::k][:nb]]
                        r_sched = np.array([xirr_many(tyr[q], tyr[sj[q]], mu[q])[0] for q in sched])
                        mult_rule = mu[b_idx].mean()
                        # local edge: dip-day multiple vs the mean multiple of sessions within +-10
                        loc = []
                        for i in b_idx:
                            w = elig_idx[(elig_idx >= i - 10) & (elig_idx <= i + 10) & (elig_idx != i)]
                            loc.append(mu[i] / np.nanmean(mu[w]) - 1)
                        base = dict(seg=seg, family=fam, x=x, instr=s, exit=ex, n_buys=nb, sessions=len(elig_idx),
                                    buys_per_year=nb / ((idx[-1] - idx[0]).days / 365.25),
                                    xirr_rule=r_rule, xirr_rand_mean=r_rand.mean(),
                                    rand_pct_beaten=(r_rule > r_rand).mean(), xirr_sched_mean=r_sched.mean(),
                                    sched_pct_beaten=(r_rule > r_sched).mean(), xirr_spy_same=r_spy,
                                    mult_rule=mult_rule, mult_rand=np.nanmean(mu[elig_idx]),
                                    local_edge_mean=np.nanmean(loc), local_edge_hit=np.mean(np.array(loc) > 0))
                        for size in SIZES:
                            D = size * E0
                            px = fill_types[ft][s]
                            eq, cash_sh, skip, pdd = account(idx, b_idx, sj, px, closes[s].values, bil, D)
                            eqs, _, _, pdds = account(idx, b_idx, sjs, fill_types[ft]["SPY"], closes["SPY"].values, bil, D)
                            mdd, uw = dd_stats(eq)
                            mdds, uws = dd_stats(eqs)
                            rows.append(dict(kind="config", **base, size=size, acct_cagr=cagr(eq, idx),
                                             acct_maxdd=mdd, acct_underwater_sessions=uw, cash_share_mean=cash_sh,
                                             skipped=skip, pos_dd_vs_cost=pdd, acct_cagr_spy_same=cagr(eqs, idx),
                                             acct_maxdd_spy_same=mdds, pos_dd_vs_cost_spy_same=pdds))
                            if ex == "hold" and size == 0.005:
                                curves[(seg, fam, x, s)] = eq
                                curves[(seg, fam, x, "SPY")] = eqs
                        print(seg, fam, x, s, ex, nb, round(r_rule, 4), round(r_rand.mean(), 4), flush=True)
        # SPY buy and hold
        bh = E0 * closes["SPY"].values / closes["SPY"].values[0]
        mdd, uw = dd_stats(bh)
        rows.append(dict(kind="spy_bh", seg=seg, acct_cagr=cagr(bh, idx), acct_maxdd=mdd, acct_underwater_sessions=uw))
        for s in INSTR:
            e = E0 * closes[s].values / closes[s].values[0]
            mdd, uw = dd_stats(e)
            rows.append(dict(kind="etf_bh", seg=seg, instr=s, acct_cagr=cagr(e, idx), acct_maxdd=mdd,
                             acct_underwater_sessions=uw))
        curves[(seg, "spy_bh")] = bh
        curves[(seg, "dates")] = idx
        # simulated daily-rebalanced leverage vs real (tracking check)
        rs = closes["SPY"].pct_change().fillna(0).values
        for s in INSTR:
            L = LEV[s]
            er = 0.0091 if L == 3 else 0.0089
            sim = np.cumprod(1 + L * rs - (L - 1) * bil - er / 252)
            real = closes[s].values / closes[s].values[0]
            yrs = (idx[-1] - idx[0]).days / 365.25
            rows.append(dict(kind="simcheck", seg=seg, instr=s, sim_cagr=sim[-1] ** (1 / yrs) - 1,
                             real_cagr=real[-1] ** (1 / yrs) - 1,
                             daily_te=np.std(np.diff(np.log(sim)) - np.diff(np.log(real))) * np.sqrt(252)))
    res = pd.DataFrame(rows)
    res.to_csv(out / "results_partA.csv", index=False, float_format="%.6g")
    pd.to_pickle(curves, out / "_curves.pkl")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
