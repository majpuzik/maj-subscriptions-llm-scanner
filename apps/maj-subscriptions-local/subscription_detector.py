#!/usr/bin/env python3
"""
Subscription Detector for Unified MCP v5
Hybrid approach: Keyword pre-filter + LLM final decision

Simplified version without Thunderbird integration - designed for unified-mcp-server
"""

import requests
import json
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_URL = "http://192.168.10.83:11434/api/generate"
MODEL_NAME = "kimi-k2:1t-cloud"
OLLAMA_TIMEOUT = 120

# Quick keyword filter (pre-screening)
SUBSCRIPTION_KEYWORDS = [
    'predplatne', 'predplatneho', 'subscription', 'abonnement',
    'clenstvi', 'membership', 'rocni poplatek', 'monthly fee',
    'renewal', 'license', 'trial', 'premium', 'pro plan',
    'invoice', 'faktura', 'ucet', 'bill', 'payment', 'platba',
    'receipt', 'potvrzeni', 'obnoveni', 'prodlouzeni',
]


def quick_keyword_filter(subject: str, body: str) -> bool:
    """
    Fast keyword-based pre-filtering
    Returns True if email MIGHT be subscription-related
    """
    content = (subject + ' ' + body[:2000]).lower()

    # Remove accents for Czech text
    content = content.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    content = content.replace('ó', 'o').replace('ú', 'u').replace('ů', 'u')
    content = content.replace('ý', 'y').replace('č', 'c').replace('ď', 'd')
    content = content.replace('ě', 'e').replace('ň', 'n').replace('ř', 'r')
    content = content.replace('š', 's').replace('ť', 't').replace('ž', 'z')

    # Check for keywords
    for keyword in SUBSCRIPTION_KEYWORDS:
        if keyword in content:
            return True

    return False


def analyze_with_llm(subject: str, sender: str, body: str) -> Dict:
    """
    Analyze email with LLM (kimi-k2:1t-cloud)
    Returns structured JSON with subscription data
    """
    prompt = f"""Analyzuj tento email a urci, jestli obsahuje informaci o predplatnem/subscription.

EMAIL:
From: {sender}
Subject: {subject}
Body (first 1000 chars):
{body[:1000]}

Pokud email obsahuje informaci o predplatnem, vrat JSON s temito udaji:
{{
    "is_subscription": true,
    "confidence": <0-100>,
    "service_name": "<nazev sluzby>",
    "amount": <castka nebo null>,
    "currency": "<mena nebo null>",
    "subscription_type": "<monthly/yearly/quarterly nebo null>",
    "reasoning": "<strucne zduvodneni>"
}}

Pokud email NENI o predplatnem, vrat:
{{
    "is_subscription": false,
    "confidence": <0-100>,
    "reasoning": "<proc to neni predplatne>"
}}

VRAT POUZE VALIDNI JSON, BEZ DALSIHO TEXTU."""

    try:
        logger.info(f"Calling LLM for: {subject[:50]}...")

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code}")
            return {
                "is_subscription": False,
                "confidence": 0,
                "reasoning": f"API error: {response.status_code}",
                "error": response.text
            }

        result_data = response.json()
        result_text = result_data.get('response', '').strip()

        # Debug: Log raw LLM output
        logger.debug(f"Raw LLM output: {result_text[:200]}...")

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        result = json.loads(result_text)

        # Debug: Log parsed values
        logger.debug(f"Parsed: is_subscription={result.get('is_subscription')}, "
                    f"confidence={result.get('confidence')}, "
                    f"service={result.get('service_name', 'N/A')}")

        logger.info(f"LLM: {'✅ SUBSCRIPTION' if result.get('is_subscription') else '❌ NOT SUBSCRIPTION'} "
                   f"(confidence: {result.get('confidence', 0)}%)")

        return result

    except requests.Timeout:
        logger.error(f"LLM timeout after {OLLAMA_TIMEOUT}s")
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": f"Request timeout (>{OLLAMA_TIMEOUT}s)",
            "error": "timeout"
        }
    except Exception as e:
        logger.error(f"LLM analysis error: {e}")
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": f"Parse error: {str(e)}",
            "error": str(e)
        }


def extract_service_name_from_sender(sender: str) -> str:
    """Extract service name from email sender"""
    import re

    if '@' in sender:
        match = re.search(r'@([a-zA-Z0-9.-]+)', sender)
        if match:
            domain = match.group(1)
            service_name = domain.split('.')[0].title()
            if service_name and len(service_name) > 2:
                return service_name
    return "Unknown"


def detect_subscription(subject: str, sender: str, body: str) -> Dict:
    """
    Main entry point for subscription detection

    Args:
        subject: Email subject
        sender: Email sender
        body: Email body

    Returns:
        Dict with subscription data and Paperless-compatible format
    """
    logger.info(f"=== Subscription Detection ===")
    logger.info(f"Subject: {subject[:60]}...")
    logger.info(f"Sender: {sender[:60]}...")

    # STEP 1: Quick keyword filter (pre-screening)
    if not quick_keyword_filter(subject, body):
        logger.info("❌ No subscription keywords found - skipping LLM")
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": "No subscription keywords found",
            "paperless": {
                "tags": [],
                "document_type": "Email"
            }
        }

    logger.info("✓ Keywords found - proceeding with LLM analysis")

    # STEP 2: LLM analysis (final decision)
    llm_result = analyze_with_llm(subject, sender, body)

    # STEP 3: Format for Paperless
    if llm_result.get('is_subscription'):
        service_name = llm_result.get('service_name') or extract_service_name_from_sender(sender)
        subscription_type = llm_result.get('subscription_type')
        amount = llm_result.get('amount')
        currency = llm_result.get('currency')

        # NULL filtering
        if amount in (None, 'null', 'NULL', ''):
            amount = None
        if currency in (None, 'null', 'NULL', ''):
            currency = None
        if subscription_type in (None, 'null', 'NULL', ''):
            subscription_type = None

        # Build tags
        tags = ['předplatné', 'subscription']
        if service_name and service_name != "Unknown":
            tags.append(service_name)
        if subscription_type:
            tags.append(subscription_type)

        llm_result['paperless'] = {
            "tags": tags,
            "correspondent": service_name if service_name != "Unknown" else None,
            "document_type": "Subscription Notification",
            "amount": amount,
            "currency": currency
        }

        logger.info(f"✅ Subscription detected: {service_name} ({amount} {currency})")
    else:
        llm_result['paperless'] = {
            "tags": [],
            "document_type": "Email"
        }
        logger.info("❌ Not a subscription")

    return llm_result


# MCP Tool wrapper for command-line testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 3:
        subject = sys.argv[1]
        sender = sys.argv[2]
        body = sys.argv[3]

        result = detect_subscription(subject, sender, body)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python3 subscription_detector.py <subject> <sender> <body>")
        print("\nExample:")
        print('python3 subscription_detector.py "Your subscription renewal" "noreply@openai.com" "Your $20/month subscription..."')
