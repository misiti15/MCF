"""reddit_1102 B: 1-minute VWAP bounce in the 15-minute trend on the day's 6 highest-volume mega caps, 09:45-11:30
(r/Trading 1xjucpo). PLAN.md section B was written before this ran. 1-minute SIP cache (data/cache_hist/1Min): the
locked block 2024-11-01..2025-02-28 and the old holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any
computation. Costs 1c + 1 bp per side, entry x gates.tod_cost_mult(bar close), target exit free, +2c on stops.
Usage: python b_vwap_bounce_1m.py > b_out.txt   Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close", "adv20"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~bad_day(D.date)]
REG = G.session_regimes(D[["date", "open", "close"]])
ETF = etf_set()
S = D[~D.symbol.isin(ETF) & D.adv20.notna()]
S = S[S.adv20.rank(ascending=False) > 0]
top30 = S.sort_values("adv20", ascending=False).groupby("date").head(30)
cand = {d: set(g.symbol) for d, g in top30.groupby("date")}
syms = sorted(set(top30.symbol))
store = BarStore(ROOT / "data/cache_hist")
print(f"candidate symbols {len(syms)}, sessions {len(cand)}")

rows = {}
for s in syms:
    m = store.load(s)
    if m.empty:
        continue
    m = m[~bad_day(m.index.strftime("%Y-%m-%d"))]
    m = m.between_time("09:30", "15:59")
    if m.empty:
        continue
    d = m.index.date
    tp = (m.high + m.low + m.close) / 3
    pv = (tp * m.volume).groupby(d).cumsum(); vv = m.volume.groupby(d).cumsum()
    vwap = (pv / vv.replace(0, np.nan)).to_numpy()
    q = m.close.resample("15min", label="left", closed="left").last().dropna()
    q = q[q.index.strftime("%H:%M") <= "15:45"]
    ema = q.ewm(span=20, adjust=False).mean()
    qe = pd.DataFrame({"c15": q.to_numpy(), "e15": ema.to_numpy()}, index=q.index + pd.Timedelta(minutes=15))  # known at bar end
    # for each 1-min bar (start t, close t+1), the last 15-min bar that ended <= t+1 (same day)
    tclose = m.index + pd.Timedelta(minutes=1)
    j = qe.index.searchsorted(tclose, side="right") - 1
    ok = j >= 0
    jj = np.where(ok, j, 0)
    same = ok & (qe.index[jj].date == d)
    c15 = np.where(same, qe.c15.to_numpy()[jj], np.nan); e15 = np.where(same, qe.e15.to_numpy()[jj], np.nan)
    hhmm = (m.index.hour * 100 + m.index.minute).to_numpy()
    # VWAP of the last completed 15-min bar's end ~ use current vwap (trend vs VWAP at signal time)
    rows[s] = dict(idx=m.index, d=d, hhmm=hhmm, o=m.open.to_numpy(), h=m.high.to_numpy(), l=m.low.to_numpy(),
                   c=m.close.to_numpy(), v=m.volume.to_numpy(), vwap=vwap, c15=c15, e15=e15)

# today's top 6 by 09:30-09:44 dollar volume among the 30 candidates
dv = []
for s, r in rows.items():
    k = (r["hhmm"] >= 930) & (r["hhmm"] <= 944)
    x = pd.Series(r["c"][k] * r["v"][k]).groupby(np.asarray(r["d"])[k]).sum()
    dv.append(pd.DataFrame({"symbol": s, "date": x.index, "dv": x.to_numpy()}))
DV = pd.concat(dv)
DV = DV[[s in cand.get(d, ()) for s, d in zip(DV.symbol, DV.date)]]
DV = DV[~GD._blackout(DV.symbol.to_numpy(), DV.date.to_numpy())]
top6 = DV.sort_values("dv", ascending=False).groupby("date").head(6)
pick = {}
for s, d in zip(top6.symbol, top6.date):
    pick.setdefault(s, set()).add(d)
print(f"symbol-days traded universe {len(top6)} over {top6.date.nunique()} sessions")


def exit_r(r, i, end, side, e, R, tgt):
    """Walk 1-minute bars i+1..end; returns (gross R, kind). Stop first when a bar touches both."""
    for j in range(i + 1, end + 1):
        if side == "long":
            if r["l"][j] <= e - R:
                return -1.0, "stop"
            if tgt and r["h"][j] >= e + 2 * R:
                return 2.0, "tgt"
        else:
            if r["h"][j] >= e + R:
                return -1.0, "stop"
            if tgt and r["l"][j] <= e - 2 * R:
                return 2.0, "tgt"
    g = (r["c"][end] - e) / R if side == "long" else (e - r["c"][end]) / R
    return g, "time"


def cost_r(e, R, kind, hhmm_close):
    c = (G.SLIP_PS + e * G.SLIP_BPS) * float(G.tod_cost_mult([hhmm_close])[0])
    if kind != "tgt":
        c += G.SLIP_PS + e * G.SLIP_BPS
    if kind == "stop":
        c += G.STOP_EXTRA
    return c / R


rng = np.random.default_rng(20261102)
out, alltr = [], {}
for side in ("long", "short"):
    for V in (1.0, 1.5):
        for ex in ("t2r", "h1130"):
            T = []
            for s, days in pick.items():
                r = rows[s]
                c, o, h, l, v, vw = r["c"], r["o"], r["h"], r["l"], r["v"], r["vwap"]
                vm = pd.Series(v).shift(1).rolling(10).mean().to_numpy()
                d = np.asarray(r["d"]); hh = r["hhmm"]
                pc = np.r_[np.nan, c[:-1]]; pd_ = np.r_[[None], d[:-1]]
                with np.errstate(invalid="ignore"):
                    if side == "long":
                        sig = (r["c15"] > r["e15"]) & (r["c15"] > vw) & (l <= vw * 1.0005) & (c > vw) & (c > o) & (pc > vw) & (v >= V * vm)
                    else:
                        sig = (r["c15"] < r["e15"]) & (r["c15"] < vw) & (h >= vw * 0.9995) & (c < vw) & (c < o) & (pc < vw) & (v >= V * vm)
                sig &= (hh >= 944) & (hh <= 1128) & (pd_ == d)
                for dd in days:
                    w = np.flatnonzero(d == dd)
                    if not len(w):
                        continue
                    endi = w[hh[w] <= 1129]
                    if not len(endi):
                        continue
                    end = endi[-1]
                    si = w[sig[w]]
                    if not len(si):
                        continue
                    i = si[0]; e = c[i]
                    R = e - (l[i] - 0.01) if side == "long" else (h[i] + 0.01) - e
                    if R < 0.0005 * e:
                        continue
                    hc = hh[i] + 1 if (hh[i] % 100) != 59 else hh[i] + 41
                    g, kind = exit_r(r, i, end, side, e, R, ex == "t2r")
                    rr = g - cost_r(e, R, kind, hc)
                    # 5 same-symbol-day random controls, same side / $ R / exit
                    pool = w[(hh[w] >= 944) & (hh[w] <= 1128)]
                    ctl = []
                    for jx in rng.choice(pool, size=min(5, len(pool)), replace=False):
                        ej = c[jx]; hj = hh[jx] + 1 if (hh[jx] % 100) != 59 else hh[jx] + 41
                        gj, kj = exit_r(r, jx, end, side, ej, R, ex == "t2r")
                        ctl.append(gj - cost_r(ej, R, kj, hj))
                    T.append((dd, s, hh[i], rr, float(np.mean(ctl)), R / e * 100, kind))
            t = pd.DataFrame(T, columns=["date", "symbol", "hhmm", "r", "ctrl", "Rpct", "kind"])
            name = f"B-vwapbounce1m-{side}-v{V:g}-{ex}"
            alltr[name] = t
            s_ = G.summary(t); rg = G.regime_split(t, REG)
            SPLIT = pd.Timestamp("2025-08-31").date()
            tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
            mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
            ex_ = G.summary(pd.DataFrame({"date": t.date, "r": t.r - t.ctrl}))
            day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax()
            N = 20; t90 = round(max(1.35, 0.9 * G.t_required(N)), 2)
            row = dict(config=name, n=s_["n"], per_session=round(s_["n"] / top6.date.nunique(), 2), win=s_["win_rate"],
                       exp_r=s_["exp_r"], t=s_["t"], wo_best_day=s_["ex_best_day"],
                       best_share=round(day.loc[b, "sum"] / day["sum"].sum(), 3) if day["sum"].sum() > 0 else np.nan,
                       train=tr.get("exp_r"), valid=va.get("exp_r"), up=rg["up"].get("exp_r"), down=rg["down"].get("exp_r"),
                       regime_pass=rg["pass"], wf_pos=round(float((mo > 0).mean()), 3), months=len(mo),
                       ctrl_exp=round(float(t.ctrl.mean()), 4), excess=ex_["exp_r"], excess_t=ex_["t"],
                       med_R_pct=round(float(t.Rpct.median()), 3), stop_share=round(float((t.kind == "stop").mean()), 3))
            row["bar90_pass"] = bool((row["t"] or -9) >= t90 and row["wf_pos"] >= 0.54 and rg["pass"] and (row["excess"] or -1) > 0
                                     and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0)
            out.append(row)
            print(name, s_["n"], s_["exp_r"], s_["t"], flush=True)
O = pd.DataFrame(out)
pd.set_option("display.width", 280)
print(O.to_string(index=False))
O.to_csv(Path(__file__).with_name("b_results.csv"), index=False)
print(json.dumps({"configs": len(O), "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
print("Educational only - not financial advice.")
