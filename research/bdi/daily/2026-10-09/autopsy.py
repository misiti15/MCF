"""BDI per-trade autopsy, primary + Testing accounts, 2026-10-09 (diagnosis only, NOT evidence: one live paper day).

Inputs: the day's trade export (journal rows), a read-only copy of the mcf-data journal (signal layers), and SIP
1-minute bars fetched read-only for the traded symbols (2026-08-10 .. 2026-10-09) into data/cache/bdi1009/ (git-ignored; fetch.py).
Rule values are recomputed the way LabStrategy/HeatStrategy saw them live: the last 40 prior-day 5-minute bars plus
today's COMPLETE 5-minute bars up to the signal; daily ATR(14) from prior days (heat_frame atr_d).
Method follows research/oct7/autopsy/autopsy.py + classify.py (same what-ifs, costs and loss-type precedence) so the
days are comparable; adds hold-to-15:55, no-stop close, stop-and-reverse, re-entry and counter-signal flags.

usage: python research/bdi/daily/2026-10-09/autopsy.py  (reads data/bdi1009/{primary,testing}.csv, journal_{primary,testing}.db,
setups_{primary,testing}.json: `git show origin/mcf-data:reports/2026-10-09.csv > data/bdi1009/primary.csv`, likewise
journal.db / setups/2026-10-09.json, and origin/mcf-data-testing for 'testing'; then fetch.py and news.py)
Adds per trade: market context at entry (universe breadth from the open, SPY from the open: the regime1009 gate G1/G3).
Educational only - not financial advice.
"""
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import extra_features  # noqa: E402

OUT = Path(__file__).resolve().parent
BARS_DIR = ROOT / "data" / "cache" / "bdi1009"
IN = ROOT / "data" / "bdi1009"
DAY = "2026-10-09"
ET = "America/New_York"
SLIP_BPS, SLIP_PS, STOP_PS = 1.0, 0.01, 0.02          # config/default.yaml production costs

NEWS = {}   # filled from data/cache/bdi1009/news.json (news.py): material headlines before/during the trade


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location("m_" + name.replace("-", "_").replace("+", "_"), ROOT / path)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((ROOT / path).parent))
    spec.loader.exec_module(m)
    return m


def bars(sym):
    g = pd.read_parquet(BARS_DIR / f"{sym}.parquet")
    g.index = g.index.tz_convert(ET)
    return g.between_time("09:30", "15:59")[["open", "high", "low", "close", "volume"]]


def cost_r(entry, R, stop_exit):
    return (2 * (entry * SLIP_BPS / 1e4 + SLIP_PS) + (STOP_PS if stop_exit else 0)) / R


def walk(path, side, entry, R, stop_r=1.0, tgt_r=None, be_at=None, trail=None, trail_after=None):
    """1-minute walk, stop first inside a bar, gaps through the stop fill at the open. -> (r_gross, why, i_exit)."""
    stop = entry - side * stop_r * R
    tgt = None if tgt_r is None else entry + side * tgt_r * R
    best = entry
    for i, (o, h, l, c) in enumerate(path[["open", "high", "low", "close"]].to_numpy()):
        adv = l if side == 1 else h
        if (adv - stop) * side <= 0:
            px = o if (o - stop) * side <= 0 else stop
            return side * (px - entry) / R, "stop", i
        fav = h if side == 1 else l
        if tgt is not None and (fav - tgt) * side >= 0:
            return side * (tgt - entry) / R, "target", i
        if side * (fav - best) > 0:
            best = fav
        mfe = side * (best - entry) / R
        if be_at is not None and mfe >= be_at:
            stop = max(stop, entry) if side == 1 else min(stop, entry)
        if trail is not None and mfe >= (trail_after or 0):
            ts = best - side * trail * R
            stop = max(stop, ts) if side == 1 else min(stop, ts)
    if not len(path):
        return 0.0, "none", -1
    return side * (path["close"].iloc[-1] - entry) / R, "time", len(path) - 1


def net(res, entry, R):
    r, why, i = res
    return r - cost_r(entry, R, why == "stop"), why, i


def excursions(path, side, entry, R):
    if path.empty:
        return dict(mfe_r=np.nan, mae_r=np.nan, t_mfe_min=np.nan, t_mae_min=np.nan)
    f = side * ((path["high"] if side == 1 else path["low"]) - entry)
    a = side * ((path["low"] if side == 1 else path["high"]) - entry)
    return dict(mfe_r=f.max() / R, mae_r=a.min() / R, t_mfe_min=int(np.argmax(f.to_numpy())) + 1,
                t_mae_min=int(np.argmin(a.to_numpy())) + 1)


