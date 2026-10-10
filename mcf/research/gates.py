"""Regime-aware gates for the multi-year history (docs/RESEARCH_RULES.md rule 19, owner 2026-10-08).

Why: finalists chosen on 40 train / 14 valid sessions failed the locked holdouts. The valid and test windows were
down-drift sessions, so short setups looked good because of the regime. These gates are fixed in advance and applied
to every setup scored on the 2-year history (research/history2y):

  production cost   lab R (1c per side) -> production R: 1c + 1 bps per side, the exit side only on non-target exits,
                    +2c extra on stop fills (as research/owner1008/score_holdouts.py; the scan_fast.py haircut is the
                    same cost with both sides always charged). `prod_r`.
  regime split      each session is classed up / flat / down by the universe's median open-to-close return, cut at
                    the terciles of that median over the open history (`session_regimes`). Expectancy after costs
                    must be > 0 in up sessions AND in down sessions, each with n >= REGIME_MIN_N (`regime_split`).
  walk-forward      rolling folds: TRAIN_MONTHS calendar months, then the next TEST_MONTHS month(s) as the test,
                    stepping one month (`walk_forward`). Reported: the share of test folds (n >= FOLD_MIN_N) with
                    expectancy > 0. Gate: share >= WF_MIN_SHARE. Also reported: the "trailing-on" variant that only
                    trades a test month when its train window was positive (does recent form carry over?).
  try-count t       the day-clustered t must reach t_required(N) = max(1.5, sqrt(2 ln N)), N = configurations tried
                    across the setup's lineage. sqrt(2 ln N) is the asymptotic expected maximum of N independent
                    standard-normal statistics, i.e. the t a pure-noise search of size N would reach by luck
                    (`t_required`). `deflated_sharpe` gives the Bailey / Lopez de Prado (2014) deflated Sharpe ratio
                    on daily P/L for reference.

Verdict (`verdict`), pre-declared:
  keep    exp > 0, t >= t_required(N), regime gate passed, walk-forward share >= WF_MIN_SHARE
  rework  not keep, but exp > 0 overall, or one regime (up / down) is positive with t >= 2 and n >= REGIME_MIN_N
          (a regime filter might rescue it; that rework is a new lineage step and counts its configurations)
  retire  everything else
Educational only - not financial advice.
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
REGIME_MIN_N = 30
FOLD_MIN_N = 10
TRAIN_MONTHS, TEST_MONTHS = 3, 1
WF_MIN_SHARE = 0.6
T_FLOOR = 1.5
# Entry-side cost multiplier by entry time (bar-close HHMM): quoted NBBO spreads vs the 1c + 1 bps model, measured on
# our traded names 2026-10-05..09 (research/swarm1010/w5_sources/spread_calibration.md). Provisional: re-measure on
# 20+ sessions. Owner-approved 2026-10-10 (ledger 2026-10-10-tod-costs). Research scoring only, not live orders.
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))


def tod_cost_mult(tod) -> np.ndarray:
    """Multiplier for the entry side's cost at bar-close time tod (HHMM); 1.0 from 10:30."""
    t = np.asarray(tod, float)
    m = np.ones_like(t)
    for edge, mult in reversed(TOD_COST):
        m = np.where(t < edge, mult, m)
    return m


# ------------------------------------------------------------------------------------------------ costs and trades
def prod_r(lab_r, win, close, atr_d, geom: str, r_frac: float = 0.25, tod=None) -> np.ndarray:
    """Production R from the lab's R. The lab charges a flat 1c per side; production charges 1c + 1 bps per side
    (the exit side is free on a target fill, a limit), plus 2c extra on stop fills. With `tod` (entry bar-close HHMM)
    the entry side is scaled by tod_cost_mult (wider spreads early in the session)."""
    up, dn = GEOMK[geom]
    R = r_frac * np.asarray(atr_d, float)
    px = np.asarray(close, float)
    lab = np.asarray(lab_r, float)
    won = np.asarray(win, float) == 1
    gross = lab + 2 * SLIP_PS / R
    stop = (~won) & (gross <= -dn + 1e-6)
    entry_mult = 1.0 if tod is None else tod_cost_mult(tod)
    cost = (SLIP_PS + px * SLIP_BPS) * entry_mult + np.where(won, 0.0, SLIP_PS + px * SLIP_BPS) + np.where(stop, STOP_EXTRA, 0.0)
    return gross - cost / R


def first_per_symbol_day(symbol, date, mask) -> np.ndarray:
    """Row indices of the first True row per (symbol, date), in frame order (frames are sorted by symbol, date, tod)."""
    idx = np.flatnonzero(np.asarray(mask, bool))
    if not len(idx):
        return idx
    key = pd.Series(np.asarray(symbol)[idx]).astype(str).to_numpy() + "|" + pd.Series(np.asarray(date)[idx]).astype(str).to_numpy()
    _, first = np.unique(key, return_index=True)
    return np.sort(idx[first])


