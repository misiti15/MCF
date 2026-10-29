"""p2_1029 (owner Prompt 2: cold-start / trade frequency): two-year diagnosis and controlled loosening of the dormant /
low-tier Testing 1 / Testing 2 lab setups (tiers.csv). Educational only - not financial advice.

Data: research/history2y lab frames (2024-10..2026-10-07, open months only; the rule-19 locked block 2024-11..2025-02
lives in a separate directory and is never loaded - asserted below). No holdout is scored.

PRE-DECLARED (written before the first run):
  * Signals: the live module's mask (unchanged code) with its parameters, the YAML window, point-in-time adv20 >= the
    YAML min_adv, first qualifying bar per symbol-day (as LabStrategy without refire), entry at the signal bar's close.
  * Exits, own path simulation on the 5-minute frame rows after entry: R = 0.25 x daily ATR, stop dn x R / target up x R
    from the module GEOM (stop first inside a bar), flat at the 15:55 bar close; GEOM "S" (CWT09) = the module's
    structural stop (first-hour high), no target, flat 15:55. Costs: production model (mcf/research/gates.py): entry
    1c + 1 bp x time-of-day multiplier, exit 1c + 1 bp (free on a target limit fill), +2c on stop fills.
  * Diagnosis (counts only): for stack setups (ST*, NS4) every filter's bar pass rate and the leave-one-out signal
    count; for every setup each exposed threshold relaxed by 20% (count elasticity). Binding knob = the numeric
    threshold whose 20% relaxation adds the most signals.
  * Grid on the binding knob only: 5 steps of 10% (x0.9 .. x0.5 of the threshold, or x1.1 .. x1.5 when the threshold
    is an upper bound), each with and without a failure time-stop (exit at the 3rd bar's close after entry unless the
    trade reached +0.5R by then), plus the parent with the time-stop: 11 scored configurations per setup.
  * Acceptance: trades/month >= 1.25 x parent AND avg R >= parent AND day-clustered t >= max(1.5, sqrt(2 ln N)),
    N = every configuration in this study (diagnosis counts included); near-miss = within 0.3 of the bar.
Usage: python bt2y.py [workers]  -> scratch trades parquet + diag.csv   (report: report.py)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(ROOT / "research/bdi/cwt/live")]
import lib  # noqa: E402
pd.set_option("future.infer_string", False)   # speed: the masks build symbol|date keys with astype(str)
from mcf.research import gates as G  # noqa: E402
import cwt_live_lib as L  # noqa: E402

import os
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
MONTHS = lib.months()
assert not set(MONTHS) & set(lib.LOCKED_MONTHS)
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/p2")
OUT = Path(__file__).resolve().parent
GEO = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5), "S": (None, None)}
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "gap", "fromOpen", "dist_pdh_atr", "dist_pdl_atr",
        "dist_hod_atr", "dist_lod_atr", "vwapDistPct", "volumeRatio", "vol_climax", "rsi", "rsi5", "emaDiff", "macdPct",
        "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "flow3", "buyPressure", "adv20"] + \
    [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05")]


def _load(path):
    spec = importlib.util.spec_from_file_location("m_" + path.stem.replace("-", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FD = ROOT / "research/bdi/fullday"
# name: account, family, side, geom, min_adv, window, params, knobs [(param, direction)]
SET = {
    "ST3-rsi5up-short-pm-t1s1-FD": dict(acct="T1", fam="st", adv=95e6, win=(950, 1500)),
    "ST5-pdbrkup-short-mid-t05s1-FD": dict(acct="T1", fam="st", adv=95e6, win=(950, 1500)),
    "ST6-volspikeup-short-mid-t1s1-FD": dict(acct="T1", fam="st", adv=95e6, win=(950, 1500)),
    "ST8-volspikedn-long-pm-t1s1-FD": dict(acct="T1", fam="st", adv=95e6, win=(950, 1500)),
    "ST4-emadn-long-am-t1s05-FD": dict(acct="T1", fam="st", adv=95e6, win=(950, 1500)),
    "NS4-pm-vwap-reclaim-oversold-short-FD": dict(acct="T1", fam="ns4", side="short", geom="t1s05", adv=95e6, win=(950, 1500),
                                                  p=dict(rsi=30.0, fo=2.0), knobs=[("rsi", "up"), ("fo", "down")]),
    "CWT04-backside-lh-a25-short": dict(acct="T2", fam="b1", side="short", geom="t1s1", adv=95e6, win=(1030, 1500), p=dict(a=2.5, trig=2), knobs=[("a", "down")]),
    "CWT04-backside-vwaptest-a25-short": dict(acct="T2", fam="b1", side="short", geom="t1s1", adv=95e6, win=(950, 1500), p=dict(a=2.5, trig=1), knobs=[("a", "down")]),
    "CWT04-backside-lh-a15-short": dict(acct="T2", fam="b1", side="short", geom="t1s1", adv=95e6, win=(1030, 1500), p=dict(a=1.5, trig=2), knobs=[("a", "down")]),
    "CWT04-backside-vwaptest-a15-short": dict(acct="T2", fam="b1", side="short", geom="t1s05", adv=95e6, win=(950, 1500), p=dict(a=1.5, trig=1), knobs=[("a", "down")]),
    "CWT05-flush-m075-v5-long": dict(acct="T2", fam="b5", side="long", geom="t05s1", adv=95e6, win=(950, 1500), p=dict(m=0.75, v=5.0), knobs=[("m", "down"), ("v", "down")]),
    "CWT05-flush-m05-v5-long": dict(acct="T2", fam="b5", side="long", geom="t05s1", adv=95e6, win=(950, 1500), p=dict(m=0.5, v=5.0), knobs=[("m", "down"), ("v", "down")]),
    "CWT05-flush-m075-v3-long": dict(acct="T2", fam="b5", side="long", geom="t05s1", adv=95e6, win=(950, 1500), p=dict(m=0.75, v=3.0), knobs=[("m", "down"), ("v", "down")]),
    "CWT09-gapdn-vwaploss-g10-short": dict(acct="T2", fam="a7", side="short", geom="S", adv=1e6, win=(1030, 1500), p=dict(gap=10.0, trig=1), knobs=[("gap", "down")]),
    "CWT09-gapdn-bounce-g10-lowerhalf-short": dict(acct="T2", fam="a7", side="short", geom="S", adv=1e6, win=(1030, 1500), p=dict(gap=10.0, trig=2), knobs=[("gap", "down")]),
    "CWT13-vwapstretch-z075-long": dict(acct="T2", fam="b2", side="long", geom="t1s1", adv=95e6, win=(950, 1500), p=dict(z=0.75), knobs=[("z", "down")]),
    "CWT13-vwapstretch-z075-short": dict(acct="T2", fam="b2", side="short", geom="t1s1", adv=95e6, win=(1100, 1500), p=dict(z=0.75), knobs=[("z", "down")]),
    "CWT12-flag-s1-long": dict(acct="T2", fam="b4b", side="long", geom="t05s1", adv=95e6, win=(950, 1500), p=dict(s=1.0), knobs=[("s", "down")]),
}
NUMERIC_ST = {"fo_with", "fo_against", "gap_against", "gap_with", "rsi5_ext", "rsi_ext", "vol"}
UPPER_ST = {"rsi5_ext", "rsi_ext"}      # p is an extreme level: loosening moves it toward 50 (x0.9 ...)
for s, d in SET.items():
    if d["fam"] == "st":
        m = _load(FD / f"{s}.py")
        d.update(side=m.SIDE, geom=m.GEOM, p=dict(filters=[list(f) for f in m.FILTERS]),
                 knobs=[(f"flt{i}", "down") for i, (nm, pv) in enumerate(m.FILTERS) if nm in NUMERIC_ST and pv is not None])


def st_mask(name, df, filters):
    m = _load(FD / f"{name}.py")
    m.FILTERS = [tuple(f) for f in filters]
    return np.asarray(m.mask(df), bool)


def ns4_mask(df, rsi, fo, drop=None):
    v = df["vwapDistPct"].to_numpy(float)
    key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
    pv = np.r_[np.nan, v[:-1]]
    pv[np.r_[True, key[1:] != key[:-1]]] = np.nan
    with np.errstate(invalid="ignore"):
        c = {"trig": (v > 0) & (pv <= 0), "rsi": df["rsi"].to_numpy(float) <= rsi, "fo": df["fromOpen"].to_numpy(float) > fo}
    out = np.ones(len(df), bool)
    for k, x in c.items():
        if k != drop:
            out &= x
    return out, c


def kernel(name, d, df, p):
    f = d["fam"]
    if f == "st":
        return st_mask(name, df, p["filters"])
    if f == "ns4":
        return ns4_mask(df, p["rsi"], p["fo"])[0]
    if f == "b1":
        return L.b1(df, a=p["a"], trig=p["trig"])
    if f == "b5":
        return L.b5(df, m=p["m"], v=p["v"])
    if f == "a7":
        return L.a7(df, gap=p["gap"], trig=p["trig"])
    if f == "b2":
        return L.b2(df, z=p["z"], side=d["side"])
    if f == "b4b":
        return L.b4b(df, s=p["s"])
    raise KeyError(f)


def relax(d, knob, mult):
    p = json.loads(json.dumps(d["p"]))
    if knob.startswith("flt"):
        i = int(knob[3:])
        p["filters"][i][1] = round(p["filters"][i][1] * mult, 4)
    else:
        p[knob] = round(p[knob] * mult, 4)
    return p


def step_mults(direction):
    return [1 + 0.1 * k for k in range(1, 6)] if direction == "up" else [1 - 0.1 * k for k in range(1, 6)]


def first_idx(df, m, d):
    tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
    lo, hi = d["win"]
    mm = m & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= d["adv"]) & (df["atr_d"].to_numpy(float) > 0)
    return G.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), mm)


def simulate(df, idx, d, seg_end, seg_start, ts=False):
    """Path simulation from the signal bar's close; returns r (production costs) and exit kind per entry."""
    c, h, l, tod, atr = (df[k].to_numpy(float) for k in ("close", "high", "low", "tod", "atr_d"))
    s = 1.0 if d["side"] == "long" else -1.0
    up, dn = GEO[d["geom"]]
    out_r, out_k = np.empty(len(idx)), []
    for n, i in enumerate(idx):
        e = c[i]; R = 0.25 * atr[i]
        if d["geom"] == "S":       # A7 structural stop: first-hour high (bars closing through 10:30), short side
            seg0 = seg_start[i]
            ii = np.arange(seg0, i + 1)
            stop = float(np.nanmax(h[ii[tod[ii] <= 1030]])) if tod[i] >= 1030 else float(np.nanmax(h[seg0:i + 1]))
            Rs = abs(stop - e)
            if not (Rs > 0):
                out_r[n] = np.nan; out_k.append("bad"); continue
            tgt = None
        else:
            Rs = R
            stop = e - s * dn * R
            tgt = e + s * up * R
        kind, px = "eod", None
        mfe = 0.0
        j = i
        for j in range(i + 1, seg_end[i] + 1):
            if tod[j] > 1555:
                j -= 1
                break
            hs, ls = (l[j], h[j]) if s > 0 else (h[j], l[j])       # adverse, favourable extremes
            if s * (hs - stop) <= 0:
                kind, px = "stop", stop; break
            if tgt is not None and s * (ls - tgt) >= 0:
                kind, px = "target", tgt; break
            mfe = max(mfe, s * (ls - e) / Rs)
            if ts and j - i == 3 and mfe < 0.5:
                kind, px = "tstop", c[j]; break
            if tod[j] >= 1555:
                break
        if px is None:
            px = c[j]
        gross = s * (px - e) / Rs
        cost = (G.SLIP_PS + e * G.SLIP_BPS) * float(G.tod_cost_mult(np.array([tod[i]]))[0])
        cost += 0.0 if kind == "target" else (G.SLIP_PS + px * G.SLIP_BPS)
        cost += G.STOP_EXTRA if kind == "stop" else 0.0
        out_r[n] = gross - cost / Rs
        out_k.append(kind)
    return out_r, out_k


