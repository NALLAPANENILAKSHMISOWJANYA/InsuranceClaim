"""
Insurance Claim Pre-Assurance – Custom HTTP Exception Helpers
Centralised exception definitions keep routes thin and messages consistent.
"""
from fastapi import HTTPException, status


class ClaimNotFoundError(HTTPException):
    """Raised when a claim_id does not exist in the database."""

    def __init__(self, claim_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found.",
        )


class DocumentNotFoundError(HTTPException):
    """Raised when a document_id does not exist in the database."""

    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )


class AssessmentNotFoundError(HTTPException):
    """Raised when no assessment exists for a given claim."""

    def __init__(self, claim_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment found for claim '{claim_id}'.",
        )


class UnsupportedFileTypeError(HTTPException):
    """Raised when an uploaded file has an unsupported MIME type."""

    def __init__(self, mime_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{mime_type}' is not supported. "
                   "Allowed: application/pdf, image/jpeg, image/png.",
        )


class FileTooLargeError(HTTPException):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {max_mb} MB.",
        )


class RagIndexNotReadyError(HTTPException):
    """Raised when a RAG query is attempted before the index is built."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG index is not available. Run 'scripts/build_rag_index.py' first.",
        )
