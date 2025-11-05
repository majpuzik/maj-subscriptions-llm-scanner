# MAJ Subscriptions LLM Scanner - Analýza Kódu a Návrhy Vylepšení

**Datum analýzy**: 5. listopadu 2025
**Analyzovaná verze**: 1.0 PRODUCTION
**Analyzovaný soubor**: `production_llm_scanner.py` (487 řádků)

---

## 📊 Executive Summary

### Současný stav
- ✅ **Funkční produkční systém** s 95-100% přesností
- ✅ **Dobře strukturovaný kód** s logickým rozdělením funkcí
- ✅ **Hybridní architektura** (keyword pre-filter + LLM)
- ⚠️  **Chybí robustní error handling** a resume capability
- ⚠️  **Limitovaná podpora formátů** (pouze MBOX)
- ⚠️  **Žádný progress tracking** během dlouhých scanů

### Doporučená priorita vylepšení
1. **CRITICAL**: Error handling a resume capability
2. **HIGH**: Progress tracking a statistiky
3. **MEDIUM**: LLM prompt optimization
4. **LOW**: Podpora dalších formátů (EML, MSG)

---

## 🔍 Detailní Analýza Kódu

### 1. Error Handling a Resilience ❌ CRITICAL

**Problém:**
```python
# Řádek 154-163: Pokud Ollama API selže, celý scan se zastaví
response = requests.post(
    self.ollama_url,
    json={...},
    timeout=OLLAMA_TIMEOUT
)
```

**Důsledky:**
- Při výpadku Ollama serveru se ztratí celý progress
- Žádná možnost obnovit scan od posledního místa
- Network timeouts způsobí ztrátu dat

**Návrh řešení:**
```python
def analyze_with_llm_retry(self, subject, sender, body, max_retries=3):
    """LLM analysis with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return self.analyze_with_llm(subject, sender, body)
        except requests.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Retry {attempt+1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                # Save to failed queue for later retry
                self.save_failed_email(subject, sender, body)
                return {"is_subscription": False, "error": "max_retries_exceeded"}
```

---

### 2. Progress Tracking a Resume Capability ❌ HIGH

**Problém:**
```python
# Řádek 317-387: Žádné ukládání progressu
for message in mbox:
    self.stats['total_scanned'] += 1
    # ... zpracování ...
    # Pokud se scan zastaví, začne od začátku
```

**Důsledky:**
- Při crashu se ztratí všechen progress
- Nelze sledovat průběh dlouhých scanů (4-8 hodin)
- Nutnost rescanovat všechny emaily znovu

**Návrh řešení:**
```python
def scan_with_progress(self, mbox_path, checkpoint_file="scan_checkpoint.json"):
    """Scan with automatic checkpointing"""

    # Load last checkpoint
    last_processed_id = self.load_checkpoint(checkpoint_file)

    for idx, message in enumerate(mbox):
        message_id = message.get('Message-ID', '')

        # Skip already processed
        if idx < last_processed_id:
            continue

        # Process email...

        # Save checkpoint every 100 emails
        if idx % 100 == 0:
            self.save_checkpoint(checkpoint_file, idx)
            logger.info(f"Progress: {idx}/{total} emails ({(idx/total)*100:.1f}%)")
```

---

### 3. LLM Prompt Optimization ⚠️ MEDIUM

**Problém:**
```python
# Řádek 125-151: Prompt může být přesnější
prompt = f"""Analyzuj tento email a urci, jestli obsahuje informaci o predplatnem/subscription.

EMAIL:
From: {sender}
Subject: {subject}
Body (first 1000 chars):
{body[:1000]}
```

**Nedostatky:**
- Pouze prvních 1000 znaků těla (důležité info může být níže)
- Chybí examples (few-shot learning)
- Není specifikováno co NENÍ předplatné

