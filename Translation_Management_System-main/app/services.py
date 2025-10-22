"""Service layer implementing translation memory, NMT, and project helpers."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Callable, Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

from sqlalchemy.orm import Session

from .models import (
    Job,
    JobStatus,
    JobStepCompletion,
    ProjectCreate,
    QAInsight,
    QualityReport,
    RiskLevel,
    SegmentUpdate,
    StudioSnapshot,
    TermEntry,
    TranslationMemoryEntry,
    TranslationSegment,
    WorkflowStep,
    WorkflowStepStatus,
)
from .db_models import (
    JobStatus as ORMJobStatus,
    Project as ORMProject,
    ProjectPriority as ORMProjectPriority,
    QualityReport as ORMQualityReport,
    RiskLevel as ORMRiskLevel,
    TermEntry as ORMTermEntry,
    TranslationSegment as ORMTranslationSegment,
    TranslationMemory as ORMTranslationMemory,
    User as ORMUser,
    WorkflowStep as ORMWorkflowStep,
    WorkflowStepStatus as ORMWorkflowStepStatus,
)
from .state import State
from .workflows import advance_workflow, build_workflow, workflow_status


@dataclass
class NMTOutput:
    """Container with machine translation outputs and quality metadata."""

    translation: str
    quality: float
    risk: RiskLevel
    qa_flags: List[str]


class TranslationMemoryService:
    """Simple fuzzy lookup for translation memory suggestions."""

    def __init__(self, state: State, session_factory: Optional[Callable[[], Session]] = None) -> None:
        self._state = state
        self._session_factory = session_factory

    @contextmanager
    def _session_scope(self):
        if self._session_factory is None:
            yield None
            return
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def load_from_db(self) -> None:
        if not self._session_factory:
            return
        session = self._session_factory()
        try:
            records = session.query(ORMTranslationMemory).all()
            for record in records:
                entry = TranslationMemoryEntry(
                    id=str(record.id),
                    source_locale=record.source_locale,
                    target_locale=record.target_locale,
                    source_text=record.source_text,
                    translated_text=record.translated_text,
                    created_at=record.created_at,
                    usage_count=record.usage_count,
                )
                self._state.add_translation_memory_entry(entry)
        finally:
            session.close()

    def add_entry(
        self,
        source_locale: str,
        target_locale: str,
        source_text: str,
        translated_text: str,
    ) -> TranslationMemoryEntry:
        entry = TranslationMemoryEntry(
            id=str(uuid4()),
            source_locale=source_locale,
            target_locale=target_locale,
            source_text=source_text,
            translated_text=translated_text,
            created_at=datetime.utcnow(),
        )
        stored_entry = self._state.add_translation_memory_entry(entry)
        self._persist_entry(stored_entry)
        return stored_entry

    def lookup(
        self, source_locale: str, target_locale: str, source_text: str
    ) -> Optional[TranslationMemoryEntry]:
        entries = self._state.list_translation_memory(source_locale, target_locale)
        best_entry: Optional[TranslationMemoryEntry] = None
        best_score = 0.0
        for entry in entries:
            score = SequenceMatcher(a=entry.source_text, b=source_text).ratio()
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry:
            best_entry.usage_count += 1
            self._persist_usage(best_entry)
        return best_entry if best_score >= 0.6 else None

    def list_entries(self, source_locale: str, target_locale: str) -> List[TranslationMemoryEntry]:
        return self._state.list_translation_memory(source_locale, target_locale)

    def _persist_entry(self, entry: TranslationMemoryEntry) -> None:
        with self._session_scope() as session:
            if session is None:
                return
            session.merge(
                ORMTranslationMemory(
                    id=entry.id,
                    source_locale=entry.source_locale,
                    target_locale=entry.target_locale,
                    source_text=entry.source_text,
                    translated_text=entry.translated_text,
                    created_at=entry.created_at,
                    usage_count=entry.usage_count,
                )
            )

    def _persist_usage(self, entry: TranslationMemoryEntry) -> None:
        if not self._session_factory:
            return
        session = self._session_factory()
        try:
            record = session.get(ORMTranslationMemory, entry.id)
            if record:
                record.usage_count = entry.usage_count
                session.commit()
        finally:
            session.close()


class TermBaseService:
    """Sector-aware term base helper service."""

    def __init__(self, state: State, session_factory: Optional[Callable[[], Session]] = None) -> None:
        self._state = state
        self._session_factory = session_factory

    @contextmanager
    def _session_scope(self):
        if self._session_factory is None:
            yield None
            return
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def load_from_db(self) -> None:
        if not self._session_factory:
            return
        session = self._session_factory()
        try:
            records = session.query(ORMTermEntry).all()
            for record in records:
                entry = TermEntry(
                    id=str(record.id),
                    sector=record.sector,
                    source_locale=record.source_locale,
                    target_locale=record.target_locale,
                    term=record.term,
                    translation=record.translation,
                    notes=record.notes,
                )
                self._state.add_term_entry(entry)
        finally:
            session.close()

    def add_entry(
        self,
        sector: str,
        source_locale: str,
        target_locale: str,
        term: str,
        translation: str,
        notes: Optional[str] = None,
    ) -> TermEntry:
        entry = TermEntry(
            id=str(uuid4()),
            sector=sector,
            source_locale=source_locale,
            target_locale=target_locale,
            term=term,
            translation=translation,
            notes=notes,
        )
        stored_entry = self._state.add_term_entry(entry)
        self._persist_entry(stored_entry)
        return stored_entry

    def lookup(
        self, sector: str, source_locale: str, target_locale: str, source_text: str
    ) -> List[TermEntry]:
        entries = self._state.list_term_entries(sector, source_locale, target_locale)
        lowered = source_text.lower()
        return [entry for entry in entries if entry.term.lower() in lowered]

    def list_entries(
        self, sector: str, source_locale: str, target_locale: str
    ) -> List[TermEntry]:
        return self._state.list_term_entries(sector, source_locale, target_locale)

    def _persist_entry(self, entry: TermEntry) -> None:
        with self._session_scope() as session:
            if session is None:
                return
            session.merge(
                ORMTermEntry(
                    id=entry.id,
                    sector=entry.sector,
                    source_locale=entry.source_locale,
                    target_locale=entry.target_locale,
                    term=entry.term,
                    translation=entry.translation,
                    notes=entry.notes,
                )
            )


class NMTService:
    """Deterministic pseudo NMT service with MTQE heuristics."""

    _LEXICON: Dict[str, Dict[str, str]] = {
        "fr-fr": {
            "welcome": "bienvenue",
            "to": "à",
            "our": "notre",
            "store": "boutique",
            "update": "mise à jour",
            "security": "sécurité",
            "protocol": "protocole",
            "account": "compte",
            "statement": "relevé",
            "legal": "juridique",
            "review": "examen",
            "payment": "paiement",
            "due": "dû",
            "today": "aujourd'hui",
        },
        "es-es": {
            "welcome": "bienvenido",
            "to": "a",
            "our": "nuestro",
            "store": "tienda",
            "security": "seguridad",
            "update": "actualización",
            "account": "cuenta",
            "statement": "extracto",
            "legal": "legal",
            "review": "revisión",
            "payment": "pago",
            "due": "vencido",
            "today": "hoy",
        },
        "de-de": {
            "welcome": "willkommen",
            "to": "zu",
            "our": "unser",
            "store": "geschäft",
            "security": "sicherheit",
            "update": "aktualisierung",
            "account": "konto",
            "statement": "kontoauszug",
            "legal": "rechtlich",
            "review": "prüfung",
            "payment": "zahlung",
            "due": "fällig",
            "today": "heute",
        },
    }

    _SECTOR_RISK_KEYWORDS: Dict[str, Sequence[str]] = {
        "bfsi": ("account", "iban", "routing", "statement", "ssn"),
        "legal": ("clause", "contract", "liability", "warranty"),
        "ecommerce": ("sale", "discount", "flash"),
    }

    def translate(
        self, source_text: str, source_locale: str, target_locale: str, sector: str
    ) -> NMTOutput:
        words = source_text.split()
        lexicon = self._LEXICON.get(target_locale.lower(), {})
        translated_words = [lexicon.get(word.lower(), word) for word in words]
        translation = " ".join(translated_words) or source_text

        base_quality = 92.0
        unknown_tokens = len([word for word in words if word.lower() not in lexicon])
        base_quality -= unknown_tokens * 4

        lowered = source_text.lower()
        risk_adjustment = 0
        for keyword in self._SECTOR_RISK_KEYWORDS.get(sector.lower(), []):
            if keyword in lowered:
                risk_adjustment += 6
        if any(char.isdigit() for char in source_text):
            risk_adjustment += 4
        if "%" in source_text or "{{" in source_text:
            risk_adjustment += 5

        quality = max(55.0, min(98.0, base_quality - risk_adjustment))
        if quality >= 85:
            risk = RiskLevel.LOW
        elif quality >= 70:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.HIGH

        qa_flags: List[str] = []
        if risk is RiskLevel.HIGH:
            qa_flags.append("high_risk_segment")
        if "http" in lowered:
            qa_flags.append("link_verification")
        if "{{" in source_text:
            qa_flags.append("placeholder_validation")

        return NMTOutput(translation=translation, quality=quality, risk=risk, qa_flags=qa_flags)


def build_segment(
    source_text: str,
    source_locale: str,
    target_locale: str,
    sector: str,
    tm_service: TranslationMemoryService,
    term_service: TermBaseService,
    nmt_service: NMTService,
) -> TranslationSegment:
    """Construct a translation segment enriched with TM, terminology, and MTQE."""

    tm_entry = tm_service.lookup(source_locale, target_locale, source_text)
    nmt_output = nmt_service.translate(source_text, source_locale, target_locale, sector)
    term_hits = term_service.lookup(sector, source_locale, target_locale, source_text)

    return TranslationSegment(
        id=str(uuid4()),
        source_text=source_text,
        target_locale=target_locale,
        tm_suggestion=tm_entry.translated_text if tm_entry else None,
        tm_score=SequenceMatcher(a=tm_entry.source_text, b=source_text).ratio() if tm_entry else None,
        nmt_suggestion=nmt_output.translation,
        risk_level=nmt_output.risk,
        quality_estimate=nmt_output.quality,
        qa_flags=nmt_output.qa_flags,
        term_hits=[term.translation for term in term_hits],
    )


class ProjectService:
    """Coordinates project creation, CAT updates, and studio snapshots."""

    MANUAL_CONNECTOR_ID = "00000000-0000-0000-0000-000000000001"

    def __init__(
        self,
        state: State,
        tm_service: TranslationMemoryService,
        term_service: TermBaseService,
        nmt_service: NMTService,
        session_factory: Optional[Callable[[], Session]] = None,
    ) -> None:
        self._state = state
        self._tm_service = tm_service
        self._term_service = term_service
        self._nmt_service = nmt_service
        self._session_factory = session_factory

    @contextmanager
    def _session_scope(self):
        if self._session_factory is None:
            yield None
            return
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def load_from_db(self) -> None:
        if not self._session_factory:
            return
        session = self._session_factory()
        try:
            projects = session.query(ORMProject).all()
            for project in projects:
                job = self._job_from_orm(project)
                self._state.add_job(job)
        finally:
            session.close()

    def create_project(self, payload: ProjectCreate) -> Job:
        connector_id = payload.connector_id or self.MANUAL_CONNECTOR_ID
        workflow = build_workflow(payload.sector)
        segments = self._build_segments(
            payload.content,
            payload.source_locale,
            payload.target_locales,
            payload.sector,
        )
        metadata = dict(payload.metadata)
        if payload.created_by_id:
            metadata["created_by_id"] = payload.created_by_id
        metadata.setdefault("workflow_mode", metadata.get("workflow_mode", "human_post_edit"))
        metadata.setdefault("_source_content", payload.content)
        job = Job(
            id=str(uuid4()),
            connector_id=connector_id,
            content_id=metadata.get("content_id", payload.name),
            sector=payload.sector,
            source_locale=payload.source_locale,
            target_locales=payload.target_locales,
            created_at=datetime.utcnow(),
            workflow=workflow,
            segments=segments,
            metadata=metadata,
            name=payload.name,
            client=payload.client,
            priority=payload.priority.value if payload.priority else None,
            due_date=payload.due_date,
            estimated_word_count=payload.estimated_word_count,
            budget=payload.budget,
            description=payload.description,
            assigned_vendor_id=payload.assigned_vendor_id,
        )
        job.status = workflow_status(job.workflow)
        job.progress = self.recalculate_progress(job)
        if payload.created_by_id:
            job.metadata["created_by_id"] = payload.created_by_id
        self._state.add_job(job)
        self._persist_job(job, payload)
        self._state.record_activity_message(
            category="project",
            message=f"Created project '{job.name or job.content_id}' for {job.sector.title()} sector.",
        )
        return job

    def list_projects(self) -> List[Job]:
        return sorted(self._state.list_jobs(), key=lambda job: job.created_at, reverse=True)

    def list_projects_for_user(self, user: ORMUser) -> List[Job]:
        role = getattr(user.role, "label", str(user.role).lower())
        jobs = self.list_projects()
        if role == "manager":
            manager_id = str(user.id)
            return [
                job
                for job in jobs
                if job.metadata.get("created_by_id") in {manager_id, None, "",}
            ]
        if role == "translator":
            return [job for job in jobs if job.status != JobStatus.COMPLETED]
        return jobs

    def get_project(self, project_id: str) -> Job:
        try:
            return self._state.get_job(project_id)
        except KeyError:
            self._reload_project(project_id)
            return self._state.get_job(project_id)

    def update_segment(self, project_id: str, segment_id: str, update: SegmentUpdate) -> TranslationSegment:
        job = self._state.get_job(project_id)
        target_segment = next((segment for segment in job.segments if segment.id == segment_id), None)
        if target_segment is None:
            raise KeyError(segment_id)
        if update.post_edit is not None:
            target_segment.post_edit = update.post_edit
        if update.reviewer_notes is not None:
            target_segment.reviewer_notes = update.reviewer_notes
        target_segment.last_updated = datetime.utcnow()
        job.progress = self.recalculate_progress(job)
        job.last_updated = datetime.utcnow()
        self._state.update_job(job)
        self._persist_job(job)
        self._state.record_activity_message(
            category="cat",
            message=f"Updated segment in project '{job.name or job.content_id}'.",
        )
        return target_segment

    def sync_job(self, job: Job) -> None:
        self._persist_job(job)

    def _persist_job(self, job: Job, payload: Optional[ProjectCreate] = None) -> None:
        if not self._session_factory:
            return
        metadata = dict(job.metadata)
        if payload:
            metadata.update(payload.metadata)
            if payload.created_by_id:
                metadata["created_by_id"] = payload.created_by_id
            metadata["_source_content"] = payload.content
        metadata = {
            str(key): (value if isinstance(value, str) else str(value) if value is not None else "")
            for key, value in metadata.items()
        }
        with self._session_scope() as session:
            if session is None:
                return
            project = session.get(ORMProject, job.id)
            if project is None:
                project = ORMProject(id=job.id, created_at=job.created_at)
                session.add(project)
            project.name = job.name or job.content_id
            project.sector = job.sector
            project.source_locale = job.source_locale
            project.target_locales = job.target_locales
            project.client = job.client
            project.priority = None
            if payload and payload.priority:
                project.priority = ORMProjectPriority(payload.priority.value)
            elif job.priority:
                project.priority = ORMProjectPriority(job.priority)
            project.due_date = job.due_date
            project.estimated_word_count = job.estimated_word_count
            project.budget = job.budget
            project.description = job.description
            project.connector_id = job.connector_id
            project.assigned_vendor_id = job.assigned_vendor_id
            created_by = metadata.get("created_by_id")
            if created_by:
                project.assigned_user_id = created_by
            project.status = ORMJobStatus(job.status.value if isinstance(job.status, JobStatus) else str(job.status))
            project.progress = job.progress
            project.config_data = metadata
            source_content = metadata.get("_source_content")
            if payload and payload.content:
                project.content = payload.content
            elif source_content:
                project.content = source_content
            project.updated_at = datetime.utcnow()
            session.flush()
            session.query(ORMTranslationSegment).filter(
                ORMTranslationSegment.project_id == project.id
            ).delete(synchronize_session=False)
            session.query(ORMWorkflowStep).filter(
                ORMWorkflowStep.project_id == project.id
            ).delete(synchronize_session=False)
            session.query(ORMQualityReport).filter(
                ORMQualityReport.project_id == project.id
            ).delete(synchronize_session=False)
            for order, step in enumerate(job.workflow):
                session.add(
                    ORMWorkflowStep(
                        project_id=project.id,
                        name=step.name,
                        automated=step.automated,
                        assignee=step.assignee,
                        status=ORMWorkflowStepStatus(step.status.value if isinstance(step.status, WorkflowStepStatus) else step.status),
                        order=order,
                        completed_at=datetime.utcnow() if step.status == WorkflowStepStatus.COMPLETED else None,
                    )
                )
            for segment in job.segments:
                session.add(
                    ORMTranslationSegment(
                        id=segment.id,
                        project_id=project.id,
                        source_text=segment.source_text,
                        target_locale=segment.target_locale,
                        tm_suggestion=segment.tm_suggestion,
                        tm_score=segment.tm_score,
                        nmt_suggestion=segment.nmt_suggestion,
                        post_edit=segment.post_edit,
                        reviewer_notes=segment.reviewer_notes,
                        risk_level=ORMRiskLevel(
                            segment.risk_level.value if isinstance(segment.risk_level, RiskLevel) else segment.risk_level
                        )
                        if segment.risk_level
                        else None,
                        quality_estimate=segment.quality_estimate,
                        qa_flags=segment.qa_flags,
                        term_hits=segment.term_hits,
                    )
                )
            for report in job.quality_reports:
                session.add(
                    ORMQualityReport(
                        project_id=project.id,
                        mtqe_score=report.mtqe_score,
                        mqm_errors=report.mqm_errors,
                        comments=report.comments,
                        submitted_at=report.submitted_at,
                        compliance_flags=report.compliance_flags,
                    )
                )

    def _build_segments(
        self,
        content: str,
        source_locale: str,
        target_locales: Sequence[str],
        sector: str,
    ) -> List[TranslationSegment]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        segments: List[TranslationSegment] = []
        for target_locale in target_locales:
            for line in lines:
                segments.append(
                    build_segment(
                        source_text=line,
                        source_locale=source_locale,
                        target_locale=target_locale,
                        sector=sector,
                        tm_service=self._tm_service,
                        term_service=self._term_service,
                        nmt_service=self._nmt_service,
                    )
                )
        return segments

    def _reload_project(self, project_id: str) -> None:
        if not self._session_factory:
            raise KeyError(project_id)
        session = self._session_factory()
        try:
            project = session.get(ORMProject, project_id)
            if project is None:
                raise KeyError(project_id)
            job = self._job_from_orm(project)
            self._state.update_job(job)
        finally:
            session.close()

    def _job_from_orm(self, project: ORMProject) -> Job:
        metadata = dict(project.config_data or {})
        metadata.setdefault("_source_content", project.content or "")
        if project.assigned_user_id:
            metadata.setdefault("created_by_id", str(project.assigned_user_id))
        workflow_steps = sorted(project.workflow_steps, key=lambda step: step.order or 0)
        workflow = [
            WorkflowStep(
                name=step.name,
                automated=step.automated,
                assignee=step.assignee or "",
                status=WorkflowStepStatus(step.status.value if step.status else WorkflowStepStatus.PENDING.value),
            )
            for step in workflow_steps
        ]
        segments = [
            TranslationSegment(
                id=str(segment.id),
                source_text=segment.source_text,
                target_locale=segment.target_locale,
                tm_suggestion=segment.tm_suggestion,
                tm_score=segment.tm_score,
                nmt_suggestion=segment.nmt_suggestion,
                post_edit=segment.post_edit,
                reviewer_notes=segment.reviewer_notes,
                risk_level=RiskLevel(segment.risk_level.value) if segment.risk_level else None,
                quality_estimate=segment.quality_estimate,
                qa_flags=segment.qa_flags or [],
                term_hits=segment.term_hits or [],
                last_updated=segment.updated_at,
            )
            for segment in project.segments
        ]
        quality_reports = [
            QualityReport(
                mtqe_score=report.mtqe_score,
                mqm_errors=report.mqm_errors or {},
                comments=report.comments,
                submitted_at=report.submitted_at,
                reviewer=report.reviewer.email if report.reviewer else None,
                compliance_flags=report.compliance_flags or {},
            )
            for report in project.quality_reports
        ]
        job = Job(
            id=str(project.id),
            connector_id=project.connector_id,
            content_id=metadata.get("content_id", project.name or str(project.id)),
            sector=project.sector,
            source_locale=project.source_locale,
            target_locales=project.target_locales or [],
            created_at=project.created_at or datetime.utcnow(),
            status=JobStatus(project.status.value if project.status else JobStatus.INTAKE.value),
            workflow=workflow,
            segments=segments,
            metadata={str(k): (v if isinstance(v, str) else str(v)) for k, v in metadata.items()},
            quality_reports=quality_reports,
            name=project.name,
            client=project.client,
            priority=project.priority.value if project.priority else None,
            due_date=project.due_date,
            estimated_word_count=project.estimated_word_count,
            budget=project.budget,
            description=project.description,
            progress=project.progress or 0.0,
            assigned_vendor_id=project.assigned_vendor_id,
            last_updated=project.updated_at or project.created_at or datetime.utcnow(),
        )
        return job

    def studio_snapshot(self, project_id: str, target_locale: str) -> StudioSnapshot:
        job = self.get_project(project_id)
        segments = [segment for segment in job.segments if segment.target_locale == target_locale]
        qa_insights = self._build_qa_insights(segments)
        return StudioSnapshot(
            project_id=job.id,
            project_name=job.name or job.content_id,
            source_locale=job.source_locale,
            target_locale=target_locale,
            sector=job.sector,
            segments=segments,
            translation_memory=self._tm_service.list_entries(job.source_locale, target_locale),
            term_base=self._term_service.list_entries(job.sector, job.source_locale, target_locale),
            qa_insights=qa_insights,
            workflow=job.workflow,
            progress=job.progress,
        )

    def _build_qa_insights(self, segments: Sequence[TranslationSegment]) -> List[QAInsight]:
        if not segments:
            return []
        insights: List[QAInsight] = []
        high_risk = [segment for segment in segments if segment.risk_level == RiskLevel.HIGH]
        medium_risk = [segment for segment in segments if segment.risk_level == RiskLevel.MEDIUM]
        if high_risk:
            insights.append(
                QAInsight(
                    title="High MT risk detected",
                    message=f"{len(high_risk)} segments require urgent human review.",
                    severity=RiskLevel.HIGH,
                )
            )
        if medium_risk:
            insights.append(
                QAInsight(
                    title="Segments to monitor",
                    message=f"{len(medium_risk)} segments flagged for additional QA.",
                    severity=RiskLevel.MEDIUM,
                )
            )
        if not insights:
            insights.append(
                QAInsight(
                    title="Machine output validated",
                    message="All segments scored high MTQE with low risk.",
                    severity=RiskLevel.LOW,
                )
            )
        return insights

    def recalculate_progress(self, job: Job) -> float:
        total_steps = len(job.workflow)
        completed_steps = len(
            [step for step in job.workflow if step.status == WorkflowStepStatus.COMPLETED]
        )
        workflow_progress = completed_steps / total_steps if total_steps else 1.0
        segments = [segment for segment in job.segments if segment.target_locale in job.target_locales]
        completed_segments = len([segment for segment in segments if segment.post_edit])
        segment_progress = completed_segments / len(segments) if segments else 0.0
        progress = (workflow_progress * 0.4) + (segment_progress * 0.6)
        return round(progress, 4)


class JobService:
    """Business logic for managing jobs and workflow progression."""

    def __init__(
        self,
        state: State,
        tm_service: TranslationMemoryService,
        project_service: ProjectService,
    ) -> None:
        self._state = state
        self._tm_service = tm_service
        self._project_service = project_service

    def complete_step(self, job: Job, step_completion: JobStepCompletion) -> Job:
        target_segments: Iterable[TranslationSegment]
        if step_completion.segment_ids:
            segment_map = {segment.id: segment for segment in job.segments}
            target_segments = [
                segment_map[segment_id]
                for segment_id in step_completion.segment_ids
                if segment_id in segment_map
            ]
        else:
            target_segments = job.segments

        for segment in target_segments:
            if step_completion.post_edit:
                segment.post_edit = step_completion.post_edit
            if step_completion.reviewer_notes:
                segment.reviewer_notes = step_completion.reviewer_notes
            if step_completion.qa_flags:
                existing = set(segment.qa_flags)
                existing.update(step_completion.qa_flags)
                segment.qa_flags = sorted(existing)
            segment.last_updated = datetime.utcnow()

        advance_workflow(job.workflow)
        job.status = workflow_status(job.workflow)
        job.progress = self._project_service.recalculate_progress(job)
        job.last_updated = datetime.utcnow()
        self._state.update_job(job)
        self._project_service.sync_job(job)
        return job

    def add_quality_report(self, job: Job, report: QualityReport) -> Job:
        job.quality_reports.append(report)
        job.status = workflow_status(job.workflow)
        job.progress = self._project_service.recalculate_progress(job)
        job.last_updated = datetime.utcnow()
        self._state.update_job(job)
        self._project_service.sync_job(job)
        return job
