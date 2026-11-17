"""Workbench blueprint (owner project WORKBENCH, 2026-11-13): put one live setup "on the Workbench" and draw every part it
is built from, one labelled block per component, like a machine blueprint.

    python -m mcf.report.blueprint L3-gap-slope-fromopen-FD [--style engine|blocks] [--trades worst2|best1|id:<n>]
                                   [--out DIR] [--no-record] [--no-png]

Workbench v2 (owner 2026-11-15): the default style draws the setup as an engine (mcf/report/engine.py) and pairs it with
a teardown PNG per picked live trade whose callouts cite the engine's part numbers; `--style blocks` keeps the v1 sheet.

Reads (never writes) the setup's config block (config/default.yaml + the account overlay, exactly as the live runner
loads it, mcf/config.py), its lab module (top-level constants + the comparisons inside mask(), parsed with `ast`; for
Setup Generator setups also the CONDS / gen spec and the id's name tokens) and, unless --no-record, its live record from
every account journal (git show origin/<data branch>:journal.db, run_id = 1, R = pnl_adj / (|entry - stop| x shares)).
Writes <out>/<setup>_engine.png + <out>/<setup>_trade<k>_<sym>_<date>.png (matplotlib) or, --style blocks,\n<out>/<setup>.png (headless Chromium), plus <out>/<setup>.md. Default out: reports/workbench/<setup>/.

OBSERVATION ONLY: nothing here changes a setup. Teardown variants are made with `python -m mcf.research.workbench spawn`
(a brand-new research-only setup; the original is never edited). Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import os
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = "Educational only — not financial advice"
SECTIONS = ("WHICH STOCKS", "WHEN", "ENTRY TRIGGER", "RISK & EXIT", "LIMITS", "ACCOUNT & SIZING", "RECORD")
GEOM_WORDS = {"t1s1": "target +1R / stop 1R", "t05s1": "target +0.5R / stop 1R", "t1s05": "target +1R / stop 0.5R",
              "t05s05": "target +0.5R / stop 0.5R", "hold": "stop 1R, no target, flat at the close",
              "holdtr": "stop 1R, no target, 1R trailing stop once +1R", "S": "structural stop (module stop_price), no fixed target"}
GEOM_RS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5), "t05s05": (0.5, 0.5), "hold": (None, 1.0),
           "holdtr": (None, 1.0)}
OPS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}
FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "==", "!=": "!="}
# frame columns the indicator library does not describe
EXTRA_LABELS = {"tod": "bar close time (HHMM ET)", "atr_d": "daily ATR(14) $", "close": "last price",
                "spy_fo": "SPY's move since its open (%)", "qqq_fo": "QQQ's move since its open (%)",
                "breadth": "share of stocks above their VWAP", "breadth_open": "share of stocks above their open",
                "qqq_vwap": "QQQ vs its VWAP"}
STRUCT_CONSTS = {"SIDE", "GEOM", "LAYERS", "CONDS", "TRIGGER", "FILTERS", "WINDOW", "MIN_ADV", "CONTEXT", "SYMBOLS",
                 "GENERIC"}
# old and new display names per account key (ledger titles use both)
ACCOUNT_ALIASES = {"primary": ["Primary"], "testing": ["Testing 1", "On Deck"], "testing2": ["Testing 2", "Testing A"],
                   "gen": ["Setup Generator", "Gen:"], "graveyard": ["Graveyard"], "explore1": ["Explore 1", "Testing B"],
                   "livelab": ["Live Lab", "Testing C"], "testingd": ["Testing D"], "testinge": ["Testing E"],
                   "testingf": ["Testing F"]}
# ST-style (research/bdi/stack1009) trigger families and filters in words
TRIG_WORDS = {"rsi50": "RSI(14) crosses {d} 50", "rsi14": "RSI(14) crosses {d} {p}", "rsi5": "RSI(5) crosses {d} {p}",
              "vwap": "price crosses {d} VWAP", "ema": "EMA9 crosses {d} EMA21", "macd": "MACD crosses {d} zero",
              "or": "breaks the 09:30-10:00 opening range {d}", "sma50": "crosses {d} the 5-min SMA50",
              "sma20": "crosses {d} the 5-min SMA20", "pdbrk": "breaks the prior-day {hl}", "pdfail": "fails back through the prior-day {hl}",
              "hodlod": "makes a new {hodlod}", "volspike": "volume spike (2x) {d}", "fo3": "move from open crosses {d} 3%",
              "slope20": "SMA20 slope turns {d}", "flow3": "3-bar flow crosses {d} 0.5", "band05": "VWAP band ±{p} ATR crossed {d}",
              "band10": "VWAP band ±{p} ATR crossed {d}"}


# ------------------------------------------------------------------------------------------------ config lookup
def account_names() -> dict[str, str]:
    from .assignments import ACCOUNTS

    return dict(ACCOUNTS)


def data_branches() -> dict[str, str]:
    from .daily_post import ACCOUNTS

    return {k: br for k, _, br, _ in ACCOUNTS}


def _load(acct: str) -> dict:
    from ..config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    os.environ["MCF_ACCOUNT"] = acct
    try:
        return load_config()
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old


def find_setup(setup_id: str) -> dict:
    """{account, accounts (enabled in), block, cfg} - the account where the setup runs now (first enabled one), else the
    first account whose config holds a block for it (then accounts = [])."""
    enabled, first = [], None
    cfgs = {}
    for a in account_names():
        cfg = _load(a)
        blk = (cfg.get("strategies") or {}).get(setup_id)
        if not isinstance(blk, dict):
            continue
        cfgs[a] = cfg
        if blk.get("enabled"):
            enabled.append(a)
        elif first is None and (blk.get("module") or blk.get("type")):
            first = a
    if not enabled and first is None:
        raise KeyError(f"{setup_id}: no setup block in any account config")
    acct = enabled[0] if enabled else first
    return dict(account=acct, accounts=enabled, block=dict(cfgs[acct]["strategies"][setup_id]), cfg=cfgs[acct])


# ------------------------------------------------------------------------------------------------ module parsing
def col_label(name: str) -> str:
    from ..research.arena.indicators import INDICATORS

    base = name.strip("|")
    if base in EXTRA_LABELS:
        d = EXTRA_LABELS[base]
    elif base in INDICATORS:
        d = INDICATORS[base].desc.replace(" (frame column)", "")
    else:
        return name
    return f"|{d}|" if name.startswith("|") else d


def _num(node, consts: dict):
    """(value, const_name or None) for a numeric literal / -literal / module constant, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value), None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        r = _num(node.operand, consts)
        return (-r[0], r[1]) if r and r[1] is None else None
    if isinstance(node, ast.Name) and isinstance(consts.get(node.id), (int, float)) and not isinstance(consts.get(node.id), bool):
        return float(consts[node.id]), node.id
    return None


