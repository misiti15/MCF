"""LEARN1 daily SKILL per model (owner "LEARN1 yes", 2026-11-17): does a model know more than the base rate?

    python -m mcf.report.skill --hunch DIR --compass DIR [--fetch] [--out docs/live/skill.json]

DIR = checkouts of the data branches mcf-data-hunch (guesses/<day>.csv) and mcf-data-compass (compass/<day>.csv,
compass/cond_obs.csv). --fetch fills sessions missing from cond_obs.csv and compass marks missing from compass/<day>.csv
(cron outages) with read-only market-data GETs, in memory; nothing is pushed. DISPLAY / RESEARCH ONLY: it reads no trading config, writes none, feeds nothing to trading.

Per model and session (all forecasts point in time; the session is the unit, so intraday guesses are not counted as
independent):
  hit        share of the model's guesses that were right (probability > 0.5 = "yes")
  base_hit   the same for the base-rate forecast (always guess the majority answer known before the session)
  skill_hit  hit - base_hit
  brier      mean (p - y)^2 of the model's probability; brier_base the same for the base-rate probability
  bss        Brier skill score 1 - brier / brier_base (> 0 = better calibrated than the base rate)
Running: mean of the daily values over the sessions so far with a 95% t interval (sessions as the unit), all live
sessions and since LEARN1 (2026-11-19, the stop/continue window, research/learn1/PLAN.md).

Models
  hunch_pooled / hunch_own  Hunch live shadow, next 3-min bar closes higher (M1), pooled / per-ticker logistic. Base =
             the live base-rate guess (majority answer in the model's history, guesses/*.csv `base_rate`); base
             probability = the share of "yes" answers on all earlier live sessions (0.5 on the first).
  compass_w60  the live Market Compass reading as the dashboard shows it ("In plain English": state -> measured
             chance SPY closes above its open, mcf/report/compass_live.plain) at each recorded 15-min mark, vs SPY's
             close vs open. Live sessions only (compass/<day>.csv).
  compass_cal  COMPCAL: chance SPY finishes on its side of the open from the last 60 sessions' moves to the close
             (mcf/report/compass_cond.calibrated) at every 10-min mark 10:00-15:50, walk-forward over every session
             in cond_obs.csv (sessions before 2026-11-17 are a deterministic replay of the same rule, tagged).
  For both compass models a second, stricter base is reported: "stay" = the share of earlier sessions that closed on
  the side of the open SPY was on at that mark (a reader of the day must beat it; the plain base rate is easy to beat
  once SPY has moved). The stop/continue rule uses it for the compass (PLAN.md).
Educational only — not financial advice.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "live" / "skill.json"
LEARN1_START = "2026-11-19"
SESSIONS_NEEDED = 20
DISCLAIMER = "Educational only — not financial advice."
LABEL = "Display only — not a trading signal"
NAMES = {"hunch_pooled": "Hunch (pooled)", "hunch_own": "Hunch (per ticker)", "compass_w60": "Market Compass (live reading)",
         "compass_cal": "Compass COMPCAL (calibrated)"}
# rule / config changes inside the windows shown (CLAUDE.md rule-change context; research/ledger.jsonl)
CHANGES = [
    {"date": "2026-11-05", "what": "Hunch live shadow starts (200 names, pooled + per-ticker logistic)"},
    {"date": "2026-11-09", "what": "Market Compass (live) recording starts"},
    {"date": "2026-11-11", "what": "Hunch: session not finalised, its guesses were never learned (catch-up added 11-19)"},
    {"date": "2026-11-17", "what": "COMPCAL calibrated line goes on the dashboard (display only)"},
    {"date": "2026-11-19", "what": "LEARN1: Hunch gains 5 inputs (breadth x2, sector from open, volume vs same bar, "
                                  "spread proxy); compass records 4 extra inputs (not votes); skill tracking starts"},
]


# ------------------------------------------------------------------------------------------------------------ scoring
def _day(p: np.ndarray, y: np.ndarray, p_base: np.ndarray, p_stay: np.ndarray | None = None) -> dict | None:
    ok = np.isfinite(p) & np.isfinite(y) & np.isfinite(p_base)
    if p_stay is not None:
        ok &= np.isfinite(p_stay)
    if not ok.any():
        return None
    p, y, pb = p[ok], y[ok], p_base[ok]
    r = dict(n=int(ok.sum()), hit=float(np.mean((p > 0.5) == (y > 0.5))), base_hit=float(np.mean((pb > 0.5) == (y > 0.5))),
             brier=float(np.mean((p - y) ** 2)), brier_base=float(np.mean((pb - y) ** 2)))
    r["skill_hit"] = r["hit"] - r["base_hit"]
    r["bss"] = 1 - r["brier"] / r["brier_base"] if r["brier_base"] > 0 else None
    if p_stay is not None:
        ps = p_stay[ok]
        r["stay_hit"] = float(np.mean((ps > 0.5) == (y > 0.5)))
        r["brier_stay"] = float(np.mean((ps - y) ** 2))
        r["skill_hit_stay"] = r["hit"] - r["stay_hit"]
        r["bss_stay"] = 1 - r["brier"] / r["brier_stay"] if r["brier_stay"] > 0 else None
    return r


def ci(x) -> dict:
    """Mean and 95% t interval of daily values (sessions as the unit)."""
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    n = len(x)
    if not n:
        return dict(n=0, mean=None, lo=None, hi=None)
    m = float(x.mean())
    if n < 2:
        return dict(n=n, mean=m, lo=None, hi=None)
    from scipy import stats

    h = float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / math.sqrt(n))
    return dict(n=n, mean=m, lo=m - h, hi=m + h)


def verdict(c: dict) -> str:
    if c["n"] < 2 or c["lo"] is None:
        return "too few sessions"
    if c["lo"] > 0:
        return "skill above base"
    if c["hi"] < 0:
        return "worse than base"
    return "no skill shown (CI includes 0)"


# ------------------------------------------------------------------------------------------------------------- Hunch
def hunch_days(gdir: Path) -> dict[str, list[dict]]:
    """Daily rows for hunch_pooled / hunch_own from guesses/<day>.csv (live guesses only: backfills left out)."""
    out = {"hunch_pooled": [], "hunch_own": []}
    yes, tot = 0.0, 0.0
    for f in sorted((gdir / "guesses").glob("*.csv")):
        g = pd.read_csv(f)
        if not len(g):
            continue
        s = g[np.isfinite(g["outcome"])]
        if "backfill" in s:
            s = s[s["backfill"] == 0]
        if not len(s):
            continue
        y = s["outcome"].to_numpy(float)
        pb = np.full(len(s), yes / tot if tot else 0.5)
        # the live base-rate GUESS is the model's own point-in-time majority answer: use it for base_hit
        guess_b = s["base_rate"].to_numpy(float)
        for mid, col in (("hunch_pooled", "p_pooled"), ("hunch_own", "p_own")):
            r = _day(s[col].to_numpy(float), y, pb)
            if r is None:
                continue
            r["base_hit"] = float(np.mean(guess_b == y))
            r["skill_hit"] = r["hit"] - r["base_hit"]
            out[mid].append(dict(date=f.stem, source="live", **r))
        yes += float(y.sum())
        tot += float(len(y))
    return out


# ----------------------------------------------------------------------------------------------------------- Compass
def _num(x):
    return pd.to_numeric(x, errors="coerce")


def session_table(obs: pd.DataFrame) -> pd.DataFrame:
    """One row per session: open, close, up (close > open)."""
    d = obs.copy()
    d["open"], d["close"] = _num(d["open"]), _num(d["close"])
    s = d.groupby("date", sort=True).agg(open=("open", "first"), close=("close", "first")).reset_index()
    s["up"] = (s["close"] > s["open"]).astype(float)
    s.loc[s["close"] == s["open"], "up"] = np.nan
    return s


def compass_cal_days(obs: pd.DataFrame, live_from: str = "2026-11-17", min_prior: int = 60) -> list[dict]:
    """COMPCAL walk-forward: for each session, p(side) at every 10-min mark from the prior 60 sessions only."""
    from . import compass_cond as CC

    obs = obs.copy()
    obs["date"] = obs["date"].astype(str)
    obs["fo"] = _num(obs["fo"])
    S = session_table(obs)
    dates = list(S["date"])
    up = dict(zip(S["date"], S["up"]))
    # stay base by mark: did SPY close on the side it was on at T (earlier sessions only)
    obs["eod_open"] = _num(obs["eod_open"])
    obs["stay"] = np.where((obs["fo"] != 0) & obs["eod_open"].notna() & (obs["eod_open"] != 0),
                           (np.sign(obs["fo"]) == obs["eod_open"]).astype(float), np.nan)
    by_date = {d: g for d, g in obs.groupby("date", sort=True)}
    rows = []
    for i, d in enumerate(dates):
        if i < min_prior or not np.isfinite(up[d]):
            continue
        prior = obs[obs["date"].isin(dates[max(0, i - CC.CAL_DAYS):i])]
        cond = {"remaining": CC.remaining(prior)}
        allp = obs[obs["date"].isin(dates[:i])]
        base_up = float(np.nanmean([up[x] for x in dates[:i]]))
        stay = allp.groupby("T")["stay"].mean()
        g = by_date[d]
        ps, pb, pst, ys = [], [], [], []
        for T, fo in zip(g["T"], g["fo"]):
            t = int(T[:2]) * 60 + int(T[3:])
            c = CC.calibrated(cond, t, fo)
            if c is None:
                continue
            ps.append(c["p"] if fo > 0 else 1 - c["p"])
            s = stay.get(T, np.nan)
            pst.append(s if fo > 0 else 1 - s)
            pb.append(base_up)
            ys.append(up[d])
        r = _day(np.array(ps, float), np.array(ys, float), np.array(pb, float), np.array(pst, float))
        if r:
            rows.append(dict(date=d, source="live" if d >= live_from else "replay", **r))
    return rows


def compass_w60_days(cdir: Path, obs: pd.DataFrame, bars_fn=None, log=print) -> list[dict]:
    """The live compass reading as shown ('In plain English' probability) at every recorded mark of every live day.
    With `bars_fn` (compass_live.fetch), a day with missing marks (cron outage) is completed in memory with the same
    point-in-time compute the workflow's backfill uses (nothing is written to the data branch)."""
    from . import compass_live as CL

    S = session_table(obs)
    up = dict(zip(S["date"].astype(str), S["up"]))
    obs = obs.copy()
    obs["date"] = obs["date"].astype(str)
    obs["fo"], obs["eod_open"] = _num(obs["fo"]), _num(obs["eod_open"])
    obs["stay"] = np.where((obs["fo"] != 0) & (obs["eod_open"] != 0), (np.sign(obs["fo"]) == obs["eod_open"]).astype(float), np.nan)
    try:
        table = json.loads(CL.PLAIN.read_text())
    except (OSError, ValueError):
        return []
    rows = []
    for f in sorted((cdir / "compass").glob("20??-??-??.csv")):
        d = f.stem
        y = up.get(d, np.nan)
        if not np.isfinite(y):
            continue
        prior = [x for x in up if x < d and np.isfinite(up[x])]
        base_up = float(np.mean([up[x] for x in prior])) if prior else 0.5
        stay = obs[obs["date"] < d].groupby("T")["stay"].mean()
        recs = [CL._typed(r) for r in CL.read_rows(f)]
        if bars_fn is not None and len(recs) < len(CL.MARKS):
            names = CL.universe()
            close = pd.Timestamp(f"{d} 16:05", tz=CL.NY)
            bars = bars_fn(d, list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names + CL.SECTORS)), close, log=log)
            if "SPY" in bars:
                have = {r["T"] for r in recs}
                new = [r for r in CL.compute(bars, d, close, names) if r["T"] not in have]
                recs = sorted(recs + new, key=lambda r: r["T"])
                log(f"skill: {d} compass marks completed in memory (+{len(new)}, not pushed)")
        ps, pb, pst, ys = [], [], [], []
        for k in range(len(recs)):
            pl = CL.plain(recs[:k + 1], d, None, table)
            fo = recs[k].get("spy_fo")
            if not pl or pl.get("hit") is None or fo is None or not np.isfinite(fo) or fo == 0:
                continue
            st = pl["state"]
            ps.append(1 - pl["hit"] if ("down" in st.lower()) else pl["hit"])
            T = recs[k]["T"]
            t10 = int(T[:2]) * 60 + int(T[3:])
            t10 = max(600, min(950, t10 - t10 % 10))
            s = stay.get(f"{t10 // 60:02d}:{t10 % 60:02d}", np.nan)
            pst.append(s if fo > 0 else 1 - s)
            pb.append(base_up)
            ys.append(y)
        r = _day(np.array(ps, float), np.array(ys, float), np.array(pb, float), np.array(pst, float))
        if r:
            rows.append(dict(date=d, source="live", **r))
    return rows


