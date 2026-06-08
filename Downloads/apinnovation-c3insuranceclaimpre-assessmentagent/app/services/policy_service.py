"""Policy business workflows."""

from __future__ import annotations

from typing import Any

from app.csv_store.policy_store import PolicyStore
from app.domain.rag.retriever import RAGRetriever


class PolicyService:
    """Provides policy retrieval and clause search orchestration."""

    def __init__(self, policy_store: PolicyStore) -> None:
        self._policy_store = policy_store

    def get_policy_by_number(self, policy_number: str) -> dict[str, Any] | None:
        """Return a single policy by policy number."""
        return self._policy_store.get_policy(policy_number)

    def get_policy_clauses(self) -> list[dict[str, Any]]:
        """Return all policy clauses."""
        return self._policy_store.get_policy_clauses()

    def search_clauses(self, query: str) -> list[dict[str, Any]]:
        """Search policy clauses using keyword retrieval."""
        retriever = RAGRetriever(self._policy_store.get_policy_clauses())
        return retriever.search(query)
