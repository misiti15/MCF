"""2026-10-15 descriptive check (out of sample, one session): would the prior-close (PC/GL) rows and the live open-based
IDX setups have fired, and with what R? Trigger/stop logic copied verbatim from pcdip.py (trigger, pc_signal); the
open-based rows use the production class. Bars: the nightly's 10-15 SIP bars + 10-14 bars (fetch_prev.py).
Usage: python today1015.py <bars_1015_dir> <bars_1014_dir>. Educational only - not financial advice."""
import os, sys
os.environ["MCF_ACCOUNT"] = "testing"
sys.path.insert(0, "/home/user/MCF")
import numpy as np, pandas as pd
from datetime import date
from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.strategies.base import DayContext, Signal, t
from mcf.strategies.index_dip import IndexDipBounce

cfg = load_config(); COST = Costs.from_cfg(cfg["costs"]); FLAT = t(cfg["session"]["flatten_by"])
B, P = sys.argv[1], sys.argv[2]
def rd(d, s):
    b = pd.read_parquet(f"{d}/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    return b.between_time("09:30", "15:59")
SY = ["SPY", "QQQ", "SPXL", "UPRO", "TQQQ"]
D = {s: rd(B, s) for s in SY}; PC = {s: float(rd(P, s).close.iloc[-1]) for s in SY}
print("prior closes", PC, "opens", {s: float(D[s].open.iloc[0]) for s in SY})
def end_times(i): return np.array((i.index + pd.Timedelta(minutes=1)).time)
def trigger(ib, ref, fam, thr, dip_by, rec=0.20, lo_w=t("09:50"), hi_w=t("10:05")):
    o = float(ib.open.iloc[0]); lows, closes = ib.low.to_numpy(float), ib.close.to_numpy(float)
    rl = np.minimum.accumulate(lows); et = end_times(ib); dip_by = t(dip_by)
    if fam == "pc": ok = (rl <= ref * (1 - thr / 100)) & (et <= dip_by)
    else:
        if o > ref * (1 - thr / 100): return None
        ok = (rl <= o * (1 - 0.0010)) & (et <= dip_by)
    if not ok.any(): return None
    for i in range(int(np.argmax(ok)), len(ib)):
        if et[i] > hi_w: break
        if et[i] < lo_w: continue
        if closes[i] >= rl[i] + rec * (ref - rl[i]): return {"i": i, "ts": ib.index[i], "drop": (rl[i] / ref - 1) * 100}
    return None
def pc_signal(sym, bars, k, ref, ex):
    seg = bars.iloc[: k + 1]; lo, px = float(seg.low.min()), float(seg.close.iloc[-1]); drop = ref - lo
    if not (drop > 0 and px > lo): return None
    s = Signal(sym, "pcdip", 1, k, lo - 0.10 * drop, None, "market")
    if ex == "TRAIL": s.trail_r, s.trail_after_r = 1.0, 1.0
    return s
rows = []
for fam, ss, thr, by in [("pc", "SPY", x, y) for x in (0.5, 0.75, 1.0) for y in ("09:45", "09:55")] + \
        [("pc", "QQQ", x, y) for x in (0.5, 0.75, 1.0) for y in ("09:45", "09:55")] + \
        [("gl", s, g, y) for s in ("SPY", "QQQ") for g in (0.3, 0.5) for y in ("09:45", "09:55")]:
    tg = trigger(D[ss], PC[ss], fam, thr, by)
    if tg is None:
        rows.append(dict(row=f"{fam} {ss} {thr} {by}", fired=False)); continue
    if ss == "QQQ": sym = "TQQQ"
    else:
        dv = {c: float((D[c][D[c].index <= tg["ts"]].close * D[c][D[c].index <= tg["ts"]].volume).sum()) for c in ("SPXL", "UPRO")}
        sym = max(dv, key=dv.get)
    k = int(D[sym].index.searchsorted(tg["ts"], side="right")) - 1
    for ex in ("TRAIL", "HOLD"):
        tr = simulate(pc_signal(sym, D[sym], k, PC[sym], ex), D[sym], FLAT, COST)
        rows.append(dict(row=f"{fam} {ss} {thr} {by}", fired=True, trig=f"{tg['ts']:%H:%M}", drop=round(tg["drop"], 3), sym=sym, exit=ex,
                         entry=tr.entry, stop=round(tr.stop, 2), exit_px=tr.exit, exit_t=f"{tr.exit_time:%H:%M}", reason=tr.exit_reason, R=round(tr.r_multiple, 3)))
for nm, ss, dp, by, cand in [("IDX5", "SPY", .5, "09:45", ["SPXL", "UPRO"]), ("IDX2", "SPY", .75, "09:45", ["SPXL", "UPRO"]),
                             ("IDX3", "SPY", .75, "09:55", ["SPXL", "UPRO"]), ("IDX1", "QQQ", 1.0, "09:55", ["TQQQ"])]:
    st = IndexDipBounce(trade_candidates=cand, pick="max_dollar_volume", signal_symbol=ss, dip_pct=dp, dip_by=by, stop_buffer_frac=0.1,
                        trigger="recovery", recovery_frac=0.2, target=None, trail_r=1.0, trail_after_r=1.0)
    sg = [x for c in cand for x in st.signals(DayContext(c, date(2026, 10, 15), D[c], 1, 1, 1, 1, np.nan, peers={ss: D[ss], **{c2: D[c2] for c2 in cand}}))]
    rows.append(dict(row=f"open-based {nm}", fired=bool(sg)))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string())
