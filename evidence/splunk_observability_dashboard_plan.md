# Splunk Observability Dashboard Plan

This plan is generated from the deterministic local demo. Use it as the checklist for the live Splunk Observability Cloud readback before publishing a Splunk-focused article.

## Required Live Readback

- APM / traces show `service.name=agentops-flight-recorder`.
- Trace attributes include `agentops.case_id`, `agentops.phase`, `agentops.actor_type`, `agentops.risk_level`, `agentops.decision`, and `agentops.human_approval_required`.
- Metrics show `agentops.events`, `agentops.approvals.required`, `agentops.blocked`, `agentops.cost.usd.estimate`, `agentops.duration.ms`, and `agentops.risk.score`.
- At least one blocked critical event is visible and traceable back to `CASE-AI-OPS-001`.
- The live screenshot or export must not expose `SPLUNK_ACCESS_TOKEN`.

## Dashboard Cards

| card | signal | split/filter | why it matters |
|---|---|---|---|
| AgentOps Event Volume | `agentops.events` | split by `phase`, `actor_type` | shows where agents, humans, APIs, and robots are doing work |
| Human Approval Load | `agentops.approvals.required` | split by `phase`, `risk_level` | shows where human judgment is still required |
| Policy Blocks | `agentops.blocked` | filter `status=blocked` | proves dangerous actions are stopped before execution |
| Estimated AI Cost | `agentops.cost.usd.estimate` | split by `phase`, `actor_type` | connects AI cost with operational workflow |
| Risk Distribution | `agentops.risk.score` | split by `case_id`, `risk_level` | makes high-risk work visible before incidents |

## Local Demo Summary

```json
{
  "events_total": 26,
  "cases_total": 3,
  "human_approval_required": 5,
  "blocked_events": 1,
  "failed_events": 1,
  "warning_events": 4,
  "high_or_critical_risk_events": 3,
  "cost_usd_estimate": 4.86,
  "events_by_actor_type": {
    "human": 7,
    "ai_agent": 10,
    "robot": 3,
    "api": 3,
    "system": 3
  },
  "events_by_phase": {
    "intake": 3,
    "planning": 3,
    "evidence_collection": 6,
    "investigation": 2,
    "risk_review": 3,
    "execution": 2,
    "approval": 4,
    "handoff": 3
  },
  "events_by_risk": {
    "none": 6,
    "low": 12,
    "medium": 5,
    "high": 2,
    "critical": 1
  },
  "case_max_risk": {
    "CASE-AI-OPS-001": "critical",
    "CASE-DFIR-002": "high",
    "CASE-CLOUD-003": "medium"
  }
}
```

## Stopline

Do not claim live Splunk Observability ingestion until a real realm, ingest token, collector run, and UI readback have all been captured.
