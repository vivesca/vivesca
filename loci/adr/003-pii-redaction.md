# ADR-003: PII Redaction Patterns for Banking

**Status:** Accepted
**Date:** 2026-01-24
**Context:** Banking FAQ chatbot audit logging and compliance

---

## Context and Problem Statement

Banking regulations require 7-year audit retention of user queries, but we must redact Personally Identifiable Information (PII) before logging. The prototype has basic redaction (email, HKID), but banking-specific PII is missing:

**Current gaps**:
- ❌ Account numbers (users may paste: "Transfer from 123-456-7890 to...")
- ❌ Credit card numbers (users may ask: "Why was 4532-1234-5678-9010 declined?")
- ❌ Transaction IDs (users may reference: "Check status of TX12345678")
- ❌ SWIFT codes (ironically, while we *want* to match SWIFT in FAQs, shouldn't log user's actual SWIFT codes)
- ❌ Phone numbers (users may provide: "Call me at +852 1234 5678")

**Risk**: Logging unredacted PII violates privacy regulations, creates security liability.

## Decision

Implement **comprehensive PII redaction** with banking-specific patterns before writing audit logs.

### Implementation
```python
import re

class BankingPIIRedactor:
    """Redact PII from user queries before audit logging."""

    patterns = {
        # Existing patterns
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'hkid': r'\b[A-Z]{1,2}\d{6}\([0-9A]\)\b',

        # NEW: Banking-specific patterns
        'account_number': r'\b\d{3}-\d{3}-\d{3,4}\b',  # Format: 123-456-7890
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # With Luhn validation
        'transaction_id': r'\b(TX|REF|TXN)[A-Z0-9]{8,14}\b',  # Prefixed IDs
        'hk_phone': r'\+852[-\s]?\d{4}[-\s]?\d{4}\b',  # +852 1234 5678
        'swift_code': r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',  # 8 or 11 chars
    }

    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """Validate credit card with Luhn algorithm (reduce false positives)."""
        digits = [int(d) for d in card_number if d.isdigit()]
        checksum = sum(digits[-1::-2]) + sum(sum(divmod(d * 2, 10)) for d in digits[-2::-2])
        return checksum % 10 == 0

    def redact(self, text: str) -> str:
        """Apply all redaction patterns."""
        redacted = text
        for pii_type, pattern in self.patterns.items():
            # Special handling for credit cards (Luhn validation)
            if pii_type == 'credit_card':
                matches = re.finditer(pattern, redacted)
                for match in matches:
                    if self.luhn_check(match.group()):
                        redacted = redacted.replace(match.group(), f'[REDACTED_{pii_type.upper()}]')
            else:
                redacted = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', redacted)
        return redacted
```

## Considered Alternatives

### Alternative 1: LLM-Based PII Detection (NER Model)
**Approach**: Use NER (Named Entity Recognition) model to detect PII
**Pros**: More context-aware, can catch unusual formats
**Cons**:
- Latency (100-200ms per query)
- False negatives (may miss novel PII formats)
- Overkill for structured banking data

**Why rejected**: Regex is faster (1-2ms), deterministic, and sufficient for structured PII.

