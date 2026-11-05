"""reddit_1105 A + B (PLAN.md was written before this ran).
A: twice-defended level that weakens, then breaks; break or retest entry; long and short (r/Daytrading 1xom7y4).
B: gap-up that holds the prior close through 09:45, long (r/Trading 1xokdhq comment).
1-minute SIP cache (rebuilt 2026-11-04, research/bdi/1104/DATA.md) resampled to 5 minutes; the locked block
2024-11-01..2025-02-28 and the old holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any computation.
Costs 1c + 1 bp per side, entry x gates.tod_cost_mult, target exits free, +2c on stops. Next-bar-open entries, stop
first, gaps through stops fill at the open.
Usage: python ab_tests.py > ab_out.txt   Educational only - not financial advice."""
import json, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set

N_STUDY = 12
SPLIT = pd.Timestamp("2025-08-31").date()
CFG_A = [("A", side, ent, m) for side in ("long", "short") for ent in ("break", "retest") for m in (1.5, 2.0)]
CFG_B = [("B", g, ex) for g in (0.5, 1.0) for ex in ("hold", "t2")]
CFG = CFG_A + CFG_B


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "adv20"])
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
REG = G.session_regimes(D[["date", "open", "close"]])
spy = D[D.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DTYPE = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ETF = etf_set()
S = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna() & D.pc.notna()]
S = S[(pd.to_datetime(S.date) - pd.to_datetime(S.prev_date)).dt.days <= 5]
top = S.sort_values("adv_prev", ascending=False).groupby("date").head(250)
top = top[~GD._blackout(top.symbol.to_numpy(), top.date.to_numpy())]
PICK = {}
for s, d, a, p in zip(top.symbol, top.date, top.atr14, top.pc):
    PICK.setdefault(s, {})[d] = (a, p)
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


def pattern(seg, lv, atr, sgn, h, l):
    """Twice-defended level check on bars `seg` (through i-1). Short side (sgn -1): lv = session low, touches are lows
    near it, bounces are highs. Long side mirrored. Returns final bounce extreme or None."""
    if sgn < 0:
        near = l[seg] <= lv + 0.10 * atr; away = h[seg]; thr = lv + 0.30 * atr
    else:
        near = h[seg] >= lv - 0.10 * atr; away = -l[seg]; thr = -(lv - 0.30 * atr)
    eps = 0; bounces = []; ext = -np.inf
    for k in range(len(seg)):
        if near[k]:
            if eps == 0:
                eps = 1
            elif ext >= thr:
                eps += 1; bounces.append(ext)
                ext = -np.inf
            ext = max(ext, away[k])
        elif eps:
            ext = max(ext, away[k])
    if eps < 2 or not (ext < bounces[-1]):
        return None
    return ext if sgn < 0 else -ext


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
    rng = np.random.default_rng(zlib.crc32(s.encode()) ^ 20261105)
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()
    o, h, l, c = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close"))

    def ctrl(w, end, lo, hi, R, sgn, mult):
        pool = w[(tod[w] >= lo) & (tod[w] <= hi)]
        if len(pool) == 0:
            return np.nan
        res = []
        for jx in rng.choice(pool, size=min(3, len(pool)), replace=False):
            ej = o[jx]; tg = None if mult is None else ej + sgn * mult * R
            pj, _ = sim(o, h, l, c, jx, end, ej, R, tg, sgn)
            res.append((pj - cost(ej, "tgt", tod[jx])) / R)
        return float(np.mean(res))

    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70 or tod[w[0]] != 930:
            continue
        atr, pcl = days[d0]; end = w[-1]
        # ---- A: both sides
        for sgn, side in ((1, "long"), (-1, "short")):
            sig = None
            for i in w[3:]:
                t = tod[i]                      # bar start; close = t + 5 -> closes 10:00..14:30
                if t < 955:
                    continue
                if t > 1425:
                    break
                seg = np.arange(w[0], i)
                lv = h[seg].max() if sgn > 0 else l[seg].min()
                if not (sgn * (c[i] - lv) > 0.05 * atr):
                    continue
                fb = pattern(seg, lv, atr, sgn, h, l)
                if fb is None:
                    continue
                sig = (i, lv, fb); break
            if sig is None:
                continue
            i, lv, fb = sig
            for ent in ("break", "retest"):
                if ent == "break":
                    j0 = i + 1
                    if j0 > end:
                        continue
                    e = o[j0]; R = sgn * (e - (fb - sgn * 0.01))
                else:
                    jj = None
                    for j in range(i + 1, min(i + 12, end - 1) + 1):
                        if tod[j] > 1455:
                            break
                        if sgn * (c[j] - lv) <= 0:          # closed back through the level: cancelled
                            break
                        touched = (l[j] <= lv + 0.02 * atr) if sgn > 0 else (h[j] >= lv - 0.02 * atr)
                        if touched:
                            jj = j; break
                    if jj is None:
                        continue
                    j0 = jj + 1
                    ext = l[i:jj + 1].min() if sgn > 0 else h[i:jj + 1].max()
                    e = o[j0]; R = sgn * (e - (ext - sgn * 0.01))
                if not (R >= 0.001 * e and R <= 1.0 * atr):
                    continue
                for m in (1.5, 2.0):
                    p, kind = sim(o, h, l, c, j0, end, e, R, e + sgn * m * R, sgn)
                    rr = (p - cost(e, "tgt", tod[j0])) / R
                    out[("A", side, ent, m)].append((d0, s, int(tod[j0]), rr, ctrl(w, end, 1005, 1500, R, sgn, m), R / e * 100, kind))
        # ---- B: gap-up holds the prior close
        op = o[w[0]]; gap = (op / pcl - 1) * 100
        if gap >= 0.5 and gap <= 8 and l[w[0]:w[0] + 3].min() > pcl and tod[w[3]] == 945:
            j0 = w[3]; e = o[j0]; R = e - (pcl - 0.01)
            if R >= 0.001 * e and R <= 1.5 * atr:
                for ex in ("hold", "t2"):
                    mult = None if ex == "hold" else 2.0
                    p, kind = sim(o, h, l, c, j0, end, e, R, None if mult is None else e + mult * R, 1)
                    rr = (p - cost(e, "tgt", tod[j0])) / R
                    cr = ctrl(w, end, 950, 1300, R, 1, mult)
                    for g in (0.5, 1.0):
                        if gap >= g:
                            out[("B", g, ex)].append((d0, s, int(tod[j0]), rr, cr, R / e * 100, kind))
    return out


def name(k):
    return f"A-{k[1]}-{k[2]}-m{k[3]:g}" if k[0] == "A" else f"B-gap{k[1]:g}-{k[2]}"


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
    t90 = round(max(1.35, 0.9 * G.t_required(N_STUDY)), 2)
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
        out.append(row)
    O = pd.DataFrame(out)
    pd.set_option("display.width", 400); pd.set_option("display.max_columns", 50)
    print(O.to_string(index=False))
    O.to_csv(Path(__file__).with_name("ab_results.csv"), index=False)
    print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": G.t_required(N_STUDY), "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
