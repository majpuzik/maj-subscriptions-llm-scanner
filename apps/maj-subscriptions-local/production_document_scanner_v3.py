#!/usr/bin/env python3
"""
Production Document Classification Scanner v3.0 - ENTERPRISE EDITION
---------------------------------------------------------------------
UPGRADE from v2.x:
- ✅ Powerful model: deepseek-v3.1:671b-cloud (671 BILLION parameters!)
- ✅ Parallel processing: 12 workers (configurable)
- ✅ CPU monitoring: Keep < 70% per core
- ✅ Memory monitoring: Keep < 70% RAM
- ✅ Auto-scaling: Dynamic worker adjustment
- ✅ Resource-aware batch processing
- ✅ Probabilistic scoring (0-200 points)

Performance Target: >95% classification accuracy
Model: deepseek-v3.1:671b-cloud (vs llama3.2:3b - 224x more powerful!)
"""

import os
import json
import sqlite3
import requests
import logging
import time
import threading
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/document_scanner_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Model configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-v3.1:671b-cloud"  # 671 BILLION parameters!
OLLAMA_TIMEOUT = 180  # 3 minutes per document (complex analysis)
MAX_RETRIES = 3

# Parallel processing
INITIAL_WORKERS = 12  # Start with 12 workers
MIN_WORKERS = 2
MAX_WORKERS = 16

# Resource limits
CPU_LIMIT_PERCENT = 70  # Maximum CPU per core
MEMORY_LIMIT_PERCENT = 70  # Maximum RAM usage
RESOURCE_CHECK_INTERVAL = 5  # Check every 5 seconds

# Database
DB_PATH = os.getenv("DB_PATH", "/data/subscriptions.db")

# Classification thresholds (probabilistic scoring)
THRESHOLD_VERY_HIGH = 150  # 75%+ score → Auto-accept
THRESHOLD_HIGH = 120  # 60%+ score → Accept with logging
THRESHOLD_MEDIUM = 80  # 40%+ score → Needs review
# < 80 → Auto-reject as "jine"


