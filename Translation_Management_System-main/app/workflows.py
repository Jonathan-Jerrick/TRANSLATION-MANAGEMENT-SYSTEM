"""Workflow orchestration helpers for the TMS prototype."""
from __future__ import annotations

from typing import Dict, List

from .models import JobStatus, WorkflowStep, WorkflowStepStatus


SECTOR_WORKFLOWS: Dict[str, List[Dict[str, object]]] = {
    "legal": [
        {"name": "intake_review", "automated": False, "assignee": "legal_pm"},
        {"name": "human_translation", "automated": False, "assignee": "linguist"},
        {"name": "compliance_review", "automated": False, "assignee": "legal_reviewer"},
        {"name": "qa_checks", "automated": True, "assignee": "quality_bot"},
        {"name": "signoff", "automated": False, "assignee": "legal_pm"},
    ],
    "bfsi": [
        {"name": "intake_review", "automated": False, "assignee": "program_manager"},
        {"name": "pii_masking", "automated": True, "assignee": "privacy_bot"},
        {"name": "nmt_translation", "automated": True, "assignee": "nmt_engine"},
        {"name": "human_post_edit", "automated": False, "assignee": "post_editor"},
        {"name": "qa_checks", "automated": True, "assignee": "quality_bot"},
    ],
    "ecommerce": [
        {"name": "intake_review", "automated": True, "assignee": "connector"},
        {"name": "nmt_translation", "automated": True, "assignee": "nmt_engine"},
        {"name": "light_review", "automated": False, "assignee": "reviewer"},
        {"name": "launch_ready", "automated": True, "assignee": "connector"},
    ],
}

DEFAULT_WORKFLOW = [
    {"name": "intake_review", "automated": True, "assignee": "connector"},
    {"name": "nmt_translation", "automated": True, "assignee": "nmt_engine"},
    {"name": "human_post_edit", "automated": False, "assignee": "post_editor"},
    {"name": "qa_checks", "automated": True, "assignee": "quality_bot"},
]


def build_workflow(sector: str) -> List[WorkflowStep]:
    """Return a workflow tailored to the sector."""

    steps = SECTOR_WORKFLOWS.get(sector.lower(), DEFAULT_WORKFLOW)
    workflow = [WorkflowStep(**step) for step in steps]
    if workflow:
        workflow[0].status = WorkflowStepStatus.IN_PROGRESS
    return workflow


def advance_workflow(workflow: List[WorkflowStep]) -> None:
    """Advance workflow state machine to the next pending step."""

    for index, step in enumerate(workflow):
        if step.status == WorkflowStepStatus.IN_PROGRESS:
            step.status = WorkflowStepStatus.COMPLETED
            if index + 1 < len(workflow):
                next_step = workflow[index + 1]
                if next_step.status == WorkflowStepStatus.PENDING:
                    next_step.status = WorkflowStepStatus.IN_PROGRESS
            break


def workflow_status(workflow: List[WorkflowStep]) -> JobStatus:
    """Compute a job's aggregate status from its workflow."""

    if not workflow:
        return JobStatus.COMPLETED

    if all(step.status == WorkflowStepStatus.COMPLETED for step in workflow):
        return JobStatus.COMPLETED

    if workflow[0].status == WorkflowStepStatus.IN_PROGRESS:
        return JobStatus.INTAKE

    return JobStatus.IN_PROGRESS
