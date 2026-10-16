"""Every product decision that might change lives here, so a rename or a rule change is one edit."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = Path(os.environ.get("TRIVIA_CONTENT_DIR", ROOT / "content"))
WEB_DIR = ROOT / "web"
DB_PATH = Path(os.environ.get("TRIVIA_DB", ROOT / "data" / "trivia.sqlite"))

# Working codename. Pick the final brand, change this one string (and the repo name).
BRAND = os.environ.get("TRIVIA_BRAND", "Deep Cut")
PUBLIC_URL = os.environ.get("TRIVIA_PUBLIC_URL", "http://localhost:8000")

# Serve questions whose sources a person has not checked yet. On for development only.
SERVE_DRAFTS = os.environ.get("TRIVIA_SERVE_DRAFTS", "1") == "1"

LEVEL_POINTS = {1: 100, 2: 200, 3: 300, 4: 500}

# Level-name themes. The user can pick one in settings; colors never change (green, gold, orange, magenta).
LEVEL_THEMES = {
    "fan":      ["Bandwagon", "Season Ticket", "Die-Hard", "Superfan"],
    "record":   ["Radio Hit", "B-Side", "Rare Groove", "Deep Cut"],
    "spicy":    ["Mild", "Medium", "Hot", "Ghost Pepper"],
    "gut":      ["Gimme", "Hold Up...", "Sweat Zone", "Oh, Come ON"],
    "odds":     ["Easy Money", "Coin Flip", "Long Shot", "Hail Mary"],
    "garage":   ["Cruise Control", "Fast Lane", "Redline", "Full Send"],
    "brain":    ["No-Brainer", "Brain Teaser", "Brain Buster", "Brain Melter"],
}
DEFAULT_LEVEL_THEME = "fan"

# Daily drop: 3-5 questions. Order of difficulty for the "ramp" mix.
DROP_SIZES = (3, 4, 5)
DEFAULT_DROP_SIZE = 3
RAMPS = {3: [1, 2, 3], 4: [1, 2, 3, 4], 5: [1, 2, 3, 3, 4]}
PERFECT_DROP_BONUS = 100

# "Give me one more": bonus questions after the drop.
# They count toward level accuracy, earn no daily-score points, and never break a streak.
# Capped so niche topics don't run out of questions in a week.
BONUS_PER_DAY = 3

# Answer-streak multipliers (drop questions only).
STREAK_MULTIPLIERS = ((5, 2.0), (3, 1.5))
