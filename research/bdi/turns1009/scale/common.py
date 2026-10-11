"""T2 scale-up (turn diagnosis): shared loaders, factor panel, turn labels and exits. See NOTES.md section 1.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = HERE / "data"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

ETFS = set(("ARKK ASHR BITO BOIL CONL DIA EEM EFA ETHA EWJ EWT EWY EWZ FBTC FXI GBTC GDX GDXJ GLD IBB IBIT IEMG IGV ITB "
            "IWF IWM IYR JETS KBE KRE KWEB LABD MDY MSTU MTUM NUGT NVDL OIH PSQ QID QQQ SCO SDS SLV SMH SOXL SOXS SOXX "
            "SPXL SPXS SPY SQQQ TLT TMF TNA TQQQ TSLL TZA UCO UNG UPRO USO UVXY VEA VNQ VUG VWO VXX XBI XHB XLB XLC XLE "
            "XLF XLI XLK XLP XLRE XLU XLV XLY XME XOP XRT").split())
NB = 77
TODS = np.array([(9 * 60 + 35 + 5 * i) // 60 * 100 + (9 * 60 + 35 + 5 * i) % 60 for i in range(NB)])  # 935..1555
I0, I1 = int(np.flatnonzero(TODS == 950)[0]), int(np.flatnonzero(TODS == 1500)[0])               # entry window
MIN_ADV = 95e6
TRAIN_END = "2025-12-31"
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
LINES = ["t1s1", "t05s1", "t1s05", "close"]
KS = (2, 3, 4)
M_APPROACH = 2.0
LOCKED = lib.LOCKED


def symbols() -> list[str]:
    return (ROOT / "research" / "lab_symbols.txt").read_text().split()


def open_dates() -> list:
    return sorted(set(lib.daily()["date"]))


_STORE = None


def load_bars(sym: str, dates64: np.ndarray) -> dict | None:
    """Dense 5-min O/H/L/C/V [session, bar] float32 (NaN = no bar). Locked rows dropped right after the load."""
    global _STORE
    if _STORE is None:
        _STORE = BarStore(ROOT / "data" / "cache_hist")
    df = _STORE.load(sym)
    if df.empty:
        return None
    day = df.index.tz_localize(None).normalize().to_numpy()
    lo64, hi64 = np.datetime64(LOCKED[0], "us"), np.datetime64(LOCKED[1], "us")
    df = df[~((day >= lo64) & (day <= hi64))]                       # locked block dropped before anything else
    day = df.index.tz_localize(None).normalize().to_numpy()
    df = df[np.isin(day, dates64)]
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m <= 959)]
    if df.empty:
        return None
    b = resample(df, "5min")
    end = b.index + pd.Timedelta(minutes=5)
    tod = np.asarray(end.hour * 100 + end.minute)
    ok = (tod >= 935) & (tod <= 1555)
    b, tod = b[ok], tod[ok]
    dd = np.searchsorted(dates64, b.index.tz_localize(None).normalize().to_numpy())
    bi = ((tod // 100) * 60 + tod % 100 - (9 * 60 + 35)) // 5
    out = {}
    for k, col in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"), ("V", "volume")):
        a = np.full((len(dates64), NB), np.nan, np.float32)
        a[dd, bi] = b[col].to_numpy(np.float32)
        out[k] = a
    return out


def fill(b: dict) -> dict:
    """Forward-fill missing bars on the flattened series: C carried, O/H/L = C, V = 0. Adds 'present'."""
    present = np.isfinite(b["C"])
    c = pd.Series(b["C"].ravel()).ffill().to_numpy(np.float32).reshape(b["C"].shape)
    out = {"present": present, "C": c}
    for k in ("O", "H", "L"):
        out[k] = np.where(present, b[k], c).astype(np.float32)
    out["V"] = np.where(present, b["V"], 0).astype(np.float32)
    return out


# ------------------------------------------------------------------------------------------------ indicators
def rsi_simple(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    g = d.clip(lower=0).rolling(n).sum() / n
    l = (-d.clip(upper=0)).rolling(n).sum() / n
    r = 100 - 100 / (1 + g / l.replace(0, np.nan))
    return r.where(l != 0, 100.0)


def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False).mean()


def day_cum(a2: np.ndarray, fn) -> np.ndarray:
    return fn(a2, axis=1)


def market_features(b: dict, atr: np.ndarray) -> dict:
    """SPY / QQQ context arrays [session, bar]: 3-bar move in its own R, RSI2, dist to LOD/HOD in atr, from-open."""
    C = b["C"]
    s = pd.Series(C.ravel())
    R = (0.25 * atr)[:, None]
    mv3 = (s - s.shift(3)).to_numpy().reshape(C.shape) / R
    rsi2 = rsi_simple(s, 2).to_numpy().reshape(C.shape)
    lod = np.fmin.accumulate(b["L"], axis=1)
    hod = np.fmax.accumulate(b["H"], axis=1)
    dopen = b["O"][:, :1]
    ret6 = (s / s.shift(6) - 1).to_numpy().reshape(C.shape)
    return {"mv3": mv3, "rsi2": rsi2, "dlod": (C - lod) / atr[:, None], "dhod": (hod - C) / atr[:, None],
            "fromopen": C - dopen, "ret6": ret6}


COND_IDS = ["O1 rsi2_5", "O2 rsi2_10", "O3 rsi5_20", "O4 rsi14_30", "O5 stoch14", "O6 wr5", "O7 cci20", "O8 mfi14",
            "O9 macdh_turn", "O10 macd_div", "O11 rsi_div", "B1 bb_out", "B2 bb_wide", "B3 kelt2", "B4 vwap2sd",
            "B5 vwap1sd", "T1 ema_dn", "T2 ema9_reclaim", "T3 sma50", "T4 sma200", "T5 adx_trend", "T6 adx_range",
            "V1 atr_exp", "V2 rvol2", "V3 rvol3", "V4 climax", "V5 obv_div", "V6 cmf", "K1 wick", "K2 engulf",
            "K3 hammer", "K4 rev3", "K5 consec4", "K6 consec6", "K7 close_top", "K8 brk_prev", "K9 bigbar",
            "L1 speed2", "L2 speed3", "L3 at_lod", "L4 new_lod", "L5 near_pdl", "L6 below_pdl", "L7 open05",
            "L8 open1", "L9 pclose1", "L10 gap05", "L11 off_hod1", "L12 range1", "M1 spy_fall", "M2 spy_nofall",
            "M3 spy_rsi2", "M4 spy_lod", "M5 qqq_fall", "M6 rs_flush", "M7 rs_strong", "M8 breadth_lo",
            "M9 breadth_turn", "M10 spy_dayup", "D1 t0950", "D2 t1030", "D3 t1200", "D4 t1400"]
NC = len(COND_IDS)
SIBLING = {"O1 rsi2_5": "O2 rsi2_10", "O2 rsi2_10": "O1 rsi2_5", "O3 rsi5_20": "O4 rsi14_30", "O4 rsi14_30": "O3 rsi5_20",
           "V2 rvol2": "V3 rvol3", "V3 rvol3": "V2 rvol2", "K5 consec4": "K6 consec6", "K6 consec6": "K5 consec4",
           "L1 speed2": "L2 speed3", "L2 speed3": "L1 speed2", "L7 open05": "L8 open1", "L8 open1": "L7 open05",
           "B4 vwap2sd": "B5 vwap1sd", "B5 vwap1sd": "B4 vwap2sd"}


P_IDS = ["P1 pd_down", "P2 pd_range", "P3 pd_weak_close", "P4 retest_low", "P5 session_pct", "P6 move3h",
         "P7 pd_extreme_retest"]
COND_IDS_X = COND_IDS + P_IDS
NCX = len(COND_IDS_X)


def conditions(b: dict, aux: dict, ctx: dict, beta: np.ndarray, extra: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Boolean [NC, session, bar] for the long reading and the short mirror (NOTES 1.3). b is filled (fill())."""
    O, H, L, C, V = b["O"], b["H"], b["L"], b["C"], b["V"]
    sh = C.shape
    f = lambda x: pd.Series(x.ravel().astype(np.float64))
    rs = lambda x: np.asarray(x, np.float64).reshape(sh)
    rb = lambda x: np.asarray(x, bool).reshape(sh)
    c, h, l, o, v = f(C), f(H), f(L), f(O), f(V)
    atr = aux["atr"][:, None].astype(np.float64)
    R = 0.25 * atr
    with np.errstate(invalid="ignore", divide="ignore"):
        rsi2, rsi5, rsi14 = rs(rsi_simple(c, 2)), rs(rsi_simple(c, 5)), rs(rsi_simple(c, 14))
        h14, l14 = h.rolling(14).max(), l.rolling(14).min()
        stoch = rs((c - l14) / (h14 - l14).replace(0, np.nan) * 100)
        h5, l5 = h.rolling(5).max(), l.rolling(5).min()
        wr5 = rs((h5 - c) / (h5 - l5).replace(0, np.nan) * -100)
        tp = (h + l + c) / 3
        tpa = tp.to_numpy()
        win = np.lib.stride_tricks.sliding_window_view(tpa, 20)
        mad = np.full(len(tpa), np.nan)
        mad[19:] = np.abs(win - win.mean(1, keepdims=True)).mean(1)
        sma_tp = tp.rolling(20).mean().to_numpy()
        cci = rs((tpa - sma_tp) / (0.015 * np.where(mad > 0, mad, np.nan)))
        mf = tp * v
        up = tp > tp.shift(1)
        dn = tp < tp.shift(1)
        pos, neg = mf.where(up, 0).rolling(14).sum(), mf.where(dn, 0).rolling(14).sum()
        mfi = rs((100 - 100 / (1 + pos / neg.replace(0, np.nan))).where(neg != 0, 100.0))
        macd = ema(c, 12) - ema(c, 26)
        hist_s = macd - ema(macd, 9)
        hist = rs(hist_s)
        hist1 = rs(hist_s.shift(1))
        lmin12, hmax12 = rs(l.shift(1).rolling(12).min()), rs(h.shift(1).rolling(12).max())
        hmin12, hmaxh12 = rs(hist_s.shift(1).rolling(12).min()), rs(hist_s.shift(1).rolling(12).max())
        lmin20, hmax20 = rs(l.shift(1).rolling(20).min()), rs(h.shift(1).rolling(20).max())
        r14s = rsi_simple(c, 14)
        rmin20, rmax20 = rs(r14s.shift(1).rolling(20).min()), rs(r14s.shift(1).rolling(20).max())
        sma20, sd20 = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
        pctb = rs((c - (sma20 - 2 * sd20)) / (4 * sd20).replace(0, np.nan))
        bw = 4 * sd20 / sma20
        bw_med = bw.rolling(50).median().shift(1)
        bb_wide = rb(bw >= 1.5 * bw_med)
        pc = c.shift(1)
        tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        e20 = ema(c, 20)
        kel_lo, kel_hi = rs(e20 - 2 * atr14), rs(e20 + 2 * atr14)
        # session VWAP and volume-weighted sd
        TP = rs(tp)
        cv = np.cumsum(V, axis=1, dtype=np.float64)
        vw = np.cumsum(TP * V, axis=1) / np.where(cv > 0, cv, np.nan)
        vw2 = np.cumsum(TP * TP * V, axis=1) / np.where(cv > 0, cv, np.nan)
        vsd = np.sqrt(np.maximum(vw2 - vw * vw, 0))
        e9, e21 = ema(c, 9), ema(c, 21)
        E9, E21 = rs(e9), rs(e21)
        E9p, Cp = rs(e9.shift(1)), rs(pc)
        sma50, sma200 = rs(c.rolling(50).mean()), rs(c.rolling(200).mean())
        # ADX (Wilder)
        upm, dnm = h.diff(), -l.diff()
        pdm = upm.where((upm > dnm) & (upm > 0), 0.0)
        mdm = dnm.where((dnm > upm) & (dnm > 0), 0.0)
        a = 1 / 14
        trs = tr.ewm(alpha=a, adjust=False).mean()
        pdi = 100 * pdm.ewm(alpha=a, adjust=False).mean() / trs.replace(0, np.nan)
        mdi = 100 * mdm.ewm(alpha=a, adjust=False).mean() / trs.replace(0, np.nan)
        dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
        adx = rs(dx.ewm(alpha=a, adjust=False).mean())
        PDI, MDI = rs(pdi), rs(mdi)
        atrexp = rs(tr.rolling(5).mean() / tr.rolling(50).mean().replace(0, np.nan))
        # relative volume by bar of day over prior 20 sessions (min 10 with a bar)
        pres = b["present"].astype(np.float64)
        Vd = np.where(b["present"], V, 0).astype(np.float64)
        cs = np.vstack([np.zeros((1, NB)), np.cumsum(Vd, 0)])
        cn = np.vstack([np.zeros((1, NB)), np.cumsum(pres, 0)])
        D = sh[0]
        lo = np.maximum(np.arange(D) - 20, 0)
        sv, nv = cs[np.arange(D)] - cs[lo], cn[np.arange(D)] - cn[lo]
        rvol = V / np.where(nv >= 10, sv / np.maximum(nv, 1), np.nan)
        vm20 = rs(v.shift(1).rolling(20).mean())
        climax_v = V >= 3 * vm20
        sgn = np.sign(c.diff()).fillna(0)
        obv = (sgn * v).cumsum()
        OBV, obvmin, obvmax = rs(obv), rs(obv.shift(1).rolling(12).min()), rs(obv.shift(1).rolling(12).max())
        mfm = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
        cmf = rs((mfm.fillna(0) * v).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan))
        rng = H - L
        body = np.abs(C - O)
        lw, uw = np.minimum(O, C) - L, H - np.maximum(O, C)
        Op, Hp, Lp = rs(o.shift(1)), rs(h.shift(1)), rs(l.shift(1))
        dnb = (c < c.shift(1))
        upb = (c > c.shift(1))
        dn4, up4 = rb(dnb.astype(float).rolling(4).sum() == 4), rb(upb.astype(float).rolling(4).sum() == 4)
        dn6, up6 = rb(dnb.astype(float).rolling(6).sum() == 6), rb(upb.astype(float).rolling(6).sum() == 6)
        dn3p, up3p = rb(dnb.astype(float).shift(1).rolling(3).sum() == 3), rb(upb.astype(float).shift(1).rolling(3).sum() == 3)
        mv3 = (C - rs(c.shift(3))) / R
        lod = np.fmin.accumulate(L, axis=1)
        hod = np.fmax.accumulate(H, axis=1)
        lodp = np.hstack([np.full((D, 1), np.inf), lod[:, :-1]])
        hodp = np.hstack([np.full((D, 1), -np.inf), hod[:, :-1]])
        dopen = O[:, :1]
        pcl, pdh, pdl = aux["pclose"][:, None], aux["pdh"][:, None], aux["pdl"][:, None]
        ret6 = rs(c / c.shift(6) - 1)
        rel6 = (ret6 - beta[:, None] * ctx["spy"]["ret6"]) * C / R
        br = ctx["breadth"]
        br2 = np.hstack([np.full((D, 2), np.nan), br[:, :-2]])
        TOD = np.broadcast_to(TODS[None, :], sh)
        sp, qq = ctx["spy"], ctx["qqq"]

    L_, S_ = [], []

    def add(lc, sc=None):
        L_.append(np.asarray(lc, bool))
        S_.append(np.asarray(lc if sc is None else sc, bool))

    with np.errstate(invalid="ignore"):
        add(rsi2 <= 5, rsi2 >= 95)
        add(rsi2 <= 10, rsi2 >= 90)
        add(rsi5 <= 20, rsi5 >= 80)
        add(rsi14 <= 30, rsi14 >= 70)
        add(stoch <= 10, stoch >= 90)
        add(wr5 <= -95, wr5 >= -5)
        add(cci <= -150, cci >= 150)
        add(mfi <= 20, mfi >= 80)
        add((hist < 0) & (hist > hist1), (hist > 0) & (hist < hist1))
        add((L <= lmin12) & (hist < 0) & (hist > hmin12), (H >= hmax12) & (hist > 0) & (hist < hmaxh12))
        add((L <= lmin20) & (rsi14 > rmin20 + 5), (H >= hmax20) & (rsi14 < rmax20 - 5))
        add(pctb <= 0, pctb >= 1)
        add(bb_wide)
        add(C <= kel_lo, C >= kel_hi)
        add(C <= vw - 2 * vsd, C >= vw + 2 * vsd)
        add(C <= vw - vsd, C >= vw + vsd)
        add(E9 < E21, E9 > E21)
        add((C > E9) & (Cp <= E9p), (C < E9) & (Cp >= E9p))
        add(C < sma50, C > sma50)
        add(C < sma200, C > sma200)
        add((adx >= 25) & (MDI > PDI), (adx >= 25) & (PDI > MDI))
        add(adx <= 20)
        add(atrexp >= 1.5)
        add(rvol >= 2)
        add(rvol >= 3)
        add(climax_v & (C < O), climax_v & (C > O))
        add((L <= lmin12) & (OBV > obvmin), (H >= hmax12) & (OBV < obvmax))
        add(cmf > 0.1, cmf < -0.1)
        add((lw >= 0.5 * rng) & (rng >= 0.5 * R), (uw >= 0.5 * rng) & (rng >= 0.5 * R))
        add((C > O) & (Cp < Op) & (C >= Op) & (O <= Cp), (C < O) & (Cp > Op) & (C <= Op) & (O >= Cp))
        add((lw >= 2 * body) & (uw <= body) & (rng >= 0.4 * R), (uw >= 2 * body) & (lw <= body) & (rng >= 0.4 * R))
        add((C > O) & dn3p, (C < O) & up3p)
        add(dn4, up4)
        add(dn6, up6)
        add((C >= L + 2 / 3 * rng) & (rng >= 0.5 * R), (C <= L + 1 / 3 * rng) & (rng >= 0.5 * R))
        add(C > Hp, C < Lp)
        add(rng >= R)
        add(mv3 <= -2, mv3 >= 2)
        add(mv3 <= -3, mv3 >= 3)
        add((C - lod) <= 0.05 * atr, (hod - C) <= 0.05 * atr)
        add(L < lodp, H > hodp)
        add(np.abs(C - pdl) <= 0.1 * atr, np.abs(C - pdh) <= 0.1 * atr)
        add(C < pdl, C > pdh)
        add(C - dopen <= -0.5 * atr, C - dopen >= 0.5 * atr)
        add(C - dopen <= -1.0 * atr, C - dopen >= 1.0 * atr)
        add(C - pcl <= -1.0 * atr, C - pcl >= 1.0 * atr)
        add(np.broadcast_to(dopen - pcl <= -0.5 * atr, sh), np.broadcast_to(dopen - pcl >= 0.5 * atr, sh))
        add(hod - C >= atr, C - lod >= atr)
        add(hod - lod >= atr)
        add(sp["mv3"] <= -1, sp["mv3"] >= 1)
        add(sp["mv3"] >= 0, sp["mv3"] <= 0)
        add(sp["rsi2"] <= 10, sp["rsi2"] >= 90)
        add(sp["dlod"] <= 0.05, sp["dhod"] <= 0.05)
        add(qq["mv3"] <= -1, qq["mv3"] >= 1)
        add(rel6 <= -1.5, rel6 >= 1.5)
        add(rel6 >= 1, rel6 <= -1)
        add(br <= 0.30, br >= 0.70)
        add(br - br2 >= 0.05, br - br2 <= -0.05)
        add(sp["fromopen"] >= 0, sp["fromopen"] <= 0)
        add((TOD >= 950) & (TOD < 1030))
        add((TOD >= 1030) & (TOD < 1200))
        add((TOD >= 1200) & (TOD < 1400))
        add((TOD >= 1400) & (TOD <= 1500))
        if extra:                                                  # amendment A2: P1..P7
            pdo = aux["pdopen"][:, None]
            pdr = pdh - pdl
            add(np.broadcast_to(pcl - pdo <= -0.5 * atr, sh), np.broadcast_to(pcl - pdo >= 0.5 * atr, sh))
            add(np.broadcast_to(pdr >= 1.2 * atr, sh))
            add(np.broadcast_to(pcl <= pdl + 0.25 * pdr, sh), np.broadcast_to(pcl >= pdh - 0.25 * pdr, sh))
            lod6 = np.hstack([np.full((D, 6), np.nan), lod[:, :-6]])
            hod6 = np.hstack([np.full((D, 6), np.nan), hod[:, :-6]])
            add((np.abs(L - lod6) <= 0.05 * atr) & (C > lod6), (np.abs(H - hod6) <= 0.05 * atr) & (C < hod6))
            add(C <= dopen * 0.99, C >= dopen * 1.01)
            c36 = rs(c.shift(36))
            add(C - c36 <= -atr, C - c36 >= atr)
            add((np.abs(L - pdl) <= 0.05 * atr) & (C > pdl), (np.abs(H - pdh) <= 0.05 * atr) & (C < pdh))
    assert len(L_) == (NCX if extra else NC), len(L_)
    return np.stack(L_), np.stack(S_)


