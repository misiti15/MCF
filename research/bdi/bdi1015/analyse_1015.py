"""BDI 2026-10-15 step 1: every real trade of Primary, Testing 1 and Testing 2 (S6 excluded), reusing
research/bdi/nightly1015/trades.csv (806 trades, MFE/MAE to exit already there) and the nightly's SIP 1-minute bars.
Educational only - not financial advice.  Usage: python analyse_1015.py <bars_dir>

Per trade: rule values at entry (recomputed from the 1-minute bars known BEFORE the entry minute), MFE/MAE to the
real exit and to 15:55, minutes to the best price, and what-if exits on the 1-minute path from the entry minute to
15:55 (stop-first inside a bar, costs in: 1c + 1 bps per side, free target side, +2c on stops):
  base   - the trade's own stop/target (re-simulated; checks the simulator against the journal)
  be05   - stop to breakeven once +0.5R was printed
  tr05   - trail 0.5R behind the best price once +0.5R was printed (target kept)
  t05 / t1 - target 0.5R / 1R, own stop
  eod    - own stop, no target, flat 15:55
  sar    - base, and if it stopped: reverse at the stop price, 1R stop / 1R target, flat 15:55 (second round trip costed)
  reent  - base, and if it stopped: re-enter the same side when price trades back through the entry within 60 min,
           same stop distance and target (second round trip costed)
  opp    - the opposite side from the entry minute, 1R stop / 1R target, flat 15:55
Hindsight check for opp: "pointer" = a rule known at entry that points to the opposite side: QQQ fromOpen at entry
is >= 0.25% against the trade's side AND the stock is on the far side of its own VWAP. Scored on all 806 trades.
Loss type: the nightly1012/ltype.py classifier, unchanged. Losers are merged into research/bdi/patterns.csv.
"""
import sys
import numpy as np
import pandas as pd

BARS = sys.argv[1]
OUT = "research/bdi/bdi1015"
DAY = "2026-10-15"
EOD = pd.Timestamp(f"{DAY} 15:55", tz="America/New_York")
T = pd.read_csv("research/bdi/nightly1015/trades.csv")
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert("America/New_York")
cache = {}


def bars(s):
    if s not in cache:
        b = pd.read_parquet(f"{BARS}/{s}.parquet")
        b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
        cache[s] = b.between_time("09:30", "15:59")
    return cache[s]


def rsi(x, n):
    d = np.diff(x)
    if len(d) < n:
        return np.nan
    d = d[-n:]
    up, dn = d[d > 0].sum(), -d[d < 0].sum()
    return 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)


def ctx(sym, t):
    b = bars(sym)
    pre = b[b.index < t.floor("min")]
    if pre.empty:
        return dict(fo=np.nan, vw=np.nan, rsi5=np.nan, bp=np.nan)
    o = b.open.iloc[0]
    tp = (pre.high + pre.low + pre.close) / 3
    vw = (tp * pre.volume).cumsum().iloc[-1] / max(pre.volume.sum(), 1)
    c5 = pre.close.resample("5min").last().dropna().to_numpy()
    last = pre.tail(95)
    sgn = np.sign(last.close - last.open)
    bp = float((sgn * last.volume).sum() / max(last.volume.sum(), 1))
    return dict(fo=(pre.close.iloc[-1] / o - 1) * 100, vw=(pre.close.iloc[-1] / vw - 1) * 100, rsi5=rsi(c5, 5), bp=bp)


def cost(px, kind_exit):
    c = 0.01 + px * 1e-4
    if kind_exit != "target":
        c += 0.01 + px * 1e-4
    if kind_exit == "stop":
        c += 0.02
    return c


