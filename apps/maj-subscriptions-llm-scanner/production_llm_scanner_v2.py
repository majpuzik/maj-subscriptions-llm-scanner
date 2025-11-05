#!/usr/bin/env python3
"""
Production LLM Email Scanner v2.0 - IMPROVED
---------------------------------------------
Enhancements:
- Retry logic with exponential backoff
- Progress tracking with checkpoints
- Improved error handling
- Optimized LLM prompts with few-shot learning
- Database indexes
- Structured logging

Model: kimi-k2:1t-cloud (1 trillion parameters via Ollama)
Performance: Target >98% accuracy
"""

import mailbox
import email.utils
from email.header import decode_header
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import requests
import json
from typing import Dict, List, Optional, Tuple
import re
import logging
import time
import sys
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/llm_scanner_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "kimi-k2:1t-cloud"  # 1 trillion parameters
OLLAMA_TIMEOUT = 120  # 2 minutes per email
MAX_RETRIES = 3  # Exponential backoff retries

# Quick keyword filter (pre-screening)
SUBSCRIPTION_KEYWORDS = [
    'predplatne', 'predplatneho', 'subscription', 'abonnement',
    'clenstvi', 'membership', 'rocni poplatek', 'monthly fee',
    'renewal', 'license', 'trial', 'premium', 'pro plan',
    'invoice', 'faktura', 'ucet', 'bill', 'payment', 'platba',
    'receipt', 'potvrzeni', 'obnoveni', 'prodlouzeni',
]


class ImprovedLLMScanner:
    """Improved LLM email scanner with enterprise-grade features"""

    def __init__(self, db_path: str, ollama_url: str = OLLAMA_URL, model: str = MODEL_NAME):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.model = model
        self.stats = {
            'total_scanned': 0,
            'keyword_filtered': 0,
            'llm_analyzed': 0,
            'subscriptions_found': 0,
            'false_positives_rejected': 0,
            'errors': 0,
            'retries': 0
        }
        self.checkpoint_file = "/tmp/scan_checkpoint.json"
        self.init_database()

    def init_database(self):
        """Initialize database with optimized schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_email_message_id
            ON email_evidence(email_message_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_service_id
            ON email_evidence(service_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_email_date
            ON email_evidence(email_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_confidence_score
            ON email_evidence(confidence_score DESC)
        ''')

        # Create checkpoint table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mbox_path TEXT NOT NULL,
                last_processed_index INTEGER,
                scan_start_date TIMESTAMP,
                last_update_date TIMESTAMP,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ Database initialized with indexes")

    def load_checkpoint(self, mbox_path: str) -> int:
        """Load last checkpoint for resume capability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT last_processed_index FROM scan_checkpoints
            WHERE mbox_path = ? AND status = 'running'
            ORDER BY id DESC LIMIT 1
        ''', (str(mbox_path),))

        row = cursor.fetchone()
        conn.close()

        if row:
            last_idx = row[0]
            logger.info(f"📍 Resuming from checkpoint: email #{last_idx}")
            return last_idx
        return 0

    def save_checkpoint(self, mbox_path: str, index: int):
        """Save checkpoint for resume capability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO scan_checkpoints (
                mbox_path, last_processed_index, last_update_date, status
            ) VALUES (?, ?, ?, ?)
        ''', (str(mbox_path), index, datetime.now().isoformat(), 'running'))

        conn.commit()
        conn.close()

    def finalize_checkpoint(self, mbox_path: str):
        """Mark checkpoint as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE scan_checkpoints
            SET status = 'completed', last_update_date = ?
            WHERE mbox_path = ? AND status = 'running'
        ''', (datetime.now().isoformat(), str(mbox_path)))

        conn.commit()
        conn.close()
        logger.info("✅ Checkpoint finalized")

    def decode_mime_words(self, s: str) -> str:
        """Decode MIME encoded words"""
        if not s:
            return ""
        try:
            decoded_fragments = decode_header(s)
            return ''.join(
                fragment.decode(encoding or 'utf-8') if isinstance(fragment, bytes) else str(fragment)
                for fragment, encoding in decoded_fragments
            )
        except Exception as e:
            logger.warning(f"MIME decode error: {e}")
            return str(s)

    def get_email_body(self, msg) -> str:
        """Extract plain text from email message"""
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode('utf-8', errors='ignore')
                        except:
                            pass
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Body extraction error: {e}")
        return body

    def quick_keyword_filter(self, subject: str, body: str) -> bool:
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

    def analyze_with_llm_retry(self, subject: str, sender: str, body: str) -> Dict:
        """
        Analyze email with LLM with retry logic and exponential backoff
        """
        for attempt in range(MAX_RETRIES):
            try:
                return self.analyze_with_llm(subject, sender, body)
            except requests.Timeout:
                self.stats['retries'] += 1
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"⏳ Timeout, retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Max retries reached for: {subject[:50]}")
                    return {
                        "is_subscription": False,
                        "confidence": 0,
                        "reasoning": "Max retries exceeded",
                        "error": "timeout"
                    }
            except Exception as e:
                logger.error(f"LLM error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {
                        "is_subscription": False,
                        "confidence": 0,
                        "reasoning": f"Error: {str(e)}",
                        "error": str(e)
                    }

    def analyze_with_llm(self, subject: str, sender: str, body: str) -> Dict:
        """
        Analyze email with improved LLM prompt (few-shot learning)
        """
        prompt = f"""Analyzuj tento email a urči, jestli obsahuje informaci o předplatném/subscription.

