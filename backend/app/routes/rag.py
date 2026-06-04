"""
Insurance Claim Pre-Assurance – RAG Router (Sprint 3)
Endpoints for policy knowledge base indexing and semantic search.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request/Response Schemas ──────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000, examples=["What is the room rent sub-limit?"])
    top_k: int = Field(5, ge=1, le=20, description="Max number of policy chunks to return")
    insurer: str | None = Field(None, description="Optional filter: only return chunks from this insurer")
    policy_type: str | None = Field(None, description="Optional filter: only return chunks of this policy type")


class ChunkResult(BaseModel):
    text: str
    source: str
    page: int
    insurer: str
    policy_type: str
    score: float


class RAGQueryResponse(BaseModel):
    query: str
    total_results: int
    chunks: list[ChunkResult]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/rebuild-index",
    summary="Rebuild FAISS index from all policy PDFs",
    response_description="Summary of how many PDFs and chunks were indexed",
)
def rebuild_index() -> dict:
    """
    Scans `datasets/policies/<insurer>/` sub-folders for PDF files,
    extracts text, chunks it, embeds with SentenceTransformer, and
    builds/saves a FAISS flat-L2 index.

    This is a synchronous operation — expect a few seconds for large PDF sets.
    Call this endpoint whenever new policy PDFs are added to the dataset.
    """
    try:
        summary = rag_service.rebuild()
        return {
            "status": "success",
            "pdfs_scanned": summary["pdfs_scanned"],
            "chunks_indexed": summary["chunks_indexed"],
            "vector_dimension": summary["vector_dimension"],
            "message": (
                f"Index built from {summary['pdfs_scanned']} PDF(s), "
                f"{summary['chunks_indexed']} chunk(s) indexed."
                if summary["chunks_indexed"] > 0
                else (
                    "No PDF content found. "
                    "Add policy PDFs to datasets/policies/<insurer>/ and retry."
                )
            ),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("RAG rebuild failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {exc}")


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Semantic search against the policy knowledge base",
)
def rag_query(payload: RAGQueryRequest) -> RAGQueryResponse:
    """
    Encode the query with the same embedding model used at index time,
    then retrieve the top-k most relevant policy chunks via FAISS.

    Optionally filter results by `insurer` or `policy_type`.

    **Use this before prompting the LLM** to ground the answer in actual
    policy text rather than hallucinated content.
    """
    status = rag_service.get_status()
    if not status["index_exists"] or status["vector_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail="Policy index is empty. POST /rag/rebuild-index first.",
        )

    try:
        results = rag_service.search(payload.query, top_k=payload.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("RAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")

    # Optional client-side filters
    if payload.insurer:
        results = [r for r in results if r.get("insurer") == payload.insurer]
    if payload.policy_type:
        results = [r for r in results if r.get("policy_type") == payload.policy_type]

    chunks = [
        ChunkResult(
            text=r["text"],
            source=r["source"],
            page=r["page"],
            insurer=r["insurer"],
            policy_type=r["policy_type"],
            score=r["score"],
        )
        for r in results
    ]

    return RAGQueryResponse(
        query=payload.query,
        total_results=len(chunks),
        chunks=chunks,
    )


@router.get(
    "/index-status",
    summary="Check RAG index status and vector count",
)
def index_status() -> dict:
    """
    Returns whether the FAISS index exists on disk, how many vectors it contains,
    and which source PDFs were indexed.
    """
    return rag_service.get_status()
