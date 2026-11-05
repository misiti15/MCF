"""REGX: one trade table (2-year lab lists TRAIN/VALID + live journals of 7 accounts) with the cell of every scheme in
PLAN.md attached at the entry minute. Needs <scratch>/bars1105.parquet and breadth500.parquet. Writes <scratch>/trades.parquet.
Usage: python cells.py <scratch>. Educational only - not financial advice."""
import re, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd

M = Path("/home/user/MCF")
S = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
BR = {"P": "mcf-data", "T1": "mcf-data-testing", "T2": "mcf-data-testing2", "GY": "mcf-data-graveyard",
      "GEN": "mcf-data-gen", "EX1": "mcf-data-explore1", "LL": "mcf-data-livelab"}
ETF = ["SPY", "QQQ", "IWM", "XLK", "XLY", "XLC", "XLP", "XLU", "XLV"]
B5 = pd.read_parquet(S / "bars1105.parquet")


def bars(sym):
    b = pd.read_parquet(M / "data/cache_hist/1Min" / f"{sym}.parquet")
    b = b[(b.index < "2024-11-01") | (b.index >= "2025-03-01")]
    x = B5[B5.symbol == sym].set_index("t")[["open", "high", "low", "close", "volume"]]
    b = pd.concat([b[["open", "high", "low", "close", "volume"]], x])
    b = b[~b.index.duplicated()]
    b["date"] = b.index.strftime("%Y-%m-%d"); b["m"] = b.index.hour * 60 + b.index.minute
    return b[(b.m >= 570) & (b.m < 960)]


def minute_table():
    """date x minute (bar start) with SPY VWAP side, range ratio, and from-open of each ETF."""
    out = None
    for s in ETF:
        b = bars(s)
        o = b.groupby("date").open.transform("first")
        t = pd.DataFrame({"date": b.date.values, "bm": b.m.values, f"{s}_fo": (b.close / o - 1).values})
        if s == "SPY":
            tp = (b.high + b.low + b.close) / 3
            pv = (tp * b.volume).groupby(b.date).cumsum(); v = b.volume.groupby(b.date).cumsum()
            t["spy_vw"] = (b.close / (pv / v) - 1).values
            hi = b.high.groupby(b.date).cummax(); lo = b.low.groupby(b.date).cummin()
            t["rng"] = ((hi - lo) / o).values
            t["close_px"] = b.close.values
        out = t if out is None else out.merge(t, on=["date", "bm"], how="left")
    # range vs median of the same minute over the prior 20 sessions
    w = out.pivot(index="date", columns="bm", values="rng").sort_index()
    med = w.shift(1).rolling(20, min_periods=10).median()
    rr = (w / med).stack().rename("rngx").reset_index()
    out = out.merge(rr, on=["date", "bm"], how="left")
    out["sect"] = out[["XLK_fo", "XLY_fo", "XLC_fo"]].mean(1) - out[["XLP_fo", "XLU_fo", "XLV_fo"]].mean(1)
    return out


def day_table():
    b = bars("SPY")
    g = b.groupby("date")
    d = pd.DataFrame({"o": g.open.first(), "c": g.close.last(), "h": g.high.max(), "l": g.low.min(), "lastm": g.m.max()})
    d["oc"] = d.c / d.o - 1; d["hl"] = (d.h - d.l) / d.o
    d["hl_med"] = d.hl.shift(1).rolling(20, min_periods=10).median()
    d["DASH"] = np.where(d.oc >= 0.005, "Bull", np.where(d.oc <= -0.005, "Bear", np.where(d.hl >= d.hl_med, "Choppy", "Quiet")))
    d["OC25"] = np.where(d.oc >= 0.0025, "up", np.where(d.oc <= -0.0025, "down", "quiet"))
    d.loc[d.lastm < 955, ["DASH", "OC25"]] = None
    # first-hour day type
    def fo_at(T):
        x = b[b.m < T].groupby("date").close.last()
        return x / d.o - 1
    a, bb = fo_at(600), fo_at(630)
    tr = (np.sign(a) == np.sign(bb)) & (bb.abs() >= 0.0025) & (bb.abs() >= 0.67 * a.abs())
    rv = (a.abs() >= 0.0015) & ((np.sign(bb) != np.sign(a)) | (bb.abs() < 0.33 * a.abs()))
    d["DAYT"] = np.where(tr & (bb > 0), "trend-up", np.where(tr & (bb < 0), "trend-down", np.where(rv, "reversal", "range")))
    return d.reset_index()


