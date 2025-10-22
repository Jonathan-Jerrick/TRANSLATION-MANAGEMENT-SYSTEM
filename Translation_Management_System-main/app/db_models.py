"""SQLAlchemy database models for the Translation Management System."""
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import CHAR, TypeDecorator

from .database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type."""

    impl = PostgresUUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            value = str(value)
        if dialect.name == "postgresql":
            return uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


class ConnectorType(PyEnum):
    CMS = "CMS"
    GIT = "GIT"


class WorkflowStepStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class JobStatus(PyEnum):
    INTAKE = "intake"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ProjectPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserRole(PyEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    TRANSLATOR = "TRANSLATOR"
    REVIEWER = "REVIEWER"
    CLIENT = "CLIENT"

    @property
    def label(self) -> str:
        """Lowercase representation used by API responses."""
        return self.value.lower()


class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.TRANSLATOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    projects = relationship("Project", back_populates="assigned_user")
    quality_reports = relationship("QualityReport", back_populates="reviewer")


class Connector(Base):
    __tablename__ = "connectors"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(ConnectorType), nullable=False)
    sector = Column(String(100), nullable=False)
    config_data = Column(JSON)
    auto_sync = Column(Boolean, default=True)
    content_paths = Column(JSON)
    last_synced_at = Column(DateTime)
    last_sync_status = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="connector")


class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    sectors = Column(JSON)  # List of sectors
    locales = Column(JSON)  # List of supported locales
    rating = Column(Float, default=0.0)
    contact_email = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="vendor")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    sector = Column(String(100), nullable=False)
    source_locale = Column(String(10), nullable=False)
    target_locales = Column(JSON, nullable=False)  # List of target locales
    content = Column(Text)
    client = Column(String(255))
    priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM)
    due_date = Column(DateTime)
    estimated_word_count = Column(Integer)
    budget = Column(Float)
    description = Column(Text)
    status = Column(Enum(JobStatus), default=JobStatus.INTAKE)
    progress = Column(Float, default=0.0)
    config_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Foreign keys
    connector_id = Column(GUID(), ForeignKey("connectors.id"))
    assigned_vendor_id = Column(GUID(), ForeignKey("vendors.id"))
    assigned_user_id = Column(GUID(), ForeignKey("users.id"))
    
    # Relationships
    connector = relationship("Connector", back_populates="projects")
    vendor = relationship("Vendor", back_populates="projects")
    assigned_user = relationship("User", back_populates="projects")
    segments = relationship("TranslationSegment", back_populates="project", cascade="all, delete-orphan")
    workflow_steps = relationship("WorkflowStep", back_populates="project", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReport", back_populates="project", cascade="all, delete-orphan")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    automated = Column(Boolean, default=False)
    assignee = Column(String(255))
    status = Column(Enum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # Foreign key
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="workflow_steps")


class TranslationSegment(Base):
    __tablename__ = "translation_segments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    source_text = Column(Text, nullable=False)
    target_locale = Column(String(10), nullable=False)
    tm_suggestion = Column(Text)
    tm_score = Column(Float)
    nmt_suggestion = Column(Text)
    post_edit = Column(Text)
    reviewer_notes = Column(Text)
    risk_level = Column(Enum(RiskLevel))
    quality_estimate = Column(Float)
    qa_flags = Column(JSON)  # List of QA flags
    term_hits = Column(JSON)  # List of term hits
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Foreign key
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="segments")


class TranslationMemory(Base):
    __tablename__ = "translation_memory"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    source_locale = Column(String(10), nullable=False)
    target_locale = Column(String(10), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tm_source_target', 'source_locale', 'target_locale'),
        Index('idx_tm_usage_count', 'usage_count'),
    )


class TermEntry(Base):
    __tablename__ = "term_entries"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sector = Column(String(100), nullable=False)
    source_locale = Column(String(10), nullable=False)
    target_locale = Column(String(10), nullable=False)
    term = Column(String(255), nullable=False)
    translation = Column(String(255), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_term_sector_locales', 'sector', 'source_locale', 'target_locale'),
    )


class QualityReport(Base):
    __tablename__ = "quality_reports"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    mtqe_score = Column(Float, nullable=False)
    mqm_errors = Column(JSON)  # Dict of error types and counts
    comments = Column(Text)
    submitted_at = Column(DateTime, default=func.now())
    compliance_flags = Column(JSON)  # Dict of compliance flags
    
    # Foreign keys
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    reviewer_id = Column(GUID(), ForeignKey("users.id"))
    
    # Relationships
    project = relationship("Project", back_populates="quality_reports")
    reviewer = relationship("User", back_populates="quality_reports")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"))
    project_id = Column(GUID(), ForeignKey("projects.id"))
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_created_at', 'created_at'),
        Index('idx_activity_category', 'category'),
    )