def _colref(node) -> str | None:
    """Frame column a mask expression reads: c('x') / col('x') / df['x'] (optionally .to_numpy(...), np.abs(...))."""
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id in ("c", "col") and node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            return node.args[0].value
        if isinstance(f, ast.Attribute) and f.attr in ("abs", "fabs") and node.args:
            inner = _colref(node.args[0])
            return f"|{inner}|" if inner else None
        if isinstance(f, ast.Attribute):          # df['x'].to_numpy(...), .astype(...)
            return _colref(f.value)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "df":
        s = node.slice
        if isinstance(s, ast.Constant) and isinstance(s.value, str):
            return s.value
    if isinstance(node, ast.Attribute) and node.attr in ("values",):
        return _colref(node.value)
    return None


def _span(node) -> list[int]:
    return [node.lineno, node.col_offset, node.end_lineno, node.end_col_offset]


def parse_module(path: str | Path) -> dict:
    """Constants, entry conditions (with source spans for the workbench spawner), time clauses and unparsed comparisons
    of a lab module. Conditions: CONDS (Setup Generator / arena) > TRIGGER + FILTERS (stack modules) > mask() comparisons."""
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    src = p.read_text()
    tree = ast.parse(src)
    consts, const_nodes = {}, {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            nm = node.targets[0].id
            try:
                consts[nm] = ast.literal_eval(node.value)
                const_nodes[nm] = node.value
            except Exception:
                pass
    doc = ast.get_docstring(tree) or ""
    out = dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), doc=doc.split("\n")[0], consts=consts,
               conds=[], time=[], unparsed=[], style="mask", layers=[x for x in consts.get("LAYERS") or [] if isinstance(x, str)])
    conds = out["conds"]
    if isinstance(consts.get("CONDS"), (list, tuple)) and consts["CONDS"]:
        out["style"] = "conds"
        for el in const_nodes["CONDS"].elts:
            n, op, v = ast.literal_eval(el)
            conds.append(dict(col=n, op=op, value=v, label=col_label(n), span=_span(el.elts[2]), source="CONDS"))
        return _keys(out)
    if consts.get("TRIGGER") is not None or consts.get("FILTERS"):
        out["style"] = "stack"
        lay = [x for x in out["layers"] if not x.lower().startswith(("full day", "window"))]
        tr = consts.get("TRIGGER")
        if tr:
            fam, d, prm = (list(tr) + [None, None, None])[:3]
            w = TRIG_WORDS.get(fam, f"{fam} trigger {{d}}").format(
                d={"up": "above", "dn": "below"}.get(d, d), p=prm, hl="high" if d == "up" else "low",
                hodlod="high of day" if d == "up" else "low of day")
            conds.append(dict(col="trigger", op="=", value=list(tr), label=lay[0] if lay else w,
                              span=_span(const_nodes["TRIGGER"]), source="TRIGGER"))
        for i, el in enumerate(const_nodes.get("FILTERS").elts if "FILTERS" in const_nodes else []):
            name, prm = ast.literal_eval(el)
            k = i + (1 if tr else 0)
            conds.append(dict(col=name, op="=", value=prm, label=lay[k] if k < len(lay) else name, span=_span(el.elts[1]),
                              source="FILTERS"))
        return _keys(out)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "mask"), None)
    for node in ast.walk(fn) if fn else []:
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        op = OPS.get(type(node.ops[0]))
        left, right = node.left, node.comparators[0]
        cl, cr, nl, nr = _colref(left), _colref(right), _num(left, consts), _num(right, consts)
        if cl and nr:
            col, (val, cname), vnode = cl, nr, right
        elif cr and nl:
            col, (val, cname), vnode, op = cr, nl, left, FLIP[op]
        else:
            if cl or cr:
                out["unparsed"].append(ast.get_source_segment(src, node))
            continue
        span = _span(const_nodes[cname]) if cname else _span(vnode)
        rec = dict(col=col, op=op, value=val, label=col_label(col), span=span, source=f"const {cname}" if cname else "mask",
                   const=cname)
        (out["time"] if col == "tod" else conds).append(rec)
    return _keys(out)


