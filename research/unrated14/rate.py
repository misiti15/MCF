"""UNRATED14 (Lead lead-20261111-2100-2, Observer obs-unrated): 2-year lab signal rate of the 14 non-Gen unrated setups,
descriptive, 0 configs. Lab setups: research/bdi/1104/bt_all.py's month_job (same signal rules, frames, chain/refire,
windows, min_adv; locked block never read) on an inventory of exactly these setups, read from whichever account yaml
carries them (enabled or not). Index setups (class index_dip_bounce): mcf.strategies.index_dip.find_trigger on the
signal symbol's 1-min SIP cache per open session. Output: trades/day, p_day = share of sessions with >= 1 trade
(direct), setup-days/week = 5 x p_day, and Scout's fit 5 x (1 - exp(-0.193 x trades/day)) beside it.
    python rate.py <scratch> [procs]        Educational only - not financial advice."""
import os, sys, glob
from pathlib import Path
from multiprocessing import Pool
import numpy as np, pandas as pd, yaml

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT / "research" / "bdi" / "1104")); sys.path.insert(0, str(ROOT))
import bt_all as B  # noqa: E402
B.HERE = HERE                                    # month_job reads HERE/setups.csv -> ours
from mcf.strategies.index_dip import find_trigger  # noqa: E402

LAB = ["LD4-st4-breadthup-t1s05-long", "LD5-st2-breadthup-t05s1-long", "LD6-spy-dip020atr-breadthturn-spxl-holdtr-long",
       "LD7-ns1-idxturn-holdtr-long", "LD8-spy-dip030-breadthturn-spxl-holdtr-long", "CWT14-failbrk-pdl-p05-R2A-short",
       "CWT04-backside-vwaptest-a25-short", "CWT04-backside-lh-a25-short", "NM-RWR1-exh150-gapdn-spyup-pm-short",
       "LIQ-pdl-sweep-open15-vwap-long"]
IDX = ["IDX1-qqq100-0955-TQQQ-hold", "IDX1-qqq100-0955-TQQQ-trail", "IDX2-spy075-0945-3x-trail", "IDX3-spy075-0955-3x-trail"]


def blocks():
    out = {}
    for f in sorted((ROOT / "config").glob("account_*.yaml")) + [ROOT / "config" / "default.yaml"]:
        for n, p in ((yaml.safe_load(f.read_text()) or {}).get("strategies") or {}).items():
            if n in LAB + IDX and n not in out:
                out[n] = (f.name, p)
    return out


def inventory(bl):
    rows = []
    for n in LAB:
        f, p = bl[n]
        m = B.load_mod(n, p["module"]); g = p.get("geom") or getattr(m, "GEOM", "t1s1")
        w = p.get("window") or [950, 1500]
        # rate only: a geometry the walker lacks (holdtr, structural S) is walked as t1s1 and its R is blanked below
        rows.append(dict(account=f, setup=n, type="lab", module=p["module"], covered=True, why="" if g in B.GEOMK else f"geom {g} (R blank)",
                         real_geom=g, side=m.SIDE, geom=g if g in B.GEOMK else "t1s1", w_lo=int(w[0]), w_hi=int(w[1]), min_adv=float(p.get("min_adv", 0) or 0),
                         refire=bool(p.get("refire", False)), cooldown=int(p.get("refire_cooldown", 1)), prefilter=p.get("prefilter") or ""))
    return pd.DataFrame(rows)


def idx_rate(bl, sessions):
    import pyarrow.dataset as pds
    NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
    res, cache = {}, {}
    for n in IDX:
        p = bl[n][1]; sym = p.get("signal_symbol", "SPY")
        if sym not in cache:
            ix = "__index_level_0__"
            s = pds.dataset(str(ROOT / f"data/cache_hist/1Min/{sym}.parquet"), format="parquet").to_table(
                filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
            if ix in s.columns: s = s.set_index(ix)
            s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")].sort_index()
            m = s.index.hour * 60 + s.index.minute; s = s[(m >= 570) & (m < 960)]
            cache[sym] = {str(d): g for d, g in s.groupby(s.index.date)}
        hit = []
        for d in sessions:
            g = cache[sym].get(d)
            if g is None or len(g) < 4:
                continue
            t = find_trigger(g, float(p.get("dip_pct", 0.75)), p.get("dip_by", "09:45"), p.get("entry_from", "09:50"),
                             p.get("entry_until", "10:05"), p.get("trigger", "recovery"), float(p.get("recovery_frac", 0.10)))
            if t is not None:
                hit.append(d)
        res[n] = (bl[n][0], sym, len(hit), sorted(hit)[-3:])
    return res


if __name__ == "__main__":
    S = Path(sys.argv[1]); (S / "bt").mkdir(parents=True, exist_ok=True)
    bl = blocks(); assert set(bl) == set(LAB + IDX), set(LAB + IDX) - set(bl)
    inv = inventory(bl); inv.to_csv(HERE / "setups.csv", index=False)
    print(inv[["account", "setup", "geom", "w_lo", "w_hi", "min_adv", "covered"]].to_string(index=False), flush=True)
    ms = [m for m in B.lib.months() if m not in B.lib.LOCKED_MONTHS and not (S / "bt" / f"sig_{m}.parquet").exists()]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 3) as pool:
        for r in pool.imap_unordered(B.month_job, [(m, str(S)) for m in ms]):
            print(r[0], r[1], r[3], "errs:", r[2][:5], flush=True)
    T = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(S / "bt" / "sig_*.parquet")))], ignore_index=True)
    # sessions = open sessions in the lab frames (from the existing 2y lists' day set, same months)
    D = sorted(set(pd.concat([pd.read_parquet(f, columns=["date"]) for f in glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/sig_*.parquet"))]).date.astype(str)))
    T["date"] = T.date.astype(str); nd = len(D)
    rows = []
    for n in LAB:
        t = T[T.setup == n]
        if bl[n][1].get("symbols"):
            t = t[t.symbol.astype(str).isin(bl[n][1]["symbols"])]
        if (bl[n][1].get("geom") or getattr(B.load_mod(n, bl[n][1]["module"]), "GEOM", "t1s1")) not in B.GEOMK:
            t = t.assign(r=np.nan)
        rows.append(dict(setup=n, home=bl[n][0], kind="lab", trades=len(t), days_hit=t.date.nunique(), trades_day=len(t) / nd,
                         gross_free_avg_r=round(t.r.mean(), 4) if len(t) else np.nan))
    for n, (f, sym, k, last) in idx_rate(bl, D).items():
        rows.append(dict(setup=n, home=f, kind=f"index {sym}", trades=k, days_hit=k, trades_day=k / nd, gross_free_avg_r=np.nan))
    O = pd.DataFrame(rows)
    O["p_day"] = O.days_hit / nd; O["days_week"] = 5 * O.p_day; O["fit_days_week"] = 5 * (1 - np.exp(-0.193 * O.trades_day))
    pd.set_option("display.width", 220)
    print(f"\nUNRATED14: {nd} open sessions (2y lab, locked block never read)")
    print(O.round(4).to_string(index=False))
    print(f"total setup-days/week (direct): {O.days_week.sum():.2f}; by fit: {O.fit_days_week.sum():.2f}")
    print("Lab r is net after production costs (not a verdict; descriptive rate only). Educational only - not financial advice.")
    O.to_csv(HERE / "unrated14.csv", index=False)
