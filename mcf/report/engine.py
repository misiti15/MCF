"""Workbench v2 (owner 2026-11-15): the setup drawn as a machine (ENGINE VIEW) plus a TRADE TEARDOWN per trade that points
back at the engine's numbered parts.

    python -m mcf.report.blueprint <setup_id> [--style engine|blocks] [--trades worst2|best1|id:<n>] [--out DIR]

ENGINE VIEW: six stages left to right, wrapping like an assembly line - INTAKE (which stocks) -> TIMER (when) -> SENSORS
(each entry condition, exact value) -> GATES (market gates, caps, latches, quote checks) -> ENTRY (order, side, size) ->
EXHAUST (stop, target, scale-out, time exit). Every part is numbered P1, P2, ... and shaded by how often it was the
binding reason where the journals measure it: exit parts by the share of live exits they made (stop / target / 15:55
flatten), gate / intake parts by the share of live signals they blocked (journal `signals.reason`).

TRADE TEARDOWN: one live trade (journal run_id = 1) on a 1-minute chart of that day with VWAP and the indicators the
setup reads, entry / stop / target, entry and exit markers, MFE / MAE, lettered callouts that cite the engine's P-numbers,
and the sensor values at the signal bar against their thresholds. Indicator values are recomputed from SIP bars with the
lab frame (mcf.research.heat.heat_frame + setup_lab.extra_features on clock-aligned 5-minute bars), so they can differ a
little from what the live poll saw (live daily priors, the forming minute).

Observation only - nothing here changes a setup. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DISCLAIMER = "Educational only — not financial advice"
TZ = "America/New_York"
# house palette (mcf/report/daily_post.py)
BG, CARD, LINE, INK, MUTED = "#f7f7f5", "#ffffff", "#e3e3e0", "#1b1b1b", "#666666"
UP, DOWN = "#15803d", "#b91c1c"
HEAT = "#d97706"
STAGES = [  # key, title, subtitle, colour
    ("INTAKE", "INTAKE", "which stocks", "#0891b2"),
    ("TIMER", "TIMER", "when it may fire", "#7c3aed"),
    ("SENSORS", "SENSORS", "entry conditions (all must be true)", "#2563eb"),
    ("GATES", "GATES", "what can still block it", "#c2410c"),
    ("ENTRY", "ENTRY", "order, side, size", "#0d9488"),
    ("EXHAUST", "EXHAUST", "how the trade ends", "#db2777"),
]
CONTEXT_COLS = {"spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap", "spy_prng"}
# journal signals.reason -> part role (what blocked the signal)
BLOCK_RULES = [
    (r"shortable|ETB|borrow", "borrow"), (r"max positions for this setup", "cap_setup"),
    (r"lot cap|already in symbol|opposite side held", "cap_symbol"), (r"twin", "twin"),
    (r"setup daily loss", "latch"), (r"^daily loss limit|halted", "acct_stop"), (r"split.tape", "split_gate"),
    (r"stop cost|cost >", "cost_filter"), (r"spread|crosscheck|quote", "quote"), (r"price below minimum", "price"),
]
EXIT_ROLE = {"stop": "stop", "target": "target", "flatten": "time", "scaled+breakeven": "scale", "scaled+target": "scale"}
EXIT_WORDS = {"stop": "stop hit", "target": "target hit", "flatten": "15:55 time exit", "scaled+breakeven": "scaled out, rest at breakeven",
              "scaled+target": "scaled out, rest at target"}


def _hhmm(x) -> str:
    x = int(x)
    return f"{x // 100:02d}:{x % 100:02d}"


def _f(v, nd=4) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n/a"
    s = f"{float(v):.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ================================================================================================ sensor definitions
# stack-module (research/bdi/stack1009 style) triggers / filters as checks on frame columns
TRIG_COLS = {"rsi50": ("rsi", lambda d, p: 50), "rsi14": ("rsi", lambda d, p: p if d == "up" else 100 - p),
             "rsi5": ("rsi5", lambda d, p: p if d == "up" else 100 - p), "vwap": ("vwapDistPct", lambda d, p: 0),
             "ema": ("emaDiff", lambda d, p: 0), "macd": ("macdPct", lambda d, p: 0),
             "sma50": ("sma50_dist_pct", lambda d, p: 0), "sma20": ("sma20_dist_pct", lambda d, p: 0),
             "fo3": ("fromOpen", lambda d, p: 3.0 if d == "up" else -3.0), "slope20": ("sma20_slope_pct", lambda d, p: 0),
             "flow3": ("flow3", lambda d, p: 0.5 if d == "up" else -0.5), "volspike": ("volumeRatio", lambda d, p: 2.0)}
GENERIC_COL = {"ema": "emaDiff", "sma50": "sma50_dist_pct", "slope20": "sma20_slope_pct", "macd": "macdPct",
               "bp": "buyPressure", "flow3": "flow3", "rsi50": "rsi", "gap": "gap", "vwap": "vwapDistPct"}


def sensor_check(cond: dict, side: str) -> dict | None:
    """{col, op, thr, cross (bool), text} - how to test one entry condition on a lab frame row, or None if unknown."""
    s = 1 if side == "long" else -1
    col = cond["col"]
    if cond.get("source") in ("CONDS", "mask") or str(cond.get("source", "")).startswith("const"):
        c = col.strip("|")
        return dict(col=c, abs=col.startswith("|"), op=cond["op"], thr=float(cond["value"]), cross=False,
                    text=f"{col} {cond['op']} {_f(float(cond['value']))}")
    if cond.get("source") == "TRIGGER":
        fam, d, p = (list(cond["value"]) + [None, None, None])[:3]
        if fam not in TRIG_COLS:
            return None
        c, thr = TRIG_COLS[fam][0], TRIG_COLS[fam][1](d, p)
        op = ">" if d == "up" else "<"
        return dict(col=c, abs=False, op=op, thr=float(thr), cross=True, text=f"{c} crosses {'above' if d == 'up' else 'below'} {_f(thr)}")
    if cond.get("source") == "FILTERS":
        name, p = col, cond["value"]
        if name == "rsi_ext":
            return dict(col="rsi", abs=False, op="<=" if s > 0 else ">=", thr=float(100 - p if s > 0 else p), cross=False,
                        text=f"rsi {'<=' if s > 0 else '>='} {_f(100 - p if s > 0 else p)}")
        if name == "rsi5_ext":
            return dict(col="rsi5", abs=False, op="<=" if s > 0 else ">=", thr=float(100 - p if s > 0 else p), cross=False,
                        text=f"rsi5 {'<=' if s > 0 else '>='} {_f(100 - p if s > 0 else p)}")
        if name in ("fo_against", "fo_with"):
            sg = s if name == "fo_with" else -s
            op, thr = (">", float(p)) if sg > 0 else ("<", -float(p))
            return dict(col="fromOpen", abs=False, op=op, thr=thr, cross=False, text=f"fromOpen {op} {_f(thr)}")
        if name == "vol":
            return dict(col="volumeRatio", abs=False, op=">=", thr=float(p), cross=False, text=f"volumeRatio >= {_f(p)}")
        if "_" in name:
            base, how = name.rsplit("_", 1)
            if base in GENERIC_COL and how in ("with", "against"):
                sg = s if how == "with" else -s
                c = GENERIC_COL[base]
                thr = 50.0 if base == "rsi50" else ((1.0 if p is None else float(p)) * sg if base == "gap" else 0.0)
                op = ">" if sg > 0 else "<"
                return dict(col=c, abs=False, op=op, thr=thr, cross=False, text=f"{c} {op} {_f(thr)}")
    return None


def _cmp(v, op, thr) -> bool:
    if v is None or not np.isfinite(v):
        return False
    return {"<": v < thr, "<=": v <= thr, ">": v > thr, ">=": v >= thr, "==": v == thr, "!=": v != thr}[op]


# ================================================================================================ engine layout data
def _part(label, value, role, note=""):
    return dict(label=label, value=value, role=role, note=note, heat=None, heat_note="")


def engine_parts(bp: dict) -> list[dict]:
    """Stages with numbered parts: [{key, title, sub, color, parts: [{pid, label, value, role, note, heat, heat_note}]}].
    Roles let the teardown cite a part: cond.<col>, window, noentry, time.<k>, refire, side, order, size, risk, stop,
    target, scale, time, borrow, cap_setup, cap_symbol, latch, acct_stop, quote, ..."""
    blk, mod = bp["block"], bp.get("module") or {}
    rows = {sec: {a: (b, c) for a, b, c in r} for sec, r in bp["sections"].items()}
    side = bp["side"]
    S = {k: [] for k, *_ in STAGES}
    st = rows["WHICH STOCKS"]
    S["INTAKE"].append(_part("Account universe", st["Account universe"][0], "universe", st["Account universe"][1]))
    if blk.get("min_adv"):
        S["INTAKE"].append(_part("Setup liquidity floor (20d avg $ vol)", st["Liquidity floor (20-day avg $ volume)"][0], "min_adv"))
    S["INTAKE"].append(_part("Price floor", st["Price floor"][0], "price"))
    S["INTAKE"].append(_part("Earnings blackout", st["Earnings blackout"][0], "earnings"))
    if "Pre-filter" in st:
        S["INTAKE"].append(_part("Pre-filter (fixed at the open)", st["Pre-filter"][0], "prefilter", st["Pre-filter"][1]))
    for k in ("Allowed symbols", "Ticker split"):
        if k in st:
            S["INTAKE"].append(_part(k, st[k][0], k.lower().replace(" ", "_")))
    if "Short borrow" in st:
        S["INTAKE"].append(_part("Short borrow", "shortable + easy to borrow", "borrow"))

    wh = rows["WHEN"]
    S["TIMER"].append(_part("Entry window (5-min bar close)", wh["Entry window (5-min bar close)"][0], "window"))
    if "Module's own window" in wh:
        S["TIMER"].append(_part("Module's own window", wh["Module's own window"][0], "module_window"))
    for t in mod.get("time", []):
        S["TIMER"].append(_part("Module time clause", f"bar close {t['op']} {_hhmm(t['value'])}", "time." + t["key"]))
    S["TIMER"].append(_part("No entries before", wh["No entries before"][0], "noentry"))
    S["TIMER"].append(_part("Refire", wh["Refire"][0], "refire"))

    for c in mod.get("conds", []):
        chk = sensor_check(c, side)
        tgt = "GATES" if c["col"].strip("|") in CONTEXT_COLS else "SENSORS"
        val = chk["text"] if chk else (" ".join(_f(x) if isinstance(x, float) else str(x) for x in c["value"] if x is not None)
                                       if isinstance(c["value"], list) else f"{c['col']} {_f(c['value']) if isinstance(c['value'], float) else c['value']}")
        lab = ("Trigger: " if c.get("source") == "TRIGGER" else "") + c["label"]
        S[tgt].append(_part(lab, val, c["key"], c.get("source", "")))
    if mod and not mod.get("conds") and mod.get("layers"):
        for x in mod["layers"]:
            S["SENSORS"].append(_part("Module rule (as described)", x, "layer"))
    if blk.get("context"):
        ctx = blk["context"]
        S["GATES"].append(_part("Market context columns", ", ".join(ctx) if isinstance(ctx, list) else str(ctx), "context"))

    en = rows["ENTRY TRIGGER"]
    if "Split-tape short gate" in en:
        S["GATES"].append(_part("Split-tape short gate", en["Split-tape short gate"][0], "split_gate"))
    lim = rows["LIMITS"]
    S["GATES"].append(_part("Open lots per setup", lim["Open lots per setup"][0], "cap_setup"))
    S["GATES"].append(_part("Lots per symbol", lim["Lots per symbol"][0], "cap_symbol"))
    if "Twin group" in lim:
        S["GATES"].append(_part("Twin group", lim["Twin group"][0], "twin"))
    S["GATES"].append(_part("Per-setup daily latch", lim["Per-setup daily latch"][0], "latch"))
    S["GATES"].append(_part("Account daily stop / halt", lim["Account daily stop"][0], "acct_stop"))
    if "Cost filter" in lim:
        S["GATES"].append(_part("Cost filter", lim["Cost filter"][0], "cost_filter"))
    S["GATES"].append(_part("Quote & spread checks", lim["Spread / size checks"][0], "quote"))

    sz = rows["ACCOUNT & SIZING"]
    rk = rows["RISK & EXIT"]
    S["ENTRY"].append(_part("Side + order", f"{side.upper()} at market, signal-bar close", "order"))
    S["ENTRY"].append(_part("1R (risk unit)", rk["1R (risk unit)"][0], "risk"))
    S["ENTRY"].append(_part("Size per trade", sz["Size per trade"][0], "size"))
    S["ENTRY"].append(_part("Max position", sz["Max position"][0], "max_pos"))

    if "Stop" in rk:
        S["EXHAUST"].append(_part("Stop", rk["Stop"][0], "stop"))
    S["EXHAUST"].append(_part("Target", rk["Target"][0], "target"))
    S["EXHAUST"].append(_part("Scale-out", rk["Scale-out"][0], "scale"))
    for lab in ("Breakeven at", "Trail", "Trail starts at", "Time stop (min)", "Time stop needs"):
        if lab in rk:
            S["EXHAUST"].append(_part(lab, rk[lab][0], lab.lower().replace(" ", "_")))
    S["EXHAUST"].append(_part("Time exit", rk["Time exit"][0], "time"))

    out, n = [], 0
    for key, title, sub, color in STAGES:
        for p in S[key]:
            n += 1
            p["pid"] = f"P{n}"
        out.append(dict(key=key, title=title, sub=sub, color=color, parts=S[key]))
    return out


def all_parts(stages: list[dict]) -> list[dict]:
    return [p for s in stages for p in s["parts"]]


def pref(stages: list[dict], role: str) -> str:
    """P-number of the part with this role ('' if the setup has none)."""
    return next((p["pid"] for p in all_parts(stages) if p["role"] == role), "")


def apply_heat(stages: list[dict], trades: list[dict], signals: list[dict]) -> dict:
    """Shade parts by how often they were binding: exit parts by share of live exits (exit_reason), intake / gate parts by
    share of live signals they blocked (signals.reason). Returns the counts used."""
    ex = {}
    for t in trades:
        r = EXIT_ROLE.get(t.get("exit_reason") or "", "other")
        ex[r] = ex.get(r, 0) + 1
    blocked, nsig = {}, len(signals)
    for s in signals:
        if s.get("status") != "skipped":
            continue
        role = next((ro for rx, ro in BLOCK_RULES if re.search(rx, s.get("reason") or "", re.I)), "other")
        blocked[role] = blocked.get(role, 0) + 1
    nt = len(trades)
    for p in all_parts(stages):
        if nt and p["role"] in ("stop", "target", "time", "scale"):
            k = ex.get(p["role"], 0)
            p["heat"] = k / nt
            p["heat_note"] = f"ended {k}/{nt} live trades ({k / nt:.0%})"
        elif nsig and p["role"] in {ro for _, ro in BLOCK_RULES}:
            k = blocked.get(p["role"], 0)
            p["heat"] = k / nsig
            p["heat_note"] = f"blocked {k}/{nsig} signals ({k / nsig:.0%})"
    return dict(exits=ex, blocked=blocked, signals=nsig, trades=nt)


# ================================================================================================ live trades
def live_trades(setup_id: str, journal=None, branches: dict | None = None) -> tuple[list[dict], list[dict]]:
    """(trades, signals) of this setup from every account journal (run_id = 1). R = pnl_adj / (|entry - stop| x shares)."""
    from . import blueprint as B

    journal = journal or B._journal
    branches = branches if branches is not None else B.data_branches()
    trades, sigs = [], []
    for acct, br in branches.items():
        db = journal(br)
        if db is None:
            continue
        try:
            cur = db.execute("SELECT id, symbol, side, date, signal_time, entry_time, entry, stop, target, exit_time, exit, "
                             "exit_reason, r_multiple, mae_r, mfe_r, shares, pnl, pnl_adj, slip_bps FROM trades WHERE run_id = 1 "
                             "AND strategy = ? AND exit_time IS NOT NULL", (setup_id,))
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                t = dict(zip(cols, row))
                pa = t["pnl_adj"] if t["pnl_adj"] is not None else (t["pnl"] or 0.0)
                risk = abs((t["entry"] or 0) - (t["stop"] or 0)) * (t["shares"] or 0)
                t["r"] = pa / risk if risk else (t["r_multiple"] or 0.0)
                t["acct"] = acct
                trades.append(t)
            for st, rs in db.execute("SELECT status, reason FROM signals WHERE run_id = 1 AND strategy = ?", (setup_id,)):
                sigs.append(dict(status=st, reason=rs, acct=acct))
        except Exception:
            continue
    return trades, sigs


def pick_trades(trades: list[dict], how: str = "worst2") -> list[dict]:
    if not trades:
        return []
    if how.startswith("id:"):
        want = how[3:]
        acct, _, tid = want.rpartition(":")
        return [t for t in trades if str(t["id"]) == tid and (not acct or t["acct"] == acct)][:1]
    m = re.fullmatch(r"(worst|best)(\d+)", how)
    if not m:
        raise ValueError(f"--trades {how!r}: use worst<n>, best<n> or id:[acct:]<n>")
    srt = sorted(trades, key=lambda t: t["r"], reverse=m.group(1) == "best")
    return srt[:int(m.group(2))]


# ================================================================================================ bars + frame
def _rth(df: pd.DataFrame) -> pd.DataFrame:
    t = df.index
    m = ((t.hour > 9) | ((t.hour == 9) & (t.minute >= 30))) & (t.hour < 16)
    return df[m]


def fetch_bars(symbol: str, day: str, lookback_days: int = 40) -> pd.DataFrame:
    """1-minute RTH bars (tz New York) for the session and ~lookback calendar days before it: read-only SIP market data
    GET (mcf.replay.store._fetch_bars)."""
    from ..replay.store import _fetch_bars

    d = pd.Timestamp(day)
    df = _fetch_bars([symbol], f"{(d - timedelta(days=lookback_days)).date()}T13:00:00Z", f"{d.date()}T21:00:00Z", "1Min")
    if df.empty:
        return df
    df = df.set_index(pd.DatetimeIndex(df["ts"]).tz_convert(TZ))[["open", "high", "low", "close", "volume"]].astype(float)
    return _rth(df.sort_index())


def fetch_daily(symbol: str, day: str, lookback_days: int = 60) -> pd.DataFrame:
    """Daily SIP bars (index = session date) strictly before `day` - the live priors' source (prev close, ATR)."""
    from ..replay.store import _fetch_bars

    d = pd.Timestamp(day)
    df = _fetch_bars([symbol], f"{(d - timedelta(days=lookback_days)).date()}T00:00:00Z", f"{d.date()}T00:00:00Z", "1Day")
    if df.empty:
        return df
    df = df.set_index(pd.DatetimeIndex(df["ts"]).tz_convert(TZ).date)[["open", "high", "low", "close", "volume"]].astype(float)
    return df[df.index < d.date()]


