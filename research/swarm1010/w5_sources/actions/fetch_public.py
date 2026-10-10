"""Fetch free public data that the Claude container's proxy blocks (run on GitHub Actions; see public-data.yml).

Sources (all no-key, polite: one request at a time, User-Agent with contact as SEC requires):
  finra   FINRA Reg SHO consolidated daily short volume, CNMSshvolYYYYMMDD.txt, pipe-delimited
          Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market (+ a trailer line). Off-exchange (TRF) short
          volume only - NOT short interest. Kept for symbols in data/universe.csv. -> finra_shvol_YYYY.parquet
  cboe    VIX, VIX9D, VIX3M, VVIX daily history CSVs from cdn.cboe.com -> cboe_vol_indices.parquet
  ff      Fama-French 3 factors + momentum daily, 12/48 industry portfolios daily (Ken French library) -> ff_*.parquet
  fred    FRED daily series via fredgraph.csv (no key): DGS10, DGS2, T10Y2Y, DFF, BAMLH0A0HYM2, DTWEXBGS -> fred.parquet
  earn    Nasdaq earnings calendar, one request per weekday (same endpoint as mcf/data/earnings.py) -> earnings_cal.parquet
The rule-19 locked block (2024-11..2025-02) is written to separate *_lockedblock.parquet files for the lead.
Usage: python fetch_public.py --out public_data --since 2024-10-01 [--only finra cboe ff fred earn]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse, io, os, time, zipfile
import pandas as pd, requests

UA = os.environ.get("SEC_UA", "MCF research (contact via GitHub repo owner)")
S = requests.Session(); S.headers["User-Agent"] = UA
LOCKED = ("2024-11-01", "2025-02-28")


def get(url, **kw):
    for a in range(5):
        try:
            r = S.get(url, timeout=120, **kw)
        except (requests.Timeout, requests.ConnectionError):
            if a == 4: raise
            time.sleep(10 * (a + 1)); continue
        if r.status_code in (429, 500, 502, 503, 504): time.sleep(5 * (a + 1)); continue
        return r
    return r


def split_locked(df, col, out, name):
    d = pd.to_datetime(df[col])
    m = (d >= LOCKED[0]) & (d <= LOCKED[1])
    df[~m].to_parquet(f"{out}/{name}.parquet", compression="zstd")
    if m.any(): df[m].to_parquet(f"{out}/{name}_lockedblock.parquet", compression="zstd")
    print(name, len(df), "rows")


def finra(out, since, universe):
    keep = set(pd.read_csv(universe)["symbol"]) if universe and os.path.exists(universe) else None
    by_year: dict[int, list] = {}
    for d in pd.bdate_range(since, pd.Timestamp.today()):
        r = get(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt")
        if r.status_code != 200: continue  # holidays
        df = pd.read_csv(io.StringIO(r.text), sep="|", dtype={"Symbol": str})
        df = df[pd.to_numeric(df["Date"], errors="coerce").notna()]
        if keep is not None: df = df[df["Symbol"].isin(keep)]
        df["Date"] = pd.to_datetime(df["Date"].astype(int).astype(str))
        by_year.setdefault(d.year, []).append(df)
        time.sleep(0.2)
    for y, parts in by_year.items():
        df = pd.concat(parts).rename(columns=str.lower)
        for c in ("shortvolume", "shortexemptvolume", "totalvolume"): df[c] = df[c].astype("float32")
        split_locked(df, "date", out, f"finra_shvol_{y}")


def cboe(out, since):
    parts = []
    for ix in ("VIX", "VIX9D", "VIX3M", "VVIX"):
        r = get(f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{ix}_History.csv")
        if r.status_code != 200: print("cboe", ix, r.status_code); continue
        df = pd.read_csv(io.StringIO(r.text)); df.columns = [c.lower() for c in df.columns]
        df = df.rename(columns={ix.lower(): "close"}); df["index"] = ix
        df["date"] = pd.to_datetime(df["date"]); parts.append(df)
    split_locked(pd.concat(parts, ignore_index=True), "date", out, "cboe_vol_indices")


def _ff_zip(url):
    z = zipfile.ZipFile(io.BytesIO(get(url).content)); txt = z.read(z.namelist()[0]).decode("latin1").splitlines()
    i = next(k for k, l in enumerate(txt) if l.strip().startswith(",") or l.lower().startswith(",mkt"))  # header row
    rows = []
    for l in txt[i + 1:]:
        p = [x.strip() for x in l.split(",")]
        if len(p) < 2 or not p[0].isdigit() or len(p[0]) != 8: break  # first block = value-weighted daily returns
        rows.append(p)
    cols = ["date"] + [c.strip() for c in txt[i].split(",")[1:]]
    df = pd.DataFrame(rows, columns=cols); df["date"] = pd.to_datetime(df["date"])
    for c in cols[1:]: df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32") / 100
    return df


def ff(out, since):
    base = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    for name, f in [("ff_factors3_daily", "F-F_Research_Data_Factors_daily_CSV.zip"), ("ff_mom_daily", "F-F_Momentum_Factor_daily_CSV.zip"),
                    ("ff_ind12_daily", "12_Industry_Portfolios_daily_CSV.zip"), ("ff_ind48_daily", "48_Industry_Portfolios_daily_CSV.zip")]:
        try: split_locked(_ff_zip(base + f), "date", out, name)
        except Exception as e: print(name, "failed", e)


def fred(out, since):
    ids = ["DGS10", "DGS2", "T10Y2Y", "DFF", "BAMLH0A0HYM2", "DTWEXBGS"]
    df = None
    for i in ids:  # one series per request: the combined query timed out (2026-10-10)
        r = get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": i, "cosd": "2000-01-01"}); r.raise_for_status()
        x = pd.read_csv(io.StringIO(r.text)); x = x.rename(columns={x.columns[0]: "date"}); x["date"] = pd.to_datetime(x["date"])
        df = x if df is None else df.merge(x, on="date", how="outer")
    for c in ids: df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    split_locked(df, "date", out, "fred")


def earn(out, since):
    h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36",
         "Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
    rows = []
    for d in pd.bdate_range(since, pd.Timestamp.today() + pd.Timedelta(days=30)):
        r = get(f"https://api.nasdaq.com/api/calendar/earnings?date={d.date()}", headers=h)
        try: data = ((r.json() or {}).get("data") or {}).get("rows") or []
        except Exception: data = []
        for x in data:
            rows.append({"date": d, "symbol": (x.get("symbol") or "").upper(), "time": x.get("time"),
                         "eps_forecast": x.get("epsForecast"), "fiscal_q": x.get("fiscalQuarterEnding"), "mcap": x.get("marketCap")})
        time.sleep(0.5)
    split_locked(pd.DataFrame(rows), "date", out, "earnings_cal")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="public_data"); ap.add_argument("--since", default="2024-10-01")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--only", nargs="*", default=["cboe", "ff", "fred", "earn", "finra"])
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only:
        try:
            finra(a.out, a.since, a.universe) if k == "finra" else globals()[k](a.out, a.since)
        except Exception as e:
            print(k, "FAILED", type(e).__name__, e)
