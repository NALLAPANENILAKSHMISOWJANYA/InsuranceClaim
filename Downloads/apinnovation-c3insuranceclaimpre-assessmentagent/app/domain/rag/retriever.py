"""Keyword-based policy clause retrieval."""

from __future__ import annotations

from typing import Any



class RAGRetriever:
    """Retrieves relevant policy clauses using weighted keyword search."""

    CLAUSE_TEXT_WEIGHT = 3
    CLAUSE_NAME_WEIGHT = 2
    CLAUSE_TYPE_WEIGHT = 1

    def __init__(self, clauses: list[dict[str, Any]]) -> None:
        self._clauses = clauses

    @staticmethod
    def _tokenize_query(query: str) -> list[str]:
        """Split a query into lowercase keyword tokens."""
        return [token for token in query.lower().split() if token]

    @classmethod
    def _score_clause(cls, clause: dict[str, Any], tokens: list[str]) -> int:
        """Score a clause using weighted keyword matches."""
        clause_text = str(clause["clause_text"]).lower()
        clause_name = str(clause["clause_name"]).lower()
        clause_type = str(clause["clause_type"]).lower()

        score = 0
        for token in tokens:
            if token in clause_text:
                score += cls.CLAUSE_TEXT_WEIGHT
            if token in clause_name:
                score += cls.CLAUSE_NAME_WEIGHT
            if token in clause_type:
                score += cls.CLAUSE_TYPE_WEIGHT
        return score

    def _filter_clauses(self, insurance_type: str | None = None) -> list[dict[str, Any]]:
        if insurance_type is None:
            return list(self._clauses)
        return [
            clause
            for clause in self._clauses
            if clause["insurance_type"] == insurance_type
        ]

    def _rank_clauses(
        self,
        clauses: list[dict[str, Any]],
        query: str,
        insurance_type: str | None = None,
    ) -> list[dict[str, Any]]:
        tokens = self._tokenize_query(query)
        if not tokens:
            return clauses

        scored_clauses: list[tuple[int, dict[str, Any]]] = []
        for clause in clauses:
            score = self._score_clause(clause, tokens)
            if score > 0:
                scored_clauses.append((score, clause))

        if scored_clauses:
            scored_clauses.sort(key=lambda item: item[0], reverse=True)
            return [clause for _, clause in scored_clauses]

        if insurance_type:
            return clauses

        return []

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search all clauses using weighted keyword matching."""
        clauses = self._filter_clauses()
        return self._rank_clauses(clauses, query)

    def search_by_insurance_type(
        self,
        query: str,
        insurance_type: str,
    ) -> list[dict[str, Any]]:
        """Search clauses filtered by insurance type."""
        clauses = self._filter_clauses(insurance_type=insurance_type)
        return self._rank_clauses(clauses, query, insurance_type=insurance_type)
