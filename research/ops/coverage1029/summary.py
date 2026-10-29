"""Tables for research/ops/coverage1029.md from funnel.py / coverage.py / live10.py outputs (<scratch>/out/).
Usage: python summary.py <scratch> <today>   Educational only - not financial advice."""
import json, sys
from pathlib import Path

S = Path(sys.argv[1]); T = sys.argv[2]
O = S / "out"
days = sorted(p.stem for p in O.glob("2026-*.json"))
SH = {"RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
      "MF2-open-rsimidhi-flowsell-FD": "MF2-FD", "MF4-h40-open-flowsell-FD": "MF4-FD", "MF4-h40-open-flowsell": "MF4",
      "ST7-rsi50dn-long-pm-t1s1-FD": "ST7", "NS1-rsidip-rsi5pop-long": "NS1", "NS5-sma50-flush-oversold-long": "NS5"}
t = json.loads((O / f"{T}.json").read_text())
print(f"## Funnel {T} (symbols; each step = same 5-minute bar, inside the setup window, cumulative)\n")
for k, v in t["setups"].items():
    f = v["funnel_traded_universe"]
    steps = [(a, b) for a, b in f.items() if not a.startswith("alone") and a != "qualifying symbol-bars"]
    alone = [x for a, x in f.items() if a.startswith("alone")][0]
    print(f"- **{SH.get(k, k)}**: " + " -> ".join(f"{a} {b}" for a, b in steps)
          + f" -> signals {v['offline_signals']} (live {v['live_signals']}, matched {v['matched']}). "
          + f"Each condition alone: {alone}. Qualifying symbol-bars {f['qualifying symbol-bars']}. "
          + f"Blackout names that would have signalled: {len(v['blackout_would_signal'])} {v['blackout_would_signal'][:8]}")
print("\n## Parity and distinct symbols per session (offline = live code on full-day SIP bars, traded universe)\n")
print("| setup | " + " | ".join(d[5:] for d in days) + " | total offline | total live | matched | distinct offline symbols | +blackout signals |")
print("|---|" + "---|" * (len(days) + 5))
tot = {}
for k in t["setups"]:
    cells, a = [], [0, 0, 0, set(), 0]
    for d in days:
        x = json.loads((O / f"{d}.json").read_text())["setups"].get(k)
        if x is None:
            cells.append("off"); continue
        cells.append(f"{x['offline_signals']}/{x['live_signals']}" + ("" if x["matched"] == x["offline_signals"] == x["live_signals"] else "*"))
        a[0] += x["offline_signals"]; a[1] += x["live_signals"]; a[2] += x["matched"]; a[3] |= set(x["offline_symbols"])
        a[4] += len(x["blackout_would_signal"])
    tot[k] = a
    print(f"| {SH.get(k, k)} | " + " | ".join(cells) + f" | {a[0]} | {a[1]} | {a[2]} | {len(a[3])} | {a[4]} |")
print("\nMismatches:")
for d in days:
    x = json.loads((O / f"{d}.json").read_text())
    for k, v in x["setups"].items():
        if v["missed_by_live"] or v["extra_in_live"]:
            print(f"- {d} {SH.get(k, k)}: missed by live {v['missed_by_live']}, extra in live {v['extra_in_live']}")
print("\nSymbols per session:", {d[5:]: json.loads((O / f'{d}.json').read_text())["symbols"] for d in days})
