"""Forward tallies 2026-11-05 for swing1104-L7 (short entries with QQQ >= +0.75% from open at the entry minute, class A
vs the same setups' other shorts) and swing1104-L8 (CWT14-failbrk-*-long entries with IWM <= -0.50% from open, class A vs
other failbrk longs); live journals run 1, all 7 accounts, R = pnl_adj / $ risk.
Usage: python forward_l78.py <scratch with bars/QQQ.parquet, bars/IWM.parquet>   Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(HERE.parent / "nightly1105" / "trades.csv"); T = T[T.run_id == 1].copy()
T["nt"] = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ).dt.floor("min")
def fo(s):
    b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    b = b.between_time("09:30", "15:59"); return (b.close / b.open.iloc[0] - 1) * 100
q, i = fo("QQQ"), fo("IWM")
T["q"] = T.nt.map(lambda t: q.asof(t)); T["i"] = T.nt.map(lambda t: i.asof(t))
sh = T[T.side == -1]; a = sh[sh.q >= 0.75]; b = sh[(sh.q < 0.75) & sh.strategy.isin(a.strategy)]
print(f"L7 2026-11-05: class A n {len(a)} avg {a.radj.mean() if len(a) else float('nan'):+.3f}; same-setup B n {len(b)}; all shorts {len(sh)} avg {sh.radj.mean():+.3f}; QQQ max fo {q.max():+.2f}%")
fb = T[T.strategy.str.match(r"CWT14-failbrk-.*-long$")]; a8, b8 = fb[fb.i <= -0.5], fb[fb.i > -0.5]
print(f"L8 2026-11-05: class A n {len(a8)} avg {a8.radj.mean():+.3f}; class B n {len(b8)} avg {b8.radj.mean() if len(b8) else float('nan'):+.3f}; "
      f"A - B {(a8.radj.mean() - b8.radj.mean()) if len(b8) else float('nan'):+.3f}; by acct " + "; ".join(f"{k} {len(g)} {g.radj.mean():+.3f}" for k, g in a8.groupby('acct')))
