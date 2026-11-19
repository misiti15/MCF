"""Coverage check for /home/user/MCF/data/cache_fresh (FRESH_PLAN sec. 1, 6). Reads only timestamps / minute counts /
volume - never prices or returns.

  * session calendar = weekdays 2022-10-03..2024-09-13 minus NYSE holidays; cross-checked against SPY's bar dates
    (any mismatch is reported as an abort condition for fresh_bt.py);
  * per symbol: sessions present / expected, first / last date, sessions with < 300 minutes (non-half-day), minutes
    total, bytes; < 50% session coverage flagged (renames / IPOs / survivorship);
  * asserts no bar outside 2022-10-03..2024-09-13 and none in the locked block;
  * writes round5/coverage_fresh.csv + coverage_fresh.json, plus a consolidated cache_fresh/daily.parquet.

    python research/ultimate_1119/round5/verify_fresh.py
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = Path("/home/user/MCF/data/cache_fresh")
HOL = set("""2022-11-24 2022-12-26 2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04
2023-09-04 2023-11-23 2023-12-25 2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04
2024-09-02""".split())
HALF = {"2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03"}


def sessions(a: str, b: str) -> list[str]:
    d, e, out = date.fromisoformat(a), date.fromisoformat(b), []
    while d <= e:
        if d.weekday() < 5 and d.isoformat() not in HOL:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def main():
    cal = sessions("2022-10-03", "2024-09-13")
    fresh = [s for s in cal if s >= "2023-01-03"]
    rows, dailies = [], []
    for p in sorted((OUT / "daily").glob("*.parquet")):
        d = pd.read_parquet(p)
        dailies.append(d)
        ds = [str(x) for x in d["date"]]
        assert min(ds) >= "2022-10-03" and max(ds) <= "2024-09-13"
        assert not any("2024-11-01" <= x <= "2025-02-28" for x in ds)
        dset = set(ds)
        short = [x for x, n in zip(ds, d["n_minutes"]) if n < 300 and x not in HALF]
        bp = OUT / "1Min" / p.name
        rows.append({"symbol": p.stem, "sessions": len(dset & set(cal)), "fresh_sessions": len(dset & set(fresh)),
                     "extra_dates": len(dset - set(cal)), "first": min(ds), "last": max(ds),
                     "short_sessions_lt300min": len(short), "minutes": int(d["n_minutes"].sum()),
                     "bars_on_disk": bp.exists(), "bytes": bp.stat().st_size if bp.exists() else 0})
    cov = pd.DataFrame(rows)
    cov["fresh_cov"] = cov["fresh_sessions"] / len(fresh)
    cov.to_csv(HERE / "coverage_fresh.csv", index=False)
    if dailies:
        pd.concat(dailies, ignore_index=True).to_parquet(OUT / "daily.parquet")
    spy = cov[cov.symbol == "SPY"]
    spy_dates = set(str(x) for x in pd.read_parquet(OUT / "daily" / "SPY.parquet")["date"]) if len(spy) else set()
    want = set((HERE / "symbols_download_all.txt").read_text().split())
    summ = {"calendar_sessions_incl_warmup": len(cal), "fresh_sessions": len(fresh),
            "spy_calendar_match": spy_dates == set(cal) if spy_dates else None,
            "spy_missing": sorted(set(cal) - spy_dates)[:20], "spy_extra": sorted(spy_dates - set(cal))[:20],
            "symbols_wanted": len(want), "symbols_with_daily": len(cov),
            "symbols_with_bars_on_disk": int(cov["bars_on_disk"].sum()) if len(cov) else 0,
            "symbols_missing": sorted(want - set(cov.symbol)) if len(cov) else sorted(want),
            "symbols_lt50pct_fresh_coverage": cov.loc[cov.fresh_cov < 0.5, "symbol"].tolist() if len(cov) else [],
            "symbols_with_short_sessions": int((cov.short_sessions_lt300min > 0).sum()) if len(cov) else 0,
            "bars_gb_on_disk": round(cov["bytes"].sum() / 1e9, 3) if len(cov) else 0,
            "free_gb": round(shutil.disk_usage("/home/user").free / 1e9, 2)}
    summ["symbols_missing_count"] = len(summ["symbols_missing"])
    (HERE / "coverage_fresh.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 15 else f"{len(v)} names") for k, v in summ.items()}, indent=1))


if __name__ == "__main__":
    main()
