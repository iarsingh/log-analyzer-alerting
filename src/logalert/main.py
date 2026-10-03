from fastapi import FastAPI
from pydantic import BaseModel

from logalert.rules import analyze

app = FastAPI(title="Log analyzer")


class LogBody(BaseModel):
    text: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/logs/analyze")
def analyze_logs(body: LogBody):
    return analyze(body.text)
