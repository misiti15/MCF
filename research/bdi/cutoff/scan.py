"""Entry-cutoff study scan + analysis (NOTES.md 0.2-0.7). One process, month by month.

  python research/bdi/cutoff/scan.py scan      # -> data/trades.parquet (every setup x set, all open sessions)
  python research/bdi/cutoff/scan.py report    # -> results.csv, pooled.csv, report.json (warm-up sessions excluded)
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from lib import LOCKED_MONTHS, load_month, months, regimes  # noqa: E402
from mcf.research import gates as G  # noqa: E402

DATA = HERE / "data"
TRADES = DATA / "trades.parquet"
WARMUP = ("2025-03-03", "2025-03-28")       # NOTES 0.1: first 20 open sessions after the locked block
N_CONFIGS = 76
T_STUDY = G.t_required(N_CONFIGS)
PRIMARY = {"exhaustion_short": (1300, "exhaustion_short"), "MF5-flowsell-vwapup-rsi5hi": (950, "MF5"),
           "NS4-pm-vwap-reclaim-oversold-short": (1130, "NS4")}
TRIES = {"exhaustion_short": 855_600, "MF5": 8_012, "NS4": 7_374}     # research/history2y/rescore.py
HEAT_CALL = re.compile(r"(regime_score\(df, \"\w+\", W, )950, 1500,")


def _exec_src(src: str, path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(src, str(path), "exec"), m.__dict__)
    return m


def setups() -> list[dict]:
    specs = json.loads((ROOT / "research/bdi/fullday/specs.json").read_text())
    out = []
    for i, s in enumerate(specs):
        path = ROOT / s["fd_module"]
        heat = path.name.startswith("heat_")
        src = path.read_text()
        if heat:
            assert len(HEAT_CALL.findall(src)) == 1, path
            src = HEAT_CALL.sub(lambda mo: f"{mo.group(1)}950, 1530,", src)
        m = _exec_src(src, path, f"fd_{i}")
        side = (("short" if m.SHORT_AT is not None else "long") if heat else m.SIDE)
        geom = "t1s1" if heat else getattr(m, "GEOM", "t1s1")
        cfg_min_adv = s["min_adv"] if not heat else 125_000_000
        base = {"mod": m, "kind": "heat" if heat else "lab", "side": side, "geom": geom, "min_adv": float(cfg_min_adv),
                "guard": hasattr(m, "vwap_band_block")}
        out.append({**base, "setup": s["name"] + "-FD", "account": "testing", "lo": 950})
        if s["name"] in PRIMARY:
            out.append({**base, "setup": s["name"], "account": "primary", "lo": PRIMARY[s["name"]][0]})
    return out


def _late(mo: str) -> pd.DataFrame:
    nxt = str(pd.Period(mo, freq="M") + 1)
    d = pads.dataset(str(DATA / "late"), format="parquet")
    x = d.to_table(filter=(pads.field("date") >= f"{mo}-01") & (pads.field("date") < f"{nxt}-01")).to_pandas()
    x["date"] = pd.to_datetime(x["date"]).dt.date
    return x


def _blocks() -> set:
    out = set()
    for root in (ROOT / "research/bdi/timeofday/data/block", DATA / "block"):
        for p in sorted(root.glob("*.parquet")):
            b = pd.read_parquet(p)
            out.update((b["symbol"].astype(str) + "|" + b["date"].astype(str) + "|" + b["tod"].astype(str)).tolist())
    return out


def trades_for(df, mk, side, geom) -> pd.DataFrame:
    """gates.lab_trades plus the exit type (target / stop / time = the 15:55 flatten)."""
    m = np.asarray(mk, bool) & np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float)) & (df["atr_d"].to_numpy(float) > 0)
    idx = G.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), m)
    lab = df[f"r_{side}_{geom}"].to_numpy(float)[idx]
    win = df[f"win_{side}_{geom}"].to_numpy(float)[idx]
    close, atr, tod = (df[c].to_numpy(float)[idx] for c in ("close", "atr_d", "tod"))
    r = G.prod_r(lab, win, close, atr, geom, tod=tod)
    up, dn = G.GEOMK[geom]
    gross = lab + 2 * G.SLIP_PS / (0.25 * atr)
    ex = np.where(win == 1, "target", np.where(gross <= -dn + 1e-6, "stop", "time"))
    return pd.DataFrame({"date": df["date"].to_numpy()[idx], "symbol": df["symbol"].to_numpy()[idx],
                         "tod": df["tod"].to_numpy()[idx].astype(int), "r": r, "exit": ex})


def _month_group(mo: str, syms: list[str]) -> pd.DataFrame:
    """One open month of history2y frames for a symbol group (+ late rows). Same guard as lib.load_month."""
    import gc
    from lib import DATA as HDATA
    if mo in LOCKED_MONTHS:
        raise PermissionError("locked block")
    f = pads.field("symbol").isin(syms)
    df = pads.dataset(str(HDATA / "frames" / f"month={mo}"), format="parquet").to_table(filter=f).to_pandas()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    nxt = str(pd.Period(mo, freq="M") + 1)
    lt = pads.dataset(str(DATA / "late"), format="parquet").to_table(
        filter=f & (pads.field("date") >= f"{mo}-01") & (pads.field("date") < f"{nxt}-01")).to_pandas()
    lt["date"] = pd.to_datetime(lt["date"]).dt.date
    df = pd.concat([df.drop(columns=["ts"]), lt[[c for c in df.columns if c != "ts"]]], ignore_index=True)
    gc.collect()
    return df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def scan(groups: int = 6):
    import gc
    sts = setups()
    blocks = _blocks()
    all_syms = sorted(pd.read_parquet(DATA / "late", columns=["symbol"])["symbol"].astype(str).unique())
    parts = DATA / "trades_parts"
    parts.mkdir(exist_ok=True)
    t0 = time.time()
    for mo in months():
        out = parts / f"{mo}.parquet"
        if out.exists():
            continue
        rows, nrows = [], 0
        for gi in range(groups):
            df = _month_group(mo, all_syms[gi::groups])
            nrows += len(df)
            tod = df["tod"].to_numpy()
            adv = df["adv20"].fillna(0).to_numpy()
            key = df["symbol"].astype(str) + "|" + df["date"].astype(str) + "|" + df["tod"].astype(str)
            df["_block"] = key.isin(blocks).to_numpy()
            del key
            cache = {}
            for s in sts:
                mk_key = s["setup"] if s["account"] == "testing" else s["setup"] + "-FD"
                if mk_key not in cache:
                    mm = next(x for x in sts if x["setup"] == mk_key)["mod"]
                    if s["guard"]:
                        mm.vwap_band_block = lambda d, k=2.0: d["_block"].to_numpy(bool)
                    with np.errstate(invalid="ignore"):
                        if s["kind"] == "heat":
                            sc = np.asarray(mm.score(df), float)
                            cache[mk_key] = (sc <= mm.SHORT_AT) if s["side"] == "short" else (sc >= mm.LONG_AT)
                        else:
                            cache[mk_key] = np.asarray(mm.mask(df), bool)
                    gc.collect()
                M = cache[mk_key] & (adv >= s["min_adv"])
                for nm, hi in (("cur", 1500), ("x1515", 1515), ("x1530", 1530)):
                    tr = trades_for(df, M & (tod >= s["lo"]) & (tod <= hi), s["side"], s["geom"])
                    tr["setup"], tr["account"], tr["set"] = s["setup"], s["account"], nm
                    rows.append(tr)
            del df, cache
            gc.collect()
        x = pd.concat(rows, ignore_index=True)
        x["symbol"] = x["symbol"].astype(str)
        x.to_parquet(out, index=False)
        print(f"{mo}: {nrows} rows, {len(x)} trades ({time.time() - t0:.0f}s)", flush=True)
    x = pd.concat([pd.read_parquet(p) for p in sorted(parts.glob("*.parquet"))], ignore_index=True)
    x.to_parquet(TRADES, index=False)
    print("trades", len(x))


# ------------------------------------------------------------------------------------------------ analysis
def diff_t(a: pd.DataFrame, b: pd.DataFrame):
    """mean(a) - mean(b) with a session-clustered SE (influence per session)."""
    if len(a) < 2 or len(b) < 2:
        return None, None
    ma, mb = a["r"].mean(), b["r"].mean()
    ua = ((a["r"] - ma) / len(a)).groupby(a["date"]).sum()
    ub = ((b["r"] - mb) / len(b)).groupby(b["date"]).sum()
    u = ua.sub(ub, fill_value=0.0)
    se = float(np.sqrt((u ** 2).sum()))
    return round(float(ma - mb), 4), (round(float((ma - mb) / se), 2) if se > 0 else None)


def stats(tr: pd.DataFrame, reg: pd.DataFrame, wf_months, n_days: int) -> dict:
    o = G.summary(tr)
    if not o.get("n"):
        return {"n": 0}
    rs = G.regime_split(tr, reg, min_n=10)
    wf = G.walk_forward(tr, months=wf_months, exclude_months=LOCKED_MONTHS)
    ex = tr["exit"].value_counts(normalize=True)
    return {"n": o["n"], "per_day": round(o["n"] / n_days, 2), "win": o["win_rate"], "exp_r": o["exp_r"], "t": o["t"],
            "ex_best_day": o["ex_best_day"], "up_n": rs["up"].get("n", 0), "up_exp": rs["up"].get("exp_r"),
            "down_n": rs["down"].get("n", 0), "down_exp": rs["down"].get("exp_r"), "flat_exp": rs["flat"].get("exp_r"),
            "wf_folds": wf["n_folds"], "wf_share": wf["share_positive"],
            "exit_target": round(float(ex.get("target", 0)), 3), "exit_stop": round(float(ex.get("stop", 0)), 3),
            "exit_time": round(float(ex.get("time", 0)), 3)}


def sets_of(t: pd.DataFrame) -> dict:
    cur = t[t["set"] == "cur"]
    x15 = t[t["set"] == "x1515"]
    x30 = t[t["set"] == "x1530"]
    return {"current": cur, "B14": cur[cur["tod"] >= 1405], "L1": x15[x15["tod"] >= 1505],
            "L2": x30[x30["tod"] >= 1520], "ext1515": x15, "ext1530": x30}


def report():
    reg = regimes()
    t = pd.read_parquet(TRADES)
    t["date"] = pd.to_datetime(t["date"]).dt.date
    # identity: <= 15:00 trades of the extended runs == current; current n == verify.json / rescore (all 426 sessions)
    ident = {}
    ver = {r["setup"]: r for r in json.loads((ROOT / "research/bdi/fullday/verify.json").read_text())["setups"]}
    for s, g in t.groupby("setup"):
        cur = g[g["set"] == "cur"].sort_values(["date", "symbol"]).reset_index(drop=True)
        same = all(
            g[(g["set"] == k) & (g["tod"] <= 1500)].sort_values(["date", "symbol"]).reset_index(drop=True)[["date", "symbol", "tod", "r"]]
            .equals(cur[["date", "symbol", "tod", "r"]]) for k in ("x1515", "x1530"))
        acct = g["account"].iloc[0]
        vr = ver.get(s if acct == "testing" else s + "-FD", {})
        ref = vr.get("n_full") if acct == "testing" else vr.get("n_current")
        ident[s] = {"le1500_identical_in_extended_runs": same, "n_current_all_sessions": int(len(cur)), "verify_json_n": ref,
                    "matches": ref == len(cur)}
    ds = t["date"].astype(str)
    t = t[(ds < WARMUP[0]) | (ds > WARMUP[1])]
    reg = reg[~((reg.index.astype(str) >= WARMUP[0]) & (reg.index.astype(str) <= WARMUP[1]))]
    n_days = len(reg)
    wf_months = sorted(set(pd.PeriodIndex(pd.to_datetime(list(reg.index)), freq="M").astype(str)))
    rows = []
    for (s, acct), g in t.groupby(["setup", "account"], sort=False):
        S = sets_of(g)
        for nm, tr in S.items():
            rows.append({"setup": s, "account": acct, "set": nm, **stats(tr, reg, wf_months, n_days)})
        for a, b in (("L1", "B14"), ("L1", "current"), ("L2", "B14"), ("L2", "current")):
            d, dt = diff_t(S[a], S[b])
            rows.append({"setup": s, "account": acct, "set": f"{a}-{b}", "exp_r": d, "t": dt})
        if acct == "primary":
            short = PRIMARY[s][1]
            for nm in ("current", "ext1515", "ext1530"):
                tr = S[nm]
                o, rs = G.summary(tr), G.regime_split(tr, reg)
                wf = G.walk_forward(tr, months=wf_months, exclude_months=LOCKED_MONTHS)
                v, f = G.verdict(o, rs, wf, TRIES[short] + N_CONFIGS)
                rows.append({"setup": s, "account": acct, "set": f"verdict_{nm}", "verdict": v, "failed": "; ".join(f),
                             "t_req": G.t_required(TRIES[short] + N_CONFIGS)})
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "results.csv", index=False)
    # pooled
    prow = []
    for pool, acct in (("pool_FD", "testing"), ("pool_primary", "primary")):
        g = t[t["account"] == acct]
        S = sets_of(g)
        for nm, tr in S.items():
            prow.append({"pool": pool, "set": nm, **stats(tr, reg, wf_months, n_days)})
        for a, b in (("L1", "B14"), ("L1", "current"), ("L2", "B14"), ("L2", "current")):
            d, dt = diff_t(S[a], S[b])
            prow.append({"pool": pool, "set": f"{a}-{b}", "exp_r": d, "t": dt})
        if acct == "testing":
            early = set((S["current"]["symbol"] + "|" + S["current"]["date"].astype(str)).tolist())
            k1 = S["L1"]["symbol"] + "|" + S["L1"]["date"].astype(str)
            l1d = S["L1"][~k1.isin(early).to_numpy()]
            early2 = early | set(k1.tolist())
            k2 = S["L2"]["symbol"] + "|" + S["L2"]["date"].astype(str)
            l2d = S["L2"][~k2.isin(early2).to_numpy()]
            for nm, tr in (("L1_dedup", l1d), ("L2_dedup", l2d)):
                # one trade per symbol-day across setups: keep the first (ties: first setup listed)
                tr = tr.sort_values(["date", "symbol", "tod"]).drop_duplicates(["date", "symbol"])
                prow.append({"pool": "pool_FD_dedup", "set": nm, **stats(tr, reg, wf_months, n_days)})
    pooled = pd.DataFrame(prow)
    pooled.to_csv(HERE / "pooled.csv", index=False)
    # late tod detail (pooled FD, per entry bar)
    g = t[t["account"] == "testing"]
    S = sets_of(g)
    bar = pd.concat([S["B14"], S["L1"], S["L2"]])
    per_bar = []
    for td, tr in bar.groupby("tod"):
        o = G.summary(tr)
        ex = tr["exit"].value_counts(normalize=True)
        per_bar.append({"tod": int(td), "n": o["n"], "exp_r": o["exp_r"], "t": o["t"],
                        "exit_time": round(float(ex.get("time", 0)), 3)})
    rep = {"note": "Educational only - not financial advice. Lab history (open two-year history, locked block never "
                   "loaded), production + time-of-day costs. Not paper or live results.",
           "sessions": n_days, "warmup_excluded": WARMUP, "n_configs": N_CONFIGS, "t_study": T_STUDY,
           "identity": ident, "per_bar_pool_FD": per_bar}
    (HERE / "report.json").write_text(json.dumps(rep, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in ident.items() if not (v["matches"] and v["le1500_identical_in_extended_runs"])}, indent=1))
    print(pooled.to_string())


if __name__ == "__main__":
    {"scan": scan, "report": report}[sys.argv[1]]()
