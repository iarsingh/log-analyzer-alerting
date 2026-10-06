# Log analyzer and alerting tool

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/logalert/main.py`](src/logalert/main.py) | HTTP handlers: `GET /healthz`, `GET /rules`, `POST /logs/analyze` |
| [`src/logalert/rules.py`](src/logalert/rules.py) | Functions: `redact`, `compile_rules`, `analyze` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`tests/test_rules.py`](tests/test_rules.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn logalert.main:app --reload
```

<!-- project-guide:end -->

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

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.

## Documentation checks

Project architecture, interview guides, and local source links are checked automatically on pushes and pull requests. Run the same check locally:

```bash
python3 .github/scripts/validate_project_docs.py
```

See [service improvements and local run instructions](docs/UPGRADES.md).
