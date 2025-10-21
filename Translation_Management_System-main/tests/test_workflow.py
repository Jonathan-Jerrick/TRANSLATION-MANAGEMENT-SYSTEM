"""Integration style tests covering the enhanced TMS prototype endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_connector_sync_and_studio_snapshot() -> None:
    connectors_resp = client.get("/connectors")
    connectors_resp.raise_for_status()
    connectors = connectors_resp.json()
    connector_id = next(connector["id"] for connector in connectors if connector["id"] != "manual-intake")

    tm_resp = client.post(
        "/translation-memory",
        params={
            "source_locale": "en-US",
            "target_locale": "es-ES",
            "source_text": "Firmware update",
            "translated_text": "Actualización de firmware",
        },
    )
    tm_resp.raise_for_status()

    job_resp = client.post(
        f"/connectors/{connector_id}/content",
        json={
            "content_id": "firmware_notice",
            "source_locale": "en-US",
            "target_locales": ["es-ES"],
            "content": "Firmware update required before activation.",
            "name": "Firmware Notice",
            "priority": "high",
            "estimated_word_count": 120,
        },
    )
    job_resp.raise_for_status()
    job = job_resp.json()

    assert job["workflow"][0]["status"] == "in_progress"
    assert job["segments"][0]["nmt_suggestion"]
    assert job["segments"][0]["quality_estimate"] is not None

    segment_id = job["segments"][0]["id"]
    update_resp = client.post(
        f"/projects/{job['id']}/segments/{segment_id}",
        json={"post_edit": "Actualización de firmware obligatoria.", "reviewer_notes": "Approved"},
    )
    update_resp.raise_for_status()

    complete_resp = client.post(
        f"/jobs/{job['id']}/steps/intake_review/complete",
        json={},
    )
    complete_resp.raise_for_status()
    updated_job = complete_resp.json()
    assert updated_job["workflow"][0]["status"] == "completed"

    snapshot_resp = client.get(
        f"/translation-studio/{job['id']}",
        params={"target_locale": job["target_locales"][0]},
    )
    snapshot_resp.raise_for_status()
    snapshot = snapshot_resp.json()

    assert snapshot["segments"][0]["post_edit"] == "Actualización de firmware obligatoria."
    assert snapshot["translation_memory"]
    assert snapshot["qa_insights"]

    quality_resp = client.post(
        f"/jobs/{job['id']}/quality",
        json={"mtqe_score": 87.5, "mqm_errors": {"terminology": 1}},
    )
    quality_resp.raise_for_status()
    job_with_quality = quality_resp.json()
    assert job_with_quality["quality_reports"][0]["mtqe_score"] == 87.5


def test_dashboard_and_analytics_overview() -> None:
    dashboard_resp = client.get("/dashboard/summary")
    dashboard_resp.raise_for_status()
    dashboard = dashboard_resp.json()
    assert dashboard["active_projects"] >= 1
    assert dashboard["recent_activity"]

    analytics_resp = client.get("/analytics/overview")
    analytics_resp.raise_for_status()
    analytics = analytics_resp.json()
    assert analytics["total_earnings"] > 0
    assert analytics["earnings_trend"]
    assert analytics["time_tracking"]["trend"]

    vendors_resp = client.get("/vendors")
    vendors_resp.raise_for_status()
    vendors = vendors_resp.json()
    assert any(vendor["active"] for vendor in vendors)
