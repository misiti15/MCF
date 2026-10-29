"""Replay the candidate size/brake rules on Primary's LIVE paper trades (run 1, current-8 setups, every session they
traded in Primary since 10-06), after costs. Weights only (every trade kept); ST-P is in the live record from 10-29
only, so a D0 replay for earlier days is also shown (block after the setup's realized day R <= -2).
Usage: python live_rules.py <scratch-pr29>   Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"
t = pd.read_csv(S / "live_all.csv"); t = t[t.cur].copy()
t["nt"] = pd.to_datetime(t.nt); t["xt"] = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
t["fam"] = np.where(t.strategy.str.match(r"^(RW3|RW5|MF2|MF4)"), "S", t.strategy.str.split("-").str[0])
t = t.sort_values("nt").reset_index(drop=True)
fs, acs, sr, seq = [], [], [], []
for r in t.itertuples():
    d = t[(t.date == r.date) & (t.xt <= r.nt)]
    fs.append(int(((d.fam == "S") & (d.exit_reason == "stop")).sum()))
    acs.append(int((d.exit_reason == "stop").sum()))
    sr.append(d[d.strategy == r.strategy].R.sum())
    o = t[(t.date == r.date) & (t.symbol == r.symbol) & (t.side == r.side) & (t.id != r.id) & (t.nt <= r.nt) & (t.xt > r.nt)]
    seq.append(1 + len(o))
t["fam_stops"], t["acct_stops"], t["setup_real"], t["lot_seq"] = fs, acs, sr, seq
t["poll"] = t.nt.dt.floor("5min"); t["poll_n"] = t.groupby(["date", "symbol", "side", "poll"]).id.transform("size")
t["stp_block"] = (t.setup_real <= -2) & (t.date < "2026-10-29")       # ST-P live from 10-29 (already in the record)
F = lambda n, w=0.5: np.where((t.fam == "S") & (t.fam_stops >= n), w, 1.0)
RULES = {"live as traded": np.ones(len(t)), "D0 ST-P on earlier days": np.where(t.stp_block, 0.0, 1.0),
         "fam>=2 stops half": F(2), "fam>=3 stops half": F(3), "fam>=4 stops half": F(4), "fam>=3 w0.33": F(3, 1 / 3),
         "poll-split": 1 / t.poll_n, "later lots half": np.where(t.lot_seq >= 2, 0.5, 1.0), "harmonic": 1 / t.lot_seq,
         "acct>=3 stops half": np.where(t.acct_stops >= 3, 0.5, 1.0), "poll-split x fam>=3 half": (1 / t.poll_n) * F(3)}
rows = []
for name, w in RULES.items():
    w = np.asarray(w, float); x = t.assign(w=w, wr=w * t.R, wu=w * t.pnl_adj)
    day = x.groupby("date").agg(R=("wr", "sum"), usd=("wu", "sum"))
    c = day.R.cumsum()
    rows.append(dict(rule=name, trades=int((w > 0).sum()), avgR_per_trade=x[w > 0].R.mean(), R_per_risk=x.wr.sum() / x.w.sum(),
                     totR=x.wr.sum(), usd=x.wu.sum(), worst_day=day.R.min(), today_R=day.R.get("2026-10-29", np.nan),
                     today_usd=day.usd.get("2026-10-29", np.nan), d1022_R=day.R.get("2026-10-22", np.nan), red_days=int((day.R < 0).sum()),
                     maxdd=float((c.cummax() - c).max()), exbest_R=x.wr.sum() - day.R.max(), days=len(day)))
pd.set_option("display.width", 250)
print(f"live current-8 Primary trades {len(t)}, sessions {t.date.nunique()} ({t.date.min()}..{t.date.max()})")
print(pd.DataFrame(rows).round(3).to_string(index=False))
t.to_csv(S / "live_ctx.csv", index=False)