def _keys(out: dict) -> dict:
    """Workbench parameter keys: cond.<col> (cond.<col>#2 for a second comparison on the same column)."""
    seen: dict[str, int] = {}
    for c in out["conds"] + out["time"]:
        base = "cond." + c["col"].strip("|")
        seen[base] = seen.get(base, 0) + 1
        c["key"] = base if seen[base] == 1 else f"{base}#{seen[base]}"
    return out


def fmt_v(v) -> str:
    if isinstance(v, float):
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    if v is None:
        return "on"
    return str(v)


# ------------------------------------------------------------------------------------------------ Setup Generator id
def gen_tokens(setup_id: str, spec: dict | None) -> list[tuple[str, str]]:
    """GEN-<yymmdd>-<nn>-<conds>-<WINDOW>-<ctx>-<geom>-<side>: each name token with its meaning (from the gen spec)."""
    if not setup_id.startswith("GEN-"):
        return []
    from ..research.generator import spec as S

    parts = setup_id.split("-")
    words: dict[str, str] = {}
    if spec:
        for c in spec.get("conds") or []:
            try:
                words[S.cond_code(tuple(c))] = S._cond_words(tuple(c))
            except Exception:
                pass
    d = parts[1]
    out = [(f"{d}-{parts[2]}", f"generated 20{d[:2]}-{d[2:4]}-{d[4:6]}, spec #{parts[2]} of that run")]
    for t in parts[3:]:
        if t in words:
            out.append((t, words[t]))
        elif t in S.WINDOWS:
            out.append((t, f"time window {S.WINDOW_WORDS[t]} ET"))
        elif t in S.GEOM_WORDS:
            out.append((t, S.GEOM_WORDS[t]))
        elif t in ("long", "short"):
            out.append((t, f"side {t}"))
        else:
            out.append((t, "(not decoded)"))
    return out


# ------------------------------------------------------------------------------------------------ live record
def _journal(branch: str):
    from .daily_post import _journal as j

    return j(branch)


def live_record(setup_id: str) -> dict | None:
    """Every account journal's live trades (run_id = 1, closed) of this setup: R = pnl_adj / (|entry - stop| x shares)."""
    trades = []
    for acct, br in data_branches().items():
        db = _journal(br)
        if db is None:
            continue
        try:
            rows = db.execute("SELECT date, entry, stop, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id = 1 "
                              "AND strategy = ? AND exit_time IS NOT NULL", (setup_id,)).fetchall()
        except Exception:
            continue
        for d, e, sp, sh, p, pa, rm in rows:
            pa = pa if pa is not None else (p or 0.0)
            risk = abs((e or 0) - (sp or 0)) * (sh or 0)
            trades.append(dict(date=d, acct=acct, r=(pa / risk) if risk else (rm or 0.0), pnl=p or 0.0))
    if not trades:
        return dict(trades=0)
    return summarize(trades)


def summarize(trades: list[dict]) -> dict:
    n = len(trades)
    tot = sum(t["r"] for t in trades)
    by_day: dict[str, float] = {}
    by_acct: dict[str, list] = {}
    for t in trades:
        by_day[t["date"]] = by_day.get(t["date"], 0.0) + t["r"]
        by_acct.setdefault(t["acct"], []).append(t["r"])
    best = max(by_day, key=by_day.get)
    nb = sum(1 for t in trades if t["date"] != best)
    wo = (tot - by_day[best]) / nb if nb else None
    share = by_day[best] / tot if tot > 0 else None
    return dict(trades=n, sessions=len(by_day), avg_r=tot / n, total_r=tot, win=sum(t["r"] > 0 for t in trades) / n,
                avg_wo_best=wo, best_day=best, best_share=share, one_day=bool(share is not None and share >= 0.5),
                first=min(by_day), last=max(by_day), pnl=sum(t["pnl"] for t in trades),
                by_acct={a: dict(trades=len(v), avg_r=sum(v) / len(v)) for a, v in by_acct.items()})


