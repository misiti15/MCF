"""Integrity check (NOTES 1.1): dense arrays vs lab frames (close, fromOpen) and SPY/QQQ vwapDistPct rebuilt from
5-minute bars. Writes parity.json. Educational only - not financial advice."""
import json
import numpy as np
import pandas as pd
from common import HERE, bars, lib

meta, C5, V5, O0, CL = bars()
si = {s: i for i, s in enumerate(meta["syms"])}
di = {d: i for i, d in enumerate(meta["dates"])}
out = {}
rng = np.random.default_rng(1)
tot = okc = okf = 0
for mo in ["2025-04", "2025-10", "2026-06"]:
    df = lib.load_month(mo, ["symbol", "date", "tod", "close", "fromOpen", "vwapDistPct", "high", "low"])
    s = df.sample(200000, random_state=1)
    j = s["symbol"].map(si).to_numpy(); d = s["date"].map(di).to_numpy()
    b = (((s["tod"] // 100) * 60 + s["tod"] % 100) - 575) // 5
    c = C5[j, d, b.to_numpy()]
    fo = (c / O0[j, d] - 1) * 100
    okc += int((np.abs(c - s["close"].to_numpy()) <= 0.005 + 1e-4 * s["close"].to_numpy()).sum())
    okf += int((np.abs(fo - s["fromOpen"].to_numpy()) <= 0.02).sum())
    tot += len(s)
out["close_match_share"] = round(okc / tot, 5)
out["fromOpen_match_share"] = round(okf / tot, 5)
out["rows_sampled"] = tot
print(out)
(HERE / "parity.json").write_text(json.dumps(out, indent=1))