# ------------------------------------------------------------------------------------------------ turn labels
def _first(mask3: np.ndarray) -> np.ndarray:
    """First True index along the last axis; NB + 1 if none."""
    any_ = mask3.any(-1)
    return np.where(any_, mask3.argmax(-1), NB + 1)


_J = np.arange(NB)
LATER = _J[None, :] > _J[:, None]           # [i, j] j > i
EARLIER = _J[None, :] < _J[:, None]         # [i, j] j < i


def turn_labels(H, L, R, ks=KS, m=M_APPROACH, tols=(1.0,), sides=("long", "short")):
    """Swing labels per NOTES 1.2. H, L [D, NB] (for close-based labels pass C as both), R [D] (price units).
    Returns {(side, k, tol): bool [D, NB]} and strict sizes {(side, k): float [D, NB] (R) where strict label}."""
    out, sizes = {}, {}
    Rr = R[:, None, None]
    for side in sides:
        if side == "long":
            X, Y = L, H                       # extreme on lows, follow-through on highs
            sgn = 1.0
        else:
            X, Y = -H, -L
            sgn = 1.0
        Xi = X[:, :, None]                    # [D, i, 1]
        Xj, Yj = X[:, None, :], Y[:, None, :]
        lower = (Xj < Xi) & EARLIER[None]     # prior bar beyond the extreme
        p = np.where(lower.any(-1), NB - 1 - lower[:, :, ::-1].argmax(-1), -1)          # last such j, or -1
        between = (_J[None, None, :] > p[:, :, None]) & EARLIER[None]
        ymax = np.where(between, Yj, -np.inf).max(-1)                                 # best opposite price into it
        approach = ymax >= X + m * R[:, None]
        for k in ks:
            ft = _first((Yj >= Xi + k * Rr) & LATER[None])
            for tol in tols:
                fa = _first((Xj < Xi - tol * Rr) & LATER[None])
                lab = approach & (ft < fa) & (ft <= NB - 1)
                out[(side, k, tol)] = lab
                if tol == 0.0:
                    excur = np.where(LATER[None] & (_J[None, None, :] < fa[:, :, None]), Yj, -np.inf).max(-1)
                    sizes[(side, k)] = np.where(lab, (excur - X) / R[:, None], np.nan)
    return out, sizes


