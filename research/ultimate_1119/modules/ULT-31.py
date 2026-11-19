# ULTIMATE CANDIDATE ULT-31 EARN-AWARE RANK (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-31"; backtest research/ultimate_1119/round4/ULT-31/RESULTS.md
# Next: only a TIER A / BEATS result goes further, with the owner's yes AND (wherever earnings-window rows trade) an owner
# exception to the 4-day earnings blackout (config earnings_blackout_days: 4). Educational only - not financial advice.
"""ULT-31 EARN-AWARE RANK - learned ranker with information-state (earnings) features, LONG + SHORT. PARTLY
CHECK-INFORMED.

Rows: every (decision 5-min bar close 10:00-15:00, name, side). A regularised model trained on FIT only scores each row
for a 45-minute time-exit trade (after-cost R per 2u). The setup takes the better side per name and enters when that
side's score is above a fixed threshold tau. The fitted model (scaler, weights or trees, tau, universe) is frozen in
ULT-31_model.json beside this module (written by round4/ULT-31/bt.py from FIT data only) and evaluated with numpy only.

Universes (UNIVS; the frozen model JSON's "univ" picks one):
  ALL  ADV20 >= $100M, cost_r <= 0.05
  EVT  names on an earnings reaction day RD or RD+1, ADV20 >= $30M, cost_r <= 0.08
Intake (both): price >= $10; |gap| < 20%; atr_d > 0; SPY context present. cost_r = LR8 stop round trip
  ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d.
Universal filters: long - not (SPY from open in [-0.75%, -0.30%] and SPY 30-min change < 0); short - gap < +0.5%,
  RSI5 >= 25, never a leveraged / inverse / volatility fund (LEV, ULT-31_symbols.json), easy-to-borrow (broker live;
  universe.csv flag in the backtest).
Earnings state (point-in-time; reaction_days() = ULT-28's: bmo -> report date, amc -> next session, dmh / unknown
  excluded, repeats within 10 sessions keep the first):
  e_rd   today is RD;  e_rd1  today is RD+1;  e_pre  an RD falls 1-3 sessions after today (scheduled date);
  e_bmo  today's RD / RD+1 event was a before-open report;  e_surp  its EPS surprise % (public before the RD open);
  e_react  REACT = close(RD)/close(RD-1) - 1 minus SPY's, % (known before the RD+1 open; RD+1 rows only);
  e_win  RD-1..RD+1 (borrow-fee window, backtest only).
Features (31, s = +1 long / -1 short; z-scored with the FIT scaler, clipped +-5, NaN -> 0):
  5 time blocks; s x gap; s x from_open_dATR; s x vwap_dist_dATR; s x (RSI14 - 50); s x (RSI5 - 50);
  s x 1[RSI2 <= 5]; s x 1[RSI2 >= 95]; s x di_diff7; s x spy_fo; s x spy_r30; s x qqq_fo; s x sector-ETF fromOpen;
  atr_d%; cost_r; log10 ADV20; is_ETF; volumeRatio; is_long;
  e_rd; e_rd1; e_pre; e_bmo; s x sign(surprise) x (e_rd|e_rd1); s x clip(surprise, +-30)/30 x (e_rd|e_rd1);
  s x gap x e_rd; s x REACT x e_rd1.
Enter: score > tau AND score >= the other side's score (when eligible).
Refire (THIN): max 2 per symbol-session, the 2nd >= 15 decision bars after the 1st (backtest chain: >= 30 min after the
  first lot's exit, one lot per symbol).
Two sides, one file: a setup name ending in "-S" / "-short" is the short side, anything else the long side.
Exit: GEOM "S": stop_price = decision close -/+ 2u (catastrophic), no target; YAML time_stop_min 45, time_stop_min_r 99.
Account side (not in the module): <= 3 entries per decision bar over both sides (highest score first), session cap 2k,
one lot per symbol. Context: `context: [spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap]`.
Live earnings source: the calendar CAL (env MCF_EARN_CAL; parquet with the earnings_yf columns symbol, date, session,
surprise_pct) and the daily closes DAILY (env MCF_DAILY_CLOSES; symbol, date, close; dated before today, must include
SPY), read once per import by today_state() through the same earn_state() the backtest uses. With EVT, SYMBOLS (YAML
`symbols: module`) = today's RD / RD+1 names. Missing files -> empty state (EVT: no trades; ALL: earnings features 0).
LIVE GAPS (RESULTS.md): the live lab frame has no `symbol` column, so the per-symbol earnings state, is_ETF and the
no-LEV-short rule need a frame `symbol` column (runner extension) or SYMBOL_HINT; the frame has no adv20 (log ADV -> z 0)
and no sector columns (sector feature -> z 0). In the backtest the frame carries e_* columns, which take precedence."""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
WINDOW = (1000, 1500)
H = 45
_HERE = Path(__file__).resolve().parent
MODEL_PATH = _HERE / "ULT-31_model.json"
_SYM = json.loads((_HERE / "ULT-31_symbols.json").read_text())
ETFS = frozenset(_SYM["ETF"])
LEV = frozenset(_SYM["LEV"])
UNIVS = {"ALL": (100_000_000, 0.05), "EVT": (30_000_000, 0.08)}
UNIV = "ALL"
MAX_PER_DAY, REFIRE_BARS = 2, 15
SYMBOL_HINT = None
REPEAT_SESSIONS = 10
BLOCKS = ((950, 1029), (1030, 1129), (1130, 1259), (1300, 1359), (1400, 1500))
EARN_COLS = ("e_rd", "e_rd1", "e_pre", "e_bmo", "e_surp", "e_react")
FEATS = ([f"blk{i}" for i in range(5)] +
         ["s_gap", "s_fo_d", "s_vwap_d", "s_rsi14", "s_rsi5", "s_rsi2lo", "s_rsi2hi", "s_di7", "s_spy_fo", "s_spy_r30",
          "s_qqq_fo", "s_sec_fo", "atr_pct", "cost_r", "log_adv", "is_etf", "vol_ratio", "is_long",
          "e_rd", "e_rd1", "e_pre", "e_bmo", "s_surp_sign", "s_surp_clip", "s_gap_rd", "s_react_rd1"])
