# ULTIMATE CANDIDATE ULT-10-regime-switch-book (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-10"; backtest research/ultimate_1119/ULT-10-regime-switch-book/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-10 regime-switch book (composite) - LONG and SHORT, all day.

Thesis: no single mechanism works in every market. A point-in-time SPY state switch routes each 5-minute decision bar
to the component rule(s) that fit the tape, so the book trades on up, flat and down sessions.

Regime at each decision bar (point-in-time; context column `spy_fo` = SPY % from its 09:30 open to this bar's close):
  spy_r30 = SPY 30-min return (this bar vs the bar 30 minutes earlier, from spy_fo); spy_s930 = spy_fo.
  flush  spy_r30 < -T                    -> ULT-02 (tape-flush washout long)
  down   else spy_s930 <= -T             -> ULT-04 (down-tape pop fade short), ULT-09 (failed-VWAP-reclaim short)
  up     else spy_s930 >= +T             -> ULT-03 (RSI-collapse dip long), ULT-05 long side, ULT-07 (pm dip long)
  flat   otherwise (spy_s930 known)      -> ULT-01 (gap-down pop fade short), ULT-06 (morning turn long),
                                            ULT-08 (pm overbought roll-over short)
  spy_r30 unknown (before 10:20) counts as "not flush"; spy_s930 unknown -> no regime -> no signal (fail safe).

Component rules are the pre-registered ULT-01..09 rules, imported from their own modules in this folder (ULT-09 has no
module of its own yet, so its rule is written here from PLAN.md sec. 3 "ULT-09"). Each component keeps its own window,
stop, target and time exit (all <= 45 min). Config set "a" = the first-listed config of each component; set "b" = each
component's fit-selected config (its fitsel.json, frozen on fit only).

Live interface: the live LabStrategy runs one side and one exit geometry per setup, so the book is deployed as one
`type: lab` setup per LEG, all pointing at THIS file; the leg, the threshold T and the config set come from the YAML
setup name (the module name LabStrategy gives is "lab_<setup name>"), e.g. "ULT-10-T30b-L04" = T 0.30%, set b, leg
ULT-04. Every leg needs `context: [spy_fo]`, `min_adv: 20000000`, `refire: true`, `refire_cooldown: 0`, the leg's
`window`, `time_stop_min` (leg HOLD) with `time_stop_min_r: 99`, and GEOM from LEG_GEOM (t1s1 / t05s1 / "S" = 2R
catastrophic stop via stop_price). Book-wide parts live at the account level: one lot per symbol across setups (the
runner's rule), the day cap 30 = account `max_trades_per_day: 30` in a dedicated arena account. The module thins each
leg (first hit, next >= (hold + 30) / 5 bars later, max 2 per symbol-session); the backtest applies the exact book
chassis (one lot per symbol across the book, re-entry 30 min after the exit, max 2 per symbol-session, cap 30).
"""
import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
_NAME = __name__

# ------------------------------------------------------------------------------------------------ configuration
ROUTE = {"flush": ("02",), "down": ("04", "09"), "up": ("03", "05", "07"), "flat": ("01", "06", "08")}
LEG_REGIME = {leg: reg for reg, legs in ROUTE.items() for leg in legs}
LEG_SIDE = {"01": "short", "02": "long", "03": "long", "04": "short", "05": "long", "06": "long", "07": "long",
            "08": "short", "09": "short"}
# exit spec per leg config: (target R or None, stop R, max hold minutes); "T" t1s1 cap45, "t05" t05s1 cap45,
# "X<n>" time exit n minutes with a 2R catastrophic stop
EXITS = {"T": (1.0, 1.0, 45), "t05": (0.5, 1.0, 45), "X20": (None, 2.0, 20), "X30": (None, 2.0, 30),
         "X45": (None, 2.0, 45)}
CONFIGS = {
    "a": {   # first-listed config of each component (PLAN sec. 3)
        "01": dict(cfg="01a", window=(1100, 1300), rsi_min=60.0, exit="T"),
        "02": dict(cfg="02a", window=(1030, 1500), spy_t=-0.30, d1=1.0, d2=1.5, exit="X30"),
        "03": dict(cfg="03a", window=(1015, 1500), rsi_max=30.0, exit="T"),
        "04": dict(cfg="04a", window=(1030, 1430), spy_t=-0.30, rsi_min=70.0, exit="T"),
        "05": dict(cfg="05a", window=(1015, 1300), g=2.0, exit="T"),
        "06": dict(cfg="06a", window=(1050, 1130), rcl=0.3, exit="X30"),
        "07": dict(cfg="07a", window=(1400, 1500), a_min=3.0, drop=1.0, exit="t05"),
        "08": dict(cfg="08a", window=(1400, 1500), run=1.5, rsi_min=80.0, exit="X20"),
        "09": dict(cfg="09a", window=(1030, 1400), s_t=-0.20, exit="T"),
    },
    "b": {   # fit-selected config of each component (each component's fitsel.json; ULT-09: this folder's fit grid)
        "01": dict(cfg="01f", window=(1100, 1500), rsi_min=60.0, exit="X45"),
        "02": dict(cfg="02k", window=(1030, 1500), spy_t=-0.50, d1=1.5, d2=2.0, exit="X45"),
        "03": dict(cfg="03b", window=(1015, 1500), rsi_max=30.0, exit="X45"),
        "04": dict(cfg="04j", window=(1030, 1430), spy_t=-0.50, rsi_min=80.0, exit="T"),
        "05": dict(cfg="05h", window=(1015, 1400), g=3.0, exit="X45"),
        "06": dict(cfg="06a", window=(1050, 1130), rcl=0.3, exit="X30"),
        "07": dict(cfg="07a", window=(1400, 1500), a_min=3.0, drop=1.0, exit="t05"),
        "08": dict(cfg="08g", window=(1400, 1500), run=2.0, rsi_min=85.0, exit="X20"),
        "09": dict(cfg="09c", window=(1030, 1500), s_t=-0.20, exit="T"),    # ULT-09 fitsel.json (W 1520; frames end 15:00)
    },
}
MIN_ADV = 20_000_000          # every leg: YAML min_adv (point-in-time ADV20 in the backtest)
COST_R_MAX = 0.10
MAX_PER_DAY = 2

# defaults = the fit-selected book config 10d T50-fitsel (fitsel.json); the YAML setup name overrides them
T_PCT, SET, LEG = 0.50, "b", "02"
_m = re.search(r"T(30|50)([ab])", _NAME)
if _m:
    T_PCT, SET = int(_m.group(1)) / 100, _m.group(2)
_m = re.search(r"L(0[1-9])", _NAME)
if _m:
    LEG = _m.group(1)
SIDE = LEG_SIDE[LEG]
_EX = EXITS[CONFIGS[SET][LEG]["exit"]]
GEOM = "S" if _EX[0] is None else ("t1s1" if _EX[0] == 1.0 else "t05s1")
HOLD = _EX[2]
WINDOW = CONFIGS[SET][LEG]["window"]
THIN = True
REFIRE_BARS = (HOLD + 30) // 5
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    f"regime switch T {T_PCT:.2f}%: flush (SPY 30-min < -T) -> 02; SPY from 09:30 <= -T -> 04+09; >= +T -> 03+05L+07; "
    "else 01+06+08",
    f"leg ULT-{LEG} ({CONFIGS[SET][LEG]['cfg']}), active only in regime '{LEG_REGIME[LEG]}'",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: {CONFIGS[SET][LEG]['exit']} (hold <= {HOLD} min)",
]


# ------------------------------------------------------------------------------------------------ helpers
def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _minutes(tod):
    t = np.asarray(tod, dtype=float)
    return (t // 100) * 60 + t % 100


def _keys(df):
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day.astype(object)


def _dates(df):
    if "date" in df:
        return df["date"].astype(str).to_numpy()
    return pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()


def _lag(x, k, key, mins):
    """x k rows earlier in the same symbol-session, only when that row is exactly 5*k minutes earlier; else NaN."""
    n = len(x)
    out = np.full(n, np.nan)
    if n <= k:
        return out
    px = np.r_[np.full(k, np.nan), x[:-k]]
    pk = np.r_[np.full(k, None, dtype=object), key[:-k]]
    pm = np.r_[np.full(k, np.nan), mins[:-k]]
    ok = (pk == key) & (mins - pm == 5 * k)
    out[ok] = px[ok]
    return out


def _spy_table(df):
    """(date, tod) -> SPY spy_fo, one row per slot (multi-symbol history frames: a symbol's missing row cannot hide a
    SPY value; live: the symbol's own rows)."""
    t = pd.DataFrame({"d": _dates(df), "tod": df["tod"].to_numpy(), "fo": df["spy_fo"].to_numpy(dtype=float)})
    return t[np.isfinite(t.fo)].groupby(["d", "tod"], sort=True)["fo"].first()


def spy_features(df):
    """spy_s930 (= spy_fo), spy_r30 and spy_s950 in %, at each row; NaN where the reference bar is unknown."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    d, tod = _dates(df), df["tod"].to_numpy().astype(int)
    tab = _spy_table(df)
    look = tab.to_dict()
    m = _minutes(tod).astype(int)
    t30 = (m - 30) // 60 * 100 + (m - 30) % 60
    p30 = np.array([look.get((a, b), np.nan) for a, b in zip(d, t30)], dtype=float)
    p950 = np.array([look.get((a, 950), np.nan) for a in d], dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        r30 = ((1 + fo / 100) / (1 + p30 / 100) - 1) * 100
        s950 = ((1 + fo / 100) / (1 + p950 / 100) - 1) * 100
    return fo, r30, s950


def regime(df, t_pct=None):
    """Array of regime labels ('flush' / 'down' / 'up' / 'flat' / '') per row, point-in-time."""
    t_pct = T_PCT if t_pct is None else t_pct
    s930, r30, _ = spy_features(df)
    out = np.full(len(df), "", dtype=object)
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(s930)
        flush = ok & np.isfinite(r30) & (r30 < -t_pct)
        down = ok & ~flush & (s930 <= -t_pct)
        up = ok & ~flush & ~down & (s930 >= t_pct)
        flat = ok & ~flush & ~down & ~up
    out[flush], out[down], out[up], out[flat] = "flush", "down", "up", "flat"
    return out


def intake(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        return (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX)


# ------------------------------------------------------------------------------------------------ components
_MODS: dict = {}
_FILES = {"01": "ULT-01-gapdn-pop-fade-short.py", "02": "ULT-02-tapeflush-washout-long.py",
          "03": "ULT-03-rsicollapse-dip-long-broad.py", "04": "ULT-04-downtape-pop-fade-short.py",
          "05": "ULT-05-withgap-continuation.py", "06": "ULT-06-late-morning-turn-long.py",
          "07": "ULT-07-pm-volatile-dip-long.py", "08": "ULT-08-pm-overbought-rollover-short.py"}


def _mod(leg):
    if leg not in _MODS:
        name = f"ult10_{leg}_" + re.sub(r"\W", "_", _NAME) + ("_long" if leg == "05" else "")
        spec = importlib.util.spec_from_file_location(name, _HERE / _FILES[leg])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.THIN = False
        _MODS[leg] = m
    return _MODS[leg]


def _with(m, fn, df, **attrs):
    old = {k: getattr(m, k) for k in attrs}
    for k, v in attrs.items():
        setattr(m, k, v)
    try:
        return np.asarray(fn(df), dtype=bool)
    finally:
        for k, v in old.items():
            setattr(m, k, v)


def ult09_mask(df, s_t, spy_s950=None) -> np.ndarray:
    """ULT-09 failed-VWAP-reclaim short (PLAN sec. 3): U; gap <= +0.5%; fromOpen < 0; sma20_dist_pct <= -1.5%; closed
    above VWAP on one of the previous 3 bars and now closes below VWAP; RSI5 >= 40; SPY since 09:50 <= s_t."""
    def c(k):
        return df[k].to_numpy(dtype=float)
    if spy_s950 is None:
        spy_s950 = spy_features(df)[2]
    vd = c("vwapDistPct")
    key, mins = _keys(df), _minutes(df["tod"].to_numpy())
    with np.errstate(invalid="ignore"):
        above = np.zeros(len(df), bool)
        for k in (1, 2, 3):
            above |= _lag(vd, k, key, mins) > 0
        return (intake(df) & (c("gap") <= 0.5) & (c("fromOpen") < 0) & (c("sma20_dist_pct") <= -1.5) & above
                & (vd < 0) & (c("rsi5") >= 40) & (spy_s950 <= s_t))


def component_mask(df, leg, p, spy=None) -> np.ndarray:
    """Un-thinned component rule for leg / config p (window included; regime NOT included)."""
    if "spy_fo" not in df.columns:
        return np.zeros(len(df), bool)
    if leg == "01":
        m = _with(_mod("01"), _mod("01").mask, df, WINDOW=p["window"], RSI_MIN=p["rsi_min"])
    elif leg == "02":
        m = _mod("02").make_mask(spy_t=p["spy_t"], d1=p["d1"], d2=p["d2"])(df)
    elif leg == "03":
        m = _with(_mod("03"), _mod("03").mask, df, WINDOW=p["window"], RSI_MAX=p["rsi_max"])
    elif leg == "04":
        m = _with(_mod("04"), _mod("04").mask, df, WINDOW=p["window"], SPY_T=p["spy_t"], RSI_MIN=p["rsi_min"])
    elif leg == "05":
        mm = _mod("05")
        m = mm.side_mask(df, 1, p["g"])
    elif leg == "06":
        m = _mod("06").make_mask(rcl=p["rcl"])(df)
    elif leg == "07":
        m = _with(_mod("07"), _mod("07").mask, df, WINDOW=p["window"], A_MIN=p["a_min"], DROP=p["drop"])
    elif leg == "08":
        m = _with(_mod("08"), _mod("08").mask, df, WINDOW=p["window"], RUN=p["run"], RSI_MIN=p["rsi_min"])
    elif leg == "09":
        m = ult09_mask(df, p["s_t"], None if spy is None else spy[2])
    else:
        raise ValueError(leg)
    tod = df["tod"].to_numpy(dtype=float)     # each component keeps its own intake (inside its mask)
    return np.asarray(m, bool) & (tod >= p["window"][0]) & (tod <= p["window"][1])


def leg_mask(df, leg, t_pct, cfg_set, reg=None) -> np.ndarray:
    """Component rule AND the regime that routes to it (un-thinned)."""
    reg = regime(df, t_pct) if reg is None else reg
    return component_mask(df, leg, CONFIGS[cfg_set][leg]) & (reg == LEG_REGIME[leg])


def _thin(m, df):
    hit = np.flatnonzero(m)
    if not len(hit):
        return m
    key = _keys(df)
    out = np.zeros(len(m), bool)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return np.zeros(len(df), bool)
    m = leg_mask(df, LEG, T_PCT, SET)
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (time-exit legs): catastrophic stop 2R = 0.5 daily ATR beyond the decision close."""
    s = 1 if SIDE == "long" else -1
    return float(f["close"].iloc[i]) - s * 2 * 0.25 * float(f["atr_d"].iloc[i])
