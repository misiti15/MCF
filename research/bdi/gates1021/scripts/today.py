"""gates1021: live-day diagnosis of 2026-10-21 for NS3-failed-vwap-reclaim-short-FD and L3-gap-slope-fromopen-FD in
Primary (PAPER results from the journal on origin/mcf-data, run_id 1). Market state at each entry from the read-only
1-minute SIP bars fetched by fetch_today.py. Writes today_trades.csv and today.json. Not a test.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
import subprocess

import numpy as np
import pandas as pd

from common import HERE, ROOT, SCR

SETUPS = ("NS3-failed-vwap-reclaim-short-FD", "L3-gap-slope-fromopen-FD")
DAY = "2026-10-21"


def five_min(b: pd.DataFrame) -> pd.DataFrame:
    """Per symbol 5-minute bars (label left) with session VWAP and fromOpen at each 5-minute close."""
    b = b[b.index.strftime("%Y-%m-%d") == DAY].copy()
    b["bucket"] = b.index.floor("5min")
    b["pv"] = (b["high"] + b["low"] + b["close"]) / 3 * b["volume"]
    g = b.groupby(["symbol", "bucket"]).agg(open=("open", "first"), close=("close", "last"), pv=("pv", "sum"),
                                            v=("volume", "sum")).reset_index()
    g = g.sort_values(["symbol", "bucket"])
    g["vwap"] = g.groupby("symbol")["pv"].cumsum() / g.groupby("symbol")["v"].cumsum()
    g["o0"] = g.groupby("symbol")["open"].transform("first")
    g["fo"] = (g["close"] / g["o0"] - 1) * 100
    g["end"] = g["bucket"] + pd.Timedelta(minutes=5)
    g["tod"] = g["end"].dt.hour * 100 + g["end"].dt.minute
    return g


def main():
    bars = pd.read_parquet(SCR / "today" / "bars_1020_1021.parquet")
    lab = set((ROOT / "research" / "lab_symbols.txt").read_text().split())
    g = five_min(bars)
    uni = g[g["symbol"].isin(lab)]
    br = uni.assign(a=(uni["close"] > uni["vwap"]).astype(float)).groupby("tod")["a"].mean().rename("breadth")
    ctx = pd.DataFrame(br)
    for ix in ("SPY", "QQQ", "IWM"):
        ctx[ix.lower() + "_fo"] = g[g["symbol"] == ix].set_index("tod")["fo"]
    ctx["d2"] = ctx["breadth"] - ctx["breadth"].shift(2)
    fo = g.pivot_table(index="tod", columns="symbol", values="fo")
    peers = json.load(open(SCR / "peers.json"))
    # SPY day so far, and 10-20
    spy = bars[bars["symbol"] == "SPY"]
    days = {}
    for d, x in spy.groupby(spy.index.strftime("%Y-%m-%d")):
        days[d] = round((x["close"].iloc[-1] / x["open"].iloc[0] - 1) * 100, 3)

    db = SCR / "j" / "mcf-data.db"
    if not db.exists():
        db.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", "origin/mcf-data:journal.db"], capture_output=True,
                                      check=True).stdout)
    c = sqlite3.connect(db)
    q = ",".join("?" * len(SETUPS))
    o = pd.read_sql(f"select created_at, symbol, strategy, qty, entry_ref, stop, target, broker_order_id from orders "
                    f"where run_id=1 and created_at like '{DAY}%' and strategy in ({q})", c, params=SETUPS)
    t = pd.read_sql(f"select symbol, strategy, signal_time, entry_time, entry, exit_time, exit, exit_reason, r_multiple, "
                    f"pnl, pnl_adj, broker_order_id from trades where run_id=1 and date='{DAY}' and strategy in ({q})",
                    c, params=SETUPS)
    m = o.merge(t[["broker_order_id", "entry_time", "entry", "exit_time", "exit", "exit_reason", "r_multiple", "pnl",
                   "pnl_adj"]], on="broker_order_id", how="left")
    et = pd.to_datetime(m["created_at"], utc=True).dt.tz_convert("America/New_York")
    m["entry_et"] = et.dt.strftime("%H:%M")
    dec = et.dt.floor("5min")                              # decision bar close = signal poll time floored
    m["tod"] = dec.dt.hour * 100 + dec.dt.minute
    xt = pd.to_datetime(m["exit_time"], utc=True).dt.tz_convert("America/New_York")
    m["exit_et"] = xt.dt.strftime("%H:%M")
    m = m.sort_values("created_at").reset_index(drop=True)
    # status: open lots unrealized
    st = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "origin/mcf-data:status.json"], capture_output=True,
                                   check=True).stdout)
    pos = {(p["symbol"], p["strategy"]): p for p in st.get("positions", [])}
    rows = []
    for i, r in m.iterrows():
        tod = int(r["tod"])
        cx = ctx.loc[tod] if tod in ctx.index else pd.Series(dtype=float)
        p = [x for x in peers.get(r["symbol"], []) if x in fo.columns]
        pv = fo.loc[tod, p].dropna().to_numpy(float) if p and tod in fo.index else np.array([])
        prior = m.iloc[:i]
        same = prior[(prior["symbol"] == r["symbol"]) & (prior["strategy"] == r["strategy"])]
        open_before = same[(same["exit_time"].isna()) | (pd.to_datetime(same["exit_time"], utc=True)
                                                         > pd.to_datetime(r["created_at"], utc=True))]
        stopped_before = same[(same["exit_reason"] == "stop") & (pd.to_datetime(same["exit_time"], utc=True)
                                                                 <= pd.to_datetime(r["created_at"], utc=True))]
        setup_open = prior[(prior["strategy"] == r["strategy"]) & ((prior["exit_time"].isna()) | (
            pd.to_datetime(prior["exit_time"], utc=True) > pd.to_datetime(r["created_at"], utc=True)))]
        rows.append({"setup": r["strategy"], "symbol": r["symbol"], "entry_et": r["entry_et"], "tod": tod,
                     "status": "closed" if pd.notna(r["exit_reason"]) else "open", "exit_et": r["exit_et"],
                     "exit_reason": r["exit_reason"], "r": r["r_multiple"], "pnl_adj": r["pnl_adj"],
                     "lot_no": len(same) + 1, "lots_open_same_symbol": len(open_before),
                     "after_stop_same_symbol": len(stopped_before) > 0, "setup_open_lots": len(setup_open),
                     "spy_fo": round(float(cx.get("spy_fo", np.nan)), 3), "qqq_fo": round(float(cx.get("qqq_fo", np.nan)), 3),
                     "breadth": round(float(cx.get("breadth", np.nan)), 3), "d2": round(float(cx.get("d2", np.nan)), 3),
                     "stock_fo": round(float(fo.loc[tod, r["symbol"]]), 2) if r["symbol"] in fo.columns and tod in fo.index else None,
                     "peer_med_fo": round(float(np.median(pv)), 2) if len(pv) >= 3 else None,
                     "peers": ",".join(p)})
    df = pd.DataFrame(rows)
    # open lots: split each position's unrealized P/L evenly over its lots (status.json has per position, not per lot)
    for (sym, s), p in pos.items():
        k = (df["symbol"] == sym) & (df["setup"] == s) & (df["status"] == "open")
        if k.any():
            df.loc[k, "upl_share"] = p["upl"] / k.sum()
    df.to_csv(HERE / "today_trades.csv", index=False)
    names = ["SPY", "QQQ", "IWM", "CIFR", "RIOT", "HUT", "CLSK", "IREN", "MARA", "WULF", "NBIS", "SKHY", "CRWV", "AAOI",
             "AKAM", "FPS", "ROIV", "FTNT", "TKNO", "IBRX", "JD", "CBRS", "AXTI"]
    cols = [x for x in (1000, 1030, 1100, 1130, 1200, 1230, 1300, 1330, 1400, 1430) if x in fo.index]
    fo.loc[cols, [n for n in names if n in fo.columns]].T.round(2).to_csv(HERE / "today_paths.csv")
    # tweak replay on today's paper trades (closed R + open unrealized $)
    out = {"spy_o2c_so_far": days, "asof_status": st.get("asof_et"), "ctx_1000_1400": ctx.loc[
        [x for x in (1000, 1030, 1100, 1130, 1200, 1300, 1400) if x in ctx.index]].round(3).to_dict("index")}
    rep = {}
    for s in SETUPS:
        x = df[df["setup"] == s].copy()
        x["usd"] = x["pnl_adj"].fillna(0) + x["upl_share"].fillna(0)
        rules = {
            "A0 as live": np.zeros(len(x), bool),
            "A1 first signal per symbol-day": x["lot_no"].to_numpy() > 1,
            "g1 no re-entry after a stop": x["after_stop_same_symbol"].to_numpy(bool),
            "g2 one lot at a time": x["lots_open_same_symbol"].to_numpy() > 0,
            "g3 spy>=0.25 & breadth rising": (x["spy_fo"] >= 0.25).to_numpy() & (x["d2"] > 0).to_numpy(),
            "g3 spy>=0.50 & breadth rising": (x["spy_fo"] >= 0.50).to_numpy() & (x["d2"] > 0).to_numpy(),
            "g4 qqq>=0.25": (x["qqq_fo"] >= 0.25).to_numpy(),
            "g4 qqq>=0.50": (x["qqq_fo"] >= 0.50).to_numpy(),
            "g5 peers>=1%": (x["peer_med_fo"].astype(float) >= 1.0).to_numpy(),
            "g5 peers>=2%": (x["peer_med_fo"].astype(float) >= 2.0).to_numpy(),
            "g6 <=11:30": (x["tod"] > 1130).to_numpy(), "g6 <=13:00": (x["tod"] > 1300).to_numpy(),
            "g6 >=10:30": (x["tod"] < 1030).to_numpy(),
            "g7 open lots>=5": (x["setup_open_lots"] >= 5).to_numpy(), "g7 open lots>=10": (x["setup_open_lots"] >= 10).to_numpy(),
        }
        # g8: -2R realized stop on the journal's own exit times
        ent = pd.to_datetime(x["entry_et"], format="%H:%M")
        cl = x[x["status"] == "closed"]
        blk = []
        for e in ent:
            done = cl[pd.to_datetime(cl["exit_et"], format="%H:%M") <= e]
            blk.append(done["r"].sum() <= -2)
        rules["g8 -2R daily stop"] = np.array(blk, bool)
        rr = {}
        for k, b in rules.items():
            kept = x[~b]
            rr[k] = {"lots_blocked": int(b.sum()), "lots_kept": int((~b).sum()),
                     "kept_closed_R": round(float(kept["r"].fillna(0).sum()), 2),
                     "kept_usd_incl_open": round(float(kept["usd"].sum()), 1),
                     "blocked_usd_incl_open": round(float(x[b]["usd"].sum()), 1)}
        rep[s] = rr
    out["replay"] = rep
    json.dump(out, open(HERE / "today.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    print(df.drop(columns=["peers"]).to_string())
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
