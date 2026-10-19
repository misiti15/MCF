"""Multi-timeframe harness: score a lab module (SIDE, GEOM, mask(df)) on decision bars of 1, 3, 5, 10 or 15 minutes.

Data: research/history2y/data/frames_tf/<m>min/month=YYYY-MM/*.parquet, built by research/tf1019/data/build_tf.py with
the setup-lab pipeline (data/cache_hist 1-minute SIP -> mcf.data.bars.resample(df, f"{m}min") -> setup_lab.build), see
`build_tf_frame`. `tod` is the true bar-close HHMM on every timeframe; lookbacks are counted in bars (RSI 14 on 1-minute
bars spans 14 minutes). The locked block (2024-11-01..2025-02-28, RESEARCH_RULES rule 19) is never in these frames and
`load_tf` refuses it.

Splits (`SPLITS`, the history2y convention of research/swarm1017): train = 2024-10 + 2025-03..2025-12,
valid = 2026-01-01..2026-10-07, forward = 2026-10-08.. (sessions added on 2026-10-19; never train), open = all of them.

Costs and statistics are research/history2y's (mcf.research.gates): one trade per symbol-day at the first qualifying
decision bar, production-cost R with time-of-day entry costs (`gates.lab_trades`), day-clustered t, the try-count bar
t_required(N) = max(1.5, sqrt(2 ln N)), regime gate (up AND down sessions > 0), walk-forward share, and a random
same-minute baseline: every trade is compared with the mean production R of ALL universe rows (same side, geometry,
adv filter and window) at the same (date, tod) - `ctrl`; `excess = r - ctrl`.

    from mcf.research import timeframes as tf
    tr = tf.run_module_tf("research/bdi/fullday/MF1-945-flowsell-vwapup-FD.py", 3, window=(950, 1500),
                          geom=None, split="open", symbols="core", min_adv=0)
    rep = tf.summarize(tr, n_tries=12)
    table = tf.compare_timeframes(path, minutes=(1, 3, 5, 10, 15), symbols="core", n_tries=12)
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import gates

ROOT = Path(__file__).resolve().parents[2]
HIST = ROOT / "research" / "history2y" / "data"
FRAMES_TF = HIST / "frames_tf"
MINUTES = (1, 3, 5, 10, 15)
LOCKED = ("2024-11-01", "2025-02-28")
LOCKED_MONTHS = ("2024-11", "2024-12", "2025-01", "2025-02")
FIRST = "2024-10-01"
SPLITS = {"train": ("2024-10-01", "2025-12-31"), "valid": ("2026-01-01", "2026-10-07"),
          "forward": ("2026-10-08", "2099-12-31"), "valid_forward": ("2026-01-01", "2099-12-31"),
          "open": ("2024-10-01", "2099-12-31")}
FRAME_GEOMS = ("t1s1", "t05s1", "t1s05")


# ------------------------------------------------------------------------------------------------ building
def build_tf_frame(bars_1min: pd.DataFrame, minutes: int, symbol: str = "X", **kw) -> pd.DataFrame:
    """setup_lab.build on `minutes`-minute bars of one symbol, with `tod` = the true bar-close HHMM.
    heat_frame stamps tod = bar start + 5 minutes (right for 5-minute bars), so the bars go in with their index shifted
    by (minutes - 5) and the index is shifted back afterwards (bar start). minutes=5 is exactly setup_lab.build."""
    from ..data.bars import resample
    from .setup_lab import build

    bars = resample(bars_1min, f"{int(minutes)}min")
    shift = pd.Timedelta(minutes=int(minutes) - 5)
    b = bars.copy()
    b.index = b.index + shift
    x = build({symbol: b}, log=lambda *_: None, **kw)
    if x is None or not len(x):
        return pd.DataFrame()
    x.index = x.index - shift
    x["open"] = bars["open"].reindex(x.index).to_numpy()
    x["volume"] = bars["volume"].reindex(x.index).to_numpy()
    return x


# ------------------------------------------------------------------------------------------------ loading
def _root(root) -> Path:
    return FRAMES_TF if root is None else Path(root)


def months(minutes: int, root=None) -> list[str]:
    d = _root(root) / f"{int(minutes)}min"
    return sorted(p.name.split("=", 1)[1] for p in d.glob("month=*"))


def universe(which: str = "all", root=None) -> list[str]:
    """'all' = symbols with 3/5/10/15-minute frames; 'core' = the subset that also has 1-minute frames."""
    f = _root(root) / ("symbols_core.txt" if which == "core" else "symbols.txt")
    return f.read_text().split()


def load_tf(minutes: int, month: str, columns: list[str] | None = None, symbols=None, root=None) -> pd.DataFrame:
    """One calendar month of `minutes`-minute frames, sorted by symbol, date, tod. The locked block is refused."""
    if month in LOCKED_MONTHS:
        raise PermissionError("the rule-19 locked block (2024-11..2025-02) is not in the timeframe frames")
    import pyarrow.dataset as ds

    p = _root(root) / f"{int(minutes)}min" / f"month={month}"
    if not p.exists():
        return pd.DataFrame(columns=columns or [])
    dset = ds.dataset(str(p), format="parquet")
    flt = None if symbols is None else ds.field("symbol").isin(list(symbols))
    df = dset.to_table(columns=columns, filter=flt).to_pandas()
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        s = df["date"].astype(str)
        df = df[~((s >= LOCKED[0]) & (s <= LOCKED[1]))]
    keys = [c for c in ("symbol", "date", "tod") if c in df]
    return df.sort_values(keys, kind="mergesort").reset_index(drop=True) if keys else df


def load_module(module_path: str):
    path = Path(module_path)
    if not path.is_absolute():
        path = ROOT / path
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"tfmod_{path.stem.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def split_months(split: str, available: list[str]) -> list[str]:
    a, b = SPLITS[split]
    return [m for m in available if a[:7] <= m <= b[:7] and m not in LOCKED_MONTHS]


# ------------------------------------------------------------------------------------------------ scoring
def _in_split(dates, split: str) -> np.ndarray:
    a, b = SPLITS[split]
    s = pd.Series(dates).astype(str).to_numpy()
    return (s >= a) & (s <= b)


def run_module_tf(module_path, minutes: int, window=(950, 1500), geom: str | None = None, split: str = "open",
                  side: str | None = None, symbols=None, min_adv: float = 0.0, context: bool = False,
                  tod_costs: bool = True, root=None) -> pd.DataFrame:
    """Trades of a lab module on `minutes`-minute decision bars (gates.lab_trades conventions: first qualifying bar per
    symbol-day, production-cost R, time-of-day entry costs). `module_path` is a path or an already loaded module
    (SIDE, GEOM, mask(df)). window = (lo, hi) bar-close HHMM, inclusive, inside 09:50-15:00. geom / side default to
    the module's. symbols: None (every symbol of that timeframe), 'core' (the 1-minute subset; like-for-like across
    all five timeframes), 'all', or a list. context=True adds spy_fo/qqq_fo/breadth/breadth_open computed over the
    frame universe (a subset of the live universe, so breadth is approximate).
    Returns DataFrame date, symbol, tod, r, ctrl, excess, minutes, split (train/valid/forward)."""
    mod = module_path if hasattr(module_path, "mask") else load_module(module_path)
    side = side or mod.SIDE
    geom = geom or getattr(mod, "GEOM", "t1s1")
    if geom not in FRAME_GEOMS:
        raise ValueError(f"geometry {geom!r} has no frame outcome columns (frames carry {FRAME_GEOMS})")
    syms = universe(symbols, root) if isinstance(symbols, str) else symbols
    lo, hi = window or (950, 1500)
    lo, hi = max(950, lo), min(1500, hi)
    out = []
    for mo in split_months(split, months(minutes, root)):
        df = load_tf(minutes, mo, symbols=syms, root=root)
        if not len(df):
            continue
        keep = _in_split(df["date"], split)
        df = df[keep].reset_index(drop=True)
        if not len(df):
            continue
        if context:
            from ..strategies.lab_context import context_from_frames

            c = context_from_frames(df)
            df = df.merge(c, on=["date", "tod"], how="left")
        tod = df["tod"].to_numpy(float)
        univ = (tod >= lo) & (tod <= hi) & (df["atr_d"].to_numpy(float) > 0)
        if min_adv:
            univ &= df["adv20"].to_numpy(float) >= min_adv
        with np.errstate(invalid="ignore"):
            m = np.asarray(mod.mask(df), dtype=bool) & univ
        t = gates.lab_trades(df, m, side, geom, tod_costs=tod_costs)
        if not len(t):
            continue
        # random same-minute baseline: mean production R of every universe row at the same (date, tod)
        ok = univ & np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float))
        pr = gates.prod_r(df[f"r_{side}_{geom}"].to_numpy(float)[ok], df[f"win_{side}_{geom}"].to_numpy(float)[ok],
                          df["close"].to_numpy(float)[ok], df["atr_d"].to_numpy(float)[ok], geom,
                          tod=tod[ok] if tod_costs else None)
        ctrl = pd.DataFrame({"date": df["date"].to_numpy()[ok], "tod": tod[ok], "c": pr}).groupby(["date", "tod"])["c"].mean()
        key = pd.MultiIndex.from_arrays([pd.Index(t["date"]), pd.Index(t["tod"].astype(float))])
        t["ctrl"] = ctrl.reindex(key).to_numpy(float)
        out.append(t)
    cols = ["date", "symbol", "tod", "r", "ctrl", "excess", "minutes", "split"]
    if not out:
        return pd.DataFrame(columns=cols)
    t = pd.concat(out, ignore_index=True)
    t["excess"] = t["r"] - t["ctrl"]
    t["minutes"] = int(minutes)
    d = pd.Series(t["date"]).astype(str)
    t["split"] = np.where(d <= SPLITS["train"][1], "train", np.where(d <= SPLITS["valid"][1], "valid", "forward"))
    return t[cols]


def regimes() -> pd.DataFrame:
    """Session regimes over the open history (research/history2y/data/daily.parquet) plus the forward sessions
    (frames_tf/daily_forward.parquet); tercile cut points from the open history up to 2026-10-07 only."""
    d = pd.read_parquet(HIST / "daily.parquet", columns=["symbol", "date", "open", "close"])
    f = FRAMES_TF / "daily_forward.parquet"
    if f.exists():
        d = pd.concat([d, pd.read_parquet(f, columns=["symbol", "date", "open", "close"])], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"]).dt.date
    s = d["date"].astype(str)
    d = d[(s >= FIRST) & ~((s >= LOCKED[0]) & (s <= LOCKED[1]))]
    s = d["date"].astype(str)
    ref = sorted(set(d.loc[s <= SPLITS["valid"][1], "date"]))
    return gates.session_regimes(d, dates=ref)


def summarize(trades: pd.DataFrame, n_tries: int, regime_table: pd.DataFrame | None = None) -> dict:
    """Overall + per-split summaries (gates.summary), the random same-minute baseline (mean ctrl, mean excess and its
    day-clustered t), regime split, walk-forward, t_required(n_tries) and gates.verdict (on the trades given)."""
    if trades is None or not len(trades):
        return {"n": 0, "t_required": gates.t_required(n_tries), "verdict": "retire"}
    reg = regime_table if regime_table is not None else regimes()
    overall = gates.summary(trades)
    ex = trades[np.isfinite(trades["excess"].to_numpy(float))][["date", "excess"]].rename(columns={"excess": "r"})
    exs = gates.summary(ex)
    rs = gates.regime_split(trades, reg)
    wf = gates.walk_forward(trades, exclude_months=LOCKED_MONTHS)
    v, fails = gates.verdict(overall, rs, wf, n_tries)
    return {"overall": overall,
            "by_split": {k: gates.summary(trades[trades["split"] == k]) for k in ("train", "valid", "forward")},
            "random_same_minute": {"ctrl_exp_r": round(float(np.nanmean(trades["ctrl"])), 4),
                                   "excess_exp_r": exs.get("exp_r"), "excess_t": exs.get("t")},
            "regime": {k: rs[k] for k in ("up", "flat", "down")}, "regime_pass": rs["pass"],
            "walk_forward": {"share_positive": wf["share_positive"], "n_folds": wf["n_folds"],
                             "trailing_on": wf["trailing_on"]},
            "t_required": gates.t_required(n_tries), "verdict": v, "fails": fails}


def compare_timeframes(module_path, minutes=MINUTES, n_tries: int = 1, symbols="core", **kw) -> pd.DataFrame:
    """One row per timeframe: n, exp_r, t, train/valid exp, excess vs random, regime pass, wf share, verdict.
    n_tries must count EVERY configuration of the lineage (each timeframe tried is one more)."""
    mod = module_path if hasattr(module_path, "mask") else load_module(module_path)
    reg = regimes()
    rows = []
    for m in minutes:
        t = run_module_tf(mod, m, symbols=symbols, **kw)
        s = summarize(t, n_tries, reg)
        o = s.get("overall", {})
        rows.append({"minutes": m, "n": o.get("n", 0), "exp_r": o.get("exp_r"), "t": o.get("t"),
                     "train_exp": s.get("by_split", {}).get("train", {}).get("exp_r"),
                     "valid_exp": s.get("by_split", {}).get("valid", {}).get("exp_r"),
                     "forward_exp": s.get("by_split", {}).get("forward", {}).get("exp_r"),
                     "excess_vs_random": s.get("random_same_minute", {}).get("excess_exp_r"),
                     "up_r": s.get("regime", {}).get("up", {}).get("exp_r"),
                     "down_r": s.get("regime", {}).get("down", {}).get("exp_r"),
                     "regime_pass": s.get("regime_pass"), "wf_share": s.get("walk_forward", {}).get("share_positive"),
                     "t_required": s["t_required"], "verdict": s["verdict"]})
    return pd.DataFrame(rows)