# ------------------------------------------------------------------------------------------------ exits
def exits(C, H, L, R):
    """Lab outcomes for every bar as entry (setup_lab._outcomes_asym on the 5-min bars, timed exit 15:55):
    {(side, geom): (lab_r (1c/side), win, exit_idx)} plus (side, 'close'): (gross R, exit_idx)."""
    out = {}
    Rr = R[:, None]
    Ci = C[:, :, None]
    Hj, Lj = H[:, None, :], L[:, None, :]
    for side, s in (("long", 1), ("short", -1)):
        for g, (up, dn) in GEOMS.items():
            tgt = Ci + s * up * Rr[:, :, None]
            stp = Ci - s * dn * Rr[:, :, None]
            ht = ((Hj >= tgt) if s == 1 else (Lj <= tgt)) & LATER[None]
            hs = ((Lj <= stp) if s == 1 else (Hj >= stp)) & LATER[None]
            ft, fs = _first(ht), _first(hs)
            won = ft < fs
            lost = (fs <= ft) & (fs <= NB - 1)
            last = np.full_like(ft, NB - 1)
            timed = s * (C[:, -1:] - C) / Rr
            val = np.where(won, up, np.where(lost, -dn, timed))
            ex = np.where(won, ft, np.where(lost, fs, last))
            ex = np.minimum(ex, NB - 1)
            out[(side, g)] = ((val - 2 * 0.01 / Rr).astype(np.float32), won, ex)
        out[(side, "close")] = ((s * (C[:, -1:] - C) / Rr).astype(np.float32), np.full(C.shape, NB - 1))
    return out


