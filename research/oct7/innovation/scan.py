"""BD innovation scan (2026-10-08). Grids are pre-declared below; every configuration is counted.
Train = 2026-07-15..08-25 (30 sessions), valid = 08-26..09-15 (14 sessions). Locked data never read.
Families:
  A  short-horizon RSI(2/3/4) layer on the live lab-replicable setups (heat_fade_short, heat_fade_long,
     exhaustion_short). ORB is an engine setup and is not in the lab frame.
  B  RSI(2/3/4) extremes as a primitive, both sides (fade and follow), 5 windows.
  C  extended opening swing: fade (owner's PENG/BKV read) and follow (what orb20_a did), up and down.
  D  web ideas wi-*: Williams vol breakout, red-to-green, lunch reversal, overreaction fade,
     VWAP first pullback, EOD reversal (14:30-15:00 proxy), narrow-IB extension.
  E  owner's RIOT read: short the bounce on a down day after 10:30 (short the drop, don't fade the rip),
     and an RSI(3) bounce-timing layer on the gap-down afternoon short primitive.
Output: research/oct7/innovation/scan_results.csv. Educational only - not financial advice."""
import itertools
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/innovation")
sys.path.insert(0, "research/setups2/candidates")
sys.path.insert(0, "research/heat/candidates")
import bdlib as B  # noqa: E402

GEOMS = ["t1s1", "t05s1", "t1s05"]
WINDOWS = {"W1": (950, 1030), "W2": (1030, 1130), "W3": (1130, 1300), "W4": (1300, 1430), "W5": (1430, 1500)}


def c(df, k):
    return df[k].to_numpy(dtype=float)


