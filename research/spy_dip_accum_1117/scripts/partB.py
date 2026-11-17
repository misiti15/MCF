"""Part B: intraday buy of SPXL / UPRO / SSO on an S&P dip measured from the previous close, out by 15:55.
Pre-declared in ../PLAN.md. LR8 costs. Usage: python partB.py OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_minute  # noqa: E402

INSTR = ["SPXL", "UPRO", "SSO"]
XS = [0.005, 0.0075, 0.01]
EXITS = ["c1555", "lowstop", "atrstop"]
FAMS = {"gap0950": 949, "d1015": 1014, "d1030": 1029, "pm1430": 1429, "wk1015": 1014}
VALID_FROM = pd.Timestamp("2026-01-01")
RNG = np.random.default_rng(1117)
NRAND = 20


def per_day(sym):
    m = load_minute(sym)
    days = {}
    for day, g in m.groupby("day"):
        days[day] = g.set_index("hm")[["open", "high", "low", "close"]]
    return days


def atr14(days):
    keys = sorted(days)
    hi = np.array([days[k].high.max() for k in keys])
    lo = np.array([days[k].low.min() for k in keys])
    cl = np.array([days[k].close.iloc[-1] for k in keys])
    out = {}
    for i, k in enumerate(keys):
        if i < 15 or (k - keys[i - 14]).days > 30:
            continue
        tr = [max(hi[j] - lo[j], abs(hi[j] - cl[j - 1]), abs(lo[j] - cl[j - 1])) for j in range(i - 14, i)]
        out[k] = float(np.mean(tr))
    return out


def fee_ps(day, px):
    sec = 20.60e-6 * px if day >= pd.Timestamp("2026-04-04") else 0.0
    taf = 0.000195 if day >= pd.Timestamp("2026-01-01") else 0.000166
    return sec + taf + 2 * 0.00005


def trade(g, e_hm, exit_, atr, day):
    """One long from the close of bar e_hm to 15:54 close / stop. Returns (R, bps) after LR8 costs or None."""
    if e_hm not in g.index or 1554 not in g.index:
        return None
    entry = g.at[e_hm, "close"]
    if exit_ == "lowstop":
        stop = g.loc[:e_hm, "low"].min() * (1 - 0.0005)
    elif exit_ == "atrstop":
        stop = entry - atr
    else:
        stop = None
    runit = (entry - stop) if stop is not None else atr
    if not runit or runit <= 0:
        return None
    after = g.loc[e_hm + 1:1554] if True else None
    after = g[(g.index > e_hm) & (g.index <= 1554)]
    px, why = g.at[1554, "close"], "mkt"
    if stop is not None and len(after):
        hit = np.nonzero(after.low.values <= stop)[0]
        if len(hit):
            o = after.open.values[hit[0]]
            px, why = (o if o <= stop else stop), "stop"
    cost = 1e-4 * entry + (max(0.02, 4e-4 * px) if why == "stop" else max(0.01, 1e-4 * px)) + fee_ps(day, px)
    pnl = px - entry - cost
    return pnl / runit, pnl / entry * 1e4


def main(outdir):
    out = Path(outdir)
    bars = {s: per_day(s) for s in ["SPY"] + INSTR}
    atrs = {s: atr14(bars[s]) for s in INSTR}
    keys = sorted(bars["SPY"])
    spy = bars["SPY"]
    prev_close, prev_wk = {}, {}
    wk = pd.Series({k: k.to_period("W-FRI") for k in keys})
    wk_last = {p: spy[max(ks)].close.iloc[-1] for p, ks in wk.groupby(wk).groups.items()}
    for i, k in enumerate(keys[1:], 1):
        if (k - keys[i - 1]).days <= 5:
            prev_close[k] = spy[keys[i - 1]].close.iloc[-1]
        p = wk[k] - 1
        # previous week must exist in the data and not border the locked block
        if p in wk_last and (k - max(wk.index[wk == p])).days <= 9:
            prev_wk[k] = wk_last[p]
    # trigger days
    trig = {}
    for fam, hm in FAMS.items():
        for x in XS:
            dd = []
            for k in keys:
                g = spy[k]
                ref = prev_wk.get(k) if fam == "wk1015" else prev_close.get(k)
                if ref is None or hm not in g.index:
                    continue
                v = g.at[930, "open"] if fam == "gap0950" and 930 in g.index else g.at[hm, "close"]
                if v <= ref * (1 - x):
                    dd.append(k)
            trig[(fam, x)] = dd
    elig_days = [k for k in keys if k in prev_close]
    # IDX-style day sets (SPY down from TODAY's open by 09:45 / 09:55; LD8-style >= 0.30% from the open by 10:30)
    idx_sets = {}
    for name, (x, hm) in {"IDX2 (0.75% from open by 09:45)": (0.0075, 944), "IDX3 (0.75% by 09:55)": (0.0075, 954),
                          "IDX5 (0.5% by 09:45)": (0.005, 944), "LD8 dip part (0.30% by 10:30)": (0.003, 1029)}.items():
        idx_sets[name] = {k for k in elig_days if 930 in spy[k].index and
                          spy[k].loc[:hm, "low"].min() <= spy[k].at[930, "open"] * (1 - x)}
    rows, trows, ov = [], [], []
    for (fam, x), dd in trig.items():
        dset = set(dd)
        for name, s in idx_sets.items():
            ov.append(dict(family=fam, x=x, idx_set=name, n_fam=len(dset), n_idx=len(s), both=len(dset & s),
                           jaccard=len(dset & s) / max(1, len(dset | s)), fam_days_not_idx=len(dset - s)))
        hm = FAMS[fam]
        for s in INSTR:
            for ex in EXITS:
                rs, bp, ds, nr = [], [], [], []
                for k in dd:
                    g = bars[s].get(k)
                    a = atrs[s].get(k)
                    if g is None or a is None:
                        continue
                    t = trade(g, hm, ex, a, k)
                    if t is None:
                        continue
                    rs.append(t[0]); bp.append(t[1]); ds.append(k)
                    # null 1: random entry bars 09:49..14:29 on the same day
                    cand = [h for h in g.index if 949 <= h <= 1429]
                    rr = [trade(g, h, ex, a, k) for h in RNG.choice(cand, NRAND)]
                    rr = [q[0] for q in rr if q is not None]
                    nr.append(np.mean(rr) if rr else np.nan)
                    trows.append(dict(family=fam, x=x, instr=s, exit=ex, day=k.date(), R=t[0], bps=t[1]))
                if not rs:
                    continue
                rs, bp = np.array(rs), np.array(bp)
                ds = pd.DatetimeIndex(ds)
                tr, va = rs[ds < VALID_FROM], rs[ds >= VALID_FROM]
                best = rs.argmax()
                # null 2: the same entry minute on every eligible session
                allr = []
                for k in elig_days:
                    g, a = bars[s].get(k), atrs[s].get(k)
                    if g is None or a is None:
                        continue
                    t = trade(g, hm, ex, a, k)
                    if t is not None:
                        allr.append(t[0])
                sd = rs.std(ddof=1) if len(rs) > 1 else np.nan
                rows.append(dict(family=fam, x=x, instr=s, exit=ex, n=len(rs), n_train=len(tr), n_valid=len(va),
                                 avgR=rs.mean(), t=rs.mean() / sd * np.sqrt(len(rs)) if sd and sd > 0 else np.nan,
                                 avgR_train=tr.mean() if len(tr) else np.nan, avgR_valid=va.mean() if len(va) else np.nan,
                                 avgR_wo_best=np.delete(rs, best).mean() if len(rs) > 1 else np.nan,
                                 best_share=rs[best] / rs.sum() if rs.sum() > 0 else np.nan,
                                 win=(rs > 0).mean(), avg_bps=bp.mean(), null_random_same_days=np.nanmean(nr),
                                 null_same_minute_all_days=np.mean(allr), n_all_days=len(allr)))
        print(fam, x, len(dd), flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(out / "results_partB.csv", index=False, float_format="%.5g")
    pd.DataFrame(trows).to_csv(out / "trades_partB.csv", index=False, float_format="%.5g")
    pd.DataFrame(ov).to_csv(out / "overlap_partB.csv", index=False, float_format="%.4g")
    print("sessions", len(keys), "eligible", len(elig_days))


if __name__ == "__main__":
    main(sys.argv[1])
