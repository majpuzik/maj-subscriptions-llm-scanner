# Unified MCP v5 Migration Guide

**Datum:** 2025-01-03 19:30
**Cíl:** Přidat Marketing Email Detector + Subscription Detector do unified-mcp-server
**Status:** 🚧 IN PROGRESS

---

## 🎯 Cíl migrace

**Unified MCP v5 = Single Source of Truth** pro všechny klasifikace napříč aplikacemi:
- Paperless-NGX
- MAJ Subscriptions
- Budoucí aplikace

---

## 📊 Aktuální stav

### ✅ Existující classifiers na NAS5:

```
/volume1/docker/unified-mcp-server/
├── legal_doc_identifier.py          (v2.0) ✓
├── cz_receipt_intelligence.py       (v2.0) ✓
├── bank_statement_processor.py      (v2.2) ✓
└── http-server.js                   (Node.js API server)
```

### API Endpointy:
- `/paperless-intelligence/classify` - unified document classification
- `/paperless-intelligence/upload` - upload do Paperless
- `/paperless-intelligence/search` - search in Paperless

---

## 🆕 Co přidáváme

### 1. **Marketing Email Detector** (v1.4)

**Soubory:**
```
/volume1/docker/unified-mcp-server/
├── marketing_email_detector.py      (NEW)
├── email_lists.py                   (NEW - whitelist/blacklist)
└── email_whitelist.json             (NEW)
└── email_blacklist.json             (NEW)
```

**Features:**
- Rule-based classification
- NOT_MARKETING patterns (subscription renewals, invoices)
- Newsletter detection
- Whitelist/Blacklist support
- Czech language support

**API Endpoint:**
```javascript
POST /api/v5/classify/marketing
{
  "subject": "Your subscription renewal",
  "from": "noreply@openai.com",
  "body": "Your subscription will renew..."
}

Response:
{
  "is_marketing": false,
  "confidence": 30,
  "category": "subscription_renewal",
  "reasons": ["Important notification detected: 3 indicators"],
  "paperless": {
    "tags": ["důležité", "předplatné"],
    "document_type": "Subscription Notification"
  }
}
```

---

### 2. **Subscription Detector** (LLM-based)

**Soubory:**
```
/volume1/docker/unified-mcp-server/
└── subscription_detector.py         (NEW - LLM-based)
```

**Features:**
- Hybrid approach (keyword pre-filter + LLM)
- Uses Kimi-k2:1t-cloud (1T parameters)
- Service name extraction
- Amount/currency detection
- Subscription type detection

**API Endpoint:**
```javascript
POST /api/v5/classify/subscription
{
  "subject": "OpenAI Subscription Renewal",
  "from": "noreply@openai.com",
  "body": "Your $20/month subscription..."
}

Response:
{
  "is_subscription": true,
  "confidence": 85,
  "service_name": "OpenAI",
  "amount": 20.0,
  "currency": "USD",
  "subscription_type": "monthly",
  "reasoning": "Clear subscription renewal with amount",
  "paperless": {
    "tags": ["předplatné", "OpenAI", "monthly"],
    "correspondent": "OpenAI",
    "document_type": "Subscription Invoice"
  }
}
```

---

### 3. **Unified Classification Endpoint**

**API Endpoint:**
```javascript
POST /api/v5/classify
{
  "file_path": "/path/to/file.pdf",
  "text_content": "...",
  "email_data": {
    "subject": "...",
    "from": "...",
    "body": "..."
  }
}

Response:
{
  "document_type": "subscription_invoice",
  "confidence": 85,
  "correspondent": "OpenAI",
  "tags": ["předplatné", "OpenAI", "monthly"],
  "amount": 20.0,
  "currency": "USD",
  "date": "2025-01-15",
  "metadata": {
    "classified_by": "subscription_detector",
    "all_results": [...]
  }
}
```

**Logic:**
1. Try all available classifiers
2. Collect results with confidence > threshold
3. Return best result (highest confidence)
4. Include metadata with all attempted classifications

---

## 🔧 Implementation Steps

