"""Guard for docs/live/index.html (owner 2026-10-21: "NOTHING is to be removed from it").

Pins every card title, element id, leaderboard column, table header, tile label and data source the live dashboard
had on 2026-10-21. New work may ADD to these lists; a test failure here means something was removed or renamed —
put it back (or ask the owner) instead of editing the list. Educational only — not financial advice.
"""
from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "docs/live/index.html").read_text()

# every element id (cards, tables, controls)
IDS = [
    "acc-all", "dm-card", "dm-sum", "dm-tab", "gen-card", "gen-sorted", "gen-sum", "gen-tab", "gl-card", "gl-sum",
    "gl-trend", "lab-when", "lb-acct", "lb-asg", "lb-card", "lb-ctl", "lb-min", "lb-show", "lb-sorted", "lb-sum", "lb-tab",
    "lh", "lh-alerts", "lh-asof", "lh-chart", "lh-days", "lh-mode", "lh-pos", "lh-tiles", "live", "lv-asof", "lv-chg",
    "lv-chg-when", "lv-closed", "lv-cmp", "lv-cmp-acct", "lv-cmp-h", "lv-days", "lv-ideas", "lv-lab", "lv-msg", "lv-phase",
    "lv-pos", "lv-score", "lv-sig", "lv-skip", "lv-tiles", "lv-val", "pt-card", "pt-flags", "pt-note", "pt-sum", "pt-tab",
    # added 2026-10-21 (UI-DASH 1: last session)
    "lb-last-band",
    # added 2026-10-21 (UI-DASH 2: replay band, pipeline card)
    "lb-replay-band", "pipe-card", "pipe-sum", "pipe-tab",
    "sd-panel", "sd-back",   # added 2026-10-21 (UI-DRILL)
    "glance", "qnav", "chg-card", "gl-pl", "gl-streak", "gl-dec", "gl-alerts",   # added 2026-10-21 (UI-DASH 4)
    "gen-last-band",   # added 2026-10-22 (Last session band in the Generated card)
    "sd-reg",   # added 2026-10-22 (regime1022: market conditions in the drill-down)
    "dec-card", "dec-list", "dec-done", "dec-done-list", "dec-n",   # added 2026-10-22 (Your decisions card)
]

# card / section titles (h2 text; a title may gain extra words, never lose these)
TITLES = [
    "MCF Update — live paper session", "Changes for the next session", "MCF Primary vs MarcoFlow", "Open MCF positions",
    "Signals today", "Why signals were skipped", "Closed MCF trades today", "Day by day", "Setups and their status",
    "Demoted from Primary — how they are doing in Testing 1", "Setup leaderboard — all accounts, since start",
    "Generated setups leaderboard — Setup Generator account", "Scorecard (last 4 sessions)", "Playing time per setup",
    "Generator Lab", "Long-hold (S6) — paper account", "Return since start", "Holdings", "Last sessions",
    "New setup pipeline",   # added 2026-10-21
    "At a glance",          # added 2026-10-21
    "Your decisions",       # added 2026-10-22
]

# leaderboard COLS entries [key, header] and how many tables carry each (setup leaderboard + generated leaderboard)
COLS = Counter({
    '["rank", "#"]': 2, '["name", "Setup"]': 2, '["acctLabel", "Account"]': 1, '["trades", "Live trades"]': 2,
    '["sessions_traded", "Sessions"]': 1, '["win_rate", "Win rate"]': 2, '["breakeven_wr", "Break-even win rate"]': 2,
    '["avg_r", "Avg R"]': 2, '["t_stat", "Confidence (t)"]': 2, '["total_r", "Total R"]': 2, '["pnl", "P/L"]': 2,
    '["profit_factor", "PF"]': 1, '["recent_avg_r", "Last 4 avg R"]': 2, '["expected_r", "Backtest R"]': 1,
    '["gap", "vs backtest"]': 1, '["sim_avg_r", "Sim. trades / sim avg R (SIMULATED)"]': 1, '["pt", "Playing time"]': 1,
    '["flag", "Flag"]': 1, '["generated", "Generated"]': 1, '["per_day", "Trades/day"]': 1,
    '["scr_train", "Screen train R"]': 1, '["scr_valid", "Screen valid R"]': 1, '["scr_day", "Screen /day"]': 1,
    # added 2026-10-21 (UI-DASH 1: last session)
    '["ls_trades", "Last-session trades"]': 1, '["ls_r", "Last-session R"]': 1, '["ls_pnl", "Last-session P/L"]': 1,
    # added 2026-10-21 (UI-DASH 2: replay band)
    '["rp_trades", "Replay trades"]': 1, '["rp_sessions", "Replay sessions"]': 1, '["rp_win_rate", "Replay win rate"]': 1,
    '["rp_avg_r", "Replay avg R"]': 1, '["rp_t", "Replay t"]': 1, '["rp_total_r", "Replay total R"]': 1,
    '["best_reg", "Best conditions"]': 1,   # added 2026-10-22 (regime1022: market conditions)
    '["exp_live", "Expected live /day"]': 1,   # added 2026-10-26 (GX5: realistic live expectation)
})