# ------------------------------------------------------------------------------------------------------------ build
def _r(x, k=4):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), k)


def summarize(mid: str, days: list[dict], stay: bool) -> dict:
    live = [d for d in days if d["source"] == "live"]
    since = [d for d in live if d["date"] >= LEARN1_START]
    key_hit, key_b = ("skill_hit_stay", "bss_stay") if stay else ("skill_hit", "bss")
    run, cum = [], []
    for i, d in enumerate(days):           # running (cumulative) mean of the daily skill, for the trend line
        cum.append(d.get(key_hit))
        c = ci(cum)
        run.append(_r(c["mean"]))
    block = lambda xs: {"sessions": len(xs), "skill_hit": {k: _r(v) for k, v in ci([x.get(key_hit) for x in xs]).items()},
                        "bss": {k: _r(v) for k, v in ci([x.get(key_b) for x in xs]).items()},
                        "skill_hit_vs_base_rate": {k: _r(v) for k, v in ci([x.get("skill_hit") for x in xs]).items()},
                        "bss_vs_base_rate": {k: _r(v) for k, v in ci([x.get("bss") for x in xs]).items()}}
    out = dict(name=NAMES[mid], rule_base="stay (side of the open at the mark)" if stay else "base rate",
               days=[{k: (_r(v) if isinstance(v, float) else v) for k, v in d.items()} | {"running": run[i]}
                     for i, d in enumerate(days)],
               all_live=block(live), since_learn1=block(since))
    if mid == "compass_cal":
        out["replay"] = block([d for d in days if d["source"] == "replay"])
    out["verdict_all_live"] = verdict(ci([x.get(key_b) for x in live]))
    out["verdict_since_learn1"] = verdict(ci([x.get(key_b) for x in since]))
    out["today"] = out["days"][-1] if out["days"] else None
    return out


