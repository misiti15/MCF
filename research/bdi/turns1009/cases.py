"""Case studies of the owner's five marked turns on 2026-10-09 (+ the true session extremes next to them).

For every moment and every panel feature (1-min and 5-min):
  value at the turn bar T (known at T+1), its percentile in the same stock's prior-20-session distribution
  (regular session, 2026-09-11..10-08), a pre-declared directional flag (percentile <= 10 / >= 90, or the binary
  pattern), whether the flag was on at T (any of bars T-2..T), the earliest flagged minute in T-60..T (lead),
  the share of the prior 60 minutes it was on (a flag that is on all hour is not timing anything), and whether it
  came on only after the extreme (T+1..T+5, "confirmation").
Hindsight / false alarms: every onset of the same flag (15-minute refractory) in that stock over the 20 prior sessions
  plus 10-09, 09:35-15:30. An onset "hits" if price then moves >= 2R in the flag's direction before 1R against,
  within 60 minutes (from the close of the onset bar; R = 0.25 x daily ATR). precision = hits / onsets; base = the
  same outcome at every minute; lift = precision / base. Main label: >= 1R before 1R against within 60 minutes
  (the lab's symmetric t1s1 geometry, no costs); secondary (suffix 2): >= 2R before 1R.
Writes data-free outputs to this folder: moments.csv, panel_at_turns.csv, confluence.csv, market.csv.
Educational only - not financial advice."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DAY = pd.Timestamp("2026-10-09").date()
TZ = "America/New_York"

# id, symbol, side, turn-bar search window (the extreme 1-min bar inside it is T), owner-marked?, note
MOMENTS = [
    ("M1", "AAPL", "long", "13:40", "13:55", True, "owner: launch of the afternoon leg"),
    ("M1b", "AAPL", "long", "12:00", "12:40", False, "midday range low (owner asked about a midday low)"),
    ("M1c", "AAPL", "long", "09:30", "09:40", False, "true session low"),
    ("M2", "AAPL", "short", "15:00", "15:20", True, "owner: top of the afternoon rally"),
    ("M3", "SPCX", "short", "10:10", "10:20", True, "owner: 10:10 bar"),
    ("M3a", "SPCX", "short", "09:58", "10:05", False, "first top of the 09:55-10:13 double top"),
    ("M3b", "SPCX", "short", "09:30", "09:40", False, "true session high"),
    ("M4", "CAT", "long", "10:10", "10:20", True, "owner: V-reversal low"),
    ("M4b", "CAT", "long", "09:40", "09:50", False, "true session low"),
    ("M5", "TSLA", "short", "10:50", "11:00", True, "owner: top after 10:20-10:50 run-up"),
    ("M5b", "TSLA", "short", "09:50", "10:00", False, "true session high"),
]

MR = ["rsi2", "rsi5", "rsi14", "stoch_k", "stoch_d", "willr", "cci20", "mfi14", "macd_hist_atr", "bb_pctb", "kelt_pos",
      "vwap_z", "ema9_21_atr", "c_ema9_atr", "sma50_dist_atr", "sma200_dist_atr", "di_diff", "obv_slope", "cmf20",
      "adl_slope", "run_len", "roc5_atr", "roc10_atr", "roc30_atr"]
BOTH_HI = ["vol_z", "rvol_tod", "atr_exp", "adx"]
BIN = {"bull_div_rsi": "long", "bull_div_macd": "long", "bull_div_obv": "long", "bear_div_rsi": "short",
       "bear_div_macd": "short", "bear_div_obv": "short", "bull_engulf": "long", "hammer": "long",
       "bear_engulf": "short", "shooting_star": "short", "climax": "both", "inside": "both", "outside": "both"}
CROSS = ["macd_cross", "ema_cross"]


def feature_specs() -> list[tuple[str, str, str]]:
    """(column, kind, family). kind: mr | trend | both_hi | both_lo | lo_long | lo_short | hi_long | hi_short |
    near | bin:<side> | cross."""
    s = []
    for tf in ("1m", "5m"):
        s += [(f"{f}_{tf}", "mr", f) for f in MR]
        s += [(f"{f}_{tf}", "both_hi", f) for f in BOTH_HI]
        s += [(f"bb_bw_{tf}", "both_lo", "bb_bw")]
        s += [(f"{f}_{tf}", f"bin:{v}", f) for f, v in BIN.items()]
        s += [(f"{f}_{tf}", "cross", f) for f in CROSS]
        s += [(f"upper_wick_{tf}", "hi_short", "upper_wick"), (f"lower_wick_{tf}", "hi_long", "lower_wick")]
    s += [("heat_5m", "trend", "heat"), ("mf_buyPressure_5m", "mr", "buyPressure"), ("lab_flow3_5m", "mr", "flow3")]
    s += [(c, "mr", c) for c in ("from_open_atr", "d_prev_close_atr", "resid30_atr", "spy_from_open_pct",
                                 "qqq_from_open_pct", "sec_from_open_pct", "spy_rsi14_1m", "qqq_rsi14_1m",
                                 "sec_rsi14_1m", "spy_vwap_z", "qqq_vwap_z", "sec_vwap_z", "spy_ret30_pct",
                                 "qqq_ret30_pct", "sec_ret30_pct", "br_above_vwap", "br_above_open", "br_hl_net")]
    s += [("br_new30l", "hi_long", "br_new30l"), ("br_new30h", "hi_short", "br_new30h")]
    s += [("dist_lod_atr", "lo_long", "dist_lod"), ("dist_hod_atr", "lo_short", "dist_hod")]
    s += [(f"absd_{k}", "near", k) for k in ("pdh", "pdl", "pmh", "pml", "prev_close", "day_open")]
    s += [("round5_atr", "near", "round5"), ("round10_atr", "near", "round10")]
    return s


NEAR_ATR = 0.10   # "at a level": within 0.10 daily ATR (fixed, not a percentile)
NEAR_ROUND = 0.05


def load(sym: str) -> pd.DataFrame:
    p = pd.read_parquet(DATA / f"panel_{sym}.parquet")
    for k in ("pdh", "pdl", "pmh", "pml", "prev_close", "day_open"):
        p[f"absd_{k}"] = p[f"d_{k}_atr"].abs()
    p["date"] = p.index.date
    p["tod"] = p.index.hour * 100 + p.index.minute
    return p


def outcome(p: pd.DataFrame, horizon: int = 60, up_r: float = 2.0, dn_r: float = 1.0) -> pd.DataFrame:
    """hit_long / hit_short per minute: >= up_r R favourable before dn_r R adverse within `horizon` minutes."""
    out = {"hit_long": np.zeros(len(p), bool), "hit_short": np.zeros(len(p), bool)}
    c, h, l = p.close.to_numpy(), p.high.to_numpy(), p.low.to_numpy()
    R = 0.25 * p.atr_d.to_numpy()
    dates = p.date.to_numpy()
    for i in range(len(p)):
        j = min(len(p), i + 1 + horizon)
        same = dates[i + 1:j] == dates[i]
        hh, ll = h[i + 1:j][same], l[i + 1:j][same]
        if not len(hh) or not np.isfinite(R[i]):
            continue
        for side, key in ((1, "hit_long"), (-1, "hit_short")):
            fav = (hh - c[i]) if side == 1 else (c[i] - ll)
            adv = (c[i] - ll) if side == 1 else (hh - c[i])
            t_f = np.flatnonzero(fav >= up_r * R[i])
            t_a = np.flatnonzero(adv >= dn_r * R[i])
            if len(t_f) and (not len(t_a) or t_f[0] < t_a[0]):
                out[key][i] = True
    return pd.DataFrame(out, index=p.index)


def flags(p: pd.DataFrame, ref: pd.DataFrame, col: str, kind: str, side: str) -> pd.Series:
    """Boolean flag for `side` at every minute (NaN-safe). Percentile thresholds from `ref` (prior 20 sessions)."""
    v = p[col]
    if kind.startswith("bin:"):
        s = kind.split(":")[1]
        return (v == 1) & (s in (side, "both"))
    if kind == "cross":
        return v == (1 if side == "long" else -1)
    if kind == "near":
        return v <= (NEAR_ROUND if col.startswith("round") else NEAR_ATR)
    r = ref[col].dropna()
    q10, q90 = r.quantile(0.10), r.quantile(0.90)
    if kind == "mr":
        return v <= q10 if side == "long" else v >= q90
    if kind == "trend":
        return v >= q90 if side == "long" else v <= q10
    if kind == "both_hi":
        return v >= q90
    if kind == "both_lo":
        return v <= q10
    if kind == "lo_long":
        return (v <= q10) if side == "long" else pd.Series(False, index=p.index)
    if kind == "lo_short":
        return (v <= q10) if side == "short" else pd.Series(False, index=p.index)
    if kind == "hi_long":
        return (v >= q90) if side == "long" else pd.Series(False, index=p.index)
    if kind == "hi_short":
        return (v >= q90) if side == "short" else pd.Series(False, index=p.index)
    raise ValueError(kind)


def pct_rank(ref: pd.Series, x: float) -> float:
    r = ref.dropna().to_numpy()
    if not len(r) or not np.isfinite(x):
        return np.nan
    return 100.0 * (np.sum(r < x) + 0.5 * np.sum(r == x)) / len(r)


def onsets(f: pd.Series, refractory: int = 15) -> pd.Series:
    """Flag onsets (False->True), dropping onsets within `refractory` minutes of the previous kept one, same day."""
    f = f.fillna(False).astype(bool)
    on = f & ~f.shift(1, fill_value=False)
    idx = on[on].index
    keep, last = [], None
    for t in idx:
        if last is None or t.date() != last.date() or (t - last) >= pd.Timedelta(minutes=refractory):
            keep.append(t)
            last = t
    return pd.Series(True, index=pd.DatetimeIndex(keep))


def swing_end(p: pd.DataFrame, T: pd.Timestamp, side: str, retrace_r: float = 1.0):
    """From the extreme bar T: follow the favourable extreme until price retraces retrace_r R from it."""
    d = p[(p.date == T.date()) & (p.index > T)]
    R = 0.25 * p.loc[T, "atr_d"]
    best, bt = (p.loc[T, "low"], T) if side == "long" else (p.loc[T, "high"], T)
    best = p.loc[T, "high"] if side == "long" else p.loc[T, "low"]
    bt = T
    for t, r in d.iterrows():
        if side == "long":
            if r.high > best:
                best, bt = r.high, t
            if best - r.low >= retrace_r * R:
                break
        else:
            if r.low < best:
                best, bt = r.low, t
            if r.high - best >= retrace_r * R:
                break
    return bt, best


def main():
    specs = feature_specs()
    rows, mom_rows, conf_rows, mkt_rows = [], [], [], []
    cache = {}
    for mid, sym, side, a, b, owner, note in MOMENTS:
        if sym not in cache:
            p = load(sym)
            days = sorted(p.date.unique())
            i = days.index(DAY)
            ref_days = days[i - 20:i]
            win = p[p.date.isin(ref_days + [DAY])].copy()
            win = win.join(outcome(win, up_r=1.0, dn_r=1.0)).join(outcome(win).add_suffix("2"))
            cache[sym] = (p, win, win[win.date.isin(ref_days)], ref_days)
        p, win, ref, ref_days = cache[sym]
        day = p[p.date == DAY]
        w = day.between_time(a, b)
        T = w.low.idxmin() if side == "long" else w.high.idxmax()
        ext = p.loc[T, "low"] if side == "long" else p.loc[T, "high"]
        atr, R = p.loc[T, "atr_d"], 0.25 * p.loc[T, "atr_d"]
        sgn = 1 if side == "long" else -1
        end_t, best = swing_end(p, T, side)
        cT = p.loc[T, "close"]
        seg = day[(day.index > T) & (day.index <= end_t)]
        mae = ((cT - seg.low.min()) if side == "long" else (seg.high.max() - cT)) if len(seg) else 0.0
        hit_col, hit2 = f"hit_{side}", f"hit_{side}2"
        mom_rows.append(dict(moment=mid, symbol=sym, side=side, owner_marked=owner, note=note,
                             turn_bar=T.strftime("%H:%M"), extreme=ext, close_T=cT, swing_end=end_t.strftime("%H:%M"),
                             swing_best=best, minutes=int((end_t - T).total_seconds() // 60),
                             daily_atr=round(atr, 3), R=round(R, 3),
                             move_from_extreme_atr=round(sgn * (best - ext) / atr, 2),
                             move_from_extreme_R=round(sgn * (best - ext) / R, 2),
                             move_from_close_T_R=round(sgn * (best - cT) / R, 2),
                             mae_after_close_T_R=round(mae / R, 2),
                             hit_1R_before_1R_60m=bool(win.loc[T, hit_col]),
                             base_1R_20d=round(win.loc[win.date.isin(ref_days), hit_col].mean(), 3),
                             hit_2R_before_1R_60m=bool(win.loc[T, hit2]),
                             base_2R_20d=round(win.loc[win.date.isin(ref_days), hit2].mean(), 3),
                             day_open=p.loc[T, "day_open"], prev_close=p.loc[T, "prev_close"],
                             hod_so_far=p.loc[T, "hod"], lod_so_far=p.loc[T, "lod"]))
        # market lead / lag and decomposition
        mk = dict(moment=mid, symbol=sym, side=side)
        sw = day[(day.index >= T) & (day.index <= end_t)]
        stock_move = (sw.close.iloc[-1] / cT - 1) * 100 if len(sw) else np.nan
        mk["stock_move_pct_T_to_end"] = round(stock_move, 3)
        for tag in ("spy", "qqq", "sec"):
            cc = day[f"{tag}_close"]
            ww = cc[(cc.index >= T - pd.Timedelta(minutes=30)) & (cc.index <= T + pd.Timedelta(minutes=30))]
            te = ww.idxmin() if side == "long" else ww.idxmax()
            mk[f"{tag}_extreme_lag_min"] = int((te - T).total_seconds() // 60)
            mk[f"{tag}_move_pct_T_to_end"] = round((cc.loc[end_t] / cc.loc[T] - 1) * 100, 3)
        beta = p.loc[T, "beta_spy"]
        mk["beta_spy_5m_20d"] = round(beta, 2)
        mk["market_part_pct"] = round(beta * mk["spy_move_pct_T_to_end"], 3)
        mk["market_share_of_move"] = round(mk["market_part_pct"] / stock_move, 2) if stock_move else np.nan
        mk["breadth_above_vwap_T"] = round(p.loc[T, "br_above_vwap"], 3)
        bw = day.br_above_vwap
        bww = bw[(bw.index >= T - pd.Timedelta(minutes=30)) & (bw.index <= T + pd.Timedelta(minutes=30))]
        tb = bww.idxmin() if side == "long" else bww.idxmax()
        mk["breadth_extreme_lag_min"] = int((tb - T).total_seconds() // 60)
        mkt_rows.append(mk)
        # per-feature panel
        lit_series = []
        for col, kind, fam in specs:
            if col not in p:
                continue
            f_win = flags(win, ref, col, kind, side).fillna(False).astype(bool)
            if kind.endswith("_long") and side == "short" or kind.endswith("_short") and side == "long" \
                    or (kind.startswith("bin:") and kind.split(":")[1] not in (side, "both")):
                continue
            pos = win.index.get_loc(T)
            near = f_win.iloc[max(0, pos - 2):pos + 1]
            atT = bool(near[near.index.date == DAY].any())
            pre = f_win.iloc[max(0, pos - 60):pos + 1]
            pre = pre[pre.index.date == DAY]
            first = pre[pre].index.min() if pre.any() else None
            post = f_win.iloc[pos + 1:pos + 6]
            run_start = np.nan          # minutes since the lit run that covers T-2..T began (the real lead)
            if atT:
                j = pos if f_win.iloc[pos] else (pos - 1 if f_win.iloc[pos - 1] else pos - 2)
                while j > 0 and f_win.iloc[j - 1] and f_win.index[j - 1].date() == DAY:
                    j -= 1
                run_start = int((T - f_win.index[j]).total_seconds() // 60)
            # false alarms: onsets 09:35-15:30
            ok = (win.tod >= 935) & (win.tod <= 1530)
            on = onsets(f_win & ok)
            on_ref = on[[t.date() in ref_days for t in on.index]] if len(on) else on
            on_day = on[[t.date() == DAY for t in on.index]] if len(on) else on
            hits_ref = win.loc[on_ref.index, hit_col].sum() if len(on_ref) else 0
            hits_day = win.loc[on_day.index, hit_col].sum() if len(on_day) else 0
            base = win.loc[ok & win.date.isin(ref_days), hit_col].mean()
            prec = hits_ref / len(on_ref) if len(on_ref) else np.nan
            hits2 = win.loc[on_ref.index, hit2].sum() if len(on_ref) else 0
            base2 = win.loc[ok & win.date.isin(ref_days), hit2].mean()
            prec2 = hits2 / len(on_ref) if len(on_ref) else np.nan
            val = p.loc[T, col]
            rows.append(dict(moment=mid, symbol=sym, side=side, turn_bar=T.strftime("%H:%M"), feature=col, family=fam,
                             kind=kind, value_T=val,
                             pct_T=round(pct_rank(ref[col], val), 1) if not kind.startswith(("bin", "cross", "near")) else np.nan,
                             value_T_minus10=p[col].shift(10).loc[T], value_T_minus30=p[col].shift(30).loc[T],
                             flag_at_T=atT, first_flag_min_before=int((T - first).total_seconds() // 60) if first is not None else np.nan,
                             lit_run_started_min_before=run_start,
                             share_of_prior60_flagged=round(pre.mean(), 2),
                             only_after_T=bool((not atT) and post.any()),
                             onsets_20d=len(on_ref), onsets_per_session=round(len(on_ref) / 20, 2),
                             precision_20d=round(prec, 3), base_rate=round(base, 3),
                             lift=round(prec / base, 2) if base and np.isfinite(prec) else np.nan,
                             precision2_20d=round(prec2, 3), base2=round(base2, 3),
                             lift2=round(prec2 / base2, 2) if base2 and np.isfinite(prec2) else np.nan,
                             onsets_1009=len(on_day), hits_1009=int(hits_day)))
            if not kind.startswith("near") and fam not in ("inside", "outside"):
                lit_series.append(f_win.rename(col))
        # confluence: number of side-specific flags lit (on in T-2..T) per minute
        L = pd.concat(lit_series, axis=1)
        L3 = L.rolling(3, min_periods=1).max().fillna(0)
        L3 = L3.where(win.tod >= 932, L.fillna(0).astype(float))   # no carry-over from the prior session
        cnt = L3.sum(axis=1)
        cT_ = cnt.loc[T]
        ok = (win.tod >= 935) & (win.tod <= 1530)
        rc = cnt[ok & win.date.isin(ref_days)]
        ge = rc >= cT_
        conf_rows.append(dict(moment=mid, symbol=sym, side=side, n_features=L.shape[1], lit_at_T=int(cT_),
                              pct_of_count_20d=round(pct_rank(rc, cT_), 1),
                              mean_count_20d=round(rc.mean(), 1), median_count_20d=float(rc.median()),
                              minutes_20d_with_count_ge=int(ge.sum()), sessions_with_any=int(win.loc[ge[ge].index, "date"].nunique()),
                              precision_count_ge=round(win.loc[ge[ge].index, hit_col].mean(), 3),
                              base_rate=round(win.loc[rc.index, hit_col].mean(), 3),
                              precision2_count_ge=round(win.loc[ge[ge].index, hit2].mean(), 3),
                              base2=round(win.loc[rc.index, hit2].mean(), 3),
                              minutes_1009_with_count_ge=int((cnt[ok & (win.date == DAY)] >= cT_).sum()),
                              max_count_1009=int(cnt[ok & (win.date == DAY)].max())))
    pd.DataFrame(mom_rows).to_csv(HERE / "moments.csv", index=False)
    pd.DataFrame(rows).to_csv(HERE / "panel_at_turns.csv", index=False)
    pd.DataFrame(conf_rows).to_csv(HERE / "confluence.csv", index=False)
    pd.DataFrame(mkt_rows).to_csv(HERE / "market.csv", index=False)
    print(pd.DataFrame(mom_rows).drop(columns=["note"]).to_string())
    print(pd.DataFrame(mkt_rows).to_string())
    print(pd.DataFrame(conf_rows).to_string())


if __name__ == "__main__":
    main()
