"""Collect every config passing all gates (F1-F6), de-duplicate (valid symbol-day Jaccard > 0.5), add same-time
controls, daily-P&L correlation and trade overlap with the live lab-reproducible setups. Writes data/passers.parquet
and prints the table. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from combos import Ctx, OPP, conds_of  # noqa: E402
from grid import WINDOWS  # noqa: E402
from lib import exit_bar, same_time_ctrl  # noqa: E402

LIVE = {  # name: (module, window, min_adv, kind)
    "exhaustion_short": ("research/setups2/candidates/volume_flip_1.py", (1300, 1500), 95e6, "lab"),
    "heat_fade_short": ("research/heat/candidates/regime_9.py", (950, 1030), 125e6, "heat"),
    "heat_fade_long": ("research/heat/candidates/regime_5.py", (1105, 1330), 125e6, "heat"),
    "MF1": ("research/primitives/marcoflow/MF-945-flowsell-vwapup.py", (950, 1030), 95e6, "lab"),
    "MF2": ("research/primitives/marcoflow/MF-open-rsimidhi-flowsell.py", (950, 1100), 95e6, "lab"),
    "MF3": ("research/primitives/marcoflow/MF-open-flowsell-rsi5hi.py", (950, 1100), 95e6, "lab"),
    "MF4": ("research/primitives/marcoflow/MF-h40-open-flowsell.py", (950, 1100), 95e6, "lab"),
    "MF5": ("research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py", (950, 1500), 95e6, "lab"),
    "NS1": ("research/owner1008/NS1-rsidip-rsi5pop-long.py", (950, 1130), 95e6, "lab"),
    "NS2": ("research/owner1008/NS2-sma50break-overbought-short.py", (950, 1130), 95e6, "lab"),
    "NS3": ("research/owner1008/NS3-failed-vwap-reclaim-short.py", (950, 1130), 95e6, "lab"),
    "NS4": ("research/owner1008/NS4-pm-vwap-reclaim-oversold-short.py", (1130, 1500), 95e6, "lab"),
    "NS5": ("research/owner1008/NS5-sma50-flush-oversold-long.py", (950, 1130), 95e6, "lab"),
}


def load_mod(p):
    spec = importlib.util.spec_from_file_location("m_" + Path(p).stem.replace("-", "_"), ROOT / p)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((ROOT / p).parent))
    spec.loader.exec_module(m)
    return m


EXTRA_COLS = ["rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat", "volumeHeat", "trendHeat", "macdHeat"]


def live_trades(cx):
    """{name: {split: (idx, side, geom)}} using the modules on the lab frame (+ YAML window + ADV)."""
    out = {}
    for nm, (p, (lo, hi), adv, kind) in LIVE.items():
        m = load_mod(p)
        out[nm] = {}
        for s, sp in cx.sp.items():
            df = sp.df
            if kind == "lab":
                mk = np.asarray(m.mask(df), bool)
                side, geom = m.SIDE, getattr(m, "GEOM", "t1s1")
            else:
                sc = np.asarray(m.score(df), float)
                if m.LONG_AT is not None:
                    mk, side = sc >= m.LONG_AT, "long"
                else:
                    mk, side = sc <= m.SHORT_AT, "short"
                geom = "t1s1"
            mk &= (sp.tod >= lo) & (sp.tod <= hi) & (np.nan_to_num(sp.adv) >= adv)
            out[nm][s] = (sp.first_per_day(np.flatnonzero(mk)), side, geom)
    return out


def daily(sp, idx, side, geom):
    r = sp.r[(side, geom)][idx]
    ok = np.isfinite(r)
    return np.bincount(sp.dcode[idx][ok], weights=r[ok], minlength=sp.ndays)


def cand_entries(cx, row):
    """Rebuild entry rows for a passing config of any family."""
    fam = row.family
    if fam in ("F1", "F2", "F3bear", "F3bull"):
        return {s: cx.entries(s, conds_of(row), row.window) for s in cx.sp}, row.side, row.geom
    if fam == "F6":
        m = re.match(r"ADV>=(\d+)M\[(\w+):(.*)@(\w+)\]", row.conds)
        tier, conds, w = float(m.group(1)) * 1e6, tuple(m.group(3).split("+")), m.group(4)
        conds = tuple(c for c in conds if c != "none")
        return {s: cx.entries(s, conds, w, extra=np.nan_to_num(cx.sp[s].adv) >= tier) for s in cx.sp}, row.side, row.geom
    if fam == "F4":
        m = re.match(r"(OR|SEQab|SEQba)\[(\w+):(.*)@(\w+)\] \[(\w+):(.*)@(\w+)\]", row.conds)
        kind, ca, wa, cb, wb = m.group(1), tuple(m.group(3).split("+")), m.group(4), tuple(m.group(6).split("+")), m.group(7)
        ent = {}
        for s, sp in cx.sp.items():
            ma, mb = cx.rowmask(s, ca, wa), cx.rowmask(s, cb, wb)
            if kind == "OR":
                mm = ma | mb
            else:
                first, second = (ma, mb) if kind == "SEQab" else (mb, ma)
                cs = np.cumsum(first)
                start = np.flatnonzero(sp.first)
                base = np.repeat(cs[start] - first[start], np.diff(np.r_[start, sp.n]))
                mm = second & ((cs - first - base) > 0)
            ent[s] = sp.first_per_day(np.flatnonzero(mm))
        return ent, row.side, row.geom
    raise ValueError(fam)


def main():
    g = pd.read_parquet(HERE / "data" / "gated.parquet")
    e = pd.read_parquet(HERE / "data" / "extra.parquet")
    p = pd.concat([g[g.g_all], e[e.g_all]], ignore_index=True).sort_values("score", ascending=False)
    cx = Ctx(EXTRA_COLS)
    live = live_trades(cx)
    sp_t, sp_v = cx.sp["train"], cx.sp["valid"]
    live_daily = {nm: np.r_[daily(sp_t, *v["train"]), daily(sp_v, *v["valid"])] for nm, v in live.items()}
    live_sum = np.sum(list(live_daily.values()), axis=0)
    live_keys = set()
    for v in live.values():
        for s, sp in cx.sp.items():
            live_keys |= set(zip([s] * len(v[s][0]), sp.sid[v[s][0]].tolist()))
    rows, kept_sets = [], []
    for _, x in p.iterrows():
        ent, side, geom = cand_entries(cx, x)
        vset = set(sp_v.sid[ent["valid"]].tolist())
        jac = max([len(vset & t) / max(1, len(vset | t)) for t in kept_sets] or [0])
        d = np.r_[daily(sp_t, ent["train"], side, geom), daily(sp_v, ent["valid"], side, geom)]
        cors = {nm: float(np.corrcoef(d, ld)[0, 1]) if ld.std() > 0 else np.nan for nm, ld in live_daily.items()}
        top = max(cors, key=lambda k: abs(np.nan_to_num(cors[k])))
        keys = set(zip(["train"] * len(ent["train"]), sp_t.sid[ent["train"]].tolist())) | \
            set(zip(["valid"] * len(ent["valid"]), sp_v.sid[ent["valid"]].tolist()))
        row = x.to_dict()
        row.update({"dup_jaccard": jac, "dedup_keep": jac <= 0.5,
                    "tr_sametime_edge": same_time_ctrl(sp_t, ent["train"], side, geom),
                    "va_sametime_edge": same_time_ctrl(sp_v, ent["valid"], side, geom),
                    "corr_live_sum": float(np.corrcoef(d, live_sum)[0, 1]), "corr_max_setup": top,
                    "corr_max": cors[top], "overlap_live": len(keys & live_keys) / max(1, len(keys)),
                    **{f"corr_{k}": v for k, v in cors.items()}})
        rows.append(row)
        if jac <= 0.5:
            kept_sets.append(vset)
    out = pd.DataFrame(rows)
    out.to_parquet(HERE / "data" / "passers.parquet")
    # live setups' own lab numbers for reference
    from lib import stats
    ref = []
    for nm, v in live.items():
        a, b = stats(sp_t, *v["train"]), stats(sp_v, *v["valid"])
        ref.append({"setup": nm, "tr_n": a and a["n"], "tr_exp": a and a["exp"], "tr_t": a and a["t"],
                    "va_n": b and b["n"], "va_exp": b and b["exp"], "va_t": b and b["t"]})
    pd.DataFrame(ref).to_csv(HERE / "data" / "live_ref.csv", index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 110)
    print(pd.DataFrame(ref).round(3).to_string())
    show = ["family", "conds", "window", "side", "geom", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t", "va_exbest",
            "va_tpd", "tr_sametime_edge", "va_sametime_edge", "dup_jaccard", "corr_live_sum", "corr_max_setup",
            "corr_max", "overlap_live"]
    print(out[show].round(3).to_string())


if __name__ == "__main__":
    main()