def apply_daily(f: pd.DataFrame, daily: pd.DataFrame | None, day) -> pd.DataFrame:
    """As live: gap / prior-day levels / daily ATR(14) of the session from DAILY bars (official close), not RTH 5-min."""
    if daily is None or len(daily) < 2:
        return f
    day = pd.Timestamp(day).date()
    m = f.index.date == day
    if not m.any():
        return f
    f = f.copy()
    pc = daily["close"].shift(1)
    tr = pd.concat([daily.high - daily.low, (daily.high - pc).abs(), (daily.low - pc).abs()], axis=1).max(axis=1)
    atr = float(tr.tail(14).mean())
    last = daily.iloc[-1]
    o = float(f.loc[m, "close"].iloc[0] / (1 + f.loc[m, "fromOpen"].iloc[0] / 100))
    c = f.loc[m, "close"]
    f.loc[m, "gap"] = (o / float(last["close"]) - 1) * 100
    f.loc[m, "atr_d"] = atr
    f.loc[m, "dist_pdh_atr"] = (float(last["high"]) - c) / atr
    f.loc[m, "dist_pdl_atr"] = (c - float(last["low"])) / atr
    return f


def lab_frame(m1: pd.DataFrame) -> pd.DataFrame:
    """Lab frame on clock-aligned 5-minute bars (index = bar start, tod = bar close HHMM) - as the live lab setups build it."""
    from ..data.bars import resample
    from ..research.heat import heat_frame
    from ..research.setup_lab import extra_features

    parts = [resample(g, "5min") for _, g in m1.groupby(m1.index.date)]
    d5 = pd.concat(parts)
    f = heat_frame(d5)
    return f.join(extra_features(d5, f))


