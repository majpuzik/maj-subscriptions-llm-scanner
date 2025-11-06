# LLM Scanner v2.2 - Probabilistic Scoring System

**Date:** 2025-11-06
**Version:** 2.2.0 (Design)
**Inspired by:** document-recognition skill (invoice_scorer.py)
**Status:** 🎯 DESIGN PHASE

---

## 🎯 Cíl upgradu v2.2

**Zlepšit přesnost detekce subscription emailů z 94.5% na 97%+ pomocí probabilistického scoring systému** místo jednoduchého binary classification.

### Problém s v2.1

```python
# V2.1: Binární klasifikace
{
    "is_subscription": true,       # Pouze True/False
    "confidence": 95,               # Jedno číslo bez kontextu
    "reasoning": "Payment confirmed"  # Obecné vysvětlení
}
```

**Nedostatky:**
- ❌ Žádná transparentnost, **proč** byl email klasifikován
- ❌ Nemožnost debuggingu false positives
- ❌ Všechna rozhodnutí stejně důležitá (binary)
- ❌ Chybí penalizace za negativní signály (unsubscribe, marketing)

### Řešení v v2.2

```python
# V2.2: Probabilistický scoring
{
    "total_score": 165,
    "max_possible": 200,
    "confidence_level": "VERY_HIGH",
    "confidence_percentage": 82.5,

    "score_breakdown": {
        "subscription_indicators": 45,  # /50
        "payment_indicators": 40,       # /40
        "temporal_indicators": 30,      # /35
        "sender_trust": 20,             # /25
        "content_structure": 15,        # /20
        "format_quality": 15,           # /15
        "bonus_combinations": 15,       # /20
        "negative_penalties": -15       # /-50
    },

    "matched_patterns": [
        "subscription_keyword",
        "monthly_price",
        "payment_confirmed",
        "known_service_sender"
    ],

    "warnings": [
        "Contains 'unsubscribe' link (-15 penalty)"
    ],

    "suggestions": [
        "Verify sender domain against whitelist"
    ]
}
```

**Výhody:**
- ✅ **Transparentní** rozhodování - vidíme každý faktor
- ✅ **Debugovatelné** - můžeme optimalizovat jednotlivé kategorie
- ✅ **Přesné** - weighted scoring redukuje false positives
- ✅ **Actionable** - warnings & suggestions pro zlepšení

---

## 📊 Scoring System Design

### Score Categories (celkem 0-200 bodů)

```python
@dataclass
class ScoreBreakdown:
    """Detailní rozklad skórování."""

    # 1. Subscription Indicators (max 50)
    subscription_indicators: int = 0

    # 2. Payment Indicators (max 40)
    payment_indicators: int = 0

    # 3. Temporal Indicators (max 35)
    temporal_indicators: int = 0

    # 4. Sender Trust Score (max 25)
    sender_trust: int = 0

    # 5. Content Structure (max 20)
    content_structure: int = 0

    # 6. Format Quality (max 15)
    format_quality: int = 0

    # 7. Bonus Combinations (max 20)
    bonus_combinations: int = 0

    # 8. Negative Penalties (max -50)
    negative_penalties: int = 0

    @property
    def total(self) -> int:
        return sum([
            self.subscription_indicators,
            self.payment_indicators,
            self.temporal_indicators,
            self.sender_trust,
            self.content_structure,
            self.format_quality,
            self.bonus_combinations,
            self.negative_penalties
        ])

    @property
    def percentage(self) -> float:
        return min(100.0, max(0.0, (self.total / 200) * 100))
```

---

## 🔍 Detailed Scoring Tables

### 1. Subscription Indicators (max 50)

| Pattern | Points | Regex/Keywords |
|---------|--------|----------------|
| `subscription_keyword` | 50 | `(?i)(subscription\|předplatné\|abonnement)` |
| `renewal_keyword` | 45 | `(?i)(renewal\|renew\|obnovení)` |
| `payment_confirmed` | 40 | `(?i)(payment confirmed\|platba potvrzena)` |
| `invoice_keyword` | 35 | `(?i)(invoice\|faktura\|rechnung)` |
| `membership_keyword` | 30 | `(?i)(membership\|členství)` |

**Příklad:**
```python
text = "Your GitHub subscription will renew on 2025-12-01"
# Match: subscription_keyword (50) + renewal_keyword (45)
# Score: max(50, 45) = 50 (nejlepší match v kategorii)
```

### 2. Payment Indicators (max 40)

| Pattern | Points | Regex |
|---------|--------|-------|
| `price_with_currency` | 40 | `[$€£¥]\d+\.\d{2}\|\d+[.,]\d{2}\s*(USD\|EUR\|CZK\|Kč)` |
| `payment_method` | 35 | `(?i)(charged to\|payment method\|card ending)` |
| `billing_date` | 30 | `(?i)(billing date\|next charge)` |
| `amount_total` | 25 | `(?i)(total\|amount\|celkem):\s*[$€£¥]?\d+` |

