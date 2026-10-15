"""Owner change 2026-10-15: each variant trades ONLY the highest-leveraged ETF with the most volume that day.
S&P variants (V2, V3, V5; signal SPY): candidates SPXL / UPRO, pick = larger dollar volume.
  rule "today" (PRODUCTION, the strategy class's `trade_candidates` + `pick: max_dollar_volume`):
      sum(close x volume) 09:30 .. the trigger bar, on today's tape (known at decision time)
  rule "prior" (robustness only): the prior session's full-day dollar volume
  rule "fullday" (hindsight diagnostic only, never a config): today's whole-session dollar volume
V1 (signal QQQ): TQQQ only (the only 3x long QQQ tracker).
Same pre-declared trigger x exit grid as grid.py (6 x 7). Costs in (config costs), locked block never loaded
(common.load). Dollar P/L uses the Testing-1 account sizing (MCF_ACCOUNT=testing: min(risk-based, slot notional)).
Writes pick3x_trades.csv, pick3x_results.csv, pick3x_picks.csv, pick3x_counts.json. Educational only - not financial advice."""
import json
import os

os.environ["MCF_ACCOUNT"] = "testing"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from common import EXITS, H2_START, OUT, TRIGGERS, VARIANTS, load, sample  # noqa: E402

from mcf.backtest.engine import Costs, slot_notional, simulate  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.strategies.base import DayContext, t  # noqa: E402
from mcf.strategies.index_dip import IndexDipBounce, find_trigger  # noqa: E402

cfg = load_config()
assert cfg["account_name"] == "testing"
COST = Costs.from_cfg(cfg["costs"])
FLAT = t(cfg["session"]["flatten_by"])
A = cfg["account"]
EQUITY = float(A["starting_equity"])
RISK_D = EQUITY * A["risk_per_trade_pct"] / 100
SLOT = slot_notional(A)
CPS = cfg["costs"]["commission_per_share"]
CANDS = ["SPXL", "UPRO"]
DATA = {s: load(s) for s in ["SPY", "QQQ", "TQQQ", *CANDS]}
DAYS = {s: sorted(v) for s, v in DATA.items()}
DV = {s: {d: float((b.close * b.volume).sum()) for d, b in DATA[s].items()} for s in CANDS}


def prior_dv(sym, d):
    days = DAYS[sym]
    i = days.index(d) if d in DATA[sym] else int(np.searchsorted(days, d))
    return DV[sym][days[i - 1]] if i > 0 else 0.0


def dollars(tr):
    per_share = abs(tr.entry - tr.stop)
    sh = int(min(RISK_D / per_share, SLOT / tr.entry))
    if sh < 1:
        return 0, 0.0, 0.0, 0.0
    return sh, (tr.exit - tr.entry) * sh - 2 * CPS * sh, per_share * sh, tr.entry * sh


def record(rows, v, tg, ex, rule, sym, d, tr, extra=None):
    sh, pnl, risk_usd, notional = dollars(tr)
    rows.append({"variant": v, "trigger": tg, "exit": ex, "rule": rule, "symbol": sym, "date": d, "sample": sample(d),
                 "R": tr.r_multiple, "bps": (tr.exit / tr.entry - 1) * 1e4, "reason": tr.exit_reason,
                 "entry_time": f"{tr.entry_time:%H:%M}", "entry": tr.entry, "shares": sh, "notional": notional,
                 "risk_usd": risk_usd, "pnl_usd": pnl, "meta": tr.meta, **(extra or {})})


