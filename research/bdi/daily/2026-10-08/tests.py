"""BDI 2026-10-08: tests of the nightly-loop hypotheses (research/backlog.jsonl) plus one pattern-driven check.
Lab train/valid (research/setups2/data) first, then the 2-year history (research/history2y/data/frames, the rule-19
locked block 2024-11..2025-02 is never loaded: lib.months() lists only open months; the older locked holdouts
Apr-Jun 2026 and Sep 16 - Oct 5 2026 are dropped from the history before scoring). No locked holdout is scored here.

Entries: every live lab/heat setup as LabStrategy/HeatStrategy trades it - module mask (or heat score crossing) inside
the YAML window, point-in-time adv20 >= min_adv (lab frames get adv20 from research/history2y/data/daily.parquet),
first qualifying bar per symbol-day, R = 0.25 x daily ATR, exit by 15:55. Cost: the production haircut of
research/owner1008/scan_fast.py, r - (2 x close x 1e-4 + 0.02) / R on top of the lab's 1c/side.

PRE-DECLARED CONFIGURATIONS (fixed before any result was looked at):
 H1 loop-1008-exhaustion-cluster: per-setup entry-rate cap - keep an entry only if fewer than k entries of the same
    setup were kept in the trailing W minutes (ties inside one bar broken by a fixed symbol hash).
    setups {exhaustion_short, heat_fade_short, heat_fade_long} x W {15, 30} x k {2..6} = 30 configurations.
    Gate (pre-declared): kept exp > 0 AND kept - all > 0 on train AND valid, and the random-drop control
    (drop the same number of entries per day at random, 1000 draws) gives p < 0.05 on valid.
 H2 loop-1008-multisetup-consensus: cs = number of live SHORT masks true on the symbol-bar (10 masks), cl = LONG (3).
    (a) pooled short: first bar per symbol-day with cs >= c, c {1,2,3,4} x geom {t1s1,t05s1,t1s05} = 12
    (b) pooled long : cl >= c, c {1,2} x 3 geoms = 6
    (c) per setup (13), its own entries split by agreement at the entry bar: same-side count >= 2 vs == 1 = 26
    = 44 configurations. Gate: backlog finalist gate (train and valid exp > 0, valid n >= 30, valid day-t >= 1.5)
    AND exp rising with the count (c=2 > c=1) on both splits.
 H3 pattern check (gave_back_gains on 3 of 3 live days): each live lab/heat setup's entries under the two
    non-native exit geometries = 13 x 2 = 26 configurations (native geometry is the baseline, not a config).
 Total 100 configurations on train/valid; the same 100 re-scored on the history (no re-selection).
History gates (rule 19, mcf/research/gates.py): day-t >= max(1.5, sqrt(2 ln N)) with N = configs of that hypothesis,
exp > 0 in up AND down sessions, walk-forward share >= 0.6.

usage: python research/bdi/daily/2026-10-08/tests.py [lab|hist|report]
Educational only - not financial advice.
"""
import importlib.util
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.research import gates as G  # noqa: E402