def specs():
    """yield (family, tag, params, side, window, geoms, mask_fn)"""
    import regime_5
    import regime_9
    import volume_flip_1 as vf

    # ---- A: RSI layer on live setups (live geometry t1s1 only)
    parents = {
        "hfs": ("short", (950, 1030), lambda d: regime_9.score(d) <= regime_9.SHORT_AT),
        "hfl": ("long", (1105, 1330), lambda d: regime_5.score(d) >= regime_5.LONG_AT),
        "exh": ("short", (1300, 1500), lambda d: vf.mask(d)),
    }
    for p, (side, win, fn) in parents.items():
        yield ("A0", f"A0-{p}-parent", {"parent": p}, side, win, ["t1s1"], fn)
        for n in (2, 3, 4):
            xs = (50, 60, 70, 80, 90) if side == "short" else (10, 20, 30, 40, 50)
            for x in xs:
                if side == "short":
                    f = (lambda fn, n, x: lambda d: fn(d) & (c(d, f"rsi{n}") >= x))(fn, n, x)
                else:
                    f = (lambda fn, n, x: lambda d: fn(d) & (c(d, f"rsi{n}") <= x))(fn, n, x)
                yield ("A", f"A-{p}-rsi{n}{'ge' if side == 'short' else 'le'}{x}", {"parent": p, "n": n, "x": x}, side, win, ["t1s1"], f)

    # ---- B: RSI extremes primitive
    for n, (wn, win), mode in itertools.product((2, 3, 4), WINDOWS.items(), ("hi", "lo")):
        for x in ((80, 90, 95) if mode == "hi" else (20, 10, 5)):
            f = (lambda n, x, mode: (lambda d: c(d, f"rsi{n}") >= x) if mode == "hi" else (lambda d: c(d, f"rsi{n}") <= x))(n, x, mode)
            for side in ("long", "short"):
                yield ("B", f"B-rsi{n}{mode}{x}-{side}-{wn}", {"n": n, "mode": mode, "x": x, "w": wn}, side, win, GEOMS, f)

    # ---- C: extended opening swing, fade and follow
    def swing_mask(d, up, t0, k, stall):
        if up:
            run = c(d, f"up_run_{t0}")
            same = c(d, "hod_px") <= c(d, f"hod_{t0}") * (1 + 1e-6)          # no new high since T0
            pb = (c(d, "hod_px") - c(d, "close")) / c(d, "atr_d")
        else:
            run = c(d, f"dn_run_{t0}")
            same = c(d, "lod_px") >= c(d, f"lod_{t0}") * (1 - 1e-6)
            pb = (c(d, "close") - c(d, "lod_px")) / c(d, "atr_d")
        m = (run >= k) & same
        if stall.startswith("pb"):
            m &= pb >= float(stall[2:])
        elif stall == "rsi3x":
            m &= (c(d, "rsi3") < 50) if up else (c(d, "rsi3") > 50)
        elif stall == "vwap":
            m &= (c(d, "vwapDistPct") < 0) if up else (c(d, "vwapDistPct") > 0)
        return m

    for up, t0, k, stall, mode in itertools.product((True, False), (950, 1000, 1010), (0.5, 0.75, 1.0, 1.5),
                                                    ("none", "pb0.1", "pb0.25", "pb0.5", "rsi3x", "vwap"), ("fade", "follow")):
        side = ("short" if up else "long") if mode == "fade" else ("long" if up else "short")
        win = (max(1000, t0 + (5 if t0 % 100 < 55 else 45)), 1130)
        f = (lambda up, t0, k, stall: lambda d: swing_mask(d, up, t0, k, stall))(up, t0, k, stall)
        yield ("C", f"C-{mode}-{'up' if up else 'dn'}-T{t0}-k{k}-{stall}", {"mode": mode, "up": up, "t0": t0, "k": k, "stall": stall},
               side, win, GEOMS, f)

    # ---- D: web ideas
    for k, wn, side in itertools.product((0.4, 0.6, 0.8, 1.0), ("am", "day"), ("long", "short")):
        win = (950, 1130) if wn == "am" else (950, 1500)
        f = (lambda k, side: (lambda d: c(d, "move_atr") >= k) if side == "long" else (lambda d: c(d, "move_atr") <= -k))(k, side)
        yield ("D1", f"D1-volbo-k{k}-{wn}-{side}", {"k": k, "w": wn}, side, win, GEOMS, f)
    for g, v, side in itertools.product((0.5, 1.0, 2.0), (0.0, 1.5), ("long", "short")):
        if side == "long":
            f = (lambda g, v: lambda d: (c(d, "gap") <= -g) & (c(d, "pc_atr") > 0) & (c(d, "volumeRatio") >= v))(g, v)
        else:
            f = (lambda g, v: lambda d: (c(d, "gap") >= g) & (c(d, "pc_atr") < 0) & (c(d, "volumeRatio") >= v))(g, v)
        yield ("D2", f"D2-r2g-g{g}-v{v}-{side}", {"g": g, "v": v}, side, (950, 1300), GEOMS, f)
    for fo, x, side in itertools.product((2.0, 3.0, 5.0), (65, 75), ("long", "short")):
        if side == "short":
            f = (lambda fo, x: lambda d: (c(d, "fromOpen") >= fo) & (c(d, "rsi") >= x) & (c(d, "volumeRatio") < 1))(fo, x)
        else:
            f = (lambda fo, x: lambda d: (c(d, "fromOpen") <= -fo) & (c(d, "rsi") <= 100 - x) & (c(d, "volumeRatio") < 1))(fo, x)
        yield ("D3", f"D3-lunch-fo{fo}-rsi{x}-{side}", {"fo": fo, "x": x}, side, (1200, 1330), GEOMS, f)
    for rng, q, wn, side in itertools.product((1.0, 1.5, 2.0), (0.3, 0.5), ("mid", "late"), ("long", "short")):
        win = (1000, 1300) if wn == "mid" else (1000, 1500)
        if side == "short":
            f = (lambda rng, q: lambda d: ((c(d, "up_run") + c(d, "dn_run")) >= rng) & (np.abs(c(d, "move_atr")) <= q * (c(d, "up_run") + c(d, "dn_run"))) & (c(d, "dist_hod_atr") <= 0.1))(rng, q)
        else:
            f = (lambda rng, q: lambda d: ((c(d, "up_run") + c(d, "dn_run")) >= rng) & (np.abs(c(d, "move_atr")) <= q * (c(d, "up_run") + c(d, "dn_run"))) & (c(d, "dist_lod_atr") <= 0.1))(rng, q)
        yield ("D4", f"D4-overreact-r{rng}-q{q}-{wn}-{side}", {"rng": rng, "q": q, "w": wn}, side, win, GEOMS, f)
    for x, vol, side in itertools.product((1.0, 2.0, 3.0), ("any", "lt1"), ("long", "short")):
        vm = (lambda vol: (lambda d: c(d, "volumeRatio") < 1) if vol == "lt1" else (lambda d: np.ones(len(d), bool)))(vol)
        if side == "long":
            f = (lambda x, vm: lambda d: (c(d, "fromOpen") > 0) & (c(d, "vwap_max") >= x) & (np.abs(c(d, "vwapDistPct")) <= 0.1) & vm(d))(x, vm)
        else:
            f = (lambda x, vm: lambda d: (c(d, "fromOpen") < 0) & (c(d, "vwap_min") <= -x) & (np.abs(c(d, "vwapDistPct")) <= 0.1) & vm(d))(x, vm)
        yield ("D5", f"D5-vwappb-x{x}-{vol}-{side}", {"x": x, "vol": vol}, side, (1000, 1400), GEOMS, f)
    for fo, side in itertools.product((2.0, 3.0, 5.0), ("long", "short")):
        f = (lambda fo, side: (lambda d: c(d, "fromOpen") <= -fo) if side == "long" else (lambda d: c(d, "fromOpen") >= fo))(fo, side)
        yield ("D6", f"D6-eodrev-fo{fo}-{side}", {"fo": fo}, side, (1430, 1500), GEOMS, f)
    for x, side in itertools.product((0.5, 0.75, 1.0), ("long", "short")):
        if side == "long":
            f = (lambda x: lambda d: ((c(d, "up_run_1030") + c(d, "dn_run_1030")) <= x) & (c(d, "close") > c(d, "hod_1030")))(x)
        else:
            f = (lambda x: lambda d: ((c(d, "up_run_1030") + c(d, "dn_run_1030")) <= x) & (c(d, "close") < c(d, "lod_1030")))(x)
        yield ("D7", f"D7-ibext-x{x}-{side}", {"x": x}, side, (1035, 1200), GEOMS, f)

    # ---- E: owner's RIOT read - short the bounce on a down day; RSI(3) timing on the gap-down short
    for fo, x, (wn, win) in itertools.product((1.0, 2.0, 3.0), (70, 80, 90), (("mid", (1030, 1200)), ("aft", (1200, 1400)), ("all", (1030, 1400)))):
        f = (lambda fo, x: lambda d: (c(d, "fromOpen") <= -fo) & (c(d, "rsi3") >= x) & (c(d, "vwapDistPct") < 0))(fo, x)
        yield ("E1", f"E1-dropbounce-fo{fo}-rsi3ge{x}-{wn}", {"fo": fo, "x": x, "w": wn}, "short", win, GEOMS, f)
    for g, x in itertools.product((0.88, 1.66, 2.66), (50, 70, 85)):
        f = (lambda g, x: lambda d: (c(d, "gap") <= -g) & (c(d, "rsi3") >= x))(g, x)
        yield ("E2", f"E2-gapdn-g{g}-rsi3ge{x}", {"g": g, "x": x}, "short", (1300, 1430), GEOMS, f)
    for g in (0.88, 1.66, 2.66):   # reference primitives (no RSI layer) for E2
        f = (lambda g: lambda d: c(d, "gap") <= -g)(g)
        yield ("E2ref", f"E2ref-gapdn-g{g}", {"g": g}, "short", (1300, 1430), GEOMS, f)


