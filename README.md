# AgentOps OpenTelemetry Flight Recorder Demo

This repository is a minimal companion demo for the Zenn article:

`AIエージェントの「やったこと」をOpenTelemetryで追跡する`

It turns AI-agent operation events into OpenTelemetry spans and metrics.

## What It Shows

- one trace per agent-operation session
- one span per operation event
- attributes for actor, phase, risk, decision, approval, and cost
- metrics for event count, human approvals, blocked actions, risk score, duration, and estimated cost
- an optional OpenTelemetry Collector gateway template for Splunk Observability Cloud
- a generated Splunk Observability dashboard/readback plan

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

The demo works without cloud credentials. If you want to send traces and metrics to a local OpenTelemetry Collector, set OpenTelemetry environment variables such as:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
python demo/agentops_otel_demo.py --output-dir evidence/latest-run
```

The generated Collector template expects Splunk Observability Cloud values at runtime:

```bash
export SPLUNK_ACCESS_TOKEN=...
export SPLUNK_REALM=...
export SPLUNK_INGEST_URL=https://ingest.${SPLUNK_REALM}.observability.splunkcloud.com
export SPLUNK_HEC_URL=https://ingest.${SPLUNK_REALM}.observability.splunkcloud.com/v1/log
```

Do not commit real access tokens. The Splunk collector file in `evidence/` is a template only. The template has been locally validated with `quay.io/signalfx/splunk-otel-collector:latest`; live ingestion still requires a real Splunk Observability Cloud realm and ingest-scoped token.

See `docs/splunk-observability-runbook.md` for the live-readback checklist.
