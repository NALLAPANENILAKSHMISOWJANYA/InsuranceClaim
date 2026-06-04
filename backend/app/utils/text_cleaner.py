"""
Insurance Claim Pre-Assurance – OCR Text Post-Processor
Cleans raw extracted text before storing in the database.
"""
import re
import unicodedata


def clean_text(raw_text: str) -> str:
    """
    Normalise and clean raw OCR/pdfplumber output.
    Steps:
      1. Unicode normalisation (NFKC)
      2. Remove non-printable control characters
      3. Collapse excessive whitespace
      4. Strip leading/trailing whitespace per line
      5. Remove blank lines (keep at most one blank line between paragraphs)
    """
    if not raw_text:
        return ""

    text = unicodedata.normalize("NFKC", raw_text)
    text = _remove_control_chars(text)
    text = _collapse_whitespace(text)
    text = _clean_lines(text)
    return text.strip()


def _remove_control_chars(text: str) -> str:
    """Remove non-printable ASCII control characters (except \\n and \\t)."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def _collapse_whitespace(text: str) -> str:
    """Replace multiple spaces/tabs on the same line with a single space."""
    return re.sub(r"[ \t]+", " ", text)


def _clean_lines(text: str) -> str:
    """Strip each line and collapse consecutive blank lines to one."""
    lines = [line.strip() for line in text.splitlines()]
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = is_blank
    return "\n".join(cleaned)
