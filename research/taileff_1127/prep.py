"""TAILEFF-1127 helpers. `python prep.py W avg` -> avg_base.csv (BASE RAW avg R per lot, setup x split; Z / P book shifts).
`python prep.py W q BOOK` -> q_<BOOK>_LO_<tgt>.csv (size-matched random-block probabilities, setup x split).
Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd

W = Path(sys.argv[1]); MODE = sys.argv[2]
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
PERS = ["FIT", "CHECK", "T2"]
LOCK = ("2024-11-01", "2025-02-28")


def load(b, c):
    x = pd.read_parquet(W / f"day_{b}_{c}.parquet")
    assert not ((x.date >= LOCK[0]) & (x.date <= LOCK[1])).any()
    return x


if MODE == "avg":
    x = load("RAW", "BASE"); rows = []
    for p, g in x.groupby("per"):
        for s, nm in enumerate(SETUPS):
            rows.append(dict(setup=nm, per=p, a=g[f"R{s}"].sum() / max(g[f"N{s}"].sum(), 1), lots=g[f"N{s}"].sum()))
    pd.DataFrame(rows).to_csv(W / "avg_base.csv", index=False); print(pd.DataFrame(rows))
else:
    book = sys.argv[3]
    f = load(book, "LO")
    for tgt in ("LO+B8", "LO+B8+K4"):
        c = load(book, tgt); rows = []
        for k, p in enumerate(PERS):
            for s in range(4):
                nf = f[f.per == p][f"N{s}"].sum(); nc = c[c.per == p][f"N{s}"].sum()
                rows.append(dict(si=s, pk=k, q=max(0.0, 1 - nc / nf) if nf else 0.0))
        pd.DataFrame(rows).to_csv(W / f"q_{book}_LO_{tgt}.csv", index=False); print(tgt, pd.DataFrame(rows).q.round(3).tolist())
