"""CWT package C amendment 2026-10-12: C8 gates (3) and C9 overlays (4) on the longhold book S6_mom12_1rev_N20_W.

Uses the saturday1010 loader (copy of longhold's data block, locked-day returns zeroed, locked days dropped from every
statistic) and checks parity with longhold's saved S6 daily returns first. Statistics follow longhold NOTES 1.6/1.8
(splits train 2017-2020, valid 2021-2024.10, valid2 2025.03+; active vs the EW universe; monthly active t).
Output: raw_s6.csv, s6_gates.csv. Educational only - not financial advice.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "bdi" / "saturday1010" / "new"))
import lib  # noqa: E402
from lib import (BORROW, C, COST_O, Cn, NS, On, R_cc, R_co, R_oc, T, WEEK_END, MONTH_END, caldays, col, dates,  # noqa: E402
                 locked, syms)

T_BAR = math.sqrt(2 * math.log(130))
SPL = {"train": ("2017-01-01", "2020-12-31"), "valid": ("2021-01-01", "2024-10-31"), "valid2": ("2025-03-01", "2026-12-31")}

# high / low for the Keltner band (same W3 file), aligned to lib's columns
_hl = pd.read_parquet(ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet",
                      columns=["symbol", "date", "high", "low"])
_hl["symbol"] = _hl["symbol"].astype(str)
Hn = _hl.pivot(index="date", columns="symbol", values="high").reindex(index=dates, columns=syms).to_numpy()
Ln = _hl.pivot(index="date", columns="symbol", values="low").reindex(index=dates, columns=syms).to_numpy()
del _hl
prevC = np.vstack([np.full(NS, np.nan), Cn[:-1]])
SMA20 = C.rolling(20, min_periods=20).mean().to_numpy()
EMA8 = C.ewm(span=8, adjust=False, ignore_na=True).mean().to_numpy()
EMA20 = C.ewm(span=20, adjust=False, ignore_na=True).mean().to_numpy()
EMA21 = C.ewm(span=21, adjust=False, ignore_na=True).mean().to_numpy()
_tr = np.fmax(Hn - Ln, np.fmax(np.abs(Hn - prevC), np.abs(Ln - prevC)))
ATR14 = pd.DataFrame(_tr, index=dates).ewm(alpha=1 / 14, adjust=False, ignore_na=True).mean().to_numpy().copy()
KUP = EMA20 + 3 * ATR14                                      # Keltner upper band at the close of t (used on t+1)

spy_c = Cn[:, col["SPY"]]
spy_s200 = C["SPY"].rolling(200, min_periods=200).mean().to_numpy()
spy_s10 = C["SPY"].rolling(10, min_periods=10).mean().to_numpy()


def ftd():
    """Same state machine as families.ftd_state (TESTPLAN amendment), on SPY from lib's data."""
    sys.path.insert(0, str(HERE))
    v = lib.Vn[:, col["SPY"]]; c = spy_c; lo = Ln[:, col["SPY"]]
    on = np.zeros(T, bool); state = False; low_since = np.inf; att_day = 0; att_low = np.nan; dist = []
    for t in range(1, T):
        if not np.isfinite(c[t]):
            on[t] = state; continue
        dd = c[t] / c[t - 1] - 1 <= -0.002 and v[t] > v[t - 1]
        dist.append(t if dd else -1)
        n_dist = sum(1 for x in dist[-25:] if x >= 0)
        if state:
            if c[t] < att_low or n_dist >= 6:
                state = False; low_since = lo[t]; att_day = 0
        else:
            if lo[t] < low_since:
                low_since = lo[t]; att_day = 0
            elif att_day == 0 and c[t] > c[t - 1]:
                att_day = 1; att_low = low_since
            elif att_day >= 1:
                att_day += 1
                if att_day >= 4 and c[t] / c[t - 1] - 1 >= 0.0125 and v[t] > v[t - 1]:
                    state = True; dist.clear()
        on[t] = state
    return on


GATE = {"spy200": spy_c > spy_s200, "spy10": spy_c > spy_s10, "ftd": ftd()}


