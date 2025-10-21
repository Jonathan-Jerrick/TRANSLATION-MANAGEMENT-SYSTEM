# System Architecture

## Architectural Principles
- **Modular services** – Decouple connectors, translation pipeline, workflow orchestration, and analytics for independent scaling.
- **Event-driven automation** – Use message queues and event buses to trigger workflows from content changes and translation milestones.
- **API-first design** – Expose REST/GraphQL APIs for integrations, with webhooks for status updates.
- **Security by design** – Implement zero-trust network segmentation, encryption in transit/at rest, and strict identity & access management.
- **Observability** – Centralize logging, metrics, and tracing for operational insight and SLA compliance.

## High-Level Component Diagram
```
+------------------+      +---------------------+      +------------------------+
|  CMS Connectors  |----->|  Ingestion Gateway   |----->|  Workflow Orchestrator |
+------------------+      +---------------------+      +------------------------+
       |                           |                                 |
       v                           v                                 v
+------------------+      +---------------------+      +------------------------+
|  Git Integrator  |----->|  Content Repository |<-----|  Job Management API    |
+------------------+      +---------------------+      +------------------------+
                                                            |
                                                            v
                                                   +----------------------+
                                                   |  Translation Engine  |
                                                   | (NMT + HITL modules) |
                                                   +----------------------+
                                                            |
                                                            v
                                                   +----------------------+
                                                   | Quality & Analytics  |
                                                   +----------------------+
                                                            |
                                                            v
                                                   +----------------------+
                                                   | Delivery Connectors  |
                                                   +----------------------+
```

## Service Responsibilities
| Service | Description | Key Tech |
| --- | --- | --- |
| **Connector Services** | Poll/subscribe to CMS or Git events, normalize content payloads, enforce delta detection. | Serverless functions, message queues, webhook listeners. |
| **Ingestion Gateway** | Authenticates connectors, validates payload schemas, routes jobs to workflow orchestrator. | API Gateway, OAuth 2.0, JSON schema validation. |
| **Workflow Orchestrator** | Applies sector-specific workflows, job routing rules, SLAs, and escalations. | BPMN engine (Camunda/Temporal), rule engine (Drools), PostgreSQL. |
| **Content Repository** | Stores source segments, metadata, TM/TB assets, and job states. | PostgreSQL for transactional data, object storage for binaries. |
| **Translation Engine** | Executes MTQE, selects NMT model, orchestrates human review tasks, writes back edits. | Microservices in Python/Go, model hosting on GPUs, annotation tools. |
| **CAT Workspace** | Browser app for translators with real-time TM/TB lookup and QA checks. | React/TypeScript front-end, WebSocket collaboration, GraphQL API. |
| **Quality & Analytics** | Aggregates MQM scores, productivity metrics, and compliance dashboards. | Data warehouse (Snowflake/BigQuery), BI layer (Metabase/Looker). |
| **Delivery Connectors** | Pushes translated content back to CMS/Git, triggers publishing workflows. | Webhooks, Git automation, CMS APIs. |

## Data Flow
1. Connector detects content change and sends payload to the ingestion gateway.
2. Gateway validates, enriches metadata, and publishes a `job.created` event.
3. Workflow orchestrator evaluates sector rules to determine pipeline steps (e.g., NMT-only vs. NMT + human review).
4. Translation engine executes MTQE, selects translation memory matches, runs NMT, and assigns segments to reviewers as needed.
5. Reviewers use CAT workspace; edits are stored back in content repository, updating TM/TB assets.
6. Quality services compute MQM scores, risk flags, and update dashboards.
7. Delivery connectors push approved translations to target CMS/Git repositories and signal completion.

## Deployment Topology
- **Core services** run in Kubernetes with autoscaling and Istio for service mesh security.
- **Connectors** can deploy as cloud-native functions near customer CMS hosting region to minimize latency.
- **Data plane segregation** by region (EU, US, APAC) with dedicated VPCs to meet residency requirements.
- **Secrets management** through HashiCorp Vault or AWS Secrets Manager.
- **Monitoring stack** using Prometheus, Grafana, ELK/Opensearch, and OpenTelemetry traces.

## Extensibility
- Connector SDK for partners to build custom CMS/Git integrations.
- Webhook subscriptions and GraphQL APIs for enterprises to integrate TMS data into internal dashboards.
- Plugin architecture for additional QA checks, MT providers, or billing integrations.