NYSE_HOLIDAYS = frozenset("""
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27
2025-12-25 2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26
2026-12-25 2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25
2027-12-24""".split())
_STATE = Path(__file__).resolve().parents[3] / "state" / "earnings"
CAL = Path(os.environ.get("MCF_EARN_CAL", str(_STATE / "earnings_cal.parquet")))
DAILY = Path(os.environ.get("MCF_DAILY_CLOSES", str(_STATE / "daily_closes.parquet")))
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r and ADV20 floor of the frozen universe (ALL / EVT = RD or RD+1 names)",
    "side filters: long not into a falling SPY; short gap < +0.5%, RSI5 >= 25, easy to borrow, no leveraged ETF",
    "learned ranker over price + information-state (earnings) features (ULT-31_model.json, FIT only): better side "
    "per name, score > tau",
    "window: bar close 1000-1500 ET; exit: 45-min time exit, 2u catastrophic stop",
]
_MODEL = {}


# ---------------------------------------------------------------- earnings state (shared by backtest and live)
def sessions(start: str, end: str) -> list:
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in NYSE_HOLIDAYS:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def reaction_days(earn, sess):
    """= modules/ULT-28.py reaction_days(): symbol, rd, rd_i, session, report_date, surprise_pct (clip +-100)."""
    import pandas as pd
    e = earn[earn["session"].isin(["bmo", "amc"])].copy()
    e["report_date"] = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    arr = np.array(sess)
    side = np.where(e["session"].to_numpy() == "amc", "right", "left")
    i_l = np.searchsorted(arr, e["report_date"].to_numpy(), side="left")
    i_r = np.searchsorted(arr, e["report_date"].to_numpy(), side="right")
    e["rd_i"] = np.where(side == "right", i_r, i_l)
    e = e[(e["rd_i"] < len(arr)) & (e["report_date"] >= arr[0])]
    e["rd"] = arr[e["rd_i"].to_numpy()]
    e["surprise_pct"] = e["surprise_pct"].astype(float).clip(-100, 100)
    e = e.sort_values(["symbol", "rd_i"], kind="mergesort")
    keep, last = [], {}
    for idx, sym, ri in zip(e.index, e["symbol"].astype(str), e["rd_i"]):
        if sym in last and ri - last[sym] < REPEAT_SESSIONS:
            continue
        last[sym] = ri
        keep.append(idx)
    return e.loc[keep, ["symbol", "rd", "rd_i", "session", "report_date", "surprise_pct"]].reset_index(drop=True)