def compass():
    """gate1 state.py + compass.py votes at 09:45, 10:00..15:30 (breadth_open: context tables; 11-05 recomputed)."""
    CPS = [585] + list(range(600, 931, 30))
    def per_day(sym, full):
        b = bars(sym); rows = []
        for d, g in b.groupby("date"):
            o = g.open.iloc[0]; c = g.close.values; m = g.m.values
            tp = (g.high + g.low + g.close).values / 3; v = g.volume.values
            cpv, cv = np.cumsum(tp * v), np.cumsum(v)
            for T in CPS:
                i = np.searchsorted(m, T) - 1
                if i < 0:
                    continue
                r = dict(date=d, T=T, fo=c[i] / o - 1)
                if full:
                    r["vw"] = c[i] / (cpv[i] / cv[i]) - 1
                rows.append(r)
        return pd.DataFrame(rows)
    st = per_day("SPY", True)
    for s in ["QQQ", "IWM"]:
        st = st.merge(per_day(s, False).rename(columns={"fo": s.lower() + "_fo"}), on=["date", "T"], how="left")
    ctx = pd.concat(pd.read_parquet(p) for p in sorted((M / "research/history2y/data/context").glob("month=*.parquet")))
    ctx["date"] = pd.to_datetime(ctx.date).dt.strftime("%Y-%m-%d"); ctx["T"] = (ctx.tod // 100) * 60 + ctx.tod % 100
    ctx = ctx[["date", "T", "breadth_open"]]
    # 11-05: universe breadth_open from the fetched bars (close of the last bar before T > the day's open)
    lab = set(M.joinpath("research/lab_symbols.txt").read_text().split())
    x = B5[B5.symbol.isin(lab)].copy(); x["m"] = x.t.dt.hour * 60 + x.t.dt.minute
    x["o"] = x.groupby("symbol").open.transform("first")
    rows = []
    for T in sorted(set(ctx["T"])):
        y = x[x.m < T].groupby("symbol").agg(c=("close", "last"), o=("o", "first"))
        if len(y):
            rows.append(dict(date="2026-11-05", T=T, breadth_open=(y.c > y.o).mean()))
    ctx = pd.concat([ctx, pd.DataFrame(rows)])
    c2 = ctx[ctx["T"] == 900].copy(); c2["T"] = 930
    st = st.merge(pd.concat([ctx, c2]).drop_duplicates(["date", "T"]), on=["date", "T"], how="left")
    st = st.sort_values(["date", "T"]).reset_index(drop=True)
    sg = lambda z: np.nan_to_num(np.sign(np.asarray(z, float))).astype(int)
    g = st.groupby("date"); st["p1"] = g.fo.shift(1); st["p2"] = g.fo.shift(2)
    pers2 = np.where(sg(st.fo) == sg(st.p1), sg(st.fo), 0)
    pers3 = np.where((sg(st.fo) == sg(st.p1)) & (sg(st.p1) == sg(st.p2)), sg(st.fo), 0)
    agree = np.where((sg(st.fo) == sg(st.qqq_fo)) & (sg(st.fo) == sg(st.iwm_fo)), sg(st.fo), 0)
    bo = st.breadth_open.where(st["T"] != 585, 0.5)
    bside = np.where(bo > 0.5, 1, np.where(bo < 0.5, -1, 0))
    v = sg(st.fo) + sg(st.vw) + pers2 + bside + agree
    comp = np.where((v >= 4) & (pers3 == 1), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pers3 == -1), -2, np.where(v <= -2, -1, 0))))
    st["COMP"] = np.where(comp > 0, "up", np.where(comp < 0, "down", "mixed"))
    st["comp5"] = comp
    return st[st["T"].between(600, 840)][["date", "T", "COMP", "comp5"]]


