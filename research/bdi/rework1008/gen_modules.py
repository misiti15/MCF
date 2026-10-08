"""Write the finalist LabStrategy modules (SIDE, GEOM, LAYERS, mask(df)) and verify each against the scan numbers.
Educational only - not financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from grid import EXPR, WINDOWS  # noqa: E402

FINALISTS = [  # id, family-conds, window, side, geom, min_adv, title, lineage note
    ("RW1-gapdn-bounce-flowsell-short", ["heat<=-20", "bp<-0.35", "rsi55-65", "gap<0"], "w0950_1100", "short", "t1s1", 95e6,
     "gap-down name bouncing to RSI 55-65 while heavy net selling persists", "MF2 (MF-open-rsimidhi-flowsell)"),
    ("RW2-exhaustion-noon-adv150-short", ["rsi5>90", "sma20>1.0", "bear_div"], "w1200_1500", "short", "t1s1", 150e6,
     "exhaustion_short opened to 12:00 on ADV >= 150M names", "exhaustion_short (volume_flip_1)"),
    ("RW3-gapdn-rsi5pop-flowsell-short", ["heat<=-20", "bp<-0.35", "rsi5>80", "gap<0"], "w0950_1100", "short", "t1s1", 95e6,
     "gap-down name with a sharp RSI(5) pop into heavy net selling", "MF3 (MF-open-flowsell-rsi5hi)"),
    ("RW4-ns3-adv150-short", ["vwap_reclaim", "dn>2%", "above_sma50"], "am", "short", "t1s1", 150e6,
     "NS3 failed VWAP reclaim, ADV >= 150M only", "NS3-failed-vwap-reclaim-short"),
    ("RW5-heat30-flowsell-rsi5pop-gapdn-short", ["heat<=-30", "bp<-0.15", "rsi5>80", "gap<0"], "w0950_1100", "short", "t1s1",
     95e6, "bearish heat <= -30, net selling, RSI(5) pop, gap-down", "MF3 / MF5"),
    ("RW6-ns2-up3-short", ["x_sma50_up", "up>3%", "rsi>=60"], "am", "short", "t1s1", 95e6,
     "NS2 with the move-from-open floor raised from 2% to 3%", "NS2-sma50break-overbought-short"),
    ("RW7-gapdn-bounce-early-short", ["heat<=-20", "bp<-0.15", "rsi55-65", "gap<0"], "w0950_1030", "short", "t1s1", 95e6,
     "RW1 with lighter selling, 09:50-10:30 only", "MF2"),
    ("RW8-sma50up-spikefade-short", ["x_sma50_up", "up>3%", "rsi<=30"], "all", "short", "t1s1", 95e6,
     "close crosses above SMA50 on a >3% up day while RSI(14) <= 30", "NS2 (scan neighbour)"),
]

NAMES = {"rsi": "rsi", "rsi5": "rsi5", "sma20": "sma20_dist_pct", "sma50": "sma50_dist_pct", "vwap": "vwapDistPct",
         "vr": "volumeRatio", "fo": "fromOpen", "gap": "gap", "heat": "heat", "bp": "buyPressure", "bdiv": "bear_div",
         "udiv": "bull_div", "uw": "upper_wick", "lw": "lower_wick", "tod": "tod"}

TEMPLATE = '''"""{id} - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). {title}.
Lineage: {lineage}. Side {side}, exit {geom} (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv {adv:.0f} and window [{lo}, {hi}] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train {tr_exp:+.3f}R t {tr_t:.2f} n {tr_n};
valid {va_exp:+.3f}R t {va_t:.2f} n {va_n}. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "{side}"
GEOM = "{geom}"
LAYERS = {layers!r}


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

{body}
    with np.errstate(invalid="ignore"):
        return {expr} & (tod >= {lo}) & (tod <= {hi})
'''

LAYER_TXT = {
    "heat<=-20": "MarcoFlow heat <= -20 (bearish)", "heat<=-30": "MarcoFlow heat <= -30 (bearish)",
    "bp<-0.35": "buyPressure < -0.35 (heavy net selling, 19 bars)", "bp<-0.15": "buyPressure < -0.15 (net selling)",
    "rsi55-65": "55 <= RSI(14) <= 65", "rsi5>80": "RSI(5) > 80", "gap<0": "gapped down at the open",
    "rsi5>90": "RSI(5) > 90", "sma20>1.0": "close > 1% above the 5-min SMA20",
    "bear_div": "bearish RSI divergence (20-bar high, RSI(14) > 5 below its 20-bar max)",
    "vwap_reclaim": "close crosses above VWAP on this bar", "dn>2%": "stock down > 2% from the open",
    "above_sma50": "close above the 5-min SMA50", "x_sma50_up": "close crosses above the 5-min SMA50 on this bar",
    "up>3%": "stock up > 3% from the open", "rsi>=60": "RSI(14) >= 60", "rsi<=30": "RSI(14) <= 30",
}


def body_for(expr):
    used = [v for v in NAMES if v in expr.replace("p_", " ")] + [v for v in ("hod", "lod", "mv") if v in expr]
    lines = []
    for v, c in NAMES.items():
        if v in used or v == "tod" or f"p_{v}" in expr:
            lines.append(f"    {v} = col({c!r})")
    for v in ("rsi", "sma20", "sma50", "vwap"):
        if f"p_{v}" in expr:
            lines.append(f"    p_{v} = prev({v})")
    if "mv" in expr:
        lines.append("    mv = (col('close') - col('close') / (1 + fo / 100)) / col('atr_d')")
    if "hod" in expr or "lod" in expr:
        raise NotImplementedError
    return "\n".join(dict.fromkeys(lines))


def main():
    from combos import Ctx
    from lib import stats

    g = pd.concat([pd.read_parquet(HERE / "data" / "gated.parquet"), pd.read_parquet(HERE / "data" / "extra.parquet")])
    outdir = HERE / "modules"
    outdir.mkdir(exist_ok=True)
    cx = Ctx()
    ver = {}
    for fid, conds, w, side, geom, adv, title, lin in FINALISTS:
        lo, hi = WINDOWS[w]
        expr = " & ".join(EXPR[c] for c in conds)
        lab = "+".join(conds)
        if adv > 95e6:
            src = g[(g.family == "F6") & (g.conds.str.startswith(f"ADV>={int(adv / 1e6)}M[")) & (g.conds.str.contains(f":{lab}@{w}]", regex=False))
                    & (g.side == side) & (g.geom == geom)].iloc[0]
        else:
            src = g[(g.conds == lab) & (g.window == w) & (g.side == side) & (g.geom == geom)].iloc[0]
        layers = [LAYER_TXT[c] for c in conds] + [f"{lo // 100:02d}:{lo % 100:02d}-{hi // 100:02d}:{hi % 100:02d} ET (bar close)"]
        if adv > 95e6:
            layers.append(f"ADV >= {adv / 1e6:.0f}M (set min_adv in the YAML)")
        code = TEMPLATE.format(id=fid, title=title, lineage=lin, side=side, geom=geom, adv=adv, lo=lo, hi=hi,
                               tr_exp=src.tr_exp, tr_t=src.tr_t, tr_n=int(src.tr_n), va_exp=src.va_exp, va_t=src.va_t,
                               va_n=int(src.va_n), layers=layers, body=body_for(expr), expr=expr)
        path = outdir / f"{fid}.py"
        path.write_text(code)
        spec = importlib.util.spec_from_file_location(fid.replace("-", "_"), path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        res = {}
        for s, sp in cx.sp.items():
            mk = np.asarray(m.mask(sp.df), bool) & (np.nan_to_num(sp.adv) >= adv if adv > 95e6 else True)
            st = stats(sp, sp.first_per_day(np.flatnonzero(mk)), m.SIDE, m.GEOM)
            res[s] = {"n": st["n"], "exp": round(st["exp"], 4), "t": round(st["t"], 3)}
        ok = (res["train"]["n"] == src.tr_n and res["valid"]["n"] == src.va_n and abs(res["train"]["exp"] - src.tr_exp) < 1e-3
              and abs(res["valid"]["exp"] - src.va_exp) < 1e-3)
        ver[fid] = {**res, "matches_scan": bool(ok), "min_adv": adv, "window": [lo, hi]}
        print(fid, res, "MATCH" if ok else "MISMATCH")
    (HERE / "verify.json").write_text(json.dumps(ver, indent=1))


if __name__ == "__main__":
    main()
