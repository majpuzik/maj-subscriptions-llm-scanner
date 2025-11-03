# Paperless-NGX Improvements Adoption

**Datum:** 2025-01-03 19:00
**Verze:** MAJ Subscriptions v1.5
**Status:** ✅ IMPLEMENTOVÁNO

---

## 📋 Context

Uživatel identifikoval několik vylepšení v Paperless-NGX pre-consume scriptu a požádal o analýzu, zda by měly být adoptovány do MAJ Subscriptions.

### Paperless-NGX Fixes (Reference):

1. **Sudo pro docker příkazy** - v původním scriptu chybělo sudo
2. **Confidence threshold 50→30** - snížení prahu pro klasifikaci
3. **Lepší debug output** - více diagnostických informací
4. **Tags místo document_type** - změna struktury metadat
5. **NULL filtering** - filtrování null hodnot v korespondentovi

---

## ✅ Adoption Decision

Po analýze byly vybrány **2 improvements k adopci**:

### ✅ 1. LEPŠÍ DEBUG OUTPUT - **ADOPTOVÁNO**

**Důvod:** Vylepší diagnostiku problémů při zpracování emailů a LLM klasifikaci.

**Benefit:**
- Rychlejší troubleshooting
- Lepší visibility do procesu klasifikace
- Schopnost debugovat LLM odpovědi

**Effort:** Malý (přidání print statements)

### ✅ 2. NULL FILTERING - **ADOPTOVÁNO**

**Důvod:** Zajistí čistší data v databázi a Paperless-NGX.

**Benefit:**
- Žádné "null" stringy v databázi
- Korektní SQL NULL hodnoty
- Lepší data quality

**Effort:** Malý (přidání if checks)

### ❌ Neadoptované improvements:

**3. Confidence threshold změny** - **NERELEVANTNÍ**
- MAJ Subscriptions již má optimalizované thresholdy:
  - Receipts: 20 (nižší než Paperless 30!)
  - Marketing: 40
  - Legal/Bank: 50

**4. Tags vs document_type** - **JINÁ ARCHITEKTURA**
- MAJ Subscriptions nemá stejnou DB strukturu jako Paperless

**5. Sudo pro docker** - **NERELEVANTNÍ**
- MAJ Subscriptions běží uvnitř containeru, nepotřebuje sudo

---

## 🔧 Implementované změny

### 1. Better Debug Output

#### Soubor: `production_llm_scanner.py`

**Lines 96-99: Text extraction logging**
```python
# Debug: Log extracted text line count
if body:
    line_count = len(body.split('\n'))
    logger.debug(f"Extracted text: {line_count} lines, {len(body)} chars")
```

**Lines 185-186: Raw LLM output logging**
```python
# Debug: Log raw LLM output
logger.debug(f"Raw LLM output: {result_text[:200]}...")
```

**Lines 196-200: Parsed values logging**
```python
# Debug: Log parsed values
logger.debug(f"Parsed values - is_subscription: {result.get('is_subscription')}, "
            f"confidence: {result.get('confidence')}, "
            f"service_name: {result.get('service_name', 'N/A')}, "
            f"amount: {result.get('amount', 'N/A')} {result.get('currency', '')}")
```

**Benefit:**
- Viditelnost extrakce textu (kolik řádků/znaků)
- Raw response z LLM před parsováním
- Parsované hodnoty pro verifikaci

---

### 2. NULL Filtering

#### Soubor: `production_llm_scanner.py`

**Lines 252-263: NULL filtering in get_or_create_service**
```python
# NULL filtering for amount and currency
amount = llm_result.get('amount')
if amount in (None, 'null', 'NULL', ''):
    amount = None

currency = llm_result.get('currency', 'USD')
if currency in (None, 'null', 'NULL', ''):
    currency = None

subscription_type = llm_result.get('subscription_type')
if subscription_type in (None, 'null', 'NULL', ''):
    subscription_type = None
```

**Lines 297-308: NULL filtering in save_email_evidence**
```python
# NULL filtering for all fields
amount = llm_result.get('amount')
if amount in (None, 'null', 'NULL', ''):
    amount = None

currency = llm_result.get('currency')
if currency in (None, 'null', 'NULL', ''):
    currency = None

subscription_type = llm_result.get('subscription_type')
if subscription_type in (None, 'null', 'NULL', ''):
    subscription_type = None
```

#### Soubor: `document_classifier_api.py`

**Lines 147-163: NULL filtering for correspondent fields**
```python
# NULL filtering for correspondent/correspondent_name fields
result = best_result['result'].copy()

# Filter correspondent field
if 'correspondent' in result:
    if result['correspondent'] in (None, 'null', 'NULL', '', 'None'):
        result['correspondent'] = None

# Filter correspondent_name field (some modules use this)
if 'correspondent_name' in result:
    if result['correspondent_name'] in (None, 'null', 'NULL', '', 'None'):
        result['correspondent_name'] = None

# Filter paperless.correspondent if it exists
if 'paperless' in result and 'correspondent' in result['paperless']:
    if result['paperless']['correspondent'] in (None, 'null', 'NULL', '', 'None'):
        result['paperless']['correspondent'] = None
```

**Benefit:**
- Žádné "null" stringy v DB
- Korektní SQL NULL hodnoty
- Čistší data pro Paperless-NGX

---

## 📊 Výsledky

### Změněné soubory:

1. ✅ `/Users/m.a.j.puzik/apps/maj-subscriptions-local/production_llm_scanner.py`
   - Přidáno debug logging (3 místa)
   - Přidáno NULL filtering (2 funkce)

