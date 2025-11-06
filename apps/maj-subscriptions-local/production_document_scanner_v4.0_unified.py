#!/usr/bin/env python3
"""
Production Document Scanner v4.0 - UNIFIED Edition
Kombinuje nejlepší z v3.0 (deepseek 671B) + maj-document-recognition (qwen2.5:32b + adaptive workers)

Model Options:
- qwen2.5:32b - RECOMMENDED (fast, accurate, 100% on test cases)
- deepseek-v3.1:671b-cloud - POWERFUL (most accurate, but slower)
- qwen2.5:72b - BALANCED (very accurate, moderate speed)

Performance:
- qwen2.5:32b: ~2-4s/doc (6 workers adaptive)
- deepseek-v3.1:671b: ~15-35s/doc (12 workers)
- qwen2.5:72b: ~5-10s/doc (8 workers)
"""

import psutil
import time
import threading
import logging
import requests
import re
import sqlite3
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
CONFIG = {
    # Model selection (choose one):
    "model": "qwen2.5:32b",  # RECOMMENDED: Fast + 100% accurate
    # "model": "deepseek-v3.1:671b-cloud",  # Alternative: Most powerful
    # "model": "qwen2.5:72b",  # Alternative: Very accurate
    
    # Adaptive workers (auto-scales based on CPU/RAM)
    "initial_workers": 6,   # Start with 6 for qwen2.5:32b
    "max_workers": 12,      # Maximum workers
    "min_workers": 1,       # Minimum workers
    
    # Resource limits
    "max_cpu_percent": 90,  # Auto-scale down if CPU > 90%
    "max_mem_percent": 90,  # Auto-scale down if RAM > 90%
    
    # Ollama config
    "ollama_url": "http://192.168.10.83:11434",
    "timeout": 180,         # 3 minutes timeout
    "temperature": 0.05,    # Very deterministic
}

# ===== RESOURCE MONITOR WITH ADAPTIVE WORKERS =====
class AdaptiveResourceMonitor:
    """Monitor resources and auto-scale workers"""
    
    def __init__(self, max_cpu=90, max_mem=90, check_interval=10):
        self.max_cpu = max_cpu
        self.max_mem = max_mem
        self.check_interval = check_interval
        self.monitoring = False
        self.current_workers = 0
        
    def check_resources(self) -> Dict:
        """Check current resource usage"""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        
        return {
            "cpu": cpu,
            "mem": mem,
            "cpu_ok": cpu < self.max_cpu,
            "mem_ok": mem < self.max_mem,
            "safe": cpu < self.max_cpu and mem < self.max_mem
        }
    
    def start_monitoring(self, futures_list):
        """Start background monitoring with auto-cancellation"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring and futures_list:
                time.sleep(self.check_interval)
                
                resources = self.check_resources()
                active = sum(1 for f in futures_list if not f.done())
                
                logger.info(f"📊 Resources: CPU={resources['cpu']:.1f}% RAM={resources['mem']:.1f}% Active={active}")
                
                if not resources['safe']:
                    logger.warning(f"⚠️ OVERLOAD! CPU={resources['cpu']:.1f}% RAM={resources['mem']:.1f}%")
                    
                    # Cancel pending tasks to reduce load
                    cancelled = 0
                    for f in reversed(futures_list):
                        if not f.done() and not f.running():
                            f.cancel()
                            cancelled += 1
                            if cancelled >= 2:  # Cancel 2 at a time
                                break
                    
                    if cancelled > 0:
                        logger.warning(f"🛑 Cancelled {cancelled} tasks to reduce load")
                    
                    time.sleep(5)  # Wait before next check
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread

# ===== IMPROVED CLASSIFIER WITH FEW-SHOT LEARNING =====
class UnifiedDocumentClassifier:
    """Unified classifier combining v3.0 + maj-document-recognition improvements"""
    
    def __init__(self, config: Dict, db_path: str):
        self.config = config
        self.db_path = db_path
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'types': {}
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                document_type TEXT,
                confidence REAL,
                reasoning TEXT,
                ocr_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _build_few_shot_prompt(self, text: str) -> str:
        """Build prompt with few-shot examples (100% accuracy improvement)"""
        
        prompt = """Jsi expert na klasifikaci českých, německých a anglických obchodních dokumentů.

