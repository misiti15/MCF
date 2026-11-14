"""MOMSIDE-LIVE scorer (frozen with PLAN.md + Amendment 1: Builder's MOMSIDE definitions and score, on LIVE trades).
  python ../guild/research/momside-live/momside_live.py --selftest
  MOMSIDE_LAB_POSTED=1 python ../guild/research/momside-live/momside_live.py <journal dir>   (ONLY after Builder's lab result)
Educational only - not financial advice."""
import os, sys, glob, time, sqlite3, requests, numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent; CACHE = HERE / "data"
def excess_by_day(t, skip):
    """Builder's score: per setup-day delta = -sum(R skipped); control = (k/n) * total; excess summed per day."""
    t = t.assign(skip=skip); rows = []
    for (d, s), g in t.groupby(["date", "strategy"]):
        n, k = len(g), int(g.skip.sum())
        if k == 0: continue
        delta = -g.r[g.skip].sum(); ctl = k / n * g.r.sum(); rows.append(dict(date=d, strategy=s, ex=delta - ctl, k=k))
    return pd.DataFrame(rows)
def summarize(x, t, skip, label):
    if x.empty: print(f"  {label}: no skipped trades"); return
    day = x.groupby("date").ex.sum(); tt = day.mean() / (day.std(ddof=1) / np.sqrt(len(day))) if len(day) > 2 else np.nan
    per = x.groupby("strategy").agg(ex=("ex", "sum"), k=("k", "sum")); per = per[per.k >= 10]; per["pt"] = per.ex / per.k
    best = day.max() / day.sum() if day.sum() > 0 else np.nan
    print(f"  {label}: skipped {int(skip.sum())} of {len(t)} ({skip.mean():.1%}); excess total {day.sum():+.2f}R, per day {day.mean():+.3f}, "
          f"day-t {tt:+.2f}, days {len(day)}; kept avg {t.r[~skip].mean():+.3f} vs all {t.r.mean():+.3f}; best-day share {best:.0%}; "
          f"setups better {int((per.pt > 0).sum())} / worse {int((per.pt <= 0).sum())}")
    top = x.groupby("strategy").ex.sum().sort_values(ascending=False)
    print(f"    top-5 setups' share of the excess: {top.head(5).sum() / day.sum():.0%}" if day.sum() != 0 else "    top-5 share: n/a")
def selftest():
    rng = np.random.default_rng(3); rows = []
    for d in range(30):
        for s in range(15):
            for _ in range(10):
                dec = int(rng.integers(1, 11)); side = int(rng.choice([-1, 1]))
                counter = (side > 0 and dec <= 3) or (side < 0 and dec >= 8)
                rows.append(dict(date=d, strategy=s, side=side, dec=dec, r=rng.normal(0, 1) - (0.3 if counter else 0)))
    t = pd.DataFrame(rows); skip = ((t.side > 0) & (t.dec <= 3)) | ((t.side < 0) & (t.dec >= 8))
    x = excess_by_day(t, skip); day = x.groupby("date").ex.sum(); tt = day.mean() / (day.std(ddof=1) / np.sqrt(len(day)))
    t0 = t.assign(r=rng.normal(0, 1, len(t))); x0 = excess_by_day(t0, skip); d0 = x0.groupby("date").ex.sum(); t0t = d0.mean() / (d0.std(ddof=1) / np.sqrt(len(d0)))
    print(f"planted -0.30 on counter: day-t {tt:+.2f}; null day-t {t0t:+.2f}"); assert tt > 3 and abs(t0t) < 3; print("selftest ok")
def closes(syms):
    CACHE.mkdir(exist_ok=True); f = CACHE / "daily.parquet"
    if f.exists(): return pd.read_parquet(f)
    H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}; out = []
    for i in range(0, len(syms), 100):
        p = {"symbols": ",".join(syms[i:i + 100]), "timeframe": "1Day", "start": "2024-09-01", "end": "2026-11-14", "feed": "sip", "adjustment": "split", "limit": 10000}
        while True:
            r = requests.get("https://data.alpaca.markets/v2/stocks/bars", headers=H, params=p, timeout=60)
            if r.status_code == 429: time.sleep(3); continue
            r.raise_for_status(); j = r.json()
            for s, bs in (j.get("bars") or {}).items(): out += [(s, b["t"][:10], b["c"]) for b in bs]
            if not j.get("next_page_token"): break
            p["page_token"] = j["next_page_token"]
        time.sleep(0.3)
    d = pd.DataFrame(out, columns=["symbol", "date", "c"]); d.to_parquet(f); return d
