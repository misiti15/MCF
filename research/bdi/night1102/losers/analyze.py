"""Per-trade features + paired what-ifs on the actual 1-minute bars, for ALL live trades 2026-10-20..11-02 (run_id 1, all
5 intraday accounts); losers are flagged (R <= -1 or an account-day's 10 worst). Usage: python analyze.py <scratch>
-> <scratch>/feat.parquet. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from sim import run
from symtype import symtype

S = Path(sys.argv[1])
t = pd.read_parquet(S / "trades.parquet").reset_index(drop=True)
t["rk"] = t.groupby(["account", "date"]).R.rank(method="first")
t["loser"] = (t.R <= -1) | (t.rk <= 10)
t["ty"] = t.symbol.map(symtype)
NY = "America/New_York"
for k in ("signal_time", "entry_time", "exit_time"):
    t[k] = pd.to_datetime(t[k], utc=True, format="mixed").dt.tz_convert(NY)
t["base"] = t.strategy.str.replace(r"-FD$", "", regex=True)

VARIANTS = {  # name: (entry kind, kwargs)
    "base": ("now", {}),
    "wait0": ("wait", {"n": 0}), "wait1": ("wait", {"n": 1}), "wait3": ("wait", {"n": 3}), "wait5": ("wait", {"n": 5}),
    "lim_vwap": ("vwap", {}), "lim_pb25": ("pb", {"k": 0.25}),
    "ts30": ("now", {"time_stop": 30}), "ts60": ("now", {"time_stop": 60}),
    "be03": ("now", {"be_at": 0.3}), "scr30": ("now", {"scratch": (30, 0.25)}), "scr15": ("now", {"scratch": (15, 0.25)}), "scr60": ("now", {"scratch": (60, 0.25)}), "part05": ("now", {"partial": 0.5}), "wide15": ("now", {"wide": 1.5}),
    "opposite": ("opp", {}),
}
rows = []
for d, g in t.groupby("date"):
    B = pd.read_parquet(S / "bars" / f"{d}.parquet")
    B["ts"] = pd.DatetimeIndex(B["ts"]).tz_convert(NY)
    bars = {s: x.set_index("ts").sort_index() for s, x in B.groupby("symbol")}
    spy = bars["SPY"]; spy_open = spy.open.iloc[0]
    spy_close = spy.close[spy.index.strftime("%H:%M") <= "15:55"].iloc[-1]
    for idx, r in g.iterrows():
        x = bars.get(r.symbol)
        out = {"i": idx}
        if x is None or len(x) < 10:
            rows.append(out); continue
        o, h, l, c, v = (x[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
        tm = x.index
        tp = (h + l + c) / 3
        vwap = np.cumsum(tp * v) / np.maximum(np.cumsum(v), 1)
        em = r.entry_time.floor("min")
        i0 = int(np.searchsorted(tm, em + pd.Timedelta(minutes=1)))  # first full bar after the fill
        end = int(np.searchsorted(tm, tm[0].normalize() + pd.Timedelta(hours=15, minutes=55), side="right")) - 1
        if i0 >= end:
            rows.append(out); continue
        side = int(r.side); e = float(r.entry); dd = abs(e - float(r.stop))
        td = abs(float(r.target) - e) if r.target == r.target else np.nan
        # context
        sm = r.signal_time.floor("min")
        j = int(np.searchsorted(tm, sm))  # bar of the signal minute
        w = slice(max(0, j - 5), j)
        hi5, lo5 = (h[w].max(), l[w].min()) if j > 0 else (np.nan, np.nan)
        out["pos5"] = (e - lo5) / (hi5 - lo5) if hi5 > lo5 else np.nan  # entry within the 5 bars before the signal (0 low .. 1 high)
        out["pos5_side"] = out["pos5"] if side > 0 else 1 - out["pos5"]  # 1 = chased (bought the high / sold the low)
        out["rng5_R"] = (hi5 - lo5) / dd if hi5 > lo5 else np.nan
        out["vwap_dist_R"] = side * (e - vwap[max(j - 1, 0)]) / dd
        out["fromopen_pct"] = (e / o[0] - 1) * 100 * side
        si = spy.index.searchsorted(em)
        sp = spy.close.iloc[max(si - 1, 0)]
        out["spy_fo"] = (sp / spy_open - 1) * 100
        out["spy_30"] = (sp / spy.close.iloc[max(si - 31, 0)] - 1) * 100
        out["spy_rest"] = (spy_close / sp - 1) * 100  # hindsight: SPY entry -> 15:55
        out["mins_to_exit"] = (r.exit_time - r.entry_time).total_seconds() / 60
        out["etod"] = em.strftime("%H%M")
        out["fill_vs_open_R"] = side * (e - o[i0]) / dd  # live fill vs the next bar's open (+ = paid up)
        out["fill_vs_bar_R"] = side * (e - c[i0 - 1]) / dd if i0 > 0 else np.nan  # vs the entry minute's close
        out["mins_after_signal"] = (r.entry_time - r.signal_time).total_seconds() / 60
        for name, (kind, kw) in VARIANTS.items():
            kw = dict(kw)
            if kind == "now":
                res = run(o, h, l, c, i0, side, e, dd, td, end, **kw)
            elif kind == "wait":
                k = i0 + kw["n"]
                res = run(o, h, l, c, k, side, o[k], dd, td, end) if k < end else (0.0, "none", k, 0.0)
            elif kind == "opp":
                res = run(o, h, l, c, i0, -side, e, dd, td, end)
            else:
                lim = vwap[i0 - 1] if kind == "vwap" else e - side * kw["k"] * dd
                if kind == "vwap" and side * (lim - e) >= 0:
                    lim = e  # VWAP on the far side: limit is marketable, fills at the entry
                fill = None
                for k in range(i0, min(end, i0 + 30)):
                    if side * ((l[k] if side > 0 else h[k]) - lim) <= -0.01:  # must trade through by 1c (queue)
                        fill = k; break
                if fill is None:
                    res = (0.0, "nofill", i0, 0.0)
                else:  # fill at the limit (or the open if it gapped through), path from the next bar
                    px = o[fill] if side * (o[fill] - lim) <= 0 else lim
                    res = run(o, h, l, c, fill + 1, side, px, dd, td, end) if fill + 1 < end else (0.0, "none", fill, 0.0)
            out[f"R_{name}"] = res[0]
            if name == "base":
                out["sim_kind"], out["sim_mfe"], out["sim_bars"] = res[1], res[3], res[2] - i0 + 1
        rows.append(out)
F = pd.DataFrame(rows).set_index("i")
t = t.join(F)
t.to_parquet(S / "feat.parquet", index=False)
print(len(t), t.R_base.notna().sum(), "simulated")
print("live vs sim baseline corr", t[["R", "R_base"]].corr().iloc[0, 1], "mean live", t.R.mean(), "sim", t.R_base.mean())