# ================================================================================================ teardown data
def signal_bar(f_day: pd.DataFrame, signal_time) -> pd.Timestamp | None:
    """Start of the last completed 5-minute bucket at the signal time (the bar the setup decided on)."""
    ts = pd.Timestamp(signal_time)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
    ts = ts.tz_convert(TZ)
    end = ts.floor("5min")
    k = end - pd.Timedelta(minutes=5)
    cand = f_day.index[f_day.index <= k]
    return cand[-1] if len(cand) else None


def teardown_data(bp: dict, stages: list[dict], trade: dict, m1: pd.DataFrame, frame: pd.DataFrame) -> dict:
    """Everything one teardown shows: day bars, signal bar, sensor readings, MFE/MAE, lettered callouts (with P-refs)."""
    side = bp["side"]
    s = 1 if side == "long" else -1
    day = pd.Timestamp(trade["date"]).date()
    d1 = m1[m1.index.date == day]
    fd = frame[frame.index.date == day]
    et = lambda x: (pd.Timestamp(x).tz_localize("UTC") if pd.Timestamp(x).tzinfo is None else pd.Timestamp(x)).tz_convert(TZ)
    t_in, t_out = et(trade["entry_time"]), et(trade["exit_time"])
    sb = signal_bar(fd, trade.get("signal_time") or trade["entry_time"])
    risk = abs(trade["entry"] - trade["stop"])
    # sensors at the signal bar
    sensors = []
    pos = fd.index.get_loc(sb) if sb is not None else None
    for c in (bp.get("module") or {}).get("conds", []):
        p = next((x for x in all_parts(stages) if x["role"] == c["key"]), None)
        chk = sensor_check(c, side)
        rec = dict(pid=p["pid"] if p else "", label=c["label"], test=chk["text"] if chk else "(not checkable here)",
                   value=None, prev=None, ok=None, flipped=False, col=chk["col"] if chk else None, chk=chk)
        if chk and pos is not None and chk["col"] in fd:
            v = fd[chk["col"]].iloc[pos]
            pv = fd[chk["col"]].iloc[pos - 1] if pos > 0 else np.nan
            if chk["abs"]:
                v, pv = abs(v), abs(pv)
            ok_now = _cmp(float(v), chk["op"], chk["thr"])
            ok_prev = _cmp(float(pv), chk["op"], chk["thr"])
            rec.update(value=float(v), prev=float(pv), ok=ok_now and (not chk["cross"] or not ok_prev),
                       flipped=ok_now and not ok_prev)
        sensors.append(rec)
    # MFE / MAE (journal values; bar extremes for where they happened)
    seg = d1[(d1.index >= t_in.floor("1min")) & (d1.index <= t_out.floor("1min"))]
    mfe_t = mae_t = None
    if len(seg):
        mfe_t = (seg["high"].idxmax() if s > 0 else seg["low"].idxmin())
        mae_t = (seg["low"].idxmin() if s > 0 else seg["high"].idxmax())
    mfe_p = trade["entry"] + s * (trade.get("mfe_r") or 0) * risk
    mae_p = trade["entry"] + s * (trade.get("mae_r") or 0) * risk
    # callouts
    call = []
    sens_p = [x["pid"] for x in sensors if x["pid"]]
    flips = [x for x in sensors if x["flipped"]]
    if sb is not None:
        tod = _hhmm(fd["tod"].loc[sb])
        last = "; last to turn true: " + ", ".join(f"{x['pid']} {x['test']}" for x in flips) if flips else \
            (f"; none newly true on this bar (all held already: {pref(stages, 'refire')} refire)" if bp["block"].get("refire") else "")
        fails = [x["pid"] for x in sensors if x["ok"] is False]
        warn = f" (recomputed bars miss {', '.join(fails)}: the live poll's data differed)" if fails else ""
        rng = f"{sens_p[0]}-{sens_p[-1]}" if len(sens_p) > 1 else (sens_p[0] if sens_p else "sensors")
        call.append(dict(tag="A", t=sb + pd.Timedelta(minutes=5), price=float(fd["close"].loc[sb]),
                         text=f"live signal at the {tod} bar close inside the {pref(stages, 'window')} window: {rng} all met{last}{warn}"))
    slip = f", slip {trade['slip_bps']:.1f} bps" if trade.get("slip_bps") is not None else ""
    call.append(dict(tag="B", t=t_in, price=trade["entry"],
                     text=f"{pref(stages, 'order')} {side} at market {t_in:%H:%M:%S} @ {trade['entry']:.2f} ({trade['shares']} sh{slip}); "
                          f"{pref(stages, 'risk')} 1R = {risk:.2f}"))
    if mfe_t is not None:
        call.append(dict(tag="C", t=mfe_t, price=mfe_p, text=f"best point (MFE) {trade.get('mfe_r') or 0:+.2f}R at {mfe_t:%H:%M}"))
        call.append(dict(tag="D", t=mae_t, price=mae_p, text=f"worst point (MAE) {trade.get('mae_r') or 0:+.2f}R at {mae_t:%H:%M}"))
    er = trade.get("exit_reason") or ""
    tr_r = (trade["target"] - trade["entry"]) * s / risk if trade.get("target") and risk else None
    if tr_r and (trade.get("mfe_r") or 0) >= tr_r and er not in ("target", "scaled+target") and call and call[-1]["tag"] == "D":
        call[-2]["text"] += f" - past the {pref(stages, 'target')} target (+{tr_r:.2f}R) yet the target did not fill"
    call.append(dict(tag="E", t=t_out, price=trade["exit"],
                     text=f"{pref(stages, EXIT_ROLE.get(er, 'time'))} {EXIT_WORDS.get(er, er)} {t_out:%H:%M:%S} @ {trade['exit']:.2f}: "
                          f"{trade['r']:+.2f}R after costs"))
    return dict(trade=trade, side=side, d1=d1, fd=fd, sb=sb, sensors=sensors, callouts=call, t_in=t_in, t_out=t_out,
                risk=risk, mfe=(mfe_t, mfe_p), mae=(mae_t, mae_p))