def mom_deciles(px, dates, lag_far):
    w = px.pivot_table(index="date", columns="symbol", values="c").sort_index(); idx = list(w.index); out = {}
    for D in dates:
        k = np.searchsorted(idx, D)            # sessions strictly before D: idx[k-1] = prior close
        if k - lag_far < 0: continue
        m = w.iloc[k - 21] / w.iloc[k - lag_far] - 1
        out[D] = np.ceil(m.dropna().rank(method="first", pct=True) * 10).clip(1, 10)
    return out
if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    cov = "--coverage" in sys.argv
    if not cov and os.environ.get("MOMSIDE_LAB_POSTED") != "1": sys.exit("gated: set MOMSIDE_LAB_POSTED=1 only after Builder's MOMSIDE lab result is on the board")
    F = []
    for f in sorted(glob.glob(f"{sys.argv[1]}/*.db")):
        F.append(pd.read_sql(f"select date, strategy, symbol, side, entry_time, exit_time{', r_multiple r' if not cov else ''} from trades where run_id=1 and exit_time "
                             "is not null and date between '2026-10-06' and '2026-11-13'", sqlite3.connect(f)))
    t = pd.concat(F, ignore_index=True); lab = sorted(set(Path("research/lab_symbols.txt").read_text().split()) | {"SPY"})
    px = closes(lab); dates = sorted(t.date.unique())
    print(f"live trades {len(t)}; names traded not in lab list: {(~t.symbol.isin(lab)).mean():.1%}")
    scope = next((a.split("=")[1] for a in sys.argv[2:] if a.startswith("--scope=")), "all")
    tod = pd.to_datetime(t.entry_time, utc=True).dt.tz_convert("America/New_York")
    t["pm"] = (tod.dt.hour * 100 + tod.dt.minute) >= 1200
    print(f"primary scope: {scope} (pm = entries >= 12:00; Builder's posted scope decides)")
    if cov:
        for lab_c, far in [("12-1", 252), ("6-1 (C4)", 126)]:
            dec = mom_deciles(px, dates, far); d = pd.Series([dec.get(a, pd.Series(dtype=float)).get(b, np.nan) for a, b in zip(t.date, t.symbol)])
            c1 = ((t.side > 0) & (d <= 3)) | ((t.side < 0) & (d >= 8)); c2 = ((t.side > 0) & (d <= 2)) | ((t.side < 0) & (d >= 9)); c3 = (t.side > 0) & (d <= 3)
            sd = t.assign(c1=c1.values).groupby(["date", "strategy"]).c1.any()
            print(f"{lab_c}: tagged {d.notna().mean():.1%}; skipped C1 {int(c1.sum())} C2 {int(c2.sum())} C3 {int(c3.sum())}; "
                  f"setup-days with a C1 skip {int(sd.sum())} of {len(sd)}; days {t.date.nunique()} (R never loaded)")
        sys.exit()
    for lab_c, far in [("12-1", 252), ("6-1 (C4)", 126)]:
        dec = mom_deciles(px, dates, far); t["dec"] = [dec.get(d, pd.Series(dtype=float)).get(s, np.nan) for d, s in zip(t.date, t.symbol)]
        print(f"{lab_c}: tagged {t.dec.notna().mean():.1%}")
        for sc in (["pm", "all"] if scope == "pm" else ["all", "pm"]):
            tt = t.dropna(subset=["dec"]); tt = tt[tt.pm] if sc == "pm" else tt
            print(f" scope {sc}{' (PRIMARY)' if sc == scope else ' (descriptive)'}: {len(tt)} tagged trades")
            for name, sk in [("C1", ((tt.side > 0) & (tt.dec <= 3)) | ((tt.side < 0) & (tt.dec >= 8))),
                             ("C2", ((tt.side > 0) & (tt.dec <= 2)) | ((tt.side < 0) & (tt.dec >= 9))),
                             ("C3", (tt.side > 0) & (tt.dec <= 3))]:
                if lab_c.startswith("6-1") and name != "C1": continue
                summarize(excess_by_day(tt, sk.values), tt, sk.values, f"{lab_c} {sc} {name} raw R")
    print("ex-market and LR8 net columns: added in the run commit per Amendment 1. Educational only - not financial advice.")
