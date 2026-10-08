"""Autopsy of the 60 live paper trades on 2026-10-06 / 2026-10-07 (diagnosis only, NOT evidence: 2 days).

Inputs: the primary paper journal (read-only copy) and SIP 1-minute bars for the two live days, fetched
for this study only (10-06 09:30 .. 10-07 16:00 ET). No bar before 2026-10-06 is read here (the locked
holdout ends 10-05), so for 10-06 entries the rule values come from the journal, and for 10-07 entries the
5-minute features are computed with 10-06 as the only prior day; daily ATR is taken from the journal
(heat/lab R = 0.25 x ATR, so ATR = 4 x |ref - stop|).

usage: python research/oct7/autopsy/autopsy.py JOURNAL BARS_PARQUET
Educational only - not financial advice.
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.journal import Journal
from mcf.research.heat import heat_frame
from mcf.research.setup_lab import extra_features
from mcf.data.bars import resample

OUT = "research/oct7/autopsy/"
ET = "America/New_York"
SLIP_BPS, SLIP_PS, STOP_PS = 1.0, 0.01, 0.02   # config/default.yaml costs

J = Journal(sys.argv[1])
RID = J.get_or_create_run("paper", "MCF Update (live paper)")
T = J.trades(RID)
SIG = J.signals(RID)
raw = pd.read_parquet(sys.argv[2])
BARS = {}
for sym, g in raw.groupby(level=0):
    g = g.droplevel(0)
    g.index = g.index.tz_convert(ET)
    g = g.between_time("09:30", "15:59")
    BARS[sym] = g[["open", "high", "low", "close", "volume"]]


def day_bars(sym, day):
    g = BARS.get(sym)
    if g is None:
        return pd.DataFrame()
    return g[g.index.date == pd.Timestamp(day).date()]


def cost_r(entry, R, stop_exit):
    c = 2 * (entry * SLIP_BPS / 1e4 + SLIP_PS) + (STOP_PS if stop_exit else 0)
    return c / R


def first_touch(path, side, entry, R, stop_r=-1.0, tgt_r=None, be_at=None, trail=None, trail_after=None, max_loss_pct=None):
    """Walk 1-minute bars (stop first inside a bar). Returns (r_gross, reason, minutes)."""
    stop = entry - side * (-stop_r) * R
    if max_loss_pct is not None:
        cap = entry * (1 - side * max_loss_pct / 100)
        stop = max(stop, cap) if side == 1 else min(stop, cap)
    tgt = None if tgt_r is None else entry + side * tgt_r * R
    best = entry
    t0 = path.index[0] if len(path) else None
    for ts, b in path.iterrows():
        hi, lo = b["high"], b["low"]
        adverse = lo if side == 1 else hi
        if (adverse - stop) * side <= 0:
            px = b["open"] if (b["open"] - stop) * side <= 0 else stop   # gap through stop fills at open
            return side * (px - entry) / R, "stop", (ts - t0).total_seconds() / 60
        fav = hi if side == 1 else lo
        if tgt is not None and (fav - tgt) * side >= 0:
            return side * (tgt - entry) / R, "target", (ts - t0).total_seconds() / 60
        if side * (fav - best) > 0:
            best = fav
        mfe = side * (best - entry) / R
        if be_at is not None and mfe >= be_at:
            stop = max(stop, entry) if side == 1 else min(stop, entry)
        if trail is not None and mfe >= (trail_after or 0):
            ts_ = best - side * trail * R
            stop = max(stop, ts_) if side == 1 else min(stop, ts_)
    if not len(path):
        return 0.0, "none", 0
    return side * (path["close"].iloc[-1] - entry) / R, "time", (path.index[-1] - t0).total_seconds() / 60


def excursions(path, side, entry, R):
    if path.empty:
        return dict(mfe_r=np.nan, mae_r=np.nan, mfe_pct=np.nan, mae_pct=np.nan, t_mfe=np.nan, mfe_before_mae1=None)
    fav = path["high"] if side == 1 else path["low"]
    adv = path["low"] if side == 1 else path["high"]
    f = side * (fav - entry)
    a = side * (adv - entry)
    i = int(np.argmax(f.to_numpy()))
    return dict(mfe_r=f.max() / R, mae_r=a.min() / R, mfe_pct=f.max() / entry * 100, mae_pct=a.min() / entry * 100,
                t_mfe=(path.index[i] - path.index[0]).total_seconds() / 60 + 1)


def features_at(sym, day, entry_time, atr):
    """Lab/heat 5-minute features at the last COMPLETE 5-min bar before the entry (10-07 only)."""
    if str(day) != "2026-10-07":
        return {}
    prev = day_bars(sym, "2026-10-06")
    cur = day_bars(sym, day)
    if prev.empty or cur.empty:
        return {}
    cut = entry_time.floor("min")
    cur = cur[cur.index < cut]
    d5p = resample(prev, "5min").iloc[-40:]
    d5 = resample(cur, "5min")
    d5 = d5[d5.index + pd.Timedelta(minutes=5) <= cut]
    if d5.empty:
        return {}
    hist = pd.concat([d5p, d5])
    f = heat_frame(hist)
    f["atr_d"] = atr
    f = f.join(extra_features(hist, f)).iloc[-len(d5):].copy()
    pc = float(prev["close"].iloc[-1])
    f["gap"] = (float(d5["open"].iloc[0]) / pc - 1) * 100
    r = f.iloc[-1]
    # 4-period RSI on 5-min closes (owner's "4-day RSI" idea, intraday analogue) and the daily-ish context
    c = hist["close"]
    d = c.diff()
    up, dn = d.clip(lower=0).rolling(4).mean(), (-d.clip(upper=0)).rolling(4).mean()
    rsi4 = (100 - 100 / (1 + up / dn.replace(0, np.nan))).iloc[-1]
    w = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
    base = sum(w[k] * float(r[k]) for k in w)
    return dict(bar=str(f.index[-1].time()), tod=int(r["tod"]), gap=round(float(r["gap"]), 2),
                fromOpen=round(float(r["fromOpen"]), 2), vwapDistPct=round(float(r["vwapDistPct"]), 2),
                rsi14=round(float(r["rsi"]), 1), rsi5=round(float(r["rsi5"]), 1), rsi4=round(float(rsi4), 1),
                pricePos=round(float(r["pricePosition"]), 2), momentum=round(float(r["momentum"]), 2),
                sma20_dist_pct=round(float(r["sma20_dist_pct"]), 2), bear_div=int(r["bear_div"]),
                bull_div=int(r["bull_div"]), dist_hod_atr=round(float(r["dist_hod_atr"]), 2),
                dist_lod_atr=round(float(r["dist_lod_atr"]), 2), dist_pdh_atr=round(float((prev["high"].max() - r["close"]) / atr), 2),
                hfs_short_score=round(-base - 8 * 8.0 / atr, 1),
                hfl_long_score=round(base + -1 * np.clip(float(r["fromOpen"]), -3, 3) * 5 - 4 * 8.0 / atr, 1),
                volumeRatio=round(float(r["volumeRatio"]), 2))


rows = []
for _, tr in T.iterrows():
    sym, day, side = tr.symbol, str(tr.date), int(tr.side)
    bars = day_bars(sym, day)
    entry, stop, R = float(tr.entry), float(tr.stop), abs(float(tr.entry) - float(tr.stop))
    ent_t = tr.entry_time
    # live journal quirk: 10-06 LW/ADBE carry signal_time after entry_time (restored from broker) - use entry_time
    after = bars[bars.index > ent_t.floor("min")]
    end_55 = after[after.index <= pd.Timestamp(f"{day} 15:54", tz=ET)]     # through the 15:54 bar = 15:55 close
    ex_t = min(tr.exit_time, pd.Timestamp(f"{day} 15:55", tz=ET))
    held = after[after.index < ex_t.floor("min") + pd.Timedelta(minutes=1)]
    exc = excursions(held, side, entry, R)
    rest = excursions(end_55, side, entry, R)
    sig = SIG[(SIG.symbol == sym) & (SIG.strategy == tr.strategy) & (SIG.day == day) & (SIG.status == "submitted")]
    info = json.loads(sig["info"].iloc[0]) if len(sig) else {}
    ref = float(sig["ref_price"].iloc[0]) if len(sig) else entry
    atr = 4 * abs(ref - stop) if tr.strategy in ("heat_fade_short", "heat_fade_long", "exhaustion_short") else np.nan
    row = dict(id=int(tr.id), symbol=sym, setup=tr.strategy, side=side, date=day, entry_time=str(ent_t.time())[:8],
               exit_time=str(tr.exit_time.time())[:8], exit_reason=tr.exit_reason, entry=entry, stop=stop,
               target=tr.target, R=R, R_pct=R / entry * 100, r_live=tr.r_multiple, pnl=tr.pnl,
               slip_bps=tr.slip_bps, heat_score=info.get("heat_score"), rv20=info.get("rv20"),
               or_width_pct=(info["or_width"] / entry * 100) if "or_width" in info else None,
               **{f"held_{k}": v for k, v in exc.items()}, **{f"day_{k}": v for k, v in rest.items()})
    # close at 15:55 (the flatten bug moved four 10-07 and eight 10-06 exits to 16:04-16:06)
    if tr.exit_reason == "flatten" and len(end_55):
        px = float(end_55["close"].iloc[-1])
        row["close_1555"] = px
        row["r_at_1555"] = side * (px - entry) / R
        row["pnl_at_1555"] = side * (px - entry) * tr.shares
    # what-ifs on the actual entry, gross R minus costs
    tgt_live = None if pd.isna(tr.target) else side * (float(tr.target) - entry) / R
    for name, kw in {"base_sim": dict(tgt_r=tgt_live), "tp0.5": dict(tgt_r=0.5), "tp1": dict(tgt_r=1.0),
                     "be0.5": dict(tgt_r=tgt_live, be_at=0.5), "be1": dict(tgt_r=tgt_live, be_at=1.0),
                     "trail0.5": dict(tgt_r=None, trail=0.5, trail_after=0.5),
                     "maxloss1.5pct": dict(tgt_r=tgt_live, max_loss_pct=1.5)}.items():
        r, why, mins = first_touch(end_55, side, entry, R, **kw)
        row[f"wi_{name}"] = r - cost_r(entry, R, why == "stop")
        row[f"wi_{name}_why"] = why
    # opposite side: same entry, same R, 1R stop / 1R target (heat/lab geometry); orb mirrored geometry too
    r, why, _ = first_touch(end_55, -side, entry, R, tgt_r=1.0)
    row["opp_1r1r"], row["opp_why"] = r - cost_r(entry, R, why == "stop"), why
    row["opp_hold_1555"] = (-side * (float(end_55["close"].iloc[-1]) - entry) / R) if len(end_55) else np.nan
    row.update({f"f_{k}": v for k, v in features_at(sym, day, ent_t, atr if np.isfinite(atr) else R * 4).items()})
    rows.append(row)

A = pd.DataFrame(rows)


# ---- loss-type classification (primary type, one per trade) ---------------------------------------------
def classify(r):
    win = r["r_live"] > 0
    big_swing = abs(r.get("f_fromOpen", 0) or 0) > 3 or (r["setup"].startswith("orb") and (r["or_width_pct"] or 0) > 4)
    if win:
        if r["exit_reason"] == "target":
            return "win: target"
        return "win: time/flatten"
    if r["held_mfe_r"] >= 0.5:
        base = "gave back gains"            # reached +0.5R or better, closed red
    elif r["held_mfe_r"] < 0.15:
        base = "never worked"               # never more than +0.15R in favour (MarcoFlow's definition, in R)
    else:
        base = "small MFE then failed"
    if r["exit_reason"] == "stop" and r["day_mfe_r"] >= 1.0 and r["held_mfe_r"] < 1.0:
        # after the stop the original side would have reached +1R from entry later in the day
        return base + " / stopped then reversed"
    if r["exit_reason"] == "flatten":
        return base + " / late hold (flattened red)"
    return base


A["loss_type"] = A.apply(classify, axis=1)
A["opp_would_win"] = A["opp_why"].eq("target")
A.to_csv(OUT + "trades_autopsy.csv", index=False)
print(A[["date", "symbol", "setup", "side", "entry_time", "exit_time", "exit_reason", "r_live", "R_pct",
         "held_mfe_r", "held_mae_r", "held_t_mfe", "day_mfe_r", "r_at_1555", "wi_tp0.5", "wi_tp1", "wi_be0.5",
         "wi_trail0.5", "wi_maxloss1.5pct", "opp_1r1r", "loss_type"]].round(2).to_string())
print(pd.crosstab(A["loss_type"], A["setup"], margins=True))