def rule_changes(setup_id: str, accounts: list[str], first: str, last: str) -> list[str]:
    """CLAUDE.md rule-change context: ledger entries effective inside the record window that name this setup or change
    sizing / stops / costs / latches (rules that move every setup's R)."""
    p = ROOT / "research" / "ledger.jsonl"
    if not p.exists() or not first:
        return []
    kw = re.compile(r"sizing|position size|slots|latch|daily stop|daily loss|cost|flatten|R after costs|LR\d", re.I)
    al = [x for a in accounts for x in ACCOUNT_ALIASES.get(a, [a])] + ["every account", "all accounts"]
    out = []
    for line in p.read_text().splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        eff = d.get("effective") if isinstance(d.get("effective"), str) else d.get("date")
        if not eff or not (first <= str(eff)[:10] <= last):
            continue
        t = d.get("title", "")
        if setup_id in json.dumps(d) or (kw.search(t) and not d.get("moves") and any(x.lower() in t.lower() for x in al)):
            out.append(f"{str(eff)[:10]}: {t or d.get('id')}")
    out.sort()
    return out


# ------------------------------------------------------------------------------------------------ blueprint
def _prefilter_words(pf: str) -> str:
    if pf.startswith(("gap_le:", "gap_ge:")):
        x = float(pf.split(":", 1)[1])
        return f"gap at the open {'<=' if pf.startswith('gap_le') else '>='} {x:.2f}%"
    if pf == "new_high_100m":
        return "new 100-minute high"
    return pf


def _hhmm(x) -> str:
    x = int(x)
    return f"{x // 100:02d}:{x % 100:02d}"