def build(hunch: Path | None, compass: Path | None, obs: pd.DataFrame | None = None, now: str | None = None,
          bars_fn=None) -> dict:
    models = {}
    if hunch and (hunch / "guesses").exists():
        for mid, days in hunch_days(hunch).items():
            models[mid] = summarize(mid, days, stay=False)
    if compass is not None and obs is not None and len(obs):
        models["compass_w60"] = summarize("compass_w60", compass_w60_days(compass, obs, bars_fn), stay=True)
        models["compass_cal"] = summarize("compass_cal", compass_cal_days(obs), stay=True)
    since = max((m["since_learn1"]["sessions"] for m in models.values()), default=0)
    return dict(generated=now or pd.Timestamp.now(tz="America/New_York").strftime("%Y-%m-%d %H:%M ET"),
                label=LABEL, disclaimer=DISCLAIMER, learn1_start=LEARN1_START,
                rule=dict(sessions_needed=SESSIONS_NEEDED, sessions_so_far=since, decision_due_est="2026-12-17",
                          text="Per model, after 20 sessions from 2026-11-19: primary = daily Brier skill (bss; vs base "
                               "rate for Hunch, vs 'stay' for the compass), 95% t interval over sessions. Interval above "
                               "0 -> skill: propose ONE pre-registered filter test. Interval includes 0 -> cut to a weekly "
                               "light check. research/learn1/PLAN.md"),
                changes=CHANGES, models=models,
                method="mcf/report/skill.py; research/learn1/PLAN.md")


