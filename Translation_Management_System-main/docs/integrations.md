# Connectors, Integrations, and Extensibility

## CMS Connectors
| Platform | Approach | Automation Features |
| --- | --- | --- |
| WordPress | Plugin using REST API + webhooks | Auto-detect draft/published changes, custom field mapping. |
| Drupal | Module leveraging JSON:API | Node revision tracking, taxonomy sync. |
| Adobe Experience Manager | OSGi bundle + Sling models | Workflow hooks, translation project automation. |
| Contentful | App Framework integration | Entry change subscriptions, localization environment support. |

### Connector Capabilities
- OAuth-based authentication or API token management.
- Change detection via webhook subscription or delta polling.
- Content packaging into locale-agnostic JSON with metadata (content type, SEO tags, release window).
- Auto-creation of translation jobs based on rules (e.g., locale coverage, TM leverage threshold).

## Git Integrations
- Support for GitHub, GitLab, Bitbucket via app installations or OAuth apps.
- Detect changes in localization branches or resource file directories.
- Automate pull request creation with translated resource files, status checks, and review workflows.
- Provide CLI utility for developers to trigger jobs locally.

## API Surface
- **REST/GraphQL APIs** for job creation, status retrieval, TM/TB management, analytics queries.
- **Webhooks** for job events (`job.created`, `job.ready`, `job.delivered`, `qa.failed`).
- **SDKs** (JavaScript, Python) for rapid integration and custom automation.

## CAT Tool Integration
- Embed third-party CAT tools via secure iframe or OAuth if customers prefer existing tooling.
- Provide standard XLIFF, TBX import/export.
- Support real-time collaboration via WebSockets with presence indicators.

## Marketplace & Vendor Management
- Allow LSPs to publish service offerings, rates, and certifications.
- Enterprises can invite vendors, negotiate contracts, and assign jobs through the platform.
- Provide performance APIs so vendors can ingest analytics into their BI systems.

## Extensibility Patterns
- **Event Bus** – Publish job events to Kafka/SNS; allow customers to subscribe for custom automations.
- **Function Hooks** – Let customers run custom scripts (e.g., pre-processing, QA) within sandboxed environment.
- **Reporting APIs** – Export data to data warehouses via scheduled pipelines (Snowflake, BigQuery, Redshift).