def extract(setup_id: str, with_record: bool = True) -> dict:
    """Everything the blueprint shows: sections -> rows (label, value, note), plus the raw config / module data."""
    from ..setup_names import _names

    f = find_setup(setup_id)
    blk, cfg, acct = f["block"], f["cfg"], f["account"]
    names = account_names()
    mod = parse_module(blk["module"]) if blk.get("module") else None
    consts = (mod or {}).get("consts", {})
    side = consts.get("SIDE") or blk.get("side") or ((blk.get("gen") or {}).get("spec") or {}).get("side") or "?"
    geom = blk.get("geom") or consts.get("GEOM") or "t1s1"
    nm = _names().get(setup_id) or {}
    S: dict[str, list] = {k: [] for k in SECTIONS}
    U, A, L, live = cfg.get("universe", {}), cfg.get("account", {}), cfg.get("live", {}), cfg.get("live", {})

    # WHICH STOCKS
    S["WHICH STOCKS"].append(("Liquidity floor (20-day avg $ volume)", f">= ${float(blk['min_adv']) / 1e6:,.0f}M" if blk.get("min_adv") else "none (0)",
                              "setup min_adv" + ("; 0 = account universe floor only" if not blk.get("min_adv") else "")))
    S["WHICH STOCKS"].append(("Account universe", f"ADV >= ${U.get('min_avg_dollar_volume', 0) / 1e6:,.0f}M core, ATR >= {U.get('min_atr_pct')}%",
                              f"extended tier ${U.get('extended_min_avg_dollar_volume', 0) / 1e6:,.0f}M with rvol >= {U.get('extended_min_rvol')}x"))
    S["WHICH STOCKS"].append(("Price floor", f">= ${cfg.get('costs', {}).get('min_price')}", "costs.min_price"))
    S["WHICH STOCKS"].append(("Earnings blackout", f"{U.get('earnings_blackout_days')} trading days either side", "universe"))
    if U.get("exclude_ptp"):
        S["WHICH STOCKS"].append(("Partnerships (PTP)", "excluded", "10% withholding on sales"))
    if blk.get("prefilter"):
        S["WHICH STOCKS"].append(("Pre-filter", _prefilter_words(str(blk["prefilter"])), f"prefilter: {blk['prefilter']}"))
    if blk.get("symbols"):
        sy = consts.get("SYMBOLS") if blk["symbols"] == "module" else blk["symbols"]
        S["WHICH STOCKS"].append(("Allowed symbols", ", ".join(map(str, sy or []))[:90] or str(blk["symbols"]), "allow-list"))
    if blk.get("ticker_split"):
        ts = blk["ticker_split"]
        S["WHICH STOCKS"].append(("Ticker split", f"part {ts.get('part')} of {ts.get('of')}", "split copy"))
    if side == "short" and cfg.get("shorts", {}).get("require_easy_to_borrow"):
        S["WHICH STOCKS"].append(("Short borrow", "shortable + easy to borrow only", "broker flags"))

    # WHEN
    w = blk.get("window") or [950, 1500]
    S["WHEN"].append(("Entry window (5-min bar close)", f"{_hhmm(w[0])}-{_hhmm(w[1])} ET", f"window: [{w[0]}, {w[1]}]"))
    if consts.get("WINDOW"):
        S["WHEN"].append(("Module's own window", f"{_hhmm(consts['WINDOW'][0])}-{_hhmm(consts['WINDOW'][1])} ET", "WINDOW constant"))
    for t in (mod or {}).get("time", []):
        S["WHEN"].append(("Module time clause", f"bar close {t['op']} {_hhmm(t['value'])}", t["key"]))
    S["WHEN"].append(("No entries before", f"{live.get('no_entry_before', '09:50')} ET", "live.no_entry_before"))
    S["WHEN"].append(("Flat by", f"{cfg.get('session', {}).get('flatten_by', '15:55')} ET", "half days: close - 5 min"))
    if blk.get("refire"):
        S["WHEN"].append(("Refire", f"every qualifying bar, cooldown {blk.get('refire_cooldown', 1)} bar(s)", "refire: true"))
    else:
        S["WHEN"].append(("Refire", "first qualifying bar per symbol-day", "refire: false"))

    # ENTRY TRIGGER
    S["ENTRY TRIGGER"].append(("Side", side.upper(), "SIDE"))
    for c in (mod or {}).get("conds", []):
        if (mod or {}).get("style") == "stack":
            val = " ".join(fmt_v(x) for x in c["value"] if x is not None) if isinstance(c["value"], list) else \
                f"{c['col']} {fmt_v(c['value'])}"
            S["ENTRY TRIGGER"].append((c["label"], val, c["key"]))
        else:
            S["ENTRY TRIGGER"].append((c["label"], f"{c['col']} {c['op']} {fmt_v(c['value'])}", c["key"]))
    if mod and not mod["conds"] and mod["layers"]:
        for x in mod["layers"]:
            S["ENTRY TRIGGER"].append(("Module rule (as described)", x, "LAYERS"))
    ctx = blk.get("context")
    if ctx:
        S["ENTRY TRIGGER"].append(("Market context columns", ", ".join(ctx) if isinstance(ctx, list) else str(ctx), "context"))
    sg = live.get("split_tape_short_gate") or {}
    if side == "short" and sg.get("enabled"):
        S["ENTRY TRIGGER"].append(("Split-tape short gate", f"no shorts while QQQ - IWM from open >= {sg.get('spread_pct')} pts", "live"))
    S["ENTRY TRIGGER"].append(("Order", "enter at the close of the signal bar", "lab outcome model"))

    # RISK & EXIT
    rf = blk.get("r_atr_frac", 0.25)
    tgt, stp = GEOM_RS.get(geom, (None, None))
    S["RISK & EXIT"].append(("1R (risk unit)", f"{rf} x daily ATR", "r_atr_frac"))
    S["RISK & EXIT"].append(("Exit geometry", f"{geom}: {GEOM_WORDS.get(geom, geom)}", "geom" if blk.get("geom") else "GEOM"))
    if stp:
        S["RISK & EXIT"].append(("Stop", f"{stp}R {'below' if side == 'long' else 'above'} entry", "bracket stop"))
    S["RISK & EXIT"].append(("Target", f"+{tgt}R" if tgt else "none (stop / trail / flat)", "bracket target"))
    so = blk["scale_out_r"] if "scale_out_r" in blk else cfg.get("exits", {}).get("scale_out_r")
    if so and live.get("scale_out_max_per_day") != 0:
        S["RISK & EXIT"].append(("Scale-out", f"{blk.get('scale_out_frac', cfg.get('exits', {}).get('scale_out_frac', 0.5)):.0%} at +{so}R, rest to breakeven", "scale_out_r"))
    else:
        S["RISK & EXIT"].append(("Scale-out", "none", "scale_out_r: null" if "scale_out_r" in blk else "live scale-out off"))
    for k, lab in (("be_at_r", "Breakeven at"), ("trail_r", "Trail"), ("trail_after_r", "Trail starts at"),
                   ("time_stop_min", "Time stop (min)"), ("time_stop_min_r", "Time stop needs")):
        if blk.get(k) is not None:
            S["RISK & EXIT"].append((lab, fmt_v(blk[k]) + ("R" if k.endswith("_r") else ""), k))
    if blk.get("spy_exit_pct") is not None:      # SPYEXIT (owner 2026-11-16)
        mv = "up" if side == "short" else "down"
        S["RISK & EXIT"].append(("SPY exit", f"close at market once SPY is {mv} {fmt_v(blk['spy_exit_pct'])}% since entry"
                                 + (" (only while losing)" if blk.get("spy_exit_only_losing") else ""), "spy_exit_pct"))
    S["RISK & EXIT"].append(("Time exit", f"flat at {cfg.get('session', {}).get('flatten_by', '15:55')} ET", "session.flatten_by"))

    # LIMITS
    S["LIMITS"].append(("Open lots per setup", str(A.get("max_positions_per_strategy")), "max_positions_per_strategy"))
    lat = A.get("max_setup_daily_loss_r")
    S["LIMITS"].append(("Per-setup daily latch", f"stops at {-lat:g}R net" if lat else "off", "max_setup_daily_loss_r"))
    S["LIMITS"].append(("Account daily stop", f"-{A.get('max_daily_loss_r')}R", "max_daily_loss_r"))
    S["LIMITS"].append(("Lots per symbol", f"{live.get('max_lots_per_symbol', 1)} (same side)", "same_setup_reentry: " + str(live.get("same_setup_reentry"))))
    if blk.get("max_lots_per_symbol") is not None:
        S["LIMITS"].append(("Lots per symbol (this setup)", f"{blk['max_lots_per_symbol']} of its own", "strategies.<id>.max_lots_per_symbol"))
    if blk.get("twin_group"):
        S["LIMITS"].append(("Twin group", str(blk["twin_group"]), "never both twins on one symbol"))
    if live.get("max_stop_cost_r") is not None:
        S["LIMITS"].append(("Cost filter", f"skip if stop costs > {live['max_stop_cost_r']}R", "max_stop_cost_r"))
    S["LIMITS"].append(("Spread / size checks", f"spread <= {live.get('max_spread_bps')} bps and <= {live.get('max_spread_risk_frac')} of stop; "
                        f"<= {live.get('max_participation', 0):.0%} of 1-min volume", "live"))

    # ACCOUNT & SIZING
    eq = A.get("starting_equity", 100000)
    slot = eq * A.get("buying_power_multiple", 1) / max(1, A.get("slots", 1))
    here = ", ".join(names.get(a, a) for a in f["accounts"]) or f"not enabled (block in {names.get(acct, acct)})"
    S["ACCOUNT & SIZING"].append(("Runs in", here, "configs now"))
    S["ACCOUNT & SIZING"].append(("Size per trade", f"min({A.get('risk_per_trade_pct')}% equity at risk, slot ~${slot:,.0f})",
                                  f"{A.get('slots')} slots x {A.get('buying_power_multiple')} BP"))
    S["ACCOUNT & SIZING"].append(("Max position", f"{A.get('max_position_notional_pct')}% of equity", "max_position_notional_pct"))

    rec = live_record(setup_id) if with_record else None
    if rec is None:
        S["RECORD"].append(("Live record", "not loaded", "--no-record"))
    elif not rec["trades"]:
        S["RECORD"].append(("Live record", "no closed live trades yet", "journals run_id=1"))
    else:
        S["RECORD"].append(("Trades / sessions", f"{rec['trades']} / {rec['sessions']}", f"{rec['first']} to {rec['last']}"))
        S["RECORD"].append(("Avg R after costs", f"{rec['avg_r']:+.3f}R", f"total {rec['total_r']:+.1f}R, win {rec['win']:.0%}"))
        wo = "n/a" if rec["avg_wo_best"] is None else f"{rec['avg_wo_best']:+.3f}R"
        sh = "" if rec["best_share"] is None else f"; best day {rec['best_day']} = {rec['best_share']:.0%} of R" + (" (1 day)" if rec["one_day"] else "")
        S["RECORD"].append(("Avg R w/o best day", wo, sh.lstrip("; ")))
        if len(rec["by_acct"]) > 1:
            S["RECORD"].append(("By account", ", ".join(f"{names.get(a, a)} {v['trades']} tr {v['avg_r']:+.2f}R" for a, v in rec["by_acct"].items()), ""))
        rc = rule_changes(setup_id, sorted(rec["by_acct"]), rec["first"], rec["last"])
        if rc:
            S["RECORD"].append(("Rule changes in window", f"{len(rc)} (listed in the markdown)",
                                   "latest: " + "; ".join(x[:60] for x in rc[-2:])))
        rec["rule_changes"] = rc

    return dict(setup=setup_id, name=nm.get("name") or setup_id, what=nm.get("what", ""), side=side, geom=geom,
                account=acct, accounts=f["accounts"], block=blk, module=mod, sections=S, record=rec,
                gen=gen_tokens(setup_id, (blk.get("gen") or {}).get("spec")), date=date.today().isoformat())


