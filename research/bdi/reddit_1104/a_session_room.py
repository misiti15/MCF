"""reddit_1104 A: morning-rally pullback long with a "session room" target check (r/Daytrading 1xnpo24 / r/Trading
1xo1lmv). PLAN.md section A was written before this ran. 1-minute SIP cache (rebuilt 2026-11-04, research/bdi/1104/
DATA.md) resampled to 5 minutes; the locked block 2024-11-01..2025-02-28 and the old holdouts (2026-04..06,
>= 2026-09-16) are dropped at load, before any computation. Costs 1c + 1 bp per side, entry x gates.tod_cost_mult,
target exits free, +2c on stops. Next-bar-open entries, stop first.
Usage: python a_session_room.py > a_out.txt   Educational only - not financial advice."""
import json, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set

N_STUDY = 6
SPLIT = pd.Timestamp("2025-08-31").date()
CFG = [(room, m) for room in ("none", 1.0, 1.25) for m in (1.5, 2.0)]


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


def sim(o, h, l, c, j0, end, e, R, tgt):
    """Long from the open of bar j0; net $/share before the entry cost; stop first; out at bar end's close."""
    stop = e - R
    for j in range(j0, end + 1):
        if j > j0 and o[j] <= stop:
            return o[j] - e - (cost(o[j], "stop", 0) - cost(o[j], "tgt", 0)), "stop"
        if l[j] <= stop:
            return stop - e - (cost(stop, "stop", 0) - cost(stop, "tgt", 0)), "stop"
        if h[j] >= tgt:
            return tgt - e, "tgt"
    x = c[end]
    return x - e - (cost(x, "time", 0) - cost(x, "tgt", 0)), "time"


def one(s):
    days = PICK[s]
    out = {k: [] for k in CFG}
    m1 = BarStore(ROOT / "data/cache_hist").load(s)
    if m1.empty:
        return out
    m1 = m1[~bad_day(m1.index.strftime("%Y-%m-%d"))].between_time("09:30", "15:59")
    if m1.empty:
        return out
    m5 = m1.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    m5 = m5[np.array([x in days for x in m5.index.date])]
    if m5.empty:
        return out
    rng = np.random.default_rng(zlib.crc32(s.encode()) ^ 20261104)
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()
    o, h, l, c = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70 or tod[w[0]] != 930:
            continue
        atr = days[d0]; op = o[w[0]]; end = w[-1]
        sig = None
        for i in w[2:]:
            t = tod[i]  # bar start; close = t+5 -> closes 10:00..13:30 = starts 955..1325
            if t < 955:
                continue
            if t > 1325:
                break
            seg = np.arange(w[0], i)            # bars through i-1
            ih = seg[np.argmax(h[seg])]; H = h[ih]
            if H < op + 0.5 * atr or ih > i - 2:
                continue
            Lpb = l[ih + 1:i].min() if ih + 1 < i else np.inf
            if not (Lpb <= H - (H - op) / 3 and Lpb > op):
                continue
            if c[i] > h[i - 1] and c[i] > Lpb and l[i] >= Lpb:
                sig = (i, Lpb, l[w[0]:i + 1].min())
                break
        if sig is None:
            continue
        i, Lpb, lod = sig
        if i + 1 > end:
            continue
        e = o[i + 1]; R = e - (Lpb - 0.01)
        if R < 0.001 * e:
            continue
        pool = w[(tod[w] >= 1005) & (tod[w] <= 1335)]
        ctl_idx = rng.choice(pool, size=min(3, len(pool)), replace=False)
        for m in (1.5, 2.0):
            tgt = e + m * R
            p, kind = sim(o, h, l, c, i + 1, end, e, R, tgt)
            rr = (p - cost(e, "tgt", tod[i + 1])) / R
            ctl = []
            for jx in ctl_idx:
                ej = o[jx]; pj, _ = sim(o, h, l, c, jx, end, ej, R, ej + m * R)
                ctl.append((pj - cost(ej, "tgt", tod[jx])) / R)
            room = (lod + atr - tgt, lod + 1.25 * atr - tgt)
            row = (d0, s, int(tod[i + 1]), rr, float(np.mean(ctl)), R / e * 100, kind)
            for rk in ("none", 1.0, 1.25):
                ok = rk == "none" or (room[0] >= 0 if rk == 1.0 else room[1] >= 0)
                out[(rk, m)].append(row + (bool(room[0] >= 0), bool(room[1] >= 0)) if ok else None)
        for k in out:
            out[k] = [x for x in out[k] if x is not None]
    return out


def main():
    print(f"universe symbols {len(PICK)}, symbol-days {len(top)}, sessions {NSESS}", flush=True)
    T = {k: [] for k in CFG}
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(one, sorted(PICK), chunksize=4)):
            for k in CFG:
                T[k].extend(r[k])
            if n % 100 == 0:
                print("symbols", n, flush=True)
    cols = ["date", "symbol", "tod", "r", "ctrl", "Rpct", "kind", "room10", "room125"]
    out = []
    t90 = round(max(1.35, 0.9 * G.t_required(N_STUDY)), 2)
    frames = {}
    for k in CFG:
        t = pd.DataFrame(T[k], columns=cols); frames[k] = t
        name = f"A-room-{k[0]}-m{k[1]:g}"
        s_ = G.summary(t); rg = G.regime_split(t, REG)
        trn, val = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
        mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
        exs = G.summary(pd.DataFrame({"date": t.date, "r": t.r - t.ctrl}))
        day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax()
        dt = t.groupby(t.date.map(DTYPE)).r.agg(["mean", "size"])
        row = dict(config=name, n=s_["n"], per_session=round(s_["n"] / NSESS, 2), win=s_["win_rate"], exp_r=s_["exp_r"], t=s_["t"],
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
        out.append(row)
    O = pd.DataFrame(out)
    pd.set_option("display.width", 360); pd.set_option("display.max_columns", 50)
    print(O.to_string(index=False))
    O.to_csv(Path(__file__).with_name("a_results.csv"), index=False)
    print("\nDiagnostic: room filter kept vs dropped (from the 'none' trades), day-clustered t of the difference")
    for m in (1.5, 2.0):
        t = frames[("none", m)]
        for col, nm in (("room10", "k1.0"), ("room125", "k1.25")):
            a, b_ = t[t[col]], t[~t[col]]
            da = a.groupby("date").r.mean(); db = b_.groupby("date").r.mean()
            j = pd.concat([da, db], axis=1, keys=["k", "d"]).dropna(); dif = j.k - j.d
            tt = dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))) if len(dif) > 2 else np.nan
            print(f"  m{m:g} {nm}: kept n {len(a)} avg {a.r.mean():+.3f} | dropped n {len(b_)} avg {b_.r.mean():+.3f} | "
                  f"paired days {len(j)} diff {dif.mean():+.3f} t {tt:+.2f}")
    print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": G.t_required(N_STUDY), "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