def sim(path, side, px, stop, tgt, be=None, trail=None):
    """path: DataFrame of 1-min bars after entry (to 15:55). Returns (exit_px, kind, exit_ts)."""
    best = px
    st = stop
    for ts, x in zip(path.index, path.itertuples()):
        if side == 1:
            if x.low <= st:
                return (min(st, x.open) if x.open < st else st), ("stop" if st != px else "be"), ts
            if tgt is not None and x.high >= tgt:
                return tgt, "target", ts
            best = max(best, x.high)
        else:
            if x.high >= st:
                return (max(st, x.open) if x.open > st else st), ("stop" if st != px else "be"), ts
            if tgt is not None and x.low <= tgt:
                return tgt, "target", ts
            best = min(best, x.low)
        R = abs(px - stop)
        if be is not None and side * (best - px) >= be * R:
            st = px if side * (px - st) > 0 else st
        if trail is not None and side * (best - px) >= trail * R:
            nst = best - side * trail * R
            st = max(st, nst) if side == 1 else min(st, nst)
    if path.empty:
        return px, "flat", None
    return path.close.iloc[-1], "flat", path.index[-1]


def rr(side, px, ex, kind, R):
    return (side * (ex - px) - cost(px, "stop" if kind in ("stop", "be") else kind)) / R


qc = {s: bars(s) for s in ("QQQ", "IWM", "SPY")}
rows, pat = [], []
for r in T.itertuples():
    b = bars(r.symbol)
    side, px, R = int(r.side), float(r.entry), abs(r.entry - r.stop)
    tgt = float(r.target) if r.target == r.target else None
    path = b[(b.index >= r.nt.floor("min")) & (b.index <= EOD)]
    c = ctx(r.symbol, r.nt)
    q = ctx("QQQ", r.nt)
    iw = ctx("IWM", r.nt)
    out = dict(id=r.id, acct=r.acct, setup=r.strategy, symbol=r.symbol, side=side, entry_t=r.nt.strftime("%H:%M"),
               r=r.r_multiple, pnl=r.pnl, exit_reason=r.exit_reason, mfe=r.mfe, mae=r.mae, refire=r.refire,
               setup_seq=r.setup_seq, lot_no=r.lot_no, fo=c["fo"], vwap=c["vw"], rsi5_5m=c["rsi5"], bp95=c["bp"],
               qqq_fo=q["fo"], iwm_fo=iw["fo"], spread_bps=None)
    try:
        import json
        out["spread_bps"] = json.loads(str(r.meta).split(";")[0]).get("spread_bps")
    except Exception:
        pass
    if R <= 0 or path.empty:
        rows.append(out); continue
    hi, lo = path.high.to_numpy(), path.low.to_numpy()
    fav = (hi - px) if side == 1 else (px - lo)
    adv = (px - lo) if side == 1 else (hi - px)
    out["mfe_eod"], out["mae_eod"] = fav.max() / R, adv.max() / R
    held = path[path.index <= r.et.floor("min")]
    if len(held):
        fh = (held.high - px) if side == 1 else (px - held.low)
        out["min_to_best"] = (fh.idxmax() - r.nt.floor("min")).total_seconds() / 60
    ex, k, ts = sim(path, side, px, r.stop, tgt)
    out["w_base"] = rr(side, px, ex, k, R); out["w_base_kind"] = k
    for nm, kw in (("w_be05", dict(be=0.5)), ("w_tr05", dict(trail=0.5)), ("w_t05", dict(t=0.5)), ("w_t1", dict(t=1.0)), ("w_eod", dict(t=None))):
        if "t" in kw:
            tt = None if kw["t"] is None else px + side * kw["t"] * R
            e2, k2, _ = sim(path, side, px, r.stop, tt)
        else:
            e2, k2, _ = sim(path, side, px, r.stop, tgt, **kw)
        out[nm] = rr(side, px, e2, k2, R)
    # stop-and-reverse and re-entry after a stop
    out["w_sar"] = out["w_base"]; out["w_reent"] = out["w_base"]; out["sar_leg"] = np.nan; out["reent_leg"] = np.nan
    if k == "stop" and ts is not None:
        after = path[path.index > ts]
        sp = float(r.stop)
        e3, k3, _ = sim(after, -side, sp, sp + side * R, sp - side * R)
        out["sar_leg"] = rr(-side, sp, e3, k3, R); out["w_sar"] = out["w_base"] + out["sar_leg"]
        win = after[after.index <= ts + pd.Timedelta(minutes=60)]
        hit = win[(win.high >= px) if side == 1 else (win.low <= px)]
        if len(hit):
            t0 = hit.index[0]
            e4, k4, _ = sim(after[after.index > t0], side, px, px - side * R, tgt)
            out["reent_leg"] = rr(side, px, e4, k4, R); out["w_reent"] = out["w_base"] + out["reent_leg"]
    e5, k5, _ = sim(path, -side, px, px + side * R, px - side * R)
    out["w_opp"] = rr(-side, px, e5, k5, R)
    out["pointer"] = bool(q["fo"] == q["fo"] and (-side) * q["fo"] >= 0.25 and (-side) * c["vw"] > 0)
    # loss type (nightly1012 classifier)
    if r.pnl < 0:
        opp_first = "target" if out["w_opp"] > 0.5 else "x"
        post = path[path.index > r.et.floor("min")]
        mfe = r.mfe if r.mfe == r.mfe else 0.0
        rev = r.exit_reason == "stop" and tgt is not None and len(post) and ((post.high.max() >= tgt) if side == 1 else (post.low.min() <= tgt))
        if rev: lt = "stopped_then_reversed"
        elif abs(c["fo"]) >= 3 and opp_first == "target": lt = "wrong_side_after_big_swing"
        elif mfe >= 0.5: lt = "gave_back_gains"
        elif r.exit_reason == "flatten": lt = "late_hold"
        elif mfe < 0.15: lt = "never_worked"
        else: lt = "small MFE then failed (0.15-0.5R)"
        out["loss_type"] = lt
        nm = {"p": "primary", "t1": "testing", "t2": "testing2"}[r.acct]
        pat.append(f"{DAY},{nm},{r.symbol},{r.strategy},{'long' if side == 1 else 'short'},{lt},bdi1015 analysis; r {r.r_multiple:.2f}; mfe {mfe:.2f}; lot {r.lot_no}; sar {out['sar_leg'] if out['sar_leg'] == out['sar_leg'] else 'na'}")
    rows.append(out)