# ------------------------------------------------------------------------------------------------ output
def to_markdown(bp: dict) -> str:
    L = [f"# Workbench blueprint: {bp['name']}", "", f"`{bp['setup']}` - {bp['side']} - built {bp['date']}", ""]
    if bp["what"]:
        L += [f"> {bp['what']}", ""]
    for sec in SECTIONS:
        rows = bp["sections"][sec]
        if not rows:
            continue
        L += [f"## {sec}", "", "| Part | Exact value | Source / note |", "|---|---|---|"]
        L += [f"| {a} | `{b}` | {c} |" for a, b, c in rows]
        L.append("")
    if bp["gen"]:
        L += ["## NAME CODE (Setup Generator id)", "", "| Token | Meaning |", "|---|---|"]
        L += [f"| `{t}` | {w} |" for t, w in bp["gen"]] + [""]
    m = bp["module"]
    if m:
        L += ["## MODULE", "", f"- file: `{m['path']}` (parsed as: {m['style']})"]
        if m["layers"]:
            L.append("- module's own layer notes: " + "; ".join(m["layers"]))
        if m["unparsed"]:
            L.append("- comparisons not parsed (read the module): " + "; ".join(f"`{u}`" for u in m["unparsed"]))
        L.append("")
    rc = (bp.get("record") or {}).get("rule_changes")
    if rc:
        L += ["## RULE CHANGES INSIDE THE RECORD WINDOW", ""] + [f"- {x}" for x in rc] + [""]
    L += ["## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)", ""]
    L += [f"- `{k}` = `{v}`" for k, v in params(bp).items()]
    L += ["", "Observation only: the original setup is never edited. " + DISCLAIMER + ".", ""]
    return "\n".join(L)