# ================================================================================================ drawing helpers
def _wrap(s: str, n: int) -> list[str]:
    return textwrap.wrap(str(s), n, break_long_words=True, break_on_hyphens=False) or [""]


def _mix(c1: str, c2: str, a: float) -> str:
    from matplotlib.colors import to_hex, to_rgb

    x, y = np.array(to_rgb(c1)), np.array(to_rgb(c2))
    return to_hex(x * (1 - a) + y * a)


def _fig(w, h):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    return fig, plt


def _canvas(fig, w, h):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return ax


def _header(bp: dict, kind: str, w: float, extra: list[str] | None = None) -> tuple[list, float]:
    """Header draw-list (inches, top-down) and its height."""
    ops, y = [], 0.32
    ops.append(("text", 0.3, y, f"MCF WORKBENCH · {kind} · {bp['date']}", dict(size=7.5, color=MUTED, weight="bold")))
    y += 0.34
    ops.append(("title", 0.3, y, bp["name"], bp["side"]))
    y += 0.24
    ops.append(("text", 0.3, y, bp["setup"], dict(size=7.5, color=MUTED, family="DejaVu Sans Mono")))
    for ln in _wrap(bp.get("what") or "", 104)[:3] if bp.get("what") else []:
        y += 0.19
        ops.append(("text", 0.3, y, ln, dict(size=8, color=INK)))
    for ln in extra or []:
        y += 0.2
        ops.append(("text", 0.3, y, ln, dict(size=8, color=INK, weight="bold")))
    return ops, y + 0.2


