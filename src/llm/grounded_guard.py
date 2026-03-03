"""Grounded guard implementation for hallucination prevention.

This module provides a hallucination guard that:
- Checks retrieval confidence thresholds
- Validates citations in generated answers
- Returns "no evidence found" for weak retrieval
- Logs hallucination guard triggers
"""

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


class GroundedGuard:
    """Hallucination guard implementation.

    Provides:
    - Retrieval confidence threshold checking
    - Citation validation
    - "No evidence found" fallback for weak retrieval

    Usage:
        guard = GroundedGuard(
            min_retrieval_count=1,
            min_avg_score=0.3,
            require_citations=True,
        )

        is_sufficient, msg = guard.check_retrieval(count, avg_score)
        is_valid, citations = guard.validate_citations(answer, expected)
    """

    DEFAULT_MIN_RETRIEVAL_COUNT = 1
    DEFAULT_MIN_AVG_SCORE = 0.3
    DEFAULT_REQUIRE_CITATIONS = True

    def __init__(
        self,
        min_retrieval_count: int = DEFAULT_MIN_RETRIEVAL_COUNT,
        min_avg_score: float = DEFAULT_MIN_AVG_SCORE,
        require_citations: bool = DEFAULT_REQUIRE_CITATIONS,
    ):
        """Initialize the grounded guard.

        Args:
            min_retrieval_count: Minimum number of documents to retrieve
            min_avg_score: Minimum average similarity score
            require_citations: Whether to require citations in answers
        """
        self._min_retrieval_count = min_retrieval_count
        self._min_avg_score = min_avg_score
        self._require_citations = require_citations

    def check_retrieval(
        self,
        retrieval_count: int,
        avg_score: float,
    ) -> tuple[bool, str]:
        """Check if retrieval quality is sufficient.

        Args:
            retrieval_count: Number of documents retrieved
            avg_score: Average similarity score of retrieved documents

        Returns:
            Tuple of (is_sufficient, message)
        """
        if retrieval_count < self._min_retrieval_count:
            msg = (
                f"Retrieval too weak: only {retrieval_count} documents retrieved "
                f"(minimum: {self._min_retrieval_count})"
            )
            logger.warning(
                "Weak retrieval detected",
                extra={
                    "retrieval_count": retrieval_count,
                    "min_required": self._min_retrieval_count,
                    "avg_score": avg_score,
                },
            )
            return False, msg

        if avg_score < self._min_avg_score:
            msg = (
                f"Retrieval quality too low: avg score {avg_score:.3f} "
                f"(minimum: {self._min_avg_score})"
            )
            logger.warning(
                "Low retrieval quality detected",
                extra={
                    "retrieval_count": retrieval_count,
                    "avg_score": avg_score,
                    "min_required": self._min_avg_score,
                },
            )
            return False, msg

        return True, "Retrieval sufficient"

    def validate_citations(
        self,
        answer: str,
        expected_citations: list[str],
    ) -> tuple[bool, list[str]]:
        """Validate that answer contains expected citations.

        Args:
            answer: Generated answer text
            expected_citations: List of expected email_hash values

        Returns:
            Tuple of (is_valid, found_citations)
        """
        if not expected_citations:
            return True, []

        found_citations = self._extract_citations(answer)

        if not found_citations:
            logger.warning(
                "No citations found in answer",
                extra={
                    "expected": expected_citations,
                    "answer_preview": answer[:200],
                },
            )
            return False, []

        valid_citations = [c for c in found_citations if c in expected_citations]

        if not valid_citations and self._require_citations:
            logger.warning(
                "Invalid citations in answer",
                extra={
                    "found": found_citations,
                    "expected": expected_citations,
                },
            )
            return False, valid_citations

        return True, valid_citations

    def _extract_citations(self, answer: str) -> list[str]:
        """Extract email_hash citations from answer text.

        Supports formats:
        - [email_hash:XXX]
        - [XXX]
        - email_hash: XXX
        """
        citations = []

        pattern1 = r"\[email_hash:([^\]]+)\]"
        citations.extend(re.findall(pattern1, answer))

        pattern2 = r"\[([a-f0-9_]+)\]"
        potential = re.findall(pattern2, answer)
        for p in potential:
            if p.startswith("email_") or "_" in p:
                citations.append(p)

        pattern3 = r"email_hash:\s*([a-f0-9_]+)"
        citations.extend(re.findall(pattern3, answer, re.IGNORECASE))

        return list(set(citations))

    def should_reject(self, validation_result: dict[str, Any]) -> tuple[bool, str]:
        """Determine if answer should be rejected.

        Args:
            validation_result: Dictionary with validation results:
                - retrieval_sufficient: bool
                - citations_valid: bool
                - citations_count: int

        Returns:
            Tuple of (should_reject, reason)
        """
        if not validation_result.get("retrieval_sufficient", True):
            return True, "Weak retrieval - no evidence found"

        if self._require_citations:
            citations_valid = validation_result.get("citations_valid", True)
            citations_count = validation_result.get("citations_count", 0)

            if not citations_valid:
                return True, "Missing required citations"

            if citations_count == 0 and self._require_citations:
                return True, "No citations provided"

        return False, "Validation passed"

    def get_no_evidence_message(self) -> str:
        """Get the 'no evidence found' message."""
        return (
            "No evidence found in the available documents to answer this question. "
            "The retrieved documents do not contain sufficient information to provide a reliable answer."
        )

    def log_guard_trigger(
        self,
        guard_type: str,
        details: dict[str, Any],
    ) -> None:
        """Log hallucination guard trigger.

        Args:
            guard_type: Type of guard triggered
            details: Additional details about the trigger
        """
        logger.warning(
            "Hallucination guard triggered",
            extra={
                "guard_type": guard_type,
                **details,
            },
        )
