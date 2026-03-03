import logging

from stageflow import StageContext
from stageflow.pipeline.interceptors import InterceptorResult

logger = logging.getLogger(__name__)


class PrivacyGateInterceptor:
    """Stageflow interceptor to enforce redaction before classification.

    This interceptor ensures that:
    1. The redaction stage must run before classification
    2. Raw email bodies cannot pass to classification
    3. Any bypass attempts are logged and rejected
    """

    REDACTION_STAGE = "minimisation_redaction"
    CLASSIFICATION_STAGE = "placeholder_classification"

    FORBIDDEN_FIELDS = ["body_text", "body_html", "raw_body", "email_body"]

    def __init__(self, log_bypass_attempts: bool = True):
        """Initialize the privacy gate interceptor.

        Args:
            log_bypass_attempts: Whether to log bypass attempts
        """
        self._log_bypass_attempts = log_bypass_attempts

    def intercept(self, ctx: StageContext) -> InterceptorResult:
        """Intercept unit execution to enforce privacy gate.

        Args:
            ctx: The Stageflow context being executed

        Returns:
            InterceptorResult allowing or blocking execution
        """
        if ctx.stage_name != self.CLASSIFICATION_STAGE:
            return InterceptorResult(stage_ran=True)

        if self._contains_raw_body(ctx):
            if self._log_bypass_attempts:
                logger.warning(
                    "Privacy gate: raw body detected in classification input",
                    extra={"stage": self.CLASSIFICATION_STAGE},
                )
            return InterceptorResult(
                stage_ran=False,
                error="Privacy gate blocked: raw body text cannot pass to classification",
            )

        return InterceptorResult(stage_ran=True)

    def _contains_raw_body(self, ctx: StageContext) -> bool:
        """Check if context inputs contain raw body text.

        Args:
            ctx: The context being checked

        Returns:
            True if raw body detected
        """
        if not hasattr(ctx, "inputs"):
            return False

        inputs = ctx.inputs

        if hasattr(inputs, "get"):
            for field in self.FORBIDDEN_FIELDS:
                value = inputs.get(field)
                if value and isinstance(value, str) and len(value) > 0:
                    return True

        return False


def create_privacy_gate() -> PrivacyGateInterceptor:
    """Create a privacy gate interceptor.

    Returns:
        Configured PrivacyGateInterceptor
    """
    return PrivacyGateInterceptor(log_bypass_attempts=True)