### Step 1: Upload Python modules ✅ PENDING

```bash
# Copy files to NAS5
scp -P 4438 marketing_email_detector.py admin@192.168.10.35:/volume1/docker/unified-mcp-server/
scp -P 4438 email_lists.py admin@192.168.10.35:/volume1/docker/unified-mcp-server/
scp -P 4438 email_whitelist.json admin@192.168.10.35:/volume1/docker/unified-mcp-server/
scp -P 4438 email_blacklist.json admin@192.168.10.35:/volume1/docker/unified-mcp-server/
scp -P 4438 subscription_detector.py admin@192.168.10.35:/volume1/docker/unified-mcp-server/
```

---

### Step 2: Add MCP tools to server.js ⏳ PENDING

**Location:** `/volume1/docker/unified-mcp-server/server.js`

Add new tool definitions:

```javascript
// Marketing Email Detector
{
  name: "classify_marketing_email",
  description: "Classify email as marketing/newsletter/subscription renewal",
  inputSchema: {
    type: "object",
    properties: {
      subject: { type: "string" },
      from: { type: "string" },
      body: { type: "string" }
    },
    required: ["subject", "from", "body"]
  }
}

// Subscription Detector
{
  name: "detect_subscription",
  description: "Detect and extract subscription information from email",
  inputSchema: {
    type: "object",
    properties: {
      subject: { type: "string" },
      from: { type: "string" },
      body: { type: "string" }
    },
    required: ["subject", "from", "body"]
  }
}

// Unified Classifier
{
  name: "classify_unified",
  description: "Universal classifier - tries all available modules",
  inputSchema: {
    type: "object",
    properties: {
      file_path: { type: "string" },
      text_content: { type: "string" },
      email_data: { type: "object" }
    }
  }
}
```

---

### Step 3: Add HTTP API endpoints ⏳ PENDING

**Location:** `/volume1/docker/unified-mcp-server/http-server.js`

```javascript
/**
 * Marketing Email Classification
 * POST /api/v5/classify/marketing
 */
app.post('/api/v5/classify/marketing', async (req, res) => {
    try {
        const { subject, from, body } = req.body;

        if (!subject || !from || !body) {
            return res.status(400).json({
                success: false,
                error: 'subject, from, and body are required'
            });
        }

        console.log(`📧 Classifying marketing email: ${subject.substring(0, 50)}...`);

        const result = await callMCPTool('classify_marketing_email', {
            subject,
            from,
            body
        });

        res.json({
            success: true,
            classification: result
        });
    } catch (error) {
        console.error('❌ Error classifying marketing email:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Subscription Detection
 * POST /api/v5/classify/subscription
 */
app.post('/api/v5/classify/subscription', async (req, res) => {
    try {
        const { subject, from, body } = req.body;

        if (!subject || !from || !body) {
            return res.status(400).json({
                success: false,
                error: 'subject, from, and body are required'
            });
        }

        console.log(`💳 Detecting subscription: ${subject.substring(0, 50)}...`);

        const result = await callMCPTool('detect_subscription', {
            subject,
            from,
            body
        });

        res.json({
            success: true,
            detection: result
        });
    } catch (error) {
        console.error('❌ Error detecting subscription:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Unified Classification (all classifiers)
 * POST /api/v5/classify
 */
app.post('/api/v5/classify', async (req, res) => {
    try {
        const { file_path, text_content, email_data } = req.body;

        console.log(`🔍 Unified classification request`);

        const result = await callMCPTool('classify_unified', {
            file_path,
            text_content,
            email_data
        });

        res.json({
            success: true,
            classification: result
        });
    } catch (error) {
        console.error('❌ Error in unified classification:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});
```

---

### Step 4: Create subscription_detector.py ⏳ PENDING

Extract from `production_llm_scanner.py`:
- `quick_keyword_filter()` method
- `analyze_with_llm()` method
- Ollama configuration
- Subscription keywords

**Simplified version (bez Thunderbird integrace):**

