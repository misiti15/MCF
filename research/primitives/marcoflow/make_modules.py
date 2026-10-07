"""Write one deployable module (SIDE, GEOM, LAYERS, mask) per distinct MarcoFlow finalist mask, and verify
each against mcf.research.setup_lab.evaluate on train/valid. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2]))
from mcf.research.setup_lab import evaluate, load  # noqa: E402

FINALISTS = [  # tag, MarcoFlow stack id (window-equivalent duplicates listed in NOTES), geom chosen on valid
    ("MF-h40-open-flowsell", "heat-40+slot-open+flow-sell", "t05s1"),
    ("MF-open-flowsell-rsi5hi", "slot-open+flow-sell+rsi5-high", "t1s1"),
    ("MF-open-flowsell-vwapup", "open-after10+flow-sell+vwap-above", "t1s05"),
    ("MF-flowsell-vwapup-rsi5hi", "flow-sell+vwap-above+rsi5-high", "t1s1"),
    ("MF-945-flowsell-vwapup", "open-945-1030+flow-sell+vwap-above", "t1s05"),
    ("MF-945-flowsell-rsi5hi", "open-945-1030+flow-sell+rsi5-high", "t05s1"),
    ("MF-short-flowsell-vwapup", "dir-short+flow-sell+vwap-above", "t1s05"),
    ("MF-rsiob-flowsell-vwapup", "rsi-ob+flow-sell+vwap-above", "t1s05"),
    ("MF-open-rsiob-flowsell", "slot-open+rsi-ob+flow-sell", "t1s05"),
    ("MF-rsimidlo-flowalign-momalign", "rsi-mid-low+flow-aligned+mom-aligned", "t1s05"),
    ("MF-rsimid-flowsell-momfall", "rsi-mid+flow-sell+mom-falling", "t1s05"),
    ("MF-flowsell-momalign-rsi5hi", "flow-sell+mom-aligned+rsi5-high", "t1s05"),
    ("MF-open-rsimidhi-flowsell", "slot-open+rsi-mid-high+flow-sell", "t1s05"),
    ("MF-open-flowalign-rsi5hi", "open-after20+flow-aligned+rsi5-high", "t1s1"),
    ("MF-open-rsimidlo-flowalign", "slot-open+rsi-mid-low+flow-aligned", "t1s05"),
    ("MF-open-rsimidlo-flowsell", "open-after10+rsi-mid-low+flow-sell", "t1s05"),
]

# short side only (every finalist is short): expressions over numpy arrays named after lab columns
EXPR = {
    "dir-short": (None, "MarcoFlow direction short (heat <= -30)"),
    "heat-40": ("(np.abs(heat) >= 40)", "|heat| >= 40 (MarcoFlow heat-40)"),
    "slot-open": ("(tod >= 950) & (tod < 1100)", "bar close 09:50-10:55 ET (MarcoFlow slot-open 9:30-11, lab starts 09:50)"),
    "open-after10": ("(tod >= 950) & (tod < 1100)", "bar close 09:50-10:55 ET (MarcoFlow open-after10)"),
    "open-after20": ("(tod >= 950) & (tod < 1100)", "bar close 09:50-10:55 ET (MarcoFlow open-after20)"),
    "open-945-1030": ("(tod >= 950) & (tod < 1030)", "bar close 09:50-10:25 ET (MarcoFlow open-945-1030)"),
    "flow-sell": ("(buyPressure < -0.25)", "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)"),
    "flow-aligned": ("(buyPressure < -0.15)", "buyPressure < -0.15 (MarcoFlow flow-aligned, short)"),
    "vwap-above": ("(vwapDistPct > 0.05)", "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)"),
    "rsi5-high": ("(rsi5 > 70)", "RSI(5) > 70 (MarcoFlow rsi5-high)"),
    "rsi-ob": ("(rsi > 65)", "RSI(14) > 65 (MarcoFlow rsi-ob)"),
    "rsi-mid": ("(rsi >= 35) & (rsi <= 65)", "35 <= RSI(14) <= 65 (MarcoFlow rsi-mid)"),
    "rsi-mid-low": ("(rsi >= 45) & (rsi < 55)", "45 <= RSI(14) < 55 (MarcoFlow rsi-mid-low)"),
    "rsi-mid-high": ("(rsi >= 55) & (rsi <= 65)", "55 <= RSI(14) <= 65 (MarcoFlow rsi-mid-high)"),
    "mom-aligned": ("(rsiSlope < -1)", "RSI(14) fell > 1 point over 3 bars (MarcoFlow mom-aligned, short)"),
    "mom-falling": ("(rsiSlope < -1)", "RSI(14) fell > 1 point over 3 bars (MarcoFlow mom-falling)"),
}
COLS = ["heat", "tod", "buyPressure", "vwapDistPct", "rsi5", "rsi", "rsiSlope"]

TEMPLATE = '''"""{tag} - MarcoFlow rule stack '{sid}' re-scored on the setup lab (short, {geom}).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB {lb}, {mft} signals, signal-level only).
Lab (1c/side): train exp_r {tr:+.4f}R (n {trn}, day-t {trt}), valid exp_r {va:+.4f}R (n {van}, day-t {vat}),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) {vap:+.4f}R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "{geom}"
LAYERS = {layers}


