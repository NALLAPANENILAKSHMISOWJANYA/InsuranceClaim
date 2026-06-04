"""
Insurance Claim Pre-Assurance – OCR Service (Sprint 2)
Extracts text from uploaded PDFs and images using:
  - pdfplumber  → for text-layer PDFs (fast, no external binary needed)
  - pytesseract → for scanned image PDFs and JPEG/PNG files
                  (requires Tesseract binary; gracefully skipped if absent)
"""
import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

# ── Tesseract availability flag ───────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image
    pytesseract.get_tesseract_version()   # will raise if binary missing
    _TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available.")
except Exception:
    _TESSERACT_AVAILABLE = False
    logger.warning(
        "Tesseract binary not found. OCR will fall back to pdfplumber text "
        "extraction only. Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki"
    )


# ── Public API ────────────────────────────────────────────────────────────────

def extract_text(file_path: str | Path, mime_type: str) -> str:
    """
    Extract text from a file based on its MIME type.

    Returns the extracted text (may be empty string if nothing could be read).
    Never raises — errors are caught and logged so OCR failures do not crash a claim.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("OCR target file not found: %s", path)
        return ""

    try:
        if mime_type == "application/pdf":
            return _extract_from_pdf(path)
        elif mime_type in ("image/jpeg", "image/png"):
            return _extract_from_image(path)
        else:
            logger.warning("Unsupported MIME for OCR: %s", mime_type)
            return ""
    except Exception as exc:
        logger.exception("OCR extraction failed for %s: %s", path.name, exc)
        return ""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_from_pdf(path: Path) -> str:
    """
    Two-pass PDF extraction:
    1. pdfplumber  → fast, works on text-layer PDFs (e.g. digitally created)
    2. pytesseract → fallback for scanned/image-only PDFs (requires Tesseract)
    """
    text = _pdfplumber_extract(path)
    if text.strip():
        logger.info("pdfplumber extracted %d chars from %s", len(text), path.name)
        return text

    # No usable text layer — try image-based OCR
    if _TESSERACT_AVAILABLE:
        logger.info("pdfplumber found no text; attempting image OCR on %s", path.name)
        text = _tesseract_pdf_extract(path)
        logger.info("Tesseract extracted %d chars from %s", len(text), path.name)
        return text

    logger.warning(
        "No text found in PDF %s and Tesseract is unavailable. "
        "The document may be a scanned image PDF.",
        path.name,
    )
    return ""


def _pdfplumber_extract(path: Path) -> str:
    """Extract text from all pages of a PDF using pdfplumber."""
    pages_text: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
    return "\n".join(pages_text)


def _tesseract_pdf_extract(path: Path) -> str:
    """
    Convert each PDF page to an image and run Tesseract OCR.
    Uses pdf2image (poppler) for the conversion step.
    Gracefully skips if pdf2image/poppler is not available.
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
    except ImportError:
        logger.warning("pdf2image not installed; cannot do image OCR on PDF.")
        return ""

    pages_text: list[str] = []
    try:
        images = convert_from_path(str(path), dpi=200)
        for img in images:
            page_text = pytesseract.image_to_string(img)
            pages_text.append(page_text)
    except Exception as exc:
        logger.exception("pdf2image/tesseract conversion failed: %s", exc)

    return "\n".join(pages_text)


def _extract_from_image(path: Path) -> str:
    """Run Tesseract OCR directly on a JPEG or PNG image."""
    if not _TESSERACT_AVAILABLE:
        logger.warning("Tesseract unavailable; cannot OCR image %s", path.name)
        return ""

    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    logger.info("Tesseract extracted %d chars from image %s", len(text), path.name)
    return text