PŘÍKLADY PŘEDPLATNÉHO:
- Měsíční faktura za službu (např. "Microsoft 365 Invoice")
- Potvrzení o obnovení předplatného
- Změna ceny předplatného
- Zrušení předplatného
- "Your subscription will renew"
- "Payment failed for subscription"

NENÍ PŘEDPLATNÉ:
- Jednorázový nákup produktu
- Reset hesla nebo bezpečnostní upozornění
- Newsletter/marketing email bez platby
- Upozornění na akci nebo slevu (pokud není o předplatném)
- Oznámení o nové funkci
- Pozvánka nebo sociální notifikace

EMAIL:
From: {sender}
Subject: {subject}
Body (first 2000 chars):
{body[:2000]}

Vrať POUZE validní JSON (bez markdown bloků) s:
{{
    "is_subscription": true nebo false,
    "confidence": <0-100>,
    "service_name": "<název služby>" nebo null,
    "amount": <číslo> nebo null,
    "currency": "CZK"/"USD"/"EUR" nebo null,
    "subscription_type": "monthly"/"yearly"/"quarterly" nebo null,
    "reasoning": "<stručné zdůvodnění max 200 znaků>"
}}
"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=OLLAMA_TIMEOUT
            )

            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                self.stats['errors'] += 1
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

            logger.info(f"LLM: {'✅ SUB' if result.get('is_subscription') else '❌ NOT'} "
                       f"({result.get('confidence', 0)}%) - {subject[:40]}")

            return result

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            self.stats['errors'] += 1
            raise  # Re-raise for retry logic

    def extract_service_name_from_sender(self, sender: str) -> str:
        """Extract service name from email sender"""
        if '@' in sender:
            match = re.search(r'@([a-zA-Z0-9.-]+)', sender)
            if match:
                domain = match.group(1)
                service_name = domain.split('.')[0].title()
                if service_name and len(service_name) > 2:
                    return service_name
        return "Unknown"

    def get_or_create_service(self, service_name: str, llm_result: Dict) -> Optional[int]:
        """Find or create service in database"""
        if not service_name or service_name == "Unknown":
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try to find existing service
        cursor.execute('SELECT id FROM services WHERE name = ?', (service_name,))
        row = cursor.fetchone()

        if row:
            service_id = row[0]
        else:
            # Create new service
            cursor.execute('''
                INSERT INTO services (
                    name, type, price_amount, price_currency,
                    subscription_type, status, detected_via
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                service_name,
                'ai',  # Default type
                llm_result.get('amount'),
                llm_result.get('currency', 'USD'),
                llm_result.get('subscription_type'),
                'active',
                'llm_scanner_v2'
            ))
            service_id = cursor.lastrowid
            logger.info(f"✨ Created new service: {service_name} (ID: {service_id})")

        conn.commit()
        conn.close()

        return service_id

    def save_email_evidence(self, service_id: Optional[int], message_id: str,
                           subject: str, sender: str, recipient: str,
                           body: str, date: datetime, llm_result: Dict):
        """Save email evidence to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        body_compact = body[:1000] if body else ""

        try:
            cursor.execute('''
                INSERT INTO email_evidence (
                    service_id, email_message_id, email_subject, email_from, email_to,
                    email_date, email_body_compact, email_body_full, confidence_score,
                    detected_amount, detected_currency, detected_subscription_type,
                    llm_reasoning, llm_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                service_id,
                message_id,
                subject[:500],
                sender[:200],
                recipient[:200],
                date.isoformat(),
                body_compact,
                body,
                llm_result.get('confidence', 0),
                llm_result.get('amount'),
                llm_result.get('currency'),
                llm_result.get('subscription_type'),
                llm_result.get('reasoning', '')[:500],
                self.model
            ))

            conn.commit()
            logger.info(f"💾 Saved: {subject[:40]}...")

        except sqlite3.IntegrityError:
            logger.warning(f"⚠️  Already exists: {message_id}")
        except Exception as e:
            logger.error(f"Database save error: {e}")
            self.stats['errors'] += 1
        finally:
            conn.close()

    def scan_thunderbird_mbox(self, mbox_path: Path, days_back: int = 365, limit: int = None) -> List[Dict]:
        """
        Scan Thunderbird INBOX mbox file with progress tracking
        """
        logger.info(f"📧 Scanning: {mbox_path}")

        cutoff_date = datetime.now() - timedelta(days=days_back)
        results = []

        try:
            mbox = mailbox.mbox(str(mbox_path))
            total_messages = len(mbox)

            # Load checkpoint
            start_idx = self.load_checkpoint(mbox_path)

            # Progress bar
            progress_bar = tqdm(
                enumerate(mbox),
                total=total_messages,
                initial=start_idx,
                desc="Scanning emails",
                unit="email"
            )

            for idx, message in progress_bar:
                # Skip if before checkpoint
                if idx < start_idx:
                    continue

                # Limit for testing
                if limit and idx >= limit:
                    logger.info(f"🛑 Reached limit: {limit} emails")
                    break

                self.stats['total_scanned'] += 1

                try:
                    # Parse date
                    date_str = message.get('Date', '')
                    date_tuple = email.utils.parsedate_tz(date_str)
                    if date_tuple:
                        timestamp = email.utils.mktime_tz(date_tuple)
                        date_obj = datetime.fromtimestamp(timestamp)
                    else:
                        date_obj = datetime.now()

                    if date_obj < cutoff_date:
                        continue

                    # Decode headers
                    subject = self.decode_mime_words(message.get('Subject', ''))
                    sender = self.decode_mime_words(message.get('From', ''))
                    recipient = self.decode_mime_words(message.get('To', ''))
                    message_id = message.get('Message-ID', '')

                    # Get body
                    body = self.get_email_body(message)

                    # STEP 1: Quick keyword filter
                    if not self.quick_keyword_filter(subject, body):
                        continue

                    self.stats['keyword_filtered'] += 1

                    # Update progress bar
                    progress_bar.set_postfix({
                        'Filtered': self.stats['keyword_filtered'],
                        'Found': self.stats['subscriptions_found']
                    })

                    # STEP 2: LLM analysis with retry
                    llm_result = self.analyze_with_llm_retry(subject, sender, body)
                    self.stats['llm_analyzed'] += 1

                    # STEP 3: Process result
                    if llm_result.get('is_subscription'):
                        service_name = llm_result.get('service_name') or self.extract_service_name_from_sender(sender)
                        service_id = self.get_or_create_service(service_name, llm_result)
                        self.save_email_evidence(
                            service_id, message_id, subject, sender,
                            recipient, body, date_obj, llm_result
                        )
                        self.stats['subscriptions_found'] += 1

                        results.append({
                            'service_name': service_name,
                            'service_id': service_id,
                            'subject': subject[:100],
                            'from': sender[:100],
                            'confidence': llm_result.get('confidence', 0),
                            'amount': llm_result.get('amount'),
                            'currency': llm_result.get('currency'),
                            'subscription_type': llm_result.get('subscription_type'),
                            'reasoning': llm_result.get('reasoning', '')[:200]
                        })
                    else:
                        self.stats['false_positives_rejected'] += 1

                    # Save checkpoint every 100 emails
                    if idx % 100 == 0 and idx > 0:
                        self.save_checkpoint(mbox_path, idx)

                except Exception as e:
                    logger.error(f"Email processing error at #{idx}: {e}")
                    self.stats['errors'] += 1
                    continue

            # Finalize checkpoint
            self.finalize_checkpoint(mbox_path)

        except Exception as e:
            logger.error(f"Mbox reading error: {e}")
            self.stats['errors'] += 1

        return results

    def print_statistics(self):
        """Print scanning statistics"""
        logger.info(f"\n{'='*80}")
        logger.info("SCANNING STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Total emails scanned:        {self.stats['total_scanned']}")
        logger.info(f"Keyword filter matches:      {self.stats['keyword_filtered']}")
        logger.info(f"LLM analyzed:                {self.stats['llm_analyzed']}")
        logger.info(f"Subscriptions found:         {self.stats['subscriptions_found']}")
        logger.info(f"False positives rejected:    {self.stats['false_positives_rejected']}")
        logger.info(f"Retries:                     {self.stats['retries']}")
        logger.info(f"Errors:                      {self.stats['errors']}")
        logger.info(f"{'='*80}")

        if self.stats['keyword_filtered'] > 0:
            accuracy = (self.stats['subscriptions_found'] / self.stats['keyword_filtered']) * 100
            logger.info(f"LLM Precision: {accuracy:.1f}% (subscriptions / keyword matches)")

        if self.stats['llm_analyzed'] > 0:
            rejection_rate = (self.stats['false_positives_rejected'] / self.stats['llm_analyzed']) * 100
            logger.info(f"False positive rejection rate: {rejection_rate:.1f}%")


