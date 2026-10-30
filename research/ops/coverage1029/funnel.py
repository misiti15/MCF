"""Offline recompute of Primary's lab setups for one session, with the LIVE code (mcf.strategies.setups.LabStrategy:
its own 5-minute frame build heat_frame + extra_features over the PRIOR5_BARS warm-up, its module mask, its YAML window,
first-hit / refire selection), on the session's full SIP 1-minute bars. Every feature is causal, so the whole-day frame's
row i equals what live computed at decision bar i (mcf/replay/fast.py makes the same argument and checks it).

For every enabled lab setup of the day's freeze file (setups/<day>.json on origin/mcf-data) it writes
  - the funnel: universe -> universe_ok -> ADV >= min_adv -> each entry condition (cumulative, same bar, inside the
    window) -> symbols with a qualifying bar -> offline signals (first hit; refire chain for refire setups)
  - the same funnel for the symbols the earnings blackout removed (what the blackout cost)
  - parity vs the live journal (run 1): matched / missed by live / extra in live, keyed by (setup, symbol, decision bar)
Inputs from fetch.py. Usage: python funnel.py <scratch> <day>  -> <scratch>/out/<day>.json
Educational only - not financial advice."""
import json, pickle, sqlite3, sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, "/home/user/MCF")
from mcf.backtest.engine import universe_ok
from mcf.strategies import setups as SU
from mcf.strategies.base import DayContext
from mcf.strategies.setups import build_strategies, refire_select

S = Path(sys.argv[1]); D = sys.argv[2]
TZ = "America/New_York"


def prev(x):
    return np.r_[np.nan, x[:-1]]


def conds(name, f):
    """Named entry conditions whose AND is the module's mask (asserted below); window is applied separately."""
    c = lambda k: f[k].to_numpy(dtype=float)
    heat, bp, rsi, rsi5, gap, fo = c("heat"), c("buyPressure"), c("rsi"), c("rsi5"), c("gap"), c("fromOpen")
    tod = c("tod")
    with np.errstate(invalid="ignore"):
        if name.startswith("RW5"):
            return [("gap<0 (gapped down)", gap < 0), ("heat<=-30", heat <= -30), ("buyPressure<-0.15", bp < -0.15),
                    ("RSI5>80", rsi5 > 80)]
        if name.startswith("RW3"):
            return [("gap<0 (gapped down)", gap < 0), ("heat<=-20", heat <= -20), ("buyPressure<-0.35", bp < -0.35),
                    ("RSI5>80", rsi5 > 80)]
        if name.startswith("MF2"):
            return [("heat<=-30", heat <= -30), ("RSI14 55-65", (rsi >= 55) & (rsi <= 65)), ("buyPressure<-0.25", bp < -0.25)]
        if name == "MF4-h40-open-flowsell":
            return [("heat<=-40", (heat <= -30) & (np.abs(heat) >= 40)), ("buyPressure<-0.25", bp < -0.25),
                    ("module tod<11:00", (tod >= 950) & (tod < 1100))]
        if name.startswith("MF4"):
            return [("heat<=-40", (heat <= -30) & (np.abs(heat) >= 40)), ("buyPressure<-0.25", bp < -0.25)]
        if name.startswith("NS1"):
            return [("fromOpen>+2%", fo > 2), ("RSI14 crosses below 40", (rsi <= 40) & (prev(rsi) > 40)), ("RSI5>=80", rsi5 >= 80),
                    ("module 09:50-11:30", (tod >= 950) & (tod <= 1130))]
        if name.startswith("NS5"):
            s50 = c("sma50_dist_pct")
            return [("fromOpen<-2%", fo < -2), ("crosses below SMA50(5m)", (s50 < 0) & (prev(s50) >= 0)), ("RSI14<=30", rsi <= 30),
                    ("module 09:50-11:30", (tod >= 950) & (tod <= 1130))]
        if name.startswith("ST7"):
            return [("fromOpen<-1%", fo < -1), ("RSI14 crosses below 50", (rsi < 50) & (prev(rsi) >= 50)), ("RSI14<=30", rsi <= 30),
                    ("buyPressure>0", bp > 0)]
    return None


cfg = yaml.safe_load(open("/home/user/MCF/config/default.yaml"))
frz = json.loads((S / "p" / "setups" / f"{D}.json").read_text())
cfg["strategies"] = {k: v for k, v in frz["strategies"].items() if v.get("enabled") and v.get("type") == "lab"}
for k in ("universe", "live", "exits", "shorts"):
    if k in frz:
        cfg[k] = frz[k]
strats = build_strategies(cfg)
pri = pickle.loads((S / "days" / D / "priors.pkl").read_bytes())
bars = pd.read_parquet(S / "days" / D / "bars.parquet")
eb = json.loads((S / "p" / "earnings" / f"{D}.json").read_text())["symbols"] if (S / "p" / "earnings" / f"{D}.json").exists() else {}
day = pd.Timestamp(D).date()

