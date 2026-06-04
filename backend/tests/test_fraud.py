"""
Insurance Claim Pre-Assurance – Fraud Detection Tests (Sprint 3)

Covers:
  POST /fraud/check/{claim_id}    – full fraud result
  GET  /fraud/signals/{claim_id}  – signals-only view

All checks use the real fraud_service logic (no mocks) so the rule
engine itself is tested, not just the route wiring.
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from tests.conftest import SAMPLE_CLAIM_PAYLOAD


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_claim(client, overrides: dict = {}) -> str:
    """Create a claim and return its ID."""
    payload = {**SAMPLE_CLAIM_PAYLOAD, **overrides}
    resp = client.post("/claims/create", json=payload)
    assert resp.status_code == 201, resp.json()
    return resp.json()["id"]


def _upload_doc(client, claim_id: str, doc_type: str = "claim_form") -> str:
    """Upload a minimal in-memory PDF to a claim; return document ID."""
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n9\n%%EOF"
    )
    resp = client.post(
        f"/claims/{claim_id}/upload-document",
        data={"document_type": doc_type},
        files={"file": ("test.pdf", minimal_pdf, "application/pdf")},
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()["id"]


# ── 404 cases ─────────────────────────────────────────────────────────────────

def test_check_nonexistent_claim_returns_404(client: TestClient) -> None:
    """POST /fraud/check with fake ID → 404."""
    resp = client.post("/fraud/check/CLM-FAKE-000000")
    assert resp.status_code == 404


def test_signals_nonexistent_claim_returns_404(client: TestClient) -> None:
    """GET /fraud/signals with fake ID → 404."""
    resp = client.get("/fraud/signals/CLM-FAKE-000000")
    assert resp.status_code == 404


# ── CLEAR / no signals ────────────────────────────────────────────────────────

def test_check_no_signals_for_clean_claim(client: TestClient) -> None:
    """
    A claim with:
      - amount < ₹5L
      - weekday incident
      - non-round amount
      - sufficient documents (claim_form + discharge_summary)
    should have risk_level CLEAR or only LOW signals.
    """
    # Wednesday, non-round, within threshold
    weekday = date(2026, 5, 6)   # Wednesday
    claim_id = _create_claim(client, {
        "claim_amount": 45_500.0,
        "incident_date": str(weekday),
        "policy_type": "health",
    })
    _upload_doc(client, claim_id, "claim_form")
    _upload_doc(client, claim_id, "discharge_summary")

    resp = client.post(f"/fraud/check/{claim_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["claim_id"] == claim_id
    assert "risk_level" in data
    assert "risk_score" in data
    assert "signals" in data
    # Should have no HIGH signals
    high_signals = [s for s in data["signals"] if s["severity"] == "HIGH"]
    assert len(high_signals) == 0


# ── HIGH_VALUE ────────────────────────────────────────────────────────────────

def test_high_value_signal_triggered(client: TestClient) -> None:
    """Claim above ₹5L threshold must trigger HIGH_VALUE signal."""
    claim_id = _create_claim(client, {"claim_amount": 600_000.0})

    resp = client.post(f"/fraud/check/{claim_id}")
    assert resp.status_code == 200
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "HIGH_VALUE" in codes

    # Find the specific signal and check its severity
    hv = next(s for s in resp.json()["signals"] if s["code"] == "HIGH_VALUE")
    assert hv["severity"] == "HIGH"
    assert resp.json()["risk_level"] in ("HIGH", "CRITICAL")


def test_high_value_signal_not_triggered_below_threshold(client: TestClient) -> None:
    """Claim below ₹5L must NOT trigger HIGH_VALUE."""
    claim_id = _create_claim(client, {"claim_amount": 499_999.0})

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "HIGH_VALUE" not in codes


# ── INSUFFICIENT_DOCS ─────────────────────────────────────────────────────────

def test_insufficient_docs_signal_triggered(client: TestClient) -> None:
    """New claim with 0 documents must trigger INSUFFICIENT_DOCS."""
    claim_id = _create_claim(client)

    resp = client.post(f"/fraud/check/{claim_id}")
    assert resp.status_code == 200
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "INSUFFICIENT_DOCS" in codes


def test_insufficient_docs_cleared_after_upload(client: TestClient) -> None:
    """After uploading 2+ documents, INSUFFICIENT_DOCS must not appear."""
    claim_id = _create_claim(client)
    _upload_doc(client, claim_id, "claim_form")
    _upload_doc(client, claim_id, "discharge_summary")

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "INSUFFICIENT_DOCS" not in codes


# ── MISSING_DISCHARGE_SUMMARY ─────────────────────────────────────────────────

def test_missing_discharge_summary_for_health_claim(client: TestClient) -> None:
    """Health claim without discharge_summary → MISSING_DISCHARGE_SUMMARY."""
    claim_id = _create_claim(client, {"policy_type": "health", "domain": "health"})
    _upload_doc(client, claim_id, "claim_form")
    _upload_doc(client, claim_id, "bill")

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "MISSING_DISCHARGE_SUMMARY" in codes


def test_no_discharge_summary_check_for_motor_claim(client: TestClient) -> None:
    """Motor claim should NOT trigger MISSING_DISCHARGE_SUMMARY."""
    claim_id = _create_claim(client, {"policy_type": "motor", "domain": "motor"})
    _upload_doc(client, claim_id, "claim_form")
    _upload_doc(client, claim_id, "bill")

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "MISSING_DISCHARGE_SUMMARY" not in codes


# ── WEEKEND_ADMISSION ─────────────────────────────────────────────────────────

def test_weekend_admission_signal_triggered(client: TestClient) -> None:
    """Incident on Saturday must trigger WEEKEND_ADMISSION."""
    saturday = date(2026, 5, 2)  # Saturday
    claim_id = _create_claim(client, {"incident_date": str(saturday)})

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "WEEKEND_ADMISSION" in codes

    wa = next(s for s in resp.json()["signals"] if s["code"] == "WEEKEND_ADMISSION")
    assert wa["severity"] == "LOW"
    assert wa["detail"]["day"] == "Saturday"


def test_weekday_admission_no_signal(client: TestClient) -> None:
    """Incident on a Tuesday must NOT trigger WEEKEND_ADMISSION."""
    tuesday = date(2026, 5, 5)   # Tuesday
    claim_id = _create_claim(client, {"incident_date": str(tuesday)})

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "WEEKEND_ADMISSION" not in codes


# ── ROUND_AMOUNT ──────────────────────────────────────────────────────────────

def test_round_amount_signal_triggered(client: TestClient) -> None:
    """₹1,00,000 is a round multiple of 10,000 above threshold — flag it."""
    claim_id = _create_claim(client, {"claim_amount": 100_000.0})

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "ROUND_AMOUNT" in codes


def test_round_amount_not_triggered_for_small_amount(client: TestClient) -> None:
    """₹40,000 is round but below the ₹50,000 minimum — should NOT flag."""
    claim_id = _create_claim(client, {"claim_amount": 40_000.0})

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "ROUND_AMOUNT" not in codes


# ── MISSING_CLAIM_FORM ────────────────────────────────────────────────────────

def test_missing_claim_form_signal(client: TestClient) -> None:
    """Claim with only a bill and no claim_form → MISSING_CLAIM_FORM."""
    claim_id = _create_claim(client)
    _upload_doc(client, claim_id, "bill")
    _upload_doc(client, claim_id, "discharge_summary")

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "MISSING_CLAIM_FORM" in codes


def test_missing_claim_form_cleared(client: TestClient) -> None:
    """After uploading claim_form, MISSING_CLAIM_FORM must not appear."""
    claim_id = _create_claim(client)
    _upload_doc(client, claim_id, "claim_form")

    resp = client.post(f"/fraud/check/{claim_id}")
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "MISSING_CLAIM_FORM" not in codes


# ── DUPLICATE_POLICY_ACTIVE ───────────────────────────────────────────────────

def test_duplicate_policy_active_signal(client: TestClient) -> None:
    """Two PENDING claims with the same policy number → DUPLICATE_POLICY_ACTIVE."""
    shared_policy = "POL-DUPLICATE-001"
    claim_id_1 = _create_claim(client, {"policy_number": shared_policy})
    claim_id_2 = _create_claim(client, {"policy_number": shared_policy})

    # Check the second claim — should see the first as a duplicate
    resp = client.post(f"/fraud/check/{claim_id_2}")
    assert resp.status_code == 200
    codes = [s["code"] for s in resp.json()["signals"]]
    assert "DUPLICATE_POLICY_ACTIVE" in codes

    dp = next(s for s in resp.json()["signals"] if s["code"] == "DUPLICATE_POLICY_ACTIVE")
    assert dp["severity"] == "HIGH"
    assert claim_id_1 in dp["detail"]["open_claim_ids"]


# ── /fraud/signals endpoint ───────────────────────────────────────────────────

def test_get_signals_response_shape(client: TestClient) -> None:
    """GET /fraud/signals must return claim_id, risk_level, signal_count, signals."""
    claim_id = _create_claim(client)

    resp = client.get(f"/fraud/signals/{claim_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim_id
    assert "risk_level" in data
    assert "signal_count" in data
    assert isinstance(data["signals"], list)


# ── Risk score ────────────────────────────────────────────────────────────────

def test_risk_score_increases_with_more_signals(client: TestClient) -> None:
    """A claim with HIGH_VALUE + DUPLICATE should score higher than one without."""
    # High-risk claim
    shared_policy = "POL-RISK-TEST-001"
    _create_claim(client, {"policy_number": shared_policy})  # creates first claim
    high_risk_id = _create_claim(client, {
        "policy_number": shared_policy,
        "claim_amount": 600_000.0,
    })

    # Low-risk claim
    low_risk_id = _create_claim(client, {
        "claim_amount": 45_000.0,
        "incident_date": "2026-05-06",  # Wednesday
    })
    _upload_doc(client, low_risk_id, "claim_form")
    _upload_doc(client, low_risk_id, "discharge_summary")

    high_resp = client.post(f"/fraud/check/{high_risk_id}").json()
    low_resp  = client.post(f"/fraud/check/{low_risk_id}").json()

    assert high_resp["risk_score"] > low_resp["risk_score"]
