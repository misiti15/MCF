# EVD1 — outside evidence (Scout source sweep, 2026-11-10 09:20 ET; read-only web, before EVD1 outcomes were posted)

*Educational only — not financial advice. Search snippets / abstracts only; nothing here is adopted untested.*

- **Overnight vs intraday "tug of war"** (Lou, Polk & Skouras, JFE 2019): overnight and intraday returns tend to move in opposite
  directions; clientele split (institutions intraday, retail overnight).
- **Earnings days, overnight vs intraday** (Liu, Hope & Hu, Journal of Corporate Finance 2023, China): the overnight window carries
  the reaction; the intraday session trades AGAINST both the news and the overnight move; abnormal overnight returns predict
  future returns, intraday ones do not. https://ideas.repec.org/a/eee/corfin/v82y2023ics0929119923001207.html
- **Option trading after the opening bell**: option activity in the first 30 minutes predicts the rest-of-day stock return, more so
  after overnight earnings news (we have no options data). https://law-journals-books.vlex.com/vid/option-trading-after-the-855622256
- **Overnight-concentrated PEAD** (SSRN working paper, 2024): post-announcement drift shows up mainly in overnight returns.
  https://www.scribd.com/document/721180055/SSRN-id4765828
- Our own: er-react-gap's best row was the gap FADE (+0.24% t 1.62, H1); er-eps-surprise: beat-but-sold-off / miss-but-rallied
  negative in 10 of 12 rows.

## Reading rule registered BEFORE the EVD1 output (no new look)
EVD1 measures every outcome in the GAP's direction, so a negative value is a fade. The prior above leans to a reaction-session fade,
not continuation. If the AGREE (or all-event) rows are negative in TRAIN and VALID, BMO and AMC, gross and ex-market, AND below the
random-gapper control, that is read as a fade lead in the same family (gap-fade lines are already inside N 858: er-react-gap,
cwt-a7); its sign was not chosen from the data. If the signs disagree across splits, EVD1 is closed either way.
