"""Round-2 crypto setup grammar: slower bars (1h / 4h / 1d), wide stops (>= 3% of price), 4h-to-7d holds,
realistic maker entries (mcf/crypto/exec1m.py), plus five event-driven SEED ideas from
research/crypto_r1/MARKET_RESEARCH.md, each run over a small fixed grid.

Every random draw and every seed-grid config is counted (draw ids continue from round 1's 500).
Long only (Alpaca crypto spot cannot short). Features at bar i use data up to bar i's close only.
Educational only — not financial advice.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .backtest import WINDOWS
from .exec1m import Plan
from .features import build

CORE = ("BTC", "ETH", "SOL")
ALTS = ("AVAX", "DOGE", "LINK", "AAVE", "UNI", "LTC", "BCH", "DOT", "XRP", "SHIB")   # tier 2: liquid high-beta alts
UNIVERSES = {"core": CORE, "all": CORE + ALTS, "alts": ALTS}
TFS = (60, 240, 1440)
PRIMS = ["ret", "stretch", "breakout", "pullback", "rsi", "trend", "volsurge", "zdrop", "wick", "btc_trend",
         "btc_ret", "volreg"]
STOP_ATR = (1.0, 1.5, 2.0, 3.0)
MIN_PCT = (0.03, 0.04, 0.05, 0.07)
TARGET_R = (1.5, 2.0, 3.0, None)
HOLD_H = (4, 8, 12, 24, 48, 96, 168)
OFFS = (0.0, 0.25, 0.5, 1.0)
P_MAKER = 0.75
SEEDS = ("flush", "orb_us", "asia_comp", "tsmom", "btc_lag")


@dataclass
class Setup2:
    draw_id: int
    tf: int
    conds: list = field(default_factory=list)            # [(prim, {params})]; a seed is [("seed:<name>", {...})]
    universe: str = "all"
    window: str = "any"
    days: str = "all"
    mode: str = "maker"
    off_atr: float = 0.0
    expiry_min: int = 60
    stop_atr: float = 2.0
    min_stop_pct: float = 0.03
    target_r: float | None = 2.0
    hold_h: float = 24
    family: str = "random"

    def plan(self, mode: str | None = None) -> Plan:
        return Plan(mode or self.mode, self.off_atr, self.expiry_min, self.stop_atr, self.min_stop_pct,
                    self.target_r, int(round(self.hold_h * 60)))

    def spec(self) -> dict:
        d = asdict(self)
        d.pop("draw_id")
        return d

    def key(self) -> str:
        return hashlib.sha1(json.dumps(self.spec(), sort_keys=True, default=str).encode()).hexdigest()[:10]

    def label(self) -> str:
        cs = "+".join(f"{p}(" + ",".join(f"{k}={v}" for k, v in sorted(a.items())) + ")" for p, a in self.conds)
        ent = f"mk{self.off_atr:g}/{self.expiry_min}m" if self.mode == "maker" else self.mode
        tgt = "none" if self.target_r is None else f"{self.target_r:g}R"
        return (f"L {self.tf}m {self.universe} {self.window}/{self.days} {cs} | {ent} s{self.stop_atr:g}atr"
                f">={self.min_stop_pct:.0%} t{tgt} h{self.hold_h:g}h")


# ------------------------------------------------------------------ features
def extra(f: pd.DataFrame, b: pd.DataFrame, tf: int, btc: pd.DataFrame | None) -> pd.DataFrame:
    """Bar-count features on top of features.build (which is minute-window based)."""
    c, h, l, v = b["c"], b["h"], b["l"], b["v"]
    atrp = f["atr_pct"].astype(float)
    x = {}
    for n in (1, 3, 6, 12):
        x[f"retb{n}"] = (c / c.shift(n) - 1) / atrp
    for n in (6, 20, 50):
        x[f"hib{n}"] = h.rolling(n).max().shift()
    x["ddhi20"] = (x["hib20"] - c) / f["atr"]
    x["vr20"] = v / v.rolling(20, min_periods=10).mean().shift()
    x["ema50"] = c.ewm(span=50, adjust=False).mean()
    r1 = np.log(c).diff()
    x["zb"] = r1 / r1.rolling(100, min_periods=50).std().shift()
    x["atrp_rank"] = atrp.rolling(200, min_periods=100).rank(pct=True)
    et = b.index.tz_convert("America/New_York")
    x["et_mod"] = et.hour * 60 + et.minute
    out = pd.DataFrame(x, index=b.index)
    if btc is not None:
        bc = btc["c"].reindex(b.index).ffill()
        out["btc_up50"] = (bc > btc["ema50"].reindex(b.index).ffill()).astype(float)
        for n in (1, 3, 6):
            out[f"btc_retb{n}"] = btc[f"retb{n}"].reindex(b.index)
        out["btc_zb"] = btc["zb"].reindex(b.index)
    return out


def seed_features(f: pd.DataFrame, b: pd.DataFrame, tf: int, btc: pd.DataFrame | None) -> pd.DataFrame:
    """15-min event features (ET-anchored US open; UTC Asia range; UTC-day momentum into the US session)."""
    if tf != 15:
        return pd.DataFrame(index=b.index)
    h, l, c, v = b["h"], b["l"], b["c"], b["v"]
    et_mod = f["et_mod"].to_numpy()
    dkey_utc = b.index.floor("D")
    et_day = b.index.tz_convert("America/New_York").floor("D")
    out = pd.DataFrame(index=b.index)
    # US opening range 09:30-10:00 ET, known from 10:00 ET
    inwin = (et_mod >= 570) & (et_mod < 600)
    ohi = h.where(inwin).groupby(et_day).transform("max")
    olo = l.where(inwin).groupby(et_day).transform("min")
    known = et_mod >= 600
    out["or_hi"], out["or_lo"] = ohi.where(known), olo.where(known)
    out["or_mid"] = (out["or_hi"] + out["or_lo"]) / 2
    # Asia range 00:00-07:00 UTC, known from 07:00 UTC, compression vs the prior 20 days' median range
    mod = f["mod"].to_numpy()
    aw = mod < 420
    ahi = h.where(aw).groupby(dkey_utc).transform("max")
    alo = l.where(aw).groupby(dkey_utc).transform("min")
    arng = (ahi - alo) / c
    daily = arng.groupby(dkey_utc).first()
    med = daily.rolling(20, min_periods=10).median().shift()
    out["asia7_hi"] = ahi.where(mod >= 420)
    out["asia_comp"] = (arng / med.reindex(dkey_utc).to_numpy()).where(mod >= 420)
    # UTC-day return and volume up to the US open (bar 09:15-09:30 ET closes at the open), vs prior 20 days
    dret = c / b["o"].groupby(dkey_utc).transform("first") - 1
    cumv = v.groupby(dkey_utc).cumsum()
    at = et_mod == 555
    r_at = dret.where(at).groupby(dkey_utc).first()
    v_at = cumv.where(at).groupby(dkey_utc).first()
    sd = r_at.rolling(20, min_periods=10).std().shift()
    vmed = v_at.rolling(20, min_periods=10).median().shift()
    out["tsmom_z"] = (dret / sd.reindex(dkey_utc).to_numpy()).where(at)
    out["tsmom_v"] = (cumv / vmed.reindex(dkey_utc).to_numpy()).where(at)
    if btc is not None and "or_mid" in btc:
        out["btc_above_ormid"] = (btc["c"].reindex(b.index) > btc["or_mid"].reindex(b.index)).astype(float)
    return out


def build2(b: pd.DataFrame, tf: int, btc: pd.DataFrame | None = None) -> pd.DataFrame:
    f = build(b, tf, btc=btc)
    f = pd.concat([f, extra(f, b, tf, btc)], axis=1)
    f = pd.concat([f, seed_features(f, b, tf, btc)], axis=1)
    num = [k for k in f.columns if k not in ("filled", "mod", "dow", "et_mod")]
    f[num] = f[num].replace([np.inf, -np.inf], np.nan).astype("float32")
    return f


# ------------------------------------------------------------------ random draws
def _prim(rng, p: str) -> dict:
    c = lambda xs: xs[int(rng.integers(len(xs)))]  # noqa: E731
    if p == "ret":
        return {"n": c([1, 3, 6, 12]), "dir": c(["up", "down"]), "k": c([1.0, 2.0, 3.0, 4.0])}
    if p == "stretch":
        return {"dir": c(["up", "down"]), "k": c([1.0, 2.0, 3.0])}
    if p == "breakout":
        return {"n": c([6, 20, 50])}
    if p == "pullback":
        return {"k": c([1.0, 2.0, 3.0])}
    if p == "rsi":
        return {"dir": "low", "lvl": c([25, 30, 35])} if rng.random() < 0.5 else {"dir": "high", "lvl": c([65, 70, 75])}
    if p == "trend":
        return {"ema": c([50, 200]), "dir": c(["up", "down"])}
    if p == "volsurge":
        return {"k": c([1.5, 2.0, 3.0])}
    if p == "zdrop":
        return {"z": c([2.0, 3.0])}
    if p == "wick":
        return {"w": c([0.4, 0.6])}
    if p == "btc_trend":
        return {"dir": c(["up", "down"])}
    if p == "btc_ret":
        return {"n": c([1, 3, 6]), "dir": c(["up", "down"]), "k": c([1.0, 2.0, 3.0])}
    if p == "volreg":
        return {"band": c(["low", "mid", "high"])}
    raise KeyError(p)


def draw(rng: np.random.Generator, draw_id: int) -> Setup2:
    tf = int(rng.choice(TFS))
    k = int(rng.choice([1, 2, 2, 3]))
    prims = list(rng.choice(PRIMS, size=k, replace=False))
    conds = [(str(p), _prim(rng, str(p))) for p in prims]
    universe = str(rng.choice(["core", "all"]))
    window, days = "any", "all"
    if tf == 60 and rng.random() < 0.5:
        window = str(rng.choice(["us_open", "asia_open", "eu_open", "us", "us_close"]))
    if tf < 1440:
        days = str(rng.choice(["all", "all", "weekday", "weekend"]))
    maker = rng.random() < P_MAKER
    off = float(rng.choice(OFFS)) if maker else 0.0
    expiry = int(rng.choice([tf, 4 * tf])) if maker else 0
    holds = [x for x in HOLD_H if x * 60 >= tf]
    return Setup2(draw_id, tf, conds, universe, window, days, "maker" if maker else "taker", off, expiry,
                  float(rng.choice(STOP_ATR)), float(rng.choice(MIN_PCT)), TARGET_R[int(rng.integers(len(TARGET_R)))],
                  float(rng.choice(holds)), "random")


def generate(n: int, seed: int, start_id: int = 0) -> list[Setup2]:
    rng = np.random.default_rng(seed)
    return [draw(rng, start_id + i) for i in range(n)]


# ------------------------------------------------------------------ seeds (5 ideas x 16-config grid)
SEED_VARIANTS = {
    "flush": [{"z": 3.5}, {"z": 4.5}],                 # 15m 1-bar drop <= -z sigma, vol >= 3x, lower wick >= 50%
    "orb_us": [{"vol": 1.5}, {"vol": 3.0}],            # 15m close crosses the 09:30-10:00 ET high, 10:00-13:00 ET
    "asia_comp": [{"k": 0.6}, {"k": 0.8}],             # Asia range <= k x 20-day median, break 07:00 UTC-16:00 ET
    "tsmom": [{"k": 0.5}, {"k": 1.0}],                 # UTC-day return to the US open >= k sigma, volume > median
    "btc_lag": [{"k": 1.5}, {"k": 2.5}],               # BTC 60m z >= k, buy the alt lagging most (lag >= 1 sigma)
}
SEED_HOLDS = {"flush": (12, 48), "orb_us": (6, 24), "asia_comp": (8, 24), "tsmom": (6.5, 24), "btc_lag": (4, 24)}


def seed_grid(start_id: int) -> list[Setup2]:
    out = []
    i = start_id
    for name in SEEDS:
        tf = 60 if name == "btc_lag" else 15
        uni = "alts" if name == "btc_lag" else "all"
        h1, h2 = SEED_HOLDS[name]
        for var, pct, (tgt, hold), mode in itertools.product(SEED_VARIANTS[name], (0.03, 0.05),
                                                              ((2.0, h1), (None, h2)), ("maker", "taker")):
            out.append(Setup2(i, tf, [(f"seed:{name}", dict(var))], uni, "any", "weekday" if name in
                              ("orb_us", "tsmom") else "all", mode, 0.0, 60 if mode == "maker" else 0, 1.0, pct,
                              tgt, float(hold), name))
            i += 1
    return out


# ------------------------------------------------------------------ masks
def time_mask(s: Setup2, f: pd.DataFrame) -> np.ndarray:
    """The setup's time filter only (window, weekday/weekend, seed clock gates): random baselines draw from it."""
    n = len(f)
    m = ~f["filled"].to_numpy() & np.isfinite(f["atr"].to_numpy(np.float64))
    mod = f["mod"].to_numpy()
    if s.window != "any":
        a, z = WINDOWS[s.window]
        m &= (mod >= a) & (mod < z)
    dow = f["dow"].to_numpy()
    if s.days == "weekday":
        m &= dow < 5
    elif s.days == "weekend":
        m &= dow >= 5
    for p, _ in s.conds:
        et = f["et_mod"].to_numpy()
        if p == "seed:orb_us":
            m &= (et >= 600) & (et < 780)
        elif p == "seed:asia_comp":
            m &= (mod >= 420) & (et < 960)
        elif p == "seed:tsmom":
            m &= et == 555
    return m if len(m) == n else np.zeros(n, bool)


