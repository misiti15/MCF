"""BDI 1104 copy of research/bdi/latch_1103/bt_all.py (unchanged logic; inventory from the live configs of tonight): two-year trade lists with entry AND exit times for every enabled lab setup in the five account
configs (PLAN.md). Signal rules as research/bdi/p3_1029/bt.py; each trade walked on the 5-min path after the entry bar
(stop first, flatten 15:55 from the head/tail file), production costs. Open months only (locked block never read).
Usage: python bt_all.py <scratch> [procs]  -> <scratch>/bt/sig_<month>.parquet + setups.csv here.
Educational only - not financial advice."""
import os, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT / "research" / "bdi" / "gates1021" / "scripts"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "bdi1104 never reads the locked block"
import lib  # noqa: E402
from common import chain, load_mod, no_locked  # noqa: E402
from mcf.research.gates import GEOMK, tod_cost_mult  # noqa: E402

HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
ACCTS = [("primary", "default.yaml"), ("testing", "account_testing.yaml"), ("testing2", "account_testing2.yaml"),
         ("graveyard", "account_graveyard.yaml"), ("gen", "account_gen.yaml")]
SL, BP, SX = 0.01, 1e-4, 0.02


def inventory():
    rows, seen = [], set()
    for acct, f in ACCTS:
        cfg = yaml.safe_load((ROOT / "config" / f).read_text()) or {}
        dref = bool((cfg.get("live") or {}).get("lab_refire", False))
        for name, p in (cfg.get("strategies") or {}).items():
            if not p.get("enabled") or name in seen:
                continue
            seen.add(name)
            r = dict(account=acct, setup=name, type=p.get("type", "classic"), module=p.get("module"), covered=False, why="")
            if r["type"] != "lab":
                r["why"] = f"type {r['type']}"
            elif p.get("symbols"):
                r["why"] = "symbol allow-list"
            else:
                try:
                    m = load_mod(name, p["module"])
                    g = p.get("geom") or getattr(m, "GEOM", "t1s1")
                    if g not in GEOMK:
                        r["why"] = f"geom {g}"
                    else:
                        w = p.get("window") or [950, 1500]
                        r.update(covered=True, side=m.SIDE, geom=g, w_lo=int(w[0]), w_hi=int(w[1]),
                                 min_adv=float(p.get("min_adv", 0) or 0), refire=bool(p.get("refire", dref)),
                                 cooldown=int(p.get("refire_cooldown", 1)), prefilter=p.get("prefilter") or "")
                except Exception as e:  # noqa: BLE001
                    r["why"] = f"load: {type(e).__name__}"
            rows.append(r)
    return pd.DataFrame(rows)


def walk(h, l, c, tod, entry, s, R, up, dn, flat=1555):
    stop = entry - s * dn * R; tgt = entry + s * up * R
    for k in range(len(c)):
        if tod[k] > flat:
            break
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return stop, tod[k], 1
        if (s == 1 and h[k] >= tgt) or (s == -1 and l[k] <= tgt):
            return tgt, tod[k], 2
        if tod[k] == flat:
            return c[k], tod[k], 0
    k = max(0, min(len(c), np.searchsorted(tod, flat, side="right")) - 1)
    return (c[k], tod[k], 0) if len(c) else (entry, flat, 0)