def _draw_header(ax, ops, w):
    from matplotlib.patches import FancyBboxPatch

    for op in ops:
        if op[0] == "text":
            ax.text(op[1], op[2], op[3], va="baseline", **op[4])
        else:
            t = ax.text(op[1], op[2], op[3], va="baseline", size=14.5, weight="bold", color=INK)
            r = t.get_window_extent(renderer=ax.figure.canvas.get_renderer())
            x1 = op[1] + r.width / ax.figure.dpi + 0.12
            col = UP if op[4] == "long" else DOWN
            ax.add_patch(FancyBboxPatch((x1, op[2] - 0.15), 0.62, 0.19, boxstyle="round,pad=0,rounding_size=0.04",
                                        fc="none", ec=col, lw=1.3))
            ax.text(x1 + 0.31, op[2] - 0.055, op[4].upper(), ha="center", va="center", size=7.5, weight="bold", color=col)


def _footer(ax, w, y, note=""):
    if note:
        ax.text(w / 2, y, note, ha="center", va="baseline", size=6.8, color=MUTED)
        y += 0.18
    ax.text(w / 2, y, f"Observation only — the original setup is never edited. Paper results. {DISCLAIMER}.",
            ha="center", va="baseline", size=7, color=MUTED)


# ================================================================================================ ENGINE VIEW
W_ENG = 7.6
LH = 0.165   # line height (in) at 8.5 pt


def _plate_h(p, wch_l, wch_v):
    nl, nv = len(_wrap(p["label"], wch_l)), len(_wrap(p["value"], wch_v))
    return 0.1 + (nl + nv) * LH + (0.22 if p["heat"] is not None else 0) + 0.06


def engine_layout(stages: list[dict], top: float) -> dict:
    """Stage boxes in a 2-column wrap (row 1: INTAKE -> TIMER, row 2: SENSORS -> GATES, row 3: ENTRY -> EXHAUST)."""
    mx, gap = 0.22, 0.42
    sw = (W_ENG - 2 * mx - gap) / 2
    wch_l, wch_v = int((sw - 0.72) / 0.064), int((sw - 0.72) / 0.07)
    boxes, y = [], top
    for r in range(0, len(stages), 2):
        row = stages[r:r + 2]
        hs = [0.5 + sum(_plate_h(p, wch_l, wch_v) + 0.07 for p in s["parts"]) + 0.06 for s in row]
        h = max(hs)
        for i, s in enumerate(row):
            boxes.append(dict(stage=s, x=mx + i * (sw + gap), y=y, w=sw, h=h, idx=r + i))
        y += h + 0.5
    return dict(boxes=boxes, bottom=y - 0.5, wch_l=wch_l, wch_v=wch_v, sw=sw, gap=gap)


