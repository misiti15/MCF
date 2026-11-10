"""OPTFLOW pilot (PLAN.md, frozen 2026-11-10 17:40 ET). Alpaca market-data GETs only (keys from env, never printed).
    python optflow.py fetch <out_dir>     python optflow.py score <out_dir>     python optflow.py --selftest
Educational only - not financial advice."""
import os, sys, json, time, gzip, datetime as dt, urllib.request, urllib.parse
import numpy as np, pandas as pd
D0, D1 = dt.date(2026, 8, 3), dt.date(2026, 11, 6)


def occ(und, expiry, cp, strike):
    return f"{und}{expiry:%y%m%d}{cp}{int(round(strike * 1000)):08d}"


def fridays(day, n=2):
    d = day + dt.timedelta(days=(4 - day.weekday()) % 7); return [d + dt.timedelta(days=7 * i) for i in range(n)]


def strikes(px, pct=0.06):
    out = set()
    for step in (1.0, 2.5, 5.0):
        lo, hi = px * (1 - pct), px * (1 + pct)
        k = np.ceil(lo / step) * step
        while k <= hi: out.add(round(k, 2)); k += step
    return sorted(out)


def selftest():
    assert occ("AAPL", dt.date(2026, 10, 16), "C", 345) == "AAPL261016C00345000"
    assert occ("SOFI", dt.date(2026, 10, 16), "P", 13.5) == "SOFI261016P00013500"
    assert fridays(dt.date(2026, 10, 15)) == [dt.date(2026, 10, 16), dt.date(2026, 10, 23)]
    assert fridays(dt.date(2026, 10, 16))[0] == dt.date(2026, 10, 16)
    s = strikes(100.0); assert 95.0 in s and 97.5 in s and 106.0 in s and 93.0 not in s and 107.0 not in s
    print("selftest ok: OCC symbols, Friday expiries, strike grids")


H = lambda: {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(path, q):
    url = "https://data.alpaca.markets" + path + "?" + urllib.parse.urlencode(q)
    for a in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H()), timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    return {}


def stock_bars(syms, start, end, tf="1Min"):
    out, tok = {}, None
    while True:
        q = {"symbols": ",".join(syms), "timeframe": tf, "start": start, "end": end, "limit": 10000, "feed": "sip", "adjustment": "split"}
        if tok: q["page_token"] = tok
        j = get("/v2/stocks/bars", q)
        for s, bs in (j.get("bars") or {}).items(): out.setdefault(s, []).extend(bs)
        tok = j.get("next_page_token")
        if not tok: return out


