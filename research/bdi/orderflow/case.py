"""OF-A case study (NOTES 1.5): the owner's five 2026-10-09 moments + SPY. Every flow feature's percentile vs the
stock's 20 prior sessions, per minute T-30..T+10, and false alarms of the same reading that day and per prior session.
-> case_summary.csv, case_minutes.csv, case_alarms.csv, case_footprint.md. Educational only - not financial advice."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import of_lib as L

HERE = Path(__file__).resolve().parent
DAY = "2026-10-09"
MOMENTS = pd.read_csv(HERE.parents[0] / "turns1009" / "moments.csv")
MOMENTS = MOMENTS[MOMENTS.owner_marked].reset_index(drop=True)
FEATS = L.FLOW + L.PRICE


def hm_to_sec(hm: str) -> int:
    h, m = map(int, hm.split(":"))
    return (h * 60 + m - 570) * 60


def swing_hit(mid: np.ndarray, t: np.ndarray, side: int, up=0.005, dn=0.0025, H=1800) -> np.ndarray:
    out = np.zeros(len(t), bool)
    for i, s in enumerate(t):
        w = mid[s + 1:min(s + 1 + H, len(mid))]
        if not len(w):
            continue
        r = w / mid[s] - 1
        a = np.flatnonzero(side * r >= up)
        b = np.flatnonzero(side * r <= -dn)
        out[i] = len(a) > 0 and (not len(b) or a[0] < b[0])
    return out


def onsets(flag: np.ndarray, lo=L.W0, hi=L.W1, refr=900) -> np.ndarray:
    idx, last = [], -10**9
    for s in np.flatnonzero(flag):
        if s < lo or s > hi:
            continue
        if s - last >= refr:
            idx.append(s)
        last = s if s - last >= refr else last
    return np.array(idx, int)


def build(sym: str):
    i = L.DAYS.index(DAY)
    days = L.DAYS[i - 20:i + 1]
    raw = {d: L.load_day(sym, d) for d in days}
    ref = L.ref_stats([L.day_stats(raw[d]) for d in days[:-1]])
    feats = {d: L.features(raw[d], ref) for d in days}
    return days, raw, feats


def main():
    syms = list(dict.fromkeys(list(MOMENTS.symbol) + ["SPY"]))
    cache = {s: build(s) for s in syms}
    summ, mins, alarms = [], [], []
    for _, mo in MOMENTS.iterrows():
        sym, side = mo.symbol, (1 if mo.side == "long" else -1)
        for who in (sym, "SPY"):
            days, raw, feats = cache[who]
            prior = pd.concat([feats[d] for d in days[:-1]])
            today = feats[DAY]
            T = hm_to_sec(mo.turn_bar)
            mid = raw[DAY].mid.to_numpy()
            for f in FEATS:
                ref = np.sort(prior[f].dropna().to_numpy())
                if not len(ref):
                    continue
                pct = 100 * np.searchsorted(ref, today[f].to_numpy(), side="right") / len(ref)
                dirp = pct if side == 1 else 100 - pct           # high = reading in the turn's direction
                pre = dirp[T - 1800:T]
                at = dirp[T - 60:T + 120]
                post = dirp[T + 60:T + 660]
                first99 = np.flatnonzero(pre >= 99)
                summ.append(dict(moment=mo.moment, symbol=sym, who=who, side=mo.side, turn=mo.turn_bar, feature=f,
                                 pre30_max=round(float(np.nanmax(pre)), 1), pre30_min=round(float(np.nanmin(pre)), 1),
                                 pre30_share_ge99=round(float((pre >= 99).mean()), 4),
                                 first_ge99_min_before=round((1800 - first99[0]) / 60, 1) if len(first99) else None,
                                 at_T_max=round(float(np.nanmax(at)), 1), at_T_min=round(float(np.nanmin(at)), 1),
                                 post10_max=round(float(np.nanmax(post)), 1), post10_min=round(float(np.nanmin(post)), 1)))
                for m in range(-30, 11):
                    s0 = T + m * 60
                    seg = dirp[s0:s0 + 60]
                    mins.append(dict(moment=mo.moment, who=who, feature=f, minute=m, end_pct=round(float(seg[-1]), 1),
                                     max_pct=round(float(np.nanmax(seg)), 1), min_pct=round(float(np.nanmin(seg)), 1)))
                if who != sym or f in L.PRICE or f in ("spread_z", "flicker10"):
                    continue
                # false alarms: onsets of the turn-direction reading >= p99 (and <= p1: flow WITH the prior move)
                for tail, cond in (("dir_ge99", lambda p: p >= 99), ("dir_le1", lambda p: p <= 1)):
                    rows = []
                    for d in days:
                        pc = 100 * np.searchsorted(ref, feats[d][f].to_numpy(), side="right") / len(ref)
                        dp = pc if side == 1 else 100 - pc
                        on = onsets(cond(dp))
                        md = raw[d].mid.to_numpy()
                        hit = swing_hit(md, on, side) if len(on) else np.zeros(0, bool)
                        near = bool(len(on) and d == DAY and np.any(np.abs(on - T) <= 300))
                        rows.append((d, len(on), int(hit.sum()), near))
                    pr = [r for r in rows if r[0] != DAY]
                    td = rows[-1]
                    alarms.append(dict(moment=mo.moment, feature=f, tail=tail, onsets_1009=td[1], hits_1009=td[2],
                                       caught_T_pm5=td[3], onsets_per_prior_session=round(np.mean([r[1] for r in pr]), 2),
                                       prior_precision=round(sum(r[2] for r in pr) / max(1, sum(r[1] for r in pr)), 3)))
            # base rate of the swing label at every 30th second in the window, prior sessions
            if who == sym:
                b = []
                for d in days[:-1]:
                    md = raw[d].mid.to_numpy()
                    tt = np.arange(L.W0, L.W1, 30)
                    b.append(swing_hit(md, tt, side).mean())
                alarms.append(dict(moment=mo.moment, feature="BASE_RATE_any_second", tail="", onsets_1009=None,
                                   hits_1009=None, caught_T_pm5=None, onsets_per_prior_session=None,
                                   prior_precision=round(float(np.mean(b)), 3)))
    pd.DataFrame(summ).to_csv(HERE / "case_summary.csv", index=False)
    pd.DataFrame(mins).to_csv(HERE / "case_minutes.csv", index=False)
    pd.DataFrame(alarms).to_csv(HERE / "case_alarms.csv", index=False)
    footprint_md()


def footprint_md():
    """Footprint (buy x sell per price) of the turn minute and the two minutes either side, per owner moment."""
    lines = ["# Footprint around the owner's moments, 2026-10-09 (SIP, Lee-Ready signed, shares)\n",
             "*Educational only - not financial advice.* Columns: price, buy volume, sell volume, delta. Turn minute T "
             "marked. Prices with < 0.5% of the minute's volume omitted.\n"]
    for _, mo in MOMENTS.iterrows():
        f = L.DATA / "footprint" / f"{mo.symbol}_{DAY}.parquet"
        if not f.exists():
            continue
        fp = pd.read_parquet(f)
        T = hm_to_sec(mo.turn_bar) // 60
        lines.append(f"\n## {mo.moment} {mo.symbol} {mo.side} {mo.turn_bar}\n")
        for m in range(T - 2, T + 3):
            g = fp[fp.m == m].sort_values("px", ascending=False)
            tot = (g.b + g.s).sum()
            g = g[(g.b + g.s) >= 0.005 * tot]
            hh, mm = divmod(570 + m, 60)
            lines.append(f"\n{hh:02d}:{mm:02d}{' (T)' if m == T else ''}  vol {int(tot):,}  delta {int((g.b - g.s).sum()):+,}\n\n```")
            for _, r in g.iterrows():
                lines.append(f"{r.px:10.2f} {int(r.b):>9,} x {int(r.s):<9,} {int(r.b - r.s):+,}")
            lines.append("```")
    (HERE / "case_footprint.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
