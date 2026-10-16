"""S6 (long-hold) equity at the 10-16 official close: cash + held qty x SIP daily close (Alpaca market data only, read-only).
Also SPY/QQQ/IWM 10-15 -> 10-16 daily closes (gap and day). Educational only - not financial advice."""
import sys, json
from datetime import datetime, timezone
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
st = json.load(open(sys.argv[1]))
pos = st["positions"]
qty = {p["symbol"]: float(p["qty"]) for p in pos} if isinstance(pos, list) else {k: float(v["qty"]) for k, v in pos.items()}
cash = st["intraday"]["cash"]
syms = sorted(qty) + ["SPY", "QQQ", "IWM"]
r = _client().get_stock_bars(StockBarsRequest(symbol_or_symbols=syms, timeframe=TimeFrame.Day, feed="sip",
                             start=datetime(2026, 10, 14, tzinfo=timezone.utc), end=datetime(2026, 10, 16, 23, tzinfo=timezone.utc)))
df = r.df.reset_index(); df["d"] = df.timestamp.dt.tz_convert("America/New_York").dt.date.astype(str)
cl = df.pivot(index="d", columns="symbol", values="close"); op = df.pivot(index="d", columns="symbol", values="open")
inv = sum(q * cl.loc["2026-10-16", s] for s, q in qty.items())
eq = cash + inv
prev = st["intraday"]["last_equity"]
print(f"S6 10-16 close: equity {eq:.2f} (cash {cash:.2f}, invested {inv:.2f}, {len(qty)} positions); day {eq - prev:+.2f} ({(eq / prev - 1) * 100:+.2f}%) vs official 10-15 mark {prev:.2f}")
for k in ["SPY", "QQQ", "IWM"]:
    print(k, "gap %+.2f%%" % ((op.loc["2026-10-16", k] / cl.loc["2026-10-15", k] - 1) * 100), "close/close %+.2f%%" % ((cl.loc["2026-10-16", k] / cl.loc["2026-10-15", k] - 1) * 100))
