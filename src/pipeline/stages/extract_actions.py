"""Action extraction stage for the pipeline.

This stage extracts required actions from emails using the LLM client.
It provides:
- LLM-powered action extraction via Instructor (auto-retries on validation failure)
- Structured output validation via Pydantic schemas
- Events for observability via ctx.try_emit_event()
- Retry config for stageflow interceptor
"""

import logging

from stageflow import StageKind, StageOutput

from src.domain.email import RedactedEmail
from src.llm.client import LLMClient, LLMValidationError
from src.llm.prompts import CURRENT_ACTION_EXTRACTION_VERSION
from src.llm.schemas import safe_validate_action_extraction

logger = logging.getLogger(__name__)


class ActionExtractionStage:
    """Stage 3: LLM-based action extraction.

    This stage uses an LLM client to extract required actions from emails.
    Actions include call backs, escalations, manual reviews, etc.

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

    name = "action_extraction"
    kind = StageKind.ENRICH

    retry_config = {
        "max_attempts": 3,
        "base_delay_ms": 500,
        "backoff_strategy": "exponential",
    }

    def __init__(
        self,
        llm_client: "LLMClient" = None,  # type: ignore[assignment]
        prompt_version: str = CURRENT_ACTION_EXTRACTION_VERSION,
    ):
        """Initialize the action extraction stage.

        Args:
            llm_client: LLM client for action extraction (required)
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
        """Execute the action extraction stage.

        Args:
            ctx: Stage context with input data

        Returns:
            StageOutput with extracted actions
        """
        try:
            ctx.try_emit_event("action_extraction.started", {"stage": self.name})

            email = self._create_redacted_email(ctx)

            raw_result = await self._llm_client.extract_actions(
                email=email,
                prompt_version=self._prompt_version,
            )

            raw_data = (
                raw_result.model_dump()
                if hasattr(raw_result, "model_dump")
                else dict(raw_result)
            )
            validation_result = safe_validate_action_extraction(raw_data)

            if not validation_result.is_valid:
                error_msg = f"Validation failed: {validation_result.errors}"
                ctx.try_emit_event(
                    "action_extraction.validation_failed",
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
            from src.domain.triage import ActionType, RequiredAction

            validated_data: dict[str, Any] = validation_result.data or {}
            actions_data = list(validated_data.get("actions", []))
            confidence = float(validated_data.get("confidence", 0.5))

            required_actions = []
            for action_dict in actions_data:
                action_type_str = action_dict.get("action_type", "manual_review")
                required_actions.append(
                    RequiredAction(
                        action_type=ActionType(action_type_str),
                        entity_refs=action_dict.get("entity_refs", {}),
                        deadline=None,
                        notes=action_dict.get("notes"),
                    )
                )

            ctx.try_emit_event(
                "action_extraction.completed",
                {
                    "email_hash": email.email_hash,
                    "actions_count": len(required_actions),
                    "confidence": confidence,
                    "model_name": self._llm_client.model_name,
                    "model_version": self._llm_client.model_version,
                    "prompt_version": self._prompt_version,
                },
            )

            logger.info(
                "Actions extracted via LLM",
                extra={
                    "email_hash": email.email_hash,
                    "actions_count": len(required_actions),
                    "confidence": confidence,
                    "model": self._llm_client.model_name,
                    "prompt_version": self._prompt_version,
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email.email_hash,
                actions=[
                    {
                        "action_type": a.action_type.value,
                        "entity_refs": a.entity_refs,
                        "deadline": a.deadline.isoformat() if a.deadline else None,
                        "notes": a.notes,
                    }
                    for a in required_actions
                ],
                confidence=confidence,
                model_name=self._llm_client.model_name,
                model_version=self._llm_client.model_version,
                prompt_version=self._prompt_version,
            )

        except LLMValidationError as e:
            logger.error(f"Action extraction validation failed: {e}")
            ctx.try_emit_event(
                "action_extraction.error",
                {
                    "error_type": "validation_error",
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Action extraction validation failed: {e}",
                data={
                    "stage": self.name,
                    "error_type": "validation_error",
                    "safe_mode": True,
                },
            )
        except Exception as e:
            logger.exception("Error in action extraction stage")
            ctx.try_emit_event(
                "action_extraction.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Action extraction error: {e}",
                data={
                    "stage": self.name,
                    "error_type": type(e).__name__,
                    "safe_mode": True,
                },
            )