def simulate_ovl(targets, ovl=None):
    """lib.simulate plus per-name exits between rebalances (sma20x2 / kidd / keltner). ovl None == lib.simulate."""
    h = np.zeros(NS); cash = 1.0; E_prev = 1.0
    out_r = np.zeros(T); out_to = np.zeros(T); out_c = np.zeros(T)
    started = False
    stage = np.zeros(NS, int)                    # kidd: 0 full, 1 half sold
    sell_frac = {}                               # name -> fraction of the current holding to sell at the next open
    for d in range(1, T):
        w = targets.get(d - 1)
        act = not locked[d]
        if w is not None:
            started = True
            h *= 1 + R_co[d]
            E = cash + h.sum()
            tgt = w * E
            co = COST_O[d]
            bad = np.isnan(co)
            if bad.any():
                tgt = np.where(bad, h, tgt)
            trade = tgt - h
            cost = np.nansum(np.abs(trade) * co)
            cash -= trade.sum() + cost
            h = tgt.copy()
            out_to[d] = np.abs(trade).sum() / 2 / E
            out_c[d] = cost / E_prev
            stage[:] = 0; sell_frac = {}
            if ovl == "keltner" and act:
                cash, c2 = _keltner(h, d, cash)
                out_c[d] += c2 / E_prev
            h *= 1 + R_oc[d]
        elif started:
            if act and (sell_frac or ovl == "keltner"):
                h *= 1 + R_co[d]
                cost = 0.0; traded = 0.0
                for s, f in sell_frac.items():
                    if h[s] > 0 and np.isfinite(COST_O[d, s]):
                        amt = h[s] * f
                        c = amt * COST_O[d, s]
                        cash += amt - c; h[s] -= amt; cost += c; traded += amt
                sell_frac = {}
                if ovl == "keltner":
                    cash, c2 = _keltner(h, d, cash)
                    cost += c2
                E0 = cash + h.sum()
                out_to[d] = traded / 2 / E0 if E0 > 0 else 0
                out_c[d] = cost / E_prev
                h *= 1 + R_oc[d]
            else:
                h *= 1 + R_cc[d]
        if started:
            short = -h[h < 0].sum()
            if short > 0 and not locked[d]:
                cash -= BORROW / 365 * caldays[d] * short
            E = cash + h.sum()
            out_r[d] = E / E_prev - 1
            E_prev = E
            if act and ovl in ("sma20x2", "kidd") and d + 1 < T and targets.get(d) is None:
                held = np.flatnonzero(h > 1e-12)
                for s in held:
                    c = Cn[d, s]
                    if not np.isfinite(c):
                        continue
                    if ovl == "sma20x2":
                        if c < SMA20[d, s] and Cn[d - 1, s] < SMA20[d - 1, s]:
                            sell_frac[s] = 1.0
                    else:
                        if stage[s] == 0 and c < EMA21[d, s]:
                            sell_frac[s] = 1.0; stage[s] = 2
                        elif stage[s] == 0 and c < EMA8[d, s]:
                            sell_frac[s] = 0.5; stage[s] = 1
                        elif stage[s] == 1 and c < EMA21[d, s]:
                            sell_frac[s] = 1.0; stage[s] = 2
    return out_r, out_to, out_c


def _keltner(h, d, cash):
    """Sell held names whose high reaches the prior close's Keltner band; h is valued at the open of d."""
    cost = 0.0
    for s in np.flatnonzero(h > 1e-12):
        tg = KUP[d - 1, s]
        if not (np.isfinite(tg) and np.isfinite(Hn[d, s]) and Hn[d, s] >= tg and np.isfinite(On[d, s])):
            continue
        px = max(On[d, s], tg)
        v = h[s] * px / On[d, s]
        c = v * (0.01 / px + 0.0001)
        cash += v - c; cost += c; h[s] = 0.0
    return cash, cost


# ---------------------------------------------------------------------------------------------- statistics (longhold)
month_key = np.asarray(dates.year * 100 + dates.month)


def pmask(name):
    if name == "trval":
        a, b = SPL["train"][0], SPL["valid"][1]
    elif name == "all":
        a, b = SPL["train"][0], "2026-12-31"
    else:
        a, b = SPL[name]
    return np.asarray((dates >= a) & (dates <= b)) & ~locked


def mdd(r):
    eq = np.cumprod(1 + r)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def mser(r, m):
    return pd.Series(r[m]).groupby(month_key[m]).apply(lambda x: (1 + x).prod() - 1)


def stats(r, b, spy, to, c, p):
    m = pmask(p)
    rr, bb = r[m], b[m]
    mr, mb, ms = mser(r, m), mser(b, m), mser(spy, m)
    act = mr - mb
    yrs = m.sum() / 252
    return {"period": p, "cagr": float(np.prod(1 + rr) ** (1 / yrs) - 1), "vol": float(rr.std() * math.sqrt(252)),
            "sharpe": float(rr.mean() / rr.std() * math.sqrt(252)), "maxdd": mdd(rr),
            "active": float((rr.mean() - bb.mean()) * 252),
            "active_t": float(act.mean() / act.std() * math.sqrt(len(act))),
            "active_up_months": float(act[ms > 0].mean() * 12), "active_down_months": float(act[ms <= 0].mean() * 12),
            "turnover_yr": float(to[m].sum() / yrs), "cost_yr": float(c[m].sum() / yrs),
            "exposure_note": None}


