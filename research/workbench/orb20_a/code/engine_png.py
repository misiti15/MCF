"""Engine view of orb20_a with the builtin ORB20 class's real parts (the blueprint reads builtins as lab setups:
window 09:50-15:00 / 1R 0.25 ATR / t1s1 are NOT this setup's parts). Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-orb20a")
from mcf.report import blueprint as B, engine as E

bp = B.extract("orb20_a")
bp["side"] = "both"
P = lambda label, value, role, note="": dict(label=label, value=value, role=role, note=note, heat=None, heat_note="")
parts = {
    "INTAKE": [P("Account universe", "ADV >= $5M core, ATR >= 1.0%", "universe", "extended tier $1M with rvol >= 3.0x"),
               P("Liquidity check (class)", "price >= 5 USD, ATR >= 0.50 USD, avg >= 1M sh/day", "liquid"),
               P("Earnings blackout / PTP", "4 trading days either side; PTP excluded", "earnings"),
               P("Stocks in play", "top 20 by 09:30-09:49 rel. volume", "top_n"),
               P("Rel. volume floor", "09:30-09:49 rvol >= 1.5", "min_rvol")],
    "TIMER": [P("Opening range", "09:30-09:49 high / low (known 09:50)", "range"),
              P("Entry window", "stop order works 09:50-11:30", "window"),
              P("Refire", "one order per symbol-day", "refire")],
    "SENSORS": [P("Direction", "09:49 close vs 09:30 open", "side"),
                P("VWAP agreement", "09:49 close on the trade side of VWAP", "vwap")],
    "GATES": [P("Caps / latch / account stop", "150 lots; 3 per symbol; latch off; -300R", "cap_setup"),
              P("Cost filter", "skip if stop costs > 0.15R", "cost_filter"),
              P("Quote & spread checks", "spread <= 30 bps and <= 0.25 of stop", "quote"),
              P("Borrow (shorts)", "ETB only", "borrow")],
    "ENTRY": [P("Order", "buy stop at high +1c / sell stop at low -1c", "order",
                "live: skipped if it traded through on an earlier bar ('missed')"),
              P("Size per trade", "min(0.25% equity at risk, slot ~$950)", "size")],
    "EXHAUST": [P("Stop", "0.5 x range beyond the entry level (1R)", "stop"),
                P("Target", "0.75 x range (= +1.5R)", "target"),
                P("Time exit", "15:50 (backtest) / flatten 15:55 live", "time"),
                P("Scale-out", "none", "scale")],
}
stages, n = [], 0
for key, title, sub, color in E.STAGES:
    ps = []
    for p in parts[key]:
        n += 1
        p["pid"] = f"P{n}"
        ps.append(p)
    stages.append(dict(key=key, title=title, sub=sub, color=color, parts=ps))
out = Path(sys.argv[1])
tr, sg = E.live_trades("orb20_a")
heat = E.apply_heat(stages, tr, sg)
E.render_engine(bp, stages, heat, out)
print(out, n, "parts")
