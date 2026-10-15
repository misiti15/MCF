"""Render the proposed YAML snippets (strategies, setup_order, setup_names) with quoted clock times.
Educational only - not financial advice."""
import yaml
from common import OUT

S = yaml.safe_load((OUT / "proposed_strategies.yaml").read_text())["strategies"]
NOTE = {
    "V1": "QQQ down >= 1.0% from the open by 09:55",
    "V2": "SPY down >= 0.75% from the open by 09:45",
    "V3": "SPY down >= 0.75% from the open by 09:55",
    "V5": "SPY down >= 0.5% from the open by 09:45",
}
LEV = {"SPY": "1x", "QQQ": "1x", "SSO": "2x S&P", "SPUU": "2x S&P", "SPXL": "3x S&P", "UPRO": "3x S&P", "QLD": "2x Nasdaq-100",
       "TQQQ": "3x Nasdaq-100"}
out, names, order, cur = [], [], [], None
for n, p in S.items():
    v = p["testing"]["variant"]
    if v != cur:
        cur = v
        out.append(f"  # ---- Index open-dip bounce {v}: {NOTE[v]} (owner 2026-10-15, research/bdi/idxdip1015). Long only.")
    ex = n.rsplit("-", 1)[1]
    tgt = "trail 1R behind the best once +1R" if ex == "trail" else "no target, no trail"
    inst = ([f"    symbols: [{p['symbols'][0]}]"] if p.get("symbols") else
            [f"    trade_candidates: [{', '.join(p['trade_candidates'])}]", f"    pick: {p['pick']}"])
    out += [f"  {n}:", "    enabled: true", "    class: index_dip_bounce", *inst,
            f"    signal_symbol: {p['signal_symbol']}", f"    dip_pct: {p['dip_pct']}", f'    dip_by: "{p["dip_by"]}"',
            '    entry_from: "09:50"', '    entry_until: "10:05"', "    trigger: recovery", "    recovery_frac: 0.20",
            "    stop_buffer_frac: 0.10", "    target: null"]
    if ex == "trail":
        out += ["    trail_r: 1.0", "    trail_after_r: 1.0"]
    out += ["    scale_out_r: null",
            f'    testing: {{added: "2026-10-16", source: "research/bdi/idxdip1015", variant: {v}, '
            f'bar: "forward test (owner request); research bar not met"}}']
    order.append(f"    - {n}")
    if p.get("symbols"):
        sym = p["symbols"][0]
        label, buy, lvl = sym, f"{sym} ({LEV[sym]})", f"{sym}'s"
    else:
        label = "3x S&P"
        buy = ("whichever of SPXL / UPRO (3x S&P) has traded more dollars since 09:30 (one trade; the journal shows "
               "which)")
        lvl = "the traded ETF's"
    names += [f"{n}:", f"  name: Index Dip Bounce {v[1:]} {label}{' (hold)' if ex == 'hold' else ''}", "  side: long",
              f'  what: "{NOTE[v]}; buy {buy} at 09:50-10:05 once the {p["signal_symbol"]} has regained 20% of the '
              f'drop off its low. Stop just under {lvl} morning low; {tgt}; out by 15:55."']
(OUT / "proposed_strategies_block.yaml").write_text("\n".join(out) + "\n")
(OUT / "proposed_setup_order.yaml").write_text("\n".join(order) + "\n")
(OUT / "proposed_setup_names.yaml").write_text("\n".join(names) + "\n")
# round-trip check
blk = yaml.safe_load("strategies:\n" + "\n".join(out))["strategies"]
for n, p in blk.items():
    q = S[n]
    assert all(p[k] == q[k] for k in q if k != "testing"), n
    assert isinstance(p["dip_by"], str) and isinstance(p["entry_until"], str)
yaml.safe_load("\n".join(names))
print(len(blk), "setups rendered; round trip OK")
