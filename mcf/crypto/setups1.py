"""First hand-built crypto setups (research/crypto_setups1/PREREG.md, SETUPS.md). Research only.

Engine ("E5c level fills"): every signal carries its own absolute levels, decided at its decision time `t`
(minutes since epoch; the close of the last bar used):
  lim     maker limit buy price. Fills ONLY on a later traded minute (volume > 0) whose low is strictly below it
          (round-2 Amendment-1 rule, as `exec1m`); fill price = lim, maker fee, no spread. Missed orders are
          counted, never chased.
  risk    stop distance (price); stop = lim - risk, taker (+ half-spread, slippage, stop extra), fills at the stop
          or at the minute's open on a gap; checked on the fill minute too (conservative).
  tgt     resting maker sell (absolute price; NaN / <= lim = none); fills only on a later traded minute whose high
          is strictly above it. Never on the fill minute.
  expiry  order life (minutes); hold = time stop (minutes after the fill), taker at the first minute at/after it.
One open position or resting order per pair; signals while busy are ignored. Long only (Alpaca spot).
Signals are built from clean traded-only bars (`exec1m.clean_traded`); fills use every minute of the
bad-print-filtered tape (`Minutes.from_bars(clean_prints(raw))`), as in rounds 2-3.
Educational only — not financial advice.
"""
from __future__ import annotations

import numba
import numpy as np
import pandas as pd

from .costs import CostModel
from .exec1m import Minutes, reprice, to_min
from .features import wilder

MAJORS = ("BTC", "ETH")
ALTS = ("SOL", "DOGE", "LINK", "UNI")
ALL6 = MAJORS + ALTS
FLOOR = {"BTC": 0.03, "ETH": 0.03}          # min stop distance (fraction of the limit); alts 0.04
ALT_FLOOR = 0.04
ATR4_K = 1.5                                # stop = max(1.5 x ATR(14, 4h), floor)
LIM_ATR1 = 0.25                             # default limit offset below the decision close, ATR(14, 1h) units
YEARS = {"2021": ("2021-01-01", "2022-01-01"), "2022": ("2022-01-01", "2023-01-01"),
         "2023": ("2023-01-01", "2024-01-01"), "2024": ("2024-01-01", "2025-01-01"),
         "2025-26": ("2025-01-01", "2026-05-26")}
SIG_COLS = ["t", "ref", "lim", "risk", "tgt", "expiry", "hold"]
# BLS CPI release days (08:30 ET). 2023-26 from research/beginner_1120/BEG-RULES/calendar.json; 2021-22 from the
# BLS schedule as recalled [verify]. Oct-2025 CPI was cancelled (shutdown).
CPI_DATES = ["2021-01-13", "2021-02-10", "2021-03-10", "2021-04-13", "2021-05-12", "2021-06-10", "2021-07-13",
             "2021-08-11", "2021-09-14", "2021-10-13", "2021-11-10", "2021-12-10", "2022-01-12", "2022-02-10",
             "2022-03-10", "2022-04-12", "2022-05-11", "2022-06-10", "2022-07-13", "2022-08-10", "2022-09-13",
             "2022-10-13", "2022-11-10", "2022-12-13", "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12",
             "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14",
             "2023-12-12", "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12",
             "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11", "2025-01-15",
             "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11", "2025-07-15", "2025-08-12",
             "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10",
             "2026-05-12"]


def floor_pct(pair: str) -> float:
    return FLOOR.get(pair, ALT_FLOOR)


