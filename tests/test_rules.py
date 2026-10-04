from fastapi.testclient import TestClient

from logalert.main import app
from logalert.rules import redact

client = TestClient(app)


def analyze(text, **extra):
    return client.post("/logs/analyze", json={"text": text, **extra})


def test_three_rules_fire_on_their_lines():
    text = "INFO started\nERROR disk full\nstatus=503 upstream\nclient timeout after 30s\n"
    body = analyze(text).json()
    assert {item["rule"] for item in body["matches"]} == {"error", "server_error", "timeout"}
    assert body["count"] == 3
    assert body["paged"] is False


def test_status_404_is_not_a_server_error():
    assert analyze("status=404 not found\n").json()["count"] == 0


def test_slow_requests_need_three_before_firing():
    two = "latency_ms=1500\nlatency_ms=2200\n"
    body = analyze(two).json()
    assert body["groups"][0]["count"] == 2
    assert body["firing"] == []
    body = analyze(two + "latency_ms=1800\n").json()
    assert body["firing"] == ["slow_request"]


def test_groups_are_ordered_by_severity_then_first_line():
    text = "client timeout\nERROR boom\nERROR again\n"
    groups = analyze(text).json()["groups"]
    assert [group["rule"] for group in groups] == ["error", "timeout"]
    assert groups[0]["count"] == 2
    assert groups[0]["first_line"] == 2


def test_min_severity_drops_low_and_medium():
    text = "client timeout\nERROR boom\n"
    body = analyze(text, min_severity="high").json()
    assert [match["rule"] for match in body["matches"]] == ["error"]


def test_secrets_are_redacted_in_the_response():
    text = "ERROR login failed password=hunter2 token=abc.def\nERROR auth Bearer eyJhbGciOi.payload.sig\n"
    lines = [match["text"] for match in analyze(text).json()["matches"]]
    assert "hunter2" not in " ".join(lines)
    assert "password=[redacted]" in lines[0]
    assert "Bearer" not in lines[1]


def test_aws_access_key_is_redacted():
    assert redact("key AKIAABCDEFGHIJKLMNOP leaked") == "key [redacted] leaked"


def test_custom_rule_replaces_the_defaults():
    rules = [{"name": "oom", "pattern": "OOMKilled", "severity": "high"}]
    body = analyze("ERROR ignored\npod OOMKilled\n", rules=rules).json()
    assert [match["rule"] for match in body["matches"]] == ["oom"]


def test_custom_rule_that_does_not_compile_is_refused():
    rules = [{"name": "bad", "pattern": "([unclosed", "severity": "high"}]
    response = analyze("x\n", rules=rules)
    assert response.status_code == 422
    assert "does not compile" in response.json()["detail"]


def test_rules_endpoint_lists_defaults():
    names = [rule["name"] for rule in client.get("/rules").json()["rules"]]
    assert names == ["error", "server_error", "timeout", "slow_request"]
