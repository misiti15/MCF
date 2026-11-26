"""Crypto research round 1: random setup generation on FIT, top-10 frozen, scored ONCE on CHECK.

    python research/crypto_r1/run_r1.py fit     # N seeded draws scored on FIT (costs in) -> finalists.json (frozen)
    python research/crypto_r1/run_r1.py check   # frozen finalists scored once on CHECK + random-entry baselines

Engine "E5 crypto" (mcf/crypto/backtest.py). Costs: mcf/crypto/costs.py (taker default; maker-entry variant shown
as a sensitivity only, never used to choose). LOCKED (2026-05-26..) is never read: the loader clips at its start.
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
from mcf.crypto.backtest import run_pair, summarize  # noqa: E402
from mcf.crypto.costs import CostModel  # noqa: E402
from mcf.crypto.features import bars_for, build  # noqa: E402
from mcf.crypto.generator import Setup, generate, mask, window_mask  # noqa: E402

HERE = Path(__file__).parent
SEED = 20261126
N_DRAWS = 500
MIN_TRADES, MAX_SHARE = 100, 0.5
TOP = 10
RAND_REPS = 100
FEATS: dict = {}          # (tf, pair) -> feature frame up to the LOCKED start
COSTS = CostModel()


def load_features(tfs=(15, 60)) -> None:
    t0 = time.time()
    pairs = [p for p in D.PAIRS if D.symbol_dir(p).exists()]
    for tf in tfs:
        btc = build(bars_for("BTC", tf), tf)
        FEATS[(tf, "BTC")] = btc
        for p in pairs:
            if p == "BTC":
                continue
            b = bars_for(p, tf)
            if len(b) > 500:
                FEATS[(tf, p)] = build(b, tf, btc=btc)
    print(f"features: {len(FEATS)} frames in {time.time()-t0:.0f}s", flush=True)


def trades_for(s: Setup, split: str, costs: CostModel = COSTS, sig_fn=None) -> pd.DataFrame:
    a, z = S.bounds(split)
    out = []
    for (tf, p), f in FEATS.items():
        if tf != s.tf:
            continue
        g = f[(f.index >= a) & (f.index < z)]
        if len(g) < 200:
            continue
        sig = sig_fn(s, g, p) if sig_fn else mask(s, g, is_btc=(p == "BTC"))
        if sig.any():
            out.append(run_pair(p, g, sig, s.exit, side=s.side, costs=costs))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["day", "r", "cost_r", "gross_r"])


def _score_fit(s: Setup) -> dict:
    tr = trades_for(s, "fit")
    r = summarize(tr)
    r.update(draw_id=s.draw_id, key=s.key(), label=s.label(), side=s.side, tf=s.tf,
             pairs=int(tr["pair"].nunique()) if len(tr) else 0)
    return r


def _score_fit_maker(s: Setup) -> dict:
    """Sensitivity only (never used to choose): the same draw with maker-fee entries and no entry spread."""
    r = summarize(trades_for(s, "fit", costs=CostModel.maker()))
    return {"draw_id": s.draw_id, "mk_n": r["n"], "mk_avg_r": r["avg_r"], "mk_wo_best": r["avg_r_wo_best"],
            "mk_t": r["day_t"]}


def eligible(r: dict) -> bool:
    return (r["side"] > 0 and r["n"] >= MIN_TRADES and r["best_day_share"] < MAX_SHARE and r["avg_r_wo_best"] > 0)


def fit() -> None:
    load_features()
    setups = generate(N_DRAWS, SEED)
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        res = pool.map(_score_fit, setups, chunksize=4)
        mk = pool.map(_score_fit_maker, setups, chunksize=4)
    print(f"scored {len(res)} draws in {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(res).merge(pd.DataFrame(mk), on="draw_id").sort_values("draw_id")
    df.to_csv(HERE / "fit_all.csv", index=False, float_format="%.4f")
    el = df[df.apply(eligible, axis=1)].copy()
    el["rank_score"] = el[["avg_r", "avg_r_wo_best"]].min(axis=1)
    el = el.sort_values("rank_score", ascending=False)
    el["eligible"] = True
    # Pre-declared fallback (2026-11-26, before CHECK was read): if fewer than 10 draws are eligible, the rest of the
    # top 10 are the best NEAR-MISSES (long, n >= 100, same ranking), flagged eligible=False. They are scored on CHECK
    # for information only and can never become survivors.
    near = df[(df.side > 0) & (df.n >= MIN_TRADES) & ~df.draw_id.isin(el.draw_id)].copy()
    near["rank_score"] = near[["avg_r", "avg_r_wo_best"]].min(axis=1)
    near["eligible"] = False
    top = pd.concat([el, near.sort_values("rank_score", ascending=False)]).head(TOP)
    by_id = {s.draw_id: s for s in setups}
    frozen = {"frozen_utc": pd.Timestamp.now(tz="UTC").isoformat(), "seed": SEED, "draws": N_DRAWS,
              "eligible": int(len(el)), "rule": "long, n>=100, best-day share<0.5, avg R w/o best day>0; "
                                                "top 10 by min(avg R, avg R w/o best day)",
              "finalists": [{"spec": by_id[int(i)].spec(), "draw_id": int(i), "eligible": bool(e),
                             "fit": df.set_index("draw_id").loc[int(i)].drop(["label", "key"]).to_dict()}
                            for i, e in zip(top["draw_id"], top["eligible"])]}
    (HERE / "finalists.json").write_text(json.dumps(frozen, indent=1, default=float))
    stats = {"draws": N_DRAWS, "long": int((df.side > 0).sum()), "short_flagged": int((df.side < 0).sum()),
             "with_trades": int((df.n > 0).sum()), "n_ge_100": int((df.n >= 100).sum()),
             "gross_pos_n100": int(((df.n >= 100) & (df.avg_gross_r > 0)).sum()),
             "net_pos_n100": int(((df.n >= 100) & (df.avg_r > 0)).sum()), "eligible": int(len(el)),
             "max_t_n100": float(df[df.n >= 100].day_t.max()),
             "median_cost_r_n100": float(df[df.n >= 100].avg_cost_r.median()),
             "maker_pos_n100": int(((df.mk_n >= 100) & (df.mk_avg_r > 0)).sum()),
             "maker_max_t_n100": float(df[df.mk_n >= 100].mk_t.max()),
             "median_gross_r_n100": float(df[df.n >= 100].avg_gross_r.median()),
             "noise_bar": float(np.sqrt(2 * np.log(N_DRAWS)))}
    (HERE / "fit_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    print(top[["draw_id", "n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t", "avg_cost_r", "label"]]
          .to_string())


def _random_sig(rng):
    def fn(s, g, p, counts):
        wm = window_mask(s, g)
        idx = np.flatnonzero(wm & np.isfinite(g["atr"].to_numpy()))
        k = min(counts.get(p, 0), len(idx))
        sig = np.zeros(len(g), bool)
        if k:
            sig[rng.choice(idx, k, replace=False)] = True
        return sig
    return fn


def random_baseline(s: Setup, split: str, counts: dict, reps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    fn = _random_sig(rng)
    out = []
    for _ in range(reps):
        tr = trades_for(s, split, sig_fn=lambda s_, g, p: fn(s_, g, p, counts))
        out.append(tr["r"].mean() if len(tr) else np.nan)
    return np.array(out)


def check() -> None:
    fz = json.loads((HERE / "finalists.json").read_text())
    load_features()
    rows = []
    for k, item in enumerate(fz["finalists"]):
        sp = item["spec"]
        s = Setup(item["draw_id"], sp["tf"], sp["side"], [tuple(c) for c in sp["conds"]], sp["window"],
                  sp["days"], sp["stop_atr"], sp["target_atr"], sp["hold_h"])
        row = {"draw_id": s.draw_id, "eligible": item["eligible"], "label": s.label()}
        for split in ("fit", "check"):
            tr = trades_for(s, split)
            sm = summarize(tr)
            counts = tr.groupby("pair").size().to_dict() if len(tr) else {}
            rb = random_baseline(s, split, counts, RAND_REPS, SEED + k)
            row.update({f"{split}_{m}": sm[m] for m in ("n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t",
                                                         "avg_cost_r", "avg_gross_r")})
            row[f"{split}_rand_mean"] = float(np.nanmean(rb))
            row[f"{split}_rand_pct"] = float(np.nanmean(rb < sm["avg_r"])) if sm["n"] else float("nan")
        mk = summarize(trades_for(s, "check", costs=CostModel.maker()))
        row["check_maker_avg_r"], row["check_maker_wo_best"] = mk["avg_r"], mk["avg_r_wo_best"]
        rows.append(row)
        print(json.dumps(row, default=float), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "check_finalists.csv", index=False, float_format="%.4f")
    print(out.drop(columns="label").to_string())


if __name__ == "__main__":
    {"fit": fit, "check": check}[sys.argv[1]]()