```python
#!/usr/bin/env python3
"""
Subscription Detector for Unified MCP v5
Hybrid approach: Keyword pre-filter + LLM final decision
"""

import requests
import json
from typing import Dict, Optional

OLLAMA_URL = "http://192.168.10.83:11434/api/generate"
MODEL_NAME = "kimi-k2:1t-cloud"
OLLAMA_TIMEOUT = 120

SUBSCRIPTION_KEYWORDS = [
    'predplatne', 'predplatneho', 'subscription', 'abonnement',
    'clenstvi', 'membership', 'rocni poplatek', 'monthly fee',
    'renewal', 'license', 'trial', 'premium', 'pro plan',
    'invoice', 'faktura', 'ucet', 'bill', 'payment', 'platba',
    'receipt', 'potvrzeni', 'obnoveni', 'prodlouzeni',
]

def quick_keyword_filter(subject: str, body: str) -> bool:
    """Fast keyword-based pre-filtering"""
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
    """Analyze email with LLM"""
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
            return {
                "is_subscription": False,
                "confidence": 0,
                "reasoning": f"API error: {response.status_code}"
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

    except Exception as e:
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": f"Error: {str(e)}"
        }

def detect_subscription(subject: str, sender: str, body: str) -> Dict:
    """Main entry point for subscription detection"""

    # STEP 1: Quick keyword filter
    if not quick_keyword_filter(subject, body):
        return {
            "is_subscription": False,
            "confidence": 0,
            "reasoning": "No subscription keywords found",
            "paperless": {
                "tags": [],
                "document_type": "Email"
            }
        }

    # STEP 2: LLM analysis
    llm_result = analyze_with_llm(subject, sender, body)

    # STEP 3: Format for Paperless
    if llm_result.get('is_subscription'):
        service_name = llm_result.get('service_name', 'Unknown')
        subscription_type = llm_result.get('subscription_type')

        tags = ['předplatné', 'subscription']
        if service_name:
            tags.append(service_name)
        if subscription_type:
            tags.append(subscription_type)

        llm_result['paperless'] = {
            "tags": tags,
            "correspondent": service_name,
            "document_type": "Subscription Notification",
            "amount": llm_result.get('amount'),
            "currency": llm_result.get('currency')
        }
    else:
        llm_result['paperless'] = {
            "tags": [],
            "document_type": "Email"
        }

    return llm_result

# MCP Tool wrapper
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        subject = sys.argv[1]
        sender = sys.argv[2]
        body = sys.argv[3]
        result = detect_subscription(subject, sender, body)
        print(json.dumps(result, indent=2))
```

---

### Step 5: Restart unified-mcp-server ⏳ PENDING

```bash
ssh admin@192.168.10.35 -p 4438
cd /volume1/docker/unified-mcp-server
sudo docker-compose restart
```

---

## 📝 Testing Plan

### Test 1: Marketing Email Detection

```bash
curl -X POST http://192.168.10.35:8080/api/v5/classify/marketing \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Newsletter: Heute meistgelesen",
    "from": "noreply@nzz.ch",
    "body": "Top stories... Unsubscribe here"
  }'
```

**Expected:**
```json
{
  "is_marketing": true,
  "confidence": 70,
  "category": "newsletter",
  "reasons": ["Newsletter pattern", "Unsubscribe link"]
}
```

### Test 2: Subscription Renewal (NOT marketing)

```bash
curl -X POST http://192.168.10.35:8080/api/v5/classify/marketing \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Your OpenAI subscription renewal",
    "from": "noreply@openai.com",
    "body": "Your $20/month subscription will renew..."
  }'
```

**Expected:**
```json
{
  "is_marketing": false,
  "confidence": 0,
  "reasons": ["Important notification detected: subscription renewal"]
}
```

### Test 3: Subscription Detection

```bash
curl -X POST http://192.168.10.35:8080/api/v5/classify/subscription \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Your OpenAI subscription renewal",
    "from": "noreply@openai.com",
    "body": "Your $20/month ChatGPT Plus subscription will renew on Jan 15..."
  }'
```