A = pd.DataFrame(rows)
A.to_csv(f"{OUT}/trades_analysis_1015.csv", index=False, float_format="%.4f")
P = open("research/bdi/patterns.csv").read().rstrip("\n").split("\n")
P = [p for p in P if not p.startswith(f"{DAY},")]
open("research/bdi/patterns.csv", "w").write("\n".join(P + pat) + "\n")
print(len(A), "trades;", len(pat), "loser rows merged")
W = ["r", "w_base", "w_be05", "w_tr05", "w_t05", "w_t1", "w_eod", "w_sar", "w_reent", "w_opp"]
pd.set_option("display.width", 250)
g = A.groupby(["acct", "setup"]).agg(n=("id", "size"), **{w: (w, "mean") for w in W}).round(3)
g.to_csv(f"{OUT}/per_setup_1015.csv")
print(A.groupby("acct")[W].mean().round(3).to_string())
print(A.groupby(["acct"]).apply(lambda d: pd.Series({"sim_vs_journal_r_corr": d.r.corr(d.w_base), "stops": (d.w_base_kind == "stop").sum()})).round(3))
print("hindsight pointer: opp R when pointer / not:", A.groupby("pointer").w_opp.agg(["size", "mean"]).round(3).to_string())
print(A.groupby(["acct", "pointer"]).w_opp.agg(["size", "mean"]).round(3).to_string())
L = A[A.pnl < 0]
print(L.groupby(["acct", "loss_type"]).size().unstack(fill_value=0).to_string())
