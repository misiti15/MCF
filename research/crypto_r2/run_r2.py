"""Crypto research round 2 (pre-registered in research/crypto_r2/PREREG.md; its sha256 is in PREREG.sha256).

    python research/crypto_r2/run_r2.py fit     # 400 random draws + 80 seed-grid configs on FIT -> finalists.json
    python research/crypto_r2/run_r2.py check   # the 10 frozen finalists scored ONCE on CHECK + random baselines

Engine "E5b crypto 1-min fills" (mcf/crypto/exec1m.py): signals on 15m/1h/4h/1d bars, fills and exits on real
1-min prints; realistic maker entries (a limit fills only when traded through). Costs: mcf/crypto/costs.py at fee
tier 1 (base); tiers 2/3 are a sensitivity only. LOCKED (2026-05-26..) is never read: the loader clips at its start.
Educational only — not financial advice.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.crypto import data as D  # noqa: E402
from mcf.crypto import splits as S  # noqa: E402
from mcf.crypto.backtest import summarize  # noqa: E402
from mcf.crypto.costs import CostModel  # noqa: E402
from mcf.crypto.exec1m import Minutes, reprice, run, to_min  # noqa: E402
from mcf.crypto.generator2 import ALTS, CORE, UNIVERSES, Setup2, build2, generate, mask, seed_grid, time_mask  # noqa

HERE = Path(__file__).parent
SEED = 20261127
R1_DRAWS = 500
N_RANDOM = 400
MIN_TRADES, MAX_SHARE = 60, 0.5
TOP, FAMILY_CAP = 10, 3
RAND_REPS = 100
CHECK_T = 1.0                       # CHECK is a first look for new finalists: rule-18 rising bar, look 1
FEATS: dict = {}                    # (tf, pair) -> feature frame (to the LOCKED start)
MINS: dict = {}                     # pair -> Minutes (real 1-min prints, to the LOCKED start)
COSTS = CostModel()


def load(tfs=(15, 60, 240, 1440)) -> None:
    t0 = time.time()
    for p in CORE + ALTS:
        raw = D.load_bars(p)
        if raw.empty:
            continue
        MINS[p] = Minutes.from_bars(raw)
        for tf in tfs:
            b = D.resample(raw, f"{tf}min", ffill=True)
            FEATS[(tf, p)] = build2(b, tf, btc=None if p == "BTC" else FEATS[(tf, "BTC")])
        del raw
    # btc_lag seed: on each 60m bar, the alt with the largest (BTC z - alt z) gets lag_rank1 = BTC z (if lag >= 1)
    zb = pd.DataFrame({p: FEATS[(60, p)]["zb"] for p in ALTS if (60, p) in FEATS})
    bz = FEATS[(60, "BTC")]["zb"].reindex(zb.index)
    lag = (-zb).add(bz, axis=0)
    best = lag.fillna(-np.inf).idxmax(axis=1)
    for p in zb.columns:
        ok = (best == p) & (lag[p] >= 1.0)
        FEATS[(60, p)]["lag_rank1"] = bz.where(ok).reindex(FEATS[(60, p)].index).astype("float32")
    print(f"loaded {len(MINS)} pairs, {len(FEATS)} frames in {time.time()-t0:.0f}s", flush=True)


def trades_for(s: Setup2, split: str, mode: str | None = None, sig_fn=None, plan=None):
    a, z = S.bounds(split)
    am, zm = int(to_min(pd.DatetimeIndex([a]))[0]), int(to_min(pd.DatetimeIndex([z]))[0])
    out, offered, missed = [], 0, 0
    plan = plan or s.plan(mode)
    for p in UNIVERSES[s.universe]:
        f = FEATS.get((s.tf, p))
        if f is None:
            continue
        dec = to_min(f.index) + s.tf                     # decision time = bar close
        sel = (dec >= am) & (dec < zm)
        if sel.sum() < 50:
            continue
        g = f[sel]
        sig = sig_fn(s, g, p) if sig_fn else mask(s, g, p)
        if not sig.any():
            continue
        tr, o, m = run(p, MINS[p].slice(am, zm), dec[sel][sig], g["c"].to_numpy(np.float64)[sig],
                       g["atr"].to_numpy(np.float64)[sig], plan, COSTS)
        offered += o
        missed += m
        if len(tr):
            out.append(tr)
    tr = pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["day", "r", "cost_r", "gross_r",
                                                                              "pair", "maker_in", "maker_out", "rpu",
                                                                              "nonfee_r"])
    return tr, offered, missed


def _sum(tr, prefix="") -> dict:
    sm = summarize(tr)
    return {f"{prefix}{k}": v for k, v in sm.items()}


def score(s: Setup2, split: str = "fit") -> dict:
    tr, off, miss = trades_for(s, split)
    r = _sum(tr)
    r.update(draw_id=s.draw_id, key=s.key(), family=s.family, tf=s.tf, mode=s.mode, universe=s.universe,
             label=s.label(), offered=off, missed=miss, pairs=int(tr["pair"].nunique()) if len(tr) else 0,
             core_n=int(tr["pair"].isin(CORE).sum()) if len(tr) else 0,
             core_avg_r=float(tr.loc[tr["pair"].isin(CORE), "r"].mean()) if len(tr) else np.nan)
    for tier in (2, 3):
        t2 = reprice(tr.copy(), tier) if len(tr) else tr
        r.update({f"t{tier}_{k}": v for k, v in summarize(t2).items() if k in ("avg_r", "avg_r_wo_best", "day_t")})
    # maker-fill effect (sensitivity only, never used to choose): same signals and exits, other entry modes
    alt = {"taker": None, "naive": None, "maker": None}
    for m in alt:
        if m == s.mode:
            continue
        pl = s.plan(m)
        if m == "maker" and s.mode == "taker":
            pl = Plan(**{**pl.__dict__, "off_atr": 0.0, "expiry_min": s.tf})
        t3, o3, m3 = trades_for(s, split, plan=pl)
        sm = summarize(t3)
        r.update({f"{m}_n": sm["n"], f"{m}_avg_r": sm["avg_r"], f"{m}_gross_r": sm["avg_gross_r"],
                  f"{m}_cost_r": sm["avg_cost_r"], f"{m}_missed": m3, f"{m}_offered": o3})
    return r


def all_setups() -> list[Setup2]:
    rnd = generate(N_RANDOM, SEED, start_id=R1_DRAWS)
    return rnd + seed_grid(R1_DRAWS + N_RANDOM)


def noise_bar(n_cum: int) -> float:
    return float(np.sqrt(2 * np.log(n_cum)))


def eligible(r, bar) -> bool:
    return (r["n"] >= MIN_TRADES and r["best_day_share"] < MAX_SHARE and r["avg_r_wo_best"] > 0
            and r["day_t"] >= bar)


def _pick(df: pd.DataFrame, k: int, taken: dict) -> list[int]:
    out = []
    for _, row in df.sort_values("day_t", ascending=False).iterrows():
        if len(out) >= k:
            break
        fam = row["family"]
        if fam != "random" and taken.get(fam, 0) >= FAMILY_CAP:
            continue
        taken[fam] = taken.get(fam, 0) + 1
        out.append(int(row["draw_id"]))
    return out


def fit() -> None:
    load()
    setups = all_setups()
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        res = pool.map(score, setups, chunksize=2)
    print(f"scored {len(res)} configs in {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(res).sort_values("draw_id")
    df.to_csv(HERE / "fit_all.csv", index=False, float_format="%.4f")
    n_cum = R1_DRAWS + len(setups)
    bar = noise_bar(n_cum)
    df["elig"] = df.apply(lambda r: eligible(r, bar), axis=1)
    taken: dict = {}
    top = _pick(df[df.elig], TOP, taken)
    near_pool = df[(~df.elig) & (df.n >= MIN_TRADES)]
    top += _pick(near_pool, TOP - len(top), taken)
    by_id = {s.draw_id: s for s in setups}
    ix = df.set_index("draw_id")
    frozen = {"frozen_utc": pd.Timestamp.now(tz="UTC").isoformat(), "seed": SEED, "configs_r2": len(setups),
              "n_cum": n_cum, "noise_bar": bar, "eligible": int(df.elig.sum()),
              "rule": "PREREG.md: n>=60, best-day share<0.5, avg R w/o best day>0, day t>=sqrt(2 ln N_cum); top 10 by "
                      "day t, <=3 per seed family; near-misses (n>=60, by day t) fill the rest, information only",
              "finalists": [{"spec": by_id[i].spec(), "draw_id": i, "eligible": bool(ix.loc[i, "elig"]),
                             "fit": ix.loc[i].drop(["label", "key"]).to_dict()} for i in top]}
    (HERE / "finalists.json").write_text(json.dumps(frozen, indent=1, default=lambda o: o if not isinstance(
        o, (np.generic,)) else o.item()))
    n60 = df[df.n >= MIN_TRADES]
    mk = df[(df["mode"] == "maker") & (df.n >= MIN_TRADES)]
    stats = {"configs_r2": len(setups), "random": N_RANDOM, "seed_grid": len(setups) - N_RANDOM, "n_cum": n_cum,
             "noise_bar": bar, "n_ge_60": int(len(n60)), "gross_pos": int((n60.avg_gross_r > 0).sum()),
             "net_pos": int((n60.avg_r > 0).sum()), "eligible": int(df.elig.sum()),
             "max_t": float(n60.day_t.max()), "median_cost_r": float(n60.avg_cost_r.median()),
             "median_gross_r": float(n60.avg_gross_r.median()),
             "t2_net_pos": int((n60.t2_avg_r > 0).sum()), "t3_net_pos": int((n60.t3_avg_r > 0).sum()),
             "t2_max_t": float(n60.t2_day_t.max()), "t3_max_t": float(n60.t3_day_t.max()),
             "maker_draws_n60": int(len(mk)),
             "maker_fill_rate_median": float((mk.n / (mk.n + mk.missed)).median()),
             "maker_real_minus_naive_r_median": float((mk.avg_r - mk.naive_avg_r).median()),
             "maker_real_minus_taker_r_median": float((mk.avg_r - mk.taker_avg_r).median()),
             "maker_real_gross_minus_naive_gross_median": float((mk.avg_gross_r - mk.naive_gross_r).median()),
             "by_family": {f: {"configs": int((df.family == f).sum()), "n60": int((n60.family == f).sum()),
                               "net_pos": int(((n60.family == f) & (n60.avg_r > 0)).sum()),
                               "best_t": float(n60[n60.family == f].day_t.max()) if (n60.family == f).any() else None,
                               "median_avg_r": float(n60[n60.family == f].avg_r.median())
                               if (n60.family == f).any() else None}
                           for f in df.family.unique()}}
    (HERE / "fit_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    print(ix.loc[top, ["n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t", "avg_cost_r", "elig", "label"]]
          .to_string())


def _random_fn(rng, counts):
    def fn(s, g, p):
        idx = np.flatnonzero(time_mask(s, g))
        k = min(counts.get(p, 0), len(idx))
        sig = np.zeros(len(g), bool)
        if k:
            sig[rng.choice(idx, k, replace=False)] = True
        return sig
    return fn


def random_baseline(s: Setup2, split: str, counts: dict, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(RAND_REPS):
        tr, _, _ = trades_for(s, split, sig_fn=_random_fn(rng, counts))
        out.append(tr["r"].mean() if len(tr) else np.nan)
    return np.array(out)


def _check_one(args):
    k, item = args
    sp = item["spec"]
    s = Setup2(item["draw_id"], **{**sp, "conds": [tuple(c) for c in sp["conds"]]})
    row = {"draw_id": s.draw_id, "eligible": item["eligible"], "family": s.family, "label": s.label()}
    for split in ("fit", "check"):
        r = score(s, split)
        tr, _, _ = trades_for(s, split)
        counts = tr.groupby("pair").size().to_dict() if len(tr) else {}
        rb = random_baseline(s, split, counts, SEED + 100 * k + (split == "check"))
        keep = ["n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t", "avg_cost_r", "avg_gross_r", "missed",
                "offered", "t2_avg_r", "t3_avg_r", "taker_avg_r", "naive_avg_r", "maker_avg_r", "core_n",
                "core_avg_r"]
        row.update({f"{split}_{m}": r.get(m, np.nan) for m in keep})
        row[f"{split}_rand_mean"] = float(np.nanmean(rb))
        row[f"{split}_rand_pct"] = float(np.nanmean(rb < r["avg_r"])) if r["n"] else float("nan")
    row["survivor"] = bool(row["eligible"] and row["check_n"] >= 20 and row["check_avg_r"] > 0
                           and row["check_avg_r_wo_best"] > 0 and row["check_best_day_share"] < MAX_SHARE
                           and row["check_day_t"] >= CHECK_T and row["check_rand_pct"] > 0.5)
    print(json.dumps(row, default=float), flush=True)
    return row


def check() -> None:
    fz = json.loads((HERE / "finalists.json").read_text())
    load()
    with mp.get_context("fork").Pool(4) as pool:
        rows = pool.map(_check_one, list(enumerate(fz["finalists"])), chunksize=1)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "check_finalists.csv", index=False, float_format="%.4f")
    print(out.drop(columns="label").to_string())


from mcf.crypto.exec1m import Plan  # noqa: E402

if __name__ == "__main__":
    {"fit": fit, "check": check}[sys.argv[1]]()
