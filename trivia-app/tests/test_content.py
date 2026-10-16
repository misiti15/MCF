import copy

from trivia import content


def test_bank_passes_checks():
    lib, problems = content.load()
    assert problems == []
    assert len(lib.questions) >= 20


def test_every_question_has_tidbit_and_https_source(lib):
    for q in lib.questions.values():
        assert q["tidbit"] and q["explanation"]
        assert q["source"]["url"].startswith("https://")


def test_validator_catches_bad_questions(lib):
    q = copy.deepcopy(next(iter(lib.questions.values())))
    q["options"] = ["a", "a", "b", "c"]
    q["source"] = {"title": "x", "url": "http://insecure"}
    q["status"] = "verified"
    problems = " ".join(content.validate_question(q, lib.topics))
    for word in ("duplicate options", "https", "checked", "excerpt"):
        assert word in problems


def test_drafts_hidden_when_serving_drafts_off(lib, monkeypatch):
    monkeypatch.setattr(content.config, "SERVE_DRAFTS", False)
    assert lib.questions_for(["sports"]) == []