rows = []         # per (setup, symbol): funnel flags
sigs = []         # offline signals
nsym = {"priors": len(pri), "with_bars": 0, "universe_ok": 0}
for sym, g in bars.groupby("symbol"):
    p = pri.get(sym)
    if p is None:
        continue
    b = g.drop(columns="symbol")
    nsym["with_bars"] += 1
    ctx = DayContext(symbol=sym, date=day, bars=b, prev_close=p.prev_close, prev_high=p.prev_high, prev_low=p.prev_low,
                     atr=p.atr, avg_dollar_volume=p.adv, avg_cum_volume=p.avg_cum, avg_move=p.avg_move,
                     prior5=getattr(p, "tail5", None), sma20=getattr(p, "sma20", float("nan")))
    if not universe_ok(ctx, cfg):
        continue
    nsym["universe_ok"] += 1
    blk = sym in eb
    f = None
    for st in strats:
        adv_ok = p.adv >= st.min_adv
        rec = {"setup": st.name, "symbol": sym, "blackout": blk, "adv_ok": bool(adv_ok)}
        rows.append(rec)
        if not adv_ok:
            continue
        if f is None:
            SU._LAB_FRAMES.clear(); SU._LAB_D5[:] = [None, None]
            st.generate(ctx)                                      # live frame build (cached by key)
            f = next(iter(SU._LAB_FRAMES.values()), None) if SU._LAB_FRAMES else None
            if f is None:
                break
        tod = f["tod"].to_numpy()
        lo, hi = st.window or (950, 1500)
        win = (tod >= max(950, lo)) & (tod <= min(1500, hi))
        mm = np.asarray(st.mod.mask(f), dtype=bool)
        cs = conds(st.name, f) or [("module mask", mm)]   # setups outside today's 8: one step
        cum = win.copy()
        for k, (lab, x) in enumerate(cs):
            cum = cum & np.nan_to_num(x, nan=0).astype(bool)
            rec[f"c{k}"] = bool(cum.any())
            rec[f"only{k}"] = bool((win & np.nan_to_num(x, nan=0).astype(bool)).any())
        assert np.array_equal(cum, mm & win), (st.name, sym)
        hit = np.flatnonzero(mm & win)
        rec["hit_bars"] = int(len(hit))
        sel = refire_select(hit, st.refire_cooldown) if st.refire else list(hit[:1])
        for i in sel:
            sigs.append({"setup": st.name, "symbol": sym, "blackout": blk, "bar": f"{(pd.Timestamp(f.index[i]).tz_convert(TZ) if pd.Timestamp(f.index[i]).tzinfo else pd.Timestamp(f.index[i])) + pd.Timedelta(minutes=4):%H%M}",   # live bar_time = the bucket's 4th-minute bar
                         "close": float(f['close'].iloc[i])})

R = pd.DataFrame(rows); G = pd.DataFrame(sigs, columns=["setup", "symbol", "blackout", "bar", "close"])
con = sqlite3.connect(S / "p" / "journal.db")
J = pd.read_sql("select ts, symbol, strategy setup, status, reason, bar_index, info from signals where day=? and run_id=1", con, params=(D,))
J["bar"] = [(json.loads(i or "{}").get("bar_time") or "") for i in J["info"]]
J["poll"] = J["ts"].str[11:16]
out = {"day": D, "symbols": nsym, "earnings_excluded": len(eb), "setups": {}}
for st in strats:
    r = R[R.setup == st.name]; cs = conds(st.name, pd.DataFrame({k: [0.0] for k in ("heat", "buyPressure", "rsi", "rsi5", "gap", "fromOpen", "tod", "sma50_dist_pct")})) or [("module mask", None)]
    labels = [c[0] for c in cs]
    def fun(x):
        d = {"universe_ok": int(len(x)), f"adv>={st.min_adv/1e6:.0f}M": int(x.adv_ok.sum())}
        for k, lab in enumerate(labels):
            d["+" + lab] = int(x.get(f"c{k}", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
        d["alone: " + " | ".join(labels)] = [int(x.get(f"only{k}", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) for k in range(len(labels))]
        d["qualifying symbol-bars"] = int(x.get("hit_bars", pd.Series(dtype=float)).fillna(0).sum())
        return d
    g = G[G.setup == st.name]
    live = J[J.setup == st.name]
    off = g[~g.blackout]
    k_off = set(zip(off.symbol, off.bar)); k_live = set(zip(live.symbol, live.bar))
    mins = lambda h: int(h[:2]) * 60 + int(h[2:])
    for so, bo in sorted(k_off - k_live):     # a missing 4th-minute bar: live decides the bucket on the next bar (<= 5 min later)
        late = [(sl, bl) for sl, bl in k_live - k_off if sl == so and 0 < mins(bl) - mins(bo) <= 5]
        if late:
            k_off.discard((so, bo)); k_off.add(late[0])
    out["setups"][st.name] = {
        "window": st.window, "refire": st.refire,
        "funnel_traded_universe": fun(r[~r.blackout]), "funnel_blackout_names": fun(r[r.blackout]),
        "offline_signals": int(len(off)), "offline_symbols": sorted(set(off.symbol)),
        "blackout_would_signal": sorted(set(g[g.blackout].symbol)),
        "live_signals": int(len(live)), "live_symbols": sorted(set(live.symbol)),
        "live_status": live.groupby(["status", "reason"]).size().rename("n").reset_index().to_dict("records"),
        "matched": len(k_off & k_live),
        "missed_by_live": sorted(k_off - k_live), "extra_in_live": sorted(k_live - k_off),
    }
(S / "out").mkdir(exist_ok=True)
(S / "out" / f"{D}.json").write_text(json.dumps(out, indent=1, default=str))
for k, v in out["setups"].items():
    print(k, "offline", v["offline_signals"], "live", v["live_signals"], "matched", v["matched"],
          "missed", v["missed_by_live"], "extra", v["extra_in_live"])
