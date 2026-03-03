"""Abstract interface for answer generation.

This module defines the AnswerGenerator Protocol that all answer generator
implementations must adhere to. This abstraction allows for:
- Easy switching between LLM providers
- Dependency injection into pipeline stages
- Unit testing with mock implementations
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AnswerGenerator(Protocol):
    """Abstract interface for answer generation.

    This Protocol defines the contract that all answer generator implementations
    must follow. Implementations should support:
    - Grounded answering using retrieved context
    - Citation of sources via email_hash
    - Constraint: no inference beyond retrieved items

    Example implementations:
    - GroundedAnswerer: LLM-based grounded answering
    - MockAnswerGenerator: For testing
    """

    async def generate_answer(
        self,
        question: str,
        context: str,
        citations: list[str],
    ) -> dict[str, Any]:
        """Generate an answer grounded in the provided context.

        Args:
            question: User question
            context: Retrieved context from vector store
            citations: List of email_hash references

        Returns:
            Dictionary containing:
            - answer: Generated answer text
            - citations: List of email_hash citations used
            - model_name: Model used for generation

        Raises:
            AnswerGenerationError: If answer generation fails
        """
        ...


class AnswerGenerationError(Exception):
    """Base exception for answer generation errors."""

    def __init__(self, message: str, is_retryable: bool = False):
        super().__init__(message)
        self.is_retryable = is_retryable


class GroundingError(AnswerGenerationError):
    """Exception raised when grounding fails."""

    def __init__(self, message: str):
        super().__init__(message, is_retryable=False)


class CitationError(AnswerGenerationError):
    """Exception raised when citation validation fails."""

    def __init__(self, message: str):
        super().__init__(message, is_retryable=False)
