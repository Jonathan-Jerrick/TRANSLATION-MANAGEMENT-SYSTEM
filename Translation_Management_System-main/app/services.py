"""Service layer implementing translation memory, NMT, and project helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

from .models import (
    Job,
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
    WorkflowStepStatus,
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

    def __init__(self, state: State) -> None:
        self._state = state

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
        return self._state.add_translation_memory_entry(entry)

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
        return best_entry if best_score >= 0.6 else None

    def list_entries(self, source_locale: str, target_locale: str) -> List[TranslationMemoryEntry]:
        return self._state.list_translation_memory(source_locale, target_locale)


class TermBaseService:
    """Sector-aware term base helper service."""

    def __init__(self, state: State) -> None:
        self._state = state

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
        return self._state.add_term_entry(entry)

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

    MANUAL_CONNECTOR_ID = "manual-intake"

    def __init__(
        self,
        state: State,
        tm_service: TranslationMemoryService,
        term_service: TermBaseService,
        nmt_service: NMTService,
    ) -> None:
        self._state = state
        self._tm_service = tm_service
        self._term_service = term_service
        self._nmt_service = nmt_service

    def create_project(self, payload: ProjectCreate) -> Job:
        connector_id = payload.connector_id or self.MANUAL_CONNECTOR_ID
        workflow = build_workflow(payload.sector)
        segments = self._build_segments(
            payload.content,
            payload.source_locale,
            payload.target_locales,
            payload.sector,
        )
        job = Job(
            id=str(uuid4()),
            connector_id=connector_id,
            content_id=payload.metadata.get("content_id", payload.name),
            sector=payload.sector,
            source_locale=payload.source_locale,
            target_locales=payload.target_locales,
            created_at=datetime.utcnow(),
            workflow=workflow,
            segments=segments,
            metadata=dict(payload.metadata),
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
        self._state.add_job(job)
        self._state.record_activity_message(
            category="project",
            message=f"Created project '{job.name or job.content_id}' for {job.sector.title()} sector.",
        )
        return job

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

    def list_projects(self) -> List[Job]:
        return self._state.list_jobs()

    def get_project(self, project_id: str) -> Job:
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
        self._state.record_activity_message(
            category="cat",
            message=f"Updated segment in project '{job.name or job.content_id}'.",
        )
        return target_segment

    def studio_snapshot(self, project_id: str, target_locale: str) -> StudioSnapshot:
        job = self._state.get_job(project_id)
        segments = [segment for segment in job.segments if segment.target_locale == target_locale]
        qa_insights = self._build_qa_insights(segments)
        snapshot = StudioSnapshot(
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
        return snapshot

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
        return job

    def add_quality_report(self, job: Job, report: QualityReport) -> Job:
        job.quality_reports.append(report)
        job.status = workflow_status(job.workflow)
        job.progress = self._project_service.recalculate_progress(job)
        job.last_updated = datetime.utcnow()
        self._state.update_job(job)
        return job