def earn_state(earn, sess, daily, drop=None):
    """Per (symbol, date) earnings state for sessions in sess: columns symbol, date, e_rd, e_rd1, e_pre, e_bmo, e_surp,
    e_react, e_win. daily: symbol, date, close (only closes of RD-1 and RD are used, for RD+1 rows). drop(dates) ->
    bool mask: events whose RD-1 / RD / RD+1 hit it are removed (the locked block in the backtest; never filled)."""
    import pandas as pd
    ev = reaction_days(earn, sess)
    arr = np.array(sess)
    n = len(arr)
    ri = ev["rd_i"].to_numpy()
    rdm1 = np.where(ri >= 1, arr[np.clip(ri - 1, 0, n - 1)], "")
    rdp1 = np.where(ri + 1 < n, arr[np.clip(ri + 1, 0, n - 1)], "")
    if drop is not None:
        bad = drop(ev["rd"].to_numpy()) | drop(rdm1) | drop(rdp1)
        ev, ri, rdm1, rdp1 = ev[~bad].reset_index(drop=True), ri[~bad], rdm1[~bad], rdp1[~bad]
    dl = daily[["symbol", "date", "close"]].copy()
    dl["date"] = pd.to_datetime(dl["date"]).dt.strftime("%Y-%m-%d")
    cl = dict(zip(dl["symbol"].astype(str) + "|" + dl["date"], dl["close"].astype(float)))
    sym = ev["symbol"].astype(str).to_numpy()
    g = lambda s, d: np.array([cl.get(a + "|" + b, np.nan) for a, b in zip(s, d)], float)   # noqa: E731
    with np.errstate(invalid="ignore", divide="ignore"):
        react = ((g(sym, ev["rd"]) / g(sym, rdm1) - 1) - (g(np.full(len(sym), "SPY"), ev["rd"]) /
                                                         g(np.full(len(sym), "SPY"), rdm1) - 1)) * 100
    bmo = (ev["session"].to_numpy() == "bmo").astype(float)
    surp = ev["surprise_pct"].to_numpy(float)
    rows = []
    z = np.zeros(len(ev))
    rows.append(pd.DataFrame({"symbol": sym, "i": ri, "e_rd": 1.0, "e_rd1": z, "e_pre": z, "e_bmo": bmo, "e_surp": surp,
                              "e_react": np.nan, "e_win": 1.0}))
    rows.append(pd.DataFrame({"symbol": sym, "i": ri + 1, "e_rd": z, "e_rd1": 1.0, "e_pre": z, "e_bmo": bmo,
                              "e_surp": surp, "e_react": react, "e_win": 1.0}))
    for k in (1, 2, 3):
        rows.append(pd.DataFrame({"symbol": sym, "i": ri - k, "e_rd": z, "e_rd1": z, "e_pre": 1.0, "e_bmo": z,
                                  "e_surp": np.nan, "e_react": np.nan, "e_win": 1.0 if k == 1 else 0.0}))
    s = pd.concat(rows, ignore_index=True)
    s = s[(s.i >= 0) & (s.i < n)]
    s["date"] = arr[s.i.to_numpy()]
    agg = {"e_rd": "max", "e_rd1": "max", "e_pre": "max", "e_bmo": "max", "e_surp": "first", "e_react": "first",
           "e_win": "max"}
    s = s.sort_values(["symbol", "date", "e_rd", "e_rd1"], ascending=[True, True, False, False])
    out = s.groupby(["symbol", "date"], as_index=False).agg(agg)
    act = (out.e_rd + out.e_rd1) > 0
    out.loc[~act, "e_bmo"] = 0.0
    if drop is not None:
        out = out[~drop(out["date"].to_numpy())]
    return out.reset_index(drop=True)


