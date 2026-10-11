"""Structure-break trigger after each marked turn: the first 1-minute close beyond the 10-minute pre-turn range
(long: above the highest high of bars T-10..T; short: below the lowest low), known at that bar's close. How much of
the swing was left from there, and the adverse excursion to the swing end. -> triggers.csv.
Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

from cases import DAY, MOMENTS, load, swing_end

HERE = Path(__file__).resolve().parent
rows = []
for mid, sym, side, a, b, owner, note in MOMENTS:
    p = load(sym)
    d = p[p.date == DAY]
    w = d.between_time(a, b)
    T = w.low.idxmin() if side == "long" else w.high.idxmax()
    R = 0.25 * p.loc[T, "atr_d"]
    pre = d[(d.index >= T - pd.Timedelta(minutes=10)) & (d.index <= T)]
    lvl = pre.high.max() if side == "long" else pre.low.min()
    after = d[(d.index > T) & (d.index <= T + pd.Timedelta(minutes=30))]
    hit = after[after.close > lvl] if side == "long" else after[after.close < lvl]
    end_t, best = swing_end(p, T, side)
    ext = p.loc[T, "low"] if side == "long" else p.loc[T, "high"]
    r = dict(moment=mid, symbol=sym, side=side, turn_bar=T.strftime("%H:%M"), range_level=lvl,
             range_from_extreme_R=round(abs(lvl - ext) / R, 2), swing_end=end_t.strftime("%H:%M"),
             swing_from_extreme_R=round(abs(best - ext) / R, 2))
    if len(hit) and hit.index[0] < end_t:
        t0 = hit.index[0]
        c0 = hit.close.iloc[0]
        seg = d[(d.index > t0) & (d.index <= end_t)]
        sg = 1 if side == "long" else -1
        r.update(trigger_bar=t0.strftime("%H:%M"), minutes_after_T=int((t0 - T).total_seconds() // 60),
                 trigger_close=c0, left_to_swing_end_R=round(sg * (best - c0) / R, 2),
                 mae_to_swing_end_R=round(((c0 - seg.low.min()) if sg == 1 else (seg.high.max() - c0)) / R, 2) if len(seg) else 0.0,
                 share_of_swing_left=round(sg * (best - c0) / abs(best - ext), 2))
    else:
        r.update(trigger_bar="none before swing end")
    rows.append(r)
t = pd.DataFrame(rows)
t.to_csv(HERE / "triggers.csv", index=False)
print(t.to_string())
