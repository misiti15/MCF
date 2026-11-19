"""TAGS1 score - run ONCE, on or after rules.json score_on_or_after, when >= 20 fresh tagged sessions exist (owner yes
2026-11-18). Refuses earlier (pre-registered; no peeking verdicts). Per rule: would-skip trades, their R after costs,
excess over random removal (same count, same setups, 2,000 draws, seed 1118), day-clustered t, avg R w/o best day,
per-setup better / worse. Educational only - not financial advice.

    python research/tags1/score.py [--tags research/tags1/tags]"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RULES = json.loads((HERE / "rules.json").read_text())


def load(tags: Path) -> pd.DataFrame:
    fs = sorted(Path(tags).glob("*.csv.gz"))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def r_after_costs(t: pd.DataFrame) -> pd.Series:
    risk = (t.entry - t.stop).abs() * t.shares.abs()
    return pd.Series(np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple), index=t.index)


def score(t: pd.DataFrame, rng_seed: int = 1118, draws: int = 2000) -> dict:
    t = t[t.source.eq("live")].copy()
    t["R"] = r_after_costs(t)
    out = {}
    rng = np.random.default_rng(rng_seed)
    for rule, spec in RULES["rules"].items():
        base = t[t.acct.eq("primary")] if spec.get("scope") == "primary" else t
        if rule not in base:
            continue
        hit = base[base[rule].astype(bool)]
        if hit.empty:
            out[rule] = {"n": 0}
            continue
        gain = -float(hit.R.sum())                       # skipping removes these trades' R
        pool = base[base.strategy.isin(hit.strategy.unique())]
        sims = [-float(pool.R.sample(len(hit), random_state=int(rng.integers(1 << 31))).sum()) for _ in range(draws)]
        day = (-hit.groupby("date").R.sum()).reindex(sorted(base.date.unique()), fill_value=0.0)
        t_day = float(day.mean() / (day.std(ddof=1) / math.sqrt(len(day)))) if len(day) > 1 and day.std(ddof=1) > 0 else None
        per = hit.groupby("strategy").R.sum()
        out[rule] = {"n": int(len(hit)), "sessions": int(day.size), "skip_gain_r": round(gain, 2),
                     "random_pct": round(float((np.array(sims) < gain).mean()) * 100, 1), "t_day": t_day,
                     "gain_wo_best_day": round(gain - float(day.max()), 2),
                     "setups_better": int((per < 0).sum()), "setups_worse": int((per > 0).sum())}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default=str(HERE / "tags"))
    a = ap.parse_args(argv)
    t = load(Path(a.tags))
    sessions = int(t.date.nunique()) if len(t) else 0
    today = pd.Timestamp.now(tz="America/New_York").date().isoformat()
    if sessions < RULES["sessions_to_score"] or today < RULES["score_on_or_after"]:
        raise SystemExit(f"TAGS1 is scored once after {RULES['sessions_to_score']} fresh sessions "
                         f"(on/after {RULES['score_on_or_after']}); {sessions} tagged so far - no score.")
    print(json.dumps({"sessions": sessions, "bar": RULES["score"]["bar_t"], "rules": score(t)}, indent=1))


if __name__ == "__main__":
    main()
