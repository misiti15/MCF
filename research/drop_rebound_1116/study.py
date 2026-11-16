"""Drop-and-rebound study (owner 2026-11-16): SPY falls >= 0.65% in the first hour, then rebounds >= 0.5% off the low.

Scan (2 years of SPY/QQQ 1-minute bars), forward index returns after the rebound trigger vs the same minute on all
days, and a pre-declared trade grid (SPXL / TQQQ / SPY x 2 stops x 3 exits, + a liquid-stock top-5 variant) with costs
in and random-entry controls on the same days. Locked block 2024-11-01..2025-02-28 never read. TRAIN <= 2025-12-31,
VALID 2026. No entry before 09:50 (owner 2026-11-14). Configs counted, bar = max(1.5, sqrt(2 ln N)).
Usage: MCF_ROOT=/home/user/MCF python research/drop_rebound_1116/study.py <recent_bars.parquet>
Educational only - not financial advice.
"""
import sys, os, json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("MCF_ROOT", HERE.parents[1]))
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TRAIN_END = pd.Timestamp("2025-12-31").date()
LAST_FULL = pd.Timestamp("2026-11-13").date()
M0 = 570
ETFS = ["SPY", "QQQ", "SPXL", "TQQQ"]
DROP, REB = 0.0065, 0.005
FIRST_HOUR_END = 59        # drop must be reached on a bar starting by 10:29
DEC_FROM, DEC_TO = 19, 149  # decision = close of bar 09:49 (09:50) .. 11:59 (12:00)
HOR = [30, 60, 90, "1555"]
RNG = np.random.default_rng(11162)


def hm(i):                                    # bar index -> clock time of its close
    m = M0 + i + 1
    return f"{m // 60:02d}:{m % 60:02d}"


def load_sym(s, rec):
    d = pd.read_parquet(ROOT / "data/cache_hist/1Min" / f"{s}.parquet")
    d.index = d.index.tz_convert("America/New_York")
    if rec is not None:
        r = rec[rec.symbol == s].set_index("ts")[["open", "high", "low", "close", "volume"]]
        r.index = r.index.tz_convert("America/New_York")
        d = pd.concat([d, r[r.index > d.index.max()]])
    mm = d.index.hour * 60 + d.index.minute
    return d[(mm >= M0) & (mm < 960)]


def to_grid(d, min_bars=380, days=None):
    g = {}
    for day, x in d.groupby(d.index.date):
        if LOCK[0] <= day <= LOCK[1] or day > LAST_FULL or (days is not None and day not in days):
            continue
        if len(x) < min_bars:
            continue
        m = (x.index.hour * 60 + x.index.minute - M0).values
        a = np.full((390, 5), np.nan)
        a[m] = x[["open", "high", "low", "close", "volume"]].values
        v = np.nan_to_num(a[:, 4])
        a = pd.DataFrame(a).ffill().bfill().to_numpy(copy=True)
        a[:, 4] = v
        g[day] = a
    return g


def daily_atr(G):
    """ATR(14) known before the open: mean true range of the 14 prior grid sessions, only if those sit within 30
    calendar days (so nothing straddles the locked block)."""
    days = sorted(G)
    tr, out = [], {}
    for k, d in enumerate(days):
        a = G[d]
        h, l, c = a[:, 1].max(), a[:, 2].min(), a[-1, 3]
        pc = G[days[k - 1]][-1, 3] if k else np.nan
        tr.append(max(h - l, abs(h - pc), abs(l - pc)) if k else h - l)
        if k >= 14 and (d - days[k - 14]).days <= 30:
            out[d] = float(np.mean(tr[k - 14:k]))
    return out


def find_signal(a, from_open=False):
    """Causal drop-rebound trigger on one SPY session grid. Returns dict or None (drop info even without trigger)."""
    o, h, l, c = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    ref = np.full(390, o[0]) if from_open else np.maximum.accumulate(h)
    dd = 1 - l / ref
    hit = np.nonzero(dd[:FIRST_HOUR_END + 1] >= DROP)[0]
    maxdd = float(dd[:FIRST_HOUR_END + 1].max())
    if not len(hit):
        return dict(drop=False, maxdd=maxdd)
    di = int(hit[0])
    peak = 0 if from_open else int(np.argmax(h[:di + 1]))
    out = dict(drop=True, maxdd=maxdd, drop_i=di, peak_i=peak, trig_i=None)
    pre950 = False
    for i in range(di, DEC_TO + 1):
        L = l[peak:i + 1].min()
        if c[i] >= L * (1 + REB):
            if i < DEC_FROM:
                pre950 = True
                continue                     # rebound already done before 09:50: first allowed decision is 09:50
            out.update(trig_i=i, low=float(L), low_i=peak + int(np.argmin(l[peak:i + 1])), pre950=pre950)
            break
    return out


