"""PREVAL 1107 step C: replay three Primary books through the as-live replay engine (the Team's method,
mcf/report/team.py -> mcf.replay.harness.run_session, fills=costs, limit_fill=through) under Primary's rules
(config/default.yaml: 0.25% risk, -2R per-setup latch, -20R halt, slots / buying power), on Primary's universe of each session.
Usage: MCF_TEAM_CACHE=... python replay.py <book> <outdir> <date> [<date> ...]   (book = asis | opt1 | opt2)
Writes <outdir>/<book>_<date>.json with the simulated trades. Read-only Alpaca market data (cached). Simulated fills.
Educational only - not financial advice."""
import sys, json, time, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from mcf.report import team as T

P = lambda s: {"id": s, "account": "primary"}
ASIS = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell",
        "MF4-h40-open-flowsell-FD", "NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long",
        "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]
BOOKS = {
    "asis": [P(s) for s in ASIS],
    "opt1": [P(s) for s in ASIS if s not in ("MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD")],
    "opt2": [P("RW3-gapdn-rsi5pop-flowsell-short-FD"), P("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"),
             P("ST7-rsi50dn-long-pm-t1s1-FD"), P("NS5-sma50-flush-oversold-long"),
             {"id": "CWT09-gapdn-vwaploss-g10-short", "account": "livelab"},
             {"id": "NM-ETF-late-dip-di-long", "account": "livelab"}],
}
# after the first replay round (asis / opt1 / opt2): MF4 base reactivates when MF4-FD leaves (twin), and CWT09-g10 lost in
# Primary's wider universe while L3-fromopen-FD carried burst days -> revised minimal (opt1b) and full book (opt2b)
BOOKS["opt1b"] = [s for s in BOOKS["opt1"] if s["id"] != "MF4-h40-open-flowsell"]
BOOKS["opt2b"] = [s for s in BOOKS["opt2"] if s["id"] != "CWT09-gapdn-vwaploss-g10-short"] + [P("L3-gap-slope-fromopen-FD")]
CACHE = Path(os.environ.get("MCF_TEAM_CACHE", ROOT / "data" / "team"))
book, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
picks = {"setups": BOOKS[book]}
spreads = T.get_spreads()
for d in sys.argv[3:]:
    f = out / f"{book}_{d}.json"
    if f.exists():
        continue
    while not (CACHE / "1Min" / f"{d}.json").exists():
        time.sleep(30)
    t0 = time.time()
    cfg = T.team_config(picks, d)
    uni, unote = T.primary_universe(d)
    syms, notes = T.team_symbols(cfg, uni, d)
    exact = sorted({s for st in cfg["strategies"].values() for s in (st.get("symbols") or []) if isinstance(st.get("symbols"), list)})
    pri = T.get_priors(syms, d, exact, log=lambda *a: None)
    bars = T.get_bars(syms, d, None, log=lambda *a: None)
    shortable = {str(s): (bool(a), bool(b)) for s, a, b in zip(uni.symbol, uni.shortable, uni.easy_to_borrow)}
    sim = T.simulate(cfg, d, bars, {s: p for s, p in pri.items() if s in set(syms)}, None, shortable, spreads, log=lambda *a: None)
    sig = sim["signals"]
    rep = {"book": book, "date": d, "setups": [s["id"] for s in picks["setups"]], "sources": cfg.get("_team_sources"),
           "order": cfg["live"]["setup_order"], "universe": unote, "symbols": notes.get("symbols"),
           "seconds": round(time.time() - t0), "stats": {k: v for k, v in (sim["stats"] or {}).items() if isinstance(v, (int, float, str))},
           "trades": sim["trades"],
           "signals_by_status": (sig.groupby(["strategy", "status"]).size().reset_index().values.tolist()
                                 if hasattr(sig, "groupby") and len(sig) and "status" in sig else [])}
    f.write_text(json.dumps(rep, default=str))
    print(book, d, len(sim["trades"]), round(sum(t["r"] for t in sim["trades"] if t["r"] == t["r"]), 2), rep["seconds"], "s", flush=True)
