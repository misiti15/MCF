"""U5 day-type specialists: one session -> trades CSV (setups S1-S4, cued + no-cue, random controls).
Streams the session's 1min/1day packs from the public GitHub release, deletes them after use.
Educational only - not financial advice."""
import os, sys, json, subprocess, shutil
import numpy as np, pandas as pd

S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u5"
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
URL = "https://github.com/misiti15/MCF/releases/download/{tag}/{kind}-{d}.parquet"


def tag(d):
    return f"bars-{d[:7]}" if d >= "2026-10-06" else f"bars2y-{d[:7]}"


def fetch(d):
    dd = f"{S}/dl/{d}"; os.makedirs(dd, exist_ok=True)
    out = {}
    for k in ("1min", "1day"):
        p = f"{dd}/{k}.parquet"
        subprocess.run(["curl", "-sSfL", "--retry", "4", "-o", p, URL.format(tag=tag(d), kind=k, d=d)], check=True)
        out[k] = pd.read_parquet(p)
    shutil.rmtree(dd)
    return out


def cost(e, px, kind):
    slip = np.where(kind == 0, np.maximum(0.02, 4e-4 * px), np.where(kind == 2, np.maximum(0.01, 1e-4 * px), 0.0))
    return e * (1e-4 + SEC) + TAF + 2 * CAT + slip


def walk(O, H, L, j0, side, e, stop, tgt):
    """1-min walk from index j0; flat at index 385 (15:55 open). kind 0 stop, 1 target, 2 time."""
    FL = 385
    if j0 >= FL:
        return None
    h, l, o = H[j0:FL], L[j0:FL], O[j0:FL]
    if side > 0:
        hs = np.nonzero(l <= stop)[0]; ht = np.nonzero(h >= tgt + 0.01)[0]
    else:
        hs = np.nonzero(h >= stop)[0]; ht = np.nonzero(l <= tgt - 0.01)[0]
    js = hs[0] if len(hs) else 10**9; jt = ht[0] if len(ht) else 10**9
    if js == 10**9 and jt == 10**9:
        return O[FL], FL, 2
    if js <= jt:
        px = min(o[js], stop) if side > 0 else max(o[js], stop)
        return px, j0 + js, 0
    return tgt, j0 + jt, 1


def first_true(m):
    any_ = m.any(1); idx = m.argmax(1)
    return np.where(any_, idx, -1)