# ------------------------------------------------------------------ engine
@numba.njit(cache=True)
def _sim_lv(t, o, h, l, c, trd, st, lim, risk, tgt, expiry, hold):
    n_sig = len(st)
    n = len(t)
    out = np.empty((n_sig, 7))       # sig, t_in, t_out, entry, exit, risk, kind
    k = 0
    missed = 0
    busy = -1
    for s in range(n_sig):
        ts = st[s]
        if ts < busy or not (risk[s] > 0) or not (lim[s] > 0):
            continue
        j = np.searchsorted(t, ts)
        if j >= n:
            break
        f = -1
        q = j
        while q < n and t[q] < ts + expiry[s]:
            if trd[q] and l[q] < lim[s]:
                f = q
                break
            q += 1
        if f < 0:
            missed += 1
            busy = ts + expiry[s]
            continue
        e = lim[s]
        stop = e - risk[s]
        tg = tgt[s] if tgt[s] > e else np.inf
        t_end = t[f] + hold[s]
        x = -1
        px = 0.0
        kind = 3
        for m in range(f, n):
            if m > f and t[m] >= t_end:
                x, px, kind = m, o[m], 0
                break
            if l[m] <= stop:
                px = stop if m == f else min(o[m], stop)
                x, kind = m, 1
                break
            if m > f and trd[m] and h[m] > tg:
                x, px, kind = m, tg, 2
                break
        if x < 0:
            x = n - 1
            px = c[n - 1]
            kind = 3
        out[k, 0] = s
        out[k, 1] = t[f]
        out[k, 2] = t[x]
        out[k, 3] = e
        out[k, 4] = px
        out[k, 5] = risk[s]
        out[k, 6] = kind
        k += 1
        busy = t[x] + 1
    return out[:k], missed


TRADE_COLS = ["pair", "sig", "entry_time", "exit_time", "day", "entry", "exit", "risk", "kind", "maker_in",
              "maker_out", "thin", "gross_r", "nonfee_r", "rpu", "fee_in", "fee_out", "fee_r", "cost_r", "r"]


def run_levels(pair: str, mins: Minutes, sig: pd.DataFrame, costs: CostModel | None = None,
               tier: int = 1) -> tuple[pd.DataFrame, int, int]:
    """Trades of one pair from a signal frame (SIG_COLS, sorted by t). Returns (trades, offered, missed)."""
    costs = costs or CostModel()
    if len(sig) == 0 or len(mins.t) == 0:
        return pd.DataFrame(columns=TRADE_COLS), len(sig), 0
    sig = sig.sort_values("t", kind="stable")
    f = lambda k, d=np.float64: np.ascontiguousarray(sig[k].to_numpy(d))  # noqa: E731
    out, missed = _sim_lv(mins.t, mins.o, mins.h, mins.l, mins.c, np.ascontiguousarray(mins.traded, np.bool_),
                          f("t", np.int64), f("lim"), f("risk"), f("tgt"), f("expiry", np.int64),
                          f("hold", np.int64))
    if len(out) == 0:
        return pd.DataFrame(columns=TRADE_COLS), len(sig), int(missed)
    t_in = pd.to_datetime(out[:, 1].astype(np.int64), unit="m", utc=True)
    t_out = pd.to_datetime(out[:, 2].astype(np.int64), unit="m", utc=True)
    en, xp, risk, kind = out[:, 3], out[:, 4], out[:, 5], out[:, 6].astype(int)
    maker_out = kind == 2
    years = t_in.year.to_numpy()
    nonfee = np.empty(len(out))
    for q in range(len(out)):
        b, _ = costs.leg(pair, int(years[q]), maker=bool(maker_out[q]), entry=False, stop_exit=bool(kind[q] == 1))
        nonfee[q] = b                                   # maker entry: no spread, no slippage
    rpu = en / risk
    df = pd.DataFrame({"pair": pair, "sig": out[:, 0].astype(int), "entry_time": t_in, "exit_time": t_out,
                       "day": t_in.floor("D"), "entry": en, "exit": xp, "risk": risk, "kind": kind,
                       "maker_in": True, "maker_out": maker_out, "thin": False, "gross_r": (xp - en) / risk,
                       "nonfee_r": nonfee * rpu, "rpu": rpu})
    reprice(df, tier)
    return df, len(sig), int(missed)