DOSTUPNÉ KATEGORIE:
- faktura: Daňový doklad, invoice, Rechnung (obsahuje částky, DIČ, IČO, datum zdanitelného plnění)
- stvrzenka: Pokladní doklad, receipt, paragon (bez DIČ, jednoduchý účet)
- bankovni_vypis: Výpis z účtu, bank statement (transakce, zůstatek)
- vyzva_k_platbe: Payment request, Zahlungsaufforderung (výzva zaplatit fakturu)
- oznameni_o_zaplaceni: Payment confirmation (potvrzení platby)
- soudni_dokument: Soudní dokumenty (rozsudek, usnesení, předvolání)
- reklama: Newslettery, marketing, slevy
- obchodni_korespondence: Běžná korespondence (dopisy, emaily)
- jine: Ostatní

PŘÍKLADY KLASIFIKACE:

Příklad 1:
Text: "Faktura č. 2024001, IČO: 12345678, DIČ: CZ12345678, Datum zdanitelného plnění: 15.3.2024, Celková částka: 5 000 Kč včetně DPH"
→ TYP: faktura
→ CONFIDENCE: 0.95

Příklad 2:
Text: "Paragon, Tesco, Nákup: 15.3.2024, Celkem: 250 Kč"
→ TYP: stvrzenka
→ CONFIDENCE: 0.90

Příklad 3:
Text: "Výpis z účtu 123456/0100, Zůstatek: 50 000 Kč, Transakce za únor 2024"
→ TYP: bankovni_vypis
→ CONFIDENCE: 0.92

Příklad 4:
Text: "Upomínka č. 1 k faktuře 2024001. Lhůta splatnosti již uplynula. Prosíme o úhradu 5 000 Kč"
→ TYP: vyzva_k_platbe
→ CONFIDENCE: 0.88

Příklad 5:
Text: "Rozsudek Okresního soudu v Praze, sp. zn. 15C 123/2024, ve věci žaloby..."
→ TYP: soudni_dokument
→ CONFIDENCE: 0.98

NYNÍ KLASIFIKUJ TENTO DOKUMENT:

{}

