#!/usr/bin/env python3
"""
PRODUKČNÍ LLM SCAN - Posledních 3 let emailů
================================================
Spouští LLM scanner na posledních 3 letech (1095 dní)
Model: kimi-k2:1t-cloud (1T parametrů)
Očekávaná doba: 4-8 hodin
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Import production scanner
sys.path.insert(0, '/tmp')
from production_llm_scanner import ProductionLLMScanner

# Konfigurace logování
LOG_FILE = f"/tmp/production_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Spustí produkční scan na 3 letech emailů"""

    # Konfigurace
    DB_PATH = "/tmp/production_subscriptions.db"
    PROFILE_PATH = Path.home() / "Library/Thunderbird/Profiles/1oli4gwg.default-esr"
    DAYS_BACK = 1095  # 3 roky = 3 × 365

    logger.info("="*80)
    logger.info("PRODUKČNÍ LLM SCAN - 3 ROKY EMAILŮ")
    logger.info("="*80)
    logger.info(f"Model: kimi-k2:1t-cloud (1 trillion parametrů)")
    logger.info(f"Databáze: {DB_PATH}")
    logger.info(f"Thunderbird profil: {PROFILE_PATH}")
    logger.info(f"Období: Posledních {DAYS_BACK} dní (3 roky)")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("="*80)

    # Ověření Thunderbird profilu
    if not PROFILE_PATH.exists():
        logger.error(f"Thunderbird profil neexistuje: {PROFILE_PATH}")
        return 1

    # Najít INBOX soubory
    inbox_paths = []
    for imap_dir in PROFILE_PATH.glob("ImapMail/*"):
        inbox = imap_dir / "INBOX"
        if inbox.exists() and inbox.is_file():
            inbox_paths.append(inbox)
            logger.info(f"Nalezen INBOX: {inbox}")

    if not inbox_paths:
        logger.error("Nenalezeny žádné INBOX soubory!")
        return 1

    logger.info(f"\nCelkem nalezeno {len(inbox_paths)} INBOX souborů")
    logger.info("Zahajuji LLM scan...")
    logger.info("")

    # Vytvoř scanner
    scanner = ProductionLLMScanner(DB_PATH)

    try:
        # Scan všech INBOX souborů
        start_time = datetime.now()
        all_results = []

        for idx, inbox_path in enumerate(inbox_paths, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"INBOX {idx}/{len(inbox_paths)}: {inbox_path.name}")
            logger.info(f"{'='*80}")

            results = scanner.scan_thunderbird_mbox(inbox_path, days_back=DAYS_BACK)
            all_results.extend(results)

            logger.info(f"\nINBOX {idx} dokončen - nalezeno {len(results)} předplatných")

        # Celková statistika
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info(f"\n{'='*80}")
        logger.info("PRODUKČNÍ SCAN DOKONČEN!")
        logger.info(f"{'='*80}")
        logger.info(f"Celková doba: {duration}")
        logger.info(f"Nalezeno předplatných: {len(all_results)}")
        logger.info(f"Databáze: {DB_PATH}")
        logger.info(f"Log file: {LOG_FILE}")

        # Detailní statistika
        scanner.print_statistics()

        # Top 20 výsledků
        if all_results:
            logger.info(f"\n{'='*80}")
            logger.info("TOP 20 NALEZENÝCH PŘEDPLATNÝCH")
            logger.info(f"{'='*80}\n")

            for i, result in enumerate(all_results[:20], 1):
                logger.info(f"{i}. {result['service_name']} ({result['confidence']}% confidence)")
                logger.info(f"   Subject: {result['subject']}")
                if result['amount']:
                    logger.info(f"   Amount: {result['amount']} {result['currency']}")
                if result['subscription_type']:
                    logger.info(f"   Type: {result['subscription_type']}")
                logger.info(f"   Reasoning: {result['reasoning']}")
                logger.info("")

        logger.info(f"\n✅ Scan úspěšně dokončen!")
        logger.info(f"Výsledky uloženy v: {DB_PATH}")
        logger.info(f"Kompletní log: {LOG_FILE}")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scan přerušen uživatelem (Ctrl+C)")
        logger.info(f"Částečné výsledky v: {DB_PATH}")
        scanner.print_statistics()
        return 130

    except Exception as e:
        logger.error(f"\n❌ Fatální chyba: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Neočekávaná chyba: {e}")
        sys.exit(1)
