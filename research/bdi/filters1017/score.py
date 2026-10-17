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
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from signals import SCR, SETUPS  # noqa: E402

SP, BP, SX = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA
K_LAST = 76
J = 74
N_STUDY = 402 + 39
T_REQ = gates.t_required(N_STUDY)
SHORTS = [s for s in SETUPS if s not in ("NS1", "NS5")]
HERE = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/f1017/data")
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
    SC = {"ALL": SETUPS, **{x: [x] for x in SETUPS}}
    for sc, lst in SC.items():
        res.append(cell("REF", "B1", sc, smask(lst), b1, ALLK, b1))
    for v, kp in {"K25": P < 0.25, "K50": P < 0.5}.items():
        for sc, lst in SC.items():
            if v == "K50" and sc != "ALL":
                continue
            res.append(cell("E1", v, sc, smask(lst), b1, kp, b1))
    stop_ref = ref - s * DN * R
    for w, nb in ((15, 3), (30, 6)):
        hh = np.full(N, -np.inf)
        for q in range(nb):
            kk = np.maximum(k - q, 0)
            hh = np.fmax(hh, B["H"][d, kk])
        kp = ~((s < 0) & (stop_ref < hh))
        for sc, lst in {"SHORTS": SHORTS, **{x: [x] for x in SHORTS}}.items():
            if w == 30 and sc != "SHORTS":
                continue
            res.append(cell("E6", f"SIR {w}m", sc, smask(lst), b1, kp, b1))
        if w == 15:
            SIR15 = kp
    # same cells with the rule-2 holdout windows (2026-04..06, 2026-09-16..10-05) removed (diagnostic)
    dts = pd.to_datetime(np.array(DATES)[sess])
    hold = ((dts >= "2026-04-01") & (dts <= "2026-06-30")) | ((dts >= "2026-09-16") & (dts <= "2026-10-05"))
    for v, kp, lst in (("K25", P < 0.25, SETUPS), ("SIR 15m", SIR15, SHORTS)):
        res.append(cell("XH", v, "ALL" if v == "K25" else "SHORTS", smask(lst) & ~hold, b1, kp, b1))
    df = pd.DataFrame(res)
    df.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
    pd.DataFrame({"date": np.array(DATES)[sess], "symbol": T["symbol"], "setup": SETUP, "k": k, "b1": b1,
                  "P": P, "sir15": ~SIR15}).to_parquet(HERE / "b1_trades.parquet", index=False)
    print(df[["family", "variant", "scope", "n_base", "n_kept", "skip_share", "open_base_exp", "train_delta", "valid_delta",
              "open_delta", "open_delta_t", "skip_exp_base", "kept_exp_base", "kept_minus_skip", "kept_minus_skip_t",
              "delta_vs_random_skip", "delta_ex_best", "delta_wf_share", "up_delta", "down_delta"]].round(4).to_string())


if __name__ == "__main__":
    main()
