"""First look at candidate confluence signatures drawn from the 10-09 case studies, on the 4 case stocks only
(AAPL, SPCX, CAT, TSLA; 20 prior sessions + 10-09, 09:45-15:30). IN-SAMPLE and hindsight-chosen: the rules were
written after looking at these very moments, so these numbers are an upper bound, not evidence. Signal level, no
costs. The scale-up worker tests them across all stocks and days under docs/RESEARCH_RULES.md.
Outcome: >= 1R in the signal's direction before 1R against within 60 min (R = 0.25 x daily ATR), and 2R before 1R.
net_1R_per_signal: (+1R hits - 1R stops) / signals, timeouts counted 0, no costs -- a rough sign, not expectancy.
-> signatures.csv. Educational only - not financial advice."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cases import DAY, MOMENTS, load, onsets, outcome

HERE = Path(__file__).resolve().parent


def pivots(s: pd.Series, k: int, kind: str) -> pd.Series:
    """Pivot value at bar i if s[i] is the min (max) of bars i-k..i+k; known only k bars later (shifted by k)."""
    roll = s.rolling(2 * k + 1, center=True)
    piv = s.where(s == (roll.min() if kind == "low" else roll.max()))
    return piv.shift(k)  # causal: becomes known k bars after the pivot


def retest(p: pd.DataFrame, side: str, k: int = 5, lb: int = 90, gap: int = 10, tol_in=0.05, tol_out=0.10) -> pd.Series:
    """Bar t tests a confirmed pivot from t-lb..t-gap: within tol_out ATR short of it or tol_in ATR beyond it,
    and closes back in the reversal half of its range. Per session (no carry-over)."""
    out = pd.Series(False, index=p.index)
    for d, g in p.groupby("date"):
        a = g.atr_d
        if side == "long":
            pv = pivots(g.low, k, "low")
            lvl = pd.concat([pv.shift(j) for j in range(gap - k, lb - k)], axis=1)
            dist = (g.low.to_numpy()[:, None] - lvl.to_numpy()) / a.to_numpy()[:, None]
            ok = np.nanmax(np.where((dist >= -tol_in) & (dist <= tol_out), 1, 0), axis=1) > 0
            rev = g.close > (g.high + g.low) / 2
        else:
            pv = pivots(g.high, k, "high")
            lvl = pd.concat([pv.shift(j) for j in range(gap - k, lb - k)], axis=1)
            dist = (lvl.to_numpy() - g.high.to_numpy()[:, None]) / a.to_numpy()[:, None]
            ok = np.nanmax(np.where((dist >= -tol_in) & (dist <= tol_out), 1, 0), axis=1) > 0
            rev = g.close < (g.high + g.low) / 2
        out.loc[g.index] = ok & rev.to_numpy()
    return out


def q(ref: pd.DataFrame, col: str, x: float) -> float:
    return ref[col].quantile(x)


def signatures(p: pd.DataFrame, ref: pd.DataFrame, side: str) -> dict[str, pd.Series]:
    L = side == "long"
    lo, hi = (lambda c, x=0.10: p[c] <= q(ref, c, x)), (lambda c, x=0.90: p[c] >= q(ref, c, x))
    ext = lo if L else hi                     # "stretched in the direction of the prior move"
    trig1 = (p.macd_cross_1m == (1 if L else -1)) | (p.bull_engulf_1m == 1 if L else p.bear_engulf_1m == 1) | \
            (p.hammer_1m == 1 if L else p.shooting_star_1m == 1)
    rt = retest(p, side)
    lv = {k: (p[f"d_{k}_atr"].abs() <= 0.10) for k in ("day_open", "prev_close", "pml" if L else "pmh", "pdl" if L else "pdh")}
    lv_n = sum(v.astype(int) for v in lv.values())
    near_lvl = (p.low if L else p.high)
    s = {
        "C1_retest_reject": rt,
        "C2_retest_after_1m_flush": rt & ext("roc10_atr_1m"),
        "C3_stretched5m_plus_1m_trigger": (ext("vwap_z_5m") | ext("rsi14_5m")) & trig1,
        "C3b_stretched5m_both_plus_trigger": ext("vwap_z_5m") & ext("rsi14_5m") & trig1,
        "C4_level_cluster_reclaim": (lv_n >= 2) & ((p.close > (p.high + p.low) / 2) if L else (p.close < (p.high + p.low) / 2)),
        "C5_retest_and_stretched5m": rt & (ext("vwap_z_5m") | ext("rsi14_5m")),
        "C6_1m_flush_plus_trigger": ext("roc10_atr_1m") & trig1,
    }
    _ = near_lvl
    return s


def main():
    rows, caught = [], []
    for sym in ("AAPL", "SPCX", "CAT", "TSLA"):
        p = load(sym)
        days = sorted(p.date.unique())
        i = days.index(DAY)
        ref_days = days[i - 20:i]
        win = p[p.date.isin(ref_days + [DAY])].copy()
        win = win.join(outcome(win, up_r=1.0, dn_r=1.0)).join(outcome(win).add_suffix("2"))
        ok = (win.tod >= 945) & (win.tod <= 1530)
        ref = win[win.date.isin(ref_days)]
        for side in ("long", "short"):
            for name, f in signatures(win, ref, side).items():
                f = f.fillna(False).astype(bool)
                on = onsets(f & ok)
                for per, dsel in (("prior20", ref_days), ("1009", [DAY])):
                    o = on[[t.date() in dsel for t in on.index]] if len(on) else on
                    base = win.loc[ok & win.date.isin(dsel), f"hit_{side}"].mean()
                    rows.append(dict(symbol=sym, side=side, signature=name, period=per, onsets=len(o),
                                     per_session=round(len(o) / len(dsel), 2),
                                     hits=int(win.loc[o.index, f"hit_{side}"].sum()) if len(o) else 0,
                                     hits2=int(win.loc[o.index, f"hit_{side}2"].sum()) if len(o) else 0,
                                     stops=int(win.loc[o.index, "hit_" + ("short" if side == "long" else "long")].sum()) if len(o) else 0,
                                     base=round(base, 3), base2=round(win.loc[ok & win.date.isin(dsel), f"hit_{side}2"].mean(), 3)))
                for mid, msym, mside, a, b, owner, _n in MOMENTS:
                    if msym != sym or mside != side:
                        continue
                    d = win[win.date == DAY].between_time(a, b)
                    T = d.low.idxmin() if side == "long" else d.high.idxmax()
                    w = f[(f.index >= T) & (f.index <= T + pd.Timedelta(minutes=5))]
                    caught.append(dict(moment=mid, signature=name, fired_T_to_T5=bool(w.any()),
                                       first_fire=w[w].index.min().strftime("%H:%M") if w.any() else ""))
    r = pd.DataFrame(rows)
    agg = r.groupby(["signature", "side", "period"]).agg(onsets=("onsets", "sum"), hits=("hits", "sum"),
                                                          hits2=("hits2", "sum"), stops=("stops", "sum"), base=("base", "mean"),
                                                          base2=("base2", "mean")).reset_index()
    agg["precision"] = (agg.hits / agg.onsets).round(3)
    agg["precision2"] = (agg.hits2 / agg.onsets).round(3)
    agg["stop_first_rate"] = (agg.stops / agg.onsets).round(3)
    agg["net_1R_per_signal"] = ((agg.hits - agg.stops) / agg.onsets).round(3)   # +1 / -1, timeouts 0, no costs
    agg["lift"] = (agg.precision / agg.base).round(2)
    agg["onsets_per_stock_session"] = (agg.onsets / (4 * np.where(agg.period == "prior20", 20, 1))).round(2)
    agg.to_csv(HERE / "signatures.csv", index=False)
    c = pd.DataFrame(caught).pivot(index="signature", columns="moment", values="first_fire")
    c.to_csv(HERE / "signatures_caught.csv")
    print(agg.to_string())
    print(c.to_string())


if __name__ == "__main__":
    main()
