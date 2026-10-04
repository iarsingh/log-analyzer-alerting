from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from logalert.rules import DEFAULT_RULES, RuleError, analyze, compile_rules

app = FastAPI(title="Log analyzer")


class CustomRule(BaseModel):
    name: str
    pattern: str
    severity: Literal["low", "medium", "high"] = "medium"
    threshold: int = Field(default=1, ge=1)


class LogBody(BaseModel):
    text: str
    rules: list[CustomRule] | None = None
    min_severity: Literal["low", "medium", "high"] = "low"


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/rules")
def list_rules():
    return {
        "rules": [
            {"name": rule.name, "pattern": rule.pattern.pattern, "severity": rule.severity, "threshold": rule.threshold}
            for rule in DEFAULT_RULES
        ]
    }


@app.post("/logs/analyze")
def analyze_logs(body: LogBody):
    try:
        rules = DEFAULT_RULES if body.rules is None else compile_rules([rule.model_dump() for rule in body.rules])
        return analyze(body.text, rules, body.min_severity)
    except RuleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
