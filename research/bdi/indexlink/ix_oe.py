"""Task 3 (NOTES 1.5, lineage ix-oe): the owner's thought experiment - SPY's move from the open at decision time T,
then buy / sell an instrument and hold to 15:55 (or 30 / 60 min). Parts A (fixed T), B (dipped at some point),
C (random entry time), D (ten-year daily, gap-conditioned). Writes oe_results.csv, oe_diag.json.
Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

from common import DATA, HERE, ROOT, SPDR, W2ETFS, bars, etf1m, ffill_rows, lib, pit_betas
from mcf.research import gates

TS = [945, 950, 1000, 1015, 1030, 1100, 1200, 1300, 1400]
THR = [0.2, 0.4, 0.6]
HOLDS = ["close", "30", "60"]
INSTR = ["SPY", "QQQ", "IWM", "DIA", "SECT", "HIBETA", "LINKED"]
N_OE = 2995
TREQ = max(2.0, gates.t_required(N_OE))
REG = lib.regimes()


def m_of(hhmm):  # 1-minute index whose bar ENDS at hhmm (minute 0 = 09:30-09:31)
    return (hhmm // 100) * 60 + hhmm % 100 - 570 - 1


def b_of(hhmm):  # 5-minute index whose bar ENDS at hhmm (bar 0 ends 09:35)
    return ((hhmm // 100) * 60 + hhmm % 100 - 575) // 5


def add_min(hhmm, k):
    t = (hhmm // 100) * 60 + hhmm % 100 + k
    return (t // 60) * 100 + t % 60


def stat(r, dates, extra=None):
    """One observation per session. r in % (net)."""
    ok = np.isfinite(r)
    r, d = r[ok], np.asarray(dates)[ok]
    n = len(r)
    if n < 2:
        return {"n": n}
    mu, sd = r.mean(), r.std(ddof=1)
    tr = pd.DataFrame({"date": d, "symbol": "x", "r": r})
    reg = pd.Series(d).map(REG["regime"]).to_numpy()
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS, min_n=5)
    b = np.argmax(r)
    yr = pd.Series(r).groupby(pd.Series([x.year for x in d])).mean().round(4).to_dict()
    out = {"n": n, "win": round(float((r > 0).mean()), 3), "mean": round(float(mu), 4), "median": round(float(np.median(r)), 4),
           "t": round(float(mu / (sd / np.sqrt(n))), 2) if sd > 0 else None,
           "up": round(float(r[reg == "up"].mean()), 4) if (reg == "up").any() else None, "up_n": int((reg == "up").sum()),
           "flat": round(float(r[reg == "flat"].mean()), 4) if (reg == "flat").any() else None,
           "down": round(float(r[reg == "down"].mean()), 4) if (reg == "down").any() else None, "down_n": int((reg == "down").sum()),
           "wf": wf["share_positive"], "ex_best_day": round(float((r.sum() - r[b]) / (n - 1)), 4),
           "by_year": json.dumps({str(k): v for k, v in yr.items()})}
    if extra:
        out.update(extra)
    return out


def welch(a, b):
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return None
    return round(float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))), 2)


def main():
    meta, C5, V5, O0, CL = bars()
    syms, dates = meta["syms"], meta["dates"]
    ND = len(dates)
    si = {s: i for i, s in enumerate(syms)}
    esyms, E = etf1m()
    ei = {s: i for i, s in enumerate(esyms)}
    Ec = ffill_rows(E["close"].astype(np.float64))
    El = E["low"].astype(np.float64)
    Eo = E["open"].astype(np.float64)
    first = np.argmax(np.isfinite(Eo), axis=2)
    E_open = np.take_along_axis(Eo, first[..., None], axis=2)[..., 0]
    spy = ei["SPY"]
    spy_o = E_open[spy]
    pb, R, adv = pit_betas(syms, dates)
    nonetf = np.array([s not in W2ETFS for s in syms])
    # point-in-time baskets (30 names, adv20 >= 95M)
    baskets = {}
    for nm, key in (("HIBETA", "beta_spy"), ("LINKED", "corr_spy")):
        mem = np.full((ND, 30), -1, int)
        for t in range(ND):
            v = pb[key][t].astype(float)
            ok = np.isfinite(v) & nonetf & (np.nan_to_num(adv[t]) >= 95e6)
            if ok.sum() >= 30:
                idx = np.flatnonzero(ok)
                mem[t] = idx[np.argsort(-v[idx])[:30]]
        baskets[nm] = mem
    np.savez(DATA / "baskets.npz", **baskets)
    C5a = C5  # memmap
    days = np.arange(ND)

    def path_1m(names, m_in, m_out):
        """Equal-weight return % and cost % for ETFs from 1-minute closes; m_in / m_out arrays [ND] or ints."""
        rets, costs = [], []
        for s in names:
            c = Ec[ei[s]]
            pin = c[days, m_in]
            pout = c[days, m_out]
            rets.append((pout / pin - 1) * 100)
            costs.append(pin)
        return np.nanmean(np.vstack(rets), 0), np.vstack(costs)

    def inst_ret(inst, hin, hout, side):
        """Net % per session: entry at hhmm hin (1-min instruments enter the minute after), exit at hhmm hout."""
        mult = float(gates.tod_cost_mult([hin])[0])
        if inst in ("SPY", "QQQ", "IWM", "DIA", "SECT"):
            names = SPDR if inst == "SECT" else [inst]
            mi, mo = m_of(add_min(hin, 1)), m_of(hout)
            rr, cc = [], []
            for s in names:
                c = Ec[ei[s]]
                pin, pout = c[:, mi], c[:, mo]
                rr.append(side * (pout / pin - 1) * 100)
                cc.append(((0.01 / pin + 1e-4) * mult + (0.01 / pout + 1e-4)) * 100)
            return np.nanmean(np.vstack(rr), 0) - np.nanmean(np.vstack(cc), 0)
        bi, bo = b_of(hin), b_of(hout)
        mem = baskets[inst]
        out = np.full(ND, np.nan)
        for t in range(ND):
            if mem[t, 0] < 0:
                continue
            pin = C5a[mem[t], t, bi].astype(float)
            pout = C5a[mem[t], t, bo].astype(float)
            r = side * (pout / pin - 1) * 100 - ((0.01 / pin + 1e-4) * mult + (0.01 / pout + 1e-4)) * 100
            out[t] = np.nanmean(r) if np.isfinite(r).any() else np.nan
        return out

    def hold_out(T, h):
        return 1555 if h == "close" else add_min(T, int(h))

    rows, cache = [], {}

    def get(inst, T, h, side):
        k = (inst, T, h, side)
        if k not in cache:
            cache[k] = inst_ret(inst, T, hold_out(T, h), side)
        return cache[k]

    spy_fo = {T: (Ec[spy][:, m_of(T)] / spy_o - 1) * 100 for T in TS + list(range(950, 1505, 5))}
    # ---------------- A: fixed time
    for T in TS:
        fo = spy_fo[T]
        for inst in INSTR:
            for h in HOLDS:
                L, S = get(inst, T, h, 1), get(inst, T, h, -1)
                for nm, r in (("uncond_long", L), ("uncond_short", S)):
                    rows.append({"part": "A", "T": T, "inst": inst, "hold": h, "cond": "all", "action": nm, "control": True,
                                 "diag": T < 950, **stat(r, dates)})
                for x in THR:
                    dip, rally = fo <= -x, fo >= x
                    for cond, msk, acts in ((f"dip{x}", dip, (("buy_dip", L, L), ("sell_follow", S, S))),
                                            (f"rally{x}", rally, (("buy_follow", L, L), ("sell_fade", S, S)))):
                        for act, r, ctrl in acts:
                            rr = np.where(msk, r, np.nan)
                            rows.append({"part": "A", "T": T, "inst": inst, "hold": h, "cond": cond, "action": act,
                                         "control": False, "diag": T < 950,
                                         **stat(rr, dates, {"vs_control_t": welch(rr, ctrl),
                                                            "control_mean": round(float(np.nanmean(ctrl)), 4)})})
        print("A", T, flush=True)
    # ---------------- B: dipped at some point (1-minute lows from 09:30 to T)
    for T in (950, 1000, 1030):
        low = np.nanmin(El[spy][:, :m_of(T) + 1], axis=1)
        mn = (low / spy_o - 1) * 100
        for inst in INSTR:
            for h in HOLDS:
                L = get(inst, T, h, 1)
                for x in THR:
                    rr = np.where(mn <= -x, L, np.nan)
                    rows.append({"part": "B", "T": T, "inst": inst, "hold": h, "cond": f"lowsofar{x}", "action": "buy_dip",
                                 "control": False, "diag": False,
                                 **stat(rr, dates, {"vs_control_t": welch(rr, L), "control_mean": round(float(np.nanmean(L)), 4)})})
    print("B done", flush=True)
    # ---------------- C: random entry time (every 5-min bar close 09:50..15:00 equally likely; one average per session)
    Tc = [t for t in range(950, 1505, 5) if t % 100 < 60]
    for inst in INSTR:
        L = np.vstack([get(inst, T, "close", 1) for T in Tc])        # [bars, ND]
        S = -L - 2 * 0  # placeholder replaced below
        S = np.vstack([get(inst, T, "close", -1) for T in Tc])
        F = np.vstack([spy_fo[T] for T in Tc])
        ctrlL, ctrlS = np.nanmean(L, 0), np.nanmean(S, 0)
        rows.append({"part": "C", "T": "random", "inst": inst, "hold": "close", "cond": "all", "action": "uncond_long",
                     "control": True, "diag": False, **stat(ctrlL, dates)})
        rows.append({"part": "C", "T": "random", "inst": inst, "hold": "close", "cond": "all", "action": "uncond_short",
                     "control": True, "diag": False, **stat(ctrlS, dates)})
        for x in (0.2, 0.4):
            for cond, msk, acts in ((f"dip{x}", F <= -x, (("buy_dip", L, ctrlL), ("sell_follow", S, ctrlS))),
                                    (f"rally{x}", F >= x, (("buy_follow", L, ctrlL), ("sell_fade", S, ctrlS)))):
                for act, M, ctrl in acts:
                    with np.errstate(invalid="ignore"):
                        rr = np.nanmean(np.where(msk, M, np.nan), 0)
                    rows.append({"part": "C", "T": "random", "inst": inst, "hold": "close", "cond": cond, "action": act,
                                 "control": False, "diag": False,
                                 **stat(rr, dates, {"vs_control_t": welch(rr, ctrl), "control_mean": round(float(np.nanmean(ctrl)), 4)})})
    print("C done", flush=True)
    # ---------------- diagnostics: SPY rest-of-day on move-to-T; entry-delay effect
    diag = {}
    for T in TS:
        x = spy_fo[T]
        y = (Ec[spy][:, m_of(1555)] / Ec[spy][:, m_of(T)] - 1) * 100
        ok = np.isfinite(x) & np.isfinite(y)
        X = np.c_[np.ones(ok.sum()), x[ok]]
        beta, res = np.linalg.lstsq(X, y[ok], rcond=None)[:2]
        e = y[ok] - X @ beta
        se = np.sqrt(e.var(ddof=2) * np.linalg.inv(X.T @ X)[1, 1])
        same = (Ec[spy][:, m_of(1555)] / Ec[spy][:, m_of(T)] - 1) * 100
        nxt = (Ec[spy][:, m_of(1555)] / Ec[spy][:, m_of(add_min(T, 1))] - 1) * 100
        diag[str(T)] = {"rod_on_move_slope": round(float(beta[1]), 4), "slope_t": round(float(beta[1] / se), 2),
                        "rho": round(float(np.corrcoef(x[ok], y[ok])[0, 1]), 3),
                        "spy_rod_mean_after_dip0.4": round(float(np.nanmean(np.where(x <= -0.4, y, np.nan))), 4),
                        "spy_rod_mean_all": round(float(np.nanmean(y)), 4),
                        "entry_delay_effect_dip0.4_pct": round(float(np.nanmean(np.where(x <= -0.4, same - nxt, np.nan))), 4),
                        "dip0.4_sessions": int((x <= -0.4).sum()), "rally0.4_sessions": int((x >= 0.4).sum())}
    (HERE / "oe_diag.json").write_text(json.dumps(diag, indent=1))
    # ---------------- D: ten-year daily, gap-conditioned
    rows += part_d()
    out = pd.DataFrame(rows)
    out["t_req"] = TREQ
    finalize(out)


def part_d():
    d = pd.read_parquet(ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet",
                        columns=["symbol", "date", "open", "close"])
    d["date"] = pd.to_datetime(d["date"]).dt.date
    s = d["date"].astype(str)
    d = d[(s < lib.LOCKED[0]) | (s > lib.LOCKED[1])]
    reg = gates.session_regimes(d[~d["symbol"].isin(W2ETFS)])
    o = d.pivot_table(index="date", columns="symbol", values="open")
    c = d.pivot_table(index="date", columns="symbol", values="close")
    dates = list(o.index)
    gap = (o["SPY"] / c["SPY"].shift(1) - 1) * 100
    # the previous row may be across the dropped locked block: no gap there
    prev = pd.Series(dates).shift(1)
    jump = np.array([(a - b).days > 5 if isinstance(b, type(a)) else True for a, b in zip(dates, prev)])
    gap[jump] = np.nan
    rows = []
    global REG
    keep_reg = REG
    REG = reg
    for inst in ("SPY", "QQQ", "IWM", "DIA", "SECT"):
        names = SPDR if inst == "SECT" else [inst]
        oo, cc = o[names].to_numpy(float), c[names].to_numpy(float)
        cost = (2 * (0.01 / oo) + 2e-4) * 100
        for side, act0 in ((1, "uncond_long"), (-1, "uncond_short")):
            r = np.nanmean(side * (cc / oo - 1) * 100 - cost, 1)
            rows.append({"part": "D", "T": "open", "inst": inst, "hold": "close", "cond": "all", "action": act0,
                         "control": True, "diag": False, **stat(r, dates)})
            for x in (0.2, 0.4, 0.6, 1.0):
                for cond, msk, act in ((f"gapdn{x}", gap <= -x, "buy_dip" if side == 1 else "sell_follow"),
                                       (f"gapup{x}", gap >= x, "buy_follow" if side == 1 else "sell_fade")):
                    rr = np.where(msk.to_numpy(), r, np.nan)
                    rows.append({"part": "D", "T": "open", "inst": inst, "hold": "close", "cond": cond, "action": act,
                                 "control": False, "diag": False,
                                 **stat(rr, dates, {"vs_control_t": welch(rr, r), "control_mean": round(float(np.nanmean(r)), 4)})})
    REG = keep_reg
    print("D done", flush=True)
    return rows


def finalize(out):
    out = out.copy()
    out["plateau_ok"] = None
    key = ["part", "inst", "hold", "action"]
    for i, r in out.iterrows():
        if r["control"] or r["part"] not in ("A", "B") or not isinstance(r["cond"], str):
            continue
        fam = r["cond"].rstrip("0123456789.")
        x = float(r["cond"][len(fam):])
        nbx = [y for y in THR if abs(y - x) < 0.21 and y != x]
        m = (out["part"] == r["part"]) & (out["inst"] == r["inst"]) & (out["hold"] == r["hold"]) & (out["action"] == r["action"])
        thr_ok = all((out.loc[m & (out["T"] == r["T"]) & (out["cond"] == f"{fam}{y}"), "mean"] > 0).all() for y in nbx)
        Ts = TS if r["part"] == "A" else [950, 1000, 1030]
        j = Ts.index(r["T"])
        nbT = [Ts[k] for k in (j - 1, j + 1) if 0 <= k < len(Ts) and Ts[k] >= 950]
        T_ok = all((out.loc[m & (out["T"] == t) & (out["cond"] == r["cond"]), "mean"] > 0).all() for t in nbT)
        out.at[i, "plateau_ok"] = bool(thr_ok and T_ok)
    cand = (~out["control"].astype(bool)) & (~out["diag"].astype(bool)) & (out["n"] >= 100) & (out["mean"] > 0) \
        & (out["up"].fillna(-1) > 0) & (out["down"].fillna(-1) > 0) & (out["t"].fillna(0) >= TREQ) \
        & (out["vs_control_t"].fillna(0) >= 2.0) & (out["wf"].fillna(0) >= 0.6) & (out["ex_best_day"].fillna(-1) > 0) \
        & ((out["part"] == "C") | (out["part"] == "D") | (out["plateau_ok"] == True))  # noqa: E712
    out["candidate"] = cand
    out.to_csv(HERE / "oe_results.csv", index=False)
    print("configs", int(len(out)), "candidates", int(cand.sum()), flush=True)


if __name__ == "__main__":
    main()