**Příklad:**
```python
text = "Total: $14.99 charged to card ending 4242"
# Match: price_with_currency (40) + payment_method (35)
# Score: 40 (highest in category)
```

### 3. Temporal Indicators (max 35)

| Pattern | Points | Keywords |
|---------|--------|----------|
| `monthly_yearly` | 35 | `(?i)(monthly\|yearly\|měsíčně\|ročně)` |
| `renewal_date` | 30 | `(?i)(renews on\|expires\|ends on)` |
| `trial_period` | 25 | `(?i)(trial ends\|trial period\|zkušební)` |
| `billing_cycle` | 20 | `(?i)(billing cycle\|payment cycle)` |

### 4. Sender Trust Score (max 25)

| Pattern | Points | Logic |
|---------|--------|-------|
| `known_service` | 25 | Sender in whitelist (GitHub, Netflix, Spotify, etc.) |
| `payment_processor` | 20 | Stripe, PayPal, Braintree |
| `no_reply_domain` | 15 | `noreply@`, `billing@`, `subscriptions@` |
| `company_domain` | 10 | Non-Gmail/Yahoo sender |

**Whitelist Example:**
```python
KNOWN_SERVICES = [
    "github.com", "netflix.com", "spotify.com",
    "adobe.com", "microsoft.com", "google.com",
    "stripe.com", "paypal.com", "apple.com"
]
```

### 5. Content Structure (max 20)

| Pattern | Points | Logic |
|---------|--------|-------|
| `professional_html` | 20 | HTML email with proper structure |
| `transaction_table` | 15 | Contains table with amounts |
| `receipt_format` | 15 | Receipt-like structure |
| `footer_links` | 10 | Terms, Privacy Policy links |

### 6. Format Quality (max 15)

| Pattern | Points | Logic |
|---------|--------|-------|
| `date_format_valid` | 15 | Valid date format detected |
| `currency_symbol` | 10 | Proper currency symbols |
| `structured_data` | 10 | Well-formatted lists/tables |

### 7. Bonus Combinations (max 20)

| Combination | Points | Logic |
|-------------|--------|-------|
| `perfect_subscription` | 20 | subscription_keyword + price + monthly/yearly |
| `perfect_payment` | 15 | payment_confirmed + amount + payment_method |
| `perfect_renewal` | 15 | renewal + renewal_date + price |
| `known_service_confirmed` | 10 | known_service + payment_confirmed |

**Example:**
```python
if all(matched for matched in [
    "subscription_keyword",
    "price_with_currency",
    "monthly_yearly"
]):
    bonus_combinations += 20  # Perfect subscription combo
```

### 8. Negative Penalties (max -50)

| Pattern | Penalty | Keywords |
|---------|---------|----------|
| `unsubscribe_link` | -30 | `(?i)unsubscribe\|opt-out\|odhlásit` |
| `newsletter_keyword` | -25 | `(?i)newsletter\|bulletin` |
| `marketing_keyword` | -20 | `(?i)(sale\|discount\|limited offer)` |
| `promotional` | -15 | `(?i)(promo\|deal\|special offer)` |
| `spam_indicators` | -40 | Multiple exclamation marks, ALL CAPS |

**Example:**
```python
text = "Your subscription renewed! Click to unsubscribe"
# Positive: subscription (50) + renewal (45)
# Negative: unsubscribe_link (-30)
# Total: 50 - 30 = 20 (LOW confidence)
```

---

## 🎚️ Confidence Levels

```python
class ConfidenceLevel(Enum):
    VERY_HIGH = "VERY_HIGH"  # 90-100% (180-200 pts) → Auto-accept
    HIGH = "HIGH"            # 75-89%  (150-179 pts) → Accept with logging
    MEDIUM = "MEDIUM"        # 50-74%  (100-149 pts) → Needs review
    LOW = "LOW"              # 0-49%   (0-99 pts)    → Auto-reject
```

### Decision Logic

```python
def get_confidence_level(percentage: float) -> ConfidenceLevel:
    if percentage >= 90:
        return ConfidenceLevel.VERY_HIGH
    elif percentage >= 75:
        return ConfidenceLevel.HIGH
    elif percentage >= 50:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW
```

### Thresholds for Production

