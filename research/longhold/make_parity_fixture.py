"""Builds the frozen signal-parity fixture for mcf/longhold/signals.py (DESIGN.md 8.1).

The reference is the study's OWN code: the data/feature part of research/longhold/study.py (everything before the
simulator) and its `stock_targets` function are executed from study.py's source text, with `pd.read_parquet` patched
to return a slice of daily_2016.parquet. So the expected targets are what study.py computes, not a re-implementation.

  python research/longhold/make_parity_fixture.py           # writes tests/data/longhold_parity.csv.gz + _expected.json
  python research/longhold/make_parity_fixture.py --full    # also checks the full 2016-2026 file (slow, local only)

Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
STUDY = HERE / "study.py"
SRC = ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet"
OUT = ROOT / "tests" / "data" / "longhold_parity.csv.gz"
EXP = ROOT / "tests" / "data" / "longhold_parity_expected.json"
COLS = ["symbol", "date", "open", "high", "close", "volume"]


def study_reference(raw: pd.DataFrame, extra: pd.DataFrame | None = None) -> dict:
    """Run study.py's data+feature section and stock_targets on `raw`; return {date: {sym: w}} for S6 N20 W."""
    src = STUDY.read_text()
    head = src.split("# ---------------------------------------------------------------------------------------------- simulator")[0]
    tb = src.split("# ---------------------------------------------------------------------------------------------- target builders")[1]
    tb = tb.split("def ew_universe_targets")[0]
    calls = iter([raw[COLS].copy(), extra if extra is not None else raw[COLS].iloc[:0].copy()])
    real = pd.read_parquet
    ns = {"__file__": str(STUDY), "__name__": "study_ref"}
    pd.read_parquet = lambda *a, **k: next(calls)
    try:
        exec(compile(head + tb, str(STUDY), "exec"), ns)
    finally:
        pd.read_parquet = real
    tg = ns["stock_targets"]("mom12_1", 20, "W", filt_rev=True)
    syms, dates = ns["syms"], ns["dates"]
    return {str(dates[t].date()): {str(syms[i]): float(w[i]) for i in np.flatnonzero(w > 0)} for t, w in tg.items()}


def mcf_targets(raw: pd.DataFrame, days: list[str]) -> dict:
    from mcf.longhold import signals

    return {d: signals.compute(raw, date.fromisoformat(d))["targets"] for d in days}


def main(full: bool = False):
    raw = pd.read_parquet(SRC, columns=COLS)
    raw["symbol"] = raw["symbol"].astype(str)
    sl = raw[(raw.date >= "2025-06-02") & (raw.date <= "2026-08-14")]
    last = sl[sl.date == sl.date.max()]
    liquid = last.assign(dv=last.close * last.volume).sort_values("dv", ascending=False).symbol.tolist()
    rng = np.random.default_rng(20261012)
    pick = sorted(set(rng.choice(liquid[:700], 110, replace=False)) | {"SPY", "QQQ", "XLK"})
    sl = sl[sl.symbol.isin(pick)].copy()
    for c in ("open", "high", "close"):
        sl[c] = sl[c].round(2)
    sl["volume"] = sl["volume"].round(0)
    sl = sl.sort_values(["symbol", "date"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sl.assign(date=sl.date.dt.strftime("%Y-%m-%d")).to_csv(OUT, index=False, compression="gzip")
    back = pd.read_csv(OUT)
    back["date"] = pd.to_datetime(back["date"])
    ref = study_reference(back)
    days = sorted(ref)[-3:]
    exp = {d: ref[d] for d in days}
    EXP.write_text(json.dumps({"strategy": "S6_mom12_1rev_N20_W", "source": "research/longhold/study.py (exec)",
                               "signal_days": exp}, indent=1, sort_keys=True))
    got = mcf_targets(back, days)
    print("slice", back.shape, "days", days, "parity", got == exp, "names", [len(v) for v in exp.values()])
    if full:
        extra = pd.read_parquet(HERE / "data" / "etf_extra.parquet", columns=COLS)
        ref = study_reference(raw, extra)
        days = sorted(ref)[-3:]
        allr = pd.concat([raw, extra[~extra.symbol.isin(raw.symbol.unique())]], ignore_index=True)
        got = mcf_targets(allr, days)
        print("FULL days", days, "parity", all(got[d] == ref[d] for d in days))
        for d in days:
            print(d, sorted(ref[d]))


if __name__ == "__main__":
    main("--full" in sys.argv)