# headers of the tables built in JS (table([...]) / head = [...]) and static <th> cells
TABLE_HEADERS = [
    "Date", "Trades", "Win rate", "P/L", "Adj. P/L", "Avg R", "PF", "Change", "Setup", "Status", "Apr–Jun backtest",
    "Symbol", "Side", "Qty", "Entry", "Last", "Unrealized", "Sector ETF", "Beta", "Time", "Price", "Reason", "Signals",
    "In", "Out", "Exit", "R", "Slip", "Current account", "Backtest expected R", "Verdict", "Rule", "Held up",
    "Found: n / success / exp R", "Checked: n / success / exp R", "Idea", "In one line", "Why look at it",
    "What changes", "What you should see", "Type", "Effective", "Setup (priority)", "Today sig / taken", "Sessions",
    "Signals / taken / trades", "Taken/day", "Expected/day", "Per week", "Lost to others", "Lost to", "Top skips",
    "Sim. trades / sim avg R (SIMULATED)", "Metric", "Run", "Screened", "New setups", "From scan", "Median screen R",
    "Best screen R", "Best t", "Today (Testing 1)", "In Testing so far", "In Primary (before demotion)",
    "Full-day twin today", "Testing sessions", "So far", "Value", "Weight", "Unrealised P/L", "Equity", "Day", "SPY",
    "EW univ.", "Replay", "Tracking diff.", "Drawdown",
    # added 2026-10-21 (UI-DASH 1: scorecard last session)
    "Last-session trades", "Last-session R", "Last-session P/L",
]
STATIC_TH = [
    "Best screen R", "Best t", "Date", "Day", "Drawdown", "EW univ.", "Entry", "Equity", "From scan", "Full-day twin today",
    "In Primary (before demotion)", "In Testing so far", "Median screen R", "Metric", "New setups", "Qty", "Replay",
    "Run", "SPY", "Screened", "Setup", "So far", "Symbol", "Testing sessions", "Today (Testing 1)", "Tracking diff.",
    "Unrealised P/L", "Value", "Weight",
]

TILES = ["Trades today", "Win rate", "P/L today", "Signals", "Data health", "Equity", "Day P/L", "Since start", "vs SPY",
         "vs EW universe", "vs backtest replay", "Drawdown", "Holdings"]

ACCOUNT_CARDS = ['"primary", name: "Primary"', '"testing", name: "Testing 1"', '"testing2", name: "Testing 2"',
                 '"gen", name: "Setup Generator"', '"graveyard", name: "Graveyard"', '"longhold", name: "Long-hold (S6)"']

# every data source the page reads
SOURCES = [
    "../live/assignments.json", "../live/generator_lab.json", "../live/ideas.json", "../live/leaderboard.json",
    "../live/linkage.json", "../live/setup_names.json", "https://raw.githubusercontent.com/misiti15/MCF/",
    "https://raw.githubusercontent.com/misiti15/MCF/claude/intraday-trading-system-witis4/research/ledger.jsonl",
    "https://raw.githubusercontent.com/misiti15/MCF/mcf-data-longhold/longhold/", "/longhold/status.json",
    "/reports/scorecard.json", "/status.json", "discovery/latest.json", "marks.csv", "mcf-data-gen/reports/scorecard.json",
    "mcf-data-testing/reports/scorecard.json", "mcf-data-testing/status.json", "mcf-data/discovery/latest.json",
    "mcf-data/reports/scorecard.json", "reports/scorecard.json", "status.json",
    "mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-gen", "mcf-data-graveyard", "mcf-data-longhold",
    # added 2026-10-21 (UI-DASH 1: per-account session reports)
    '"/reports/" + date + ".csv"',
    "../live/replay.json", "../live/pipeline.json",   # added 2026-10-21 (UI-DASH 2)
    "claude/intraday-trading-system-witis4/research/owner_inbox/OPEN_ITEMS.md",   # added 2026-10-21 (UI-DASH 4)
    "../live/regimes.json",   # added 2026-10-22 (regime1022)
    "../live/decisions.json",   # added 2026-10-22 (Your decisions card)
]


