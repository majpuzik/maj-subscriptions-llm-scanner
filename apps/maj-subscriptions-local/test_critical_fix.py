#!/usr/bin/env python3
"""
Test script for critical classification bug fix
Tests marketing email detection and legal document classification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from document_classifier_api import UniversalDocumentClassifier

# Test cases
TEST_CASES = [
    {
        "name": "AutoScout24 newsletter (previously misclassified as german_court)",
        "text": """Subject: Neue Angebote für Mercedes-Benz
From: noreply@autoscout24.de

Hallo,

Neue Fahrzeuge in Ihrer Region:
- Mercedes-Benz E-Klasse
- Mercedes-Benz C-Klasse

Beste Grüße,
Ihr AutoScout24 Team

Abmelden: https://autoscout24.de/unsubscribe""",
        "expected_type": "marketing_email",
        "should_not_be": "german_court"
    },
    {
        "name": "Blinkist promotional email (previously misclassified as german_court)",
        "text": """Subject: 7-Day Free Trial - Premium Access
From: hello@blinkist.com

Start your journey today!

Unsubscribe here: https://blinkist.com/unsubscribe""",
        "expected_type": "marketing_email",
        "should_not_be": "german_court"
    },
    {
        "name": "Political newsletter mentioning Polizei (should be marketing, not german_police)",
        "text": """Subject: Kopp Report Newsletter
From: newsletter@kopp-report.de

Die Bundespolizei hat heute neue Maßnahmen angekündigt...

[ARTIKEL TEXT...]

Newsletter abbestellen: https://kopp-report.de/unsubscribe""",
        "expected_type": "marketing_email",
        "should_not_be": "german_police"
    },
    {
        "name": "Real German court document (should still be classified correctly)",
        "text": """Amtsgericht München

Sp. zn.: 123 C 4567/2024

Vorladung

§ 128 ZPO

Der Termin ist auf den 15.01.2025 anberaumt.

gez. JUDr. Schmidt
Richter am Amtsgericht""",
        "expected_type": "german_court",
        "should_not_be": "marketing_email"
    },
    {
        "name": "Newsletter mentioning Amtsgericht (should be marketing, not court)",
        "text": """Subject: NZZ Daily Digest
From: newsletter@nzz.ch

Heute meistgelesen:

Artikel: "Urteil des Amtsgericht Berlin sorgt für Diskussion"

[ARTIKEL TEXT...]

Newsletter abbestellen""",
        "expected_type": "marketing_email",
        "should_not_be": "german_court"
    }
]

def test_classification():
    """Run all test cases"""
    classifier = UniversalDocumentClassifier()

    print("=" * 80)
    print("CRITICAL BUG FIX - CLASSIFICATION TEST")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_CASES)}: {test['name']}")
        print(f"{'=' * 80}")

        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write(test['text'])
            tmp.flush()

            # Classify
            result = classifier.classify_document(tmp.name, text_content=test['text'])
            os.unlink(tmp.name)

        doc_type = result.get('document_type')
        confidence = result.get('confidence', 0)

        print(f"\n📄 Document Type: {doc_type}")
        print(f"📊 Confidence: {confidence}%")
        print(f"🏷️  Tags: {result.get('paperless', {}).get('tags', [])}")

        # Check expectations
        expected = test['expected_type']
        should_not = test['should_not_be']

        if doc_type == expected and doc_type != should_not:
            print(f"\n✅ PASS: Correctly classified as '{expected}'")
            passed += 1
        else:
            print(f"\n❌ FAIL:")
            print(f"   Expected: '{expected}'")
            print(f"   Got: '{doc_type}'")
            if doc_type == should_not:
                print(f"   ⚠️  CRITICAL: Still misclassified as '{should_not}'!")
            failed += 1

    # Summary
    print(f"\n{'=' * 80}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"✅ Passed: {passed}/{len(TEST_CASES)}")
    print(f"❌ Failed: {failed}/{len(TEST_CASES)}")
    print(f"{'=' * 80}")

    return failed == 0

if __name__ == "__main__":
    success = test_classification()
    sys.exit(0 if success else 1)
