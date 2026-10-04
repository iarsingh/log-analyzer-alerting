# Log analyzer and alerting tool

Level: Beginner

Skills: Python, regex, logs, alert thresholds, secret redaction

Paste a log. Rules match lines, matches are grouped by rule, and a group fires only when it reaches its threshold.

| Rule | Matches | Severity | Fires at |
| --- | --- | --- | --- |
| `error` | the word `ERROR` | high | 1 |
| `server_error` | `status=5xx` (a 404 does not count) | high | 1 |
| `timeout` | the word `timeout` | medium | 1 |
| `slow_request` | `latency_ms=` of 1000 or more | low | 3 |

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn logalert.main:app --reload
```

```bash
curl -s -X POST localhost:8000/logs/analyze \
  -H 'content-type: application/json' \
  -d '{"text":"ERROR disk full\nstatus=503 upstream\n","min_severity":"medium"}'
```

The response has every match with its line number, a group per rule with a count and `firing`, and the list of firing rules. `GET /rules` lists the defaults.

## Your own rules

Send `rules` to replace the defaults for one request. Each rule needs a name, a pattern up to 200 characters, a severity of low, medium, or high, and a threshold of at least 1. A pattern that does not compile is refused with the reason.

## What it will not do

- Echo a secret. `password=`, `token=`, `secret=`, `api_key=`, bearer tokens, and AWS access key ids are redacted in the returned line.
- Page anyone. `paged` is always false.
- Store the log, or read more than 50,000 lines in one request.
