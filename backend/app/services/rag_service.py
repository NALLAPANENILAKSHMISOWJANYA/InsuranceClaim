"""
Insurance Claim Pre-Assurance – RAG Service (Sprint 3)

Provides a Retrieval-Augmented Generation index over policy PDFs.

Pipeline:
  1. Ingest  → scan POLICY_DATASET_DIR for PDFs, extract text via pdfplumber
  2. Chunk   → split text into overlapping windows (CHUNK_SIZE / CHUNK_OVERLAP)
  3. Embed   → encode chunks with SentenceTransformer (all-MiniLM-L6-v2)
  4. Index   → store vectors in a FAISS flat-L2 index, persist to disk
  5. Search  → encode query, retrieve top-k nearest chunks

The index is persisted as two files in VECTOR_STORE_DIR:
  - faiss.index   (FAISS binary)
  - metadata.json (list of chunk dicts: source, page, text, insurer, policy_type)

Usage (from route layer):
    from app.services import rag_service
    rag_service.rebuild()          # re-ingest all PDFs
    results = rag_service.search("room rent limit", top_k=5)
    status  = rag_service.get_status()
"""

import json
import logging
from pathlib import Path
from typing import Any

import pdfplumber

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Index file paths ──────────────────────────────────────────────────────────
_INDEX_PATH    = settings.VECTOR_STORE_DIR / "faiss.index"
_METADATA_PATH = settings.VECTOR_STORE_DIR / "metadata.json"

# ── Lazy singletons ───────────────────────────────────────────────────────────
_index    = None   # faiss.IndexFlatL2 | None
_metadata: list[dict] = []  # parallel list of chunk dicts


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

def rebuild() -> dict:
    """
    Re-ingest all policy PDFs from POLICY_DATASET_DIR, rebuild the FAISS
    index, and persist it to VECTOR_STORE_DIR.

    Returns a summary dict: {pdfs_scanned, chunks_indexed, vector_dimension}.
    """
    global _index, _metadata

    try:
        import faiss  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "RAG dependencies missing. Run: pip install faiss-cpu sentence-transformers"
        ) from exc

    logger.info("RAG rebuild started. Scanning: %s", settings.POLICY_DATASET_DIR)

    # 1. Collect all PDFs
    all_pdfs = list(Path(settings.POLICY_DATASET_DIR).rglob("*.pdf"))
    logger.info("Found %d policy PDF(s).", len(all_pdfs))

    # 2. Extract + chunk
    chunks: list[dict] = []
    for pdf_path in all_pdfs:
        pdf_chunks = _extract_and_chunk(pdf_path)
        chunks.extend(pdf_chunks)
        logger.debug("  %s → %d chunk(s)", pdf_path.name, len(pdf_chunks))

    if not chunks:
        logger.warning(
            "No text chunks extracted. "
            "Place policy PDFs in %s/<insurer>/ sub-folders.",
            settings.POLICY_DATASET_DIR,
        )
        # Still save an empty index so status doesn't crash
        _index = faiss.IndexFlatL2(384)  # MiniLM dim
        _metadata = []
        _persist(_index, _metadata)
        return {"pdfs_scanned": len(all_pdfs), "chunks_indexed": 0, "vector_dimension": 384}

    # 3. Embed
    logger.info("Embedding %d chunks with model '%s'…", len(chunks), settings.EMBEDDING_MODEL)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)

    # 4. Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # 5. Persist
    _persist(index, chunks)
    _index = index
    _metadata = chunks

    summary = {
        "pdfs_scanned": len(all_pdfs),
        "chunks_indexed": len(chunks),
        "vector_dimension": dim,
    }
    logger.info("RAG index rebuilt: %s", summary)
    return summary