def params(bp: dict) -> dict:
    """Spawnable parameters: config keys of the block + module conditions (cond.<col>)."""
    out = {k: v for k, v in bp["block"].items() if k not in ("enabled", "type", "module", "tags", "gen", "from_testing2",
                                                              "former_primary") and not isinstance(v, dict)}
    for k in ("window", "min_adv", "refire", "refire_cooldown", "scale_out_r", "geom", "r_atr_frac", "max_lots_per_symbol",
              "spy_exit_pct"):
        out.setdefault(k, {"geom": bp["geom"], "r_atr_frac": 0.25, "refire": False, "refire_cooldown": 1}.get(k))
    for c in (bp["module"] or {}).get("conds", []) + (bp["module"] or {}).get("time", []):
        out[c["key"]] = c["value"]
    return out


CSS = """
*{box-sizing:border-box} body{margin:0;background:#0d2a52;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#eaf2ff}
#cap{width:760px;padding:22px 20px 10px;background-color:#0d2a52;
 background-image:linear-gradient(rgba(255,255,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.06) 1px,transparent 1px),
 linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
 background-size:100px 100px,100px 100px,20px 20px,20px 20px}
.tb{border:2px solid #cfe1ff;padding:12px 14px;margin-bottom:14px;position:relative}
.tb .k{font-size:10.5px;letter-spacing:.14em;color:#8fb4ea} h1{font-size:23px;margin:3px 0 4px;line-height:1.2}
.tb .id{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;color:#bcd3f5;word-break:break-all}
.tb .what{font-size:12.5px;color:#d6e4fb;margin-top:6px;line-height:1.35}
.side{display:inline-block;font-size:11px;font-weight:700;padding:1px 8px;border:1.5px solid currentColor;border-radius:3px;margin-left:8px;vertical-align:3px}
.long{color:#7ee2a8} .short{color:#ff9d9d}
.blk{border:1.5px solid #9fc2f5;margin:0 0 12px;background:rgba(13,42,82,.82)}
.blk h2{margin:0;font-size:12px;letter-spacing:.16em;padding:6px 10px;border-bottom:1.5px solid #9fc2f5;color:#ffffff;display:flex;justify-content:space-between}
.blk h2 span{color:#8fb4ea;font-weight:500;letter-spacing:.05em}
table{width:100%;border-collapse:collapse;font-size:12.5px}
td{padding:5px 10px;vertical-align:top;border-top:1px dashed rgba(159,194,245,.35)} tr:first-child td{border-top:none}
td.l{width:40%;color:#d6e4fb} td.v{font-family:ui-monospace,Menlo,Consolas,monospace;color:#fff;font-weight:600;word-break:break-word}
td.v small{display:block;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-weight:400;color:#8fb4ea;font-size:10.5px;margin-top:1px}
.code{font-size:11px;color:#bcd3f5} .code td.l{font-family:ui-monospace,Menlo,Consolas,monospace;width:34%;color:#fff;word-break:break-all}
.foot{font-size:10.5px;color:#8fb4ea;text-align:center;padding:6px 0 8px}
"""


