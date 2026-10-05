# log-analyzer-alerting — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does log-analyzer-alerting address, and what can you demonstrate?

Paste a log. Rules match lines, matches are grouped by rule, and a group fires only when it reaches its threshold.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/logalert/main.py`](src/logalert/main.py): Implementation or supporting configuration.
- [`src/logalert/rules.py`](src/logalert/rules.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`tests/test_rules.py`](tests/test_rules.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `analyze` and explain the decision it makes?

The main walkthrough here is `analyze(text, rules=DEFAULT_RULES, min_severity='low')` in [`src/logalert/rules.py`](src/logalert/rules.py#L65).

```python
def analyze(text, rules=DEFAULT_RULES, min_severity="low"):
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        raise RuleError(f"log has {len(lines)} lines; the limit is {MAX_LINES}")
    floor = SEVERITIES.index(min_severity)
    matches = []
    for number, line in enumerate(lines, start=1):
        for rule in rules:
            if SEVERITIES.index(rule.severity) < floor:
                continue
            if rule.pattern.search(line):
                matches.append({"line": number, "rule": rule.name, "severity": rule.severity, "text": redact(line.strip())})
    groups = {}
    for match in matches:
        group = groups.setdefault(match["rule"], {"rule": match["rule"], "severity": match["severity"], "count": 0, "first_line": match["line"]})
        group["count"] += 1
    thresholds = {rule.name: rule.threshold for rule in rules}
    alerts = []
    for group in groups.values():
        group["threshold"] = thresholds[group["rule"]]
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `RuleError`, `SEVERITIES.index`, `alerts.append`, `enumerate`, `groups.setdefault`, `groups.values`, `len`, `line.strip`, `matches.append`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `compile_rules` have?

`compile_rules(custom)` is defined in [`src/logalert/rules.py`](src/logalert/rules.py#L42).

Its return expressions include:

- `tuple(rules)`

It uses `', '.join`, `Rule`, `RuleError`, `int`, `item.get`, `len`, `re.compile`, `rules.append`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=str(exc))` in [`src/logalert/main.py`](src/logalert/main.py#L45).
- `RuleError(f'log has {len(lines)} lines; the limit is {MAX_LINES}')` in [`src/logalert/rules.py`](src/logalert/rules.py#L68).
- `RuleError('a rule needs a name')` in [`src/logalert/rules.py`](src/logalert/rules.py#L50).
- `RuleError(f'rule {name} pattern must be 1 to {MAX_PATTERN} characters')` in [`src/logalert/rules.py`](src/logalert/rules.py#L52).
- `RuleError(f"rule {name} severity must be one of {', '.join(SEVERITIES)}")` in [`src/logalert/rules.py`](src/logalert/rules.py#L54).
- `RuleError(f'rule {name} threshold must be at least 1')` in [`src/logalert/rules.py`](src/logalert/rules.py#L56).
- `RuleError(f'rule {name} pattern does not compile: {exc}')` in [`src/logalert/rules.py`](src/logalert/rules.py#L60).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_rules.py`](tests/test_rules.py#L13) contains `test_three_rules_fire_on_their_lines`:

```python
def test_three_rules_fire_on_their_lines():
    text = "INFO started\nERROR disk full\nstatus=503 upstream\nclient timeout after 30s\n"
    body = analyze(text).json()
    assert {item["rule"] for item in body["matches"]} == {"error", "server_error", "timeout"}
    assert body["count"] == 3
    assert body["paged"] is False
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/logalert/main.py`](src/logalert/main.py#L25).
- `GET /rules` → `list_rules` in [`src/logalert/main.py`](src/logalert/main.py#L30).
- `POST /logs/analyze` → `analyze_logs` in [`src/logalert/main.py`](src/logalert/main.py#L40).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. How would you investigate data ownership and persistence?

Trace the data/configuration files and the code that reads or writes them in the component table. Identify which files are examples, which records are mutable, and which external store is actually configured. I would document those facts before discussing retention, backup, or tenant isolation.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `analyze`?

In [`src/logalert/rules.py`](src/logalert/rules.py#L65), `analyze(text, rules=DEFAULT_RULES, min_severity='low')` receives the inputs. The function computes these intermediate values:

- `lines = text.splitlines()`
- `floor = SEVERITIES.index(min_severity)`
- `matches = []`
- `groups = {}`
- `thresholds = {rule.name: rule.threshold for rule in rules}`
- `alerts = []`
- `ordered = sorted(groups.values(), key=lambda group: (-SEVERITIES.index(group['severity']), group['first_line']))`

Its result is defined by:

- `{'lines': len(lines), 'matches': matches, 'count': len(matches), 'groups': ordered, 'firing': alerts, 'paged': False}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/logalert/rules.py`](src/logalert/rules.py#L65) branches on:

- `len(lines) > MAX_LINES`
- `group['firing']`
- `SEVERITIES.index(rule.severity) < floor`
- `rule.pattern.search(line)`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