def lab_trades(df: pd.DataFrame, mask, side: str, geom: str, tod_costs: bool = True) -> pd.DataFrame:
    """One trade per symbol-day (first qualifying bar), production-cost R with time-of-day entry costs (default
    since 2026-10-10; tod_costs=False reproduces earlier studies). Columns: date, symbol, tod, r."""
    m = np.asarray(mask, bool) & np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float)) & (df["atr_d"].to_numpy(float) > 0)
    idx = first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), m)
    r = prod_r(df[f"r_{side}_{geom}"].to_numpy(float)[idx], df[f"win_{side}_{geom}"].to_numpy(float)[idx],
               df["close"].to_numpy(float)[idx], df["atr_d"].to_numpy(float)[idx], geom,
               tod=df["tod"].to_numpy(float)[idx] if tod_costs else None)
    return pd.DataFrame({"date": pd.to_datetime(df["date"].to_numpy()[idx]).date, "symbol": df["symbol"].to_numpy()[idx],
                         "tod": df["tod"].to_numpy()[idx], "r": r})


# ------------------------------------------------------------------------------------------------ statistics
def summary(trades: pd.DataFrame) -> dict:
    """n, sessions, win rate, exp R, day-clustered SE and t, green days, expectancy without the best day."""
    if trades is None or not len(trades):
        return {"n": 0}
    r = trades["r"].to_numpy(float)
    g = trades.groupby("date")["r"].agg(["sum", "size"])
    mu = float(r.mean())
    se = float(np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)) if len(g) > 1 else float("nan")
    b = g["sum"].idxmax()
    return {"n": int(len(r)), "days": int(len(g)), "win_rate": round(float((r > 0).mean()), 4), "exp_r": round(mu, 4),
            "se": round(se, 4) if np.isfinite(se) else None,
            "t": round(mu / se, 2) if np.isfinite(se) and se > 0 else None,
            "green_days": round(float((g["sum"] > 0).mean()), 3),
            "ex_best_day": round(float((g["sum"].sum() - g.loc[b, "sum"]) / max(1, len(r) - g.loc[b, "size"])), 4)}


def t_required(n_tries: int, floor: float = T_FLOOR) -> float:
    """Try-count-scaled bar: max(floor, sqrt(2 ln N)) - the t a search over N null configurations reaches by luck."""
    n = max(1, int(n_tries))
    return round(max(floor, math.sqrt(2 * math.log(n))) if n > 1 else floor, 3)


def deflated_sharpe(daily_pnl, n_tries: int, sr_var: float | None = None) -> dict:
    """Bailey & Lopez de Prado (2014) deflated Sharpe ratio on per-session P/L (non-annualised).
    SR0 = sqrt(V[SR]) * ((1 - g) * z(1 - 1/N) + g * z(1 - 1/(N e))), g = Euler-Mascheroni; V[SR] defaults to the
    variance of the SR estimator under the null, 1/(T-1). DSR = P(true SR > SR0) given skew and kurtosis."""
    x = np.asarray(daily_pnl, float)
    x = x[np.isfinite(x)]
    T = len(x)
    if T < 3 or x.std(ddof=1) == 0:
        return {"sr": None, "sr0": None, "dsr": None, "T": T}
    sr = x.mean() / x.std(ddof=1)
    z = (x - x.mean()) / x.std(ddof=0)
    skew, kurt = float((z ** 3).mean()), float((z ** 4).mean())
    nd, g = NormalDist(), 0.5772156649
    v = sr_var if sr_var is not None else 1.0 / (T - 1)
    n = max(2, int(n_tries))
    sr0 = math.sqrt(v) * ((1 - g) * nd.inv_cdf(1 - 1 / n) + g * nd.inv_cdf(1 - 1 / (n * math.e)))
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr ** 2))
    dsr = nd.cdf((sr - sr0) * math.sqrt(T - 1) / den)
    return {"sr": round(float(sr), 4), "sr0": round(float(sr0), 4), "dsr": round(float(dsr), 4), "T": T}


# ------------------------------------------------------------------------------------------------ regimes
def session_regimes(daily: pd.DataFrame, dates=None) -> pd.DataFrame:
    """Class each session up / flat / down by the cross-sectional median open-to-close return (%) of the universe.
    `daily` has columns date, open, close (one row per symbol-day). Tercile cut points are computed over `dates`
    (default: every session in `daily`), so a locked block can be left out of the cut points.
    Returns DataFrame indexed by date: med_o2c, regime."""
    d = daily[(daily["open"] > 0) & np.isfinite(daily["close"])]
    med = ((d["close"] / d["open"] - 1) * 100).groupby(d["date"]).median().rename("med_o2c")
    ref = med if dates is None else med[med.index.isin(set(dates))]
    lo, hi = np.quantile(ref.to_numpy(), [1 / 3, 2 / 3])
    out = med.to_frame()
    out["regime"] = np.where(med <= lo, "down", np.where(med >= hi, "up", "flat"))
    out.attrs["cuts"] = (float(lo), float(hi))
    return out


