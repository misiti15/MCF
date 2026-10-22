"""Broad replay set: today's setups of each account replayed over many sessions (python -m mcf.replay run, costs in,
trade-through limits). Per account: R per session against the market regime (rule 19 terciles of the universe's median
open-to-close, cut points from the open 2-year history: down < -0.226 %, up > 0.212 %), the recent live weeks against
the weeks before, and the touch-fill counterfactual.

    python research/replay/broad.py --run data/replay/runs/broad [--out research/replay/broad.json]

Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "replay"))

CUTS = (-0.2257916422542917, 0.21235704422257376)   # research/history2y lib.regimes() attrs (open history)
LIVE_FROM = "2026-10-06"


def _stats(r: pd.Series, day: pd.Series) -> dict:
    from mcf.replay.export import setup_stats

    return setup_stats(pd.DataFrame({"r_multiple": r.to_numpy(), "session": day.to_numpy()}))


def main():
    from gap import regime

    from mcf.replay.__main__ import load_run

    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--accounts", default="primary,testing,testing2")
    ap.add_argument("--out")
    a = ap.parse_args()
    run = Path(a.run)
    out = {}
    days_all = sorted({p.parent.name for acct in a.accounts.split(",") for p in (run / acct).glob("*/stats.json")})
    reg = regime(days_all)
    reg["regime"] = np.where(reg.median_oc < CUTS[0], "down", np.where(reg.median_oc > CUTS[1], "up", "flat"))
    out["regimes"] = reg.round(3).to_dict(orient="records")
    rmap = dict(zip(reg.day, reg.regime))
    for acct in a.accounts.split(","):
        tr, sg = load_run(run / acct)
        if not len(tr):
            continue
        tr["regime"] = tr.session.map(rmap)
        tr["period"] = np.where(tr.session >= LIVE_FROM, "live weeks (10-06..)", "before (..10-05)")
        res = {"all": _stats(tr.r_multiple, tr.session),
               "touch_fill_all": _stats(tr.r_touch, tr.session) if "r_touch" in tr else None,
               "by_regime": {k: _stats(g.r_multiple, g.session) for k, g in tr.groupby("regime")},
               "by_period": {k: _stats(g.r_multiple, g.session) for k, g in tr.groupby("period")},
               "period_regime_mix": {k: g.drop_duplicates("session").regime.value_counts().to_dict()
                                     for k, g in tr.groupby("period")}}
        # regime-adjusted expectation for the live weeks: each regime's per-trade R from the earlier sessions,
        # weighted by the live weeks' trade mix
        early, late = tr[tr.session < LIVE_FROM], tr[tr.session >= LIVE_FROM]
        if len(early) and len(late):
            per = early.groupby("regime").r_multiple.mean()
            mix = late.regime.value_counts(normalize=True)
            res["live_weeks_expected_from_regime_mix"] = round(float(sum(per.get(k, np.nan) * w
                                                                         for k, w in mix.items())), 3)
        per_setup = []
        for n, g in tr.groupby("strategy"):
            s = _stats(g.r_multiple, g.session)
            s["setup"] = n
            s["touch_total_r"] = round(float(g.r_touch.sum()), 2) if "r_touch" in g else None
            for k, h in g.groupby("regime"):
                s[f"avg_r_{k}"] = round(float(h.r_multiple.mean()), 3)
            per_setup.append(s)
        res["per_setup"] = sorted(per_setup, key=lambda x: -x["trades"])
        sk = sg[sg.status != "submitted"] if len(sg) else sg
        res["signals"] = {"total": int(len(sg)), "submitted": int((sg.status == "submitted").sum()) if len(sg) else 0,
                          "skips": sk.reason.astype(str).str.replace(r"\d+(\.\d+)?", "#", regex=True).str[:40]
                          .value_counts().head(12).to_dict() if len(sk) else {}}
        out[acct] = res
        print(acct, res["all"], {k: v["avg_r"] for k, v in res["by_regime"].items()},
              {k: v["avg_r"] for k, v in res["by_period"].items()})
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=str))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
