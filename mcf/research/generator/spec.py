"""Setup Generator specs (owner 2026-10-19): random-but-sensible layered setups for the Setup Generator paper account.

A spec is an AND of 3-5 conditions on the 5-minute decision bars (live trades 5-min bars only):
  * one time-of-day window (always)                                    - required
  * one market-context filter on spy_fo / qqq_fo / breadth / breadth_open (mcf/strategies/lab_context.py) - required
  * 1-2 triggers (fast, event-like indicators from the arena library)  - at least one required
  * 0-2 state filters (slower indicators: trend, stretch, volatility, structure)
plus side, lab geometry (t05s1, t1s1, t1s05, t05s05, hold, holdtr) and a liquidity floor (adv20).
Only indicators the live LabStrategy frame can compute are used (mcf.research.arena.indicators, live=True).
One condition per indicator group, so a spec never stacks near-duplicates (e.g. RSI5 and RSI7).

Canonical hash: thresholds rounded as stored, conditions sorted -> sha1. The registry
(research/generator/registry.jsonl) keeps every spec ever generated so none is generated twice. The "family
signature" (indicator + direction set, side, window; thresholds ignored) is used to avoid ideas already tried in
research/ (arena-style modules with a CONDS list).
Educational only - not financial advice.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

# window name -> (lo, hi) bar-close HHMM, as the YAML `window` (inclusive both ends, live and backtest)
WINDOWS = {"OPEN": (950, 1030), "AM": (950, 1100), "LAM": (1030, 1200), "MID": (1100, 1300),
           "LUNCH": (1130, 1400), "PM": (1300, 1500), "LATE": (1400, 1500)}
WINDOW_WORDS = {"OPEN": "09:50-10:30", "AM": "09:50-11:00", "LAM": "10:30-12:00", "MID": "11:00-13:00",
                "LUNCH": "11:30-14:00", "PM": "13:00-15:00", "LATE": "14:00-15:00"}
GEOMS = ("t05s1", "t1s1", "t1s05", "t05s05", "hold", "holdtr")
GEOM_WORDS = {"t05s1": "target +0.5R / stop 1R", "t1s1": "target +1R / stop 1R", "t1s05": "target +1R / stop 0.5R",
              "t05s05": "target +0.5R / stop 0.5R", "hold": "stop 1R, no target, flat 15:55",
              "holdtr": "stop 1R, no target, 1R trailing stop once +1R, flat 15:55"}
ADV_FLOORS = (20e6, 50e6, 95e6, 150e6)
SIDES = ("long", "short")

# --- context filters: (column, op, value). Values in % (spy_fo / qqq_fo) or share 0..1 (breadth*).
CONTEXT = {
    "spy_fo": [(">", 0.0), (">", 0.25), (">", 0.5), ("<", 0.0), ("<", -0.25), ("<", -0.5)],
    "qqq_fo": [(">", 0.0), (">", 0.3), (">", 0.6), ("<", 0.0), ("<", -0.3), ("<", -0.6)],
    "breadth": [(">", 0.5), (">", 0.6), (">", 0.7), ("<", 0.5), ("<", 0.4), ("<", 0.3)],
    "breadth_open": [(">", 0.5), (">", 0.65), ("<", 0.5), ("<", 0.35)],
}
CONTEXT_CODE = {"spy_fo": "SPY", "qqq_fo": "QQQ", "breadth": "BRvw", "breadth_open": "BRop"}
CONTEXT_WORDS = {"spy_fo": "SPY's move since its open (%)", "qqq_fo": "QQQ's move since its open (%)",
                 "breadth": "the share of stocks above their VWAP", "breadth_open": "the share of stocks above their open"}

# --- indicators: name -> (role, group, code, kinds). role trigger|state; kinds: "lo" (<= low quantile),
# "hi" (>= high quantile), "bin" (== 1), "cat-1"/"cat1" (== -1 / == 1).
IND = {
    # triggers
    "ret1": ("trigger", "ret", "Ret5m", "lo hi"),
    "ret3": ("trigger", "ret", "Ret15m", "lo hi"),
    "ret3_atr": ("trigger", "ret", "Ret15mATR", "lo hi"),
    "rsi2": ("trigger", "osc", "RSI2", "lo hi"),
    "rsi5": ("trigger", "osc", "RSI5", "lo hi"),
    "rsi7": ("trigger", "osc", "RSI7", "lo hi"),
    "z12": ("trigger", "osc", "Z12", "lo hi"),
    "bb_pctb12": ("trigger", "osc", "BBpct", "lo hi"),
    "flow3": ("trigger", "flow", "Flow3", "lo hi"),
    "flow_shift": ("trigger", "flow", "FlowShift", "lo hi"),
    "volumeRatio": ("trigger", "vol", "VolRatio", "hi"),
    "range_exp": ("trigger", "rng", "RangeExp", "hi"),
    "bar_range_atr": ("trigger", "rng", "BarRngATR", "hi"),
    "new_hod": ("trigger", "hod", "NewHOD", "bin"),
    "new_lod": ("trigger", "lod", "NewLOD", "bin"),
    "orb_fail_up": ("trigger", "orb", "ORBfailUp", "bin"),
    "orb_fail_dn": ("trigger", "orb", "ORBfailDn", "bin"),
    "bear_div": ("trigger", "div", "BearDiv", "bin"),
    "bull_div": ("trigger", "div", "BullDiv", "bin"),
    "upper_wick": ("trigger", "wick", "UpWick", "hi"),
    "lower_wick": ("trigger", "wick", "LowWick", "hi"),
    "vwapReclaim": ("trigger", "vwapx", "VWAPx", "cat1 cat-1"),
    "macd_hist": ("trigger", "macdh", "MACDh", "lo hi"),
    "emaDiff_chg3": ("trigger", "macdh", "EMAdChg", "lo hi"),
    "rsiSlope": ("trigger", "rsislope", "RSIslope", "lo hi"),
    # state filters
    "rsi": ("state", "osc14", "RSI14", "lo hi"),
    "fromOpen_atr": ("state", "day", "FromOpenATR", "lo hi"),
    "from_pc_atr": ("state", "day", "FromPCATR", "lo hi"),
    "ret_since950_atr": ("state", "day", "Since950ATR", "lo hi"),
    "day_pos": ("state", "daypos", "DayPos", "lo hi"),
    "gap": ("state", "gap", "Gap", "lo hi"),
    "vwap_atr": ("state", "vwap", "VWAPatr", "lo hi"),
    "vwap_side_bars": ("state", "vwap", "VWAPbars", "lo hi"),
    "sma20_dist_pct": ("state", "sma", "SMA20d", "lo hi"),
    "sma50_dist_pct": ("state", "sma", "SMA50d", "lo hi"),
    "emaDiff": ("state", "trend", "EMAdiff", "lo hi"),
    "sma20_slope_pct": ("state", "trend", "SMA20slope", "lo hi"),
    "slope6_atr": ("state", "trend", "Slope6", "lo hi"),
    "adx7": ("state", "adx", "ADX7", "lo hi"),
    "eff6": ("state", "eff", "Eff6", "lo hi"),
    "atr_d_pct": ("state", "atrd", "ATRd", "lo hi"),
    "day_vs_prev_range": ("state", "drng", "DayRngVsPrev", "lo hi"),
    "compress6_atr": ("state", "comp", "Compress6", "lo"),
    "rvol_day": ("state", "rvol", "RVolDay", "lo hi"),
    "buyPressure": ("state", "bp", "BuyPress", "lo hi"),
    "vwap_cross_n": ("state", "vwapn", "VWAPcrosses", "lo hi"),
    "or_high_dist_atr": ("state", "or", "ORHdist", "lo hi"),
    "or_low_dist_atr": ("state", "or", "ORLdist", "lo hi"),
    "dist_pdh_atr": ("state", "pd", "PDHdist", "lo"),
    "dist_pdl_atr": ("state", "pd", "PDLdist", "lo"),
    "bars_since_hod": ("state", "hod", "BarsSinceHOD", "lo hi"),
    "bars_since_lod": ("state", "lod", "BarsSinceLOD", "lo hi"),
}
INDICATOR_NAMES = tuple(IND)
# Seed-only indicators (mcf/research/generator/seeds.py, owner 2026-10-19): live frame columns that a weekly Setup lab
# rule needs for a faithful translation but that random specs never draw (kept out of IND so the random generator and
# its quantile table are unchanged). They are in the screen panel (generator.data) and computed live like IND.
SEED_IND = {
    "fromOpen": ("state", "day", "FromOpen", "lo hi"),
}
ALL_IND = {**IND, **SEED_IND}
PANEL_NAMES = INDICATOR_NAMES + tuple(SEED_IND)
QUANT_LO = (0.05, 0.10, 0.20, 0.30)
QUANT_HI = (0.70, 0.80, 0.90, 0.95)


@dataclass
class Spec:
    side: str
    window: str
    geom: str
    min_adv: float
    conds: list = field(default_factory=list)       # [(name, op, value)] incl. the context condition

    def canon(self) -> dict:
        cs = sorted((c[0], c[1], round(float(c[2]), 6)) for c in self.conds)
        return {"side": self.side, "window": self.window, "geom": self.geom, "min_adv": float(self.min_adv),
                "conds": [list(c) for c in cs]}

    def key(self) -> str:
        return hashlib.sha1(json.dumps(self.canon(), sort_keys=True).encode()).hexdigest()[:16]

    def family(self) -> str:
        """Thresholds ignored: indicator + direction set, side, window."""
        return family_sig([(c[0], c[1]) for c in self.conds], self.side, WINDOWS[self.window])

    def n_conditions(self) -> int:
        return len(self.conds) + 1     # + the time window

    def roles(self) -> dict:
        r = {"trigger": 0, "state": 0, "context": 0}
        for c in self.conds:
            r["context" if c[0] in CONTEXT else ALL_IND[c[0]][0]] += 1
        return r


def _dir(op: str) -> str:
    return "lo" if op in ("<", "<=") else ("hi" if op in (">", ">=") else "eq")


def family_sig(name_ops, side, window) -> str:
    s = sorted(f"{n}:{_dir(o)}" for n, o in name_ops)
    return f"{side}|{int(window[0])}-{int(window[1])}|" + ",".join(s)


def valid(spec: Spec) -> tuple[bool, str]:
    r = spec.roles()
    if spec.n_conditions() < 3 or spec.n_conditions() > 5:
        return False, "needs 3-5 conditions incl. the window"
    if r["trigger"] < 1 or r["context"] != 1:
        return False, "needs >= 1 trigger and exactly 1 context filter"
    if spec.window not in WINDOWS or spec.geom not in GEOMS or spec.side not in SIDES:
        return False, "bad window/geom/side"
    groups = [IND[c[0]][1] for c in spec.conds if c[0] in IND]
    if len(groups) != len(set(groups)):
        return False, "two conditions from one indicator group"
    return True, "ok"


def valid_seed(spec: Spec) -> tuple[bool, str]:
    """Rules for specs translated from a Setup lab rule (seeds.py): >= 3 conditions incl. the window, exactly one
    context filter, >= 1 stock condition (the lab rule's own layers: a lab rule may be state-only, so no trigger is
    required), indicators the panel and the live frame have, and one indicator group per condition except a range
    (one `>=`/`>` and one `<=`/`<` on the same indicator, e.g. "gap within 2%")."""
    r = spec.roles()
    if spec.n_conditions() < 3:
        return False, "needs >= 3 conditions incl. the window"
    if r["context"] != 1 or r["trigger"] + r["state"] < 1:
        return False, "needs exactly 1 context filter and >= 1 stock condition"
    if spec.window not in WINDOWS or spec.geom not in GEOMS or spec.side not in SIDES:
        return False, "bad window/geom/side"
    by_group: dict = {}
    for c in spec.conds:
        if c[0] in CONTEXT:
            continue
        if c[0] not in ALL_IND:
            return False, f"unknown indicator {c[0]}"
        by_group.setdefault(ALL_IND[c[0]][1], []).append(c)
    for cs in by_group.values():
        if len(cs) == 1:
            continue
        if len(cs) == 2 and cs[0][0] == cs[1][0] and {_dir(cs[0][1]), _dir(cs[1][1])} == {"lo", "hi"}:
            continue
        return False, "two conditions from one indicator group (not a range)"
    return True, "ok"


def nice(v: float) -> float:
    """Round a threshold to 2 significant figures (stable names, readable rules)."""
    if not np.isfinite(v) or v == 0:
        return 0.0
    mag = 10 ** (np.floor(np.log10(abs(v))) - 1)
    return float(round(round(v / mag) * mag, 10))


def random_spec(rng: np.random.Generator, qtab: dict) -> Spec:
    """One random spec. qtab: indicator -> {quantile: value} (train distribution in the universe)."""
    side = str(rng.choice(SIDES))
    window = str(rng.choice(list(WINDOWS)))
    geom = str(rng.choice(GEOMS))
    adv = float(rng.choice(ADV_FLOORS))
    cn = str(rng.choice(list(CONTEXT)))
    op, v = CONTEXT[cn][rng.integers(len(CONTEXT[cn]))]
    conds = [(cn, op, float(v))]
    n_trig = int(rng.choice([1, 1, 2]))
    n_state = int(rng.choice([0, 1, 1, 2]))
    n_state = min(n_state, 4 - n_trig)                  # <= 4 non-window conditions (5 incl. window)
    used = set()
    trig = [k for k, x in IND.items() if x[0] == "trigger" and k in qtab]
    state = [k for k, x in IND.items() if x[0] == "state" and k in qtab]
    for pool, n in ((trig, n_trig), (state, n_state)):
        for _ in range(n):
            cands = [k for k in pool if IND[k][1] not in used]
            if not cands:
                break
            k = str(rng.choice(cands))
            used.add(IND[k][1])
            kind = str(rng.choice(IND[k][3].split()))
            if kind == "bin":
                conds.append((k, "==", 1.0))
            elif kind == "cat1":
                conds.append((k, "==", 1.0))
            elif kind == "cat-1":
                conds.append((k, "==", -1.0))
            elif kind == "lo":
                q = float(rng.choice(QUANT_LO))
                conds.append((k, "<=", nice(qtab[k][q])))
            else:
                q = float(rng.choice(QUANT_HI))
                conds.append((k, ">=", nice(qtab[k][q])))
    return Spec(side, window, geom, adv, conds)


# ------------------------------------------------------------------------------------------------ naming
def _num(v: float) -> str:
    s = f"{abs(v):g}".replace(".", "p")
    return ("m" if v < 0 else "") + s


def cond_code(c) -> str:
    n, op, v = c
    if n in CONTEXT:
        code = CONTEXT_CODE[n]
        if n in ("spy_fo", "qqq_fo") and v == 0:
            return code + ("up" if op in (">", ">=") else "dn")
        return code + ("gt" if op in (">", ">=") else "lt") + _num(v)
    code = ALL_IND[n][2]
    if op == "==":
        return code if v == 1 and ALL_IND[n][3] == "bin" else code + ("Up" if v > 0 else "Dn")
    return code + ("le" if op in ("<", "<=") else "ge") + _num(v)


def setup_name(spec: Spec, date: str, idx: int) -> str:
    d = date.replace("-", "")[2:]
    trig = [c for c in spec.conds if c[0] in ALL_IND and ALL_IND[c[0]][0] == "trigger"]
    state = [c for c in spec.conds if c[0] in ALL_IND and ALL_IND[c[0]][0] == "state"]
    ctx = [c for c in spec.conds if c[0] in CONTEXT]
    parts = [cond_code(c) for c in trig + state] + [spec.window] + [cond_code(c) for c in ctx] + [spec.geom, spec.side]
    return f"GEN-{d}-{idx:02d}-" + "-".join(parts)


def module_slug(spec: Spec, date: str, idx: int) -> str:
    d = date.replace("-", "")[2:]
    stock = [c for c in spec.conds if c[0] in ALL_IND]
    trig = ([c for c in stock if ALL_IND[c[0]][0] == "trigger"] or stock)[0]     # seeds may be state-only
    lab = ALL_IND[trig[0]][2].lower() + ("-" + _dir(trig[1]) if trig[1] != "==" else "")
    return f"GEN-{d}-{idx:02d}-{lab}-{spec.window.lower()}-{spec.side}"


def _cond_words(c) -> str:
    n, op, v = c
    if n in CONTEXT:
        w = {">": "above", ">=": "at or above", "<": "below", "<=": "at or below"}[op]
        return f"{CONTEXT_WORDS[n]} is {w} {v:g}"
    from ..arena.indicators import INDICATORS

    desc = INDICATORS[n].desc
    if op == "==":
        return f"{desc} = {v:g}"
    return f"{desc} {op} {v:g}"


def what(spec: Spec) -> str:
    lo, hi = WINDOWS[spec.window]
    adv = f"${spec.min_adv / 1e6:.0f}M"
    conds = "; ".join(_cond_words(c) for c in spec.conds)
    return (f"{'Buy' if spec.side == 'long' else 'Short'} on the first 5-minute bar closing {WINDOW_WORDS[spec.window]} ET "
            f"where {conds} (stocks with 20-day average dollar volume >= {adv}). Exit {GEOM_WORDS[spec.geom]}, "
            f"R = 0.25 x daily ATR. Machine-generated for exploration; not a tested edge.")


def display_name(spec: Spec) -> str:
    stock = [c for c in spec.conds if c[0] in ALL_IND]
    trig = [c for c in stock if ALL_IND[c[0]][0] == "trigger"] or stock          # seeds may be state-only
    ctx = [c for c in spec.conds if c[0] in CONTEXT][0]
    t = ", ".join(cond_code(c) for c in trig)
    return f"Generated: {t} {spec.window} {spec.side} ({cond_code(ctx)}, {spec.geom})"
