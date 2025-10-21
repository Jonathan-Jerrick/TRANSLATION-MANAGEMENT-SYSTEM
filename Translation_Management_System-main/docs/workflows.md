# Workflow Automation & Sector Playbooks

## Workflow Engine Overview
- **Trigger sources**: CMS webhook, Git commit, manual job creation, API call.
- **Workflow definition**: BPMN/DSL describing tasks, conditions, SLAs, notification rules.
- **Dynamic routing**: Rule engine evaluates sector, content type, risk score, and locale to select pipeline path.
- **Automation hooks**: Scripted actions for glossary application, TM leverage, pseudotranslation, staging preview generation.

## Reference Pipelines
### E-Commerce (Speed Optimized)
1. **Content ingest** via CMS connector (product catalog update).
2. **MTQE assessment**; if risk < threshold, auto-approve NMT output.
3. **Human post-edit** only for high-risk segments.
4. **Automated QA** (terminology lock, formatting checks).
5. **Preview generation** for localized storefront.
6. **Delivery** back to CMS with optional automatic publish.

### BFSI (Accuracy & Compliance)
1. **Content ingest** (policy update) triggers **manual approval gate** by compliance officer.
2. **Human translator assignment** with sector-certified linguist pool.
3. **Parallel SME review** for critical locales; enforce two-person review rule.
4. **QA checks**: MQM, regex validation for account numbers, PII masking verification.
5. **Compliance sign-off** with audit log capture.
6. **Delivery** with staged deployment and masked preview URLs.

### Government & Legal (Security Priority)
1. **Secure ingest** via isolated connector within government VPC.
2. **Immediate human translation**; NMT used only for suggestions with strict confidentiality tags.
3. **Legal review** with clause-by-clause approval.
4. **Terminology lock** using legislative glossary and translation memory.
5. **QA and certification** generating legally admissible translation certificate.
6. **Delivery** to CMS/Git with immutable audit trail.

## Job Lifecycle States
```
NEW -> IN_REVIEW -> IN_TRANSLATION -> HITL_REVIEW -> QA -> READY -> DELIVERED -> ARCHIVED
```

States are customizable per workflow; SLAs and escalations attach to transitions.

## Automation Rules Examples
| Rule | Condition | Action |
| --- | --- | --- |
| Auto-assign translator | Locale = "fr-FR" AND sector = BFSI | Assign to translator pool "BFSI_FR_Tier1" |
| Enforce human review | Risk score > 0.7 | Insert HITL task, notify reviewer via Slack/Email |
| Auto-publish | Sector = E-Commerce AND TM leverage > 85% | Skip human review and push to CMS staging |
| Compliance hold | Content contains PII AND sector = BFSI | Mask sensitive fields, require compliance approval |

## SLA & Escalation Management
- **SLA Templates** per sector with response and resolution times.
- **Escalation paths**: translator -> lead linguist -> project manager -> program owner.
- **Notification channels**: email, Slack/Teams, in-app alerts.
- **Breach handling**: automatic job reprioritization, extra reviewer assignment, or vendor switch.

## Multi-LSP Coordination
- Allow multiple LSP vendors per locale; orchestrator balances workload based on capacity, performance, and cost.
- Vendor scorecards feed into routing decisions and analytics dashboards.

## Direct Enterprise Usage
- Enterprises without LSPs can invite freelance translators and use platform-native vendor marketplace.
- Workflow templates can be cloned and modified via low-code builder.
- Self-service analytics provide cost forecasting and volume projections.
