"""BDI 2026-10-15 Part B (PLAN.md): index dip-bounce with the drop measured from the PRIOR CLOSE (PC) and the
gap-down + early-low variant (GL), vs the live open-based IDX setups. 80 configurations, pre-declared.
Production fill model (mcf.backtest.engine.simulate) and config costs. The rule-19 locked block
2024-11-01..2025-02-28 is excluded at read time (pyarrow filter) - no locked row is ever loaded.
Writes pcdip_trades.csv, pcdip_results.csv, pcdip_counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ["MCF_ACCOUNT"] = "testing"
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mcf.backtest.engine import Costs, simulate  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.strategies.base import DayContext, Signal, t  # noqa: E402
from mcf.strategies.index_dip import IndexDipBounce  # noqa: E402

OUT = ROOT / "research" / "bdi" / "bdi1015"
H = ROOT / "data" / "cache_hist" / "1Min"
TZ = "America/New_York"
LOCK = (date(2024, 11, 1), date(2025, 2, 28))
HOLDOUTS = [(date(2026, 4, 1), date(2026, 6, 30)), (date(2026, 9, 16), date(2026, 10, 7))]
H2_START = date(2025, 9, 1)
SEED = 20261015

cfg = load_config()
COST = Costs.from_cfg(cfg["costs"])
FLAT = t(cfg["session"]["flatten_by"])
CANDS = ["SPXL", "UPRO"]


def sample(d):
    if LOCK[0] <= d <= LOCK[1]:
        raise RuntimeError("locked date reached the study")
    return "HOLDOUT" if any(a <= d <= b for a, b in HOLDOUTS) else "DEV"


def load(sym):
    """{date: RTH bars} and {date: prior session close}; locked rows filtered out inside the parquet reader."""
    a = pd.Timestamp(LOCK[0], tz=TZ)
    b = pd.Timestamp(LOCK[1], tz=TZ) + pd.Timedelta(days=1)
    col = "__index_level_0__"
    df = pd.read_parquet(H / f"{sym}.parquet", filters=[[(col, "<", a)], [(col, ">=", b)]])
    assert not ((df.index >= a) & (df.index < b)).any()
    df = df.between_time("09:30", "15:59")
    days = {d: g for d, g in df.groupby(df.index.date)}
    ds = sorted(days)
    pc = {}
    for i in range(1, len(ds)):
        prev, cur = ds[i - 1], ds[i]
        if prev < LOCK[0] <= cur:          # prior session is inside the locked block (2025-03-03): skip
            continue
        pc[cur] = float(days[prev]["close"].iloc[-1])
    return days, pc


SYMS = ["SPY", "QQQ", "TQQQ", *CANDS]
DATA, PC = {}, {}
for s in SYMS:
    DATA[s], PC[s] = load(s)


def end_times(idx):
    return np.array((idx.index + pd.Timedelta(minutes=1)).time)


def trigger(ib, ref, fam, thr, dip_by, rec=0.20, lo_w=t("09:50"), hi_w=t("10:05")):
    """First trigger on the signal bars `ib` with reference `ref` (prior close). fam 'pc': running low <= ref*(1-thr%)
    by dip_by; fam 'gl': open <= ref*(1-thr%) and running low <= open*(1-0.10%) by dip_by. Causal."""
    if ib is None or len(ib) < 380 or not ref:
        return None
    o = float(ib.open.iloc[0])
    lows, closes = ib.low.to_numpy(float), ib.close.to_numpy(float)
    rl = np.minimum.accumulate(lows)
    et = end_times(ib)
    dip_by = t(dip_by)
    if fam == "pc":
        ok = (rl <= ref * (1 - thr / 100)) & (et <= dip_by)
    elif fam == "gl":
        if o > ref * (1 - thr / 100):
            return None
        ok = (rl <= o * (1 - 0.0010)) & (et <= dip_by)
    elif fam == "open":                     # the live open-based version (check only; production class used below)
        ok = (rl <= o * (1 - thr / 100)) & (et <= dip_by)
        ref = o
    else:
        raise ValueError(fam)
    if not ok.any():
        return None
    for i in range(int(np.argmax(ok)), len(ib)):
        if et[i] > hi_w:
            break
        if et[i] < lo_w:
            continue
        if closes[i] >= rl[i] + rec * (ref - rl[i]):
            return {"i": i, "ts": ib.index[i], "low": float(rl[i]), "drop_pct": (rl[i] / ref - 1) * 100,
                    "gap_pct": (o / ref - 1) * 100}
    return None


def pick(d, ts):
    dv = {c: float((lambda s: (s.close * s.volume).sum())(DATA[c][d][DATA[c][d].index <= ts])) for c in CANDS}
    best = max(dv.values())
    return (next(c for c in CANDS if dv[c] == best) if best > 0 else None), dv


def pc_signal(sym, bars, k, ref, exit_kind, meta=None):
    """Long at bar k's close decision: stop = running low - 0.10 x (traded prior close - running low)."""
    if k < 0 or k >= len(bars):
        return None
    seg = bars.iloc[: k + 1]
    lo, px = float(seg.low.min()), float(seg.close.iloc[-1])
    drop = ref - lo
    if not (drop > 0 and px > lo):
        return None
    sig = Signal(sym, "pcdip", 1, k, lo - 0.10 * drop, None, "market", meta=meta or {})
    if exit_kind == "TRAIL":
        sig.trail_r, sig.trail_after_r = 1.0, 1.0
    return sig


