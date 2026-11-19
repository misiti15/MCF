# ULTIMATE CANDIDATE ULT-21 ETF-RANK (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-21"; backtest research/ultimate_1119/round3/ULT-21/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-21 ETF-RANK - learned ranker inside equity-basket ETFs, LONG only (short exposure via inverse funds).

Universe EQB (ULT-21_universe.json, YAML `symbols: module`): the WB4 ETF list plus every other lab ETF holding an equity
basket of >= 10 stocks, at any leverage, long or inverse; single-stock, commodity, crypto, volatility, bond, managed-
futures and option-income funds excluded. Built from fund names / types only, before any fit scoring.
Rule (point-in-time, at the decision 5-minute bar close 10:30-15:00; the SAME `raw_features` / `predict` code runs in
round3/ULT-21/bt.py):
  intake   price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.08 (LR8 stop round trip ((1c + 1bp) x tod mult
           + 1c + 1bp + 2c) / u, u = 0.25 x daily ATR); ADV20 >= $30M (YAML min_adv live; `adv20` column in history)
  tape     universal long filter on long-exposure funds: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min
           change < 0 (inverse funds are exempt: buying one is a short exposure, not a long into a falling tape)
  rank     pred = model(features), frozen in ULT-21_model.json (FIT only), units of after-cost R of a 45-min time exit
  enter    pred > tau (tau = FIT in-sample constant that gives k entries/session through the account chassis)
  refire   (THIN) second hit only >= (45 + 30) / 5 bars after the first, max 2 per symbol-session