def search(query: str, top_k: int | None = None) -> list[dict]:
    """
    Semantic search over the policy index.

    Args:
        query:  Natural-language question (e.g. "Does room rent have a sub-limit?")
        top_k:  Number of results; defaults to settings.RAG_TOP_K

    Returns:
        List of chunk dicts ordered by relevance:
        [{"text", "source", "page", "insurer", "policy_type", "score"}, ...]
    """
    global _index, _metadata

    if top_k is None:
        top_k = settings.RAG_TOP_K

    try:
        import faiss  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise RuntimeError("RAG dependencies missing.") from exc

    # Lazy-load from disk if not in memory
    _ensure_loaded(faiss)

    if _index is None or _index.ntotal == 0:
        logger.warning("RAG index is empty. Call /rag/rebuild-index first.")
        return []

    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    query_vec = model.encode([query])

    k = min(top_k, _index.ntotal)
    distances, indices = _index.search(query_vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        chunk = dict(_metadata[idx])
        chunk["score"] = float(dist)   # lower = closer in L2
        results.append(chunk)

    return results


def get_status() -> dict:
    """Return index existence, vector count, and source PDF list."""
    global _index, _metadata

    index_exists = _INDEX_PATH.exists() and _METADATA_PATH.exists()

    if not index_exists:
        return {
            "index_exists": False,
            "vector_count": 0,
            "chunk_count": 0,
            "sources": [],
            "message": "Index not built yet. POST /rag/rebuild-index to create it.",
        }

    try:
        import faiss  # type: ignore
        _ensure_loaded(faiss)
    except Exception:
        return {"index_exists": True, "vector_count": 0, "chunk_count": 0, "sources": [], "message": "Failed to load index."}

    sources = sorted({c.get("source", "") for c in _metadata})
    return {
        "index_exists": True,
        "vector_count": _index.ntotal if _index else 0,
        "chunk_count": len(_metadata),
        "sources": sources,
        "message": "Index is ready.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _extract_and_chunk(pdf_path: Path) -> list[dict]:
    """
    Extract text from every page of a PDF and split into overlapping chunks.
    Returns a list of chunk dicts with source metadata.
    """
    # Derive insurer + policy_type from directory hierarchy
    # Expected layout: datasets/policies/<insurer>/<policy_type>/<file>.pdf
    #                  or: datasets/policies/<insurer>/<file>.pdf
    parts = pdf_path.relative_to(settings.POLICY_DATASET_DIR).parts
    insurer     = parts[0] if len(parts) >= 1 else "unknown"
    policy_type = parts[1] if len(parts) >= 3 else "general"

    chunks: list[dict] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if not text.strip():
                    continue
                page_chunks = _chunk_text(text)
                for chunk_text in page_chunks:
                    chunks.append({
                        "text": chunk_text,
                        "source": pdf_path.name,
                        "page": page_num,
                        "insurer": insurer,
                        "policy_type": policy_type,
                    })
    except Exception as exc:
        logger.error("Failed to extract PDF %s: %s", pdf_path.name, exc)

    return chunks


def _chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping windows.
    Uses character-level splitting for simplicity and predictable chunk sizes.
    """
    size    = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    chunks  = []
    start   = 0

    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap

    return chunks


def _persist(index: Any, metadata: list[dict]) -> None:
    """Save FAISS index and chunk metadata to disk."""
    try:
        import faiss  # type: ignore
        settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(_INDEX_PATH))
        _METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("RAG index persisted: %d vectors → %s", index.ntotal, _INDEX_PATH)
    except Exception as exc:
        logger.exception("Failed to persist RAG index: %s", exc)
        raise


def _ensure_loaded(faiss_module: Any) -> None:
    """Load index and metadata from disk into module-level singletons."""
    global _index, _metadata

    if _index is not None:
        return  # already in memory

    if not _INDEX_PATH.exists() or not _METADATA_PATH.exists():
        return  # nothing to load

    try:
        _index = faiss_module.read_index(str(_INDEX_PATH))
        _metadata = json.loads(_METADATA_PATH.read_text(encoding="utf-8"))
        logger.info("RAG index loaded from disk: %d vectors, %d chunks", _index.ntotal, len(_metadata))
    except Exception as exc:
        logger.exception("Failed to load RAG index from disk: %s", exc)
        _index = None
        _metadata = []