def run(sig, bars):
    tr = simulate(sig, bars, FLAT, COST)
    if tr is None:
        return None
    return {"R": tr.r_multiple, "bps": (tr.exit / tr.entry - 1) * 1e4, "reason": tr.exit_reason,
            "entry_time": f"{tr.entry_time:%H:%M}", "exit_time": f"{tr.exit_time:%H:%M}"}


FAMS = []
for sig_sym in ("SPY", "QQQ"):
    for d in (0.5, 0.75, 1.0):
        for by in ("09:45", "09:55"):
            FAMS.append(("pc", sig_sym, d, by))
    for g in (0.3, 0.5):
        for by in ("09:45", "09:55"):
            FAMS.append(("gl", sig_sym, g, by))
EXITS = ("TRAIL", "HOLD")
INSTR = ("3x", "index")
N_NEW = len(FAMS) * len(EXITS) * len(INSTR)
assert N_NEW == 80

trades = []
sig_days = sorted(set(DATA["SPY"]) & set(DATA["QQQ"]))
for fam, ss, thr, by in FAMS:
    for d in sig_days:
        ib = DATA[ss][d]
        tg = trigger(ib, PC[ss].get(d), fam, thr, by)
        if tg is None:
            continue
        for inst in INSTR:
            if inst == "index":
                sym = ss
                dv = {}
            elif ss == "QQQ":
                sym, dv = "TQQQ", {}
            else:
                if any(d not in DATA[c] for c in CANDS):
                    continue
                sym, dv = pick(d, tg["ts"])
                if sym is None:
                    continue
            bars, ref = DATA[sym].get(d), PC[sym].get(d)
            if bars is None or not ref:
                continue
            k = int(bars.index.searchsorted(tg["ts"], side="right")) - 1
            for ex in EXITS:
                sig = pc_signal(sym, bars, k, ref, ex)
                if sig is None or (res := run(sig, bars)) is None:
                    continue
                trades.append({"fam": fam, "signal": ss, "thr": thr, "dip_by": by, "exit": ex, "instr": inst,
                               "symbol": sym, "date": d, "sample": sample(d), "trig": f"{tg['ts']:%H:%M}",
                               "idx_drop_pc": tg["drop_pct"], "idx_gap": tg["gap_pct"], **res})
T = pd.DataFrame(trades)

# ---- the live open-based setups, production class, same sessions (parity with idxdip1015/pick3x_results.csv)
OPEN = {"IDX5": ("SPY", 0.5, "09:45"), "IDX2": ("SPY", 0.75, "09:45"), "IDX3": ("SPY", 0.75, "09:55"),
        "IDX1": ("QQQ", 1.0, "09:55")}
otr = []
for nm, (ss, dp, by) in OPEN.items():
    for ex in EXITS:
        EP = dict(target=None, trail_r=1.0, trail_after_r=1.0) if ex == "TRAIL" else dict(target=None)
        base = dict(signal_symbol=ss, dip_pct=dp, dip_by=by, stop_buffer_frac=0.10, trigger="recovery",
                    recovery_frac=0.20, **EP)
        for inst in INSTR:
            if inst == "index":
                st, cand = IndexDipBounce(symbols=[ss], **base), [ss]
            elif ss == "QQQ":
                st, cand = IndexDipBounce(symbols=["TQQQ"], **base), ["TQQQ"]
            else:
                st, cand = IndexDipBounce(trade_candidates=CANDS, pick="max_dollar_volume", **base), CANDS
            for d in sig_days:
                if (ss == "SPY" and d not in PC["SPY"]) or (ss == "QQQ" and d not in PC["QQQ"]):
                    continue       # same session set as the PC rows (prior close available)
                ib = DATA[ss][d]
                if len(ib) < 380 or any(d not in DATA[c] for c in cand):
                    continue
                peers = {ss: ib, **{c: DATA[c][d] for c in cand}}
                for c in cand:
                    for sg in st.signals(DayContext(c, d, DATA[c][d], 1, 1, 1, 1, np.nan, peers=peers)):
                        if (res := run(sg, DATA[c][d])):
                            otr.append({"setup": nm, "signal": ss, "exit": ex, "instr": inst, "symbol": c, "date": d,
                                        "sample": sample(d), **res})
