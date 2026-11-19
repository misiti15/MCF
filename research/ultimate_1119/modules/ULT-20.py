# ULTIMATE CANDIDATE ULT-20 EVR (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-20"; backtest research/ultimate_1119/round3/ULT-20/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-20 EVR - event-conditioned learned ranker, LONG and SHORT, decision bars 09:50-15:00. CHECK-INFORMED.

Only (bar, name, side) rows where at least one library trigger of that side fires are ranked. A regularised model trained
on FIT only scores each such row for a 45-minute time-exit trade (after-cost R per 2u); the setup takes the better side
per name and enters when that side's score is above a fixed threshold tau. The fitted model (scaler, weights or trees,
tau, universe) is frozen in ULT-20_model.json beside this module (written by round3/ULT-20/bt.py from FIT data only)
and evaluated with numpy only (no sklearn at run time).

Events (decision 5-min bar close, point-in-time; frame columns rsi = RSI14, rsi5, buyPressure 19-bar, dist_hod_atr /
dist_lod_atr in daily ATRs, sma20_dist_pct, upper_wick; ret3 / ret12 / di_diff7 / atr_d_pct via
mcf.research.arena.indicators.compute as WB4):
  long  L1 WB4-A dip: ret3 <= -0.21 x atr_d% AND ret12 >= -0.28 x atr_d% AND di_diff7 >= -5
        L2 one-bar RSI14 collapse: RSI14[prev bar] >= 50 AND RSI14 <= 35 AND buyPressure > 0
        L3 RSI5 up-cross 30 on this or the previous bar AND buyPressure > 0
        L4 depth: from_open_dATR <= -1.0 OR dist_hod_atr >= 1.5
        L5 RSI2 <= 5 (Wilder RSI(2) of the session's 5-min closes from 09:50)
  short S1 pop: 60 <= RSI5 < 90 AND dist_lod_atr >= 0.5 AND |sma20_dist_pct| >= 1.5
        S2 roll-over: RSI5[prev] >= 80 AND RSI5 < RSI5[prev] AND upper_wick > 0
        S3 from_open_dATR >= +1.0
        S4 RSI2 >= 95
  both  E5 sector lag (ULT-17 rule, S 0.15, LMIN 0.10) in the sector's direction (needs sec_fo / sec_atrp / sec_beta
        columns; missing -> no E5)
