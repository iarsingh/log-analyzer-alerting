# Log analyzer and alerting tool

Level: Beginner

Skills: Python, regex, logs, automation

Paste a log. Three rules create alerts: a line with `ERROR`, a line with `status=5xx`, and a line with `timeout`.

The response is the line number and the rule name. It does not page anyone and it does not store the log.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn logalert.main:app --reload
```

