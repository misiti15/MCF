"""reddit_1109 A + B (PLAN.md was written before this ran). Harness copied from research/bdi/reddit_1106/a_tests.py.
A: leader pulled back 3-7 days into the rising daily 9/21 EMA, intraday trigger, long (r/swingtrading 1xqieam).
B: daily inside-day breakout, both sides (r/Daytrading 1xrs4yu).
1-minute SIP cache (rebuilt 2026-11-04) resampled to 5 minutes; the locked block 2024-11-01..2025-02-28 and the old
holdouts (2026-04..06, >= 2026-09-16) are dropped at load, before any computation. Costs 1c + 1 bp per side, entry x
gates.tod_cost_mult, target exits free, +2c on stops. Next-bar-open entries, stop first, gaps through stops fill at
the open.  Usage: python ab_tests.py > ab_out.txt   Educational only - not financial advice."""
import json, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.data.store import BarStore
from mcf.longhold.signals import etf_set

N_STUDY = 14
SPLIT = pd.Timestamp("2025-08-31").date()
CFG = [("A", T, X) for T in (1, 2, 3) for X in ("close", "2R")] + \
      [("B", side, S, X) for side in ("long", "short") for S in ("mid", "far") for X in ("close", "2R")]
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
dts = pd.to_datetime(D.date)
e9 = g.close.transform(lambda x: x.ewm(span=9, adjust=False).mean())
e21 = g.close.transform(lambda x: x.ewm(span=21, adjust=False).mean())
e9p, e21p = e9.groupby(D.symbol).shift(1), e21.groupby(D.symbol).shift(1)
e21p6 = e21.groupby(D.symbol).shift(6)
ret60 = g.close.shift(1) / g.close.shift(61)
span60 = (dts - pd.to_datetime(g.date.shift(61))).dt.days
# sessions before D of the highest close among the last 10 sessions (D-1 .. D-10): 1 = D-1
hik = g.close.transform(lambda x: x.shift(1).rolling(10).apply(lambda a: 10 - int(np.argmax(a)), raw=True))
D["ctxA"] = ((ret60 >= 1.20) & (span60 <= 100) & (e21p > e21p6) & (pc > 0.98 * e21p) & hik.between(3, 7)
             & (g.low.shift(1) <= 1.005 * e9p))
D["pdh"], D["pdl"] = g.high.shift(1), g.low.shift(1)
D["inside"] = ((g.high.shift(1) < g.high.shift(2)) & (g.low.shift(1) > g.low.shift(2))
               & ((dts - pd.to_datetime(g.date.shift(2))).dt.days <= 7))
REG = G.session_regimes(D[["date", "open", "close"]])
spy = D[D.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DTYPE = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ETF = etf_set()
S_ = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna() & D.pc.notna()]
S_ = S_[(pd.to_datetime(S_.date) - pd.to_datetime(S_.prev_date)).dt.days <= 5]
top = S_.sort_values("adv_prev", ascending=False).groupby("date").head(250)
top = top[~GD._blackout(top.symbol.to_numpy(), top.date.to_numpy())]
PICK = {}
for s, d, a, h_, l_, ca, ib in zip(top.symbol, top.date, top.atr14, top.pdh, top.pdl, top.ctxA, top.inside):
    PICK.setdefault(s, {})[d] = (a, h_, l_, bool(ca), bool(ib))
