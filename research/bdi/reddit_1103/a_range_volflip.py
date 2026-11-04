"""reddit_1103 A: range-low volume-flip long with a "magnet" target (r/Daytrading 1xn4wdn). PLAN.md section A was
written before this ran. 1-minute SIP cache resampled to 5 minutes; the locked block 2024-11-01..2025-02-28 and the
old holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any computation. Costs 1c + 1 bp per side,
entry x gates.tod_cost_mult(entry time), target exits free, +2c on stops. Next-bar-open entries, stop first.
Usage: python a_range_volflip.py > a_out.txt   Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set

N_STUDY = 11
SPLIT = pd.Timestamp("2025-08-31").date()


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "adv20"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~bad_day(D.date)].sort_values(["symbol", "date"])
pc = D.groupby("symbol").close.shift(1)
tr = np.maximum(D.high, pc) - np.minimum(D.low, pc)
D["atr14"] = tr.groupby(D.symbol).transform(lambda x: x.rolling(14).mean().shift(1))
D["adv_prev"] = D.groupby("symbol").adv20.shift(1)
REG = G.session_regimes(D[["date", "open", "close"]])
spy = D[D.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DTYPE = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ETF = etf_set()
S = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna()]
top = S.sort_values("adv_prev", ascending=False).groupby("date").head(250)
top = top[~GD._blackout(top.symbol.to_numpy(), top.date.to_numpy())]
pick = {}
for s, d, a in zip(top.symbol, top.date, top.atr14):
    pick.setdefault(s, {})[d] = a
NSESS = top.date.nunique()
print(f"universe symbols {len(pick)}, symbol-days {len(top)}, sessions {NSESS}", flush=True)
store = BarStore(ROOT / "data/cache_hist")
rng = np.random.default_rng(20261103)


def cost(e, kind, tod):
    c = (G.SLIP_PS + e * G.SLIP_BPS) * float(G.tod_cost_mult([tod])[0])
    if kind != "tgt":
        c += G.SLIP_PS + e * G.SLIP_BPS
    if kind == "stop":
        c += G.STOP_EXTRA
    return c


def sim(o, h, l, c, j0, end, e, R, tgt, ex):
    """Long from the open of bar j0; returns (net $ per share before the entry cost, exit kinds). Exits through bar end."""
    stop = e - R
    if ex == "E2":
        for j in range(j0, end + 1):
            if j > j0 and o[j] <= stop:
                return o[j] - e - cost(o[j], "stop", 0) + cost(o[j], "tgt", 0), "stop"
            if l[j] <= stop:
                return stop - e - (cost(stop, "stop", 0) - cost(stop, "tgt", 0)), "stop"
            if h[j] >= tgt:
                return tgt - e, "tgt"
        x = c[end]
        return x - e - (cost(x, "time", 0) - cost(x, "tgt", 0)), "time"
    # E1: half at +1R, rest stop to breakeven, rest target = tgt
    half = False; pnl = 0.0
    for j in range(j0, end + 1):
        if j > j0 and o[j] <= stop:
            x = o[j]; k = 1.0 if not half else 0.5
            return pnl + k * (x - e - (cost(x, "stop", 0) - cost(x, "tgt", 0))), "stop" if not half else "half_be"
        if l[j] <= stop:
            k = 1.0 if not half else 0.5
            return pnl + k * (stop - e - (cost(stop, "stop", 0) - cost(stop, "tgt", 0))), "stop" if not half else "half_be"
        if not half and h[j] >= e + R:
            half = True; pnl += 0.5 * R; stop = e
            if h[j] >= tgt:
                return pnl + 0.5 * (tgt - e), "tgt"
            continue
        if half and h[j] >= tgt:
            return pnl + 0.5 * (tgt - e), "tgt"
    x = c[end]; k = 0.5 if half else 1.0
    return pnl + k * (x - e - (cost(x, "time", 0) - cost(x, "tgt", 0))), "time" if not half else "half_time"


CFG = [(ctx, m, ex) for ctx in ("none", "quiet") for m in (1.2, 1.5) for ex in ("E1", "E2")]
T = {k: [] for k in CFG}
done = 0
for s, days in pick.items():
    m1 = store.load(s)
    if m1.empty:
        continue
    m1 = m1[~bad_day(m1.index.strftime("%Y-%m-%d"))]
    m1 = m1.between_time("09:30", "15:59")
    if m1.empty:
        continue
    m5 = m1.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    dd = m5.index.date
    keep = np.array([x in days for x in dd])
    m5 = m5[keep]
    if m5.empty:
        continue
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()   # bar start
    o, h, l, c, v = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    g = pd.Series(dd)
    hod = pd.Series(h).groupby(g).cummax().to_numpy(); lod = pd.Series(l).groupby(g).cummin().to_numpy()
    bear = c < o; bull = c > o
    body_ok = (c - o) >= 0.5 * (h - l)
    same2 = np.r_[[False, False], dd[2:] == dd[:-2]]
    b1 = np.r_[False, bear[:-1]]; b2 = np.r_[[False, False], bear[:-2]]
    key = np.maximum(np.r_[np.nan, v[:-1]], np.r_[[np.nan, np.nan], v[:-2]])
    rngsf = hod - lod
    loc = (l - lod) <= 0.30 * rngsf
    # bar i closes at tod+5: closes 10:00..14:55 -> start 955..1450
    base = same2 & b1 & b2 & bull & body_ok & loc & (rngsf > 0) & (tod >= 955) & (tod <= 1450)
    atr = np.array([days[x] for x in dd])
    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70:
            continue
        end = w[-1]  # 15:55 bar, exit at its close
        bw = w[base[w]]
        if not len(bw):
            continue
        for ctx in ("none", "quiet"):
            for mm in (1.2, 1.5):
                cand = bw[(v[bw] >= mm * key[bw])]
                if ctx == "quiet":
                    cand = cand[rngsf[cand] <= 0.75 * atr[cand]]
                if not len(cand):
                    continue
                i = cand[0]
                if i + 1 > end:
                    continue
                e = o[i + 1]; R = e - (min(l[i - 2], l[i - 1], l[i]) - 0.01)
                if R < 0.001 * e:
                    continue
                seg = np.arange(w[0], i + 1)
                bseg = seg[bull[seg]]
                mag = h[bseg[np.argmax(v[bseg])]] if len(bseg) else np.nan
                if not (mag >= e + R):
                    mag = hod[i] if hod[i] >= e + R else e + R
                pool = w[(tod[w] >= 1005) & (tod[w] <= 1500)]
                for ex in ("E1", "E2"):
                    p, kind = sim(o, h, l, c, i + 1, end, e, R, mag, ex)
                    rr = (p - cost(e, "tgt", tod[i + 1])) / R
                    ctl = []
                    for jx in rng.choice(pool, size=min(3, len(pool)), replace=False):
                        ej = o[jx]; tj = max(mag, ej + R)
                        pj, _ = sim(o, h, l, c, jx, end, ej, R, tj, ex)
                        ctl.append((pj - cost(ej, "tgt", tod[jx])) / R)
                    T[(ctx, mm, ex)].append((d0, s, int(tod[i + 1]), rr, float(np.mean(ctl)), R / e * 100, kind, mag >= hod[i] - 1e-9))
    done += 1
    if done % 50 == 0:
        print("symbols", done, flush=True)

out = []
t90 = round(max(1.35, 0.9 * G.t_required(N_STUDY)), 2)
for k in CFG:
    t = pd.DataFrame(T[k], columns=["date", "symbol", "tod", "r", "ctrl", "Rpct", "kind", "mag_is_hod"])
    name = f"A-volflip-{k[0]}-m{k[1]:g}-{k[2]}"
    s_ = G.summary(t); rg = G.regime_split(t, REG)
    trn, val = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
    mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    exs = G.summary(pd.DataFrame({"date": t.date, "r": t.r - t.ctrl}))
    day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax()
    dt = t.groupby(t.date.map(DTYPE)).r.agg(["mean", "size"])
    row = dict(config=name, n=s_["n"], per_session=round(s_["n"] / NSESS, 2), win=s_["win_rate"], exp_r=s_["exp_r"], t=s_["t"],
               wo_best_day=s_["ex_best_day"], best_share=round(day.loc[b, "sum"] / day["sum"].sum(), 3) if day["sum"].sum() > 0 else np.nan,
               train=trn.get("exp_r"), valid=val.get("exp_r"), up=rg["up"].get("exp_r"), down=rg["down"].get("exp_r"), regime_pass=rg["pass"],
               spy_up=round(dt["mean"].get("up", np.nan), 3), spy_down=round(dt["mean"].get("down", np.nan), 3), spy_quiet=round(dt["mean"].get("quiet", np.nan), 3),
               n_spy_quiet=int(dt["size"].get("quiet", 0)), wf_pos=round(float((mo > 0).mean()), 3), months=len(mo),
               ctrl=round(float(t.ctrl.mean()), 4), excess=exs["exp_r"], excess_t=exs["t"], med_R_pct=round(float(t.Rpct.median()), 3),
               stop_share=round(float((t.kind == "stop").mean()), 3), tgt_share=round(float((t.kind == "tgt").mean()), 3))
    row["bar90_pass"] = bool((row["t"] or -9) >= t90 and row["wf_pos"] >= 0.54 and rg["pass"] and (row["excess"] or -1) > 0
                             and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0)
    out.append(row)
O = pd.DataFrame(out)
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
print(O.to_string(index=False))
O.to_csv(Path(__file__).with_name("a_results.csv"), index=False)
print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": G.t_required(N_STUDY), "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
print("Educational only - not financial advice.")