def prod_lines(ex, C, R, tod_mult, beta, spyC):
    """Production R for the 4 lines per side, raw [0:4] and SPY-hedged [4:8]. Returns {side: float32 [8, D, NB]}."""
    from mcf.research.gates import prod_r
    D = C.shape[0]
    Rf = np.broadcast_to(R[:, None], C.shape)
    todf = np.broadcast_to(TODS[None, :], C.shape)
    out = {}
    for side, s in (("long", 1), ("short", -1)):
        arr = np.full((8, D, NB), np.nan, np.float32)
        for gi, g in enumerate(LINES):
            if g == "close":
                gross, exi = ex[(side, g)]
                cost = (0.01 + C * 1e-4) * tod_mult + (0.01 + C * 1e-4)
                r = gross - cost / Rf
            else:
                lab, won, exi = ex[(side, g)]
                with np.errstate(invalid="ignore", divide="ignore"):
                    r = prod_r(lab.ravel(), won.ravel().astype(float), C.ravel(), (4 * Rf).ravel(), g,
                               tod=todf.ravel()).reshape(C.shape)
            arr[gi] = r
            se = spyC[np.arange(D)[:, None], exi]
            bt = beta[:, None]
            with np.errstate(invalid="ignore", divide="ignore"):
                hed = s * bt * C * (se / spyC - 1) / Rf
                hcost = 2 * bt * C * (0.01 / spyC + 1e-4) / Rf
            arr[4 + gi] = r - hed - hcost
        out[side] = arr
    return out


def exits_pct(C, H, L, tgt=0.005, stp=0.0035):
    """Percent geometry from every bar's close (5-min bars, later bars, stop first, timed exit 15:55):
    {side: (gross bps, won, stopped, exit_idx)}."""
    out = {}
    Ci = C[:, :, None]
    Hj, Lj = H[:, None, :], L[:, None, :]
    for side, s in (("long", 1), ("short", -1)):
        t_ = Ci * (1 + s * tgt)
        s_ = Ci * (1 - s * stp)
        ht = ((Hj >= t_) if s == 1 else (Lj <= t_)) & LATER[None]
        hs = ((Lj <= s_) if s == 1 else (Hj >= s_)) & LATER[None]
        ft, fs = _first(ht), _first(hs)
        won = ft < fs
        lost = (fs <= ft) & (fs <= NB - 1)
        timed = s * (C[:, -1:] / C - 1) * 1e4
        val = np.where(won, tgt * 1e4, np.where(lost, -stp * 1e4, timed))
        ex = np.minimum(np.where(won, ft, np.where(lost, fs, NB - 1)), NB - 1)
        out[side] = (val, won, lost, ex)
    return out