def fam(s):
    m = re.match(r"[A-Za-z]+[0-9]*", s)
    return m.group(0) if m else s


def trades():
    lab = pd.concat(pd.read_parquet(p, columns=["setup", "side", "date", "tod", "r"])
                    for p in sorted((M / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
    lab["date"] = lab.date.astype(str)
    lab = lab[~lab.date.between(*LOCK) & (lab.date <= "2026-10-05")]
    lab["w"] = np.where(lab.date < "2026-01-01", "TRAIN", "VALID")
    lab["m"] = (lab.tod // 100) * 60 + lab.tod % 100
    lab["acct"] = "bt"
    rows = [lab[["setup", "side", "date", "m", "r", "w", "acct"]]]
    for a, b in BR.items():
        t = pd.read_sql("select strategy setup, side, date, entry_time, entry, stop, shares, pnl_adj, pnl from trades "
                        "where run_id=1 and date>='2026-10-06' and entry_time is not null and exit_time is not null",
                        sqlite3.connect(S / "j" / f"{b}.db"))
        risk = (t.entry - t.stop).abs() * t.shares
        t["r"] = t.pnl_adj.fillna(t.pnl) / risk
        t = t[np.isfinite(t.r) & (risk > 0)].copy()
        et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
        t["m"] = et.dt.hour * 60 + et.dt.minute; t["w"] = "LIVE"; t["acct"] = a
        rows.append(t[["setup", "side", "date", "m", "r", "w", "acct"]])
    T = pd.concat(rows, ignore_index=True)
    T["date"] = T.date.astype(str); T["m"] = T.m.astype("int64")
    T["side"] = np.where(T.side > 0, "long", "short")
    T["fam"] = T.setup.map(fam)
    return T


if __name__ == "__main__":
    T = trades(); print(T.groupby("w").size(), flush=True)
    mt = minute_table(); dt = day_table(); cp = compass()
    T["bm"] = T.m - 1
    T = T.sort_values("bm")
    T = pd.merge_asof(T, mt.sort_values("bm")[["date", "bm", "spy_vw", "rngx", "sect"]].astype({"bm": "int64"}),
                      on="bm", by="date", direction="backward")
    T["VWAP"] = np.where(T.spy_vw > 0, "above", np.where(T.spy_vw < 0, "below", None))
    T.loc[T.spy_vw.isna(), "VWAP"] = None
    T["VOL"] = np.where(T.rngx < 0.75, "low", np.where(T.rngx > 1.33, "high", "normal")); T.loc[T.rngx.isna(), "VOL"] = None
    T["SECT"] = np.where(T.sect >= 0.002, "offense", np.where(T.sect <= -0.002, "defense", "neutral")); T.loc[T.sect.isna(), "SECT"] = None
    br = pd.read_parquet(S / "breadth500.parquet")[["date", "b", "brd"]].astype({"b": "int64"}).sort_values("b")
    T = pd.merge_asof(T.sort_values("m"), br, left_on="m", right_on="b", by="date", direction="backward")
    T["BRD"] = np.where(T.brd >= 0.6, "strong", np.where(T.brd <= 0.4, "weak", "mixed")); T.loc[T.brd.isna(), "BRD"] = None
    T = pd.merge_asof(T, cp.astype({"T": "int64"}).sort_values("T"), left_on="m", right_on="T", by="date", direction="backward")
    T = T.merge(dt[["date", "DASH", "OC25", "DAYT", "oc"]], on="date", how="left")
    T.loc[T.m < 630, "DAYT"] = None
    T.to_parquet(S / "trades.parquet")
    for s in ["DASH", "OC25", "VWAP", "COMP", "DAYT", "VOL", "BRD", "SECT"]:
        print(s, T.groupby("w")[s].apply(lambda x: x.notna().mean()).round(3).to_dict(), T[s].value_counts().to_dict())
    print(dt.tail(4)[["date", "oc", "DASH", "OC25", "DAYT"]])
