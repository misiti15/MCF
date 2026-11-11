"""reddit_1110 G (PLAN.md was written before this ran). Harness copied from research/bdi/reddit_1109/ab_tests.py.
G: "grind with no real pullback" continuation, both sides (r/Daytrading 1xszib3).
1-minute SIP cache (rebuilt 2026-11-04) resampled to 5 minutes; the locked block 2024-11-01..2025-02-28 and the old
holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any computation. Costs 1c + 1 bp per side, entry x
gates.tod_cost_mult, target exits free, +2c on stops. Next-bar-open entries, stop first, gaps through stops fill at
the open.  Usage: python g_tests.py > g_out.txt   Educational only - not financial advice."""
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
CFG = [("G", side, Tc, E) for side in ("long", "short") for Tc in (1100, 1230) for E in (0.30, 0.45)]
MINR = 0.003


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "volume", "adv20"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~bad_day(D.date)].sort_values(["symbol", "date"]).reset_index(drop=True)
g = D.groupby("symbol")
pc = g.close.shift(1)
D["pc"] = pc
D["prev_date"] = g.date.shift(1)
tr = np.maximum(D.high, pc) - np.minimum(D.low, pc)
D["atr14"] = tr.groupby(D.symbol).transform(lambda x: x.rolling(14).mean().shift(1))
D["adv_prev"] = g.adv20.shift(1)
REG = G.session_regimes(D[["date", "open", "close"]])
spy = D[D.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DTYPE = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ETF = etf_set()
S_ = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna() & D.pc.notna()]
S_ = S_[(pd.to_datetime(S_.date) - pd.to_datetime(S_.prev_date)).dt.days <= 5]
top = S_.sort_values("adv_prev", ascending=False).groupby("date").head(250)
top = top[~GD._blackout(top.symbol.to_numpy(), top.date.to_numpy())]
PICK = {}
for s, d, a in zip(top.symbol, top.date, top.atr14):
    PICK.setdefault(s, {})[d] = a
NSESS = top.date.nunique()


def cost(e, kind, tod):
    c = (G.SLIP_PS + e * G.SLIP_BPS) * float(G.tod_cost_mult([tod])[0])
    if kind != "tgt":
        c += G.SLIP_PS + e * G.SLIP_BPS
    if kind == "stop":
        c += G.STOP_EXTRA
    return c


def sim(o, h, l, c, j0, end, e, R, tgt, sgn):
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
    m1 = m1[np.array([x in days for x in m1.index.date])]
    if m1.empty:
        return out
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    m5 = m1.resample("5min", label="left", closed="left").agg(agg).dropna()
    if m5.empty:
        return out
    rng = np.random.default_rng(zlib.crc32(s.encode()) ^ 20261110)
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()
    o, h, l, c, v = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))

    def run(j0, end, e, R, sgn):
        p, kind = sim(o, h, l, c, j0, end, e, R, None, sgn)
        return (p - cost(e, "tgt", tod[j0])) / R, kind

    def ctrl(w, end, R, sgn):
        pool = w[(tod[w] >= 1000) & (tod[w] <= 1430)]
        if len(pool) == 0:
            return np.nan
        return float(np.mean([run(jx, end, o[jx], R, sgn)[0] for jx in rng.choice(pool, size=min(3, len(pool)), replace=False)]))

    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70 or tod[w[0]] != 930:
            continue
        atr = days[d0]; end = w[-1]; op = o[w[0]]
        path = np.abs(np.diff(np.concatenate([[op], c[w]])))
        cum = np.cumsum(path)
        for Tc in (1100, 1230):
            bt = Tc - 45 if Tc % 100 == 0 else Tc - 5     # bar start: 10:55, 12:25
            ii = np.flatnonzero(tod[w] == bt)
            if len(ii) == 0:
                continue
            i = int(ii[0])
            if i + 1 >= len(w):
                continue
            mv = c[w[i]] - op
            er = abs(mv) / max(cum[i], 1e-9)
            for side, sgn in (("long", 1), ("short", -1)):
                if sgn * mv < 0.5 * atr:
                    continue
                hh, ll = h[w[:i + 1]], l[w[:i + 1]]
                if sgn > 0:
                    ext = hh.max() - op
                    retr = float(np.max(np.maximum.accumulate(hh) - ll))
                    near = c[w[i]] >= hh.max() - 0.25 * ext
                else:
                    ext = op - ll.min()
                    retr = float(np.max(hh - np.minimum.accumulate(ll)))
                    near = c[w[i]] <= ll.min() + 0.25 * ext
                if ext <= 0 or retr > 0.35 * ext or not near:
                    continue
                j0 = w[i + 1]; e = o[j0]
                st = (l[w[max(0, i - 5):i + 1]].min() - 0.01) if sgn > 0 else (h[w[max(0, i - 5):i + 1]].max() + 0.01)
                R = sgn * (e - st)
                if not (R >= MINR * e and R <= 1.5 * atr):
                    continue
                rr, kind = run(j0, end, e, R, sgn)
                cr = ctrl(w, end, R, sgn)
                for E in (0.30, 0.45):
                    if er >= E:
                        out[("G", side, Tc, E)].append((d0, s, int(tod[j0]), rr, cr, R / e * 100, kind))
    return out


def name(k):
    return f"G-{k[1]}-{k[2]}-E{k[3]:.2f}"


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
        if len(t) < 5:
            out.append(dict(config=name(k), n=len(t))); continue
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
    O.to_csv(Path(__file__).with_name("g_results.csv"), index=False)
    print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": tfull, "pass_bar90": int(O.get("bar90_pass", pd.Series(dtype=bool)).fillna(False).sum()),
                      "pass_full": int(O.get("full_bar_pass", pd.Series(dtype=bool)).fillna(False).sum()), "best_t": float(O.t.max())}))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
