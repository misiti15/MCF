import pytest
from fastapi.testclient import TestClient

from trivia import api, db
from trivia.content import library


@pytest.fixture
def con():
    return db.connect(":memory:")


@pytest.fixture
def lib():
    return library()


@pytest.fixture
def client(con, monkeypatch):
    monkeypatch.setattr(api, "_con", con)
    return TestClient(api.app)


@pytest.fixture
def user(con):
    return db.create_user(con, ["reds", "marshall", "jerseys", "exotic"], drop_size=3)