OUT = Path(__file__).resolve().parent
CACHE = ROOT / "data" / "cache" / "bdi1008"
GEOMS = ("t1s1", "t05s1", "t1s05")
SETUPS = {  # name: (path, kind, window, min_adv)
    "exhaustion_short": ("research/setups2/candidates/volume_flip_1.py", "lab", (1300, 1500), 95e6),
    "heat_fade_short": ("research/heat/candidates/regime_9.py", "heat", (950, 1030), 125e6),
    "heat_fade_long": ("research/heat/candidates/regime_5.py", "heat", (1105, 1330), 125e6),
    "MF1-945-flowsell-vwapup": ("research/primitives/marcoflow/MF-945-flowsell-vwapup.py", "lab", (950, 1030), 95e6),
    "MF2-open-rsimidhi-flowsell": ("research/primitives/marcoflow/MF-open-rsimidhi-flowsell.py", "lab", (950, 1100), 95e6),
    "MF3-open-flowsell-rsi5hi": ("research/primitives/marcoflow/MF-open-flowsell-rsi5hi.py", "lab", (950, 1100), 95e6),
    "MF4-h40-open-flowsell": ("research/primitives/marcoflow/MF-h40-open-flowsell.py", "lab", (950, 1100), 95e6),
    "MF5-flowsell-vwapup-rsi5hi": ("research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py", "lab", (950, 1500), 95e6),
    "NS1-rsidip-rsi5pop-long": ("research/owner1008/NS1-rsidip-rsi5pop-long.py", "lab", (950, 1130), 95e6),
    "NS2-sma50break-overbought-short": ("research/owner1008/NS2-sma50break-overbought-short.py", "lab", (950, 1130), 95e6),
    "NS3-failed-vwap-reclaim-short": ("research/owner1008/NS3-failed-vwap-reclaim-short.py", "lab", (950, 1130), 95e6),
    "NS4-pm-vwap-reclaim-oversold-short": ("research/owner1008/NS4-pm-vwap-reclaim-oversold-short.py", "lab", (1130, 1500), 95e6),
    "NS5-sma50-flush-oversold-long": ("research/owner1008/NS5-sma50-flush-oversold-long.py", "lab", (950, 1130), 95e6),
}
CAP_SETUPS = ["exhaustion_short", "heat_fade_short", "heat_fade_long"]
CAPS = [(w, k) for w in (15, 30) for k in (2, 3, 4, 5, 6)]
N_CONF = {"H1": 30, "H2": 44, "H3": 26}


def _mod(name, path):
    p = ROOT / path
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location("bdi_" + name.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MODS = {k: _mod(k, v[0]) for k, v in SETUPS.items()}


def side_geom(name):
    m, kind = MODS[name], SETUPS[name][1]
    if kind == "lab":
        return m.SIDE, getattr(m, "GEOM", "t1s1")
    return ("long" if getattr(m, "LONG_AT", None) is not None else "short"), "t1s1"


def mask(name, df):
    m, (_, kind, (lo, hi), adv) = MODS[name], SETUPS[name]
    tod = df["tod"].to_numpy()
    base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (df["adv20"].fillna(0).to_numpy() >= adv)
    with np.errstate(invalid="ignore"):
        if kind == "lab":
            return np.asarray(m.mask(df), bool) & base
        s = np.asarray(m.score(df), float)
        return base & ((s >= m.LONG_AT) if m.LONG_AT is not None else (s <= m.SHORT_AT))


def entries(df):
    """Entry tables for one frame (sorted by symbol, date, tod)."""
    R = 0.25 * df["atr_d"].to_numpy(float)
    hair = (2 * df["close"].to_numpy(float) * 1e-4 + 0.02) / R
    ok_r = np.isfinite(R) & (R > 0)
    M = {k: mask(k, df) & ok_r for k in SETUPS}
    sg = {k: side_geom(k) for k in SETUPS}
    cs = sum(M[k].astype(np.int8) for k in SETUPS if sg[k][0] == "short")
    cl = sum(M[k].astype(np.int8) for k in SETUPS if sg[k][0] == "long")
    sym, date = df["symbol"].to_numpy(), df["date"].to_numpy()
    base = {"date": date, "symbol": sym, "tod": df["tod"].to_numpy()}

    def table(m, side, label):
        idx = G.first_per_symbol_day(sym, date, m)
        t = pd.DataFrame({k: v[idx] for k, v in base.items()})
        t["setup"], t["side"], t["cs"], t["cl"] = label, side, cs[idx], cl[idx]
        for g in GEOMS:
            t[f"r_{g}"] = df[f"r_{side}_{g}"].to_numpy(float)[idx] - hair[idx]
        return t[np.isfinite(t["r_t1s1"])]

    out = [table(M[k], sg[k][0], k) for k in SETUPS]
    out += [table(cs >= c, "short", f"pool_short_c{c}") for c in (1, 2, 3, 4)]
    out += [table(cl >= c, "long", f"pool_long_c{c}") for c in (1, 2)]
    x = pd.concat(out, ignore_index=True)
    x["symbol"] = x["symbol"].astype(str)
    return x


def build_lab():
    d = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "adv20"])
    d["date"] = pd.to_datetime(d["date"]).dt.date
    for split in ("train", "valid"):
        f = pd.read_parquet(ROOT / f"research/setups2/data/{split}.parquet")
        f["date"] = pd.to_datetime(f["date"]).dt.date
        f["symbol"] = f["symbol"].astype(str)
        f = f.merge(d, on=["symbol", "date"], how="left").sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        print(split, len(f), "rows; adv20 missing share", round(float(f["adv20"].isna().mean()), 4), flush=True)
        entries(f).to_parquet(CACHE / f"entries_{split}.parquet")


