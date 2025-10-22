"""Domain and API models for the Translation Management System."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ConnectorType(str, Enum):
    """Supported connector categories."""

    CMS = "cms"
    GIT = "git"


class WorkflowStepStatus(str, Enum):
    """Lifecycle states for a workflow step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class JobStatus(str, Enum):
    """High-level job progress states."""

    INTAKE = "intake"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ProjectPriority(str, Enum):
    """Prioritisation labels for managed projects."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk categories derived from MTQE and sector heuristics."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConnectorCreate(BaseModel):
    """Payload to register a new connector."""

    name: str
    type: ConnectorType
    sector: str = Field(
        ..., description="Target sector to determine workflow automation policies."
    )
    metadata: Dict[str, str] = Field(default_factory=dict)
    auto_sync: bool = Field(
        default=True, description="Whether the connector performs automatic syncs."
    )
    content_paths: List[str] = Field(
        default_factory=list,
        description="Content collections monitored by the connector.",
    )


class Connector(ConnectorCreate):
    """Persisted connector representation."""

    id: str
    created_at: datetime
    last_synced_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    active: bool = True


class Vendor(BaseModel):
    """Registered language service provider information."""

    id: str
    name: str
    sectors: List[str]
    locales: List[str]
    rating: float = Field(..., ge=0, le=5)
    contact_email: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TermEntry(BaseModel):
    """Term base entry stored per sector and locale pair."""

    id: str
    sector: str
    source_locale: str
    target_locale: str
    term: str
    translation: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentSyncRequest(BaseModel):
    """Payload for content pushed from a connector into the TMS."""

    content_id: str
    source_locale: str
    target_locales: List[str]
    content: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    name: Optional[str] = None
    client: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_word_count: Optional[int] = None
    budget: Optional[float] = None
    description: Optional[str] = None
    assigned_vendor_id: Optional[str] = None


class TranslationMemoryEntry(BaseModel):
    """Entry stored in translation memory."""

    id: str
    source_locale: str
    target_locale: str
    source_text: str
    translated_text: str
    created_at: datetime
    usage_count: int = 0


class TranslationSegment(BaseModel):
    """Segment within a translation job."""

    id: str
    source_text: str
    target_locale: str
    tm_suggestion: Optional[str] = None
    tm_score: Optional[float] = None
    nmt_suggestion: Optional[str] = None
    post_edit: Optional[str] = None
    reviewer_notes: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    quality_estimate: Optional[float] = Field(default=None, ge=0, le=100)
    qa_flags: List[str] = Field(default_factory=list)
    term_hits: List[str] = Field(default_factory=list)
    last_updated: Optional[datetime] = None


class WorkflowStep(BaseModel):
    """Single workflow stage for a job."""

    name: str
    automated: bool
    assignee: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING


class QualityReport(BaseModel):
    """Human and automated quality evaluation data."""

    mtqe_score: float = Field(..., ge=0, le=100)
    mqm_errors: Dict[str, int] = Field(default_factory=dict)
    comments: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewer: Optional[str] = None
    compliance_flags: Dict[str, bool] = Field(default_factory=dict)


class Job(BaseModel):
    """Translation job created from inbound content or manual project setup."""

    id: str
    connector_id: Optional[str]
    content_id: str
    sector: str
    source_locale: str
    target_locales: List[str]
    created_at: datetime
    status: JobStatus = JobStatus.INTAKE
    workflow: List[WorkflowStep]
    segments: List[TranslationSegment]
    metadata: Dict[str, str] = Field(default_factory=dict)
    quality_reports: List[QualityReport] = Field(default_factory=list)
    name: Optional[str] = None
    client: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_word_count: Optional[int] = None
    budget: Optional[float] = None
    description: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    assigned_vendor_id: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sector_risk_profile: Dict[str, int] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    """Manual project creation payload used by dashboards and integrations."""

    name: str
    sector: str
    source_locale: str
    target_locales: List[str]
    content: str
    client: Optional[str] = None
    priority: ProjectPriority = ProjectPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_word_count: Optional[int] = None
    budget: Optional[float] = None
    description: Optional[str] = None
    assigned_vendor_id: Optional[str] = None
    connector_id: Optional[str] = None
    created_by_id: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class SegmentUpdate(BaseModel):
    """Updates applied to a translation segment inside the CAT workspace."""

    post_edit: Optional[str] = None
    reviewer_notes: Optional[str] = None


class JobStepCompletion(BaseModel):
    """Request payload to advance a workflow step."""

    reviewer_notes: Optional[str] = None
    post_edit: Optional[str] = None
    segment_ids: Optional[List[str]] = None
    qa_flags: Optional[List[str]] = None


class ActivityEntry(BaseModel):
    """Log entry describing recent project events."""

    id: str
    message: str
    created_at: datetime
    category: str


class DeadlineEntry(BaseModel):
    """Upcoming deadline for dashboard consumption."""

    project_id: str
    project_name: str
    due_date: datetime
    priority: Optional[str] = None


class DashboardSummary(BaseModel):
    """Aggregated dashboard view consumed by the UI."""

    active_projects: int
    pending_reviews: int
    monthly_earnings: float
    words_translated: int
    recent_activity: List[ActivityEntry]
    upcoming_deadlines: List[DeadlineEntry]


class AnalyticsSummary(BaseModel):
    """Aggregate analytics for dashboard experiences."""

    total_connectors: int
    total_jobs: int
    completed_jobs: int
    average_mtqe: Optional[float]
    sector_breakdown: Dict[str, Dict[str, int]]
    translator_productivity: Dict[str, float] = Field(default_factory=dict)


class EarningsPoint(BaseModel):
    """Weekly analytics datapoint for the analytics dashboard."""

    label: str
    earnings: float
    words: int
    projects: int


class LanguagePairPerformance(BaseModel):
    """Distribution of effort per language pair."""

    pair: str
    value: float


class TimeTrackingPoint(BaseModel):
    """Time tracking entry for analytics charts."""

    label: str
    hours: float


class TimeTrackingAnalysis(BaseModel):
    """Breakdown used in analytics dashboards."""

    total_hours: float
    breakdown: Dict[str, float]
    daily_average: float
    trend: List[TimeTrackingPoint]


class AnalyticsOverview(BaseModel):
    """High fidelity analytics overview consumed by the UI."""

    total_earnings: float
    words_translated: int
    projects_completed: int
    average_rating: float
    earnings_trend: List[EarningsPoint]
    language_pair_performance: List[LanguagePairPerformance]
    time_tracking: TimeTrackingAnalysis


class QAInsight(BaseModel):
    """Automated QA insight surfaced in the CAT view."""

    title: str
    message: str
    severity: RiskLevel


class StudioSnapshot(BaseModel):
    """Payload returned for translation studio experiences."""

    project_id: str
    project_name: str
    source_locale: str
    target_locale: str
    sector: str
    segments: List[TranslationSegment]
    translation_memory: List[TranslationMemoryEntry]
    term_base: List[TermEntry]
    qa_insights: List[QAInsight]
    workflow: List[WorkflowStep]
    progress: float


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    TRANSLATOR = "translator"
    REVIEWER = "reviewer"
    CLIENT = "client"


class UserCreate(BaseModel):
    """User registration payload."""
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(default=UserRole.TRANSLATOR, description="User role")


class UserLogin(BaseModel):
    """User login payload."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

    @validator("role", pre=True)
    def _normalize_role(cls, value):
        """Ensure database enum values map to API enum."""
        if isinstance(value, str):
            return value.lower()
        # Handle SQLAlchemy Enum instances exposing .value/.name
        if hasattr(value, "label"):
            return value.label
        if hasattr(value, "value"):
            return value.value.lower()
        return value
