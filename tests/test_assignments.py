"""Owner 2026-10-20: the dashboard's setup assignments must always match the configs. Any promotion / demotion /
move must regenerate docs/live/assignments.json (python -m mcf.report.assignments) in the same commit."""
import json
from pathlib import Path

from mcf.report import assignments as A


def test_assignments_file_matches_configs():
    d = json.loads((Path(A.OUT)).read_text())
    cur = A.current()
    assert d["accounts"] == cur, "docs/live/assignments.json is stale: run python -m mcf.report.assignments"
    for name, v in d["setups"].items():
        assert v["accounts"] == sorted(a for a, s in cur.items() if name in s), name
    assert d.get("last_change", {}).get("at")


def test_build_stamps_only_real_changes():
    prev = A.build(None)
    same = A.build(prev)
    assert same["last_change"] == prev["last_change"]          # nothing moved: timestamp unchanged
    moved = json.loads(json.dumps(prev))
    k = next(iter(moved["setups"]))
    moved["setups"][k]["accounts"] = ["nowhere"]
    new = A.build(moved)
    assert new["last_change"]["changes"][0]["setup"] == k and new["setups"][k]["since"]


def split_violations(strategies: dict) -> list[str]:
    """Owner 2026-10-20: promotion = move; a setup runs in ONE account, except split copies ("Goals for copies"):
    at most one copy per testing account (testing + testing2 only), each with ticker_split of the same `of`, with
    parts that differ and cover 0..of-1. Primary / graveyard / gen never share a setup."""
    acc = A.current(strategies)
    where: dict[str, list[str]] = {}
    for a, v in acc.items():
        for s in v:
            where.setdefault(s, []).append(a)
    bad = []
    for name, accts in where.items():
        if len(accts) < 2:
            continue
        if not set(accts) <= set(A.SPLIT_ACCOUNTS):
            bad.append(f"{name}: in {sorted(accts)} (only testing + testing2 may hold split copies)")
            continue
        ts = [(strategies[a][name] or {}).get("ticker_split") for a in accts]
        if not all(ts):
            bad.append(f"{name}: in {sorted(accts)} without ticker_split in every copy")
            continue
        ofs = {int(t["of"]) for t in ts}
        parts = sorted(int(t["part"]) for t in ts)
        if len(ofs) != 1 or parts != list(range(next(iter(ofs)))):
            bad.append(f"{name}: ticker_split parts {parts} of {sorted(ofs)} do not split the tickers exactly once")
    return bad


def test_no_setup_runs_in_two_accounts():
    """Owner 2026-10-20: promotion = move; no copies of a setup in any account - except split-ticker copies in the
    two testing accounts (owner 2026-10-20, 'Goals for copies')."""
    assert split_violations(A._strategies()) == []


def test_split_guard_rules():
    lab = {"type": "lab", "module": "x.py"}
    on = lambda **k: {**lab, "enabled": True, **k}           # noqa: E731
    half = lambda p: on(ticker_split={"part": p, "of": 2})   # noqa: E731
    base = {a: {} for a in A.ACCOUNTS}
    ok = {**base, "testing": {"S": half(0)}, "testing2": {"S": half(1)}}
    assert split_violations(ok) == []
    assert split_violations({**base, "testing": {"S": half(0)}, "testing2": {"S": half(0)}})          # same half
    assert split_violations({**base, "testing": {"S": on()}, "testing2": {"S": half(1)}})             # one unsplit
    assert split_violations({**base, "primary": {"S": half(0)}, "testing2": {"S": half(1)}})          # primary copy
    assert split_violations({**base, "gen": {"S": half(0)}, "testing": {"S": half(1)}})               # gen copy
    assert split_violations({**base, "testing": {"S": half(0)},
                             "testing2": {"S": on(ticker_split={"part": 1, "of": 3})}})              # mixed `of`
    assert split_violations({**base, "testing": {"S": on()}, "testing2": {"S": {**on(), "enabled": False}}}) == []


def test_split_halves_disjoint_and_cover():
    from mcf.strategies.base import ticker_part
    uni = [f"S{i}" for i in range(500)] + ["AAPL", "msft", "SPY", "QQQ", "TQQQ", "BRK.B"]
    h0 = {s for s in uni if ticker_part(s, 2) == 0}
    h1 = {s for s in uni if ticker_part(s, 2) == 1}
    assert h0.isdisjoint(h1) and h0 | h1 == set(uni)
    assert 150 < len(h0) < 356                                   # a real split, not everything on one side
    assert ticker_part("msft", 2) == ticker_part("MSFT", 2)      # case-insensitive, stable (crc32)
    import zlib
    assert ticker_part("AAPL", 2) == zlib.crc32(b"AAPL") % 2


def test_split_strategy_signals_only_its_half():
    """A split copy produces no signals for the other half, in the backtest path (Strategy.signals) and the runner
    path (Strategy.trades_symbol, checked before anything is journaled); absent ticker_split = every symbol."""
    from types import SimpleNamespace

    from mcf.strategies.base import Signal, Strategy, ticker_part
    from mcf.strategies.setups import build_strategies

    class Always(Strategy):
        name = "always"

        def generate(self, ctx):
            return [Signal(ctx.symbol, self.name, 1, 0, 1.0)]

    syms = [f"T{i}" for i in range(60)]
    whole, a, b = Always(), Always(), Always()
    a.ticker_split, b.ticker_split = (0, 2), (1, 2)
    ctx = lambda s: SimpleNamespace(symbol=s)                # noqa: E731
    got = {k: {s for s in syms if st.signals(ctx(s))} for k, st in (("all", whole), ("a", a), ("b", b))}
    assert got["all"] == set(syms)
    assert got["a"].isdisjoint(got["b"]) and got["a"] | got["b"] == set(syms)
    assert all(ticker_part(s, 2) == 0 for s in got["a"])
    assert {s for s in syms if a.trades_symbol(s)} == got["a"]
    # from config: ticker_split is parsed onto the strategy, never passed to its params
    cfg = {"strategies": {"X": {"enabled": True, "class": "orb", "ticker_split": {"part": 1, "of": 2}},
                          "Y": {"enabled": True, "class": "orb"}}}
    st = {s.name: s for s in build_strategies(cfg)}
    assert st["X"].ticker_split == (1, 2) and st["Y"].ticker_split is None
    assert "ticker_split" not in st["X"].params
