"""regime1022: as-run trades per covered setup = refire chain (scan) + per-setup lot cap 3 per symbol (lots exit at
their 5-minute-path exit bar), the gates1021 Part A 'A0' rule; plus the hindsight regime label of the session.
Writes $SCR/asrun.parquet (every signal, with keep flag `asrun`). Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from rc import HERE, SCR, no_locked, split_of
from regime import day_table


def sequence(dates, tods, syms, exits, cap=3):
    """Vectorised-per-day version of gates1021 part_a.sequence (cap only)."""
    keep = np.zeros(len(dates), bool)
    order = np.lexsort((syms, tods, dates))
    cur_d, lots = None, []
    for i in order:
        if dates[i] != cur_d:
            cur_d, lots = dates[i], []
        t = tods[i]
        lots = [L for L in lots if L[1] > t]
        if sum(L[0] == syms[i] for L in lots) >= cap:
            continue
        keep[i] = True
        lots.append((syms[i], exits[i]))
    return keep


def load_sig() -> pd.DataFrame:
    s = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "sig").glob("*.parquet"))], ignore_index=True)
    if "error" in s:
        bad = s[s["error"].notna()]
        assert bad.empty, bad.head()
        s = s.drop(columns="error")
    s["date"] = pd.to_datetime(s["date"]).dt.date
    no_locked(s["date"].unique())
    meta = pd.read_csv(HERE / "setups_scored.csv")
    s = s.merge(meta[["skey", "setup", "names", "accounts", "side", "geom"]], on="skey", how="left")
    return s


def main():
    s = load_sig()
    keep = np.zeros(len(s), bool)
    for k, g in s.groupby("skey"):
        idx = g.index.to_numpy()
        keep[idx] = sequence(g["date"].astype(str).to_numpy(), g["tod"].to_numpy(), g["symbol"].to_numpy(),
                             g["exit_tod"].to_numpy())
    s["asrun"] = keep
    dt = day_table()
    s = s.join(dt[["regime", "o2c", "range"]], on="date")
    s["split"] = split_of(s["date"])
    s.to_parquet(SCR / "asrun.parquet")
    print(s.groupby("setup")["asrun"].agg(["size", "sum"]).to_string())


if __name__ == "__main__":
    main()
