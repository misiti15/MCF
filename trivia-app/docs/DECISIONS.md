# Product decisions

Working codename: **Deep Cut**. Brand lives in `trivia/config.py` (`BRAND`) only.
Status: names and level names are **open**; everything else below is the current rule in code.

## 1. Name shortlist

How to choose (do this before buying anything):
1. Say it out loud to five people. Can they spell it after hearing it once?
2. Read it inside a text: "_Name_: 3 new questions on the Reds. Tap to play."
3. Search USPTO trademarks (tmsearch.uspto.gov), classes 9 (apps) and 41 (games), plus the App Store and Google Play.
4. Check the .com or .app domain and the Instagram/TikTok handle.
5. Only then register the domain and handles the same day.

| Name | Why it works | Known risk |
|---|---|---|
| **Fanatiq** | Fanatic + IQ. Says "fan of anything" and "smart" at once. Coined word, easier to own. | "Phanatiq" fan-club app announced 2023; Fanatec (racing gear). Spelling must be taught once. |
| **Deep Cut** | Music term for the track only real fans know: exactly the niche pitch. Hardest level shares the name. | "Deep Cuts Music Trivia" (live Zoom event, deepcutstrivia.com) is in trivia already. |
| **Called It** | What you say when you get one right. Great in a text. | Common phrase; harder to trademark. |
| **Trivyou** | Trivia + you: personal by definition. | Close to "Trivy" (2015 app). Spelling. |
| **Bragging Rights** | The payoff of the light show. | Long; an open-source trivia project uses it. |
| **Superfan** | Instantly clear. | Very generic; many products use it. |
| **Brainbait** | Hooky, playful, works for any topic. | Doesn't say "personal". |
| **Nerd Snipe** | Internet slang for a question you can't resist. | Niche slang; not everyone knows it. |
| **In the Weeds** | Idiom for deep detail. | Also means "overwhelmed" in restaurant talk. |
| **Inside Baseball** | Idiom for insider detail. | Sounds sports-only. |
| Also: Know-It-All, Smarty, Quiz Drip, Brain Snack, Daily Drop, Nichey, Fandom'd, Pocket Trivia, The Clutch | | |

Recommendation: shortlist **Fanatiq**, **Deep Cut**, **Called It**, run steps 1-4 on all three, pick the first that clears.

## 2. Level names

Colors are fixed: green, gold, orange, magenta. Names are a theme the player can switch in Settings (all are in `config.LEVEL_THEMES`).

| Theme | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| fan (default) | Bandwagon | Season Ticket | Die-Hard | Superfan |
| record | Radio Hit | B-Side | Rare Groove | Deep Cut |
| spicy | Mild | Medium | Hot | Ghost Pepper |
| gut | Gimme | Hold Up... | Sweat Zone | Oh, Come ON |
| odds | Easy Money | Coin Flip | Long Shot | Hail Mary |
| garage | Cruise Control | Fast Lane | Redline | Full Send |
| brain | No-Brainer | Brain Teaser | Brain Buster | Brain Melter |

More to try: Warm-Up / Starting Lineup / Extra Innings / Hall of Fame; Bunny Hill / Blue Square / Black Diamond / Double Black;
Sunny / Cloudy / Stormy / Tornado; Rookie / Starter / All-Star / GOAT.
Pick the default to match the name (Fanatiq -> fan, Deep Cut -> record).

## 3. After every answer

Always shown, right or wrong: the **correct answer**, a one-line explanation, a **bonus tidbit** (a second true fact
related to the answer), the source link, and "Challenge this fact".
15 shouts for right answers, 15 for wrong ones, plus 6 sub-lines each (`web/app.js`, `WIN`/`LOSE`).

## 4. Daily drop size

3, 4 or 5 questions; **3 is the default**. 3 = Bandwagon, Season Ticket, Die-Hard. 4 = one of each level.
5 = 1, 2, 3, 3, 4. Easiest first so the day starts with a win. Spread across the player's topics.

## 5. "Give me one more"

- Appears only after the drop is finished.
- Up to **3 per day** (`BONUS_PER_DAY`), so niche topics don't run dry in a week.
- **Counts toward level accuracy** (it's real knowledge), **earns no points, never breaks the streak**.
  Why: the daily score stays fair (everyone gets the same N), and a bonus is zero-risk, so people tap it more.

## 6. Scoring

Drop questions: 100 / 200 / 300 / 500 by level. 3 right in a row = 1.5x, 5 = 2x. Perfect drop = +100.
Tracked per level: answered, right, accuracy. Also: total points, day streak, best run.

## 7. Picking subjects (the big one)

Three ways in, all on the first screen. No account needed until after the first drop.
1. **Type it.** One box: "What are you into?" Typed text is matched to the topic tree with aliases and typo
   tolerance ("lambos" -> Lamborghini, "herd football" -> Thundering Herd athletics). No match -> "Request it",
   queued for research with an honest status.
2. **Starter packs.** One tap: Cincinnati sports fan, Herd nation, Car person, Jersey nerd, A little of everything.
3. **Quick pick.** Yes / Nah cards, one topic at a time, for people who freeze at a blank box.

Then **Go deeper** (optional): children of each pick ("Cincinnati Reds" -> Big Red Machine, 1990 champions...).
Later: thumbs up/down after questions to steer, and "You aced 5 Reds questions. Unlock Big Red Machine?"

## 8. Accuracy before niche

- A question ships only with an https source, an explanation and a tidbit (`python -m trivia.content` enforces it).
- `status: draft` until a person opens the source and records `source.checked` (date) and `source.excerpt`
  (the passage that proves the answer). Production runs with `TRIVIA_SERVE_DRAFTS=0`: drafts never reach players.
- A requested topic opens only when enough questions pass a two-source check.
- "Challenge this fact" records a flag for review.

## 9. Delivery and what it costs

| Channel | Cost | Notes |
|---|---|---|
| App notification (web push) | Free | Android, and iPhone once the app is added to the home screen. Phase 2. |
| Email | Free tiers | Any SMTP provider. Built (`notify.Email`). |
| Text (Twilio) | About $0.0083 per text plus carrier fees (roughly 1.1-1.3 cents all-in), about $1.15/month per number, plus registration | Built (`notify.TwilioSMS`). US carriers require 10DLC or toll-free verification before delivery. Opt-in checkbox, STOP handling. |

There is no reliable free texting option: AT&T and T-Mobile have shut down their email-to-text gateways, and Verizon's
is scheduled to close. Rough math for texts: 100 players x 5 drops a week ~ 2,200 texts a month ~ $25-30.
Plan: launch on push + email (free), turn on texts once the number is registered.
Keep texts under 160 plain characters: one emoji drops the limit to 70 and doubles the cost (`sms_segments`).