class ResourceMonitor:
    """Real-time CPU and Memory monitoring with auto-scaling"""

    def __init__(self):
        self.cpu_overload = False
        self.memory_overload = False
        self.running = False
        self.monitor_thread = None
        self.max_cpu = 0.0
        self.avg_cpu = 0.0
        self.memory_percent = 0.0

    def start(self):
        """Start monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("📊 Resource monitor started")

    def stop(self):
        """Stop monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("📊 Resource monitor stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Check CPU per core
                cpu_per_core = psutil.cpu_percent(percpu=True, interval=1)
                self.max_cpu = max(cpu_per_core) if cpu_per_core else 0
                self.avg_cpu = sum(cpu_per_core) / len(cpu_per_core) if cpu_per_core else 0

                # Check memory
                memory = psutil.virtual_memory()
                self.memory_percent = memory.percent

                # Update overload flags
                self.cpu_overload = self.max_cpu > CPU_LIMIT_PERCENT
                self.memory_overload = self.memory_percent > MEMORY_LIMIT_PERCENT

                # Log warnings
                if self.cpu_overload:
                    logger.warning(f"⚠️  CPU overload: {self.max_cpu:.1f}% (limit: {CPU_LIMIT_PERCENT}%)")
                if self.memory_overload:
                    logger.warning(f"⚠️  Memory overload: {self.memory_percent:.1f}% (limit: {MEMORY_LIMIT_PERCENT}%)")

                time.sleep(RESOURCE_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
                time.sleep(RESOURCE_CHECK_INTERVAL)

    def is_overloaded(self) -> bool:
        """Check if system is overloaded"""
        return self.cpu_overload or self.memory_overload

    def get_status(self) -> Dict[str, float]:
        """Get current resource status"""
        return {
            "max_cpu": self.max_cpu,
            "avg_cpu": self.avg_cpu,
            "memory_percent": self.memory_percent,
            "cpu_overload": self.cpu_overload,
            "memory_overload": self.memory_overload
        }


class DocumentClassifier:
    """
    Enterprise-grade document classifier with:
    - Parallel processing (12 workers)
    - Resource monitoring
    - Auto-scaling
    - Probabilistic scoring
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Resource management
        self.resource_monitor = ResourceMonitor()
        self.current_workers = INITIAL_WORKERS
        self.max_workers = MAX_WORKERS

        # Statistics
        self.stats = {
            "total_processed": 0,
            "classified": 0,
            "rejected_as_jine": 0,
            "errors": 0,
            "retries": 0,
            "worker_adjustments": 0
        }

        logger.info(f"🚀 Document Classifier v3.0 initialized")
        logger.info(f"📦 Model: {MODEL_NAME} (671B parameters)")
        logger.info(f"👥 Workers: {self.current_workers} (max: {self.max_workers})")

    def analyze_with_llm(self, text_content: str, filename: str = "") -> Dict[str, Any]:
        """
        Analyze document with DeepSeek v3.1 (671B parameters)

        Returns probabilistic classification with confidence score
        """
        prompt = f"""Analyzuj tento dokument a urči jeho typ s probabilistickým scoring systémem (0-200 bodů).

SCORING SYSTÉM (celkem 200 bodů):

1. DOCUMENT TYPE INDICATORS (0-60 bodů):
   - Faktura/Invoice: 60 bodů
   - Bankovní výpis: 55 bodů
   - Účtenka/Receipt: 50 bodů
   - Soudní dokument: 55 bodů
   - Policejní protokol: 55 bodů
   - Marketing email: -30 bodů (penalty!)

2. CONTENT STRUCTURE (0-50 bodů):
   - Číslo dokladu/IČO/DIČ: +15 bodů
   - Datum vystavení: +10 bodů
   - Částka s měnou: +15 bodů
   - Podpis/razítko: +10 bodů

3. LANGUAGE & FORMALITY (0-40 bodů):
   - Formální jazyk: +20 bodů
   - Právní termíny (§, zákon): +20 bodů
   - Neformální/marketing: -20 bodů

4. OCR QUALITY (0-30 bodů):
   - Vysoká čitelnost (>90%): +30 bodů
   - Střední čitelnost (60-90%): +15 bodů
   - Nízká čitelnost (<60%): +5 bodů

5. METADATA (0-20 bodů):
   - Známý odesílatel: +10 bodů
   - Datumové razítko: +5 bodů
   - Příloh není: +5 bodů

KLASIFIKAČNÍ PRAHY:
- 150-200 bodů (75-100%): VERY_HIGH → Auto-accept
- 120-149 bodů (60-74%): HIGH → Accept with logging
- 80-119 bodů (40-59%): MEDIUM → Needs review
- 0-79 bodů (0-39%): LOW → Reject as "jine"

DOKUMENTY K ANALÝZE:
Filename: {filename}
Content (first 3000 chars):
{text_content[:3000]}

Vrať POUZE validní JSON (bez markdown bloků):
{{
    "document_type": "<faktura/uctenka/soudni_dokument/bankovni_vypis/jine>",
    "score": <0-200>,
    "confidence_percent": <0-100>,
    "confidence_level": "<VERY_HIGH/HIGH/MEDIUM/LOW>",
    "breakdown": {{
        "type_indicators": <0-60>,
        "content_structure": <0-50>,
        "language_formality": <0-40>,
        "ocr_quality": <0-30>,
        "metadata": <0-20>
    }},
    "reasoning": "<1-2 věty proč tento score>",
    "tags": ["tag1", "tag2"],
    "correspondent": "<název firmy/instituce nebo null>",
    "detected_amount": <částka nebo null>,
    "detected_currency": "<CZK/EUR/USD nebo null>"
}}
"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent results
                        "num_predict": 1000
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )
            response.raise_for_status()

            result = response.json()
            llm_text = result.get("response", "")

            # Parse JSON response
            llm_text = llm_text.strip()
            if llm_text.startswith("```json"):
                llm_text = llm_text[7:]
            if llm_text.endswith("```"):
                llm_text = llm_text[:-3]
            llm_text = llm_text.strip()

            parsed = json.loads(llm_text)

            # CRITICAL FIX: Ensure confidence_percent is capped at 100%!
            score = parsed.get("score", 0)
            confidence_percent = min(100, (score / 200) * 100)  # CAP AT 100%!
            parsed["confidence_percent"] = round(confidence_percent, 1)

            # Auto-determine confidence level based on score
            if score >= 150:
                parsed["confidence_level"] = "VERY_HIGH"
            elif score >= 120:
                parsed["confidence_level"] = "HIGH"
            elif score >= 80:
                parsed["confidence_level"] = "MEDIUM"
            else:
                parsed["confidence_level"] = "LOW"

            return parsed

        except requests.Timeout:
            raise  # Re-raise for retry logic
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            # Return low-confidence "jine" classification
            return {
                "document_type": "jine",
                "score": 0,
                "confidence_percent": 0,
                "confidence_level": "LOW",
                "breakdown": {},
                "reasoning": f"Error: {str(e)}",
                "tags": ["error", "needs_review"],
                "correspondent": None,
                "detected_amount": None,
                "detected_currency": None
            }

    def analyze_with_retry(self, text_content: str, filename: str = "") -> Dict[str, Any]:
        """Analyze with exponential backoff retry"""
        for attempt in range(MAX_RETRIES):
            try:
                return self.analyze_with_llm(text_content, filename)
            except requests.Timeout:
                self.stats['retries'] += 1
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"⏳ Timeout, retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed after {MAX_RETRIES} retries")
                    return {
                        "document_type": "jine",
                        "score": 0,
                        "confidence_percent": 0,
                        "confidence_level": "LOW",
                        "breakdown": {},
                        "reasoning": "Timeout after retries",
                        "tags": ["timeout", "needs_review"],
                        "correspondent": None,
                        "detected_amount": None,
                        "detected_currency": None
                    }

    def process_document(self, doc_data: Dict) -> Dict[str, Any]:
        """Process single document"""
        try:
            file_path = doc_data.get("file_path", "")
            text_content = doc_data.get("text_content", "")
            filename = Path(file_path).name if file_path else "unknown"

            # Analyze with LLM
            result = self.analyze_with_retry(text_content, filename)

            # Add metadata
            result["file_path"] = file_path
            result["filename"] = filename
            result["processed_at"] = datetime.now().isoformat()

            # Update stats
            self.stats["total_processed"] += 1

            if result["score"] >= THRESHOLD_MEDIUM:
                self.stats["classified"] += 1
            else:
                self.stats["rejected_as_jine"] += 1

            return result

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            self.stats["errors"] += 1
            return {
                "file_path": doc_data.get("file_path", ""),
                "document_type": "jine",
                "score": 0,
                "confidence_percent": 0,
                "confidence_level": "LOW",
                "error": str(e)
            }

    def adjust_workers(self):
        """Auto-scale workers based on resource usage"""
        if self.resource_monitor.is_overloaded():
            # Reduce workers if overloaded
            new_workers = max(MIN_WORKERS, self.current_workers - 1)
            if new_workers != self.current_workers:
                logger.warning(f"🔻 Reducing workers: {self.current_workers} → {new_workers}")
                self.current_workers = new_workers
                self.stats["worker_adjustments"] += 1
        else:
            # Increase workers if under load
            if self.current_workers < self.max_workers:
                resources = self.resource_monitor.get_status()
                if resources["max_cpu"] < CPU_LIMIT_PERCENT * 0.5:  # Less than 50% of limit
                    new_workers = min(self.max_workers, self.current_workers + 1)
                    if new_workers != self.current_workers:
                        logger.info(f"🔺 Increasing workers: {self.current_workers} → {new_workers}")
                        self.current_workers = new_workers
                        self.stats["worker_adjustments"] += 1

    def scan_documents(self, documents: List[Dict], batch_size: int = 50) -> List[Dict]:
        """
        Scan documents in parallel batches with resource monitoring

        Args:
            documents: List of dicts with 'file_path' and 'text_content'
            batch_size: Process in batches to enable dynamic scaling

        Returns:
            List of classification results
        """
        results = []

        # Start resource monitor
        self.resource_monitor.start()

        try:
            # Process in batches
            total_batches = (len(documents) + batch_size - 1) // batch_size

            progress_bar = tqdm(
                total=len(documents),
                desc="🔍 Classifying documents",
                unit="doc"
            )

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(documents))
                batch = documents[start_idx:end_idx]

                # Adjust workers before each batch
                self.adjust_workers()

                # Process batch in parallel
                with ThreadPoolExecutor(max_workers=self.current_workers) as executor:
                    future_to_doc = {
                        executor.submit(self.process_document, doc): doc
                        for doc in batch
                    }

                    for future in as_completed(future_to_doc):
                        result = future.result()
                        results.append(result)
                        progress_bar.update(1)

                        # Update progress bar description
                        resources = self.resource_monitor.get_status()
                        progress_bar.set_postfix({
                            "Workers": self.current_workers,
                            "CPU": f"{resources['max_cpu']:.1f}%",
                            "RAM": f"{resources['memory_percent']:.1f}%",
                            "Classified": self.stats["classified"],
                            "Rejected": self.stats["rejected_as_jine"]
                        })

            progress_bar.close()

        finally:
            # Stop resource monitor
            self.resource_monitor.stop()

        return results

    def print_summary(self):
        """Print classification summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 CLASSIFICATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Processed:      {self.stats['total_processed']}")
        logger.info(f"✅ Classified:         {self.stats['classified']}")
        logger.info(f"❌ Rejected as 'jine': {self.stats['rejected_as_jine']}")
        logger.info(f"⚠️  Errors:             {self.stats['errors']}")
        logger.info(f"🔄 Retries:            {self.stats['retries']}")
        logger.info(f"📈 Worker Adjustments: {self.stats['worker_adjustments']}")
        logger.info("=" * 60)

        # Calculate accuracy
        total = self.stats['total_processed']
        if total > 0:
            success_rate = (self.stats['classified'] / total) * 100
            logger.info(f"✨ Success Rate: {success_rate:.1f}%")

    def close(self):
        """Clean up resources"""
        self.resource_monitor.stop()
        self.conn.close()


if __name__ == "__main__":
    logger.info("🚀 Starting Production Document Scanner v3.0")
    logger.info(f"📦 Model: {MODEL_NAME} (671 BILLION parameters!)")
    logger.info(f"👥 Initial Workers: {INITIAL_WORKERS}")
    logger.info(f"🎯 Target: >95% classification accuracy")

    # Example usage
    classifier = DocumentClassifier()

    # Example documents (in real use, load from database/files)
    test_documents = [
        {
            "file_path": "/tmp/test_invoice.pdf",
            "text_content": "Faktura č. 2025001\nIČO: 12345678\nCelkem: 1500 CZK"
        }
    ]

    try:
        results = classifier.scan_documents(test_documents)
        classifier.print_summary()

        # Print results
        for result in results:
            logger.info(f"\n📄 {result['filename']}")
            logger.info(f"   Type: {result['document_type']}")
            logger.info(f"   Score: {result['score']}/200 ({result['confidence_percent']}%)")
            logger.info(f"   Level: {result['confidence_level']}")

    finally:
        classifier.close()