def main():
    rows = []
    t0 = time.time()
    tr, va = B.load("train"), B.load("valid")
    for fam, tag, params, side, win, geoms, fn in specs():
        mtr, mva = np.asarray(fn(tr), bool), np.asarray(fn(va), bool)
        for g in geoms:
            a, b = B.score(tr, mtr, side, g, win), B.score(va, mva, side, g, win)
            rows.append({"family": fam, "tag": f"{tag}-{g}", "base_tag": tag, "geom": g, "side": side, "window": f"{win[0]}-{win[1]}",
                         **{f"p_{k}": v for k, v in params.items()}, **B.flat("tr", a), **B.flat("va", b), "gate": B.gate(a, b)})
        if len(rows) % 200 < len(geoms):
            print(len(rows), tag, round(time.time() - t0), "s", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("research/oct7/innovation/scan_results.csv", index=False)
    cnt = out[~out.family.isin(["A0", "E2ref"])]
    print("configs (excl. parents/references):", len(cnt), "gate passes:", int(cnt.gate.sum()))
    print(out[out.gate].sort_values("va_t_day", ascending=False)[["tag", "tr_n", "tr_exp_r_prod", "tr_t_day", "va_n", "va_exp_r_prod", "va_t_day", "va_ex_best", "va_edge_win", "va_edge_st"]].to_string())


if __name__ == "__main__":
    main()