O = pd.DataFrame(otr)

# ---- rule-6 controls
rng = np.random.default_rng(SEED)
ctrl = []
for ss in ("SPY", "QQQ"):
    for d in sig_days:
        if sample(d) != "DEV" or d not in PC[ss]:
            continue
        ib = DATA[ss][d]
        if len(ib) < 380:
            continue
        w = np.flatnonzero((end_times(ib) >= t("09:50")) & (end_times(ib) <= t("10:05")))
        for kk in rng.choice(w, size=3):
            ts = ib.index[int(kk)]
            for inst in INSTR:
                sym = ss if inst == "index" else ("TQQQ" if ss == "QQQ" else (pick(d, ts)[0] if all(d in DATA[c] for c in CANDS) else None))
                if sym is None or d not in DATA[sym] or not PC[sym].get(d):
                    continue
                bars, ref = DATA[sym][d], PC[sym][d]
                k = int(bars.index.searchsorted(ts, side="right")) - 1
                if k < 0 or (ref - bars.low.iloc[: k + 1].min()) / ref < 0.0005:
                    continue
                for ex in EXITS:
                    sig = pc_signal(sym, bars, k, ref, ex)
                    if sig is not None and (res := run(sig, bars)):
                        ctrl.append({"signal": ss, "instr": inst, "exit": ex, "date": d, "R": res["R"]})
C = pd.DataFrame(ctrl).groupby(["signal", "instr", "exit", "date"]).R.mean().reset_index()


def same_day_ctrl(rows):
    """20 seeded random entry bars in the window on the row's trigger sessions, same geometry; per-day mean."""
    out = []
    for r in rows.itertuples():
        bars, ref = DATA[r.symbol][r.date], PC[r.symbol][r.date]
        w = np.flatnonzero((end_times(bars) >= t("09:50")) & (end_times(bars) <= t("10:05")))
        rs = []
        for kk in rng.choice(w, size=20):
            sig = pc_signal(r.symbol, bars, int(kk), ref, r.exit)
            if sig is not None and (res := run(sig, bars)):
                rs.append(res["R"])
        if rs:
            out.append(np.mean(rs))
    return float(np.mean(out)) if out else np.nan


def stats(r, dates):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return dict(n=0)
    sd = r.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, mean_R=r.mean(), t=r.mean() / sd * np.sqrt(n) if n > 1 and sd > 0 else np.nan, win=(r > 0).mean(),
                ex_best=np.delete(r, int(np.argmax(r))).mean() if n > 1 else np.nan, best_day=str(dates[int(np.argmax(r))]))


def mapped(fam, ss, thr, by):
    if ss == "QQQ":
        return "IDX1"
    if fam == "pc":
        return {(0.5, "09:45"): "IDX5", (0.75, "09:45"): "IDX2", (0.75, "09:55"): "IDX3"}.get((thr, by))
    return {"09:45": "IDX5", "09:55": "IDX3"}[by]


rows = []
for (fam, ss, thr, by, ex, inst), g in T.groupby(["fam", "signal", "thr", "dip_by", "exit", "instr"]):
    dev = g[g["sample"] == "DEV"].sort_values("date")
    s = stats(dev.R.to_numpy(), dev.date.to_numpy())
    m = mapped(fam, ss, thr, by)
    od = O[(O.setup == m) & (O.exit == ex) & (O.instr == inst) & (O["sample"] == "DEV")] if m else O.iloc[:0]
    so = stats(od.R.to_numpy(), od.date.to_numpy())
    inc = dev[~dev.date.isin(set(od.date))]
    both = dev[dev.date.isin(set(od.date))]
    c = C[(C.signal == ss) & (C.instr == inst) & (C.exit == ex)]
    rows.append({"fam": fam, "signal": ss, "thr": thr, "dip_by": by, "exit": ex, "instr": inst, **s,
                 "H1_n": int((dev.date < H2_START).sum()), "H1_R": dev[dev.date < H2_START].R.mean(),
                 "H2_n": int((dev.date >= H2_START).sum()), "H2_R": dev[dev.date >= H2_START].R.mean(),
                 "mapped": m, "open_n": so.get("n", 0), "open_R": so.get("mean_R"), "open_t": so.get("t"),
                 "overlap_n": len(both), "incr_n": len(inc), "incr_R": inc.R.mean() if len(inc) else np.nan,
                 "ctrl_all_R": c.R.mean(), "ctrl_all_n": len(c), "ctrl_same_R": same_day_ctrl(dev),
                 "picked": ",".join(f"{k}:{v}" for k, v in dev.symbol.value_counts().items())})
