"""Stream 1-min release packs (gh api asset download), keep family symbol-days + SPY, delete each pack.
Educational only - not financial advice."""
import os, subprocess, pickle, json, pandas as pd
S = "<scratch>"
SET = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "L3-gap-slope-rsi5hi-FD",
       "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD"]
t = pd.read_pickle(f"{S}/trades.pkl"); x = t[t.strategy.isin(SET)]
need = x.groupby("date").symbol.apply(set)
assets = {}
for tag in ["bars-2026-10", "bars-2026-11"]:
    r = subprocess.run(["gh", "api", f"repos/misiti15/MCF/releases/tags/{tag}", "--jq", ".assets[]|[.name,.id]|@tsv"], capture_output=True, text=True)
    for line in r.stdout.split("\n"):
        if line.strip(): n, i = line.split("\t"); assets[n] = i
paths = {}
for d, syms in need.items():
    assert not ("2024-11-01" <= d <= "2025-02-28")
    a = assets.get(f"1min-{d}.parquet")
    if not a: print(d, "no pack"); continue
    f = f"{S}/pack.parquet"
    with open(f, "wb") as fh:
        r = subprocess.run(["gh", "api", "-H", "Accept: application/octet-stream", f"repos/misiti15/MCF/releases/assets/{a}"], stdout=fh)
    if r.returncode: print(d, "download failed"); continue
    m = pd.read_parquet(f, filters=[("symbol", "in", sorted(syms | {"SPY"}))]); os.remove(f)
    m["ts"] = pd.to_datetime(m.ts, utc=True).dt.tz_convert("America/New_York")
    m = m[(m.ts.dt.strftime("%H:%M") >= "09:30") & (m.ts.dt.strftime("%H:%M") < "16:00")]
    for s, b in m.groupby("symbol", observed=True):
        b = b.sort_values("ts")
        paths[(d, str(s))] = dict(m=((b.ts.dt.hour * 60 + b.ts.dt.minute) - 570).to_numpy(), o=b.open.to_numpy(),
                                  h=b.high.to_numpy(), l=b.low.to_numpy(), c=b.close.to_numpy())
    print(d, len(syms), flush=True)
pickle.dump(paths, open(f"{S}/paths.pkl", "wb"))
print("symbol-days", len(paths))
