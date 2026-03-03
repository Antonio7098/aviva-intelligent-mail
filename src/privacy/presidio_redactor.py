import logging

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


logger = logging.getLogger(__name__)

PLACEHOLDERS = {
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[PHONE]",
    "UK_NINO": "[NINO]",
    "PERSON": "[PERSON]",
    "LOCATION": "[LOCATION]",
    "ORGANIZATION": "[ORGANIZATION]",
    "CUSTOM_CLAIM_ID": "[CLAIM_ID]",
    "CUSTOM_POLICY_NUMBER": "[POLICY_ID]",
    "CUSTOM_BROKER_REF": "[BROKER_REF]",
}


class PresidioRedactor:
    """Presidio-based PII detection and redaction implementation.

    Implements the PIIRedactor interface using Microsoft Presidio for
    detecting and redacting PII from text.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        safe_mode: bool = True,
    ):
        """Initialize the Presidio redactor.

        Args:
            confidence_threshold: Minimum confidence score for PII detection
            safe_mode: If True, fail on redaction errors; if False, return original text
        """
        self._confidence_threshold = confidence_threshold
        self._safe_mode = safe_mode

        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()

        self._add_custom_recognizers()

    def _add_custom_recognizers(self) -> None:
        """Add custom recognizers for insurance-specific PII patterns."""
        claim_id_pattern = Pattern(
            name="claim_id",
            regex=r"\b[A-Z]{2}-\d{6}\b",
            score=0.9,
        )
        claim_id_recognizer = PatternRecognizer(
            supported_entity="CUSTOM_CLAIM_ID",
            patterns=[claim_id_pattern],
            name="Claim ID Recognizer",
            supported_language="en",
        )

        policy_pattern = Pattern(
            name="policy_number",
            regex=r"\bPOL-\d{9}\b",
            score=0.9,
        )
        policy_recognizer = PatternRecognizer(
            supported_entity="CUSTOM_POLICY_NUMBER",
            patterns=[policy_pattern],
            name="Policy Number Recognizer",
            supported_language="en",
        )

        broker_pattern = Pattern(
            name="broker_reference",
            regex=r"\bBROK-\d{5}\b",
            score=0.9,
        )
        broker_recognizer = PatternRecognizer(
            supported_entity="CUSTOM_BROKER_REF",
            patterns=[broker_pattern],
            name="Broker Reference Recognizer",
            supported_language="en",
        )

        self._analyzer.registry.add_recognizer(claim_id_recognizer)
        self._analyzer.registry.add_recognizer(policy_recognizer)
        self._analyzer.registry.add_recognizer(broker_recognizer)

    def redact_text(self, text: str) -> tuple[str, dict[str, int]]:
        """Redact PII from text, replacing with consistent placeholders.

        Args:
            text: The text to redact PII from

        Returns:
            Tuple of (redacted text, PII counts by type)
        """
        if not text:
            return "", {}

        try:
            entities = self._analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self._confidence_threshold,
            )

            if not entities:
                return text, {}

            operator_config = self._build_operator_config()

            result = self._anonymizer.anonymize(
                text=text,
                analyzer_results=entities,
                operators=operator_config,
            )

            counts = self._count_entities(entities)

            return result.text, counts

        except Exception as e:
            logger.error(f"Error during redaction: {e}")
            if self._safe_mode:
                raise
            return text, {}

    def detect_pii(self, text: str) -> dict[str, list[dict]]:
        """Detect PII entities in text without redacting.

        Args:
            text: The text to scan for PII

        Returns:
            Dictionary mapping entity types to lists of detected entities
        """
        if not text:
            return {}

        try:
            entities = self._analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self._confidence_threshold,
            )

            result: dict[str, list[dict]] = {}
            for entity in entities:
                entity_type = entity.entity_type
                if entity_type not in result:
                    result[entity_type] = []
                result[entity_type].append(
                    {
                        "text": entity.text,
                        "start": entity.start,
                        "end": entity.end,
                        "score": entity.score,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error during PII detection: {e}")
            return {}

    def count_pii(self, text: str) -> dict[str, int]:
        """Count PII instances by type (without storing raw values).

        Args:
            text: The text to count PII in

        Returns:
            Dictionary mapping entity types to their counts
        """
        if not text:
            return {}

        try:
            entities = self._analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self._confidence_threshold,
            )

            return self._count_entities(entities)

        except Exception as e:
            logger.error(f"Error during PII counting: {e}")
            return {}

    def _build_operator_config(self) -> dict[str, OperatorConfig]:
        """Build operator configuration for anonymization."""
        operators: dict[str, OperatorConfig] = {}

        for entity_type, placeholder in PLACEHOLDERS.items():
            operators[entity_type] = OperatorConfig(
                operator_name="replace",
                params={"new_value": placeholder},
            )

        return operators

    def _count_entities(
        self,
        entities: list,
    ) -> dict[str, int]:
        """Count entities by type."""
        counts: dict[str, int] = {}

        entity_type_map = {
            "EMAIL_ADDRESS": "EMAIL",
            "PHONE_NUMBER": "PHONE",
            "UK_NINO": "NINO",
            "PERSON": "PERSON",
            "LOCATION": "LOCATION",
            "ORGANIZATION": "ORGANIZATION",
            "CUSTOM_CLAIM_ID": "CLAIM_ID",
            "CUSTOM_POLICY_NUMBER": "POLICY_ID",
            "CUSTOM_BROKER_REF": "BROKER_REF",
        }

        for entity in entities:
            entity_type = entity.entity_type
            display_type = entity_type_map.get(entity_type, entity_type)

            counts[display_type] = counts.get(display_type, 0) + 1

        return counts
