"""Daily drops, "one more" bonus questions, answering and scoring.

Scoring rules (see docs/DECISIONS.md):
- Drop questions earn level points x streak multiplier, plus a bonus for a perfect drop.
- Bonus ("one more") questions count toward level accuracy, earn no points,
  and never break or extend the answer streak. Capped at config.BONUS_PER_DAY.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config
from .content import Library
from .db import now


class GameError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def today_for(user: dict, at: datetime | None = None) -> str:
    at = at or datetime.now(ZoneInfo("UTC"))
    return at.astimezone(ZoneInfo(user["tz"])).date().isoformat()


def public(q: dict, lib: Library, kind: str) -> dict:
    """What the client sees before answering: never the answer."""
    return {
        "id": q["id"], "kind": kind, "level": q["level"], "points": config.LEVEL_POINTS[q["level"]],
        "question": q["question"], "options": q["options"], "image": q.get("image"),
        "topic": [lib.topics[t].name for t in lib.lineage(q["topic"])][-2:],
    }


def _seen(con, uid: str) -> dict[str, str]:
    """question_id -> last day it was shown (drops and bonuses)."""
    seen = {}
    for day, ids in con.execute("SELECT day, question_ids FROM drops WHERE user_id=?", [uid]):
        for qid in json.loads(ids):
            seen[qid] = max(day, seen.get(qid, ""))
    for day, qid in con.execute("SELECT day, question_id FROM bonus WHERE user_id=?", [uid]):
        seen[qid] = max(day, seen.get(qid, ""))
    return seen


def _owner(lib: Library, user_topics: list[str], q: dict) -> str:
    """Which of the user's picked topics this question belongs to, for spreading a drop across topics."""
    line = lib.lineage(q["topic"])
    return next((t for t in user_topics if t in line), q["topic"])


def _pick(lib, user, pool, seen, levels, rng) -> list[dict]:
    unseen = [q for q in pool if q["id"] not in seen]
    # Oldest-seen first once someone has played through their topics.
    reruns = sorted((q for q in pool if q["id"] in seen), key=lambda q: seen[q["id"]])
    chosen, used_topics = [], {}
    for want in levels:
        for bucket in (unseen, reruns):
            left = [q for q in bucket if q not in chosen]
            if not left:
                continue
            closest = min(abs(q["level"] - want) for q in left)
            cands = [q for q in left if abs(q["level"] - want) == closest]
            fewest = min(used_topics.get(_owner(lib, user["topics"], q), 0) for q in cands)
            cands = [q for q in cands if used_topics.get(_owner(lib, user["topics"], q), 0) == fewest]
            if bucket is reruns:
                cands = cands[:1]
            q = rng.choice(cands)
            chosen.append(q)
            o = _owner(lib, user["topics"], q)
            used_topics[o] = used_topics.get(o, 0) + 1
            break
    # Keep the ramp feeling: easiest first.
    return sorted(chosen, key=lambda q: q["level"]) if user["mix"] == "ramp" else chosen


def target_levels(user: dict, rng: random.Random) -> list[int]:
    n = user["drop_size"]
    if user["mix"] == "deep":
        return [4] * n
    if user["mix"] == "mix":
        return [rng.randint(1, 4) for _ in range(n)]
    return list(config.RAMPS[n])


def get_or_build_drop(con, lib: Library, user: dict, day: str) -> list[str]:
    row = con.execute("SELECT question_ids FROM drops WHERE user_id=? AND day=?", [user["id"], day]).fetchone()
    if row:
        return json.loads(row[0])
    pool = lib.questions_for(user["topics"])
    if not pool:
        raise GameError("No questions for your topics yet. Add a topic with questions, or wait for a requested topic to open.", 404)
    rng = random.Random(f"{user['id']}:{day}")
    picked = _pick(lib, user, pool, _seen(con, user["id"]), target_levels(user, rng), rng)
    ids = [q["id"] for q in picked]
    con.execute("INSERT INTO drops (user_id, day, question_ids) VALUES (?,?,?)", [user["id"], day, json.dumps(ids)])
    con.commit()
    return ids


