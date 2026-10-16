"""Send today's drop to everyone whose send time has passed. Run every 15 minutes (cron, or a hosted scheduler).

    python -m trivia.scheduler            # send what's due
    python -m trivia.scheduler --dry-run  # show what would be sent
"""
from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, db, game, notify
from .content import library

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def due(user: dict, at: datetime) -> bool:
    local = at.astimezone(ZoneInfo(user["tz"]))
    if DAYS[local.weekday()] not in user["send_days"]:
        return False
    return local.strftime("%H:%M") >= user["send_time"]


def run(con, at: datetime | None = None, dry_run: bool = False, console: notify.Console | None = None) -> list[dict]:
    lib = library()
    at = at or datetime.now(ZoneInfo("UTC"))
    out = []
    for user in db.all_users(con):
        if not user["topics"] or not due(user, at):
            continue
        day = game.today_for(user, at)
        row = con.execute("SELECT sent_at FROM drops WHERE user_id=? AND day=?", [user["id"], day]).fetchone()
        if row and row["sent_at"]:
            continue
        try:
            game.get_or_build_drop(con, lib, user, day)
        except game.GameError as e:
            out.append({"user": user["id"], "skipped": str(e)})
            continue
        link = f"{config.PUBLIC_URL}/d/{user['token']}"
        text = notify.drop_message(user, [lib.topics[t].name for t in user["topics"] if t in lib.topics], link)
        result = {"user": user["id"], "channel": user["channel"], "text": text, "segments": notify.sms_segments(text)}
        if not dry_run:
            try:
                result["provider_id"] = notify.provider_for(user, console).send(user, text)
                con.execute("UPDATE drops SET sent_at=? WHERE user_id=? AND day=?", [db.now(), user["id"], day])
                con.commit()
            except Exception as e:  # one bad number must not stop everyone else's drop
                result["error"] = type(e).__name__
        out.append(result)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for r in run(db.connect(), dry_run=args.dry_run):
        print(r)


if __name__ == "__main__":
    main()
