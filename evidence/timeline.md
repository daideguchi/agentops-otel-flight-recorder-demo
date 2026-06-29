# AgentOps OpenTelemetry Timeline

| time | case | actor | phase | risk | status | summary |
|---|---|---|---|---|---|---|
| 2026-05-19T12:00:41Z | CASE-AI-OPS-001 | human | intake | none | info | Human opened an AI-agent operations case after a release bot proposed a production change. |
| 2026-05-19T12:01:22Z | CASE-AI-OPS-001 | ai_agent | planning | low | success | Agent created a read-only investigation plan with explicit approval gates before any production action. |
| 2026-05-19T12:02:03Z | CASE-AI-OPS-001 | robot | evidence_collection | low | success | Robot gathered the change ticket, linked pull request, deployment window, and service owner. |
| 2026-05-19T12:02:44Z | CASE-AI-OPS-001 | api | evidence_collection | low | success | API confirmed the pull request touches payment retry behavior and has one approving review. |
| 2026-05-19T12:03:25Z | CASE-AI-OPS-001 | ai_agent | investigation | medium | failed | Agent found a failing retry regression test that was not mentioned in the change ticket. |
| 2026-05-19T12:04:06Z | CASE-AI-OPS-001 | ai_agent | risk_review | high | warning | Case risk escalated because the proposed release affects payments and has failing verification. |
| 2026-05-19T12:04:47Z | CASE-AI-OPS-001 | ai_agent | execution | critical | blocked | Attempted production deployment was blocked by policy before execution. |
| 2026-05-19T12:05:28Z | CASE-AI-OPS-001 | human | approval | medium | success | Human requested more evidence instead of approving the production deployment. |
| 2026-05-19T12:06:09Z | CASE-AI-OPS-001 | robot | evidence_collection | low | success | Robot requested service-owner signoff and attached the failed test evidence. |
| 2026-05-19T12:06:50Z | CASE-AI-OPS-001 | human | approval | low | success | Service owner rejected the release until the retry regression is fixed. |
| 2026-05-19T12:07:31Z | CASE-AI-OPS-001 | system | handoff | none | success | Generated a case handoff report with cited evidence IDs and final rejection decision. |
| 2026-05-19T12:08:12Z | CASE-DFIR-002 | human | intake | none | info | Security analyst opened a suspicious email investigation with attached endpoint telemetry. |
| 2026-05-19T12:08:53Z | CASE-DFIR-002 | ai_agent | planning | low | success | Agent proposed an evidence-first DFIR plan: preserve artifacts, list hypotheses, then verify each claim. |
| 2026-05-19T12:09:34Z | CASE-DFIR-002 | robot | evidence_collection | low | success | Collected email headers, attachment hash, browser download timeline, and endpoint process list. |
| 2026-05-19T12:10:15Z | CASE-DFIR-002 | ai_agent | investigation | medium | warning | Agent generated an initial hypothesis but flagged one claim as unsupported by current evidence. |
| 2026-05-19T12:10:56Z | CASE-DFIR-002 | ai_agent | risk_review | high | warning | System marked the draft finding as provisional because execution evidence was missing. |
| 2026-05-19T12:11:37Z | CASE-DFIR-002 | api | evidence_collection | medium | success | Hash lookup returned low-confidence phishing kit association; raw indicator was redacted in report output. |
| 2026-05-19T12:12:18Z | CASE-DFIR-002 | human | approval | low | success | Human approved containment of the reported message and requested no endpoint isolation. |
| 2026-05-19T12:12:59Z | CASE-DFIR-002 | system | handoff | none | success | Generated DFIR report with evidence IDs, unsupported claims, and human containment decision. |
| 2026-05-19T12:13:40Z | CASE-CLOUD-003 | human | intake | none | info | Support manager requested an agent that answers customer questions and escalates uncertain cases. |
| 2026-05-19T12:14:21Z | CASE-CLOUD-003 | ai_agent | planning | low | success | Agent created a workflow plan using retrieval, MCP tools, cost guardrails, and human escalation. |
| 2026-05-19T12:15:02Z | CASE-CLOUD-003 | api | evidence_collection | low | success | MCP retrieval returned the current refund policy and source URL for citation. |
| 2026-05-19T12:15:43Z | CASE-CLOUD-003 | ai_agent | execution | low | success | Agent drafted a customer answer grounded in the retrieved refund policy. |
| 2026-05-19T12:16:24Z | CASE-CLOUD-003 | ai_agent | risk_review | medium | warning | Cost guardrail warned that the high-quality model should be reserved for escalations. |
| 2026-05-19T12:17:05Z | CASE-CLOUD-003 | human | approval | low | success | Human approved the workflow with a rule that expensive model calls are escalation-only. |
| 2026-05-19T12:17:46Z | CASE-CLOUD-003 | system | handoff | none | success | Closed cloud-agent workflow case with source citations, cost guardrail, and human approval captured. |
