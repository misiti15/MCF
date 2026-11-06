"""reddit_1106 A (PLAN.md was written before this ran).
A: low-volume pullback day, then a volume-confirmed 15-minute EMA20 bounce, long (r/Daytrading 1xpp3mz).
Harness copied from research/bdi/reddit_1105/ab_tests.py.
1-minute SIP cache (rebuilt 2026-11-04, research/bdi/1104/DATA.md) resampled to 5 minutes; the locked block
2024-11-01..2025-02-28 and the old holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any computation.
Costs 1c + 1 bp per side, entry x gates.tod_cost_mult, target exits free, +2c on stops. Next-bar-open entries, stop
first, gaps through stops fill at the open.
Usage: python a_tests.py > a_out.txt   Educational only - not financial advice."""
import json, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set

N_STUDY = 8
SPLIT = pd.Timestamp("2025-08-31").date()
CFG = [("A", ctx, v, m) for ctx in ("on", "off") for v in (1.5, 2.0) for m in (1.5, 2.0)]


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "volume", "adv20"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~bad_day(D.date)].sort_values(["symbol", "date"])
# prior close from the raw daily table is only valid when the previous row is the previous session; dropped blocks
# make gaps, so prior close is taken from consecutive rows and rows right after a dropped block are skipped below.
pc = D.groupby("symbol").close.shift(1)
D["pc"] = pc
D["prev_date"] = D.groupby("symbol").date.shift(1)
tr = np.maximum(D.high, pc) - np.minimum(D.low, pc)
D["atr14"] = tr.groupby(D.symbol).transform(lambda x: x.rolling(14).mean().shift(1))
D["adv_prev"] = D.groupby("symbol").adv20.shift(1)
g = D.groupby("symbol")
ema20 = g.close.transform(lambda x: x.ewm(span=20, adjust=False).mean())
D["ctx"] = ((g.close.shift(2) > g.open.shift(2)) & (g.close.shift(2) > g.close.shift(3)) & (g.close.shift(1) < g.open.shift(1))
            & (g.volume.shift(1) <= 0.75 * g.volume.shift(2)) & (g.close.shift(1) > ema20.groupby(D.symbol).shift(1))
            & ((pd.to_datetime(D.date) - pd.to_datetime(g.date.shift(3))).dt.days <= 7))
REG = G.session_regimes(D[["date", "open", "close"]])
spy = D[D.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DTYPE = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ETF = etf_set()
S = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna() & D.pc.notna()]
S = S[(pd.to_datetime(S.date) - pd.to_datetime(S.prev_date)).dt.days <= 5]
top = S.sort_values("adv_prev", ascending=False).groupby("date").head(250)
top = top[~GD._blackout(top.symbol.to_numpy(), top.date.to_numpy())]
PICK = {}
for s, d, a, p, cx in zip(top.symbol, top.date, top.atr14, top.pc, top.ctx):
    PICK.setdefault(s, {})[d] = (a, p, bool(cx))
NSESS = top.date.nunique()


def cost(e, kind, tod):
    c = (G.SLIP_PS + e * G.SLIP_BPS) * float(G.tod_cost_mult([tod])[0])
    if kind != "tgt":
        c += G.SLIP_PS + e * G.SLIP_BPS
    if kind == "stop":
        c += G.STOP_EXTRA
    return c


def sim(o, h, l, c, j0, end, e, R, tgt, sgn):
    """Entry at the open of bar j0 (sgn +1 long / -1 short); net $/share before the entry cost; stop first."""
    stop = e - sgn * R
    for j in range(j0, end + 1):
        if j > j0 and sgn * (o[j] - stop) <= 0:
            return sgn * (o[j] - e) - (cost(o[j], "stop", 0) - cost(o[j], "tgt", 0)), "stop"
        if (l[j] <= stop) if sgn > 0 else (h[j] >= stop):
            return sgn * (stop - e) - (cost(stop, "stop", 0) - cost(stop, "tgt", 0)), "stop"
        if tgt is not None and ((h[j] >= tgt) if sgn > 0 else (l[j] <= tgt)):
            return sgn * (tgt - e), "tgt"
    x = c[end]
    return sgn * (x - e) - (cost(x, "time", 0) - cost(x, "tgt", 0)), "time"



