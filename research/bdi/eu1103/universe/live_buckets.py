"""eu1103/universe step 1: LIVE paper trades (run_id 1, all 5 accounts, 2026-10-06..11-02) by universe attribute.
R = pnl_adj / $ risk (|entry - stop| x shares), costs in (journal pnl_adj). Symbol attributes come from the live
universe snapshot used that morning (origin/mcf-data universe.csv history; 10-06 uses data/universe.csv of 10-05):
ADV, ATR%, ETB, tier. Price = entry price. Spread = journal entry quote (meta spread_bps). Kind = stock / ETF-fund /
leveraged-or-inverse ETF (name rules below). Sector = the sector SPDR with the highest daily-return correlation
2025-03..2026-09 (daily.parquet from fetch_daily.py; residual of SPY removed first). Move-history = how often the name
was a top-50 |open->close| / ATR mover of the day among ADV >= $50M names, 2025-03-03..2026-10-05 (before the live window).
"exc" = trade R minus its setup-account mean R (so a bucket is not just a different setup mix).
Usage: python live_buckets.py <scratch> -> live_trades.parquet in scratch, live_buckets_out.txt here.
Educational only - not financial advice."""
import glob
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
ACC = [("mcf-data", "p"), ("mcf-data-testing", "t1"), ("mcf-data-testing2", "t2"), ("mcf-data-graveyard", "gy"), ("mcf-data-gen", "gen")]
FUND = re.compile(r"ETF|ETN|Fund|Trust,? Series|SPDR|iShares|ProShares|Direxion|GraniteShares|Leverage Shares|Tradr|Defiance|T-Rex|"
                  r"Roundhill|YieldMax|MicroSectors|iPath|Invesco|Vanguard|Schwab|WisdomTree|Global X|VanEck|ARK |Amplify|First Trust|"
                  r"Grayscale|Bitwise|21Shares|CoinShares|United States (?:Oil|Natural|Gasoline|12)|Teucrium|Sprott Physical|Select Sector", re.I)
LEV = re.compile(r"\b\d(?:\.\d+)?x\b|ultra|\bbull\b|\bbear\b|inverse|leveraged|\bdaily\b|-1x", re.I)
SPDR = "XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC".split()


def kind(name):
    name = str(name)
    if FUND.search(name):
        return "lev/inv ETF" if LEV.search(name) else "ETF/fund"
    return "stock"


def trades():
    out = []
    for b, a in ACC:
        c = sqlite3.connect(S / f"{b}.db")
        t = pd.read_sql("select symbol,strategy,side,date,entry_time,entry,stop,shares,pnl_adj,exit_reason,meta from trades "
                        "where run_id=1 and date>='2026-10-06' and date<='2026-11-02'", c)
        t["acct"] = a
        out.append(t)
    t = pd.concat(out, ignore_index=True)
    t["risk"] = (t.entry - t.stop).abs() * t.shares
    t = t[(t.risk > 0) & t.pnl_adj.notna()].copy()
    t["R"] = t.pnl_adj / t.risk
    t["spread_bps"] = t.meta.str.extract(r'"spread_bps": ([0-9.]+)')[0].astype(float)
    t["hhmm"] = pd.to_datetime(t.entry_time.str[11:16], format="%H:%M").dt.strftime("%H%M").astype(int)
    return t.drop(columns=["meta"])


def snapshots():
    snaps = {"2026-10-05": pd.read_csv("/home/user/MCF/data/universe.csv")}
    for p in sorted(glob.glob(str(S / "uni" / "*.csv"))):
        snaps[Path(p).stem] = pd.read_csv(p)
    return snaps


def attach(t, snaps):
    keys = sorted(snaps)
    rows = []
    for d, g in t.groupby("date"):
        k = max(x for x in keys if x <= d)
        u = snaps[k][["symbol", "name", "adv", "atr_pct", "easy_to_borrow", "shortable", "tier"]].drop_duplicates("symbol")
        rows.append(g.merge(u, on="symbol", how="left").assign(snap=k))
    t = pd.concat(rows, ignore_index=True)
    # symbols missing from that morning's snapshot: fall back to the nearest snapshot that has them
    allu = pd.concat([v.assign(snap=k) for k, v in snaps.items()]).drop_duplicates("symbol", keep="last").set_index("symbol")
    for c in ("name", "adv", "atr_pct", "easy_to_borrow", "shortable", "tier"):
        miss = t[c].isna()
        t.loc[miss, c] = t.loc[miss, "symbol"].map(allu[c])
    t["kind"] = t["name"].map(kind)
    return t


def sector_and_moves():
    d = pd.read_parquet(S / "daily.parquet")
    d = d.sort_values(["symbol", "date"])
    d["ret"] = d.groupby("symbol").close.pct_change()
    hist = d[(d.date >= "2025-03-03") & (d.date <= "2026-09-30")]
    R = hist.pivot(index="date", columns="symbol", values="ret")
    spy = R["SPY"]
    beta = R.apply(lambda s: s.cov(spy) / spy.var())
    res = R - np.outer(spy.fillna(0), beta.fillna(0))
    sec = res[SPDR]
    ok = R.notna().sum() >= 120
    corr = pd.DataFrame({e: res.loc[:, ok].corrwith(sec[e]) for e in SPDR})
    best = corr.idxmax(axis=1)
    best[corr.max(axis=1) < 0.15] = "none"
    # move history: top-50 |open->close| / ATR(14) daily movers among ADV >= $50M names
    d["tr"] = np.maximum(d.high - d.low, np.maximum((d.high - d.groupby("symbol").close.shift()).abs(),
                                                    (d.low - d.groupby("symbol").close.shift()).abs()))
    d["atr"] = d.groupby("symbol").tr.transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    d["adv"] = (d.close * d.volume).groupby(d.symbol).transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    d["mv"] = (d.close - d.open).abs() / d.atr
    h = d[(d.date >= "2025-03-03") & (d.date <= "2026-10-05") & (d.adv >= 50e6) & d.mv.notna()].copy()
    h["rk"] = h.groupby("date").mv.rank(ascending=False)
    elig = h.groupby("symbol").size()
    top = h[h.rk <= 50].groupby("symbol").size()
    mh = pd.DataFrame({"days_elig": elig, "top50": top}).fillna(0)
    mh["top50_rate"] = mh.top50 / mh.days_elig
    return best.rename("sector"), mh, d