def _answers(con, uid: str, day: str | None = None) -> dict[str, dict]:
    sql, args = "SELECT * FROM answers WHERE user_id=?", [uid]
    if day:
        sql, args = sql + " AND day=?", args + [day]
    return {r["question_id"] + "|" + r["day"]: dict(r) for r in con.execute(sql + " ORDER BY id", args)}


def drop_state(con, lib: Library, user: dict, day: str) -> dict:
    ids = get_or_build_drop(con, lib, user, day)
    done = {a["question_id"]: a for a in _answers(con, user["id"], day).values() if a["kind"] == "drop"}
    bonus_used = con.execute("SELECT COUNT(*) FROM bonus WHERE user_id=? AND day=?", [user["id"], day]).fetchone()[0]
    return {
        "day": day,
        "questions": [public(lib.questions[i], lib, "drop") | ({"answered": _reveal(lib.questions[i], done[i])} if i in done else {}) for i in ids],
        "complete": all(i in done for i in ids),
        "score": day_score(con, user["id"], day),
        "bonus_left": max(0, config.BONUS_PER_DAY - bonus_used),
    }


def _reveal(q: dict, a: dict) -> dict:
    return {
        "choice": a["choice"], "correct": bool(a["correct"]), "answer": q["answer"],
        "answer_text": q["options"][q["answer"]], "explanation": q["explanation"], "tidbit": q["tidbit"],
        "source": {"title": q["source"]["title"], "url": q["source"]["url"]}, "points": a["points"],
    }


def current_streak(con, uid: str) -> int:
    streak = 0
    for (correct,) in con.execute("SELECT correct FROM answers WHERE user_id=? AND kind='drop' ORDER BY id DESC", [uid]):
        if not correct:
            break
        streak += 1
    return streak


def multiplier(streak: int) -> float:
    return next((m for n, m in config.STREAK_MULTIPLIERS if streak >= n), 1.0)


