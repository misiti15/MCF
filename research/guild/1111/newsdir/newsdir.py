"""NEWSDIR pilot (PLAN.md, frozen 2026-11-10 19:20 ET). Alpaca news + reuse of OPTFLOW stock bars. GET only, keys from env.
    python newsdir.py <optflow_data_dir>          python newsdir.py --selftest
Educational only - not financial advice."""
import os, re, sys, json, time, urllib.request, urllib.parse
import numpy as np, pandas as pd
UP = r"upgrade|upgrades|upgraded|outperform|overweight|buy rating|raises price target|price target raised|approval|approved|wins|awarded|contract|partnership|record|buyback|repurchase|beats|expands|launches|acquired by|to be acquired"
DN = r"downgrade|downgrades|downgraded|underperform|underweight|sell rating|cuts price target|price target cut|lowers price target|recall|lawsuit|sued|probe|investigation|subpoena|offering|dilution|delay|delays|halts|resigns|misses|warns|layoffs|fine|fined|rejects|rejected|short report"
ERN = r"earnings|\beps\b|quarter|\bq[1-4]\b|results|revenue|guidance|reports"
UPR, DNR, ERR = (re.compile(rf"\b(?:{x})\b", re.I) for x in (UP, DN, ERN))


def polarity(headline):
    if ERR.search(headline): return None
    return len(UPR.findall(headline)) - len(DNR.findall(headline))


def selftest():
    assert polarity("Morgan Stanley upgrades XYZ to Overweight") == 2
    assert polarity("XYZ downgraded to Underperform at BofA") == -2
    assert polarity("XYZ Q3 earnings beat estimates") is None
    assert polarity("XYZ announces $5B buyback") == 1 and polarity("XYZ faces DOJ probe") == -1
    assert polarity("XYZ CEO to speak at conference") == 0
    print("selftest ok: lexicon, earnings exclusion, word boundaries")


H = lambda: {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    url = "https://data.alpaca.markets/v1beta1/news?" + urllib.parse.urlencode(q)
    for a in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H()), timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    return {}


def main(DIR):
    names = json.load(open(f"{DIR}/names.json"))
    news_p = f"{DIR}/news.csv.gz"
    if not os.path.exists(news_p):
        rows = []
        for i in range(0, len(names), 10):
            tok = None
            while True:
                q = {"symbols": ",".join(names[i:i + 10]), "start": "2026-08-01T00:00:00Z", "end": "2026-11-07T00:00:00Z", "limit": 50, "sort": "asc"}
                if tok: q["page_token"] = tok
                j = get(q)
                for it in j.get("news", []): rows.append((it["created_at"], "|".join(it.get("symbols", [])), it.get("headline", "")))
                tok = j.get("next_page_token")
                if not tok: break
            print("news", i, len(rows), flush=True)
        pd.DataFrame(rows, columns=["t", "symbols", "headline"]).to_csv(news_p, index=False)
    N = pd.read_csv(news_p); N["t"] = pd.to_datetime(N.t, utc=True).dt.tz_convert("America/New_York")
    N = N[N.symbols.fillna("").str.count(r"\|") == 0].copy(); N["sym"] = N.symbols
    N["pol"] = N.headline.fillna("").map(polarity)
    S = pd.read_csv(f"{DIR}/stock1m.csv.gz"); S["t"] = pd.to_datetime(S.t, utc=True).dt.tz_convert("America/New_York")
    S["d"] = S.t.dt.strftime("%Y-%m-%d"); S["m"] = S.t.dt.hour * 60 + S.t.dt.minute
    sess = sorted(S[S.symbol == "SPY"].d.unique())
    Dd = pd.read_csv(f"{DIR}/daily.csv.gz").sort_values(["symbol", "date"]); pc = Dd.groupby("symbol").c.shift(1)
    tr = np.maximum(Dd.h - Dd.l, np.maximum((Dd.h - pc).abs(), (Dd.low - pc).abs() if "low" in Dd else (Dd.l - pc).abs()))
    Dd["pc"] = pc; Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    INFO = {(s, d): (p, a) for s, d, p, a in Dd[["symbol", "date", "pc", "atr"]].itertuples(index=False)}
    spy = {d: g.set_index("m") for d, g in S[S.symbol == "SPY"].groupby("d")}
    out = []
    for k, d in enumerate(sess[1:], 1):
        lo = pd.Timestamp(f"{sess[k - 1]} 16:00", tz="America/New_York"); hi = pd.Timestamp(f"{d} 09:45", tz="America/New_York")
        W = N[(N.t >= lo) & (N.t < hi) & N.pol.notna()]
        sc = W.groupby("sym").pol.sum()
        sp = spy.get(d)
        if sp is None or 590 not in sp.index or 955 not in sp.index: continue
        spm = float(sp.loc[955, "c"]) / float(sp.loc[590, "o"]) - 1
        for s, g in S[(S.d == d) & (S.symbol != "SPY")].groupby("symbol"):
            g = g.set_index("m"); inf = INFO.get((s, d))
            if inf is None or not all(x in g.index for x in (570, 590, 955)) or not (np.isfinite(inf[1]) and inf[1] > 0): continue
            p, a = inf; e, x = float(g.loc[590, "o"]), float(g.loc[955, "c"]); gap = float(g.loc[570, "o"]) / p - 1
            out.append(dict(symbol=s, date=d, pol=int(np.sign(sc.get(s, 0))), n_items=int((W.sym == s).sum()), gap=gap,
                            ex=(x - e) / a - spm * e / a))
    X = pd.DataFrame(out); X["exd"] = X.ex - X.groupby("date").ex.transform("mean")
    Y = X[X.pol != 0].copy(); Y["sx"] = Y.pol * Y.exd; Y["gx"] = np.sign(Y.gap) * Y.exd
    def dt_(v, d):
        g = v.groupby(d).mean(); return g.mean(), g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g), int((g > 0).sum())
    print(f"name-days {len(X)} ({X.symbol.nunique()} names, {X.date.nunique()} sessions); qualifying single-symbol non-earnings items "
          f"{int((N.pol.notna()).sum())}; name-days with a polarity signal {len(Y)} (UP {int((Y.pol > 0).sum())} / DOWN {int((Y.pol < 0).sum())})")
    m, t, n, pos = dt_(Y.sx, Y.date); mg, tg, _, _ = dt_(Y.gx, Y.date)
    print(f"THE LOOK: polarity-signed, day-demeaned ex-market 09:50->15:55 = {m:+.3f} ATR, day-t {t:.2f}, + on {pos}/{n} days | "
          f"gap-sign baseline on the same name-days {mg:+.3f} (t {tg:.2f})")
    for lab, Z in (("AGREE (pol = gap sign)", Y[np.sign(Y.gap) == Y.pol]), ("DISAGREE", Y[np.sign(Y.gap) == -Y.pol])):
        if len(Z) > 20:
            m2, t2, n2, _ = dt_(Z.sx, Z.date); print(f"  {lab}: n {len(Z)} mean {m2:+.3f} t {t2:.2f} days {n2}")
    for sgn, lab in ((1, "UP"), (-1, "DOWN")):
        Z = Y[Y.pol == sgn]
        if len(Z) > 20: m3, t3, n3, _ = dt_(Z.sx, Z.date); print(f"  {lab} only: n {len(Z)} signed mean {m3:+.3f} t {t3:.2f}")
    X.to_csv(f"{DIR}/newsdir_rows.csv.gz", index=False)
    print("Headline lexicon (fixed in PLAN), single-symbol items, earnings excluded, 16:00 prior -> 09:45. Gross, beta 1 ex-market.")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main(sys.argv[1])
