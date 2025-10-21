"""FastAPI application exposing a feature-rich Translation Management System prototype."""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import structlog

from .database import get_db, create_tables
from .auth import get_current_user, authenticate_user, create_access_token, get_password_hash
from .llm_service import LLMService
from .websocket_manager import manager, websocket_handler
from .bootstrap import seed_initial_data
from .models import (
    AnalyticsOverview,
    AnalyticsSummary,
    Connector,
    ConnectorCreate,
    ContentSyncRequest,
    DashboardSummary,
    Job,
    JobStepCompletion,
    ProjectCreate,
    ProjectPriority,
    QualityReport,
    SegmentUpdate,
    StudioSnapshot,
    TranslationMemoryEntry,
    TranslationSegment,
    Vendor,
    WorkflowStepStatus,
    UserCreate,
    UserLogin,
    UserResponse,
)
from .services import (
    JobService,
    NMTService,
    ProjectService,
    TermBaseService,
    TranslationMemoryService,
)
from .state import state
from .db_models import User, Project, TranslationSegment as DBSegment
import json


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Translation Management System",
    description=(
        "Comprehensive TMS prototype showcasing automated connectors, "
        "human-in-the-loop NMT, analytics, and CAT collaboration experiences."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
llm_service = LLMService()


tm_service = TranslationMemoryService(state)
term_service = TermBaseService(state)
nmt_service = NMTService()
project_service = ProjectService(state, tm_service, term_service, nmt_service)
job_service = JobService(state, tm_service, project_service)

# Create database tables
create_tables()

# Seed initial data
seed_initial_data(state, project_service, tm_service, term_service)


# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse, summary="Register a new user")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info("User registered", user_id=str(user.id), email=user.email)
    return UserResponse.from_orm(user)


@app.post("/auth/login", summary="Login user")
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse.from_orm(user)}


@app.get("/auth/me", response_model=UserResponse, summary="Get current user")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.from_orm(current_user)


# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time collaboration."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await websocket_handler.handle_message(websocket, user_id, message, next(get_db()))
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info("WebSocket disconnected", user_id=user_id)


# File upload endpoints
@app.post("/upload", summary="Upload file for translation")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file for translation."""
    # Validate file type
    allowed_types = [".txt", ".docx", ".pdf", ".xlsx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    # Create upload directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, f"{uuid4()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    logger.info("File uploaded", user_id=str(current_user.id), file_path=file_path)
    return {"filename": file.filename, "file_path": file_path, "size": len(content)}


# LLM-powered translation endpoints
@app.post("/translate", summary="Translate text using LLM")
async def translate_text(
    source_text: str = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    context: Optional[str] = Form(None),
    provider: str = Form("openai"),
    current_user: User = Depends(get_current_user)
):
    """Translate text using LLM service."""
    result = await llm_service.translate_text(
        source_text, source_lang, target_lang, context, provider
    )
    logger.info("Translation completed", user_id=str(current_user.id), provider=provider)
    return result


@app.post("/quality-estimate", summary="Estimate translation quality")
async def estimate_quality(
    source_text: str = Form(...),
    translated_text: str = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Estimate translation quality using LLM."""
    result = await llm_service.estimate_quality(
        source_text, translated_text, source_lang, target_lang
    )
    logger.info("Quality estimation completed", user_id=str(current_user.id))
    return result


