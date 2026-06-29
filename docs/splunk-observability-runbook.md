# Splunk Observability Cloud Runbook

This runbook is for turning the local AgentOps OpenTelemetry demo into a live Splunk Observability Cloud proof.

## Boundary

The public demo runs locally without Splunk credentials. Do not claim live Splunk Observability ingestion until all of these are captured:

- Splunk Observability Cloud realm.
- Ingest-scoped access token stored outside Git.
- Collector process started with the generated template.
- Demo run sent OTLP traces and metrics to the Collector.
- Splunk UI readback shows the AgentOps service, trace attributes, and metrics.
- Screenshots or exports are checked for token leakage.

## Runtime Environment

```bash
export SPLUNK_REALM=us0
export SPLUNK_ACCESS_TOKEN=replace-with-ingest-token
export SPLUNK_INGEST_URL=https://ingest.${SPLUNK_REALM}.observability.splunkcloud.com
export SPLUNK_HEC_URL=https://ingest.${SPLUNK_REALM}.observability.splunkcloud.com/v1/log
```

Use the actual realm from the Splunk Observability Cloud organization.

## Collector

The demo writes `evidence/latest-run/otel-collector-splunk-template.yaml`.

Run a Collector with that file, then send OTLP from the Python demo to the Collector's local OTLP HTTP endpoint:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
python demo/agentops_otel_demo.py --output-dir evidence/latest-run
```

## Splunk Readback Checklist

In Splunk Observability Cloud, verify:

- Service or trace search finds `service.name=agentops-flight-recorder`.
- Trace attributes include:
  - `agentops.case_id`
  - `agentops.phase`
  - `agentops.actor_type`
  - `agentops.risk_level`
  - `agentops.human_approval_required`
  - `agentops.decision`
- Metric search finds:
  - `agentops.events`
  - `agentops.approvals.required`
  - `agentops.blocked`
  - `agentops.cost.usd.estimate`
  - `agentops.duration.ms`
  - `agentops.risk.score`
- A critical blocked event exists for `CASE-AI-OPS-001`.
- Dashboard cards match `evidence/latest-run/splunk_observability_dashboard_plan.md`.

## Sources

- Splunk Observability Cloud Collector docs: https://help.splunk.com/en/splunk-observability-cloud/manage-data/splunk-distribution-of-the-opentelemetry-collector/get-started-with-the-splunk-distribution-of-the-opentelemetry-collector
- Splunk OpenTelemetry Collector repo: https://github.com/signalfx/splunk-otel-collector
- Splunk gateway config reference: https://github.com/signalfx/splunk-otel-collector/blob/main/cmd/otelcol/config/collector/gateway_config.yaml
