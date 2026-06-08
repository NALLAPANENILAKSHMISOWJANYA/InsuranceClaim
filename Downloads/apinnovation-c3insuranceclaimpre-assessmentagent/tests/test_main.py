"""Tests for ClaimSense AI API endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import PROJECT_ROOT, build_app, validate_datasets

DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Provide an isolated API client backed by a temporary data directory."""
    for filename in [
        "claims.csv",
        "policies.csv",
        "policy_clauses.csv",
        "audit_events.csv",
    ]:
        shutil.copy(DATA_DIR / filename, tmp_path / filename)

    (tmp_path / "audit_events.csv").write_text(
        "event_id,claim_id,event_type,actor,event_description,event_timestamp\n",
        encoding="utf-8",
    )

    test_app = build_app(data_dir=tmp_path)
    return TestClient(test_app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "ClaimSense AI Running"}


def test_list_claims(client: TestClient) -> None:
    response = client.get("/claims")
    assert response.status_code == 200

    claims = response.json()
    assert isinstance(claims, list)
    assert len(claims) > 0
    assert claims[0]["claim_id"] == "CP-H-001"


def test_get_claim_by_id(client: TestClient) -> None:
    response = client.get("/claims/CP-H-001")
    assert response.status_code == 200

    claim = response.json()
    assert claim["claim_id"] == "CP-H-001"
    assert claim["policy_number"] == "HG-2023-001"
    assert claim["claimant_name"] == "Ravi Shankar Rao"


def test_get_claim_not_found(client: TestClient) -> None:
    response = client.get("/claims/CP-MISSING")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_policy_by_number(client: TestClient) -> None:
    response = client.get("/policies/HG-2023-001")
    assert response.status_code == 200

    policy = response.json()
    assert policy["policy_number"] == "HG-2023-001"
    assert policy["insurance_type"] == "HEALTH"


def test_get_policy_not_found(client: TestClient) -> None:
    response = client.get("/policies/HG-9999-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_rag_search(client: TestClient) -> None:
    response = client.get("/rag/search", params={"q": "waiting"})
    assert response.status_code == 200

    clauses = response.json()
    assert isinstance(clauses, list)
    assert len(clauses) > 0
    assert any(
        "waiting" in str(clause.get("clause_text", "")).lower()
        or "waiting" in str(clause.get("clause_type", "")).lower()
        or "waiting" in str(clause.get("clause_name", "")).lower()
        for clause in clauses
    )


def test_rag_search_no_matches(client: TestClient) -> None:
    response = client.get("/rag/search", params={"q": "nonexistentkeyword"})
    assert response.status_code == 200
    assert response.json() == []


def test_pre_assessment(client: TestClient) -> None:
    response = client.get("/pre-assessment/CP-H-001")
    assert response.status_code == 200

    assessment = response.json()
    assert assessment["claim_id"] == "CP-H-001"
    assert assessment["claimant_name"] == "Ravi Shankar Rao"
    assert assessment["policy_number"] == "HG-2023-001"
    assert assessment["claimed_amount"] == 9000
    assert assessment["policy_found"] is True
    assert assessment["recommendation"] == "REVIEW_REQUIRED"
    assert assessment["generated_by"] == "ClaimSense AI"
    assert isinstance(assessment["relevant_clauses"], list)
    assert len(assessment["relevant_clauses"]) > 0
    assert all(
        clause["insurance_type"] == "HEALTH"
        for clause in assessment["relevant_clauses"]
    )


def test_pre_assessment_creates_audit_event(client: TestClient, tmp_path: Path) -> None:
    client.get("/pre-assessment/CP-H-001")

    audit_events = pd.read_csv(tmp_path / "audit_events.csv")
    assert len(audit_events) == 1
    assert audit_events.iloc[0]["claim_id"] == "CP-H-001"
    assert audit_events.iloc[0]["event_type"] == "PRE_ASSESSMENT"
    assert audit_events.iloc[0]["actor"] == "SYSTEM"


def test_pre_assessment_claim_not_found(client: TestClient) -> None:
    response = client.get("/pre-assessment/CP-MISSING")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_dashboard_stats(client: TestClient) -> None:
    response = client.get("/dashboard/stats")
    assert response.status_code == 200

    stats = response.json()
    assert stats == {
        "total_claims": 650,
        "health_claims": 150,
        "vehicle_claims": 150,
        "life_claims": 150,
        "home_claims": 100,
        "crop_claims": 100,
    }


def test_validate_datasets_raises_for_missing_file(tmp_path: Path) -> None:
    shutil.copy(DATA_DIR / "claims.csv", tmp_path / "claims.csv")

    with pytest.raises(RuntimeError, match="Missing required dataset: policies.csv"):
        validate_datasets(tmp_path)