### Alternative 2: No Redaction (Hash User Queries)
**Approach**: Store SHA256 hash of queries instead of plaintext
**Pros**: No PII in logs at all
**Cons**:
- Debugging impossible (can't read actual queries)
- Can't analyze common query patterns
- Defeats purpose of audit logs (regulators need explainability)

**Why rejected**: Audit logs must be human-readable for compliance and debugging.

### Alternative 3: Microsoft Presidio (PII Detection Library)
**Approach**: Use Presidio's pre-built recognizers
**Pros**: Comprehensive, multi-language, well-tested
**Cons**:
- Heavy dependency (adds 50MB+)
- Overkill for defined patterns
- Requires model downloads for NER

**Why rejected**: Our PII patterns are well-defined and static. Regex is simpler and faster.

## Rationale

### Why Regex Patterns
1. **Performance**: <2ms latency per query (acceptable overhead)
2. **Deterministic**: Same input always produces same output (testable)
3. **Explainable**: Easy to audit what's being redacted
4. **Sufficient**: Banking PII follows structured formats (account numbers, cards)

### Why Luhn Validation for Credit Cards
**Problem**: Generic `\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}` matches any 16 digits (false positives)
**Example false positive**: "Transaction 1234 5678 9012 3456 was processed" (not a card number)
**Solution**: Validate checksum with Luhn algorithm (only real card formats pass)
**Trade-off**: Slightly higher false negative rate (invalid checksums not redacted) - acceptable

### Pattern Design Rationale

| Pattern | Format | Rationale |
|---------|--------|-----------|
| Account number | `\d{3}-\d{3}-\d{3,4}` | Most HK banks use 9-10 digit accounts with dashes |
| Credit card | `\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}` + Luhn | Standard 16-digit format with optional separators |
| Transaction ID | `(TX\|REF\|TXN)[A-Z0-9]{8,14}` | Bank-specific prefixes + alphanumeric ID |
| HK phone | `\+852[-\s]?\d{4}[-\s]?\d{4}` | Country code + 8 digits (HK format) |
| SWIFT code | `[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?` | ISO 9362 standard (8 or 11 chars) |

## Consequences

### Positive
- ✅ Compliant audit logs (PII-redacted)
- ✅ Fast (<2ms overhead per query)
- ✅ Testable and deterministic
- ✅ Debuggable (redacted logs still show query structure)

### Negative
- ❌ False positives possible (e.g., "I need 1234 5678 9012 3456 points" matches card pattern - Luhn mitigates)
- ❌ False negatives possible (novel PII formats not in regex)
- ❌ Maintenance burden (add patterns as new PII types discovered)

### Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives (redact non-PII) | Lost context in logs | Luhn validation for cards, prefix checks for IDs |
| False negatives (miss PII) | Compliance violation | Comprehensive test suite with 50+ samples |
| New PII format not covered | Logs contain PII | Quarterly review of sample logs for new patterns |
| Performance regression | Latency increase | Benchmark in CI (alert if redaction >5ms) |

## Validation

### Success Criteria
- ✅ 95% PII detection rate on test dataset (50 anonymized queries)
- ✅ <2ms redaction latency per query (benchmarked on 1000 queries)
- ✅ Zero false negatives on known PII formats (credit cards, account numbers)
- ✅ <5% false positive rate (non-PII incorrectly redacted)

### Test Dataset (Anonymized Examples)
Create `tests/fixtures/pii_samples.yaml`:
```yaml
- query: "Transfer $500 from 123-456-7890 to 098-765-4321"
  expected: "Transfer $500 from [REDACTED_ACCOUNT_NUMBER] to [REDACTED_ACCOUNT_NUMBER]"

- query: "Why was card 4532-1234-5678-9010 declined?"
  expected: "Why was card [REDACTED_CREDIT_CARD] declined?"

- query: "Check status of TX12345678"
  expected: "Check status of [REDACTED_TRANSACTION_ID]"

- query: "Call me at +852 9123 4567"
  expected: "Call me at [REDACTED_HK_PHONE]"

- query: "SWIFT code is HKBAHKHH"
  expected: "SWIFT code is [REDACTED_SWIFT_CODE]"

# False positive test (should NOT redact)
- query: "I need 1234 5678 9012 3450 points"  # Invalid Luhn checksum
  expected: "I need 1234 5678 9012 3450 points"  # No redaction
```

### Integration Test
```python
def test_audit_log_contains_no_pii():
    """Verify audit logs are PII-free."""
    # Send query with PII
    response = client.post('/v1/chat', json={
        'query': 'Transfer from 123-456-7890 to 098-765-4321',
        'session_id': 'test-session'
    })

    # Check audit log
    audit_log = get_latest_audit_log()
    assert '123-456-7890' not in audit_log['query']
    assert '[REDACTED_ACCOUNT_NUMBER]' in audit_log['query']
```

## Monitoring

### Metrics to Track
- **PII detection rate**: % of queries with redactions (expect ~5-10% for banking FAQs)
- **Redaction latency**: p50/p95/p99 (target: <2ms p95)
- **False positive reports**: User complaints about over-redaction

### Quarterly Review
1. Sample 1000 random audit logs (human review)
2. Identify any missed PII patterns (false negatives)
3. Update regex patterns and test suite
4. Re-run on historical logs if critical gap found

## References

- **Problem identified by**: Security sentinel agent
- **Industry standards**: [ISO/IEC 27001: PII Protection](https://www.iso.org/standard/75652.html)
- **Luhn algorithm**: [Credit Card Validation](https://en.wikipedia.org/wiki/Luhn_algorithm)
- **Banking compliance**: [HKMA Privacy Guidelines](https://www.hkma.gov.hk/)
