"""GX5 (owner 2026-10-26): a realistic live expectation for each GEN setup, shown next to its 2-year screen per_day.
Display only: nothing here changes which trades are taken.

The screen's `per_day` is a 2-year MEAN of a skewed, regime-gated count; live sees far fewer on a typical recent day.
research/ops/genexposure1025.md measured why, and these factors come from there:

    expected live trades/day = median-day per_day over the last 60 sessions of the screen history
                               x LIVE_GATE_SHARE (0.97) x (1 + OUTSIDE_SHARE (0.40)) x (1 - FILTER_SHARE (0.19))

  median day, last 60   section 1 / 6 fix 5: the mean (200/day for the 10-23 set) vs the median day (143) vs the last
                        47 sessions (118). Zero days count (a day without a signal is a day of the median).
  LIVE_GATE_SHARE 0.97  section 3, clock-gate what-if (GX1): with the 5-minute clock gate the live runner reproduces
                        1,288 of 1,324 screen signals (97.3%) on the 10-01..07 replay; the old bar-count gate 0.73.
  OUTSIDE_SHARE 0.40    section 4 (a) / 5: live trades every name >= $20M ADV (~2,500), the screen only the 1,222 lab
                        names; outside-lab names added 29 signals to 70 lab signals on 10-19..23 (+40% on the lab count).
  FILTER_SHARE 0.19     section 4 (f): 19 of 99 live Gen signals were skipped at entry (spread 14, ETB 4, opposite
                        side 1) on 10-19..23.
Five live sessions measured these; treat the result as an order of magnitude, not a forecast. Account caps are not in it.
Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np

RECENT_SESSIONS = 60
LIVE_GATE_SHARE = 0.97
OUTSIDE_SHARE = 0.40
FILTER_SHARE = 0.19
SOURCE = "research/ops/genexposure1025.md"


def factor() -> float:
    return LIVE_GATE_SHARE * (1 + OUTSIDE_SHARE) * (1 - FILTER_SHARE)


def expected_live_per_day(median_day: float | None) -> float | None:
    """Expected live trades/day from the screen's median day over the last RECENT_SESSIONS sessions (None: unknown)."""
    if median_day is None:
        return None
    return round(float(median_day) * factor(), 2)


def basis() -> dict:
    """The formula and where each factor comes from (written next to the numbers in generator_lab.json)."""
    return {"formula": "median-day screen trades/day over the last 60 sessions x live-gate share x (1 + outside-universe "
                       "share) x (1 - filter share)",
            "recent_sessions": RECENT_SESSIONS, "live_gate_share": LIVE_GATE_SHARE, "outside_share": OUTSIDE_SHARE,
            "filter_share": FILTER_SHARE, "factor": round(factor(), 4), "source": SOURCE,
            "why": {"median_day": "the screen per_day is a 2-year mean of a skewed, regime-gated count (genexposure1025 s.1)",
                    "live_gate_share": "clock-gate (GX1) replay reproduced 1,288 of 1,324 screen signals, 10-01..07 (s.3)",
                    "outside_share": "names outside the screen's lab universe: +29 signals on 70 lab signals, 10-19..23 (s.4a)",
                    "filter_share": "19 of 99 live signals skipped at entry: spread 14, ETB 4, opposite side 1 (s.4f)"},
            "set_level": "the account total uses the median of the live setups' daily TOTAL over the same 60 sessions "
                         "(a per-setup median is 0 for a setup that fires on fewer than half of the days, so the sum "
                         "of per-setup values understates the set)",
            "note": "Order of magnitude from 5 live sessions; account caps not applied. Display only. "
                    "Educational only - not financial advice."}


def recent_days(P, n: int = RECENT_SESSIONS) -> np.ndarray:
    """Day codes of the panel's last n sessions (P.days is in factorize order, not sorted). Cached on the panel."""
    k = ("_recent_days", n)
    cache = P.__dict__.setdefault("_gx5_cache", {})
    if k not in cache:
        cache[k] = np.argsort(np.asarray(P.days, dtype=str), kind="stable")[-n:]
    return cache[k]


