"""Fetch per-event earnings surprise data and quarterly revenue for the lab universe (run on GitHub Actions; see
.github/workflows/earnings-data.yml - the Claude container's proxy blocks Yahoo and SEC).

Sources
  yf   Yahoo Finance earnings calendar via yfinance==1.7.0 `Ticker.get_earnings_dates(limit=40)` (scrapes
       finance.yahoo.com/calendar/earnings?symbol=X&size=50; one request per symbol, ~10 years of quarters).
       Per event: report datetime (America/New_York, hour -> bmo / amc / dmh / unknown), EPS estimate (consensus at
       the time, as Yahoo shows it), reported EPS (Yahoo's figure, usually the adjusted / non-GAAP EPS the consensus
       is on), surprise %. -> earnings_yf.parquet
  sec  SEC EDGAR XBRL companyfacts (data.sec.gov/api/xbrl/companyfacts/CIK##########.json), one request per company,
       <= 8 req/s (SEC limit 10/s), User-Agent from env SEC_UA (must carry a contact e-mail).
       Raw revenue + diluted/basic EPS facts (USD, as first filed: earliest `filed` per concept/period, so no later
       restatements leak back) -> sec_facts.parquet
       Derived per fiscal quarter (Q4 = FY - Q1 - Q2 - Q3 when only the 10-K has it): revenue, YoY / QoQ growth and a
       naive revenue "beat" proxy -> sec_revenue_q.parquet.
       THERE IS NO FREE CONSENSUS REVENUE. rev_beat_proxy = YoY growth this quarter minus YoY growth last quarter
       (did growth accelerate?), and rev_vs_naive = revenue / (same quarter last year x (1 + last quarter's YoY)) - 1.
       Neither is a consensus surprise. `filed` is the 10-Q/10-K date, usually days to weeks AFTER the earnings
       release (the press release, 8-K ex. 99.1, carries the same revenue on the report day); users match the event to
       the fiscal quarter by period end, not by `filed`.

Robustness: retries with backoff on 429/5xx/timeouts; a circuit breaker per source (CB_FAILS consecutive failures ->
one long pause, then the source is abandoned and whatever was fetched is published); checkpoints every 100 symbols;
a status JSON lists done / failed / missing symbols. With --prev DIR (the previous files from the research-data
branch), rows of symbols not refetched successfully this run are carried over, so a partial run never loses data.

Rule-19 locked block (2024-11-01..2025-02-28): rows whose event date (yf) / filed date (sec) falls in it are written to
separate *_lockedblock.parquet files for the lead only.

Usage: python fetch_earnings.py --out earnings_data [--only yf sec] [--symbols AAPL MSFT] [--max-symbols N]
                                [--prev prev_dir] [--sleep-yf 1.5]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
LOCKED = ("2024-11-01", "2025-02-28")
CB_FAILS = 25            # consecutive failures before the breaker trips
CB_PAUSE = 300           # seconds to wait once before giving up on a source
REV_CONCEPTS = [         # first available per period wins, in this order
    "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueGoodsNet", "SalesRevenueServicesNet",
    "RevenuesNetOfInterestExpense", "InterestAndDividendIncomeOperating", "TotalRevenuesAndOtherIncome",
]
EPS_CONCEPTS = ["EarningsPerShareDiluted", "EarningsPerShareBasic"]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def universe(args) -> list[str]:
    if args.symbols:
        return [s.upper() for s in args.symbols]
    syms = [l.strip().upper() for l in (ROOT / "research" / "lab_symbols.txt").read_text().splitlines() if l.strip()]
    meta = ROOT / "research" / "swarm1010" / "w3_daily" / "assets_meta.csv"
    if meta.exists():
        m = pd.read_csv(meta)
        etf = set(m.loc[m["is_etf"].astype(str).str.lower() == "true", "symbol"].str.upper())
        syms = [s for s in syms if s not in etf]
    return syms[: args.max_symbols] if args.max_symbols else syms


class Breaker:
    def __init__(self, name):
        self.name, self.fails, self.paused, self.open = name, 0, False, False

    def ok(self):
        self.fails = 0

    def fail(self):
        self.fails += 1
        if self.fails >= CB_FAILS:
            if not self.paused:
                log(f"{self.name}: {self.fails} consecutive failures, pausing {CB_PAUSE}s")
                time.sleep(CB_PAUSE)
                self.paused, self.fails = True, 0
            else:
                log(f"{self.name}: breaker open, abandoning source (partial publish)")
                self.open = True


def split_locked(df: pd.DataFrame, col: str, out: Path, name: str):
    if df is None or df.empty:
        log(name, "empty, not written")
        return
    d = pd.to_datetime(df[col], errors="coerce")
    m = (d >= LOCKED[0]) & (d <= pd.Timestamp(LOCKED[1]) + pd.Timedelta(hours=23, minutes=59))
    df[~m].to_parquet(out / f"{name}.parquet", compression="zstd", index=False)
    if m.any():
        df[m].to_parquet(out / f"{name}_lockedblock.parquet", compression="zstd", index=False)
    log(name, len(df), "rows,", int(m.sum()), "in locked block (separate file)")


def carry_over(new: pd.DataFrame, prev_dir: str | None, name: str, done: set[str]) -> pd.DataFrame:
    """Add previous rows (normal + locked file) of symbols not fetched successfully in this run."""
    if not prev_dir:
        return new
    parts = [new]
    for suffix in ("", "_lockedblock"):
        p = Path(prev_dir) / f"{name}{suffix}.parquet"
        if p.exists():
            old = pd.read_parquet(p)
            old = old[~old["symbol"].isin(done)]
            log(f"carry over {len(old)} rows of {old['symbol'].nunique()} symbols from {p.name}")
            parts.append(old)
    parts = [p for p in parts if p is not None and not p.empty]
    return pd.concat(parts, ignore_index=True) if parts else new


# ------------------------------------------------------------------------------------------------- Yahoo
def _session_class(hour: float) -> str:
    if pd.isna(hour):
        return "unknown"
    if hour == 0:
        return "unknown"            # Yahoo shows 12 AM when it has no time
    if hour < 9.5:
        return "bmo"
    if hour >= 16:
        return "amc"
    return "dmh"


def yf_one(tk, sym: str) -> pd.DataFrame | None:
    df = tk.get_earnings_dates(limit=40)
    if df is None or df.empty:
        return None
    df = df.reset_index()
    cols = {c: str(c).strip().lower().replace(" ", "_").replace("(%)", "_pct").replace("%", "pct") for c in df.columns}
    df = df.rename(columns=cols)
    dcol = next(c for c in df.columns if "date" in c)
    ts = pd.to_datetime(df[dcol], utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame({
        "symbol": sym,
        "report_dt_et": ts.dt.tz_localize(None),
        "date": ts.dt.tz_localize(None).dt.normalize(),
        "hour_et": (ts.dt.hour + ts.dt.minute / 60).astype("float32"),
    })
    out["session"] = out["hour_et"].map(_session_class)

    def num(*keys):
        for k in df.columns:
            if all(x in k for x in keys):
                return pd.to_numeric(df[k], errors="coerce").astype("float32")
        return pd.Series(float("nan"), index=df.index, dtype="float32")

    out["eps_estimate"] = num("eps", "estimate")
    out["eps_reported"] = num("reported")
    out["surprise_pct"] = num("surprise")
    for c in df.columns:                     # keep any extra columns Yahoo adds (e.g. event type) as text
        if c not in (dcol,) and not any(k in c for k in ("estimate", "reported", "surprise")):
            out["yf_" + c] = df[c].astype(str)
    return out


def fetch_yf(syms, out: Path, args, status):
    import yfinance as yf
    log("yfinance", yf.__version__)
    br = Breaker("yf")
    rows, done, failed = [], [], []
    for i, s in enumerate(syms):
        if br.open:
            break
        res = None
        for a in range(3):
            try:
                res = yf_one(yf.Ticker(s.replace(".", "-")), s)
                break
            except Exception as e:  # noqa: BLE001
                msg = f"{type(e).__name__}: {e}"[:200]
                if "rate" in msg.lower() or "429" in msg:
                    time.sleep(30 * (a + 1))
                else:
                    time.sleep(3 * (a + 1))
        else:
            log("yf fail", s, msg)
        if res is None:
            failed.append(s); br.fail()
        else:
            rows.append(res); done.append(s); br.ok()
        if (i + 1) % 100 == 0:
            log(f"yf {i + 1}/{len(syms)} ok {len(done)} failed {len(failed)}")
            _write_yf(rows, out, args, set(done))          # checkpoint
        time.sleep(args.sleep_yf)
    _write_yf(rows, out, args, set(done))
    status["yf"] = {"done": len(done), "failed": failed, "not_attempted": syms[len(done) + len(failed):],
                    "breaker_open": br.open}


def _write_yf(rows, out, args, done):
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["symbol", "date"])
    df = carry_over(df, args.prev, "earnings_yf", done)
    if not df.empty:
        df = df.drop_duplicates(["symbol", "report_dt_et"]).sort_values(["symbol", "date"])
        split_locked(df, "date", out, "earnings_yf")


# ------------------------------------------------------------------------------------------------- SEC
class SecClient:
    def __init__(self):
        import requests
        ua = os.environ.get("SEC_UA", "").strip()
        if "@" not in ua:
            log("WARNING: SEC_UA has no contact e-mail; SEC may answer 403")
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": ua or "MCF research", "Accept-Encoding": "gzip, deflate"})
        self.last = 0.0

    def get(self, url):
        import requests
        for a in range(5):
            wait = 0.125 - (time.time() - self.last)           # <= 8 req/s, SEC allows 10
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            try:
                r = self.s.get(url, timeout=60)
            except (requests.Timeout, requests.ConnectionError):
                time.sleep(5 * (a + 1)); continue
            if r.status_code == 404:
                return None
            if r.status_code in (403, 429, 500, 502, 503, 504):
                time.sleep(10 * (a + 1) if r.status_code != 403 else 60); continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"SEC gave up on {url}")


def sec_one(cli, sym, cik) -> pd.DataFrame | None:
    js = cli.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json")
    if js is None:
        return None
    rows = []
    for tax in ("us-gaap", "ifrs-full"):
        facts = (js.get("facts") or {}).get(tax) or {}
        for concept in REV_CONCEPTS + EPS_CONCEPTS + ["Revenue"]:
            f = facts.get(concept)
            if not f:
                continue
            for unit, lst in (f.get("units") or {}).items():
                if not (unit == "USD" or unit.startswith("USD/")):
                    continue
                for x in lst:
                    if x.get("form") not in ("10-Q", "10-K", "10-Q/A", "10-K/A", "20-F", "40-F", "6-K"):
                        continue
                    rows.append({"symbol": sym, "cik": int(cik), "taxonomy": tax, "concept": concept, "unit": unit,
                                 "start": x.get("start"), "end": x.get("end"), "val": x.get("val"), "fy": x.get("fy"),
                                 "fp": x.get("fp"), "form": x.get("form"), "filed": x.get("filed"),
                                 "accn": x.get("accn"), "frame": x.get("frame")})
    if not rows:
        return pd.DataFrame(columns=["symbol"])
    df = pd.DataFrame(rows)
    for c in ("start", "end", "filed"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["val"] = pd.to_numeric(df["val"], errors="coerce")
    df["days"] = (df["end"] - df["start"]).dt.days
    # as first filed: earliest filing per concept / period (later comparatives and restatements dropped)
    df = df.sort_values("filed").drop_duplicates(["concept", "unit", "start", "end"], keep="first")
    return df


def derive_quarters(facts: pd.DataFrame) -> pd.DataFrame:
    """One revenue value per (symbol, fiscal quarter end). Quarterly facts = 75..105 days; Q4 = FY - (Q1+Q2+Q3)."""
    out = []
    rev = facts[facts["concept"].isin(REV_CONCEPTS + ["Revenue"]) & (facts["unit"] == "USD")]
    for sym, g in rev.groupby("symbol"):
        g = g.copy()
        g["prio"] = g["concept"].map({c: i for i, c in enumerate(REV_CONCEPTS + ["Revenue"])})
        q = g[g["days"].between(75, 105)].sort_values(["prio", "filed"]).drop_duplicates("end")
        q = q[["end", "start", "val", "filed", "concept", "form"]].assign(derived_q4=False)
        fy = g[g["days"].between(350, 380)].sort_values(["prio", "filed"]).drop_duplicates("end")
        add = []
        for _, y in fy.iterrows():
            if (q["end"] - y["end"]).abs().min() <= pd.Timedelta(days=10) if len(q) else False:
                continue
            inside = q[(q["start"] >= y["start"] - pd.Timedelta(days=10)) & (q["end"] <= y["end"] - pd.Timedelta(days=60))]
            if len(inside) == 3:
                add.append({"end": y["end"], "start": inside["end"].max() + pd.Timedelta(days=1),
                            "val": y["val"] - inside["val"].sum(), "filed": y["filed"], "concept": y["concept"],
                            "form": y["form"], "derived_q4": True})
        if add:
            q = pd.concat([q, pd.DataFrame(add)], ignore_index=True)
        q = q.sort_values("end").reset_index(drop=True)
        q["symbol"] = sym
        out.append(q)
    if not out:
        return pd.DataFrame()
    q = pd.concat(out, ignore_index=True).rename(columns={"end": "period_end", "start": "period_start", "val": "revenue"})

    def lag(g, months):
        tgt = g["period_end"] - pd.DateOffset(months=months)
        idx = pd.Index(g["period_end"])
        res = []
        for t in tgt:
            k = idx.get_indexer([t], method="nearest")[0]
            res.append(g["revenue"].iloc[k] if k >= 0 and abs((idx[k] - t).days) <= 20 else float("nan"))
        return pd.Series(res, index=g.index)

    parts = []
    for sym, g in q.groupby("symbol"):
        g = g.copy()
        g["rev_yoy"] = g["revenue"] / lag(g, 12) - 1
        g["rev_qoq"] = g["revenue"] / lag(g, 3) - 1
        g["rev_yoy_prev"] = g["rev_yoy"].shift(1)
        g["rev_beat_proxy"] = g["rev_yoy"] - g["rev_yoy_prev"]               # growth acceleration, NOT a surprise
        g["rev_vs_naive"] = g["revenue"] / (lag(g, 12) * (1 + g["rev_yoy_prev"])) - 1
        parts.append(g)
    q = pd.concat(parts, ignore_index=True)
    for c in ("revenue", "rev_yoy", "rev_qoq", "rev_yoy_prev", "rev_beat_proxy", "rev_vs_naive"):
        q[c] = q[c].astype("float64")
    return q


def fetch_sec(syms, out: Path, args, status):
    cli = SecClient()
    tick = cli.get("https://www.sec.gov/files/company_tickers.json") or {}
    cikmap = {v["ticker"].upper(): v["cik_str"] for v in tick.values()}
    br = Breaker("sec")
    parts, done, failed, nocik = [], [], [], []
    for i, s in enumerate(syms):
        if br.open:
            break
        cik = cikmap.get(s) or cikmap.get(s.replace(".", "-"))
        if cik is None:
            nocik.append(s); continue
        try:
            df = sec_one(cli, s, cik)
            if df is not None:
                parts.append(df)
            done.append(s); br.ok()
        except Exception as e:  # noqa: BLE001
            log("sec fail", s, type(e).__name__, str(e)[:150]); failed.append(s); br.fail()
        if (i + 1) % 100 == 0:
            log(f"sec {i + 1}/{len(syms)} ok {len(done)} failed {len(failed)} no-cik {len(nocik)}")
            _write_sec(parts, out, args, set(done))
    _write_sec(parts, out, args, set(done))
    status["sec"] = {"done": len(done), "failed": failed, "no_cik": nocik, "breaker_open": br.open}


def _write_sec(parts, out, args, done):
    parts = [p for p in parts if not p.empty]
    facts = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["symbol", "filed"])
    facts = carry_over(facts, args.prev, "sec_facts", done)
    if facts.empty:
        return
    split_locked(facts, "filed", out, "sec_facts")
    q = derive_quarters(facts)          # derived from ALL facts (incl. locked) so YoY is right; split by filed
    split_locked(q, "filed", out, "sec_revenue_q")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="earnings_data")
    ap.add_argument("--only", nargs="*", default=["yf", "sec"])
    ap.add_argument("--symbols", nargs="*")
    ap.add_argument("--max-symbols", type=int, default=0)
    ap.add_argument("--prev", default=None, help="dir with the previous research-data files (carry-over)")
    ap.add_argument("--sleep-yf", type=float, default=1.5)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    syms = universe(args)
    log("symbols", len(syms))
    status = {"started_utc": pd.Timestamp.utcnow().isoformat(), "symbols": len(syms), "only": args.only}
    for k in args.only:
        try:
            {"yf": fetch_yf, "sec": fetch_sec}[k](syms, out, args, status)
        except Exception as e:  # noqa: BLE001 - one source failing must not stop the other
            log(k, "FAILED", type(e).__name__, e)
            status[k] = {"error": f"{type(e).__name__}: {e}"[:500]}
    status["finished_utc"] = pd.Timestamp.utcnow().isoformat()
    (out / "earnings_fetch_status.json").write_text(json.dumps(status, indent=1, default=str))
    ok = any(p.suffix == ".parquet" for p in out.iterdir())
    log("done; parquet written:", ok)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
