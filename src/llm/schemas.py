"""Output schema validation for LLM responses.

This module provides Pydantic-based validation for LLM outputs, ensuring
structured JSON responses conform to expected schemas.

The validation approach uses Pydantic models which provide:
- Type validation
- Enum constraint checking
- Confidence score bounds checking
- Required field validation
- Clear error messages

Usage:
    from src.llm.schemas import ClassificationOutput, validate_classification_output

    # Validate LLM output
    result = validate_classification_output(llm_output_dict)
"""

import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.domain.triage import Classification, Priority, RiskTag

logger = logging.getLogger(__name__)


class ClassificationOutput(BaseModel):
    """Pydantic schema for LLM classification output.

    This model validates the JSON response from the LLM classification
    endpoint, ensuring all required fields are present and valid.
    """

    classification: Classification = Field(
        ...,
        description="Email classification category",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for classification (0.0-1.0)",
    )
    priority: Priority = Field(
        ...,
        description="Assigned priority level",
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation for classification",
    )
    risk_tags: list[RiskTag] = Field(
        default_factory=list,
        description="Risk tags applied to the email",
    )

    model_config = {
        "use_enum_values": True,
    }


class ActionExtractionOutput(BaseModel):
    """Pydantic schema for LLM action extraction output.

    This model validates the JSON response from the LLM action extraction
    endpoint, ensuring all required fields are present and valid.
    """

    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of required actions",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for action extraction (0.0-1.0)",
    )

    model_config = {
        "use_enum_values": True,
    }


def validate_classification_output(data: dict[str, Any]) -> ClassificationOutput:
    """Validate LLM classification output against schema.

    Args:
        data: Raw dictionary from LLM response

    Returns:
        Validated ClassificationOutput instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        return ClassificationOutput(**data)
    except ValidationError as e:
        logger.error(f"Classification output validation failed: {e}")
        raise


def validate_action_extraction_output(data: dict[str, Any]) -> ActionExtractionOutput:
    """Validate LLM action extraction output against schema.

    Args:
        data: Raw dictionary from LLM response

    Returns:
        Validated ActionExtractionOutput instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        return ActionExtractionOutput(**data)
    except ValidationError as e:
        logger.error(f"Action extraction output validation failed: {e}")
        raise


class ValidationResult:
    """Result of LLM output validation.

    Encapsulates validation success/failure and any error details.
    """

    def __init__(
        self,
        is_valid: bool,
        data: dict[str, Any] | None = None,
        errors: list[str] | None = None,
    ):
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or []

    @classmethod
    def success(cls, data: dict[str, Any]) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, data=data)

    @classmethod
    def failure(cls, errors: list[str]) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(is_valid=False, errors=errors)


def safe_validate_classification(
    data: dict[str, Any],
) -> ValidationResult:
    """Safely validate classification output, returning result object.

    This function wraps validation in a try-except and returns a ValidationResult
    instead of raising exceptions, making it easier to handle in pipeline stages.

    Args:
        data: Raw dictionary from LLM response

    Returns:
        ValidationResult with success/failure status and data/errors
    """
    try:
        validated = validate_classification_output(data)
        return ValidationResult.success(validated.model_dump())
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return ValidationResult.failure(errors)


def safe_validate_action_extraction(
    data: dict[str, Any],
) -> ValidationResult:
    """Safely validate action extraction output, returning result object.

    This function wraps validation in a try-except and returns a ValidationResult
    instead of raising exceptions, making it easier to handle in pipeline stages.

    Args:
        data: Raw dictionary from LLM response

    Returns:
        ValidationResult with success/failure status and data/errors
    """
    try:
        validated = validate_action_extraction_output(data)
        return ValidationResult.success(validated.model_dump())
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return ValidationResult.failure(errors)


def validate_confidence_threshold(
    confidence: float,
    threshold: float = 0.5,
) -> bool:
    """Validate that confidence meets minimum threshold.

    Args:
        confidence: Confidence score to validate
        threshold: Minimum required confidence (default 0.5)

    Returns:
        True if confidence meets threshold

    Raises:
        ValueError: If confidence is below threshold
    """
    if confidence < threshold:
        raise ValueError(f"Confidence {confidence} below threshold {threshold}")
    return True


def validate_rationale_present(rationale: str) -> bool:
    """Validate that rationale field is present and non-empty.

    Args:
        rationale: Rationale string to validate

    Returns:
        True if rationale is valid

    Raises:
        ValueError: If rationale is missing or empty
    """
    if not rationale or not rationale.strip():
        raise ValueError("Rationale field is required and cannot be empty")
    return True


def validate_json_structure(data: dict[str, Any]) -> bool:
    """Validate that data is a valid JSON object.

    Args:
        data: Data to validate

    Returns:
        True if data is a valid dict

    Raises:
        ValueError: If data is not a valid JSON object
    """
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data).__name__}")
    return True
