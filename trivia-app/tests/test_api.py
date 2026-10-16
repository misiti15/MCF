def signup(client, **extra):
    r = client.post("/api/users", json={"topics": ["reds", "marshall"], "drop_size": 3} | extra)
    assert r.status_code == 200, r.text
    return {"X-User-Token": r.json()["token"]}


def test_full_round(client):
    h = signup(client)
    drop = client.get("/api/drop/today", headers=h).json()
    assert len(drop["questions"]) == 3 and "answer" not in drop["questions"][0]
    assert client.post("/api/one-more", headers=h).status_code == 409
    for q in drop["questions"]:
        r = client.post("/api/answer", headers=h, json={"question_id": q["id"], "choice": 0}).json()
        assert "tidbit" in r and "answer_text" in r
    assert client.get("/api/drop/today", headers=h).json()["complete"]
    bonus = client.post("/api/one-more", headers=h).json()
    assert bonus["kind"] == "bonus"
    stats = client.get("/api/stats", headers=h).json()
    assert set(stats["levels"]) == {"1", "2", "3", "4"}


def test_auth_required(client):
    assert client.get("/api/drop/today").status_code == 401
    assert client.get("/api/drop/today", headers={"X-User-Token": "nope"}).status_code == 401


def test_validation(client):
    assert client.post("/api/users", json={"topics": ["nope"]}).status_code == 400
    assert client.post("/api/users", json={"topics": ["reds"], "drop_size": 20}).status_code == 422
    assert client.post("/api/users", json={"topics": ["reds"], "phone": "555"}).status_code == 422


def test_search_and_requests(client):
    m = client.get("/api/topics/search", params={"q": "big red machine"}).json()["matches"]
    assert m[0]["id"] == "brm"
    assert client.post("/api/requests", json={"text": "Cincinnati Reds"}).json()["queued"] is False
    assert client.post("/api/requests", json={"text": "1950s Belgian cyclocross"}).json()["queued"] is True


def test_sms_webhook_rejects_unsigned(client, monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
    assert client.post("/api/sms/inbound", data={"Body": "STOP"}).status_code == 403


def test_web_app_served(client):
    assert client.get("/").status_code == 200
    assert client.get("/d/sometoken").status_code == 200