Features (24): ret1/3/6/12 in daily ATR, +DI(7)-(-DI(7)), RSI2, RSI5, RSI14, VWAP / open / HOD / LOD distance in daily
ATR, volumeRatio, ATR% of price, cost_r, leverage (1/2/3), inverse flag, spy_fo, spy_r30, 5 time blocks; z-scored with
the FIT scaler, clipped +-5, NaN -> 0. Indicators via mcf.research.arena.indicators.compute (as WB4 / ULT-12).
Exit: GEOM per the frozen pick (t05s1 = +0.5u / -1u around the decision close with YAML time_stop_min 45; or "S" =
2u catastrophic stop + YAML time_stop_min 45, time_stop_min_r 99). Flat 15:50 implied (last entry 15:00).
Account side (not in the module): <= 3 entries per decision bar (highest pred first), session cap 2k entries, ONE open
lot per exposure group (GROUP map below, e.g. QQQ/TQQQ/SQQQ share "NDX"), one lot per symbol, refire >= 30 min after
the exit. Context: `context: [spy_fo]`."""
import json
from pathlib import Path

import numpy as np

from mcf.research.arena.indicators import compute

SIDE = "long"
_HERE = Path(__file__).resolve().parent
MODEL_PATH = _HERE / "ULT-21_model.json"
_U = json.loads((_HERE / "ULT-21_universe.json").read_text())
SYMBOLS = frozenset(_U["EQB"])
LEVERAGE = {k: int(v) for k, v in _U["leverage"].items()}
INVERSE = frozenset(_U["inverse"])
GROUP = dict(_U["group"])
# GEOM from the frozen pick's exit (T5 -> "t05s1", TX -> "S"); a YAML `geom:` overrides
GEOM = ("S" if json.loads(MODEL_PATH.read_text()).get("exit") == "TX" else "t05s1") if MODEL_PATH.exists() else "t05s1"
WINDOW = (1030, 1500)
MIN_ADV = 30_000_000
COST_R_MAX = 0.08
H = 45
MAX_PER_DAY = 2
BLOCKS = ((1030, 1129), (1130, 1229), (1230, 1329), (1330, 1429), (1430, 1500))
FEATS = (["ret1_d", "ret3_d", "ret6_d", "ret12_d", "di7", "rsi2", "rsi5", "rsi14", "vwap_d", "fo_d", "hod_d", "lod_d",
          "vol_ratio", "atr_pct", "cost_r", "lev", "inv", "spy_fo", "spy_r30"] + [f"blk{i}" for i in range(5)])
LAYERS = [
    "universe EQB: equity-basket ETFs (>= 10 stocks, any leverage, long or inverse); YAML symbols: module, min_adv $30M",
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.08",
    "long-exposure funds: skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
    "learned ranker (ULT-21_model.json, FIT only): pred > tau",
    "window: bar close 1030-1500 ET; exit per frozen pick, 45-min cap; account: one lot per exposure group",
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


def _symbols(df, sym=None):
    if "symbol" in getattr(df, "columns", ()):
        return df["symbol"].astype(str).to_numpy()
    return np.full(len(df), sym or "")


def cost_r(df) -> np.ndarray:
    px, atr, tod = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        return (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)


def spy_r30(df) -> np.ndarray:
    import pandas as pd
    fo, tod = _col(df, "spy_fo"), _col(df, "tod")
    key = _keys(df)
    m = _m2(tod)
    s = pd.Series(np.where(tod >= 950, fo, np.nan), index=pd.MultiIndex.from_arrays([key, m]))
    s = s[~s.index.duplicated()]
    lag = s.reindex(pd.MultiIndex.from_arrays([key, m - 30])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + lag / 100) - 1) * 100


def eligible(df, sym=None) -> np.ndarray:
    """Intake + window + universe + universal long filter (long-exposure funds only)."""
    px, atr, tod, gap = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod"), _col(df, "gap")
    syms = _symbols(df, sym)
    inv = np.isin(syms, list(INVERSE))
    fo, r30 = _col(df, "spy_fo"), spy_r30(df)
    with np.errstate(invalid="ignore"):
        ok = ((px >= 10) & (np.abs(gap) < 20) & (atr > 0) & (cost_r(df) <= COST_R_MAX) & (tod >= WINDOW[0])
              & (tod <= WINDOW[1]) & np.isfinite(fo) & np.isin(syms, list(SYMBOLS)))
        if "adv20" in df.columns:          # history frames; live: YAML min_adv on the runner's ADV
            ok &= np.nan_to_num(_col(df, "adv20")) >= MIN_ADV
        ok &= inv | ~((fo >= -0.75) & (fo <= -0.30) & (r30 < 0))
    return ok


def raw_features(df, sym=None) -> np.ndarray:
    """(n, len(FEATS)); point-in-time: the row's own and earlier bars of the same symbol-day, its context columns and
    prior-day values (atr_d, gap, adv20). Rows before 09:50 are NaN."""
    x = compute(df, names=["ret1", "ret3", "ret6", "ret12", "di_diff7", "rsi2", "vwap_atr", "fromOpen_atr"], context=False)
    c, atr, tod = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod")
    syms = _symbols(df, sym)
    with np.errstate(invalid="ignore", divide="ignore"):
        F = {}
        for k in (1, 3, 6, 12):
            r = x[f"ret{k}"].to_numpy(float)
            F[f"ret{k}_d"] = (c - c / (1 + r / 100)) / atr
        F.update(di7=x["di_diff7"].to_numpy(float), rsi2=x["rsi2"].to_numpy(float), rsi5=_col(df, "rsi5"),
                 rsi14=_col(df, "rsi"), vwap_d=x["vwap_atr"].to_numpy(float), fo_d=x["fromOpen_atr"].to_numpy(float),
                 hod_d=_col(df, "dist_hod_atr"), lod_d=_col(df, "dist_lod_atr"), vol_ratio=_col(df, "volumeRatio"),
                 atr_pct=atr / c * 100, cost_r=cost_r(df),
                 lev=np.array([LEVERAGE.get(s, 1) for s in syms], float),
                 inv=np.isin(syms, list(INVERSE)).astype(float), spy_fo=_col(df, "spy_fo"), spy_r30=spy_r30(df))
        for i, (a, b) in enumerate(BLOCKS):
            F[f"blk{i}"] = ((tod >= a) & (tod <= b)).astype(float)
    out = np.column_stack([np.asarray(F[k], float) for k in FEATS])
    out[tod < 950] = np.nan
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


def predict_z(Z, m) -> np.ndarray:
    if m["kind"] == "ridge":
        return Z @ np.asarray(m["w"]) + float(m["b"])
    return _trees_predict(Z, m)


def load_model(path=None):
    p = Path(path or MODEL_PATH)
    if str(p) not in _MODEL:
        _MODEL[str(p)] = json.loads(p.read_text())
    return _MODEL[str(p)]


def predict(df, model=None, sym=None):
    """(pred, ok): pred in after-cost R units of the training target; -inf where not eligible."""
    model = model or load_model()
    ok = eligible(df, sym)
    p = np.full(len(df), -np.inf)
    if ok.any():
        Z = zscore(raw_features(df, sym), model)
        p[ok] = predict_z(Z[ok], model["model"])
    return p, ok


def _thin(m, df):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    if not len(hit):
        return out
    key = _keys(df)
    gap_bars = int(np.ceil((H + 30) / 5))
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= gap_bars:
            out[i] = True; last = i; n += 1
    return out


def mask(df, sym=None) -> np.ndarray:
    if "spy_fo" not in df.columns or not MODEL_PATH.exists():     # fail safe: no context / no frozen model -> nothing
        return np.zeros(len(df), bool)
    if "symbol" not in df.columns and sym is None:
        sym = _infer_symbol(df)
        if sym is None:                  # symbol unknown -> universe / leverage / inverse flags unknown -> nothing
            return np.zeros(len(df), bool)
    model = load_model()
    p, ok = predict(df, model, sym)
    return _thin(np.isfinite(p) & (p > float(model["tau"])), df)


def _infer_symbol(df):
    """Live LabStrategy frames carry no symbol column. The runner caches one feature frame per (symbol, date, n bars,
    last bar) in mcf.strategies.setups._LAB_FRAMES; the frame passed here is that frame (or a context copy of it), so
    the symbol is the cache key whose frame has the same index and closes. None when no unique match."""
    try:
        from mcf.strategies.setups import _LAB_FRAMES
    except Exception:
        return None
    hits = set()
    c = _col(df, "close")
    for key, f in list(_LAB_FRAMES.items()):
        if len(f) == len(df) and f.index.equals(df.index) and np.array_equal(_col(f, "close"), c, equal_nan=True):
            hits.add(key[0])
    return hits.pop() if len(hits) == 1 else None


def stop_price(f, i) -> float:
    """GEOM "S" only: catastrophic stop 2u = 0.5 daily ATR below the decision close."""
    return float(f["close"].iloc[i]) - 2 * 0.25 * float(f["atr_d"].iloc[i])