def one(s):
    days = PICK[s]
    out = {k: [] for k in CFG}
    m1 = BarStore(ROOT / "data/cache_hist").load(s)
    if m1.empty:
        return out
    m1 = m1[~bad_day(m1.index.strftime("%Y-%m-%d"))].between_time("09:30", "15:59")
    if m1.empty:
        return out
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    q = m1.resample("15min", label="left", closed="left").agg(agg).dropna()
    q["ema"] = q.close.ewm(span=20, adjust=False).mean()       # carried across sessions (chart EMA)
    q = q[np.array([x in days for x in q.index.date])]
    m5 = m1.resample("5min", label="left", closed="left").agg(agg).dropna()
    m5 = m5[np.array([x in days for x in m5.index.date])]
    if m5.empty or q.empty:
        return out
    rng = np.random.default_rng(zlib.crc32(s.encode()) ^ 20261106)
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()
    o, h, l, c = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    qd = q.index.date; qt = (q.index.hour * 100 + q.index.minute).to_numpy()
    qo, qh, ql, qc, qv, qe = (q[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume", "ema"))
    pos5 = {t: i for i, t in enumerate(m5.index)}

    def ctrl(w, end, lo, hi, R, mult):
        pool = w[(tod[w] >= lo) & (tod[w] <= hi)]
        if len(pool) == 0:
            return np.nan
        res = []
        for jx in rng.choice(pool, size=min(3, len(pool)), replace=False):
            ej = o[jx]
            pj, _ = sim(o, h, l, c, jx, end, ej, R, ej + mult * R, 1)
            res.append((pj - cost(ej, "tgt", tod[jx])) / R)
        return float(np.mean(res))

    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70 or tod[w[0]] != 930:
            continue
        atr, pcl, cx = days[d0]; end = w[-1]
        wq = np.flatnonzero(qd == d0)
        if len(wq) < 20 or qt[wq[0]] != 930:
            continue
        for v in (1.5, 2.0):
            sig = None
            for k in wq[1:]:
                if qt[k] < 945:
                    continue
                if qt[k] > 1415:                 # bar closes 10:00..14:30
                    break
                if k < 4:
                    continue
                if (ql[k] <= qe[k] + 0.05 * atr and qc[k] > qe[k] and qc[k] > qo[k] and qc[k - 1] < qo[k - 1]
                        and qv[k] >= v * qv[k - 1] and qe[k] > qe[k - 4]):
                    sig = k; break
            if sig is None:
                continue
            ts = q.index[sig] + pd.Timedelta(minutes=15)
            j0 = pos5.get(ts)
            if j0 is None or dd[j0] != d0:
                continue
            e = o[j0]; R = e - (ql[sig] - 0.01)
            if not (R >= 0.001 * e and R <= 1.0 * atr):
                continue
            for m in (1.5, 2.0):
                p, kind = sim(o, h, l, c, j0, end, e, R, e + m * R, 1)
                rr = (p - cost(e, "tgt", tod[j0])) / R
                row = (d0, s, int(tod[j0]), rr, ctrl(w, end, 1005, 1445, R, m), R / e * 100, kind)
                out[("A", "off", v, m)].append(row)
                if cx:
                    out[("A", "on", v, m)].append(row)
    return out


def name(k):
    return f"A-ctx{k[1]}-v{k[2]:g}-m{k[3]:g}"


def main():
    print(f"universe symbols {len(PICK)}, symbol-days {len(top)}, sessions {NSESS}", flush=True)
    T = {k: [] for k in CFG}
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(one, sorted(PICK), chunksize=4)):
            for k in CFG:
                T[k].extend(r[k])
            if n % 100 == 0:
                print("symbols", n, flush=True)
    cols = ["date", "symbol", "tod", "r", "ctrl", "Rpct", "kind"]
    out = []
    t90 = round(max(1.35, 0.9 * G.t_required(N_STUDY)), 2); tfull = G.t_required(N_STUDY)
    for k in CFG:
        t = pd.DataFrame(T[k], columns=cols).dropna(subset=["ctrl"])
        s_ = G.summary(t); rg = G.regime_split(t, REG)
        trn, val = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
        mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
        exs = G.summary(pd.DataFrame({"date": t.date, "r": t.r - t.ctrl}))
        day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax()
        dt = t.groupby(t.date.map(DTYPE)).r.agg(["mean", "size"])
        row = dict(config=name(k), n=s_["n"], per_session=round(s_["n"] / NSESS, 2), win=s_["win_rate"], exp_r=s_["exp_r"], t=s_["t"],
                   wo_best_day=s_["ex_best_day"], best_share=round(day.loc[b, "sum"] / day["sum"].sum(), 3) if day["sum"].sum() > 0 else np.nan,
                   train=trn.get("exp_r"), train_t=trn.get("t"), valid=val.get("exp_r"), valid_t=val.get("t"),
                   up=rg["up"].get("exp_r"), down=rg["down"].get("exp_r"), regime_pass=rg["pass"],
                   spy_up=round(dt["mean"].get("up", np.nan), 3), spy_down=round(dt["mean"].get("down", np.nan), 3), spy_quiet=round(dt["mean"].get("quiet", np.nan), 3),
                   n_up=int(dt["size"].get("up", 0)), n_down=int(dt["size"].get("down", 0)), n_quiet=int(dt["size"].get("quiet", 0)),
                   wf_pos=round(float((mo > 0).mean()), 3), months=len(mo),
                   ctrl=round(float(t.ctrl.mean()), 4), excess=exs["exp_r"], excess_t=exs["t"], med_R_pct=round(float(t.Rpct.median()), 3),
                   stop_share=round(float((t.kind == "stop").mean()), 3), tgt_share=round(float((t.kind == "tgt").mean()), 3))
        row["bar90_pass"] = bool((row["t"] or -9) >= t90 and row["wf_pos"] >= 0.54 and rg["pass"] and (row["excess"] or -1) > 0
                                 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0)
        row["full_bar_pass"] = bool(row["bar90_pass"] and row["t"] >= tfull)
        out.append(row)
    O = pd.DataFrame(out)
    pd.set_option("display.width", 400); pd.set_option("display.max_columns", 50)
    print(O.to_string(index=False))
    O.to_csv(Path(__file__).with_name("a_results.csv"), index=False)
    print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": G.t_required(N_STUDY), "pass_bar90": int(O.bar90_pass.sum()), "pass_full": int(O.full_bar_pass.sum()), "best_t": float(O.t.max())}))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
