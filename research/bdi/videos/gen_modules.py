"""Write `type: lab` modules for the video-digest finalists and verify each one reproduces the scan exactly.
Usage: python research/bdi/videos/gen_modules.py      (reads finalists.json written by report.py)
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import scan  # noqa: E402
from vid_rules import BASE  # noqa: E402

DESC = {
    "MP": "Ross Cameron micro-pullback: trend beyond VWAP and EMA9, a 1..{kmax}-bar pullback that touches the {touch} level and holds VWAP{vol}, entry on the first bar making a new {ext}",
    "VT": "Ross Cameron volume {top}: new {hl} of day, {wick} wick >= 0.5 of the range, {kind}",
    "JD": "Jdub 9 EMA + VWAP ride: beyond VWAP, EMA9 beyond VWAP, the bar touches EMA9 without closing through it{trend}",
    "VA": "Fractal Flow value-area re-entry: opened outside the prior-day 70% value area, back inside ({kind}), POC still ahead",
    "BLK": "Trader Dale block retest: {L}-bar block with range <= {c}% ATR, breakout, >= 0.25 ATR extension, first POC retest",
    "LVN": "Fractal Flow LVN air pocket: close beyond the 6-bar extreme, composite-profile density ahead < {a} x POC",
    "AVR": "Jumpstart AVWAP first retest ({anchor} anchor): >= 0.3 ATR departure, first touch holds{delta}",
    "AVF": "Jumpstart AVWAP fade ({anchor} anchor): {k} SD extension on fading volume, counter-trend",
}
EXIT_TXT = {"t1s1": "lab t1s1 (+1R / -1R)", "t05s1": "lab t05s1 (+0.5R / -1R)", "t1s05": "lab t1s05 (+1R / -0.5R)",
            "jd": "STRUCTURAL jd: exit on a 5-min close through the closer of EMA9/VWAP, 2R hard stop",
            "e9c1": "STRUCTURAL e9c1: exit on a 1-min close through the 1-min EMA9, 2R hard stop",
            "vt": "STRUCTURAL vt: stop beyond the 3-bar extreme, exit at the next volume top", "vt9": "STRUCTURAL vt9: vt + 5-min close through EMA9",
            "tx": "STRUCTURAL tx: hold to 15:55, 2R hard stop", "poc": "STRUCTURAL poc: target prior-day POC, stop beyond the session extreme",
            "poc2": "STRUCTURAL poc2: target the opposite prior-day VA edge, stop beyond the session extreme",
            "avw": "STRUCTURAL avw: target a touch of the anchored VWAP, 1R stop", "blk": "STRUCTURAL blk: limit at the block POC, stop beyond VAL/VAH, target the breakout extreme"}
LTXT = {"rvol15": "cumulative RVOL >= 1.5", "rvol2": "cumulative RVOL >= 2", "vwap_with": "price on the trade side of VWAP",
        "vwap_against": "price on the far side of VWAP (fade)", "e9_with": "close beyond EMA9 on the trade side",
        "m15_with": "15-minute close beyond its EMA9 and VWAP on the trade side", "rsi5_hi": "RSI(5) >= 70", "rsi5_lo": "RSI(5) <= 30",
        "flowsell": "buyPressure < -0.25 (flow-sell)", "flowbuy": "buyPressure > 0.25 (flow-buy)", "gap_with": "gap >= 1% in the trade direction",
        "gap_against": "gap >= 1% against the trade direction", "gapper": "abs(gap) >= 2%", "orb_with": "close beyond the 15-min opening range",
        "dsma20_with": "close beyond the daily SMA20 on the trade side", "pdroom": "no prior-day high/low within 0.5 ATR ahead"}

TEMPLATE = '''"""{name} - BDI video-digest finalist (2026-10-08), research/bdi/videos.
{desc}
Side {side}; exit {exit_txt}; window {w0}-{w1} ET.
Train (06-30..08-25): n {tr_n}, exp {tr_exp:+.4f}R, day-t {tr_t:.2f}; valid (08-26..09-15): n {va_n}, exp {va_exp:+.4f}R, day-t {va_t:.2f},
ex-best-day {va_exbest:+.4f}R. After costs (production haircut / 1c+1bps per side +2c stops). Plateau positive.
{struct_note}
LIVE NEEDS: LabStrategy.generate must join features.day_features(ctx.bars, <prior-session 1-minute bars>, ctx.prior5,
ctx.avg_cum_volume, ctx.atr) and set d_sma20 = ctx.sma20, atr_b = ctx.atr. DayContext does not carry the prior
session's 1-minute bars today (needed for the prior-day profile and prior-day anchors).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from vid_rules import layer, trig  # noqa: E402  (the scanner's own rule code)