def render_engine(bp: dict, stages: list[dict], heat: dict | None, path: Path) -> None:
    from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

    rec = bp.get("record") or {}
    extra = []
    if rec.get("trades"):
        tag = "  [1 day]" if rec.get("one_day") else ""
        wo = "n/a" if rec.get("avg_wo_best") is None else f"{rec['avg_wo_best']:+.3f}R"
        extra.append(f"Live: {rec['trades']} trades / {rec['sessions']} sessions ({rec['first']} to {rec['last']}) · "
                     f"avg {rec['avg_r']:+.3f}R after costs · win {rec['win']:.0%}")
        bs = "" if rec.get("best_share") is None else f" (best day {rec['best_day']} = {rec['best_share']:.0%} of R){tag}"
        extra.append(f"Avg R w/o best day {wo}{bs}")
    hdr, top = _header(bp, "ENGINE VIEW", W_ENG, extra)
    rc = rec.get("rule_changes") or []
    rc_lines = []
    if rc:
        rc_lines = [f"Rule changes inside the record window: {len(rc)} (full list in the markdown). Latest:"] + \
                   [x if len(x) <= 118 else x[:117] + "…" for x in rc[-2:]]
    top += 0.05 + (len(rc_lines) * 0.17 if rc_lines else 0)
    lay = engine_layout(stages, top + 0.1)
    legend_h = 0.75
    H = lay["bottom"] + legend_h + 0.55
    fig, plt = _fig(W_ENG, H)
    ax = _canvas(fig, W_ENG, H)
    _draw_header(ax, hdr, W_ENG)
    y0 = top - (len(rc_lines) * 0.17 if rc_lines else 0) - 0.05
    for i, ln in enumerate(rc_lines):
        ax.text(0.3, y0 + i * 0.17, ln, size=6.8, color=MUTED if i else "#b45309", va="baseline",
                weight="bold" if i == 0 else "normal")
    wl, wv = lay["wch_l"], lay["wch_v"]
    B = lay["boxes"]
    for b in B:
        s, x, y, w, h = b["stage"], b["x"], b["y"], b["w"], b["h"]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08", fc=_mix(CARD, s["color"], 0.04),
                                    ec=s["color"], lw=1.6))
        ax.add_patch(FancyBboxPatch((x, y), w, 0.4, boxstyle="round,pad=0,rounding_size=0.08", fc=s["color"], ec=s["color"], lw=1.6))
        ax.add_patch(Rectangle((x, y + 0.25), w, 0.15, fc=s["color"], ec="none"))
        ax.text(x + 0.14, y + 0.27, f"{b['idx'] + 1}  {s['title']}", color="white", size=10.5, weight="bold", va="baseline")
        ax.text(x + w - 0.12, y + 0.265, s["sub"], color="white", size=6.8, va="baseline", ha="right", alpha=0.92)
        py = y + 0.5
        for p in s["parts"]:
            ph = _plate_h(p, wl, wv)
            fc = CARD if not p["heat"] else _mix("#fffbeb", HEAT, 0.12 + 0.75 * min(1.0, p["heat"] ** 0.6))
            ax.add_patch(FancyBboxPatch((x + 0.1, py), w - 0.2, ph, boxstyle="round,pad=0,rounding_size=0.05", fc=fc,
                                        ec=_mix(LINE, s["color"], 0.35), lw=0.9))
            ax.add_patch(Circle((x + 0.34, py + 0.22), 0.165, fc=s["color"], ec="none"))
            ax.text(x + 0.34, py + 0.225, p["pid"], color="white", size=7 if len(p["pid"]) < 3 else 6.2, weight="bold",
                    ha="center", va="center")
            ty = py + 0.08 + LH * 0.75
            for ln in _wrap(p["label"], wl):
                ax.text(x + 0.6, ty, ln, size=8, color=MUTED, va="baseline")
                ty += LH
            for ln in _wrap(p["value"], wv):
                ax.text(x + 0.6, ty, ln, size=8.3, color=INK, weight="bold", va="baseline", family="DejaVu Sans Mono")
                ty += LH
            if p["heat"] is not None:
                bw = w - 0.2 - 0.62 - 0.12
                bx, by = x + 0.6, ty - 0.06
                ax.add_patch(Rectangle((bx, by), bw, 0.07, fc="#f3e8d8", ec="none"))
                ax.add_patch(Rectangle((bx, by), bw * min(1.0, p["heat"]), 0.07, fc=HEAT, ec="none"))
                ax.text(bx, by + 0.19, p["heat_note"], size=6.6, color="#92400e", va="baseline")
            py += ph + 0.07
    # drive shafts between stages
    kw = dict(arrowstyle="-|>,head_length=0.5,head_width=0.3", color="#94a3b8", lw=2.6, mutation_scale=12)
    for a, b in zip(B, B[1:]):
        if a["y"] == b["y"]:
            yy = a["y"] + 0.2
            ax.add_patch(FancyArrowPatch((a["x"] + a["w"] + 0.03, yy), (b["x"] - 0.03, yy), **kw))
        else:
            ym = a["y"] + a["h"] + 0.25
            xa, xb = a["x"] + a["w"] / 2, b["x"] + b["w"] / 2
            ax.plot([xa, xa, xb], [a["y"] + a["h"] + 0.02, ym, ym], color="#94a3b8", lw=2.6, solid_capstyle="round")
            ax.add_patch(FancyArrowPatch((xb, ym), (xb, b["y"] - 0.02), **kw))
    # legend
    ly = lay["bottom"] + 0.28
    ax.add_patch(Rectangle((0.3, ly - 0.09), 0.5, 0.1, fc=_mix("#fffbeb", HEAT, 0.12), ec="none"))
    ax.add_patch(Rectangle((0.8, ly - 0.09), 0.5, 0.1, fc=_mix("#fffbeb", HEAT, 0.87), ec="none"))
    ax.text(1.4, ly, "shade = how often the part was the binding reason: exit parts by share of live exits, intake / gate "
                     "parts by share of", size=6.8, color=MUTED, va="baseline")
    ax.text(1.4, ly + 0.16, "live signals they blocked (refire setups re-signal every bar while held). White = always "
                            "required / not measured.", size=6.8, color=MUTED, va="baseline")
    n = (heat or {}).get("trades", 0)
    _footer(ax, W_ENG, ly + 0.5, f"{n} live trades, {(heat or {}).get('signals', 0)} live signals (journals run_id=1) · "
                                f"module {(bp.get('module') or {}).get('path', '-')}")
    fig.savefig(path, dpi=200, facecolor=BG)
    plt.close(fig)


# ================================================================================================ TRADE TEARDOWN
OSC = [("rsi", "RSI(14)", (0, 100)), ("rsi5", "RSI(5)", (0, 100)), ("buyPressure", "buy pressure (19 bars)", (-1, 1)),
       ("flow3", "3-bar flow", (-1, 1)), ("macdPct", "MACD %", None), ("emaDiff", "EMA9-EMA21 %", None),
       ("sma20_slope_pct", "SMA20 slope % (5 bars)", None), ("fromOpen", "move from open %", None),
       ("volumeRatio", "volume / 20-bar avg", None)]
PRICE_COLS = {"vwapDistPct", "sma20_dist_pct", "sma50_dist_pct", "gap", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr",
              "dist_pdl_atr"}


