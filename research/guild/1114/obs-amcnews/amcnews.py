"""Observer: can Alpaca news timestamps serve as a point-in-time AMC source for FAMC (option C)? Count only, 0 configs.
For each AMC event (Yahoo earnings_yf, session 'amc') on report dates D in [start, end], ask Alpaca news (read-only GET) for
headlines on that symbol between D 15:30 ET and D+1 09:30 ET; 'covered' = at least one headline matching earnings words, published
after 16:00 ET on D and before 09:30 ET on D+1. Also counts BMO events wrongly matched by the same window (false AMC flags) from
the D-1 evening... (reported as BMO-on-D headlines between D-1 16:00 and D 09:30, which look 'AMC-like' for the previous day).
Run only outside 07:30-16:00 ET. usage: python amcnews.py <earnings_yf.parquet> <start> <end>. Educational only - not financial advice."""
import os, re, sys, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd, requests
ET = ZoneInfo("America/New_York"); n = datetime.now(ET)
if n.weekday() < 5 and 450 <= n.hour * 60 + n.minute < 960: sys.exit("refusing: 07:30-16:00 ET")
E = pd.read_parquet(sys.argv[1]); E["d"] = pd.to_datetime(E.date).dt.tz_localize(None).dt.normalize()
E = E[(E.d >= sys.argv[2]) & (E.d <= sys.argv[3]) & E.session.isin(["amc", "bmo"])]
lab = set(open("research/lab_symbols.txt").read().split()); E = E[E.symbol.isin(lab)]
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
WORD = re.compile(r"earn|result|quarter|Q[1-4]\b|revenue|EPS|guidance|beats|misses|reports", re.I)
def news(sym, a, b):
    r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=H, timeout=20,
                     params={"symbols": sym, "start": a.isoformat(), "end": b.isoformat(), "limit": 50, "sort": "asc"})
    if r.status_code == 429: time.sleep(3); return news(sym, a, b)
    return r.json().get("news", []) if r.status_code == 200 else None
rows = []
for _, e in E.iterrows():
    D = e.d.to_pydatetime().replace(tzinfo=ET)
    if e.session == "amc": a, b = D.replace(hour=16), (D + pd.offsets.BDay(1)).to_pydatetime().replace(hour=9, minute=30, tzinfo=ET)
    else: a, b = (D - pd.offsets.BDay(1)).to_pydatetime().replace(hour=16, tzinfo=ET), D.replace(hour=9, minute=30)
    nw = news(e.symbol, a, b); time.sleep(0.35)
    hit = None if nw is None else any(WORD.search(x.get("headline", "") or "") for x in nw)
    first = None
    if nw: ts = [pd.Timestamp(x["created_at"]).tz_convert(ET) for x in nw if WORD.search(x.get("headline", "") or "")]; first = min(ts).strftime("%H:%M") if ts else None
    rows.append(dict(symbol=e.symbol, date=str(e.d.date()), session=e.session, n_news=None if nw is None else len(nw), covered=hit, first_earn_hdl=first))
R = pd.DataFrame(rows)
print(f"events {len(R)} ({sys.argv[2]}..{sys.argv[3]}, lab names), API errors {int(R.covered.isna().sum())}")
print(R.groupby("session").agg(n=("covered", "size"), covered=("covered", "mean"), any_news=("n_news", lambda s: (s > 0).mean())).round(3).to_string())
print("AMC: earnings headline in window by time bucket of first headline:", R[(R.session == "amc") & R.covered.fillna(False)].first_earn_hdl.str[:2].value_counts().sort_index().to_dict())
R.to_csv(sys.argv[0].replace(".py", "_rows.csv"), index=False)
print("Reading: 'covered' AMC share = how many AMC names a news-based nightly list would catch; the BMO row = how many BMO names would be wrongly flagged as 'AMC the evening before' by the same window. Educational only - not financial advice.")
