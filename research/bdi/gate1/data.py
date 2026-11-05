"""GATE1: one trade table (2-year lab lists + live paper journals) with the gate state attached. Writes <scratch>/trades.parquet.
Usage: python data.py <scratch>. Educational only - not financial advice."""
import re, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd

M = Path("/home/user/MCF")
BR = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
      "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}


def fam(s):
    m = re.match(r"[A-Za-z_]+", s)
    return m.group(0).rstrip("_") if m else s


def win(d):
    d = str(d)
    if "2024-11-01" <= d <= "2025-02-28":
        return "LOCKED"
    if d < "2026-01-01":
        return "TRAIN"
    if d <= "2026-10-05":
        return "VALID"
    return "LIVE_BT"


def main(S):
    S = Path(S)
    lab = pd.concat(pd.read_parquet(p) for p in sorted((M / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
    acc = pd.read_csv(M / "research/history2y/data/bt_lab1104/setups.csv")
    acc = acc[acc.covered == True].drop_duplicates("setup").set_index("setup").account
    lab = pd.DataFrame(dict(src="lab", acct=lab.setup.map(acc).values, setup=lab.setup.values, side=lab.side.values,
                            date=lab.date.astype(str).values, m=((lab.tod // 100) * 60 + lab.tod % 100).values, r=lab.r.values))
    lab["w"] = lab.date.map(win)
    lab = lab[lab.w != "LOCKED"]
    rows = []
    for a, b in BR.items():
        c = sqlite3.connect(S / "j" / f"{b}.db")
        t = pd.read_sql("select strategy setup, side, date, entry_time, entry, stop, shares, pnl_adj, pnl from trades "
                        "where run_id=1 and date>='2026-10-06' and entry_time is not null and exit_time is not null", c)
        risk = (t.entry - t.stop).abs() * t.shares
        t["r"] = t.pnl_adj.fillna(t.pnl) / risk
        t = t[np.isfinite(t.r) & (risk > 0)].copy()
        et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
        t["m"] = et.dt.hour * 60 + et.dt.minute
        t["acct"], t["src"], t["w"] = a, "live", "LIVE"
        rows.append(t[["src", "acct", "setup", "side", "date", "m", "r", "w"]])
    T = pd.concat([lab] + rows, ignore_index=True)
    T["fam"] = T.setup.map(fam)
    T["fs"] = T.fam + np.where(T.side > 0, "+L", "+S")
    T["date"] = T.date.astype(str)
    st = pd.read_parquet(S / "state.parquet")
    st["date"] = st.date.astype(str)
    # state of the latest checkpoint T <= entry minute (10:00..15:30), k=1 and k=2
    T["m"] = T.m.astype("int64"); T = T.sort_values("m")
    g = st[st["T"] >= 600][["date", "T", "st", "st2", "fo", "dtype"]].astype({"T": "int64"}).sort_values("T")
    T = pd.merge_asof(T, g.rename(columns={"T": "cp"}), left_on="m", right_on="cp", by="date", direction="backward")
    d10 = st[st["T"] == 600][["date", "fo", "dtype"]].rename(columns={"fo": "fo10", "dtype": "dtype_d"})
    T = T.drop(columns=["dtype"]).merge(d10, on="date", how="left").rename(columns={"dtype_d": "dtype"})
    T.to_parquet(S / "trades.parquet")
    print(T.groupby(["src", "w"]).agg(n=("r", "size"), days=("date", "nunique"), avg=("r", "mean"), nostate=("cp", lambda x: x.isna().mean())))
    print(T[T.src == "live"].groupby("acct").agg(n=("r", "size"), setups=("setup", "nunique"), avg=("r", "mean")))


if __name__ == "__main__":
    main(sys.argv[1])
