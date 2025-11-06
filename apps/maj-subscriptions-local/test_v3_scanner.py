#!/usr/bin/env python3
"""
Test Production Document Scanner v3.0
Compares v3.0 (deepseek 671B) vs old system (llama3.2 3B)
"""

import sys
import os
from production_document_scanner_v3 import DocumentClassifier

# Test documents (problematic ones from user's analysis)
TEST_DOCUMENTS = [
    {
        "file_path": "/tmp/test_faktura.txt",
        "text_content": """
FAKTURA č. 2025-001
Datum vystavení: 2025-01-15
Dodavatel: ABC s.r.o., IČO: 12345678, DIČ: CZ12345678

Položky:
- Služby: 1500 CZK

Celkem k úhradě: 1500 CZK
Splatnost: 2025-01-30
"""
    },
    {
        "file_path": "/tmp/test_uctenka.txt",
        "text_content": """
ALBERTЧEKЦÁ
Praha 4, Nusle

Datum: 15.01.2025 14:32

Pečivo             45.90
Mléko 1L           28.50
Jogurt             12.90

CELKEM:            87.30 Kč
Hotově:           100.00 Kč
Vráceno:           12.70 Kč

Děkujeme za nákup!
"""
    },
    {
        "file_path": "/tmp/test_soudni_dokument.txt",
        "text_content": """
OKRESNÍ SOUD V PRAZE
Sp. zn.: 45 C 123/2024

USNESENÍ

Okresní soud v Praze rozhodl ve věci žalobce Jan Novák
proti žalovanému Petr Svoboda o zaplacení částky 50 000 Kč

ROZHODNUTÍ:
Žaloba se zamítá.

Odůvodnění dle § 157 OSŘ:
[...]

V Praze dne 15.01.2025
JUDr. Marie Černá
předsedkyně senátu
"""
    },
    {
        "file_path": "/tmp/test_marketing_email.txt",
        "text_content": """
Vážený zákazníku,

máme pro Vás skvělou nabídku! Jen dnes sleva 50% na všechny produkty!

Nakupujte nyní:
- Oblečení
- Elektronika
- Hračky

Klikněte ZDE pro více informací!

Odhlášení: klikněte zde

S pozdravem,
E-shop Team
"""
    },
    {
        "file_path": "/tmp/test_bankovni_vypis.txt",
        "text_content": """
ČESKÁ SPOŘITELNA, a.s.
Výpis z účtu č. 123456789/0800

Období: 01.01.2025 - 31.01.2025

Datum      Popis                    Částka      Zůstatek
------------------------------------------------------
15.01.2025 Platba kartou           -245.50     15 234.50
16.01.2025 Příchozí platba        +5 000.00    20 234.50
17.01.2025 Trvalý příkaz          -1 200.00    19 034.50

Konečný zůstatek: 19 034.50 CZK
"""
    }
]

def main():
    print("="*60)
    print("🧪 TESTING PRODUCTION DOCUMENT SCANNER v3.0")
    print("="*60)
    print(f"📦 Model: deepseek-v3.1:671b-cloud (671B parameters)")
    print(f"👥 Workers: 12 (auto-scaling)")
    print(f"🎯 Target: <20% 'jine' classification (vs old 74%)")
    print("="*60)
    print()

    # Initialize classifier
    classifier = DocumentClassifier(db_path=":memory:")  # In-memory DB for testing

    try:
        # Run classification
        results = classifier.scan_documents(TEST_DOCUMENTS)

        # Print results
        print("\n" + "="*60)
        print("📊 CLASSIFICATION RESULTS")
        print("="*60)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result['filename']}")
            print(f"   Type: {result['document_type']}")
            print(f"   Score: {result['score']}/200 ({result['confidence_percent']}%)")
            print(f"   Level: {result['confidence_level']}")
            print(f"   Reasoning: {result.get('reasoning', 'N/A')}")

            # Check for >100% bug
            if result['confidence_percent'] > 100:
                print(f"   ⚠️ WARNING: Confidence > 100%! BUG DETECTED!")

        # Print summary
        classifier.print_summary()

        # Calculate "jine" rate
        total = len(results)
        jine_count = sum(1 for r in results if r['document_type'] == 'jine')
        jine_rate = (jine_count / total) * 100 if total > 0 else 0

        print("\n" + "="*60)
        print("🎯 PERFORMANCE COMPARISON")
        print("="*60)
        print(f"Old System (llama3.2:3b): 74% 'jine' classification ❌")
        print(f"New System (deepseek 671B): {jine_rate:.1f}% 'jine' classification", end="")
        if jine_rate < 20:
            print(" ✅")
        else:
            print(" ⚠️")
        print()

        # Check for confidence >100% bug
        bug_found = any(r['confidence_percent'] > 100 for r in results)
        print(f"AI Confidence >100% Bug: {'FIXED ✅' if not bug_found else 'STILL PRESENT ❌'}")
        print("="*60)

    finally:
        classifier.close()

if __name__ == "__main__":
    main()
