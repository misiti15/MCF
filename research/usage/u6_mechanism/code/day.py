"""U6 mechanism setups (M1-M5) + random controls: one session -> trades CSV.
Streams the session's 1min/1day packs from the public GitHub release, deletes them after use (rules in ../PLAN.md).
Educational only - not financial advice."""
import os, sys, json, re, subprocess, shutil, glob
import numpy as np, pandas as pd

S = os.environ.get("U6S", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u6")
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
URL = "https://github.com/misiti15/MCF/releases/download/{tag}/{kind}-{d}.parquet"
ETF_RX = r"\bETF\b|ETN|ProShares|Direxion|\bTrust\b|Leverage|2X|3X|-1X|Bull|Bear|Ultra|iShares|SPDR|Invesco|Fund|Shares"
LEV_RX = r"2X|3X|-1X|-2X|-3X|Ultra|Bull|Bear|Inverse|Short|VIX|Volatility|Leveraged|Daily"
SECT = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "XBI", "KRE", "XOP", "ITB"]
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))

U = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"])
NM = dict(zip(U.symbol.astype(str), U.name.fillna("").astype(str)))
ISETF = {s for s, n in NM.items() if re.search(ETF_RX, n)}
ISLEV = {s for s, n in NM.items() if re.search(LEV_RX, n) and s in ISETF}
EARN = json.load(open(f"{S}/earn_union.json")) if os.path.exists(f"{S}/earn_union.json") else {}


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


def tmult(tod):
    # PLAN: 3.8 up to and incl. the 09:35 close, 2.1 to 09:50, 1.4 to 10:30 (gates.py edges, 09:35 made inclusive)
    if tod <= 935:
        return 3.8
    for edge, m in TOD_COST[1:]:
        if tod < edge:
            return m
    return 1.0


def cost_entry(px, tod):
    return (0.01 + px * 1e-4) * tmult(tod) + px * 1e-4 + FEE_SEC * px + TAF + CAT


def cost_exit(px, kind):
    base = 0.01 + px * 1e-4
    c = 0.0 if kind == 1 else (base + max(0.02, 4e-4 * px) if kind == 0 else base + max(0.01, 1e-4 * px))
    return c + FEE_SEC * px + TAF + CAT


def walk(O, H, L, f, X, d, stop, tgt):
    """fill at O[f]; minutes f..X-1; time exit at O[X]. kind 0 stop, 1 target, 2 time."""
    h, l, o = H[f:X], L[f:X], O[f:X]
    if d > 0:
        hs = np.nonzero(l <= stop)[0]; ht = np.nonzero(h >= tgt + 0.01)[0] if tgt is not None else []
    else:
        hs = np.nonzero(h >= stop)[0]; ht = np.nonzero(l <= tgt - 0.01)[0] if tgt is not None else []
    js = hs[0] if len(hs) else 10**9; jt = ht[0] if len(ht) else 10**9
    if js == 10**9 and jt == 10**9:
        return O[X], X, 2
    if js <= jt:
        px = min(o[js], stop) if d > 0 else max(o[js], stop)
        return px, f + js, 0
    return tgt, f + jt, 1


