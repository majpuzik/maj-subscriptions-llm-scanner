#!/usr/bin/env python3
"""
Subscription Scoring System v2.2
=================================

Advanced probabilistic system for detecting subscription emails.
Inspired by document-recognition invoice_scorer.py.

Features:
- 8-category weighted scoring (0-200 points)
- 4 confidence levels (VERY_HIGH/HIGH/MEDIUM/LOW)
- Detailed score breakdown with transparency
- Matched patterns + warnings + suggestions
- Fuzzy matching for OCR tolerance
- Negative penalties for marketing indicators

Author: Claude Code
Version: 2.2.0
Date: 2025-11-06
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


# ============================================================================
# ENUMS AND CONFIDENCE LEVELS
# ============================================================================

class ConfidenceLevel(Enum):
    """Confidence levels for subscription detection."""
    VERY_HIGH = "VERY_HIGH"  # 90-100% (180-200 pts) → Auto-accept
    HIGH = "HIGH"            # 75-89%  (150-179 pts) → Accept with logging
    MEDIUM = "MEDIUM"        # 50-74%  (100-149 pts) → Needs review
    LOW = "LOW"              # 0-49%   (0-99 pts)    → Auto-reject


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ScoreBreakdown:
    """Detailed score breakdown across 8 categories."""

    # Category 1: Subscription Indicators (max 50)
    subscription_indicators: int = 0

    # Category 2: Payment Indicators (max 40)
    payment_indicators: int = 0

    # Category 3: Temporal Indicators (max 35)
    temporal_indicators: int = 0

    # Category 4: Sender Trust Score (max 25)
    sender_trust: int = 0

    # Category 5: Content Structure (max 20)
    content_structure: int = 0

    # Category 6: Format Quality (max 15)
    format_quality: int = 0

    # Category 7: Bonus Combinations (max 20)
    bonus_combinations: int = 0

    # Category 8: Negative Penalties (max -50)
    negative_penalties: int = 0

    @property
    def total(self) -> int:
        """Calculate total score."""
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
    def max_possible(self) -> int:
        """Maximum possible score (without penalties)."""
        return 200  # 50 + 40 + 35 + 25 + 20 + 15 + 20

    @property
    def percentage(self) -> float:
        """Score as percentage (0-100%)."""
        return min(100.0, max(0.0, (self.total / self.max_possible) * 100))


@dataclass
class SubscriptionScore:
    """Complete subscription scoring result."""

    score_breakdown: ScoreBreakdown
    confidence_level: ConfidenceLevel
    matched_patterns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        """Total score."""
        return self.score_breakdown.total

    @property
    def confidence_percentage(self) -> float:
        """Confidence as percentage."""
        return self.score_breakdown.percentage

    @property
    def is_subscription(self) -> bool:
        """Legacy compatibility: binary classification."""
        return self.confidence_level in [
            ConfidenceLevel.VERY_HIGH,
            ConfidenceLevel.HIGH
        ]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_score": self.total_score,
            "max_possible": 200,
            "confidence_level": self.confidence_level.value,
            "confidence_percentage": round(self.confidence_percentage, 2),
            "is_subscription": self.is_subscription,
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

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# FUZZY MATCHING FOR OCR TOLERANCE
# ============================================================================

class FuzzyMatcher:
    """Fuzzy matching for OCR errors and typos."""

    # Common OCR substitutions
    OCR_REPLACEMENTS = {
        '0': ['O', 'o'],
        '1': ['l', 'I', 'i'],
        '5': ['S', 's'],
        '8': ['B'],
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for fuzzy matching."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Common OCR errors
        text = text.replace('rn', 'm')  # OCR often sees 'm' as 'rn'
        text = text.replace('|', 'I')
        text = text.replace('!', 'i')
        return text

    @classmethod
    def fuzzy_search(cls, pattern: str, text: str, case_sensitive: bool = False) -> bool:
        """
        Search for pattern in text with OCR tolerance.

        Args:
            pattern: Regex pattern to search for
            text: Text to search in
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            True if pattern found (with tolerance), False otherwise
        """
        # Normalize text
        normalized = cls.normalize_text(text)

        # Try exact match first
        flags = 0 if case_sensitive else re.IGNORECASE
        if re.search(pattern, normalized, flags):
            return True

        # Try with common OCR substitutions
        for digit, replacements in cls.OCR_REPLACEMENTS.items():
            for repl in replacements:
                variant = pattern.replace(digit, repl)
                if re.search(variant, normalized, flags):
                    return True

        return False


# ============================================================================
# SUBSCRIPTION SCORER
# ============================================================================

class SubscriptionScorer:
    """Main class for scoring subscription emails."""

    # Regex patterns for subscription detection
    PATTERNS = {
        # Category 1: Subscription Indicators (max 50)
        "subscription_keyword": r"(?i)(subscription|předplatné|abonnement|členství)",
        "renewal_keyword": r"(?i)(renewal|renew|obnovení|renewed|obnoví)",
        "payment_confirmed": r"(?i)(payment\s+confirmed|platba\s+potvrzena|charge\s+successful|successfully\s+charged)",
        "invoice_keyword": r"(?i)(invoice|faktura|rechnung|bill|účtenka)",
        "membership_keyword": r"(?i)(membership|členství|member|premium)",

        # Category 2: Payment Indicators (max 40)
        "price_with_currency": r"([$€£¥]\s?\d{1,3}([,\.]\d{3})*([,\.]\d{2})?|\d{1,3}([,\.\s]\d{3})*[,\.]\d{2}\s*(USD|EUR|CZK|Kč|€|\$))",
        "payment_method": r"(?i)(charged\s+to|payment\s+method|card\s+ending|paypal|stripe|credit\s+card)",
        "billing_date": r"(?i)(billing\s+date|next\s+charge|next\s+payment|charge\s+on)",
        "amount_total": r"(?i)(total|amount|celkem|suma):\s*[$€£¥]?\d+",

        # Category 3: Temporal Indicators (max 35)
        "monthly_yearly": r"(?i)(monthly|yearly|měsíčně|ročně|per\s+month|per\s+year|/month|/year)",
        "renewal_date": r"(?i)(renews\s+on|expires|ends\s+on|platnost\s+do|expiry\s+date)",
        "trial_period": r"(?i)(trial\s+ends|trial\s+period|zkušební\s+doba|free\s+trial)",
        "billing_cycle": r"(?i)(billing\s+cycle|payment\s+cycle|cyklus\s+platby)",

        # Category 4: Sender Trust (max 25) - checked separately
        "known_service_domain": r"@(github\.com|netflix\.com|spotify\.com|adobe\.com|microsoft\.com|google\.com|stripe\.com|paypal\.com|apple\.com)",
        "payment_processor": r"@(stripe\.com|paypal\.com|braintree\.com|square\.com)",
        "noreply_billing": r"(noreply|billing|subscriptions|payments)@",

        # Category 5: Content Structure (max 20) - checked separately
        "html_table": r"<table",
        "receipt_structure": r"(?i)(receipt|kvitance|potvrzení)",

        # Category 6: Format Quality (max 15)
        "date_format": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        "currency_symbol": r"[$€£¥Kč]",

        # Negative Penalties (max -50)
        "unsubscribe_link": r"(?i)(unsubscribe|opt-out|odhlásit|abbestellen)",
        "newsletter_keyword": r"(?i)(newsletter|bulletin|zpravodaj)",
        "marketing_keyword": r"(?i)(sale|discount|limited\s+offer|akce|sleva|výprodej)",
        "promotional": r"(?i)(promo|deal|special\s+offer|save\s+\d+%)",
        "spam_indicators": r"([!]{3,}|[A-Z]{10,})",  # Multiple !!! or ALL CAPS
    }

    # Scoring tables for each pattern
    SCORING_TABLES = {
        # Category 1: Subscription Indicators
        "subscription_keyword": 50,
        "renewal_keyword": 45,
        "payment_confirmed": 40,
        "invoice_keyword": 35,
        "membership_keyword": 30,

        # Category 2: Payment Indicators
        "price_with_currency": 40,
        "payment_method": 35,
        "billing_date": 30,
        "amount_total": 25,

        # Category 3: Temporal Indicators
        "monthly_yearly": 35,
        "renewal_date": 30,
        "trial_period": 25,
        "billing_cycle": 20,

        # Category 4: Sender Trust
        "known_service_domain": 25,
        "payment_processor": 20,
        "noreply_billing": 15,

        # Category 5: Content Structure
        "html_table": 15,
        "receipt_structure": 15,

        # Category 6: Format Quality
        "date_format": 15,
        "currency_symbol": 10,

        # Negative Penalties
        "unsubscribe_link": -30,
        "newsletter_keyword": -25,
        "marketing_keyword": -20,
        "promotional": -15,
        "spam_indicators": -40,
    }

    # Known subscription services (for sender trust)
    KNOWN_SERVICES = [
        "github.com", "netflix.com", "spotify.com", "adobe.com",
        "microsoft.com", "google.com", "apple.com", "dropbox.com",
        "slack.com", "zoom.us", "notion.so", "figma.com",
        "canva.com", "grammarly.com", "evernote.com",
        "stripe.com", "paypal.com", "braintree.com"
    ]

    def __init__(self, fuzzy: bool = True):
        """
        Initialize subscription scorer.

        Args:
            fuzzy: Whether to use fuzzy matching for OCR tolerance
        """
        self.fuzzy = fuzzy
        self.fuzzy_matcher = FuzzyMatcher() if fuzzy else None

    def score_email(
        self,
        subject: str,
        sender: str,
        body: str,
        content_type: str = "text"
    ) -> SubscriptionScore:
        """
        Score an email for subscription indicators.

        Args:
            subject: Email subject line
            sender: Email sender address
            body: Email body text
            content_type: "text" or "html"

        Returns:
            SubscriptionScore object with detailed breakdown
        """
        breakdown = ScoreBreakdown()
        matched = []
        warnings = []
        suggestions = []

        # Combine all text for analysis
        full_text = f"{subject}\n{sender}\n{body}"

        # Category 1: Subscription Indicators
        sub_score = 0
        for pattern_name in ["subscription_keyword", "renewal_keyword",
                             "payment_confirmed", "invoice_keyword",
                             "membership_keyword"]:
            if self._match_pattern(pattern_name, full_text):
                matched.append(pattern_name)
                score = self.SCORING_TABLES[pattern_name]
                sub_score = max(sub_score, score)  # Take best match

        breakdown.subscription_indicators = sub_score

        # Category 2: Payment Indicators
        pay_score = 0
        for pattern_name in ["price_with_currency", "payment_method",
                             "billing_date", "amount_total"]:
            if self._match_pattern(pattern_name, full_text):
                matched.append(pattern_name)
                score = self.SCORING_TABLES[pattern_name]
                pay_score = max(pay_score, score)

        breakdown.payment_indicators = pay_score

        # Category 3: Temporal Indicators
        temp_score = 0
        for pattern_name in ["monthly_yearly", "renewal_date",
                             "trial_period", "billing_cycle"]:
            if self._match_pattern(pattern_name, full_text):
                matched.append(pattern_name)
                score = self.SCORING_TABLES[pattern_name]
                temp_score = max(temp_score, score)

        breakdown.temporal_indicators = temp_score

        # Category 4: Sender Trust
        sender_score = 0
        sender_lower = sender.lower()

        # Check known services
        for service in self.KNOWN_SERVICES:
            if service in sender_lower:
                matched.append("known_service_domain")
                sender_score = max(sender_score, 25)
                break

        # Check payment processors
        if re.search(self.PATTERNS["payment_processor"], sender_lower):
            matched.append("payment_processor")
            sender_score = max(sender_score, 20)

        # Check noreply/billing addresses
        if re.search(self.PATTERNS["noreply_billing"], sender_lower):
            matched.append("noreply_billing")
            sender_score = max(sender_score, 15)

        breakdown.sender_trust = sender_score

        # Category 5: Content Structure
        struct_score = 0
        if content_type == "html" and "<table" in body.lower():
            matched.append("html_table")
            struct_score = max(struct_score, 15)

        if self._match_pattern("receipt_structure", full_text):
            matched.append("receipt_structure")
            struct_score = max(struct_score, 15)

        breakdown.content_structure = struct_score

        # Category 6: Format Quality
        fmt_score = 0
        if self._match_pattern("date_format", full_text):
            matched.append("date_format")
            fmt_score = max(fmt_score, 15)

        if self._match_pattern("currency_symbol", full_text):
            matched.append("currency_symbol")
            fmt_score = max(fmt_score, 10)

        breakdown.format_quality = fmt_score

        # Category 7: Bonus Combinations
        bonus = 0

        # Perfect subscription combo
        if all(p in matched for p in ["subscription_keyword", "price_with_currency", "monthly_yearly"]):
            matched.append("perfect_subscription_combo")
            bonus += 20

        # Perfect payment combo
        elif all(p in matched for p in ["payment_confirmed", "amount_total", "payment_method"]):
            matched.append("perfect_payment_combo")
            bonus += 15

        # Perfect renewal combo
        elif all(p in matched for p in ["renewal_keyword", "renewal_date", "price_with_currency"]):
            matched.append("perfect_renewal_combo")
            bonus += 15

        # Known service + payment
        if "known_service_domain" in matched and "payment_confirmed" in matched:
            matched.append("trusted_service_payment")
            bonus += 10

        breakdown.bonus_combinations = bonus

        # Category 8: Negative Penalties
        penalties = 0

        # Unsubscribe link (strong negative signal)
        if self._match_pattern("unsubscribe_link", full_text):
            matched.append("unsubscribe_link")
            penalties += self.SCORING_TABLES["unsubscribe_link"]
            warnings.append("Contains 'unsubscribe' link (-30 penalty)")

        # Newsletter
        if self._match_pattern("newsletter_keyword", full_text):
            matched.append("newsletter_keyword")
            penalties += self.SCORING_TABLES["newsletter_keyword"]
            warnings.append("Newsletter keyword detected (-25 penalty)")

        # Marketing
        if self._match_pattern("marketing_keyword", full_text):
            matched.append("marketing_keyword")
            penalties += self.SCORING_TABLES["marketing_keyword"]
            warnings.append("Marketing keywords detected (-20 penalty)")

        # Promotional
        if self._match_pattern("promotional", full_text):
            matched.append("promotional")
            penalties += self.SCORING_TABLES["promotional"]
            warnings.append("Promotional content detected (-15 penalty)")

        # Spam indicators
        if self._match_pattern("spam_indicators", full_text):
            matched.append("spam_indicators")
            penalties += self.SCORING_TABLES["spam_indicators"]
            warnings.append("Spam indicators detected (-40 penalty)")

        breakdown.negative_penalties = penalties

        # Determine confidence level
        percentage = breakdown.percentage

        if percentage >= 90:
            confidence = ConfidenceLevel.VERY_HIGH
        elif percentage >= 75:
            confidence = ConfidenceLevel.HIGH
        elif percentage >= 50:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        # Generate suggestions
        if breakdown.subscription_indicators == 0:
            suggestions.append("No subscription keywords found - check if this is really a subscription")

        if breakdown.payment_indicators < 20:
            suggestions.append("Missing payment information (amount, currency, method)")

        if breakdown.sender_trust == 0:
            suggestions.append("Unknown sender - verify sender domain")

        if penalties < -30:
            suggestions.append("Multiple negative indicators - likely marketing/newsletter")

        return SubscriptionScore(
            score_breakdown=breakdown,
            confidence_level=confidence,
            matched_patterns=matched,
            warnings=warnings,
            suggestions=suggestions
        )

    def _match_pattern(self, pattern_name: str, text: str) -> bool:
        """Match a pattern in text (with optional fuzzy matching)."""
        pattern = self.PATTERNS.get(pattern_name)
        if not pattern:
            return False

        if self.fuzzy and self.fuzzy_matcher:
            return self.fuzzy_matcher.fuzzy_search(pattern, text)
        else:
            return bool(re.search(pattern, text, re.IGNORECASE))

    def get_detailed_report(self, score: SubscriptionScore) -> str:
        """
        Generate detailed human-readable report.

        Args:
            score: SubscriptionScore object

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("SUBSCRIPTION SCORING REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Total Score: {score.total_score}/200 ({score.confidence_percentage:.1f}%)")
        report.append(f"Confidence: {score.confidence_level.value}")
        report.append(f"Is Subscription: {'YES' if score.is_subscription else 'NO'}")
        report.append("")
        report.append("Score Breakdown:")
        report.append(f"  1. Subscription Indicators: {score.score_breakdown.subscription_indicators}/50")
        report.append(f"  2. Payment Indicators: {score.score_breakdown.payment_indicators}/40")
        report.append(f"  3. Temporal Indicators: {score.score_breakdown.temporal_indicators}/35")
        report.append(f"  4. Sender Trust: {score.score_breakdown.sender_trust}/25")
        report.append(f"  5. Content Structure: {score.score_breakdown.content_structure}/20")
        report.append(f"  6. Format Quality: {score.score_breakdown.format_quality}/15")
        report.append(f"  7. Bonus Combinations: {score.score_breakdown.bonus_combinations}/20")
        report.append(f"  8. Negative Penalties: {score.score_breakdown.negative_penalties} (max -50)")
        report.append("")

        if score.matched_patterns:
            report.append(f"Matched Patterns ({len(score.matched_patterns)}):")
            for pattern in score.matched_patterns:
                report.append(f"  - {pattern}")
            report.append("")

        if score.warnings:
            report.append("⚠️  Warnings:")
            for warning in score.warnings:
                report.append(f"  - {warning}")
            report.append("")

        if score.suggestions:
            report.append("💡 Suggestions:")
            for suggestion in score.suggestions:
                report.append(f"  - {suggestion}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_github_subscription():
    """Example: GitHub subscription renewal."""
    scorer = SubscriptionScorer(fuzzy=True)

    email = {
        "subject": "Your GitHub subscription will renew on December 1, 2025",
        "sender": "billing@github.com",
        "body": """
        Hi there,

        Your GitHub Team subscription will automatically renew on December 1, 2025.

        Amount: $14.99/month
        Payment method: Card ending in 4242

        Thanks for being a GitHub customer!
        """
    }

    score = scorer.score_email(
        subject=email["subject"],
        sender=email["sender"],
        body=email["body"]
    )

    print("\n" + "="*80)
    print("EXAMPLE 1: GitHub Subscription")
    print("="*80)
    print(scorer.get_detailed_report(score))
    print("\nJSON Output:")
    print(score.to_json())


def example_marketing_email():
    """Example: Marketing email (should be rejected)."""
    scorer = SubscriptionScorer(fuzzy=True)

    email = {
        "subject": "BIG SALE!!! 50% OFF Premium Subscription!!!",
        "sender": "marketing@someservice.com",
        "body": """
        LIMITED TIME OFFER!!!

        Get 50% off our premium subscription!
        Save big on our monthly plan - only $9.99!

        Click here to unsubscribe from future emails.
        """
    }

    score = scorer.score_email(
        subject=email["subject"],
        sender=email["sender"],
        body=email["body"]
    )

    print("\n" + "="*80)
    print("EXAMPLE 2: Marketing Email (Should Be Rejected)")
    print("="*80)
    print(scorer.get_detailed_report(score))


def example_netflix_payment():
    """Example: Netflix payment confirmation."""
    scorer = SubscriptionScorer(fuzzy=True)

    email = {
        "subject": "Payment confirmed for your Netflix subscription",
        "sender": "info@netflix.com",
        "body": """
        Payment Confirmed

        Your monthly Netflix subscription has been renewed.

        Total: $15.99
        Payment method: Card ending in 1234
        Next billing date: November 6, 2025

        Thank you for being a member.
        """
    }

    score = scorer.score_email(
        subject=email["subject"],
        sender=email["sender"],
        body=email["body"]
    )

    print("\n" + "="*80)
    print("EXAMPLE 3: Netflix Payment Confirmation")
    print("="*80)
    print(scorer.get_detailed_report(score))


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SUBSCRIPTION SCORING SYSTEM v2.2 - EXAMPLES")
    print("="*80)

    example_github_subscription()
    example_netflix_payment()
    example_marketing_email()

    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")
