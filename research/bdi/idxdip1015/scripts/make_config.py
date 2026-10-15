"""Owner change 2026-10-15: 5 setups - V2/V3/V5 trade the day's 3x S&P pick (SPXL/UPRO, max dollar volume so far),
V1 trades TQQQ (trail and hold). Emit the proposed Testing-1 YAML (PROPOSED_CONFIG.md) and check it builds and reproduces the grid rows through
build_strategies + the production backtest path. Educational only - not financial advice."""
import numpy as np
import pandas as pd
import yaml
from common import OUT, VARIANTS, load

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.strategies.base import DayContext, t
from mcf.strategies.setups import build_strategies

TAG = {"V1": ("IDX1", "qqq100-0955"), "V2": ("IDX2", "spy075-0945"), "V3": ("IDX3", "spy075-0955"), "V5": ("IDX5", "spy050-0945")}
EXIT = {"trail": {"target": None, "trail_r": 1.0, "trail_after_r": 1.0}, "hold": {"target": None}}
PLAN = [("V1", "trail"), ("V1", "hold"), ("V2", "trail"), ("V3", "trail"), ("V5", "trail")]
CANDS = ["SPXL", "UPRO"]
setups = {}
for v, ex in PLAN:
    P = VARIANTS[v]
    inst = {"symbols": ["TQQQ"]} if v == "V1" else {"trade_candidates": CANDS, "pick": "max_dollar_volume"}
    if True:
        name = f"{TAG[v][0]}-{TAG[v][1]}-{'TQQQ' if v == 'V1' else '3x'}-{ex}"
        setups[name] = {"enabled": True, "class": "index_dip_bounce", **inst, "signal_symbol": P["signal_symbol"],
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
T = pd.read_csv(OUT / "pick3x_trades.csv", parse_dates=["date"])
costs = Costs.from_cfg(cfg["costs"])
ext = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"]["extended_slippage_per_share"]})
data = {s: load(s) for s in ["TQQQ", *CANDS, "SPY", "QQQ"]}
bad = 0
for name, st in strats.items():
    v, ex = setups[name]["testing"]["variant"], name.rsplit("-", 1)[1].upper()
    ss = setups[name]["signal_symbol"]
    syms = st.tradeable()
    got = []
    for d, ib in data[ss].items():
        if len(ib) < 380 or any(d not in data[s] for s in syms):
            continue
        peers = {ss: ib, **{s: data[s][d] for s in syms}}
        for s in syms:
            for sig in st.signals(DayContext(s, d, data[s][d], 1, 1, 1, 1, np.nan, peers=peers)):
                tr = simulate(sig, data[s][d], t("15:55"), costs)
                if tr:
                    got.append((s, tr.r_multiple))
    rule = "tqqq" if v == "V1" else "today"
    ref = T[(T.variant == v) & (T.trigger == "rec20") & (T.exit == ex) & (T.rule == rule)]
    ok = len(ref) == len(got) and np.allclose(sorted(ref.R), sorted(r for _, r in got)) and \
        sorted(ref.symbol) == sorted(s for s, _ in got)
    got = [r for _, r in got]
    ref = ref.R.to_numpy()
    bad += not ok
    print(f"{name:34s} trades {len(got):3d} grid {len(ref):3d} {'OK' if ok else 'MISMATCH'}")
print("parity:", "all OK" if not bad else f"{bad} mismatches")