def configs(name, d):
    """(config id, params, time-stop, scored?) - diagnosis rows are counted but not scored."""
    rows = [("P", d["p"], False, True), ("P+TS", d["p"], True, True)]
    for kn, dr in d["knobs"]:
        rows.append((f"D:{kn}x{'1.2' if dr == 'up' else '0.8'}", relax(d, kn, 1.2 if dr == "up" else 0.8), False, False))
    return rows


def day_prefilter(sub, d, plan_rows):
    """Exact symbol-day prefilter for the stateful kernels: a day whose largest run off the open (b1, b4b) or largest
    6-bar drop (b5) is below the loosest threshold in the plan can never fire, so it is skipped."""
    f = d["fam"]
    if f not in ("b1", "b4b", "b5"):
        return None
    seg = sub["_seg"].to_numpy()
    c, atr = sub["close"].to_numpy(float), sub["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        if f in ("b1", "b4b"):
            open_d = c / (1 + sub["fromOpen"].to_numpy(float) / 100)
            o0 = pd.Series(open_d).groupby(seg).transform("first").to_numpy()
            a0 = pd.Series(atr).groupby(seg).transform("first").to_numpy()
            x = (sub["high"].to_numpy(float) - o0) / a0
            k = "a" if f == "b1" else "s"
        else:
            c6 = pd.Series(c).groupby(seg).shift(6).to_numpy()
            x = (c6 - c) / pd.Series(atr).groupby(seg).transform("first").to_numpy()
            k = "m"
    need = min(p[k] for _, p, _, _ in plan_rows)
    dm = pd.Series(np.nan_to_num(x, nan=-9)).groupby(seg).transform("max").to_numpy()
    return dm >= need - 1e-9


def month_job(args):
    mo, plan = args
    t0 = time.time()
    df = lib.load_month(mo, columns=COLS)
    sc = pd.Categorical(df["symbol"].astype(object)); SYM = np.asarray(sc.categories, dtype=object)
    df["symbol"] = sc.codes.astype(np.int64)                 # integer keys: the masks' astype(str) stays cheap
    dd = pd.to_datetime(pd.Series(df["date"]))
    df["date"] = (dd.dt.year * 10000 + dd.dt.month * 100 + dd.dt.day).to_numpy(np.int64)
    trades, diag = [], []
    for adv in sorted({d["adv"] for d in SET.values()}):
        day_adv = df.groupby(["symbol", "date"])["adv20"].transform("max").fillna(0).to_numpy()
        sub = df[day_adv >= adv].reset_index(drop=True)
        sy_, dt_ = sub["symbol"].to_numpy(), sub["date"].to_numpy()
        nw = np.r_[True, (sy_[1:] != sy_[:-1]) | (dt_[1:] != dt_[:-1])]
        sub["_seg"] = np.cumsum(nw)
        pos = np.arange(len(sub))
        seg_end = pd.Series(pos).groupby(sub["_seg"].to_numpy()).transform("max").to_numpy()
        seg_start = pd.Series(pos).groupby(sub["_seg"].to_numpy()).transform("min").to_numpy()
        for name, d in SET.items():
            if d["adv"] != adv:
                continue
            keep = day_prefilter(sub, d, plan[name])
            if keep is not None:
                ss = sub[keep].reset_index(drop=True)
                ps = np.arange(len(ss)); sg = ss["_seg"].to_numpy()
                se_, ss_ = (pd.Series(ps).groupby(sg).transform(f).to_numpy() for f in ("max", "min"))
            else:
                ss, se_, ss_ = sub, seg_end, seg_start
            for cid, p, ts, scored in plan[name]:
                m = kernel(name, d, ss, p)
                idx = first_idx(ss, m, d)
                if not scored:
                    diag.append(dict(setup=name, config=cid, month=mo, n=len(idx)))
                    continue
                r, k = simulate(ss, idx, d, se_, ss_, ts=ts)
                if d["geom"] != "S" and not ts:     # cross-check: the frame's 1-minute outcome, production costs
                    sd, g = d["side"], d["geom"]
                    rf = G.prod_r(ss[f"r_{sd}_{g}"].to_numpy(float)[idx], ss[f"win_{sd}_{g}"].to_numpy(float)[idx],
                                  ss["close"].to_numpy(float)[idx], ss["atr_d"].to_numpy(float)[idx], g,
                                  tod=ss["tod"].to_numpy(float)[idx])
                else:
                    rf = np.full(len(idx), np.nan)
                trades.append(pd.DataFrame(dict(setup=name, config=cid, date=pd.to_datetime(ss["date"].to_numpy()[idx].astype(str)).date,
                                                symbol=SYM[ss["symbol"].to_numpy()[idx]], tod=ss["tod"].to_numpy()[idx],
                                                r=r, r_frame=rf, exit=k)))
            # stack funnels (bar pass rates + leave-one-out) on in-window, adv-ok bars
            if d["fam"] in ("st", "ns4"):
                tod = sub["tod"].to_numpy(); lo, hi = d["win"]
                inw = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (sub["adv20"].fillna(0).to_numpy() >= adv)
                if d["fam"] == "ns4":
                    full, cc = ns4_mask(sub, d["p"]["rsi"], d["p"]["fo"])
                    for kx, x in cc.items():
                        diag.append(dict(setup=name, config=f"pass:{kx}", month=mo, n=int((x & inw).sum()), bars=int(inw.sum())))
                        lo1, _ = ns4_mask(sub, d["p"]["rsi"], d["p"]["fo"], drop=kx)
                        diag.append(dict(setup=name, config=f"LOO:{kx}", month=mo, n=len(first_idx(sub, lo1, d))))
                else:
                    fl = d["p"]["filters"]
                    for i in range(len(fl)):
                        lo1 = st_mask(name, sub, [f for j, f in enumerate(fl) if j != i])
                        diag.append(dict(setup=name, config=f"LOO:{fl[i][0]}", month=mo, n=len(first_idx(sub, lo1, d))))
                    trig_only = st_mask(name, sub, [])
                    diag.append(dict(setup=name, config="LOO:all_filters(trigger only)", month=mo, n=len(first_idx(sub, trig_only, d))))
    print(f"{mo} done {time.time() - t0:.0f}s", flush=True)
    return (pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()), pd.DataFrame(diag)


def main(workers=2, stage="diag"):
    SCR.mkdir(parents=True, exist_ok=True)
    if stage == "diag":
        plan = {s: configs(s, d) for s, d in SET.items()}
    else:   # grid on the binding knob chosen from diag.csv (binding.json)
        B = json.load(open(OUT / "binding.json"))
        plan = {}
        for s, d in SET.items():
            kn = B[s]["knob"]; dr = dict(d["knobs"])[kn]
            plan[s] = [(f"{kn}x{mu:.1f}" + ("+TS" if ts else ""), relax(d, kn, mu), ts, True)
                       for mu in step_mults(dr) for ts in (False, True)]
    with Pool(workers) as pool:
        res = pool.map(month_job, [(m, plan) for m in MONTHS])
    T = pd.concat([r[0] for r in res], ignore_index=True)
    D = pd.concat([r[1] for r in res], ignore_index=True)
    T.to_parquet(SCR / f"trades_{stage}.parquet", index=False)
    D.to_csv(OUT / f"diag_{stage}.csv", index=False)
    print(len(T), "trades;", len(D), "diag rows")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2, sys.argv[2] if len(sys.argv) > 2 else "diag")
