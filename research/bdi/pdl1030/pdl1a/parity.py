"""PDL-1a parity: the live modules CWT14-failbrk-pdl-p05-R2A-{long,short} (research/bdi/cwt/live, pdl1a_lib.py) vs the
entries and sides regime-day/score.py scored for row R2A. Educational only - not financial advice.

    python research/bdi/pdl1030/pdl1a/parity.py 2025-06 2025-10 2026-02 2026-08   # -> parity.json (small)

Research side = regime-day/build.py month_job up to the entries (no sim): CWT14 kernel S6.b3_any (PD, side +1, p 0.05,
any volume), adv20 >= 95M, atr_d > 0, bar close 09:50-15:00, first per symbol-day, cost_rt_R <= 0.05, side from the
SPY first-bar prng vs the TRAIN-median cut. Live side = the modules' mask(df) on the same frame rows (frames + 09:35-09:45
head rows, as verify.py), with the lab context column spy_prng set per date.
spy_prng check: the live column is (prev_high - prev_low) / atr of SPY's daily prior (mcf.data.priors._daily_part on
the history daily bars, i.e. what prep builds live) - compared with the frame prng per session.
TRAIN / VALID months only: the locked block 2024-11..2025-02 and HOLD months (2026-04..06, 2026-09-16..10) are refused.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(k, "1")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = Path("/home/user/MCF")   # the history frames / research harness live in the main checkout (not in git)
sys.path[:0] = [str(DATA / "research/bdi/top5_1028"), str(DATA / "research/bdi/top5_1019"),
                str(DATA / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa: E402
from scan_1019 import CL, S6  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
CUT_R2 = 0.7956493496894836
OK_MONTHS = {"2024-10", *(f"2025-{m:02d}" for m in range(3, 13)), "2026-01", "2026-02", "2026-03", "2026-07", "2026-08"}


def _load(name):
    p = REPO / "research/bdi/cwt/live" / f"{name}.py"
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LONG, SHORT = _load("CWT14-failbrk-pdl-p05-R2A-long"), _load("CWT14-failbrk-pdl-p05-R2A-short")


def live_prng(dates) -> pd.Series:
    """SPY (prev_high - prev_low) / ATR(14) per session from the daily bars, exactly as live prep (mcf.data.priors)."""
    from mcf.data.priors import _daily_part

    d = pd.read_parquet(DATA / "research/history2y/data/daily.parquet", filters=[("symbol", "==", "SPY")])
    d = d.assign(timestamp=pd.to_datetime(d["date"]).dt.tz_localize("America/New_York") + pd.Timedelta(hours=4))
    g = d.set_index(["symbol", "timestamp"])[["open", "high", "low", "close", "volume"]]
    out = {}
    for day in dates:
        p = _daily_part(g, pd.Timestamp(day).date()).get("SPY")
        out[str(day)] = np.nan if p is None else (p["prev_high"] - p["prev_low"]) / p["atr"]
    return pd.Series(out)


def month(m):
    assert m in OK_MONTHS, f"{m} is not an open TRAIN/VALID month"
    f, fh, P, dend, fh2P = SC.build_paths(m)
    ds = fh["date"].astype(str)
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    # SPY daily regime (build.py DAY prng: first-bar dist_pdh_atr + dist_pdl_atr)
    sp = f[f["symbol"] == "SPY"]
    fb = sp.sort_values(["date", "tod"]).groupby(sp["date"].astype(str)).first()
    prng = (fb["dist_pdh_atr"] + fb["dist_pdl_atr"]).astype(float)
    # ---- research entries (build.py)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    c = P["close"].to_numpy(float)
    x = CL.arrays(fh)
    lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
        mres = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=np.inf), 0.05), bool)
        mm = mres & base & (ftod >= 950) & (ftod <= 1500)
    e1 = gates.first_per_symbol_day(fsym, fdat, mm)
    ent = fh2P[e1].astype(np.int64)
    cst = (0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4
    cost_rt_R = cst * tier_fh[e1] / risk[e1]
    pr = prng.reindex(fdat[e1]).to_numpy(float)
    side = np.where(pr > CUT_R2, "long", np.where(pr < CUT_R2, "short", ""))
    keep = (cost_rt_R <= 0.05) & (side != "")
    R = pd.DataFrame({"date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "side": side})[keep]
    # ---- live modules on the same rows (adv filter = the YAML min_adv, day-constant)
    g = fh[adv >= 95e6].reset_index(drop=True)
    g["spy_prng"] = prng.reindex(g["date"].astype(str)).to_numpy(float)
    tod = g["tod"].to_numpy()
    win = (tod >= 950) & (tod <= 1500)
    rows = []
    for mod in (LONG, SHORT):
        k = np.flatnonzero(np.asarray(mod.mask(g), bool) & win)
        rows.append(pd.DataFrame({"date": g["date"].astype(str).to_numpy()[k], "symbol": g["symbol"].to_numpy()[k],
                                  "tod": tod[k], "side": mod.SIDE}))
    Lv = pd.concat(rows, ignore_index=True)
    key = ["date", "symbol", "tod", "side"]
    both = R.merge(Lv, on=key, how="inner")
    sd = R.merge(Lv, on=["date", "symbol"], how="inner", suffixes=("_r", "_l"))
    one_day = Lv.groupby(["date"])["side"].nunique().max() if len(Lv) else 0
    lp = live_prng(sorted(prng.index))
    dif = (lp - prng.reindex(lp.index)).abs()
    agree = ((lp > CUT_R2) == (prng.reindex(lp.index) > CUT_R2)).mean()
    out = {"month": m, "sessions": int(prng.size), "research_entries": int(len(R)), "live_entries": int(len(Lv)),
           "matched": int(len(both)), "match_research_pct": round(100 * len(both) / max(1, len(R)), 3),
           "match_live_pct": round(100 * len(both) / max(1, len(Lv)), 3),
           "same_symbol_day_side_agree_pct": round(100 * float((sd["side_r"] == sd["side_l"]).mean()), 3) if len(sd) else None,
           "long_days": int((prng > CUT_R2).sum()), "short_days": int((prng < CUT_R2).sum()),
           "max_sides_per_day_live": int(one_day),
           "entries_per_session_research": round(len(R) / max(1, prng.size), 1),
           "spy_prng_live_vs_frame_max_abs_diff": round(float(dif.max()), 6),
           "spy_prng_live_vs_frame_side_agree_pct": round(100 * float(agree), 2)}
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    res = [month(m) for m in sys.argv[1:]]
    tot = {k: sum(r[k] for r in res) for k in ("research_entries", "live_entries", "matched", "sessions")}
    tot["match_research_pct"] = round(100 * tot["matched"] / max(1, tot["research_entries"]), 3)
    tot["match_live_pct"] = round(100 * tot["matched"] / max(1, tot["live_entries"]), 3)
    (HERE / "parity.json").write_text(json.dumps({"note": "Educational only - not financial advice.", "months": res,
                                                  "total": tot}, indent=1))
    print("TOTAL", json.dumps(tot))
