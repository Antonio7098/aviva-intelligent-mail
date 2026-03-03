"""LLM module for email classification and action extraction.

This module provides:
- Abstract LLM client interface (llm/client.py)
- OpenAI SDK implementation (llm/openai_client.py)
- Prompt templates with versioning (llm/prompts/)
- Output validation schemas (llm/schemas.py)
- Failure handling utilities (llm/failures.py)
"""

from src.llm.client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    LLMValidationError,
    LLMRateLimitError,
)

from src.llm.failures import (
    SafeModeManager,
    log_safe_mode_trigger,
)

__all__ = [
    "LLMClient",
    "LLMError",
    "LLMTimeoutError",
    "LLMValidationError",
    "LLMRateLimitError",
    "SafeModeManager",
    "log_safe_mode_trigger",
]
