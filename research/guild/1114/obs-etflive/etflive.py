"""OBS-ETFLIVE (Observer 2026-11-14, Lead lead-20261114-0100-4): our live trades in leveraged / index ETFs vs the up-day null.
Live journals run 1, all 10 accounts, all dates. For each trade: market exposure (+1 = profits if the index rises: long a
bull ETF or short a bear ETF), underlying (SPY / QQQ / IWM; SOXL/SOXS use QQQ as proxy, UDOW/SDOW use SPY), the underlying's
sign so far at entry (vs prior close), the underlying's move entry->exit in the exposure direction (bps; the 'index alone'
null for that hold), R, and entry spread as a share of stop distance (meta JSON prefix, checklist 33). Descriptive, 0 configs.
Educational only - not financial advice. usage (MCF checkout): python ../guild/research/obs-etflive/etflive.py <journal dir>"""
import sqlite3, sys, json, glob, importlib.util, pandas as pd, numpy as np
from pathlib import Path
spec = importlib.util.spec_from_file_location("un", str(Path(__file__).parents[1] / "obs-upday-null" / "upnull.py"))
BULL = {"SPXL": "SPY", "UPRO": "SPY", "SSO": "SPY", "SPY": "SPY", "UDOW": "SPY", "TQQQ": "QQQ", "QLD": "QQQ", "QQQ": "QQQ",
        "SOXL": "QQQ", "TNA": "IWM", "IWM": "IWM"}
BEAR = {"SPXS": "SPY", "SPXU": "SPY", "SDOW": "SPY", "SQQQ": "QQQ", "SOXS": "QQQ", "TZA": "IWM"}
F = []
for f in sorted(glob.glob(f"{sys.argv[1]}/*.db")):
    t = pd.read_sql("select date, strategy, symbol, side, entry, stop, exit, entry_time, exit_time, r_multiple r, meta from trades "
                    "where run_id=1 and exit_time is not null", sqlite3.connect(f))
    t["acct"] = Path(f).stem.replace("mcf-data-", "").replace("mcf-data", "primary"); F.append(t)
t = pd.concat(F, ignore_index=True); t = t[t.symbol.isin(BULL.keys() | BEAR.keys())].copy()
t["und"] = t.symbol.map({**BULL, **BEAR}); t["expo"] = np.where(t.symbol.isin(BULL), 1, -1) * t.side
def sp(m):
    try: return json.loads(str(m).split(";")[0]).get("spread_bps")
    except Exception: return np.nan
t["sor"] = t.meta.map(sp).astype(float) / ((t.entry - t.stop).abs() / t.entry * 1e4)
# underlying minute closes (SPY/QQQ from the up-day null cache; IWM fetched the same way)
import types; un = types.ModuleType("un"); un.__dict__["__file__"] = spec.origin; src = Path(spec.origin).read_text().split("T = [")[0]; exec(src, un.__dict__)
px = {}
for u in ["SPY", "QQQ", "IWM"]:
    d = un.bars(u); d = d.set_index("t").sort_index(); px[u] = d
def at(u, ts):
    d = px[u]; i = d.index.searchsorted(ts, side="right") - 1; return d.c.iloc[i] if i >= 0 else np.nan
def prior_close(u, day):
    d = px[u]; x = d[(d.index.date < day) & (d.index.time < pd.Timestamp("16:00").time())]; return x.c.iloc[-1]
rows = []
for _, r in t.iterrows():
    e = pd.Timestamp(r.entry_time).tz_convert("America/New_York"); x = pd.Timestamp(r.exit_time).tz_convert("America/New_York")
    u = r.und; pe, pxx, pc = at(u, e), at(u, x), prior_close(u, e.date())
    rows.append(dict(sofar=np.sign(pe / pc - 1), idx_bps=r.expo * (pxx / pe - 1) * 1e4, hour=e.hour))
t = pd.concat([t.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
t["with_state"] = (t.expo == t.sofar)
assert t.r.notna().all()
def summ(g):
    d = g.groupby("date").r.sum(); best = d.max() if len(d) else 0
    return pd.Series(dict(n=len(g), days=g.date.nunique(), R=g.r.sum(), avgR=g.r.mean(), avgR_wo_best=(g.r.sum() - best) / max(1, len(g) - (g.date == d.idxmax()).sum()) if len(d) > 1 else np.nan,
                          best_share=best / g.r.sum() if g.r.sum() > 0 else np.nan, idx_bps=g.idx_bps.mean(), win_idx=(g.idx_bps > 0).mean(), sor_med=g.sor.median()))
pd.set_option("display.width", 200)
print(f"ETF trades {len(t)} on {t.date.nunique()} sessions ({t.date.min()}..{t.date.max()}), {t.strategy.nunique()} setups, accounts {sorted(t.acct.unique())}")
print("\nby market exposure (+1 bullish, -1 bearish) and whether entry went WITH the index's sign so far:")
print(t.groupby(["expo", "with_state"]).apply(summ).round(3).to_string())
print("\ndedicated index-ETF setups (LD*, NM-ETF*, intraday_momentum):")
ded = t[t.strategy.str.match(r"^(LD\d|NM-ETF|intraday_momentum)")]
print(ded.groupby("strategy").apply(summ).round(3).to_string())
print("\nall ETF trades by entry hour:"); print(t.groupby("hour").apply(summ)[["n", "avgR", "idx_bps", "win_idx"]].round(3).to_string())
print(f"\ncorr(trade R, index move over the hold in exposure direction) = {t.r.corr(t.idx_bps):.2f}; median spread/stop {t.sor.median():.3f} "
      f"(non-ETF live median ~0.08 for comparison, OBS-STOPSLIP)")