def mask(df) -> np.ndarray:
{cols}
    with np.errstate(invalid="ignore"):
        return {expr}
'''


def main():
    res = pd.read_csv(HERE / "results.csv")
    stacks = {d["id"]: d for d in json.load(open(HERE / "stacks.json"))}
    tr = load("train", columns=COLS + ["symbol", "date"] + [f"{a}_short_{g}" for a in ("r", "win") for g in ("t1s1", "t05s1", "t1s05")])
    va = load("valid", columns=COLS + ["symbol", "date"] + [f"{a}_short_{g}" for a in ("r", "win") for g in ("t1s1", "t05s1", "t1s05")])
    out = []
    for tag, sid, geom in FINALISTS:
        keys = sid.split("+")
        parts = ["(heat <= -30)"] + [EXPR[k][0] for k in keys if EXPR[k][0]]
        layers = ["heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)"] + [EXPR[k][1] for k in keys if k != "dir-short"]
        used = [c for c in COLS if any(c in p for p in parts)]
        if any("tod" in p for p in parts) is False:
            layers.append("time window 09:50-15:00 ET (lab frame)")
        row = res[(res.id == sid) & (res.side == "short") & (res.geom == geom)].iloc[0]
        cols = "\n".join(f'    {c} = df["{c}"].to_numpy(dtype=float)' for c in used)
        src = TEMPLATE.format(tag=tag, sid=sid, geom=geom, lb=stacks[sid].get("best_lb"), mft=stacks[sid].get("mf_trades"),
                              tr=row.tr_exp_r, trn=int(row.tr_n), trt=row.tr_t_day, va=row.va_exp_r, van=int(row.va_n),
                              vat=row.va_t_day, vap=row.va_exp_r_prod, layers=json.dumps(layers, indent=4).replace("\n]", ",\n]"),
                              cols=cols, expr=" & ".join(parts))
        p = HERE / f"{tag}.py"
        p.write_text(src)
        ns = {}
        exec(compile(src, str(p), "exec"), ns)
        a, b = evaluate(tr, ns["mask"](tr), "short", geom), evaluate(va, ns["mask"](va), "short", geom)
        ok = a["n"] == row.tr_n and b["n"] == row.va_n and abs(b["exp_r"] - row.va_exp_r) < 1e-3
        out.append({"tag": tag, "id": sid, "geom": geom, "verify_ok": bool(ok), "train": a, "valid": b})
        print(tag, ok, a["n"], a["exp_r"], b["n"], b["exp_r"], flush=True)
    json.dump(out, open(HERE / "finalists_verify.json", "w"), indent=1)


if __name__ == "__main__":
    main()