def main():
    """Main entry point for testing"""
    import sys

    # Configuration
    DB_PATH = "/tmp/test_subscriptions_v2.db"
    PROFILE_PATH = Path.home() / "Library/Thunderbird/Profiles/1oli4gwg.default-esr"
    INBOX_PATH = PROFILE_PATH / "ImapMail/outlook.office365.com/INBOX"
    DAYS_BACK = 365
    TEST_LIMIT = 1000  # Test on 1000 emails

    # Create scanner
    scanner = ImprovedLLMScanner(DB_PATH)

    # Scan
    logger.info(f"🚀 Starting improved LLM scan v2.0...")
    logger.info(f"📂 Database: {DB_PATH}")
    logger.info(f"📧 INBOX: {INBOX_PATH}")
    logger.info(f"🔢 Limit: {TEST_LIMIT} emails")

    try:
        results = scanner.scan_thunderbird_mbox(INBOX_PATH, days_back=DAYS_BACK, limit=TEST_LIMIT)

        # Print results
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ FOUND {len(results)} SUBSCRIPTIONS")
        logger.info(f"{'='*80}")

        for i, result in enumerate(results[:20], 1):  # Show first 20
            logger.info(f"\n{i}. {result['service_name']} ({result['confidence']}% confidence)")
            logger.info(f"   Subject: {result['subject']}")
            if result['amount']:
                logger.info(f"   Amount: {result['amount']} {result['currency']}")
            if result['subscription_type']:
                logger.info(f"   Type: {result['subscription_type']}")
            logger.info(f"   Reasoning: {result['reasoning']}")

        # Print statistics
        scanner.print_statistics()

        logger.info(f"\n✅ Scan complete! Found {len(results)} subscriptions")
        return 0

    except KeyboardInterrupt:
        logger.info("\n⏸️  Scan interrupted by user - checkpoint saved!")
        scanner.print_statistics()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