def frame_at(sym, sig_t, B):
    """Live-equivalent lab frame at the signal: 40 prior 5-min bars + today's complete 5-min bars before sig_t."""
    day = B[B.index.date == pd.Timestamp(DAY).date()]
    prior = B[B.index.date < pd.Timestamp(DAY).date()]
    d5p_all = resample(prior, "5min")
    full = heat_frame(pd.concat([d5p_all, resample(day, "5min")]))          # for atr_d only (prior-day ATR(14))
    atr = float(full["atr_d"].iloc[-1])
    cut = sig_t.floor("min")
    d5 = resample(day[day.index < cut], "5min")
    d5 = d5[d5.index + pd.Timedelta(minutes=5) <= cut]
    hist = pd.concat([d5p_all.iloc[-40:], d5])
    f = heat_frame(hist)
    f["atr_d"] = atr
    f = f.join(extra_features(hist, f)).iloc[-len(d5):].copy()
    pday = prior[prior.index.date == prior.index.date[-1]]
    f["gap"] = (float(d5["open"].iloc[0]) / float(pday["close"].iloc[-1]) - 1) * 100
    f["dist_pdh_atr"] = (float(pday["high"].max()) - f["close"]) / atr
    f["dist_pdl_atr"] = (f["close"] - float(pday["low"].min())) / atr
    return f, atr


def breadth():
    """Universe breadth from the open per minute on DAY (lab symbols, data/cache/bdi1009/universe_1009.parquet)."""
    U = pd.read_parquet(BARS_DIR / "universe_1009.parquet")
    U.index = U.index.tz_convert(ET)
    U = U[U.index.date == pd.Timestamp(DAY).date()].between_time("09:30", "15:59")
    op = U.groupby("symbol")["open"].transform("first")
    U = U.assign(up=(U["close"] > op).astype(float))
    # last close per symbol up to each minute: pivot then ffill
    P = U.pivot_table(index=U.index, columns="symbol", values="close").ffill()
    O = U.groupby("symbol")["open"].first()
    return (P > O.reindex(P.columns).to_numpy()).mean(axis=1)


def main():
    BR = breadth()
    BR.to_frame("brd").to_csv(OUT / "breadth_1009.csv")
    allrows = []
    for acct in ("primary", "testing"):
        allrows.append(run(acct, BR))
    A = pd.concat(allrows, ignore_index=True)
    classify(A)


