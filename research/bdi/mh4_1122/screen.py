"""BDI-MH4 1122 screen (pre-registered in PLAN.md): crypto-complex-follows-BTC and peer-group laggards.

  python screen.py WORK        (needs WORK/rows_t1, rows_t2, daily_t1, etb_rate.parquet from build.py)
Writes fit_all.csv, picks.csv, out.txt beside this script. FIT for every config; CHECK + T2 once for the FIT picks only.
Educational only - not financial advice."""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
W = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
TOD_MULT_950 = 1.4          # mcf.research.gates.tod_cost_mult(950): TOD_COST ((935,3.8),(950,2.1),(1030,1.4))
BORROW = 1.2e-4
ADV_MIN = 20e6
RNG = np.random.default_rng(20261122)
EXITS = ("t1s1", "hold")


def no_locked(d):
    d = pd.Series(list(d)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def half(d):
    d = pd.Series(d).astype(str).to_numpy()
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    return np.where(fit, "fit", np.where(d >= "2025-10-01", "check", "t2"))


# ------------------------------------------------------------------------------------------------ rows + R
def load_rows(test):
    X = pd.read_parquet(W / f"rows_{test}.parquet")
    no_locked(X.date.unique())
    if test == "t2":
        X = X[(X.date >= "2023-01-03") & (X.date <= "2024-09-13")]
    X = X.reset_index(drop=True)
    e = X.c950.to_numpy()
    risk = 0.25 * X.atr_d.to_numpy()
    tier = np.where((np.abs(X.gap.to_numpy()) >= 20) | (e < 5), 3.0, 1.0)
    ecost = (0.01 + e * 1e-4) * TOD_MULT_950
    for sn, s in (("L", 1), ("S", -1)):
        for ex in EXITS:
            px = X[f"px_{sn}_{ex}"].to_numpy()
            k = X[f"kind_{sn}_{ex}"].to_numpy()
            xc = np.where(k == 2, 0.0, 0.01 + px * 1e-4) + np.where(k == 1, 0.02, 0.0)
            bor = BORROW * e if s < 0 else 0.0
            g = s * (px - e)
            X[f"rg_{sn}_{ex}"] = g / risk
            X[f"r_{sn}_{ex}"] = np.where(k >= 0, (g - tier * (ecost + xc) - bor) / risk, np.nan)
    X["scr"] = (2 * (0.01 + e * 1e-4) + 0.02) / risk
    X["half"] = half(X.date)
    return X


def eligible(X, side, etb):
    ok = (X.adv20 >= ADV_MIN) & (X.c950 >= 5) & (X.scr <= 0.15)
    if side < 0:
        ok &= X.symbol.map(etb).fillna(0).ge(0.9)
    return ok.to_numpy()


def spy_type(X, daily):
    s = X[X.symbol == "SPY"][["date", "open"]].merge(daily[daily.symbol == "SPY"][["date", "close"]], on="date")
    ret = (s.close / s.open - 1) * 100
    return pd.Series(np.where(ret >= 0.3, "up", np.where(ret <= -0.3, "down", "flat")), index=s.date)


# ------------------------------------------------------------------------------------------------ stats
def clustered_t(r, d):
    if len(r) < 3:
        return float("nan")
    m = r.mean()
    e = (r - m).groupby(d).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(r)
    return float(m / se) if se > 0 else float("nan")


def stats(t, nses, spy):
    """t: DataFrame with date, r, rg, symbol"""
    if not len(t):
        return {"trades": 0}
    day = t.groupby("date").r.sum().sort_values(ascending=False)
    tot = float(t.r.sum())
    b1 = day.index[:1]
    b2 = day.index[:2]
    mo = t.groupby(t.date.str[:7]).r.sum()
    apr = t.date.str.startswith("2025-04")
    ty = t.date.map(spy)
    o = {"trades": len(t), "sessions_traded": int(day.size), "tps": round(len(t) / nses, 3),
         "win": round(float((t.r > 0).mean()), 3), "avg_r": round(float(t.r.mean()), 4),
         "avg_r_gross": round(float(t.rg.mean()), 4),
         "wo_best": round(float(t.r[~t.date.isin(b1)].mean()), 4) if (~t.date.isin(b1)).any() else None,
         "wo_top2": round(float(t.r[~t.date.isin(b2)].mean()), 4) if (~t.date.isin(b2)).any() else None,
         "best_day": str(b1[0]), "best_share": round(float(day.iloc[0] / tot), 3) if tot > 0 else None,
         "total_r": round(tot, 2), "r_per_session": round(tot / nses, 4), "worst_day": round(float(day.min()), 2),
         "t_cl": round(clustered_t(t.r, t.date), 2), "symbols": int(t.symbol.nunique()),
         "wf_pos": round(float((mo > 0).mean()), 3), "months": int(mo.size),
         "apr25_trades": int(apr.sum()), "apr25_r": round(float(t.r[apr].sum()), 2),
         "ex_apr_avg_r": round(float(t.r[~apr].mean()), 4) if (~apr).any() else None}
    for k in ("up", "flat", "down"):
        x = t.r[ty == k]
        o[f"spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_{k}"] = int(len(x))
    return o


def book(sel, X, cap=100):
    """sel: boolean mask over X rows (already eligible). cap 100 per session (all entries at 09:50, symbol order)."""
    t = X.loc[sel, ["symbol", "date"]].copy()
    t = t.sort_values(["date", "symbol"], kind="mergesort")
    t = t[t.groupby("date").cumcount() < cap]
    return t.index.to_numpy()


def trades(X, idx, side, ex):
    sn = "L" if side > 0 else "S"
    t = X.loc[idx, ["symbol", "date", "half"]].copy()
    t["r"] = X.loc[idx, f"r_{sn}_{ex}"].to_numpy()
    t["rg"] = X.loc[idx, f"rg_{sn}_{ex}"].to_numpy()
    return t[t.r.notna()]


def random_null(X, t, side, ex, elig, draws=1000):
    """percentile of t's avg R among draws of the same per-session count from that session's eligible pool"""
    sn = "L" if side > 0 else "S"
    cnt = t.groupby("date").size()
    tot = np.zeros(draws)
    n = 0
    for d, k in cnt.items():
        pool = POOLS[(id(X), sn, ex, side)].get(d)
        if pool is None or not len(pool):
            continue
        tot += pool[RNG.integers(0, len(pool), size=(draws, k))].sum(1)
        n += k
    nullm = tot / max(n, 1)
    return round(float((nullm < t.r.mean()).mean() * 100), 1), round(float(nullm.mean()), 4)


POOLS: dict = {}


def build_pools(X, etb):
    for side, sn in ((1, "L"), (-1, "S")):
        el = eligible(X, side, etb)
        for ex in EXITS:
            r = X[f"r_{sn}_{ex}"].to_numpy()
            ok = el & np.isfinite(r)
            s = pd.Series(r[ok]).groupby(X.date.to_numpy()[ok])
            POOLS[(id(X), sn, ex, side)] = {d: v.to_numpy() for d, v in s}


# ------------------------------------------------------------------------------------------------ idea 1: crypto
MEMBERS = ["FBTC", "GBTC", "BITO", "ETHA", "BITX", "MSTU", "MSTX", "CONL", "ETHU", "MSTR", "COIN", "HOOD", "GLXY", "CRCL",
           "BMNR", "FIGR", "MARA", "CLSK", "RIOT", "HUT", "CIFR", "WULF", "IREN", "BTDR", "CORZ", "APLD"]


def crypto_configs():
    for k in (0.50, 0.75):
        for st in ("all", "lag"):
            for ex in EXITS:
                for side in (1, -1):
                    yield {"idea": "crypto", "id": f"CX-{'L' if side > 0 else 'S'}-k{int(k*100)}-{st}-{ex}",
                           "k": k, "set": st, "exit": ex, "side": side}


def crypto_signal(X, c):
    btc = X[X.symbol == "IBIT"].set_index("date").move
    bm = X.date.map(btc).to_numpy(float)
    s = c["side"]
    trig = (s * bm >= c["k"])
    mem = X.symbol.isin(MEMBERS).to_numpy()
    sig = trig & mem
    if c["set"] == "lag":
        sig &= (s * X.move.to_numpy(float) < 0.5 * np.abs(bm))
    ctrl = mem & ~trig & np.isfinite(bm)
    return sig, ctrl


# ------------------------------------------------------------------------------------------------ idea 2: peers
ETF_PAT = re.compile(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Select Sector|Invesco QQQ|"
                     r"\b[23]X\b|Leveraged|Ultra|\bTrust\b.*(Bitcoin|Ether|Gold|Silver|Oil)|Daily .*(Bull|Bear|Long|Short)|"
                     r"Inverse|Index", re.I)


def stock_set():
    u = pd.read_csv("/home/user/MCF/data/universe.csv")
    return set(u.symbol[~u.name.fillna("").str.contains(ETF_PAT)])


def daily_returns(test):
    fr = pd.read_parquet("/home/user/MCF/data/cache_fresh/daily.parquet", columns=["symbol", "date", "close"])
    fr["date"] = pd.to_datetime(fr["date"]).dt.date.astype(str)
    fr["seg"] = 0
    if test == "t1":
        d1 = pd.read_parquet(W / "daily_t1.parquet")[["symbol", "date", "close", "seg"]]
        d1["seg"] = d1["seg"] + 10          # seg 11 = 2024-09-16..10-31, seg 12 = 2025-03..
        D = pd.concat([fr, d1], ignore_index=True)
    else:
        D = fr
    no_locked(D.date.unique())
    D = D.sort_values(["symbol", "date"])
    # the cache_fresh (seg 0) -> cache_hist (seg 11) join is contiguous (2024-09-13 Fri -> 09-16 Mon); the lock gap is not
    D["sg"] = D["seg"].replace({11: 0})
    D["ret"] = D.groupby(["symbol", "sg"]).close.pct_change(fill_method=None)
    return D.pivot_table(index="date", columns="symbol", values="ret").sort_index()


def peer_lists(RET, month, univ, cmin, kmax=10, need=3):
    w = RET[RET.index < month + "-01"].tail(120)
    if len(w) < 50:
        return {}
    cols = [c for c in w.columns if c in univ or c == "SPY"]
    w = w[cols]
    w = w.loc[:, w.notna().mean() >= 0.9]
    s = w["SPY"].fillna(0).to_numpy()
    w = w.drop(columns=["SPY"])
    A = w.fillna(0).to_numpy()
    beta = (A - A.mean(0)).T @ (s - s.mean()) / max(((s - s.mean()) ** 2).sum(), 1e-12)
    res = A - np.outer(s, beta)
    C = np.corrcoef(res.T)
    np.fill_diagonal(C, -1)
    names = w.columns.to_numpy()
    out = {}
    for i, c in enumerate(names):
        j = np.argsort(-C[i])[:kmax]
        j = j[C[i, j] >= cmin]
        if len(j) >= need:
            out[c] = list(names[j])
    return out


def peer_signals(X, RET, univ, c, m, cache):
    key0 = ("sig", id(X), c, m)
    if key0 not in cache:
        cache[key0] = _peer_signals(X, RET, univ, c, m, cache)
    return cache[key0]


def _peer_signals(X, RET, univ, c, m, cache):
    """boolean masks (long, short) over X rows for one (c, m); cache keeps peer tables per (month, c)"""
    L = np.zeros(len(X), bool)
    S = np.zeros(len(X), bool)
    mv = X.move.to_numpy(float)
    mon = X.date.str[:7].to_numpy()
    for month in np.unique(mon):
        key = (month, c)
        if key not in cache:
            cache[key] = peer_lists(RET, month, univ, c)
        P = cache[key]
        if not P:
            continue
        ii = np.flatnonzero(mon == month)
        sub = X.iloc[ii]
        for d, g in sub.groupby("date"):
            mvd = dict(zip(g.symbol, g.move))
            for sym, gi in zip(g.symbol.to_numpy(), g.index.to_numpy()):
                peers = P.get(sym)
                if not peers:
                    continue
                pm = np.array([mvd.get(p, np.nan) for p in peers])
                up = int(np.nansum(pm >= m))
                dn = int(np.nansum(pm <= -m))
                own = mvd[sym]
                lu = up >= 3 and dn <= 1 and -0.5 < own < 0.25
                ld = dn >= 3 and up <= 1 and -0.5 < -own < 0.25
                if lu and ld:
                    continue
                L[gi] = lu
                S[gi] = ld
    return L, S


def mh4_overlap_mask(X, RET, univ, cache):
    """approximate MH4 lag signal at the 09:50 row (peers K=10 corr>=0.30 need 6; P >= 0.40, agree >= 0.7, own z < P/2)"""
    zr = (X.fo / (X.atr_d / X.c950 * 100)).to_numpy(float)
    big = (X.adv20 >= 95e6).to_numpy()
    Z = pd.Series(zr)
    med = Z[big].groupby(X.date[big]).median()
    z = zr - X.date.map(med).to_numpy(float)
    L = np.zeros(len(X), bool)
    S = np.zeros(len(X), bool)
    mon = X.date.str[:7].to_numpy()
    for month in np.unique(mon):
        key = ("mh4", month)
        if key not in cache:
            cache[key] = peer_lists(RET, month, univ, 0.30, need=6)
        P = cache[key]
        ii = np.flatnonzero(mon == month)
        sub = X.iloc[ii]
        for d, g in sub.groupby("date"):
            zd = dict(zip(g.symbol, z[g.index]))
            for sym, gi in zip(g.symbol.to_numpy(), g.index.to_numpy()):
                peers = P.get(sym)
                if not peers:
                    continue
                pz = np.array([zd.get(p, np.nan) for p in peers])
                pz = pz[np.isfinite(pz)]
                if len(pz) < 6:
                    continue
                Pm = float(np.median(pz))
                if abs(Pm) < 0.40:
                    continue
                sg = np.sign(Pm)
                if (np.sign(pz) == sg).mean() < 0.7:
                    continue
                if sg * zd[sym] < abs(Pm) / 2:
                    (L if sg > 0 else S)[gi] = True
    return L, S


def peer_configs():
    for c in (0.35, 0.50):
        for m in (0.50, 0.75):
            for ex in EXITS:
                for side in (1, -1):
                    yield {"idea": "peer", "id": f"PG-{'L' if side > 0 else 'S'}-c{int(c*100)}-m{int(m*100)}-{ex}",
                           "c": c, "m": m, "exit": ex, "side": side}


# ------------------------------------------------------------------------------------------------ main
def main():
    etb = pd.read_parquet(W / "etb_rate.parquet").rate
    X1 = load_rows("t1")
    X2 = load_rows("t2")
    d1 = pd.read_parquet(W / "daily_t1.parquet")
    d2 = pd.read_parquet(W / "daily_t2.parquet")
    spy1, spy2 = spy_type(X1, d1), spy_type(X2, d2)
    days1 = pd.Series(sorted(X1[X1.symbol == "SPY"].date.unique()))
    nses = {"fit": int((half(days1) == "fit").sum()), "check": int((half(days1) == "check").sum()),
            "t2": int(X2[X2.symbol == "SPY"].date.nunique())}
    nses["comb"] = nses["fit"] + nses["check"]
    build_pools(X1, etb)
    build_pools(X2, etb)
    univ = stock_set()
    R1, R2 = daily_returns("t1"), daily_returns("t2")
    pc1, pc2 = {}, {}
    lines = [f"sessions {nses}"]
    fit_rows, sigs = [], {}
    for c in list(crypto_configs()) + list(peer_configs()):
        side, ex = c["side"], c["exit"]
        el1 = eligible(X1, side, etb)
        if c["idea"] == "crypto":
            sig, ctrl = crypto_signal(X1, c)
        else:
            Lm, Sm = peer_signals(X1, R1, univ & set(X1.symbol), c["c"], c["m"], pc1)
            sig = Lm if side > 0 else Sm
            ctrl = None
        sigs[c["id"]] = (sig, ctrl)
        idx = book(sig & el1, X1)
        t = trades(X1, idx, side, ex)
        f = t[t.half == "fit"]
        st = stats(f, nses["fit"], spy1)
        fit_rows.append({**{k: c[k] for k in ("idea", "id")}, **st})
    FIT = pd.DataFrame(fit_rows)
    FIT.to_csv(HERE / "fit_all.csv", index=False)
    cols = ["id", "trades", "tps", "win", "avg_r", "avg_r_gross", "wo_best", "wo_top2", "best_share", "t_cl", "wf_pos",
            "apr25_r", "ex_apr_avg_r", "spy_up", "spy_down"]
    lines.append("\n== FIT, every config (32)\n" + FIT[cols].to_string(index=False))
    # ---- picks: per idea + side, best FIT t with >= 20 trades
    picks = []
    for idea in ("crypto", "peer"):
        for sd in ("L", "S"):
            z = FIT[(FIT.idea == idea) & FIT.id.str.contains(f"-{sd}-") & (FIT.trades >= 20)]
            if len(z):
                picks.append(z.sort_values("t_cl", ascending=False).iloc[0].id)
    lines.append(f"\nFIT picks (scored once on CHECK / T2): {picks}")
    cfgs = {c["id"]: c for c in list(crypto_configs()) + list(peer_configs())}
    rows = []
    mh4L = mh4S = None
    for pid in picks:
        c = cfgs[pid]
        side, ex = c["side"], c["exit"]
        sig, ctrl = sigs[pid]
        el1 = eligible(X1, side, etb)
        t = trades(X1, book(sig & el1, X1), side, ex)
        out = {"id": pid}
        for h, nm in (("fit", "fit"), ("check", "check")):
            out[nm] = stats(t[t.half == h], nses[h], spy1)
        out["comb"] = stats(t[t.half != "t2"], nses["comb"], spy1)
        for nm, sub in (("fit", t[t.half == "fit"]), ("check", t[t.half == "check"]), ("comb", t)):
            if len(sub):
                out[nm]["null_pct"], out[nm]["null_mean"] = random_null(X1, sub, side, ex, el1)
        # day-type control
        if c["idea"] == "crypto":
            cidx = book(ctrl & el1, X1)
        else:
            names = set(t.symbol)
            cidx = book(X1.symbol.isin(names).to_numpy() & ~sig & el1 & np.isfinite(X1.move.to_numpy()), X1, cap=10 ** 6)
        ct = trades(X1, cidx, side, ex)
        for nm, h in (("fit", "fit"), ("check", "check")):
            cc = ct[ct.half == h]
            out[nm]["ctrl_n"], out[nm]["ctrl_avg_r"] = int(len(cc)), (round(float(cc.r.mean()), 4) if len(cc) else None)
        # T2
        if c["idea"] == "crypto":
            out["t2"] = {"trades": 0, "note": "not scorable: no BTC proxy in data/cache_fresh"}
        else:
            el2 = eligible(X2, side, etb)
            Lm, Sm = peer_signals(X2, R2, univ & set(X2.symbol), c["c"], c["m"], pc2)
            t2 = trades(X2, book((Lm if side > 0 else Sm) & el2, X2), side, ex)
            out["t2"] = stats(t2, nses["t2"], spy2)
            if len(t2):
                out["t2"]["null_pct"], out["t2"]["null_mean"] = random_null(X2, t2, side, ex, el2)
            # MH4 overlap (T1)
            if mh4L is None:
                mh4L, mh4S = mh4_overlap_mask(X1, R1, univ & set(X1.symbol), pc1)
            mm = mh4L if side > 0 else mh4S
            out["mh4_overlap"] = round(float(mm[t.index.to_numpy()].mean()), 3) if len(t) else None
        rows.append(out)
        lines.append(f"\n== PICK {pid}\n" + json.dumps(out, indent=1, default=float))
    json.dump(rows, open(HERE / "picks.json", "w"), indent=1, default=float)
    flat = []
    for o in rows:
        for test in ("fit", "check", "comb", "t2"):
            flat.append({"id": o["id"], "test": test, **{k: v for k, v in o[test].items()}, "mh4_overlap": o.get("mh4_overlap")})
    pd.DataFrame(flat).to_csv(HERE / "picks.csv", index=False)
    # signal-day counts per idea (descriptive)
    btc = X1[X1.symbol == "IBIT"].set_index("date").move
    for k in (0.5, 0.75):
        lines.append(f"IBIT trigger days |move|>={k}: up {int((btc >= k).sum())}, down {int((btc <= -k).sum())} of {btc.size}")
    lines.append("Educational only - not financial advice.")
    (HERE / "out.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