def recent_stats(P, day: np.ndarray, n: int = RECENT_SESSIONS) -> dict:
    """Median and mean signals per session over the panel's last n sessions, for a setup whose first-bar trades fall on
    the day codes `day` (one entry per trade). Sessions without a trade count as 0. A panel without session dates
    (P.days) gives None values."""
    if getattr(P, "days", None) is None:
        return {"per_day_median60": None, "per_day_mean60": None, "recent_window": None, "counts60": None}
    last = recent_days(P, n)
    counts = np.bincount(np.asarray(day, dtype=np.int64), minlength=P.n_days)[last] if len(day) else np.zeros(len(last))
    days = np.asarray(P.days, dtype=str)[last]
    return {"per_day_median60": round(float(np.median(counts)), 3) if len(counts) else None,
            "per_day_mean60": round(float(np.mean(counts)), 3) if len(counts) else None,
            "recent_window": [str(days[0]), str(days[-1])] if len(days) else None,   # `last` is in date order
            "counts60": [int(x) for x in counts]}   # per session, oldest first: the set-level total (summary)


def backfill(months: list[str] | None = None, workers: int = 3, log=print) -> dict:
    """Fill the expectation for the GEN setups already in config/account_gen.yaml without a full generator run: build the
    panel of the last open months only (enough for 60 sessions; the screen's row masks are per row, so the counts are
    the full panel's) and write research/generator/expected_live.json. Each later generator run refreshes every setup
    in its own report (`expected_live`), which the summary prefers."""
    import json
    from datetime import date

    from ..arena import data as AD
    from . import data as D
    from . import screen as S
    from .apply import GEN_DIR, load_account, spec_from_cfg

    ms = months or AD.months("all")[-4:]
    P = D.load(workers=workers, months=ms, log=log)
    acct = load_account()
    out = {}
    for k, v in sorted(acct["strategies"].items()):
        s = spec_from_cfg(v) if k.startswith("GEN-") else None
        if s is not None:
            res = S.evaluate(P, s)
            res["per_day"] = ((v.get("gen") or {}).get("screen") or {}).get("per_day")   # the 2-year screen's
            out[k] = entry(res)
    rep = {"computed": str(date.today()), "months": list(ms), "basis": basis(), "setups": out,
           "note": "Backfill of the GX5 expectation for GEN setups generated before 2026-10-26. Educational only - "
                   "not financial advice."}
    (GEN_DIR / "expected_live.json").write_text(json.dumps(rep, indent=1) + "\n")
    return rep


def entry(res: dict) -> dict:
    """The expectation fields of one screen result (generator run report `expected_live`, generator_lab.json)."""
    return {"per_day": res.get("per_day"), "per_day_median60": res.get("per_day_median60"),
            "per_day_mean60": res.get("per_day_mean60"), "recent_window": res.get("recent_window"),
            "expected_live_per_day": expected_live_per_day(res.get("per_day_median60")),
            "expected_live_mean_basis": expected_live_per_day(res.get("per_day_mean60")),
            "counts60": res.get("counts60")}


def set_total(entries: list[dict]) -> dict | None:
    """Set level (the live GEN setups together): the median of the DAILY TOTAL over the same 60 sessions, x factor().
    A per-setup median is 0 for a setup that fires on fewer than half of the sessions (most regime-gated GEN specs),
    so the sum of per-setup medians understates the set; the median of the daily total is the research's measure
    (genexposure1025: 143 for the 10-23 set). None when the setups' windows differ or counts are missing."""
    xs = [e for e in entries if e.get("counts60")]
    if not xs or len({tuple(e.get("recent_window") or ()) for e in xs}) != 1 or len({len(e["counts60"]) for e in xs}) != 1:
        return None
    tot = np.sum([e["counts60"] for e in xs], axis=0)
    med = float(np.median(tot))
    return {"setups": len(xs), "median_day_total": round(med, 1), "mean_day_total": round(float(tot.mean()), 1),
            "expected_live_per_day": round(med * factor(), 1), "recent_window": xs[0].get("recent_window")}