SIDE = "{side}"
GEOM = {geom}
EXIT = "{exit}"
LAYERS = {layers_txt}
SPEC = {spec}
REQUIRES = "features.day_features columns + lab frame columns (rsi5, buyPressure, gap, vwapDistPct, volumeRatio, dist_pdh_atr, dist_pdl_atr, atr_d)"


def mask(df) -> np.ndarray:
    D = {{k: df[k].to_numpy() for k in df.columns if k not in ("symbol", "date")}}
    if "atr_b" not in D:
        D["atr_b"] = D["atr_d"]
    s = 1 if SIDE == "long" else -1
    m = np.asarray(trig(D, SPEC["fam"], s, SPEC["var"], SPEC["params"], SPEC["exit"]), bool)
    for nm in SPEC["layers"]:
        m &= np.asarray(layer(D, nm, s), bool)
    tod = np.asarray(D["tod"], float)
    return m & (tod >= SPEC["window"][0]) & (tod <= SPEC["window"][1])
'''


def describe(fam, v, side):
    s = side == "long"
    f = dict(v)
    if fam == "MP":
        f.update(vol=", on lighter volume" if v["vol"] == "light" else "", ext="high" if s else "low",
                 touch={"e9": "EMA9", "vw": "VWAP", "any": "EMA9 or VWAP"}[v["touch"]])
    if fam == "VT":
        f.update(top="bottom (long)" if s else "top (short)", hl="low" if s else "high", wick="lower" if s else "upper",
                 kind="volume = today's peak" if v["kind"] == "peak" else "volumeRatio >= 2")
    if fam == "JD":
        f.update(trend=", >= 80% of closes on that side of VWAP" if v["trend"] == "strong" else "")
    if fam == "AVR":
        f.update(delta=", bar closes in the trade direction" if v["delta"] == "green" else "")
    return DESC[fam].format(**f)


def write(rows, sc):
    out = []
    for k, r in enumerate(rows, 1):
        v = json.loads(r["var"])
        fam, side, ex = r["fam"], r["side"], r["exit"]
        lay = [x for x in r["layers"].split("+") if x != "-"]
        tag = "-".join([fam.lower()] + [str(x) for x in v.values()] + lay + [side, r["window"], ex]).replace(".", "")
        name = f"VID{k}-{tag}"
        w = scan.WIN[r["window"]]
        spec = {"fam": fam, "var": v, "params": dict(BASE[fam]), "exit": ex, "layers": lay, "window": list(w)}
        struct = ex not in ("t1s1", "t05s1", "t1s05")
        txt = TEMPLATE.format(
            name=name, desc=describe(fam, v, side), side=side, exit_txt=EXIT_TXT[ex], w0=w[0], w1=w[1],
            tr_n=r["tr_n"], tr_exp=r["tr_exp"], tr_t=r["tr_t"], va_n=r["va_n"], va_exp=r["va_exp"], va_t=r["va_t"],
            va_exbest=r["va_exbest"],
            struct_note=("STRUCTURAL EXIT: LabStrategy only runs fixed target/stop geometries; this exit needs new exit code "
                         "(see NOTES.md section 7). GEOM is None." if struct else "Lab geometry: LabStrategy runs this exit as is."),
            geom=("None" if struct else f'"{ex}"'), exit=ex, layers_txt=json.dumps([describe(fam, v, side)] + [LTXT[x] for x in lay]
                                                                                      + [f"bar close {w[0]}-{w[1]} ET"], indent=4),
            spec=json.dumps(spec))
        path = HERE / f"{name}.py"
        path.write_text(txt)
        # verify: module mask on the scan frame reproduces the scan's n and expectancy
        import importlib.util
        sp = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        m = np.asarray(mod.mask(sc.df), bool)
        rr = sc.outcome(1 if side == "long" else -1, ex, v, fam, spec["params"])
        m &= np.isfinite(rr)
        i = np.flatnonzero(m)
        st = sc.stats(i, rr[i])
        ok = st["tr"]["n"] == r["tr_n"] and st["va"]["n"] == r["va_n"] and abs(st["va"]["exp"] - r["va_exp"]) < 1e-6
        out.append({"module": path.name, "tr_n": st["tr"]["n"], "tr_exp": round(float(st["tr"]["exp"]), 4), "va_n": st["va"]["n"],
                    "va_exp": round(float(st["va"]["exp"]), 4), "reproduces_scan": bool(ok)})
        print(out[-1])
    json.dump(out, open(HERE / "finalists_verify.json", "w"), indent=1)


if __name__ == "__main__":
    rows = json.load(open(HERE / "finalists.json"))
    sc = scan.S(scan.frame())
    write(rows, sc)