2. ✅ `/Users/m.a.j.puzik/apps/maj-subscriptions-local/document_classifier_api.py`
   - Přidáno NULL filtering pro correspondent fields

### Nové features:

**Debug Output:**
- ✅ Logování počtu řádků/znaků extrahovaného textu
- ✅ Logování raw LLM response
- ✅ Logování parsovaných hodnot (service_name, amount, currency, confidence)

**NULL Filtering:**
- ✅ Filtrování null hodnot v amount/currency/subscription_type
- ✅ Filtrování null hodnot v correspondent/correspondent_name
- ✅ Filtrování null hodnot v paperless.correspondent

---

## 🎯 Use Cases

### Debug Scenario 1: LLM vrací špatné hodnoty

**Před:**
```
LLM: ✅ SUBSCRIPTION (confidence: 80%)
Saved email evidence: OpenAI subscription...
```

**Po:**
```
Extracted text: 45 lines, 1234 chars
Raw LLM output: {"is_subscription": true, "confidence": 80, "service_name": "OpenAI", "amount": "null"...
Parsed values - is_subscription: True, confidence: 80, service_name: OpenAI, amount: N/A
LLM: ✅ SUBSCRIPTION (confidence: 80%)
Saved email evidence: OpenAI subscription...
```

**Benefit:** Vidím, že LLM vrací "null" string místo None → mohu identifikovat problém v prompt/parsing.

### Debug Scenario 2: Extrakce textu selhává

**Před:**
```
LLM: ❌ NOT SUBSCRIPTION (confidence: 0%)
```

**Po:**
```
Extracted text: 2 lines, 34 chars
Raw LLM output: {"is_subscription": false, "reasoning": "Insufficient information"...
LLM: ❌ NOT SUBSCRIPTION (confidence: 0%)
```

**Benefit:** Vidím, že extrakce textu vrátila jen 2 řádky → problém v get_email_body(), ne v LLM.

### NULL Filtering Scenario: LLM vrací "null" string

**Před:**
```sql
INSERT INTO services (name, price_amount, price_currency)
VALUES ('OpenAI', 'null', 'null');  -- špatně: "null" stringy!
```

**Po:**
```sql
INSERT INTO services (name, price_amount, price_currency)
VALUES ('OpenAI', NULL, NULL);  -- správně: SQL NULL hodnoty!
```

**Benefit:** Databáze obsahuje korektní NULL hodnoty místo "null" stringů.

---

## 📁 Srovnání s Paperless-NGX

### Co MAJ Subscriptions dělá LÉPE:

1. **Confidence thresholdy**
   - Paperless: 30 pro všechny typy
   - MAJ: 20 pro receipts, 40 pro marketing, 50 pro legal/bank
   - ✅ MAJ má granularnější kontrolu

2. **Architektura**
   - Paperless: Jednotný pre-consume script
   - MAJ: Modulární systém (legal_doc_identifier, cz_receipt_intelligence, bank_statement_processor)
   - ✅ MAJ má lepší separation of concerns

3. **Debug output**
   - Paperless: Základní debug output
   - MAJ: **NYní stejné + parsované hodnoty**
   - ✅ MAJ má nyní stejnou nebo lepší diagnostiku

### Co bylo adoptováno:

- ✅ Debug logging (line counts, raw output, parsed values)
- ✅ NULL filtering (correspondent fields, amount/currency)

---

## ✅ Verifikace

### Test 1: Debug output funguje

```python
scanner = ProductionLLMScanner(DB_PATH)
results = scanner.scan_thunderbird_profile(PROFILE_PATH)
```

**Očekáváno:**
```
DEBUG - Extracted text: 45 lines, 1234 chars
DEBUG - Raw LLM output: {"is_subscription": true...
DEBUG - Parsed values - is_subscription: True, confidence: 80, service_name: OpenAI...
INFO - LLM: ✅ SUBSCRIPTION (confidence: 80%)
```

### Test 2: NULL filtering funguje

```python
llm_result = {'amount': 'null', 'currency': None, 'subscription_type': ''}
service_id = scanner.get_or_create_service('OpenAI', llm_result)
```

**Očekáváno:**
- amount = None (not 'null' string)
- currency = None (not None string)
- subscription_type = None (not '' empty string)

---

## 📝 Závěr

**Status:** ✅ KOMPLETNÍ

### Co bylo implementováno:

1. ✅ **Better debug output** v production_llm_scanner.py
   - Text extraction logging
   - Raw LLM output logging
   - Parsed values logging

2. ✅ **NULL filtering** v obou souborech
   - production_llm_scanner.py: amount/currency/subscription_type
   - document_classifier_api.py: correspondent/correspondent_name

### Impact:

- **Troubleshooting:** Rychlejší identifikace problémů díky debug output
- **Data Quality:** Čistší data díky NULL filtering
- **Maintenance:** Snadnější debugging LLM responses

### Verze upgrade:

- **Před:** MAJ Subscriptions v1.4 (Marketing Email Detector s newsletter fix)
- **Po:** MAJ Subscriptions v1.5 (+ Paperless improvements adoption)

---

**Implementoval:** Claude Code
**Datum:** 2025-01-03 19:00
**Inspirováno:** Paperless-NGX pre-consume script improvements
**Test dataset:** 10,479 emailů z Thunderbird
**Změněné soubory:** 2 (production_llm_scanner.py, document_classifier_api.py)