def mask(s: Setup2, f: pd.DataFrame, pair: str) -> np.ndarray:
    m = time_mask(s, f)
    col = lambda k: f[k].to_numpy(np.float64) if k in f else np.full(len(f), np.nan)  # noqa: E731
    c = col("c")
    for p, a in s.conds:
        if p == "ret":
            x = col(f"retb{a['n']}")
            m &= (x >= a["k"]) if a["dir"] == "up" else (x <= -a["k"])
        elif p == "stretch":
            x = col("stretch")
            m &= (x >= a["k"]) if a["dir"] == "up" else (x <= -a["k"])
        elif p == "breakout":
            m &= c > col(f"hib{a['n']}")
        elif p == "pullback":
            m &= col("ddhi20") >= a["k"]
        elif p == "rsi":
            x = col("rsi")
            m &= (x <= a["lvl"]) if a["dir"] == "low" else (x >= a["lvl"])
        elif p == "trend":
            e = col(f"ema{a['ema']}")
            m &= (c > e) if a["dir"] == "up" else (c < e)
        elif p == "volsurge":
            m &= col("vr20") >= a["k"]
        elif p == "zdrop":
            m &= col("zb") <= -a["z"]
        elif p == "wick":
            m &= col("lwick") >= a["w"]
        elif p == "btc_trend":
            x = col("btc_up50") if pair != "BTC" else (c > col("ema50")).astype(float)
            m &= (x > 0.5) if a["dir"] == "up" else (x < 0.5)
        elif p == "btc_ret":
            x = col(f"btc_retb{a['n']}") if pair != "BTC" else col(f"retb{a['n']}")
            m &= (x >= a["k"]) if a["dir"] == "up" else (x <= -a["k"])
        elif p == "volreg":
            x = col("atrp_rank")
            m &= {"low": x < 0.3, "mid": (x >= 0.3) & (x <= 0.7), "high": x > 0.7}[a["band"]]
        elif p == "seed:flush":
            m &= (col("z1") <= -a["z"]) & (col("vol_ratio") >= 3.0) & (col("lwick") >= 0.5)
        elif p == "seed:orb_us":
            hi = col("or_hi")
            prev = np.r_[np.nan, c[:-1]]
            m &= (c > hi) & ~(prev > hi) & (col("vol_ratio") >= a["vol"])
            if pair != "BTC":
                m &= col("btc_above_ormid") > 0.5
        elif p == "seed:asia_comp":
            hi = col("asia7_hi")
            prev = np.r_[np.nan, c[:-1]]
            m &= (col("asia_comp") <= a["k"]) & (c > hi) & ~(prev > hi)
        elif p == "seed:tsmom":
            m &= (col("tsmom_z") >= a["k"]) & (col("tsmom_v") > 1.0)
        elif p == "seed:btc_lag":
            m &= col("lag_rank1") >= a["k"]           # set by the runner: BTC z on the bar if this alt lags most
        else:
            raise KeyError(p)
    return m & np.isfinite(c)