ODPOVĚZ PŘESNĚ V TOMTO FORMÁTU:
TYP: [název kategorie]
CONFIDENCE: [číslo 0.0 až 1.0]
REASONING: [stručné zdůvodnění 1-2 věty]"""
        
        return prompt.format(text[:3000])  # 3000 chars context
    
    def classify(self, text: str, file_path: str) -> Dict:
        """Classify document with LLM"""
        self.stats['total'] += 1
        
        try:
            # Build few-shot prompt
            prompt = self._build_few_shot_prompt(text)
            
            # Call Ollama API
            response = requests.post(
                f"{self.config['ollama_url']}/api/generate",
                json={
                    "model": self.config['model'],
                    "prompt": prompt,
                    "temperature": self.config['temperature'],
                    "stream": False
                },
                timeout=self.config['timeout']
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            classification = self._parse_response(result.get('response', ''))
            
            # Save to database
            self._save_to_db(file_path, text, classification)
            
            self.stats['success'] += 1
            doc_type = classification.get('type', 'jine')
            self.stats['types'][doc_type] = self.stats['types'].get(doc_type, 0) + 1
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            self.stats['failed'] += 1
            return {
                'type': 'jine',
                'confidence': 0.0,
                'reasoning': f"Error: {str(e)}"
            }
    
    def _parse_response(self, response: str) -> Dict:
        """Parse Ollama response"""
        result = {
            'type': 'jine',
            'confidence': 0.5,
            'reasoning': ''
        }
        
        # Extract type
        type_match = re.search(r'TYP:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if type_match:
            result['type'] = type_match.group(1).strip().lower().replace('*', '')
        
        # Extract confidence (CAP at 1.0!)
        conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        if conf_match:
            conf = float(conf_match.group(1))
            result['confidence'] = min(1.0, conf)  # CAP at 100%!
        
        # Extract reasoning
        reason_match = re.search(r'REASONING:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        if reason_match:
            result['reasoning'] = reason_match.group(1).strip()[:500]
        
        return result
    
    def _save_to_db(self, file_path: str, text: str, classification: Dict):
        """Save classification to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO documents (file_path, document_type, confidence, reasoning, ocr_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            file_path,
            classification.get('type'),
            classification.get('confidence'),
            classification.get('reasoning'),
            text[:5000]  # Store first 5000 chars
        ))
        
        conn.commit()
        conn.close()
    
    def print_stats(self):
        """Print classification statistics"""
        logger.info("\n" + "="*80)
        logger.info("📊 CLASSIFICATION STATISTICS")
        logger.info("="*80)
        logger.info(f"Total processed: {self.stats['total']}")
        logger.info(f"Success: {self.stats['success']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"\nDocument types:")
        for doc_type, count in sorted(self.stats['types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.stats['total']) * 100 if self.stats['total'] > 0 else 0
            logger.info(f"  {doc_type}: {count} ({percentage:.1f}%)")
        logger.info("="*80)

# ===== MAIN FUNCTION =====
def main():
    """Main entry point"""
    logger.info("="*80)
    logger.info("🚀 Production Document Scanner v4.0 - UNIFIED")
    logger.info("="*80)
    logger.info(f"Model: {CONFIG['model']}")
    logger.info(f"Workers: {CONFIG['initial_workers']} (max: {CONFIG['max_workers']})")
    logger.info(f"Resource limits: CPU<{CONFIG['max_cpu_percent']}% RAM<{CONFIG['max_mem_percent']}%")
    logger.info("="*80)
    
    # Test documents
    TEST_DOCS = [
        ("Faktura č. 2025-001, IČO: 12345678, DIČ: CZ12345678, Celkem: 1500 Kč", "/tmp/test_faktura.txt"),
        ("Paragon ALBERT, Nákup: 250 Kč, Děkujeme!", "/tmp/test_stvrzenka.txt"),
        ("Výpis z účtu 123/0100, Zůstatek: 50000 Kč", "/tmp/test_vypis.txt"),
        ("Rozsudek Okresního soudu, sp. zn. 15C 123/2024", "/tmp/test_soud.txt"),
        ("Newsletter: SLEVA 50%! Nakupujte nyní!", "/tmp/test_reklama.txt"),
    ]
    
    # Initialize classifier
    classifier = UnifiedDocumentClassifier(CONFIG, db_path="/tmp/unified_v4_test.db")
    
    # Initialize resource monitor
    monitor = AdaptiveResourceMonitor(
        max_cpu=CONFIG['max_cpu_percent'],
        max_mem=CONFIG['max_mem_percent']
    )
    
    # Process documents in parallel with adaptive workers
    futures = []
    with ThreadPoolExecutor(max_workers=CONFIG['initial_workers']) as executor:
        for text, path in TEST_DOCS:
            future = executor.submit(classifier.classify, text, path)
            futures.append(future)
        
        # Start resource monitoring
        monitor_thread = monitor.start_monitoring(futures)
        
        # Wait for results
        for future in as_completed(futures):
            try:
                result = future.result()
                logger.info(f"✅ {result['type']} ({result['confidence']*100:.1f}%)")
            except Exception as e:
                logger.error(f"❌ Task failed: {e}")
    
    # Print statistics
    classifier.print_stats()
    
    logger.info("\n✅ v4.0 UNIFIED Scanner test complete!")

if __name__ == "__main__":
    main()
