import re

RULES = (
    ("error", re.compile(r"\bERROR\b", re.I)),
    ("server_error", re.compile(r"\bstatus=(5\d\d)\b")),
    ("timeout", re.compile(r"\btimeout\b", re.I)),
)


def analyze(text):
    alerts = []
    for number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in RULES:
            if pattern.search(line):
                alerts.append({"line": number, "rule": name, "text": line.strip()})
    return {"alerts": alerts, "count": len(alerts)}