def today_state(day=None) -> dict:
    """Live: {symbol: {e_rd, ..., e_react}} for today from CAL + DAILY (closes strictly before today). Fail safe -> {}."""
    try:
        import pandas as pd
        day = day or datetime.now().strftime("%Y-%m-%d")
        if not CAL.exists():
            return {}
        d0 = (date.fromisoformat(day) - timedelta(days=40)).isoformat()
        d1 = (date.fromisoformat(day) + timedelta(days=10)).isoformat()
        earn = pd.read_parquet(CAL, columns=["symbol", "date", "session", "surprise_pct"])
        earn = earn[pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d").between(d0, d1)]
        if DAILY.exists():
            daily = pd.read_parquet(DAILY, columns=["symbol", "date", "close"])
            daily = daily[pd.to_datetime(daily["date"]).dt.strftime("%Y-%m-%d") < day]
        else:
            daily = pd.DataFrame({"symbol": [], "date": [], "close": []})
        st = earn_state(earn, sessions(d0, d1), daily)
        st = st[st["date"] == day]
        return {r.symbol: {k: getattr(r, k) for k in EARN_COLS} for r in st.itertuples()}
    except Exception:
        return {}


STATE = today_state()
SYMBOLS = frozenset(s for s, v in STATE.items() if v["e_rd"] or v["e_rd1"])     # EVT allow-list (`symbols: module`)


# ---------------------------------------------------------------- features
def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _m2(t):
    t = np.asarray(t, float)
    return np.floor(t / 100) * 60 + t % 100


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def _symbols(df):
    if "symbol" in df.columns:
        return df["symbol"].astype(str).to_numpy()
    return np.full(len(df), SYMBOL_HINT if SYMBOL_HINT else "", dtype=object)


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _lag(v, key, mins, lag):
    import pandas as pd
    s = pd.Series(np.asarray(v, float), index=pd.MultiIndex.from_arrays([key, mins]))
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, mins - lag])).to_numpy(dtype=float)


def _rsi2(close, key):
    import pandas as pd
    s = pd.Series(close)
    d = s.groupby(key).diff()
    up, dn = d.clip(lower=0), (-d).clip(lower=0)
    au = up.groupby(key).transform(lambda x: x.ewm(alpha=0.5, adjust=False, ignore_na=True).mean())
    ad = dn.groupby(key).transform(lambda x: x.ewm(alpha=0.5, adjust=False, ignore_na=True).mean())
    with np.errstate(invalid="ignore", divide="ignore"):
        r = 100 - 100 / (1 + au / ad)
    r = np.where((ad == 0) & (au > 0), 100.0, r)
    return np.asarray(r, float)


def cost_r(df) -> np.ndarray:
    px, atr, tod = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        return (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)


def _earn(d, sym):
    """e_* columns: from the frame when present (backtest), else today's STATE by symbol (live)."""
    if all(k in d.columns for k in EARN_COLS):
        return {k: _col(d, k) for k in EARN_COLS}
    out = {k: np.zeros(len(d)) for k in ("e_rd", "e_rd1", "e_pre", "e_bmo")}
    out["e_surp"], out["e_react"] = np.full(len(d), np.nan), np.full(len(d), np.nan)
    for i, s in enumerate(sym):
        v = STATE.get(s)
        if v:
            for k in EARN_COLS:
                out[k][i] = v[k]
    return out


