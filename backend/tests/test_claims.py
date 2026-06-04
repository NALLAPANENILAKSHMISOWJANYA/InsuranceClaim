"""
Insurance Claim Pre-Assurance – Claims Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import SAMPLE_CLAIM_PAYLOAD


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_claim_returns_201(client: TestClient) -> None:
    """POST /claims/create must return 201 with a generated claim ID."""
    response = client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("CLM-")
    assert data["status"] == "PENDING"
    assert data["customer_name"] == SAMPLE_CLAIM_PAYLOAD["customer_name"]


def test_create_claim_missing_required_field_returns_422(client: TestClient) -> None:
    """Missing required fields must return 422 Unprocessable Entity."""
    bad_payload = {k: v for k, v in SAMPLE_CLAIM_PAYLOAD.items() if k != "policy_number"}
    response = client.post("/claims/create", json=bad_payload)
    assert response.status_code == 422


def test_create_claim_negative_amount_returns_422(client: TestClient) -> None:
    """Negative claim_amount must be rejected."""
    payload = {**SAMPLE_CLAIM_PAYLOAD, "claim_amount": -100}
    response = client.post("/claims/create", json=payload)
    assert response.status_code == 422


def test_create_claim_invalid_insurer_returns_422(client: TestClient) -> None:
    """Insurer value not in InsurerType enum must be rejected."""
    payload = {**SAMPLE_CLAIM_PAYLOAD, "insurer": "unknown_insurer"}
    response = client.post("/claims/create", json=payload)
    assert response.status_code == 422


# ── Read ──────────────────────────────────────────────────────────────────────

def test_get_claim_returns_correct_data(client: TestClient) -> None:
    """GET /claims/{id} must return the created claim."""
    create_resp = client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    claim_id = create_resp.json()["id"]

    get_resp = client.get(f"/claims/{claim_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == claim_id


def test_get_nonexistent_claim_returns_404(client: TestClient) -> None:
    """GET /claims/{id} with a fake ID must return 404."""
    response = client.get("/claims/CLM-FAKE-000000")
    assert response.status_code == 404


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_claims_returns_paginated_response(client: TestClient) -> None:
    """GET /claims must return total, page, page_size, and items."""
    # Create 2 claims
    client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    client.post("/claims/create", json={**SAMPLE_CLAIM_PAYLOAD, "policy_number": "TEST-002"})

    response = client.get("/claims?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert "items" in data
    assert data["page"] == 1


def test_list_claims_filter_by_status(client: TestClient) -> None:
    """Status filter must only return claims with matching status."""
    client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    response = client.get("/claims?status=PENDING")
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["status"] == "PENDING"


# ── Status Update ─────────────────────────────────────────────────────────────

def test_update_claim_status(client: TestClient) -> None:
    """PATCH /claims/{id}/status must update the claim status."""
    create_resp = client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    claim_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/claims/{claim_id}/status",
        json={"status": "UNDER_REVIEW", "notes": "Adjuster review started"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "UNDER_REVIEW"


def test_update_status_invalid_value_returns_422(client: TestClient) -> None:
    """Invalid status value must return 422."""
    create_resp = client.post("/claims/create", json=SAMPLE_CLAIM_PAYLOAD)
    claim_id = create_resp.json()["id"]

    response = client.patch(
        f"/claims/{claim_id}/status",
        json={"status": "APPROVED_AUTOMATICALLY"},
    )
    assert response.status_code == 422
