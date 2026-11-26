"""Crypto round 3, section 1 (PREREG.md): earlier near-misses re-scored on CLEAN signal bars (traded minutes only,
after the Amendment-1 bad-print filter). Information only; NOT counted as configs.

    python research/crypto_r3/recheck.py r2   # the 10 frozen round-2 v2 near-misses, FIT + CHECK (E5b fills)
    python research/crypto_r3/recheck.py r1   # round-1 near-misses 31, 477, 459 (r1 engine E5, bar fills)
Educational only — not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.crypto import data as D  # noqa: E402
from mcf.crypto.backtest import summarize  # noqa: E402
from mcf.crypto.exec1m import Minutes, clean_prints, clean_traded  # noqa: E402

HERE = Path(__file__).parent
R1_IDS = (31, 477, 459)


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def r2() -> None:
    R2 = _mod("run_r2", ROOT / "research" / "crypto_r2" / "run_r2.py")
    t0 = time.time()
    for p in R2.CORE + R2.ALTS:
        raw = D.load_bars(p)
        if raw.empty:
            continue
        R2.MINS[p] = Minutes.from_bars(clean_prints(raw))          # fills: as round 2
        sig = clean_traded(raw)                                       # signals: traded minutes only
        for tf in (15, 60, 240, 1440):
            b = D.resample(sig, f"{tf}min", ffill=True)
            R2.FEATS[(tf, p)] = R2.build2(b, tf, btc=None if p == "BTC" else R2.FEATS[(tf, "BTC")])
    print(f"loaded in {time.time()-t0:.0f}s", flush=True)
    fz = json.loads((ROOT / "research" / "crypto_r2" / "finalists.json").read_text())
    rows = []
    for item in fz["finalists"]:
        sp = item["spec"]
        s = R2.Setup2(item["draw_id"], **{**sp, "conds": [tuple(c) for c in sp["conds"]]})
        row = {"draw_id": s.draw_id, "label": s.label()}
        for split in ("fit", "check"):
            tr, off, miss = R2.trades_for(s, split)
            sm = summarize(tr)
            row.update({f"{split}_{k}": sm[k] for k in ("n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t",
                                                         "avg_cost_r")})
        rows.append(row)
        print(json.dumps(row, default=float), flush=True)
    pd.DataFrame(rows).to_csv(HERE / "recheck_r2.csv", index=False, float_format="%.4f")


def r1() -> None:
    R1 = _mod("run_r1", ROOT / "research" / "crypto_r1" / "run_r1.py")

    def bars_clean(base, tf, start=None, end=None, cache=None):
        raw = D.load_bars(base, start, end, cache)
        if raw.empty:
            return raw
        return D.resample(clean_traded(raw), f"{tf}min", ffill=True)

    R1.bars_for = bars_clean
    fz = json.loads((ROOT / "research" / "crypto_r1" / "finalists.json").read_text())
    items = [it for it in fz["finalists"] if it["draw_id"] in R1_IDS]
    R1.load_features(tfs=tuple(sorted({it["spec"]["tf"] for it in items})))
    rows = []
    for item in items:
        sp = item["spec"]
        s = R1.Setup(item["draw_id"], sp["tf"], sp["side"], [tuple(c) for c in sp["conds"]], sp["window"],
                     sp["days"], sp["stop_atr"], sp["target_atr"], sp["hold_h"])
        row = {"draw_id": s.draw_id, "label": s.label()}
        for split in ("fit", "check"):
            sm = summarize(R1.trades_for(s, split))
            row.update({f"{split}_{k}": sm[k] for k in ("n", "avg_r", "avg_r_wo_best", "day_t", "avg_cost_r")})
        rows.append(row)
        print(json.dumps(row, default=float), flush=True)
    pd.DataFrame(rows).to_csv(HERE / "recheck_r1.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    np.seterr(all="ignore")
    {"r1": r1, "r2": r2}[sys.argv[1]]()