def render_teardown(bp: dict, stages: list[dict], td: dict, path: Path, rank: str = "") -> None:
    from matplotlib.patches import FancyBboxPatch

    t, side, d1, fd = td["trade"], td["side"], td["d1"], td["fd"]
    s = 1 if side == "long" else -1
    used = [x["col"] for x in td["sensors"] if x["col"]]
    oscs = [o for o in OSC if o[0] in used][:2]
    W = 7.6
    res_col = UP if t["r"] > 0 else DOWN
    extra = [f"{rank}{t['symbol']} · {t['date']} · {t['acct']} trade #{t['id']} · {t['r']:+.2f}R after costs · "
             f"{EXIT_WORDS.get(t.get('exit_reason') or '', t.get('exit_reason') or '')}"]
    hdr, top = _header(dict(bp, what=""), "TRADE TEARDOWN", W, extra)
    ph, oh = 3.3, 1.05
    calls = td["callouts"]
    cw = 100
    cl_lines = sum(len(_wrap(c["text"], cw)) for c in calls)
    sens = td["sensors"]
    sens_h = 0.42 + 0.21 * len(sens) + 0.2
    H = top + 0.15 + ph + oh * len(oscs) + 0.45 + 0.3 + cl_lines * 0.17 + 0.25 + sens_h + 0.7
    fig, plt = _fig(W, H)
    ax0 = _canvas(fig, W, H)
    _draw_header(ax0, hdr, W)
    ax0.texts[-1].set_color(res_col)

    def axes_at(y, h):  # y from top, inches
        return fig.add_axes([0.62 / W, 1 - (y + h) / H, (W - 0.62 - 0.8) / W, h / H])

    x_of = lambda ts: (ts.hour - 9) * 60 + ts.minute - 30 + ts.second / 60
    xs0 = [x_of(td["t_in"])] + ([x_of(td["sb"])] if td["sb"] is not None else [])
    v0 = max(0.0, min(xs0) - 70)
    v1 = min(390.0, max(x_of(td["t_out"]) + 50, v0 + 160))
    v0 = max(0.0, min(v0, v1 - 160))
    ticks = [m for m in range(0, 391, 15 if v1 - v0 <= 200 else 30) if v0 <= m <= v1]
    tlab = [f"{(m + 570) // 60:02d}:{(m + 570) % 60:02d}" for m in ticks]
    y = top + 0.15
    ax = axes_at(y, ph)
    ax.set_facecolor(CARD)
    xs = np.array([x_of(i) for i in d1.index])
    o, h, l, c = (d1[k].to_numpy() for k in ("open", "high", "low", "close"))
    upc = c >= o
    ax.vlines(xs, l, h, color=np.where(upc, "#86b49a", "#d79a9a"), lw=0.6, zorder=2)
    ax.bar(xs, np.where(np.abs(c - o) < 1e-9, (h - l) * 0.02 + 1e-6, c - o), bottom=o, width=0.75,
           color=np.where(upc, "#4d9a6c", "#c25b5b"), zorder=3, lw=0)
    typ = (d1["high"] + d1["low"] + d1["close"]) / 3
    vw = (typ * d1["volume"]).cumsum() / d1["volume"].cumsum().replace(0, np.nan)
    ax.plot(xs, vw.to_numpy(), color="#7c3aed", lw=1.2, label="VWAP", zorder=4)
    fx = np.array([x_of(i + pd.Timedelta(minutes=5)) for i in fd.index])
    if any(k.startswith("sma20") for k in used) or not used:
        sma = fd["close"].rolling(20, min_periods=1).mean()   # day-local fallback when history is short
        if "sma20_dist_pct" in fd:
            sma = fd["close"] / (1 + fd["sma20_dist_pct"] / 100)
        ax.plot(fx, sma.to_numpy(), color="#0891b2", lw=1.1, label="SMA20 (5-min)", zorder=4)
    if "sma50_dist_pct" in used:
        ax.plot(fx, (fd["close"] / (1 + fd["sma50_dist_pct"] / 100)).to_numpy(), color="#65a30d", lw=1.1, label="SMA50 (5-min)")
    day_open = float(d1["open"].iloc[0]) if len(d1) else np.nan
    rlab = []
    if "fromOpen" in used:
        ax.axhline(day_open, color="#64748b", lw=0.8, ls=(0, (2, 2)))
        rlab.append((day_open, f" open {day_open:.2f}", "#64748b"))
        for x in sens:
            if x["col"] == "fromOpen":
                chk = x["chk"]
                lvl = day_open * (1 + chk["thr"] / 100)
                ax.axhline(lvl, color="#2563eb", lw=0.8, ls=(0, (4, 2)))
                rlab.append((lvl, f" {x['pid']} {chk['thr']:+.2f}%", "#2563eb"))
    ti, to = x_of(td["t_in"]), x_of(td["t_out"])
    lvl_labels = []
    for lvl, col, lab in ((t["entry"], INK, f"entry {t['entry']:.2f}"),
                          (t["stop"], DOWN, f"{pref(stages, 'stop')} stop {t['stop']:.2f}"),
                          (t["target"], UP, f"{pref(stages, 'target')} target {t['target']:.2f}" if t["target"] is not None else "")):
        if lvl is None:
            continue
        ax.plot([ti, to], [lvl, lvl], color=col, lw=1.3, ls="-" if col == INK else (0, (5, 2)), zorder=5)
        lvl_labels.append((lvl, lab, col))
        continue
        ax.text(to + 2, lvl, lab, size=6.8, color=col, va="center", weight="bold", zorder=6,
                bbox=dict(fc=CARD, ec="none", pad=0.6, alpha=0.85))
    ax.axvspan(ti, to, color="#fde68a", alpha=0.18, zorder=1)
    w0, w1 = bp["block"].get("window") or [950, 1500]
    xw0, xw1 = (w0 // 100 - 9) * 60 + w0 % 100 - 30, (w1 // 100 - 9) * 60 + w1 % 100 - 30
    ax.axvspan(0, xw0, color="#e5e7eb", alpha=0.55, zorder=0)
    ax.axvspan(xw1, 390, color="#e5e7eb", alpha=0.55, zorder=0)
    if xw0 > v0 + 6:
        ax.text((max(v0, 0) + xw0) / 2, 0.015, f"{pref(stages, 'noentry')} no entry", transform=ax.get_xaxis_transform(), size=6,
                color=MUTED, ha="center", va="bottom")
    if xw1 < v1 - 6:
        ax.text((xw1 + min(v1, 390)) / 2, 0.015, f"{pref(stages, 'window')} closed", transform=ax.get_xaxis_transform(), size=6,
                color=MUTED, ha="center", va="bottom")
    ax.scatter([ti], [t["entry"]], marker="^" if s > 0 else "v", s=70, color=INK, zorder=7, edgecolor="white", lw=0.8)
    ax.scatter([to], [t["exit"]], marker="X", s=70, color=res_col, zorder=7, edgecolor="white", lw=0.8)
    vis = (xs >= v0) & (xs <= v1)
    lo = np.nanmin([np.nanmin(l[vis]) if vis.any() else np.nan, t["stop"], t["target"] or np.inf])
    hi = np.nanmax([np.nanmax(h[vis]) if vis.any() else np.nan, t["stop"], t["target"] or -np.inf])
    pad = (hi - lo) * 0.06
    ax.set_ylim(lo - pad, hi + pad * 1.6)
    for lv, txt, colr in lvl_labels:   # level labels at the right edge, away from the trade's callouts
        ax.plot([to, v1], [lv, lv], color=colr, lw=0.5, ls=":", zorder=4)
        ax.text(v1 - 1, lv, txt, size=6.8, color=colr, va="center", ha="right", weight="bold", zorder=6,
                bbox=dict(fc=CARD, ec="none", pad=0.8, alpha=0.9))
    for lv, txt, colr in rlab:
        if lo - pad <= lv <= hi + pad * 1.6:
            ax.text(v1 + 2, lv, txt, size=6.5, color=colr, va="center", clip_on=False)
    yr = hi - lo + 2.6 * pad
    for cobj in calls:
        if cobj["t"] is None:
            continue
        cx, cy = x_of(cobj["t"]), cobj["price"]
        off = {"A": (-26, 22), "B": (-26, -24), "C": (0, 30) if s < 0 else (0, -30), "D": (24, 26) if s < 0 else (24, -26),
               "E": (30, 6)}[cobj["tag"]]
        fr = (cy - (lo - pad)) / yr
        if fr < 0.18 and off[1] < 0 or fr > 0.85 and off[1] > 0:
            off = (off[0] if off[0] else 26, -off[1])
        ax.annotate(cobj["tag"], (cx, cy), off, textcoords="offset points", size=8, weight="bold", color="white", ha="center",
                    va="center", zorder=9,
                    bbox=dict(boxstyle="circle,pad=0.25", fc="#1e3a8a", ec="none"),
                    arrowprops=dict(arrowstyle="-", color="#1e3a8a", lw=0.9, shrinkA=0, shrinkB=2))
    ax.set_xlim(v0 - 1, v1 + 1)
    ax.set_xticks(ticks)
    ax.set_xticklabels(tlab if not oscs else [""] * len(ticks))
    ax.tick_params(labelsize=7, colors=MUTED, length=2)
    for sp in ax.spines.values():
        sp.set_color(LINE)
    ax.grid(axis="y", color="#f0f0ee", lw=0.6)
    ax.legend(loc="lower right", fontsize=6.5, frameon=True, framealpha=0.85, edgecolor=LINE, ncol=3, borderaxespad=0.3)
    ax.text(0, 1.012, f"1-min bars, {tlab[0] if tlab else ''}-{tlab[-1] if tlab else ''} zoom · VWAP · setup indicators", transform=ax.transAxes, size=6.8, color=MUTED, va="bottom")
    ax.text(1, 1.012, f"MFE {t.get('mfe_r') or 0:+.2f}R · MAE {t.get('mae_r') or 0:+.2f}R", transform=ax.transAxes, size=6.8,
            color=MUTED, va="bottom", ha="right")
    y += ph
    for i, (col, lab, lim) in enumerate(oscs):
        y += 0.06
        a2 = axes_at(y, oh - 0.06)
        a2.set_facecolor(CARD)
        a2.plot(fx, fd[col].to_numpy(), color="#2563eb", lw=1.2)
        a2.axvspan(ti, to, color="#fde68a", alpha=0.18)
        for x in sens:
            if x["col"] == col:
                chk = x["chk"]
                a2.axhline(chk["thr"], color="#c2410c", lw=0.9, ls=(0, (4, 2)))
                a2.text(v1 + 2, chk["thr"], f" {x['pid']} {chk['op']} {_f(chk['thr'], 2)}", size=6.3, color="#c2410c",
                        va="center", clip_on=False)
        if td["sb"] is not None:
            sx = x_of(td["sb"] + pd.Timedelta(minutes=5))
            a2.axvline(sx, color="#1e3a8a", lw=0.8, ls=":")
            a2.scatter([sx], [fd[col].loc[td["sb"]]], s=22, color="#1e3a8a", zorder=5)
        if lim:
            a2.set_ylim(*lim)
            a2.set_yticks([20, 50, 80] if lim[1] == 100 else [-0.5, 0, 0.5])
        a2.set_xlim(v0 - 1, v1 + 1)
        a2.set_xticks(ticks)
        a2.set_xticklabels(tlab if i == len(oscs) - 1 else [""] * len(ticks))
        vv = fd[col].to_numpy()[(fx >= v0) & (fx <= v1)]
        if not lim and len(vv) and np.isfinite(vv).any():
            ths = [x["chk"]["thr"] for x in sens if x["col"] == col]
            a, b = np.nanmin(np.r_[vv, ths]), np.nanmax(np.r_[vv, ths])
            a2.set_ylim(a - (b - a) * 0.1 - 1e-6, b + (b - a) * 0.15 + 1e-6)
        a2.tick_params(labelsize=7, colors=MUTED, length=2)
        for sp in a2.spines.values():
            sp.set_color(LINE)
        a2.text(0.005, 0.96, lab + " (5-min)", transform=a2.transAxes, size=6.8, color=MUTED, va="top")
        y += oh - 0.06
    y += 0.45
    # callouts
    ax0.text(0.3, y, "WHAT HAPPENED (letters on the chart · P-numbers = parts of the engine view)", size=7.5, weight="bold",
             color=INK, va="baseline")
    y += 0.24
    for cobj in calls:
        lines = _wrap(cobj["text"], cw)
        ax0.text(0.42, y - 0.045, cobj["tag"], size=7, weight="bold", color="white", ha="center", va="center",
                 bbox=dict(boxstyle="circle,pad=0.2", fc="#1e3a8a", ec="none"))
        for ln in lines:
            ax0.text(0.62, y, ln, size=7.6, color=INK, va="baseline")
            y += 0.17
        y += 0.02
    y += 0.2
    # sensor panel
    ax0.add_patch(FancyBboxPatch((0.25, y - 0.05), W - 0.5, sens_h - 0.1, boxstyle="round,pad=0,rounding_size=0.06", fc=CARD,
                                 ec=LINE, lw=1))
    sbt = "n/a" if td["sb"] is None else _hhmm(fd["tod"].loc[td["sb"]])
    ax0.text(0.4, y + 0.17, f"SENSORS AT THE SIGNAL BAR ({sbt} bar close, recomputed)", size=7.5, weight="bold", color="#2563eb",
             va="baseline")
    cols_x = [0.4, 0.85, 4.15, 5.3, 6.3]
    yy = y + 0.38
    for xh, hd in zip(cols_x, ["part", "test", "bar before", "signal bar", "met"]):
        ax0.text(xh, yy, hd, size=6.6, color=MUTED, va="baseline")
    for x in sens:
        yy += 0.21
        ax0.text(cols_x[0], yy, x["pid"], size=7.4, weight="bold", color="#2563eb", va="baseline")
        ax0.text(cols_x[1], yy, x["test"][:44], size=7.2, color=INK, va="baseline", family="DejaVu Sans Mono")
        ax0.text(cols_x[2], yy, _f(x["prev"], 3), size=7.2, color=MUTED, va="baseline", family="DejaVu Sans Mono")
        ax0.text(cols_x[3], yy, _f(x["value"], 3), size=7.2, color=INK, va="baseline", family="DejaVu Sans Mono", weight="bold")
        mk = "n/a" if x["ok"] is None else ("yes" if x["ok"] else "NO")
        ax0.text(cols_x[4], yy, mk + (" · flipped" if x["flipped"] else ""), size=7.2, va="baseline",
                 color=MUTED if x["ok"] is None else (UP if x["ok"] else DOWN), weight="bold")
    y += sens_h + 0.12
    _footer(ax0, W, y, "Indicators recomputed from SIP bars (lab frame); live values can differ slightly. Prices from "
                       "the account journal (run_id=1).")
    fig.savefig(path, dpi=200, facecolor=BG)
    plt.close(fig)


# ================================================================================================ markdown
def engine_markdown(stages: list[dict], heat: dict | None) -> list[str]:
    L = ["## ENGINE VIEW (numbered parts)", "", "| Part | Stage | Component | Exact value | Binding share |", "|---|---|---|---|---|"]
    for s in stages:
        for p in s["parts"]:
            L.append(f"| {p['pid']} | {s['title']} | {p['label']} | `{p['value']}` | {p['heat_note'] or '-'} |")
    if heat:
        L += ["", f"Exit mix: {heat['exits']} of {heat['trades']} live trades; blocked signals: {heat['blocked']} of "
                  f"{heat['signals']} live signals (refire setups re-signal every bar while held).", ""]
    return L


def teardown_markdown(td: dict, png: str) -> list[str]:
    t = td["trade"]
    L = [f"### {t['symbol']} {t['date']} ({t['acct']} #{t['id']}): {t['r']:+.2f}R, {t.get('exit_reason')}", "", f"![]({png})", ""]
    L += [f"- **{c['tag']}** {c['text']}" for c in td["callouts"]]
    L += ["", "| Part | Test | Bar before | Signal bar | Met |", "|---|---|---|---|---|"]
    for x in td["sensors"]:
        L.append(f"| {x['pid']} | `{x['test']}` | {_f(x['prev'], 3)} | {_f(x['value'], 3)} | "
                 f"{'n/a' if x['ok'] is None else ('yes' if x['ok'] else 'NO')}{' (flipped)' if x['flipped'] else ''} |")
    return L + [""]
