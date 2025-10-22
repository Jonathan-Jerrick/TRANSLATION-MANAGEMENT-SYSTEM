"""In-memory persistence layer for the TMS prototype."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from threading import Lock
from typing import Deque, Dict, List, Tuple
from uuid import uuid4

from .models import (
    ActivityEntry,
    AnalyticsOverview,
    AnalyticsSummary,
    Connector,
    DashboardSummary,
    DeadlineEntry,
    EarningsPoint,
    Job,
    JobStatus,
    LanguagePairPerformance,
    TermEntry,
    TimeTrackingAnalysis,
    TimeTrackingPoint,
    TranslationMemoryEntry,
    Vendor,
    WorkflowStepStatus,
)


class State:
    """Stores prototype data structures with coarse locking."""

    def __init__(self) -> None:
        self._connectors: Dict[str, Connector] = {}
        self._jobs: Dict[str, Job] = {}
        self._translation_memory: Dict[str, List[TranslationMemoryEntry]] = defaultdict(list)
        self._term_base: Dict[str, List[TermEntry]] = defaultdict(list)
        self._vendors: Dict[str, Vendor] = {}
        self._activity: Deque[ActivityEntry] = deque(maxlen=50)
        self._time_tracking_breakdown: Dict[str, float] = {
            "translation": 0.0,
            "review": 0.0,
            "communication": 0.0,
        }
        self._time_tracking_trend: List[TimeTrackingPoint] = []
        self._lock = Lock()
        self._seeded = False

    @property
    def seeded(self) -> bool:
        return self._seeded

    # Connector operations -------------------------------------------------
    def add_connector(self, connector: Connector) -> Connector:
        with self._lock:
            self._connectors[connector.id] = connector
        return connector

    def list_connectors(self) -> List[Connector]:
        with self._lock:
            return list(self._connectors.values())

    def get_connector(self, connector_id: str) -> Connector:
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise KeyError(connector_id)
        return connector

    def update_connector(self, connector: Connector) -> None:
        with self._lock:
            self._connectors[connector.id] = connector

    # Vendor operations ----------------------------------------------------
    def add_vendor(self, vendor: Vendor) -> Vendor:
        with self._lock:
            self._vendors[vendor.id] = vendor
        return vendor

    def list_vendors(self) -> List[Vendor]:
        with self._lock:
            return list(self._vendors.values())

    # Job operations -------------------------------------------------------
    def add_job(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def list_jobs(self) -> List[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get_job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    def update_job(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    # Translation memory operations ---------------------------------------
    def add_translation_memory_entry(self, entry: TranslationMemoryEntry) -> TranslationMemoryEntry:
        key = self._tm_key(entry.source_locale, entry.target_locale)
        with self._lock:
            self._translation_memory[key].append(entry)
        return entry

    def list_translation_memory(self, source_locale: str, target_locale: str) -> List[TranslationMemoryEntry]:
        key = self._tm_key(source_locale, target_locale)
        with self._lock:
            return list(self._translation_memory.get(key, []))

    # Term base operations -------------------------------------------------
    def add_term_entry(self, entry: TermEntry) -> TermEntry:
        key = self._term_key(entry.sector, entry.source_locale, entry.target_locale)
        with self._lock:
            self._term_base[key].append(entry)
        return entry

    def list_term_entries(self, sector: str, source_locale: str, target_locale: str) -> List[TermEntry]:
        key = self._term_key(sector, source_locale, target_locale)
        with self._lock:
            return list(self._term_base.get(key, []))

    # Activity -------------------------------------------------------------
    def record_activity(self, entry: ActivityEntry) -> None:
        with self._lock:
            self._activity.appendleft(entry)

    def record_activity_message(self, category: str, message: str) -> None:
        entry = ActivityEntry(
            id=str(uuid4()),
            message=message,
            category=category,
            created_at=datetime.utcnow(),
        )
        self.record_activity(entry)

    # Time tracking --------------------------------------------------------
    def set_time_tracking(self, breakdown: Dict[str, float], trend: List[TimeTrackingPoint]) -> None:
        with self._lock:
            self._time_tracking_breakdown = breakdown
            self._time_tracking_trend = trend

    # Analytics ------------------------------------------------------------
    def dashboard_summary(self) -> DashboardSummary:
        jobs = self.list_jobs()
        active_projects = len([job for job in jobs if job.status != JobStatus.COMPLETED])
        pending_reviews = sum(
            1
            for job in jobs
            for step in job.workflow
            if step.status == WorkflowStepStatus.IN_PROGRESS and not step.automated
        )
        monthly_earnings = sum(job.budget or 0 for job in jobs if job.due_date and job.due_date.month == datetime.utcnow().month)
        words_translated = sum(job.estimated_word_count or 0 for job in jobs if job.status == JobStatus.COMPLETED)
        upcoming_deadlines = sorted(
            [
                DeadlineEntry(
                    project_id=job.id,
                    project_name=job.name or job.content_id,
                    due_date=job.due_date,
                    priority=job.priority,
                )
                for job in jobs
                if job.due_date and job.status != JobStatus.COMPLETED
            ],
            key=lambda entry: entry.due_date,
        )[:5]
        recent_activity = list(self._activity)[:6]
        return DashboardSummary(
            active_projects=active_projects,
            pending_reviews=pending_reviews,
            monthly_earnings=round(monthly_earnings, 2),
            words_translated=words_translated,
            recent_activity=recent_activity,
            upcoming_deadlines=upcoming_deadlines,
        )

    def analytics_summary(self) -> AnalyticsSummary:
        jobs = self.list_jobs()
        total_jobs = len(jobs)
        completed_jobs = len([job for job in jobs if job.status == JobStatus.COMPLETED])
        mtqe_scores: List[float] = [
            report.mtqe_score
            for job in jobs
            for report in job.quality_reports
        ]
        average_mtqe = sum(mtqe_scores) / len(mtqe_scores) if mtqe_scores else None

        breakdown: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "completed": 0})
        translator_productivity: Dict[str, float] = defaultdict(float)
        for job in jobs:
            sector_key = job.sector.lower()
            breakdown[sector_key]["total"] += 1
            if job.status == JobStatus.COMPLETED:
                breakdown[sector_key]["completed"] += 1
            translator = job.metadata.get("translator")
            if translator:
                translator_productivity[translator] += float(job.metadata.get("translation_hours", 0))

        return AnalyticsSummary(
            total_connectors=len(self.list_connectors()),
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            average_mtqe=average_mtqe,
            sector_breakdown=dict(breakdown),
            translator_productivity=dict(translator_productivity),
        )

    def analytics_overview(self) -> AnalyticsOverview:
        jobs = self.list_jobs()
        total_earnings = sum(job.budget or 0 for job in jobs)
        words_translated = sum(job.estimated_word_count or 0 for job in jobs)
        projects_completed = len([job for job in jobs if job.status == JobStatus.COMPLETED])
        ratings = [float(job.metadata.get("rating", 0)) for job in jobs if job.metadata.get("rating")]
        average_rating = sum(ratings) / len(ratings) if ratings else 4.8

        trend_map: Dict[str, EarningsPoint] = {}
        for job in jobs:
            label = job.metadata.get("reporting_week", "Week 1")
            if label not in trend_map:
                trend_map[label] = EarningsPoint(label=label, earnings=0.0, words=0, projects=0)
            point = trend_map[label]
            point.earnings += job.budget or 0
            point.words += job.estimated_word_count or 0
            point.projects += 1

        def _trend_sort_key(point: EarningsPoint) -> tuple[int, str]:
            parts = point.label.split()
            if len(parts) == 2 and parts[1].isdigit():
                return (int(parts[1]), point.label)
            return (0, point.label)

        earnings_trend = sorted(trend_map.values(), key=_trend_sort_key)

        language_pairs: Dict[str, float] = defaultdict(float)
        for job in jobs:
            for locale in job.target_locales:
                pair = f"{job.source_locale}-{locale}"
                language_pairs[pair] += job.estimated_word_count or 0

        language_performance = [
            LanguagePairPerformance(pair=pair, value=value)
            for pair, value in language_pairs.items()
        ]

        time_breakdown = dict(self._time_tracking_breakdown)
        total_hours = sum(time_breakdown.values())
        time_tracking = TimeTrackingAnalysis(
            total_hours=total_hours,
            breakdown=time_breakdown,
            daily_average=round(total_hours / 30, 2) if total_hours else 0.0,
            trend=self._time_tracking_trend,
        )

        return AnalyticsOverview(
            total_earnings=round(total_earnings, 2),
            words_translated=words_translated,
            projects_completed=projects_completed,
            average_rating=round(average_rating, 2),
            earnings_trend=earnings_trend,
            language_pair_performance=language_performance,
            time_tracking=time_tracking,
        )

    # Seed helpers ---------------------------------------------------------
    def mark_seeded(self) -> None:
        self._seeded = True

    # Internal utilities ---------------------------------------------------
    @staticmethod
    def _tm_key(source_locale: str, target_locale: str) -> str:
        return f"{source_locale.lower()}::{target_locale.lower()}"

    @staticmethod
    def _term_key(sector: str, source_locale: str, target_locale: str) -> str:
        return f"{sector.lower()}::{source_locale.lower()}::{target_locale.lower()}"


state = State()
"""Module-level singleton used by the API."""