def answer(con, lib: Library, user: dict, qid: str, choice: int, day: str) -> dict:
    if qid not in lib.questions:
        raise GameError("Unknown question.", 404)
    drop_ids = get_or_build_drop(con, lib, user, day)
    is_bonus = con.execute("SELECT 1 FROM bonus WHERE user_id=? AND day=? AND question_id=?", [user["id"], day, qid]).fetchone()
    if qid in drop_ids:
        kind = "drop"
    elif is_bonus:
        kind = "bonus"
    else:
        raise GameError("That question isn't in today's drop.", 403)
    if con.execute("SELECT 1 FROM answers WHERE user_id=? AND question_id=? AND day=?", [user["id"], qid, day]).fetchone():
        raise GameError("Already answered.", 409)
    q = lib.questions[qid]
    if not isinstance(choice, int) or not 0 <= choice < len(q["options"]):
        raise GameError("Pick one of the four options.")
    correct = choice == q["answer"]
    streak = current_streak(con, user["id"])
    points = 0
    if kind == "drop":
        streak = streak + 1 if correct else 0
        if correct:
            points = round(config.LEVEL_POINTS[q["level"]] * multiplier(streak))
    con.execute("INSERT INTO answers (user_id, question_id, day, kind, level, choice, correct, points, answered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                [user["id"], qid, day, kind, q["level"], choice, int(correct), points, now()])
    con.commit()
    state = drop_state(con, lib, user, day)
    perfect = kind == "drop" and state["complete"] and all(x["answered"]["correct"] for x in state["questions"])
    return _reveal(q, {"choice": choice, "correct": correct, "points": points}) | {
        "kind": kind, "streak": streak, "multiplier": multiplier(streak) if kind == "drop" else None,
        "drop_complete": state["complete"], "perfect_drop": perfect, "day_score": state["score"],
        "bonus_left": state["bonus_left"],
    }


def one_more(con, lib: Library, user: dict, day: str) -> dict:
    state = drop_state(con, lib, user, day)
    if not state["complete"]:
        raise GameError("Finish today's drop first.", 409)
    # A bonus question waiting to be answered comes back instead of a new one.
    pending = con.execute("""SELECT b.question_id FROM bonus b LEFT JOIN answers a
        ON a.user_id=b.user_id AND a.question_id=b.question_id AND a.day=b.day
        WHERE b.user_id=? AND b.day=? AND a.id IS NULL""", [user["id"], day]).fetchone()
    if pending:
        return public(lib.questions[pending[0]], lib, "bonus") | {"bonus_left": state["bonus_left"]}
    if state["bonus_left"] <= 0:
        raise GameError(f"That's all {config.BONUS_PER_DAY} bonus questions for today. New drop tomorrow.", 429)
    rng = random.Random(f"{user['id']}:{day}:bonus:{state['bonus_left']}")
    pool = lib.questions_for(user["topics"])
    picked = _pick(lib, user | {"mix": "mix"}, pool, _seen(con, user["id"]), [rng.randint(1, 4)], rng)
    if not picked:
        raise GameError("No more questions for your topics right now.", 404)
    q = picked[0]
    con.execute("INSERT INTO bonus VALUES (?,?,?)", [user["id"], day, q["id"]])
    con.commit()
    return public(q, lib, "bonus") | {"bonus_left": state["bonus_left"] - 1}


def day_score(con, uid: str, day: str) -> int:
    rows = con.execute("SELECT correct, points FROM answers WHERE user_id=? AND day=? AND kind='drop'", [uid, day]).fetchall()
    drop = con.execute("SELECT question_ids FROM drops WHERE user_id=? AND day=?", [uid, day]).fetchone()
    total = sum(r["points"] for r in rows)
    if drop and len(rows) == len(json.loads(drop[0])) and rows and all(r["correct"] for r in rows):
        total += config.PERFECT_DROP_BONUS
    return total


def stats(con, user: dict, today: str) -> dict:
    uid = user["id"]
    levels = {}
    for lvl in config.LEVEL_POINTS:
        r = con.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM answers WHERE user_id=? AND level=?", [uid, lvl]).fetchone()
        levels[lvl] = {"answered": r[0], "correct": r[1], "accuracy": round(r[1] / r[0], 3) if r[0] else None}
    days = [r[0] for r in con.execute("SELECT DISTINCT day FROM answers WHERE user_id=? AND kind='drop' ORDER BY day", [uid])]
    total = sum(day_score(con, uid, d) for d in days)
    # Day streak: consecutive days with a finished drop, ending today or yesterday.
    finished = {d for d in days if drop_finished(con, uid, d)}
    streak_days, d = 0, date.fromisoformat(today)
    if d.isoformat() not in finished:
        d -= timedelta(days=1)
    while d.isoformat() in finished:
        streak_days += 1
        d -= timedelta(days=1)
    best = run = 0
    for (c,) in con.execute("SELECT correct FROM answers WHERE user_id=? AND kind='drop' ORDER BY id", [uid]):
        run = run + 1 if c else 0
        best = max(best, run)
    return {"levels": levels, "total_points": total, "today": day_score(con, uid, today),
            "day_streak": streak_days, "answer_streak": current_streak(con, uid), "best_answer_streak": best}


def drop_finished(con, uid: str, day: str) -> bool:
    drop = con.execute("SELECT question_ids FROM drops WHERE user_id=? AND day=?", [uid, day]).fetchone()
    if not drop:
        return False
    n = con.execute("SELECT COUNT(*) FROM answers WHERE user_id=? AND day=? AND kind='drop'", [uid, day]).fetchone()[0]
    return n == len(json.loads(drop[0]))
