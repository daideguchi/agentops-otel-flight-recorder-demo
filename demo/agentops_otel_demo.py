#!/usr/bin/env python3
"""Turn AgentOps event JSONL into OpenTelemetry spans and metrics.

The script is intentionally deterministic so it can support a Zenn article:
readers can run it locally without cloud credentials, then optionally set OTLP
environment variables to send the same telemetry to a collector.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


RISK_SCORE = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def default_events_path() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "data" / "agentops_events.jsonl"


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return sorted(events, key=lambda event: event["timestamp"])


def unix_ns(iso_timestamp: str) -> int:
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1_000_000_000)


def as_attributes(event: dict[str, Any]) -> dict[str, str | int | float | bool]:
    attrs: dict[str, str | int | float | bool] = {
        "agentops.event_id": event["event_id"],
        "agentops.session_id": event["session_id"],
        "agentops.case_id": event["case_id"],
        "agentops.task_id": event["task_id"],
        "agentops.phase": event["phase"],
        "agentops.event_type": event["event_type"],
        "agentops.actor_type": event["actor_type"],
        "agentops.actor_name": event["actor_name"],
        "agentops.status": event["status"],
        "agentops.risk_level": event["risk_level"],
        "agentops.risk_score": RISK_SCORE[event["risk_level"]],
        "agentops.human_approval_required": event["human_approval_required"],
        "agentops.decision": event.get("decision", "none"),
    }
    for key in ("tool", "action", "target", "risk_reason"):
        if key in event:
            attrs[f"agentops.{key}"] = str(event[key])
    if "duration_ms" in event:
        attrs["agentops.duration_ms"] = int(event["duration_ms"])
    if "cost_usd_estimate" in event:
        attrs["agentops.cost_usd_estimate"] = float(event["cost_usd_estimate"])
    return attrs


def otlp_export_enabled(signal: str) -> bool:
    return bool(os.getenv(f"OTEL_EXPORTER_OTLP_{signal.upper()}_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))


def maybe_add_otlp_span_processor(provider: TracerProvider) -> None:
    if not otlp_export_enabled("traces"):
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))


def metric_readers() -> list[MetricReader]:
    readers: list[MetricReader] = [
        PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=300)
    ]
    if otlp_export_enabled("metrics"):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

        readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=300))
    return readers


def build_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_case[event["case_id"]].append(event)

    return {
        "events_total": len(events),
        "cases_total": len(by_case),
        "human_approval_required": sum(1 for event in events if event["human_approval_required"]),
        "blocked_events": sum(1 for event in events if event["status"] == "blocked"),
        "failed_events": sum(1 for event in events if event["status"] == "failed"),
        "warning_events": sum(1 for event in events if event["status"] == "warning"),
        "high_or_critical_risk_events": sum(1 for event in events if event["risk_level"] in {"high", "critical"}),
        "cost_usd_estimate": round(sum(float(event.get("cost_usd_estimate", 0.0)) for event in events), 6),
        "events_by_actor_type": dict(Counter(event["actor_type"] for event in events)),
        "events_by_phase": dict(Counter(event["phase"] for event in events)),
        "events_by_risk": dict(Counter(event["risk_level"] for event in events)),
        "case_max_risk": {
            case_id: max(case_events, key=lambda event: RISK_SCORE[event["risk_level"]])["risk_level"]
            for case_id, case_events in by_case.items()
        },
    }


def write_splunk_collector_template(output_dir: Path) -> None:
    template = """# Optional gateway template for Splunk Observability Cloud.
# Based on the Splunk OpenTelemetry Collector pattern:
# - SPLUNK_ACCESS_TOKEN authenticates ingest.
# - SPLUNK_REALM selects the Observability Cloud realm, for example us0.
# - SPLUNK_INGEST_URL and SPLUNK_HEC_URL can be set explicitly when needed.
# Do not commit real access tokens.
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  resource/agentops:
    attributes:
      - key: service.namespace
        value: dd-ai-organization
        action: upsert
      - key: deployment.environment
        value: zenn-splunk-observability-demo
        action: upsert
  batch:

