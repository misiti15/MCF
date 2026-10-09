"""Verify the full-day (-FD) modules against their sources on the open two-year history (research/history2y; the
rule-19 locked block is refused by the loader and MCF_HIST_ALLOW_LOCKED is never set).

Checks per setup, every open month, every bar:
  raw:        FD_mask & source_module_window == source_mask                  (exact, bar by bar)
  effective:  FD_mask & source_module_window & source_YAML_window == source_mask & source_YAML_window
              (what live trades: LabStrategy.generate intersects the mask with the YAML window and 09:50-15:00)
  heat:       FD score inside the source window == source score (NaN outside), bar by bar
Also: FD full-day trade count (first qualifying bar per symbol-day, 09:50-15:00, adv20 >= min_adv; gates.lab_trades)
compared with research/bdi/timeofday/results.csv 'full' rows where the setup was in that study, and a live-shaped run of
each FD module on single symbol-day frames without symbol/date columns (must equal the offline result).
RW6G1 needs 5-minute volume for its VWAP band guard: the real guard is run on the symbol-days covered by
research/bdi/trendguard/data/feat (volume joined by symbol/date/tod); the trade count uses the time-of-day study's
precomputed guard (research/bdi/timeofday/data/block), exactly as that study did.

    python research/bdi/fullday/verify.py      # writes research/bdi/fullday/verify.json
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from lib import LOCKED, load_month, months  # noqa: E402
from mcf.research import gates as G  # noqa: E402

FULL = (950, 1500)
LIVE_MONTH = "2026-09"
_S = None


def _load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def specs() -> list[dict]:
    out = json.loads((HERE / "specs.json").read_text())
    for i, s in enumerate(out):
        s["kind"] = "heat" if s["fd_module"].startswith("research/bdi/fullday/heat_") else "lab"
        s["orig"] = _load(ROOT / s["source"], f"src_{i}")
        s["fd"] = _load(ROOT / s["fd_module"], f"fd_{i}")
        s["guard"] = hasattr(s["orig"], "vwap_band_block")
        s["side"] = s["orig"].SIDE if s["kind"] == "lab" else ("short" if s["orig"].SHORT_AT is not None else "long")
        s["geom"] = getattr(s["orig"], "GEOM", "t1s1")
    return out


def _feat_volume() -> pd.DataFrame:
    F = pd.concat([pd.read_parquet(p, columns=["symbol", "date", "tod", "close", "volume"])
                   for p in sorted((ROOT / "research/bdi/trendguard/data/feat").glob("part-*.parquet"))])
    F["date"] = pd.to_datetime(F["date"]).dt.date.astype(str)
    F = F[(F["date"] < LOCKED[0]) | (F["date"] > LOCKED[1])]
    return F.rename(columns={"close": "close_feat"})


def _block() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(p) for p in sorted((ROOT / "research/bdi/timeofday/data/block").glob("*.parquet"))])
    b["date"] = b["date"].astype(str)
    return b


def _init():
    global _S
    _S = specs()


def win(tod, lo, hi, strict=False):
    return (tod >= lo) & ((tod < hi) if strict else (tod <= hi))


def run_mask(s, which, df):
    m = s[which]
    with np.errstate(invalid="ignore"):
        if s["kind"] == "lab":
            return np.asarray(m.mask(df), bool), None
        sc = np.asarray(m.score(df), float)
        return (sc <= m.SHORT_AT) if s["side"] == "short" else (sc >= m.LONG_AT), sc


def one_month(mo: str) -> dict:
    df = load_month(mo)
    ds = df["date"].astype(str)
    tod = df["tod"].to_numpy()
    adv = df["adv20"].fillna(0).to_numpy()
    full = win(tod, *FULL)
    res = {}
    # RW6G1 helpers: precomputed study guard (trade counts) and feat volume (real guard, covered symbol-days only)
    need_guard = any(s["guard"] for s in _S)
    if need_guard:
        bm = BLOCK[BLOCK["date"].str.startswith(mo)]
        key = df["symbol"].astype(str) + "|" + ds + "|" + df["tod"].astype(str)
        study_block = key.isin(set(bm["symbol"] + "|" + bm["date"] + "|" + bm["tod"].astype(str))).to_numpy()
        fv = FEAT[FEAT["date"].str.startswith(mo)]
        dv = df.assign(date_s=ds).merge(fv, how="left", left_on=["symbol", "date_s", "tod"],
                                        right_on=["symbol", "date", "tod"], suffixes=("", "_f"))
        assert len(dv) == len(df)
        sd = dv["volume"].notna().groupby([dv["symbol"], dv["date_s"]], sort=False).transform("all").to_numpy(bool)
        covered = df.loc[sd].reset_index(drop=True).copy()
        covered["volume"] = dv.loc[sd, "volume"].to_numpy(float)
        close_ok = np.isclose(dv.loc[sd, "close"].to_numpy(float), dv.loc[sd, "close_feat"].to_numpy(float),
                              rtol=1e-4, atol=1e-4)
    for s in _S:
        r = {}
        lo, hi = s["module_window"]
        ylo, yhi = s["yaml_window"]
        mw = win(tod, lo, hi, s["strict_hi"])
        yw = win(tod, max(950, ylo), min(1500, yhi))
        if s["guard"]:
            # real code path, covered symbol-days (volume present)
            ct = covered["tod"].to_numpy()
            o, _ = run_mask(s, "orig", covered)
            f, _ = run_mask(s, "fd", covered)
            cmw = win(ct, lo, hi, s["strict_hi"])
            cyw = win(ct, max(950, ylo), min(1500, yhi))
            r.update(rows=int(len(covered)), symbol_days=int(covered.groupby(["symbol", "date"]).ngroups),
                     close_match=int(close_ok.sum()), raw_mismatch=int((o != (f & cmw)).sum()),
                     eff_mismatch=int(((o & cyw) != (f & cmw & cyw)).sum()), src_bars=int(o.sum()),
                     fd_bars=int((f & win(ct, *FULL)).sum()))
            # trade counts on all rows with the study's guard (as research/bdi/timeofday/scan.py)
            saved = {w: s[w].vwap_band_block for w in ("orig", "fd")}
            for w in ("orig", "fd"):
                s[w].vwap_band_block = lambda d, k=2.0: d["_block"].to_numpy(bool)
            d2 = df.assign(_block=study_block)
            o2, _ = run_mask(s, "orig", d2)
            f2, _ = run_mask(s, "fd", d2)
            r.update(raw_mismatch_studyguard=int((o2 != (f2 & mw)).sum()),
                     eff_mismatch_studyguard=int(((o2 & yw) != (f2 & mw & yw)).sum()))
            for w in ("orig", "fd"):
                s[w].vwap_band_block = saved[w]   # back to the module's own guard
            o, f = o2, f2
        else:
            o, so = run_mask(s, "orig", df)
            f, sf = run_mask(s, "fd", df)
            r.update(rows=int(len(df)), raw_mismatch=int((o != (f & mw)).sum()),
                     eff_mismatch=int(((o & yw) != (f & mw & yw)).sum()), src_bars=int(o.sum()),
                     fd_bars=int((f & full).sum()))
            if so is not None:
                r["score_mismatch"] = int((~np.isclose(np.where(mw, sf, np.nan), so, equal_nan=True, rtol=0, atol=0)).sum())
        ok = adv >= s["min_adv"]
        tr_cur = G.lab_trades(df, o & yw & ok, s["side"], s["geom"])
        tr_fd = G.lab_trades(df, f & full & ok, s["side"], s["geom"])
        r["n_current"], r["n_full"] = int(len(tr_cur)), int(len(tr_fd))
        r["n_full_before_1110"] = int((tr_fd["tod"] < 1110).sum())
        r["n_full_outside_src_window"] = int((~win(tr_fd["tod"].to_numpy(), max(950, lo, ylo), min(1500, hi, yhi),
                                                    s["strict_hi"])).sum())
        res[s["name"]] = r
    out = {"month": mo, "sessions": int(df["date"].nunique()), "setups": res}
    if mo == LIVE_MONTH:
        out["live"] = live_shaped(df, covered if need_guard else None)
    return out


def live_shaped(df: pd.DataFrame, covered: pd.DataFrame | None) -> dict:
    """Run each FD module on single symbol-day frames without symbol/date columns (as LabStrategy.generate builds them)
    and compare with the offline (multi-symbol-day) result on the same rows."""
    out = {}
    rng = np.random.default_rng(20261009)
    for s in _S:
        src = covered if s["guard"] else df
        f, sc = run_mask(s, "fd", src)
        key = src["symbol"].astype(str) + "|" + src["date"].astype(str)
        hits = key[f].unique()
        miss = np.setdiff1d(key.unique(), hits)
        pick = list(rng.choice(hits, min(5, len(hits)), replace=False)) + list(rng.choice(miss, min(3, len(miss)), replace=False))
        n_ok, n_fire, err = 0, 0, None
        for k in pick:
            sel = (key == k).to_numpy()
            one = src.loc[sel].drop(columns=["symbol", "date"]).reset_index(drop=True)
            try:
                g, sg = run_mask(s, "fd", one)
            except Exception as e:  # noqa: BLE001
                err = repr(e)
                break
            same = np.array_equal(g, f[sel]) and (sc is None or np.allclose(sg, sc[sel], equal_nan=True))
            n_ok += int(same)
            n_fire += int(g.any())
        out[s["name"]] = {"frames": len(pick), "equal": n_ok, "frames_firing": n_fire, "error": err}
    return out


def main():
    global FEAT, BLOCK
    from multiprocessing import get_context
    t0 = time.time()
    FEAT, BLOCK = _feat_volume(), _block()
    res = []
    with get_context("fork").Pool(3, initializer=_init) as pool:
        for r in pool.imap_unordered(one_month, months()):
            res.append(r)
            print(f"{r['month']} ({time.time() - t0:.0f}s)", flush=True)
    res.sort(key=lambda r: r["month"])
    sts = specs()
    study = pd.read_csv(ROOT / "research/bdi/timeofday/results.csv")
    study = study[study["set"] == "full"].drop_duplicates("setup").set_index("setup")
    cur = pd.read_csv(ROOT / "research/bdi/timeofday/results.csv")
    cur = cur[cur["set"] == "current"].drop_duplicates("setup").set_index("setup")
    sessions = sum(r["sessions"] for r in res)
    live = next(r["live"] for r in res if "live" in r)
    summary = []
    for s in sts:
        agg = {}
        for r in res:
            for k, v in r["setups"][s["name"]].items():
                agg[k] = agg.get(k, 0) + v
        src_name = s["name"]
        row = {"setup": s["name"] + "-FD", "source": s["source"], "fd_module": s["fd_module"], "account": s["account"],
               "side": s["side"], "geom": s["geom"], "min_adv": s["min_adv"], "source_module_window": s["module_window"],
               "source_strict_hi": s["strict_hi"], "source_yaml_window": s["yaml_window"],
               "clauses_removed": s["clauses_removed"], **agg,
               "full_per_day": round(agg["n_full"] / sessions, 2), "current_per_day": round(agg["n_current"] / sessions, 2),
               "study_full_n": int(study.loc[src_name, "n"]) if src_name in study.index else None,
               "study_full_per_day": float(study.loc[src_name, "per_day"]) if src_name in study.index else None,
               "study_full_exp_r": float(study.loc[src_name, "exp_r"]) if src_name in study.index else None,
               "study_current_n": int(cur.loc[src_name, "n"]) if src_name in cur.index else None,
               "live_shaped": live[s["name"]]}
        mism = [k for k in ("raw_mismatch", "eff_mismatch", "score_mismatch", "raw_mismatch_studyguard",
                            "eff_mismatch_studyguard") if row.get(k)]
        row["identical"] = not mism
        row["count_matches_study"] = None if row["study_full_n"] is None else row["study_full_n"] == row["n_full"]
        row["current_matches_study"] = None if row["study_current_n"] is None else row["study_current_n"] == row["n_current"]
        summary.append(row)
    doc = {"note": "Educational only - not financial advice. Open two-year history only (locked block refused; "
                   "MCF_HIST_ALLOW_LOCKED never set). Lab history, not paper or live results.",
           "months": [r["month"] for r in res], "sessions": sessions,
           "all_identical": all(r["identical"] for r in summary),
           "all_live_shaped_ok": all(r["live_shaped"]["error"] is None and r["live_shaped"]["equal"] == r["live_shaped"]["frames"]
                                     for r in summary),
           "setups": summary}
    (HERE / "verify.json").write_text(json.dumps(doc, indent=1) + "\n")
    for r in summary:
        print(f"{r['setup']:45s} ident {r['identical']!s:5s} raw {r['raw_mismatch']} eff {r['eff_mismatch']} "
              f"n_cur {r['n_current']} (study {r['study_current_n']}) n_full {r['n_full']} (study {r['study_full_n']}) "
              f"/day {r['full_per_day']} live {r['live_shaped']['equal']}/{r['live_shaped']['frames']} "
              f"fire {r['live_shaped']['frames_firing']} err {r['live_shaped']['error']}")
    print("all identical", doc["all_identical"], "live ok", doc["all_live_shaped_ok"])


FEAT = BLOCK = None

if __name__ == "__main__":
    main()
