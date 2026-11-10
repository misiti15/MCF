"""SIZEBKT descriptive (PLAN.md). python sizebkt.py <hodsep_data_dir>. 0 configs. Educational only - not financial advice."""
import re, sys, numpy as np, pandas as pd
DIR = sys.argv[1]
ETP_RE = re.compile(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Inverse|"
                    r"\bUltra|\bBear\b|\bBull\b|Daily Target|GraniteShares|Tradr|Defiance|T-Rex|Volatility|VIX|Physical (?:Gold|Silver)", re.I)
uni = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"])
etp = set(uni[uni.name.fillna("").str.contains(ETP_RE)].symbol) | {"SPY", "QQQ", "IWM", "DIA"} | set("XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split())
SL, BP, SP, SX = 0.01, 1e-4, 4.4e-4, 0.02


def win(arr, lo, hi):
    assert lo >= 0, f"negative window start {lo}"
    return arr[lo:hi]


D = pd.read_csv(f"{DIR}/daily.csv.gz"); D["date"] = pd.to_datetime(D.t, utc=True).dt.tz_convert("America/New_York").dt.date
D = D.sort_values(["symbol", "date"]); g = D.groupby("symbol"); D["pc"] = g.c.shift(1)
tr = np.maximum(D.h - D.l, np.maximum((D.h - D.pc).abs(), (D.l - D.pc).abs()))
D["atr"] = tr.groupby(D.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
D["adv20"] = (D.c * D.v).groupby(D.symbol).transform(lambda s: s.shift(1).rolling(20, min_periods=15).mean())
INFO = {(s, d): (a, adv) for s, d, a, adv in D[["symbol", "date", "atr", "adv20"]].itertuples(index=False)}
M = pd.read_csv(f"{DIR}/m5.csv.gz"); M["t"] = pd.to_datetime(M.t, utc=True).dt.tz_convert("America/New_York")
mm = M.t.dt.hour * 60 + M.t.dt.minute; M = M[(mm >= 570) & (mm < 960)].copy()
M["b"] = ((M.t.dt.hour * 60 + M.t.dt.minute) - 570) // 5; M["date"] = M.t.dt.date
A = {}
for (s, d), x in M.groupby(["symbol", "date"]):
    if s in etp: continue
    a = np.full((78, 5), np.nan); a[x.b.to_numpy()] = x[["o", "h", "l", "c", "v"]].to_numpy()
    if np.isnan(a[0, 0]): continue
    c = pd.Series(a[:, 3]).ffill().to_numpy(); miss = np.isnan(a[:, 0]); a[miss, :3] = c[miss, None]; a[:, 3] = c; a[miss, 4] = 0
    A[(s, d)] = a
BARS = [5 + 6 * k for k in range(9)]                       # bar index of the 10:00, 10:30, ..., 14:00 closes
assert all(b >= 5 for b in BARS)


def bracket(a, b, atr, k):
    """-> (gross R, cost R, kind) or None if no leg triggers; stop at c, target 2k, time exit at b+12 close."""
    c = a[b, 3]; up, dn = c + k * atr, c - k * atr; R = k * atr
    for i in range(b + 1, b + 13):
        o, h, l, cl = a[i, :4]
        hu, hd = h >= up, l <= dn
        if hu and hd: return -1.0, None, "both"            # conservative: ambiguous bar = a full stop
        if hu or hd:
            s = 1 if hu else -1; e = max(o, up) if s > 0 else min(o, dn)          # gap through the level fills at the open
            stop, tgt = c, e + s * 2 * R
            for j in range(i, b + 13):
                o2, h2, l2, c2 = a[j, :4]
                if j > i and s * (o2 - stop) <= 0: return s * (o2 - e) / R, e, "stop"
                if (s > 0 and l2 <= stop) or (s < 0 and h2 >= stop):
                    if j == i: return s * (stop - e) / R, e, "stop"   # stop first inside the entry bar
                    return s * (stop - e) / R, e, "stop"
                if (s > 0 and h2 >= tgt) or (s < 0 and l2 <= tgt): return 2.0, e, "target"
            return s * (a[b + 12, 3] - e) / R, e, "time"
    return None


rows = []
for (s, d), a in A.items():
    inf = INFO.get((s, d))
    if inf is None: continue
    atr, adv = inf
    if not (np.isfinite(atr) and atr > 0 and adv >= 60e6): continue
    prev = [A[(s, x)] for x in sorted({dd for (ss, dd) in A if ss == s} if False else []) ]
    rows.append((s, d))
# volume norms per symbol over prior sessions (sorted dates)
bysym = {}
for (s, d) in rows: bysym.setdefault(s, []).append(d)
out = []
for s, ds in bysym.items():
    ds = sorted(ds); allds = sorted(d for (ss, d) in A if ss == s)
    for d in ds:
        k_ = allds.index(d)
        if k_ < 6: continue
        prev = [A[(s, x)] for x in allds[max(0, k_ - 20):k_]]; a = A[(s, d)]; atr = INFO[(s, d)][0]
        hod = np.maximum.accumulate(a[:, 1]); lod = np.minimum.accumulate(a[:, 2])
        for b in BARS:
            vn = np.mean([win(p, b - 2, b + 1)[:, 4].sum() for p in prev])
            if not vn > 0: continue
            rv = win(a, b - 2, b + 1)[:, 4].sum() / vn; ra = (hod[b] - lod[b]) / atr
            mv = abs(a[b + 12, 3] - a[b, 3]) / atr
            rec = dict(symbol=s, date=d, bar=b, rvol15=rv, range_atr=ra, absmove=mv)
            for kk in (0.15, 0.25):
                res = bracket(a, b, atr, kk)
                if res is None: rec[f"g{kk}"] = np.nan; rec[f"c{kk}"] = np.nan; continue
                gR, e, kind = res; rec[f"g{kk}"] = gR; rec[f"both{kk}"] = kind == "both"
                e = e if e is not None else a[b, 3]
                rec[f"c{kk}"] = ((SL + e * BP) + SP * e + SL + e * BP + (SX if kind in ("stop", "both") else 0)) / (kk * atr)
            out.append(rec)
X = pd.DataFrame(out)
X["score"] = (X.rvol15.rank(pct=True) + X.range_atr.rank(pct=True)) / 2
print(f"rows {len(X)} ({X.symbol.nunique()} names, {X.date.nunique()} days, bars 10:00..14:00 every 30 min)")
dates = sorted(X.date.unique()); half = X.date < dates[len(dates) // 2]
for f in ("score", "rvol15", "range_atr"):
    q = pd.qcut(X[f].rank(method="first"), 5, labels=False)
    print(f"\n== by {f} quintile: mean |60-min move| / ATR {X.groupby(q).absmove.mean().round(3).tolist()}")
    for kk in (0.15, 0.25):
        g_ = X[f"g{kk}"]; trig = X.groupby(q)[f"g{kk}"].apply(lambda v: v.notna().mean()).round(2).tolist()
        gm = X.groupby(q)[f"g{kk}"].mean().round(3).tolist(); cm = X.groupby(q)[f"c{kk}"].median().round(3).tolist()
        dd = X.assign(q=q).groupby("date").apply(lambda z: z[f"g{kk}"][z.q == 4].mean() - z[f"g{kk}"][z.q == 0].mean()).dropna()
        tq5 = X[q == 4].groupby("date")[f"g{kk}"].mean().dropna()
        h1 = X[(q == 4) & half][f"g{kk}"].mean(); h2 = X[(q == 4) & ~half][f"g{kk}"].mean()
        print(f"  k {kk}: trigger rate {trig} | gross R/trigger Q1..Q5 {gm} | median cost R {cm} | Q5-Q1 per day + {int((dd > 0).sum())}/{len(dd)} "
              f"day-t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):.2f} | Q5 gross day-t {tq5.mean() / (tq5.std(ddof=1) / np.sqrt(len(tq5))):.2f} "
              f"| Q5 halves {h1:+.3f} / {h2:+.3f}")
X.to_csv(f"{DIR}/sizebkt_rows.csv.gz", index=False)
print("\nconservative: a bar touching both levels = -1R; gap through a level fills at the open; stop at the bracket centre;"
      "\ntarget 2k; time exit 60 min. Gross R; costs shown separately. Educational only - not financial advice.")
# sensitivity (reported, not a new look): drop ambiguous both-touch bars instead of scoring them -1R
print("\n--- sensitivity: ambiguous both-touch triggers EXCLUDED (not scored)")
for kk in (0.15, 0.25):
    q = pd.qcut(X.score.rank(method="first"), 5, labels=False)
    Y = X.assign(q=q); Y = Y[~Y[f"both{kk}"].fillna(False).astype(bool)]
    print(f"  k {kk}: both-touch share by score quintile {X.assign(q=q).groupby('q')[f'both{kk}'].mean().round(3).tolist()} | "
          f"gross R/trigger ex-both Q1..Q5 {Y.groupby('q')[f'g{kk}'].mean().round(3).tolist()}")
