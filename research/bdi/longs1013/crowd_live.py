"""longs1013 Q3 (live, descriptive): what happened to LONG signals in the three paper journals.

Journals: git show origin/{mcf-data, mcf-data-testing, mcf-data-testing2}:journal.db -> data/{p,t1,t2}/journal.db.
Paper results (rule 7); no setup is scored. Writes tables/crowd_*.csv and prints the tables used in NOTES.md.
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "tables"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 300)
ACC = {"p": "primary", "t1": "Testing 1", "t2": "Testing 2"}


def holder(sig: pd.DataFrame) -> pd.DataFrame:
    """For each 'already in symbol' skip: held_by from info, else the last submitted signal on that symbol before it."""
    sig = sig.sort_values("ts").copy()
    sig["held_by"] = sig["info"].map(lambda s: (json.loads(s) if s else {}).get("held_by") if isinstance(s, str) and s.startswith("{") else None)
    sub = sig[sig.status == "submitted"]
    last = {}
    hb, hs = [], []
    side_of = {}
    for r in sig.itertuples():
        if r.status == "submitted":
            last[(r.day, r.symbol)] = (r.strategy, r.side)
            side_of[(r.day, r.strategy)] = r.side
    lastrun = {}
    for r in sig.itertuples():
        k = (r.day, r.symbol)
        if r.status == "skipped" and r.reason == "already in symbol":
            h = r.held_by or (lastrun.get(k, (None, None))[0])
            hb.append(h)
            hs.append(lastrun.get(k, (None, None))[1] if not r.held_by else side_of.get((r.day, r.held_by), lastrun.get(k, (None, None))[1]))
        else:
            hb.append(None)
            hs.append(None)
        if r.status == "submitted":
            lastrun[k] = (r.strategy, r.side)
    sig["holder"], sig["holder_side"] = hb, hs
    return sig


def main():
    allrows = []
    for a, name in ACC.items():
        c = sqlite3.connect(HERE / "data" / a / "journal.db")
        sig = pd.read_sql("select run_id, day, ts, symbol, strategy, side, status, reason, info from signals", c)
        runs = pd.read_sql("select id, kind from runs", c)
        sig = holder(sig)
        sig["reason_g"] = sig.reason.str.replace(r"\d+(\.\d+)?", "#", regex=True)
        wi = pd.read_sql("select t.symbol, t.strategy, t.date, t.r_multiple, t.meta from trades t join runs r on t.run_id=r.id "
                         "where r.kind='whatif'", c)
        wi = wi.drop_duplicates(["symbol", "strategy", "date"], keep="last")
        sig = sig.merge(wi.rename(columns={"date": "day", "r_multiple": "whatif_r"})[["symbol", "strategy", "day", "whatif_r"]],
                        on=["symbol", "strategy", "day"], how="left")
        real = pd.read_sql("select t.symbol, t.strategy, t.date, t.side, t.r_multiple from trades t join runs r on t.run_id=r.id "
                           "where r.kind!='whatif' and r.kind!='backtest'", c)
        sig["acct"] = name
        allrows.append(sig)
        L = sig[sig.side == 1]
        print(f"\n=== {name}: long signals {len(L)} of {len(sig)}; days {sorted(sig.day.unique())}")
        print(sig.pivot_table(index="day", columns="side", values="symbol", aggfunc="size", fill_value=0).rename(columns={-1: "short sig", 1: "long sig"}).join(
            sig[sig.status == "submitted"].pivot_table(index="day", columns="side", values="symbol", aggfunc="size", fill_value=0).rename(columns={-1: "short taken", 1: "long taken"})).to_string())
        print("long status/reason by day:")
        print(L.pivot_table(index="reason_g", columns="day", values="symbol", aggfunc="size", fill_value=0).to_string())
        b = L[L.reason == "already in symbol"]
        if len(b):
            print("long 'already in symbol' by blocked setup x holder side:")
            print(b.assign(hs=b.holder_side.map({1: "long", -1: "short"}).fillna("?")).pivot_table(index="strategy", columns="hs", values="symbol", aggfunc="size", fill_value=0).to_string())
            print("top holders:", b.holder.value_counts().head(10).to_dict())
            print("what-if R of blocked longs: n", b.whatif_r.notna().sum(), "mean", round(b.whatif_r.mean(), 3), "sum", round(b.whatif_r.sum(), 2))
        cap = L[L.reason_g.str.contains("max positions|max concurrent|slots", regex=True)]
        if len(cap):
            print("long cap skips:", cap.groupby(["day", "strategy"]).size().to_dict(), "what-if mean", round(cap.whatif_r.mean(), 3))
        # shorts blocked by longs, for symmetry
        S = sig[(sig.side == -1) & (sig.reason == "already in symbol")]
        print("short 'already in symbol': n", len(S), "held by long", int((S.holder_side == 1).sum()), "by short", int((S.holder_side == -1).sum()))
        # long realised vs what-if per setup
        tk = real[real.side == 1].groupby("strategy").r_multiple.agg(["size", "mean"]).round(3)
        sk = L[L.status != "submitted"].groupby("strategy").whatif_r.agg(["size", "mean"]).round(3)
        print("long setups: taken (real) vs not taken (what-if):")
        print(tk.join(sk, how="outer", lsuffix="_taken", rsuffix="_skipped").fillna("").to_string())
    A = pd.concat(allrows, ignore_index=True)
    A.drop(columns=["info"]).to_csv(OUT / "crowd_signals.csv", index=False)
    L = A[A.side == 1]
    t = L.groupby(["acct", "day"]).agg(long_signals=("symbol", "size"), taken=("status", lambda s: int((s == "submitted").sum())),
                                       in_symbol=("reason", lambda s: int((s == "already in symbol").sum())),
                                       cap=("reason_g", lambda s: int(s.str.contains("max positions|max concurrent").sum())),
                                       spread=("reason_g", lambda s: int(s.str.contains("spread").sum())),
                                       other=("reason_g", lambda s: int((~s.str.contains("spread|max positions|max concurrent|already in symbol|ok")).sum())))
    hb = L[L.reason == "already in symbol"].groupby(["acct", "day"]).holder_side.agg(by_short=lambda s: int((s == -1).sum()), by_long=lambda s: int((s == 1).sum()))
    t = t.join(hb).fillna(0).astype(int)
    t.to_csv(OUT / "crowd_long_per_day.csv")
    print("\n", t.to_string())


if __name__ == "__main__":
    main()
