"""Q10/Q11 trade lists: every lab setup of the swarm1017 rework parent families (config/*.yaml, as configured) on the
OPEN 2-year history (never the locked block), with decision-time context (SPY / QQQ / sector ETF fromOpen, breadth).
    python research/swarm1017/followup/extract.py OUT.parquet [month ...]
Educational only - not financial advice."""
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from mcf.research.arena import data as D  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402
from research.history2y import lib  # noqa: E402


def family(name):
    if name.startswith("MF"):
        return "MF"
    if name.startswith(("NS", "RW6G1")):
        return "NS"
    if name.startswith("RW"):
        return "RW"
    if name.startswith("ST"):
        return "ST"
    if name.startswith("L3"):
        return "L3"
    if name.startswith("CWT"):
        return "CWT"
    if name.startswith(("exhaustion_short", "LIQ")):
        return "MISC"
    return None


def setups():
    out, seen = [], set()
    for f in ("default.yaml", "account_testing.yaml", "account_testing2.yaml"):
        c = yaml.safe_load(open(ROOT / "config" / f))
        for name, p in c["strategies"].items():
            if p.get("type") != "lab" or family(name) is None:
                continue
            key = (p["module"], tuple(p.get("window") or (950, 1500)), p.get("min_adv", 0), p.get("prefilter"), bool(p.get("refire")))
            if key in seen:
                continue
            seen.add(key)
            out.append({"name": name, "family": family(name), "module": p["module"], "window": key[1], "min_adv": float(key[2] or 0),
                        "prefilter": p.get("prefilter"), "refire": bool(p.get("refire")), "cd": int(p.get("refire_cooldown", 1)),
                        "scale_out_r": p.get("scale_out_r"), "live_scale_out": bool(p.get("live_scale_out"))})
    return out


def load_mod(s):
    path = ROOT / s["module"]
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("m_" + s["name"].replace("-", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SEC = pd.read_csv(ROOT / "research/bdi/indexlink/linkage.csv")[["symbol", "sector_etf"]]
SEC = dict(zip(SEC.symbol, SEC.sector_etf.fillna("SPY")))

if __name__ == "__main__":
    out_path = Path(sys.argv[1])
    months = sys.argv[2:] or D.months("all")
    S = setups()
    for s in S:
        s["mod"] = load_mod(s)
    skipped = [s["name"] for s in S if s["mod"].GEOM not in gates.GEOMK]
    print("structural-exit setups not scored (no lab outcome in the frames):", skipped, flush=True)
    S = [s for s in S if s["mod"].GEOM in gates.GEOMK]
    print(len(S), "setups", flush=True)
    parts = []
    for mo in months:
        assert mo not in lib.LOCKED_MONTHS
        t0 = time.time()
        d = lib.load_month(mo)
        tod = d.tod.to_numpy()
        sym = d.symbol.astype(str).to_numpy()
        fo = d.fromOpen.to_numpy(float)
        # context per (date, tod)
        ctx = d.loc[d.adv20 >= 95e6].assign(up=lambda x: x.fromOpen > 0).groupby(["date", "tod"])["up"].mean().rename("breadth").reset_index()
        idxfo = d.loc[d.symbol.isin(["SPY", "QQQ"] + sorted(set(SEC.values()))), ["symbol", "date", "tod", "fromOpen"]]
        piv = idxfo.pivot_table(index=["date", "tod"], columns="symbol", values="fromOpen")
        out = D.outcomes(d)
        key = pd.MultiIndex.from_arrays([pd.Index(d["date"]), tod])
        uni = (d.adv20.to_numpy(float) >= 95e6) & (tod >= 950) & (tod <= 1500)
        ctl = {}
        tier = np.where((np.abs(d.gap.to_numpy(float)) >= 20) | (d.close.to_numpy(float) < 5), 3.0, 1.0)
        for s in S:
            m = s["mod"]
            g, sd = m.GEOM, m.SIDE
            o = f"{sd}_{g}"
            if o not in ctl:
                ctl[o] = pd.Series(np.where(uni, out[o], np.nan), index=key).groupby(level=[0, 1]).mean().reindex(key).to_numpy()
            ok = (d.adv20.to_numpy(float) >= s["min_adv"]) & (d.atr_d.to_numpy(float) > 0) & np.isfinite(out[o])
            ok &= (tod >= max(950, s["window"][0])) & (tod <= min(1500, s["window"][1]))
            pf = s["prefilter"] or ""
            if pf.startswith("gap_le:"):
                ok &= d.gap.to_numpy(float) <= float(pf.split(":")[1])
            try:
                hit = np.flatnonzero(np.asarray(m.mask(d), bool) & ok)
            except Exception as e:                       # report, never silently drop
                print("MASK FAIL", s["name"], repr(e), flush=True)
                continue
            if not len(hit):
                continue
            k = pd.factorize(pd.Series(sym[hit]) + "|" + pd.Series(d.date.to_numpy()[hit]).astype(str))[0]
            if not s["refire"]:
                sel = hit[np.r_[True, k[1:] != k[:-1]]]
            else:
                sel = []
                starts = np.flatnonzero(np.r_[True, k[1:] != k[:-1], True])
                for a, b in zip(starts[:-1], starts[1:]):
                    h = hit[a:b]
                    bi = ((tod[h] // 100) * 60 + tod[h] % 100 - 570) // 5
                    sel += [h[int(np.searchsorted(bi, x))] for x in refire_select(bi.tolist(), s["cd"])]
                sel = np.array(sel, int)
            rp = gates.prod_r(d[f"r_{o}"].to_numpy(float)[sel], d[f"win_{o}"].to_numpy(float)[sel], d.close.to_numpy(float)[sel],
                              d.atr_d.to_numpy(float)[sel], g, tod=tod[sel].astype(float))
            parts.append(pd.DataFrame({
                "setup": s["name"], "family": s["family"], "side": sd, "geom": g, "date": d.date.to_numpy()[sel],
                "symbol": sym[sel], "tod": tod[sel].astype(np.int16), "r": out[o][sel], "r_prod": rp.astype(np.float32),
                "ctrl": ctl[o][sel].astype(np.float32), "close": d.close.to_numpy(float)[sel], "atr_d": d.atr_d.to_numpy(float)[sel],
                "tier": tier[sel].astype(np.float32), "fo": fo[sel].astype(np.float32), "gap": d.gap.to_numpy(float)[sel].astype(np.float32)}))
        del d, out
        print(mo, f"{time.time()-t0:.0f}s", sum(len(p) for p in parts), flush=True)
        # attach context
        cx = ctx.merge(piv.reset_index(), on=["date", "tod"], how="left")
        for i, p in enumerate(parts):
            if "breadth" in p:
                continue
            q = p.merge(cx[["date", "tod", "breadth", "SPY", "QQQ"]], on=["date", "tod"], how="left")
            secname = q.symbol.map(SEC).fillna("SPY").where(lambda x: x.isin(cx.columns), "SPY")
            lk = cx.set_index(["date", "tod"])
            vals = np.full(len(q), np.nan)
            for e, grp in q.groupby(secname):
                ser = lk[e]
                vals[grp.index] = ser.reindex(pd.MultiIndex.from_arrays([grp.date, grp.tod])).to_numpy()
            q["sec_etf"] = secname.to_numpy()
            q["sec_fo"] = vals
            q = q.rename(columns={"SPY": "spy_fo", "QQQ": "qqq_fo"})
            parts[i] = q
    T = pd.concat(parts, ignore_index=True)
    T.to_parquet(out_path, index=False)
    print("done", len(T), T.groupby("setup").size().to_dict())