def build(df) -> dict:
    """Features, intake and side filters on the rows inside WINDOW. Point-in-time: only the row's own and earlier bars of
    the same symbol-day, its context columns, prior-day values (atr_d, gap, adv20), the prior-session sector map and the
    earnings state known before the session open."""
    from mcf.research.arena.indicators import compute
    n = len(df)
    tod_all = _col(df, "tod")
    sel = np.flatnonzero((tod_all >= WINDOW[0]) & (tod_all <= WINDOW[1]))
    # indicators use the session's bars from 09:50 (= the lab frames' first bar; the live frame starts earlier, so the
    # live build is clamped to the same rows), then the WINDOW rows are selected
    s950 = np.flatnonzero((tod_all >= 950) & (tod_all <= WINDOW[1]))
    d0 = df.iloc[s950]
    key0 = _keys(d0)
    di7_0 = compute(d0, names=["di_diff7"], context=False)["di_diff7"].to_numpy(float)
    rsi2_0 = _rsi2(_col(d0, "close"), key0)
    spy0 = _col(d0, "spy_fo")
    spy_r30_0 = ((1 + spy0 / 100) / (1 + _lag(spy0, key0, _m2(tod_all[s950]), 30) / 100) - 1) * 100
    pos = np.searchsorted(s950, sel)
    d = df.iloc[sel]
    t = tod_all[sel]
    c, atr = _col(d, "close"), _col(d, "atr_d")
    rsi, r5, gap = _col(d, "rsi"), _col(d, "rsi5"), _col(d, "gap")
    di7, rsi2, spy_r30 = di7_0[pos], rsi2_0[pos], spy_r30_0[pos]
    sym = _symbols(d)
    E = _earn(d, sym)
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = atr / c * 100
        fo = _col(d, "fromOpen")
        op = c / (1 + fo / 100)
        foa = (c - op) / atr
        vd = _col(d, "vwapDistPct")
        vwap_d = c * vd / (100 + vd) / atr
        sfo_spy = _col(d, "spy_fo")
        cr = cost_r(d)
        adv = _col(d, "adv20")
        is_etf = np.array([s in ETFS for s in sym], float)
        is_lev = np.array([s in LEV for s in sym], bool)
        base = (c >= 10) & (np.abs(gap) < 20) & (atr > 0) & np.isfinite(sfo_spy)
        long_ok = ~((sfo_spy >= -0.75) & (sfo_spy <= -0.30) & (spy_r30 < 0))
        short_ok = (gap < 0.5) & (r5 >= 25) & ~is_lev
        e_rd, e_rd1 = np.nan_to_num(E["e_rd"]), np.nan_to_num(E["e_rd1"])
        act = np.maximum(e_rd, e_rd1)
        surp = E["e_surp"]
        react = E["e_react"]
    blk = {f"blk{i}": ((t >= a) & (t <= b)).astype(float) for i, (a, b) in enumerate(BLOCKS)}
    common = {"atr_pct": atrp, "cost_r": cr, "log_adv": np.log10(np.where(adv > 0, adv, np.nan)), "is_etf": is_etf,
              "vol_ratio": _col(d, "volumeRatio"), "e_rd": e_rd, "e_rd1": e_rd1, "e_pre": np.nan_to_num(E["e_pre"]),
              "e_bmo": np.nan_to_num(E["e_bmo"]) * act, **blk}
    signed = {"s_gap": gap, "s_fo_d": foa, "s_vwap_d": vwap_d, "s_rsi14": rsi - 50, "s_rsi5": r5 - 50,
              "s_rsi2lo": (rsi2 <= 5).astype(float), "s_rsi2hi": (rsi2 >= 95).astype(float), "s_di7": di7,
              "s_spy_fo": sfo_spy, "s_spy_r30": spy_r30, "s_qqq_fo": _col(d, "qqq_fo"), "s_sec_fo": _col(d, "sec_fo"),
              "s_surp_sign": np.nan_to_num(np.sign(surp)) * act, "s_surp_clip": np.nan_to_num(np.clip(surp, -30, 30) / 30) * act,
              "s_gap_rd": np.nan_to_num(gap) * e_rd, "s_react_rd1": np.nan_to_num(react) * e_rd1}
    return {"n": n, "sel": sel, "common": common, "signed": signed, "base": base, "long_ok": long_ok,
            "short_ok": short_ok, "cost_r": cr, "adv": adv, "evt": act > 0}