# ------------------------------------------------------------------ data prep (per pair)
def prep_pair(sig_1m: pd.DataFrame, end: pd.Timestamp) -> dict:
    """Hourly / 4h / daily frames from clean traded-only 1-min bars (o/h/l/c/v[/vw]). Everything at a row uses
    data up to that bar's close. Returns {"H": hourly grid, "A4": ATR(14,4h) by close time, "D": daily}."""
    s = sig_1m[sig_1m.index < end]
    g = pd.DataFrame({"o": s["o"].resample("60min").first(), "h": s["h"].resample("60min").max(),
                      "l": s["l"].resample("60min").min(), "c": s["c"].resample("60min").last(),
                      "nm": s["c"].resample("60min").count()})
    g["ok"] = g["c"].notna()
    g["cf"] = g["c"].ffill()                                     # last traded price at the hour's close
    g["r"] = np.log(g["c"] / g["c"].shift(1))                    # NaN unless both hours traded
    g["z"] = g["r"] / g["r"].rolling(720, min_periods=200).std().shift(1)
    hf = g[["o", "h", "l"]].copy()
    for k in ("o", "h", "l"):
        hf[k] = hf[k].fillna(g["cf"])
    pc = g["cf"].shift(1)
    tr = pd.concat([hf["h"] - hf["l"], (hf["h"] - pc).abs(), (hf["l"] - pc).abs()], axis=1).max(axis=1)
    g["atr1"] = wilder(tr, 14)
    q = pd.DataFrame({"h": s["h"].resample("240min").max(), "l": s["l"].resample("240min").min(),
                      "c": s["c"].resample("240min").last()})
    q["c"] = q["c"].ffill()
    q["h"] = q["h"].fillna(q["c"])
    q["l"] = q["l"].fillna(q["c"])
    pq = q["c"].shift(1)
    tr4 = pd.concat([q["h"] - q["l"], (q["h"] - pq).abs(), (q["l"] - pq).abs()], axis=1).max(axis=1)
    a4 = wilder(tr4, 14)
    a4.index = a4.index + pd.Timedelta("240min")                 # known at the 4h bar's close
    d = pd.DataFrame({"o": s["o"].resample("1D").first(), "h": s["h"].resample("1D").max(),
                      "l": s["l"].resample("1D").min(), "c": s["c"].resample("1D").last()})
    d["c"] = d["c"].ffill()
    for k in ("o", "h", "l"):
        d[k] = d[k].fillna(d["c"])
    d["sma50"] = d["c"].rolling(50, min_periods=50).mean()
    d["ret"] = d["c"] / d["c"].shift(1) - 1
    lr = np.log(d["c"] / d["c"].shift(1))
    d["zd"] = lr / lr.rolling(90, min_periods=60).std().shift(1)
    pdc = d["c"].shift(1)
    trd = pd.concat([d["h"] - d["l"], (d["h"] - pdc).abs(), (d["l"] - pdc).abs()], axis=1).max(axis=1)
    d["atr1d"] = wilder(trd, 14)
    d["up"] = d["c"] > d["sma50"]
    d["down_off"] = (d["c"] < d["sma50"]) & (d["sma50"] < d["sma50"].shift(10))
    return {"H": g, "A4": a4, "D": d}


def daily_at(d: pd.DataFrame, col: str, taus: pd.DatetimeIndex) -> np.ndarray:
    """Value of daily column `col` for the last COMPLETED UTC day at each decision time (day end <= tau)."""
    key = taus.floor("D") - pd.Timedelta("1D")      # a decision at 00:00 of D+1 or later inside D+1 sees day D
    return d[col].reindex(key).to_numpy()


def _flag(v: np.ndarray) -> np.ndarray:
    """Boolean array from a reindexed flag column (missing -> False)."""
    return np.array([bool(x) if not pd.isna(x) else False for x in v], bool)