class _H2(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth, self.cur, self.titles = 0, "", []

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.depth += 1
            self.cur = ""

    def handle_endtag(self, tag):
        if tag == "h2" and self.depth:
            self.depth -= 1
            self.titles.append(re.sub(r"\s+", " ", self.cur).strip())

    def handle_data(self, data):
        if self.depth:
            self.cur += data


def test_ids_kept():
    have = set(re.findall(r'\bid="([^"$]+)"', HTML))
    assert not [i for i in IDS if i not in have]


def test_card_titles_kept():
    p = _H2()
    p.feed(HTML)
    missing = [t for t in TITLES if not any(t in h for h in p.titles)]
    assert not missing


def test_leaderboard_columns_kept():
    missing = {c: n for c, n in COLS.items() if HTML.count(c) < n}
    assert not missing


def test_table_headers_kept():
    assert not [h for h in TABLE_HEADERS if f'"{h}"' not in HTML and f">{h}</th>" not in HTML]
    assert not [h for h in STATIC_TH if f">{h}</th>" not in HTML]


def test_tiles_and_account_cards_kept():
    assert not [t for t in TILES if f'"{t}"' not in HTML]
    assert not [a for a in ACCOUNT_CARDS if a not in HTML]


def test_data_sources_kept():
    assert not [s for s in SOURCES if s not in HTML]


def test_disclaimer_kept():
    assert HTML.count("Educational only — not financial advice") >= 5


def test_glossary_covers_new_columns():
    for term in ("Last session", "Last-session trades", "Last-session R", "Last-session P/L", "Replay", "Replay trades",
                 "Replay sessions", "Replay win rate", "Replay avg R", "Replay t", "Replay total R", "Stage",
                 "Best conditions", "Bull", "Bear", "Choppy", "Quiet", "Expected live /day"):
        assert f'"{term}":' in HTML, term


def test_setup_drilldown_panel():
    """UI-DRILL (owner 2026-10-21): side panel opened from any setup, Esc / outside click closes, Prev / Next and arrow
    keys follow the table order, #setup=<code> deep link, bottom sheet on phones."""
    for needle in ('id="sd-panel"', '"Escape"', '"ArrowLeft"', '"ArrowRight"', "#setup=", "history.pushState",
                   "hashchange", "max-width: 640px", "Previous session", "Record — live · replay · backtest", "Daily R since start"):
        assert needle in HTML, needle


def test_usability_strip_nav_and_collapse():
    """UI-DASH 4 (owner 2026-10-21): at-a-glance strip, section quick-nav, collapsible cards remembered per viewer
    (browser storage always inside try/catch), a one-line "what this tells you" per card."""
    for a in ('href="#live">Today', 'href="#lb-card">Setups', 'href="#pipe-card">Research', 'href="#acc-all">Accounts',
              'href="#chg-card">System'):
        assert a in HTML, a
    assert "flatten_failed" in HTML and "data_stale" in HTML
    assert 'try { saved = JSON.parse(localStorage.getItem("mcf.cards")' in HTML
    assert 'try { localStorage.setItem("mcf.cards"' in HTML
    assert HTML.count("localStorage") == 2
    assert 'class="why"' in HTML and ".card.collapsed" in HTML


def test_generated_card_last_session():
    """Owner 2026-10-22: the Generated setups card carries the same Last session band as the setup leaderboard."""
    gen = HTML[HTML.index("// Generated setups leaderboard (owner 2026-10-19)"):]
    gen = gen[:gen.index("</script>")]
    for c in ('["ls_trades", "Last-session trades"]', '["ls_r", "Last-session R"]', '["ls_pnl", "Last-session P/L"]'):
        assert c in gen, c
    assert 'id="gen-last-band"' in gen and "daySummary" in gen and "last_session" in gen