def regime_split(trades: pd.DataFrame, regimes: pd.DataFrame, min_n: int = REGIME_MIN_N) -> dict:
    """Per-regime summary and the gate: exp > 0 in up AND down sessions, each with n >= min_n."""
    if trades is None or not len(trades):
        return {"up": {"n": 0}, "flat": {"n": 0}, "down": {"n": 0}, "pass": False}
    reg = trades["date"].map(regimes["regime"])
    out = {k: summary(trades[reg.to_numpy() == k]) for k in ("up", "flat", "down")}
    out["pass"] = all(out[k].get("n", 0) >= min_n and out[k].get("exp_r", -1) > 0 for k in ("up", "down"))
    return out


# ------------------------------------------------------------------------------------------------ walk-forward
def walk_forward(trades: pd.DataFrame, months=None, train_months: int = TRAIN_MONTHS, test_months: int = TEST_MONTHS,
                 min_n: int = FOLD_MIN_N, exclude_months=()) -> dict:
    """Rolling folds over calendar months: train = `train_months` consecutive months, test = the next `test_months`.
    The setup is fixed, so the train window does not fit anything; it is used for the trailing-on variant (trade the
    test month only if the train window's expectancy was > 0). Folds whose window touches an excluded month (the
    locked block) are skipped. Returns folds, share_positive (test folds with n >= min_n), and trailing-on stats."""
    if trades is None or not len(trades):
        return {"folds": [], "n_folds": 0, "share_positive": None, "trailing_on": {"n_folds": 0}}
    per = pd.PeriodIndex(pd.to_datetime(trades["date"]), freq="M")
    months = sorted(set(per)) if months is None else sorted(pd.Period(m, freq="M") for m in months)
    excl = {pd.Period(m, freq="M") for m in exclude_months}
    r = trades["r"].to_numpy(float)
    folds = []
    for i in range(len(months) - train_months - test_months + 1):
        tr_m, te_m = months[i:i + train_months], months[i + train_months:i + train_months + test_months]
        if excl & set(tr_m + te_m) or any((b - a).n != 1 for a, b in zip(tr_m + te_m, (tr_m + te_m)[1:])):
            continue
        a, b = np.isin(per, tr_m), np.isin(per, te_m)
        folds.append({"test": str(te_m[0]), "train_n": int(a.sum()), "train_exp": float(r[a].mean()) if a.any() else None,
                      "test_n": int(b.sum()), "test_exp": float(r[b].mean()) if b.any() else None,
                      "test_sum": float(r[b].sum())})
    ok = [f for f in folds if f["test_n"] >= min_n]
    share = round(sum(f["test_exp"] > 0 for f in ok) / len(ok), 3) if ok else None
    on = [f for f in ok if f["train_n"] >= min_n and f["train_exp"] > 0]
    n_on = sum(f["test_n"] for f in on)
    trailing = {"n_folds": len(on), "n": n_on, "exp_r": round(sum(f["test_sum"] for f in on) / n_on, 4) if n_on else None,
                "share_positive": round(sum(f["test_exp"] > 0 for f in on) / len(on), 3) if on else None}
    return {"folds": folds, "n_folds": len(ok), "share_positive": share, "trailing_on": trailing}


# ------------------------------------------------------------------------------------------------ verdict
def per_quarter(trades: pd.DataFrame) -> dict:
    if trades is None or not len(trades):
        return {}
    q = pd.PeriodIndex(pd.to_datetime(trades["date"]), freq="Q").astype(str)
    g = trades.groupby(q)["r"].agg(["mean", "size"])
    return {k: {"exp_r": round(float(v["mean"]), 4), "n": int(v["size"])} for k, v in g.iterrows()}


def verdict(overall: dict, regime: dict, wf: dict, n_tries: int) -> tuple[str, list[str]]:
    """keep / rework / retire with the list of failed gates (pre-declared; see module docstring)."""
    fails = []
    exp, t = overall.get("exp_r", -1), overall.get("t") or 0.0
    if not overall.get("n") or exp <= 0:
        fails.append("exp<=0")
    treq = t_required(n_tries)
    if t < treq:
        fails.append(f"t {t} < {treq}")
    if not regime.get("pass"):
        fails.append("regime (up and down must both be > 0)")
    if wf.get("share_positive") is None or wf["share_positive"] < WF_MIN_SHARE:
        fails.append(f"walk-forward share {wf.get('share_positive')} < {WF_MIN_SHARE}")
    if not fails:
        return "keep", fails
    rescue = any(regime.get(k, {}).get("n", 0) >= REGIME_MIN_N and regime[k].get("exp_r", -1) > 0 and (regime[k].get("t") or 0) >= 2
                 for k in ("up", "down"))
    return ("rework" if exp > 0 or rescue else "retire"), fails
