"""REPV step 2: rep POTENTIAL per setup - every setup of interest replayed together on Primary's full universe with NO
account caps (as-live engine mcf.report.team -> mcf.replay.harness.run_session, fills=costs, limit_fill=through).

Caps removed: slots / per-setup cap / lot cap / twin block / per-setup -2R latch / account halt / cost filter / split-tape
gate / trades-per-day. Kept (structural): Primary universe minus earnings blackout and PTP, the 09:50 no-entry rule,
easy-to-borrow for shorts, the quote/spread realism checks (synthetic quotes from journaled spreads, so spread skips are
rarer than live), the setup's own window and gates. Signals that clash with ANOTHER setup on the same symbol
(opposite side held) are counted as potential entries, because each setup would take them in its own account.

Post-hoc flags per signal: in Testing A's top-500 pool (UNI1 rule, from that day's priors); stop-exit cost in R (the CF
0.15R filter). Sizing is Primary's ($77-slot notional) and never limits a signal count.

    MCF_TEAM_CACHE=/home/user/MCF/data/team MCF_REPLAY_STORE=/home/user/MCF/data/replay \
        python research/repv/potential.py --days 2026-11-04,2026-11-05 --jobs 4

Cached data only (bars / priors already in data/team); no Alpaca calls if the cache covers the session.
Writes research/repv/potential/<day>.csv (one row per journaled signal). Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "potential"
ACCTS = ("testing", "testing2", "explore1", "livelab", "gen", "graveyard")


def setup_set(gen_top: list[str]) -> dict[str, str]:
    """setup -> home account: every enabled setup in On Deck / Testing A / B / C (config in this checkout) + Gen picks."""
    out = {}
    for a in ("testing", "testing2", "explore1", "livelab"):
        cfg = yaml.safe_load((ROOT / "config" / f"account_{a}.yaml").read_text())
        for k, v in (cfg.get("strategies") or {}).items():
            if isinstance(v, dict) and v.get("enabled", True) is not False and not k.startswith("GEN-"):
                out.setdefault(k, a)
    for g in gen_top:
        out[g] = "gen"
    return out


def nocap(cfg: dict) -> dict:
    a = cfg["account"]
    a.update(max_concurrent_positions=10**6, max_positions_per_strategy=10**6, max_daily_loss_r=10**9,
             max_setup_daily_loss_r=None, max_trades_per_day=10**7)
    lv = cfg.setdefault("live", {})
    lv.update(max_lots_per_symbol=10**4, block_twin_same_symbol=False, max_stop_cost_r=None,
              split_tape_short_gate={"enabled": False, "spread_pct": 0.5}, retry_after_release=True)
    return cfg


MASK_FAIL: dict = {}


def _guard_masks():
    """Runtime guard for this research run only (no repo code changed): a lab module whose vectorised mask() raises on
    a symbol (seen: LD1 breadth shift on a 1-row frame) yields no signal on that symbol instead of ending the session.
    Failures are counted per setup and written to <day>.json."""
    import numpy as np
    from mcf.replay import fast

    if getattr(fast.FastSession.full_mask, "_repv", False):
        return
    orig = fast.FastSession.full_mask

    def full_mask(self, name, sym):
        try:
            return orig(self, name, sym)
        except Exception as e:  # noqa: BLE001
            MASK_FAIL[name] = MASK_FAIL.get(name, 0) + 1
            f = self.frame(sym)
            self.masks[(name, sym)] = np.zeros(len(f) if f is not None else 0, dtype=bool)
            return self.masks[(name, sym)]

    full_mask._repv = True
    fast.FastSession.full_mask = full_mask


def run_day(args):
    day, setups = args
    _guard_masks()
    MASK_FAIL.clear()
    from mcf.data.universe import top_n_symbols
    from mcf.report import team as T

    f = OUT / f"{day}.csv"
    if f.exists():
        return str(f)
    t0 = time.time()
    picks = {"setups": [{"id": s, "account": a} for s, a in setups.items()]}
    cfg = nocap(T.team_config(picks, day))
    uni, unote = T.primary_universe(day)
    syms, notes = T.team_symbols(cfg, uni, day)
    exact = sorted({s for st in cfg["strategies"].values() for s in (st.get("symbols") or [])
                    if isinstance(st.get("symbols"), list)})
    pri = T.get_priors(syms, day, exact, log=lambda *a: None)
    bars = T.get_bars(syms, day, None, log=lambda *a: None)
    shortable = {str(s): (bool(x), bool(y)) for s, x, y in zip(uni.symbol, uni.shortable, uni.easy_to_borrow)}
    ss = set(syms)
    sim = T.simulate(cfg, day, {s: b for s, b in bars.items() if s in ss}, {s: p for s, p in pri.items() if s in ss},
                     None, shortable, T.get_spreads(), log=lambda *a: None)
    sig = sim["signals"].copy() if len(sim["signals"]) else pd.DataFrame()
    rows = ((s, p.adv, (p.atr / p.prev_close * 100) if p.prev_close else float("nan")) for s, p in pri.items() if s in ss)
    pool = top_n_symbols(rows, {"top_n": 500, "top_n_min_adv": 95_000_000}) or set()
    if len(sig):
        sig["in_top500"] = sig.symbol.isin(pool)
        px = sig.ref_price.astype(float)
        risk = (px - sig.stop.astype(float)).abs()
        one = 0.01 + px * 1.0 / 1e4
        sig["stop_cost_r"] = ((2 * one + 0.02) / risk.where(risk > 0)).round(3)
        sig["home"] = sig.strategy.map(setups)
        sig["day"] = day
        keep = [c for c in ("day", "ts", "symbol", "strategy", "home", "side", "ref_price", "stop", "status", "reason",
                            "in_top500", "stop_cost_r") if c in sig.columns]
        sig = sig[keep]
    tr = pd.DataFrame(sim["trades"])
    OUT.mkdir(parents=True, exist_ok=True)
    sig.to_csv(f, index=False)
    if len(tr):
        tr.to_csv(OUT / f"{day}_trades.csv", index=False)
    (OUT / f"{day}.json").write_text(json.dumps({"day": day, "universe": unote, "notes": notes, "symbols": len(ss),
                                                  "setups": len(setups), "seconds": round(time.time() - t0),
                                                  "mask_failures": MASK_FAIL}, default=str))
    return str(f)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", required=True)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--gen", default=str(Path(__file__).resolve().parent / "gen_top.txt"))
    a = ap.parse_args(argv)
    gen = [x.strip() for x in Path(a.gen).read_text().split() if x.strip()] if Path(a.gen).exists() else []
    setups = setup_set(gen)
    print(f"{len(setups)} setups ({len(gen)} GEN)", flush=True)
    items = [(d, setups) for d in a.days.split(",")]
    if a.jobs > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(min(a.jobs, 4)) as p:
            for r in p.imap_unordered(run_day, items):
                print("done", r, flush=True)
    else:
        for i in items:
            print("done", run_day(i), flush=True)


if __name__ == "__main__":
    main()
