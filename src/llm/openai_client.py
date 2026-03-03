"""OpenAI SDK implementation of LLM client using Instructor.

This module provides an LLM client implementation using the Instructor library.
Instructor provides:
- Structured JSON output using Pydantic models
- Automatic retry on validation failure
- Multi-provider support (OpenAI, OpenRouter, etc.)

Configuration is provided via constructor for dependency injection.
"""

import logging
import os

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.domain.email import RedactedEmail
from src.llm.client import (
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMValidationError,
)
from src.llm.schemas import ClassificationOutput, ActionExtractionOutput

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI SDK implementation of LLM client using Instructor.

    Connects to OpenRouter (https://openrouter.ai) for:
    - Privacy: No data retention by OpenAI
    - Cost: Competitive pricing
    - Model selection: Access to many models

    Usage:
        client = OpenAIClient(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model="nvidia/nemotron-3-nano-30b-a3b:free",
        )
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        model: str = "",
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """Initialize the OpenAI client with Instructor.

        Args:
            base_url: Base URL for API (defaults to OpenRouter)
            api_key: API key for authentication
            model: Model name (defaults to nvidia/nemotron-3-nano-30b-a3b:free)
            max_retries: Maximum retries on validation failure (Instructor handles this)
            timeout: Request timeout in seconds
        """
        self._model = model or self.DEFAULT_MODEL
        self._max_retries = max_retries
        self._timeout = timeout

        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self._client = instructor.from_openai(
            client=AsyncOpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
                timeout=timeout,
                max_retries=0,
            ),
            mode=instructor.Mode.JSON,
        )

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def model_version(self) -> str:
        return "latest"

    async def classify(
        self, email: RedactedEmail, prompt_version: str = "v1.0"
    ) -> ClassificationOutput:
        """Classify an email using the LLM.

        Args:
            email: Redacted email to classify
            prompt_version: Version of prompt to use

        Returns:
            ClassificationOutput with classification, confidence, priority, and rationale
        """
        from src.llm.prompts import get_classification_prompt, sanitize_user_input

        prompt = get_classification_prompt(prompt_version)
        email_text = f"Subject: {email.subject}\n\n{email.body_text}"
        email_text = sanitize_user_input(email_text)

        try:
            result = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": email_text},
                ],
                response_model=ClassificationOutput,
                max_retries=self._max_retries,
                temperature=0.0,
                max_tokens=1024,
            )
            return result
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                logger.error(f"LLM timeout: {e}")
                raise LLMTimeoutError(f"LLM request timed out: {e}") from e
            elif "rate limit" in error_msg.lower():
                logger.error(f"LLM rate limit: {e}")
                raise LLMRateLimitError(f"LLM rate limit exceeded: {e}") from e
            elif "validation" in error_msg.lower():
                logger.error(f"LLM validation error: {e}")
                raise LLMValidationError(f"LLM response validation failed: {e}") from e
            else:
                logger.error(f"LLM error: {e}")
                raise LLMError(f"LLM request failed: {e}") from e

    async def extract_actions(
        self, email: RedactedEmail, prompt_version: str = "v1.0"
    ) -> ActionExtractionOutput:
        """Extract required actions from an email using the LLM.

        Args:
            email: Redacted email to extract actions from
            prompt_version: Version of prompt to use

        Returns:
            ActionExtractionOutput with list of actions and confidence
        """
        from src.llm.prompts import get_action_extraction_prompt, sanitize_user_input

        prompt = get_action_extraction_prompt(prompt_version)
        email_text = f"Subject: {email.subject}\n\n{email.body_text}"
        email_text = sanitize_user_input(email_text)

        try:
            result = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": email_text},
                ],
                response_model=ActionExtractionOutput,
                max_retries=self._max_retries,
                temperature=0.0,
                max_tokens=1024,
            )
            return result
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                logger.error(f"LLM timeout: {e}")
                raise LLMTimeoutError(f"LLM request timed out: {e}") from e
            elif "rate limit" in error_msg.lower():
                logger.error(f"LLM rate limit: {e}")
                raise LLMRateLimitError(f"LLM rate limit exceeded: {e}") from e
            elif "validation" in error_msg.lower():
                logger.error(f"LLM validation error: {e}")
                raise LLMValidationError(f"LLM response validation failed: {e}") from e
            else:
                logger.error(f"LLM error: {e}")
                raise LLMError(f"LLM request failed: {e}") from e

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        response_model: type[BaseModel] | None = None,
    ) -> str | BaseModel:
        """Generate a response using the LLM.

        This is a general-purpose method for more flexible LLM usage.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature setting (0.0 for deterministic)
            response_model: Optional Pydantic model for structured output

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if response_model:
                result = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,  # type: ignore[arg-type]
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=2048,
                )
                return result.model_dump_json()  # type: ignore[return-value]
            else:
                result = await self._client.chat.completions.create(  # type: ignore[call-overload]
                    model=self._model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=2048,
                )
                return result.choices[0].message.content or ""  # type: ignore[union-attr]
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            raise LLMError(f"LLM generation failed: {e}") from e


def create_openai_client(api_key: str = "", **kwargs) -> OpenAIClient:
    """Create an OpenAI client with Instructor.

    Args:
        api_key: API key for OpenRouter
        **kwargs: Additional arguments to pass to OpenAIClient

    Returns:
        OpenAIClient instance
    """
    return OpenAIClient(api_key=api_key, **kwargs)