def fetch(out):
    os.makedirs(out, exist_ok=True)
    lab = [s.strip() for s in open("/home/user/MCF/research/lab_symbols.txt") if s.strip()]
    uni = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"])
    etp = set(uni[uni.name.fillna("").str.contains(r"ETF|ETN|Fund|ProShares|Direxion|iShares|SPDR|Trust|Leveraged|Inverse|Ultra", regex=True)].symbol)
    cand = [s for s in lab if s not in etp and s not in ("SPY", "QQQ", "IWM", "DIA")]
    daily = {}
    for i in range(0, len(cand), 100):
        for s, bs in stock_bars(cand[i:i + 100], "2026-06-15T00:00:00Z", "2026-11-07T00:00:00Z", "1Day").items(): daily[s] = bs
    rows = [(s, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for s, bs in daily.items() for b in bs]
    Dd = pd.DataFrame(rows, columns=["symbol", "date", "o", "h", "l", "c", "v"]); Dd.to_csv(f"{out}/daily.csv.gz", index=False)
    Dd["dv"] = Dd.c * Dd.v
    top = Dd[(Dd.date >= "2026-07-01") & (Dd.date <= "2026-07-31")].groupby("symbol").dv.mean().nlargest(60).index.tolist()
    json.dump(top, open(f"{out}/names.json", "w")); print("names", len(top), flush=True)
    sess = sorted(d for d in Dd[Dd.symbol == top[0]].date.unique() if str(D0) <= d <= str(D1))
    with gzip.open(f"{out}/stock1m.csv.gz", "wt") as f:
        f.write("symbol,t,o,h,l,c,v\n")
        for i in range(0, len(top), 20):
            for d in sess:
                for s, bs in stock_bars(top[i:i + 20] + (["SPY"] if i == 0 else []), f"{d}T13:30:00Z", f"{d}T20:00:00Z").items():
                    for b in bs: f.write(f"{s},{b['t']},{b['o']},{b['h']},{b['l']},{b['c']},{b['v']}\n")
            print("stock", i, flush=True)
    opens = {}
    S = pd.read_csv(f"{out}/stock1m.csv.gz"); S["d"] = S.t.str[:10]
    for (s, d), g in S.groupby(["symbol", "d"]): opens[(s, d)] = float(g.sort_values("t").iloc[0].o)
    with gzip.open(f"{out}/opt30.csv.gz", "wt") as f:
        f.write("und,date,contract,cp,v,c\n"); n = 0
        for d in sess:
            day = dt.date.fromisoformat(d); batch = []
            for s in top:
                px = opens.get((s, d))
                if not px: continue
                for ex in fridays(day):
                    for k in strikes(px):
                        for cp in "CP": batch.append((s, occ(s, ex, cp, k), cp))
            for i in range(0, len(batch), 100):
                chunk = batch[i:i + 100]; m = {c: (u, cp) for u, c, cp in chunk}
                tok = None
                while True:
                    q = {"symbols": ",".join(m), "timeframe": "30Min", "start": f"{d}T13:30:00Z", "end": f"{d}T14:00:00Z", "limit": 10000}
                    if tok: q["page_token"] = tok
                    j = get("/v1beta1/options/bars", q)
                    for c, bs in (j.get("bars") or {}).items():
                        for b in bs:
                            if b["t"].startswith(f"{d}T13:30"): f.write(f"{m[c][0]},{d},{c},{m[c][1]},{b['v']},{b['c']}\n"); n += 1
                    tok = j.get("next_page_token")
                    if not tok: break
            print("opt", d, n, flush=True)
    print("done", flush=True)


def score(out):
    Dd = pd.read_csv(f"{out}/daily.csv.gz").sort_values(["symbol", "date"]); pc = Dd.groupby("symbol").c.shift(1)
    tr = np.maximum(Dd.h - Dd.l, np.maximum((Dd.h - pc).abs(), (Dd.l - pc).abs()))
    Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    ATR = {(s, d): a for s, d, a in Dd[["symbol", "date", "atr"]].itertuples(index=False)}
    S = pd.read_csv(f"{out}/stock1m.csv.gz"); S["t"] = pd.to_datetime(S.t, utc=True).dt.tz_convert("America/New_York")
    S["d"] = S.t.dt.strftime("%Y-%m-%d"); S["m"] = S.t.dt.hour * 60 + S.t.dt.minute
    O = pd.read_csv(f"{out}/opt30.csv.gz"); O["prem"] = O.v * O.c * 100
    P = O.pivot_table(index=["und", "date"], columns="cp", values="prem", aggfunc="sum").fillna(0)
    P["cs"] = P.C / (P.C + P.P)
    rows = []
    spy = {d: g.set_index("m") for d, g in S[S.symbol == "SPY"].groupby("d")}
    for (s, d), g in S[S.symbol != "SPY"].groupby(["symbol", "d"]):
        g = g.set_index("m"); a = ATR.get((s, d))
        if a is None or not np.isfinite(a) or d not in spy or (s, d) not in P.index: continue
        if 570 not in g.index or 600 not in g.index or 955 not in g.index: continue
        sp = spy[d]
        if 600 not in sp.index or 955 not in sp.index: continue
        e, x = float(g.loc[600, "o"]), float(g.loc[955, "c"])
        r30 = float(g.loc[599, "c"]) / float(g.loc[570, "o"]) - 1 if 599 in g.index else np.nan
        sdv = float((g.loc[570:599, "c"] * g.loc[570:599, "v"]).sum())
        spm = float(sp.loc[955, "c"]) / float(sp.loc[600, "o"]) - 1
        rows.append(dict(symbol=s, date=d, fwd=(x - e) / a, ex=(x - e) / a - spm * e / a, r30=r30,
                         cs=float(P.loc[(s, d), "cs"]), prem=float(P.loc[(s, d), "C"] + P.loc[(s, d), "P"]), sdv=sdv))
    X = pd.DataFrame(rows).sort_values(["symbol", "date"])
    g = X.groupby("symbol")
    X["cs_norm"] = g.cs.transform(lambda v: v.shift(1).rolling(20, min_periods=10).mean())
    X["acs"] = X.cs - X.cs_norm
    X["os"] = X.prem / X.sdv; X["os_ab"] = X.os / g.os.transform(lambda v: v.shift(1).rolling(20, min_periods=10).mean())
    X = X.dropna(subset=["acs", "ex", "r30"])
    X["exd"] = X.ex - X.groupby("date").ex.transform("mean")
    print(f"pilot rows {len(X)} ({X.symbol.nunique()} names, {X.date.nunique()} sessions)")
    def q5q1(Y, col="acs"):
        Y = Y.assign(q=Y.groupby("date")[col].transform(lambda v: pd.qcut(v.rank(method="first"), 5, labels=False) if len(v) >= 10 else np.nan))
        d = Y.groupby("date").apply(lambda z: z.exd[z.q == 4].mean() - z.exd[z.q == 0].mean()).dropna()
        return d.mean(), d.mean() / (d.std(ddof=1) / np.sqrt(len(d))), int((d > 0).sum()), len(d), Y.groupby("q").exd.mean().round(3).tolist()
    m, t, pos, n, qq = q5q1(X)
    print(f"THE LOOK - abnormal call share quintiles (within day), day-demeaned ex-market 10:00->15:55 (ATR): Q1..Q5 {qq}; "
          f"Q5-Q1 {m:+.3f} ATR, day-t {t:.2f}, + on {pos}/{n} days")
    X["r30t"] = X.groupby("date").r30.transform(lambda v: pd.qcut(v.rank(method="first"), 3, labels=["r30_lo", "r30_mid", "r30_hi"]))
    for tt, Y in X.groupby("r30t"):
        m, t, pos, n, _ = q5q1(Y.drop(columns="q", errors="ignore")) if len(Y) > 200 else (np.nan,) * 5
        print(f"  control - inside the stock's own 09:30-10:00 return tercile {tt}: Q5-Q1 {m:+.3f} day-t {t:.2f} (+{pos}/{n})")
    m2, t2, _, _, qq2 = q5q1(X, "r30")
    print(f"  reference - the stock's own first-30-min return as the signal: Q1..Q5 {qq2}; Q5-Q1 {m2:+.3f} day-t {t2:.2f}")
    X.to_csv(f"{out}/optflow_rows.csv.gz", index=False)
    print("unsigned premium proxy (not the paper's signed score); beta 1 ex-market; gross. Educational only - not financial advice.")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    elif sys.argv[1] == "fetch": fetch(sys.argv[2])
    else: score(sys.argv[2])