def run(d, rng_seed):
    P = fetch(d)
    day = P["1day"].copy(); day["date"] = pd.to_datetime(day.ts, utc=True).dt.tz_convert("America/New_York").dt.date
    day = day[(day.date < pd.Timestamp(d).date()) & (day.date > LOCK_B)]
    assert not ((day.date >= LOCK_A) & (day.date <= LOCK_B)).any()
    day = day.sort_values(["symbol", "date"])
    g = day.groupby("symbol", observed=True)
    pc = g.close.shift(1)
    day["tr"] = np.maximum(day.high, pc) - np.minimum(day.low, pc)
    day["dv"] = day.close * day.volume
    last = g.tail(20).groupby("symbol", observed=True).agg(adv=("dv", "mean"), n=("dv", "size"))
    atr = day.groupby("symbol", observed=True).tail(14).groupby("symbol", observed=True).agg(atr=("tr", "mean"), na=("tr", "count"))
    pcl = g.close.last().rename("pc")
    F = pd.concat([last, atr, pcl], axis=1)
    F = F[(F.n >= 20) & (F.na >= 14)]
    F.index = F.index.astype(str)

    m = P["1min"]; m = m.assign(symbol=m.symbol.astype(str))
    t = pd.to_datetime(m.ts, utc=True).dt.tz_convert("America/New_York")
    assert (t.dt.date == pd.Timestamp(d).date()).all()
    m["mn"] = (t.dt.hour * 60 + t.dt.minute).values
    m = m[(m.mn >= 570) & (m.mn <= 959)]
    uni = F[(F.pc >= 10) & (F.adv >= 20e6) & (F.atr / F.pc >= 0.01) & (F.atr / F.pc <= 0.08)].index
    syms = sorted(set(uni) & set(m.symbol.unique()) | {"SPY"})
    if "SPY" not in set(m.symbol) or "SPY" not in F.index:
        return None
    m = m[m.symbol.isin(syms)]
    syms = sorted(m.symbol.unique()); si = {s: i for i, s in enumerate(syms)}
    n = len(syms)
    A = {}
    for c in ("open", "high", "low", "close", "volume"):
        a = np.full((n, 390), np.nan); a[m.symbol.map(si).values, m.mn.values - 570] = m[c].values; A[c] = a
    C1 = pd.DataFrame(A["close"]).ffill(axis=1).bfill(axis=1).values
    O1 = np.where(np.isnan(A["open"]), C1, A["open"]); H1 = np.where(np.isnan(A["high"]), C1, A["high"])
    L1 = np.where(np.isnan(A["low"]), C1, A["low"]); V1 = np.nan_to_num(A["volume"])
    # need the first minute traded and enough bars
    ok = (~np.isnan(A["open"][:, :5])).any(1) & ((~np.isnan(A["close"])).sum(1) >= 200)
    O5 = O1.reshape(n, 78, 5)[:, :, 0]; C5 = C1.reshape(n, 78, 5)[:, :, 4]
    H5 = H1.reshape(n, 78, 5).max(2); L5 = L1.reshape(n, 78, 5).min(2)
    tp = (H1 + L1 + C1) / 3; cv = np.cumsum(V1, 1); vw1 = np.cumsum(tp * V1, 1) / np.where(cv > 0, cv, np.nan)
    vw1 = pd.DataFrame(vw1).ffill(axis=1).values; vw1 = np.where(np.isnan(vw1), tp, vw1)
    VW = vw1[:, 4::5]
    atr = F.atr.reindex(syms).values; pcv = F.pc.reindex(syms).values
    sess_open = O1[:, 0]; gap = sess_open / pcv - 1
    sp = si["SPY"]; atrs = atr[sp]
    ORhi = H5[:, :6].max(1); ORlo = L5[:, :6].min(1); ORw = ORhi - ORlo; ORmid = (ORhi + ORlo) / 2
    p950 = C5[:, 3]
    # SPY cues per bar k
    or30s = ORw[sp] / atrs
    rng_to = np.maximum.accumulate(H5[sp]) - np.minimum.accumulate(L5[sp])
    or20hi = H5[sp, :4].max()
    isuni = ok.copy(); isuni[sp] = False
    breadth = (C5[isuni] > p950[isuni, None]).mean(0)
    up = (C5[sp] > or20hi) & (C5[sp] >= p950[sp] + 0.10 * atrs) & (breadth >= 0.55)
    up[:4] = False
    K = np.arange(78)
    rows, rand = [], []
    rng = np.random.default_rng(rng_seed)
    base_ok = isuni & (atr > 0)
    rngok = base_ok & (np.abs(gap) <= 0.03)
    upok = base_ok & (np.abs(gap) <= 0.08)
    win_q = (K >= 11) & (K <= 59); win_u = (K >= 8) & (K <= 47)
    A_ = atr[:, None]
    setups = {}
    # S1 failed breakdown long / S2 failed breakout short
    for sid, side in (("S1", 1), ("S2", -1)):
        if side > 0:
            brk = (L5 < (ORlo - 0.05 * atr)[:, None]) & (K >= 6)
        else:
            brk = (H5 > (ORhi + 0.05 * atr)[:, None]) & (K >= 6)
        fb = first_true(brk)
        after = (K[None, :] >= fb[:, None]) & (fb[:, None] >= 0)
        if side > 0:
            ext = np.minimum.accumulate(np.where(after, L5, np.inf), 1); stop = ext - 0.03 * A_
            back = C5 > ORlo[:, None]
        else:
            ext = np.maximum.accumulate(np.where(after, H5, -np.inf), 1); stop = ext + 0.03 * A_
            back = C5 < ORhi[:, None]
        within = after & (K[None, :] <= fb[:, None] + 6)
        okw = ((ORw >= 0.25 * atr) & (ORw <= 0.90 * atr) & rngok)[:, None]
        tgt = np.broadcast_to(ORmid[:, None], C5.shape)
        sig = within & back & okw
        setups[sid] = (side, sig, stop, tgt, win_q, "Q", rngok)
    # S3 VWAP stretch long
    lowsofar = np.minimum.accumulate(L5, 1); stop3 = lowsofar - 0.03 * A_
    prevc = np.concatenate([C5[:, :1], C5[:, :-1]], 1)
    sig3 = (C5 <= VW - 0.40 * A_) & (C5 > O5) & (C5 > prevc) & rngok[:, None]
    setups["S3"] = (1, sig3, stop3, VW, win_q, "Q", rngok)
    # S4 up-day VWAP pullback long (leaders at 10:00)
    lead = (C5[:, 5] >= p950 + 0.25 * atr) & (C5[:, 5] > VW[:, 5]) & upok
    stop4 = np.minimum(L5, VW) - 0.05 * A_
    sig4 = lead[:, None] & (L5 <= VW + 0.05 * A_) & (C5 > VW) & (C5 > O5)
    setups["S4"] = (1, sig4, stop4, None, win_u, "U", upok)
    quiet = (or30s <= QCUT) & (rng_to <= 1.25 * ORw[sp])
    quiet[:6] = False
    for sid, (side, sig, stop, tgt, win, cue, pool) in setups.items():
        e = C5; R = side * (e - stop)
        tg = (e + side * 2.0 * R) if tgt is None else tgt
        rr_ok = (R >= 0.08 * A_) & (R <= 0.40 * A_) & np.isfinite(R)
        if tgt is not None:
            rr_ok &= side * (tg - e) >= R
        base = sig & rr_ok & win[None, :]
        cvec = quiet if cue == "Q" else up
        for var, mask in (("cue", base & cvec[None, :]), ("nocue", base)):
            ft = first_true(mask)
            for i in np.nonzero(ft >= 0)[0]:
                k = ft[i]; ee = e[i, k]; st = stop[i, k]; tt = tg[i, k]; RR = R[i, k]
                w = walk(O1[i], H1[i], L1[i], 5 * (k + 1), side, ee, st, tt)
                if w is None:
                    continue
                px, jx, kind = w
                net = (side * (px - ee) - cost(ee, px, np.array(kind))) / RR
                rows.append((d, sid, var, syms[i], int(k), 5 * (k + 1), jx, side, ee, st, tt, RR / atr[i], side * (px - ee) / RR,
                             float(net), int(kind), gap[i]))
                if var == "cue":
                    cand = np.nonzero(pool)[0]; cand = cand[cand != i]
                    for j in rng.choice(cand, size=min(3, len(cand)), replace=False):
                        e2 = C5[j, k]; R2 = (RR / atr[i]) * atr[j]; st2 = e2 - side * R2; tt2 = e2 + side * (side * (tt - ee) / RR) * R2
                        w2 = walk(O1[j], H1[j], L1[j], 5 * (k + 1), side, e2, st2, tt2)
                        if w2 is None:
                            continue
                        px2, jx2, kd2 = w2
                        net2 = (side * (px2 - e2) - cost(e2, px2, np.array(kd2))) / R2
                        rand.append((d, sid, syms[j], int(k), side, float(net2)))
    cols = ["date", "setup", "var", "symbol", "k", "em", "xm", "side", "e", "stop", "tgt", "r_atr", "r_gross", "r", "kind", "gap"]
    T = pd.DataFrame(rows, columns=cols)
    RD = pd.DataFrame(rand, columns=["date", "setup", "symbol", "k", "side", "r"])
    info = dict(date=d, n_uni=int(isuni.sum()), or30s=float(or30s), atrs=float(atrs), quiet_any=bool(quiet.any()),
                quiet_k=int(np.argmax(quiet)) if quiet.any() else -1, up_any=bool(up.any()),
                up_k=int(np.argmax(up)) if up.any() else -1, spy_oc=float(C1[sp, -1] / O1[sp, 0] - 1),
                spy_950_close=float(C1[sp, -1] / p950[sp] - 1), breadth_1000=float(breadth[5]), breadth_max=float(breadth.max()))
    return T, RD, info


QCUT = float(os.environ.get("QCUT", "9"))

if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    days = sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    for d in days:
        fo = f"{out}/{d}"
        if os.path.exists(fo + ".json"):
            continue
        try:
            r = run(d, int(d.replace("-", "")))
        except Exception as ex:  # noqa
            print("ERR", d, repr(ex), flush=True); continue
        if r is None:
            print("SKIP", d, flush=True); continue
        T, RD, info = r
        T.to_csv(fo + "_t.csv", index=False); RD.to_csv(fo + "_r.csv", index=False)
        json.dump(info, open(fo + ".json", "w"))
        print("OK", d, len(T), flush=True)
