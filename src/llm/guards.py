"""Abstract interface for hallucination guards.

This module defines the HallucinationGuard Protocol that all hallucination
prevention implementations must adhere to. This abstraction allows for:
- Configurable retrieval confidence thresholds
- Citation validation
- "No evidence found" fallback for weak retrieval
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HallucinationGuard(Protocol):
    """Abstract interface for hallucination prevention.

    This Protocol defines the contract that all hallucination guard implementations
    must follow. Implementations should support:
    - Retrieval confidence threshold checking
    - Citation validation
    - "No evidence found" fallback for weak retrieval

    Example implementations:
    - GroundedGuard: Implementation with configurable thresholds
    - MockHallucinationGuard: For testing
    """

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
            - is_sufficient: True if retrieval is good enough
            - message: Explanation of the decision
        """
        ...

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
            - is_valid: True if citations are present
            - found_citations: List of found citation identifiers
        """
        ...

    def should_reject(self, validation_result: dict[str, Any]) -> tuple[bool, str]:
        """Determine if answer should be rejected.

        Args:
            validation_result: Dictionary with validation results

        Returns:
            Tuple of (should_reject, reason)
        """
        ...


class HallucinationDetectedError(Exception):
    """Exception raised when hallucination is detected."""

    def __init__(self, message: str, validation_errors: list[str] | None = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class WeakRetrievalError(Exception):
    """Exception raised when retrieval is too weak."""

    def __init__(self, message: str, retrieval_count: int = 0, avg_score: float = 0.0):
        super().__init__(message)
        self.retrieval_count = retrieval_count
        self.avg_score = avg_score
