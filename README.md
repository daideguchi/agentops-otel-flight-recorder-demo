# AgentOps OpenTelemetry Flight Recorder Demo

This repository is a minimal companion demo for the Zenn article:

`AIエージェントの「やったこと」をOpenTelemetryで追跡する`

It turns AI-agent operation events into OpenTelemetry spans and metrics.

## What It Shows

- one trace per agent-operation session
- one span per operation event
- attributes for actor, phase, risk, decision, approval, and cost
- metrics for event count, human approvals, blocked actions, risk score, duration, and estimated cost
- an optional OpenTelemetry Collector template for Splunk Observability Cloud

## Run Locally

```bash
python3.11 -m venv .venv311
. .venv311/bin/activate
pip install -r demo/requirements.txt
python demo/agentops_otel_demo.py --output-dir evidence/latest-run
```

Expected summary:

```json
{
  "events_total": 26,
  "cases_total": 3,
  "human_approval_required": 5,
  "blocked_events": 1,
  "failed_events": 1,
  "warning_events": 4,
  "high_or_critical_risk_events": 3,
  "cost_usd_estimate": 4.86
}
```

## Optional Splunk Export

The demo works without cloud credentials. If you want to send traces to an OTLP endpoint, set OpenTelemetry environment variables such as `OTEL_EXPORTER_OTLP_ENDPOINT`.

Do not commit real access tokens. The Splunk collector file in `evidence/` is a template only.