def main():
    base_t = lib.stock_targets(lib.MOM12_1, 20, "W", filt_rev=True, start=0)
    ref = pd.read_parquet(lib.LH / "data" / "daily_returns.parquet", columns=["S6_mom12_1rev_N20_W"]).iloc[:, 0]
    ref = ref.reindex(dates).to_numpy()
    base = simulate_ovl(base_t)
    par = float(np.nanmax(np.abs(base[0] - ref)))
    print("parity S6 max abs diff", par, flush=True)
    assert par < 1e-6, par   # reference saved as float32
    ew = lib.simulate(lib.ew_universe_targets(start=0))[0]
    spy = lib.simulate(lib.bh_targets(["SPY"], start=0))[0]
    eq = np.cumprod(1 + base[0])
    wk = [t for t in WEEK_END if t in base_t]
    series = {"S6_base": base}
    for g, on in GATE.items():
        tg = {t: (w if on[t] else np.zeros(NS)) for t, w in base_t.items()}
        series[f"C8_{g}_on_S6"] = simulate_ovl(tg)
        print(g, "on-share at signals", round(float(np.mean([on[t] for t in base_t])), 3), flush=True)
    for o in ("sma20x2", "kidd", "keltner"):
        series[f"C9_{o}_on_S6"] = simulate_ovl(base_t, o)
        print(o, flush=True)
    gov = {}
    eqw = pd.Series(eq[wk], index=wk)
    ma = eqw.rolling(20).mean()
    half = 0
    for t, w in base_t.items():
        g = 0.5 if (t in ma.index and np.isfinite(ma[t]) and eqw[t] < ma[t]) else 1.0
        half += g < 1
        gov[t] = w * g
    print("governor half-size share", round(half / len(base_t), 3), flush=True)
    series["C9_governor_on_S6"] = simulate_ovl(gov)
    rows = []
    for k, (r, to, c) in series.items():
        for p in ("train", "valid", "valid2", "trval", "all"):
            rows.append({"id": k, **stats(r, ew, spy, to, c, p)})
    for k in ("EW", "SPY"):
        rr = ew if k == "EW" else spy
        for p in ("train", "valid", "valid2", "trval", "all"):
            rows.append({"id": f"bench_{k}", **stats(rr, ew, spy, np.zeros(T), np.zeros(T), p)})
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "raw_s6.csv", index=False, float_format="%.5f")
    R = res.set_index(["id", "period"])
    g_rows = []
    for k in series:
        if k == "S6_base":
            continue
        a = [R.loc[(k, p), "active"] for p in SPL]
        ab = [R.loc[("S6_base", p), "active"] for p in SPL]
        sh = [R.loc[(k, p), "sharpe"] for p in SPL]
        shb = [R.loc[("S6_base", p), "sharpe"] for p in SPL]
        A1 = all(x > 0 for x in a)
        A2 = R.loc[(k, "trval"), "active_t"] >= T_BAR
        A4 = R.loc[(k, "all"), "active_up_months"] > 0 and R.loc[(k, "all"), "active_down_months"] > 0
        imp_a = all(x > y for x, y in zip(a, ab))
        imp_s = all(x > y for x, y in zip(sh, shb)) and R.loc[(k, "trval"), "maxdd"] > R.loc[("S6_base", "trval"), "maxdd"]
        verdict = "candidate" if (A1 and A2 and A4 and (imp_a or imp_s)) else ("no_improvement" if not (imp_a or imp_s) else "improves_but_fails_tierA")
        g_rows.append({"id": k, "verdict": verdict, "A1": A1, "A2_t": round(R.loc[(k, "trval"), "active_t"], 2), "t_bar": round(T_BAR, 2),
                       "A4": A4, "improves_active_all3": imp_a, "improves_sharpe_all3_and_dd": imp_s,
                       **{f"active_{p}": round(x, 4) for p, x in zip(SPL, a)},
                       **{f"d_active_{p}": round(x - y, 4) for p, x, y in zip(SPL, a, ab)},
                       **{f"sharpe_{p}": round(x, 3) for p, x in zip(SPL, sh)},
                       **{f"d_sharpe_{p}": round(x - y, 3) for p, x, y in zip(SPL, sh, shb)},
                       "maxdd_trval": round(R.loc[(k, "trval"), "maxdd"], 4),
                       "base_maxdd_trval": round(R.loc[("S6_base", "trval"), "maxdd"], 4),
                       "turnover_trval": round(R.loc[(k, "trval"), "turnover_yr"], 2)})
    G = pd.DataFrame(g_rows)
    G.to_csv(HERE / "s6_gates.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.loc[["S6_base"]].round(3).to_string())
    print(G.to_string(index=False))


if __name__ == "__main__":
    main()