**Expected:**
```json
{
  "is_subscription": true,
  "confidence": 85,
  "service_name": "OpenAI",
  "amount": 20.0,
  "currency": "USD",
  "subscription_type": "monthly"
}
```

---

## 🔄 Client Integration

### Paperless-NGX pre-consume script

```bash
#!/bin/bash
# /volume1/docker/paperless-ngx/scripts/unified_pre_consume.sh

FILE_PATH="$1"

# Extract email data
SUBJECT=$(python3 extract_email.py --field subject "$FILE_PATH")
FROM=$(python3 extract_email.py --field from "$FILE_PATH")
BODY=$(python3 extract_email.py --field body "$FILE_PATH")

# Call unified-mcp-server
RESULT=$(curl -s -X POST http://192.168.10.35:8080/api/v5/classify \
  -H "Content-Type: application/json" \
  -d "{
    \"email_data\": {
      \"subject\": \"$SUBJECT\",
      \"from\": \"$FROM\",
      \"body\": \"$BODY\"
    }
  }")

# Parse result
DOC_TYPE=$(echo "$RESULT" | jq -r '.classification.document_type')
TAGS=$(echo "$RESULT" | jq -r '.classification.paperless.tags | join(",")')
CORRESPONDENT=$(echo "$RESULT" | jq -r '.classification.paperless.correspondent')

# Export for Paperless
export PAPERLESS_DOCUMENT_TYPE="$DOC_TYPE"
export PAPERLESS_TAGS="$TAGS"
export PAPERLESS_CORRESPONDENT="$CORRESPONDENT"
```

### MAJ Subscriptions API client

```python
# apps/maj-subscriptions-local/unified_mcp_client.py

import requests
from typing import Dict

class UnifiedMCPClient:
    """Client for unified-mcp-server v5 API"""

    def __init__(self, base_url="http://192.168.10.35:8080"):
        self.base_url = base_url

    def classify_marketing(self, subject: str, sender: str, body: str) -> Dict:
        """Classify email as marketing/newsletter"""
        response = requests.post(
            f"{self.base_url}/api/v5/classify/marketing",
            json={"subject": subject, "from": sender, "body": body}
        )
        return response.json()

    def detect_subscription(self, subject: str, sender: str, body: str) -> Dict:
        """Detect subscription information"""
        response = requests.post(
            f"{self.base_url}/api/v5/classify/subscription",
            json={"subject": subject, "from": sender, "body": body}
        )
        return response.json()

    def classify_unified(self, email_data: Dict) -> Dict:
        """Universal classifier"""
        response = requests.post(
            f"{self.base_url}/api/v5/classify",
            json={"email_data": email_data}
        )
        return response.json()
```

---

## ✅ Success Criteria

1. ✅ Marketing emails correctly tagged as "newsletter"/"marketing"
2. ✅ Subscription renewals NOT tagged as marketing
3. ✅ Subscription information extracted (amount, currency, service)
4. ✅ All confidence scores > thresholds
5. ✅ Paperless-NGX pre-consume script uses unified API
6. ✅ MAJ Subscriptions uses unified API
7. ✅ Same classification results across all apps

---

## 📊 Migration Timeline

| Step | Task | Status | ETA |
|------|------|--------|-----|
| 1 | Upload Python modules | ⏳ PENDING | 10 min |
| 2 | Update server.js MCP tools | ⏳ PENDING | 15 min |
| 3 | Add HTTP endpoints | ⏳ PENDING | 20 min |
| 4 | Test marketing classifier | ⏳ PENDING | 10 min |
| 5 | Test subscription detector | ⏳ PENDING | 10 min |
| 6 | Update Paperless script | ⏳ PENDING | 15 min |
| 7 | Update MAJ Subscriptions | ⏳ PENDING | 15 min |
| 8 | End-to-end testing | ⏳ PENDING | 30 min |

**Total ETA:** ~2 hours

---

**Verze:** Unified MCP v5.0
**Implementoval:** Claude Code
**Datum:** 2025-01-03 19:30
**Cíl:** Single Source of Truth pro všechny klasifikace
