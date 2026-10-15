"""Emit the proposed Testing-1 YAML (PROPOSED_CONFIG.md) and check it builds and reproduces the grid rows through
build_strategies + the production backtest path. Educational only - not financial advice."""
import numpy as np
import pandas as pd
import yaml
from common import OUT, VARIANTS, load, sample

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.strategies.base import DayContext, t
from mcf.strategies.setups import build_strategies

TAG = {"V1": ("IDX1", "qqq100-0955"), "V2": ("IDX2", "spy075-0945"), "V3": ("IDX3", "spy075-0955"), "V5": ("IDX5", "spy050-0945")}
EXIT = {"trail": {"target": None, "trail_r": 1.0, "trail_after_r": 1.0}, "hold": {"target": None}}
PLAN = [("V1", "trail"), ("V1", "hold"), ("V2", "trail"), ("V3", "trail"), ("V5", "trail")]
setups = {}
for v, ex in PLAN:
    P = VARIANTS[v]
    for sym in P["symbols"]:
        name = f"{TAG[v][0]}-{TAG[v][1]}-{sym}-{ex}"
        setups[name] = {"enabled": True, "class": "index_dip_bounce", "symbols": [sym], "signal_symbol": P["signal_symbol"],
                        "dip_pct": P["dip_pct"], "dip_by": P["dip_by"], "entry_from": "09:50", "entry_until": "10:05",
                        "trigger": "recovery", "recovery_frac": 0.20, "stop_buffer_frac": 0.10, **EXIT[ex],
                        "scale_out_r": None,
                        "testing": {"added": "2026-10-16", "source": "research/bdi/idxdip1015", "variant": v,
                                    "bar": "forward test (owner request); research bar not met"}}
text = yaml.safe_dump({"strategies": setups}, sort_keys=False, default_flow_style=None, width=200)
(OUT / "proposed_strategies.yaml").write_text(text)

# check: builds through the production factory and reproduces the grid's trades
cfg = load_config()
cfg["strategies"] = setups
strats = {s.name: s for s in build_strategies(cfg)}
assert set(strats) == set(setups), "every proposed setup must build"
T = pd.read_csv(OUT / "trades.csv", parse_dates=["date"])
costs = Costs.from_cfg(cfg["costs"])
ext = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"]["extended_slippage_per_share"]})
data = {s: load(s) for s in {x["symbols"][0] for x in setups.values()} | {"SPY", "QQQ"}}
bad = 0
for name, st in strats.items():
    v, ex = setups[name]["testing"]["variant"], name.rsplit("-", 1)[1].upper()
    sym, ss = setups[name]["symbols"][0], setups[name]["signal_symbol"]
    got = []
    for d, bars in data[sym].items():
        ib = data[ss].get(d)
        if ib is None or len(ib) < 380:
            continue
        for sig in st.signals(DayContext(sym, d, bars, 1, 1, 1, 1, np.nan, peers={ss: ib})):
            tr = simulate(sig, bars, t("15:55"), ext if sym == "SPUU" else costs)
            if tr:
                got.append(tr.r_multiple)
    ref = T[(T.variant == v) & (T.trigger == "rec20") & (T.exit == ex) & (T.symbol == sym)].R.to_numpy()
    ok = len(ref) == len(got) and np.allclose(sorted(ref), sorted(got))
    bad += not ok
    print(f"{name:34s} trades {len(got):3d} grid {len(ref):3d} {'OK' if ok else 'MISMATCH'}")
print("parity:", "all OK" if not bad else f"{bad} mismatches")