@app.post("/suggest-improvements", summary="Get translation improvement suggestions")
async def suggest_improvements(
    source_text: str = Form(...),
    translated_text: str = Form(...),
    context: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Get suggestions for improving a translation."""
    suggestions = await llm_service.suggest_improvements(source_text, translated_text, context)
    logger.info("Improvement suggestions generated", user_id=str(current_user.id))
    return {"suggestions": suggestions}


# Enhanced project endpoints with database integration
@app.get("/projects/{project_id}/segments", response_model=List[TranslationSegment], summary="Get project segments")
def get_project_segments(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all segments for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    segments = db.query(DBSegment).filter(DBSegment.project_id == project_id).all()
    return [TranslationSegment.from_orm(segment) for segment in segments]


@app.post("/projects/{project_id}/segments/{segment_id}/update", response_model=TranslationSegment, summary="Update segment")
def update_segment(
    project_id: str,
    segment_id: str,
    segment_update: SegmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a translation segment."""
    segment = db.query(DBSegment).filter(
        DBSegment.id == segment_id,
        DBSegment.project_id == project_id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    if segment_update.post_edit:
        segment.post_edit = segment_update.post_edit
    if segment_update.reviewer_notes:
        segment.reviewer_notes = segment_update.reviewer_notes
    
    segment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(segment)
    
    logger.info("Segment updated", user_id=str(current_user.id), segment_id=segment_id)
    return TranslationSegment.from_orm(segment)


@app.post("/connectors", response_model=Connector, summary="Register a new connector")
def create_connector(payload: ConnectorCreate) -> Connector:
    connector = Connector(
        id=str(uuid4()),
        created_at=datetime.utcnow(),
        **payload.dict(),
    )
    state.add_connector(connector)
    return connector


@app.get("/connectors", response_model=List[Connector], summary="List registered connectors")
def list_connectors() -> List[Connector]:
    return state.list_connectors()


@app.post(
    "/connectors/{connector_id}/content",
    response_model=Job,
    summary="Push new or updated content into the TMS",
)
def sync_content(connector_id: str, payload: ContentSyncRequest) -> Job:
    try:
        connector = state.get_connector(connector_id)
    except KeyError as exc:  # pragma: no cover - FastAPI handles 404 conversion
        raise HTTPException(status_code=404, detail="Connector not found") from exc

    if payload.priority:
        try:
            priority = ProjectPriority(payload.priority.lower())
        except ValueError:
            priority = ProjectPriority.MEDIUM
    else:
        priority = ProjectPriority.MEDIUM
    project_payload = ProjectCreate(
        name=payload.name or payload.metadata.get("title", payload.content_id),
        sector=connector.sector,
        source_locale=payload.source_locale,
        target_locales=payload.target_locales,
        content=payload.content,
        client=payload.client or payload.metadata.get("client"),
        priority=priority,
        due_date=payload.due_date,
        estimated_word_count=payload.estimated_word_count,
        budget=payload.budget,
        description=payload.description,
        assigned_vendor_id=payload.assigned_vendor_id,
        connector_id=connector.id,
        metadata=payload.metadata,
    )
    job = project_service.create_project(project_payload)
    connector.last_synced_at = datetime.utcnow()
    connector.last_sync_status = "success"
    state.update_connector(connector)
    return job


@app.get("/jobs", response_model=List[Job], summary="List translation jobs")
def list_jobs() -> List[Job]:
    return state.list_jobs()


@app.get("/projects", response_model=List[Job], summary="List projects")
def list_projects() -> List[Job]:
    return project_service.list_projects()


@app.post("/projects", response_model=Job, summary="Create a project manually")
def create_project(payload: ProjectCreate) -> Job:
    job = project_service.create_project(payload)
    return job


@app.post("/projects/{project_id}/segments/{segment_id}", response_model=TranslationSegment)
def update_segment(project_id: str, segment_id: str, payload: SegmentUpdate) -> TranslationSegment:
    try:
        return project_service.update_segment(project_id, segment_id, payload)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Segment not found") from exc


@app.post("/translation-memory", response_model=TranslationMemoryEntry, summary="Add TM entry")
def add_translation_memory_entry(
    source_locale: str,
    target_locale: str,
    source_text: str,
    translated_text: str,
) -> TranslationMemoryEntry:
    return tm_service.add_entry(source_locale, target_locale, source_text, translated_text)


@app.get("/translation-studio/{project_id}", response_model=StudioSnapshot, summary="CAT workspace snapshot")
def translation_studio(project_id: str, target_locale: str = Query(..., description="Target locale to inspect")) -> StudioSnapshot:
    try:
        return project_service.studio_snapshot(project_id, target_locale)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.post("/jobs/{job_id}/steps/{step_name}/complete", response_model=Job)
def complete_step(job_id: str, step_name: str, payload: JobStepCompletion) -> Job:
    try:
        job = state.get_job(job_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Job not found") from exc

    step_lookup = {step.name: step for step in job.workflow}
    if step_name not in step_lookup:
        raise HTTPException(status_code=400, detail="Unknown workflow step")

    if step_lookup[step_name].status != WorkflowStepStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Step is not in progress")

    updated_job = job_service.complete_step(job, payload)
    return updated_job


@app.post("/jobs/{job_id}/quality", response_model=Job, summary="Submit a quality report")
def submit_quality(job_id: str, payload: QualityReport) -> Job:
    try:
        job = state.get_job(job_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Job not found") from exc

    updated_job = job_service.add_quality_report(job, payload)
    return updated_job


@app.get("/analytics/summary", response_model=AnalyticsSummary, summary="Platform analytics")
def analytics_summary() -> AnalyticsSummary:
    return state.analytics_summary()


@app.get("/analytics/overview", response_model=AnalyticsOverview, summary="Detailed analytics overview")
def analytics_overview() -> AnalyticsOverview:
    return state.analytics_overview()


@app.get("/dashboard/summary", response_model=DashboardSummary, summary="Dashboard metrics")
def dashboard_summary() -> DashboardSummary:
    return state.dashboard_summary()


@app.get("/vendors", response_model=List[Vendor], summary="List integrated vendors")
def list_vendors() -> List[Vendor]:
    return state.list_vendors()


@app.get("/health", summary="Health check")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