def univ_ok(b, univ) -> np.ndarray:
    mn, cmax = UNIVS[univ]
    with np.errstate(invalid="ignore"):
        ok = b["base"] & (b["cost_r"] <= cmax)
        adv = b["adv"]
        if np.isfinite(adv).any():
            ok &= np.nan_to_num(adv) >= mn
    if univ == "EVT":
        ok &= b["evt"]
    return ok


def side_rows(b, sgn, univ) -> np.ndarray:
    return univ_ok(b, univ) & (b["long_ok"] if sgn > 0 else b["short_ok"])


def side_features(b, sgn) -> np.ndarray:
    m = len(b["sel"])
    F = dict(b["common"])
    F["is_long"] = np.full(m, 1.0 if sgn > 0 else 0.0)
    for k, v in b["signed"].items():
        F[k] = sgn * v
    return np.column_stack([np.asarray(F[k], float) for k in FEATS])


def zscore(X, model) -> np.ndarray:
    m, s = np.asarray(model["mean"]), np.asarray(model["sd"])
    with np.errstate(invalid="ignore"):
        Z = np.clip((X - m) / s, -5, 5)
    return np.nan_to_num(Z, nan=0.0)


def _trees_predict(Z, g):
    out = np.full(len(Z), float(g["baseline"]))
    for tr in g["trees"]:
        f, thr, le, ri, leaf, val = (np.asarray(tr[k]) for k in ("f", "thr", "l", "r", "leaf", "v"))
        node = np.zeros(len(Z), int)
        for _ in range(int(tr.get("depth", 8)) + 1):
            nl = ~leaf[node]
            if not nl.any():
                break
            go_left = Z[np.arange(len(Z)), f[node]] <= thr[node]
            node = np.where(nl, np.where(go_left, le[node], ri[node]), node)
        out += val[node]
    return out


def predict_z(Z, m) -> np.ndarray:
    if m["kind"] in ("ridge", "linear"):
        return Z @ np.asarray(m["w"]) + float(m["b"])
    return _trees_predict(Z, m)


def load_model(path=None):
    p = Path(path or MODEL_PATH)
    if str(p) not in _MODEL:
        _MODEL[str(p)] = json.loads(p.read_text())
    return _MODEL[str(p)]


def predict(df, model=None, b=None):
    """(score_long, score_short) per row of df; -inf where the side is not eligible."""
    model = model or load_model()
    b = b or build(df)
    univ = model.get("univ", UNIV)
    out = []
    for sgn in (1, -1):
        ok = side_rows(b, sgn, univ)
        p = np.full(b["n"], -np.inf)
        if ok.any():
            Z = zscore(side_features(b, sgn)[ok], model)
            p[b["sel"][ok]] = predict_z(Z, model["model"])
        out.append(p)
    return out[0], out[1]


def _thin(m, df):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    if not len(hit):
        return out
    key = _keys(df)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns or not MODEL_PATH.exists():   # fail safe: no context / no frozen model -> no signal
        return np.zeros(len(df), bool)
    model = load_model()
    pl, ps = predict(df, model)
    mine, other = (pl, ps) if _SGN > 0 else (ps, pl)
    m = np.isfinite(mine) & (mine > float(model["tau"])) & (mine >= other)
    return _thin(m, df)


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
