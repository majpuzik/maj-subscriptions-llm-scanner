#!/usr/bin/env python3
"""
Srovnávací test: Ollama LLM (kimi-k2:1t) vs Keyword Matching
Testuje přesnost detekce předplatných v emailech
"""

import sqlite3
import json
from pathlib import Path
import requests

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "kimi-k2:1t-cloud"  # 1 trillion parameters

def analyze_email_with_llm(subject: str, sender: str, body: str) -> dict:
    """Nechá LLM analyzovat email a určit, jestli obsahuje předplatné"""

    prompt = f"""Analyzuj tento email a urči, jestli obsahuje informaci o předplatném/subscription.

EMAIL:
From: {sender}
Subject: {subject}
Body (first 1000 chars):
{body[:1000]}

Pokud email obsahuje informaci o předplatném, vrať JSON s těmito údaji:
{{
    "is_subscription": true,
    "confidence": <0-100>,
    "service_name": "<název služby>",
    "amount": <částka nebo null>,
    "currency": "<měna nebo null>",
    "subscription_type": "<monthly/yearly/quarterly nebo null>",
    "reasoning": "<stručné zdůvodnění>"
}}

Pokud email NENÍ o předplatném, vrať:
{{
    "is_subscription": false,
    "confidence": <0-100>,
    "reasoning": "<proč to není předplatné>"
}}

VRAŤ POUZE VALIDNÍ JSON, BEZ DALŠÍHO TEXTU."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120  # 2 minutes timeout
        )

        if response.status_code != 200:
            return {
                "is_subscription": False,
                "confidence": 0,
                "reasoning": f"API error: {response.status_code}",
                "error": response.text
            }

        result_data = response.json()
        result_text = result_data.get('response', '').strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        result = json.loads(result_text)
        return result

    except requests.Timeout:
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": "Request timeout (>120s)",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": f"Parse error: {str(e)}",
            "error": str(e)
        }


def get_sample_emails(db_path: str, sample_size: int = 20):
    """Vezme vzorek emailů - mix vysokých a nízkých confidence scores"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vezmi mix:
    # - 10 s nejvyšším confidence (keyword matching říká "jistě předplatné")
    # - 10 s nejnižším confidence (keyword matching je nejistý)

    high_confidence = cursor.execute('''
        SELECT email_from, email_subject, email_body_compact, confidence_score
        FROM email_evidence
        ORDER BY confidence_score DESC
        LIMIT ?
    ''', (sample_size // 2,)).fetchall()

    low_confidence = cursor.execute('''
        SELECT email_from, email_subject, email_body_compact, confidence_score
        FROM email_evidence
        ORDER BY confidence_score ASC
        LIMIT ?
    ''', (sample_size // 2,)).fetchall()

    conn.close()

    return {
        'high_confidence': high_confidence,
        'low_confidence': low_confidence
    }


def run_comparison_test(db_path: str, output_file: str = '/tmp/llm_vs_keywords_test.json'):
    """Spustí srovnávací test"""

    print(f"🔬 Srovnávací test: {MODEL_NAME} vs Keyword Matching")
    print("=" * 80)

    # Vezmi vzorky
    samples = get_sample_emails(db_path, sample_size=20)

    results = {
        'model': MODEL_NAME,
        'high_confidence_samples': [],
        'low_confidence_samples': [],
        'statistics': {
            'total_analyzed': 0,
            'llm_agrees': 0,
            'llm_disagrees': 0,
            'llm_higher_confidence': 0,
            'keyword_higher_confidence': 0
        }
    }

    print(f"\n📊 Analyzuji {len(samples['high_confidence']) + len(samples['low_confidence'])} emailů...\n")

    # Test high confidence emails
    print("🔥 HIGH CONFIDENCE (keyword matching říká: určitě předplatné)")
    print("-" * 80)

    for idx, (sender, subject, body, kw_confidence) in enumerate(samples['high_confidence'], 1):
        print(f"\n{idx}. {subject[:60]}...")
        print(f"   Keyword confidence: {kw_confidence}")

        llm_result = analyze_email_with_llm(subject, sender, body or "")

        print(f"   LLM says: {'✅ JE předplatné' if llm_result.get('is_subscription') else '❌ NENÍ předplatné'}")
        print(f"   LLM confidence: {llm_result.get('confidence', 0)}")
        print(f"   Reasoning: {llm_result.get('reasoning', 'N/A')[:80]}...")

        results['high_confidence_samples'].append({
            'subject': subject,
            'sender': sender,
            'keyword_confidence': kw_confidence,
            'llm_result': llm_result
        })

        results['statistics']['total_analyzed'] += 1
        if llm_result.get('is_subscription'):
            results['statistics']['llm_agrees'] += 1
        else:
            results['statistics']['llm_disagrees'] += 1

    # Test low confidence emails
    print("\n\n❄️  LOW CONFIDENCE (keyword matching nejistý)")
    print("-" * 80)

    for idx, (sender, subject, body, kw_confidence) in enumerate(samples['low_confidence'], 1):
        print(f"\n{idx}. {subject[:60]}...")
        print(f"   Keyword confidence: {kw_confidence}")

        llm_result = analyze_email_with_llm(subject, sender, body or "")

        print(f"   LLM says: {'✅ JE předplatné' if llm_result.get('is_subscription') else '❌ NENÍ předplatné'}")
        print(f"   LLM confidence: {llm_result.get('confidence', 0)}")
        print(f"   Reasoning: {llm_result.get('reasoning', 'N/A')[:80]}...")

        results['low_confidence_samples'].append({
            'subject': subject,
            'sender': sender,
            'keyword_confidence': kw_confidence,
            'llm_result': llm_result
        })

        results['statistics']['total_analyzed'] += 1
        if not llm_result.get('is_subscription'):
            results['statistics']['llm_agrees'] += 1
        else:
            results['statistics']['llm_disagrees'] += 1

    # Uložit výsledky
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Statistiky
    print("\n\n📈 CELKOVÉ STATISTIKY")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Celkem analyzováno: {results['statistics']['total_analyzed']}")
    print(f"LLM souhlasí s keywords: {results['statistics']['llm_agrees']}")
    print(f"LLM nesouhlasí: {results['statistics']['llm_disagrees']}")
    print(f"\nShoda: {results['statistics']['llm_agrees'] / results['statistics']['total_analyzed'] * 100:.1f}%")
    print(f"\nVýsledky uloženy do: {output_file}")

    return results


if __name__ == '__main__':
    db_path = "/tmp/test_subscriptions.db"

    print(f"🚀 Spouštím srovnávací test s {MODEL_NAME}...")
    print()

    results = run_comparison_test(db_path)

    print("\n✅ Test dokončen!")
