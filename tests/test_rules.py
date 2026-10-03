from fastapi.testclient import TestClient

from logalert.main import app

client = TestClient(app)


def test_three_rules_fire_on_their_lines():
    text = "INFO started\nERROR disk full\nstatus=503 upstream\nclient timeout after 30s\n"
    body = client.post("/logs/analyze", json={"text": text}).json()
    rules = {item["rule"] for item in body["alerts"]}
    assert rules == {"error", "server_error", "timeout"}
    assert body["count"] == 3
