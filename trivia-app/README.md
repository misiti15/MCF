# Deep Cut (working name)

Personal trivia on the things you're actually into, from "Sports" all the way down to "the Big Red Machine".
A daily drop of 3-5 questions arrives by notification, email or text. Every answer comes with the correct answer,
a bonus tidbit and a source you can check.

Product rules and open decisions (names, level names, scoring, costs): **[docs/DECISIONS.md](docs/DECISIONS.md)**.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m trivia.content          # check the question bank
pytest -q                         # tests
uvicorn trivia.api:app --reload   # app at http://localhost:8000
python -m trivia.scheduler --dry-run   # who gets a drop right now
```

No-server demo (all logic in the browser): `python scripts/build_demo.py --standalone`, then open `dist/demo.html`.

## Layout

| Path | What |
|---|---|
| `content/topics.json` | Topic tree, aliases for the free-text matcher, starter packs |
| `content/questions.json` | Question bank: question, 4 options, answer, explanation, tidbit, source, status |
| `web/img/` | Pictures for picture questions |
| `trivia/config.py` | Brand, points, level-name themes, drop sizes, bonus cap |
| `trivia/content.py` | Loads content and enforces the accuracy rules |
| `trivia/topics.py` | Free text -> topics ("lambos" -> Lamborghini), "go deeper" suggestions |
| `trivia/game.py` | Daily drop builder, answering, "one more", scoring, stats |
| `trivia/notify.py` | Console, email (SMTP) and text (Twilio) senders |
| `trivia/scheduler.py` | Sends drops when they're due. Run every 15 minutes |
| `trivia/api.py` | HTTP API and the web app |
| `web/` | The app (one page, no build step) |

## Adding questions

Add to `content/questions.json` with `"status": "draft"`. A person then opens the source, adds
`source.checked` (date) and `source.excerpt` (the sentence that proves the answer), and sets `"status": "verified"`.
Production runs with `TRIVIA_SERVE_DRAFTS=0`, so only verified questions reach players.

## Secrets

Copy `.env.example` to `.env`. Never commit it. Texts and email stay off until their variables are set;
until then drops print to the console.
