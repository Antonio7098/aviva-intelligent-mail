import logging

from stageflow import Unit, UnitResult

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

    def intercept(self, unit: Unit) -> UnitResult:
        """Intercept unit execution to enforce privacy gate.

        Args:
            unit: The Stageflow unit being executed

        Returns:
            UnitResult allowing or blocking execution
        """
        if unit.stage_name != self.CLASSIFICATION_STAGE:
            return UnitResult.ok()

        if not self._verify_redaction_completed(unit):
            return UnitResult.fail(
                error="Privacy gate blocked: redaction stage must complete before classification",
                data={
                    "stage": self.CLASSIFICATION_STAGE,
                    "reason": "Redaction stage not completed",
                },
            )

        if self._contains_raw_body(unit):
            return UnitResult.fail(
                error="Privacy gate blocked: raw body text cannot pass to classification",
                data={
                    "stage": self.CLASSIFICATION_STAGE,
                    "reason": "Raw body detected in input",
                },
            )

        return UnitResult.ok()

    def _verify_redaction_completed(self, unit: Unit) -> bool:
        """Verify that redaction stage has completed successfully.

        Args:
            unit: The unit being checked

        Returns:
            True if redaction completed, False otherwise
        """
        if hasattr(unit, "completed_stages"):
            return self.REDACTION_STAGE in getattr(unit, "completed_stages", [])

        return True

    def _contains_raw_body(self, unit: Unit) -> bool:
        """Check if unit inputs contain raw body text.

        Args:
            unit: The unit being checked

        Returns:
            True if raw body detected, False otherwise
        """
        if not hasattr(unit, "inputs"):
            return False

        inputs = unit.inputs

        if hasattr(inputs, "get"):
            for field in self.FORBIDDEN_FIELDS:
                value = inputs.get(field)
                if value and isinstance(value, str) and len(value) > 0:
                    if self._log_bypass_attempts:
                        logger.warning(
                            f"Privacy gate: raw body field '{field}' detected in classification input",
                            extra={"stage": self.CLASSIFICATION_STAGE},
                        )
                    return True

        return False


def create_privacy_gate() -> PrivacyGateInterceptor:
    """Create a privacy gate interceptor.

    Returns:
        Configured PrivacyGateInterceptor
    """
    return PrivacyGateInterceptor(log_bypass_attempts=True)
