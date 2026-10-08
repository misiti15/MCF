"""Task 1 - the 'falling knife' re-evaluation: MANAGEMENT variants on heat_fade_long's own signals.
Signals: the production first signal per symbol-day (collect.py), Jul 15 - Sep 15 2026 (train <= 08-25, valid
08-26..09-15). Every variant is simulated with mcf.backtest.engine.simulate + production costs; results in R0
(0.25 x daily ATR of the signal). Also replays every variant on the six 2026-10-06 11:05 entries (live day,
outside the locked holdout; 1-minute bars fetched for the autopsy). Educational only - not financial advice.

usage: python research/oct7/bdi/task1_knife.py [LIVE_BARS_PARQUET]"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/bdi")
from lib import D, five, load, paired, r0, run, stats, vwap  # noqa: E402
from mcf.strategies.base import Signal  # noqa: E402

NAME = "heat_fade_long"
ET = "America/New_York"


def leg(tr, R0, kind):
    return dict(r=r0(tr, R0), kind=kind, reason=tr.exit_reason, entry_time=str(tr.entry_time.time()),
                exit_time=str(tr.exit_time.time()), entry=tr.entry, exit=tr.exit)


def base_sig(row, stop_r=1.0, tgt_r=1.0):
    px, R0 = row["px"], row["R0"]
    return Signal(row["symbol"], NAME, 1, int(row["end"]), stop=px - stop_r * R0,
                  target=None if tgt_r is None else px + tgt_r * R0)


def v_base(row, b):
    tr, _ = run(base_sig(row), b, row["ext"])
    return [leg(tr, row["R0"], "long")] if tr else []


def v_sar(m):
    def f(row, b):
        R0 = row["R0"]
        tr, k = run(base_sig(row), b, row["ext"])
        if not tr:
            return []
        out = [leg(tr, R0, "long")]
        if tr.exit_reason == "stop" and k + 1 < len(b):
            o1 = float(b["open"].iloc[k + 1])
            s = Signal(row["symbol"], NAME, -1, k, stop=o1 + R0, target=None if m is None else o1 - m * R0)
            t2, _ = run(s, b, row["ext"])
            if t2:
                out.append(leg(t2, R0, "rev_short"))
        return out
    return f


def v_tight(trigger, stop_r=0.5, until_min=330):   # until 15:00 (minute-of-session 330)
    def f(row, b):
        R0 = row["R0"]
        tr, k = run(base_sig(row, stop_r=stop_r), b, row["ext"])
        if not tr:
            return []
        out = [leg(tr, R0, "long")]
        if trigger is None or tr.exit_reason != "stop":
            return out
        o, h, l, c, last = five(b)
        vw = vwap(b)
        js = np.flatnonzero(last > k)   # 5-minute bars that complete after the stop bar
        lowest = np.inf
        for j in js:
            if j * 5 >= until_min:
                break
            vw_ok = c[j] > vw[last[j]]
            hl_ok = j > js[0] and l[j] > lowest and c[j] > h[j - 1]
            lowest = min(lowest, l[j])
            if (trigger == "vwap" and vw_ok) or (trigger == "hl" and hl_ok) or (trigger == "either" and (vw_ok or hl_ok)):
                s = Signal(row["symbol"], NAME, 1, int(last[j]), stop=c[j] - stop_r * R0, target=c[j] + R0)
                t2, _ = run(s, b, row["ext"])
                if t2:
                    out.append(leg(t2, R0, "re_long"))
                break
        return out
    return f


def v_confirm(trigger, window_bars):
    def f(row, b):
        R0 = row["R0"]
        o, h, l, c, last = five(b)
        vw = vwap(b)
        i5 = int(np.flatnonzero(last == row["end"])[0]) if (last == row["end"]).any() else None
        if i5 is None:
            return []
        for j in range(i5 + 1, min(i5 + 1 + window_bars, len(c))):
            ph = c[j] > h[j - 1]
            vr = c[j] > vw[last[j]]
            if (trigger == "prevhigh" and ph) or (trigger == "vwap" and vr) or (trigger == "either" and (ph or vr)):
                s = Signal(row["symbol"], NAME, 1, int(last[j]), stop=c[j] - R0, target=c[j] + R0)
                tr, _ = run(s, b, row["ext"])
                return [leg(tr, R0, "conf_long")] if tr else []
        return []
    return f


def v_cont(nbars, exit_kind):
    def f(row, b):
        R0 = row["R0"]
        o, h, l, c, last = five(b)
        hit = np.flatnonzero(last == row["end"])
        if not len(hit):
            return []
        i5 = int(hit[0])
        if i5 + nbars >= len(c):
            return []
        for j in range(i5 + 1, i5 + nbars + 1):
            if not l[j] < l[j - 1]:
                return []
        j = i5 + nbars
        if exit_kind == "t1":
            s = Signal(row["symbol"], NAME, -1, int(last[j]), stop=c[j] + R0, target=c[j] - R0)
        else:
            tr_r, after = exit_kind
            s = Signal(row["symbol"], NAME, -1, int(last[j]), stop=c[j] + R0, target=None, trail_r=tr_r, trail_after_r=after)
        tr, _ = run(s, b, row["ext"])
        return [leg(tr, R0, "cont_short")] if tr else []
    return f


VARIANTS = {"base": v_base}
for m in (1, 2, None):
    VARIANTS[f"a_sar_t{m}"] = v_sar(m)
for trg in (None, "vwap", "hl", "either"):
    VARIANTS[f"b_stop05_re_{trg}"] = v_tight(trg)
for trg in ("prevhigh", "vwap", "either"):
    for w in (6, 12):
        VARIANTS[f"c_conf_{trg}_{w*5}m"] = v_confirm(trg, w)
for n in (1, 2, 3):
    for ek, lab in (("t1", "t1"), ((0.5, 0.5), "trail05"), ((1.0, 1.0), "trail1")):
        VARIANTS[f"d_cont_ll{n}_{lab}"] = v_cont(n, ek)
CAPS = [(k, scope) for scope in ("allbars", "1105") for k in (1, 2, 3, 5)]


def cap_filter(S, k, scope):
    """Keep the top-k signals by heat score within each (date, signal bar); scope '1105' caps only the 11:05 bar."""
    S = S.sort_values("score", ascending=False)
    rk = S.groupby(["date", "end"]).cumcount()
    keep = rk < k
    if scope == "1105":
        keep |= S["sig_hhmm"] != "11:05"
    return S[keep]


def spy_state(spy_day: pd.DataFrame, end_idx_time) -> tuple[bool, bool]:
    """(SPY below its VWAP, SPY below its open) at the close of the signal minute - known at entry."""
    b = spy_day[spy_day.index <= end_idx_time]
    if b.empty:
        return False, False
    vw = vwap(b)[-1]
    return bool(b["close"].iloc[-1] < vw), bool(b["close"].iloc[-1] < b["open"].iloc[0])


def market_variants(S, base, spy_days):
    """f: per-setup daily circuit breaker (no new entry after N stops already closed today);
    g: skip (or flip to a 1R/1R short) when SPY is below VWAP at the signal."""
    out = {}
    B = base.copy()
    B["key"] = list(zip(B.symbol, B.date))
    for N in (2, 3):
        keep = []
        for d, g in B.sort_values("entry_time").groupby("date"):
            for r in g.itertuples():
                n_stops = int(((g.reason == "stop") & (g.exit_time <= r.entry_time)).sum())
                if n_stops < N:
                    keep.append(r.Index)
        out[f"f_breaker{N}"] = B.loc[keep].drop(columns="key")
    st = {}
    for r in S.itertuples():
        sd = spy_days.get(r.date)
        st[(r.symbol, r.date)] = spy_state(sd, r.sig_time) if sd is not None else (False, False)
    below_vw = B.key.map(lambda k: st[k][0])
    below_op = B.key.map(lambda k: st[k][1])
    out["g_skip_spy_below_vwap"] = B[~below_vw].drop(columns="key")
    out["g_skip_spy_below_vwap_and_open"] = B[~(below_vw & below_op)].drop(columns="key")
    return out, st


def main():
    H, bars, F = load()
    dates = {sp: sorted(F.date[F.date.map(lambda d: d <= "2026-08-25")]) if sp == "train"
             else sorted(F.date[F.date > "2026-08-25"]) for sp in ("train", "valid")}
    S = H[(H.setup == NAME) & (H.kind == "all")].sort_values("end").groupby(["symbol", "date"]).head(1).copy()
    S["R0"] = 0.25 * S["atr"]
    S["sig_hhmm"] = [(bars[(s, d)].index[e] + pd.Timedelta(minutes=1)).strftime("%H:%M") for s, d, e in zip(S.symbol, S.date, S.end)]
    S["sig_time"] = [bars[(s_, d)].index[e] for s_, d, e in zip(S.symbol, S.date, S.end)]
    rows = S.to_dict("records")
    legs = {}
    for name, fn in VARIANTS.items():
        L = []
        for row in rows:
            for x in fn(row, bars[(row["symbol"], row["date"])]):
                L.append({**x, "date": row["date"], "symbol": row["symbol"], "split": row["split"]})
        legs[name] = pd.DataFrame(L)
    base = legs["base"]
    bmap = {(r.symbol, r.date): r.r for r in base.itertuples()}
    for k, scope in CAPS:
        kept = cap_filter(S, k, scope)
        ks = set(zip(kept.symbol, kept.date))
        legs[f"e_cap{k}_{scope}"] = base[[(s, d) in ks for s, d in zip(base.symbol, base.date)]].copy()
    from mcf.config import load_config
    from mcf.data.store import BarStore
    spy = BarStore(load_config()["data"]["cache_dir"]).load("SPY", start="2026-07-01", end="2026-09-16")
    spy.index = spy.index.tz_convert(ET)
    spy = spy.between_time("09:30", "15:59")
    spy_days = {str(d): g for d, g in spy.groupby(spy.index.date)}
    mv, st = market_variants(S, base, spy_days)
    legs.update(mv)
    # g_flip: SPY below VWAP at the signal -> 1R/1R short instead of the long
    L = []
    for row in rows:
        b = bars[(row["symbol"], row["date"])]
        if st[(row["symbol"], row["date"])][0]:
            sg = Signal(row["symbol"], NAME, -1, int(row["end"]), stop=row["px"] + row["R0"], target=row["px"] - row["R0"])
            tr, _ = run(sg, b, row["ext"])
            if tr:
                L.append({**leg(tr, row["R0"], "flip_short"), "date": row["date"], "symbol": row["symbol"], "split": row["split"]})
        else:
            for x in v_base(row, b):
                L.append({**x, "date": row["date"], "symbol": row["symbol"], "split": row["split"]})
    legs["g_flip_short_spy_below_vwap"] = pd.DataFrame(L)
    # e2: skip EVERY signal of a bar where >= m signals fire together (a sector-wide drop, not a stock-specific dip)
    csize = S.groupby(["date", "end"]).symbol.transform("size")
    for m in (3, 4, 6):
        ks = set(zip(S.symbol[csize < m], S.date[csize < m]))
        legs[f"e2_skip_cluster_ge{m}"] = base[[(s_, d) in ks for s_, d in zip(base.symbol, base.date)]].copy()
    out = []
    for name, L in legs.items():
        for sp in ("train", "valid"):
            Ls = L[L.split == sp] if len(L) else L
            Bs = base[base.split == sp]
            nsig = int((S.split == sp).sum())
            st = stats(Ls, nsig=nsig)
            pr = paired(Ls, Bs, dates[sp]) if name != "base" else {}
            extra = {}
            if len(Ls) and "kind" in Ls:
                for kd, g in Ls.groupby("kind"):
                    extra[f"leg_{kd}"] = f"n={len(g)} exp={g.r.mean():+.3f} tot={g.r.sum():+.1f}"
            out.append({"variant": name, "split": sp, **st, **pr, **extra})
    R = pd.DataFrame(out)
    R.to_csv("research/oct7/bdi/task1_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(R[["variant", "split", "n", "days", "win", "exp", "tot", "t_day", "ex_best", "per_sig", "diff_tot", "diff_t",
             "diff_ex_best"]].to_string())
    for name, L in legs.items():
        L.to_csv(f"{D}t1_legs_{name}.csv", index=False)
    print("configs tried (task 1):", len(legs) - 1)
    if len(sys.argv) > 1:
        live(sys.argv[1], S)


def live(path, S):
    """Replay each variant on the six 2026-10-06 11:05 entries. Signal price / R0 from the live journal
    (ref = (stop + target) / 2, R0 = (target - stop) / 2); bars: 2026-10-06 only."""
    A = pd.read_csv("research/oct7/autopsy/trades_autopsy.csv")
    A = A[(A.setup == NAME) & (A.date == "2026-10-06") & (A.entry_time.str.startswith("11:05"))]
    raw = pd.read_parquet(path)
    res = []
    for r in A.itertuples():
        g = raw.loc[r.symbol].copy()
        g.index = g.index.tz_convert(ET)
        b = g[g.index.date == pd.Timestamp("2026-10-06").date()].between_time("09:30", "15:59")[["open", "high", "low", "close", "volume"]]
        end = int(b.index.searchsorted(pd.Timestamp("2026-10-06 11:04", tz=ET)))
        row = dict(symbol=r.symbol, date="2026-10-06", end=end, px=(r.stop + r.target) / 2, R0=(r.target - r.stop) / 2,
                   ext=False, score=r.heat_score)
        for name, fn in VARIANTS.items():
            L = fn(row, b)
            res.append(dict(symbol=r.symbol, variant=name, legs=len(L), r=round(sum(x["r"] for x in L), 2),
                            detail="; ".join(f"{x['kind']} {x['entry_time'][:5]}->{x['exit_time'][:5]} {x['reason']} {x['r']:+.2f}" for x in L)))
    Rl = pd.DataFrame(res)
    Rl.to_csv("research/oct7/bdi/task1_live_1006.csv", index=False)
    piv = Rl.pivot(index="variant", columns="symbol", values="r")
    six = ["GRML", "TEM", "CAI", "TWLO", "TWST", "GH"]
    symcols = list(piv.columns)
    piv["six_total"] = piv[[c for c in six if c in symcols]].sum(axis=1)
    piv["all_1105_total"] = piv[symcols].sum(axis=1)
    print(piv.round(2).to_string())
    for ix in ("SPY", "QQQ"):
        g = raw.loc[ix].copy()
        g.index = g.index.tz_convert(ET)
        g = g[g.index.date == pd.Timestamp("2026-10-06").date()].between_time("09:30", "15:59")
        bv, bo = spy_state(g, pd.Timestamp("2026-10-06 11:04", tz=ET))
        print(f"10-06 11:04 {ix}: below VWAP={bv}, below open={bo}")
    sc = A.set_index("symbol").heat_score.sort_values(ascending=False)
    print("10-06 11:05 scores:", sc.round(1).to_dict())
    for k in (1, 2, 3, 5):
        keep = list(sc.index[:k])
        print(f"cap k={k}: keeps {keep} -> base R {piv.loc['base', keep].sum():+.2f} (all {len(sc)} 11:05 entries {piv.loc['base', list(sc.index)].sum():+.2f})")


if __name__ == "__main__":
    main()