trades, picks = [], []
for v, P in VARIANTS.items():
    ss = P["signal_symbol"]
    for tg, TP in TRIGGERS.items():
        for ex, EP in EXITS.items():
            base = dict(signal_symbol=ss, dip_pct=P["dip_pct"], dip_by=P["dip_by"], stop_buffer_frac=0.10, **TP, **EP)
            if v == "V1":
                st = IndexDipBounce(symbols=["TQQQ"], **base)
                for d, bars in DATA["TQQQ"].items():
                    ib = DATA[ss].get(d)
                    if ib is None or len(ib) < 380:
                        continue
                    for sig in st.signals(DayContext("TQQQ", d, bars, 1, 1, 1, 1, np.nan, peers={ss: ib})):
                        if (tr := simulate(sig, bars, FLAT, COST)):
                            record(trades, v, tg, ex, "tqqq", "TQQQ", d, tr)
                continue
            # rule "today": the production class, both candidates offered, at most one may signal
            st = IndexDipBounce(trade_candidates=CANDS, pick="max_dollar_volume", **base)
            single = {c: IndexDipBounce(symbols=[c], **base) for c in CANDS}
            for d, ib in DATA[ss].items():
                if len(ib) < 380 or any(d not in DATA[c] for c in CANDS):
                    continue
                peers = {ss: ib, **{c: DATA[c][d] for c in CANDS}}
                got = [s for c in CANDS for s in st.signals(DayContext(c, d, DATA[c][d], 1, 1, 1, 1, np.nan, peers=peers))]
                assert len(got) <= 1, (v, d, got)
                for sig in got:
                    if (tr := simulate(sig, DATA[sig.symbol][d], FLAT, COST)):
                        record(trades, v, tg, ex, "today", sig.symbol, d, tr)
                # rule "prior" (robustness) and "fullday" (hindsight diagnostic)
                for rule, val in (("prior", {c: prior_dv(c, d) for c in CANDS}), ("fullday", {c: DV[c][d] for c in CANDS})):
                    c = max(CANDS, key=lambda s: val[s])
                    for sig in single[c].signals(DayContext(c, d, DATA[c][d], 1, 1, 1, 1, np.nan, peers=peers)):
                        if (tr := simulate(sig, DATA[c][d], FLAT, COST)):
                            record(trades, v, tg, ex, rule, c, d, tr)
                # pick diagnostics once per variant (rec20 trigger days)
                if tg == "rec20" and ex == "TRAIL":
                    trig = find_trigger(ib, P["dip_pct"], P["dip_by"], "09:50", "10:05", "recovery", 0.20)
                    if trig:
                        today_c, dv = st.choose(DayContext(CANDS[0], d, DATA[CANDS[0]][d], 1, 1, 1, 1, np.nan,
                                                         peers=peers), trig["ts"])
                        picks.append({"variant": v, "date": d, "sample": sample(d), "trigger_bar": f"{trig['ts']:%H:%M}",
                                      **{f"dv_today_{c}": dv[c] for c in CANDS},
                                      **{f"dv_prior_{c}": prior_dv(c, d) for c in CANDS},
                                      **{f"dv_full_{c}": DV[c][d] for c in CANDS}, "pick_today": today_c,
                                      "pick_prior": max(CANDS, key=lambda s: prior_dv(s, d)),
                                      "pick_fullday": max(CANDS, key=lambda s: DV[s][d])})
T = pd.DataFrame(trades)
T.to_csv(OUT / "pick3x_trades.csv", index=False)
PK = pd.DataFrame(picks)
PK.to_csv(OUT / "pick3x_picks.csv", index=False)


def stats(r):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return dict(n=0)
    sd = r.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, mean_R=r.mean(), t=r.mean() / sd * np.sqrt(n) if n > 1 and sd > 0 else np.nan, win=(r > 0).mean(),
                mean_R_ex_best=np.delete(r, int(np.argmax(r))).mean() if n > 1 else np.nan)


rows = []
for (v, tg, ex, rule), g in T.groupby(["variant", "trigger", "exit", "rule"]):
    dev, hold = g[g["sample"] == "DEV"], g[g["sample"] == "HOLDOUT"]
    rows.append({"variant": v, "trigger": tg, "exit": ex, "rule": rule, **stats(dev.R),
                 "mean_bps": dev.bps.mean(), "mean_pnl_usd": dev.pnl_usd.mean(), "mean_risk_usd": dev.risk_usd.mean(),
                 "mean_notional": dev.notional.mean(), "picked": ",".join(f"{k}:{n}" for k, n in dev.symbol.value_counts().items()),
                 "H1_n": int((dev.date < H2_START).sum()), "H2_n": int((dev.date >= H2_START).sum()),
                 "holdout_n": len(hold), "holdout_R": hold.R.mean() if len(hold) else np.nan,
                 "holdout_pnl_usd": hold.pnl_usd.mean() if len(hold) else np.nan})
Rz = pd.DataFrame(rows)
N_new = 3 * len(TRIGGERS) * len(EXITS) * 2          # S&P x {today, prior} pick rules (fullday is hindsight, not a config)
N_rerun = len(TRIGGERS) * len(EXITS)                  # V1 TQQQ: identical to grid.py rows (already counted)
prev = json.load(open(OUT / "counts.json"))
lin = prev["N_lineage"] + N_new
Rz["bar_t"] = max(1.5, np.sqrt(2 * np.log(lin)))
Rz.round(4).to_csv(OUT / "pick3x_results.csv", index=False)
json.dump({"N_new_configs": N_new, "N_rerun_identical": N_rerun, "N_lineage": lin,
           "bar_t_lineage": max(1.5, np.sqrt(2 * np.log(lin))), "sizing": {"equity": EQUITY, "risk_usd": RISK_D,
                                                                           "slot_notional": SLOT}},
          open(OUT / "pick3x_counts.json", "w"), indent=1)
print("trades", len(T), "rows", len(Rz), "new configs", N_new, "lineage", lin)
