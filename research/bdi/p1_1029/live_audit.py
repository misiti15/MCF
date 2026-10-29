"""p1_1029 task 1: long-book audit from the live (paper) journals of Primary / Testing 1 / Testing 2.
Journals are copied read-only from origin/mcf-data, origin/mcf-data-testing, origin/mcf-data-testing2 (git show
<branch>:journal.db, the same branches nightly1028/fetch.py and top5_1028/live_rank.py read). run_id = 1, complete
sessions only (2026-10-29 is in progress and is excluded). avg R = pnl_adj / $ risk (costs in, as nightly1028).
Shrunk avg R = avgR x n / (n + 20). Setups listed per account where they are assigned now (docs/live/assignments.json)
and merged across the three accounts by setup name (as the dashboard does).
Educational only - not financial advice.

    python research/bdi/p1_1029/live_audit.py <scratch>     # expects <scratch>/{p,t1,t2}.db
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
S = Path(sys.argv[1])
TODAY = "2026-10-29"
ACC = {"p": "primary", "t1": "testing", "t2": "testing2"}


def stats(d):
    r = d["R"]
    n = len(r)
    day = d.groupby("date")["R"].sum()
    best = day.idxmax() if len(day) else None
    exb = (r.sum() - day.max()) / (n - (d.date == best).sum()) if n > (d.date == best).sum() else np.nan
    share = day.max() / r.sum() if r.sum() > 0 else np.nan
    dn = d.groupby("date")["R"].agg(["sum", "size"])
    m = r.mean()
    se = np.sqrt(((dn["sum"] - m * dn["size"]) ** 2).sum()) / n if n else np.nan
    return {"n": n, "sessions": d.date.nunique(), "win": round((r > 0).mean(), 3), "avgR": round(m, 4),
            "shrunk": round(m * n / (n + 20), 4), "t_day": round(m / se, 2) if se > 0 else np.nan,
            "pnl_net": round(d.pnl_adj.sum(), 2), "exbest": round(exb, 4), "best_share": round(share, 2) if share == share else None}


def main():
    a = json.load(open(ROOT / "docs/live/assignments.json"))["accounts"]
    fr = []
    for k, acct in ACC.items():
        c = sqlite3.connect(S / f"{k}.db")
        t = pd.read_sql("select * from trades where run_id=1", c)
        t["acct"] = acct
        fr.append(t)
    t = pd.concat(fr, ignore_index=True)
    t = t[(t.date < TODAY) & t.pnl_adj.notna() & t.exit_time.notna()]
    risk = (t.entry - t.stop).abs() * t.shares
    t = t[risk > 0].copy()
    t["R"] = t.pnl_adj / risk[risk > 0]
    longs = t[t.side == 1]
    rows = []
    for acct in ACC.values():
        for s in a[acct]:
            d_acc = longs[(longs.strategy == s) & (longs.acct == acct)]
            d_all = longs[longs.strategy == s]
            if not len(d_all):
                if s.endswith("long") or "long" in s:
                    rows.append({"setup": s, "account": acct, "n": 0})
                continue
            ra = stats(d_all)
            rows.append({"setup": s, "account": acct, **{f"{k}": v for k, v in ra.items()},
                         "n_this_acct": len(d_acc), "avgR_this_acct": round(d_acc.R.mean(), 4) if len(d_acc) else np.nan,
                         "first": d_all.date.min(), "last": d_all.date.max()})
    df = pd.DataFrame(rows).drop_duplicates(["setup", "account"])
    df.to_csv(OUT / "live_longs.csv", index=False)
    pd.set_option("display.width", 250)
    print("Educational only - not financial advice. Live paper, run 1, complete sessions <", TODAY)
    print(df.sort_values("shrunk").to_string(index=False))
    flag = df[(df.n >= 15) & (df.shrunk < 0)]
    print("\nflagged n>=15 & shrunk<0:", len(flag))
    print(flag[["setup", "account", "n", "sessions", "avgR", "shrunk", "t_day", "pnl_net", "exbest", "best_share"]].to_string(index=False))
    # whole live book by side
    for side, g in t.groupby("side"):
        print("side", side, stats(g))


if __name__ == "__main__":
    main()
