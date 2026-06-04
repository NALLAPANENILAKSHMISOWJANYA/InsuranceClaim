"""
Insurance Claim Pre-Assurance – RAG Endpoint Tests (Sprint 3)

Tests cover:
  - GET  /rag/index-status  → status when index missing vs present
  - POST /rag/rebuild-index → builds index from seed PDFs
  - POST /rag/query         → returns ranked chunks; validation errors
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── index-status (no index yet) ───────────────────────────────────────────────

def test_index_status_no_index(client: TestClient, tmp_path: Path) -> None:
    """GET /rag/index-status must report index_exists=False when no index on disk."""
    with patch("app.services.rag_service._INDEX_PATH", tmp_path / "faiss.index"), \
         patch("app.services.rag_service._METADATA_PATH", tmp_path / "metadata.json"), \
         patch("app.services.rag_service._index", None), \
         patch("app.services.rag_service._metadata", []):
        response = client.get("/rag/index-status")

    assert response.status_code == 200
    data = response.json()
    assert data["index_exists"] is False
    assert data["vector_count"] == 0
    assert "message" in data


# ── rebuild-index (mocked) ────────────────────────────────────────────────────

def test_rebuild_index_no_pdfs(client: TestClient) -> None:
    """
    POST /rag/rebuild-index with no PDFs in dataset should succeed but report 0 chunks.
    Mocked so the test doesn't require faiss/sentence-transformers to be installed.
    """
    mock_summary = {
        "pdfs_scanned": 0,
        "chunks_indexed": 0,
        "vector_dimension": 384,
    }
    with patch("app.services.rag_service.rebuild", return_value=mock_summary):
        response = client.post("/rag/rebuild-index")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pdfs_scanned"] == 0
    assert data["chunks_indexed"] == 0
    assert "No PDF content" in data["message"]


def test_rebuild_index_returns_summary(client: TestClient) -> None:
    """
    POST /rag/rebuild-index should return a valid summary dict.
    Mock rag_service.rebuild to avoid heavy ML model loading in tests.
    """
    mock_summary = {
        "pdfs_scanned": 3,
        "chunks_indexed": 42,
        "vector_dimension": 384,
    }
    with patch("app.services.rag_service.rebuild", return_value=mock_summary):
        response = client.post("/rag/rebuild-index")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pdfs_scanned"] == 3
    assert data["chunks_indexed"] == 42
    assert data["vector_dimension"] == 384
    assert "message" in data


def test_rebuild_index_503_on_missing_deps(client: TestClient) -> None:
    """POST /rag/rebuild-index must return 503 if ML deps are missing."""
    with patch(
        "app.services.rag_service.rebuild",
        side_effect=RuntimeError("faiss-cpu not installed"),
    ):
        response = client.post("/rag/rebuild-index")

    assert response.status_code == 503


# ── query ─────────────────────────────────────────────────────────────────────

def test_query_returns_404_when_no_index(client: TestClient) -> None:
    """POST /rag/query must return 404 when the index has not been built."""
    with patch(
        "app.services.rag_service.get_status",
        return_value={"index_exists": False, "vector_count": 0, "chunk_count": 0, "sources": []},
    ):
        response = client.post(
            "/rag/query",
            json={"query": "room rent limit", "top_k": 3},
        )

    assert response.status_code == 404


def test_query_returns_chunks(client: TestClient) -> None:
    """POST /rag/query must return ranked chunk results when index is populated."""
    mock_chunks = [
        {
            "text": "Room rent is limited to 1% of Sum Insured per day.",
            "source": "hdfc_ergo_health_policy.pdf",
            "page": 1,
            "insurer": "hdfc_ergo",
            "policy_type": "health",
            "score": 0.12,
        },
        {
            "text": "ICU charges capped at 2% of Sum Insured per day.",
            "source": "hdfc_ergo_health_policy.pdf",
            "page": 1,
            "insurer": "hdfc_ergo",
            "policy_type": "health",
            "score": 0.25,
        },
    ]
    with patch(
        "app.services.rag_service.get_status",
        return_value={"index_exists": True, "vector_count": 10, "chunk_count": 10, "sources": []},
    ), patch("app.services.rag_service.search", return_value=mock_chunks):
        response = client.post(
            "/rag/query",
            json={"query": "room rent sub-limit", "top_k": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert data["query"] == "room rent sub-limit"
    assert len(data["chunks"]) == 2
    assert data["chunks"][0]["insurer"] == "hdfc_ergo"
    assert "score" in data["chunks"][0]


def test_query_filter_by_insurer(client: TestClient) -> None:
    """POST /rag/query with insurer filter must only return matching chunks."""
    mock_chunks = [
        {
            "text": "Star Health room rent policy.",
            "source": "star_health_comprehensive.pdf",
            "page": 2,
            "insurer": "star_health",
            "policy_type": "health",
            "score": 0.15,
        },
        {
            "text": "HDFC room rent is 1%.",
            "source": "hdfc_ergo_health.pdf",
            "page": 1,
            "insurer": "hdfc_ergo",
            "policy_type": "health",
            "score": 0.20,
        },
    ]
    with patch(
        "app.services.rag_service.get_status",
        return_value={"index_exists": True, "vector_count": 10, "chunk_count": 10, "sources": []},
    ), patch("app.services.rag_service.search", return_value=mock_chunks):
        response = client.post(
            "/rag/query",
            json={"query": "room rent", "top_k": 5, "insurer": "star_health"},
        )

    assert response.status_code == 200
    data = response.json()
    # Only the star_health chunk should survive the filter
    assert data["total_results"] == 1
    assert data["chunks"][0]["insurer"] == "star_health"


def test_query_validation_short_query(client: TestClient) -> None:
    """POST /rag/query with a query shorter than 3 chars must return 422."""
    response = client.post("/rag/query", json={"query": "ab"})
    assert response.status_code == 422


def test_query_validation_top_k_exceeds_limit(client: TestClient) -> None:
    """POST /rag/query with top_k > 20 must return 422."""
    response = client.post(
        "/rag/query",
        json={"query": "waiting period", "top_k": 99},
    )
    assert response.status_code == 422


# ── index-status (with mock index) ───────────────────────────────────────────

def test_index_status_with_populated_index(client: TestClient) -> None:
    """GET /rag/index-status returns vector_count and sources when index exists."""
    mock_status = {
        "index_exists": True,
        "vector_count": 42,
        "chunk_count": 42,
        "sources": ["hdfc_ergo_health_policy.pdf", "star_health_comprehensive.pdf"],
        "message": "Index is ready.",
    }
    with patch("app.services.rag_service.get_status", return_value=mock_status):
        response = client.get("/rag/index-status")

    assert response.status_code == 200
    data = response.json()
    assert data["index_exists"] is True
    assert data["vector_count"] == 42
    assert len(data["sources"]) == 2
