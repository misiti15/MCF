"""R3B step 4: live books. (a) walk-forward weekly with rule B1 on live records; comparators top-10 by total R before the
week, Primary account actual; (b) frozen lab books' live record 10-06..11-24 and 11-05..11-24.
Educational only - not financial advice."""
import json, itertools, re
import numpy as np, pandas as pd
from common import metrics, paired, P, FAM, TOP10, PRIM
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
L = pd.read_parquet(X + "live_dedup.parquet")[["strategy", "symbol", "side", "date", "signal_time", "r", "account"]]
st = pd.to_datetime(L.signal_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
L["T"] = st.dt.hour * 100 + st.dt.minute
tt = pd.read_parquet(P + "tt1_live.parquet")[["date", "T", "TT1"]]
so = pd.read_parquet(P + "spyopen.parquet"); so = so[so.src == "LIVE"][["date", "T", "spyopen"]]
L = L.merge(tt, on=["date", "T"], how="left").merge(so, on=["date", "T"], how="left")
L["TT1"] = L.TT1.fillna(False).astype(bool); L["SPYOPEN"] = L.spyopen.fillna(False).astype(bool)
DAYS = sorted(L.date.unique())
NAME = {"L3-fromopen": "L3-gap-slope-fromopen-FD", "RW3": "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "RW5": "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "L3-lowdist": "L3-gap-slope-lowdist-FD",
        "L3-rsi5hi": "L3-gap-slope-rsi5hi-FD", "RW6": "RW6-ns2-up3-short-FD",
        "GEN-261029-06": "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short",
        "GEN-261023-06": "GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short",
        "CWT09": "CWT09-gapdn-vwaploss-g10-short", "CWT14": "CWT14-failbrk-orl-p10-long-WB5",
        "NM-RWN4": "NM-RWN4-ns2-spyup05-notfri-short", "NM-ETF": "NM-ETF-late-dip-di-long", "B3": None,
        "GEN-261019-02": "GEN-261019-02-BBpctle0p017-SMA20slopege0p46-PM-QQQdn-t05s1-long",
        "GEN-261027-01": "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"}

def fam(s):
    b = re.sub(r"-WB\d+$", "", s)
    if re.search(r"gapdn|gap-slope|gapdown|GAPDN", b): return "GD"
    return b

def trades_of(var, df=L):
    base, _, g = var.partition("+")
    x = df[df.strategy == base]
    return x[x[g]] if g else x

def day_series(x, days, w=1.0):
    return (x.groupby("date").r.sum() * w).reindex(days, fill_value=0.0)

def wf():
    mondays = [d for d in DAYS if pd.Timestamp(d).dayofweek == 0 or d == DAYS[0]]
    weeks = []
    for i, m in enumerate(mondays):
        nxt = mondays[i + 1] if i + 1 < len(mondays) else "9999"
        weeks.append((m, [d for d in DAYS if m <= d < nxt]))
    rows, books = [], []
    for m, wdays in weeks[1:]:
        hist = [d for d in DAYS if d < m]; H = L[L.date < m]
        cnt = H.groupby("strategy").size(); pool = list(cnt[cnt >= 20].index)
        side = H.groupby("strategy").side.first()
        first = H.groupby("strategy").date.min()
        def tps(v, x):
            nses = sum(1 for d in hist if d >= first[v.partition("+")[0]])
            return len(x) / max(1, nses)
        V = {}
        for s in pool:
            vs = [s] if side[s] < 0 else [s + "+TT1", s + "+SPYOPEN"]
            for v in vs:
                x = trades_of(v, H)
                if not len(x): continue
                w = 1.0 / max(1.0, tps(v, x))
                V[v] = (w, day_series(x, hist, w).to_numpy(), day_series(x, hist).to_numpy())
        obj = lambda d: d.mean() - 0.05 * abs(np.sort(d)[:5].mean())
        sh = sorted([v for v in V if side[v.partition("+")[0]] < 0], key=lambda v: -obj(V[v][1]))[:12]
        lb = {}
        for v in V:
            b = v.partition("+")[0]
            if side[b] > 0: lb.setdefault(b, []).append(v)
        lbase = sorted(lb, key=lambda b: -max(obj(V[v][1]) for v in lb[b]))[:6]
        best, bs = None, -1e9
        for nl in (2, 3):
            if len(lbase) < nl: continue
            for lbs in itertools.combinations(lbase, nl):
                for lv in itertools.product(*[lb[b] for b in lbs]):
                    for sv in itertools.combinations(sh, 5 - nl):
                        fams = [fam(v.partition("+")[0]) for v in lv + sv]
                        if max(fams.count(f) for f in set(fams)) > 2: continue
                        s_ = obj(sum(V[v][1] for v in lv + sv))
                        if s_ > bs: bs, best = s_, lv + sv
        tot = H.groupby("strategy").r.sum()
        t10 = list(tot[cnt >= 20].sort_values(ascending=False).index[:10])
        W = L[L.date.isin(wdays)]
        def score_book(vs, wmap, scale=1.0):
            return sum(day_series(trades_of(v, W), wdays, wmap[v] * scale) for v in vs)
        if best is None:
            continue
        w5 = {v: V[v][0] for v in best}
        w10 = {}
        for s in t10:
            x = H[H.strategy == s]; w10[s] = 1.0 / max(1.0, len(x) / max(1, sum(1 for d in hist if d >= first[s])))
        b5w2 = score_book(best, w5); b10w2 = score_book(t10, w10, 0.5)
        b5w1 = score_book(best, {v: 1.0 for v in best}); b10w1 = score_book(t10, {v: 1.0 for v in t10}, 0.5)
        prim = day_series(W[W.account == "primary"], wdays)
        for d in wdays:
            rows.append({"week": m, "date": d, "b5_w2": b5w2[d], "t10_w2_half": b10w2[d], "b5_w1": b5w1[d],
                         "t10_w1_half": b10w1[d], "primary_actual": prim[d]})
        books.append({"week": m, "book5": list(best), "top10": t10, "n_pool": len(pool)})
    R = pd.DataFrame(rows).set_index("date")
    return R, books

def frozen_live(frozen):
    out = {}
    for k, b in frozen["books"].items():
        vs = b["book"]
        for lab, days in (("live_all", DAYS), ("live_after_1104", [d for d in DAYS if d > "2026-11-04"])):
            W = L[L.date.isin(days)]
            parts = {}
            for v in vs:
                base, _, g = v.partition("+")
                nm = NAME.get(base)
                parts[v] = day_series(trades_of(nm + ("+" + g if g else ""), W), days) if nm else pd.Series(0.0, index=days)
            d = sum(parts.values())
            ntr = {v: int(len(trades_of(NAME[v.partition('+')[0]] + ('+' + v.partition('+')[2] if '+' in v else ''), W)))
                   if NAME.get(v.partition('+')[0]) else 0 for v in vs}
            out.setdefault(k, {})[lab] = {"w1": metrics(d), "per_setup_R": {v: round(float(parts[v].sum()), 2) for v in vs},
                                          "trades": ntr}
    for ref, lst in (("TOP10_half", TOP10), ("PRIMARY_roster", PRIM)):
        for lab, days in (("live_all", DAYS), ("live_after_1104", [d for d in DAYS if d > "2026-11-04"])):
            W = L[L.date.isin(days)]
            sc = 0.5 if ref == "TOP10_half" else 1.0
            parts = {v: day_series(W[W.strategy == NAME[v]], days, sc) for v in lst}
            out.setdefault(ref, {})[lab] = {"w1": metrics(sum(parts.values())),
                                            "per_setup_R": {v: round(float(parts[v].sum()), 2) for v in lst}}
    for lab, days in (("live_all", DAYS), ("live_after_1104", [d for d in DAYS if d > "2026-11-04"])):
        out.setdefault("PRIMARY_account_actual", {})[lab] = {"w1": metrics(day_series(L[(L.account == "primary") & L.date.isin(days)], days))}
    return out

if __name__ == "__main__":
    fz = json.load(open(P + "frozen.json"))
    R, books = wf()
    R.to_csv(P + "wf_daily.csv")
    res = {"wf_books": books, "wf": {c: metrics(R[c]) for c in R.columns if c != "week"},
           "wf_paired_w2": paired(R.b5_w2, R.t10_w2_half), "wf_paired_w1": paired(R.b5_w1, R.t10_w1_half),
           "wf_weekly": R.groupby("week").sum().round(2).to_dict(orient="index"),
           "frozen_live": frozen_live(fz)}
    json.dump(res, open(P + "live.json", "w"), indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("wf", "wf_paired_w2", "wf_paired_w1", "wf_weekly")}, indent=1, default=float))