exporters:
  otlphttp/splunk_traces:
    traces_endpoint: ${SPLUNK_INGEST_URL}/v2/trace/otlp
    headers:
      X-SF-Token: ${SPLUNK_ACCESS_TOKEN}
  signalfx:
    access_token: ${SPLUNK_ACCESS_TOKEN}
    realm: ${SPLUNK_REALM}
  splunk_hec:
    token: ${SPLUNK_ACCESS_TOKEN}
    endpoint: ${SPLUNK_HEC_URL}
    source: agentops-otel-demo
    sourcetype: agentops:otel

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resource/agentops, batch]
      exporters: [otlphttp/splunk_traces]
    metrics:
      receivers: [otlp]
      processors: [resource/agentops, batch]
      exporters: [signalfx]
    logs:
      receivers: [otlp]
      processors: [resource/agentops, batch]
      exporters: [splunk_hec]
"""
    (output_dir / "otel-collector-splunk-template.yaml").write_text(template, encoding="utf-8")


def write_splunk_dashboard_plan(summary: dict[str, Any], output_dir: Path) -> None:
    lines = [
        "# Splunk Observability Dashboard Plan",
        "",
        "This plan is generated from the deterministic local demo. Use it as the checklist for the live Splunk Observability Cloud readback before publishing a Splunk-focused article.",
        "",
        "## Required Live Readback",
        "",
        "- APM / traces show `service.name=agentops-flight-recorder`.",
        "- Trace attributes include `agentops.case_id`, `agentops.phase`, `agentops.actor_type`, `agentops.risk_level`, `agentops.decision`, and `agentops.human_approval_required`.",
        "- Metrics show `agentops.events`, `agentops.approvals.required`, `agentops.blocked`, `agentops.cost.usd.estimate`, `agentops.duration.ms`, and `agentops.risk.score`.",
        "- At least one blocked critical event is visible and traceable back to `CASE-AI-OPS-001`.",
        "- The live screenshot or export must not expose `SPLUNK_ACCESS_TOKEN`.",
        "",
        "## Dashboard Cards",
        "",
        "| card | signal | split/filter | why it matters |",
        "|---|---|---|---|",
        "| AgentOps Event Volume | `agentops.events` | split by `phase`, `actor_type` | shows where agents, humans, APIs, and robots are doing work |",
        "| Human Approval Load | `agentops.approvals.required` | split by `phase`, `risk_level` | shows where human judgment is still required |",
        "| Policy Blocks | `agentops.blocked` | filter `status=blocked` | proves dangerous actions are stopped before execution |",
        "| Estimated AI Cost | `agentops.cost.usd.estimate` | split by `phase`, `actor_type` | connects AI cost with operational workflow |",
        "| Risk Distribution | `agentops.risk.score` | split by `case_id`, `risk_level` | makes high-risk work visible before incidents |",
        "",
        "## Local Demo Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stopline",
        "",
        "Do not claim live Splunk Observability ingestion until a real realm, ingest token, collector run, and UI readback have all been captured.",
    ]
    (output_dir / "splunk_observability_dashboard_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_timeline(events: list[dict[str, Any]], output_dir: Path) -> None:
    lines = [
        "# AgentOps OpenTelemetry Timeline",
        "",
        "| time | case | actor | phase | risk | status | summary |",
        "|---|---|---|---|---|---|---|",
    ]
    for event in events:
        lines.append(
            "| {time} | {case} | {actor} | {phase} | {risk} | {status} | {summary} |".format(
                time=event["timestamp"],
                case=event["case_id"],
                actor=event["actor_type"],
                phase=event["phase"],
                risk=event["risk_level"],
                status=event["status"],
                summary=event["summary"].replace("|", "/"),
            )
        )
    (output_dir / "timeline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def configure_otel() -> tuple[trace.Tracer, metrics.Meter, TracerProvider, MeterProvider]:
    resource = Resource.create(
        {
            "service.name": "agentops-flight-recorder",
            "service.version": "2026.06.zenn",
            "deployment.environment": "local-article-demo",
            "service.namespace": "dd-ai-organization",
        }
    )

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    maybe_add_otlp_span_processor(trace_provider)
    trace.set_tracer_provider(trace_provider)

    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers())
    metrics.set_meter_provider(meter_provider)

    return trace.get_tracer("agentops.zenn.demo"), metrics.get_meter("agentops.zenn.demo"), trace_provider, meter_provider


def emit(events: list[dict[str, Any]], tracer: trace.Tracer, meter: metrics.Meter) -> None:
    event_counter = meter.create_counter("agentops.events", unit="1", description="AgentOps events by type")
    approval_counter = meter.create_counter("agentops.approvals.required", unit="1")
    blocked_counter = meter.create_counter("agentops.blocked", unit="1")
    cost_counter = meter.create_counter("agentops.cost.usd.estimate", unit="USD")
    duration_histogram = meter.create_histogram("agentops.duration.ms", unit="ms")
    risk_histogram = meter.create_histogram("agentops.risk.score", unit="1")

    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        sessions[event["session_id"]].append(event)

    for session_id, session_events in sessions.items():
        session_events = sorted(session_events, key=lambda event: event["timestamp"])
        case_ids = ",".join(sorted({event["case_id"] for event in session_events}))
        session_start_ns = unix_ns(session_events[0]["timestamp"])
        session_end_ns = max(
            unix_ns(event["timestamp"]) + max(int(event.get("duration_ms", 1)), 1) * 1_000_000
            for event in session_events
        )
        session_span = tracer.start_span(
            f"agentops.session/{session_id}",
            start_time=session_start_ns,
            attributes={
                "agentops.session_id": session_id,
                "agentops.case_ids": case_ids,
                "agentops.events_in_session": len(session_events),
            },
        )
        with trace.use_span(session_span, end_on_exit=False):
            for event in session_events:
                attrs = as_attributes(event)
                duration_ms = int(event.get("duration_ms", 1))
                start_ns = unix_ns(event["timestamp"])
                end_ns = start_ns + max(duration_ms, 1) * 1_000_000
                with tracer.start_as_current_span(
                    f"{event['phase']}.{event['event_type']}",
                    start_time=start_ns,
                    end_on_exit=False,
                    attributes=attrs,
                ) as span:
                    span.add_event("agentops.summary", {"summary": event["summary"]}, timestamp=start_ns)
                    if event["status"] in {"failed", "blocked", "warning"}:
                        span.add_event(
                            "agentops.needs_human_review",
                            {
                                "status": event["status"],
                                "risk_level": event["risk_level"],
                                "risk_reason": event.get("risk_reason", ""),
                            },
                            timestamp=end_ns,
                        )
                    span.end(end_time=end_ns)

                metric_attrs = {
                    "event_type": event["event_type"],
                    "phase": event["phase"],
                    "actor_type": event["actor_type"],
                    "risk_level": event["risk_level"],
                    "status": event["status"],
                }
                event_counter.add(1, metric_attrs)
                risk_histogram.record(RISK_SCORE[event["risk_level"]], metric_attrs)
                if "duration_ms" in event:
                    duration_histogram.record(duration_ms, metric_attrs)
                if event.get("cost_usd_estimate"):
                    cost_counter.add(float(event["cost_usd_estimate"]), metric_attrs)
                if event["human_approval_required"]:
                    approval_counter.add(1, metric_attrs)
                if event["status"] == "blocked":
                    blocked_counter.add(1, metric_attrs)

            session_span.add_event(
                "agentops.session.closed",
                {
                    "events": len(session_events),
                    "max_risk": max(session_events, key=lambda event: RISK_SCORE[event["risk_level"]])["risk_level"],
                },
                timestamp=session_end_ns,
            )
        session_span.end(end_time=session_end_ns + 1_000_000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=default_events_path())
    parser.add_argument("--output-dir", type=Path, default=Path("evidence/latest-run"))
    args = parser.parse_args()

    events = read_events(args.events)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    tracer, meter, trace_provider, meter_provider = configure_otel()
    emit(events, tracer, meter)
    trace_provider.force_flush()
    meter_provider.force_flush()
    time.sleep(0.1)

    summary = build_metrics(events)
    (args.output_dir / "metric_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_timeline(events, args.output_dir)
    write_splunk_collector_template(args.output_dir)
    write_splunk_dashboard_plan(summary, args.output_dir)

    print(json.dumps({"status": "ok", "events": args.events.as_posix(), "output_dir": args.output_dir.as_posix(), **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