def fwd(a, e, h):
    ex = 384 if h == "1555" else min(e + h, 384)
    return (a[ex, 3] / a[e, 3] - 1) * 1e4


def trade(L, e, stop, exit_kind):
    """Long L (one session grid) at the close of bar e. Returns (R after costs, stopped) or None."""
    ent = L[e, 3]
    risk = ent - stop
    if not risk > 0:
        return None
    ex_i = 384 if exit_kind in ("1555", "trail") else min(e + 90, 384)
    st, hh = stop, ent
    for i in range(e + 1, ex_i + 1):
        if L[i, 2] <= st:
            px = min(st, L[i, 0])
            cost = 0.02 + 1e-4 * (ent + px) + 0.02
            return (px - ent - cost) / risk, True
        if exit_kind == "trail":
            hh = max(hh, L[i, 1])
            st = max(st, hh - risk)          # 1R chandelier trail, updated after the bar (no look-ahead)
    px = L[ex_i, 3]
    return (px - ent - 0.02 - 1e-4 * (ent + px)) / risk, False


LEV = {"SPY": 1, "SPXL": 3, "TQQQ": 3}


def stop_for(L, e, kind, atr):
    ent = L[e, 3]
    if kind == "low":                         # below the traded instrument's own low since 09:30, 5 bp x leverage buffer
        return L[:e + 1, 2].min() * (1 - 0.0005)
    return ent - atr if atr and np.isfinite(atr) else np.nan   # 1 x daily ATR(14)


