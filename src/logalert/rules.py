import re
from dataclasses import dataclass

MAX_PATTERN = 200
MAX_LINES = 50000


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern
    severity: str
    threshold: int = 1


DEFAULT_RULES = (
    Rule("error", re.compile(r"\bERROR\b", re.I), "high"),
    Rule("server_error", re.compile(r"\bstatus=(5\d\d)\b"), "high"),
    Rule("timeout", re.compile(r"\btimeout\b", re.I), "medium"),
    Rule("slow_request", re.compile(r"\blatency_ms=(\d{4,})\b"), "low", threshold=3),
)

SECRETS = (
    re.compile(r"(?i)\b(password|passwd|secret|token|api_key)=\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)

SEVERITIES = ("low", "medium", "high")


class RuleError(ValueError):
    pass


def redact(line):
    for pattern in SECRETS:
        line = pattern.sub(lambda match: match.group(0).split("=")[0] + "=[redacted]" if "=" in match.group(0) else "[redacted]", line)
    return line


def compile_rules(custom):
    rules = []
    for item in custom:
        name = str(item.get("name", "")).strip()
        source = str(item.get("pattern", ""))
        severity = item.get("severity", "medium")
        threshold = int(item.get("threshold", 1))
        if not name:
            raise RuleError("a rule needs a name")
        if not source or len(source) > MAX_PATTERN:
            raise RuleError(f"rule {name} pattern must be 1 to {MAX_PATTERN} characters")
        if severity not in SEVERITIES:
            raise RuleError(f"rule {name} severity must be one of {', '.join(SEVERITIES)}")
        if threshold < 1:
            raise RuleError(f"rule {name} threshold must be at least 1")
        try:
            pattern = re.compile(source)
        except re.error as exc:
            raise RuleError(f"rule {name} pattern does not compile: {exc}") from exc
        rules.append(Rule(name, pattern, severity, threshold))
    return tuple(rules)


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
        group["firing"] = group["count"] >= group["threshold"]
        if group["firing"]:
            alerts.append(group["rule"])
    ordered = sorted(groups.values(), key=lambda group: (-SEVERITIES.index(group["severity"]), group["first_line"]))
    return {
        "lines": len(lines),
        "matches": matches,
        "count": len(matches),
        "groups": ordered,
        "firing": alerts,
        "paged": False,
    }