def bucket_table(t, col, order=None):
    g = t.groupby(col, observed=True)
    rows = []
    for k, x in g:
        if not len(x):
            continue
        ds = x.groupby("date").R.agg(["sum", "size"])
        mu = x.R.mean()
        se = np.sqrt(((ds["sum"] - ds["size"] * mu) ** 2).sum()) / len(x) if len(ds) > 1 else np.nan
        de = x.groupby("date").exc.agg(["sum", "size"])
        me = x.exc.mean()
        see = np.sqrt(((de["sum"] - de["size"] * me) ** 2).sum()) / len(x) if len(de) > 1 else np.nan
        bd = ds["sum"].idxmax()
        rows.append(dict(bucket=str(k), n=len(x), days=len(ds), avgR=round(mu, 3), se=round(se, 3), t=round(mu / se, 2) if se > 0 else np.nan,
                         totR=round(x.R.sum(), 1), exc=round(me, 3), exc_t=round(me / see, 2) if see > 0 else np.nan,
                         wo_best=round((ds["sum"].sum() - ds.loc[bd, "sum"]) / max(1, len(x) - ds.loc[bd, "size"]), 3),
                         win=round((x.R > 0).mean(), 3), spread=round(x.spread_bps.median(), 1)))
    return pd.DataFrame(rows)


def main():
    t = attach(trades(), snapshots())
    sec, mh, _ = sector_and_moves()
    t["sector"] = t.symbol.map(sec).fillna("n/a")
    t.loc[t.kind != "stock", "sector"] = "fund"
    t = t.join(mh[["top50_rate"]], on="symbol")
    mv = pd.read_csv("/home/user/MCF/research/bdi/moves/moves.csv")
    mvc = mv.groupby("symbol").size()
    t["mh_list"] = t.symbol.map(mvc).fillna(0)
    t["key"] = t.acct + "|" + t.strategy
    t["exc"] = t.R - t.groupby("key").R.transform("mean")
    t["adv_b"] = pd.cut(t.adv, [0, 20e6, 50e6, 95e6, 150e6, 300e6, 1e9, 1e14], labels=["<20M", "20-50M", "50-95M", "95-150M", "150-300M", "300M-1B", ">1B"])
    t["px_b"] = pd.cut(t.entry, [0, 10, 20, 50, 100, 250, 1e9], labels=["<10", "10-20", "20-50", "50-100", "100-250", ">250"])
    t["atr_b"] = pd.cut(t.atr_pct, [0, 2, 3, 4, 6, 10, 1e3], labels=["<2%", "2-3%", "3-4%", "4-6%", "6-10%", ">10%"])
    t["spr_b"] = pd.cut(t.spread_bps, [-1, 3, 6, 10, 20, 1e4], labels=["<=3bp", "3-6", "6-10", "10-20", ">20"])
    t["mh_b"] = pd.cut(t.top50_rate, [-1, 0.0, 0.02, 0.05, 0.10, 1.1], labels=["never", "<2%", "2-5%", "5-10%", ">=10%"])
    t["etb"] = np.where(t.easy_to_borrow.astype(str) == "True", "ETB", "not ETB")
    t["sidel"] = np.where(t.side > 0, "long", "short")
    t["advxatr"] = t.adv * t.atr_pct
    t.to_parquet(S / "live_trades.parquet", index=False)
    lines = [f"Educational only - not financial advice. LIVE paper trades run_id 1, 5 accounts, {t.date.min()}..{t.date.max()}: "
             f"{len(t)} trades, {t.date.nunique()} sessions, {t.symbol.nunique()} symbols. avg R after costs; se/t day-clustered; "
             "exc = R minus setup-account mean (setup mix removed); wo_best = avg R without the bucket's best session; spread = median entry spread bps."]
    for col in ("adv_b", "px_b", "atr_b", "spr_b", "kind", "etb", "sector", "mh_b", "tier"):
        lines.append(f"\n== {col} (all accounts)")
        lines.append(bucket_table(t, col).to_string(index=False))
    for col in ("adv_b", "atr_b", "kind"):
        for s in ("long", "short"):
            lines.append(f"\n== {col} x {s}")
            lines.append(bucket_table(t[t.sidel == s], col).to_string(index=False))
    for col in ("adv_b", "atr_b", "px_b"):
        lines.append(f"\n== {col}, Primary only")
        lines.append(bucket_table(t[t.acct == "p"], col).to_string(index=False))
    # moves list (3 Move Hunt days only - thin)
    lines.append("\n== names on the Move Hunt list (moves.csv, 10-29/10-30/11-02 top movers) vs not")
    lines.append(bucket_table(t.assign(on=np.where(t.mh_list > 0, "on list", "not on list")), "on").to_string(index=False))
    (HERE / "live_buckets_out.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
