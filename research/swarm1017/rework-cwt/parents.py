"""Parent re-scores on the event tables (with and without the live earnings blackout) vs research/bdi/cwt/live/NOTES.md.
Educational only - not financial advice.   python parents.py <scratch>  -> parents.json"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan as SC  # noqa: E402

scr = sys.argv[1]
parts = sorted(Path(scr).glob("ev_*.parquet"))
S0 = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
S0["date"] = pd.to_datetime(S0["date"]).dt.date
S0 = S0.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
LIVE = {"B1": {"a1.5-d0.4-T2": "CWT04-backside-lh-a15-short", "a2.5-d0.4-T2": "CWT04-backside-lh-a25-short",
               "a1.5-d0.4-T1": "CWT04-backside-vwaptest-a15-short", "a2.5-d0.4-T1": "CWT04-backside-vwaptest-a25-short"},
        "B2": {"below-z0.5": "CWT13-vwapstretch-z05-long", "below-z0.75": "CWT13-vwapstretch-z075-long",
               "above-z0.5": "CWT13-vwapstretch-z05-short", "above-z0.75": "CWT13-vwapstretch-z075-short"},
        "B4a": {"k4-tc3": "CWT12-coil-k4-long", "k6-tc3": "CWT12-coil-k6-long"},
        "B4b": {"s1.0-pb0.3-0.5": "CWT12-flag-s1-long"},
        "B5": {"m0.5-v3": "CWT05-flush-m05-v3-long", "m0.5-v5": "CWT05-flush-m05-v5-long",
               "m0.75-v3": "CWT05-flush-m075-v3-long", "m0.75-v5": "CWT05-flush-m075-v5-long"},
        "A7": {"g5-T1": "CWT09-gapdn-vwaploss-g5-short", "g10-T1": "CWT09-gapdn-vwaploss-g10-short",
               "g5-T2": "CWT09-gapdn-bounce-g5-lowerhalf-short", "g10-T2": "CWT09-gapdn-bounce-g10-lowerhalf-short"}}
out = {}
for black in (False, True):
    S = S0[~S0["black"].astype(bool)].reset_index(drop=True) if black else S0
    for fam, V in SC.families().items():
        C = SC.Ctx(S, "ball" if fam == "A7" else "b95")
        validS = np.isfinite(C.R[("short", "S")][0]) if fam == "A7" else None
        for vid, prm, par, ps, pw, pe, fn in V:
            if vid not in LIVE[fam]:
                continue
            m = fn(S)
            idx = C.pick(m, pw, False, validS if pe == "S" else None)
            o = C.score(idx, ps, pe)
            k = LIVE[fam][vid]
            out.setdefault(k, {})["blackout" if black else "no_blackout"] = {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in o.items()}
            out[k]["window"], out[k]["exit"] = pw, pe
            print(k, black, o["n_all"], round(o["exp_all"], 4), round(o["t_all"], 2), "tr", round(o["exp_tr"], 3), "va", round(o["exp_va"], 3), "xs", round(o["xs_all"], 3), flush=True)
json.dump(out, open(HERE / "parents.json", "w"), indent=1)
