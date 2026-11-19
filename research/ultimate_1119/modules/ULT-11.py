# ULTIMATE CANDIDATE ULT-11 LR-RANK (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-11"; backtest research/ultimate_1119/round2/ULT-11/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-11 LR-RANK - learned ranker (wide point-in-time features), LONG and SHORT, decision bars 09:50-15:00.

A regularised model trained only on FIT ranks every 5-minute decision bar for a long and a short time-exit trade; the
setup takes the better side per name and enters only when that side's prediction is above a fixed threshold tau.
The fitted model (scaler, per-side ridge weights or gradient-boosted trees, tau, h) is frozen in a JSON file beside this
module (ULT-11_model.json), written by research/ultimate_1119/round2/ULT-11/bt.py from FIT data only; it is evaluated
here with numpy only (no sklearn at run time).

Rule (all point-in-time, at the decision 5-minute bar close; the SAME `raw_features` / `predict` code is used by bt.py):
  intake U2 price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.08 (LR8 stop round trip ((1c + 1bp) x tod mult
            + 1c + 1bp + 2c) / u, u = 0.25 x daily ATR); ADV20 >= $50M via the YAML min_adv
  side      long: not (SPY from open in [-0.75%, -0.30%] and SPY 30-min return < 0)
            short: gap < +0.5% and RSI(5) >= 25 (and easy-to-borrow: broker side live, universe.csv ETB in the backtest)
  rank      pred_side = model(features) in u units of after-cost R of a time exit h minutes later
  enter     pred_side > tau AND pred_side >= pred of the other side (when the other side is eligible)
  refire    (THIN) a second hit only >= (h + 30) / 5 bars after the first, max 2 per symbol-session
Two sides, one file: LabStrategy has one side per setup, so the account carries TWO `type: lab` entries pointing at this
file; the side comes from the setup name (a name ending in "-S" / "-short" is the short side, anything else the long side).
Exit: GEOM "S" (stop_price = 2u catastrophic stop beyond the entry, no target) + YAML time_stop_min h, time_stop_min_r 99.
Account side (not in the module): at most 3 entries per decision bar over both sides (highest pred first), session cap
2k entries, one lot per symbol.
Live gaps (documented in RESULTS.md): the live lab frame has no `adv20` column and no sector-ETF columns
(`sec_fo`, `sec_r30`, `sec_beta`); the module then treats them as missing (z = 0, sector-missing flag = 1), which is
NOT what the backtest saw for most rows. A runner extension (per-name sector map + ADV20 column) is needed before any
live use. Context: `context: [spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap]`."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
WINDOW = (950, 1500)
MIN_ADV = 50_000_000
COST_R_MAX = 0.08
MODEL_PATH = Path(__file__).resolve().parent / "ULT-11_model.json"
MAX_PER_DAY = 2
BLOCKS = ((950, 1029), (1030, 1129), (1130, 1259), (1300, 1359), (1400, 1500))
FEATS = (["mins"] + [f"blk{i}" for i in range(5)] +
         ["gap", "gap_atr", "fo_d", "vwap_d", "hod_d", "lod_d", "pdh_d", "pdl_d",
          "rsi14", "rsi5", "rsi2", "rsi_slope", "ret1", "ret3", "ret6", "ret12",
          "vol_ratio", "buy_press", "flow3", "upper_wick", "lower_wick",
          "sma20_dist", "sma50_dist", "sma20_slope", "atr_pct", "log_adv", "cost_r",
          "spy_fo", "spy_r30", "qqq_fo", "qqq_vwap", "breadth", "breadth_chg",
          "sec_fo", "sec_r30", "sec_rel", "sec_missing"])
LAYERS = [
    "intake U2: price >= $10, |gap| < 20%, cost_r <= 0.08, ADV20 >= $50M (YAML min_adv)",
    "side filters: long not into a falling SPY (-0.30..-0.75% from open and 30-min < 0); short gap < +0.5%, RSI5 >= 25",
    "learned ranker (ULT-11_model.json, FIT only): better side per name, pred > tau",
    "window: bar close 0950-1500 ET; exit: h-minute time exit, 2u catastrophic stop",
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


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _lag(v, key, mins, lag):
    """Value of v at (same key, mins - lag), exact time match among rows with tod >= 09:50; NaN otherwise."""
    import pandas as pd
    idx = pd.MultiIndex.from_arrays([key, mins])
    s = pd.Series(v, index=idx)
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, mins - lag])).to_numpy(dtype=float)


def _rsi2(close, key):
    """Wilder RSI(2) of the 5-minute closes within the symbol-day (rows from 09:50 only, as the history frames)."""
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


def intake(df) -> np.ndarray:
    px, atr, tod, gap = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod"), _col(df, "gap")
    with np.errstate(invalid="ignore"):
        ok = (px >= 10) & (np.abs(gap) < 20) & (atr > 0) & (cost_r(df) <= COST_R_MAX) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        if "adv20" in df.columns:          # history frames; live: YAML min_adv on the runner's ADV
            ok &= np.nan_to_num(_col(df, "adv20")) >= MIN_ADV
    return ok


def spy_r30(df) -> np.ndarray:
    tod = _col(df, "tod")
    key = _keys(df)
    fo = _col(df, "spy_fo")
    sel = tod >= 950
    out = np.full(len(df), np.nan)
    lag = _lag(fo[sel], key[sel], _m2(tod[sel]), 30)
    with np.errstate(invalid="ignore"):
        out[sel] = ((1 + fo[sel] / 100) / (1 + lag / 100) - 1) * 100
    return out