def load_obs(compass: Path | None, fetch: bool = False, upto: str | None = None, log=print) -> pd.DataFrame | None:
    from . import compass_cond as CC

    if compass is None:
        return None
    obs = CC.read_obs(compass / "compass" / "cond_obs.csv")
    if not fetch or not len(obs):
        return obs
    have = set(obs["date"].astype(str))
    last = upto or str(pd.Timestamp.now(tz="America/New_York").date())
    lo = pd.Timestamp(str(obs["date"].max())) - pd.Timedelta(days=14)
    for d in pd.bdate_range(lo, last):
        d = str(d.date())
        if d in have:
            continue
        spy = CC.fetch_spy(d, log=log)
        if spy is None or not len(spy) or (spy.index.hour * 60 + spy.index.minute).max() < 955:
            continue
        prev = obs[obs["date"].astype(str) < d].sort_values(["date", "T"])
        pc = float(prev["close"].iloc[-1]) if len(prev) else None
        obs = pd.concat([obs, pd.DataFrame(CC.day_obs(spy, d, pc))], ignore_index=True)
        log(f"skill: {d} SPY session added in memory (not pushed)")
    return obs.sort_values(["date", "T"]).reset_index(drop=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LEARN1 model skill - display only, not a trading signal")
    ap.add_argument("--hunch", default=None, help="checkout of mcf-data-hunch")
    ap.add_argument("--compass", default=None, help="checkout of mcf-data-compass")
    ap.add_argument("--fetch", action="store_true", help="fill sessions missing from cond_obs.csv (read-only SPY GET)")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    comp = Path(a.compass) if a.compass else None
    from . import compass_live as CL

    js = build(Path(a.hunch) if a.hunch else None, comp, load_obs(comp, a.fetch), bars_fn=CL.fetch if a.fetch else None)
    Path(a.out).write_text(json.dumps(js, indent=1, default=float) + "\n")
    for mid, m in js["models"].items():
        t, st = m["today"] or {}, "stay" in m["rule_base"]
        sk, b = ("skill_hit_stay", "bss_stay") if st else ("skill_hit", "bss")
        print(f"{mid}: {t.get('date')} hit {t.get('hit')} vs {m['rule_base']}: skill {t.get(sk)} bss {t.get(b)} | live "
              f"bss {m['all_live']['bss']} -> {m['verdict_all_live']}")
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