def build_hist():
    from research.history2y.lib import load_month, months
    out = []
    for mo in months():                      # open months only; the locked block lives in data/locked
        f = load_month(mo)
        out.append(entries(f))
        print(mo, len(f), flush=True)
        del f
    pd.concat(out, ignore_index=True).to_parquet(CACHE / "entries_hist.parquet")


# ------------------------------------------------------------------------------------------------ scoring
def tmin(hhmm):
    hhmm = np.asarray(hhmm, int)
    return (hhmm // 100) * 60 + hhmm % 100


def cap_keep(t, W, k):
    """Boolean keep-vector for a per-setup rate cap (t: one setup's entries)."""
    t = t.assign(_m=tmin(t["tod"]), _h=[zlib.crc32(s.encode()) for s in t["symbol"]]).sort_values(["date", "_m", "_h"])
    keep = np.zeros(len(t), bool)
    for _, g in t.groupby("date", sort=False):
        kept = []
        pos = g.index
        for i, m in zip(pos, g["_m"].to_numpy()):
            n = sum(1 for x in kept if x > m - W)
            if n < k:
                kept.append(m)
                keep[t.index.get_loc(i)] = True
    return pd.Series(keep, index=t.index).reindex(t.index), t


def summ(t, col="r_t1s1"):
    if not len(t):
        return {"n": 0}
    return G.summary(pd.DataFrame({"date": t["date"].to_numpy(), "r": t[col].to_numpy(float)}))


def random_drop_p(t, keep, col, obs_delta, reps=1000, seed=20261008):
    rng = np.random.default_rng(seed)
    r = t[col].to_numpy(float)
    day = pd.factorize(t["date"])[0]
    drop_n = pd.Series(~keep.to_numpy()).groupby(day).sum().to_numpy()
    allm = r.mean()
    ge = 0
    for _ in range(reps):
        u = rng.random(len(r))
        rank = pd.Series(u).groupby(day).rank(method="first").to_numpy() - 1
        kk = rank >= drop_n[day]
        if r[kk].mean() - allm >= obs_delta:
            ge += 1
    return (ge + 1) / (reps + 1)


def h1(E, split):
    rows = []
    for s in CAP_SETUPS:
        t = E[E.setup == s].reset_index(drop=True)
        a = summ(t)
        for W, k in CAPS:
            keep, ts = cap_keep(t, W, k)
            kt, dt = ts[keep.to_numpy()], ts[~keep.to_numpy()]
            ks, ds = summ(kt), summ(dt)
            delta = (ks.get("exp_r", np.nan) - a["exp_r"]) if ks.get("n") else np.nan
            p = random_drop_p(ts, keep, "r_t1s1", delta) if ds.get("n") and np.isfinite(delta) else None
            rows.append({"split": split, "setup": s, "W": W, "k": k, "all_n": a["n"], "all_exp": a["exp_r"],
                         "kept_n": ks.get("n"), "kept_exp": ks.get("exp_r"), "kept_t": ks.get("t"),
                         "dropped_n": ds.get("n", 0), "dropped_exp": ds.get("exp_r"), "delta": delta,
                         "p_random_drop": p, "kept_sum": round(float(kt["r_t1s1"].sum()), 2),
                         "all_sum": round(float(t["r_t1s1"].sum()), 2)})
    return pd.DataFrame(rows)


def h2(E, split):
    rows = []
    for c in (1, 2, 3, 4):
        t = E[E.setup == f"pool_short_c{c}"]
        for g in GEOMS:
            rows.append({"split": split, "config": f"pool_short cs>={c}", "geom": g, **summ(t, f"r_{g}")})
    for c in (1, 2):
        t = E[E.setup == f"pool_long_c{c}"]
        for g in GEOMS:
            rows.append({"split": split, "config": f"pool_long cl>={c}", "geom": g, **summ(t, f"r_{g}")})
    for s in SETUPS:
        side, geom = side_geom(s)
        t = E[E.setup == s]
        cnt = t["cs"] if side == "short" else t["cl"]
        for lab, m in (("agree>=2", cnt >= 2), ("alone==1", cnt == 1)):
            rows.append({"split": split, "config": f"{s} {lab}", "geom": geom, **summ(t[m], f"r_{geom}")})
    return pd.DataFrame(rows)


def h3(E, split):
    rows = []
    for s in SETUPS:
        side, geom = side_geom(s)
        t = E[E.setup == s]
        for g in GEOMS:
            rows.append({"split": split, "setup": s, "geom": g, "native": g == geom, **summ(t, f"r_{g}")})
    return pd.DataFrame(rows)


def hist_gates(t, col, n_conf, reg):
    tr = pd.DataFrame({"date": t["date"].to_numpy(), "r": t[col].to_numpy(float)})
    o = G.summary(tr)
    rs = G.regime_split(tr, reg)
    wf = G.walk_forward(tr)
    v, fails = G.verdict(o, rs, wf, n_conf)
    return {**o, "up_exp": rs["up"].get("exp_r"), "down_exp": rs["down"].get("exp_r"), "wf_share": wf["share_positive"],
            "t_req": G.t_required(n_conf), "verdict": v, "fails": "; ".join(fails)}


def report():
    res = {}
    for split in ("train", "valid"):
        E = pd.read_parquet(CACHE / f"entries_{split}.parquet")
        res.setdefault("h1", []).append(h1(E, split))
        res.setdefault("h2", []).append(h2(E, split))
        res.setdefault("h3", []).append(h3(E, split))
    H1, H2, H3 = (pd.concat(res[k], ignore_index=True) for k in ("h1", "h2", "h3"))
    hp = CACHE / "entries_hist.parquet"
    if hp.exists():
        from research.history2y.lib import regimes
        reg = regimes()
        E = pd.read_parquet(hp)
        E["date"] = pd.to_datetime(E["date"]).dt.date
        ds = E["date"].astype(str)
        hold = ((ds >= "2026-04-01") & (ds <= "2026-06-30")) | ((ds >= "2026-09-16") & (ds <= "2026-10-05"))
        E = E[~hold].reset_index(drop=True)      # the two older locked holdouts are not scored here (lead only)
        H1 = pd.concat([H1, h1(E, "hist")], ignore_index=True)
        H2 = pd.concat([H2, h2(E, "hist")], ignore_index=True)
        H3 = pd.concat([H3, h3(E, "hist")], ignore_index=True)
        g = []
        for s in CAP_SETUPS:
            t = E[E.setup == s].reset_index(drop=True)
            g.append({"hyp": "H1", "config": f"{s} uncapped", **hist_gates(t, "r_t1s1", 1, reg)})
            for W, k in CAPS:
                keep, ts = cap_keep(t, W, k)
                g.append({"hyp": "H1", "config": f"{s} W{W} k{k}", **hist_gates(ts[keep.to_numpy()], "r_t1s1", N_CONF["H1"], reg)})
        for c in (1, 2, 3, 4):
            for gg in GEOMS:
                g.append({"hyp": "H2", "config": f"pool_short cs>={c} {gg}", **hist_gates(E[E.setup == f"pool_short_c{c}"], f"r_{gg}", N_CONF["H2"], reg)})
        pd.DataFrame(g).to_csv(OUT / "tests_hist_gates.csv", index=False)
    H1.to_csv(OUT / "tests_h1_cluster_cap.csv", index=False)
    H2.to_csv(OUT / "tests_h2_consensus.csv", index=False)
    H3.to_csv(OUT / "tests_h3_exit_geom.csv", index=False)
    print("configurations:", N_CONF, "total", sum(N_CONF.values()))


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    {"lab": build_lab, "hist": build_hist, "report": report}[sys.argv[1]]()