def run(acct, BR):
    T = pd.read_csv(IN / f"{acct}.csv")
    con = sqlite3.connect(IN / f"journal_{acct}.db")
    S = pd.read_sql("select * from signals where day=?", con, params=(DAY,))
    SET = json.load(open(IN / f"setups_{acct}.json"))["strategies"]
    for c in ("signal_time", "entry_time", "exit_time"):
        T[c] = pd.to_datetime(T[c], format="ISO8601").dt.tz_convert(ET)
    T["artifact"] = T.exit_reason.eq("flatten") & ((T.exit_time - T.entry_time).dt.total_seconds() < 60)
    mods = {}
    for k in set(T.strategy):
        c = SET.get(k, {})
        p = c.get("module") or c.get("formula")
        if p:
            mods[k] = load_mod(k, p)
    news = json.load(open(BARS_DIR / "news.json")) if (BARS_DIR / "news.json").exists() else {}
    spy = bars("SPY")
    spy_d = spy[spy.index.date == pd.Timestamp(DAY).date()]
    rows = []
    for _, tr in T.sort_values("id").iterrows():
        sym, side, setup = tr.symbol, int(tr.side), tr.strategy
        B = bars(sym)
        day = B[B.index.date == pd.Timestamp(DAY).date()]
        entry, stop = float(tr.entry), float(tr.stop)
        R = abs(entry - stop)
        after = day[day.index > tr.entry_time.floor("min")]
        to55 = after[after.index <= pd.Timestamp(f"{DAY} 15:54", tz=ET)]
        ex_t = min(tr.exit_time, pd.Timestamp(f"{DAY} 15:55", tz=ET))
        held = after[after.index < ex_t.floor("min") + pd.Timedelta(minutes=1)]
        tgt_r = side * (float(tr.target) - entry) / R
        row = dict(account=acct, id=int(tr.id), symbol=sym, setup=setup, side=side, artifact=bool(tr.artifact),
                   signal_time=str(tr.signal_time.time())[:8], entry_time=str(tr.entry_time.time())[:8],
                   exit_time=str(tr.exit_time.time())[:8], exit_reason=tr.exit_reason, entry=entry, stop=stop,
                   target=float(tr.target), R=R, R_pct=R / entry * 100, R_atr=np.nan, tgt_r_live=tgt_r,
                   r_live=float(tr.r_multiple), pnl=float(tr.pnl), pnl_adj=float(tr.pnl_adj), shares=int(tr.shares),
                   slip_bps=float(tr.slip_bps))
        exc, rest = excursions(held, side, entry, R), excursions(to55, side, entry, R)
        row.update({f"held_{k}": v for k, v in exc.items()})
        row.update({f"day_{k}": v for k, v in rest.items()})
        row["close_1555"] = float(to55["close"].iloc[-1]) if len(to55) else np.nan
        row["r_hold_nostop_1555"] = side * (row["close_1555"] - entry) / R - cost_r(entry, R, False)
        # ---- what-ifs on the same entry (net of production costs)
        wi = {"base_sim": dict(tgt_r=tgt_r), "be0.5": dict(tgt_r=tgt_r, be_at=0.5),
              "trail0.5": dict(trail=0.5, trail_after=0.5), "tp0.5": dict(tgt_r=0.5), "tp1": dict(tgt_r=1.0),
              "hold_1555": dict()}
        for k, kw in wi.items():
            r, why, _ = net(walk(to55, side, entry, R, **kw), entry, R)
            row[f"wi_{k}"], row[f"wi_{k}_why"] = r, why
        # stop-and-reverse: if the live-geometry trade stops, reverse at the stop with the same R, 1R/1R, to 15:55
        r0, why0, i0 = net(walk(to55, side, entry, R, tgt_r=tgt_r), entry, R)
        sar = r0
        if why0 == "stop":
            rest_p = to55.iloc[i0 + 1:]
            px = entry - side * R
            sar += net(walk(rest_p, -side, px, R, tgt_r=1.0), px, R)[0]
        row["wi_stop_and_reverse"] = sar
        # re-entry: after a stop, re-enter the same side at the close of the first later 5-min bar that closes back
        # through the original entry (the move resumed), same R, 1R/1R, to 15:55
        reent = r0
        if why0 == "stop":
            rest_p = to55.iloc[i0 + 1:]
            c5 = resample(rest_p, "5min") if len(rest_p) else rest_p
            hit = c5[side * (entry - c5["close"]) > 0] if len(c5) else c5   # short: close back below entry
            if len(hit):
                t5 = hit.index[0] + pd.Timedelta(minutes=5)
                px = float(hit["close"].iloc[0])
                reent += net(walk(rest_p[rest_p.index >= t5], side, px, R, tgt_r=1.0), px, R)[0]
                row["reentry_time"] = str(t5.time())[:5]
        row["wi_reentry"] = reent
        # opposite side, same entry and R, 1R/1R
        r, why, _ = net(walk(to55, -side, entry, R, tgt_r=1.0), entry, R)
        row["opp_1r1r"], row["opp_why"] = r, why
        row["opp_hold_1555"] = -side * (row["close_1555"] - entry) / R
        # ---- rule values at the signal (live-equivalent recomputation) + counter-signal flags
        try:
            f, atr = frame_at(sym, tr.signal_time, B)
            x = f.iloc[-1]
            row["R_atr"] = R / atr
            row["atr_d"] = atr
            for k in ("tod", "gap", "fromOpen", "vwapDistPct", "rsi", "rsi5", "heat", "buyPressure", "sma20_dist_pct",
                      "sma50_dist_pct", "sma20_slope_pct", "bear_div", "volumeRatio", "dist_hod_atr", "dist_lod_atr",
                      "flow3"):
                row[f"f_{k}"] = float(x[k])
            if setup in mods:
                m = mods[setup]
                if hasattr(m, "mask"):
                    row["mask_recomputed"] = bool(np.asarray(m.mask(f), bool)[-1])
                else:
                    s = np.asarray(m.score(f), float)
                    row["f_score"] = float(s[-1])
                    row["mask_recomputed"] = bool(s[-1] >= m.LONG_AT) if m.LONG_AT is not None else bool(s[-1] <= m.SHORT_AT)
            # day move into the entry, 60-minute move into the entry (in daily ATRs)
            o = float(day["open"].iloc[0])
            pre = day[day.index < tr.entry_time.floor("min")]
            row["move_open_to_entry_pct"] = (entry / o - 1) * 100
            row["chase_pct"] = side * row["move_open_to_entry_pct"]
            p60 = pre[pre.index >= tr.entry_time.floor("min") - pd.Timedelta(minutes=60)]
            row["move_60m_atr"] = side * (float(pre["close"].iloc[-1]) - float(p60["open"].iloc[0])) / atr
            sp = spy_d[spy_d.index < tr.entry_time.floor("min")]
            sp30 = sp[sp.index >= tr.entry_time.floor("min") - pd.Timedelta(minutes=30)]
            row["spy_fromopen_pct"] = (float(sp["close"].iloc[-1]) / float(spy_d["open"].iloc[0]) - 1) * 100
            row["spy_30m_pct"] = (float(sp["close"].iloc[-1]) / float(sp30["open"].iloc[0]) - 1) * 100
            row["flag_spy30_against"] = side * row["spy_30m_pct"] < -0.05            # market moving against the trade
            row["flag_trend_against"] = side * row["f_sma20_slope_pct"] < 0          # 5-min SMA20 sloping against
            row["flag_fromopen_against"] = side * row["f_fromOpen"] < 0              # fading the day's direction
            row["flag_flow3_against"] = side * row["f_flow3"] < -0.3                 # last 15 min of flow against
            # regime1009 market context at the signal bar close (last complete minute before the signal)
            bk = BR[BR.index < tr.signal_time.floor("min")]
            row["ctx_brd_fo"] = float(bk.iloc[-1]) if len(bk) else np.nan
            row["ctx_g1_allows"] = bool((side == 1 and row["ctx_brd_fo"] > 0.5) or (side == -1 and row["ctx_brd_fo"] < 0.5))
            row["ctx_g3_allows"] = bool(side * row["spy_fromopen_pct"] > 0)
        except Exception as e:  # noqa: BLE001
            row["feature_error"] = repr(e)[:120]
        sig = S[(S.symbol == sym) & (S.strategy == setup) & (S.status == "submitted")]
        row["layers"] = json.loads(sig["info"].iloc[0]).get("layers", "") if len(sig) else ""
        hl = [h for h in news.get(sym, []) if h["t"] <= str(tr.exit_time)[:19]]
        row["news_all"] = " | ".join(f"{h['t'][11:16]} {h['headline'][:90]}" for h in hl)
        row["news"] = " | ".join(f"{h['t'][11:16]} {h['headline'][:90]}" for h in hl if h["material"])
        rows.append(row)
    return pd.DataFrame(rows)