def to_html(bp: dict) -> str:
    e = lambda s: html.escape(str(s))
    out = [f'<div id="cap"><div class="tb"><div class="k">MCF WORKBENCH · BLUEPRINT · {e(bp["date"])}</div>'
           f'<h1>{e(bp["name"])}<span class="side {e(bp["side"])}">{e(bp["side"].upper())}</span></h1>'
           f'<div class="id">{e(bp["setup"])}</div>' + (f'<div class="what">{e(bp["what"])}</div>' if bp["what"] else "") + "</div>"]
    for i, sec in enumerate(SECTIONS, 1):
        rows = bp["sections"][sec]
        if not rows:
            continue
        tr = "".join(f'<tr><td class="l">{e(a)}</td><td class="v">{e(b)}' + (f"<small>{e(c)}</small>" if c else "") + "</td></tr>"
                     for a, b, c in rows)
        out.append(f'<div class="blk"><h2>{e(sec)}<span>BLOCK {chr(64 + i)}</span></h2><table>{tr}</table></div>')
    if bp["gen"]:
        tr = "".join(f'<tr><td class="l">{e(t)}</td><td>{e(w)}</td></tr>' for t, w in bp["gen"])
        out.append(f'<div class="blk"><h2>NAME CODE<span>GENERATOR ID</span></h2><table class="code">{tr}</table></div>')
    m = bp["module"]
    if m:
        note = f"module {m['path']}" + (f" · {len(m['unparsed'])} comparison(s) not parsed, see markdown" if m["unparsed"] else "")
        out.append(f'<div class="foot">{e(note)}</div>')
    out.append(f'<div class="foot">Observation only — the original setup is never edited. Paper results. {DISCLAIMER}.</div></div>')
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>"


def render_png(h: str, path: Path) -> None:
    from playwright.sync_api import sync_playwright

    from .daily_post import CHROME

    exe = next((c for c in CHROME if Path(c).is_file()), None)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 800, "height": 900}, device_scale_factor=2)
        pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        pg.set_content(h, wait_until="domcontentloaded")
        pg.locator("#cap").screenshot(path=str(path))
        b.close()


def build(setup_id: str, out: Path, with_record: bool = True, png: bool = True, style: str = "engine",
          trades: str | None = "worst2", log=print) -> dict:
    """Blueprint markdown + PNG(s). style engine (default, Workbench v2): engine view + one teardown PNG per picked live
    trade (--trades worst2 | best1 | id:[acct:]<n>; needs the journals and read-only market data). style blocks: the v1
    table blueprint."""
    from . import engine as E

    bp = extract(setup_id, with_record=with_record)
    out.mkdir(parents=True, exist_ok=True)
    md = to_markdown(bp).rstrip("\n").split("\n")
    tail = md[-1]
    md = md[:-1]
    bp["files"] = []
    if style == "blocks":
        if png:
            render_png(to_html(bp), out / f"{setup_id}.png")
            bp["files"].append(out / f"{setup_id}.png")
    else:
        stages = E.engine_parts(bp)
        tr, sigs = E.live_trades(setup_id) if with_record else ([], [])
        heat = E.apply_heat(stages, tr, sigs) if (tr or sigs) else None
        bp["stages"], bp["heat"] = stages, heat
        md += E.engine_markdown(stages, heat)
        if png:
            E.render_engine(bp, stages, heat, out / f"{setup_id}_engine.png")
            bp["files"].append(out / f"{setup_id}_engine.png")
        picked = E.pick_trades(tr, trades) if trades else []
        if picked:
            md += ["## TRADE TEARDOWNS", ""]
        for k, t in enumerate(picked, 1):
            try:
                m1 = E.fetch_bars(t["symbol"], t["date"])
                fr = E.apply_daily(E.lab_frame(m1), E.fetch_daily(t["symbol"], t["date"]), t["date"])
                td = E.teardown_data(bp, stages, t, m1, fr)
            except Exception as ex:   # no bars / no network: the engine view still stands
                log(f"  teardown {t['symbol']} {t['date']}: skipped ({ex})")
                continue
            name = f"{setup_id}_trade{k}_{t['symbol']}_{t['date']}.png"
            if png:
                E.render_teardown(bp, stages, td, out / name, rank=f"{trades} #{k} · ")
                bp["files"].append(out / name)
            md += E.teardown_markdown(td, name)
    (out / f"{setup_id}.md").write_text("\n".join(md + ["", tail, ""]))
    return bp


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("setup")
    ap.add_argument("--out", default=None, help="default reports/workbench/<setup>/")
    ap.add_argument("--style", choices=("engine", "blocks"), default="engine")
    ap.add_argument("--trades", default="worst2", help="worst<n> | best<n> | id:[acct:]<n> | none (engine style)")
    ap.add_argument("--no-record", action="store_true", help="skip the live record (no data branches available)")
    ap.add_argument("--no-png", action="store_true", help="markdown only")
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else ROOT / "reports" / "workbench" / a.setup
    bp = build(a.setup, out, with_record=not a.no_record, png=not a.no_png, style=a.style,
               trades=None if a.trades == "none" else a.trades)
    print(f"{a.setup}: {out / (a.setup + '.md')}")
    for f in bp["files"]:
        print(f"  {f}")
    if bp["module"] and bp["module"]["unparsed"]:
        print(f"  note: {len(bp['module']['unparsed'])} module comparison(s) not parsed")
    print(DISCLAIMER)


if __name__ == "__main__":
    main()
