"""st7_1022 Part 0: the live (paper) ST7-FD trades of 10-20 and 10-21 in context. Read-only SIP 1-minute bars (market
data GET only; keys come from the environment and are never written) for the traded names, SPY and QQQ; the setup
state at the signal bar recomputed with mcf.research.heat.heat_frame (the lab's own feature code) and the FD module's
mask. Writes live_trades.csv. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import sqlite3
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from sc import HERE, ROOT, W

from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import extra_features  # noqa: E402

TZ = ZoneInfo("America/New_York")
MOD = ROOT / "research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py"


def journal() -> pd.DataFrame:
    p = W / "journal.db"
    p.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", "origin/mcf-data-testing:journal.db"],
                                 capture_output=True, check=True).stdout)
    c = sqlite3.connect(p)
    t = pd.read_sql("select symbol,date,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,r_multiple,"
                    "mae_r,mfe_r,shares,pnl,meta from trades where run_id=1 and strategy='ST7-rsi50dn-long-pm-t1s1-FD'", c)
    return t


def main():
    t = journal()
    t.drop(columns="meta").to_csv(W / "live_all.csv", index=False)
    rec = t[t["date"] >= "2026-10-20"].copy()
    syms = sorted(set(rec["symbol"])) + ["SPY", "QQQ"]
    got = fetch_bars(syms, datetime(2026, 9, 1, 9, 30, tzinfo=TZ), datetime(2026, 10, 21, 16, 0, tzinfo=TZ),
                     feed="sip", client=_client())
    spec = importlib.util.spec_from_file_location("st7fd", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    fr, one = {}, {}
    for s, df in got.items():
        d = df.copy()
        d.index = pd.to_datetime(d.index, utc=True).tz_convert(TZ)
        d = d[(d.index.time >= pd.Timestamp("09:30").time()) & (d.index.time < pd.Timestamp("16:00").time())]
        one[s] = d
        d5 = resample(d, "5min")
        f = heat_frame(d5)
        f = f.join(extra_features(d5, f))
        f["date"] = f.index.date.astype(str)
        f["symbol"] = s
        fr[s] = f
    rows = []
    for _, r in rec.iterrows():
        f = fr[r["symbol"]]
        st = pd.Timestamp(r["signal_time"]).tz_convert(TZ)
        dtod = int(r["meta"].split('"coid": "')[1].split('"')[0].rsplit("-", 1)[1])
        dec = (dtod // 100) * 60 + dtod % 100 + 1                       # coid HHMM = decision bar close - 1 minute
        dec_tod = (dec // 60) * 100 + dec % 60
        day = f[f["date"] == r["date"]].copy()
        mk = m.mask(day.reset_index(drop=True))
        day["mask"] = mk
        b = day[day["tod"] == dec_tod].iloc[0]
        prev = day[day["tod"] < dec_tod].iloc[-1]
        sig_bars = day.loc[day["mask"], "tod"].tolist()
        R = r["entry"] - r["stop"]
        d1 = one[r["symbol"]]
        et = pd.Timestamp(r["entry_time"]).tz_convert(TZ)
        xt = pd.Timestamp(r["exit_time"]).tz_convert(TZ)
        hold = d1[(d1.index >= et.floor("min")) & (d1.index <= xt)]
        rest = d1[(d1.index >= et.floor("min")) & (d1.index.date == et.date())]
        sp = {}
        for ix in ("SPY", "QQQ"):
            x = one[ix][one[ix].index.date == et.date()]
            o = x["open"].iloc[0]
            typ = (x["high"] + x["low"] + x["close"]) / 3
            vw = (typ * x["volume"]).cumsum() / x["volume"].cumsum()
            at = x.index[x.index <= st][-1]
            ex = x.index[x.index <= xt][-1]
            sp[ix] = dict(fo_entry=(x.loc[at, "close"] / o - 1) * 100, vwap_entry=(x.loc[at, "close"] / vw[at] - 1) * 100,
                          fo_exit=(x.loc[ex, "close"] / o - 1) * 100, fo_close=(x["close"].iloc[-1] / o - 1) * 100,
                          low_hold=(x.loc[at:ex, "low"].min() / o - 1) * 100)
        rows.append({
            "date": r["date"], "symbol": r["symbol"], "signal_et": st.strftime("%H:%M:%S"), "decision_bar": dec_tod,
            "lab_mask_bars_today": " ".join(map(str, sig_bars)), "first_lab_signal": sig_bars[0] if sig_bars else None,
            "rsi_prev": round(prev["rsi"], 1), "rsi": round(b["rsi"], 1), "fromOpen": round(b["fromOpen"], 2),
            "buyPressure": round(b["buyPressure"], 3), "gap": round(b["gap"], 2), "vwapDistPct": round(b["vwapDistPct"], 2),
            "RS_vs_spy": round(b["fromOpen"] - sp["SPY"]["fo_entry"], 2),
            "entry": r["entry"], "R_$": round(R, 3), "exit_et": xt.strftime("%H:%M"), "exit_reason": r["exit_reason"],
            "r": round(r["r_multiple"], 3), "pnl": r["pnl"],
            "mfe_r_hold": round((hold["high"].max() - r["entry"]) / R, 2),
            "mae_r_hold": round((hold["low"].min() - r["entry"]) / R, 2),
            "mfe_r_to_close": round((rest["high"].max() - r["entry"]) / R, 2),
            "close_r": round((rest["close"].iloc[-1] - r["entry"]) / R, 2),
            "spy_fo_entry": round(sp["SPY"]["fo_entry"], 2), "spy_vwap_entry": round(sp["SPY"]["vwap_entry"], 2),
            "qqq_fo_entry": round(sp["QQQ"]["fo_entry"], 2), "qqq_vwap_entry": round(sp["QQQ"]["vwap_entry"], 2),
            "spy_fo_exit": round(sp["SPY"]["fo_exit"], 2), "spy_low_during_hold": round(sp["SPY"]["low_hold"], 2),
            "spy_fo_close": round(sp["SPY"]["fo_close"], 2), "qqq_fo_close": round(sp["QQQ"]["fo_close"], 2),
        })
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "live_trades.csv", index=False)
    print(out.T.to_string())
    # SPY / QQQ intraday path of both days (15-minute marks)
    for ix in ("SPY", "QQQ"):
        for d in ("2026-10-20", "2026-10-21"):
            x = one[ix][one[ix].index.date.astype(str) == d]
            o = x["open"].iloc[0]
            typ = (x["high"] + x["low"] + x["close"]) / 3
            vw = (typ * x["volume"]).cumsum() / x["volume"].cumsum()
            q = x.iloc[14::15]
            print(ix, d, " ".join(f"{i:%H:%M} {(c / o - 1) * 100:+.2f}{'v' if c < vw[i] else '^'}"
                                  for i, c in zip(q.index, q["close"])))


if __name__ == "__main__":
    main()