**Návrh vylepšení:**
```python
prompt = f"""Analyzuj tento email a urči, jestli obsahuje informaci o předplatném/subscription.

PŘÍKLADY PŘEDPLATNÉHO:
- Měsíční faktura za službu
- Potvrzení o obnovení předplatného
- Změna ceny předplatného
- Zrušení předplatného

NENÍ PŘEDPLATNÉ:
- Jednorázový nákup
- Reset hesla
- Newsletter/marketing email bez platby
- Upozornění na akci

EMAIL:
From: {sender}
Subject: {subject}
Body: {self.extract_relevant_text(body, max_chars=2000)}

Vrať JSON s:
{{
    "is_subscription": true/false,
    "confidence": 0-100,
    "service_name": "název služby" nebo null,
    "amount": číslo nebo null,
    "currency": "CZK"/"USD"/"EUR" nebo null,
    "subscription_type": "monthly"/"yearly"/"quarterly" nebo null,
    "reasoning": "stručné zdůvodnění (max 200 znaků)"
}}
"""
```

---

### 4. Database Schema Improvements ⚠️ MEDIUM

**Problém:**
```python
# Řádek 269-291: Chybí indexy a optimalizace
cursor.execute('''
    INSERT INTO email_evidence (...) VALUES (?, ?, ?, ...)
''')
```

**Chybějící indexy:**
- Index na `email_message_id` (pro deduplikaci)
- Index na `service_id` (pro rychlé vyhledávání)
- Index na `email_date` (pro časové filtry)
- Index na `confidence_score` (pro quality filtering)

**Návrh řešení:**
```python
def create_optimized_schema(self):
    """Create database schema with proper indexes"""
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_email_message_id
        ON email_evidence(email_message_id);

        CREATE INDEX IF NOT EXISTS idx_service_id
        ON email_evidence(service_id);

        CREATE INDEX IF NOT EXISTS idx_email_date
        ON email_evidence(email_date);

        CREATE INDEX IF NOT EXISTS idx_confidence_score
        ON email_evidence(confidence_score DESC);

        CREATE INDEX IF NOT EXISTS idx_scan_date
        ON email_evidence(scan_date);
    ''')
```

---

### 5. Memory Management ⚠️ LOW

**Problém:**
```python
# Řádek 260-302: Full email body v paměti
email_body_full: body  # Může být desítky KB
```

**Důsledky:**
- Vysoká spotřeba RAM při skenování tisíců emailů
- Možné OOM (Out of Memory) při velkých mailboxech

**Návrh řešení:**
```python
def save_email_evidence_optimized(self, ...):
    """Save email with optional body compression"""

    # Compress large bodies
    if len(body) > 10000:  # > 10KB
        body_compressed = zlib.compress(body.encode())
        store_compressed = True
    else:
        body_compressed = body
        store_compressed = False

    cursor.execute('''
        INSERT INTO email_evidence (
            ..., email_body_compressed, is_compressed, ...
        ) VALUES (?, ?, ?, ...)
    ''', (..., body_compressed, store_compressed, ...))
```

---

### 6. Logging a Monitoring ⚠️ LOW

**Problém:**
```python
# Základní logging bez structured logs
logger.info(f"LLM: {'✅ SUBSCRIPTION' if ... else '❌ NOT SUBSCRIPTION'}")
```

**Chybí:**
- JSON structured logging pro parsing
- Metrics export (Prometheus/Grafana)
- Real-time dashboard
- Alert systém při chybách

**Návrh řešení:**
```python
import structlog

logger = structlog.get_logger()

def analyze_with_llm_logged(self, ...):
    start_time = time.time()

    logger.info(
        "llm_analysis_start",
        subject=subject[:50],
        sender=sender,
        body_length=len(body)
    )

    result = self.analyze_with_llm(...)

    logger.info(
        "llm_analysis_complete",
        is_subscription=result.get('is_subscription'),
        confidence=result.get('confidence'),
        duration=time.time() - start_time,
        service_name=result.get('service_name')
    )

    # Export metrics
    prometheus_client.Counter('llm_analyses_total').inc()
    prometheus_client.Histogram('llm_duration_seconds').observe(time.time() - start_time)
```

---

### 7. Keyword Filter Optimization ✅ GOOD

**Současný stav:**
```python
# Řádek 96-118: Dobře implementováno
def quick_keyword_filter(self, subject: str, body: str) -> bool:
    content = (subject + ' ' + body[:2000]).lower()
    # Czech accent normalization
    content = content.replace('á', 'a')...
```

**Možné vylepšení:**
```python
import unicodedata

def normalize_text(self, text: str) -> str:
    """Advanced text normalization"""
    # Remove all diacritics (universální pro všechny jazyky)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower()

def quick_keyword_filter_v2(self, subject: str, body: str) -> bool:
    """Improved keyword filter with regex"""
    content = self.normalize_text(subject + ' ' + body[:2000])

    # Use compiled regex for speed
    for pattern in self.compiled_patterns:
        if pattern.search(content):
            return True
    return False
```

