#!/usr/bin/env python3
"""
Marketing Email Detector v1.1
Rule-based classifier pro detekci marketingových/spam emailů
+ Whitelist/Blacklist integrace
"""

import re
from typing import Dict, Any, Tuple
from email.utils import parseaddr

# Import whitelist/blacklist
try:
    from email_lists import is_whitelisted, is_blacklisted, get_list_reason
    LISTS_AVAILABLE = True
except ImportError:
    LISTS_AVAILABLE = False
    print("⚠️  Whitelist/Blacklist není dostupný")


class MarketingEmailDetector:
    """
    Detekuje marketingové emaily pomocí pravidel a heuristik
    """

    # Marketingové klíčové fráze v předmětu
    MARKETING_SUBJECT_PATTERNS = [
        r'\b(sale|discount|offer|deal|save|free|limited|exclusive|special)\b',
        r'\b(today only|act now|don\'t miss|last chance|hurry)\b',
        r'\b(\d+%\s*off|save\s*\$|get\s*\d+)\b',
        r'[🎁🎉💰🔥⚡🎯💎✨🌟⭐]',  # Marketing emoji
        r'\b(sleva|akce|zdarma|výprodej|nabídka)\b',
        r'\b(black friday|cyber monday|flash sale)\b',
    ]

    # Marketingové domény odesílatelů
    MARKETING_FROM_PATTERNS = [
        r'^(no-?reply|noreply|do-not-reply)',
        r'^(newsletter|marketing|promo|promotions|offers)',
        r'^(news|info|hello|team|support)',
        r'@(mail\.|email\.|newsletter\.|promo\.)',
    ]

    # Unsubscribe indikátory
    UNSUBSCRIBE_PATTERNS = [
        r'unsubscribe',
        r'opt-out',
        r'opt out',
        r'remove from (this )?list',
        r'odhlásit',
        r'zrušit odběr',
        r'manage (your )?preferences',
        r'update (your )?preferences',
    ]

    # Typické marketingové fráze v těle
    MARKETING_BODY_PATTERNS = [
        r'view (this email )?in (your )?browser',
        r'click here',
        r'shop now',
        r'buy now',
        r'learn more',
        r'get started',
        r'sign up',
        r'subscribe now',
        r'limited time',
        r'while supplies last',
    ]

    # Důležité notifikace (NOT marketing) - negative patterns
    NOT_MARKETING_PATTERNS = [
        r'\b(subscription renewal|renewing your subscription|will renew)\b',
        r'\b(payment (confirmed|received|processed|successful))\b',
        r'\b(invoice|receipt|order confirmation)\b',
        r'\b(your order|order #\d+)\b',
        r'\b(account notification|important (account )?update)\b',
        r'\b(security alert|password reset|verify your account)\b',
        r'\b(statement|transaction|billing summary)\b',
        r'\b(obnov[aá] předplatn[éě]ho|potvrzení platby|faktura)\b',
        r'\b(předplatn[éě]|subscription)\b',  # Standalone subscription/předplatné
        r'\b(ukončení předplatn[éě]ho)\b',    # Subscription cancellation
        r'\b(renewal order|order receipt)\b',  # Renewal receipts
    ]

    def __init__(self):
        self.subject_regex = re.compile(
            '|'.join(self.MARKETING_SUBJECT_PATTERNS),
            re.IGNORECASE
        )
        self.from_regex = re.compile(
            '|'.join(self.MARKETING_FROM_PATTERNS),
            re.IGNORECASE
        )
        self.unsubscribe_regex = re.compile(
            '|'.join(self.UNSUBSCRIBE_PATTERNS),
            re.IGNORECASE
        )
        self.body_regex = re.compile(
            '|'.join(self.MARKETING_BODY_PATTERNS),
            re.IGNORECASE
        )
        self.not_marketing_regex = re.compile(
            '|'.join(self.NOT_MARKETING_PATTERNS),
            re.IGNORECASE
        )

    def analyze(self, email_data: Dict[str, Any]) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Analyzuje email a určí, zda je marketingový

        Args:
            email_data: Dictionary s klíči: subject, from, body, html_body (optional)

        Returns:
            Tuple[is_marketing, confidence_score, details]
            - is_marketing: True pokud je email detekován jako marketing
            - confidence_score: 0-100 skóre důvěry
            - details: Důvody klasifikace
        """
        score = 0
        max_score = 100
        reasons = []

        subject = email_data.get('subject', '')
        from_addr = email_data.get('from', '')
        body = email_data.get('body', '')
        html_body = email_data.get('html_body', '')

        # Combined text for analysis
        combined_text = f"{subject} {body} {html_body}".lower()

        # 0. NOT-MARKETING check (důležité notifikace) - HIGHEST PRIORITY
        not_marketing_matches = len(self.not_marketing_regex.findall(combined_text))
        if not_marketing_matches > 0:
            not_marketing_penalty = min(60, not_marketing_matches * 50)  # Silnější penalty!
            score -= not_marketing_penalty
            reasons.append(f"Important notification detected: {not_marketing_matches} indicators (invoice/receipt/renewal)")

        # 1. Whitelist/Blacklist check (NEGARANTUJE ne-marketing!)
        # Whitelist = důležitý odesilatel, ALE musí se testovat na marketing markery
        # (včera faktura, zítra může být marketing)
        is_whitelisted_sender = False
        if LISTS_AVAILABLE:
            _, email_addr = parseaddr(from_addr)
            if email_addr:
                domain = email_addr.split('@')[1] if '@' in email_addr else ''

                # Whitelist check - SNÍŽÍ score o 20 bodů (ne okamžitý return!)
                if is_whitelisted(email_addr, domain):
                    score -= 20  # Bonus pro důležité odesílatele
                    is_whitelisted_sender = True
                    reasons.append(f'Whitelisted: {domain} (but testing for marketing)')

                # Blacklist check - přidá vysoké skóre
                if is_blacklisted(email_addr, domain):
                    score += 60  # Silný indikátor marketingu
                    reasons.append(f'Blacklisted domain: {domain}')

        # 1. Analýza předmětu (25 bodů)
        subject_matches = len(self.subject_regex.findall(subject))
        if subject_matches > 0:
            subject_score = min(25, subject_matches * 8)
            score += subject_score
            reasons.append(f"Marketing keywords in subject: {subject_matches}")

        # Check for excessive capitalization
        if subject and len([c for c in subject if c.isupper()]) / len(subject) > 0.5:
            score += 10
            reasons.append("Excessive capitalization in subject")

        # 2. Analýza odesílatele (20 bodů)
        _, email_addr = parseaddr(from_addr)
        from_matches = []
        if email_addr:
            from_matches = self.from_regex.findall(email_addr.lower())
            if from_matches:
                score += 20
                reasons.append(f"Marketing sender pattern: {from_matches[0]}")

        # 3. Unsubscribe link (30 bodů - silný indikátor)
        if self.unsubscribe_regex.search(combined_text):
            score += 30
            reasons.append("Unsubscribe link found")

        # 4. Marketingové fráze v těle (15 bodů)
        body_matches = len(self.body_regex.findall(combined_text))
        if body_matches > 0:
            body_score = min(15, body_matches * 3)
            score += body_score
            reasons.append(f"Marketing phrases in body: {body_matches}")

        # 5. HTML analýza (10 bodů)
        link_count = 0
        img_count = 0
        if html_body:
            # Počet odkazů
            link_count = len(re.findall(r'<a\s+href=', html_body, re.IGNORECASE))
            if link_count > 5:
                score += 5
                reasons.append(f"Many links in HTML: {link_count}")

            # Obrázky
            img_count = len(re.findall(r'<img\s+', html_body, re.IGNORECASE))
            if img_count > 3:
                score += 5
                reasons.append(f"Many images: {img_count}")

        # 6. Tracking pixels (5 bodů)
        if re.search(r'(tracking|pixel|beacon|analytics)', combined_text, re.IGNORECASE):
            score += 5
            reasons.append("Tracking elements detected")

        # Normalizace skóre (nemůže být záporné ani přes 100)
        confidence = max(0, min(100, score))

        # Rozhodnutí - threshold 40
        is_marketing = confidence >= 40

        details = {
            'confidence': confidence,
            'reasons': reasons,
            'is_whitelisted': is_whitelisted_sender,
            'score_breakdown': {
                'subject_analysis': subject_matches * 8 if subject_matches else 0,
                'sender_analysis': 20 if from_matches else 0 if email_addr else 0,
                'unsubscribe_present': 30 if self.unsubscribe_regex.search(combined_text) else 0,
                'body_phrases': min(15, body_matches * 3) if body_matches else 0,
                'html_elements': min(10, (5 if link_count > 5 else 0) + (5 if img_count > 3 else 0)) if html_body else 0,
                'whitelist_bonus': -20 if is_whitelisted_sender else 0,
            }
        }

        return is_marketing, confidence, details

    def classify_batch(self, emails: list) -> list:
        """
        Klasifikuje více emailů najednou

        Args:
            emails: List[Dict] - seznam emailů k analýze

        Returns:
            List[Dict] s výsledky klasifikace
        """
        results = []
        for email in emails:
            is_marketing, confidence, details = self.analyze(email)
            results.append({
                'email': email,
                'is_marketing': is_marketing,
                'confidence': confidence,
                'details': details
            })
        return results


if __name__ == "__main__":
    # Test příklad
    detector = MarketingEmailDetector()

    test_emails = [
        {
            'subject': '🎉 50% OFF - Limited Time Only!',
            'from': 'newsletter@shop.example.com',
            'body': 'Click here to shop now! Unsubscribe at any time.',
            'html_body': '<a href="#">Shop Now</a>' * 10
        },
        {
            'subject': 'Meeting reminder for tomorrow',
            'from': 'john.doe@company.com',
            'body': 'Hi, just a reminder about our meeting tomorrow at 2pm.',
            'html_body': ''
        }
    ]

    for idx, email in enumerate(test_emails, 1):
        is_marketing, confidence, details = detector.analyze(email)
        print(f"\n{'='*60}")
        print(f"Email {idx}: {email['subject'][:50]}")
        print(f"Marketing: {is_marketing} (confidence: {confidence}%)")
        print(f"Reasons: {', '.join(details['reasons'])}")