Intake (UNIV): price >= $10; |gap| < 20%; atr_d > 0; cost_r <= COST_R_MAX (LR8 stop round trip ((1c + 1bp) x tod mult
  + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= MIN_ADV (frame adv20 when present, else YAML min_adv).
Universal filters: long - not (SPY from open in [-0.75%, -0.30%] and SPY 30-min change < 0); short - gap < +0.5%,
  RSI5 >= 25, never a leveraged / inverse / volatility ETF (LEV list, ULT-20_symbols.json), easy-to-borrow (broker live;
  universe.csv flag in the backtest).
Features (29, z-scored with the FIT scaler, clipped +-5, NaN -> 0): 9 event flags L1-L5 S1-S4, E5 in the row's side,
  is_long, number of the row side's events, 5 time blocks, s x gap, s x from_open_dATR, s x vwap_dist_dATR,
  s x (RSI14 - 50), s x di_diff7, atr_d%, cost_r, log10 ADV20, is_ETF, volumeRatio, s x spy_fo, s x spy_r30 (s = +1 long,
  -1 short). One pooled model for both sides (side enters through is_long and the signed features).
Enter: the row's side has >= 1 event AND score > tau AND score >= the other side's score (when eligible).
Refire (THIN): max 2 per symbol-session, the 2nd >= 15 decision bars after the 1st (backtest chain: >= 30 min after the
  first lot's exit, one lot per symbol).
Two sides, one file: LabStrategy has one side per setup, so the account carries TWO `type: lab` entries pointing at this
file; a setup name ending in "-S" / "-short" is the short side, anything else the long side.
Exit: GEOM "S": stop_price = decision close -/+ 2u (catastrophic), no target; YAML time_stop_min 45, time_stop_min_r 99.
Account side (not in the module): <= 3 entries per decision bar over both sides (highest score first), session cap 2k,
one lot per symbol. Context: `context: [spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap]`.
LIVE GAPS (RESULTS.md): the live lab frame has no adv20 (log ADV -> z 0) and no sector columns (E5 never fires live);
is_ETF needs the symbol (frame `symbol` column or module SYMBOL_HINT); a runner extension is needed before live use."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
WINDOW = (950, 1500)
H = 45
MODEL_PATH = Path(__file__).resolve().parent / "ULT-20_model.json"
_SYM = json.loads((Path(__file__).resolve().parent / "ULT-20_symbols.json").read_text())
ETFS = frozenset(_SYM["ETF"])
LEV = frozenset(_SYM["LEV"])
UNIVS = {"L1": (100_000_000, 0.05), "L2": (50_000_000, 0.08)}
UNIV = "L1"                      # overwritten from the frozen model JSON ("univ") when it is present
MAX_PER_DAY, REFIRE_BARS = 2, 15
SYMBOL_HINT = None               # live single-symbol frames without a `symbol` column may set this
BLOCKS = ((950, 1029), (1030, 1129), (1130, 1259), (1300, 1359), (1400, 1500))
EVL = ("L1", "L2", "L3", "L4", "L5")
EVS = ("S1", "S2", "S3", "S4")
FEATS = (["evL1", "evL2", "evL3", "evL4", "evL5", "evS1", "evS2", "evS3", "evS4", "evE5", "is_long", "n_ev"] +
         [f"blk{i}" for i in range(5)] +
         ["s_gap", "s_fo_d", "s_vwap_d", "s_rsi14", "s_di7", "atr_pct", "cost_r", "log_adv", "is_etf", "vol_ratio",
          "s_spy_fo", "s_spy_r30"])
E5_S, E5_LMIN = 0.15, 0.10
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r and ADV20 floor of the frozen universe",
    "at least one library event of this side (dip / RSI collapse / RSI5 up-cross / depth / RSI2 <= 5 long; "
    "pop / roll-over / +1 ATR from open / RSI2 >= 95 short; sector lag both)",
    "side filters: long not into a falling SPY; short gap < +0.5%, RSI5 >= 25, easy to borrow, no leveraged ETF",
    "learned ranker (ULT-20_model.json, FIT only): better side per name, score > tau",
    "window: bar close 0950-1500 ET; exit: 45-min time exit, 2u catastrophic stop",
]
_MODEL = {}


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
    """v at (same key, mins - lag), exact time match; NaN otherwise."""
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


def build(df) -> dict:
    """Events, side filters and shared feature parts for every row (rows before 09:50 / after 15:00 get NaN / False).
    Point-in-time: only the row's own and earlier bars of the same symbol-day, the row's context columns, prior-day
    values (atr_d, gap, adv20) and the prior-session sector map."""
    from mcf.research.arena.indicators import compute
    n = len(df)
    tod_all = _col(df, "tod")
    sel = np.flatnonzero((tod_all >= WINDOW[0]) & (tod_all <= WINDOW[1]))
    d = df.iloc[sel]
    key = _keys(d)
    t = _col(d, "tod")
    mins = _m2(t)
    c, atr = _col(d, "close"), _col(d, "atr_d")
    ind = compute(d, names=["atr_d_pct", "di_diff7", "ret3", "ret12"], context=False)
    ret3, ret12 = ind["ret3"].to_numpy(float), ind["ret12"].to_numpy(float)
    di7, atrp_i = ind["di_diff7"].to_numpy(float), ind["atr_d_pct"].to_numpy(float)
    rsi, r5, bp = _col(d, "rsi"), _col(d, "rsi5"), _col(d, "buyPressure")
    gap = _col(d, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = atr / c * 100
        fo = _col(d, "fromOpen")
        op = c / (1 + fo / 100)
        foa = (c - op) / atr
        vd = _col(d, "vwapDistPct")
        vwap_d = c * vd / (100 + vd) / atr
        rsi2 = _rsi2(c, key)
        rsi_p, r5_p = _lag(rsi, key, mins, 5), _lag(r5, key, mins, 5)
        ev = {}
        ev["L1"] = (ret3 <= -0.21 * atrp_i) & (ret12 >= -0.28 * atrp_i) & (di7 >= -5)
        ev["L2"] = (rsi_p >= 50) & (rsi <= 35) & (bp > 0)
        up30 = (r5 >= 30) & (r5_p < 30)
        up30_p = _lag(up30.astype(float), key, mins, 5) == 1.0
        ev["L3"] = (up30 | up30_p) & (bp > 0)
        ev["L4"] = (foa <= -1.0) | (_col(d, "dist_hod_atr") >= 1.5)
        ev["L5"] = rsi2 <= 5
        ev["S1"] = (r5 >= 60) & (r5 < 90) & (_col(d, "dist_lod_atr") >= 0.5) & (np.abs(_col(d, "sma20_dist_pct")) >= 1.5)
        ev["S2"] = (r5_p >= 80) & (r5 < r5_p) & (_col(d, "upper_wick") > 0)
        ev["S3"] = foa >= 1.0
        ev["S4"] = rsi2 >= 95
        # E5 sector lag (ULT-17)
        sfo, satrp, beta = _col(d, "sec_fo"), _col(d, "sec_atrp"), _col(d, "sec_beta")
        sret3 = ((1 + sfo / 100) / (1 + _lag(sfo, key, mins, 15) / 100) - 1) * 100
        nret3 = (c / _lag(c, key, mins, 15) - 1) * 100
        sg = np.sign(sret3)
        lagv = sg * (np.clip(beta, 0.3, 3.0) * sret3 - nret3) / atrp
        e5 = np.isfinite(lagv) & np.isfinite(satrp) & (np.abs(sret3) / satrp >= E5_S) & (lagv >= E5_LMIN)
        ev["E5L"], ev["E5S"] = e5 & (sg > 0), e5 & (sg < 0)
        sfo_spy = _col(d, "spy_fo")
        spy_r30 = ((1 + sfo_spy / 100) / (1 + _lag(sfo_spy, key, mins, 30) / 100) - 1) * 100
        cr = cost_r(d)
        adv = _col(d, "adv20")
        sym = _symbols(d)
        is_etf = np.array([s in ETFS for s in sym], float)
        is_lev = np.array([s in LEV for s in sym], bool)
        base = (c >= 10) & (np.abs(gap) < 20) & (atr > 0) & np.isfinite(sfo_spy)
        long_ok = ~((sfo_spy >= -0.75) & (sfo_spy <= -0.30) & (spy_r30 < 0))
        short_ok = (gap < 0.5) & (r5 >= 25) & ~is_lev
    for k in ev:
        ev[k] = np.nan_to_num(ev[k].astype(float)) > 0
    blk = {f"blk{i}": ((t >= a) & (t <= b)).astype(float) for i, (a, b) in enumerate(BLOCKS)}
    common = {"atr_pct": atrp, "cost_r": cr, "log_adv": np.log10(np.where(adv > 0, adv, np.nan)), "is_etf": is_etf,
              "vol_ratio": _col(d, "volumeRatio"), **blk}
    signed = {"s_gap": gap, "s_fo_d": foa, "s_vwap_d": vwap_d, "s_rsi14": rsi - 50, "s_di7": di7, "s_spy_fo": sfo_spy,
              "s_spy_r30": spy_r30}
    return {"n": n, "sel": sel, "ev": ev, "common": common, "signed": signed, "base": base, "long_ok": long_ok,
            "short_ok": short_ok, "cost_r": cr, "adv": adv}


def univ_ok(b, univ) -> np.ndarray:
    """Intake of universe univ on the selected rows (ADV only when the frame has adv20; live: YAML min_adv)."""
    mn, cmax = UNIVS[univ]
    with np.errstate(invalid="ignore"):
        ok = b["base"] & (b["cost_r"] <= cmax)
        adv = b["adv"]
        if np.isfinite(adv).any():
            ok &= np.nan_to_num(adv) >= mn
    return ok


def side_rows(b, sgn, univ) -> np.ndarray:
    """Eligible rows (on b['sel']) for side sgn: intake, side filter, >= 1 side event."""
    ev = b["ev"]
    if sgn > 0:
        anye = ev["L1"] | ev["L2"] | ev["L3"] | ev["L4"] | ev["L5"] | ev["E5L"]
        return univ_ok(b, univ) & b["long_ok"] & anye
    anye = ev["S1"] | ev["S2"] | ev["S3"] | ev["S4"] | ev["E5S"]
    return univ_ok(b, univ) & b["short_ok"] & anye


def side_features(b, sgn) -> np.ndarray:
    """(len(sel), len(FEATS)) raw features of side sgn on the selected rows."""
    ev = b["ev"]
    m = len(b["sel"])
    F = {f"ev{k}": ev[k].astype(float) for k in EVL + EVS}
    e5 = ev["E5L"] if sgn > 0 else ev["E5S"]
    F["evE5"] = e5.astype(float)
    F["is_long"] = np.full(m, 1.0 if sgn > 0 else 0.0)
    names = EVL if sgn > 0 else EVS
    F["n_ev"] = sum(ev[k].astype(float) for k in names) + e5.astype(float)
    F.update(b["common"])
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