def atr4_at(a4: pd.Series, taus: pd.DatetimeIndex) -> np.ndarray:
    s = a4.dropna()
    if s.empty:
        return np.full(len(taus), np.nan)
    i = np.searchsorted(s.index.values, taus.values, side="right") - 1
    v = np.where(i >= 0, s.to_numpy()[np.clip(i, 0, None)], np.nan)
    return v


def _frame(pair: str, P: dict, taus: pd.DatetimeIndex, ref, lim, tgt, expiry, hold, risk=None) -> pd.DataFrame:
    lim = np.asarray(lim, float)
    if risk is None:
        a4 = atr4_at(P[pair]["A4"], taus)
        risk = np.maximum(ATR4_K * np.nan_to_num(a4, nan=0.0), floor_pct(pair) * lim)
    risk = np.asarray(risk, float)
    n = len(taus)
    df = pd.DataFrame({"t": to_min(taus) if n else np.array([], np.int64), "ref": np.asarray(ref, float),
                       "lim": lim, "risk": risk,
                       "tgt": np.broadcast_to(np.asarray(tgt, float), n).copy() if n else np.array([]),
                       "expiry": np.broadcast_to(np.asarray(expiry, np.int64), n).copy() if n else np.array([], np.int64),
                       "hold": np.broadcast_to(np.asarray(hold, np.int64), n).copy() if n else np.array([], np.int64)})
    df = df[np.isfinite(df["lim"]) & (df["lim"] > 0) & np.isfinite(df["risk"])]
    return df.sort_values("t").reset_index(drop=True)


def _gate(P: dict, taus: pd.DatetimeIndex, gate: str | None) -> np.ndarray:
    if gate is None or len(taus) == 0:
        return np.ones(len(taus), bool)
    bd = P["BTC"]["D"]
    if gate == "not_down":
        known = ~pd.isna(daily_at(bd, "sma50", taus).astype(float))
        return known & ~_flag(daily_at(bd, "down_off", taus))
    if gate == "btc_up":
        return _flag(daily_at(bd, "up", taus))
    raise ValueError(gate)