| Confidence | Score Range | Action | Expected Accuracy |
|------------|-------------|--------|-------------------|
| VERY_HIGH | 180-200 | Auto-save to DB | 99%+ |
| HIGH | 150-179 | Save + log for review | 95-98% |
| MEDIUM | 100-149 | Flag for manual review | 80-94% |
| LOW | 0-99 | Auto-reject (don't save) | N/A |

---

## 🧪 Fuzzy Matching for OCR Errors

Inspiration from document-recognition:

```python
class FuzzyMatcher:
    """Tolerantní matching pro OCR chyby."""

    OCR_REPLACEMENTS = {
        '0': ['O', 'o'],
        '1': ['l', 'I', 'i'],
        '5': ['S', 's'],
        '8': ['B'],
    }

    def fuzzy_match(self, text: str, pattern: str) -> bool:
        """Match s tolerancí OCR chyb."""
        # Normalize text
        normalized = self._normalize_ocr(text)

        # Try exact match first
        if re.search(pattern, normalized, re.IGNORECASE):
            return True

        # Try fuzzy variants
        variants = self._generate_variants(pattern)
        for variant in variants:
            if re.search(variant, normalized, re.IGNORECASE):
                return True

        return False

    def _normalize_ocr(self, text: str) -> str:
        """Remove common OCR artifacts."""
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        # Fix common OCR errors
        text = text.replace('rn', 'm')  # OCR často vidí 'm' jako 'rn'
        return text
```

**Examples:**
```python
"subscripti0n" → "subscription" ✅
"rnewal" → "renewal" ✅
"m0nthly" → "monthly" ✅
"paym3nt" → "payment" ✅
```

---

## 📦 Database Schema Updates

### New Fields for v2.2

```sql
-- Add to email_evidence table
ALTER TABLE email_evidence ADD COLUMN score_total INTEGER;
ALTER TABLE email_evidence ADD COLUMN score_breakdown TEXT; -- JSON
ALTER TABLE email_evidence ADD COLUMN confidence_level TEXT; -- VERY_HIGH/HIGH/MEDIUM/LOW
ALTER TABLE email_evidence ADD COLUMN matched_patterns TEXT; -- JSON array
ALTER TABLE email_evidence ADD COLUMN warnings TEXT; -- JSON array
ALTER TABLE email_evidence ADD COLUMN suggestions TEXT; -- JSON array
```

**Example JSON storage:**
```json
{
  "score_breakdown": {
    "subscription_indicators": 50,
    "payment_indicators": 40,
    "temporal_indicators": 35,
    "sender_trust": 25,
    "content_structure": 20,
    "format_quality": 15,
    "bonus_combinations": 20,
    "negative_penalties": -15
  },
  "matched_patterns": [
    "subscription_keyword",
    "monthly_price",
    "known_service_sender"
  ],
  "warnings": [
    "Contains 'unsubscribe' link (-15 penalty)"
  ],
  "suggestions": []
}
```

---

## 🔄 Migration from v2.1 to v2.2

### Backward Compatibility

```python
def convert_v2_1_to_v2_2(llm_result: Dict) -> SubscriptionScore:
    """Convert old v2.1 format to new v2.2 scoring."""

    # Old format
    is_subscription = llm_result.get("is_subscription", False)
    confidence = llm_result.get("confidence", 0)

    if not is_subscription:
        # Low score for non-subscriptions
        return SubscriptionScore(
            total_score=0,
            confidence_level=ConfidenceLevel.LOW,
            ...
        )

    # Map old confidence to new scoring
    if confidence >= 95:
        estimated_score = 185  # VERY_HIGH
    elif confidence >= 85:
        estimated_score = 165  # HIGH
    elif confidence >= 70:
        estimated_score = 125  # MEDIUM
    else:
        estimated_score = 75   # LOW

    return SubscriptionScore(
        total_score=estimated_score,
        confidence_level=get_confidence_level((estimated_score/200)*100),
        ...
    )
```

---

## 🧮 Implementation Classes

### Core Classes

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ScoreBreakdown:
    subscription_indicators: int = 0
    payment_indicators: int = 0
    temporal_indicators: int = 0
    sender_trust: int = 0
    content_structure: int = 0
    format_quality: int = 0
    bonus_combinations: int = 0
    negative_penalties: int = 0

    @property
    def total(self) -> int:
        return (
            self.subscription_indicators +
            self.payment_indicators +
            self.temporal_indicators +
            self.sender_trust +
            self.content_structure +
            self.format_quality +
            self.bonus_combinations +
            self.negative_penalties
        )

    @property
    def percentage(self) -> float:
        return min(100.0, max(0.0, (self.total / 200) * 100))


@dataclass
class SubscriptionScore:
    score_breakdown: ScoreBreakdown
    confidence_level: ConfidenceLevel
    matched_patterns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return self.score_breakdown.total

    @property
    def confidence_percentage(self) -> float:
        return self.score_breakdown.percentage

    def to_dict(self) -> Dict:
        return {
            "total_score": self.total_score,
            "max_possible": 200,
            "confidence_level": self.confidence_level.value,
            "confidence_percentage": round(self.confidence_percentage, 2),
            "score_breakdown": {
                "subscription_indicators": self.score_breakdown.subscription_indicators,
                "payment_indicators": self.score_breakdown.payment_indicators,
                "temporal_indicators": self.score_breakdown.temporal_indicators,
                "sender_trust": self.score_breakdown.sender_trust,
                "content_structure": self.score_breakdown.content_structure,
                "format_quality": self.score_breakdown.format_quality,
                "bonus_combinations": self.score_breakdown.bonus_combinations,
                "negative_penalties": self.score_breakdown.negative_penalties,
            },
            "matched_patterns": self.matched_patterns,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
        }
```

---

## 📈 Expected Performance Improvements

### v2.1 vs v2.2 Comparison

| Metric | v2.1 | v2.2 (Expected) | Improvement |
|--------|------|-----------------|-------------|
| **Accuracy** | 94.5% | 97%+ | +2.5% |
| **False Positives** | ~5% | ~2% | -60% |
| **False Negatives** | ~3% | ~2% | -33% |
| **Transparency** | Low | High | ✅ |
| **Debuggability** | Low | High | ✅ |
| **Processing Speed** | ~2 emails/sec | ~1.8 emails/sec | -10% |

**Trade-offs:**
- ✅ **+2.5% accuracy** worth the slight speed decrease
- ✅ **Much better debugging** with score breakdown
- ✅ **Fewer false positives** reduces manual review needed

---

## 🚀 Implementation Roadmap

### Phase 1: Core Scoring System (Week 1)
- [x] Design scoring tables and categories
- [ ] Implement `ScoreBreakdown` class
- [ ] Implement `SubscriptionScore` class
- [ ] Write unit tests for scoring logic

### Phase 2: Pattern Matching (Week 1)
- [ ] Define regex patterns for all categories
- [ ] Implement fuzzy matching
- [ ] Create known_services whitelist
- [ ] Test pattern accuracy

### Phase 3: Integration with LLM (Week 2)
- [ ] Modify LLM prompt to return score breakdown
- [ ] Implement JSON parsing from LLM response
- [ ] Add fallback for old v2.1 format
- [ ] Test on sample emails

### Phase 4: Database Migration (Week 2)
- [ ] Add new columns to schema
- [ ] Write migration script
- [ ] Test backward compatibility
- [ ] Deploy to test database

### Phase 5: Production Testing (Week 3)
- [ ] Run v2.2 on test set (1000+ emails)
- [ ] Compare results with v2.1
- [ ] Analyze false positives/negatives
- [ ] Fine-tune scoring weights

### Phase 6: Production Deployment (Week 3)
- [ ] Deploy to NAS5
- [ ] Monitor performance
- [ ] Adjust thresholds if needed
- [ ] Document lessons learned

---

## 🧪 Testing Strategy

### Unit Tests

```python
def test_subscription_keyword_scoring():
    scorer = SubscriptionScorer()
    text = "Your GitHub subscription will renew on 2025-12-01 for $14.99"
    score = scorer.score_text(text)

    assert score.total_score >= 150  # Should be HIGH confidence
    assert "subscription_keyword" in score.matched_patterns
    assert "monthly_yearly" not in score.matched_patterns  # "renew" != "monthly"
    assert score.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
```

### Integration Tests

```python
def test_false_positive_reduction():
    """Test that marketing emails are correctly rejected."""
    scorer = SubscriptionScorer()

    marketing_email = """
    Big Sale! Get 50% off our premium subscription!
    Limited time offer - click to unsubscribe.
    """

    score = scorer.score_text(marketing_email)

    # Should have negative penalties
    assert score.score_breakdown.negative_penalties < 0
    # Should not exceed MEDIUM confidence
    assert score.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]
    # Should have warnings
    assert len(score.warnings) > 0
```

---

## 📊 Success Criteria

### Minimum Viable Product (MVP)

- ✅ Accuracy ≥ 96%
- ✅ False positive rate ≤ 3%
- ✅ Processing speed ≥ 1.5 emails/sec
- ✅ All 200 patterns implemented
- ✅ Database migration successful
- ✅ Backward compatibility with v2.1

### Stretch Goals

- 🎯 Accuracy ≥ 98%
- 🎯 False positive rate ≤ 1%
- 🎯 Auto-learning from corrections
- 🎯 Real-time dashboard for scoring breakdown
- 🎯 A/B testing framework

---

## 🔗 References

- **document-recognition skill:** `/Users/m.a.j.puzik/.claude/skills/document-recognition/invoice_scorer.py`
- **LLM Scanner v2.1:** `production_llm_scanner_v2.1.py`
- **v2.1 Test Report:** `LLM_SCANNER_V2.1_SUMMARY.md`

---

**END OF DESIGN DOCUMENT**
