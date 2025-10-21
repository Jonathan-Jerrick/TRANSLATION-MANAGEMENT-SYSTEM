# Security, Compliance, and Data Governance

## Compliance Frameworks
- **GDPR / UK GDPR** – Data subject rights, DPA with customers, EU data residency options.
- **SOC 2 Type II** – Trust service criteria for security, availability, confidentiality.
- **ISO 27001** – Information security management system (ISMS) to govern policies, risk assessments, and audits.
- **Industry-specific** – PCI DSS (payments), HIPAA (healthcare), CJIS (US government) as required per client.

## Data Residency Strategy
- Regional clusters (EU, US, APAC) with customer choice at onboarding.
- Content, TM/TB, and logs stored in-region; cross-region replication optional with customer consent.
- Key management per region via KMS and customer-managed keys support.

## Security Controls
| Layer | Controls |
| --- | --- |
| Identity & Access | SSO (SAML/OIDC), MFA enforcement, RBAC with least privilege, SCIM provisioning. |
| Network | Private VPCs, security groups, WAF, DDoS mitigation, IP allowlists. |
| Application | OWASP testing, secure SDLC, dependency scanning, runtime application self-protection (RASP). |
| Data | AES-256 encryption at rest, TLS 1.2+ in transit, field-level encryption for PII/PHI, secrets vault. |
| Operations | Continuous monitoring, anomaly detection, automated patching, incident response runbooks. |

## Privacy & Masking
- Automated detection of PII/PHI with pattern and ML-based classifiers.
- Mask sensitive fields during previews and when exporting translation memories.
- Redaction policies for logging and analytics pipelines.

## Audit & Reporting
- Immutable audit logs for content access, translation edits, and workflow actions.
- Tamper-evident storage using append-only logs (AWS QLDB/Hash chains).
- Scheduled compliance reports and customer-accessible audit dashboards.

## Business Continuity
- Active-active architecture across availability zones.
- Regular disaster recovery drills with RPO < 1 hour, RTO < 4 hours.
- Backup encryption and quarterly restore testing.

## Vendor & LSP Management
- Due diligence checklist including security questionnaires and certifications.
- Contractual obligations for data handling, confidentiality, and breach notification.
- Vendor performance dashboards highlighting quality and compliance adherence.
