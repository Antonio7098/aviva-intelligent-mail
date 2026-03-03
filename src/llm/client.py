"""Abstract interface for LLM clients.

This module defines the LLMClient Protocol that all LLM provider implementations
must adhere to. This abstraction allows for:
- Easy switching between LLM providers (OpenAI, Anthropic, Azure, etc.)
- Dependency injection of LLM clients into pipeline stages
- Unit testing with mock implementations
"""

from typing import Any, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from src.domain.email import RedactedEmail


T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """Abstract interface for LLM providers.

    This Protocol defines the contract that all LLM client implementations
    must follow. Implementations should support:
    - Structured JSON output for classification
    - Structured JSON output for action extraction
    - Configurable temperature for deterministic outputs
    - Audit trail information (model name, version)

    Example implementations:
    - OpenAIClient: Using OpenAI SDK (works with OpenRouter via base_url)
    - AnthropicClient: Using Anthropic SDK
    - AzureOpenAIClient: Using Azure OpenAI Service
    - MockLLMClient: For testing

    Usage with dependency injection:
        class MyStage:
            def __init__(self, llm_client: LLMClient):
                self._llm_client = llm_client

            async def process(self, email: RedactedEmail):
                result = await self._llm_client.classify(email)
    """

    @property
    def model_name(self) -> str:
        """Return the model name being used.

        Returns:
            The name of the model (e.g., 'gpt-4o-mini', 'claude-3-opus')
        """
        ...

    @property
    def model_version(self) -> str:
        """Return the model version or tag.

        Returns:
            The version string of the model
        """
        ...

    async def classify(
        self,
        email: RedactedEmail,
        prompt_version: str = "v1.0",
    ) -> dict[str, Any]:
        """Classify a redacted email into a category.

        Args:
            email: The redacted email to classify (no raw PII)
            prompt_version: Version of the prompt template to use

        Returns:
            Dictionary containing:
            - classification: Category string (e.g., 'new_claim', 'complaint')
            - confidence: Confidence score (0.0-1.0)
            - priority: Priority level (e.g., 'p1_critical', 'p4_low')
            - rationale: Human-readable explanation
            - risk_tags: List of applicable risk tags

        Raises:
            LLMError: If the classification fails
        """
        ...

    async def extract_actions(
        self,
        email: RedactedEmail,
        prompt_version: str = "v1.0",
    ) -> dict[str, Any]:
        """Extract required actions from a redacted email.

        Args:
            email: The redacted email to extract actions from
            prompt_version: Version of the prompt template to use

        Returns:
            Dictionary containing:
            - actions: List of action objects with:
                - action_type: Type of action (e.g., 'call_back', 'escalate')
                - entity_refs: Dictionary of entity references
                - deadline: Optional deadline ISO string
                - notes: Optional notes for handler
            - confidence: Confidence score for extraction

        Raises:
            LLMError: If action extraction fails
        """
        ...

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        response_model: type[BaseModel] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response using the LLM.

        This is a general-purpose method for more flexible LLM usage.
        For classification and action extraction, use the dedicated methods
        which include prompt versioning and structured output handling.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting (0.0 for deterministic)
            response_model: Optional Pydantic model for structured output

        Returns:
            Generated text or parsed JSON if response_model provided

        Raises:
            LLMError: If generation fails
        """
        ...


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        is_retryable: bool = False,
    ):
        super().__init__(message)
        self.model_name = model_name
        self.is_retryable = is_retryable


class LLMValidationError(LLMError):
    """Exception raised when LLM output fails validation."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        validation_errors: list[str] | None = None,
    ):
        super().__init__(message, model_name, is_retryable=False)
        self.validation_errors = validation_errors or []


class LLMTimeoutError(LLMError):
    """Exception raised when LLM request times out."""

    def __init__(self, message: str, model_name: str | None = None):
        super().__init__(message, model_name, is_retryable=True)


class LLMRateLimitError(LLMError):
    """Exception raised when LLM rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message, model_name, is_retryable=True)
        self.retry_after = retry_after
