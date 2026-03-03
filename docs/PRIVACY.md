# Privacy Layer Documentation

> Sprint 4: Privacy Minimisation & Redaction Implementation

---

## Overview

The privacy layer ensures no raw PII reaches downstream systems. It implements defense-in-depth with multiple independent protections.

## Architecture

### Pipeline Position

```
Email Input → [Ingestion] → [Minimisation & Redaction] → [Classification] → [Persistence]
                                     ↑
                              Privacy Gate
```

The redaction stage runs **before** classification, ensuring all PII is redacted before any AI processing.

---

## Components

### 1. EmailPreprocessor (`src/privacy/preprocessing.py`)

Applies preprocessing before PII detection:

- **Thread trimming** - Removes quoted replies (Gmail, Outlook formats)
- **Signature removal** - Strips common signature patterns
- **Attachment metadata** - Extracts filename only, discards content

### 2. PresidioRedactor (`src/privacy/presidio_redactor.py`)

Microsoft Presidio-based PII detection and redaction:

**Built-in detectors:**
- EMAIL_ADDRESS → `[EMAIL]`
- PHONE_NUMBER → `[PHONE]`
- UK_NINO → `[NINO]`
- PERSON → `[PERSON]`
- LOCATION → `[LOCATION]`
- ORGANIZATION → `[ORGANIZATION]`

**Custom insurance recognisers:**
- Claim IDs (`AB-123456`) → `[CLAIM_ID]`
- Policy numbers (`POL-123456789`) → `[POLICY_ID]`
- Broker references (`BROK-12345`) → `[BROKER_REF]`

### 3. PrivacyGateInterceptor (`src/privacy/gate.py`)

Stageflow interceptor that enforces redaction before classification:

- Blocks raw body fields from reaching classification
- Denies by default when stage tracking unavailable
- Logs all bypass attempts

### 4. EventSanitizer (`src/privacy/event_sanitizer.py`)

Audit event sanitiser ensuring no raw content enters event store:

- Allow-listed payload fields only
- Regex-based forbidden pattern detection
- Email hashing for identifiers
- Field truncation for long text

---

## Usage

### Running the Pipeline

```python
from src.pipeline.graph import create_email_pipeline
from src.privacy.presidio_redactor import PresidioRedactor
from src.privacy.event_sanitizer import EventSanitizer

pipeline = create_email_pipeline(
    pii_redactor=PresidioRedactor(safe_mode=True),
)
```

### Custom Redactor

Implement the `PIIRedactor` protocol for custom implementations:

```python
from src.privacy.redactor import PIIRedactor

class CustomRedactor(PIIRedactor):
    def redact_text(self, text: str) -> tuple[str, dict[str, int]]:
        # Custom implementation
        ...

    def detect_pii(self, text: str) -> dict[str, list[dict]]:
        # Custom detection
        ...

    def count_pii(self, text: str) -> dict[str, int]:
        # Custom counting
        ...
```

---

## Privacy Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| No raw email persistence | All content redacted before storage |
| No PII in logs | EventSanitizer scrubs all events |
| No PII in vectors | Only redacted summaries indexed |
| Audit integrity | Append-only event store |
| Reproducibility | Hash-based email identifiers |

---

## Testing

Run privacy-specific tests:

```bash
pytest src/tests/test_redaction_safety.py -v
pytest src/tests/test_preprocessing.py -v
pytest src/tests/test_event_sanitizer.py -v
```

Key test scenarios:
- PII removal verification
- Thread trimming effectiveness
- Signature removal coverage
- Event sanitisation enforcement
- Privacy gate blocking

---

## Configuration

Environment variables (future):
- `PII_CONFIDENCE_THRESHOLD` - Minimum detection confidence (default: 0.5)
- `SAFE_MODE` - Fail on redaction errors (default: true)
- `REDACTION_LOGGING` - Log redaction decisions (default: false)
