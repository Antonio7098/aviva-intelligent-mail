"""LLM-based classification stage for the pipeline.

This stage replaces the placeholder classification with LLM-based
classification using the LLMClient interface. It provides:
- LLM-powered email classification via Instructor (auto-retries on validation failure)
- Structured output validation via Pydantic schemas
- Events for observability via ctx.try_emit_event()
- Retry config for stageflow interceptor
"""

import logging

from stageflow import StageKind, StageOutput

from src.domain.email import RedactedEmail
from src.llm.client import LLMClient, LLMValidationError
from src.llm.prompts import CURRENT_CLASSIFICATION_VERSION
from src.llm.schemas import safe_validate_classification

logger = logging.getLogger(__name__)


class LLMClassificationStage:
    """Stage 2: LLM-based email classification.

    This stage uses an LLM client to classify emails into categories
    with confidence scores and priority levels.

    Uses Instructor for:
    - Structured JSON output via Pydantic models
    - Automatic retry on validation failure

    Uses stageflow for:
    - ctx.try_emit_event() for observability
    - retry_config for retry interceptor
    - Circuit breaker from default interceptors

    Dependency Injection:
        The stage accepts LLMClient via constructor,
        enabling easy testing and configuration.
    """

    name = "llm_classification"
    kind = StageKind.ENRICH

    retry_config = {
        "max_attempts": 3,
        "base_delay_ms": 500,
        "backoff_strategy": "exponential",
    }

    def __init__(
        self,
        llm_client: "LLMClient" = None,  # type: ignore[assignment]
        prompt_version: str = CURRENT_CLASSIFICATION_VERSION,
    ):
        """Initialize the LLM classification stage.

        Args:
            llm_client: LLM client for classification (required)
            prompt_version: Version of prompt template to use
        """
        if llm_client is None:
            raise ValueError("llm_client is required")
        self._llm_client = llm_client
        self._prompt_version = prompt_version

    def _create_redacted_email(self, ctx) -> RedactedEmail:
        """Create RedactedEmail from stage context."""
        from src.domain.email import create_redacted_email_from_data

        redaction_data = {
            "email_hash": ctx.inputs.get_from(
                "minimisation_redaction", "email_hash", default=""
            ),
            "subject": ctx.inputs.get_from(
                "minimisation_redaction", "subject", default=""
            ),
            "body_text": ctx.inputs.get_from(
                "minimisation_redaction", "body_text", default=""
            ),
            "sender": ctx.inputs.get_from(
                "minimisation_redaction", "sender", default=""
            ),
            "recipient": ctx.inputs.get_from(
                "minimisation_redaction", "recipient", default=""
            ),
        }
        return create_redacted_email_from_data(redaction_data)

    async def execute(self, ctx) -> StageOutput:
        """Execute the LLM classification stage.

        Args:
            ctx: Stage context with input data from redaction stage

        Returns:
            StageOutput with classification results
        """
        try:
            ctx.try_emit_event("llm_classification.started", {"stage": self.name})

            email = self._create_redacted_email(ctx)

            raw_result = await self._llm_client.classify(
                email=email,
                prompt_version=self._prompt_version,
            )

            if hasattr(raw_result, "model_dump"):
                raw_data = raw_result.model_dump()
            elif isinstance(raw_result, dict):
                raw_data = raw_result
            else:
                raw_data = {
                    "classification": "general",
                    "priority": "p4_low",
                    "confidence": 0.0,
                }
            validation_result = safe_validate_classification(raw_data)

            if not validation_result.is_valid:
                error_msg = f"Validation failed: {validation_result.errors}"
                ctx.try_emit_event(
                    "llm_classification.validation_failed",
                    {
                        "error": error_msg,
                        "email_hash": email.email_hash,
                    },
                )
                return StageOutput.fail(
                    error=error_msg,
                    data={
                        "stage": self.name,
                        "error_type": "validation_error",
                        "safe_mode": True,
                    },
                )

            from typing import Any

            validated_data: dict[str, Any] = validation_result.data or {}
            classification = str(validated_data.get("classification", "general"))
            confidence = float(validated_data.get("confidence", 0.5))
            priority = str(validated_data.get("priority", "p4_low"))
            rationale = str(validated_data.get("rationale", ""))
            risk_tags = list(validated_data.get("risk_tags", []))

            ctx.try_emit_event(
                "llm_classification.completed",
                {
                    "email_hash": email.email_hash,
                    "classification": classification,
                    "priority": priority,
                    "confidence": confidence,
                    "model_name": self._llm_client.model_name,
                    "model_version": self._llm_client.model_version,
                    "prompt_version": self._prompt_version,
                },
            )

            logger.info(
                "Email classified via LLM",
                extra={
                    "email_hash": email.email_hash,
                    "classification": classification,
                    "priority": priority,
                    "confidence": confidence,
                    "model": self._llm_client.model_name,
                    "prompt_version": self._prompt_version,
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email.email_hash,
                classification=classification,
                confidence=confidence,
                priority=priority,
                rationale=rationale,
                risk_tags=risk_tags,
                required_actions=[],
                model_name=self._llm_client.model_name,
                model_version=self._llm_client.model_version,
                prompt_version=self._prompt_version,
            )

        except LLMValidationError as e:
            logger.error(f"Classification validation failed: {e}")
            ctx.try_emit_event(
                "llm_classification.error",
                {
                    "error_type": "validation_error",
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Classification validation failed: {e}",
                data={
                    "stage": self.name,
                    "error_type": "validation_error",
                    "safe_mode": True,
                },
            )
        except Exception as e:
            logger.exception("Error in LLM classification stage")
            ctx.try_emit_event(
                "llm_classification.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Classification error: {e}",
                data={
                    "stage": self.name,
                    "error_type": type(e).__name__,
                    "safe_mode": True,
                },
            )
