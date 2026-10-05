from mcf.backtest.engine import Backtester
from mcf.config import load_config
from mcf.dashboard.build import build
from mcf.data.synthetic import make_universe
from mcf.journal import Journal
from mcf.strategies.setups import build_strategies


def test_journal_roundtrip_and_dashboard(tmp_path):
    cfg = load_config()
    cfg["universe"]["min_avg_dollar_volume"] = 0
    trades = Backtester(build_strategies(cfg), cfg).run(make_universe(["SPY", "QQQ", "AAA", "BBB"], days=30))
    db = tmp_path / "j.db"
    j = Journal(db)
    run = j.new_run("backtest", "t")
    j.add_trades(run, trades)
    assert len(j.trades(run_id=run)) == len(trades)
    out = build(db, tmp_path / "d.html")
    html = out.read_text()
    assert "/*__DATA__*/null" not in html and '"sources"' in html