# ------------------------------------------------------------------ setups (signal builders)
def sig_flush(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-FLUSH-1: a 1h flush (z <= -3) -> maker bid 0.25 ATR1h under its close, live 120 min; 12h time stop."""
    H = P[pair]["H"]
    m = H["ok"] & H["ok"].shift(1, fill_value=False) & (H["nm"] >= 3) & (H["z"] <= c.get("z", -3.0))
    g = H[m]
    taus = g.index + pd.Timedelta("60min")
    ok = _gate(P, taus, c.get("gate", "not_down"))
    g, taus = g[ok], taus[ok]
    return _frame(pair, P, taus, g["c"], g["c"] - LIM_ATR1 * g["atr1"], np.nan, 120, c.get("hold", 720))


def sig_shock(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-SHOCK-1: a -2..-3 sigma hour in the vol clock (weekday 13-21 UTC or the 00 UTC hour); skip one hour,
    then a maker bid 0.25 ATR1h under the next hour's close, live 60 min; 12h time stop."""
    H = P[pair]["H"]
    hr = H.index.hour
    clock = (H.index.dayofweek < 5) & (((hr >= 13) & (hr <= 20)) | (hr == 0))
    m = (H["ok"] & H["ok"].shift(1, fill_value=False) & (H["nm"] >= 3) & (H["z"] <= -2.0) & (H["z"] > -3.0)
         & clock)
    nxt = m.shift(1, fill_value=False) & H["ok"]                  # hour h+1 (must trade); decide at its close
    g = H[nxt]
    taus = g.index + pd.Timedelta("60min")
    ok = _gate(P, taus, "not_down")
    g, taus = g[ok], taus[ok]
    return _frame(pair, P, taus, g["c"], g["c"] - LIM_ATR1 * g["atr1"], np.nan, 60, 720)


def sig_rev12(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-REV12-1: at 00:00 / 12:00 UTC, prior 12h block return <= -2 sigma12 -> maker bid 0.25 ATR1h under,
    live 60 min; hold 12h. Weekday decisions only."""
    H = P[pair]["H"]
    last = H[H.index.hour.isin([11, 23])]                         # last hour of each 12h block
    r12 = np.log(last["cf"] / last["cf"].shift(1))
    sd = r12.rolling(180, min_periods=120).std().shift(1)
    m = (r12 <= -2.0 * sd) & last["ok"]
    g = last[m]
    taus = g.index + pd.Timedelta("60min")
    keep = taus.dayofweek < 5
    g, taus = g[keep], taus[keep]
    ok = _gate(P, taus, "not_down")
    g, taus = g[ok], taus[ok]
    return _frame(pair, P, taus, g["cf"], g["cf"] - LIM_ATR1 * g["atr1"], np.nan, 60, 720)


def sig_updip(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-UPDIP-1: an extreme up-day (UTC day z >= +2, weekday, BTC > SMA50) -> do not chase: next day, maker bid
    at a 50% retrace of the day's body, live 24h; target = the up-day close (maker); 24h time stop."""
    D = P[pair]["D"]
    body = D["c"] - D["o"]
    m = (D["zd"] >= 2.0) & (body > 0) & (D.index.dayofweek < 5)
    g = D[m]
    taus = g.index + pd.Timedelta("1D")
    ok = _gate(P, taus, "btc_up")
    g, taus = g[ok], taus[ok]
    lim = g["c"] - 0.5 * (g["c"] - g["o"])
    return _frame(pair, P, taus, g["c"], lim, g["c"].to_numpy(), 1440, 1440)


def _day2_thr(pair: str) -> float:
    return -0.08 if pair in MAJORS else -0.12


def sig_day2(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-DAY2-1: a crash day D (<= -8% majors, <= -12% alts). Variant 'reclaim': on D+1 00-16 UTC, after a
    trade below D's low, the first 1h close back above it -> maker bid at D's low, live 4h. Variant 'open':
    at 00:00 D+1 a maker bid 0.25 ATR1d under D's close, live 16h. Target = midpoint of D's range (>= +0.5R);
    24h time stop. No trend gate (the setup exists for crashes)."""
    D = P[pair]["D"]
    H = P[pair]["H"]
    crash = D[D["ret"] <= _day2_thr(pair)]
    taus, ref, lim, tgt = [], [], [], []
    for d0, row in crash.iterrows():
        d1 = d0 + pd.Timedelta("1D")
        mid = row["l"] + 0.5 * (row["h"] - row["l"])
        if c["mode"] == "reclaim":
            w = H[(H.index >= d1) & (H.index < d1 + pd.Timedelta("16h"))]
            swept = (w["l"] < row["l"]).cummax()
            hit = w[swept & w["ok"] & (w["c"] > row["l"])]
            if hit.empty:
                continue
            taus.append(hit.index[0] + pd.Timedelta("60min"))
            ref.append(hit["c"].iloc[0])
            lim.append(row["l"])
        else:
            taus.append(d1)
            ref.append(row["c"])
            lim.append(row["c"] - 0.25 * row["atr1d"])
        tgt.append(mid)
    taus = pd.DatetimeIndex(taus) if taus else pd.DatetimeIndex([], tz="UTC")
    df = _frame(pair, P, taus, ref, lim, tgt, 240 if c["mode"] == "reclaim" else 960, 1440)
    df["tgt"] = np.maximum(df["tgt"], df["lim"] + 0.5 * df["risk"])
    return df


def friday_close_times(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Fri 16:00 America/New_York in UTC (20:00 in summer, 21:00 in winter)."""
    days = pd.date_range(start.tz_convert(None).normalize(), end.tz_convert(None).normalize(), freq="W-FRI")
    et = (days + pd.Timedelta("16h")).tz_localize("America/New_York")
    return et.tz_convert("UTC")


def sig_wknd(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-WKND-1: weekend low <= Friday close (16:00 ET) -4% majors / -6% alts; then the first 1h close back
    above the Friday close between Sun 22:00 and Mon 15:00 UTC -> maker bid at the Friday close, live 4h;
    target max(weekend high, +1R) maker; 24h time stop; BTC down-trend switch-off."""
    H = P[pair]["H"]
    thr = 0.04 if pair in MAJORS else 0.06
    taus, ref, lim, tgt = [], [], [], []
    for fc_t in friday_close_times(H.index[0], H.index[-1]):
        pre = H["cf"][H.index < fc_t]
        if pre.empty or not np.isfinite(pre.iloc[-1]):
            continue
        fc = pre.iloc[-1]
        sun22 = (fc_t.normalize() + pd.Timedelta(days=2, hours=22))
        wk = H[(H.index >= fc_t) & (H.index < sun22)]
        if wk.empty or not (wk["l"].min() <= fc * (1 - thr)):
            continue
        mon15 = sun22 + pd.Timedelta("17h")
        w = H[(H.index >= sun22) & (H.index <= mon15 - pd.Timedelta("60min"))]   # hour closes in (Sun 22, Mon 15]
        hit = w[w["ok"] & (w["c"] > fc)]
        if hit.empty:
            continue
        taus.append(hit.index[0] + pd.Timedelta("60min"))
        ref.append(hit["c"].iloc[0])
        lim.append(fc)
        tgt.append(wk["h"].max())
    taus = pd.DatetimeIndex(taus) if taus else pd.DatetimeIndex([], tz="UTC")
    ok = _gate(P, taus, "not_down")
    keep = np.flatnonzero(ok)
    taus = taus[keep]
    ref, lim, tgt = (np.asarray(x, float)[keep] for x in (ref, lim, tgt))
    df = _frame(pair, P, taus, ref, lim, tgt, 240, 1440)
    df["tgt"] = np.maximum(df["tgt"], df["lim"] + df["risk"])
    return df


def sig_cpi(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-CPI-1: CPI day, 08:45 ET: price >= +1.2% vs the 08:29 print and above the 08:30-08:45 VWAP -> maker bid
    at that VWAP, live 30 min; stop at the 08:29 price (>= 2%); target +2R maker; time stop 16:00 ET (435 min)."""
    s = P[pair]["M1"]
    taus, ref, lim, risk = [], [], [], []
    for d in CPI_DATES:
        t830 = pd.Timestamp(f"{d} 08:30", tz="America/New_York").tz_convert("UTC")
        t845 = t830 + pd.Timedelta("15min")
        pre = s[(s.index < t830) & (s.index >= t830 - pd.Timedelta("6h"))]
        win = s[(s.index >= t830) & (s.index < t845)]
        if pre.empty or win.empty or win["v"].sum() <= 0:
            continue
        p0, p1 = pre["c"].iloc[-1], win["c"].iloc[-1]
        vw = float((win["vw"].fillna(win["c"]) * win["v"]).sum() / win["v"].sum())
        if p1 >= p0 * 1.012 and p1 > vw:
            taus.append(t845)
            ref.append(p1)
            lim.append(vw)
            risk.append(max(vw - p0, 0.02 * vw))
    taus = pd.DatetimeIndex(taus) if taus else pd.DatetimeIndex([], tz="UTC")
    df = _frame(pair, P, taus, ref, lim, np.nan, 30, 435, risk=risk)
    df["tgt"] = df["lim"] + 2 * df["risk"]
    return df


def sig_dip(P: dict, pair: str, c: dict) -> pd.DataFrame:
    """CRY-DIP-1: oversold inside an uptrend. At each 4h close (weekdays): 24h return <= -1.5 sigma24, the coin's
    and BTC's last daily close > their SMA50 -> maker bid 0.25 ATR1h under, live 4h; 24h time stop."""
    H = P[pair]["H"]
    D = P[pair]["D"]
    q = H[(H.index.hour % 4) == 3]                                # last hour of each 4h block
    r24 = np.log(q["cf"] / q["cf"].shift(6))
    sd = r24.rolling(540, min_periods=360).std().shift(1)
    taus_all = q.index + pd.Timedelta("60min")
    m = (r24 <= -1.5 * sd).to_numpy() & q["ok"].to_numpy() & (taus_all.dayofweek < 5)
    own = daily_at(D, "up", taus_all)
    m &= _flag(own)
    g, taus = q[m], taus_all[m]
    ok = _gate(P, taus, "btc_up")
    g, taus = g[ok], taus[ok]
    return _frame(pair, P, taus, g["cf"], g["cf"] - LIM_ATR1 * g["atr1"], np.nan, 240, 1440)


BUILDERS = {"flush": sig_flush, "shock": sig_shock, "rev12": sig_rev12, "updip": sig_updip, "day2": sig_day2,
            "wknd": sig_wknd, "cpi": sig_cpi, "dip": sig_dip}


# ------------------------------------------------------------------ random baseline + stats
def random_signals(rng: np.random.Generator, sig: pd.DataFrame, H: pd.DataFrame, a: pd.Timestamp,
                   z: pd.Timestamp) -> pd.DataFrame:
    """Same number of signals at random real-hour closes in [a, z), each with the geometry (limit offset, stop and
    target as fractions of the limit, expiry, hold) of a random real signal of the same pair."""
    if len(sig) == 0:
        return sig
    taus = H.index[H["ok"].to_numpy()] + pd.Timedelta("60min")
    taus = taus[(taus >= a) & (taus < z)]
    if len(taus) == 0:
        return sig.iloc[:0]
    pick = np.sort(rng.choice(len(taus), min(len(sig), len(taus)), replace=False))
    tt = taus[pick]
    ref = H["c"].reindex(tt - pd.Timedelta("60min")).to_numpy()
    g = sig.iloc[rng.integers(0, len(sig), len(tt))]
    lim = ref * (g["lim"] / g["ref"]).to_numpy()
    out = pd.DataFrame({"t": to_min(tt), "ref": ref, "lim": lim, "risk": lim * (g["risk"] / g["lim"]).to_numpy(),
                        "tgt": lim * (g["tgt"] / g["lim"]).to_numpy(), "expiry": g["expiry"].to_numpy(),
                        "hold": g["hold"].to_numpy()})
    return out.sort_values("t").reset_index(drop=True)


def max_dd_r(trades: pd.DataFrame) -> float:
    if len(trades) == 0:
        return 0.0
    eq = trades.sort_values("exit_time")["r"].cumsum().to_numpy()
    eq = np.concatenate([[0.0], eq])
    return float((np.maximum.accumulate(eq) - eq).max())


def active_days(trades: pd.DataFrame) -> pd.DatetimeIndex:
    """UTC days on which the setup held a position (any pair)."""
    if len(trades) == 0:
        return pd.DatetimeIndex([], tz="UTC")
    days = []
    for a, b in zip(trades["entry_time"], trades["exit_time"]):
        days.append(pd.date_range(a.floor("D"), b.floor("D"), freq="D"))
    return pd.DatetimeIndex(np.unique(np.concatenate([d.values for d in days]))).tz_localize("UTC")


def by_year(trades: pd.DataFrame) -> dict:
    out = {}
    for k, (a, b) in YEARS.items():
        m = (trades["entry_time"] >= pd.Timestamp(a, tz="UTC")) & (trades["entry_time"] < pd.Timestamp(b, tz="UTC"))
        x = trades.loc[m, "r"]
        out[k] = (int(len(x)), float(x.mean()) if len(x) else np.nan)
    return out