NSESS = top.date.nunique()
NCTX = (int(top.ctxA.sum()), int(top.inside.sum()))


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
    rng = np.random.default_rng(zlib.crc32(s.encode()) ^ 20261109)
    dd = m5.index.date
    tod = (m5.index.hour * 100 + m5.index.minute).to_numpy()
    o, h, l, c, v = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))

    def run(j0, end, e, R, sgn, X):
        tgt = e + sgn * 2 * R if X == "2R" else None
        p, kind = sim(o, h, l, c, j0, end, e, R, tgt, sgn)
        return (p - cost(e, "tgt", tod[j0])) / R, kind

    def ctrl(w, end, lo, hi, R, sgn, X):
        pool = w[(tod[w] >= lo) & (tod[w] <= hi)]
        if len(pool) == 0:
            return np.nan
        return float(np.mean([run(jx, end, o[jx], R, sgn, X)[0] for jx in rng.choice(pool, size=min(3, len(pool)), replace=False)]))

    for d0 in sorted(set(dd)):
        w = np.flatnonzero(dd == d0)
        if len(w) < 70 or tod[w[0]] != 930:
            continue
        atr, pdh, pdl, ca, ib = days[d0]; end = w[-1]
        if not (ca or ib):
            continue
        tp = (h[w] + l[w] + c[w]) / 3
        vw = np.cumsum(tp * v[w]) / np.maximum(np.cumsum(v[w]), 1)
        lod = np.minimum.accumulate(l[w])
        hod = np.maximum.accumulate(h[w])
        if ca:
            orh = h[w[:3]].max()
            sig = {1: None, 2: None, 3: None}
            below = False
            for i in range(1, len(w) - 1):
                t_ = tod[w[i]]
                if t_ > 1125:       # bar closes 09:45..11:30
                    break
                if t_ >= 940:
                    if sig[1] is None and c[w[i]] > orh:
                        sig[1] = i
                    if sig[2] is None and lod[i] < pdl and c[w[i]] > pdl:
                        sig[2] = i
                    if sig[3] is None and below and c[w[i]] > vw[i]:
                        sig[3] = i
                if c[w[i]] < vw[i]:
                    below = True
            for T, i in sig.items():
                if i is None:
                    continue
                j0 = w[i + 1]; e = o[j0]; R = e - (lod[i] - 0.01)
                if not (R >= MINR * e and R <= 1.5 * atr):
                    continue
                for X in ("close", "2R"):
                    rr, kind = run(j0, end, e, R, 1, X)
                    out[("A", T, X)].append((d0, s, int(tod[j0]), rr, ctrl(w, end, 950, 1130, R, 1, X), R / e * 100, kind))
        if ib:
            for side, sgn in (("long", 1), ("short", -1)):
                lvl = pdh if sgn > 0 else pdl
                i = next((i for i in range(len(w) - 1) if 930 <= tod[w[i]] <= 1455 and sgn * (c[w[i]] - lvl) > 0), None)
                if i is None:
                    continue
                j0 = w[i + 1]; e = o[j0]
                for S in ("mid", "far"):
                    st = (pdh + pdl) / 2 if S == "mid" else (pdl if sgn > 0 else pdh)
                    st = st - sgn * 0.01
                    R = sgn * (e - st)
                    if not (R >= MINR * e and R <= 1.5 * atr):
                        continue
                    for X in ("close", "2R"):
                        rr, kind = run(j0, end, e, R, sgn, X)
                        out[("B", side, S, X)].append((d0, s, int(tod[j0]), rr, ctrl(w, end, 935, 1500, R, sgn, X), R / e * 100, kind))
    return out


def name(k):
    return f"A-T{k[1]}-{k[2]}" if k[0] == "A" else f"B-{k[1]}-{k[2]}-{k[3]}"


def main():
    print(f"universe symbols {len(PICK)}, symbol-days {len(top)}, sessions {NSESS}, ctxA days {NCTX[0]}, inside days {NCTX[1]}", flush=True)
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
    O.to_csv(Path(__file__).with_name("ab_results.csv"), index=False)
    print(json.dumps({"configs": len(O), "bar90": t90, "full_bar": tfull, "pass_bar90": int(O.get("bar90_pass", pd.Series(dtype=bool)).fillna(False).sum()),
                      "pass_full": int(O.get("full_bar_pass", pd.Series(dtype=bool)).fillna(False).sum()), "best_t": float(O.t.max())}))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
