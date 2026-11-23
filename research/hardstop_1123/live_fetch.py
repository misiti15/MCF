"""hardstop_1123: Primary run-1 journal 10-23..11-23 (LR8 cost-R) + SIP 1-minute RTH bars for every traded symbol-day
and SPY (read-only Alpaca market-data GET via mcf.data.priors). Usage: python live_fetch.py CHECKOUT JOURNAL.db OUTDIR.
Educational only - not financial advice."""
import sqlite3, sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
CK, DB, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, CK)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client
con = sqlite3.connect(DB)
t = pd.read_sql("SELECT id, strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                "shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
con.close()
t["date"] = t["date"].astype(str).str[:10]
t = t[t.date >= "2026-10-23"].copy()
t["r"] = cost_r_lr8(t, load_config()).astype(float)
t["side"] = t["side"].map(lambda s: 1 if str(s).lower() in ("1", "long", "buy") else -1)
t.to_parquet(OUT / "live.parquet", index=False)
print(t.shape, t.date.nunique(), t.r.isna().sum())
if len(sys.argv) > 4:
    dc, parts = _client(), []
    for D, g in t.groupby("date"):
        syms = sorted(set(g.symbol) | {"SPY"})
        day = pd.Timestamp(D).date()
        a = datetime.combine(day, datetime.min.time()) + timedelta(hours=13)
        raw = _bars(dc, syms, a, a + timedelta(hours=8), 1, "sip")
        for s, x in raw.groupby(level=0):
            x = rth(normalize(x.droplevel(0)))
            x = x[x.index.date == day][["close"]].copy()
            x["symbol"], x["date"] = s, D
            parts.append(x)
        # SPY prior close
        p = _bars(dc, ["SPY"], a - timedelta(days=5), a, 1440, "sip") if False else None
        print(D, len(syms), flush=True)
    B = pd.concat(parts)
    B.index.name = "ts"
    B.reset_index().to_parquet(OUT / "livebars.parquet", index=False)
    print(B.shape)
