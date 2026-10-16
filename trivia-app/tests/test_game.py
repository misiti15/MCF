import pytest

from trivia import config, game

DAY = "2026-10-16"


def finish_drop(con, lib, user, right=True):
    out = []
    for qid in game.get_or_build_drop(con, lib, user, DAY):
        q = lib.questions[qid]
        choice = q["answer"] if right else (q["answer"] + 1) % 4
        out.append(game.answer(con, lib, user, qid, choice, DAY))
    return out


@pytest.mark.parametrize("size", config.DROP_SIZES)
def test_drop_size_and_ramp(con, lib, user, size):
    user["drop_size"] = size
    ids = game.get_or_build_drop(con, lib, user, DAY)
    levels = [lib.questions[i]["level"] for i in ids]
    assert len(ids) == size == len(set(ids))
    assert levels == sorted(levels) and levels[0] == 1


def test_drop_is_stable_for_the_day_and_spreads_topics(con, lib, user):
    user["drop_size"] = 4
    a = game.get_or_build_drop(con, lib, user, DAY)
    assert a == game.get_or_build_drop(con, lib, user, DAY)
    owners = {game._owner(lib, user["topics"], lib.questions[i]) for i in a}
    assert len(owners) == 4


def test_no_repeats_until_bank_runs_out(con, lib, user):
    seen = []
    for d in range(1, 8):
        seen += game.get_or_build_drop(con, lib, user, f"2026-10-{d:02d}")
    assert len(set(seen[:21])) == 21


def test_public_question_hides_answer(lib):
    q = next(iter(lib.questions.values()))
    p = game.public(q, lib, "drop")
    assert "answer" not in p and "tidbit" not in p and "explanation" not in p


def test_answer_reveals_answer_and_tidbit(con, lib, user):
    r = finish_drop(con, lib, user)[0]
    assert r["correct"] and r["answer_text"] and r["tidbit"] and r["source"]["url"]


def test_scoring_streaks_and_perfect_bonus(con, lib, user):
    user["drop_size"] = 3
    results = finish_drop(con, lib, user)
    levels = [lib.questions[i]["level"] for i in game.get_or_build_drop(con, lib, user, DAY)]
    pts = config.LEVEL_POINTS
    expected = pts[levels[0]] + pts[levels[1]] + round(pts[levels[2]] * 1.5)
    assert [r["points"] for r in results] == [pts[levels[0]], pts[levels[1]], round(pts[levels[2]] * 1.5)]
    assert results[-1]["perfect_drop"]
    assert game.day_score(con, user["id"], DAY) == expected + config.PERFECT_DROP_BONUS


def test_wrong_answer_resets_streak(con, lib, user):
    results = finish_drop(con, lib, user, right=False)
    assert all(r["points"] == 0 and r["streak"] == 0 for r in results)
    assert not results[-1]["perfect_drop"]


def test_cannot_answer_twice_or_outside_drop(con, lib, user):
    qid = game.get_or_build_drop(con, lib, user, DAY)[0]
    game.answer(con, lib, user, qid, 0, DAY)
    with pytest.raises(game.GameError) as e:
        game.answer(con, lib, user, qid, 0, DAY)
    assert e.value.status == 409
    outside = next(i for i in lib.questions if i not in game.get_or_build_drop(con, lib, user, DAY))
    with pytest.raises(game.GameError) as e:
        game.answer(con, lib, user, outside, 0, DAY)
    assert e.value.status == 403


def test_one_more_rules(con, lib, user):
    with pytest.raises(game.GameError):
        game.one_more(con, lib, user, DAY)            # drop not finished
    finish_drop(con, lib, user)
    before = game.day_score(con, user["id"], DAY)
    streak = game.current_streak(con, user["id"])
    for _ in range(config.BONUS_PER_DAY):
        q = game.one_more(con, lib, user, DAY)
        assert q["kind"] == "bonus"
        assert game.one_more(con, lib, user, DAY)["id"] == q["id"]   # unanswered bonus comes back
        r = game.answer(con, lib, user, q["id"], (lib.questions[q["id"]]["answer"] + 1) % 4, DAY)  # wrong on purpose
        assert r["points"] == 0
    assert game.day_score(con, user["id"], DAY) == before           # bonus never changes the daily score
    assert game.current_streak(con, user["id"]) == streak           # and never breaks the streak
    with pytest.raises(game.GameError) as e:
        game.one_more(con, lib, user, DAY)
    assert e.value.status == 429
    s = game.stats(con, user, DAY)
    assert sum(v["answered"] for v in s["levels"].values()) == 3 + config.BONUS_PER_DAY  # bonus counts for accuracy


def test_day_streak(con, lib, user):
    for d in ("2026-10-14", "2026-10-15", "2026-10-16"):
        for qid in game.get_or_build_drop(con, lib, user, d):
            game.answer(con, lib, user, qid, 0, d)
    assert game.stats(con, user, "2026-10-16")["day_streak"] == 3
    assert game.stats(con, user, "2026-10-17")["day_streak"] == 3   # today not played yet
    assert game.stats(con, user, "2026-10-18")["day_streak"] == 0
