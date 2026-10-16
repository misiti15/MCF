import pytest

from trivia import topics


@pytest.mark.parametrize("text,expected", [
    ("Cincinnati Reds", "reds"),
    ("big red machine", "brm"),
    ("herd football", "herd-fb"),
    ("Marshall University", "marshall"),
    ("lambos", "lambo"),
    ("koenigseg", "koenigsegg"),          # typo
    ("US professional sports jerseys", "jerseys"),
    ("exotic cars", "exotic"),
    ("We Are Marshall", "crash-1970"),
])
def test_free_text_finds_topic(lib, text, expected):
    found = topics.match(lib, text)
    assert found and found[0]["id"] == expected, found


def test_unknown_niche_has_no_confident_match(lib):
    found = topics.match(lib, "1950s Belgian cyclocross")
    assert not found or not found[0]["confident"]


def test_deeper_lists_children(lib):
    kids = [k["id"] for k in topics.suggest_deeper(lib, "reds")]
    assert "brm" in kids and "reds-90" in kids