def stats(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n == 0:
        return dict(n=0)
    srt = np.sort(x)[::-1]
    tot = x.sum()
    return dict(n=n, avgR=round(x.mean(), 3), win=round((x > 0).mean(), 3),
                t=round(x.mean() / (x.std(ddof=1) / math.sqrt(n)), 2) if n > 2 else None,
                worst=round(x.min(), 2), best=round(x.max(), 2),
                avgR_wo_best=round(srt[1:].mean(), 3) if n > 1 else None,
                best_share=round(srt[0] / tot, 2) if tot > 0 else None)


def main():
    rec = pd.read_parquet(sys.argv[1]) if len(sys.argv) > 1 else None
    G = {s: to_grid(load_sym(s, rec), 380 if s in ("SPY", "QQQ") else 150) for s in ETFS}
    days = sorted(set(G["SPY"]) & set(G["QQQ"]))
    split = {d: "TRAIN" if d <= TRAIN_END else "VALID" for d in days}
    ATR = {s: daily_atr(G[s]) for s in ("SPY", "SPXL", "TQQQ")}
    print(len(days), days[0], days[-1])

    # ---------------- scan ----------------
    rows = []
    for d in days:
        a = G["SPY"][d]
        for defn, fo in (("from_runhigh", False), ("from_open", True)):
            s = find_signal(a, fo)
            r = dict(day=d, split=split[d], defn=defn, drop=s["drop"], maxdd_pct=round(100 * s["maxdd"], 3))
            if s["drop"]:
                r.update(drop_time=hm(s["drop_i"]), peak_time=hm(s["peak_i"] - 1) if s["peak_i"] else "09:30")
            if s.get("trig_i") is not None:
                e = s["trig_i"]
                r.update(trig=True, trig_i=e, trig_time=hm(e), low=s["low"], low_time=f"{(M0 + s['low_i']) // 60:02d}:{(M0 + s['low_i']) % 60:02d}",  # bar start
                         low_i=s["low_i"], rebound_before_950=s["pre950"],
                         **{f"{sym}_{h}": fwd(G[sym][d], e, h) for sym in ("SPY", "QQQ") for h in HOR})
            else:
                r.update(trig=False)
            rows.append(r)
    S = pd.DataFrame(rows)
    S.to_csv(HERE / "scan_days.csv", index=False)

    # same-minute all-days null for each trigger minute
    null = {(sym, h): np.array([[fwd(G[sym][d], e, h) for e in range(DEC_FROM, DEC_TO + 1)] for d in days])
            for sym in ("SPY", "QQQ") for h in HOR}
    dpos = {d: k for k, d in enumerate(days)}
    cells = []
    for defn in ("from_runhigh", "from_open"):
        T = S[(S.defn == defn) & S.trig]
        for sym in ("SPY", "QQQ"):
            for h in HOR:
                for sp in ("TRAIN", "VALID", "ALL"):
                    x = T if sp == "ALL" else T[T.split == sp]
                    keep = [k for k, d in enumerate(days) if sp == "ALL" or split[d] == sp]
                    nm = null[(sym, h)][keep].mean(axis=0)
                    r = x[f"{sym}_{h}"].to_numpy()
                    base = np.array([nm[int(e) - DEC_FROM] for e in x.trig_i])
                    ex = r - base
                    n = len(r)
                    cells.append(dict(defn=defn, sym=sym, h=str(h), split=sp, n=n, mean_bps=round(r.mean(), 2),
                                      up=round((r > 0).mean(), 3), null_same_minute_bps=round(base.mean(), 2),
                                      excess_bps=round(ex.mean(), 2),
                                      t=round(ex.mean() / (ex.std(ddof=1) / math.sqrt(n)), 2) if n > 2 else None))
    C = pd.DataFrame(cells)
    C.to_csv(HERE / "fwd_cells.csv", index=False)

    # frequency summary
    freq = {}
    for defn in ("from_runhigh", "from_open"):
        x = S[S.defn == defn]
        for sp in ("TRAIN", "VALID", "ALL"):
            y = x if sp == "ALL" else x[x.split == sp]
            t_ = y[y.trig]
            freq[f"{defn}_{sp}"] = dict(sessions=len(y), drop_days=int(y["drop"].sum()), trig_days=int(len(t_)),
                                        drop_share=round(y["drop"].mean(), 3), trig_share=round(len(t_) / len(y), 3),
                                        trig_given_drop=round(len(t_) / max(y["drop"].sum(), 1), 3),
                                        rebound_before_950=int(t_.rebound_before_950.sum()) if len(t_) else 0,
                                        low_after_1030=int((t_.low_i >= 60).sum()) if len(t_) else 0,
                                        med_low_time=sorted(t_.low_time)[len(t_) // 2] if len(t_) else None,
                                        med_trig_time=sorted(t_.trig_time)[len(t_) // 2] if len(t_) else None)
    print(json.dumps(freq, indent=1))

    # ---------------- ETF trade grid (primary definition) ----------------
    T = S[(S.defn == "from_runhigh") & S.trig].copy()
    sig_days = list(T.day)
    tr_rows, ctl_rows = [], []
    for _, r in T.iterrows():
        d, e = r.day, int(r.trig_i)
        for inst in ("SPXL", "TQQQ", "SPY"):
            if d not in G[inst]:
                continue
            L = G[inst][d]
            for sk in ("low", "atr"):
                for xk in ("1555", "90", "trail"):
                    st = stop_for(L, e, sk, ATR[inst].get(d))
                    if not np.isfinite(st):
                        continue
                    o = trade(L, e, st, xk)
                    if o is None:
                        continue
                    tr_rows.append(dict(day=d, split=r.split, inst=inst, stop=sk, exit=xk, R=o[0], stopped=o[1],
                                        trig_time=r.trig_time, risk_pct=round(100 * (L[e, 3] - st) / L[e, 3], 2)))
                    # random-entry control: same day, same rules, 20 random decision bars 09:50-12:00
                    cs = []
                    for ee in RNG.integers(DEC_FROM, DEC_TO + 1, 20):
                        st2 = stop_for(L, int(ee), sk, ATR[inst].get(d))
                        o2 = trade(L, int(ee), st2, xk) if np.isfinite(st2) else None
                        if o2 is not None:
                            cs.append(o2[0])
                    ctl_rows.append(dict(day=d, split=r.split, inst=inst, stop=sk, exit=xk, R=np.mean(cs)))
    TR = pd.DataFrame(tr_rows); CT = pd.DataFrame(ctl_rows)
    TR.to_csv(HERE / "trades_etf.csv", index=False)
    grid_rows = []
    for (inst, sk, xk), g in TR.groupby(["inst", "stop", "exit"]):
        c = CT[(CT.inst == inst) & (CT.stop == sk) & (CT.exit == xk)]
        row = dict(config=f"{inst}|stop={sk}|exit={xk}", inst=inst, stop=sk, exit=xk,
                   med_risk_pct=float(g.risk_pct.median()), stop_rate=round(g.stopped.mean(), 3))
        for sp in ("TRAIN", "VALID", "ALL"):
            x = g if sp == "ALL" else g[g.split == sp]
            cc = c if sp == "ALL" else c[c.split == sp]
            st_ = stats(x.R)
            row.update({f"{k}_{sp}": v for k, v in st_.items()})
            row[f"random_avgR_{sp}"] = round(cc.R.mean(), 3)
        grid_rows.append(row)
    GR = pd.DataFrame(grid_rows)
    GR.to_csv(HERE / "trade_grid.csv", index=False)
    print(GR[["config", "n_ALL", "avgR_TRAIN", "avgR_VALID", "avgR_ALL", "t_ALL", "avgR_wo_best_ALL", "worst_ALL",
              "random_avgR_ALL", "win_ALL"]].to_string())
    json.dump(dict(sessions=len(days), first=str(days[0]), last=str(days[-1]), freq=freq),
              open(HERE / "summary.json", "w"), indent=1, default=str)
    T.to_csv(HERE / "signal_days.csv", index=False)


if __name__ == "__main__":
    main()
