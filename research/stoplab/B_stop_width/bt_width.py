"""stoplab grid B3: per-trade stop width k x the setup's own stop distance on the 2-year lab history.
Signals: latch_1103 trade lists (bt_lab1104/sig_*.parquet, 92 traded setups) re-walked here; plus traded lab setups
with a t/s geometry missing from those lists (signals rebuilt with latch_1103 bt_all's rules from the module mask and
the setup's config entry). Walk = latch_1103 bt_all.walk (5-min path after the signal bar, stop first, flatten 15:55),
production costs (entry 1c+1bps x tod mult, exits 1c+1bps unless target, +2c on stops, x3 extended tier).
k in {0.75,0.9,1.0,1.1,1.25,1.5}: stop = entry -/+ k*dn*R, target PRICE unchanged, same $ risk (size / k) so
r_k = net points / (k*dn*R). Also r_sc = r_1 / k (same trade, old stop, the smaller/larger size: size-only control).
Locked block never read. Educational only - not financial advice.
Usage: python bt_width.py <out_dir> [procs]"""
import os, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT / "research" / "bdi" / "gates1021" / "scripts"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "stoplab never reads the locked block"
import lib  # noqa: E402
from common import chain, load_mod, no_locked  # noqa: E402
from mcf.research.gates import GEOMK, tod_cost_mult  # noqa: E402

BT = ROOT / "research" / "history2y" / "data" / "bt_lab1104"
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
WT = HERE.parents[2]  # worktree root (configs as of this branch)
CFGS = ["default.yaml", "account_testing.yaml", "account_testing2.yaml", "account_gen.yaml", "account_graveyard.yaml",
        "account_explore1.yaml", "account_livelab.yaml"]
KS = (0.75, 0.9, 1.0, 1.1, 1.25, 1.5)
SL, BP, SX = 0.01, 1e-4, 0.02


def inventory():
    L = pd.read_csv(HERE.parent / "lab_modules.csv")
    L["g"] = L.geom.astype(str).str.extract(r"([A-Za-z0-9+]+)")[0]
    traded = set(pd.read_csv(HERE.parent / "trades.csv.gz", usecols=["setup", "whatif"]).query("~whatif").setup)
    bts = pd.read_csv(BT / "setups.csv")
    cov = set(bts[bts.covered].setup)
    rows = []
    cfgs = {f: yaml.safe_load((WT / "config" / f).read_text()) or {} for f in CFGS}
    for r in L.to_dict("records"):
        s = r["setup"]
        if s not in traded:
            continue
        d = dict(setup=s, geom=r["g"], src="", why="")
        if r["g"] not in GEOMK:
            d["why"] = f"geom {r['g']} (harness covers t/s only)"
        elif s in cov:
            d["src"] = "bt_lab1104"
        else:
            ent = None
            for f, c in cfgs.items():
                p = (c.get("strategies") or {}).get(s)
                if p and p.get("type") == "lab" and p.get("module"):
                    ent = (f, p, bool((c.get("live") or {}).get("lab_refire", False)))
                    break
            if ent is None:
                d["why"] = "no type:lab config entry (classic in config)"
            elif ent[1].get("symbols"):
                d["why"] = "symbol allow-list"
            else:
                f, p, dref = ent
                try:
                    m = load_mod(s, p["module"])
                    w = p.get("window") or [950, 1500]
                    d.update(src="rebuilt", module=p["module"], side=m.SIDE, w_lo=int(w[0]), w_hi=int(w[1]),
                             min_adv=float(p.get("min_adv", 0) or 0), refire=bool(p.get("refire", dref)),
                             cooldown=int(p.get("refire_cooldown", 1)), prefilter=p.get("prefilter") or "")
                    g = p.get("geom") or getattr(m, "GEOM", r["g"])
                    if g not in GEOMK:
                        d.update(src="", why=f"geom {g}")
                    else:
                        d["geom"] = g
                except Exception as e:  # noqa: BLE001
                    d["why"] = f"load: {type(e).__name__}"
        rows.append(d)
    return pd.DataFrame(rows)


def walk(h, l, c, tod, entry, s, stop, tgt, flat=1555):
    for k in range(len(c)):
        if tod[k] > flat:
            break
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return stop, 1
        if (s == 1 and h[k] >= tgt) or (s == -1 and l[k] <= tgt):
            return tgt, 2
        if tod[k] == flat:
            return c[k], 0
    k = max(0, min(len(c), np.searchsorted(tod, flat, side="right")) - 1)
    return (c[k], 0) if len(c) else (entry, 0)