def trade(O, H, L, f, X, d, sd_atr, atr, tR, k):
    e = O[f]; R = sd_atr * atr; stop = e - d * R
    tgt = None if tR is None else e + d * tR * R
    w = walk(O, H, L, f, X, d, stop, tgt)
    px, jx, kind = w
    tm = 9 * 60 + 35 + 5 * k
    hhmm = (tm // 60) * 100 + tm % 60
    net = d * (px - e) - cost_entry(e, hhmm) - cost_exit(px, kind)
    return e, stop, px, jx, kind, d * (px - e) / R, net / R


def blackout(d):
    if not EARN:
        return set()
    out = set()
    for s, ds in EARN.items():
        for e in ds:
            a, b = sorted([e, d])
            if abs(np.busday_count(a, b)) <= 4:
                out.add(s); break
    return out


def run(d, seed):
    P = fetch(d)
    day = P["1day"].copy(); day["symbol"] = day.symbol.astype(str)
    day["date"] = pd.to_datetime(day.ts, utc=True).dt.tz_convert("America/New_York").dt.date
    day = day[(day.date < pd.Timestamp(d).date()) & (day.date > LOCK_B)]
    assert not ((day.date >= LOCK_A) & (day.date <= LOCK_B)).any()
    day = day.sort_values(["symbol", "date"])
    g = day.groupby("symbol")
    pc = g.close.shift(1)
    day["tr"] = np.maximum(day.high, pc) - np.minimum(day.low, pc)
    day["dv"] = day.close * day.volume
    t20 = g.tail(20).groupby("symbol").agg(adv=("dv", "mean"), advsh=("volume", "mean"), n=("dv", "size"))
    a14 = day.groupby("symbol").tail(14).groupby("symbol").agg(atr=("tr", "mean"), na=("tr", "count"))
    F = pd.concat([t20, a14, g.close.last().rename("pc")], axis=1)
    F = F[(F.n >= 20) & (F.na >= 14)]
    # 50-session daily returns
    piv = day.pivot(index="date", columns="symbol", values="close").sort_index().iloc[-51:]
    ret = piv.pct_change().iloc[1:]

    m = P["1min"]; m = m.assign(symbol=m.symbol.astype(str))
    t = pd.to_datetime(m.ts, utc=True).dt.tz_convert("America/New_York")
    assert (t.dt.date == pd.Timestamp(d).date()).all()
    m["mn"] = (t.dt.hour * 60 + t.dt.minute).values
    m = m[(m.mn >= 570) & (m.mn <= 959)]
    bo = blackout(d)
    stk = F[(F.pc >= 10) & (F.adv >= 20e6) & (F.atr / F.pc >= 0.01) & (F.atr / F.pc <= 0.08)].index
    stk = {s for s in stk if s not in ISETF and s not in bo}
    lev = F[(F.pc >= 5) & (F.adv >= 20e6) & (F.atr / F.pc >= 0.01) & (F.atr / F.pc <= 0.20)].index
    lev = {s for s in lev if s in ISLEV}
    need = {"SPY"} | set(SECT)
    present = set(m.symbol.unique())
    if "SPY" not in present or "SPY" not in F.index:
        return None
    syms = sorted((stk | lev | need) & present & set(F.index))
    m = m[m.symbol.isin(syms)]
    si = {s: i for i, s in enumerate(syms)}; n = len(syms)
    A = {}
    for c in ("open", "high", "low", "close", "volume"):
        a = np.full((n, 390), np.nan); a[m.symbol.map(si).values, m.mn.values - 570] = m[c].values; A[c] = a
    C1 = pd.DataFrame(A["close"]).ffill(axis=1).bfill(axis=1).values
    O1 = np.where(np.isnan(A["open"]), C1, A["open"]); H1 = np.where(np.isnan(A["high"]), C1, A["high"])
    L1 = np.where(np.isnan(A["low"]), C1, A["low"]); V1 = np.nan_to_num(A["volume"])
    ok = (~np.isnan(A["open"][:, :5])).any(1) & ((~np.isnan(A["close"])).sum(1) >= 200)
    O5 = O1.reshape(n, 78, 5)[:, :, 0]; C5 = C1.reshape(n, 78, 5)[:, :, 4]
    H5 = H1.reshape(n, 78, 5).max(2); L5 = L1.reshape(n, 78, 5).min(2)
    tp = (H1 + L1 + C1) / 3; cv = np.cumsum(V1, 1); vw1 = np.cumsum(tp * V1, 1) / np.where(cv > 0, cv, np.nan)
    vw1 = pd.DataFrame(vw1).ffill(axis=1).values; vw1 = np.where(np.isnan(vw1), tp, vw1)
    VW = vw1[:, 4::5]; CV = cv[:, 4::5]
    HOD = np.maximum.accumulate(H5, 1); LOD = np.minimum.accumulate(L5, 1)
    rpos = (C5 - LOD) / np.where(HOD - LOD > 0, HOD - LOD, np.nan)
    atr = F.atr.reindex(syms).values; pcv = F.pc.reindex(syms).values; advsh = F.advsh.reindex(syms).values
    op = O1[:, 0]; gap = op / pcv - 1
    A_ = atr[:, None]
    mv = (C5 - op[:, None]) / A_
    K = np.arange(78)
    isstk = np.array([s in stk for s in syms]) & ok
    islev = np.array([s in lev for s in syms]) & ok
    sp = si["SPY"]
    prevc = np.concatenate([C5[:, :1], C5[:, :-1]], 1)

    # correlations (50 sessions)
    R_ = ret.reindex(columns=syms)
    Z = (R_ - R_.mean()) / R_.std()
    cnt = R_.notna().sum().values
    Zv = Z.fillna(0).values; nn = len(R_)
    corr_spy = (Zv * Zv[:, [sp]]).sum(0) / max(nn - 1, 1)
    sidx = [si[e] for e in SECT if e in si]
    cs = (Zv[:, :, None] * Zv[:, sidx][:, None, :]).sum(0) / max(nn - 1, 1)  # n x nsect
    best = cs.argmax(1); bestc = cs.max(1)
    etf_of = np.array(sidx)[best]
    mapped = (bestc >= 0.60) & (cnt >= 40)

    defs = []  # (sid, d, sig, strength, sd_atr, tR, exit_minute, cap)
    for d_ in (1, -1):
        # M1 opening drive
        thr = (0.05 + 0.025 * K)[None, :] * advsh[:, None]
        pos = rpos >= 0.80 if d_ > 0 else rpos <= 0.20
        sig = (isstk & (np.abs(gap) <= 0.03))[:, None] & (d_ * mv >= 0.40) & pos & (d_ * (C5 - VW) > 0) & (CV >= thr) & (K <= 2)[None, :]
        defs.append(("M1", d_, sig, d_ * mv, 0.40, 2.0, 90, 10))
        # M2 gap-and-go
        gq = (isstk & (d_ * gap >= np.maximum(0.02, 0.5 * atr / pcv)) & (np.abs(gap) <= 0.15))
        if d_ > 0:
            held = (L5[:, :3].min(1) >= pcv + 0.5 * (op - pcv)) & (C5[:, 2] >= op)
            brk = C5 > H5[:, :3].max(1)[:, None]
        else:
            held = (H5[:, :3].max(1) <= pcv + 0.5 * (op - pcv)) & (C5[:, 2] <= op)
            brk = C5 < L5[:, :3].min(1)[:, None]
        sig = (gq & held)[:, None] & brk & (d_ * (C5 - VW) > 0) & ((K >= 3) & (K <= 12))[None, :]
        defs.append(("M2", d_, sig, np.broadcast_to((d_ * gap / (atr / pcv))[:, None], C5.shape), 0.50, 2.5, 385, 10))
        # M3 sector lag
        E = d_ * mv[etf_of]
        s_ = d_ * mv
        sig = (isstk & mapped & (np.abs(gap) <= 0.03))[:, None] & (E >= 0.75) & (s_ >= -0.25) & (s_ <= 0.35 * E) & \
            (d_ * (C5 - prevc) > 0) & (d_ * (C5 - VW) > 0) & ((K >= 5) & (K <= 47))[None, :]
        defs.append(("M3", d_, sig, E - s_, 0.40, 2.0, 385, 10))
        # M5 afternoon trend
        viol = (d_ * (C5 - VW) <= 0) & (K >= 17)[None, :]
        clean = np.cumsum(viol, 1) == 0
        prevext = np.maximum.accumulate(np.concatenate([np.full((n, 1), -np.inf), d_ * C5[:, :-1]], 1), 1)
        sig = (isstk & (np.abs(gap) <= 0.08))[:, None] & (d_ * mv >= 0.80) & clean & (d_ * C5 > prevext) & ((K >= 41) & (K <= 59))[None, :]
        defs.append(("M5", d_, sig, d_ * mv, 0.40, None, 385, 10))
    # M4 lev-ETF drive (long only)
    D = mv[sp]
    sig = (islev & (np.abs(corr_spy) >= 0.5) & (cnt >= 40))[:, None] & (np.abs(D) >= 0.25)[None, :] & \
        (np.sign(corr_spy)[:, None] == np.sign(D)[None, :]) & (mv >= 0.40) & (rpos >= 0.80) & (C5 > VW) & ((K >= 1) & (K <= 3))[None, :]
    defs.append(("M4", 1, sig, mv, 0.40, 2.0, 150, 5))

    rng = np.random.default_rng(seed)
    rows, rand = [], []
    for sid, d_, sig, stg, sd, tR, X, cap in defs:
        sig = sig & np.isfinite(A_) & (A_ > 0)
        taken = set(); cnt_ = 0
        pool = np.nonzero(islev if sid == "M4" else isstk)[0]
        for k in range(78):
            if cnt_ >= cap:
                break
            c = np.nonzero(sig[:, k])[0]
            if not len(c):
                continue
            c = c[np.argsort(-np.asarray(stg[c, k], float))]
            for i in c:
                if cnt_ >= cap or i in taken:
                    continue
                f = 5 * (k + 1)
                if f >= X:
                    continue
                e, stp, px, jx, kind, rg, rn = trade(O1[i], H1[i], L1[i], f, X, d_, sd, atr[i], tR, k)
                taken.add(i); cnt_ += 1
                rows.append((d, sid, syms[i], d_, k, f, jx, e, stp, px, kind, rg, rn, gap[i], float(stg[i, k])))
                cand = pool[pool != i]
                for j in rng.choice(cand, size=min(3, len(cand)), replace=False):
                    e2, s2, p2, j2, k2, rg2, rn2 = trade(O1[j], H1[j], L1[j], f, X, d_, sd, atr[j], tR, k)
                    rand.append((d, sid, syms[j], d_, k, rn2))
    T = pd.DataFrame(rows, columns=["date", "setup", "symbol", "side", "k", "fill_min", "exit_min", "e", "stop", "px",
                                    "kind", "r_gross", "r", "gap", "strength"])
    RD = pd.DataFrame(rand, columns=["date", "setup", "symbol", "side", "k", "r"])
    info = dict(date=d, n_stk=int(isstk.sum()), n_lev=int(islev.sum()), n_bo=len(bo), n_mapped=int((mapped & isstk).sum()),
                spy_oc=float(C1[sp, -1] / O1[sp, 0] - 1), spy_d935=float(mv[sp, 0]))
    return T, RD, info


if __name__ == "__main__":
    out = sys.argv[1]; days = sys.argv[2:]
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
