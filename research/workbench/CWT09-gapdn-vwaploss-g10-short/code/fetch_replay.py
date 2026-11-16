"""Replay data for sessions 2026-10-12..11-13 (read-only SIP GETs via mcf.replay.store._fetch_bars):
 1. per-day live universe + ETB flags from the data branches' universe.csv snapshots (nearest snapshot at or before
    the session), and the per-day earnings blackout lists (earnings/<day>.json, as live);
 2. daily bars for every snapshot symbol -> gap, adv20, ATR(14) priors;
 3. 1-minute bars for symbol-days with gap <= -7% (+ SPY) -> lab frames as live (engine.lab_frame + apply_daily).
Educational only - not financial advice."""
import io, json, subprocess, sys
import numpy as np, pandas as pd
from datetime import timedelta
from common import OUT, REPLAY, GAP_LOOSE, CODE_ROOT
sys.path.insert(0, CODE_ROOT)
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
R = "/home/user/MCF"
def git(*a): return subprocess.run(["git", "-C", R, *a], capture_output=True, text=True, check=True).stdout
step = sys.argv[1] if len(sys.argv) > 1 else "all"
if step in ("all", "univ"):
    snaps = []
    for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
        for h in git("log", "--format=%H", f"origin/{br}", "--", "universe.csv").split():
            try:
                u = pd.read_csv(io.StringIO(git("show", f"{h}:universe.csv")), usecols=["symbol", "name", "shortable", "easy_to_borrow", "adv", "price", "built_at"])
                snaps.append(u)
            except Exception:
                pass
    U = pd.concat(snaps).drop_duplicates(["symbol", "built_at"])
    U["day"] = pd.to_datetime(U.built_at, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    U["etb"] = (U.shortable.astype(bool) & U.easy_to_borrow.astype(bool))
    U.to_parquet(OUT + "univ_snaps.parquet"); print("snapshots", U.day.nunique(), U.day.min(), U.day.max(), U.symbol.nunique())
    ER = {}
    for day in pd.bdate_range(REPLAY[0], REPLAY[1]).strftime("%Y-%m-%d"):
        for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
            try:
                ER[day] = sorted(json.loads(git("show", f"origin/{br}:earnings/{day}.json"))["symbols"]); break
            except Exception:
                continue
    json.dump(ER, open(OUT + "earn_replay.json", "w")); print("earnings days", len(ER))
if step in ("all", "daily"):
    U = pd.read_parquet(OUT + "univ_snaps.parquet")
    syms = sorted(set(U.symbol.astype(str)) | {"SPY"})
    dl = _fetch_bars(syms, "2026-08-15T00:00:00Z", "2026-11-14T00:00:00Z", "1Day")
    dl.to_parquet(OUT + "rep_daily.parquet"); print("daily", len(dl), dl.symbol.nunique(), flush=True)
if step in ("all", "m1"):
    dl = pd.read_parquet(OUT + "rep_daily.parquet")
    dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).strftime("%Y-%m-%d")
    dl = dl.sort_values(["symbol", "d"]).reset_index(drop=True)
    pc = dl.groupby("symbol").close.shift(1)
    dl["gap"] = (dl.open / pc - 1) * 100
    dl["adv_p"] = (dl.close * dl.volume).groupby(dl.symbol).transform(lambda s: s.rolling(20, min_periods=10).mean().shift(1))
    w = dl[(dl.d >= REPLAY[0]) & (dl.d <= REPLAY[1]) & (dl.gap <= -GAP_LOOSE) & (dl.adv_p >= 1e6)]
    w[["symbol", "d", "gap", "adv_p", "open"]].to_parquet(OUT + "rep_gapdays.parquet")
    print("gap symbol-days", len(w), w.symbol.nunique(), flush=True)
    F, M = [], []
    for day, g in w.groupby("d"):
        syms = sorted(set(g.symbol))
        d = pd.Timestamp(day)
        m1 = _fetch_bars(syms + ["SPY"], f"{(d - timedelta(days=6)).date()}T13:00:00Z", f"{d.date()}T21:05:00Z", "1Min")
        for sym in syms + ["SPY"]:
            gg = m1[m1.symbol == sym]
            if gg.empty: continue
            gg = gg.set_index(pd.DatetimeIndex(gg.ts).tz_convert(E.TZ))[["open", "high", "low", "close", "volume"]].astype(float)
            gg = E._rth(gg.sort_index())
            dd = dl[(dl.symbol == sym) & (dl.d < day)].set_index(pd.to_datetime(dl[(dl.symbol == sym) & (dl.d < day)].d).dt.date)[["open", "high", "low", "close", "volume"]].astype(float)
            x = gg[gg.index.strftime("%Y-%m-%d") == day].copy(); x["symbol"] = sym; x["date"] = day; M.append(x)
            if sym == "SPY": continue
            try:
                fr = E.apply_daily(E.lab_frame(gg), dd, day)
            except Exception as e:
                print("frame fail", day, sym, e); continue
            fr = fr[fr.index.strftime("%Y-%m-%d") == day].copy(); fr["symbol"] = sym; fr["date"] = day
            fr["adv20"] = float(g[g.symbol == sym].adv_p.iloc[0])
            F.append(fr)
        print(day, len(syms), flush=True)
    pd.concat(F).to_parquet(OUT + "replay_frames.parquet")
    pd.concat(M).to_parquet(OUT + "replay_1min.parquet")
