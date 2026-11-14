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
        rec = bool(np.isfinite(U) and (fav[i_s:] >= U).any())           # stopped, then the target price traded later
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
    d = d.merge(div.rename(columns={"rate": "div"})[["symbol", "date", "div"]], on=["symbol", "date"], how="left")
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
    st = (T.setup + "|" + T.date.str[:7]).to_numpy(); idx = pd.Series(range(len(T))).groupby(st)
    ks = pd.Series(rule.astype(int)).groupby(st).sum()
    out = np.empty(NDRAW)
    groups = {s: g.to_numpy() for s, g in idx}
    for b in range(NDRAW):
        tot = 0.0
        for s, kk in ks.items():
            if kk:
                tot += eff[rng.choice(groups[s], kk, replace=False)].sum()
        out[b] = tot
    return out


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


def main():
    st = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "PLAN.md", "sizestop.py"], capture_output=True, text=True).stdout
    assert not st.strip(), "PLAN.md and sizestop.py must be committed before the score"
    raise SystemExit("score body: written in the scoring run after MOMSIDE (inputs: BR.load_lists, size_quintiles, leg, cond_effect)")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
