"""HTTP API plus the web app. Run: uvicorn trivia.api:app --reload"""
from __future__ import annotations

import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, db, game, notify, topics
from .content import library

app = FastAPI(title=f"{config.BRAND} API")
_con = None


def con():
    global _con
    if _con is None:
        _con = db.connect()
    return _con


def lib():
    return library()


@app.exception_handler(game.GameError)
def _game_error(_, e: game.GameError):
    return JSONResponse({"detail": str(e)}, status_code=e.status)


def me(x_user_token: str = Header(default="")) -> dict:
    user = db.user_by_token(con(), x_user_token) if x_user_token else None
    if not user:
        raise HTTPException(401, "Sign in again from your latest drop link.")
    return user


Channel = Literal["push", "sms", "email"]
Mix = Literal["ramp", "mix", "deep"]


class Settings(BaseModel):
    name: str | None = Field(None, max_length=40)
    phone: str | None = Field(None, pattern=r"^\+[1-9]\d{7,14}$")
    email: str | None = Field(None, max_length=120)
    channel: Channel | None = None
    drop_size: int | None = Field(None, ge=min(config.DROP_SIZES), le=max(config.DROP_SIZES))
    mix: Mix | None = None
    send_days: list[Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]] | None = None
    send_time: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    tz: str | None = None
    level_theme: str | None = None
    sms_opt_in: bool | None = None


class NewUser(Settings):
    topics: list[str] = Field(min_length=1, max_length=25)


def _check_topics(ids: list[str]) -> list[str]:
    bad = [t for t in ids if t not in lib().topics]
    if bad:
        raise HTTPException(400, f"Unknown topics: {', '.join(bad)}")
    return list(dict.fromkeys(ids))


def _check_settings(s: Settings) -> dict:
    data = s.model_dump(exclude_none=True, exclude={"topics"})
    if "level_theme" in data and data["level_theme"] not in config.LEVEL_THEMES:
        raise HTTPException(400, "Unknown level theme.")
    if "tz" in data:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            ZoneInfo(data["tz"])
        except (ZoneInfoNotFoundError, ValueError):
            raise HTTPException(400, "Unknown time zone.")
    if "sms_opt_in" in data:
        data["sms_opt_in"] = int(data["sms_opt_in"])
    return data


@app.get("/api/config")
def get_config():
    return {"brand": config.BRAND, "level_points": config.LEVEL_POINTS, "level_themes": config.LEVEL_THEMES,
            "default_level_theme": config.DEFAULT_LEVEL_THEME, "drop_sizes": config.DROP_SIZES,
            "bonus_per_day": config.BONUS_PER_DAY, "perfect_drop_bonus": config.PERFECT_DROP_BONUS,
            "ramps": config.RAMPS, "streak_multipliers": config.STREAK_MULTIPLIERS}


@app.get("/api/topics")
def get_topics():
    L = lib()
    return {"tree": topics.tree(L), "packs": [p | {"questions": len(L.questions_for(p["topics"]))} for p in L.packs]}


@app.get("/api/topics/search")
def search_topics(q: str):
    return {"query": q, "matches": topics.match(lib(), q[:80])}


@app.get("/api/topics/{topic_id}/deeper")
def deeper(topic_id: str):
    if topic_id not in lib().topics:
        raise HTTPException(404, "Unknown topic.")
    return {"kids": topics.suggest_deeper(lib(), topic_id)}


@app.post("/api/users")
def create_user(body: NewUser):
    user = db.create_user(con(), _check_topics(body.topics), **_check_settings(body))
    return {"token": user["token"], "user": _public_user(user)}


def _public_user(u: dict) -> dict:
    return {k: v for k, v in u.items() if k not in ("token",)}


@app.get("/api/me")
def get_me(user=Depends(me)):
    return _public_user(user)


@app.patch("/api/me")
def patch_me(body: Settings, user=Depends(me)):
    return _public_user(db.update_user(con(), user["id"], **_check_settings(body)))


class TopicList(BaseModel):
    topics: list[str] = Field(min_length=1, max_length=25)


@app.put("/api/me/topics")
def put_topics(body: TopicList, user=Depends(me)):
    db.set_topics(con(), user["id"], _check_topics(body.topics))
    return {"topics": db.get_user(con(), user["id"])["topics"]}


@app.get("/api/drop/today")
def today(user=Depends(me)):
    return game.drop_state(con(), lib(), user, game.today_for(user))


class Answer(BaseModel):
    question_id: str
    choice: int


@app.post("/api/answer")
def post_answer(body: Answer, user=Depends(me)):
    return game.answer(con(), lib(), user, body.question_id, body.choice, game.today_for(user))


@app.post("/api/one-more")
def post_one_more(user=Depends(me)):
    return game.one_more(con(), lib(), user, game.today_for(user))


@app.get("/api/stats")
def get_stats(user=Depends(me)):
    return game.stats(con(), user, game.today_for(user))


class TopicRequest(BaseModel):
    text: str = Field(min_length=2, max_length=80)


@app.post("/api/requests")
def request_topic(body: TopicRequest, x_user_token: str = Header(default="")):
    """Free-text topic box: return matches; queue it for research when nothing fits well."""
    matches = topics.match(lib(), body.text)
    if matches and matches[0]["confident"] and not matches[0]["soon"]:
        return {"queued": False, "matches": matches}
    user = db.user_by_token(con(), x_user_token) if x_user_token else None
    con().execute("INSERT INTO topic_requests (user_id, text, created_at) VALUES (?,?,?)",
                  [user and user["id"], body.text.strip(), db.now()])
    con().commit()
    return {"queued": True, "matches": matches,
            "status": "Researching. It opens once enough questions pass two-source checks."}


class Flag(BaseModel):
    question_id: str
    note: str | None = Field(None, max_length=500)


@app.post("/api/flags")
def flag(body: Flag, user=Depends(me)):
    if body.question_id not in lib().questions:
        raise HTTPException(404, "Unknown question.")
    con().execute("INSERT INTO flags (user_id, question_id, note, created_at) VALUES (?,?,?,?)",
                  [user["id"], body.question_id, body.note, db.now()])
    con().commit()
    return {"ok": True, "message": "Thanks. A person will re-check this one against its sources."}


STOP_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit"}
START_WORDS = {"start", "yes", "unstop"}


@app.post("/api/sms/inbound")
async def sms_inbound(request: Request):
    """Twilio webhook for replies. Handles STOP/START so opt-outs are honored on our side too."""
    form = {k: str(v) for k, v in (await request.form()).items()}
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not token or not notify.twilio_signature_ok(token, str(request.url), form, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(403, "Bad signature.")
    word = form.get("Body", "").strip().lower()
    phone = form.get("From", "")
    if word in STOP_WORDS:
        con().execute("UPDATE users SET sms_opt_in=0 WHERE phone=?", [phone])
    elif word in START_WORDS:
        con().execute("UPDATE users SET sms_opt_in=1 WHERE phone=?", [phone])
    con().commit()
    return PlainTextResponse("<Response/>", media_type="application/xml")


@app.get("/d/{token}")
def drop_link(token: str):
    """The link inside each text/notification. The page reads the token from the URL."""
    return FileResponse(config.WEB_DIR / "index.html")


app.mount("/", StaticFiles(directory=config.WEB_DIR, html=True), name="web")
