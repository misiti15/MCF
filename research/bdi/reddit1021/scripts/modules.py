"""reddit1021 modules: generate lab modules for the finalists, score their exact lab-runnable versions (counted
configurations), and check module-vs-scan parity on frames built the way LabStrategy builds them (heat_frame over the
5-minute bars + volume + prior-day distances; optional pm/ah context columns).

    python modules.py <spec.json>
spec: list of {name, group, cfg (engine params), side (1/-1), symbols (list|null), status, desc, ctx_ext (bool)}.
Writes modules/<name>.py, module_versions.csv, verify_modules.json. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import sys

import numpy as np
import pandas as pd

from common import HERE, SCR, split_of
import engine as E
import run as RUN

from mcf.research import gates  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402

ENTRY_DOC = {
    "fib5m": ("Lab-runnable form: the signal bar is the first of the next two 5-minute bars whose range trades through the __FIB__\n"
              "retrace of the trigger candle; entry at that bar's close (LabStrategy enters at the close of the qualifying bar - it\n"
              "has no resting limit order)."),
    "close": ("Entry at the close of the trigger candle itself (no retrace wait) - the LabStrategy-native form.")}
TPL = (HERE / "scripts" / "module_template.py").read_text()


def frame_for(sym, z, ctx_ext):
    """Lab-shaped 5-minute frame for every session of `sym` (all rows 09:35..16:00)."""
    days = z["days"]
    nd = len(days)
    rows = []
    for col in ("o", "h", "l", "c", "v"):
        pass
    idx = []
    for d in range(nd):
        for k in range(78):
            if np.isfinite(z["f_c"][d, k]):
                idx.append((d, k))
    idx = np.array(idx)
    ts = pd.DatetimeIndex([pd.Timestamp(days[d] + " 09:30", tz="America/New_York") + pd.Timedelta(minutes=5 * k)
                           for d, k in idx])
    d5 = pd.DataFrame({"open": z["f_o"][idx[:, 0], idx[:, 1]], "high": z["f_h"][idx[:, 0], idx[:, 1]],
                       "low": z["f_l"][idx[:, 0], idx[:, 1]], "close": z["f_c"][idx[:, 0], idx[:, 1]],
                       "volume": z["f_v"][idx[:, 0], idx[:, 1]]}, index=ts)
    f = heat_frame(d5)
    f["volume"] = d5["volume"].to_numpy()
    LV = z["LV"]
    di = idx[:, 0]
    atr = f["atr_d"].to_numpy(float)
    atr = np.where(np.isfinite(atr) & (atr > 0), atr, 1.0)
    f["atr_d"] = atr
    f["dist_pdh_atr"] = (LV[di, 6] - f["close"].to_numpy()) / atr
    f["dist_pdl_atr"] = (f["close"].to_numpy() - LV[di, 7]) / atr
    if ctx_ext:
        f["pm_high"], f["pm_low"], f["ah_high"], f["ah_low"] = LV[di, 2], LV[di, 3], LV[di, 4], LV[di, 5]
    f["date"] = days[di]
    f["symbol"] = sym
    f["_d"] = di
    f["_k"] = idx[:, 1]
    return f.reset_index(drop=True)


def write_module(spec, numbers):
    c = dict(spec["cfg"])
    mcfg = {"type": c.get("type_", 0), "k": c.get("k", 1.5), "vol": c.get("vol", 1), "fresh": c.get("fresh", 1),
            "trend": c.get("trend", 0), "fib": c.get("fib", 0.5), "mult": c.get("mult", 2.0),
            "fammask": c.get("fammask", 31), "side_only": spec["side"], "klo": c.get("klo", 3), "khi": c.get("khi", 23),
            "entry": "close" if c.get("entry", 0) == 2 else "fib5m"}
    assert c.get("vol", 1) in (0, 1, 2) and c.get("trend", 0) in (0, 1), "module supports vol 0/1/2 and trend 0/1"
    layers = [f"{'continuation' if mcfg['type'] == 0 else 'reversal'} 5m candle through an "
              f"{'untouched' if mcfg['fresh'] else 'any (touched or not)'} level (OR/PD/SW{'/PM/AH' if spec['ctx_ext'] else ''})",
              f"candle range >= {mcfg['k']} x 5m ATR", {0: "no volume filter", 1: "volume > previous 5m bar",
                                                         2: "volume > 1.5x previous 5m bar"}[mcfg["vol"]],
              (f"retrace through the {mcfg['fib']} fib within 2 bars, entry at that bar's close" if mcfg["entry"] == "fib5m"
               else "entry at the trigger candle's close"),
              f"trigger candle closes {mcfg['klo']}..{mcfg['khi']} (bar index, 3 = 09:50, 23 = 11:30)",
              f"stop beyond the candle, target {mcfg['mult']}R, flat 15:55", "first signal of the day"]
    if mcfg["trend"] == 1:
        layers.insert(3, "trade only with own close vs session VWAP")
    src = (TPL.replace("__NAME__", spec["name"]).replace("__STATUS__", spec["status"])
           .replace("__DESC__", spec["desc"]).replace("__FIB__", str(mcfg["fib"])).replace("__MULT__", str(mcfg["mult"]))
           .replace("__NUMBERS__", numbers).replace("__ENTRY_DOC__", ENTRY_DOC[mcfg["entry"]].replace("__FIB__", str(mcfg["fib"]))).replace("__SIDE__", "long" if spec["side"] > 0 else "short")
           .replace("__SIDE_NOTE__", "the other side is a separate module")
           .replace("__SYMBOLS__", f"SYMBOLS = {spec['symbols']!r}" if spec.get("symbols") else "# no SYMBOLS: stock universe via min_adv")
           .replace("__LAYERS__", repr(layers)).replace("__CFG__", repr(mcfg)))
    p = HERE / "modules" / f"{spec['name']}.py"
    p.write_text(src)
    return p


def load_module(p):
    spec = importlib.util.spec_from_file_location("m_" + p.stem.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def engine_trades(sym, z, cfg, group):
    days = z["days"]
    if group == "idx":
        elig = np.ones(len(days), bool); tv, te = RUN.trend_arrays(z, None)
    else:
        elig = np.nan_to_num(z["adv"]) >= 95e6; tv, te = RUN.trend_arrays(z, RUN.load("SPY"))
    P = E.params(**cfg)
    tr = E.run(P, z["start"], z["m_o"], z["m_h"], z["m_l"], z["m_c"], z["m_min"], z["LV"], z["tier"], elig,
               z["f_o"], z["f_h"], z["f_l"], z["f_c"], z["f_v"], z["f_atr_prev"], z["f_ema20"], z["f_v20_prev"],
               z["f_v_prev"], z["f_c_prev"], z["f_vwap"], tv, te)
    df = pd.DataFrame(tr, columns=["d", "k", "side", "fam", "r", "gross", "kind", "fill_min", "rfrac", "entry",
                                   "exit_min", "cost", "tier", "rng_atr"])
    df["date"] = days[df.d.astype(int)]
    df["symbol"] = sym
    return df, elig


def parity(spec, syms):
    p = HERE / "modules" / f"{spec['name']}.py"
    m = load_module(p)
    cfg = dict(spec["cfg"], entry=2 if spec["cfg"].get("entry", 0) == 2 else 3, first=2, sideonly=spec["side"])
    if not spec["ctx_ext"]:
        cfg["fammask"] = cfg.get("fammask", 31) & ~(2 | 4)
    match = mod_only = eng_only = stop_diff = 0
    for sym in syms:
        z = RUN.load(sym)
        f = frame_for(sym, z, spec["ctx_ext"])
        et, elig = engine_trades(sym, z, cfg, spec["group"])
        f = f[elig[f["_d"].to_numpy()]].reset_index(drop=True)
        msk = m.mask(f)
        hits = np.flatnonzero(msk)
        mod = {(int(f["_d"].iat[i]), int(f["_k"].iat[i])): m.stop_price(f, i) for i in hits}
        # engine: fill bar = minute fill_min -> 5m bar (fill_min // 5)
        eng = {(int(r.d), int(r.fill_min) // 5): r.entry - r.side * r.rfrac * r.entry for r in et.itertuples()}
        for key, st in mod.items():
            if key in eng:
                match += 1
                if abs(eng[key] - st) > 1e-6:
                    stop_diff += 1
            else:
                mod_only += 1
        eng_only += sum(1 for key in eng if key not in mod)
    return dict(module=spec["name"], symbols=len(syms), match=match, module_only=mod_only, scan_only=eng_only,
                stop_mismatch=stop_diff)


def score_version(spec, syms, label, cfg):
    parts = []
    for sym in syms:
        z = RUN.load(sym)
        et, _ = engine_trades(sym, z, cfg, spec["group"])
        parts.append(et)
    t = pd.concat(parts)
    row = {"module": spec["name"], "version": label}
    if not len(t):
        return row
    t["split"] = split_of(t.date)
    for s in ("train", "valid", "all"):
        u = t if s == "all" else t[t.split == s]
        sm = gates.summary(u[["date", "r"]])
        row.update({f"{s}_n": sm.get("n", 0), f"{s}_exp": sm.get("exp_r"), f"{s}_t": sm.get("t"),
                    f"{s}_win": sm.get("win_rate")})
    row["all_ex_best"] = gates.summary(t[["date", "r"]]).get("ex_best_day")
    return row


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1]))
    rows, ver = [], []
    for spec in specs:
        syms = spec.get("symbols") or sorted(p.stem for p in (SCR / "prep").glob("*.npz") if p.stem not in ("SPY", "QQQ"))
        base = dict(spec["cfg"], sideonly=spec["side"])
        ent = 2 if base.get("entry", 0) == 2 else 3
        v_live = dict(base, entry=ent, first=2, fammask=base.get("fammask", 31) & ~(2 | 4))
        v_ctx = dict(base, entry=ent, first=2)
        r1 = score_version(spec, syms, "scan form (limit fill), this side", base)
        r2 = score_version(spec, syms, "module form, OR/PD/SW only (runnable now)", v_live)
        r3 = score_version(spec, syms, "module form, with PM/AH context (needs new context)", v_ctx)
        ver += [r1, r2, r3]
        fmt = lambda r: (f"train n {r.get('train_n')} {r.get('train_exp')}R t {r.get('train_t')}; valid n {r.get('valid_n')} "
                         f"{r.get('valid_exp')}R t {r.get('valid_t')}")
        numbers = ("Open history, production costs, 1-minute simulator:\n"
                   f"- scan form (resting limit at the fib, trade-through fill), this side: {fmt(r1)}\n"
                   f"- this module as runnable now (OR/PD/SW levels): {fmt(r2)}\n"
                   f"- this module with PM/AH context columns: {fmt(r3)}")
        write_module(spec, numbers)
        psyms = syms if len(syms) <= 2 else syms[:: max(1, len(syms) // 60)]
        rows.append(parity(dict(spec, ctx_ext=False), psyms))
        rows.append(dict(parity(dict(spec, ctx_ext=True), psyms), context="pm/ah columns"))
        print(rows[-2], rows[-1], flush=True)
    out = pd.DataFrame(ver)
    out.to_csv(HERE / "module_versions.csv", index=False)
    json.dump(rows, open(HERE / "verify_modules.json", "w"), indent=1)
    print(out.to_string())
