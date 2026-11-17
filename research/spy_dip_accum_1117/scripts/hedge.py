"""Hedge value: the chosen dip book (SEG-B run from 2025-03-03, $100k) vs the live intraday book (all ten accounts and
Primary alone, live paper run_id 1, 2026-10-06..2026-11-16). Daily and weekly correlations, the dip book after the
intraday book's losing days / weeks, and the combined curve against SPY.
Usage: python hedge.py DAILY.parquet OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_daily  # noqa: E402


def main(daily_path, outdir):
    out = Path(outdir)
    d = load_daily(daily_path)
    live = pd.read_csv(out / "live_book_daily.csv", parse_dates=["date"]).set_index("date")
    book = pd.read_csv(out / "rule_segB_daily.csv", parse_dates=["date"]).set_index("date")
    spy = d["close"]["SPY"]
    df = pd.DataFrame({"live_pl": live.pl, "live_R": live.R, "primary_pl": live.pl_primary})
    df["dip_pl"] = book.equity.diff().reindex(df.index)
    df["dip_weight"] = book.weight.reindex(df.index)
    df["spy_pl_100k"] = (spy.pct_change() * 100_000).reindex(df.index)
    df = df.dropna(subset=["dip_pl"])
    df["dip_next1"] = book.equity.diff().shift(-1).reindex(df.index)
    df["dip_next5"] = (book.equity.shift(-5) - book.equity).reindex(df.index)
    rows = []
    for a in ("live_pl", "live_R", "primary_pl"):
        for b in ("dip_pl", "spy_pl_100k", "dip_next1", "dip_next5"):
            ok = df[[a, b]].dropna()
            rows.append(dict(freq="daily", x=a, y=b, n=len(ok), corr=ok[a].corr(ok[b])))
    wk = df.groupby(df.index.to_period("W-FRI"))[["live_pl", "live_R", "primary_pl", "dip_pl", "spy_pl_100k"]].sum()
    for a in ("live_pl", "live_R", "primary_pl"):
        for b in ("dip_pl", "spy_pl_100k"):
            rows.append(dict(freq="weekly", x=a, y=b, n=len(wk), corr=wk[a].corr(wk[b])))
            rows.append(dict(freq="weekly_next", x=a, y=b, n=len(wk) - 1, corr=wk[a].corr(wk[b].shift(-1))))
    cond = []
    for lab, m in (("live losing days", df.live_pl < 0), ("live winning days", df.live_pl >= 0),
                   ("Primary losing days", df.primary_pl < 0), ("Primary winning days", df.primary_pl >= 0)):
        cond.append(dict(days=lab, n=int(m.sum()), dip_same_day=df.dip_pl[m].mean(), dip_next_day=df.dip_next1[m].mean(),
                         dip_next5=df.dip_next5[m].mean(), live_pl=df.live_pl[m].mean()))
    for lab, m in (("live losing weeks", wk.live_pl < 0), ("live winning weeks", wk.live_pl >= 0)):
        cond.append(dict(days=lab, n=int(m.sum()), dip_same_day=wk.dip_pl[m].mean(), live_pl=wk.live_pl[m].mean()))
    pd.DataFrame(rows).to_csv(out / "hedge_corr.csv", index=False, float_format="%.4g")
    pd.DataFrame(cond).to_csv(out / "hedge_conditional.csv", index=False, float_format="%.1f")
    df.to_csv(out / "hedge_daily.csv", float_format="%.2f")
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(df.index, df.live_pl.cumsum() / 1000, color="#cf222e", label="live intraday book, all 10 accounts")
    ax.plot(df.index, df.primary_pl.cumsum() / 1000, color="#cf222e", ls=":", label="live Primary only")
    ax.plot(df.index, df.dip_pl.cumsum() / 1000, color="#1f6feb", label="dip book ($100k, chosen rule)")
    ax.plot(df.index, (df.live_pl + df.dip_pl).cumsum() / 1000, color="#6e40c9", lw=1.8, label="combined (all + dip)")
    ax.plot(df.index, (df.primary_pl + df.dip_pl).cumsum() / 1000, color="#6e40c9", ls=":", label="combined (Primary + dip)")
    ax.plot(df.index, df.spy_pl_100k.cumsum() / 1000, color="#2da44e", label="SPY buy-and-hold $100k")
    ax.axhline(0, color="#57606a", lw=0.6)
    ax.set_ylabel("cumulative P/L ($k)")
    ax.legend(fontsize=7.5, frameon=False, ncol=2)
    ax.set_title(f"Hedge check {df.index[0].date()}..{df.index[-1].date()} ({len(df)} live sessions; live = paper, "
                 "cost-in P/L; dip book = backtest). Educational only - not financial advice.", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "hedge_1006_1116.png", dpi=110)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print(pd.DataFrame(cond).round(1).to_string(index=False))
    print("totals", df[["live_pl", "primary_pl", "dip_pl", "spy_pl_100k"]].sum().round(0).to_dict(), "weight",
          df.dip_weight.mean().round(3))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