def classify(A):

    # ---- loss types: research/oct7/autopsy/classify.py precedence (comparable across days)
    real = ~A.artifact
    loss = real & (A.r_live <= 0)
    tags = pd.DataFrame(index=A.index)
    tags["news_earnings"] = loss & A.news.ne("")
    tags["stopped_then_reversed"] = loss & A.exit_reason.eq("stop") & (A.day_mfe_r >= 1.0) & (A.held_mfe_r < 1.0)
    tags["wrong_side_after_big_swing"] = loss & (A.chase_pct.abs() >= 3) & A.opp_why.eq("target")
    tags["gave_back_gains"] = loss & (A.held_mfe_r >= 0.5)
    tags["late_hold"] = loss & A.exit_reason.eq("flatten")
    tags["never_worked"] = loss & (A.held_mfe_r < 0.15)
    order = list(tags.columns)
    A["loss_type"] = np.where(A.artifact, "artifact (stacking bug)", np.where(~loss, "win", "small MFE then failed (0.15-0.5R)"))
    for c in reversed(order):
        A.loc[tags[c], "loss_type"] = c
    A["tags"] = tags.apply(lambda r: ",".join(c for c in tags.columns if r[c]), axis=1)
    A.round(4).to_csv(OUT / "trades.csv", index=False)
    pd.set_option("display.width", 250)
    R_ = A[real]
    print(R_[["account", "id", "symbol", "setup", "entry_time", "exit_time", "exit_reason", "r_live", "R_atr", "held_mfe_r", "held_mae_r",
              "held_t_mfe_min", "day_mfe_r", "day_t_mfe_min", "wi_be0.5", "wi_trail0.5", "wi_tp0.5", "wi_tp1", "wi_hold_1555",
              "wi_stop_and_reverse", "wi_reentry", "opp_1r1r", "loss_type"]].round(2).to_string())
    for a, g in R_.groupby("account"):
        print(a)
        print(pd.crosstab(g.loss_type, g.setup, margins=True).to_string())


if __name__ == "__main__":
    main()
