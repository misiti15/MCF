"""swarm1013 backtest step 3: score every pre-declared configuration of PLAN.md (E1-E6 + references).

Vectorised exit engine on 5-minute bars (offset j = 1.. from the fill bar k+1 to the 15:55 bar), prices expressed in
the trade's favourable direction in lab R relative to the fill. Production costs per PLAN section 0. Open history only
(inputs from signals.py / bars.py; the locked block is never loaded).
Writes results.csv (every cell), finalists.csv, summary.json, data_trades_B1.parquet-free (nothing large in git).
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from signals import SCR, SETUPS  # noqa: E402

SP, BP, SX = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA
K_LAST = 76
J = 74
N_STUDY = 402
T_REQ = gates.t_required(N_STUDY)
SHORTS = [s for s in SETUPS if s not in ("NS1", "NS5")]
LONGS = ["NS1", "NS5"]
MF = ["MF1", "MF2", "MF3", "MF4", "MF5"]

# ------------------------------------------------------------------------------------------------ data
T = pd.read_parquet(SCR / "trades0.parquet")
Z = np.load(SCR / "bars.npz")
B = {k: Z[k].astype(np.float64) for k in Z.files}
DAYS = pd.read_parquet(SCR / "days.parquet")
MK = np.load(SCR / "mkt.npz")
REG = lib.regimes()
DATES = sorted(REG.index)
REGC = np.array([{"up": 0, "flat": 1, "down": 2}[REG.loc[d, "regime"]] for d in DATES])
NS = len(DATES)

T = T[(T["k"] <= 65)].reset_index(drop=True)
N = len(T)
d = T["drow"].to_numpy(int)
k = T["k"].to_numpy(int)
sess = T["sess"].to_numpy(int)
s = np.where(T["side"].to_numpy() == "long", 1.0, -1.0)
UP = np.array([gates.GEOMK[g][0] for g in T["geom"]])
DN = np.array([gates.GEOMK[g][1] for g in T["geom"]])
R = 0.25 * T["atr_d"].to_numpy(float)
ref = B["C"][d, k]
gap = T["gap"].to_numpy(float)
ext = np.where((np.abs(gap) >= 20) | (ref < 5), 3.0, 1.0)
mult = gates.tod_cost_mult(T["tod"].to_numpy())
h = (SP + ref * BP) * mult * ext                                         # half spread paid in the fill price
fill = B["O"][d, k + 1] + s * h
valid_sess = np.array([str(x) > "2025-12-31" for x in DATES])
VA = valid_sess[sess]
RG = REGC[sess]

# bar matrices in favourable-direction R relative to the fill: offset j -> bar k + j (j = 1 is the fill bar)
cols = k[:, None] + np.arange(1, J + 1)[None, :]
inb = cols <= K_LAST
cc = np.minimum(cols, K_LAST)
rows = d[:, None]
O_, H_, L_, C_ = (B[x][rows, cc] for x in "OHLC")
fav_px = np.where(s[:, None] > 0, H_, L_)
adv_px = np.where(s[:, None] > 0, L_, H_)
U = lambda px, base: s[:, None] * (px - base[:, None]) / R[:, None]
OPN, FAV, ADV, CLS = U(O_, fill), U(fav_px, fill), U(adv_px, fill), U(C_, fill)
JLAST = K_LAST - k                                                       # offset of the 15:55 bar
ok_trade = np.isfinite(fill) & np.isfinite(ref) & (R > 0) & np.isfinite(CLS[np.arange(N), JLAST - 1])
P = s * (fill - ref) / R                                                 # progress of the fill toward target (R)
del O_, H_, L_, C_, fav_px, adv_px

# index condition arrays: s * (idx close - idx VWAP) at offsets and at the signal bar
esyms = [str(x) for x in MK["syms"]]
lk = pd.read_csv(ROOT / "research/bdi/indexlink/linkage.csv", usecols=["symbol", "sector_etf"]).set_index("symbol")["sector_etf"]
sect = T["symbol"].map(lk).where(lambda x: x.isin(esyms), "QQQ").fillna("QQQ").to_numpy()


def idx_side(etf_per_trade):
    out = np.full((N, J), np.nan)
    sig = np.full(N, np.nan)
    for e in np.unique(etf_per_trade):
        m = etf_per_trade == e
        C, VW = MK[f"{e}_C"].astype(float), MK[f"{e}_VW"].astype(float)
        dd = s[m][:, None] * (C - VW)[sess[m][:, None], cc[m]]
        out[m] = dd
        sig[m] = s[m] * (C - VW)[sess[m], k[m]]
    return out, sig


IDX = {"QQQ": idx_side(np.array(["QQQ"] * N)), "SMH": idx_side(np.array(["SMH"] * N)), "SECT": idx_side(sect)}


# ------------------------------------------------------------------------------------------------ engine
def sim(anchor="ref", entry="fill", partial=None, trail=None, trail_arm=None, bar_trail=False, notarget=False,
        idx=None, idx_aln=False, tstop=None, be=None):
    """Net R per trade (lab R). anchor: 'ref' (live) or 'fill'. entry 'close' = B0 lab baseline."""
    if entry == "close":
        base = ref
        opn, fav, adv, cls = (X + (s * (fill - ref) / R)[:, None] for X in (OPN, FAV, ADV, CLS))
        p0 = np.zeros(N)
        entry_cost = h / R
    else:
        opn, fav, adv, cls = OPN, FAV, ADV, CLS
        p0 = P if anchor == "ref" else np.zeros(N)
        entry_cost = np.zeros(N)
        base = fill
    stop = -p0 - DN
    tgt = np.full(N, np.inf) if notarget else UP - p0
    pos = np.ones(N)
    gross = np.zeros(N)
    cost = entry_cost.copy()
    best = np.full(N, -np.inf)
    armed = np.zeros(N, bool)
    done = ~ok_trade.copy()
    exit_j = np.full(N, -1)
    did_partial = np.zeros(N, bool)
    unit_px = lambda u: base + s * u * R
    stop_c = lambda u: (SP + unit_px(u) * BP + SX) * ext / R
    mkt_c = lambda u: (SP + unit_px(u) * BP) * ext / R
    if idx is not None:
        icond, isig = IDX[idx]
        iarm = (isig >= 0) if idx_aln else np.ones(N, bool)
    for j in range(1, J + 1):
        a = ~done & (j <= JLAST)
        if not a.any():
            break
        o, f, v, c = opn[:, j - 1], fav[:, j - 1], adv[:, j - 1], cls[:, j - 1]
        # 1) stop first (gap through fills at the open)
        gs = a & (o <= stop)
        hs = a & ~gs & (v <= stop)
        xs = np.where(gs, o, stop)
        m = gs | hs
        gross[m] += pos[m] * xs[m]
        cost[m] += pos[m] * stop_c(xs)[m]
        pos[m] = 0
        done |= m
        exit_j[m] = j
        a &= ~m
        # 2) target (limit, free)
        ht = a & (f >= tgt)
        if partial is not None:
            first = ht & ~did_partial
            gross[first] += 0.5 * tgt[first]
            pos[first] = 0.5
            did_partial |= first
            tgt = np.where(first, np.inf, tgt)
        else:
            gross[ht] += pos[ht] * tgt[ht]
            pos[ht] = 0
            done |= ht
            exit_j[ht] = j
            a &= ~ht
        # 3) bar-close market exits
        mexit = np.zeros(N, bool)
        if idx is not None:
            mexit |= a & iarm & (icond[:, j - 1] < 0)
        best = np.where(a, np.fmax(best, f), best)
        if tstop is not None and j == tstop:
            mexit |= a & (best < 0.5)
        mexit |= a & (j == JLAST)
        gross[mexit] += pos[mexit] * c[mexit]
        cost[mexit] += pos[mexit] * mkt_c(c)[mexit]
        pos[mexit] = 0
        done |= mexit
        exit_j[mexit] = j
        a &= ~mexit
        # 4) stop updates for the next bar
        if be is not None:
            stop = np.where(a & (best >= be), np.fmax(stop, 0.0), stop)
        if trail is not None:
            if partial is not None:
                arm_now = did_partial
            else:
                arm_now = best >= trail_arm
            armed |= a & arm_now
            if bar_trail:
                stop = np.where(a & armed, np.fmax(stop, v), stop)
            else:
                stop = np.where(a & armed, np.fmax(stop, best - trail), stop)
    net = gross - cost
    net[~ok_trade] = np.nan
    return net, exit_j


# ------------------------------------------------------------------------------------------------ statistics
def tstat(r, ss):
    n = len(r)
    if n < 2:
        return (float(r.mean()) if n else np.nan), np.nan
    mu = r.mean()
    sm = np.bincount(ss, r, NS)
    cn = np.bincount(ss, minlength=NS)
    se = np.sqrt(((sm - cn * mu) ** 2).sum()) / n
    return float(mu), float(mu / se) if se > 0 else np.nan


MONTHS = sorted(set(pd.PeriodIndex(pd.to_datetime(DATES), freq="M").astype(str)))


def cell(family, variant, scope, sel, r_rule, kept, r_base):
    """sel: boolean scope mask over trades. r_rule: rule R (NaN = not a trade); kept: rule took the trade."""
    m = sel & np.isfinite(r_base)
    rb = r_base[m]
    rr = np.where(kept[m], r_rule[m], 0.0)
    dl = rr - rb
    ss, va, rg = sess[m], VA[m], RG[m]
    kp = kept[m]
    out = {"family": family, "variant": variant, "scope": scope, "n_base": int(m.sum()), "n_kept": int(kp.sum())}
    for nm, mm in (("train", ~va), ("valid", va), ("open", np.ones(len(rb), bool))):
        e, t = tstat(rr[mm & kp], ss[mm & kp])
        out[f"{nm}_n"], out[f"{nm}_exp"], out[f"{nm}_t"] = int((mm & kp).sum()), e, t
        e, t = tstat(rb[mm], ss[mm])
        out[f"{nm}_base_exp"] = e
        e, t = tstat(dl[mm], ss[mm])
        out[f"{nm}_delta"], out[f"{nm}_delta_t"] = e, t
    for code, nm in ((0, "up"), (1, "flat"), (2, "down")):
        mm = rg == code
        out[f"{nm}_delta"] = float(dl[mm].mean()) if mm.any() else np.nan
        out[f"{nm}_exp"] = float(rr[mm & kp].mean()) if (mm & kp).any() else np.nan
    # post-hoc diagnostic for skip rules (not a gate; NOTES.md): selectivity vs a random skip of the same share
    q = 1 - kp.mean() if len(kp) else np.nan
    out["skip_share"] = q
    if (~kp).sum() >= 2 and kp.sum() >= 2:
        es, ses = tstat(rb[~kp], ss[~kp])
        ek, sek = tstat(rb[kp], ss[kp])
        se = np.sqrt((es / ses) ** 2 + (ek / sek) ** 2) if np.isfinite(ses) and np.isfinite(sek) and ses and sek else np.nan
        out["skip_exp_base"], out["kept_exp_base"] = es, ek
        out["kept_minus_skip"], out["kept_minus_skip_t"] = ek - es, (ek - es) / se if se and np.isfinite(se) else np.nan
        out["delta_vs_random_skip"] = out["open_delta"] + q * out["open_base_exp"]
    if len(dl):
        ds = np.bincount(ss, dl, NS)
        dc = np.bincount(ss, minlength=NS)
        b = int(np.argmax(ds))
        out["delta_ex_best"] = float((ds.sum() - ds[b]) / max(1, len(dl) - dc[b]))
        wf = gates.walk_forward(pd.DataFrame({"date": np.array(DATES)[ss], "r": dl}), months=MONTHS,
                                exclude_months=lib.LOCKED_MONTHS)
        out["delta_wf_share"] = wf["share_positive"]
    return out


SCOPES = {"ALL": SETUPS, **{x: [x] for x in SETUPS}}
SETUP = T["setup"].to_numpy()
smask = lambda lst: np.isin(SETUP, lst)


def main():
    res = []
    ALLK = np.ones(N, bool)
    b1, b1_exit = sim()
    b0, _ = sim(entry="close")
    for sc, lst in SCOPES.items():
        res.append(cell("REF", "B1", sc, smask(lst), b1, ALLK, b1))
        res.append(cell("REF", "B0", sc, smask(lst), b0, ALLK, b1))
    # E1
    a_fill, _ = sim(anchor="fill")
    e1 = {"A": (a_fill, ALLK), "K25": (b1, P < 0.25), "K50": (b1, P < 0.5), "AK25": (a_fill, P < 0.25), "AK50": (a_fill, P < 0.5)}
    for v, (r, kp) in e1.items():
        for sc, lst in SCOPES.items():
            res.append(cell("E1", v, sc, smask(lst), r, kp, b1))
    print("E1", flush=True)
    # E2
    e2 = {"P-T05": sim(partial=0.5, trail=0.5)[0], "P-BAR": sim(partial=0.5, trail=0.0, bar_trail=True)[0],
          "NT075": sim(notarget=True, trail=0.5, trail_arm=0.75)[0], "NT100": sim(notarget=True, trail=0.5, trail_arm=1.0)[0]}
    for v, r in e2.items():
        for sc, lst in SCOPES.items():
            res.append(cell("E2", v, sc, smask(lst), r, ALLK, b1))
    print("E2", flush=True)
    # E3
    sc3 = {"ALL": SETUPS, "SHORTS": SHORTS, "LONGS": LONGS, **{x: [x] for x in SETUPS}}
    for ix in ("QQQ", "SMH", "SECT"):
        for aln in (False, True):
            r, _ = sim(idx=ix, idx_aln=aln)
            for sc, lst in sc3.items():
                res.append(cell("E3", f"{ix}-{'aln' if aln else 'any'}", sc, smask(lst), r, ALLK, b1))
    print("E3", flush=True)
    # E4
    for v, kw in {"T20": {"tstop": 4}, "T30": {"tstop": 6}, "T45": {"tstop": 9}, "BE03": {"be": 0.3},
                  "T20+BE": {"tstop": 4, "be": 0.3}, "T30+BE": {"tstop": 6, "be": 0.3}, "T45+BE": {"tstop": 9, "be": 0.3}}.items():
        r, _ = sim(**kw)
        for sc, lst in SCOPES.items():
            res.append(cell("E4", v, sc, smask(lst), r, ALLK, b1))
    print("E4", flush=True)
    # E5
    from book import corr_cap
    for v, kp in corr_cap(T, b1, b1_exit, ok_trade, sect).items():
        for sc, lst in SCOPES.items():
            res.append(cell("E5", v, "BOOK" if sc == "ALL" else sc, smask(lst), b1, kp, b1))
    print("E5", flush=True)
    # E6
    fo, vd = T["fromOpen"].to_numpy(float), T["vwapDistPct"].to_numpy(float)
    for v, kp in {"fo>0&vd>=0.10": (fo > 0) & (vd >= 0.10), "fo>0": fo > 0, "vd>=0.10": vd >= 0.10,
                  "fo>0&vd>=0.20": (fo > 0) & (vd >= 0.20)}.items():
        res.append(cell("E6", f"MF5-a {v}", "MF5", smask(["MF5"]), b1, kp, b1))
    o0 = DAYS.set_index("drow")["open0"].reindex(d).to_numpy(float)
    c_back = np.where(k >= 6, B["C"][d, np.maximum(k - 6, 0)], o0)
    r30 = (ref / c_back - 1) * 100
    for th in (0.25, 0.50):
        kp = ~(r30 > th)
        for sc, lst in {"MF": MF, **{x: [x] for x in MF}}.items():
            res.append(cell("E6", f"FS30 >{th:.2f}%", sc, smask(lst), b1, kp, b1))
    dl = lib.daily()[["symbol", "date", "close"]].copy()
    dl["date"] = pd.to_datetime(dl["date"])
    dl = dl.sort_values(["symbol", "date"])
    g = dl.groupby("symbol")
    dl["c1"], dl["c4"], dl["d4"] = g["close"].shift(1), g["close"].shift(4), g["date"].shift(4)
    dl["ret3"] = np.where((dl["date"] - dl["d4"]).dt.days <= 8, (dl["c1"] / dl["c4"] - 1) * 100, np.nan)
    ret3 = T[["symbol", "date"]].merge(dl[["symbol", "date", "ret3"]], on=["symbol", "date"], how="left")["ret3"].to_numpy()
    for th in (-10, -15):
        kp = ~(ret3 < th)
        for sc, lst in {"NS2": ["NS2"], "RW6G1": ["RW6G1"], "NS2+RW6G1": ["NS2", "RW6G1"]}.items():
            res.append(cell("E6", f"NS2-3D <{th}%", sc, smask(lst), b1, kp, b1))
    stop_ref = ref - s * DN * R
    for w, nb in ((15, 3), (30, 6)):
        hh = np.full(N, -np.inf)
        for q in range(nb):
            kk = np.maximum(k - q, 0)
            hh = np.fmax(hh, B["H"][d, kk])
        kp = ~((s < 0) & (stop_ref < hh))
        for sc, lst in {"SHORTS": SHORTS, **{x: [x] for x in SHORTS}}.items():
            res.append(cell("E6", f"SIR {w}m", sc, smask(lst), b1, kp, b1))
    print("E6", flush=True)

    df = pd.DataFrame(res)
    df.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
    pd.DataFrame({"date": np.array(DATES)[sess], "symbol": T["symbol"], "setup": SETUP, "k": k, "b1": b1, "b0": b0,
                  "P": P, "exit_j": b1_exit}).to_parquet(SCR / "b1_trades.parquet", index=False)
    print("cells", len(df), "N_STUDY", N_STUDY, flush=True)


if __name__ == "__main__":
    main()
