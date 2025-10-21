"""Bootstrap utilities to seed the prototype with representative data."""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from .models import (
    Connector,
    ConnectorType,
    ProjectCreate,
    ProjectPriority,
    TimeTrackingPoint,
    Vendor,
    WorkflowStepStatus,
)
from .services import ProjectService, TermBaseService, TranslationMemoryService
from .state import State
from .workflows import workflow_status


def seed_initial_data(
    state: State,
    project_service: ProjectService,
    tm_service: TranslationMemoryService,
    term_service: TermBaseService,
) -> None:
    """Populate the in-memory stores with curated demo data."""

    if state.seeded:
        return

    now = datetime.utcnow()

    connectors = [
        Connector(
            id="manual-intake",
            name="Manual Intake",
            type=ConnectorType.CMS,
            sector="ecommerce",
            created_at=now,
            metadata={"mode": "manual"},
            auto_sync=False,
        ),
        Connector(
            id=str(uuid4()),
            name="Shopify Connector",
            type=ConnectorType.CMS,
            sector="ecommerce",
            created_at=now,
            metadata={"platform": "shopify"},
            content_paths=["/products", "/collections"],
        ),
        Connector(
            id=str(uuid4()),
            name="Banking Git Sync",
            type=ConnectorType.GIT,
            sector="bfsi",
            created_at=now,
            metadata={"repository": "git@corp/bfsi-portal"},
            content_paths=["/src/locales"],
        ),
        Connector(
            id=str(uuid4()),
            name="Legal CMS Connector",
            type=ConnectorType.CMS,
            sector="legal",
            created_at=now,
            metadata={"platform": "drupal"},
            content_paths=["/cases", "/knowledge"],
        ),
    ]
    for connector in connectors:
        state.add_connector(connector)

    vendors = [
        Vendor(
            id=str(uuid4()),
            name="Global LSP Alliance",
            sectors=["ecommerce", "bfsi"],
            locales=["en-US", "es-ES", "fr-FR"],
            rating=4.9,
            contact_email="projects@globallsp.com",
        ),
        Vendor(
            id=str(uuid4()),
            name="LexiLegal Partners",
            sectors=["legal"],
            locales=["en-US", "es-ES", "fr-FR"],
            rating=4.7,
            contact_email="ops@lexilegal.example",
        ),
    ]
    for vendor in vendors:
        state.add_vendor(vendor)

    # Seed translation memory with sample strings used across the demo content
    tm_service.add_entry("en-US", "es-ES", "Welcome to our store!", "¡Bienvenido a nuestra tienda!")
    tm_service.add_entry("en-US", "fr-FR", "Welcome to our store!", "Bienvenue dans notre boutique !")
    tm_service.add_entry("en-US", "de-DE", "Secure payment portal", "Sicheres Zahlungsportal")
    tm_service.add_entry("en-US", "es-ES", "Account statement", "Estado de cuenta")
    tm_service.add_entry("en-US", "fr-FR", "Compliance update", "Mise à jour de conformité")

    # Term base entries per sector
    term_service.add_entry("bfsi", "en-US", "es-ES", "routing number", "número de ruta", "Banking terminology")
    term_service.add_entry("bfsi", "en-US", "fr-FR", "routing number", "numéro d'acheminement")
    term_service.add_entry("legal", "en-US", "es-ES", "indemnification", "indemnización", "Contractual clause")
    term_service.add_entry("legal", "en-US", "fr-FR", "indemnification", "indemnisation")
    term_service.add_entry("ecommerce", "en-US", "es-ES", "shopping cart", "carrito de compras")

    project_payloads = [
        ProjectCreate(
            name="Tech Manual EN-ES",
            sector="ecommerce",
            source_locale="en-US",
            target_locales=["es-ES"],
            content=(
                "Welcome to our store!\n"
                "Ensure all firmware is updated before installation.\n"
                "Contact support for warranty claims."
            ),
            client="TechCorp Inc",
            priority=ProjectPriority.HIGH,
            due_date=now + timedelta(days=2),
            estimated_word_count=1800,
            budget=2450.0,
            description="Localization of installation manual for consumer hardware.",
            assigned_vendor_id=vendors[0].id,
            connector_id=connectors[1].id,
            metadata={
                "reporting_week": "Week 1",
                "translator": "carlos.vega",
                "translation_hours": "18",
                "rating": "4.9",
            },
        ),
        ProjectCreate(
            name="Legal Document FR-EN",
            sector="legal",
            source_locale="fr-FR",
            target_locales=["en-US"],
            content=(
                "Cette clause couvre l'indemnisation des partenaires.\n"
                "La mise à jour de conformité doit être signée avant le 30 juin."
            ),
            client="Legal Services Co",
            priority=ProjectPriority.CRITICAL,
            due_date=now + timedelta(days=1),
            estimated_word_count=2300,
            budget=3200.0,
            description="Contract localization for cross-border compliance.",
            assigned_vendor_id=vendors[1].id,
            connector_id=connectors[3].id,
            metadata={
                "reporting_week": "Week 2",
                "translator": "amelie.leroy",
                "translation_hours": "24",
                "rating": "4.8",
            },
        ),
        ProjectCreate(
            name="Marketing Copy EN-DE",
            sector="ecommerce",
            source_locale="en-US",
            target_locales=["de-DE"],
            content=(
                "Flash sale ends tonight!\n"
                "Secure payment portal with express checkout."
            ),
            client="Global Marketing",
            priority=ProjectPriority.MEDIUM,
            due_date=now + timedelta(days=4),
            estimated_word_count=950,
            budget=1280.0,
            description="Homepage hero and campaign banners for EU region.",
            assigned_vendor_id=vendors[0].id,
            connector_id=connectors[1].id,
            metadata={
                "reporting_week": "Week 3",
                "translator": "hannah.mueller",
                "translation_hours": "9",
                "rating": "4.7",
            },
        ),
        ProjectCreate(
            name="Website Content ES-EN",
            sector="bfsi",
            source_locale="es-ES",
            target_locales=["en-US"],
            content=(
                "La actualización de seguridad entra en vigor hoy.\n"
                "Los clientes deben confirmar su número de cuenta."
            ),
            client="Banca Segura",
            priority=ProjectPriority.HIGH,
            due_date=now + timedelta(days=3),
            estimated_word_count=1600,
            budget=2100.0,
            description="Customer portal update for security procedures.",
            assigned_vendor_id=vendors[0].id,
            connector_id=connectors[2].id,
            metadata={
                "reporting_week": "Week 4",
                "translator": "marco.rivera",
                "translation_hours": "15",
                "rating": "4.6",
            },
        ),
    ]

    created_jobs = [project_service.create_project(payload) for payload in project_payloads]

    # Manually adjust workflow states and progress to mirror dashboard visuals
    for job in created_jobs:
        if job.workflow:
            job.workflow[0].status = WorkflowStepStatus.COMPLETED
            if len(job.workflow) > 1:
                job.workflow[1].status = WorkflowStepStatus.IN_PROGRESS
        job.status = workflow_status(job.workflow)
        job.progress = project_service.recalculate_progress(job)
        state.update_job(job)

    # Apply sample post edits to reflect human in the loop actions
    for job in created_jobs:
        for segment in job.segments[:1]:
            segment.post_edit = f"{segment.nmt_suggestion} (reviewed)"
        job.progress = project_service.recalculate_progress(job)
        job.last_updated = datetime.utcnow()
        state.update_job(job)

    # Sample activity log aligned with dashboard visuals
    state.record_activity_message(
        category="project",
        message="New project from Client #23 – due in 3 days.",
    )
    state.record_activity_message(
        category="finance",
        message="Payment received: $1,250 for 'Marketing Copy'.",
    )
    state.record_activity_message(
        category="workflow",
        message="Translator review completed for 'Legal Document'.",
    )

    # Time tracking and utilisation metrics used by analytics dashboard
    state.set_time_tracking(
        breakdown={"translation": 102.0, "review": 36.0, "communication": 18.0},
        trend=[
            TimeTrackingPoint(label="Mon", hours=5.2),
            TimeTrackingPoint(label="Tue", hours=6.0),
            TimeTrackingPoint(label="Wed", hours=4.8),
            TimeTrackingPoint(label="Thu", hours=5.5),
            TimeTrackingPoint(label="Fri", hours=5.9),
            TimeTrackingPoint(label="Sat", hours=2.4),
            TimeTrackingPoint(label="Sun", hours=1.5),
        ],
    )

    state.mark_seeded()