def side_ok(df, sgn: int) -> np.ndarray:
    ok = intake(df)
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            fo, r30 = _col(df, "spy_fo"), spy_r30(df)
            ok &= ~((fo >= -0.75) & (fo <= -0.30) & (r30 < 0))
            ok &= np.isfinite(fo)
        else:
            ok &= (_col(df, "gap") < 0.5) & (_col(df, "rsi5") >= 25)
    return ok


def raw_features(df) -> np.ndarray:
    """(n, len(FEATS)) float array; rows before 09:50 get NaN. Point-in-time: only the row's own and earlier bars of the
    same symbol-day, the row's context columns, and prior-day values (atr_d, gap, adv20, pdh/pdl, sector map)."""
    n = len(df)
    tod = _col(df, "tod")
    sel = tod >= 950
    d = df.iloc[np.flatnonzero(sel)]
    key = _keys(d)
    t = _col(d, "tod")
    mins = _m2(t)
    c, atr = _col(d, "close"), _col(d, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = atr / c * 100
        gap = _col(d, "gap")
        fo = _col(d, "fromOpen")
        op = c / (1 + fo / 100)
        vd = _col(d, "vwapDistPct")
        F = {"mins": mins - 570}
        for i, (a, b) in enumerate(BLOCKS):
            F[f"blk{i}"] = ((t >= a) & (t <= b)).astype(float)
        F.update(gap=gap, gap_atr=gap / atrp, fo_d=(c - op) / atr, vwap_d=c * vd / (100 + vd) / atr,
                 hod_d=_col(d, "dist_hod_atr"), lod_d=_col(d, "dist_lod_atr"), pdh_d=_col(d, "dist_pdh_atr"),
                 pdl_d=_col(d, "dist_pdl_atr"), rsi14=_col(d, "rsi"), rsi5=_col(d, "rsi5"), rsi2=_rsi2(c, key),
                 rsi_slope=_col(d, "rsiSlope"))
        for k, nb in (("ret1", 1), ("ret3", 3), ("ret6", 6), ("ret12", 12)):
            F[k] = (c - _lag(c, key, mins, 5 * nb)) / atr
        F.update(vol_ratio=_col(d, "volumeRatio"), buy_press=_col(d, "buyPressure"), flow3=_col(d, "flow3"),
                 upper_wick=_col(d, "upper_wick"), lower_wick=_col(d, "lower_wick"),
                 sma20_dist=_col(d, "sma20_dist_pct"), sma50_dist=_col(d, "sma50_dist_pct"),
                 sma20_slope=_col(d, "sma20_slope_pct"), atr_pct=atrp,
                 log_adv=np.log10(np.where(_col(d, "adv20") > 0, _col(d, "adv20"), np.nan)), cost_r=cost_r(d))
        sfo = _col(d, "spy_fo")
        F.update(spy_fo=sfo, spy_r30=((1 + sfo / 100) / (1 + _lag(sfo, key, mins, 30) / 100) - 1) * 100,
                 qqq_fo=_col(d, "qqq_fo"), qqq_vwap=_col(d, "qqq_vwap"), breadth=_col(d, "breadth"),
                 breadth_chg=_col(d, "breadth") - _col(d, "breadth_open"))
        sec, sr30, beta = _col(d, "sec_fo"), _col(d, "sec_r30"), _col(d, "sec_beta")
        F.update(sec_fo=sec, sec_r30=sr30, sec_rel=fo - beta * sec, sec_missing=(~np.isfinite(sec)).astype(float))
    out = np.full((n, len(FEATS)), np.nan)
    out[sel] = np.column_stack([np.asarray(F[k], float) for k in FEATS])
    return out


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


def predict_z(Z, side_model) -> np.ndarray:
    if side_model["kind"] == "ridge":
        return Z @ np.asarray(side_model["w"]) + float(side_model["b"])
    return _trees_predict(Z, side_model)


def load_model(path=None):
    p = Path(path or MODEL_PATH)
    if str(p) not in _MODEL:
        _MODEL[str(p)] = json.loads(p.read_text())
    return _MODEL[str(p)]


def predict(df, model=None):
    """(pred_long, pred_short, ok_long, ok_short) in u units; pred is -inf where the side is not eligible."""
    model = model or load_model()
    Z = zscore(raw_features(df), model)
    out = []
    for sgn, nm in ((1, "long"), (-1, "short")):
        ok = side_ok(df, sgn)
        p = np.full(len(df), -np.inf)
        if ok.any():
            p[ok] = predict_z(Z[ok], model[nm])
        out.append((p, ok))
    return out[0][0], out[1][0], out[0][1], out[1][1]


def _thin(m, df, h):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    if not len(hit):
        return out
    key = _keys(df)
    gap_bars = int(np.ceil((h + 30) / 5))
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= gap_bars:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal
        return np.zeros(len(df), bool)
    if not MODEL_PATH.exists():
        return np.zeros(len(df), bool)
    model = load_model()
    pl, ps, okl, oks = predict(df, model)
    mine, other = (pl, ps) if _SGN > 0 else (ps, pl)
    m = np.isfinite(mine) & (mine > float(model["tau"])) & (mine >= other)
    return _thin(m, df, int(model["h"]))


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