def month_job(args):
    month, S = args
    t0 = time.time()
    SET = pd.read_csv(HERE / "setups.csv").query("covered").to_dict("records")
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht.tod > 1500].rename(columns={"h": "high", "l": "low", "c": "close"})
    ht["symbol"] = ht["symbol"].astype(str); ht["date"] = pd.to_datetime(ht["date"]).dt.date
    tod = f["tod"].to_numpy(); adv = f["adv20"].fillna(0).to_numpy(); atr = f["atr_d"].to_numpy(float)
    gap = f["gap"].to_numpy(float); okd = np.isfinite(f["r_long_t1s1"].to_numpy(float))
    rows, errs = [], []
    for st in SET:
        try:
            m = load_mod(st["setup"], st["module"])
            with np.errstate(invalid="ignore", divide="ignore"):
                mk = np.asarray(m.mask(f), bool)
        except Exception as e:  # noqa: BLE001
            errs.append((st["setup"], type(e).__name__)); continue
        ok = mk & (tod >= max(950, st["w_lo"])) & (tod <= min(1500, st["w_hi"])) & (adv >= st["min_adv"]) & (atr > 0) & okd
        pf = st["prefilter"] if isinstance(st["prefilter"], str) else ""
        if pf.startswith("gap_le:"):
            ok &= gap <= float(pf.split(":", 1)[1])
        elif pf.startswith("gap_ge:"):
            ok &= gap >= float(pf.split(":", 1)[1])
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        idx = hit[chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], bool(st["refire"]), int(st["cooldown"]))]
        rows.append(pd.DataFrame({"setup": st["setup"], "row": idx, "side": 1 if st["side"] == "long" else -1, "geom": st["geom"]}))
    if not rows:
        return month, 0, errs, 0
    sig = pd.concat(rows, ignore_index=True)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], ht[["symbol", "date", "tod", "high", "low", "close"]]],
                  ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = (P.symbol + "|" + P.date.astype(str)).values
    brk = np.r_[True, key[1:] != key[:-1]]; st_ = np.flatnonzero(brk); en_ = np.r_[st_[1:], len(key)]
    rng = {k: (a_, b_) for k, a_, b_ in zip(key[st_], st_, en_)}
    Ph, Pl, Pc = (P[k].to_numpy(float) for k in ("high", "low", "close"))
    Pt = P["tod"].to_numpy()
    fs, fd, fc = f.symbol.to_numpy(), f.date.astype(str).to_numpy(), f.close.to_numpy(float)
    out = {k: [] for k in ("symbol", "date", "tod", "entry", "R", "gap", "xtod", "kind", "px")}
    for r in sig.itertuples():
        i = r.row; sym, d, t0r = fs[i], fd[i], tod[i]
        e = fc[i]; R = 0.25 * atr[i]
        a_, b_ = rng[sym + "|" + d]; tt = Pt[a_:b_]; j = np.searchsorted(tt, t0r, side="right")
        up, dn = GEOMK[r.geom]
        px, et, kd = walk(Ph[a_:b_][j:], Pl[a_:b_][j:], Pc[a_:b_][j:], tt[j:], e, r.side, R, up, dn)
        for k_, v_ in zip(out, (sym, d, t0r, e, R, gap[i], et, kd, px)):
            out[k_].append(v_)
    o = pd.concat([sig.drop(columns=["row"]).reset_index(drop=True), pd.DataFrame(out)], axis=1)
    tier = np.where((np.abs(o.gap) >= 20) | (o.entry < 5), 3.0, 1.0)
    dn = o.geom.map(lambda g: GEOMK[g][1]).to_numpy(float)
    ecost = (SL + o.entry * BP) * tod_cost_mult(o.tod.to_numpy())
    kd = o.kind.to_numpy(); px = o.px.to_numpy(float)
    gross = o.side * (px - o.entry) / o.R
    xcost = np.where(kd == 2, 0.0, SL + px * BP) + np.where(kd == 1, SX, 0.0)
    o["r"] = (gross - tier * (ecost + xcost) / o.R) / dn
    o = o.drop(columns=["px", "gap", "entry", "R"])
    no_locked(o["date"].unique())
    o.to_parquet(Path(S) / "bt" / f"sig_{month}.parquet")
    return month, len(o), errs, round(time.time() - t0, 1)


if __name__ == "__main__":
    S = Path(sys.argv[1]); (S / "bt").mkdir(parents=True, exist_ok=True)
    inv = inventory(); inv.to_csv(HERE / "setups.csv", index=False)
    print(len(inv), "enabled;", int(inv.covered.sum()), "covered;", inv[~inv.covered].why.value_counts().to_dict(), flush=True)
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS and not (S / "bt" / f"sig_{m}.parquet").exists()]
    if len(sys.argv) > 3:
        ms = ms[:int(sys.argv[3])]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as p:
        for r in p.imap_unordered(month_job, [(m, str(S)) for m in ms]):
            print(r[0], r[1], r[3], "errs:", r[2][:5], len(r[2]), flush=True)