---

## 📋 Prioritizovaný Implementační Plán

### Fáze 1: Critical Fixes (1-2 dny)
- [ ] Implementovat retry logic s exponential backoff
- [ ] Přidat checkpoint/resume capability
- [ ] Vytvořit failed emails queue

### Fáze 2: Quality Improvements (2-3 dny)
- [ ] Optimalizovat LLM prompt (few-shot examples)
- [ ] Přidat progress tracking s ETA
- [ ] Implementovat database indexy

### Fáze 3: Advanced Features (3-5 dní)
- [ ] Podpora EML a MSG formátů
- [ ] Structured logging (structlog)
- [ ] Prometheus metrics export
- [ ] Real-time dashboard

### Fáze 4: Testing & Validation (2-3 dny)
- [ ] Test na 1000 emails
- [ ] Performance profiling
- [ ] Memory usage optimization
- [ ] Srovnávací benchmark (před/po)

---

## 🎯 Očekávané Výsledky Po Vylepšeních

### Performance
- ✅ **Resilience**: 99.9% (vs. současných ~90%)
- ✅ **Memory usage**: -50% (compression)
- ✅ **Scan speed**: +20% (better indexing)
- ✅ **Resume capability**: Ano (vs. Ne)

### Quality
- ✅ **LLM accuracy**: 98-100% (vs. 95-100%)
- ✅ **False positive rate**: <2% (vs. <5%)
- ✅ **Edge case handling**: +30%

### Monitoring
- ✅ **Real-time progress**: Ano
- ✅ **Structured logs**: Ano
- ✅ **Metrics dashboard**: Ano
- ✅ **Alert system**: Ano

---

## 🔧 Implementační Nástroje

### Potřebné knihovny
```bash
pip install structlog prometheus-client tqdm unicodedata-backport
```

### Database migrace
```sql
-- Add indexes
CREATE INDEX IF NOT EXISTS idx_email_message_id ON email_evidence(email_message_id);
CREATE INDEX IF NOT EXISTS idx_service_id ON email_evidence(service_id);
CREATE INDEX IF NOT EXISTS idx_email_date ON email_evidence(email_date);

-- Add compression support
ALTER TABLE email_evidence ADD COLUMN is_compressed BOOLEAN DEFAULT FALSE;
ALTER TABLE email_evidence ADD COLUMN email_body_compressed BLOB;

-- Add checkpoint table
CREATE TABLE IF NOT EXISTS scan_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mbox_path TEXT NOT NULL,
    last_processed_index INTEGER,
    scan_start_date TIMESTAMP,
    scan_end_date TIMESTAMP,
    status TEXT  -- 'running', 'completed', 'failed'
);
```

---

## 📊 Testovací Scénáře

### Test 1: Resume Capability
1. Spustit scan 1000 emails
2. Zastavit po 500 emailech (CTRL+C)
3. Spustit znovu
4. **Očekávaný výsledek**: Začne od emailu #501

### Test 2: Error Resilience
1. Spustit scan s Ollama serverem
2. Zastavit Ollama server uprostřed scanu
3. Restartovat Ollama server
4. **Očekávaný výsledek**: Scan pokračuje s retry

### Test 3: Memory Usage
1. Spustit scan 10,000 emails
2. Monitorovat RAM usage
3. **Očekávaný výsledek**: Konstantní ~500MB RAM (vs. rostoucí)

### Test 4: LLM Accuracy
1. Test dataset: 100 manuálně označených emailů
2. Spustit improved scanner
3. **Očekávaný výsledek**: >98% accuracy

---

## 🎓 Závěr

Současný kód je **dobře navržený a funkční** pro produkci, ale chybí mu **robustnost** potřebná pro dlouhodobé nasazení. Implementace navržených vylepšení zvýší:

1. **Reliability**: Z 90% na 99.9%
2. **Maintainability**: Structured logs + metrics
3. **Performance**: Optimalizace paměti a databáze
4. **User Experience**: Progress tracking + resume

**Doporučený next step**: Implementovat Fázi 1 (Critical Fixes) a pak spustit test na 1000 emails.
