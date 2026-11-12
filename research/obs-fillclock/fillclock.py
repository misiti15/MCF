"""OBS-FILLCLOCK (Observer 2026-11-11): is FWDCAL's exact-minute shortfall replay error or live fill latency?
Live journals only (data branches, root journal.db), sessions 2026-11-10..11-11 (= FWDCAL holdout). For each live
trade joined to its submitted signal (broker_order_id): decision bar = signal info.bar_time, fill = trades.entry_time
(broker fill clock; seconds != 0 in 96-100%). Offset = fill minute - decision bar minute. One global replay delay can
match at most the modal offset's share -> the exact-minute ceiling. 0 configs. Educational only - not financial advice.
usage: python fillclock.py <dir with mcf-data*.db>"""
import sqlite3, sys, collections, pandas as pd
D = sys.argv[1]; tot = cap = 0
for nm, b in [('Primary','mcf-data'),('On Deck','mcf-data-testing'),('Testing A','mcf-data-testing2'),('Testing B','mcf-data-explore1'),
              ('Testing C','mcf-data-livelab'),('Graveyard','mcf-data-graveyard'),('Gen','mcf-data-gen')]:
    c = sqlite3.connect(f"{D}/{b}.db")
    t = pd.read_sql("select t.entry_time, s.ts, s.info from trades t join signals s on s.broker_order_id=t.broker_order_id "
                    "where t.run_id=1 and t.date in ('2026-11-10','2026-11-11') and s.status='submitted'", c)
    n = c.execute("select count(*) from trades where run_id=1 and date in ('2026-11-10','2026-11-11')").fetchone()[0]
    assert len(t) == n, (nm, len(t), n)
    e = pd.to_datetime(t.entry_time, utc=True); s = pd.to_datetime(t.ts, utc=True)
    bt = t["info"].str.extract(r'"bar_time": "(\d{4})"')[0]
    em = e.dt.tz_convert("America/New_York").dt.strftime("%H%M")
    off = ((pd.to_datetime(em, format="%H%M") - pd.to_datetime(bt, format="%H%M")).dt.total_seconds() / 60).dropna().astype(int)
    cc = collections.Counter(off); m, k = cc.most_common(1)[0]; lag = (e - s).dt.total_seconds() / 60
    print(f"{nm:10s} n {n:5d}  decision->fill min: med {lag.median():.2f} p90 {lag.quantile(.9):.2f}  offsets {dict(sorted(cc.items()))}"
          f"  modal +{m} share {k/len(off):.3f}")
    tot += len(off); cap += k
print(f"pooled ceiling (modal offset per account) {cap/tot:.3f} of {tot}")