Rz = pd.DataFrame(rows)

# ---- pre-declared choice rule (PLAN.md), evaluated on the main instrument rows (3x; exit TRAIL, or HOLD for QQQ)
def neighbours_ok(r):
    if r.fam != "pc":
        alt = Rz[(Rz.fam == "gl") & (Rz.signal == r.signal) & (Rz.dip_by == r.dip_by) & (Rz.exit == r.exit) & (Rz.instr == r.instr) & (Rz.thr != r.thr)]
    else:
        ths = [0.5, 0.75, 1.0]
        i = ths.index(r.thr)
        adj = [ths[j] for j in (i - 1, i + 1) if 0 <= j < 3]
        alt = Rz[(Rz.fam == "pc") & (Rz.signal == r.signal) & (Rz.dip_by == r.dip_by) & (Rz.exit == r.exit) & (Rz.instr == r.instr) & (Rz.thr.isin(adj))]
    return bool(len(alt) and (alt.mean_R > 0).all())


Rz["main_row"] = (Rz.instr == "3x") & (((Rz.signal == "SPY") & (Rz.exit == "TRAIL")) | (Rz.signal == "QQQ"))
Rz["plateau"] = [neighbours_ok(r) for r in Rz.itertuples()]
Rz["as_good"] = (Rz.main_row & Rz.mapped.notna() & (Rz.mean_R >= Rz.open_R) & (Rz.t >= Rz.open_t)
                 & (Rz.incr_R > 0) & (Rz.mean_R > Rz.ctrl_all_R) & Rz.plateau & (Rz.n >= 3))
LIN = 1134 + N_NEW
BAR = max(1.5, float(np.sqrt(2 * np.log(LIN))))
Rz["bar_t"] = BAR
Rz["bar_met"] = Rz.t >= BAR
# holdout: scored once, only for rows that pass the choice rule
Rz["holdout_n"], Rz["holdout_R"] = np.nan, np.nan
for i, r in Rz[Rz.as_good].iterrows():
    h = T[(T.fam == r.fam) & (T.signal == r.signal) & (T.thr == r.thr) & (T.dip_by == r.dip_by) & (T.exit == r.exit)
          & (T.instr == r.instr) & (T["sample"] == "HOLDOUT")]
    Rz.loc[i, "holdout_n"], Rz.loc[i, "holdout_R"] = len(h), h.R.mean() if len(h) else np.nan

T[T["sample"] == "DEV"].to_csv(OUT / "pcdip_trades_dev.csv", index=False)
O[O["sample"] == "DEV"].to_csv(OUT / "pcdip_open_trades_dev.csv", index=False)
Rz.round(4).to_csv(OUT / "pcdip_results.csv", index=False)
osum = O[O["sample"] == "DEV"].groupby(["setup", "exit", "instr"]).R.agg(["size", "mean"]).round(4)
json.dump({"N_new_configs": N_NEW, "N_lineage": LIN, "bar_t": BAR, "seed": SEED,
           "dev_sessions": int(sum(1 for d in sig_days if sample(d) == "DEV")),
           "open_based_dev": {f"{a}|{b}|{c}": {"n": int(v["size"]), "mean_R": float(v["mean"])} for (a, b, c), v in osum.iterrows()}},
          open(OUT / "pcdip_counts.json", "w"), indent=1)
pd.set_option("display.width", 260)
pd.set_option("display.max_rows", 200)
print(osum.to_string())
cols = ["fam", "signal", "thr", "dip_by", "exit", "instr", "n", "mean_R", "t", "win", "ex_best", "H1_n", "H1_R", "H2_n", "H2_R",
        "mapped", "open_n", "open_R", "open_t", "incr_n", "incr_R", "ctrl_all_R", "ctrl_same_R", "plateau", "as_good",
        "holdout_n", "holdout_R"]
print(Rz[cols].round(3).to_string())
print("N new", N_NEW, "lineage", LIN, "bar", round(BAR, 3))
