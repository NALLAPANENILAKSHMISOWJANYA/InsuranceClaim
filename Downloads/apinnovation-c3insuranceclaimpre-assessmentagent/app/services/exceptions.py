"""Service-layer exceptions."""


class ClaimNotFoundError(Exception):
    """Raised when a claim cannot be located."""

    def __init__(self, claim_id: str) -> None:
        self.claim_id = claim_id
        super().__init__(f"Claim '{claim_id}' not found")