def month_job(args):
    month, out = args
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    INV = pd.read_csv(Path(out) / "inventory.csv")
    keep_bt = set(INV[INV.src == "bt_lab1104"].setup)
    REB = INV[INV.src == "rebuilt"].to_dict("records")
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht.tod > 1500].rename(columns={"h": "high", "l": "low", "c": "close"})
    ht["symbol"] = ht["symbol"].astype(str); ht["date"] = pd.to_datetime(ht["date"]).dt.date
    tod = f["tod"].to_numpy(); adv = f["adv20"].fillna(0).to_numpy(); atr = f["atr_d"].to_numpy(float)
    gap = f["gap"].to_numpy(float); okd = np.isfinite(f["r_long_t1s1"].to_numpy(float))
    fs, fd = f.symbol.to_numpy(), f.date.astype(str).to_numpy()
    # (1) bt_lab1104 signals -> frame rows
    sp = BT / f"sig_{month}.parquet"
    sig = []
    if sp.exists():
        b = pd.read_parquet(sp)
        b = b[b.setup.isin(keep_bt)].reset_index(drop=True)
        key = pd.DataFrame({"symbol": fs, "date": fd, "tod": tod, "row": np.arange(len(f))})
        b["date"] = b["date"].astype(str)
        b = b.merge(key, on=["symbol", "date", "tod"], how="left")
        miss = int(b.row.isna().sum())
        b = b[b.row.notna()]
        sig.append(pd.DataFrame({"setup": b.setup, "row": b.row.astype(int), "side": b.side, "geom": b.geom,
                                 "bt_r": b.r, "src": "bt_lab1104"}))
    else:
        miss = 0
    # (2) rebuilt signals
    errs = []
    for st in REB:
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
        idx = hit[chain(fs[hit], fd[hit], tod[hit], bool(st["refire"]), int(st["cooldown"]))]
        side = st["side"]
        side = (1 if side == "long" else -1) if isinstance(side, str) else int(side)
        sig.append(pd.DataFrame({"setup": st["setup"], "row": idx, "side": side, "geom": st["geom"], "bt_r": np.nan,
                                 "src": "rebuilt"}))
    sig = pd.concat(sig, ignore_index=True)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], ht[["symbol", "date", "tod", "high", "low", "close"]]],
                  ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = (P.symbol + "|" + P.date.astype(str)).values
    brk = np.r_[True, key[1:] != key[:-1]]; st_ = np.flatnonzero(brk); en_ = np.r_[st_[1:], len(key)]
    rng = {k: (a_, b_) for k, a_, b_ in zip(key[st_], st_, en_)}
    Ph, Pl, Pc = (P[k].to_numpy(float) for k in ("high", "low", "close"))
    Pt = P["tod"].to_numpy()
    fc = f.close.to_numpy(float)
    rows = sig["row"].to_numpy(); sides = sig["side"].to_numpy(); geoms = sig["geom"].to_numpy()
    res = np.full((len(sig), len(KS)), np.nan); kinds = np.zeros((len(sig), len(KS)), np.int8)
    for q in range(len(sig)):
        i = rows[q]; s = sides[q]
        e = fc[i]; R = 0.25 * atr[i]; up, dn = GEOMK[geoms[q]]
        a_, b_ = rng[fs[i] + "|" + fd[i]]; tt = Pt[a_:b_]; j = np.searchsorted(tt, tod[i], side="right")
        h_, l_, c_, t_ = Ph[a_:b_][j:], Pl[a_:b_][j:], Pc[a_:b_][j:], tt[j:]
        tgt = e + s * up * R
        tier = 3.0 if (abs(gap[i]) >= 20 or e < 5) else 1.0
        ec = (SL + e * BP) * tod_cost_mult(np.array([tod[i]]))[0]
        for kk, k in enumerate(KS):
            stop = e - s * k * dn * R
            px, kd = walk(h_, l_, c_, t_, e, s, stop, tgt)
            xc = (0.0 if kd == 2 else SL + px * BP) + (SX if kd == 1 else 0.0)
            res[q, kk] = (s * (px - e) - tier * (ec + xc)) / (k * dn * R)
            kinds[q, kk] = kd
    o = pd.DataFrame({"setup": sig.setup.to_numpy(), "src": sig.src.to_numpy(), "symbol": fs[rows], "date": fd[rows],
                      "tod": tod[rows], "side": sides, "geom": geoms, "bt_r": sig.bt_r.to_numpy()})
    for kk, k in enumerate(KS):
        o[f"r{k}"] = res[:, kk].astype("float32"); o[f"x{k}"] = kinds[:, kk]
    no_locked(o["date"].unique())
    o.to_parquet(Path(out) / f"w_{month}.parquet")
    return month, len(o), miss, errs, round(time.time() - t0, 1)


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    inv = inventory(); inv.to_csv(out / "inventory.csv", index=False); inv.to_csv(HERE / "inventory.csv", index=False)
    print(inv.src.replace("", "none").value_counts().to_dict(), inv[inv.src.isna() | (inv.src == "")].why.value_counts().to_dict(), flush=True)
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS and not (out / f"w_{m}.parquet").exists()]
    if len(sys.argv) > 3:
        ms = ms[:int(sys.argv[3])]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as p:
        for r in p.imap_unordered(month_job, [(m, str(out)) for m in ms]):
            print(r[0], r[1], "unmatched", r[2], "errs", r[3][:5], r[4], "s", flush=True)
